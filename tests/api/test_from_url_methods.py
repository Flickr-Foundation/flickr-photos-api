"""
Tests for ``flickr_photos_api.api.from_url_methods``.
"""

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
    Tests for ``FromUrlMethods.get_photos_from_flickr_url``.
    """

    def test_get_single_photo_url(self, api: FlickrApi) -> None:
        """
        Get the URL for a single photo.
        """
        actual = api.get_photos_from_flickr_url(
            url="https://www.flickr.com/photos/coast_guard/32812033543"
        )
        expected = get_fixture("32812033543.json", model=SinglePhoto)

        assert actual == expected

    @pytest.mark.parametrize("path_identifier", ["joshuatreenp", "115357548@N08"])
    def test_get_album_url(self, api: FlickrApi, path_identifier: str) -> None:
        """
        Get photos from a URL to an album.
        """
        url = (
            f"https://www.flickr.com/photos/{path_identifier}/albums/72157640898611483"
        )

        actual = api.get_photos_from_flickr_url(url)
        expected = get_fixture("album-72157640898611483.json", model=PhotosInAlbum)

        assert actual == expected

    def test_get_photos_in_album_page_2(self, api: FlickrApi) -> None:
        """
        Get photos from a URL that points to the second page of an album.
        """
        actual = api.get_photos_from_flickr_url(
            url="https://www.flickr.com/photos/joshuatreenp/albums/72157640898611483/page2"
        )
        expected = get_fixture(
            "album-72157640898611483-page2.json", model=PhotosInAlbum
        )

        assert actual == expected

    @pytest.mark.parametrize("path_identifier", ["spike_yun", "132051449@N06"])
    def test_get_photos_in_user_profile(
        self, api: FlickrApi, path_identifier: str
    ) -> None:
        """
        Get photos from a URL that points to a user's profile.
        """
        url = f"https://www.flickr.com/photos/{path_identifier}/"

        actual = api.get_photos_from_flickr_url(url)
        expected = get_fixture("user-spike_yun.json", model=CollectionOfPhotos)

        assert actual == expected

    def test_get_photos_in_gallery(self, api: FlickrApi) -> None:
        """
        Get photos from a URL that points to a gallery.
        """
        actual = api.get_photos_from_flickr_url(
            url="https://www.flickr.com/photos/meldaniel/galleries/72157716953066942/"
        )
        expected = get_fixture("gallery-72157716953066942.json", model=PhotosInGallery)

        assert actual == expected

    def test_get_photos_in_group(self, api: FlickrApi) -> None:
        """
        Get photos from a URL that points to a group.
        """
        actual = api.get_photos_from_flickr_url(
            url="https://www.flickr.com/groups/geologists/"
        )
        expected = get_fixture("group-geologists.json", model=PhotosInGroup)

        assert actual == expected

    def test_get_photos_with_tag(self, api: FlickrApi) -> None:
        """
        Get photos from a URL that points to a tag.
        """
        actual = api.get_photos_from_flickr_url(
            url="https://www.flickr.com/photos/tags/botany"
        )
        expected = get_fixture("tag-botany.json", model=CollectionOfPhotos)

        assert actual == expected


@pytest.mark.parametrize(
    "url",
    [
        pytest.param(
            "https://www.flickr.com/photos/joshuatreenp/albums/72157640898611483",
            id="album",
        ),
        pytest.param("https://www.flickr.com/photos/spike_yun", id="user"),
        pytest.param(
            "https://www.flickr.com/photos/meldaniel/galleries/72157716953066942",
            id="gallery",
        ),
        pytest.param("https://www.flickr.com/groups/geologists/pool", id="group"),
        pytest.param("https://www.flickr.com/photos/tags/botany", id="tag"),
    ],
)
def test_get_photos_from_flickr_url_is_paginated(api: FlickrApi, url: str) -> None:
    first_resp = api.get_photos_from_flickr_url(url)
    second_resp = api.get_photos_from_flickr_url(url + "/page2")

    assert first_resp["photos"] != second_resp["photos"]  # type: ignore


def test_unrecognised_url_type_is_error(api: FlickrApi) -> None:
    with pytest.raises(TypeError, match="Unrecognised URL type"):
        api.get_photos_from_parsed_flickr_url(parsed_url={"type": "unknown"})  # type: ignore
