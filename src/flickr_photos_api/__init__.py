from .api import FlickrApi
from .downloader import download_file
from .exceptions import (
    FlickrApiException,
    InsufficientPermissionsToComment,
    InvalidApiKey,
    InvalidXmlException,
    PhotoIsPrivate,
    ResourceNotFound,
    LicenseNotFound,
    UnrecognisedFlickrApiException,
    UserDeleted,
)
from .types import (
    Comment,
    CommonsInstitution,
    MachineTags,
    License,
    User,
    UserInfo,
    TakenGranularity,
    DateTaken,
    LocationInfo,
    Size,
    SafetyLevel,
    SinglePhoto,
    CollectionOfPhotos,
    PhotosFromUrl,
    PhotosInAlbum,
    PhotosInGallery,
    PhotosInGroup,
    AlbumContext,
    AlbumInfo,
    GalleryContext,
    GalleryInfo,
    GroupContext,
    GroupInfo,
    MediaType,
    PhotoContext,
    SinglePhotoInfo,
    Tag,
    Visibility,
)


__version__ = "2.16.2"


__all__ = [
    "download_file",
    "FlickrApi",
    "FlickrApiException",
    "ResourceNotFound",
    "InvalidApiKey",
    "InvalidXmlException",
    "LicenseNotFound",
    "License",
    "LocationInfo",
    "MachineTags",
    "User",
    "UserInfo",
    "TakenGranularity",
    "Comment",
    "CommonsInstitution",
    "DateTaken",
    "Size",
    "SafetyLevel",
    "SinglePhoto",
    "SinglePhotoInfo",
    "CollectionOfPhotos",
    "PhotosFromUrl",
    "PhotosInAlbum",
    "PhotosInGallery",
    "PhotosInGroup",
    "AlbumContext",
    "AlbumInfo",
    "GalleryContext",
    "GalleryInfo",
    "GroupContext",
    "GroupInfo",
    "InsufficientPermissionsToComment",
    "MediaType",
    "PhotoContext",
    "PhotoIsPrivate",
    "Tag",
    "UnrecognisedFlickrApiException",
    "UserDeleted",
    "Visibility",
    "__version__",
]
