"""
Get photos from a URL that points to Flickr.com.
"""

from flickr_url_parser import ParseResult

from .collection_methods import CollectionMethods
from .single_photo_methods import SinglePhotoMethods
from .user_methods import UserMethods
from ..types import PhotosFromUrl


class FromUrlMethods(CollectionMethods, SinglePhotoMethods, UserMethods):
    """
    A couple of methods for getting data from a Flickr.com URL.

    This allows us to build interfaces where people can select photos
    by giving us a URL they found in their web browser, and we work
    out what it points to.
    """

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
            return self.get_photos_in_user_photostream(
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
