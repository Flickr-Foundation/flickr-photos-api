"""
Fixtures and utilities to use in the tests.
"""

from collections.abc import Iterator
import json

from authlib.integrations.httpx_client import OAuth1Client
import keyring
import keyring.errors
from nitrate.cassettes import cassette_name, vcr_cassette
import pytest
import vcr

from flickr_api import FlickrApi
from flickr_api.fixtures import flickr_api, flickr_oauth_api


@pytest.fixture
def user_agent() -> str:
    """
    Returns a User-Agent header to use in testing.

    Although not required, Flickr strongly encourages all API clients
    to provide a User-Agent header.
    """
    return "flickr-photos-api/dev (https://github.com/Flickr-Foundation/flickr-photos-api; hello@flickr.org)"


def get_optional_password(username: str, password: str, *, default: str) -> str:
    """
    Get a password from the system keychain, or a default if unavailable.
    """
    try:
        return keyring.get_password(username, password) or default
    except keyring.errors.NoKeyringError:  # pragma: no cover
        return default


@pytest.fixture(scope="function")
def comments_api(cassette_name: str, user_agent: str) -> Iterator[FlickrApi]:
    """
    Creates an instance of the FlickrApi class which has permission
    to post comments to Flickr.

    This instance of the API will record its interactions as "cassettes"
    using vcr.py, which can be replayed offline (e.g. in CI tests).
    """
    with vcr.use_cassette(
        cassette_name,
        cassette_library_dir="tests/fixtures/cassettes",
        filter_query_parameters=[
            "oauth_consumer_key",
            "oauth_nonce",
            "oauth_signature",
            "oauth_signature_method",
            "oauth_timestamp",
            "oauth_token",
            "oauth_verifier",
            "oauth_version",
        ],
        decode_compressed_response=True,
    ):
        stored_token = json.loads(
            get_optional_password("flickr_photos_api", "oauth_token", default="{}")
        )

        client = OAuth1Client(
            client_id=get_optional_password(
                "flickr_photos_api", "api_key", default="123"
            ),
            client_secret=get_optional_password(
                "flickr_photos_api", "api_secret", default="456"
            ),
            signature_type="QUERY",
            token=stored_token.get("oauth_token"),
            token_secret=stored_token.get("oauth_token_secret"),
            headers={},
        )

        yield FlickrApi(client)


__all__ = [
    "cassette_name",
    "flickr_api",
    "flickr_oauth_api",
    "vcr_cassette",
    "user_agent",
    "comments_api",
]
