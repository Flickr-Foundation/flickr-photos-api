import pytest

from flickr_photos_api import FlickrApi


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
