"""
Tests for ``flickr_photos_api.types.machine_tags``.
"""

from flickr_photos_api.types import get_machine_tags


def test_empty_tags_is_empty_machine_tags() -> None:
    """
    If there are no tags, there are no machine tags.
    """
    assert get_machine_tags(tags=[]) == {}


def test_keyword_tags_are_not_machine_tags() -> None:
    """
    If all the tags are "keywords" (unstructured text) then there
    are no machine tags.
    """
    tags = ["Natural history", "Periodicals", "Physical sciences"]
    assert get_machine_tags(tags) == {}


def test_get_single_machine_tag() -> None:
    """
    If some tags are machine tags and some aren't, only the machine tags
    are returned.
    """
    tags = [
        "Natural history",
        "Periodicals",
        "Physical sciences",
        "bhl:page=33665645",
    ]
    assert get_machine_tags(tags) == {"bhl:page": ["33665645"]}


def test_get_repeated_namespace_predicate() -> None:
    """
    If there are multiple machine tags with the same namespace/predicate,
    they're grouped together.
    """
    tags = [
        "Natural history",
        "Periodicals",
        "Physical sciences",
        "bhl:page=33665645",
        "taxonomy:genus=Loxodonta",
        "taxonomy:binomial=Elephas maximus",
        "taxonomy:binomial=Elephas indicus",
    ]
    machine_tags = {
        "bhl:page": ["33665645"],
        "taxonomy:genus": ["Loxodonta"],
        "taxonomy:binomial": ["Elephas maximus", "Elephas indicus"],
    }

    assert get_machine_tags(tags) == machine_tags
