"""
Types for the licenses used on Flickr.
"""

import typing


class License(typing.TypedDict):
    """
    The license of a particular photo.

    The ID is a human-readable ID chosen by us; the label and URL
    come from Flickr.
    """

    id: "LicenseId"
    label: str
    url: str | None


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
