"""
Methods for getting information about licenses from the Flickr API.
"""

import functools
import re

from .base import FlickrApi
from ..exceptions import LicenseNotFound
from ..models import License, LicenseId


class LicenseMethods(FlickrApi):
    """
    License-related methods for the Flickr API.
    """

    # Note: this list of licenses almost never changes, so we call this once
    # and cache the result for efficiency.
    @functools.cache
    def get_licenses(self) -> dict[str, License]:
        """
        Returns a list of licenses, organised by numeric ID.

        In particular, IDs can be looked up using the numeric ID
        returned by many Flickr API methods.

        See https://www.flickr.com/services/api/flickr.photos.licenses.getInfo.htm
        """
        license_resp = self.call(method="flickr.photos.licenses.getInfo")

        result: dict[str, License] = {}

        # Add a short ID which can be used to more easily refer to this
        # license throughout the codebase.
        license_ids: dict[str, LicenseId] = {
            "All Rights Reserved": "all-rights-reserved",
            "Attribution-NonCommercial-ShareAlike License": "cc-by-nc-sa-2.0",
            "Attribution-NonCommercial License": "cc-by-nc-2.0",
            "Attribution-NonCommercial-NoDerivs License": "cc-by-nc-nd-2.0",
            "Attribution License": "cc-by-2.0",
            "Attribution-ShareAlike License": "cc-by-sa-2.0",
            "Attribution-NoDerivs License": "cc-by-nd-2.0",
            "No known copyright restrictions": "nkcr",
            "United States Government Work": "usgov",
            "Public Domain Dedication (CC0)": "cc0-1.0",
            "Public Domain Mark": "pdm",
        }

        license_labels = {
            "Attribution-NonCommercial-ShareAlike License": "CC BY-NC-SA 2.0",
            "Attribution-NonCommercial License": "CC BY-NC 2.0",
            "Attribution-NonCommercial-NoDerivs License": "CC BY-NC-ND 2.0",
            "Attribution License": "CC BY 2.0",
            "Attribution-ShareAlike License": "CC BY-SA 2.0",
            "Attribution-NoDerivs License": "CC BY-ND 2.0",
            "Public Domain Dedication (CC0)": "CC0 1.0",
        }

        for lic in license_resp.findall(".//license"):
            result[lic.attrib["id"]] = {
                "id": license_ids[lic.attrib["name"]],
                "label": license_labels.get(lic.attrib["name"], lic.attrib["name"]),
                "url": lic.attrib["url"] or None,
            }

        return result

    @functools.cache
    def lookup_license_by_id(self, *, id: str) -> License:
        """
        Return the license for a license ID.

        The ID can be one of:

        *   The numeric license ID returned from the Flickr API
            (e.g. "0" ~> "All Rights Reserved")
        *   The human-readable license ID returned from this library
            (e.g. "cc-by-2.0" ~> "CC BY 2.0")

        """
        licenses = self.get_licenses()

        # If this is a numeric ID, then it must have come from the
        # Flickr API.  Look it up directly in the dict.
        if re.match(r"^[0-9]+$", id):
            try:
                return licenses[id]
            except KeyError:
                raise LicenseNotFound(license_id=id)

        # Otherwise, this is a human-readable license ID from our
        # library, so look for a matching license.
        try:
            matching_license = next(lic for lic in licenses.values() if lic["id"] == id)
            return matching_license
        except StopIteration:
            raise LicenseNotFound(license_id=id)
