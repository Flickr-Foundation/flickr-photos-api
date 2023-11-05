import functools
from typing import Union
import xml.etree.ElementTree as ET

import httpx

from .exceptions import FlickrApiException, LicenseNotFound, ResourceNotFound


class BaseApi:
    """
    This is a thin wrapper for calling the Flickr API.

    It doesn't do much interesting stuff; the goal is just to reduce boilerplate
    in the rest of the codebase, e.g. have the XML parsing in one place rather
    than repeated everywhere.
    """

    def __init__(self, *, api_key: str, user_agent: str) -> None:
        self.client = httpx.Client(
            base_url="https://api.flickr.com/services/rest/",
            params={"api_key": api_key},
            headers={"User-Agent": user_agent},
        )

    def call(self, method: str, **params: Union[str, int]) -> ET.Element:
        params["method"] = method

        resp = self.client.get(url="", params=params)
        resp.raise_for_status()

        # Note: the xml.etree.ElementTree is not secure against maliciously
        # constructed data (see warning in the Python docs [1]), but that's
        # fine here -- we're only using it for responses from the Flickr API,
        # which we trust.
        #
        # [1]: https://docs.python.org/3/library/xml.etree.elementtree.html
        xml = ET.fromstring(resp.text)

        # If the Flickr API call fails, it will return a block of XML like:
        #
        #       <rsp stat="fail">
        #       	<err
        #               code="1"
        #               msg="Photo &quot;1211111111111111&quot; not found (invalid ID)"
        #           />
        #       </rsp>
        #
        # Different API endpoints have different codes, and so we just throw
        # and let calling functions decide how to handle it.
        if xml.attrib["stat"] == "fail":
            errors = xml.find(".//err").attrib

            # Although I haven't found any explicit documentation of this,
            # it seems like a pretty common convention that error code "1"
            # means "not found".
            if errors["code"] == "1":
                raise ResourceNotFound(**params)
            else:
                raise FlickrApiException(errors)

        return xml


class FlickrPhotosApi(BaseApi):
    @functools.lru_cache
    def get_licenses(self):
        """
        Returns a list of licenses, arranged by code.

        See https://www.flickr.com/services/api/flickr.photos.licenses.getInfo.htm
        """
        license_resp = self.call("flickr.photos.licenses.getInfo")

        result = {}

        # Add a short ID which can be used to more easily refer to this
        # license throughout the codebase.
        license_ids = {
            "All Rights Reserved": "in-copyright",
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

    @functools.lru_cache(maxsize=None)
    def lookup_license_by_id(self, *, id: str):
        """
        Given a license ID from the Flickr API, return the license data.

        e.g. a Flickr API response might include a photo in the following form:

            <photo license="0" …>

        Then you'd call this function to find out what that means:

            >>> api.lookup_license_by_id(license_id="0")
            {"id": "in-copyright", "name": "All Rights Reserved", "url": None}

        See https://www.flickr.com/services/api/flickr.photos.licenses.getInfo.htm
        """
        licenses = self.get_licenses()

        try:
            return licenses[id]
        except KeyError:
            raise LicenseNotFound(license_id=id)
