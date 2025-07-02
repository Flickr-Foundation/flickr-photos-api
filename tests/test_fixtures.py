"""
Tests for `flickr_api.fixtures`.
"""

import os

import pytest

from flickr_api import FlickrApi


@pytest.mark.skipif(
    "FLICKR_API_KEY" in os.environ,
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


def test_using_flickr_oauth_api_fixture_without_env_var_is_error(
    flickr_oauth_api: FlickrApi,
) -> None:
    """
    If you try to record a new VCR cassette without the right
    OAuth credentials, you get an error telling you to set some env vars.
    """

    def test_login(api: FlickrApi) -> None:
        """Call the `login` API to get a basic response."""
        api.call(method="flickr.test.login")

    with pytest.raises(
        RuntimeError, match="Pass OAuth credentials in the following env vars"
    ):
        test_login(flickr_oauth_api)
