import os
import typing

import keyring
import keyring.errors
from nitrate.json import DatetimeDecoder
from nitrate.types import read_typed_json

T = typing.TypeVar("T")


def get_fixture(filename: str, *, model: type[T]) -> T:
    return read_typed_json(
        os.path.join("tests/fixtures/api_responses", filename),
        model=model,
        cls=DatetimeDecoder,
    )


def get_optional_password(username: str, password: str, *, default: str) -> str:
    """
    Get a password from the system keychain, or a default if unavailable.
    """
    try:
        return keyring.get_password(username, password) or default
    except keyring.errors.NoKeyringError:  # pragma: no cover
        return default
