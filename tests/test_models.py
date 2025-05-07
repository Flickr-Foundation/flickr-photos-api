"""
Tests for `flickr_api.models`.
"""

from nitrate.types import validate_type

from flickr_api import FlickrApi
from flickr_api.models import SinglePhoto


def test_validate_single_photo_info(api: FlickrApi) -> None:
    """
    We can use `SinglePhoto` with `validate_type`.

    We use this helper extensively in our other projects, and it's
    important that it's compatible with this model.
    """
    photo = api.get_single_photo(photo_id="54159643533")

    assert validate_type(photo, model=SinglePhoto)
