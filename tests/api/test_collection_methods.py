"""
Tests for ``flickr_photos_api.api.collection_methods``.
"""

import pytest

from data import FlickrUserIds
from flickr_photos_api import FlickrApi, ResourceNotFound
from flickr_photos_api.types import PhotosInAlbum
from utils import get_fixture


class TestCollectionsPhotoResponse:
    """
    This class contains tests for the _parse_collection_of_photos_response,
    which is shared among all collection responses (albums, galleries, etc.)

    We don't want to expose/test that function directly; instead we test
    how it affects the final response.
    """

    def test_sets_owner_and_url_on_collection(self, api: FlickrApi) -> None:
        """
        The photos include an ``owner`` and ``url`` parameter.
        """
        resp = api.get_photos_in_album(
            user_id="115357548@N08",
            album_id="72157640898611483",
        )

        expected_owner = {
            "id": "115357548@N08",
            "username": "Joshua Tree National Park",
            "realname": None,
            "path_alias": "joshuatreenp",
            "photos_url": "https://www.flickr.com/photos/joshuatreenp/",
            "profile_url": "https://www.flickr.com/people/joshuatreenp/",
        }

        assert all(p["owner"] == expected_owner for p in resp["photos"])

        assert (
            resp["photos"][0]["url"]
            == "https://www.flickr.com/photos/joshuatreenp/49021434741/"
        )

    def test_sets_date_unknown_on_date_taken_in_collection(
        self, api: FlickrApi
    ) -> None:
        """
        The photos don't include "date taken" if it's not known
        for a photo in the collection.
        """
        resp = api.get_photos_in_album(
            user_id="31575009@N05",
            album_id="72157664284840282",
        )

        assert resp["photos"][0]["date_taken"] is None

    def test_only_gets_publicly_available_sizes(self, api: FlickrApi) -> None:
        """
        Only get the list of publicly available sizes.
        """
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
        """
        If the photo can't be downloaded, then the ``original_format`` is None.
        """
        # This user doesn't allow downloading of their original photos,
        # so when we try to look up an album of their photos in the API,
        # we shouldn't get an Original size.
        resp = api.get_photos_in_album(
            user_id="28724605@N05",
            album_id="72157711742505183",
        )

        assert all(photo["original_format"] is None for photo in resp["photos"])

    def test_discards_location_if_accuracy_zero(self, api: FlickrApi) -> None:
        """
        If a photo has location accuracy 0, the location information
        is discarded.
        """
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
        """
        Get a collection which includes videos.
        """
        api.get_photos_in_album(
            user_id="91178292@N00",
            album_id="72157624715342071",
        )

    def test_gets_description_when_present(self, api: FlickrApi) -> None:
        """
        Get a collection where all the photos have descriptions.
        """
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
        ],
    )
    def test_methods_are_paginated(
        self, api: FlickrApi, method: str, kwargs: dict[str, str]
    ) -> None:
        """
        You can page through methods for getting collections of photos.
        """
        api_method = getattr(api, method)

        all_resp = api_method(**kwargs, page=1)

        # Getting the 5th page with a page size of 1 means getting the 5th image
        individual_resp = api_method(
            **kwargs,
            page=5,
            per_page=1,
        )

        assert individual_resp["photos"][0] == all_resp["photos"][4]


class TestGetAlbum:
    """
    Tests for ``collection_methods.get_photos_in_album``.
    """

    def test_get_album_by_user_id(self, api: FlickrApi) -> None:
        """
        Get an album by album ID and user ID.
        """
        photos = api.get_photos_in_album(
            user_id="132051449@N06",
            album_id="72157677773252346",
        )

        assert photos == get_fixture(
            "album-72157677773252346.json", model=PhotosInAlbum
        )

    def test_get_album_by_user_url(self, api: FlickrApi) -> None:
        """
        Get an album by album ID and user URL.
        """
        photos = api.get_photos_in_album(
            user_url="https://www.flickr.com/photos/132051449@N06",
            album_id="72157677773252346",
        )

        assert photos == get_fixture(
            "album-72157677773252346.json", model=PhotosInAlbum
        )

    def test_empty_album_title_is_none(self, api: FlickrApi) -> None:
        """
        Get an album where some of the photos don't have titles.
        """
        album = api.get_photos_in_album(
            user_id="132051449@N06",
            album_id="72157677773252346",
        )

        assert album["photos"][0]["title"] == "Seoul"
        assert album["photos"][7]["title"] is None

    def test_empty_album_description_is_none(self, api: FlickrApi) -> None:
        """
        Get an album where none of the photos have descriptions.
        """
        album_without_desc = api.get_photos_in_album(
            user_id="32834977@N03",
            album_id="72157626164453131",
        )

        assert all(
            photo["description"] is None for photo in album_without_desc["photos"]
        )

    def test_user_without_pathalias_is_none(self, api: FlickrApi) -> None:
        """
        If the album's owner doesn't have a path alias set, we don't
        set it on any of their photos.
        """
        result = api.get_photos_in_album(
            user_id="121626365@N06", album_id="72177720316555672"
        )

        assert result["album"]["owner"]["path_alias"] is None
        assert all(photo["owner"]["path_alias"] is None for photo in result["photos"])

    def test_user_without_realname_is_none(self, api: FlickrApi) -> None:
        """
        If the album's owner doesn't have a realname set, we don't
        set it on any of their photos.
        """
        result = api.get_photos_in_album(
            user_id="115357548@N08", album_id="72177720303084733"
        )

        assert result["album"]["owner"]["realname"] is None
        assert all(photo["owner"]["realname"] is None for photo in result["photos"])

    def test_non_existent_album_is_error(self, api: FlickrApi) -> None:
        """
        Getting an album that doesn't exist throws a ``ResourceNotFound``.
        """
        with pytest.raises(ResourceNotFound):
            api.get_photos_in_album(
                user_id=FlickrUserIds.FlickrFoundation, album_id="12345678901234567890"
            )

    def test_non_existent_user_id_is_error(self, api: FlickrApi) -> None:
        """
        Getting an album owned by a user ID that doesn't exist
        throws a ``ResourceNotFound``.
        """
        with pytest.raises(ResourceNotFound):
            api.get_photos_in_album(user_id=FlickrUserIds.NonExistent, album_id="1234")

    def test_non_existent_user_url_is_error(self, api: FlickrApi) -> None:
        """
        Getting an album owned by a user URL that doesn't exist
        throws a ``ResourceNotFound``.
        """
        with pytest.raises(ResourceNotFound):
            api.get_photos_in_album(
                user_url="https://www.flickr.com/photos/DefinitelyDoesNotExist",
                album_id="1234",
            )
