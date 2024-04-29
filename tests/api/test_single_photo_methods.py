import pytest

from flickr_photos_api import FlickrPhotosApi


@pytest.mark.parametrize(
    ["photo_id", "is_deleted"], [("16062734376", True), ("53509656752", False)]
)
def test_is_photo_deleted(
    api: FlickrPhotosApi, photo_id: str, is_deleted: bool
) -> None:
    assert api.is_photo_deleted(photo_id=photo_id) == is_deleted
