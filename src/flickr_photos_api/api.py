from collections.abc import Iterator
import functools
import itertools
import xml.etree.ElementTree as ET

from flickr_url_parser import ParseResult, parse_flickr_url
import httpx
from nitrate.xml import (
    find_optional_text,
    find_required_elem,
    find_required_text,
)
from tenacity import (
    retry,
    retry_if_exception,
    RetryError,
    stop_after_attempt,
    wait_random_exponential,
)

from .exceptions import (
    FlickrApiException,
    InvalidApiKey,
    InvalidXmlException,
    LicenseNotFound,
    ResourceNotFound,
)
from .types import (
    CollectionOfElements,
    CollectionOfPhotos,
    Comment,
    GroupInfo,
    License,
    PhotosFromUrl,
    PhotosInAlbum,
    PhotosInGallery,
    PhotosInGroup,
    SinglePhoto,
    SinglePhotoInfo,
    Size,
    User,
    UserInfo,
)
from .utils import (
    parse_date_posted,
    parse_date_taken,
    parse_location,
    parse_safety_level,
    parse_sizes,
)


def is_retryable(exc: BaseException) -> bool:
    """
    Returns True if this is an exception we can safely retry (i.e. flaky
    or transient errors that might return a different result),or
    False otherwise.
    """
    if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code == 500:
        return True

    if isinstance(exc, httpx.ReadTimeout):
        return True

    if isinstance(exc, InvalidXmlException):
        return True

    # Sometimes we get an error from the Flickr API like:
    #
    #     <err
    #       code="201"
    #       msg="Sorry, the Flickr API service is not currently available."
    #     />
    #
    # but this indicates a flaky connection rather than a genuine failure.
    if (
        isinstance(exc, FlickrApiException)
        and isinstance(exc.args[0], dict)
        and exc.args[0].get("code") == "201"
    ):
        return True

    return False


class BaseApi:
    """
    This is a thin wrapper for calling the Flickr API.

    It doesn't do much interesting stuff; the goal is just to reduce boilerplate
    in the rest of the codebase, e.g. have the XML parsing in one place rather
    than repeated everywhere.
    """

    def __init__(self, *, api_key: str, user_agent: str) -> None:
        if not api_key:
            raise ValueError(
                "Cannot create a client with an empty string as the API key"
            )

        self.client = httpx.Client(
            base_url="https://api.flickr.com/services/rest/",
            params={"api_key": api_key},
            headers={"User-Agent": user_agent},
        )

    def call(self, *, method: str, params: dict[str, str] | None = None) -> ET.Element:
        try:
            return self._call_api(method=method, params=params)
        except RetryError as retry_err:
            retry_err.reraise()

    @retry(
        retry=retry_if_exception(is_retryable),
        stop=stop_after_attempt(5),
        wait=wait_random_exponential(),
    )
    def _call_api(self, *, method: str, params: dict[str, str] | None) -> ET.Element:
        if params is not None:
            get_params = {"method": method, **params}
        else:
            get_params = {"method": method}

        resp = self.client.get(url="", params=get_params, timeout=15)
        resp.raise_for_status()

        # Note: the xml.etree.ElementTree is not secure against maliciously
        # constructed data (see warning in the Python docs [1]), but that's
        # fine here -- we're only using it for responses from the Flickr API,
        # which we trust.
        #
        # However, on occasion I have seen it return error messages in
        # JSON rather than XML, which causes this method to fail -- make
        # sure we log the offending text, and allow it to be retried as
        # a temporary failure.
        #
        # [1]: https://docs.python.org/3/library/xml.etree.elementtree.html
        try:
            xml = ET.fromstring(resp.text)
        except ET.ParseError as err:
            raise InvalidXmlException(
                f"Unable to parse response as XML ({resp.text!r}), got error {err}"
            )

        # If the Flickr API call fails, it will return a block of XML like:
        #
        #       <rsp stat="fail">
        #       	<err
        #               code="1"
        #               msg="Photo &quot;1211111111111111&quot; not found (invalid ID)"
        #           />
        #       </rsp>
        #
        # Different API endpoints have different codes, and so we just throw
        # and let calling functions decide how to handle it.
        if xml.attrib["stat"] == "fail":
            errors = find_required_elem(xml, path=".//err").attrib

            # Although I haven't found any explicit documentation of this,
            # it seems like a pretty common convention that error code "1"
            # means "not found".
            if errors["code"] == "1":
                raise ResourceNotFound(method, params)
            elif errors["code"] == "100":
                raise InvalidApiKey(message=errors["msg"])
            else:
                raise FlickrApiException(errors)

        return xml

    def _get_page_of_photos(
        self,
        *,
        method: str,
        params: dict[str, str],
        page: int = 1,
        per_page: int = 1,
    ) -> CollectionOfElements:
        """
        Get a single page of photos from the Flickr API.

        This returns a list of the raw XML elements, so different callers
        can apply their own processing, e.g. depending on which ``extras``
        they decided to include.
        """
        resp = self.call(
            method=method,
            params={**params, "page": str(page), "per_page": str(per_page)},
        )

        collection_elem = resp[0]

        # The wrapper element includes a couple of attributes related
        # to pagination, e.g.
        #
        #     <photoset pages="1" total="2" …>
        #
        page_count = int(collection_elem.attrib["pages"])
        total_photos = int(collection_elem.attrib["total"])

        elements = collection_elem.findall(".//photo")

        return {
            "page_count": page_count,
            "total_photos": total_photos,
            "root": resp,
            "elements": elements,
        }

    def _get_stream_of_photos(
        self, *, method: str, params: dict[str, str]
    ) -> Iterator[ET.Element]:
        """
        Get a continuous stream of photos from the Flickr API.

        This returns an iterator of the raw XML elements, so different callers
        can apply their own processing, e.g. depending on which ``extras``
        they decided to include.
        """
        if "extras" not in params:
            params["extras"] = "date_upload"
        elif "date_upload" not in params["extras"].split(","):
            params["extras"] += ",date_upload"

        assert "per_page" not in params
        assert "page" not in params

        for page in itertools.count(start=1):
            resp = self.call(
                method=method,
                params={
                    "per_page": "500",
                    "page": str(page),
                    **params,
                },
            )

            if len(resp) == 1:
                collection_elem = resp[0]
            else:  # pragma: no cover
                raise ValueError(
                    f"Found multiple elements in response: {ET.tostring(resp).decode('utf8')}"
                )

            photos_in_page = collection_elem.findall("photo")

            yield from photos_in_page

            if not photos_in_page:
                break

        # This branch will only be executed if the ``for`` loop exits
        # without a ``break``.  This will never happen; this is just here
        # to satisfy coverage.
        else:  # pragma: no cover
            assert False


class FlickrPhotosApi(BaseApi):
    @functools.lru_cache()
    def get_licenses(self) -> dict[str, License]:
        """
        Returns a list of licenses, arranged by code.

        See https://www.flickr.com/services/api/flickr.photos.licenses.getInfo.htm
        """
        license_resp = self.call(method="flickr.photos.licenses.getInfo")

        result: dict[str, License] = {}

        # Add a short ID which can be used to more easily refer to this
        # license throughout the codebase.
        license_ids = {
            "All Rights Reserved": "in-copyright",
            "Attribution-NonCommercial-ShareAlike License": "cc-by-nc-sa-2.0",
            "Attribution-NonCommercial License": "cc-by-nc-2.0",
            "Attribution-NonCommercial-NoDerivs License": "cc-by-nc-nd-2.0",
            "Attribution License": "cc-by-2.0",
            "Attribution-ShareAlike License": "cc-by-sa-2.0",
            "Attribution-NoDerivs License": "cc-by-nd-2.0",
            "No known copyright restrictions": "nkcr",
            "United States Government Work": "usgov",
            "Public Domain Dedication (CC0)": "cc0-1.0",
            "Public Domain Mark": "pdm",
        }

        license_labels = {
            "Attribution-NonCommercial-ShareAlike License": "CC BY-NC-SA 2.0",
            "Attribution-NonCommercial License": "CC BY-NC 2.0",
            "Attribution-NonCommercial-NoDerivs License": "CC BY-NC-ND 2.0",
            "Attribution License": "CC BY 2.0",
            "Attribution-ShareAlike License": "CC BY-SA 2.0",
            "Attribution-NoDerivs License": "CC BY-ND 2.0",
            "Public Domain Dedication (CC0)": "CC0 1.0",
        }

        for lic in license_resp.findall(".//license"):
            result[lic.attrib["id"]] = {
                "id": license_ids[lic.attrib["name"]],
                "label": license_labels.get(lic.attrib["name"], lic.attrib["name"]),
                "url": lic.attrib["url"] or None,
            }

        return result

    @functools.lru_cache(maxsize=None)
    def lookup_license_by_id(self, *, id: str) -> License:
        """
        Given a license ID from the Flickr API, return the license data.

        e.g. a Flickr API response might include a photo in the following form:

            <photo license="0" …>

        Then you'd call this function to find out what that means:

            >>> api.lookup_license_by_id(id="0")
            {"id": "in-copyright", "name": "All Rights Reserved", "url": None}

        See https://www.flickr.com/services/api/flickr.photos.licenses.getInfo.htm
        """
        licenses = self.get_licenses()

        try:
            return licenses[id]
        except KeyError:
            raise LicenseNotFound(license_id=id)

    def lookup_user_by_id(self, *, user_id: str) -> UserInfo:
        """
        Given the link to a user's photos or profile, return their info.

            >>> api.lookup_user_by_id(user_id="12403504@N02")
            {
                "id": "12403504@N02",
                "username": "The British Library",
                "realname": "British Library",
                "photos_url": "https://www.flickr.com/photos/britishlibrary/",
                "profile_url": "https://www.flickr.com/people/britishlibrary/",
                "pathalias": "britishlibrary",
                "description": "The British Library’s collections…",
                "has_pro_account": True,
                "count_photos": 1234,
            }

        See https://www.flickr.com/services/api/flickr.people.getInfo.htm

        """
        # The getInfo response is of the form:
        #
        #     <person id="12403504@N02" path_alias="britishlibrary" …>
        #   	<username>The British Library</username>
        #       <realname>British Library</realname>
        #       <description>The British Library’s collections…</description>
        #       <photosurl>flickr.com/photos/britishlibrary/</photosurl>
        #       <profileurl>flickr.com/people/britishlibrary/</profileurl>
        #       <photos>
        #         <count>1234</count>
        #       </photos>
        #       …
        #     </person>
        #
        info_resp = self.call(
            method="flickr.people.getInfo", params={"user_id": user_id}
        )

        person_elem = find_required_elem(info_resp, path="person")

        username = find_required_text(person_elem, path="username")
        photos_url = find_required_text(person_elem, path="photosurl")
        profile_url = find_required_text(person_elem, path="profileurl")
        description = find_optional_text(person_elem, path="description")

        path_alias = person_elem.attrib["path_alias"] or None

        photos_elem = find_required_elem(person_elem, path="photos")
        count_photos = int(find_required_text(photos_elem, path="count"))

        # This is a 0/1 boolean attribute
        has_pro_account = person_elem.attrib["ispro"] == "1"

        # If the user hasn't set a realname in their profile, the element
        # will be absent from the response.
        realname_elem = person_elem.find(path="realname")

        if realname_elem is None:
            realname = None
        else:
            realname = realname_elem.text

        return {
            "id": user_id,
            "username": username,
            "realname": realname,
            "description": description,
            "has_pro_account": has_pro_account,
            "path_alias": path_alias,
            "photos_url": photos_url,
            "profile_url": profile_url,
            "count_photos": count_photos,
        }

    def lookup_user_by_url(self, *, url: str) -> UserInfo:
        """
        Given the link to a user's photos or profile, return their info.

            >>> api.lookup_user_by_url(user_url="https://www.flickr.com/photos/britishlibrary/")
            {
                "id": "12403504@N02",
                "username": "The British Library",
                "realname": "British Library",
                "photos_url": "https://www.flickr.com/photos/britishlibrary/",
                "profile_url": "https://www.flickr.com/people/britishlibrary/",
                "pathalias": "britishlibrary",
                "description": "The British Library’s collections…",
                "has_pro_account": True,
                "count_photos": 1234,
            }

        See https://www.flickr.com/services/api/flickr.urls.lookupUser.htm
        See https://www.flickr.com/services/api/flickr.people.getInfo.htm

        """
        # The lookupUser response is of the form:
        #
        #       <user id="12403504@N02">
        #       	<username>The British Library</username>
        #       </user>
        #
        lookup_resp = self.call(method="flickr.urls.lookupUser", params={"url": url})
        user_id = find_required_elem(lookup_resp, path=".//user").attrib["id"]

        return self.lookup_user_by_id(user_id=user_id)

    def get_single_photo_info(self, *, photo_id: str) -> SinglePhotoInfo:
        """
        Look up the information for a single photo.

        This uses the flickr.photos.getInfo API.
        """
        info_resp = self.call(
            method="flickr.photos.getInfo", params={"photo_id": photo_id}
        )

        # The getInfo response is a blob of XML of the form:
        #
        #       <?xml version="1.0" encoding="utf-8" ?>
        #       <rsp stat="ok">
        #       <photo license="8" …>
        #       	<owner
        #               nsid="30884892@N08
        #               username="U.S. Coast Guard"
        #               realname="Coast Guard" …
        #           >
        #       		…
        #       	</owner>
        #       	<title>Puppy Kisses</title>
        #           <description>Seaman Nina Bowen shows …</description>
        #       	<dates
        #               posted="1490376472"
        #               taken="2017-02-17 00:00:00"
        #               …
        #           />
        #       	<urls>
        #       		<url type="photopage">https://www.flickr.com/photos/coast_guard/32812033543/</url>
        #       	</urls>
        #           <tags>
        #    		  <tag raw="indian ocean" …>indianocean</tag>
        #           …
        #       </photo>
        #       </rsp>
        #
        photo_elem = find_required_elem(info_resp, path=".//photo")

        safety_level = parse_safety_level(photo_elem.attrib["safety_level"])

        license = self.lookup_license_by_id(id=photo_elem.attrib["license"])

        title = find_optional_text(photo_elem, path="title")
        description = find_optional_text(photo_elem, path="description")

        owner_elem = find_required_elem(photo_elem, path="owner")
        user_id = owner_elem.attrib["nsid"]
        path_alias = owner_elem.attrib["path_alias"] or None

        owner: User = {
            "id": user_id,
            "username": owner_elem.attrib["username"],
            "realname": owner_elem.attrib["realname"] or None,
            "path_alias": path_alias,
            "photos_url": f"https://www.flickr.com/photos/{path_alias or user_id}/",
            "profile_url": f"https://www.flickr.com/people/{path_alias or user_id}/",
        }

        dates = find_required_elem(photo_elem, path="dates").attrib

        date_posted = parse_date_posted(dates["posted"])

        date_taken = parse_date_taken(
            value=dates["taken"],
            granularity=dates["takengranularity"],
            unknown=dates["takenunknown"] == "1",
        )

        photo_page_url = find_required_text(
            photo_elem, path='.//urls/url[@type="photopage"]'
        )

        count_comments = int(find_required_text(photo_elem, path="comments"))
        count_views = int(photo_elem.attrib["views"])

        # The originalformat parameter will only be returned if the user
        # allows downloads of the photo.
        #
        # We only need this parameter for photos that can be uploaded to
        # Wikimedia Commons.  All CC-licensed photos allow downloads, so
        # we'll always get this parameter for those photos.
        #
        # See https://www.flickr.com/help/forum/32218/
        # See https://www.flickrhelp.com/hc/en-us/articles/4404079715220-Download-permissions
        original_format = photo_elem.get("originalformat")

        # We have two options with tags: we can use the 'raw' version
        # entered by the user, or we can use the normalised version in
        # the tag text.
        #
        # e.g. "bay of bengal" vs "bayofbengal"
        #
        # We prefer the normalised version because it makes it possible
        # to compare tags across photos, and we only get the normalised
        # versions from the collection endpoints.
        tags_elem = find_required_elem(photo_elem, path="tags")

        tags = []
        for t in tags_elem.findall("tag"):
            assert t.text is not None
            tags.append(t.text)

        # Get location information about the photo.
        #
        # The <location> tag is only present in photos which have
        # location data; if the user hasn't made location available to
        # public users, it'll be missing.
        location_elem = photo_elem.find(path="location")

        if location_elem is not None:
            location = parse_location(location_elem)
        else:
            location = None

        return {
            "id": photo_id,
            "secret": photo_elem.attrib["secret"],
            "server": photo_elem.attrib["server"],
            "farm": photo_elem.attrib["farm"],
            "original_format": original_format,
            "owner": owner,
            "safety_level": safety_level,
            "license": license,
            "title": title,
            "description": description,
            "tags": tags,
            "date_posted": date_posted,
            "date_taken": date_taken,
            "location": location,
            "count_comments": count_comments,
            "count_views": count_views,
            "photo_page_url": photo_page_url,
        }

    def get_single_photo(self, *, photo_id: str) -> SinglePhoto:
        """
        Look up the information for a single photo.
        """
        info = self.get_single_photo_info(photo_id=photo_id)

        sizes_resp = self.call(
            method="flickr.photos.getSizes", params={"photo_id": photo_id}
        )

        # The getSizes response is a blob of XML of the form:
        #
        #       <?xml version="1.0" encoding="utf-8" ?>
        #       <rsp stat="ok">
        #       <sizes canblog="0" canprint="0" candownload="1">
        #           <size
        #               label="Square"
        #               width="75"
        #               height="75"
        #               source="https://live.staticflickr.com/2903/32812033543_c1b3784192_s.jpg"
        #               url="https://www.flickr.com/photos/coast_guard/32812033543/sizes/sq/"
        #               media="photo"
        #           />
        #           <size
        #               label="Large Square"
        #               width="150"
        #               height="150"
        #               source="https://live.staticflickr.com/2903/32812033543_c1b3784192_q.jpg"
        #               url="https://www.flickr.com/photos/coast_guard/32812033543/sizes/q/"
        #               media="photo"
        #           />
        #           …
        #       </sizes>
        #       </rsp>
        #
        # Within this function, we just return all the sizes -- we leave it up to the
        # caller to decide which size is most appropriate for their purposes.
        sizes: list[Size] = []

        for s in sizes_resp.findall(".//size"):
            if s.attrib["media"] == "photo":
                sizes.append(
                    {
                        "label": s.attrib["label"],
                        "width": int(s.attrib["width"]),
                        "height": int(s.attrib["height"]),
                        "media": "photo",
                        "source": s.attrib["source"],
                    }
                )

            elif s.attrib["media"] == "video":
                try:
                    width = int(s.attrib["width"])
                except ValueError:
                    width = None

                try:
                    height = int(s.attrib["height"])
                except ValueError:
                    height = None

                sizes.append(
                    {
                        "label": s.attrib["label"],
                        "width": width,
                        "height": height,
                        "media": "video",
                        "source": s.attrib["source"],
                    }
                )
            else:  # pragma: no cover
                raise ValueError(f"Unrecognised media type: {s.attrib['media']}")

        return {
            "id": photo_id,
            "title": info["title"],
            "description": info["description"],
            "owner": info["owner"],
            "date_posted": info["date_posted"],
            "date_taken": info["date_taken"],
            "safety_level": info["safety_level"],
            "license": info["license"],
            "url": info["photo_page_url"],
            "sizes": sizes,
            "original_format": info["original_format"],
            "tags": info["tags"],
            "location": info["location"],
        }

    # There are a bunch of similar flickr.XXX.getPhotos methods;
    # these are some constants and utility methods to help when
    # calling them.
    extras = [
        "license",
        "date_upload",
        "date_taken",
        "media",
        "original_format",
        "owner_name",
        "url_sq",
        "url_t",
        "url_s",
        "url_m",
        "url_o",
        "tags",
        "geo",
        # These parameters aren't documented, but they're quite
        # useful for our purposes!
        "url_q",  # Large Square
        "url_l",  # Large
        "description",
        "safety_level",
        "realname",
    ]

    def _to_photo(
        self, photo_elem: ET.Element, collection_owner: User | None = None
    ) -> SinglePhoto:
        photo_id = photo_elem.attrib["id"]

        title = photo_elem.attrib["title"] or None
        description = find_optional_text(photo_elem, path="description")

        tags = photo_elem.attrib["tags"].split()

        owner: User
        if collection_owner is None:
            owner_name = photo_elem.attrib["owner"]
            path_alias = photo_elem.attrib.get("pathalias") or None

            owner = {
                "id": photo_elem.attrib["owner"],
                "username": photo_elem.attrib["ownername"],
                "realname": photo_elem.attrib.get("realname") or None,
                "path_alias": path_alias,
                "photos_url": f"https://www.flickr.com/photos/{path_alias or owner_name}/",
                "profile_url": f"https://www.flickr.com/people/{path_alias or owner_name}/",
            }
        else:
            owner = {
                "id": collection_owner["id"],
                "username": collection_owner["username"],
                "realname": collection_owner["realname"],
                "path_alias": collection_owner["path_alias"],
                "photos_url": collection_owner["photos_url"],
                "profile_url": collection_owner["profile_url"],
            }

        assert owner["photos_url"].endswith("/")
        url = owner["photos_url"] + photo_id + "/"

        # The lat/long/accuracy fields will always be populated, even
        # if there's no geo-information on this photo -- they're just
        # set to zeroes.
        #
        # We have to use the presence of geo permissions on the
        # <photo> element to determine if there's actually location
        # information here, or if we're getting the defaults.
        if photo_elem.attrib.get("geo_is_public") == "1":
            location = parse_location(photo_elem)
        else:
            location = None

        return {
            "id": photo_id,
            "title": title,
            "description": description,
            "date_posted": parse_date_posted(photo_elem.attrib["dateupload"]),
            "date_taken": parse_date_taken(
                value=photo_elem.attrib["datetaken"],
                granularity=photo_elem.attrib["datetakengranularity"],
                unknown=photo_elem.attrib["datetakenunknown"] == "1",
            ),
            "license": self.lookup_license_by_id(id=photo_elem.attrib["license"]),
            "sizes": parse_sizes(photo_elem),
            "original_format": photo_elem.attrib.get("originalformat"),
            "safety_level": parse_safety_level(photo_elem.attrib["safety_level"]),
            "owner": owner,
            "url": url,
            "tags": tags,
            "location": location,
        }

    def get_photos_in_album(
        self, *, user_url: str, album_id: str, page: int = 1, per_page: int = 10
    ) -> PhotosInAlbum:
        """
        Get the photos in an album.
        """
        user_info = self.lookup_user_by_url(url=user_url)

        user: User = {
            "id": user_info["id"],
            "username": user_info["username"],
            "realname": user_info["realname"],
            "path_alias": user_info["path_alias"],
            "photos_url": user_info["photos_url"],
            "profile_url": user_info["profile_url"],
        }

        # https://www.flickr.com/services/api/flickr.photosets.getPhotos.html
        resp = self._get_page_of_photos(
            method="flickr.photosets.getPhotos",
            params={
                "user_id": user["id"],
                "photoset_id": album_id,
                "extras": ",".join(self.extras),
            },
            page=page,
            per_page=per_page,
        )

        # https://www.flickr.com/services/api/flickr.photosets.getInfo.html
        album_resp = self.call(
            method="flickr.photosets.getInfo",
            params={"user_id": user["id"], "photoset_id": album_id},
        )
        album_title = find_required_text(album_resp, path=".//title")

        return {
            "photos": [
                self._to_photo(photo_elem, collection_owner=user)
                for photo_elem in resp["elements"]
            ],
            "page_count": resp["page_count"],
            "total_photos": resp["total_photos"],
            "album": {"owner": user, "title": album_title},
        }

    def get_photos_in_gallery(
        self, *, gallery_id: str, page: int = 1, per_page: int = 10
    ) -> PhotosInGallery:
        """
        Get the photos in a gallery.
        """
        # https://www.flickr.com/services/api/flickr.galleries.getPhotos.html
        resp = self._get_page_of_photos(
            method="flickr.galleries.getPhotos",
            params={
                "gallery_id": gallery_id,
                "get_gallery_info": "1",
                "extras": ",".join(self.extras + ["path_alias"]),
            },
            page=page,
            per_page=per_page,
        )

        gallery_elem = find_required_elem(resp["root"], path=".//gallery")

        gallery_title = find_required_text(gallery_elem, path="title")
        gallery_owner_name = gallery_elem.attrib["username"]

        return {
            "photos": [self._to_photo(photo_elem) for photo_elem in resp["elements"]],
            "page_count": resp["page_count"],
            "total_photos": resp["total_photos"],
            "gallery": {"owner_name": gallery_owner_name, "title": gallery_title},
        }

    def get_public_photos_by_user(
        self, user_url: str, page: int = 1, per_page: int = 10
    ) -> CollectionOfPhotos:
        """
        Get all the public photos by a user on Flickr.
        """
        user = self.lookup_user_by_url(url=user_url)

        # See https://www.flickr.com/services/api/flickr.people.getPublicPhotos.html
        resp = self._get_page_of_photos(
            method="flickr.people.getPublicPhotos",
            params={
                "user_id": user["id"],
                "extras": ",".join(self.extras),
            },
            page=page,
            per_page=per_page,
        )

        return {
            "total_photos": resp["total_photos"],
            "page_count": resp["page_count"],
            "photos": [
                self._to_photo(photo_elem, collection_owner=user)
                for photo_elem in resp["elements"]
            ],
        }

    def lookup_group_from_url(self, *, url: str) -> GroupInfo:
        """
        Given the link to a group's photos or profile, return some info.
        """
        resp = self.call(method="flickr.urls.lookupGroup", params={"url": url})

        # The lookupUser response is of the form:
        #
        #       <group id="34427469792@N01">
        #         <groupname>FlickrCentral</groupname>
        #       </group>
        #
        group_elem = find_required_elem(resp, path=".//group")

        return {
            "id": group_elem.attrib["id"],
            "name": find_required_text(group_elem, path="groupname"),
        }

    def get_photos_in_group_pool(
        self, group_url: str, page: int = 1, per_page: int = 10
    ) -> PhotosInGroup:
        """
        Get all the photos in a group pool.
        """
        group_info = self.lookup_group_from_url(url=group_url)

        # See https://www.flickr.com/services/api/flickr.groups.pools.getPhotos.html
        resp = self._get_page_of_photos(
            method="flickr.groups.pools.getPhotos",
            params={
                "group_id": group_info["id"],
                "extras": ",".join(self.extras),
            },
            page=page,
            per_page=per_page,
        )

        return {
            "photos": [self._to_photo(photo_elem) for photo_elem in resp["elements"]],
            "page_count": resp["page_count"],
            "total_photos": resp["total_photos"],
            "group": group_info,
        }

    def get_photos_with_tag(
        self, tag: str, page: int = 1, per_page: int = 10
    ) -> CollectionOfPhotos:
        """
        Get all the photos that use a given tag.
        """
        resp = self._get_page_of_photos(
            method="flickr.photos.search",
            params={
                "tags": tag,
                # This is so we get the same photos as you see on the "tag" page
                # under "All Photos Tagged XYZ" -- if you click the URL to the
                # full search results, you end up on a page like:
                #
                #     https://flickr.com/search/?sort=interestingness-desc&…
                #
                "sort": "interestingness-desc",
                "extras": ",".join(self.extras),
            },
            page=page,
            per_page=per_page,
        )

        return {
            "total_photos": resp["total_photos"],
            "page_count": resp["page_count"],
            "photos": [self._to_photo(photo_elem) for photo_elem in resp["elements"]],
        }

    def get_photos_from_flickr_url(self, url: str) -> PhotosFromUrl:
        """
        Given a URL on Flickr.com, return the photos at that URL
        (if possible).

        This can throw a ``NotAFlickrUrl`` and ``UnrecognisedUrl`` exceptions.
        """
        parsed_url = parse_flickr_url(url)

        return self.get_photos_from_parsed_flickr_url(parsed_url)

    def get_photos_from_parsed_flickr_url(
        self, parsed_url: ParseResult
    ) -> PhotosFromUrl:
        """
        Given a URL on Flickr.com that's been parsed with flickr-url-parser,
        return the photos at that URL (if possible).
        """
        if parsed_url["type"] == "single_photo":
            return self.get_single_photo(photo_id=parsed_url["photo_id"])
        elif parsed_url["type"] == "album":
            return self.get_photos_in_album(
                user_url=parsed_url["user_url"],
                album_id=parsed_url["album_id"],
                page=parsed_url["page"],
                per_page=100,
            )
        elif parsed_url["type"] == "user":
            return self.get_public_photos_by_user(
                user_url=parsed_url["user_url"], page=parsed_url["page"], per_page=100
            )
        elif parsed_url["type"] == "gallery":
            return self.get_photos_in_gallery(
                gallery_id=parsed_url["gallery_id"],
                page=parsed_url["page"],
                per_page=100,
            )
        elif parsed_url["type"] == "group":
            return self.get_photos_in_group_pool(
                group_url=parsed_url["group_url"], page=parsed_url["page"], per_page=100
            )
        elif parsed_url["type"] == "tag":
            return self.get_photos_with_tag(
                tag=parsed_url["tag"], page=parsed_url["page"], per_page=100
            )
        else:
            raise TypeError(f"Unrecognised URL type: {parsed_url['type']}")

    @functools.lru_cache(maxsize=128)
    def get_buddy_icon_url(self, user_id: str) -> str:
        """
        Returns the URL of a user's "buddy icon".

        See https://www.flickr.com/services/api/misc.buddyicons.html
        """
        resp = self.call(method="flickr.people.getInfo", params={"user_id": user_id})

        person_elem = find_required_elem(resp, path="person")

        iconserver = int(person_elem.attrib["iconserver"])
        iconfarm = int(person_elem.attrib["iconfarm"])

        if iconserver > 0:
            return f"https://farm{iconfarm}.staticflickr.com/{iconserver}/buddyicons/{user_id}.jpg"
        else:
            return "https://www.flickr.com/images/buddyicon.gif"

    def list_all_comments(self, *, photo_id: str) -> list[Comment]:
        """
        List all the comments on a photo.

        See https://www.flickr.com/services/api/flickr.photos.comments.getList.htm
        """
        resp = self.call(
            method="flickr.photos.comments.getList", params={"photo_id": photo_id}
        )

        result: list[Comment] = []

        # The structure of the response is soemthing like:
        #
        #     <comment
        #       id="6065-109722179-72057594077818641"
        #       author="35468159852@N01"
        #       authorname="Rev Dan Catt"
        #       realname="Daniel Catt"
        #       datecreate="1141841470"
        #       permalink="http://www.flickr.com/photos/…"
        #     >
        #       Umm, I'm not sure, can I get back to you on that one?
        #     </comment>
        #
        for comment_elem in resp.findall(".//comment"):
            author_id = comment_elem.attrib["author"]
            author_path_alias = comment_elem.attrib["path_alias"] or None

            author: User = {
                "id": author_id,
                "username": comment_elem.attrib["authorname"],
                "realname": comment_elem.attrib["realname"] or None,
                "path_alias": author_path_alias,
                "photos_url": f"https://www.flickr.com/photos/{author_path_alias or author_id}/",
                "profile_url": f"https://www.flickr.com/people/{author_path_alias or author_id}/",
            }

            result.append(
                {
                    "id": comment_elem.attrib["id"],
                    "photo_id": photo_id,
                    "author_is_deleted": comment_elem.attrib["author_is_deleted"]
                    == "1",
                    "author": author,
                    "text": comment_elem.text or "",
                    "permalink": comment_elem.attrib["permalink"],
                    "date": parse_date_posted(comment_elem.attrib["datecreate"]),
                }
            )

        return result
