import contextlib
import typing

def use_cassette(
    cassette_name: str,
    cassette_library_dir: str,
    decode_compressed_response: typing.Literal[True],
    filter_query_parameters: list[str] | None = None,
) -> contextlib.AbstractContextManager[None]: ...
