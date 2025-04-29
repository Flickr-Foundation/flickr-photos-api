"""
Types for the sizes returned by the ``flickr.photos.getSizes`` API.
"""

import typing


class PhotoSize(typing.TypedDict):
    """
    A variant of a photo you can download.

    This always has a width/height.
    """

    label: str
    width: int
    height: int
    media: typing.Literal["photo"]
    source: str


class VideoSize(typing.TypedDict):
    """
    A variant of a video you can download.

    This may not have a width/height, e.g. videos with the 'appletv' label.
    """

    label: str
    width: int | None
    height: int | None
    media: typing.Literal["video"]
    source: str


Size = PhotoSize | VideoSize
