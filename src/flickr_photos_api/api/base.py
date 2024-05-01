import abc
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
        method: str,
        params: dict[str, str] | None = None,
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
        return NotImplemented


def is_retryable(exc: BaseException) -> bool:
    """
    Returns True if this is an exception we can safely retry (i.e. flaky
    or transient errors that might return a different result),or
    False otherwise.
    """
    if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code == 500:
        return True

    if isinstance(exc, httpx.ReadTimeout):
        return True

    if isinstance(exc, InvalidXmlException):
        return True

    # Sometimes we get an error from the Flickr API like:
    #
    #     <err
    #       code="201"
    #       msg="Sorry, the Flickr API service is not currently available."
    #     />
    #
    # but this indicates a flaky connection rather than a genuine failure.
    if (
        isinstance(exc, UnrecognisedFlickrApiException)
        and isinstance(exc.args[0], dict)
        and exc.args[0].get("code") == "201"
    ):
        return True

    return False


class HttpxImplementation(FlickrApi):
    """
    An implementation of the Flickr API that uses ``httpx`` to make HTTP calls,
    and ``tenacity`` for retrying failed API calls.
    """

    def __init__(self, *, api_key: str, user_agent: str) -> None:
        if not api_key:
            raise ValueError(
                "Cannot create a client with an empty string as the API key"
            )

        self.client = httpx.Client(
            base_url="https://api.flickr.com/services/rest/",
            params={"api_key": api_key},
            headers={"User-Agent": user_agent},
        )

    def call(
        self,
        *,
        method: str,
        params: dict[str, str] | None = None,
        exceptions: dict[str, Exception] | None = None,
    ) -> ET.Element:
        try:
            return self._call_api(
                method=method, params=params, exceptions=exceptions or {}
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
        method: str,
        params: dict[str, str] | None,
        exceptions: dict[str, Exception],
    ) -> ET.Element:
        if params is not None:
            get_params = {"method": method, **params}
        else:
            get_params = {"method": method}

        resp = self.client.get(url="", params=get_params, timeout=15)
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
                raise UnrecognisedFlickrApiException(errors)

        return xml
