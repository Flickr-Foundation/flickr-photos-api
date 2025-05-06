"""
Models related to Flickr user accounts.
"""

from datetime import datetime
import typing


class User(typing.TypedDict):
    """
    Basic information about a user.  This is enough to identify the
    owner of a photo and display an attribution link.
    """

    id: str
    username: str
    realname: str | None
    path_alias: str | None
    photos_url: str
    profile_url: str
    is_deleted: typing.NotRequired[bool]


class UserInfo(User):
    """
    A user with extra information, as returned from ``user_info``.

    This includes:

    * their profile description (if any)
    * their location (if any)
    * the number of photos they've uploaded
    * their buddy icon URL
    * whether they have Flickr Pro, and if so, when it expires

    The ``pro_account_expires`` field will be present if and only if
    the user has a Pro account.
    """

    description: str | None
    location: str | None
    count_photos: int
    buddy_icon_url: str

    # Note: I tried expressing the relationship ``pro_account_expires``
    # requires ``has_pro_account = True`` in the type system, but
    # it required a Union type that broke subclassing, i.e.
    #
    #     class UserInfoWithPro(…)
    #         has_pro_account: typing.Literal[True]
    #         pro_account_expires: datetime
    #
    #     class UserInfoWithoutPro(…)
    #         has_pro_account: typing.Literal[False]
    #
    #     UserInfo = UserInfoWithPro | UserInfoWithoutPro
    #
    # but this prevents subclassing this type, which we do in the
    # Commons Explorer -- so it's a convention rather than enforced
    # by the type system.
    has_pro_account: bool
    pro_account_expires: typing.NotRequired[datetime]
