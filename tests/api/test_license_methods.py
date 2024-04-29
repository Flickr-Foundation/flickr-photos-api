import pytest

from flickr_photos_api import FlickrPhotosApi, LicenseNotFound


def test_get_licenses(api: FlickrPhotosApi) -> None:
    assert api.get_licenses() == {
        "0": {"id": "in-copyright", "label": "All Rights Reserved", "url": None},
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
            "url": "http://www.usa.gov/copyright.shtml",
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


def test_lookup_license_by_id(api: FlickrPhotosApi) -> None:
    assert api.lookup_license_by_id(id="0") == {
        "id": "in-copyright",
        "label": "All Rights Reserved",
        "url": None,
    }


def test_throws_license_not_found_for_bad_id(api: FlickrPhotosApi) -> None:
    with pytest.raises(LicenseNotFound, match="ID -1"):
        api.lookup_license_by_id(id="-1")
