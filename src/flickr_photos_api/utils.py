import xml.etree.ElementTree as ET


def find_required_elem(elem: ET.Element, *, path: str) -> ET.Element:
    """
    Find the first subelement matching ``match``, or throw if absent.

    We use this when we're parsing responses from the Flickr API, and
    there are certain elements we know should always be present in responses.
    It helps us write type-checked code.

    e.g. we know that photos always have a <title>, so we'd normally write:

        photo_elem.find(".//title")

    mypy can't tell that we always expect this to find a matching element,
    so it thinks the return value is Optional[Element].

    But we know it should be Element, so we wrap it in this call:

        find_required(photo_elem, match=".//title")

    which mypy can see always returns an Element.

    """
    matching_elem = elem.find(path=path)

    if matching_elem is None:
        raise ValueError(f"Could not find required match for {path!r} in {elem!r}")

    return matching_elem


def find_required_text(elem: ET.Element, *, path: str) -> str:
    """
    Find the text of the first element matching ``match``, or throw if absent.
    """
    matching_elem = find_required_elem(elem, path=path)
    text = matching_elem.text

    if text is None:
        raise ValueError(f"Could not find required text in {matching_elem}")

    return text
