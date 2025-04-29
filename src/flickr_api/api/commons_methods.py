"""
Methods for getting information about the Flickr Commons.
"""

from datetime import datetime, timezone

from nitrate.xml import find_optional_text, find_required_text

from .base import FlickrApi
from ..models import CommonsInstitution


class FlickrCommonsMethods(FlickrApi):
    """
    Methods for getting information about the Flickr Commons.
    """

    def list_commons_institutions(self) -> list[CommonsInstitution]:
        """
        Get a list of all the institutions in the Flickr Commons.
        """
        resp = self.call(method="flickr.commons.getInstitutions")

        result = []

        # The structure of the XML is something like:
        #
        # 	<institution nsid="8623220@N02" date_launch="1200470400">
        #   	<name>The Library of Congress</name>
        #   	<urls>
        #   		<url type="site">http://www.loc.gov/</url>
        #   		<url type="license">http://www.loc.gov/rr/print/195_copr.html#noknown</url>
        #   		<url type="flickr">http://flickr.com/photos/library_of_congress/</url>
        #   	</urls>
        #   </institution>
        #
        for institution_elem in resp.findall(path=".//institution"):
            user_id = institution_elem.attrib["nsid"]

            date_launch = datetime.fromtimestamp(
                int(institution_elem.attrib["date_launch"]), tz=timezone.utc
            )

            name = find_required_text(institution_elem, path="name")

            site_url = find_optional_text(institution_elem, path='.//url[@type="site"]')
            license_url = find_required_text(
                institution_elem, path='.//url[@type="license"]'
            )

            institution: CommonsInstitution = {
                "user_id": user_id,
                "date_launch": date_launch,
                "name": name,
                "site_url": site_url,
                "license_url": license_url,
            }

            result.append(institution)

        return result
