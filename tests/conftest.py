from collections.abc import Iterator
import os

from nitrate.cassettes import cassette_name, vcr_cassette
import pytest
import vcr

from flickr_photos_api import FlickrApi


@pytest.fixture
def user_agent() -> str:
    return "flickr-photos-api/dev (https://github.com/Flickr-Foundation/flickr-photos-api; hello@flickr.org)"


@pytest.fixture(scope="function")
def api(cassette_name: str, user_agent: str) -> Iterator[FlickrApi]:
    """
    Creates an instance of the FlickrApi class for use in tests.

    This instance of the API will record its interactions as "cassettes"
    using vcr.py, which can be replayed offline (e.g. in CI tests).
    """
    with vcr.use_cassette(
        cassette_name,
        cassette_library_dir="tests/fixtures/cassettes",
        filter_query_parameters=["api_key"],
    ):
        yield FlickrApi.with_api_key(
            api_key=os.environ.get("FLICKR_API_KEY", "<REDACTED>"),
            user_agent=user_agent,
        )


__all__ = ["cassette_name", "vcr_cassette", "user_agent", "api"]
