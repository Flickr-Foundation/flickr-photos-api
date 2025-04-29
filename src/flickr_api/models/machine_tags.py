"""
On Flickr, machine tag are used to store structured data in types,
e.g. ``geo:lat=12.34`` is a tag with location information.
"""

import typing


MachineTags: typing.TypeAlias = dict[str, list[str]]
