from collections.abc import Iterator
import json

from authlib.integrations.httpx_client import OAuth1Client
import httpx
import pytest
import vcr

from flickr_photos_api import FlickrApi, InsufficientPermissionsToComment
from utils import get_optional_password


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
def test_finds_all_comments(api: FlickrApi, photo_id: str, count: int) -> None:
    comments = api.list_all_comments(photo_id=photo_id)

    assert len(comments) == count


def test_if_no_realname_then_empty(api: FlickrApi) -> None:
    # The first comment is one where the ``author_realname`` attribute
    # is an empty string, which we should map to ``None``.
    comments = api.list_all_comments(photo_id="53654427282")

    assert comments[0]["author"]["realname"] is None


@pytest.fixture(scope="function")
def flickr_comments_api(cassette_name: str, user_agent: str) -> Iterator[FlickrApi]:
    """
    Creates an instance of the FlickrCommentsApi class for use in tests.

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


class TestPostComment:
    def test_throws_if_not_allowed_to_post_comment(
        self, flickr_comments_api: FlickrApi
    ) -> None:
        with pytest.raises(InsufficientPermissionsToComment):
            flickr_comments_api.post_comment(
                photo_id="53374767803",
                comment_text="This is a comment on a photo where I’ve disabled commenting",
            )

    def test_throws_if_invalid_oauth_signature(self, cassette_name: str) -> None:
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
            token_secret=None,
        )

        api = FlickrApi(client=client)

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
        ):
            with pytest.raises(httpx.HTTPStatusError):
                api.post_comment(
                    photo_id="53374767803",
                    comment_text="This is a comment that uses bogus OAuth 1.0a credentials",
                )

    def test_can_successfully_post_a_comment(
        self,
        flickr_comments_api: FlickrApi,
    ) -> None:
        comment_id = flickr_comments_api.post_comment(
            photo_id="53373661077",
            comment_text="This is a comment posted by the Flickypedia unit tests",
        )

        # Check that if we double-post, we get the same comment ID back --
        # that is, that commenting is an idempotent operation.
        comment_id2 = flickr_comments_api.post_comment(
            photo_id="53373661077",
            comment_text="This is a comment posted by the Flickypedia unit tests",
        )

        assert comment_id == comment_id2
