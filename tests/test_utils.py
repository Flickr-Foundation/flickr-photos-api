import pytest

from flickr_photos_api.utils import parse_date_taken, parse_safety_level


def test_unrecognised_safety_level_is_error() -> None:
    with pytest.raises(ValueError, match="Unrecognised safety level"):
        parse_safety_level("-1")


def test_unrecognised_date_granularity_is_error() -> None:
    with pytest.raises(ValueError, match="Unrecognised date granularity"):
        parse_date_taken(value="2017-02-17 00:00:00", granularity="-1", unknown=False)
