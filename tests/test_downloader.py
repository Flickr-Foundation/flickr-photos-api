"""
Tests for ``flickr_photos_api.downloader``.
"""

from collections.abc import Iterator
import hashlib
import pathlib
import time

import httpx
import pytest
import vcr

from flickr_photos_api import download_photo


@pytest.fixture
def vcr_cassette(cassette_name: str) -> Iterator[str]:
    """
    A basic pytest fixture to save responses to the cassette directory,
    so we don't download the file every time.
    """
    with vcr.use_cassette(
        cassette_name,
        cassette_library_dir="tests/fixtures/cassettes",
        decode_compressed_response=True,
    ):
        yield cassette_name


def test_download_photo(vcr_cassette: str, tmp_path: pathlib.Path) -> None:
    """
    Download a photo from Flickr and check it's downloaded correctly.
    """
    out_path = tmp_path / "53574198477.jpg"

    download_photo(
        url="https://live.staticflickr.com/65535/53574198477_fba34d20ca_c_d.jpg",
        out_path=out_path,
    )

    assert out_path.exists()
    assert out_path.stat().st_size == 126058
    assert (
        hashlib.md5(out_path.read_bytes()).hexdigest()
        == "392b2e74d29ff90bb707658d422d14ad"
    )


def test_not_found_is_error(vcr_cassette: str, tmp_path: pathlib.Path) -> None:
    """
    Trying to fetch a Flickr URL that doesn't exist throws an immediate
    404 error.
    """
    t0 = time.time()

    with pytest.raises(httpx.HTTPStatusError):
        download_photo(
            url="https://live.staticflickr.com/65535/doesnotexist.jpg",
            out_path=tmp_path / "doesnotexist.jpg",
        )

    # Check that less than 5 seconds elapsed -- we weren't waiting for
    # the library to retry anything.
    assert time.time() - t0 < 5
