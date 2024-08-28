"""
The Flickr API returns dates in several formats; the helpers in this file
parse these dates and turn them into native Python types.
"""

import datetime


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
