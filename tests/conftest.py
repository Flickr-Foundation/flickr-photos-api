from collections.abc import Generator
import os

from nitrate.cassettes import cassette_name, vcr_cassette
import pytest
import vcr

from flickr_photos_api import FlickrPhotosApi


@pytest.fixture
def user_agent() -> str:
    return "flickr-photos-api/dev (https://github.com/Flickr-Foundation/flickr-photos-api; hello@flickr.org)"


@pytest.fixture(scope="function")
def api(cassette_name: str, user_agent: str) -> Generator[FlickrPhotosApi, None, None]:
    """
    Creates an instance of the FlickrPhotosApi class for use in tests.

    This instance of the API will record its interactions as "cassettes"
    using vcr.py, which can be replayed offline (e.g. in CI tests).
    """
    with vcr.use_cassette(
        cassette_name,
        cassette_library_dir="tests/fixtures/cassettes",
        filter_query_parameters=["api_key"],
    ):
        yield FlickrPhotosApi(
            api_key=os.environ.get("FLICKR_API_KEY", "<REDACTED>"),
            user_agent=user_agent,
        )


__all__ = ["cassette_name", "vcr_cassette", "user_agent", "api"]
