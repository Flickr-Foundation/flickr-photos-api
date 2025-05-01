"""
Types for the licenses used on Flickr.
"""

from datetime import datetime
import typing


class License(typing.TypedDict):
    """
    The license of a particular photo.

    The ID is a human-readable ID chosen by us; the label and URL
    come from Flickr.
    """

    id: "LicenseId"
    label: str
    url: str


LicenseId = typing.Literal[
    "all-rights-reserved",
    "cc-by-nc-sa-2.0",
    "cc-by-nc-2.0",
    "cc-by-nc-nd-2.0",
    "cc-by-2.0",
    "cc-by-sa-2.0",
    "cc-by-nd-2.0",
    "nkcr",
    "usgov",
    "cc0-1.0",
    "pdm",
]


class LicenseChangeEntry:
    """
    Events in the license history of a photo -- both the initial license
    and any subsequent changes.
    """

    # The initial license, set when the photo was uploaded
    InitialLicense = typing.TypedDict(
        "InitialLicense", {"date_posted": datetime, "license": License}
    )

    # Any changes to the license made after the initial upload
    ChangedLicense = typing.TypedDict(
        "ChangedLicense",
        {"date_changed": datetime, "old_license": License, "new_license": License},
    )


LicenseChange = LicenseChangeEntry.InitialLicense | LicenseChangeEntry.ChangedLicense
