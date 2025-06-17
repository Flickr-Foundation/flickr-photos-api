"""
Tests for ``flickr_api.api.user_methods``.
"""

from collections.abc import Mapping
from datetime import datetime, timezone
import typing
from xml.etree import ElementTree as ET

import pytest

from data import FlickrUserIds
from flickr_api import (
    FlickrApi,
    ResourceNotFound,
    UnrecognisedFlickrApiException,
    UserDeleted,
)
from flickr_api.api.user_methods import UserMethods


class TestGetUser:
    """
    Tests for ``UserMethods.get_user``.
    """

    def test_get_user_by_id(self, flickr_api: FlickrApi) -> None:
        """
        Look up a user with their Flickr NSID.
        """
        user = flickr_api.get_user(user_id="199258389@N04")

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

    def test_get_user_by_url(self, flickr_api: FlickrApi) -> None:
        """
        Look up a user with a URL to their profile on Flickr.com.
        """
        user = flickr_api.get_user(
            user_url="https://www.flickr.com/photos/199246608@N02"
        )

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

    def test_uses_url_not_username(self, flickr_api: FlickrApi) -> None:
        """
        When you look up a user by URL, it treats the URL component
        as their path alias, not their username.

        This is a regression test from a bug based on my misunderstanding
        of Flickr usernames/path aliases: here ``britishlibrary`` is the
        path alias, not the username.

        *   path alias = `britishlibrary` points to `12403504@N02`, the
            official account used by the British Library

        *   username = `britishlibrary` points to `156987034@N08`, an empty
            account with no photos and no activity

        Make sure we pickm the right one!
        """
        user_info = flickr_api.get_user(
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
        self, flickr_api: FlickrApi, user_id: str, realname: str | None
    ) -> None:
        """
        Looking up a user gets their real name, if set.
        """
        user = flickr_api.get_user(user_id=user_id)

        assert user["realname"] == realname

    @pytest.mark.parametrize(
        ["user_id", "realname"],
        [
            ("62173425@N02", "Stockholm Transport Museum"),
            ("32162360@N00", "beachcomber australia"),
        ],
    )
    def test_fixes_realname(
        self, flickr_api: FlickrApi, user_id: str, realname: str
    ) -> None:
        """
        We apply our real name "fixes" for users of particular interest.
        """
        user = flickr_api.get_user(user_id=user_id)
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
        self, flickr_api: FlickrApi, user_id: str, description: str | None
    ) -> None:
        """
        Looking up a user gets their profile description, if set.
        """
        user = flickr_api.get_user(user_id=user_id)

        assert user["description"] == description

    def test_knows_about_flickr_pro(self, flickr_api: FlickrApi) -> None:
        """
        If an account has Flickr Pro, then we set two attributes:

        *   ``has_pro_account=True``
        *   ``pro_account_expires``

        """
        user = flickr_api.get_user(user_id=FlickrUserIds.FlickrFoundation)

        assert user["has_pro_account"]
        assert user["pro_account_expires"] == datetime(
            2033, 7, 19, 4, 0, tzinfo=timezone.utc
        )

    def test_knows_about_non_flickr_pro(self, flickr_api: FlickrApi) -> None:
        """
        If an account doesn't have Flickr Pro, then we set one attribute:

        *   ``has_pro_account=False``

        We shouldn't set an expiry date, because it doesn't apply here.
        """
        user = flickr_api.get_user(user_id=FlickrUserIds.Alexwlchan)

        assert not user["has_pro_account"]
        assert "pro_account_expires" not in user

    def test_get_deleted_user_id(self, flickr_api: FlickrApi) -> None:
        """
        Looking up a deleted user by ID throws a ``UserDeleted`` error.
        """
        with pytest.raises(UserDeleted):
            flickr_api.get_user(user_id=FlickrUserIds.Deleted)

    def test_get_deleted_user_url(self, flickr_api: FlickrApi) -> None:
        """
        Looking up a deleted user by profile URL throws a ``UserDeleted`` error.
        """
        with pytest.raises(UserDeleted):
            flickr_api.get_user(
                user_url=f"https://www.flickr.com/photos/{FlickrUserIds.Deleted}/"
            )

    def test_get_user_with_unexpected_error(self) -> None:
        """
        If calling the Flickr API throws an unexpected error, then
        ``get_user`` throws an ``UnrecognisedFlickrApiException``.
        """

        class BrokenApi(UserMethods):
            """
            A broken API that returns weird errors.
            """

            def call(
                self,
                *,
                http_method: typing.Any = None,
                method: str,
                params: Mapping[str, str | int] | None = None,
                exceptions: dict[str, Exception] | None = None,
            ) -> ET.Element:
                """
                Rather than calling the HTTP method, just throw an error.
                """
                raise UnrecognisedFlickrApiException(
                    {"code": "6", "msg": "Mysterious error"}
                )

        api = BrokenApi()

        with pytest.raises(UnrecognisedFlickrApiException):
            api.get_user(user_id="-1")

    def test_gets_no_location_if_not_set(self, flickr_api: FlickrApi) -> None:
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
        user = flickr_api.get_user(user_id=FlickrUserIds.FlickrFoundation)

        assert user["location"] is None

    def test_gets_no_location_if_private(self, flickr_api: FlickrApi) -> None:
        """
        If the user's location isn't private, their location is ``None``.
        """
        # The Colección Amadeo León account seems to have their location
        # private -- when you call the ``flickr.people.getInfo`` API,
        # there's no ``<location>`` element at all.
        #
        # (Retrieved 30 August 2024)
        user = flickr_api.get_user(user_id="134319968@N02")

        assert user["location"] is None

    def test_gets_user_location_if_set(self, flickr_api: FlickrApi) -> None:
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
        user = flickr_api.get_user(user_id="47062778@N06")

        assert user["location"] == "Kyoto, Japan"

    def test_get_buddy_icon_url(self, flickr_api: FlickrApi) -> None:
        """
        Get the user's custom buddy icon, if set.
        """
        user = flickr_api.get_user(user_id="28660070@N07")

        assert (
            user["buddy_icon_url"]
            == "https://farm6.staticflickr.com/5556/buddyicons/28660070@N07.jpg"
        )

    def test_get_default_buddy_icon_url(self, flickr_api: FlickrApi) -> None:
        """
        If a user hasn't set a buddy icon, we get the default URL.
        """
        user = flickr_api.get_user(user_id="199246608@N02")

        assert user["buddy_icon_url"] == "https://www.flickr.com/images/buddyicon.gif"


class TestEnsureUserId:
    """
    Tests that you can call ``get_user()`` with a ``user_id`` or
    ``user_url``, but not both.
    """

    def test_passing_neither_of_user_id_or_url_is_error(
        self, flickr_api: FlickrApi
    ) -> None:
        """
        If you don't pass ``user_id`` or ``user_url``, it throws
        a ``TypeError``.
        """
        with pytest.raises(
            TypeError, match="You must pass one of `user_id` or `user_url`!"
        ):
            flickr_api.get_user()

    def test_passing_both_of_user_id_or_url_is_error(
        self, flickr_api: FlickrApi
    ) -> None:
        """
        If you pass both ``user_id`` and ``user_url``, it throws
        a ``TypeError``.
        """
        with pytest.raises(
            TypeError, match="You can only pass one of `user_id` and `user_url`!"
        ):
            flickr_api.get_user(
                user_id="123", user_url="https://www.flickr.com/photos/123"
            )

    def test_passing_a_non_user_url_is_error(self, flickr_api: FlickrApi) -> None:
        """
        If you pass a ``user_url`` which is a Flickr URL but not a user
        profile, it throws a ``ValueError``.
        """
        with pytest.raises(
            ValueError,
            match="user_url was not the URL for a Flickr user: 'https://www.flickr.com'",
        ):
            flickr_api.get_user(user_url="https://www.flickr.com")

    def test_passing_a_non_flickr_url_is_error(self, flickr_api: FlickrApi) -> None:
        """
        If you pass a ``user_url`` which isn't a Flickr URL, it throws
        a ``ValueError``.
        """
        with pytest.raises(
            ValueError,
            match="user_url was not the URL for a Flickr user: 'https://www.example.com'",
        ):
            flickr_api.get_user(user_url="https://www.example.com")


class TestGetProfile:
    """
    Tests for `UserMethods.get_profile()`.
    """

    def test_get_public_profile_info(self, flickr_api: FlickrApi) -> None:
        """
        Get the profile information about a public user.
        """
        profile = flickr_api.get_profile(user_id="66956608@N06")

        assert profile == {
            "id": "66956608@N06",
            "join_date": datetime(2004, 2, 10, 20, 0, 0, tzinfo=timezone.utc),
            "occupation": None,
            "hometown": "San Francisco",
            "showcase_album_id": "72157677399602224",
            "showcase_album_title": "Profile Showcase",
            "first_name": "Flickr",
            "last_name": None,
            "email": None,
            "profile_description": 'Welcome to the official Flickr account on Flickr.   Follow us to learn about new exciting things happening in Flickr\'s community, the product, and the team here, and also find us on social media - we are on Facebook, Twitter, Instagram and anywhere else! (See links below).  For any site and customer service-related issues, go here: <a href="https://help.flickr.com/" rel="noreferrer nofollow">help.flickr.com/</a>  Make sure to check out the <a href="https://blog.flickr.net/en" rel="noreferrer nofollow">Flickr Blog</a> where you can find features on some of our favorite photographers, events, product updates and more!  If you\'d like your work featured by Flickr feel free to join our official groups:  <a href="https://www.flickr.com/groups/flickrsocialmedia/">www.flickr.com/groups/flickrsocialmedia/</a> <a href="https://www.flickr.com/groups/flickr10photowalks/">www.flickr.com/groups/flickr10photowalks/</a>',
            "city": None,
            "country": None,
            "facebook": "flickr",
            "twitter": "Flickr",
            "tumblr": "flickr",
            "instagram": "flickr",
            "pinterest": "flickr",
        }

    def test_get_private_profile_info(self, flickr_oauth_api: FlickrApi) -> None:
        """
        If you're logged in as a user, you can see their email address.
        """
        profile = flickr_oauth_api.get_profile(user_id="197130754@N07")

        assert profile["email"] == "hello@flickr.org"

    def test_get_nonexistent_user_is_error(self, flickr_oauth_api: FlickrApi) -> None:
        """
        Looking up the profile information of a user who doesn't exist
        is an error.
        """
        with pytest.raises(ResourceNotFound):
            flickr_oauth_api.get_profile(user_id="does_not_exist")
