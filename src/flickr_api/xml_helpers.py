"""
Helpers for parsing Flickr API XML responses leniently.
"""

import logging
from xml.etree import ElementTree as ET

from .models import MediaType

logger = logging.getLogger(__name__)

__all__ = [
    "attrib_flag",
    "attrib_str",
    "parse_media_type",
    "sanitize_xml_text",
]


def _is_xml_char_allowed(code: int) -> bool:
    """Return True if a Unicode code point is legal in XML 1.0 text content."""
    return code in (0x9, 0xA, 0xD) or 0x20 <= code <= 0xD7FF or 0xE000 <= code <= 0xFFFD


def sanitize_xml_text(text: str) -> str:
    """
    Strip characters Flickr sometimes embeds in responses that break XML 1.0 parsing.
    """
    return "".join(char for char in text if _is_xml_char_allowed(ord(char)))


def attrib_str(elem: ET.Element, key: str, *, default: str = "") -> str:
    """
    Read a string attribute from an XML element, using a default when missing.
    """
    if key in elem.attrib:
        return elem.attrib[key]
    logger.warning(
        "Missing XML attribute %r on <%s>; defaulting to %r",
        key,
        elem.tag,
        default,
    )
    return default


def attrib_flag(elem: ET.Element, key: str, *, default: str = "0") -> bool:
    """
    Read a Flickr 0/1 flag attribute, using a default when missing.
    """
    return attrib_str(elem, key, default=default) == "1"


def parse_media_type(raw: str) -> MediaType:
    """
    Parse the ``media`` attribute on a photo, defaulting unknown values to ``photo``.
    """
    if raw in {"photo", "video"}:
        return raw  # type: ignore[return-value]
    logger.warning("Unrecognised media type %r; defaulting to 'photo'", raw)
    return "photo"
