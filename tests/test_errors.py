"""
Tests that we handle errors from the Flickr API in a consistent way.

We test errors here rather than in per-method test files to ensure
we're handling errors consistently across methods.
"""

import typing

import httpx
import pytest

from data import FlickrPhotoIds
from flickr_api import (
    FlickrApi,
    FlickrApiException,
    InvalidApiKey,
    InvalidXmlException,
    ResourceNotFound,
    UnrecognisedFlickrApiException,
)


class TestInvalidPhotoIds:
    """
    Flickr photo IDs have a fixed format: they're numeric strings.

    If you pass a non-numeric string as the ``photo_id`` parameter,
    these methods throw a ``ValueError`` immediately rather than passing
    obviously bad data to the Flickr API.
    """

    @pytest.mark.parametrize("photo_id", FlickrPhotoIds.Invalid)
    def test_get_single_photo(self, api: FlickrApi, photo_id: str) -> None:
        """
        Looking up a single photo with an invalid ID throws a ``ValueError``.
        """
        with pytest.raises(ValueError, match="Not a Flickr photo ID"):
            api.get_single_photo(photo_id=photo_id)

    @pytest.mark.parametrize("photo_id", FlickrPhotoIds.Invalid)
    def test_get_photo_contexts(self, api: FlickrApi, photo_id: str) -> None:
        """
        Getting the contexts of a photo with an invalid ID throws
        a ``ValueError``.
        """
        with pytest.raises(ValueError, match="Not a Flickr photo ID"):
            api.get_photo_contexts(photo_id=photo_id)

    @pytest.mark.parametrize("photo_id", FlickrPhotoIds.Invalid)
    def test_list_all_comments(self, api: FlickrApi, photo_id: str) -> None:
        """
        Looking up comments for an invalid photo ID throws a ``ValueError``.
        """
        with pytest.raises(ValueError, match="Not a Flickr photo ID"):
            api.list_all_comments(photo_id=photo_id)

    @pytest.mark.parametrize("photo_id", FlickrPhotoIds.Invalid)
    def test_post_comment(self, comments_api: FlickrApi, photo_id: str) -> None:
        """
        Posting a comment to an invalid photo ID throws a ``ValueError``.
        """
        with pytest.raises(ValueError, match="Not a Flickr photo ID"):
            comments_api.post_comment(
                photo_id=photo_id, comment_text="This comment is for testing purposes"
            )


class TestNonExistentPhotos:
    """
    Not every numeric string points to a real Flickr photo.

    If you pass the ID of a photo that doesn't exist, these methods
    throw a ``ResourceNotFound`` error.
    """

    @pytest.mark.parametrize("photo_id", FlickrPhotoIds.NonExistent)
    def test_get_single_photo(self, api: FlickrApi, photo_id: str) -> None:
        """
        Looking up a single photo which doesn't exist throws
        ``ResourceNotFound``.
        """
        with pytest.raises(ResourceNotFound, match="Could not find photo with ID"):
            api.get_single_photo(photo_id=photo_id)

    @pytest.mark.parametrize("photo_id", FlickrPhotoIds.NonExistent)
    def test_get_photo_contexts(self, api: FlickrApi, photo_id: str) -> None:
        """
        Getting the contexts of a photo which doesn't exist throws
        ``ResourceNotFound``.
        """
        with pytest.raises(ResourceNotFound, match="Could not find photo with ID"):
            api.get_photo_contexts(photo_id=photo_id)

    @pytest.mark.parametrize("photo_id", FlickrPhotoIds.NonExistent)
    def test_list_all_comments(self, api: FlickrApi, photo_id: str) -> None:
        """
        Listing the comments on a photo which doesn't exist throws
        ``ResourceNotFound``.
        """
        with pytest.raises(ResourceNotFound, match="Could not find photo with ID"):
            api.list_all_comments(photo_id=photo_id)

    # TODO: Add test that posting comments to a non-existent photo
    # throws ``ResourceNotFound``.
    #
    # I need to remember how to set up that fixture with commenting perms.


def test_it_throws_if_bad_auth(vcr_cassette: str, user_agent: str) -> None:
    """
    If you call the Flickr API with a non-existent key, you get
    a ``FlickrApiException``.
    """
    api = FlickrApi.with_api_key(api_key="doesnotexist", user_agent=user_agent)

    with pytest.raises(FlickrApiException):
        api.get_user(user_url="https://www.flickr.com/photos/flickr/")


def test_empty_api_key_is_error(user_agent: str) -> None:
    """
    If you create a Flickr API client with an empty string as the key,
    you get a ``ValueError``.
    """
    with pytest.raises(
        ValueError, match="Cannot create a client with an empty string as the API key"
    ):
        FlickrApi.with_api_key(api_key="", user_agent=user_agent)


def test_invalid_api_key_is_error(user_agent: str) -> None:
    """
    If you call the Flickr API with a non-empty string which isn't
    a valid API key (judged by Flickr), you get an ``InvalidApiKey`` error.
    """
    api = FlickrApi.with_api_key(api_key="<bad key>", user_agent=user_agent)

    with pytest.raises(InvalidApiKey) as err:
        api.get_single_photo(photo_id="52578982111")

    assert (
        err.value.args[0]
        == "Flickr API rejected the API key as invalid (Key has invalid format)"
    )

    # Note: we need to explicitly close the httpx client here,
    # or we get a warning in the 'setup' of the next test:
    #
    #     ResourceWarning: unclosed <ssl.SSLSocket fd=13, family=2,
    #     type=1, proto=0, laddr=('…', 58686), raddr=('…', 443)>
    #
    api.client.close()


class FlakyClient:
    """
    This is a version of the Flickr API client that will throw the
    given exception on the first request, then fall back to the
    working client.
    """

    def __init__(self, underlying: httpx.Client, exc: Exception):
        self.underlying = underlying
        self.exception = exc
        self.request_count = 0

    def request(
        self,
        *,
        method: typing.Literal["GET"] = "GET",
        url: str,
        params: dict[str, str],
        timeout: int,
    ) -> httpx.Response:
        """
        Throw the exception if this is the first request, or make
        a real HTTP call if not.
        """
        self.request_count += 1

        if self.request_count == 1:
            raise self.exception
        else:
            return self.underlying.request(
                method=method, url=url, params=params, timeout=timeout
            )


@pytest.mark.parametrize(
    "exc",
    [
        pytest.param(httpx.ReadTimeout("The read operation timed out"), id="timeout"),
        pytest.param(
            httpx.ConnectError("[Errno 54] Connection reset by peer"), id="conn_reset"
        ),
        pytest.param(
            httpx.RemoteProtocolError(
                "Server disconnected without sending a response."
            ),
            id="disconnect",
        ),
    ],
)
def test_retryable_exceptions_are_retried(api: FlickrApi, exc: Exception) -> None:
    """
    If you get a retryable exception, it gets retried and you get
    the correct response.
    """
    api.client = FlakyClient(underlying=api.client, exc=exc)  # type: ignore

    photo = api.get_single_photo(photo_id="32812033543")

    assert photo["title"] == "Puppy Kisses"


def test_an_unexplained_connecterror_fails(api: FlickrApi) -> None:
    """
    If you get an unexpected/unexplained error from the underlying
    HTTP call, it's immediately raised.
    """
    api.client = FlakyClient(
        underlying=api.client, exc=httpx.ConnectError(message="BOOM!")
    )  # type: ignore

    with pytest.raises(httpx.ConnectError):
        api.get_single_photo(photo_id="32812033543")


def test_retries_5xx_error(api: FlickrApi) -> None:
    """
    If you get a single 5xx error, it gets retried and you get the
    correct response.
    """
    # The cassette for this test was constructed manually: I edited
    # an existing cassette to add a 500 response as the first response,
    # then we want to see it make a second request to retry it.
    photo = api.get_single_photo(photo_id="32812033543")

    assert photo["title"] == "Puppy Kisses"


def test_a_persistent_5xx_error_is_raised(api: FlickrApi) -> None:
    """
    If you keep getting 5xx errors, eventually the retrying gives up
    and throws the error.
    """
    # The cassette for this test was constructed manually: I copy/pasted
    # the 500 response from the previous test so that there were more
    # than it would retry.
    with pytest.raises(httpx.HTTPStatusError) as err:
        api.get_single_photo(photo_id="32812033543")

    assert err.value.response.status_code == 500


def test_retries_invalid_xml_error(api: FlickrApi) -> None:
    """
    If you get a single invalid XML response, it gets retried and you
    get the correct response.
    """
    # The cassette for this test was constructed manually: I edited
    # an existing cassette to add the invalid XML as the first response,
    # then we want to see it make a second request to retry it.
    photo = api.get_single_photo(photo_id="32812033543")

    assert photo["title"] == "Puppy Kisses"


def test_a_persistent_invalid_xml_error_is_raised(api: FlickrApi) -> None:
    """
    If you keep getting invalid XML, eventually the retrying gives up
    and throws the error.
    """
    # The cassette for this test was constructed manually: I copy/pasted
    # the invalid XML from the previous test so that there were more
    # than it would retry.
    with pytest.raises(InvalidXmlException):
        api.get_single_photo(photo_id="32812033543")


def test_retries_error_code_201(api: FlickrApi) -> None:
    """
    If you get a single error code 201 response, it gets retried and you
    get the correct response.
    """
    # The cassette for this test was constructed manually: I edited
    # an existing cassette to add the invalid XML as the first response,
    # then we want to see it make a second request to retry it.
    photo = api.get_single_photo(photo_id="32812033543")

    assert photo["title"] == "Puppy Kisses"


def test_a_persistent_error_201_is_raised(api: FlickrApi) -> None:
    """
    If you keep getting error code 201, eventually the retrying gives up
    and throws the error.
    """
    # The cassette for this test was constructed manually: I edited
    # an existing cassette to add the invalid XML as the first response,
    # then we want to see it make a second request to retry it.
    with pytest.raises(UnrecognisedFlickrApiException) as exc:
        api.get_single_photo(photo_id="32812033543")

    assert exc.value.args[0] == {
        "code": "201",
        "msg": "Sorry, the Flickr API service is not currently available.",
    }


def test_an_unrecognised_error_is_generic_exception(api: FlickrApi) -> None:
    """
    A completely unrecognised error code from the Flickr API is thrown
    as a ``UnrecognisedFlickrApiException``.
    """
    with pytest.raises(UnrecognisedFlickrApiException) as exc:
        api.call(method="flickr.test.null")

    assert exc.value.args[0]["code"] == "99"


def test_error_code_1_is_unrecognised_if_not_found(api: FlickrApi) -> None:
    """
    This is a regression test for an old mistake, where we were mapping
    error code ``1`` a bit too broadly, and this call was throwing a
    ``ResourceNotFound`` exception, which is wrong.
    """
    with pytest.raises(UnrecognisedFlickrApiException) as exc:
        api.call(method="flickr.galleries.getListForPhoto")

    assert exc.value.args[0] == {"code": "1", "msg": "Required parameter missing"}
