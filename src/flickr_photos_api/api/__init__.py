from .base import HttpxImplementation as HttpxImplementation
from .comment_methods import CommentMethods
from .commons_methods import FlickrCommonsMethods
from .license_methods import LicenseMethods
from .single_photo_methods import SinglePhotoMethods
from .user_methods import UserMethods


class FlickrApiMethods(
    CommentMethods,
    FlickrCommonsMethods,
    SinglePhotoMethods,
    LicenseMethods,
    UserMethods,
):
    pass


class FlickrApi(HttpxImplementation, FlickrApiMethods):
    pass
