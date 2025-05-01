"""
Methods for getting information about licenses from the Flickr API.
"""

import functools
import itertools
import re
import typing

from .base import FlickrApi
from ..exceptions import LicenseNotFound, ResourceNotFound
from ..models import License, LicenseChange, LicenseId
from ..models.licenses import LicenseChangeEntry
from ..parsers import parse_timestamp


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
                "url": lic.attrib["url"],
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

    def get_license_history(self, photo_id: str) -> list[LicenseChange]:
        """
        Return the license history of a photo.

        This always returns license events in sorted order.
        """
        licenses_by_url = {lic["url"]: lic for lic in self.get_licenses().values()}

        # First call the getLicenseHistory API.
        # See https://www.flickr.com/services/api/flickr.photos.licenses.getLicenseHistory.html
        history_resp = self.call(
            method="flickr.photos.licenses.getLicenseHistory",
            params={"photo_id": photo_id},
            exceptions={"1": ResourceNotFound()},
        )

        # Look for <license_history> elements in the response.
        history_elems = history_resp.findall("./license_history")

        # If there's a single <license_history> element and the `new_license`
        # is empty, it means this is the original license.
        #
        #     <rsp stat="ok">
        #       <license_history
        #         date_change="1733215279"
        #         old_license="All Rights Reserved" old_license_url="https://www.flickrhelp.com/hc/en-us/articles/10710266545556-Using-Flickr-images-shared-by-other-members"
        #         new_license="" new_license_url=""
        #       />
        #     </rsp>
        #
        if len(history_elems) == 1 and history_elems[0].attrib["new_license"] == "":
            date_posted = parse_timestamp(history_elems[0].attrib["date_change"])
            license_url = history_elems[0].attrib["old_license_url"]

            return [
                {
                    "date_posted": date_posted,
                    "license": licenses_by_url[license_url],
                }
            ]

        # Restructure the <license_history> elements -- at this point,
        # we know that they all have both an `old_license` and a `new_license`.
        #
        # While we're here, let's make sure the events are in date order.
        # The Flickr API usually returns them in this order, but it's
        # not guaranteed -- let's make sure that's true.
        license_events: list[LicenseChangeEntry.ChangedLicense] = sorted(
            [
                {
                    "date_changed": parse_timestamp(elem.attrib["date_change"]),
                    "old_license": licenses_by_url[elem.attrib["old_license_url"]],
                    "new_license": licenses_by_url[elem.attrib["new_license_url"]],
                }
                for elem in history_elems
            ],
            key=lambda ev: ev["date_changed"],
        )

        # Do a quick consistency check that this history makes sense
        # -- when a license changes, the `old_license` is the same
        # as the previous `new_license`.
        for ev1, ev2 in itertools.pairwise(license_events):
            assert ev1["new_license"] == ev2["old_license"]

        return typing.cast(list[LicenseChange], license_events)
