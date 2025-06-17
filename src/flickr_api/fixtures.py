"""
Fixtures for creating instances of the FlickrApi class in tests.

To use these fixtures, add the following lines to the `conftest.py` file
in your project:

    from flickr_api.fixtures import flickr_api, flickr_oauth_api

    __all__ = ["flickr_api", "flickr_oauth_api"]

"""

from collections.abc import Iterator
import os
import typing

import httpx
from nitrate.cassettes import cassette_name
import pytest
import vcr

from flickr_api import FlickrApi


__all__ = ["cassette_name", "flickr_api", "flickr_oauth_api"]


def check_for_invalid_api_key(response: typing.Any) -> typing.Any:
    """
    Before we record a new response to a cassette, check if it's
    a Flickr API response telling us we're missing an API key -- that
    means we didn't set up the test correctly.

    If so, give the developer an instruction explaining what to do next.
    """
    try:
        body: bytes = response["body"]["string"]
    except KeyError:
        body = response["content"]

    is_error_response = body == (
        b'<?xml version="1.0" encoding="utf-8" ?>\n'
        b'<rsp stat="fail">\n\t'
        b'<err code="100" msg="Invalid API Key (Key has invalid format)" />\n'
        b"</rsp>\n"
    )
    skip_invalid_api_key_check = os.environ.get("SKIP_INVALID_API_KEY_CHECK") == "true"

    if is_error_response and not skip_invalid_api_key_check:
        raise RuntimeError(
            "You tried to record a new call to the Flickr API, \n"
            "but the tests didn't get a valid API key.\n"
            "\n"
            "Either:\n"
            "1. Pass an API key as an env var FLICKR_API_KEY=ae84…,\n"
            "   and re-run the test, or\n"
            "2. Pass an env var SKIP_INVALID_API_KEY_CHECK=true, if you \n"
            "   want to record an API call with an invalid key."
        )

    return response


@pytest.fixture
def flickr_api(cassette_name: str) -> Iterator[FlickrApi]:
    """
    Create an instance of the FlickrApi class for use in tests.

    This API is authenticated using an API key, which means it acts as
    a public user of the site -- it has no access to sensitive information.

    This API will record its interactions as "cassettes" using vcr.py --
    that is, the request and response are saved to YAML files which can
    be checked into the repo, then replayed offline (e.g. in CI tests).
    The cassette is redacted to ensure it does not contain our API key.
    """
    with vcr.use_cassette(
        cassette_name,
        cassette_library_dir="tests/fixtures/cassettes",
        filter_query_parameters=["api_key"],
        decode_compressed_response=True,
        before_record_response=check_for_invalid_api_key,
    ):
        client = httpx.Client(
            params={"api_key": os.environ.get("FLICKR_API_KEY", "<REDACTED>")},
            headers={
                "User-Agent": "flickr-photos-api <hello@flickr.org>",
                #
                # This forces the connection to close immediately after the
                # API returns a response, which avoids any warnings about
                # unclosed sockets
                "Connection": "Close",
            },
        )

        yield FlickrApi(client)


def check_for_oauth_token(response: typing.Any) -> typing.Any:
    """
    Before we record a new response to a cassette, check if it's
    a Flickr API response telling us we're missing an API key -- that
    means we didn't set up the test correctly.

    If so, give the developer an instruction explaining what to do next.
    """
    try:
        body: bytes = response["body"]["string"]
    except KeyError:  # pragma: no cover
        body = response["content"]

    is_error_response = body == (
        b'<?xml version="1.0" encoding="utf-8" ?>\n'
        b'<rsp stat="fail">\n\t<err code="98" msg="Invalid auth token" />\n</rsp>'
        b"\n"
    )
    skip_invalid_api_key_check = os.environ.get("SKIP_INVALID_API_KEY_CHECK") == "true"

    if is_error_response and not skip_invalid_api_key_check:
        raise RuntimeError(
            "You tried to record a new call to the Flickr API, \n"
            "but the tests didn't get a valid OAuth credentials.\n"
            "\n"
            "Either:\n"
            "1. Pass OAuth credentials in the following env vars:\n"
            "      - FLICKR_CLIENT_KEY\n"
            "      - FLICKR_CLIENT_SECRET\n"
            "      - FLICKR_OAUTH_TOKEN\n"
            "      - FLICKR_OAUTH_TOKEN_SECRET"
            "   and re-run the test, or\n"
            "2. Pass an env var SKIP_INVALID_API_KEY_CHECK=true, if you \n"
            "   want to record an API call with invalid credentials."
        )

    return response


@pytest.fixture
def flickr_oauth_api(cassette_name: str) -> Iterator[FlickrApi]:
    """
    Create an instance of the FlickrApi class for use in tests.

    This API is authenticated using an OAuth token, which means it acts as
    if it's logged in as this OAuth user, and has access to potentially
    private information.

    This API will record its interactions as "cassettes" using vcr.py --
    that is, the request and response are saved to YAML files which can
    be checked into the repo, then replayed offline (e.g. in CI tests).
    The cassette is redacted to ensure it does not contain OAuth credentials.
    """
    from authlib.integrations.httpx_client import OAuth1Client

    client_id = os.environ.get("FLICKR_CLIENT_KEY", "CLIENT_KEY")
    client_secret = os.environ.get("FLICKR_CLIENT_SECRET", "CLIENT_SECRET")
    token = os.environ.get("FLICKR_OAUTH_TOKEN", "OAUTH_TOKEN")
    token_secret = os.environ.get("FLICKR_OAUTH_TOKEN_SECRET", "OAUTH_TOKEN_SECRET")

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
        before_record_response=check_for_oauth_token,
    ):
        client = OAuth1Client(
            client_id=client_id,
            client_secret=client_secret,
            signature_type="QUERY",
            token=token,
            token_secret=token_secret,
            headers={
                "User-Agent": "flickr-photos-api <hello@flickr.org>",
                #
                # This forces the connection to close immediately after the
                # API returns a response, which avoids any warnings about
                # unclosed sockets
                "Connection": "Close",
            },
        )

        yield FlickrApi(client)
