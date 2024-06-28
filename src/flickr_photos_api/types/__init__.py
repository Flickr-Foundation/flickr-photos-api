import datetime
import typing

from .contexts import AlbumContext, GalleryContext, GroupContext, PhotoContext
from .machine_tags import get_machine_tags, MachineTags
from .users import User, UserInfo, create_user


__all__ = [
    "AlbumContext",
    "GalleryContext",
    "GroupContext",
    "MachineTags",
    "PhotoContext",
    "User",
    "UserInfo",
    "create_user",
    "get_machine_tags",
]


class License(typing.TypedDict):
    id: str
    label: str
    url: str | None


class LocationInfo(typing.TypedDict):
    latitude: float
    longitude: float
    accuracy: int


# Represents the accuracy to which we know a date taken to be true.
#
# See https://www.flickr.com/services/api/misc.dates.html
TakenGranularity = typing.Literal["second", "month", "year", "circa"]


class DateTaken(typing.TypedDict):
    value: datetime.datetime
    granularity: TakenGranularity


class Size(typing.TypedDict):
    label: str
    width: int | None
    height: int | None
    media: typing.Literal["photo", "video"]
    source: str


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
    date: datetime.datetime


# Represents the safety level of a photo on Flickr.
#
# https://www.flickrhelp.com/hc/en-us/articles/4404064206996-Content-filters#h_01HBRRKK6F4ZAW6FTWV8BPA2G7
SafetyLevel = typing.Literal["safe", "moderate", "restricted"]


class SinglePhotoInfo(typing.TypedDict):
    """
    Represents a response from the flickr.photos.getInfo API.
    """

    id: str

    secret: str
    server: str
    farm: str
    original_format: str | None

    owner: User

    safety_level: SafetyLevel

    license: License

    title: str | None
    description: str | None
    tags: list[str]
    machine_tags: MachineTags

    date_posted: datetime.datetime
    date_taken: DateTaken | None
    location: LocationInfo | None

    count_comments: int
    count_views: int

    url: str


class SinglePhoto(SinglePhotoInfo):
    sizes: list[Size]


class CollectionOfPhotos(typing.TypedDict):
    photos: list[SinglePhoto]

    # Note: there are no parameters named like this in the Flickr API;
    # these names were chosen to match parameters that do exist like
    # `count_views` or `count_comments`.
    count_pages: int
    count_photos: int


class AlbumInfo(typing.TypedDict):
    owner: User
    title: str


class PhotosInAlbum(CollectionOfPhotos):
    album: AlbumInfo


class GalleryInfo(typing.TypedDict):
    owner_name: str
    title: str


class PhotosInGallery(CollectionOfPhotos):
    gallery: GalleryInfo


class GroupInfo(typing.TypedDict):
    id: str
    name: str


class PhotosInGroup(CollectionOfPhotos):
    group: GroupInfo


PhotosFromUrl = (
    SinglePhoto | CollectionOfPhotos | PhotosInAlbum | PhotosInGallery | PhotosInGroup
)


class CommonsInstitution(typing.TypedDict):
    """
    Represents an institution in the Flickr Commons programme.
    """

    user_id: str
    date_launch: datetime.datetime
    name: str
    site_url: str
    license_url: str
