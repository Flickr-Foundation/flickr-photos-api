"""
When we call the Flickr API, sometimes the HTTP call fails with a retryable error.
For example:

*   An HTTP 500 Internal Server Error response
*   An HTTP 429 Too Many Requests response
*   A connection timeout or failure

In these cases, we can safely retry the request after a short delay and we
should get a successful response.

However, we don't want to retry all errors. For example, an HTTP 404 Not Found
is a permanent error that we should fail immediately, and not retry.

This file contains a function for deciding if a particular error can be retried,
or if we should give up immediately.
"""

import httpx

from .exceptions import InvalidXmlException, UnrecognisedFlickrApiException


__all__ = ["is_retryable"]


def is_retryable(exc: BaseException) -> bool:
    """
    Returns True if this is an exception we can safely retry (i.e. flaky
    or transient errors that might return a different result), or
    False otherwise.
    """
    if isinstance(exc, httpx.HTTPStatusError):
        if exc.response.status_code == 429 or exc.response.status_code >= 500:
            return True

    if isinstance(
        exc,
        (
            httpx.ConnectError,
            httpx.ConnectTimeout,
            httpx.ReadError,
            httpx.ReadTimeout,
            httpx.RemoteProtocolError,
            InvalidXmlException,
        ),
    ):
        return True

    # Sometimes we get an error from the Flickr API like:
    #
    #     <err
    #       code="201"
    #       msg="Sorry, the Flickr API service is not currently available."
    #     />
    #
    # but this indicates a flaky connection rather than a genuine failure.
    #
    # We've seen similar with code "0", so we match on the error message
    # rather than the code.
    if (
        isinstance(exc, UnrecognisedFlickrApiException)
        and isinstance(exc.args[0], dict)
        and exc.args[0].get("msg")
        == "Sorry, the Flickr API service is not currently available."
    ):
        return True

    return False
