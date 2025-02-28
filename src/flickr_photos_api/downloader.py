"""
Functions for actually downloading a photo -- you get the URL from
the Flickr API, then download the image itself here.
"""

from pathlib import Path
import typing
import uuid

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception


default_client = httpx.Client(headers={"User-Agent": "flickr-photos-api"})


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
    if isinstance(
        exc, (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout)
    ):  # pragma: no cover
        return True

    return False


class DownloadedFile(typing.TypedDict):
    """
    Represents a downloaded file.
    """

    path: Path
    content_type: str


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception(is_retryable),
)
def download_file(
    client: httpx.Client = default_client,
    *,
    url: str,
    download_dir: Path,
    base_name: str,
) -> DownloadedFile:
    """
    Download a file from Flickr.com.

    This function will retry the download a certain number of times
    if it fails, e.g. if Flickr returns an error or if the download
    is rate-limited.
    """
    download_dir.mkdir(exist_ok=True, parents=True)

    download_path = download_dir / base_name

    # We use a streaming response from HTTPX because some Flickr files
    # can be very big, e.g. original video files.  We don't need or
    # want to buffer the whole thing into memory.
    tmp_path = download_path.with_suffix(f".{uuid.uuid4()}.tmp")

    with client.stream("GET", url, follow_redirects=True) as resp:
        resp.raise_for_status()

        with open(tmp_path, "xb") as out_file:
            for data in resp.iter_bytes():
                out_file.write(data)

    # Now work out the correct file extension to use for this content type.
    #
    # If we can't work out a good file extension, leave it blank.
    content_type = resp.headers["content-type"]

    try:
        file_suffix = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/gif": ".gif",
            "video/mp4": ".mp4",
        }[content_type]

        out_path = download_path.with_suffix(file_suffix)
    except KeyError:
        out_path = download_path

    # Rename the temporarily downloaded file to the final file.
    tmp_path.rename(out_path)

    return {"path": out_path, "content_type": content_type}
