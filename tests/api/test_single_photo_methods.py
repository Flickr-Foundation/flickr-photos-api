"""
Tests for ``flickr_photos_api.api.single_photo_methods``.
"""

import datetime

import pytest

from flickr_photos_api import FlickrApi, PhotoIsPrivate, ResourceNotFound, SinglePhoto
from utils import get_fixture


class TestGetSinglePhoto:
    """
    Tests for ``SinglePhotoMethods.get_single_photo``.
    """

    def test_can_get_single_photo(self, api: FlickrApi) -> None:
        """
        Get a single photo and compared it to a saved response.
        """
        photo = api.get_single_photo(photo_id="32812033543")

        assert photo == get_fixture("32812033543.json", model=SinglePhoto)

    def test_sets_realname_to_none_if_empty(self, api: FlickrApi) -> None:
        """
        If the photo's owner doesn't have a real name, then
        ``realname`` is None.
        """
        info = api.get_single_photo(photo_id="31073485032")

        assert info["owner"]["realname"] is None

    @pytest.mark.parametrize(
        ["photo_id", "realname"],
        [
            ("29826215532", "Stockholm Transport Museum"),
            ("27242558570", "beachcomber australia"),
        ],
    )
    def test_fixes_realname(self, api: FlickrApi, photo_id: str, realname: str) -> None:
        """
        This function applies the realname "fixes" we have for users
        of particular interest.
        """
        photo = api.get_single_photo(photo_id=photo_id)

        assert photo["owner"]["realname"] == realname

    def test_sets_path_alias_to_none_if_empty(self, api: FlickrApi) -> None:
        """
        If the photo's owner doesn't have a path alias, then
        ``path_alias`` is None.
        """
        # This photo was posted by a user who doesn't have a path_alias
        # set on their profile.  Retrieved 7 August 2024.
        info = api.get_single_photo(photo_id="4895431370")

        assert info["owner"]["path_alias"] is None

    def test_sets_granularity_on_date_taken(self, api: FlickrApi) -> None:
        """
        The photo's ``date_taken`` has the correct granularity.
        """
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
        """
        If the Flickr API doesn't know when the photo was taken, or
        the date taken is ambiguous, then ``date_taken`` is None.
        """
        info = api.get_single_photo(photo_id=photo_id)

        assert info["date_taken"] is None

    def test_gets_photo_description(self, api: FlickrApi) -> None:
        """
        Get a photo with a description.
        """
        photo = api.get_single_photo(photo_id="53248070597")
        assert photo["description"] == "Paris Montmartre"

    def test_empty_photo_description_is_none(self, api: FlickrApi) -> None:
        """
        Get a photo without a description.
        """
        photo = api.get_single_photo(photo_id="5536044022")
        assert photo["description"] is None

    def test_gets_photo_title(self, api: FlickrApi) -> None:
        """
        Get a photo with a title.
        """
        photo_with_title = api.get_single_photo(photo_id="20428374183")
        assert photo_with_title["title"] == "Hapjeong"

    def test_empty_photo_title_is_none(self, api: FlickrApi) -> None:
        """
        Get a photo without a title.
        """
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
        """
        Get the original format of a photo.
        """
        photo = api.get_single_photo(photo_id=photo_id)
        assert photo["original_format"] == original_format

    def test_sets_human_readable_safety_level(self, api: FlickrApi) -> None:
        """
        Get the safety level of a photo.
        """
        photo = api.get_single_photo(photo_id="53248070597")
        assert photo["safety_level"] == "safe"

    def test_gets_location_for_photo(self, api: FlickrApi) -> None:
        """
        Get a photo with location information.
        """
        photo = api.get_single_photo(photo_id="52994452213")

        assert photo["location"] == {
            "latitude": 9.135158,
            "longitude": 40.083811,
            "accuracy": 16,
        }

    def test_get_empty_location_for_photo_without_geo(self, api: FlickrApi) -> None:
        """
        Get a photo without location information.
        """
        photo = api.get_single_photo(photo_id="53305573272")

        assert photo["location"] is None

    def test_it_discards_location_if_accuracy_is_zero(self, api: FlickrApi) -> None:
        """
        If a photo has location accuracy 0, then discard the
        location information.
        """
        # This is an photo with some geo/location information, but the
        # accuracy parameter is 0, which we treat as so low as to be unusable.
        photo = api.get_single_photo(photo_id="52578982111")

        assert photo["location"] is None

    def test_it_can_get_a_video(self, api: FlickrApi) -> None:
        """
        Get a "photo" which is a video.
        """
        video = api.get_single_photo(photo_id="4960396261")

        assert video["media"] == "video"
        assert video["sizes"][-1] == {
            "label": "iphone_wifi",
            "width": None,
            "height": None,
            "source": "https://www.flickr.com/photos/brampitoyo/4960396261/play/iphone_wifi/18120df31a/",
            "media": "video",
        }

    def test_get_empty_tags_for_untagged_photo(self, api: FlickrApi) -> None:
        """
        Get a photo which doesn't have any tags.
        """
        photo = api.get_single_photo(photo_id="53331717974")
        assert photo["tags"] == []
        assert photo["machine_tags"] == {}

    def test_gets_machine_tags(self, api: FlickrApi) -> None:
        """
        Get the machine tags on a photo.
        """
        photo = api.get_single_photo(photo_id="51281775881")

        assert photo["machine_tags"] == {
            "bhl:page": ["33665645"],
            "dc:identifier": ["httpsbiodiversitylibraryorgpage33665645"],
            "taxonomy:binomial": [
                "elephasmaximus",
                "elephasindicus",
                "elephasafricanus",
            ],
            "taxonomy:genus": ["loxodonta"],
        }

    def test_a_photo_with_an_empty_tag(self, api: FlickrApi) -> None:
        """
        Get a photo which has an empty string as a tag.
        """
        photo = api.get_single_photo(photo_id="52483149404")

        assert "" in photo["tags"]

    def test_gets_raw_tag_information(self, api: FlickrApi) -> None:
        """
        Get the raw tag information on a photo.
        """
        photo = api.get_single_photo(photo_id="21609597615")

        assert photo["tags"] == ["church", "wesleyanchurch", "geo:locality=ngaruawahia"]

        assert photo["raw_tags"] == [
            {
                "author_id": "126912357@N06",
                "author_name": "valuable basket",
                "raw_value": "Church",
                "normalized_value": "church",
                "is_machine_tag": False,
            },
            {
                "author_id": "126912357@N06",
                "author_name": "valuable basket",
                "raw_value": "Wesleyan Church",
                "normalized_value": "wesleyanchurch",
                "is_machine_tag": False,
            },
            {
                "author_id": "126912357@N06",
                "author_name": "valuable basket",
                "raw_value": "geo:locality=Ngaruawahia",
                "normalized_value": "geo:locality=ngaruawahia",
                "is_machine_tag": True,
            },
        ]


class TestIsPhotoDeleted:
    """
    Tests for ``SinglePhotoMethods.is_photo_deleted``.
    """

    def test_if_photo_exists_its_not_deleted(self, api: FlickrApi) -> None:
        """
        If a photo exists, it's not deleted.
        """
        assert not api.is_photo_deleted(photo_id="53509656752")
        api.get_single_photo(photo_id="53509656752")

    def test_if_photo_doesnt_exist_its_deleted(self, api: FlickrApi) -> None:
        """
        If a photo doesn't exist, it's deleted.
        """
        assert api.is_photo_deleted(photo_id="16062734376")

        with pytest.raises(ResourceNotFound):
            api.get_single_photo(photo_id="16062734376")


class TestGetPhotoContexts:
    """
    Tests for ``SinglePhotoMethods.get_photo_contexts()``.
    """

    def test_gets_empty_lists_if_no_contexts(self, api: FlickrApi) -> None:
        """
        Get the contexts of a photo which isn't in any albums,
        galleries, or groups.
        """
        contexts = api.get_photo_contexts(photo_id="53645428203")

        assert contexts == {"albums": [], "galleries": [], "groups": []}

    def test_gets_album_info(self, api: FlickrApi) -> None:
        """
        Get the context of a photo which is in multiple albums.
        """
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
        """
        Get the context of a photo which is in multiple galleries.
        """
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
        """
        Get the context of a photo which is in a group.
        """
        contexts = api.get_photo_contexts(photo_id="51011950927")

        assert len(contexts["groups"]) == 70

        assert contexts["groups"][0] == {
            "id": "78249294@N00",
            "title": "Beautiful Scenery & Landscapes",
            "url": "https://www.flickr.com/groups/scenery/pool/",
            "count_items": 668576,
            "count_members": 43105,
        }


class TestPrivatePhotos:
    """
    Tests that involve private photos.

    Note, 12 September 2024: Flickr is changing the way private photos
    are returned for API users who aren't logged in, so these tests
    will need redoing at some point.

    See https://github.com/Flickr-Foundation/flickr-photos-api/issues/103
    """

    # Private photos are difficult to find (intentionally!).
    #
    # I found a link to this private photo from a Wikimedia Commons file,
    # where it's listed as the source image.  This is the WMC file:
    # https://commons.wikimedia.org/wiki/File:Capital_Pride_Festival_2017_(35366357641).jpg

    def test_get_private_photo_is_error(self, api: FlickrApi) -> None:
        """
        If you look up a single photo, you get a ``PhotoIsPrivate`` error.
        """
        with pytest.raises(PhotoIsPrivate):
            api.get_single_photo(photo_id="35366357641")

    def test_private_photo_is_not_deleted(self, api: FlickrApi) -> None:
        """
        Private photos aren't deleted.
        """
        assert not api.is_photo_deleted(photo_id="35366357641")

    def test_get_private_photo_contexts_is_error(self, api: FlickrApi) -> None:
        """
        If you get the contexts of private photo, you get
        a ``PhotoIsPrivate`` error.
        """
        with pytest.raises(ResourceNotFound):
            api.get_photo_contexts(photo_id="35366357641")
