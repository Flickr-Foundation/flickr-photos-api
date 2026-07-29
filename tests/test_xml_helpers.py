"""
Tests for ``flickr_api.xml_helpers``.
"""

from xml.etree import ElementTree as ET

from flickr_api.xml_helpers import (
    attrib_flag,
    attrib_str,
    parse_media_type,
    sanitize_xml_text,
)


def test_sanitize_xml_text_strips_illegal_control_characters() -> None:
    """Illegal XML control characters are removed from Flickr response text."""
    assert sanitize_xml_text("hello\x14world") == "helloworld"


def test_attrib_str_uses_default_for_missing_attribute() -> None:
    """Missing attributes fall back to the provided default value."""
    elem = ET.fromstring('<photo id="123" />')

    assert attrib_str(elem, "missing", default="fallback") == "fallback"


def test_attrib_flag_parses_flickr_boolean() -> None:
    """Flickr boolean attributes are parsed as Python booleans."""
    elem = ET.fromstring('<usage candownload="1" />')

    assert attrib_flag(elem, "candownload") is True
    assert attrib_flag(elem, "canprint") is False


def test_parse_media_type_defaults_unknown_values_to_photo() -> None:
    """Unknown media types default to ``photo``."""
    assert parse_media_type("gif") == "photo"
    assert parse_media_type("video") == "video"
