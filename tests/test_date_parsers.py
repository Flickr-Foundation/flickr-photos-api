"""
Tests for ``flickr_photos_api.date_parsers``.
"""

import pytest

from flickr_photos_api.date_parsers import parse_date_taken


def test_unrecognised_date_granularity_is_error() -> None:
    """
    If you pass an unrecognised date taken granularity,
    it throws ``ValueError``.
    """
    with pytest.raises(ValueError, match="Unrecognised date granularity"):
        parse_date_taken(value="2017-02-17 00:00:00", granularity="-1", unknown=False)
