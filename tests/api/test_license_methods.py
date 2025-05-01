"""
Tests for ``flickr_api.api.licenses``.
"""

from datetime import datetime, timezone

import pytest

from flickr_api import FlickrApi, LicenseNotFound, ResourceNotFound


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

    @pytest.mark.parametrize("bad_id", ["-1", "100"])
    def test_throws_license_not_found_for_bad_id(
        self, api: FlickrApi, bad_id: str
    ) -> None:
        """
        If you try to look up a license ID which doesn't exist, you
        get a ``LicenseNotFound`` error.
        """
        with pytest.raises(LicenseNotFound, match=bad_id):
            api.lookup_license_by_id(id=bad_id)


class TestGetLicenseHistory:
    """
    Tests for `get_license_history`.
    """

    def test_photo_with_initial_license(self, api: FlickrApi) -> None:
        """
        The license history of a photo which has the same license as
        it was initially uploaded with has a single entry.
        """
        expected = [
            {
                "date_posted": datetime(2009, 9, 23, 21, 36, 56, tzinfo=timezone.utc),
                "license": {
                    "id": "nkcr",
                    "label": "No known copyright restrictions",
                    "url": "https://www.flickr.com/commons/usage/",
                },
            }
        ]
        actual = api.get_license_history(photo_id="3948976954")

        assert expected == actual

    def test_photo_with_single_license_change(self, api: FlickrApi) -> None:
        """
        The license history of a photo which has a single license change
        has two entries: the initial license and the change.
        """
        expected = [
            {
                "date_changed": datetime(2025, 5, 1, 11, 15, 8, tzinfo=timezone.utc),
                "old_license": {
                    "id": "cc-by-2.0",
                    "label": "CC BY 2.0",
                    "url": "https://creativecommons.org/licenses/by/2.0/",
                },
                "new_license": {
                    "id": "cc-by-sa-2.0",
                    "label": "CC BY-SA 2.0",
                    "url": "https://creativecommons.org/licenses/by-sa/2.0/",
                },
            },
        ]
        actual = api.get_license_history(photo_id="54049228596")

        assert expected == actual

    def test_photo_with_changed_license(self, api: FlickrApi) -> None:
        """
        The license history of a photo whose license has been edited
        multiple times has multiple entries.
        """
        expected = [
            {
                "date_changed": datetime(2025, 4, 14, 2, 34, 50, tzinfo=timezone.utc),
                "old_license": {
                    "id": "all-rights-reserved",
                    "label": "All Rights Reserved",
                    "url": "https://www.flickrhelp.com/hc/en-us/articles/10710266545556-Using-Flickr-images-shared-by-other-members",
                },
                "new_license": {
                    "id": "pdm",
                    "label": "Public Domain Mark",
                    "url": "https://creativecommons.org/publicdomain/mark/1.0/",
                },
            },
            {
                "date_changed": datetime(2025, 4, 17, 15, 58, 25, tzinfo=timezone.utc),
                "old_license": {
                    "id": "pdm",
                    "label": "Public Domain Mark",
                    "url": "https://creativecommons.org/publicdomain/mark/1.0/",
                },
                "new_license": {
                    "id": "nkcr",
                    "label": "No known copyright restrictions",
                    "url": "https://www.flickr.com/commons/usage/",
                },
            },
        ]
        actual = api.get_license_history(photo_id="54450311696")

        assert expected == actual

    @pytest.mark.parametrize(
        "photo_id", ["does_not_exist", "12345678901234567890", "-1"]
    )
    def test_non_existent_photo_is_error(self, api: FlickrApi, photo_id: str) -> None:
        """
        Looking up the license history of a non-existent photo is
        an error.
        """
        with pytest.raises(ResourceNotFound):
            api.get_license_history(photo_id)
