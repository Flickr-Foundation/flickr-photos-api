import sys
from typing import Optional

# See https://mypy.readthedocs.io/en/stable/runtime_troubles.html#using-new-additions-to-the-typing-module
# See https://github.com/python/mypy/issues/8520
if sys.version_info >= (3, 8):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict


class License(TypedDict):
    id: str
    label: str
    url: Optional[str]
