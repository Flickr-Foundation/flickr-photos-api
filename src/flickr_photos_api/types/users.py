import typing


class User(typing.TypedDict):
    id: str
    username: str
    realname: str | None
    path_alias: str | None
    photos_url: str
    profile_url: str


def create_user(
    id: str, username: str, realname: str | None, path_alias: str | None
) -> User:
    """
    Given some core attributes, construct a ``User`` object.

    This function is only intended for internal user.
    """
    # This is a fudge for a Flickr Commons member -- they removed the
    # 'S' so it would look good with the big 'S' in their buddy icon,
    # which doesn't work outside the Flickr.com website.
    #
    # This name needed fixing on 23 July 2024; if they ever change
    # the name on the actual account, we can remove this fudge.
    if id == "62173425@N02" and realname == "tockholm Transport Museum":
        realname = "Stockholm Transport Museum"

    # The Flickr API is a bit inconsistent about how some undefined attributes
    # are returned, e.g. ``realname`` can sometimes be null, sometimes an
    # empty string.
    #
    # In our type system, we want all of these empty values to map to ``None``.
    return {
        "id": id,
        "username": username,
        "realname": realname or None,
        "path_alias": path_alias or None,
        "photos_url": f"https://www.flickr.com/photos/{path_alias or id}/",
        "profile_url": f"https://www.flickr.com/people/{path_alias or id}/",
    }


class UserInfo(User):
    description: str | None
    has_pro_account: bool
    count_photos: int
