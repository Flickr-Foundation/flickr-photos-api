"""
Tests for ``flickr_api.downloader``.
"""

from collections.abc import Iterator
import hashlib
from pathlib import Path
import time

import httpx
import pytest
import vcr

from flickr_api import download_file


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


def test_download_photo(vcr_cassette: str, tmp_path: Path) -> None:
    """
    Download a photo from Flickr and check it's downloaded correctly.
    """
    result = download_file(
        url="https://live.staticflickr.com/65535/53574198477_fba34d20ca_c_d.jpg",
        download_dir=tmp_path,
        base_name="53574198477",
    )

    assert result == {
        "path": tmp_path / "53574198477.jpg",
        "content_type": "image/jpeg",
    }

    assert result["path"].exists()
    assert result["path"].stat().st_size == 126058
    assert (
        hashlib.md5(result["path"].read_bytes()).hexdigest()
        == "392b2e74d29ff90bb707658d422d14ad"
    )


def test_download_video(vcr_cassette: str, tmp_path: Path) -> None:
    """
    Download a video from Flickr and check it's downloaded correctly.
    """
    result = download_file(
        url="https://www.flickr.com/photos/straytoaster/51572201979/play/360p/6737dcd2a7/",
        download_dir=tmp_path,
        base_name="51572201979",
    )

    assert result == {"path": tmp_path / "51572201979.mp4", "content_type": "video/mp4"}


def test_not_found_is_error(vcr_cassette: str, tmp_path: Path) -> None:
    """
    Trying to fetch a Flickr URL that doesn't exist throws an immediate
    404 error.
    """
    t0 = time.time()

    with pytest.raises(httpx.HTTPStatusError):
        download_file(
            url="https://live.staticflickr.com/65535/doesnotexist.jpg",
            download_dir=tmp_path,
            base_name="doesnotexist",
        )

    # Check that less than 5 seconds elapsed -- we weren't waiting for
    # the library to retry anything.
    assert time.time() - t0 < 5


def test_an_unrecognised_content_type_is_downloaded_sans_extension(
    vcr_cassette: str, tmp_path: Path
) -> None:
    """
    If the URL has an unrecognised Content-Type, it's downloaded
    without an extension.
    """
    result = download_file(
        url="https://flickr.com",
        download_dir=tmp_path,
        base_name="homepage",
    )

    assert result == {
        "path": tmp_path / "homepage",
        "content_type": "text/html",
    }
