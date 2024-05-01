import datetime

import pytest

from flickr_photos_api import FlickrApi, SinglePhoto
from utils import get_fixture


class TestGetSinglePhoto:
    def test_can_get_single_photo(self, api: FlickrApi) -> None:
        photo = api.get_single_photo(photo_id="32812033543")

        assert photo == get_fixture("32812033543.json", model=SinglePhoto)

    def test_sets_realname_to_none_if_empty(self, api: FlickrApi) -> None:
        info = api.get_single_photo(photo_id="31073485032")

        assert info["owner"]["realname"] is None

    def test_sets_granularity_on_date_taken(self, api: FlickrApi) -> None:
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
        self, api: FlickrApi, photo_id: str
    ) -> None:
        info = api.get_single_photo(photo_id=photo_id)

        assert info["date_taken"] is None

    def test_gets_photo_description(self, api: FlickrApi) -> None:
        photo = api.get_single_photo(photo_id="53248070597")
        assert photo["description"] == "Paris Montmartre"

    def test_empty_photo_description_is_none(self, api: FlickrApi) -> None:
        photo = api.get_single_photo(photo_id="5536044022")
        assert photo["description"] is None

    def test_gets_photo_title(self, api: FlickrApi) -> None:
        photo_with_title = api.get_single_photo(photo_id="20428374183")
        assert photo_with_title["title"] == "Hapjeong"

    def test_empty_photo_title_is_none(self, api: FlickrApi) -> None:
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
        self, api: FlickrApi, photo_id: str, original_format: str
    ) -> None:
        photo = api.get_single_photo(photo_id=photo_id)
        assert photo["original_format"] == original_format

    def test_sets_human_readable_safety_level(self, api: FlickrApi) -> None:
        photo = api.get_single_photo(photo_id="53248070597")
        assert photo["safety_level"] == "safe"

    def test_get_empty_tags_for_untagged_photo(self, api: FlickrApi) -> None:
        photo = api.get_single_photo(photo_id="53331717974")
        assert photo["tags"] == []

    def test_gets_location_for_photo(self, api: FlickrApi) -> None:
        photo = api.get_single_photo(photo_id="52994452213")

        assert photo["location"] == {
            "latitude": 9.135158,
            "longitude": 40.083811,
            "accuracy": 16,
        }

    def test_get_empty_location_for_photo_without_geo(self, api: FlickrApi) -> None:
        photo = api.get_single_photo(photo_id="53305573272")

        assert photo["location"] is None

    def test_it_discards_location_if_accuracy_is_zero(self, api: FlickrApi) -> None:
        # This is an photo with some geo/location information, but the accuracy parameter is 0, which we treat as so low as to be unusable.
        photo = api.get_single_photo(photo_id="52578982111")

        assert photo["location"] is None

    def test_it_can_get_a_video(self, api: FlickrApi) -> None:
        video = api.get_single_photo(photo_id="4960396261")

        assert video["sizes"][-1] == {
            "label": "iphone_wifi",
            "width": None,
            "height": None,
            "source": "https://www.flickr.com/photos/brampitoyo/4960396261/play/iphone_wifi/18120df31a/",
            "media": "video",
        }

    @pytest.mark.parametrize(
        ["photo_id", "is_deleted"], [("16062734376", True), ("53509656752", False)]
    )
    def test_is_photo_deleted(
        self, api: FlickrApi, photo_id: str, is_deleted: bool
    ) -> None:
        assert api.is_photo_deleted(photo_id=photo_id) == is_deleted


class TestGetPhotoContexts:
    def test_gets_empty_lists_if_no_contexts(self, api: FlickrApi) -> None:
        contexts = api.get_photo_contexts(photo_id="53645428203")

        assert contexts == {"albums": [], "galleries": [], "groups": []}

    def test_gets_album_info(self, api: FlickrApi) -> None:
        contexts = api.get_photo_contexts(photo_id="51800056877")

        assert len(contexts["albums"]) == 3

        assert contexts["albums"][0] == {
            "id": "72157718247390872",
            "title": "Con trâu trên đất Việt",
            "count_photos": 168,
            "count_videos": 0,
            "count_views": 1868,
            "count_comments": 0,
        }

    def test_gets_gallery_info(self, api: FlickrApi) -> None:
        contexts = api.get_photo_contexts(photo_id="53563844904")

        assert len(contexts["galleries"]) == 11

        assert contexts["galleries"][0] == {
            "id": "72157721626742458",
            "url": "https://www.flickr.com/photos/72804335@N03/galleries/72157721626742458",
            "owner": {
                "id": "72804335@N03",
                "username": "Josep M.Toset",
                "realname": None,
                "path_alias": None,
                "photos_url": "https://www.flickr.com/photos/72804335@N03/",
                "profile_url": "https://www.flickr.com/people/72804335@N03/",
            },
            "title": "paisatges",
            "description": None,
            "date_created": datetime.datetime.fromtimestamp(
                1680980061, tz=datetime.timezone.utc
            ),
            "date_updated": datetime.datetime.fromtimestamp(
                1714564015, tz=datetime.timezone.utc
            ),
            "count_photos": 166,
            "count_videos": 0,
            "count_views": 152,
            "count_comments": 4,
        }

        # Check that the ``description`` is populated when present
        assert contexts["galleries"][3]["title"] == "Ciudades y lugares asombrosos"
        assert contexts["galleries"][3]["description"] == (
            "galeria de aquellas, ciudades, pueblos, bosques, montañas,"
            "y lugares que me gustaria visitar, explorar y disfrutar"
        )

    def test_gets_group_info(self, api: FlickrApi) -> None:
        contexts = api.get_photo_contexts(photo_id="51011950927")

        assert len(contexts["groups"]) == 70

        assert contexts["groups"][0] == {
            "id": "78249294@N00",
            "title": "Beautiful Scenery & Landscapes",
            "url": "https://www.flickr.com/groups/scenery/pool/",
            "count_items": 668576,
            "count_members": 43105,
        }
