import functools
from typing import Dict, Union
import xml.etree.ElementTree as ET

import httpx

from .exceptions import FlickrApiException, LicenseNotFound, ResourceNotFound
from .utils import find_required_elem, find_required_text
from ._types import License, User


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
        resp = self.client.get(url="", params={"method": method, **params})
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
            errors = find_required_elem(xml, path=".//err").attrib

            # Although I haven't found any explicit documentation of this,
            # it seems like a pretty common convention that error code "1"
            # means "not found".
            if errors["code"] == "1":
                raise ResourceNotFound(method, **params)
            else:
                raise FlickrApiException(errors)

        return xml


class FlickrPhotosApi(BaseApi):
    @functools.lru_cache
    def get_licenses(self) -> Dict[str, License]:
        """
        Returns a list of licenses, arranged by code.

        See https://www.flickr.com/services/api/flickr.photos.licenses.getInfo.htm
        """
        license_resp = self.call("flickr.photos.licenses.getInfo")

        result: Dict[str, License] = {}

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
    def lookup_license_by_id(self, *, id: str) -> License:
        """
        Given a license ID from the Flickr API, return the license data.

        e.g. a Flickr API response might include a photo in the following form:

            <photo license="0" …>

        Then you'd call this function to find out what that means:

            >>> api.lookup_license_by_id(id="0")
            {"id": "in-copyright", "name": "All Rights Reserved", "url": None}

        See https://www.flickr.com/services/api/flickr.photos.licenses.getInfo.htm
        """
        licenses = self.get_licenses()

        try:
            return licenses[id]
        except KeyError:
            raise LicenseNotFound(license_id=id)

    def lookup_user_by_url(self, *, url: str) -> User:
        """
        Given the link to a user's photos or profile, return their info.

            >>> api.lookup_user_by_url(user_url="https://www.flickr.com/photos/britishlibrary/")
            {
                "id": "12403504@N02",
                "username": "The British Library",
                "realname": "British Library",
                "photos_url": "https://www.flickr.com/photos/britishlibrary/",
                "profile_url": "https://www.flickr.com/people/britishlibrary/",
            }

        See https://www.flickr.com/services/api/flickr.urls.lookupUser.htm
        See https://www.flickr.com/services/api/flickr.people.getInfo.htm

        """
        # The lookupUser response is of the form:
        #
        #       <user id="12403504@N02">
        #       	<username>The British Library</username>
        #       </user>
        #
        lookup_resp = self.call("flickr.urls.lookupUser", url=url)
        user_id = find_required_elem(lookup_resp, path=".//user").attrib["id"]

        # The getInfo response is of the form:

        #     <person id="12403504@N02"…">
        #   	<username>The British Library</username>
        #       <realname>British Library</realname>
        #       <photosurl>https://www.flickr.com/photos/britishlibrary/</photosurl>
        #       <profileurl>https://www.flickr.com/people/britishlibrary/</profileurl>
        #       …
        #     </person>
        #
        info_resp = self.call("flickr.people.getInfo", user_id=user_id)
        username = find_required_text(info_resp, path=".//username")
        photos_url = find_required_text(info_resp, path=".//photosurl")
        profile_url = find_required_text(info_resp, path=".//profileurl")

        # If the user hasn't set a realname in their profile, the element
        # will be absent from the response.
        realname_elem = info_resp.find(path=".//realname")

        if realname_elem is None:
            realname = None
        else:
            realname = realname_elem.text

        return {
            "id": user_id,
            "username": username,
            "realname": realname,
            "photos_url": photos_url,
            "profile_url": profile_url,
        }
