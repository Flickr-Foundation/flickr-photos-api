"""
Methods for getting information about a single photo in the Flickr API.
"""

from nitrate.xml import find_optional_text, find_required_elem, find_required_text

from .license_methods import LicenseMethods
from ..exceptions import ResourceNotFound
from ..types import SinglePhotoInfo, SinglePhoto, Size, create_user
from ..utils import (
    parse_date_posted,
    parse_date_taken,
    parse_location,
    parse_safety_level,
)


class SinglePhotoMethods(LicenseMethods):
    def get_single_photo_info(self, *, photo_id: str) -> SinglePhotoInfo:
        """
        Look up the information for a single photo.

        This uses the flickr.photos.getInfo API.
        """
        info_resp = self.call(
            method="flickr.photos.getInfo", params={"photo_id": photo_id}
        )

        # The getInfo response is a blob of XML of the form:
        #
        #       <?xml version="1.0" encoding="utf-8" ?>
        #       <rsp stat="ok">
        #       <photo license="8" …>
        #           <owner
        #               nsid="30884892@N08
        #               username="U.S. Coast Guard"
        #               realname="Coast Guard" …
        #           >
        #               …
        #           </owner>
        #           <title>Puppy Kisses</title>
        #           <description>Seaman Nina Bowen shows …</description>
        #           <dates
        #               posted="1490376472"
        #               taken="2017-02-17 00:00:00"
        #               …
        #           />
        #           <urls>
        #               <url type="photopage">https://www.flickr.com/photos/coast_guard/32812033543/</url>
        #           </urls>
        #           <tags>
        #           <tag raw="indian ocean" …>indianocean</tag>
        #           …
        #       </photo>
        #       </rsp>
        #
        photo_elem = find_required_elem(info_resp, path=".//photo")

        safety_level = parse_safety_level(photo_elem.attrib["safety_level"])

        license = self.lookup_license_by_id(id=photo_elem.attrib["license"])

        title = find_optional_text(photo_elem, path="title")
        description = find_optional_text(photo_elem, path="description")

        owner_elem = find_required_elem(photo_elem, path="owner")
        owner = create_user(
            id=owner_elem.attrib["nsid"],
            username=owner_elem.attrib["username"],
            realname=owner_elem.attrib["realname"],
            path_alias=owner_elem.attrib["path_alias"],
        )

        dates = find_required_elem(photo_elem, path="dates").attrib

        date_posted = parse_date_posted(dates["posted"])

        date_taken = parse_date_taken(
            value=dates["taken"],
            granularity=dates["takengranularity"],
            unknown=dates["takenunknown"] == "1",
        )

        photo_page_url = find_required_text(
            photo_elem, path='.//urls/url[@type="photopage"]'
        )

        count_comments = int(find_required_text(photo_elem, path="comments"))
        count_views = int(photo_elem.attrib["views"])

        # The originalformat parameter will only be returned if the user
        # allows downloads of the photo.
        #
        # We only need this parameter for photos that can be uploaded to
        # Wikimedia Commons.  All CC-licensed photos allow downloads, so
        # we'll always get this parameter for those photos.
        #
        # See https://www.flickr.com/help/forum/32218/
        # See https://www.flickrhelp.com/hc/en-us/articles/4404079715220-Download-permissions
        original_format = photo_elem.get("originalformat")

        # We have two options with tags: we can use the 'raw' version
        # entered by the user, or we can use the normalised version in
        # the tag text.
        #
        # e.g. "bay of bengal" vs "bayofbengal"
        #
        # We prefer the normalised version because it makes it possible
        # to compare tags across photos, and we only get the normalised
        # versions from the collection endpoints.
        tags_elem = find_required_elem(photo_elem, path="tags")

        tags = []
        for t in tags_elem.findall("tag"):
            assert t.text is not None
            tags.append(t.text)

        # Get location information about the photo.
        #
        # The <location> tag is only present in photos which have
        # location data; if the user hasn't made location available to
        # public users, it'll be missing.
        location_elem = photo_elem.find(path="location")

        if location_elem is not None:
            location = parse_location(location_elem)
        else:
            location = None

        return {
            "id": photo_id,
            "secret": photo_elem.attrib["secret"],
            "server": photo_elem.attrib["server"],
            "farm": photo_elem.attrib["farm"],
            "original_format": original_format,
            "owner": owner,
            "safety_level": safety_level,
            "license": license,
            "title": title,
            "description": description,
            "tags": tags,
            "date_posted": date_posted,
            "date_taken": date_taken,
            "location": location,
            "count_comments": count_comments,
            "count_views": count_views,
            "photo_page_url": photo_page_url,
        }

    def get_single_photo_sizes(self, *, photo_id: str) -> list[Size]:
        """
        Look up the sizes for a single photo.

        This uses the flickr.photos.getSizes API.
        """
        sizes_resp = self.call(
            method="flickr.photos.getSizes", params={"photo_id": photo_id}
        )

        # The getSizes response is a blob of XML of the form:
        #
        #       <?xml version="1.0" encoding="utf-8" ?>
        #       <rsp stat="ok">
        #       <sizes canblog="0" canprint="0" candownload="1">
        #           <size
        #               label="Square"
        #               width="75"
        #               height="75"
        #               source="https://live.staticflickr.com/2903/32812033543_c1b3784192_s.jpg"
        #               url="https://www.flickr.com/photos/coast_guard/32812033543/sizes/sq/"
        #               media="photo"
        #           />
        #           <size
        #               label="Large Square"
        #               width="150"
        #               height="150"
        #               source="https://live.staticflickr.com/2903/32812033543_c1b3784192_q.jpg"
        #               url="https://www.flickr.com/photos/coast_guard/32812033543/sizes/q/"
        #               media="photo"
        #           />
        #           …
        #       </sizes>
        #       </rsp>
        #
        # Within this function, we just return all the sizes -- we leave it up to the
        # caller to decide which size is most appropriate for their purposes.
        sizes: list[Size] = []

        for s in sizes_resp.findall(".//size"):
            if s.attrib["media"] == "photo":
                sizes.append(
                    {
                        "label": s.attrib["label"],
                        "width": int(s.attrib["width"]),
                        "height": int(s.attrib["height"]),
                        "media": "photo",
                        "source": s.attrib["source"],
                    }
                )

            elif s.attrib["media"] == "video":
                try:
                    width = int(s.attrib["width"])
                except ValueError:
                    width = None

                try:
                    height = int(s.attrib["height"])
                except ValueError:
                    height = None

                sizes.append(
                    {
                        "label": s.attrib["label"],
                        "width": width,
                        "height": height,
                        "media": "video",
                        "source": s.attrib["source"],
                    }
                )
            else:  # pragma: no cover
                raise ValueError(f"Unrecognised media type: {s.attrib['media']}")

        return sizes

    def get_single_photo(self, *, photo_id: str) -> SinglePhoto:
        """
        Look up the information for a single photo.
        """
        info = self.get_single_photo_info(photo_id=photo_id)
        sizes = self.get_single_photo_sizes(photo_id=photo_id)

        return {
            "id": photo_id,
            "title": info["title"],
            "description": info["description"],
            "owner": info["owner"],
            "date_posted": info["date_posted"],
            "date_taken": info["date_taken"],
            "safety_level": info["safety_level"],
            "license": info["license"],
            "url": info["photo_page_url"],
            "sizes": sizes,
            "original_format": info["original_format"],
            "tags": info["tags"],
            "location": info["location"],
        }

    def is_photo_deleted(self, *, photo_id: str) -> bool:
        """
        Check if a photo has been deleted from Flickr.
        """
        try:
            self.call(method="flickr.photos.getInfo", params={"photo_id": photo_id})
        except ResourceNotFound:
            return True
        else:
            return False
