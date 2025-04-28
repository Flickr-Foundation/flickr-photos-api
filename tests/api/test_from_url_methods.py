"""
Tests for ``flickr_photos_api.api.from_url_methods``.
"""

from flickr_url_parser import ParseResult
import pytest

from flickr_photos_api import FlickrApi
from flickr_photos_api.types import (
    CollectionOfPhotos,
    PhotosInAlbum,
    PhotosInGallery,
    PhotosInGroup,
    SinglePhoto,
)
from utils import get_fixture


class TestGetPhotosFromFlickrUrl:
    """
    Tests for ``FromUrlMethods.get_photos_from_parsed_flickr_url``.
    """

    def test_get_single_photo_url(self, api: FlickrApi) -> None:
        """
        Get the URL for a single photo.
        """
        actual = api.get_photos_from_parsed_flickr_url(
            parsed_url={
                "type": "single_photo",
                "photo_id": "32812033543",
                "user_url": "https://www.flickr.com/photos/coast_guard/",
                "user_id": None,
            }
        )
        expected = get_fixture("32812033543.json", model=SinglePhoto)

        assert actual == expected

    def test_get_album_url_with_path_alias(self, api: FlickrApi) -> None:
        """
        Get photos from a URL to an album.
        """
        actual = api.get_photos_from_parsed_flickr_url(
            parsed_url={
                "type": "album",
                "user_url": "https://www.flickr.com/photos/joshuatreenp/",
                "album_id": "72157640898611483",
                "page": 1,
            }
        )
        expected = get_fixture("album-72157640898611483.json", model=PhotosInAlbum)

        assert actual == expected

    def test_get_album_url_with_user_id(self, api: FlickrApi) -> None:
        """
        Get photos from a URL to an album.
        """
        actual = api.get_photos_from_parsed_flickr_url(
            parsed_url={
                "type": "album",
                "user_url": "https://www.flickr.com/photos/115357548@N08/",
                "album_id": "72157640898611483",
                "page": 1,
            }
        )
        expected = get_fixture("album-72157640898611483.json", model=PhotosInAlbum)

        assert actual == expected

    def test_get_photos_in_album_page_2(self, api: FlickrApi) -> None:
        """
        Get photos from a URL that points to the second page of an album.
        """
        actual = api.get_photos_from_parsed_flickr_url(
            parsed_url={
                "type": "album",
                "user_url": "https://www.flickr.com/photos/joshuatreenp/",
                "album_id": "72157640898611483",
                "page": 2,
            }
        )
        expected = get_fixture(
            "album-72157640898611483-page2.json", model=PhotosInAlbum
        )

        assert actual == expected

    def test_get_photos_in_user_profile_with_path_alias(self, api: FlickrApi) -> None:
        """
        Get photos from a URL that points to a user's profile.
        """
        actual = api.get_photos_from_parsed_flickr_url(
            {
                "type": "user",
                "user_url": "https://www.flickr.com/photos/spike_yun/",
                "user_id": None,
                "page": 1,
            }
        )
        expected = get_fixture("user-spike_yun.json", model=CollectionOfPhotos)

        assert actual == expected

    def test_get_photos_in_user_profile_with_user_id(self, api: FlickrApi) -> None:
        """
        Get photos from a URL that points to a user's profile.
        """
        actual = api.get_photos_from_parsed_flickr_url(
            {
                "type": "user",
                "user_url": "https://www.flickr.com/photos/132051449@N06/",
                "user_id": "132051449@N06",
                "page": 1,
            }
        )
        expected = get_fixture("user-spike_yun.json", model=CollectionOfPhotos)

        assert actual == expected

    def test_get_photos_in_gallery(self, api: FlickrApi) -> None:
        """
        Get photos from a URL that points to a gallery.
        """
        actual = api.get_photos_from_parsed_flickr_url(
            parsed_url={"type": "gallery", "gallery_id": "72157716953066942", "page": 1}
        )
        expected = get_fixture("gallery-72157716953066942.json", model=PhotosInGallery)

        assert actual == expected

    def test_get_photos_in_group(self, api: FlickrApi) -> None:
        """
        Get photos from a URL that points to a group.
        """
        actual = api.get_photos_from_parsed_flickr_url(
            {
                "type": "group",
                "group_url": "https://www.flickr.com/groups/geologists",
                "page": 1,
            }
        )
        expected = get_fixture("group-geologists.json", model=PhotosInGroup)

        assert actual == expected

    def test_get_photos_with_tag(self, api: FlickrApi) -> None:
        """
        Get photos from a URL that points to a tag.
        """
        actual = api.get_photos_from_parsed_flickr_url(
            parsed_url={"type": "tag", "tag": "botany", "page": 1}
        )
        expected = get_fixture("tag-botany.json", model=CollectionOfPhotos)

        assert actual == expected


@pytest.mark.parametrize(
    "parsed_url",
    [
        pytest.param(
            {
                "type": "album",
                "user_url": "https://www.flickr.com/photos/joshuatreenp/",
                "album_id": "72157640898611483",
                "page": 1,
            },
            id="album",
        ),
        pytest.param(
            {
                "type": "user",
                "user_url": "https://www.flickr.com/photos/spike_yun/",
                "user_id": None,
                "page": 1,
            },
            id="user",
        ),
        pytest.param(
            {"type": "gallery", "gallery_id": "72157716953066942", "page": 1},
            id="gallery",
        ),
        pytest.param(
            {
                "type": "group",
                "group_url": "https://www.flickr.com/groups/geologists",
                "page": 1,
            },
            id="group",
        ),
        pytest.param({"type": "tag", "tag": "botany", "page": 1}, id="tag"),
    ],
)
def test_get_photos_from_flickr_url_is_paginated(
    api: FlickrApi, parsed_url: ParseResult
) -> None:
    """
    If you look up photos from a paginated URL, you get photos from
    that specific page.
    """
    first_resp = api.get_photos_from_parsed_flickr_url(parsed_url)

    parsed_url["page"] = 2  # type: ignore
    second_resp = api.get_photos_from_parsed_flickr_url(parsed_url)

    assert first_resp["photos"] != second_resp["photos"]  # type: ignore


def test_unrecognised_url_type_is_error(api: FlickrApi) -> None:
    """
    If you try to look up an unrecognised type of URL, it fails
    with a ``TypeError``.
    """
    with pytest.raises(TypeError, match="Unrecognised URL type"):
        api.get_photos_from_parsed_flickr_url(parsed_url={"type": "unknown"})  # type: ignore
