"""
Convert values retrieved from the Flickr API into nicely-typed values.
"""

from xml.etree import ElementTree as ET

from .types import LocationInfo, SafetyLevel


def parse_safety_level(s: str) -> SafetyLevel:
    """
    Converts a numeric safety level ID in the Flickr API into
    a human-readable value.

    See https://www.flickrhelp.com/hc/en-us/articles/4404064206996-Content-filters
    """
    lookup_table: dict[str, SafetyLevel] = {
        "0": "safe",
        "1": "moderate",
        "2": "restricted",
    }

    try:
        return lookup_table[s]
    except KeyError:
        raise ValueError(f"Unrecognised safety level: {s}")


def parse_location(elem_with_location: ET.Element) -> LocationInfo | None:
    """
    Get location information about a photo.

    This takes an XML element with latitude/longitude/accuracy attributes;
    this can be a <location> element (on a single photo) or a <photo> element
    (on collection responses).
    """
    # The accuracy parameter in the Flickr API response tells us
    # the precision of the location information (15 November 2023):
    #
    #     Recorded accuracy level of the location information.
    #     World level is 1, Country is ~3, Region ~6, City ~11, Street ~16.
    #     Current range is 1-16.
    #
    # But some photos have an accuracy of 0!  It's unclear what this
    # means or how we should map this -- lower numbers mean less accurate,
    # so this location information might be completely useless.
    #
    # Discard it rather than risk propagating bad data.
    if elem_with_location.attrib["accuracy"] == "0":
        return None

    return {
        "latitude": float(elem_with_location.attrib["latitude"]),
        "longitude": float(elem_with_location.attrib["longitude"]),
        "accuracy": int(elem_with_location.attrib["accuracy"]),
    }
