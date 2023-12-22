import re


class FlickrApiException(Exception):
    """
    Base class for all exceptions thrown from the Flickr API.
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

    def __init__(self, method: str, params: dict[str, str] | None):
        super().__init__(
            f"Unable to find resource at {method} with properties {params}"
        )


class LicenseNotFound(FlickrApiException):
    def __init__(self, license_id: str):
        super().__init__(f"Unable to find license with ID {license_id}")
