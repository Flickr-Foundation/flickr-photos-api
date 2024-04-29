from collections.abc import Iterator
import itertools
import xml.etree.ElementTree as ET

from flickr_url_parser import ParseResult, parse_flickr_url
from nitrate.xml import (
    find_optional_text,
    find_required_elem,
    find_required_text,
)

from .base import HttpxImplementation as NewBaseApi, HttpxImplementation
from .comment_methods import CommentMethods
from .license_methods import LicenseMethods
from .single_photo_methods import SinglePhotoMethods
from .user_methods import UserMethods
from ..types import (
    CollectionOfElements,
    CollectionOfPhotos,
    GroupInfo,
    ParsedElement,
    PhotosFromUrl,
    PhotosInAlbum,
    PhotosInGallery,
    PhotosInGroup,
    SinglePhoto,
    User,
    user_info_to_user,
)
from ..utils import (
    parse_date_posted,
    parse_date_taken,
    parse_location,
    parse_safety_level,
    parse_sizes,
)


class FlickrApiMethods(CommentMethods, SinglePhotoMethods, LicenseMethods, UserMethods):
    pass


class FlickrApi(HttpxImplementation, FlickrApiMethods):
    pass


class BaseApi(NewBaseApi, FlickrApiMethods):
    def _to_parsed_element(self, photo_elem: ET.Element) -> ParsedElement:
        """
        Given a <photo> element from a collection response, parse some
        common fields that we expect we will always use.
        """
        owner: User | None
        try:
            owner_id = photo_elem.attrib["owner"]
            path_alias = photo_elem.attrib["pathalias"] or None

            owner = {
                "id": owner_id,
                "username": photo_elem.attrib["ownername"],
                "realname": photo_elem.attrib.get("realname"),
                "path_alias": path_alias,
                "photos_url": f"https://www.flickr.com/photos/{path_alias or owner_id}/",
                "profile_url": f"https://www.flickr.com/people/{path_alias or owner_id}/",
            }
        except KeyError:
            owner = None

        date_posted = parse_date_posted(photo_elem.attrib["dateupload"])
        date_taken = parse_date_taken(
            value=photo_elem.attrib["datetaken"],
            granularity=photo_elem.attrib["datetakengranularity"],
            unknown=photo_elem.attrib["datetakenunknown"] == "1",
        )
        license = self.lookup_license_by_id(id=photo_elem.attrib["license"])
        sizes = parse_sizes(photo_elem)

        return {
            "photo_elem": photo_elem,
            "id": photo_elem.attrib["id"],
            "owner": owner,
            "date_posted": date_posted,
            "date_taken": date_taken,
            "license": license,
            "sizes": sizes,
        }

    # We always include these extras in our API calls, because we always
    # expect to use them.
    required_extras = [
        "license",
        "date_upload",
        "date_taken",
        "owner_name",
        "owner",
        "path_alias",
        "realname",
    ]

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
        extras = params.get("extras", "").split(",")
        for e in self.required_extras:
            if e not in extras:
                extras.append(e)
        params["extras"] = ",".join(extras)

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

        elements = [
            self._to_parsed_element(elem)
            for elem in collection_elem.findall(".//photo")
        ]

        return {
            "page_count": page_count,
            "total_photos": total_photos,
            "root": resp,
            "elements": elements,
        }

    def _get_stream_of_photos(
        self, *, method: str, params: dict[str, str]
    ) -> Iterator[ParsedElement]:
        """
        Get a continuous stream of photos from the Flickr API.

        This returns an iterator of the raw XML elements, so different callers
        can apply their own processing, e.g. depending on which ``extras``
        they decided to include.
        """
        extras = params.get("extras", "").split(",")
        for e in self.required_extras:
            if e not in extras:
                extras.append(e)
        params["extras"] = ",".join(extras)

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

            for photo_elem in photos_in_page:
                yield self._to_parsed_element(photo_elem)

            if not photos_in_page:
                break

        # This branch will only be executed if the ``for`` loop exits
        # without a ``break``.  This will never happen; this is just here
        # to satisfy coverage.
        else:  # pragma: no cover
            assert False


class FlickrPhotosApi(BaseApi):
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
        self, parsed_elem: ParsedElement, *, collection_owner: User | None = None
    ) -> SinglePhoto:
        photo_elem = parsed_elem["photo_elem"]

        title = photo_elem.attrib["title"] or None
        description = find_optional_text(photo_elem, path="description")

        tags = photo_elem.attrib["tags"].split()

        owner = parsed_elem["owner"] or collection_owner
        assert owner is not None

        assert owner["photos_url"].endswith("/")
        url = owner["photos_url"] + parsed_elem["id"] + "/"

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
            "id": parsed_elem["id"],
            "title": title,
            "description": description,
            "date_posted": parsed_elem["date_posted"],
            "date_taken": parsed_elem["date_taken"],
            "license": parsed_elem["license"],
            "sizes": parsed_elem["sizes"],
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
        Get a page of photos from an album.
        """
        user_info = self.lookup_user_by_url(url=user_url)
        user = user_info_to_user(user_info)

        # https://www.flickr.com/services/api/flickr.photosets.getPhotos.html
        resp = self._get_page_of_photos(
            method="flickr.photosets.getPhotos",
            params={
                "user_id": user_info["id"],
                "photoset_id": album_id,
                "extras": ",".join(self.extras),
            },
            page=page,
            per_page=per_page,
        )

        # The wrapper element is of the form:
        #
        #   <photoset id="72157624715342071" […] title="Delhi Life">
        #
        photoset_elem = find_required_elem(resp["root"], path=".//photoset")
        album_title = photoset_elem.attrib["title"]

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
            "photos": [self._to_photo(photo_elem) for photo_elem in resp["elements"]],
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
