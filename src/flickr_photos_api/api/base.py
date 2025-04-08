"""
Base classes for the Flickr API client.
"""

import abc
from collections.abc import Mapping
import typing
from xml.etree import ElementTree as ET

import httpx
from nitrate.xml import find_required_elem
from tenacity import (
    retry,
    retry_if_exception,
    RetryError,
    stop_after_attempt,
    wait_random_exponential,
)

from ..exceptions import (
    InvalidApiKey,
    InvalidXmlException,
    UnrecognisedFlickrApiException,
)


HttpMethod = typing.Literal["GET", "POST"]


class FlickrApi(abc.ABC):
    """
    This is a basic model for Flickr API implementations: they have to provide
    a ``call()`` method that takes a Flickr API method and parameters, and returns
    the parsed XML.

    We deliberately split out the interface and implementation here -- currently
    we use httpx and tenacity, but this abstraction would allow us to swap out
    the underlying HTTP framework easily if we wanted to.
    """

    @abc.abstractmethod
    def call(
        self,
        *,
        http_method: HttpMethod = "GET",
        method: str,
        params: Mapping[str, str | int] | None = None,
        exceptions: dict[str, Exception] | None = None,
    ) -> ET.Element:
        """
        Call the Flickr API and return the XML of the result.

        :param method: The name of the Flickr API method, for example
            ``flickr.photos.getInfo``

        :param params: Any arguments to pass to the Flickr API method,
            for example ``{"photo_id": "1234"}``

        :param exceptions: A map from Flickr API error code to exceptions that should
            be thrown.
        """
        raise NotImplementedError


def is_retryable(exc: BaseException) -> bool:
    """
    Returns True if this is an exception we can safely retry (i.e. flaky
    or transient errors that might return a different result),or
    False otherwise.
    """
    if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code >= 500:
        return True

    if isinstance(exc, httpx.ReadTimeout):
        return True

    if isinstance(exc, InvalidXmlException):
        return True

    # These are a particular set of slightly flaky errors that are hard
    # to reproduce -- relying on matching the text of the error is a bit
    # fragile, but that's all we get from httpx.
    if isinstance(exc, (httpx.ReadError, httpx.ConnectError)) and exc.args == (
        "[Errno 54] Connection reset by peer",
    ):
        return True

    if isinstance(exc, httpx.RemoteProtocolError) and exc.args == (
        "Server disconnected without sending a response.",
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


class HttpxImplementation(FlickrApi):
    """
    An implementation of the Flickr API that uses ``httpx`` to make HTTP calls,
    and ``tenacity`` for retrying failed API calls.
    """

    def __init__(self, *, client: httpx.Client) -> None:
        """
        Create an API from an ``httpx`` client.

        This is useful if you want to customise the behaviour of the
        underlying client.
        """
        client.base_url = httpx.URL("https://api.flickr.com/services/rest/")
        self.client = client

    @classmethod
    def with_api_key(cls, *, api_key: str, user_agent: str) -> typing.Self:
        """
        Create a client from a Flickr API key.

        This also requires a User-Agent, which is a recommended good
        practice with the Flickr API (tho not required).
        """
        if not api_key:
            raise ValueError(
                "Cannot create a client with an empty string as the API key"
            )

        client = httpx.Client(
            params={"api_key": api_key},
            headers={"User-Agent": user_agent},
        )

        return cls(client=client)

    def call(
        self,
        *,
        http_method: HttpMethod = "GET",
        method: str,
        params: Mapping[str, str | int] | None = None,
        exceptions: dict[str, Exception] | None = None,
    ) -> ET.Element:
        """
        Call the Flickr API and return the XML of the result.

        :param method: The name of the Flickr API method, for example
            ``flickr.photos.getInfo``

        :param params: Any arguments to pass to the Flickr API method,
            for example ``{"photo_id": "1234"}``

        :param exceptions: A map from Flickr API error code to exceptions that should
            be thrown.
        """
        try:
            return self._call_api(
                http_method=http_method,
                method=method,
                params=params,
                exceptions=exceptions or {},
            )
        except RetryError as retry_err:
            retry_err.reraise()

    @retry(
        retry=retry_if_exception(is_retryable),
        stop=stop_after_attempt(5),
        wait=wait_random_exponential(),
    )
    def _call_api(
        self,
        *,
        http_method: HttpMethod,
        method: str,
        params: Mapping[str, str | int] | None,
        exceptions: dict[str, Exception],
    ) -> ET.Element:
        """
        Call the Flickr API and return the XML of the result.

        This function may be retried if the Flickr API returns an error
        that we think is retryable, e.g. if it returns
        a 500 Internal Server Erorr.
        """
        if params is not None:
            req_params = {"method": method, **params}
        else:
            req_params = {"method": method}

        resp = self.client.request(
            method=http_method, url="", params=req_params, timeout=15
        )
        resp.raise_for_status()

        # Note: the xml.etree.ElementTree is not secure against maliciously
        # constructed data (see warning in the Python docs [1]), but that's
        # fine here -- we're only using it for responses from the Flickr API,
        # which we trust.
        #
        # However, on occasion I have seen it return error messages in
        # JSON rather than XML, which causes this method to fail -- make
        # sure we log the offending text, and allow it to be retried as
        # a temporary failure.
        #
        # [1]: https://docs.python.org/3/library/xml.etree.elementtree.html
        try:
            xml = ET.fromstring(resp.text)
        except ET.ParseError as err:
            raise InvalidXmlException(
                f"Unable to parse response as XML ({resp.text!r}), got error {err}"
            )

        # If the Flickr API call fails, it will return a block of XML like:
        #
        #       <rsp stat="fail">
        #       	<err
        #               code="1"
        #               msg="Photo &quot;1211111111111111&quot; not found (invalid ID)"
        #           />
        #       </rsp>
        #
        # Different API endpoints have different codes, and so we just throw
        # and let calling functions decide how to handle it.
        if xml.attrib["stat"] == "fail":
            errors = find_required_elem(xml, path=".//err").attrib

            if errors["code"] == "100":
                raise InvalidApiKey(message=errors["msg"])

            try:
                raise exceptions[errors["code"]]
            except KeyError:
                # Note: the `from None` means we don't include the KeyError in
                # the traceback -- this is to avoid exposing internal details
                # of the library to external callers.
                raise UnrecognisedFlickrApiException(errors) from None

        return xml
