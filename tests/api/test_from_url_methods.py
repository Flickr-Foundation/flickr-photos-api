"""
Tests for ``flickr_photos_api.api.from_url_methods``.
"""

import typing

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


T = typing.TypeVar("T")


@pytest.mark.parametrize(
    ["url", "filename", "model"],
    [
        pytest.param(
            "https://www.flickr.com/photos/coast_guard/32812033543",
            "32812033543.json",
            SinglePhoto,
            id="single_photo",
        ),
        pytest.param(
            "https://www.flickr.com/photos/joshuatreenp/albums/72157640898611483",
            "album-72157640898611483.json",
            PhotosInAlbum,
            id="album",
        ),
        pytest.param(
            "https://www.flickr.com/photos/115357548@N08/albums/72157640898611483",
            "album-72157640898611483.json",
            PhotosInAlbum,
            id="album_with_user_id",
        ),
        pytest.param(
            "https://www.flickr.com/photos/joshuatreenp/albums/72157640898611483/page2",
            "album-72157640898611483-page2.json",
            PhotosInAlbum,
            id="album-page2",
        ),
        pytest.param(
            "https://www.flickr.com/photos/spike_yun/",
            "user-spike_yun.json",
            CollectionOfPhotos,
            id="user",
        ),
        pytest.param(
            "https://www.flickr.com/photos/132051449@N06/",
            "user-spike_yun.json",
            CollectionOfPhotos,
            id="user_with_id",
        ),
        pytest.param(
            "https://www.flickr.com/photos/meldaniel/galleries/72157716953066942/",
            "gallery-72157716953066942.json",
            PhotosInGallery,
            id="gallery",
        ),
        pytest.param(
            "https://www.flickr.com/groups/geologists/",
            "group-geologists.json",
            PhotosInGroup,
            id="group",
        ),
        pytest.param(
            "https://www.flickr.com/photos/tags/botany",
            "tag-botany.json",
            CollectionOfPhotos,
            id="tag",
        ),
    ],
)
def test_get_photos_from_flickr_url(
    api: FlickrApi, url: str, filename: str, model: type[T]
) -> None:
    """
    Get one or more photos from a Flickr.com URL.
    """
    photos = api.get_photos_from_flickr_url(url)

    assert photos == get_fixture(filename, model=model)


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
    """
    If you get page 1 and page 2 of a paginated collection, you get
    a diffeent set of photos.
    """
    first_resp = api.get_photos_from_flickr_url(url)
    second_resp = api.get_photos_from_flickr_url(url + "/page2")

    assert first_resp["photos"] != second_resp["photos"]  # type: ignore


def test_unrecognised_url_type_is_error(api: FlickrApi) -> None:
    """
    If you try to get photos from a URL which isn't a string, it
    throws a ``TypeError``.
    """
    with pytest.raises(TypeError, match="Unrecognised URL type"):
        api.get_photos_from_parsed_flickr_url(parsed_url={"type": "unknown"})  # type: ignore
