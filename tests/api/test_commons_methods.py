"""
Tests for ``flickr_api.api.commons_methods``.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock
from xml.etree import ElementTree as ET

from flickr_api import FlickrApi
from flickr_api.api.commons_methods import FlickrCommonsMethods


class TestCommonsMethods:
    """
    Tests for ``FlickrCommonsMethods``.
    """

    def test_list_commons_institutions(self, flickr_api: FlickrApi) -> None:
        """
        When we call ``list_commons_institutions()``, we get a list
        of institutions in Flickr Commons.
        """
        institutions = flickr_api.list_commons_institutions()

        assert len(institutions) == 115
        assert institutions[0] == {
            "user_id": "134017397@N03",
            "date_launch": datetime(2024, 10, 30, 19, 14, 23, tzinfo=timezone.utc),
            "name": "Community Archives of Belleville & Hastings County",
            "site_url": "https://www.cabhc.ca/",
            "license_url": "https://www.cabhc.ca/en/collections/collections.aspx",
        }

    def test_belleville_hastings_date(self, flickr_api: FlickrApi) -> None:
        """
        The join date of Belleville & Hastings County is correct.

        When doing some stuff with the Flickr Commons Admin APIs,
        I inadvertently reset their join date!
        """
        institutions = flickr_api.list_commons_institutions()

        belleville = next(
            inst for inst in institutions if inst["user_id"] == "134017397@N03"
        )

        assert belleville["date_launch"] == datetime(
            2024, 10, 30, 19, 14, 23, tzinfo=timezone.utc
        )

    def test_empty_license_url_does_not_abort_list(self) -> None:
        """
        An empty license URL is returned as ``""``; other institutions
        in the same response are still returned.
        """
        xml = """
        <rsp stat="ok">
          <institutions>
            <institution nsid="111@N00" date_launch="1722472152">
              <name>Empty License Org</name>
              <urls>
                <url type="site">https://example.org/</url>
                <url type="license"></url>
              </urls>
            </institution>
            <institution nsid="222@N00" date_launch="1200470400">
              <name>Has License Org</name>
              <urls>
                <url type="site">https://example.com/</url>
                <url type="license">https://example.com/license</url>
              </urls>
            </institution>
          </institutions>
        </rsp>
        """
        api = MagicMock()
        api.call.return_value = ET.fromstring(xml)

        institutions = FlickrCommonsMethods.list_commons_institutions(api)

        assert institutions == [
            {
                "user_id": "111@N00",
                "date_launch": datetime(2024, 8, 1, 0, 29, 12, tzinfo=timezone.utc),
                "name": "Empty License Org",
                "site_url": "https://example.org/",
                "license_url": "",
            },
            {
                "user_id": "222@N00",
                "date_launch": datetime(2008, 1, 16, 8, 0, 0, tzinfo=timezone.utc),
                "name": "Has License Org",
                "site_url": "https://example.com/",
                "license_url": "https://example.com/license",
            },
        ]
