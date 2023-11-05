import datetime
from typing import Dict, Optional
import xml.etree.ElementTree as ET

from ._types import SafetyLevel


def find_required_elem(elem: ET.Element, *, path: str) -> ET.Element:
    """
    Find the first subelement matching ``path``, or throw if absent.
    """
    # We use this when we're parsing responses from the Flickr API, and
    # there are certain elements we know should always be present in responses.
    #
    # e.g. we know that photos always have a <title>, so we could write:
    #
    #     photo_elem.find(".//title")
    #
    # But the type checker only knows that ``find()`` returns Optional[Element] --
    # it doesn't know that this path should always be present in the response.
    #
    # If we call it from this function instead:
    #
    #     find_required(photo_elem, path=".//title")
    #
    # Then the type checker can see that it returns a well-defined Element,
    # and it's happy for us to use it without checking in the rest of the code.
    matching_elem = elem.find(path=path)

    if matching_elem is None:
        raise ValueError(f"Could not find required match for {path!r} in {elem!r}")

    return matching_elem


def find_required_text(elem: ET.Element, *, path: str) -> str:
    """
    Find the text of the first element matching ``path``, or throw if absent.
    """
    # We use this when we're parsing responses from the Flickr API, and
    # there are certain elements we know should always be present and have text.
    #
    # e.g. we know that users always have a <id> with some text, so we could write:
    #
    #     user_elem.find(".//id")
    #
    # But the type checker only knows that ``find()`` returns Optional[Element] --
    # it doesn't know that this path should always be present in the response.
    #
    # If we call it from this function instead:
    #
    #     find_required_text(user_elem, path=".//id")
    #
    # Then the type checker can see that it returns a well-defined Element,
    # and it's happy for us to use it without checking in the rest of the code.
    matching_elem = find_required_elem(elem, path=path)
    text = matching_elem.text

    if text is None:
        raise ValueError(f"Could not find required text in {matching_elem}")

    return text


def find_optional_text(elem: ET.Element, *, path: str) -> Optional[str]:
    """
    Find the text of the first element matching ``path``, or return None
    if the element is missing, has no text, or has empty text.
    """
    matching_elem = elem.find(path=path)

    if matching_elem is None:
        return None

    return matching_elem.text or None


def parse_date_posted(p: str) -> datetime.datetime:
    # See https://www.flickr.com/services/api/misc.dates.html
    #
    #     The posted date is always passed around as a unix timestamp,
    #     which is an unsigned integer specifying the number of seconds
    #     since Jan 1st 1970 GMT.
    #
    # e.g. '1490376472'
    return datetime.datetime.fromtimestamp(int(p), tz=datetime.timezone.utc)


def parse_date_taken(p: str) -> datetime.datetime:
    # See https://www.flickr.com/services/api/misc.dates.html
    #
    #     The date taken should always be displayed in the timezone
    #     of the photo owner, which is to say, don't perform
    #     any conversion on it.
    #
    # e.g. '2017-02-17 00:00:00'
    return datetime.datetime.strptime(p, "%Y-%m-%d %H:%M:%S")


def to_safety_level(s: str) -> SafetyLevel:
    """
    Converts a numeric safety level ID in the Flickr API into
    a human-readable string.

    See https://www.flickrhelp.com/hc/en-us/articles/4404064206996-Content-filters
    """
    lookup_table: Dict[str, SafetyLevel] = {
        "0": "safe",
        "1": "moderate",
        "2": "restricted",
    }

    try:
        return lookup_table[s]
    except KeyError:
        raise ValueError(f"Unrecognised safety level: {s}")
