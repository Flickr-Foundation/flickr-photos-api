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

        assert len(institutions) == 115
        assert institutions[0] == {
            "user_id": "134017397@N03",
            "date_launch": datetime.datetime(
                2024, 10, 30, 19, 14, 23, tzinfo=datetime.timezone.utc
            ),
            "name": "Community Archives of Belleville & Hastings County",
            "site_url": "https://www.cabhc.ca/",
            "license_url": "https://www.cabhc.ca/en/collections/collections.aspx",
        }
