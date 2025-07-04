"""
Tests for `flickr_api.models.licenses`.
"""

import pytest

from flickr_api.models import LicenseId, assert_have_all_license_ids


def test_assert_have_all_license_ids() -> None:
    """
    If you have all the `LicenseId` values, then `assert_have_all_license_ids`
    returns silently.
    """
    license_ids: list[LicenseId] = [
        "all-rights-reserved",
        "cc-by-nc-sa-2.0",
        "cc-by-nc-2.0",
        "cc-by-nc-nd-2.0",
        "cc-by-2.0",
        "cc-by-sa-2.0",
        "cc-by-nd-2.0",
        "nkcr",
        "usgov",
        "cc0-1.0",
        "pdm",
        "cc-by-4.0",
        "cc-by-sa-4.0",
        "cc-by-nd-4.0",
        "cc-by-nc-4.0",
        "cc-by-nc-sa-4.0",
        "cc-by-nc-nd-4.0",
    ]

    assert_have_all_license_ids(license_ids, label="testing")


def test_assert_have_all_license_ids_if_missing_licenses() -> None:
    """
    If you're missing some licenses, then `assert_have_all_license_ids`
    throws an AssertionError.
    """
    license_ids: list[LicenseId] = ["all-rights-reserved"]

    with pytest.raises(AssertionError):
        assert_have_all_license_ids(license_ids, label="testing")
