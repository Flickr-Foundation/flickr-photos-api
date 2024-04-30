import pytest

from flickr_photos_api import FlickrApi, FlickrApi as FlickrPhotosApi


def test_lookup_user_by_url(api: FlickrPhotosApi) -> None:
    assert api.lookup_user_by_url(
        url="https://www.flickr.com/photos/199246608@N02"
    ) == {
        "id": "199246608@N02",
        "username": "cefarrjf87",
        "realname": "Alex Chan",
        "description": None,
        "has_pro_account": False,
        "path_alias": None,
        "photos_url": "https://www.flickr.com/photos/199246608@N02/",
        "profile_url": "https://www.flickr.com/people/199246608@N02/",
        "count_photos": 38,
    }


def test_lookup_user_by_url_doesnt_use_username(api: FlickrPhotosApi) -> None:
    # In this URL the last component is the _path alias_, not the
    # username, but I got that mixed up when I was new to the Flickr API.
    #
    # Make sure this library does the right thing!
    user_info = api.lookup_user_by_url(
        url="https://www.flickr.com/photos/britishlibrary/"
    )

    assert user_info["id"] == "12403504@N02"
    assert user_info["username"] == "The British Library"


def test_lookup_user_by_id(api: FlickrPhotosApi) -> None:
    assert api.lookup_user_by_id(user_id="199258389@N04") == {
        "id": "199258389@N04",
        "username": "alexwlchan",
        "realname": "Alex Chan",
        "path_alias": "alexwlchan",
        "photos_url": "https://www.flickr.com/photos/alexwlchan/",
        "profile_url": "https://www.flickr.com/people/alexwlchan/",
        "description": "Tech lead at the Flickr Foundation.",
        "has_pro_account": False,
        "count_photos": 1,
    }


@pytest.mark.parametrize(
    ["user_id", "realname"],
    [
        ("199258389@N04", "Alex Chan"),
        ("35591378@N03", None),
    ],
)
def test_lookup_user_gets_realname(
    api: FlickrPhotosApi, user_id: str, realname: str | None
) -> None:
    user_info = api.lookup_user_by_id(user_id=user_id)

    assert user_info["realname"] == realname


@pytest.mark.parametrize(
    ["user_id", "description"],
    [
        pytest.param(
            "199258389@N04",
            "Tech lead at the Flickr Foundation.",
            id="user_with_description",
        ),
        pytest.param("46143783@N04", None, id="user_without_description"),
    ],
)
def test_lookup_user_gets_description(
    api: FlickrPhotosApi, user_id: str, description: str | None
) -> None:
    user_info = api.lookup_user_by_id(user_id=user_id)

    assert user_info["description"] == description


@pytest.mark.parametrize(
    ["user_id", "has_pro_account"],
    [("199258389@N04", False), ("12403504@N02", True)],
)
def test_lookup_user_gets_has_pro_account(
    api: FlickrPhotosApi, user_id: str, has_pro_account: bool
) -> None:
    user_info = api.lookup_user_by_id(user_id=user_id)

    assert user_info["has_pro_account"] == has_pro_account


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
def test_get_buddy_icon_url(api: FlickrApi, user_id: str, expected_url: str) -> None:
    assert api.get_buddy_icon_url(user_id=user_id) == expected_url
