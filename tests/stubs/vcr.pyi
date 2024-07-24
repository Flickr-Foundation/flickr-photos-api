import contextlib
import typing

def use_cassette(
    cassette_name: str,
    cassette_library_dir: str,
    filter_query_parameters: list[str],
    decode_compressed_response: typing.Literal[True],
) -> contextlib.AbstractContextManager[None]: ...
