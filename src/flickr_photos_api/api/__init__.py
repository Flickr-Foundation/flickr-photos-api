from collections.abc import Iterator
import itertools
import xml.etree.ElementTree as ET

from flickr_url_parser import ParseResult, parse_flickr_url
from nitrate.xml import (
    find_optional_text,
    find_required_elem,
    find_required_text,
)

from .base import HttpxImplementation as NewBaseApi, HttpxImplementation
from .collection_methods import CollectionMethods
from .comment_methods import CommentMethods
from .from_url_methods import FromUrlMethods
from .license_methods import LicenseMethods
from .single_photo_methods import SinglePhotoMethods
from .user_methods import UserMethods
from ..types import (
    CollectionOfElements,
    CollectionOfPhotos,
    GroupInfo,
    ParsedElement,
    PhotosFromUrl,
    PhotosInGallery,
    PhotosInGroup,
    SinglePhoto,
    User,
)
from ..utils import (
    parse_date_posted,
    parse_date_taken,
    parse_location,
    parse_safety_level,
    parse_sizes,
)


class FlickrApiMethods(
    FromUrlMethods, CommentMethods, CollectionMethods, SinglePhotoMethods, LicenseMethods, UserMethods
):
    pass


class FlickrApi(HttpxImplementation, FlickrApiMethods):
    pass
