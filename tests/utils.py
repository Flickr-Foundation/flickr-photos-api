import os
import typing

from nitrate.json import DatetimeDecoder
from nitrate.types import read_typed_json

T = typing.TypeVar("T")


def get_fixture(filename: str, *, model: type[T]) -> T:
    return read_typed_json(
        os.path.join("tests/fixtures/api_responses", filename),
        model=model,
        cls=DatetimeDecoder,
    )
