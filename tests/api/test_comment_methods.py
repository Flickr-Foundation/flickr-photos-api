"""
Tests for ``flickr_api.api.comment_methods``.
"""

from authlib.integrations.httpx_client import OAuth1Client
import httpx
import pytest

from flickr_api import (
    FlickrApi,
    InsufficientPermissionsToComment,
)


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
        self, api: FlickrApi, photo_id: str, count: int
    ) -> None:
        """
        It gets all the comments on a photo, even if the photo has
        a lot of comments.
        """
        comments = api.list_all_comments(photo_id=photo_id)

        assert len(comments) == count

    def test_if_no_realname_then_empty(self, api: FlickrApi) -> None:
        """
        If the comment author doesn't have a real name, then the
        ``realname`` property in the result is ``None``.
        """
        # The first comment comes from user 'pellepoet', who has no realname.
        #
        # The ``author_realname`` attribute in the response is
        # an empty string, which we should map to ``None``.
        comments = api.list_all_comments(photo_id="40373414385")

        assert comments[0]["author"]["realname"] is None


class TestPostComment:
    """
    Tests for ``CommentMethods.post_comment``.
    """

    def test_can_successfully_post_a_comment(
        self,
        comments_api: FlickrApi,
    ) -> None:
        """
        You can post a comment, and posting is idempotent.
        """
        comment_id = comments_api.post_comment(
            photo_id="53373661077",
            comment_text="This is a comment posted by the Flickypedia unit tests",
        )

        # Check that if we double-post, we get the same comment ID back --
        # that is, that commenting is an idempotent operation.
        comment_id2 = comments_api.post_comment(
            photo_id="53373661077",
            comment_text="This is a comment posted by the Flickypedia unit tests",
        )

        assert comment_id == comment_id2

    def test_throws_if_not_allowed_to_post_comment(
        self, api: FlickrApi, comments_api: FlickrApi
    ) -> None:
        """
        If you try to comment on a photo but you're not allowed to,
        you get an ``InsufficientPermissionsToComment`` error.
        """
        with pytest.raises(InsufficientPermissionsToComment):
            comments_api.post_comment(
                photo_id="53374767803",
                comment_text="This is a comment on a photo where I’ve disabled commenting",
            )

    def test_throws_if_invalid_oauth_signature(
        self, api: FlickrApi, comments_api: FlickrApi, cassette_name: str
    ) -> None:
        """
        If you don't pass a valid OAuth signature, trying to post
        a comment will fail with a ``httpx.HTTPStatusError``.
        """
        assert isinstance(comments_api.client, OAuth1Client)
        comments_api.client.token_secret = None

        with pytest.raises(httpx.HTTPStatusError):
            comments_api.post_comment(
                photo_id="53374767803",
                comment_text="This is a comment that uses bogus OAuth 1.0a credentials",
            )
