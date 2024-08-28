import pytest

from flickr_photos_api.utils import parse_safety_level


def test_unrecognised_safety_level_is_error() -> None:
    with pytest.raises(ValueError, match="Unrecognised safety level"):
        parse_safety_level("-1")
