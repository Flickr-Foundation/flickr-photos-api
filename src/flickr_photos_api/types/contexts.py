import datetime
import typing


class AlbumContext(typing.TypedDict):
    id: str
    title: str

    count_photos: int
    count_videos: int

    count_views: int
    count_comments: int


class GalleryContext(typing.TypedDict):
    id: str
    url: str
    owner_id: str

    title: str
    description: str

    date_created: datetime.datetime
    date_updated: datetime.datetime

    count_photos: int
    count_videos: int

    count_views: int
    count_comments: int


class GroupContext(typing.TypedDict):
    id: str
    url: str
    title: str

    count_items: int
    count_members: int


class PhotoContext:
    albums: list[AlbumContext]
    galleries: list[GalleryContext]
    groups: list[GroupContext]
