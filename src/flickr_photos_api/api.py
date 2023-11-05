import functools
from typing import Dict, List, Union
import xml.etree.ElementTree as ET

import httpx

from .exceptions import FlickrApiException, LicenseNotFound, ResourceNotFound
from .utils import (
    find_optional_text,
    find_required_elem,
    find_required_text,
    parse_date_posted,
    parse_date_taken,
    parse_date_taken_granularity,
    parse_safety_level,
)
from ._types import (
    DateTaken,
    License,
    SinglePhoto,
    Size,
    User,
)


class BaseApi:
    """
    This is a thin wrapper for calling the Flickr API.

    It doesn't do much interesting stuff; the goal is just to reduce boilerplate
    in the rest of the codebase, e.g. have the XML parsing in one place rather
    than repeated everywhere.
    """

    def __init__(self, *, api_key: str, user_agent: str) -> None:
        self.client = httpx.Client(
            base_url="https://api.flickr.com/services/rest/",
            params={"api_key": api_key},
            headers={"User-Agent": user_agent},
        )

    def call(self, method: str, **params: Union[str, int]) -> ET.Element:
        resp = self.client.get(url="", params={"method": method, **params})
        resp.raise_for_status()

        # Note: the xml.etree.ElementTree is not secure against maliciously
        # constructed data (see warning in the Python docs [1]), but that's
        # fine here -- we're only using it for responses from the Flickr API,
        # which we trust.
        #
        # [1]: https://docs.python.org/3/library/xml.etree.elementtree.html
        xml = ET.fromstring(resp.text)

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
                raise ResourceNotFound(method, **params)
            else:
                raise FlickrApiException(errors)

        return xml


class FlickrPhotosApi(BaseApi):
    @functools.lru_cache
    def get_licenses(self) -> Dict[str, License]:
        """
        Returns a list of licenses, arranged by code.

        See https://www.flickr.com/services/api/flickr.photos.licenses.getInfo.htm
        """
        license_resp = self.call("flickr.photos.licenses.getInfo")

        result: Dict[str, License] = {}

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

    def lookup_user_by_url(self, *, url: str) -> User:
        """
        Given the link to a user's photos or profile, return their info.

            >>> api.lookup_user_by_url(user_url="https://www.flickr.com/photos/britishlibrary/")
            {
                "id": "12403504@N02",
                "username": "The British Library",
                "realname": "British Library",
                "photos_url": "https://www.flickr.com/photos/britishlibrary/",
                "profile_url": "https://www.flickr.com/people/britishlibrary/",
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
        lookup_resp = self.call("flickr.urls.lookupUser", url=url)
        user_id = find_required_elem(lookup_resp, path=".//user").attrib["id"]

        # The getInfo response is of the form:

        #     <person id="12403504@N02"…">
        #   	<username>The British Library</username>
        #       <realname>British Library</realname>
        #       <photosurl>https://www.flickr.com/photos/britishlibrary/</photosurl>
        #       <profileurl>https://www.flickr.com/people/britishlibrary/</profileurl>
        #       …
        #     </person>
        #
        info_resp = self.call("flickr.people.getInfo", user_id=user_id)
        username = find_required_text(info_resp, path=".//username")
        photos_url = find_required_text(info_resp, path=".//photosurl")
        profile_url = find_required_text(info_resp, path=".//profileurl")

        # If the user hasn't set a realname in their profile, the element
        # will be absent from the response.
        realname_elem = info_resp.find(path=".//realname")

        if realname_elem is None:
            realname = None
        else:
            realname = realname_elem.text

        return {
            "id": user_id,
            "username": username,
            "realname": realname,
            "photos_url": photos_url,
            "profile_url": profile_url,
        }

    def get_single_photo(self, *, photo_id: str) -> SinglePhoto:
        """
        Look up the information for a single photo.
        """
        info_resp = self.call("flickr.photos.getInfo", photo_id=photo_id)
        sizes_resp = self.call("flickr.photos.getSizes", photo_id=photo_id)

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
        #           …
        #       </photo>
        #       </rsp>
        #
        photo_elem = find_required_elem(info_resp, path=".//photo")

        title = find_optional_text(photo_elem, path="title")
        description = find_optional_text(photo_elem, path="description")

        owner_elem = find_required_elem(photo_elem, path="owner")
        user_id = owner_elem.attrib["nsid"]
        path_alias = owner_elem.attrib["path_alias"] or user_id

        owner: User = {
            "id": user_id,
            "username": owner_elem.attrib["username"],
            "realname": owner_elem.attrib["realname"] or None,
            "photos_url": f"https://www.flickr.com/photos/{path_alias}/",
            "profile_url": f"https://www.flickr.com/people/{path_alias}/",
        }

        dates = find_required_elem(photo_elem, path="dates").attrib

        date_posted = parse_date_posted(dates["posted"])

        date_taken: DateTaken
        if dates["takenunknown"] == "1":
            date_taken = {"unknown": True}
        else:
            date_taken = {
                "value": parse_date_taken(dates["taken"]),
                "granularity": parse_date_taken_granularity(dates["takengranularity"]),
                "unknown": False,
            }

        photo_page_url = find_required_text(
            photo_elem, path='.//urls/url[@type="photopage"]'
        )

        license = self.lookup_license_by_id(id=photo_elem.attrib["license"])

        safety_level = parse_safety_level(photo_elem.attrib["safety_level"])

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
        sizes: List[Size] = []

        for s in sizes_resp.findall(".//size"):
            sizes.append(
                {
                    "label": s.attrib["label"],
                    "width": int(s.attrib["width"]),
                    "height": int(s.attrib["height"]),
                    "media": s.attrib["media"],
                    "source": s.attrib["source"],
                    "url": s.attrib["url"],
                }
            )

        return {
            "id": photo_id,
            "title": title,
            "description": description,
            "owner": owner,
            "date_posted": date_posted,
            "date_taken": date_taken,
            "safety_level": safety_level,
            "license": license,
            "url": photo_page_url,
            "sizes": sizes,
            "original_format": original_format,
        }
