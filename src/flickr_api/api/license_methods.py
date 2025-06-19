"""
Methods for getting information about licenses from the Flickr API.

When Flickr adds new licenses, we add support for them as follows:

*   Add a new human-readable ID in `flickr_api.models.licenses`,
    e.g. we refer to a license as "cc-by-2.0" rather than "4"

    This needs to be added to `LicenseId` and `NAME_TO_LICENSE_ID`.

*   Optionally: add a new mapping to NAME_OVERRIDES, if you want to change
    the label on the license from that supplied by the Flickr API.

*   Delete all the test cassettes named `TestLicenseMethods.*` and re-run
    the tests.

You may need to regenerate the test cassettes for vcrpy, to include the
new licenses in the response.  There's an example script for doing that
in the ticket where we added support for CC 4.0 licenses:
https://github.com/Flickr-Foundation/flickr-photos-api/issues/158
"""

import functools
import itertools
import re
import typing
from xml.etree import ElementTree as ET

from .base import FlickrApi
from ..exceptions import LicenseNotFound, ResourceNotFound
from ..models import License, LicenseChange
from ..models.licenses import LicenseChangeEntry, NAME_TO_LICENSE_ID, NAME_OVERRIDES
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

        # This API returns results in the form:
        #
        #     <licenses>
        #       <license
        #         id="4"
        #         name="CC BY 2.0"
        #         url="https://creativecommons.org/licenses/by/2.0/"/>
        #       <license …>
        #       <license …>
        #       …
        #     </license>
        #
        return {
            lic_elem.attrib["id"]: self._parse_license_elem(lic_elem)
            for lic_elem in license_resp.findall(".//license")
        }

    @staticmethod
    def _parse_license_elem(elem: ET.Element) -> License:
        """
        Map a <license> element from the `flickr.photos.licenses.getInfo`
        to our nicely-typed `License` model.
        """
        human_readable_id = NAME_TO_LICENSE_ID[elem.attrib["name"]]

        label = NAME_OVERRIDES.get(elem.attrib["name"], elem.attrib["name"])

        url = elem.attrib["url"]

        return {"id": human_readable_id, "label": label, "url": url}

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
