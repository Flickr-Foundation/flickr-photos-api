"""
Tests for ``flickr_photos_api.api.licenses``.
"""

import pytest

from flickr_photos_api import FlickrApi, LicenseNotFound


class TestLicenseMethods:
    """
    Tests for ``LicenseMethods``.
    """

    def test_get_licenses(self, api: FlickrApi) -> None:
        """
        You can get a complete list of licenses from the API.
        """
        assert api.get_licenses() == {
            "0": {
                "id": "all-rights-reserved",
                "label": "All Rights Reserved",
                "url": "https://www.flickrhelp.com/hc/en-us/articles/10710266545556-Using-Flickr-images-shared-by-other-members",
            },
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
                "url": "https://www.usa.gov/government-copyright",
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

    def test_lookup_license_by_numeric_id(self, api: FlickrApi) -> None:
        """
        You can look up a license by its numeric ID.
        """
        assert api.lookup_license_by_id(id="0") == {
            "id": "all-rights-reserved",
            "label": "All Rights Reserved",
            "url": "https://www.flickrhelp.com/hc/en-us/articles/10710266545556-Using-Flickr-images-shared-by-other-members",
        }

    def test_lookup_license_by_human_readable_id(self, api: FlickrApi) -> None:
        """
        You can look up a license by its human-readable ID.
        """
        assert api.lookup_license_by_id(id="all-rights-reserved") == {
            "id": "all-rights-reserved",
            "label": "All Rights Reserved",
            "url": "https://www.flickrhelp.com/hc/en-us/articles/10710266545556-Using-Flickr-images-shared-by-other-members",
        }

    def test_throws_license_not_found_for_bad_id(self, api: FlickrApi) -> None:
        """
        If you try to look up a license ID which doesn't exist, you
        get a ``LicenseNotFound`` error.
        """
        with pytest.raises(LicenseNotFound, match="ID -1"):
            api.lookup_license_by_id(id="-1")
