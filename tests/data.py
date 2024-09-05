class FlickrUserIds:
    """
    Named Flickr user IDs we can use for testing.
    """

    FlickrFoundation = "197130754@N07"

    # My personal Flickr account
    Alexwlchan = "199258389@N04"


class FlickrPhotoIds:
    """
    Named Flickr photo IDs we can use for testing.
    """

    # Flickr photo IDs are numeric strings; these strings are not that
    Invalid = ["-1", "does_not_exist", ""]

    # Strings that are numeric and could be Flickr photo IDs, but aren't
    NonExistent = ["1", "12345678901234567890"]
