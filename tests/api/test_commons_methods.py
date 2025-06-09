"""
Tests for ``flickr_api.api.commons_methods``.
"""

from datetime import datetime, timezone

from flickr_api import FlickrApi


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
            "date_launch": datetime(2024, 10, 30, 19, 14, 23, tzinfo=timezone.utc),
            "name": "Community Archives of Belleville & Hastings County",
            "site_url": "https://www.cabhc.ca/",
            "license_url": "https://www.cabhc.ca/en/collections/collections.aspx",
        }

    def test_belleville_hastings_date(self, api: FlickrApi) -> None:
        """
        The join date of Belleville & Hastings County is correct.

        When doing some stuff with the Flickr Commons Admin APIs,
        I inadvertently reset their join date!
        """
        institutions = api.list_commons_institutions()

        belleville = next(
            inst for inst in institutions if inst["user_id"] == "134017397@N03"
        )

        assert belleville["date_launch"] == datetime(
            2024, 10, 30, 19, 14, 23, tzinfo=timezone.utc
        )
