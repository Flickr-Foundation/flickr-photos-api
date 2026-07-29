"""
Tests for ``flickr_api.api.comment_methods``.
"""

from authlib.integrations.httpx_client import OAuth1Client
from unittest.mock import MagicMock

import httpx
import pytest
from tenacity import RetryError

from flickr_api import FlickrApi, InsufficientPermissionsToComment
from flickr_api.exceptions import InvalidXmlException


class TestListAllComments:
    """
    Tests for ``CommentMethods.list_all_comments()``.
    """

    # These all the outliers in terms of number of comments.
    #
    # The expected value comes from the "count_comments" field on the
    # photos API response.  This API seems to return everything at once,
    # and doesn't do pagination, but let's make sure it actually does.
    @pytest.mark.parametrize(
        ["photo_id", "count"],
        [
            ("12584715825", 154),
            ("3334095096", 376),
            ("2780177093", 501),
            ("2960116125", 1329),
        ],
    )
    def test_finds_all_comments(
        self, flickr_api: FlickrApi, photo_id: str, count: int
    ) -> None:
        """
        It gets all the comments on a photo, even if the photo has
        a lot of comments.
        """
        comments = flickr_api.list_all_comments(photo_id=photo_id)

        assert len(comments) == count

    def test_if_no_realname_then_empty(self, flickr_api: FlickrApi) -> None:
        """
        If the comment author doesn't have a real name, then the
        ``realname`` property in the result is ``None``.
        """
        # The first comment comes from user 'pellepoet', who has no realname.
        #
        # The ``author_realname`` attribute in the response is
        # an empty string, which we should map to ``None``.
        comments = flickr_api.list_all_comments(photo_id="40373414385")

        assert comments[0]["author"]["realname"] is None

    def test_list_comments_with_illegal_xml_char(
        self, flickr_api: FlickrApi, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Comment bodies with illegal XML control characters are sanitized.
        """
        bad_xml = (
            '<?xml version="1.0" encoding="utf-8" ?>'
            '<rsp stat="ok"><comments page="1" pages="1" perpage="1000" total="1">'
            '<comment id="1" author="35468159852@N01" authorname="Rev Dan Catt"'
            ' realname="Daniel Catt" datecreate="1141841470"'
            ' permalink="http://www.flickr.com/photos/example/1" path_alias=""'
            ' author_is_deleted="0">hello\x14world</comment>'
            "</comments></rsp>"
        )

        def mock_call(*args: object, **kwargs: object) -> None:
            """Simulate malformed XML from the Flickr comments API."""
            raise InvalidXmlException("bad xml")

        monkeypatch.setattr(flickr_api, "call", mock_call)
        monkeypatch.setattr(
            flickr_api,
            "fetch_raw_api_response",
            lambda *, method, params: bad_xml,
        )

        comments = flickr_api.list_all_comments(photo_id="53373661077")

        assert len(comments) == 1
        assert comments[0]["text"] == "helloworld"

    def test_returns_empty_list_when_xml_still_invalid_after_sanitization(
        self, flickr_api: FlickrApi, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        If sanitization cannot produce parseable XML, return no comments.
        """

        def mock_call(*args: object, **kwargs: object) -> None:
            """Simulate malformed XML from the Flickr comments API."""
            raise InvalidXmlException("bad xml")

        monkeypatch.setattr(flickr_api, "call", mock_call)
        monkeypatch.setattr(
            flickr_api,
            "fetch_raw_api_response",
            lambda *, method, params: "not xml at all",
        )

        comments = flickr_api.list_all_comments(photo_id="53373661077")

        assert comments == []

    def test_returns_empty_list_when_sanitized_response_is_api_failure(
        self, flickr_api: FlickrApi, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Unrecognised Flickr API errors after sanitization return no comments.
        """
        fail_xml = (
            '<?xml version="1.0" encoding="utf-8" ?>'
            '<rsp stat="fail"><err code="999" msg="Unknown error" /></rsp>'
        )

        def mock_call(*args: object, **kwargs: object) -> None:
            """Simulate malformed XML from the Flickr comments API."""
            raise InvalidXmlException("bad xml")

        monkeypatch.setattr(flickr_api, "call", mock_call)
        monkeypatch.setattr(
            flickr_api,
            "fetch_raw_api_response",
            lambda *, method, params: fail_xml,
        )

        comments = flickr_api.list_all_comments(photo_id="53373661077")

        assert comments == []

    def test_list_comments_after_retry_error_with_invalid_xml(
        self, flickr_api: FlickrApi, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Retryable ``InvalidXmlException`` errors fall back to sanitized parsing.
        """
        bad_xml = (
            '<?xml version="1.0" encoding="utf-8" ?>'
            '<rsp stat="ok"><comments page="1" pages="1" perpage="1000" total="1">'
            '<comment id="1" author="35468159852@N01" authorname="a"'
            ' realname="" datecreate="1141841470"'
            ' permalink="http://www.flickr.com/photos/example/1" path_alias=""'
            ' author_is_deleted="0">ok</comment>'
            "</comments></rsp>"
        )
        attempt = MagicMock()
        attempt.exception.return_value = InvalidXmlException("bad xml")

        def mock_call(*args: object, **kwargs: object) -> None:
            """Simulate a retried Flickr API call that still has invalid XML."""
            raise RetryError(attempt)

        monkeypatch.setattr(flickr_api, "call", mock_call)
        monkeypatch.setattr(
            flickr_api,
            "fetch_raw_api_response",
            lambda *, method, params: bad_xml,
        )

        comments = flickr_api.list_all_comments(photo_id="53373661077")

        assert len(comments) == 1
        assert comments[0]["text"] == "ok"

    def test_list_comments_reraises_retry_error_for_non_xml_cause(
        self, flickr_api: FlickrApi, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        ``RetryError`` causes other than ``InvalidXmlException`` are re-raised.
        """
        attempt = MagicMock()
        attempt.exception.return_value = ValueError("transient error")

        def mock_call(*args: object, **kwargs: object) -> None:
            """Simulate a retried Flickr API call that failed for another reason."""
            raise RetryError(attempt)

        monkeypatch.setattr(flickr_api, "call", mock_call)

        with pytest.raises(RetryError):
            flickr_api.list_all_comments(photo_id="53373661077")


class TestFetchRawApiResponse:
    """
    Tests for ``FlickrApi.fetch_raw_api_response()``.
    """

    def test_returns_raw_xml(
        self, flickr_api: FlickrApi, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        The raw response body can be fetched without parsing it as XML.
        """
        captured_params: dict[str, object] = {}

        def mock_request(
            *, method: str, url: str, params: dict[str, object], timeout: int
        ) -> httpx.Response:
            """Record the request params and return a fake response."""
            captured_params.update(params)
            request = httpx.Request(method, "https://api.flickr.com/services/rest/")
            return httpx.Response(
                200,
                text='<?xml version="1.0" ?><rsp stat="ok"><echo>hello</echo></rsp>',
                request=request,
            )

        monkeypatch.setattr(flickr_api.client, "request", mock_request)

        raw = flickr_api.fetch_raw_api_response(
            method="flickr.test.echo", params={"name": "hello"}
        )

        assert 'stat="ok"' in raw
        assert captured_params == {"method": "flickr.test.echo", "name": "hello"}

    def test_returns_raw_xml_without_extra_params(
        self, flickr_api: FlickrApi, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        ``fetch_raw_api_response`` works when no extra params are passed.
        """
        captured_params: dict[str, object] = {}

        def mock_request(
            *, method: str, url: str, params: dict[str, object], timeout: int
        ) -> httpx.Response:
            """Record the request params and return a fake response."""
            captured_params.update(params)
            request = httpx.Request(method, "https://api.flickr.com/services/rest/")
            return httpx.Response(200, text='<rsp stat="ok"/>', request=request)

        monkeypatch.setattr(flickr_api.client, "request", mock_request)

        flickr_api.fetch_raw_api_response(method="flickr.test.echo")

        assert captured_params == {"method": "flickr.test.echo"}


class TestPostComment:
    """
    Tests for ``CommentMethods.post_comment``.
    """

    def test_can_successfully_post_a_comment(
        self,
        flickr_oauth_api: FlickrApi,
    ) -> None:
        """
        You can post a comment, and posting is idempotent.
        """
        comment_id = flickr_oauth_api.post_comment(
            photo_id="53373661077",
            comment_text="This is a comment posted by the Flickypedia unit tests",
        )

        # Check that if we double-post, we get the same comment ID back --
        # that is, that commenting is an idempotent operation.
        comment_id2 = flickr_oauth_api.post_comment(
            photo_id="53373661077",
            comment_text="This is a comment posted by the Flickypedia unit tests",
        )

        assert comment_id == comment_id2

    def test_throws_if_not_allowed_to_post_comment(
        self, flickr_api: FlickrApi, flickr_oauth_api: FlickrApi
    ) -> None:
        """
        If you try to comment on a photo but you're not allowed to,
        you get an ``InsufficientPermissionsToComment`` error.
        """
        with pytest.raises(InsufficientPermissionsToComment):
            flickr_oauth_api.post_comment(
                photo_id="53374767803",
                comment_text="This is a comment on a photo where I’ve disabled commenting",
            )

    def test_throws_if_invalid_oauth_signature(
        self, flickr_api: FlickrApi, flickr_oauth_api: FlickrApi, cassette_name: str
    ) -> None:
        """
        If you don't pass a valid OAuth signature, trying to post
        a comment will fail with a ``httpx.HTTPStatusError``.
        """
        assert isinstance(flickr_oauth_api.client, OAuth1Client)
        flickr_oauth_api.client.token_secret = None

        with pytest.raises(httpx.HTTPStatusError):
            flickr_oauth_api.post_comment(
                photo_id="53374767803",
                comment_text="This is a comment that uses bogus OAuth 1.0a credentials",
            )
