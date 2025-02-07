"""
Utility functions for use in the test suite.

These functions are *not* part of the published library, and are
just for use in the flickr-photos-api tests.
"""

from pathlib import Path
import typing

from nitrate.json import NitrateDecoder
from nitrate.types import read_typed_json

T = typing.TypeVar("T")


def get_fixture(filename: str, *, model: type[T]) -> T:
    """
    Read a JSON fixture and check it's the right type.
    """
    fixtures_dir = Path("tests/fixtures/api_responses")

    return read_typed_json(
        fixtures_dir / filename,
        model=model,
        cls=NitrateDecoder,
    )
