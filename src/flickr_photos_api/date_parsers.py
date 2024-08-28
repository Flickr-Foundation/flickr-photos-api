"""
The Flickr API returns dates in several formats; the helpers in this file
parse these dates and turn them into native Python types.
"""

import datetime

from flickr_photos_api.types import DateTaken, TakenGranularity


def parse_timestamp(ts: str, /) -> datetime.datetime:
    """
    Convert a Unix timestamp into a Python-native ``datetime.datetime``.

    Example:

        >>> parse_timestamp('1490376472')
        datetime.datetime(2017, 3, 24, 17, 27, 52, tzinfo=datetime.timezone.utc)

    The Flickr API frequently returns dates as Unix timestamps, for example:

    *   When you call ``flickr.photos.getInfo``, the ``<dates>`` element
        includes the upload and last update dates as a timestamp
    *   When you call ``flickr.people.getInfo`` for a user with Flickr Pro,
        the ``expires`` attribute is a numeric timestamp.

    In this case a Unix timestamp is "an unsigned integer specifying
    the number of seconds since Jan 1st 1970 GMT" [1].

    [1] https://www.flickr.com/services/api/misc.dates.html
    """
    return datetime.datetime.fromtimestamp(int(ts), tz=datetime.timezone.utc)


def _parse_date_taken_value(dt: str) -> datetime.datetime:
    """
    Convert a "date taken" string to a Python-native ``datetime.datetime``.

    Example:

        >>> _parse_date_taken_value('2017-02-17 00:00:00')
        datetime.datetime(2017, 2, 17, 0, 0)

    """
    # See https://www.flickr.com/services/api/misc.dates.html
    #
    #     The date taken should always be displayed in the timezone
    #     of the photo owner, which is to say, don't perform
    #     any conversion on it.
    #
    return datetime.datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")


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
