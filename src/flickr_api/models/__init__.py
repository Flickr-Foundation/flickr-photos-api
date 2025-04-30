from datetime import datetime
import typing

from .contexts import AlbumContext, GalleryContext, GroupContext, PhotoContext
from .licenses import License, LicenseId
from .machine_tags import MachineTags
from .photo import (
    Location,
    LocationContext,
    NamedLocation,
    NumericLocation,
    Rotation,
)
from .sizes import Size
from .users import User, UserInfo


__all__ = [
    "AlbumContext",
    "GalleryContext",
    "GroupContext",
    "License",
    "LicenseId",
    "Location",
    "LocationContext",
    "MachineTags",
    "NamedLocation",
    "NumericLocation",
    "PhotoContext",
    "Rotation",
    "Size",
    "User",
    "UserInfo",
    "Visibility",
]


# Represents the accuracy to which we know a date taken to be true.
#
# See https://www.flickr.com/services/api/misc.dates.html
TakenGranularity = typing.Literal["second", "month", "year", "circa"]


class DateTaken(typing.TypedDict):
    value: datetime
    granularity: TakenGranularity


class Comment(typing.TypedDict):
    """
    A comment as received from the Flickr API.
    """

    id: str
    photo_id: str
    author_is_deleted: bool
    author: User
    text: str
    permalink: str
    date: datetime


class Tag(typing.TypedDict):
    raw_value: str
    normalized_value: str

    author_id: str
    author_name: str

    is_machine_tag: bool


class Visibility(typing.TypedDict):
    is_public: bool
    is_friend: bool
    is_family: bool


# Represents the safety level of a photo on Flickr.
#
# https://www.flickrhelp.com/hc/en-us/articles/4404064206996-Content-filters#h_01HBRRKK6F4ZAW6FTWV8BPA2G7
SafetyLevel = typing.Literal["safe", "moderate", "restricted"]


MediaType = typing.Literal["photo", "video"]


class SinglePhotoInfo(typing.TypedDict):
    """
    Represents a response from the flickr.photos.getInfo API.
    """

    id: str
    media: MediaType

    secret: str
    server: str
    farm: str
    original_format: str | None

    rotation: Rotation

    owner: User

    safety_level: SafetyLevel

    license: License

    title: str | None
    description: str | None
    tags: list[str]
    machine_tags: MachineTags
    raw_tags: typing.NotRequired[list[Tag]]

    date_posted: datetime
    date_taken: DateTaken | None
    location: Location | None

    count_comments: int
    count_views: int

    visibility: typing.NotRequired[Visibility]

    url: str


class SinglePhoto(SinglePhotoInfo):
    sizes: list[Size]


class CommonsInstitution(typing.TypedDict):
    """
    Represents an institution in the Flickr Commons programme.
    """

    user_id: str
    date_launch: datetime
    name: str
    site_url: str | None
    license_url: str
