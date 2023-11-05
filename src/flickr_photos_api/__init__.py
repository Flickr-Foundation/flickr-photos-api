from .api import FlickrPhotosApi
from .exceptions import FlickrApiException, ResourceNotFound, LicenseNotFound
from ._types import (
    License,
    User,
    DateTaken,
    Size,
    SinglePhoto,
    CollectionOfPhotos,
    PhotosInAlbum,
    PhotosInGallery,
    PhotosInGroup,
)


__version__ = "1.0.2"


__all__ = [
    "FlickrPhotosApi",
    "FlickrApiException",
    "ResourceNotFound",
    "LicenseNotFound",
    "License",
    "User",
    "DateTaken",
    "Size",
    "SinglePhoto",
    "CollectionOfPhotos",
    "PhotosInAlbum",
    "PhotosInGallery",
    "PhotosInGroup",
    "__version__",
]
