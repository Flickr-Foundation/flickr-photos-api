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


__version__ = "2.21.0"


__all__ = [
    "download_file",
    "FlickrApi",
    "FlickrApiException",
    "ResourceNotFound",
    "InvalidApiKey",
    "InvalidXmlException",
    "LicenseNotFound",
    "InsufficientPermissionsToComment",
    "PhotoContext",
    "PhotoIsPrivate",
    "UnrecognisedFlickrApiException",
    "UserDeleted",
    "__version__",
]
