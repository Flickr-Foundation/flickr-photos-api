from .api import FlickrPhotosApi
from .exceptions import (
    FlickrApiException,
    InvalidApiKey,
    InvalidXmlException,
    ResourceNotFound,
    LicenseNotFound,
)
from .types import (
    Comment,
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
    AlbumInfo,
    GalleryInfo,
    GroupInfo,
)


__version__ = "1.11.0"


__all__ = [
    "FlickrPhotosApi",
    "FlickrApiException",
    "ResourceNotFound",
    "InvalidApiKey",
    "InvalidXmlException",
    "LicenseNotFound",
    "License",
    "LocationInfo",
    "User",
    "UserInfo",
    "TakenGranularity",
    "Comment",
    "DateTaken",
    "Size",
    "SafetyLevel",
    "SinglePhoto",
    "CollectionOfPhotos",
    "PhotosFromUrl",
    "PhotosInAlbum",
    "PhotosInGallery",
    "PhotosInGroup",
    "AlbumInfo",
    "GalleryInfo",
    "GroupInfo",
    "__version__",
]
