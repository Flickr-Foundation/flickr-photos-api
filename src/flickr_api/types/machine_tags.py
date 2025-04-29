"""
On Flickr, machine tag are used to store structured data in types,
e.g. ``geo:lat=12.34`` is a tag with location information.

This file has a few functions for dealing with machine tags.
"""

import collections
import re
import typing


# The best documentation I can find for Flickr's implementation of
# machine tags is a group post from a Flickr staff member in 2007:
# https://www.flickr.com/groups/51035612836@N01/discuss/72157594497877875/
#
# A machine tag is made of three parts:
#
#     {namespace}:{predicate}={value}
#
# The ``namespace`` and ``predicate`` can only contain ASCII characters.
MACHINE_TAG_RE = re.compile(
    r"""
    ^
    (?P<namespace>[a-zA-Z0-9_]+)
    :
    (?P<predicate>[a-zA-Z0-9_]+)
    =
    (?P<value>.+)
    $
    """,
    re.VERBOSE,
)


MachineTags: typing.TypeAlias = dict[str, list[str]]


def get_machine_tags(tags: list[str]) -> MachineTags:
    """
    Given a list of raw tags on Flickr, parse the machine tags
    as key-value pairs.

    The keys are namespace/predicate; the values are values.

    Example:

        >>> tags = [
        ...     "square",
        ...     "shape:sides=4",
        ...     "shape:color=red",
        ...     "shape:color=blue"
        ... ]
        ...
        >>> get_machine_tags(tags)
        {"shape:sides": ["4"], "shape:color": ["red", "blue"]}

    This function is a "best effort" parsing of machine tags -- it may
    not match Flickr perfectly, but is meant to make it easier for
    callers to work with machine tags.
    """
    result: MachineTags = collections.defaultdict(list)

    for t in tags:
        if m := MACHINE_TAG_RE.match(t):
            namespace = m.group("namespace")
            predicate = m.group("predicate")
            value = m.group("value")

            result[f"{namespace}:{predicate}"].append(value)

    return dict(result)
