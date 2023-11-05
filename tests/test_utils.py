import xml.etree.ElementTree as ET

import pytest

from flickr_photos_api.utils import find_required_elem, find_required_text


XML = ET.fromstring(
    """
    <?xml version="1.0" encoding="utf-8" ?>
    <greeting>
        <english>Hello world</english>
        <french/>
    </greeting>""".strip()
)


def test_find_required_elem() -> None:
    english = find_required_elem(XML, path=".//english")
    assert english is not None
    assert english.text == "Hello world"


def test_find_required_elem_throws_if_cannot_find_element() -> None:
    with pytest.raises(ValueError, match="Could not find required match"):
        find_required_elem(XML, path=".//german")


def test_find_required_text() -> None:
    assert find_required_text(XML, path=".//english") == "Hello world"


def test_find_required_text_throws_if_finds_element_without_text() -> None:
    with pytest.raises(ValueError, match="Could not find required text"):
        find_required_text(XML, path=".//french")


def test_find_required_text_throws_if_cannot_find_element() -> None:
    with pytest.raises(ValueError, match="Could not find required match"):
        find_required_text(XML, path=".//german")
