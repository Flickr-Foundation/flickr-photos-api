from flickr_photos_api import FlickrPhotosApi


class TestCollectionsPhotoResponse:
    """
    This class contains tests for the _parse_collection_of_photos_response,
    which is shared among all collection responses (albums, galleries, etc.)

    We don't want to expose/test that function directly; instead we test
    how it affects the final response.
    """

    def test_sets_owner_and_url_on_collection(self, api: FlickrPhotosApi) -> None:
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
            resp["photos"][0]["photo_page_url"]
            == "https://www.flickr.com/photos/joshuatreenp/49021434741/"
        )

    def test_sets_date_unknown_on_date_taken_in_collection(
        self, api: FlickrPhotosApi
    ) -> None:
        resp = api.get_photos_in_album(
            user_id="31575009@N05",
            album_id="72157664284840282",
        )

        assert resp["photos"][0]["date_taken"] is None

    def test_only_gets_publicly_available_sizes(self, api: FlickrPhotosApi) -> None:
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

    def test_sets_originalformat_to_none_if_no_downloads(
        self, api: FlickrPhotosApi
    ) -> None:
        # This user doesn't allow downloading of their original photos,
        # so when we try to look up an album of their photos in the API,
        # we shouldn't get an Original size.
        resp = api.get_photos_in_album(
            user_id="28724605@N05",
            album_id="72157711742505183",
        )

        assert all(photo["original_format"] is None for photo in resp["photos"])

    def test_discards_location_if_accuracy_zero(self, api: FlickrPhotosApi) -> None:
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

    def test_can_get_collection_with_videos(self, api: FlickrPhotosApi) -> None:
        api.get_photos_in_album(
            user_id="91178292@N00",
            album_id="72157624715342071",
        )
