"""
Tests for `flickr_api.parsers`.
"""

import pytest

from flickr_api.parsers import parse_date_taken, parse_machine_tags, parse_safety_level


def test_unrecognised_date_granularity_is_error() -> None:
    """
    If you pass an unrecognised date taken granularity,
    it throws ``ValueError``.
    """
    with pytest.raises(ValueError, match="Unrecognised date granularity"):
        parse_date_taken(value="2017-02-17 00:00:00", granularity="-1", unknown=False)


def test_unrecognised_safety_level_is_error() -> None:
    """
    Parsing an unrecognised value as a safety level throws ``ValueError``.
    """
    with pytest.raises(ValueError, match="Unrecognised safety level"):
        parse_safety_level("-1")


class TestParseMachine_Tags:
    """
    Tests for `parse_machine_tags`.
    """

    def test_empty_tags_is_empty_machine_tags(self) -> None:
        """
        If there are no tags, there are no machine tags.
        """
        assert parse_machine_tags(tags=[]) == {}

    def test_keyword_tags_are_not_machine_tags(self) -> None:
        """
        If all the tags are "keywords" (unstructured text) then there
        are no machine tags.
        """
        tags = ["Natural history", "Periodicals", "Physical sciences"]
        assert parse_machine_tags(tags) == {}

    def test_get_single_machine_tag(self) -> None:
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
        assert parse_machine_tags(tags) == {"bhl:page": ["33665645"]}
