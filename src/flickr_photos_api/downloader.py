"""
Functions for actually downloading a photo -- you get the URL from
the Flickr API, then download the image itself here.
"""

import pathlib
import uuid

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception


def is_retryable(exc: BaseException) -> bool:
    """
    Returns True if this is an exception we can safely retry (i.e. flaky
    or transient errors that might return a different result),or
    False otherwise.
    """
    if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code in {
        403,
        429,
    }:
        return True  # pragma: no cover

    if isinstance(exc, httpx.RemoteProtocolError):
        return True  # pragma: no cover

    # We can retry a download if it timed out.
    #
    # There's no easy way to simulate this in tests, so we just don't
    # test this branch -- but it's simple enough not to be a big issue.
    if isinstance(exc, httpx.ReadTimeout):  # pragma: no cover
        return True

    return False


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception(is_retryable),
)
def download_photo(url: str, out_path: pathlib.Path) -> None:
    """
    Download a photo from Flickr.com.

    This function will retry the download a certain number of times
    if it fails, e.g. if Flickr returns an error or if the download
    is rate-limited.
    """
    out_path.parent.mkdir(exist_ok=True, parents=True)

    tmp_path = out_path.with_suffix(f".{uuid.uuid4()}.tmp")

    # We use a streaming response from HTTPX because some Flickr files
    # can be very big, e.g. original video files.  We don't need or
    # want to buffer the whole thing into memory.
    with httpx.stream("GET", url) as resp:
        resp.raise_for_status()

        with open(tmp_path, "xb") as out_file:
            for data in resp.iter_bytes():
                out_file.write(data)

    tmp_path.rename(out_path)
