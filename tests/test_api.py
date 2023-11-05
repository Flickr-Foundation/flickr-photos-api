import datetime
from typing import Dict

import pytest

from flickr_photos_api import FlickrPhotosApi
from flickr_photos_api.exceptions import (
    FlickrApiException,
    LicenseNotFound,
    ResourceNotFound,
)
from flickr_photos_api._types import User
from utils import get_fixture, jsonify


@pytest.mark.parametrize(
    ["method", "params"],
    [
        pytest.param(
            "lookup_user_by_url",
            {"url": "https://www.flickr.com/photos/DefinitelyDoesNotExist"},
            id="lookup_user_by_url",
        ),
        pytest.param(
            "get_single_photo",
            {"photo_id": "12345678901234567890"},
            id="get_single_photo",
        ),
    ],
)
def test_methods_fail_if_not_found(
    api: FlickrPhotosApi, method: str, params: Dict[str, str]
) -> None:
    with pytest.raises(ResourceNotFound):
        getattr(api, method)(**params)


def test_it_throws_if_bad_auth(vcr_cassette: str, user_agent: str) -> None:
    api = FlickrPhotosApi(api_key="doesnotexist", user_agent=user_agent)

    with pytest.raises(FlickrApiException):
        api.lookup_user_by_url(url="https://www.flickr.com/photos/flickr/")


class TestLicenses:
    def test_get_licenses(self, api: FlickrPhotosApi) -> None:
        assert api.get_licenses() == {
            "0": {"id": "in-copyright", "label": "All Rights Reserved", "url": None},
            "1": {
                "id": "cc-by-nc-sa-2.0",
                "label": "CC BY-NC-SA 2.0",
                "url": "https://creativecommons.org/licenses/by-nc-sa/2.0/",
            },
            "2": {
                "id": "cc-by-nc-2.0",
                "label": "CC BY-NC 2.0",
                "url": "https://creativecommons.org/licenses/by-nc/2.0/",
            },
            "3": {
                "id": "cc-by-nc-nd-2.0",
                "label": "CC BY-NC-ND 2.0",
                "url": "https://creativecommons.org/licenses/by-nc-nd/2.0/",
            },
            "4": {
                "id": "cc-by-2.0",
                "label": "CC BY 2.0",
                "url": "https://creativecommons.org/licenses/by/2.0/",
            },
            "5": {
                "id": "cc-by-sa-2.0",
                "label": "CC BY-SA 2.0",
                "url": "https://creativecommons.org/licenses/by-sa/2.0/",
            },
            "6": {
                "id": "cc-by-nd-2.0",
                "label": "CC BY-ND 2.0",
                "url": "https://creativecommons.org/licenses/by-nd/2.0/",
            },
            "7": {
                "id": "nkcr",
                "label": "No known copyright restrictions",
                "url": "https://www.flickr.com/commons/usage/",
            },
            "8": {
                "id": "usgov",
                "label": "United States Government Work",
                "url": "http://www.usa.gov/copyright.shtml",
            },
            "9": {
                "id": "cc0-1.0",
                "label": "CC0 1.0",
                "url": "https://creativecommons.org/publicdomain/zero/1.0/",
            },
            "10": {
                "id": "pdm",
                "label": "Public Domain Mark",
                "url": "https://creativecommons.org/publicdomain/mark/1.0/",
            },
        }

    def test_lookup_license_by_id(self, api: FlickrPhotosApi) -> None:
        assert api.lookup_license_by_id(id="0") == {
            "id": "in-copyright",
            "label": "All Rights Reserved",
            "url": None,
        }

    def test_throws_license_not_found_for_bad_id(self, api: FlickrPhotosApi) -> None:
        with pytest.raises(LicenseNotFound, match="ID -1"):
            api.lookup_license_by_id(id="-1")


@pytest.mark.parametrize(
    ["url", "user"],
    [
        # A user who doesn't have a "realname" assigned
        pytest.param(
            "https://www.flickr.com/photos/35591378@N03",
            {
                "id": "35591378@N03",
                "username": "Obama White House Archived",
                "realname": None,
                "photos_url": "https://www.flickr.com/photos/obamawhitehouse/",
                "profile_url": "https://www.flickr.com/people/obamawhitehouse/",
            },
            id="obamawhitehouse",
        ),
        # A user who has a username, but their username is different from
        # their path alias.
        #
        # i.e. although the user URL ends 'britishlibrary', if you look up
        # the user with username 'britishlibrary' you'll find somebody different.
        pytest.param(
            "https://www.flickr.com/photos/britishlibrary/",
            {
                "id": "12403504@N02",
                "username": "The British Library",
                "realname": "British Library",
                "photos_url": "https://www.flickr.com/photos/britishlibrary/",
                "profile_url": "https://www.flickr.com/people/britishlibrary/",
            },
            id="britishlibrary",
        ),
        # A user URL that uses the numeric ID rather than a path alias.
        pytest.param(
            "https://www.flickr.com/photos/199246608@N02",
            {
                "id": "199246608@N02",
                "username": "cefarrjf87",
                "realname": "Alex Chan",
                "photos_url": "https://www.flickr.com/photos/199246608@N02/",
                "profile_url": "https://www.flickr.com/people/199246608@N02/",
            },
            id="199246608@N02",
        ),
    ],
)
def test_lookup_user_by_url(api: FlickrPhotosApi, url: str, user: User) -> None:
    assert api.lookup_user_by_url(url=url) == user


class TestGetSinglePhoto:
    def test_can_get_single_photo(self, api: FlickrPhotosApi) -> None:
        resp = api.get_single_photo(photo_id="32812033543")

        assert jsonify(resp) == get_fixture(filename="32812033543.json")

    def test_sets_realname_to_none_if_empty(self, api: FlickrPhotosApi) -> None:
        info = api.get_single_photo(photo_id="31073485032")

        assert info["owner"]["realname"] is None

    def test_sets_granularity_on_date_taken(self, api: FlickrPhotosApi) -> None:
        info = api.get_single_photo(photo_id="5240741057")

        assert info["date_taken"] == {
            "value": datetime.datetime(1950, 1, 1, 0, 0, 0),
            "granularity": "6",
            "unknown": False,
        }

    def test_sets_date_unknown_on_date_taken(self, api: FlickrPhotosApi) -> None:
        info = api.get_single_photo(photo_id="25868667441")

        assert info["date_taken"] == {
            "value": datetime.datetime(2016, 3, 21, 16, 15, 39),
            "granularity": "0",
            "unknown": True,
        }

    def test_gets_photo_description(self, api: FlickrPhotosApi) -> None:
        photo = api.get_single_photo(photo_id="53248070597")
        assert photo["description"] == "Paris Montmartre"

    def test_empty_photo_description_is_none(self, api: FlickrPhotosApi) -> None:
        photo = api.get_single_photo(photo_id="5536044022")
        assert photo["description"] is None

    def test_gets_photo_title(self, api: FlickrPhotosApi) -> None:
        photo_with_title = api.get_single_photo(photo_id="20428374183")
        assert photo_with_title["title"] == "Hapjeong"

    def test_empty_photo_title_is_none(self, api: FlickrPhotosApi) -> None:
        photo_without_title = api.get_single_photo(photo_id="20967567081")
        assert photo_without_title["title"] is None

    @pytest.mark.parametrize(
        ["photo_id", "original_format"],
        [
            ("53248070597", None),
            ("32812033543", "jpg"),
            ("12533665685", "png"),
            ("4079570071", "gif"),
        ],
    )
    def test_gets_original_format(
        self, api: FlickrPhotosApi, photo_id: str, original_format: str
    ) -> None:
        photo = api.get_single_photo(photo_id=photo_id)
        assert photo["original_format"] == original_format
