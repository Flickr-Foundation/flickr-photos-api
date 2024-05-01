from .base import HttpxImplementation as HttpxImplementation
from .collection_methods import CollectionMethods
from .comment_methods import CommentMethods
from .commons_methods import FlickrCommonsMethods
from .from_url_methods import FromUrlMethods
from .license_methods import LicenseMethods
from .single_photo_methods import SinglePhotoMethods
from .user_methods import UserMethods


class FlickrApiMethods(
    FromUrlMethods,
    CommentMethods,
    FlickrCommonsMethods,
    CollectionMethods,
    SinglePhotoMethods,
    LicenseMethods,
    UserMethods,
):
    pass


class FlickrApi(HttpxImplementation, FlickrApiMethods):
    pass
