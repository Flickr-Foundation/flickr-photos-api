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


class TestLookupUser:
    def test_lookup_user_by_url(self, api: FlickrPhotosApi) -> None:
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

    def test_lookup_user_by_url_doesnt_use_username(self, api: FlickrPhotosApi) -> None:
        # In this URL the last component is the _path alias_, not the
        # username, but I got that mixed up when I was new to the Flickr API.
        #
        # Make sure this library does the right thing!
        user_info = api.lookup_user_by_url(
            url="https://www.flickr.com/photos/britishlibrary/"
        )

        assert user_info["id"] == "12403504@N02"
        assert user_info["username"] == "The British Library"

    def test_lookup_user_by_id(self, api: FlickrPhotosApi) -> None:
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
    def test_realname(
        self, api: FlickrPhotosApi, user_id: str, realname: str | None
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
    def test_description(
        self, api: FlickrPhotosApi, user_id: str, description: str | None
    ) -> None:
        user_info = api.lookup_user_by_id(user_id=user_id)

        assert user_info["description"] == description

    @pytest.mark.parametrize(
        ["user_id", "has_pro_account"],
        [("199258389@N04", False), ("12403504@N02", True)],
    )
    def test_has_pro_account(
        self, api: FlickrPhotosApi, user_id: str, has_pro_account: bool
    ) -> None:
        user_info = api.lookup_user_by_id(user_id=user_id)

        assert user_info["has_pro_account"] == has_pro_account


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

    def test_it_can_get_a_video(self, api: FlickrPhotosApi) -> None:
        video = api.get_single_photo(photo_id="4960396261")

        assert video["sizes"][-1] == {
            "label": "iphone_wifi",
            "width": None,
            "height": None,
            "source": "https://www.flickr.com/photos/brampitoyo/4960396261/play/iphone_wifi/18120df31a/",
            "media": "video",
        }


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
        # This retrieves an album which a photo that has location accuracy 0,
        # so we want to make sure we discard the location info.
        resp = api.get_photos_in_album(
            user_url="https://www.flickr.com/photos/howardtj/",
            album_id="72157710756587587",
            per_page=500,
        )

        photo_from_album = [
            photo for photo in resp["photos"] if photo["id"] == "53283697350"
        ][0]

        assert photo_from_album["location"] is None

    def test_can_get_collection_with_videos(self, api: FlickrPhotosApi) -> None:
        api.get_photos_in_album(
            user_url="https://www.flickr.com/photos/brampitoyo/",
            album_id="72157624715342071",
        )


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
