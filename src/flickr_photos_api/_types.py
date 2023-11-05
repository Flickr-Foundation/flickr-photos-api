import datetime
import sys
from typing import List, Literal, Optional, Union

# See https://mypy.readthedocs.io/en/stable/runtime_troubles.html#using-new-additions-to-the-typing-module
# See https://github.com/python/mypy/issues/8520
if sys.version_info >= (3, 8):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict


class License(TypedDict):
    id: str
    label: str
    url: Optional[str]


class User(TypedDict):
    id: str
    username: str
    realname: Optional[str]
    photos_url: str
    profile_url: str


# Represents the accuracy to which we know a date taken to be true.
#
# See https://www.flickr.com/services/api/misc.dates.html
TakenGranularity = Literal["second", "month", "year", "circa"]


class KnownDateTaken(TypedDict):
    value: datetime.datetime
    granularity: TakenGranularity
    unknown: Literal[False]


class UnknownDateTaken(TypedDict):
    unknown: Literal[True]


DateTaken = Union[KnownDateTaken, UnknownDateTaken]


class Size(TypedDict):
    label: str
    width: int
    height: int
    media: str
    source: str


# Represents the safety level of a photo on Flickr.
#
# https://www.flickrhelp.com/hc/en-us/articles/4404064206996-Content-filters#h_01HBRRKK6F4ZAW6FTWV8BPA2G7
SafetyLevel = Literal["safe", "moderate", "restricted"]


class SinglePhoto(TypedDict):
    id: str
    title: Optional[str]
    description: Optional[str]
    owner: User
    date_posted: datetime.datetime
    date_taken: DateTaken
    safety_level: SafetyLevel
    license: License
    url: str
    sizes: List[Size]
    original_format: Optional[str]


class CollectionOfPhotos(TypedDict):
    page_count: int
    total_photos: int
    photos: List[SinglePhoto]


class AlbumInfo(TypedDict):
    owner: User
    title: str


class PhotosInAlbum(CollectionOfPhotos):
    album: AlbumInfo


class GalleryInfo(TypedDict):
    owner_name: str
    title: str


class PhotosInGallery(CollectionOfPhotos):
    gallery: GalleryInfo
