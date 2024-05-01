import pytest

from flickr_photos_api import FlickrApi
from flickr_photos_api.types import (
    PhotosInAlbum,
    PhotosInGallery,
    PhotosInGroup,
    CollectionOfPhotos,
)
from utils import get_fixture


class TestCollectionsPhotoResponse:
    """
    This class contains tests for the _parse_collection_of_photos_response,
    which is shared among all collection responses (albums, galleries, etc.)

    We don't want to expose/test that function directly; instead we test
    how it affects the final response.
    """

    def test_sets_owner_and_url_on_collection(self, api: FlickrApi) -> None:
        resp = api.get_photos_in_album(
            user_id="115357548@N08",
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
        self, api: FlickrApi
    ) -> None:
        resp = api.get_photos_in_album(
            user_id="31575009@N05",
            album_id="72157664284840282",
        )

        assert resp["photos"][0]["date_taken"] is None

    def test_only_gets_publicly_available_sizes(self, api: FlickrApi) -> None:
        # This user doesn't allow downloading of their original photos,
        # so when we try to look up an album of their photos in the API,
        # we shouldn't get an Original size.
        resp = api.get_photos_in_album(
            user_id="28724605@N05",
            album_id="72157711742505183",
        )

        assert not any(
            size for size in resp["photos"][0]["sizes"] if size["label"] == "Original"
        )

    def test_sets_originalformat_to_none_if_no_downloads(self, api: FlickrApi) -> None:
        # This user doesn't allow downloading of their original photos,
        # so when we try to look up an album of their photos in the API,
        # we shouldn't get an Original size.
        resp = api.get_photos_in_album(
            user_id="28724605@N05",
            album_id="72157711742505183",
        )

        assert all(photo["original_format"] is None for photo in resp["photos"])

    def test_discards_location_if_accuracy_zero(self, api: FlickrApi) -> None:
        # This retrieves an album which a photo that has location accuracy 0,
        # so we want to make sure we discard the location info.
        resp = api.get_photos_in_album(
            user_id="25925838@N00",
            album_id="72157710756587587",
            per_page=500,
        )

        photo_from_album = [
            photo for photo in resp["photos"] if photo["id"] == "53283697350"
        ][0]

        assert photo_from_album["location"] is None

    def test_can_get_collection_with_videos(self, api: FlickrApi) -> None:
        api.get_photos_in_album(
            user_id="91178292@N00",
            album_id="72157624715342071",
        )

    def test_gets_description_when_present(self, api: FlickrApi) -> None:
        # This is a collection of screenshots from a Flickr Foundation album,
        # which we know have descriptions populated
        album_with_desc = api.get_photos_in_album(
            user_id="197130754@N07",
            album_id="72177720315673331",
        )

        assert all(
            isinstance(photo["description"], str) for photo in album_with_desc["photos"]
        )

    @pytest.mark.parametrize(
        ["method", "kwargs"],
        [
            pytest.param(
                "get_photos_in_album",
                {
                    "user_id": "132051449@N06",
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
                "get_photos_in_user_photostream",
                {"user_id": "34427469121@N01"},
                id="get_photos_in_user_photostream",
            ),
            pytest.param(
                "get_photos_in_group_pool",
                {"group_url": "https://www.flickr.com/groups/slovenia/pool/"},
                id="get_photos_in_group_pool",
            ),
        ],
    )
    def test_methods_are_paginated(
        self, api: FlickrApi, method: str, kwargs: dict[str, str]
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

    def test_user_without_pathalias_is_none(self, api: FlickrApi) -> None:
        gallery = api.get_photos_in_gallery(gallery_id="72157722258598968")

        assert gallery["photos"][0]["id"] == "53651808642"
        assert gallery["photos"][0]["owner"]["path_alias"] is None

    def test_user_without_realname_is_none(self, api: FlickrApi) -> None:
        gallery = api.get_photos_in_gallery(gallery_id="72157722112740042")

        assert gallery["photos"][0]["id"] == "53683422277"
        assert gallery["photos"][0]["owner"]["realname"] is None


class TestGetAlbum:
    def test_get_album_by_user_id(self, api: FlickrApi) -> None:
        photos = api.get_photos_in_album(
            user_id="132051449@N06",
            album_id="72157677773252346",
        )

        assert photos == get_fixture(
            "album-72157677773252346.json", model=PhotosInAlbum
        )

    def test_get_album_by_user_url(self, api: FlickrApi) -> None:
        photos = api.get_photos_in_album(
            user_url="https://www.flickr.com/photos/132051449@N06",
            album_id="72157677773252346",
        )

        assert photos == get_fixture(
            "album-72157677773252346.json", model=PhotosInAlbum
        )

    def test_empty_album_title_is_none(self, api: FlickrApi) -> None:
        album = api.get_photos_in_album(
            user_id="132051449@N06",
            album_id="72157677773252346",
        )

        assert album["photos"][0]["title"] == "Seoul"
        assert album["photos"][7]["title"] is None

    def test_empty_album_description_is_none(self, api: FlickrApi) -> None:
        album_without_desc = api.get_photos_in_album(
            user_id="32834977@N03",
            album_id="72157626164453131",
        )

        assert all(
            photo["description"] is None for photo in album_without_desc["photos"]
        )

    def test_user_without_pathalias_is_none(self, api: FlickrApi) -> None:
        photos = api.get_photos_in_album(
            user_id="121626365@N06", album_id="72177720316555672"
        )

        assert photos["album"]["owner"]["path_alias"] is None
        assert photos["photos"][0]["owner"]["path_alias"] is None

    def test_user_without_realname_is_none(self, api: FlickrApi) -> None:
        photos = api.get_photos_in_album(
            user_id="115357548@N08", album_id="72177720303084733"
        )

        assert photos["album"]["owner"]["realname"] is None
        assert photos["photos"][0]["owner"]["realname"] is None


def test_get_gallery_from_id(api: FlickrApi) -> None:
    photos = api.get_photos_in_gallery(gallery_id="72157720932863274")

    assert photos == get_fixture(
        "gallery-72157677773252346.json", model=PhotosInGallery
    )


class TestGetPhotosInUserPhotostream:
    def test_get_photos_by_user_id(self, api: FlickrApi) -> None:
        photos = api.get_photos_in_user_photostream(user_id="34427469121@N01")

        assert photos == get_fixture("user-george.json", model=CollectionOfPhotos)

    def test_get_photos_by_user_url(self, api: FlickrApi) -> None:
        photos = api.get_photos_in_user_photostream(
            user_url="https://www.flickr.com/photos/34427469121@N01"
        )

        assert photos == get_fixture("user-george.json", model=CollectionOfPhotos)

    def test_empty_result_if_no_public_photos(self, api: FlickrApi) -> None:
        # This is a user who doesn't have any public photos.
        #
        # I found them by looking for users on the Flickr help forums who wanted
        # to make all their photos private:
        # https://www.flickr.com/help/forum/en-us/72157668446667394/
        photos = api.get_photos_in_user_photostream(user_id="51635425@N00")

        assert photos == {"count_pages": 1, "count_photos": 0, "photos": []}

    def test_no_realname_is_none(self, api: FlickrApi) -> None:
        # This is the Commons Test account, which doesn't have
        # a 'realname' set
        result = api.get_photos_in_user_photostream(user_id="200049760@N08")

        owner = result["photos"][0]["owner"]
        assert owner["realname"] is None

    def test_no_path_alias_is_none(self, api: FlickrApi) -> None:
        # This is the Commons Test account, which doesn't have
        # a 'path_alias' set
        result = api.get_photos_in_user_photostream(user_id="200049760@N08")

        owner = result["photos"][0]["owner"]
        assert owner["path_alias"] is None


def test_get_photos_in_group_pool(api: FlickrApi) -> None:
    photos = api.get_photos_in_group_pool(
        group_url="https://www.flickr.com/groups/slovenia/pool/"
    )

    assert photos == get_fixture("group-slovenia.json", model=PhotosInGroup)


def test_get_photos_with_tag(api: FlickrApi) -> None:
    photos = api.get_photos_with_tag(tag="sunset")

    assert photos == get_fixture("tag-sunset.json", model=CollectionOfPhotos)
