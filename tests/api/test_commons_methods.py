"""
Tests for ``flickr_photos_api.api.commons_methods``.
"""

import datetime

from flickr_photos_api import FlickrApi


class TestCommonsMethods:
    """
    Tests for ``FlickrCommonsMethods``.
    """

    def test_list_commons_institutions(self, api: FlickrApi) -> None:
        """
        When we call ``list_commons_institutions()``, we get a list
        of institutions in Flickr Commons.
        """
        institutions = api.list_commons_institutions()

        assert len(institutions) == 113
        assert institutions[0] == {
            "date_launch": datetime.datetime(
                2024, 1, 29, 17, 24, 17, tzinfo=datetime.timezone.utc
            ),
            "license_url": "https://flickr.org",
            "name": "CommonsTestAccount",
            "site_url": "https://flickr.org",
            "user_id": "200049760@N08",
        }
