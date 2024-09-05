from collections.abc import Iterator
import json
import os

from authlib.integrations.httpx_client import OAuth1Client
from nitrate.cassettes import cassette_name, vcr_cassette
import pytest
import vcr

from flickr_photos_api import FlickrApi
from utils import get_optional_password


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
        decode_compressed_response=True,
    ):
        yield FlickrApi.with_api_key(
            api_key=os.environ.get("FLICKR_API_KEY", "<REDACTED>"),
            user_agent=user_agent,
        )


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
        )

        yield FlickrApi(client=client)


__all__ = ["cassette_name", "vcr_cassette", "user_agent", "api", "comments_api"]
