"""
Exceptions and errors that are thrown by this library.
"""

import re


class FlickrApiException(Exception):
    """
    Base class for all exceptions thrown from the Flickr API.
    """

    pass


class UnrecognisedFlickrApiException(FlickrApiException):
    """
    Thrown when we get an unrecognised error from the Flickr API.
    """

    pass


class InvalidXmlException(FlickrApiException):
    """
    Thrown when we get invalid XML from the Flickr API.
    """

    pass


class InvalidApiKey(FlickrApiException):
    """
    Thrown when you try to use an API key with an invalid format.
    """

    def __init__(self, message: str):
        # We extract the key part of the message to highlight it, e.g.:
        #
        #       'Invalid API Key (Key has expired)'
        #    ~> 'Flickr API rejected the API key as invalid (Key has expired)'
        #
        # I've never seen an example of an error from this API that doesn't
        # follow this pattern, but we have a branch to handle it just in case.
        # Add a test if you find an example!
        m = re.match(r"^Invalid API Key \((?P<explanation>[^\)]+)\)$", message)

        if m is None:  # pragma: no cover
            explanation = message
        else:
            explanation = m.group("explanation")

        super().__init__(f"Flickr API rejected the API key as invalid ({explanation})")


class ResourceNotFound(FlickrApiException):
    """
    Thrown when you try to look up a resource that doesn't exist.
    """

    pass


class UserDeleted(ResourceNotFound):
    """
    Thrown when you try to look up a user who's deleted their account.
    """

    def __init__(self, user_id: str):
        super().__init__(f"User is deleted: {user_id!r}")


class PhotoIsPrivate(FlickrApiException):
    """
    Thrown when you try to look up a photo which is private.
    """

    def __init__(self, photo_id: str):
        super().__init__(f"Photo is private: {photo_id}")


class LicenseNotFound(FlickrApiException):
    """
    Thrown when you try to look up a license ID, but there's no such license.
    """

    def __init__(self, license_id: str):
        super().__init__(f"Unable to find license with ID {license_id}")


class InsufficientPermissionsToComment(FlickrApiException):
    """
    Thrown when you try to comment on a photo, but you're not allowed to.
    """

    def __init__(self, *, photo_id: str) -> None:
        super().__init__(f"Insufficient permissions to comment on photo {photo_id}")


class PermissionDenied(FlickrApiException):
    """
    Thrown when you try to look up something you're not allowed to access.
    """
