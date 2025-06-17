"""
Fixtures and utilities to use in the tests.
"""

from nitrate.cassettes import cassette_name, vcr_cassette
import pytest

from flickr_api.fixtures import flickr_api, flickr_oauth_api


@pytest.fixture
def user_agent() -> str:
    """
    Returns a User-Agent header to use in testing.

    Although not required, Flickr strongly encourages all API clients
    to provide a User-Agent header.
    """
    return "flickr-photos-api/dev (https://github.com/Flickr-Foundation/flickr-photos-api; hello@flickr.org)"


__all__ = [
    "cassette_name",
    "flickr_api",
    "flickr_oauth_api",
    "vcr_cassette",
    "user_agent",
]
