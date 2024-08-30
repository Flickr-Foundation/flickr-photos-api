import datetime
import typing
from xml.etree import ElementTree as ET

import pytest

from data import FlickrUserIds
from flickr_photos_api import (
    FlickrApi,
    UnrecognisedFlickrApiException,
    UserDeleted,
)
from flickr_photos_api.api.user_methods import UserMethods


class TestGetUser:
    def test_get_user_by_id(self, api: FlickrApi) -> None:
        """
        Look up a user with their Flickr NSID.
        """
        user = api.get_user(user_id="199258389@N04")

        assert user == {
            "id": "199258389@N04",
            "username": "alexwlchan",
            "realname": "Alex Chan",
            "location": None,
            "path_alias": "alexwlchan",
            "photos_url": "https://www.flickr.com/photos/alexwlchan/",
            "profile_url": "https://www.flickr.com/people/alexwlchan/",
            "buddy_icon_url": "https://farm66.staticflickr.com/65535/buddyicons/199258389@N04.jpg",
            "description": "Tech lead at the Flickr Foundation.",
            "has_pro_account": False,
            "count_photos": 1,
        }

    def test_get_user_by_url(self, api: FlickrApi) -> None:
        """
        Look up a user with a URL to their profile on Flickr.com.
        """
        user = api.get_user(user_url="https://www.flickr.com/photos/199246608@N02")

        assert user == {
            "id": "199246608@N02",
            "username": "cefarrjf87",
            "realname": "Alex Chan",
            "description": None,
            "location": None,
            "has_pro_account": False,
            "path_alias": None,
            "photos_url": "https://www.flickr.com/photos/199246608@N02/",
            "profile_url": "https://www.flickr.com/people/199246608@N02/",
            "buddy_icon_url": "https://www.flickr.com/images/buddyicon.gif",
            "count_photos": 38,
        }

    def test_uses_url_not_username(self, api: FlickrApi) -> None:
        # In this URL the last component is the _path alias_, not the
        # username, but I got that mixed up when I was new to the Flickr API.
        #
        # Make sure this library does the right thing!
        user_info = api.get_user(
            user_url="https://www.flickr.com/photos/britishlibrary/"
        )

        assert user_info["id"] == "12403504@N02"
        assert user_info["username"] == "The British Library"

    @pytest.mark.parametrize(
        ["user_id", "realname"],
        [
            ("199258389@N04", "Alex Chan"),
            ("35591378@N03", None),
        ],
    )
    def test_gets_realname(
        self, api: FlickrApi, user_id: str, realname: str | None
    ) -> None:
        user = api.get_user(user_id=user_id)

        assert user["realname"] == realname

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
    def test_gets_description(
        self, api: FlickrApi, user_id: str, description: str | None
    ) -> None:
        user = api.get_user(user_id=user_id)

        assert user["description"] == description

    def test_knows_about_flickr_pro(self, api: FlickrApi) -> None:
        """
        If an account has Flickr Pro, then we set two attributes:

        *   ``has_pro_account=True``
        *   ``pro_account_expires``

        """
        user = api.get_user(user_id=FlickrUserIds.FlickrFoundation)

        assert user["has_pro_account"]
        assert user["pro_account_expires"] == datetime.datetime(
            2033, 7, 19, 4, 0, tzinfo=datetime.timezone.utc
        )

    def test_knows_about_non_flickr_pro(self, api: FlickrApi) -> None:
        """
        If an account doesn't have Flickr Pro, then we set one attribute:

        *   ``has_pro_account=False``

        We shouldn't set an expiry date, because it doesn't apply here.
        """
        user = api.get_user(user_id=FlickrUserIds.Alexwlchan)

        assert not user["has_pro_account"]
        assert "pro_account_expires" not in user

    def test_get_deleted_user_id(self, api: FlickrApi) -> None:
        with pytest.raises(UserDeleted):
            api.get_user(user_id="51979177@N02")

    def test_get_deleted_user_url(self, api: FlickrApi) -> None:
        with pytest.raises(UserDeleted):
            api.get_user(user_url="https://www.flickr.com/photos/51979177@N02/")

    def test_get_user_with_unexpected_error(self) -> None:
        class BrokenApi(UserMethods):
            def call(
                self,
                *,
                http_method: typing.Any = None,
                method: str,
                params: dict[str, str] | None = None,
                exceptions: dict[str, Exception] | None = None,
            ) -> ET.Element:
                raise UnrecognisedFlickrApiException(
                    {"code": "6", "msg": "Mysterious error"}
                )

        api = BrokenApi()

        with pytest.raises(UnrecognisedFlickrApiException):
            api.get_user(user_id="-1")

    @pytest.mark.parametrize(
        ["user_id", "realname"],
        [
            ("62173425@N02", "Stockholm Transport Museum"),
            ("32162360@N00", "beachcomber australia"),
        ],
    )
    def test_fixes_realname(self, api: FlickrApi, user_id: str, realname: str) -> None:
        user = api.get_user(user_id=user_id)
        assert user["realname"] == realname

    def test_gets_no_location_if_not_set(self, api: FlickrApi) -> None:
        """
        If the user doesn't have a location set, their location is ``None``.
        """
        # The Flickr Foundation account doesn't set a city/location;
        # the XML response includes an empty ``<location/>`` element.
        #
        # In the account settings, location info is *not* private, it's
        # just not set (https://www.flickr.com/account/privacy):
        #
        #     Who can see what on your profile
        #     Current city: Public (n/a)
        #
        # (Retrieved 30 August 2024)
        user = api.get_user(user_id=FlickrUserIds.FlickrFoundation)

        assert user["location"] is None

    def test_gets_no_location_if_private(self, api: FlickrApi) -> None:
        """
        If the user's location isn't private, their location is ``None``.
        """
        # The Colección Amadeo León account seems to have their location
        # private -- when you call the ``flickr.people.getInfo`` API,
        # there's no ``<location>`` element at all.
        #
        # (Retrieved 30 August 2024)
        user = api.get_user(user_id="134319968@N02")

        assert user["location"] is None

    def test_gets_user_location_if_set(self, api: FlickrApi) -> None:
        """
        If a user has a public location, it's returned in this response.
        """
        # This is a user who was recommended to me while browsing Flickr.
        # If you look at their profile, it says:
        #
        #     Current city    Kyoto
        #     Country         Japan
        #
        # (Retrieved 30 August 2024)
        user = api.get_user(user_id="47062778@N06")

        assert user["location"] == "Kyoto, Japan"


class TestEnsureUserId:
    def test_passing_neither_of_user_id_or_url_is_error(self, api: FlickrApi) -> None:
        with pytest.raises(
            TypeError, match="You must pass one of `user_id` or `user_url`!"
        ):
            api.get_user()

    def test_passing_both_of_user_id_or_url_is_error(self, api: FlickrApi) -> None:
        with pytest.raises(
            TypeError, match="You can only pass one of `user_id` and `user_url`!"
        ):
            api.get_user(user_id="123", user_url="https://www.flickr.com/photos/123")

    def test_passing_a_non_user_url_is_error(self, api: FlickrApi) -> None:
        with pytest.raises(
            ValueError, match="user_url was not the URL for a Flickr user"
        ):
            api.get_user(user_url="https://www.flickr.com")

    def test_passing_a_non_flickr_url_is_error(self, api: FlickrApi) -> None:
        with pytest.raises(
            ValueError, match="user_url was not the URL for a Flickr user"
        ):
            api.get_user(user_url="https://www.example.com")


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
    assert api.get_user(user_id=user_id)["buddy_icon_url"] == expected_url
