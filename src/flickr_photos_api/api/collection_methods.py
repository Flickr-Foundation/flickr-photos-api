"""
Methods for getting information about collections of photos in Flickr
(albums, galleries, groups, and so on).
"""

from xml.etree import ElementTree as ET

from nitrate.xml import find_optional_text, find_required_elem, find_required_text

from .license_methods import LicenseMethods
from ..types import (
    CollectionOfPhotos2,
    PhotosInAlbum2,
    PhotosInGallery2,
    SinglePhotoInfoWithSizes,
    User,
)
from ..utils import (
    parse_date_posted,
    parse_date_taken,
    parse_location,
    parse_safety_level,
    parse_sizes,
)


class CollectionMethods(LicenseMethods):
    def _from_collection_photo(
        self, photo_elem: ET.Element, owner: User | None
    ) -> SinglePhotoInfoWithSizes:
        """
        Given a <photo> element from a collection response, extract all the photo info.
        """
        photo_id = photo_elem.attrib["id"]

        secret = photo_elem.attrib["secret"]
        server = photo_elem.attrib["server"]
        farm = photo_elem.attrib["farm"]

        original_format = photo_elem.attrib.get("originalformat")

        if owner is None:
            owner_id = photo_elem.attrib["owner"]
            path_alias = photo_elem.attrib["pathalias"]

            owner = {
                "id": owner_id,
                "username": photo_elem.attrib["ownername"],
                "realname": photo_elem.attrib.get("realname"),
                "path_alias": path_alias,
                "photos_url": f"https://www.flickr.com/photos/{path_alias or owner_id}/",
                "profile_url": f"https://www.flickr.com/people/{path_alias or owner_id}/",
            }

        assert owner is not None

        safety_level = parse_safety_level(photo_elem.attrib["safety_level"])

        license = self.lookup_license_by_id(id=photo_elem.attrib["license"])

        title = photo_elem.attrib["title"] or None
        description = find_optional_text(photo_elem, path="description")
        tags = photo_elem.attrib["tags"].split()

        date_posted = parse_date_posted(photo_elem.attrib["dateupload"])
        date_taken = parse_date_taken(
            value=photo_elem.attrib["datetaken"],
            granularity=photo_elem.attrib["datetakengranularity"],
            unknown=photo_elem.attrib["datetakenunknown"] == "1",
        )

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

        count_comments = int(photo_elem.attrib["count_comments"])
        count_views = int(photo_elem.attrib["count_views"])

        assert owner["photos_url"].endswith("/")
        photo_page_url = owner["photos_url"] + photo_id + "/"

        sizes = parse_sizes(photo_elem)

        return {
            "id": photo_id,
            "secret": secret,
            "server": server,
            "farm": farm,
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
            "sizes": sizes,
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
        "path_alias",
        "count_comments",
        "count_views",
    ]

    def _create_collection(
        self, collection_elem: ET.Element, owner: User | None = None
    ) -> CollectionOfPhotos2:
        photos = [
            self._from_collection_photo(photo_elem, owner=owner)
            for photo_elem in collection_elem.findall("photo")
        ]

        # The wrapper element includes a couple of attributes related
        # to pagination, e.g.
        #
        #     <photoset pages="1" total="2" …>
        #
        count_pages = int(collection_elem.attrib["pages"])
        count_photos = int(collection_elem.attrib["total"])

        return {
            "photos": photos,
            "count_pages": count_pages,
            "count_photos": count_photos,
        }

    def get_photos_in_album(
        self, *, user_id: str, album_id: str, page: int = 1, per_page: int = 10
    ) -> PhotosInAlbum2:
        """
        Get a page of photos from an album.
        """
        # https://www.flickr.com/services/api/flickr.photosets.getPhotos.html
        resp = self.call(
            method="flickr.photosets.getPhotos",
            params={
                "user_id": user_id,
                "photoset_id": album_id,
                "extras": ",".join(self.extras),
                "page": str(page),
                "per_page": str(per_page),
            },
        )

        photoset_elem = find_required_elem(resp, path="photoset")
        owner_id = photoset_elem.attrib["owner"]
        owner_username = photoset_elem.attrib["ownername"]

        # Albums are always non-empty, so we know we'll find something here
        photo_elem = find_required_elem(photoset_elem, path="photo")
        realname = photo_elem.attrib.get("realname")
        path_alias = photo_elem.attrib.get("pathalias")

        owner: User = {
            "id": owner_id,
            "username": owner_username,
            "realname": realname,
            "path_alias": path_alias,
            "photos_url": f"https://www.flickr.com/photos/{path_alias or owner_id}/",
            "profile_url": f"https://www.flickr.com/people/{path_alias or owner_id}/",
        }

        album_title = photoset_elem.attrib["title"]

        return {
            **self._create_collection(photoset_elem, owner=owner),
            "album": {
                "owner": owner,
                "title": album_title,
            },
        }

    def get_photos_in_gallery(
        self, *, gallery_id: str, page: int = 1, per_page: int = 10
    ) -> PhotosInGallery2:
        """
        Get the photos in a gallery.
        """
        # https://www.flickr.com/services/api/flickr.galleries.getPhotos.html
        resp = self.call(
            method="flickr.galleries.getPhotos",
            params={
                "gallery_id": gallery_id,
                "get_gallery_info": "1",
                "extras": ",".join(self.extras),
                "page": str(page),
                "per_page": str(per_page),
            },
        )

        gallery_elem = find_required_elem(resp, path="gallery")

        gallery_title = find_required_text(gallery_elem, path="title")
        gallery_owner_name = gallery_elem.attrib["username"]

        photos_elem = find_required_elem(resp, path="photos")

        return {
            **self._create_collection(photos_elem),
            "gallery": {"owner_name": gallery_owner_name, "title": gallery_title},
        }

    def get_photos_in_user_photostream(
        self, *, user_id: str, page: int = 1, per_page: int = 10
    ) -> CollectionOfPhotos2:
        """
        Get all the public photos by a user on Flickr.
        """
        resp = self.call(
            method="flickr.people.getPublicPhotos",
            params={
                "user_id": user_id,
                "extras": ",".join(self.extras),
                "page": str(page),
                "per_page": str(page),
            },
        )

        first_photo = resp.find(".//photo")

        # The user hasn't uploaded any photos
        if first_photo is None:
            return {
                'count_pages': 1,
                'count_photos': 0,
                'photos': []
            }

        owner_id = first_photo.attrib["owner"]
        owner_username = first_photo.attrib["ownername"]

        realname = first_photo.attrib.get("realname")
        path_alias = first_photo.attrib.get("pathalias")

        owner: User = {
            "id": owner_id,
            "username": owner_username,
            "realname": realname,
            "path_alias": path_alias,
            "photos_url": f"https://www.flickr.com/photos/{path_alias or owner_id}/",
            "profile_url": f"https://www.flickr.com/people/{path_alias or owner_id}/",
        }

        return self._create_collection(resp.find("photos"), owner=owner)