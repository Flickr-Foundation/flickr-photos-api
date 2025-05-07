"""
Models for fields you get on photo objects.
"""

import typing


# When somebody uploads a photo to Flickr, they can choose to rotate it.
#
# As of April 2025, there are only four rotation options.
Rotation = typing.Literal[0, 90, 180, 270]


class NumericLocation(typing.TypedDict):
    """
    Coordinates for a location.
    """

    latitude: float
    longitude: float
    accuracy: int


LocationContext = typing.Literal["indoors", "outdoors"]


class NamedLocation(typing.TypedDict):
    """
    Human-readable names for a location.
    """

    context: LocationContext | None
    neighborhood: str | None
    locality: str | None
    county: str | None
    region: str | None
    country: str | None


class Location(NumericLocation, NamedLocation):
    """
    Both numeric and named information about a location.
    """


class Usage(typing.TypedDict):
    """
    Describes the permissions that can be set on a photo.
    """

    can_download: bool
    can_blog: bool
    can_print: bool
    can_share: bool


class ExifTag(typing.TypedDict):
    """
    An EXIF/TIFF/GPS tag for a photo, as returned by the
    `flickr.photos.getExif` API.

    See https://www.flickr.com/services/api/flickr.photos.getExif.html
    """

    tagspace: str
    tagspaceid: str
    tag: str
    label: str
    raw_value: str
    clean_value: typing.NotRequired[str]
