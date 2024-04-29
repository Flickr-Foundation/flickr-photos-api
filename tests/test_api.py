import typing

import pytest

from flickr_photos_api import (
    CollectionOfPhotos,
    FlickrPhotosApi,
    PhotosInAlbum,
    PhotosInGallery,
    PhotosInGroup,
    SinglePhoto,
)
from utils import get_fixture


def test_get_photos_with_tag(api: FlickrPhotosApi) -> None:
    photos = api.get_photos_with_tag(tag="sunset")

    assert photos == get_fixture("tag-sunset.json", model=CollectionOfPhotos)


@pytest.mark.parametrize(
    ["method", "kwargs"],
    [
        pytest.param(
            "get_photos_in_album",
            {
                "user_url": "https://www.flickr.com/photos/spike_yun/",
                "album_id": "72157677773252346",
            },
            id="get_photos_in_album",
        ),
        pytest.param(
            "get_photos_in_gallery",
            {"gallery_id": "72157720932863274"},
            id="get_photos_in_gallery",
        ),
        pytest.param(
            "get_public_photos_by_user",
            {"user_url": "https://www.flickr.com/photos/george/"},
            id="get_public_photos_by_user",
        ),
        pytest.param(
            "get_photos_in_group_pool",
            {"group_url": "https://www.flickr.com/groups/slovenia/pool/"},
            id="get_photos_in_group_pool",
        ),
    ],
)
def test_get_collection_methods_are_paginated(
    api: FlickrPhotosApi, method: str, kwargs: dict[str, str]
) -> None:
    api_method = getattr(api, method)

    all_resp = api_method(**kwargs, page=1)

    # Getting the 5th page with a page size of 1 means getting the 5th image
    individual_resp = api_method(
        **kwargs,
        page=5,
        per_page=1,
    )

    assert individual_resp["photos"][0] == all_resp["photos"][4]


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
    api: FlickrPhotosApi, url: str, filename: str, model: type[T]
) -> None:
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
def test_get_photos_from_flickr_url_is_paginated(
    api: FlickrPhotosApi, url: str
) -> None:
    first_resp = api.get_photos_from_flickr_url(url)
    second_resp = api.get_photos_from_flickr_url(url + "/page2")

    assert first_resp["photos"] != second_resp["photos"]  # type: ignore


def test_unrecognised_url_type_is_error(api: FlickrPhotosApi) -> None:
    with pytest.raises(TypeError, match="Unrecognised URL type"):
        api.get_photos_from_parsed_flickr_url(parsed_url={"type": "unknown"})  # type: ignore


@pytest.mark.parametrize(
    ["user_id", "expected_url"],
    [
        pytest.param(
            "199246608@N02",
            "https://www.flickr.com/images/buddyicon.gif",
            id="user_with_no_buddyicon",
        ),
        pytest.param(
            "28660070@N07",
            "https://farm6.staticflickr.com/5556/buddyicons/28660070@N07.jpg",
            id="user_with_buddyicon",
        ),
    ],
)
def test_get_buddy_icon_url(
    api: FlickrPhotosApi, user_id: str, expected_url: str
) -> None:
    assert api.get_buddy_icon_url(user_id=user_id) == expected_url


# These all the outliers in terms of number of comments.
#
# The expected value comes from the "count_comments" field on the
# photos API response.  This API seems to return everything at once,
# and doesn't do pagination, but let's make sure it actually does.
@pytest.mark.parametrize(
    ["photo_id", "count"],
    [
        ("12584715825", 154),
        ("3334095096", 376),
        ("2780177093", 501),
        ("2960116125", 1329),
    ],
)
def test_finds_all_comments(api: FlickrPhotosApi, photo_id: str, count: int) -> None:
    comments = api.list_all_comments(photo_id=photo_id)

    assert len(comments) == count


def test_if_no_realname_then_empty(api: FlickrPhotosApi) -> None:
    # The first comment is one where the ``author_realname`` attribute
    # is an empty string, which we should map to ``None``.
    comments = api.list_all_comments(photo_id="53654427282")

    assert comments[0]["author"]["realname"] is None


@pytest.mark.parametrize(
    "params",
    [
        {"user_id": "39758725@N03", "extras": ""},
        {"user_id": "39758725@N03", "extras": "geo"},
        {"user_id": "39758725@N03", "extras": "geo,title,license,"},
    ],
)
def test_gets_stream_of_photos(api: FlickrPhotosApi, params: dict[str, str]) -> None:
    iterator = api._get_stream_of_photos(
        method="flickr.people.getPublicPhotos", params=params
    )

    assert sum(1 for _ in iterator) == 870
