import datetime
import typing


class License(typing.TypedDict):
    id: str
    label: str
    url: str | None


class LocationInfo(typing.TypedDict):
    latitude: float
    longitude: float
    accuracy: int


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

    date_posted: datetime.datetime
    date_taken: DateTaken | None
    location: LocationInfo | None

    count_comments: int
    count_views: int

    photo_page_url: str


class SinglePhoto(typing.TypedDict):
    id: str
    title: str | None
    description: str | None
    owner: User
    date_posted: datetime.datetime
    date_taken: DateTaken | None
    safety_level: SafetyLevel
    license: License
    url: str
    sizes: list[Size]
    original_format: str | None
    tags: list[str]
    location: LocationInfo | None


class SinglePhotoInfoWithSizes(SinglePhotoInfo):
    sizes: list[Size]


class CollectionOfPhotos(typing.TypedDict):
    photos: list[SinglePhotoInfoWithSizes]

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
