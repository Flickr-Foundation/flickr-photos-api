"""
For Flickr, a "context" is anywhere a photo appears as part of
a larger collection -- not just on its own.

It could be part of an album, a gallery, or a group.
"""

from datetime import datetime
import typing

from .users import User


class AlbumContext(typing.TypedDict):
    """
    An album is a collection of photos that are owned by the
    album's creator.

    If Alice creates an album, she can put her photos in it, but
    she can't put Bob's photos in her album, and vice versa.
    """

    id: str
    title: str

    count_photos: int
    count_videos: int

    count_views: int
    count_comments: int


class GalleryContext(typing.TypedDict):
    """
    An gallery is a collection of photos that are not owned by
    the album's gallery's photos.

    If Alice creates an album, she can't put her own photos in it,
    but she could put Bob's photos in it.
    """

    id: str
    url: str
    owner: User

    title: str
    description: str | None

    date_created: datetime
    date_updated: datetime

    count_photos: int
    count_videos: int

    count_views: int
    count_comments: int


class GroupContext(typing.TypedDict):
    """
    An group is a collection of Flickr users with a common interest,
    who create a shared pool of relevant photos.

    Alice could create a group and add her photos to the group pool.
    Bob could then join as a member and add some of his photos to
    the pool.
    """

    id: str
    title: str
    url: str

    count_items: int
    count_members: int


class PhotoContext(typing.TypedDict):
    """
    Places where a photo might appear on Flickr.com.
    """

    albums: list[AlbumContext]
    galleries: list[GalleryContext]
    groups: list[GroupContext]
