import datetime
import sys
from typing import List, Literal, Optional

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


class DateTaken(TypedDict):
    value: datetime.datetime
    granularity: str
    unknown: bool


class Size(TypedDict):
    label: str
    width: int
    height: int
    media: str
    source: str
    url: str


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
