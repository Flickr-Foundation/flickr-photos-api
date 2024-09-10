"""
Utility functions for use in the test suite.

These functions are *not* part of the published library, and are
just for use in the flickr-photos-api tests.
"""

import os
import typing

from nitrate.json import DatetimeDecoder
from nitrate.types import read_typed_json

T = typing.TypeVar("T")


def get_fixture(filename: str, *, model: type[T]) -> T:
    """
    Read a JSON fixture and check it's the right type.
    """
    return read_typed_json(
        os.path.join("tests/fixtures/api_responses", filename),
        model=model,
        cls=DatetimeDecoder,
    )
