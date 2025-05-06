"""
Convert values from the Flickr API into nicely-typed values.
"""

import collections
from datetime import datetime, timezone
import re
import typing
from xml.etree import ElementTree as ET

from nitrate.xml import find_optional_text

from .models import (
    DateTaken,
    LocationContext,
    MachineTags,
    NumericLocation,
    NamedLocation,
    Rotation,
    SafetyLevel,
    TakenGranularity,
    User,
)


__all__ = [
    "create_user",
    "fix_realname",
    "parse_date_taken",
    "parse_machine_tags",
    "parse_numeric_location",
    "parse_named_location",
    "parse_safety_level",
    "parse_timestamp",
]


def parse_timestamp(ts: str, /) -> datetime:
    """
    Convert a Unix timestamp into a Python-native ``datetime``.

    Example:

        >>> parse_timestamp('1490376472')
        datetime(2017, 3, 24, 17, 27, 52, tzinfo=timezone.utc)

    The Flickr API frequently returns dates as Unix timestamps, for example:

    *   When you call ``flickr.photos.getInfo``, the ``<dates>`` element
        includes the upload and last update dates as a timestamp
    *   When you call ``flickr.people.getInfo`` for a user with Flickr Pro,
        the ``expires`` attribute is a numeric timestamp.

    In this case a Unix timestamp is "an unsigned integer specifying
    the number of seconds since Jan 1st 1970 GMT" [1].

    [1] https://www.flickr.com/services/api/misc.dates.html
    """
    return datetime.fromtimestamp(int(ts), tz=timezone.utc)


def _parse_date_taken_value(dt: str) -> datetime:
    """
    Convert a "date taken" string to a Python-native ``datetime``.

    Example:

        >>> _parse_date_taken_value('2017-02-17 00:00:00')
        datetime(2017, 2, 17, 0, 0)

    """
    # See https://www.flickr.com/services/api/misc.dates.html
    #
    #     The date taken should always be displayed in the timezone
    #     of the photo owner, which is to say, don't perform
    #     any conversion on it.
    #
    return datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")


def _parse_date_taken_granularity(g: str) -> TakenGranularity:
    """
    Converts a numeric granularity level in the Flickr API into a
    human-readable value.

    See https://www.flickr.com/services/api/misc.dates.html
    """
    lookup_table: dict[str, TakenGranularity] = {
        "0": "second",
        "4": "month",
        "6": "year",
        "8": "circa",
    }

    try:
        return lookup_table[g]
    except KeyError:
        raise ValueError(f"Unrecognised date granularity: {g}")


def parse_date_taken(
    *, value: str, granularity: str, unknown: bool
) -> DateTaken | None:
    """
    Parse a "date taken" value from the Flickr API.

    When you retrieve a photo with ``flickr.photos.getInfo``, the taken
    value is made of several parts:

        <dates … takengranularity="0" takenunknown="1" lastupdate="1705439827"/>

    This function converts these parts into nicely-typed objects.  This
    may be ``None`` if the date taken is unknown.
    """
    # We intentionally omit sending any 'date taken' information
    # to callers if it's unknown.
    #
    # There will be a value in the API response, but if the taken date
    # is unknown, it's defaulted to the date the photo was posted.
    # See https://www.flickr.com/services/api/misc.dates.html
    #
    # This value isn't helpful to callers, so we omit it.  This reduces
    # the risk of somebody skipping the ``unknown`` parameter and using
    # the value in the wrong place.
    if unknown:
        return None

    # This is a weird value I've seen returned on some videos; I'm
    # not sure what it means, but it's not something we can interpret
    # as a valid date, so we treat "date taken" as unknown even if
    # the API thinks it knows it.
    elif value.startswith("0000-"):
        return None

    else:
        return {
            "value": _parse_date_taken_value(value),
            "granularity": _parse_date_taken_granularity(granularity),
        }


def parse_safety_level(s: str) -> SafetyLevel:
    """
    Converts a numeric safety level ID in the Flickr API into
    a human-readable value.

    See https://www.flickrhelp.com/hc/en-us/articles/4404064206996-Content-filters
    """
    lookup_table: dict[str, SafetyLevel] = {
        "0": "safe",
        "1": "moderate",
        "2": "restricted",
    }

    try:
        return lookup_table[s]
    except KeyError:
        raise ValueError(f"Unrecognised safety level: {s}")


def parse_numeric_location(elem_with_location: ET.Element) -> NumericLocation | None:
    """
    Get location information about a photo.

    This takes an XML element with latitude/longitude/accuracy attributes;
    this can be a <location> element (on a single photo) or a <photo> element
    (on collection responses).
    """
    # The accuracy parameter in the Flickr API response tells us
    # the precision of the location information (15 November 2023):
    #
    #     Recorded accuracy level of the location information.
    #     World level is 1, Country is ~3, Region ~6, City ~11, Street ~16.
    #     Current range is 1-16.
    #
    # But some photos have an accuracy of 0!  It's unclear what this
    # means or how we should map this -- lower numbers mean less accurate,
    # so this location information might be completely useless.
    #
    # Discard it rather than risk propagating bad data.
    if elem_with_location.attrib["accuracy"] == "0":
        return None

    return {
        "latitude": float(elem_with_location.attrib["latitude"]),
        "longitude": float(elem_with_location.attrib["longitude"]),
        "accuracy": int(elem_with_location.attrib["accuracy"]),
    }


def parse_named_location(location_elem: ET.Element) -> NamedLocation:
    """
    Get named location information about a photo.
    """
    # The context tells us whether the photo is indoors or outdoors.
    # See https://www.flickr.com/services/api/flickr.photos.geo.setLocation.html
    context_lookup: dict[str, LocationContext | None] = {
        "0": None,
        "1": "indoors",
        "2": "outdoors",
    }

    try:
        context = context_lookup[location_elem.attrib["context"]]
    except KeyError:  # pragma: no cover
        raise ValueError(
            f"Unrecognised location conext: {location_elem.attrib['context']}"
        )

    # On responses form the `flickr.photos.getInfo` endpoint, the
    # <location> element will be of the form:
    #
    #     <location latitude="9.135158" longitude="40.083811" accuracy="16" context="0">
    #       <locality>Galoch</locality>
    #       <neighbourhood/>
    #       <region>Āfar</region>
    #       <country>Ethiopia</country>
    #     </location>
    #
    return {
        "context": context,
        "locality": find_optional_text(location_elem, path="locality"),
        "county": find_optional_text(location_elem, path="county"),
        "region": find_optional_text(location_elem, path="region"),
        "country": find_optional_text(location_elem, path="country"),
        # The mismatched spelling here is intentional --
        # the Flickr API uses the British English spelling, but
        # we use US English throughout Data Lifeboat so we fix it.
        "neighborhood": find_optional_text(location_elem, path="neighbourhood"),
    }


def create_user(
    user_id: str,
    username: str,
    realname: str | None,
    path_alias: str | None,
    is_deleted: bool = False,
) -> User:
    """
    Given some core attributes, construct a ``User`` object.

    This function is only intended for internal user.
    """
    realname = fix_realname(user_id, username=username, realname=realname)

    # The Flickr API is a bit inconsistent about how some undefined attributes
    # are returned, e.g. ``realname`` can sometimes be null, sometimes an
    # empty string.
    #
    # In our type system, we want all of these empty values to map to ``None``.
    user: User = {
        "id": user_id,
        "username": username,
        "realname": realname,
        "path_alias": path_alias or None,
        "photos_url": f"https://www.flickr.com/photos/{path_alias or user_id}/",
        "profile_url": f"https://www.flickr.com/people/{path_alias or user_id}/",
    }

    if is_deleted:
        return {**user, "is_deleted": True}
    else:
        return user


def fix_realname(user_id: str, username: str, realname: str | None) -> str | None:
    """
    Override the ``realname`` returned by the Flickr API.

    In general we should avoid adding too many fixes here because it would
    quickly get unwieldy, but it's a useful place to consolidate these
    fixes for members we work with a lot.
    """
    realname = realname or None

    # The museum removed the 'S' so it would look good with the big 'S'
    # in their buddy icon, but that doesn't work outside Flickr.com.
    #
    # This name needed fixing on 23 July 2024; if they ever change
    # the name on the actual account, we can remove this fudge.
    if user_id == "62173425@N02" and realname == "tockholm Transport Museum":
        return "Stockholm Transport Museum"

    # This is a frequent commenter on Flickr Commons photos.  There's a
    # realname present if you visit their profile on Flickr.com,
    # but it isn't returned in the API.
    #
    # This name needed fixing on 7 August 2024 and I've reported it
    # as an API bug; if it ever gets fixed, we can remove this branch.
    if user_id == "32162360@N00" and username == "ɹǝqɯoɔɥɔɐǝq" and realname is None:
        return "beachcomber australia"

    return realname


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


def parse_machine_tags(tags: list[str]) -> MachineTags:
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


def parse_rotation(rs: str) -> Rotation:
    """
    Given a raw rotation value from Flickr, turn it into a rotation.
    """
    if rs not in {"0", "90", "180", "270"}:  # pragma: no cover
        raise ValueError(f"Unrecognised rotation value: {rs!r}")

    return typing.cast(Rotation, int(rs))
