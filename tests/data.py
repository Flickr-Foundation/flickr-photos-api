"""
This is some hard-coded data we can use as test values.

Defining them in a single place allows us to keep notes on why we
picked these IDs together, and keep the individual tests cleaner.
It reduces the number of "magic values" in each test.
"""


class FlickrUserIds:
    """
    Named Flickr user IDs we can use for testing.
    """

    FlickrFoundation = "197130754@N07"

    # My personal Flickr account
    Alexwlchan = "199258389@N04"

    # This is the user ID of the Upper Midwest Jewish Archives, who deleted
    # their Flickr account in May 2024.
    Deleted = "48143042@N05"


class FlickrPhotoIds:
    """
    Named Flickr photo IDs we can use for testing.
    """

    # Flickr photo IDs are numeric strings; these strings are not that
    Invalid = ["-1", "does_not_exist", ""]

    # Strings that are numeric and could be Flickr photo IDs, but aren't
    NonExistent = ["1", "12345678901234567890"]
