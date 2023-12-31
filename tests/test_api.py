import datetime
import os
from typing import TypeVar

from nitrate.json import DatetimeDecoder
from nitrate.types import read_typed_json
import pytest

from flickr_photos_api import (
    CollectionOfPhotos,
    FlickrPhotosApi,
    LicenseNotFound,
    PhotosInAlbum,
    PhotosInGallery,
    PhotosInGroup,
    SinglePhoto,
    User,
)


T = TypeVar("T")


def get_fixture(filename: str, *, model: type[T]) -> T:
    return read_typed_json(
        os.path.join("tests/fixtures/api_responses", filename),
        model=model,
        cls=DatetimeDecoder,
    )


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
                "path_alias": "obamawhitehouse",
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
                "path_alias": "britishlibrary",
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
                "path_alias": None,
                "photos_url": "https://www.flickr.com/photos/199246608@N02/",
                "profile_url": "https://www.flickr.com/people/199246608@N02/",
            },
            id="199246608@N02",
        ),
    ],
)
def test_lookup_user_by_url(api: FlickrPhotosApi, url: str, user: User) -> None:
    assert api.lookup_user_by_url(url=url) == user


def test_lookup_user_by_id(api: FlickrPhotosApi) -> None:
    assert api.lookup_user_by_id(user_id="12403504@N02") == {
        "id": "12403504@N02",
        "username": "The British Library",
        "realname": "British Library",
        "path_alias": "britishlibrary",
        "photos_url": "https://www.flickr.com/photos/britishlibrary/",
        "profile_url": "https://www.flickr.com/people/britishlibrary/",
    }


class TestGetSinglePhoto:
    def test_can_get_single_photo(self, api: FlickrPhotosApi) -> None:
        photo = api.get_single_photo(photo_id="32812033543")

        assert photo == get_fixture("32812033543.json", model=SinglePhoto)

    def test_sets_realname_to_none_if_empty(self, api: FlickrPhotosApi) -> None:
        info = api.get_single_photo(photo_id="31073485032")

        assert info["owner"]["realname"] is None

    def test_sets_granularity_on_date_taken(self, api: FlickrPhotosApi) -> None:
        info = api.get_single_photo(photo_id="5240741057")

        assert info["date_taken"] == {
            "value": datetime.datetime(1950, 1, 1, 0, 0, 0),
            "granularity": "year",
        }

    @pytest.mark.parametrize(
        "photo_id",
        [
            # This is a random example of a photo I found in which the
            # taken date is unknown, i.e.:
            #
            #     <dates takenunknown="1" …>
            #
            "25868667441",
            #
            # This is a video I found in which the taken date is allegedly
            # known, but it's all zeroes, i.e.:
            #
            #     <dates taken="0000-00-00 00:00:00" takenunknown="0" … />
            #
            "52052991809",
            #
            # This is a photo I found in which the date taken is allegedly
            # known, but it's mostly zeroes, i.e.:
            #
            #    <dates taken="0000-01-01 00:00:00" takenunknown="0" … />
            #
            "3701264363",
        ],
    )
    def test_sets_date_unknown_on_date_taken(
        self, api: FlickrPhotosApi, photo_id: str
    ) -> None:
        info = api.get_single_photo(photo_id=photo_id)

        assert info["date_taken"] is None

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

    def test_sets_human_readable_safety_level(self, api: FlickrPhotosApi) -> None:
        photo = api.get_single_photo(photo_id="53248070597")
        assert photo["safety_level"] == "safe"

    def test_get_empty_tags_for_untagged_photo(self, api: FlickrPhotosApi) -> None:
        photo = api.get_single_photo(photo_id="53331717974")
        assert photo["tags"] == []

    def test_gets_location_for_photo(self, api: FlickrPhotosApi) -> None:
        photo = api.get_single_photo(photo_id="52994452213")

        assert photo["location"] == {
            "latitude": 9.135158,
            "longitude": 40.083811,
            "accuracy": 16,
        }

    def test_get_empty_location_for_photo_without_geo(
        self, api: FlickrPhotosApi
    ) -> None:
        photo = api.get_single_photo(photo_id="53305573272")

        assert photo["location"] is None

    def test_it_discards_location_if_accuracy_is_zero(
        self, api: FlickrPhotosApi
    ) -> None:
        # This is an photo with some geo/location information, but the accuracy parameter is 0, which we treat as so low as to be unusable.
        photo = api.get_single_photo(photo_id="52578982111")

        assert photo["location"] is None


class TestCollectionsPhotoResponse:
    """
    This class contains tests for the _parse_collection_of_photos_response,
    which is shared among all collection responses (albums, galleries, etc.)

    We don't want to expose/test that function directly; instead we test
    how it affects the final response.
    """

    def test_sets_owner_and_url_on_collection(self, api: FlickrPhotosApi) -> None:
        resp = api.get_photos_in_album(
            user_url="https://www.flickr.com/photos/joshuatreenp/",
            album_id="72157640898611483",
        )

        assert resp["photos"][0]["owner"] == {
            "id": "115357548@N08",
            "username": "Joshua Tree National Park",
            "realname": None,
            "path_alias": "joshuatreenp",
            "photos_url": "https://www.flickr.com/photos/joshuatreenp/",
            "profile_url": "https://www.flickr.com/people/joshuatreenp/",
        }

        assert (
            resp["photos"][0]["url"]
            == "https://www.flickr.com/photos/joshuatreenp/49021434741/"
        )

    def test_sets_date_unknown_on_date_taken_in_collection(
        self, api: FlickrPhotosApi
    ) -> None:
        resp = api.get_photos_in_album(
            user_url="https://www.flickr.com/photos/nationalarchives/",
            album_id="72157664284840282",
        )

        assert resp["photos"][0]["date_taken"] is None

    def test_only_gets_publicly_available_sizes(self, api: FlickrPhotosApi) -> None:
        # This user doesn't allow downloading of their original photos,
        # so when we try to look up an album of their photos in the API,
        # we shouldn't get an Original size.
        resp = api.get_photos_in_album(
            user_url="https://www.flickr.com/photos/mary_faith/",
            album_id="72157711742505183",
        )

        assert not any(
            size for size in resp["photos"][0]["sizes"] if size["label"] == "Original"
        )

    def test_sets_originalformat_to_none_if_no_downloads(
        self, api: FlickrPhotosApi
    ) -> None:
        # This user doesn't allow downloading of their original photos,
        # so when we try to look up an album of their photos in the API,
        # we shouldn't get an Original size.
        resp = api.get_photos_in_album(
            user_url="https://www.flickr.com/photos/mary_faith/",
            album_id="72157711742505183",
        )

        assert all(photo["original_format"] is None for photo in resp["photos"])

    def test_discards_location_if_accuracy_zero(self, api: FlickrPhotosApi) -> None:
        # This is an album where every photo has some geo/location information,
        # but the accuracy parameter is 0, which we treat as such low accuracy
        # as to be unusable.
        resp = api.get_photos_in_album(
            user_url="https://www.flickr.com/photos/rudrpeter/",
            album_id="72157633859840285",
            per_page=1,
        )

        assert all(photo["location"] is None for photo in resp["photos"])


class TestGetAlbum:
    def test_can_get_album(self, api: FlickrPhotosApi) -> None:
        album = api.get_photos_in_album(
            user_url="https://www.flickr.com/photos/spike_yun/",
            album_id="72157677773252346",
        )

        assert album == get_fixture("album-72157677773252346.json", model=PhotosInAlbum)

    def test_empty_album_title_is_none(self, api: FlickrPhotosApi) -> None:
        album = api.get_photos_in_album(
            user_url="https://www.flickr.com/photos/spike_yun/",
            album_id="72157677773252346",
        )

        assert album["photos"][0]["title"] == "Seoul"
        assert album["photos"][7]["title"] is None

    def test_empty_album_description_is_none(self, api: FlickrPhotosApi) -> None:
        album_without_desc = api.get_photos_in_album(
            user_url="https://www.flickr.com/photos/aljazeeraenglish/",
            album_id="72157626164453131",
        )

        assert all(
            photo["description"] is None for photo in album_without_desc["photos"]
        )

        album_with_desc = api.get_photos_in_album(
            user_url="https://www.flickr.com/photos/zeeyolqpictures/",
            album_id="72157631707062493",
        )

        assert all(
            isinstance(photo["description"], str) for photo in album_with_desc["photos"]
        )


def test_get_gallery_from_id(api: FlickrPhotosApi) -> None:
    photos = api.get_photos_in_gallery(gallery_id="72157720932863274")

    assert photos == get_fixture(
        "gallery-72157677773252346.json", model=PhotosInGallery
    )


def test_get_public_photos_by_user(api: FlickrPhotosApi) -> None:
    photos = api.get_public_photos_by_user(
        user_url="https://www.flickr.com/photos/george"
    )

    assert photos == get_fixture("user-george.json", model=CollectionOfPhotos)


def test_get_photos_in_group_pool(api: FlickrPhotosApi) -> None:
    photos = api.get_photos_in_group_pool(
        group_url="https://www.flickr.com/groups/slovenia/pool/"
    )

    assert photos == get_fixture("group-slovenia.json", model=PhotosInGroup)


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
        pytest.param(
            "get_photos_with_tag", {"tag": "sunset"}, id="get_photos_with_tag"
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
    resp = api.get_photos_from_flickr_url(url)

    assert resp == get_fixture(filename, model=model)


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
