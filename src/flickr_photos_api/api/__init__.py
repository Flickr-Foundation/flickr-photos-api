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
from .collection_methods import CollectionMethods
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
    PhotosInGallery,
    PhotosInGroup,
    SinglePhoto,
    User,
)
from ..utils import (
    parse_date_posted,
    parse_date_taken,
    parse_location,
    parse_safety_level,
    parse_sizes,
)


class FlickrApiMethods(
    CommentMethods, CollectionMethods, SinglePhotoMethods, LicenseMethods, UserMethods
):
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
