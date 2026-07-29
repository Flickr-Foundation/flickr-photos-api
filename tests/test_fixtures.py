"""
Tests for `flickr_api.fixtures`.
"""

import os

import pytest

from flickr_api import FlickrApi
from flickr_api.fixtures import check_for_oauth_token


def test_check_for_oauth_token_raises_for_invalid_token_response() -> None:
    """
    Recording with placeholder credentials and an invalid-token response is an error.
    """
    response = {
        "body": {
            "string": (
                b'<?xml version="1.0" encoding="utf-8" ?>\n'
                b'<rsp stat="fail">\n\t<err code="98" msg="Invalid auth token" />\n</rsp>'
                b"\n"
            )
        }
    }

    with pytest.raises(RuntimeError, match="Pass OAuth credentials in the following env vars"):
        check_for_oauth_token(response)


def test_check_for_oauth_token_raises_for_invalid_api_key_with_placeholder_credentials() -> (
    None
):
    """
    Invalid API key responses are treated as missing OAuth setup when recording.
    """
    response = {
        "body": {
            "string": (
                b'<?xml version="1.0" encoding="utf-8" ?>\n'
                b'<rsp stat="fail">\n\t'
                b'<err code="100" msg="Invalid API Key (Key has invalid format)" />\n'
                b"</rsp>\n"
            )
        }
    }

    with pytest.raises(RuntimeError, match="Pass OAuth credentials in the following env vars"):
        check_for_oauth_token(response)


def test_check_for_oauth_token_can_be_skipped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    ``SKIP_INVALID_API_KEY_CHECK`` disables the OAuth credential check.
    """
    monkeypatch.setenv("SKIP_INVALID_API_KEY_CHECK", "true")
    response = {
        "body": {
            "string": (
                b'<?xml version="1.0" encoding="utf-8" ?>\n'
                b'<rsp stat="fail">\n\t<err code="98" msg="Invalid auth token" />\n</rsp>'
                b"\n"
            )
        }
    }

    assert check_for_oauth_token(response) == response


def test_check_for_oauth_token_allows_non_auth_failures_with_placeholder_credentials() -> (
    None
):
    """
    API failures unrelated to OAuth credentials are not blocked when recording.
    """
    response = {
        "body": {
            "string": (
                b'<?xml version="1.0" encoding="utf-8" ?>\n'
                b'<rsp stat="fail">\n\t<err code="1" msg="Invalid NSID provided" />\n</rsp>\n'
            )
        }
    }

    assert check_for_oauth_token(response) == response


def test_check_for_oauth_token_allows_auth_failures_with_real_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Auth failures are only blocked when placeholder credentials are in use.
    """
    monkeypatch.setenv("FLICKR_CLIENT_KEY", "real_key")
    monkeypatch.setenv("FLICKR_OAUTH_TOKEN", "real_token")
    response = {
        "body": {
            "string": (
                b'<?xml version="1.0" encoding="utf-8" ?>\n'
                b'<rsp stat="fail">\n\t'
                b'<err code="100" msg="Invalid API Key (Key has invalid format)" />\n'
                b"</rsp>\n"
            )
        }
    }

    assert check_for_oauth_token(response) == response


@pytest.mark.skipif(
    os.environ.get("FLICKR_API_KEY", "") != "",
    reason="This test relies on the FLICKR_API_KEY env var not being set",
)
def test_using_flickr_api_fixture_without_env_var_is_error(
    flickr_api: FlickrApi,
) -> None:
    """
    If you try to record a new VCR cassette without passing an API key,
    you get an error telling you to set an env var.
    """

    def test_echo(api: FlickrApi) -> None:
        """Call the `echo` API to get a basic response."""
        api.call(method="flickr.test.echo")

    with pytest.raises(
        RuntimeError, match="Pass an API key as an env var FLICKR_API_KEY"
    ):
        test_echo(flickr_api)
