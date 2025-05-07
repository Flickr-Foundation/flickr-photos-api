"""
Methods for getting information about a single photo in the Flickr API.
"""

import typing
from xml.etree import ElementTree as ET

from flickr_url_parser import looks_like_flickr_photo_id
from nitrate.xml import find_optional_text, find_required_elem, find_required_text

from .license_methods import LicenseMethods
from ..exceptions import PhotoIsPrivate, ResourceNotFound
from ..models import (
    AlbumContext,
    BoundingBox,
    ExifTag,
    GalleryContext,
    GroupContext,
    Location,
    MediaType,
    Note,
    Person,
    PhotoContext,
    SinglePhotoInfo,
    SinglePhoto,
    Size,
    Tag,
    Usage,
    Visibility,
)
from ..parsers import (
    create_user,
    parse_date_taken,
    parse_machine_tags,
    parse_named_location,
    parse_numeric_location,
    parse_rotation,
    parse_timestamp,
    parse_safety_level,
)


class SinglePhotoMethods(LicenseMethods):
    """
    Methods for getting information about a single photo.
    """

    def parse_single_photo_info(
        self, info_resp: ET.Element, *, photo_id: str
    ) -> SinglePhotoInfo:
        """
        Parse the XML response from the ``flickr.photos.getInfo`` API.
        """
        # The getInfo response is a blob of XML of the form:
        #
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
            user_id=owner_elem.attrib["nsid"],
            username=owner_elem.attrib["username"],
            realname=owner_elem.attrib["realname"],
            path_alias=owner_elem.attrib["path_alias"],
        )

        dates = find_required_elem(photo_elem, path="dates").attrib

        date_posted = parse_timestamp(dates["posted"])

        date_taken = parse_date_taken(
            value=dates["taken"],
            granularity=dates["takengranularity"],
            unknown=dates["takenunknown"] == "1",
        )

        url = find_required_text(photo_elem, path='.//urls/url[@type="photopage"]')

        count_comments = int(find_required_text(photo_elem, path="comments"))
        count_views = int(photo_elem.attrib["views"])

        rotation = parse_rotation(photo_elem.attrib["rotation"])

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

        # When you look up tags on a single photo, you get a structured
        # block of data, e.g.:
        #
        #     <tags>
        #       <tag
        #         id="32695993-21609597615-765"
        #         author="126912357@N06"
        #         authorname="valuable basket"
        #         raw="Church"
        #         machine_tag="0">church</tag>
        #       ...
        #     </tags>
        #
        # We write the normalized value into the "tags" field, because
        # this matches the values we get from the collection endpoints.
        #
        # However, in some context it's useful to have the raw value as
        # entered by the user, so we store this in the ``raw_tags`` list.
        #
        # Note: it's rare, but some Flickr photos do have empty text for
        # the tag value.  See the tests for an example.
        tags_elem = find_required_elem(photo_elem, path="tags")

        tags = []
        raw_tags: list[Tag] = []

        for t in tags_elem.findall("tag"):
            tags.append(t.text or "")
            raw_tags.append(
                {
                    "author_id": t.attrib["author"],
                    "author_name": t.attrib["authorname"],
                    "raw_value": t.attrib["raw"],
                    "normalized_value": t.text or "",
                    "is_machine_tag": t.attrib["machine_tag"] == "1",
                }
            )

        # The notes on the photo are stored as a structured block of data:
        #
        #     <notes>
        #       <note
        #         id="72157620890011304"
        #         photo_id="2959326615"
        #         author="34870218@N07"
        #         authorname="othercoby"
        #         authorrealname=""
        #         authorispro="0"
        #         authorisdeleted="0"
        #         x="236" y="200" w="50" h="50">the size of those paws!</note>
        #       …
        #
        notes_elem = find_required_elem(photo_elem, path="notes")

        notes: list[Note] = []

        for n in notes_elem.findall("note"):
            note_text = n.text
            assert isinstance(note_text, str)

            notes.append(
                {
                    "id": n.attrib["id"],
                    "author": create_user(
                        user_id=n.attrib["author"],
                        username=n.attrib["authorname"],
                        realname=n.attrib["authorrealname"],
                        path_alias=None,
                        is_deleted=n.attrib["authorisdeleted"] == "1",
                    ),
                    "bounding_box": {
                        "x": int(n.attrib["x"]),
                        "y": int(n.attrib["y"]),
                        "width": int(n.attrib["w"]),
                        "height": int(n.attrib["h"]),
                    },
                    "text": note_text,
                }
            )

        # Get location information about the photo.
        #
        # The <location> tag is only present in photos which have
        # location data; if the user hasn't made location available to
        # public users, it'll be missing.
        location_elem = photo_elem.find(path="location")
        location: Location | None = None

        if location_elem is not None:
            numeric_location = parse_numeric_location(location_elem)

            if numeric_location is not None:
                named_location = parse_named_location(location_elem)
                location = {**numeric_location, **named_location}

        # Get visibility information about the photo.
        #
        # This is returned in the form:
        #
        #     <visibility ispublic="1" isfriend="0" isfamily="0"/>
        #
        visibility_elem = find_required_elem(photo_elem, path="visibility")
        visibility: Visibility = {
            "is_public": visibility_elem.attrib["ispublic"] == "1",
            "is_friend": visibility_elem.attrib["isfriend"] == "1",
            "is_family": visibility_elem.attrib["isfamily"] == "1",
        }

        # Get usage information about the photo.
        #
        # This is returned in the form:
        #
        #     <usage candownload="0" canblog="0" canprint="0" canshare="0"/>
        #
        # fmt: off
        usage_elem = find_required_elem(photo_elem, path="usage")
        usage: Usage = {
            "can_download": usage_elem.attrib["candownload"] == "1",
            "can_blog":     usage_elem.attrib["canblog"]     == "1",
            "can_print":    usage_elem.attrib["canprint"]    == "1",
            "can_share":    usage_elem.attrib["canshare"]    == "1",
        }
        # fmt: on

        # Determine whether there are any people in the photo.
        #
        # This is returned in the form:
        #
        #     <people haspeople="1"/>
        #
        people_elem = find_required_elem(photo_elem, path="people")
        has_people = people_elem.attrib["haspeople"] == "1"

        assert photo_elem.attrib["media"] in {"photo", "video"}
        media_type = typing.cast(MediaType, photo_elem.attrib["media"])

        return {
            "id": photo_id,
            "media": media_type,
            "secret": photo_elem.attrib["secret"],
            "server": photo_elem.attrib["server"],
            "farm": photo_elem.attrib["farm"],
            "original_format": original_format,
            "rotation": rotation,
            "owner": owner,
            "safety_level": safety_level,
            "license": license,
            "title": title,
            "description": description,
            "tags": tags,
            "raw_tags": raw_tags,
            "notes": notes,
            "machine_tags": parse_machine_tags(tags),
            "date_posted": date_posted,
            "date_taken": date_taken,
            "location": location,
            "count_comments": count_comments,
            "count_views": count_views,
            "has_people": has_people,
            "url": url,
            "visibility": visibility,
            "usage": usage,
        }

    def get_single_photo_info(self, *, photo_id: str) -> SinglePhotoInfo:
        """
        Look up the information for a single photo.

        This uses the flickr.photos.getInfo API.
        """
        if not looks_like_flickr_photo_id(photo_id):
            raise ValueError(f"Not a Flickr photo ID: {photo_id!r}")

        info_resp = self.call(
            method="flickr.photos.getInfo",
            params={"photo_id": photo_id},
            exceptions={
                "1": ResourceNotFound(f"Could not find photo with ID: {photo_id!r}"),
                "2": PhotoIsPrivate(photo_id),
            },
        )

        return self.parse_single_photo_info(info_resp, photo_id=photo_id)

    def get_single_photo_sizes(self, *, photo_id: str) -> list[Size]:
        """
        Look up the sizes for a single photo.

        This uses the flickr.photos.getSizes API.
        """
        sizes_resp = self.call(
            method="flickr.photos.getSizes",
            params={"photo_id": photo_id},
            exceptions={
                "1": ResourceNotFound(f"Could not find photo with ID: {photo_id!r}"),
            },
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

        return {**info, "sizes": sizes}

    def list_people_in_photo(self, *, photo_id: str) -> list[Person]:
        """
        Return a list of people who are tagged in this photo.

        See https://www.flickr.com/services/api/flickr.photos.people.getList.html
        """
        resp = self.call(
            method="flickr.photos.people.getList",
            params={"photo_id": photo_id},
            exceptions={
                "1": ResourceNotFound(f"Could not find photo with ID: {photo_id!r}"),
            },
        )

        # The response will be of the form
        #
        #    <rsp stat="ok">
        #      <people total="1" photo_width="500" photo_height="333">
        #        <person nsid="87944415@N00" username="hitherto" iconserver="1" iconfarm="1" path_alias="hitherto" added_by="12289718@N00" is_deleted="0" realname="Simon Batistoni"/>
        #      </people>
        #    </rsp>
        #
        result: list[Person] = []

        for person_elem in resp.findall(".//person"):
            user = create_user(
                user_id=person_elem.attrib["nsid"],
                username=person_elem.attrib["username"],
                realname=person_elem.attrib["realname"],
                path_alias=person_elem.attrib["path_alias"],
                is_deleted=person_elem.attrib["is_deleted"] == "1",
            )

            try:
                bounding_box: BoundingBox | None = {
                    "x": int(person_elem.attrib["x"]),
                    "y": int(person_elem.attrib["y"]),
                    "width": int(person_elem.attrib["w"]),
                    "height": int(person_elem.attrib["h"]),
                }
            except KeyError:
                bounding_box = None

            result.append({"user": user, "bounding_box": bounding_box})

        return result

    def is_photo_deleted(self, *, photo_id: str) -> bool:
        """
        Check if a photo has been deleted from Flickr.

        TODO: This can tell us whether a photo exists, but not whether
        it's been deleted -- we can't know whether a given photo ID
        never existed, or if it used to exist but doesn't.

        We should change this method to ``get_photo_state()`` returning
        an enum like exists/does_not_exist/private.
        """
        try:
            self.call(
                method="flickr.photos.getInfo",
                params={"photo_id": photo_id},
                exceptions={"1": ResourceNotFound(), "2": PhotoIsPrivate(photo_id)},
            )
        except ResourceNotFound:
            return True
        except PhotoIsPrivate:
            return False
        else:
            return False

    def get_photo_contexts(self, *, photo_id: str) -> PhotoContext:
        """
        Find the contexts where this photo appears on Flickr.

        This includes albums, galleries, and groups.
        """
        if not looks_like_flickr_photo_id(photo_id):
            raise ValueError(f"Not a Flickr photo ID: {photo_id!r}")

        # See https://www.flickr.com/services/api/flickr.photos.getAllContexts.html
        contexts_resp = self.call(
            method="flickr.photos.getAllContexts",
            params={"photo_id": photo_id},
            exceptions={
                "1": ResourceNotFound(f"Could not find photo with ID: {photo_id!r}")
            },
        )

        # Within the response, the albums are in XML with the following structure:
        #
        #     <
        #       set
        #       title="Landscape / Nature"
        #       id="72157650910758151"
        #       view_count="2312"
        #       comment_count="0"
        #       count_photo="269"
        #       count_video="0" […] />
        #
        albums: list[AlbumContext] = [
            {
                "id": set_elem.attrib["id"],
                "title": set_elem.attrib["title"],
                "count_photos": int(set_elem.attrib["count_photo"]),
                "count_videos": int(set_elem.attrib["count_video"]),
                "count_views": int(set_elem.attrib["view_count"]),
                "count_comments": int(set_elem.attrib["comment_count"]),
            }
            for set_elem in contexts_resp.findall(".//set")
        ]

        # Within the response, the groups are in XML with the following structure:
        #
        #     <
        #       pool
        #       title="A Picture, A Story, A Pearl"
        #       url="/groups/14776652@N22/pool/"
        #       id="14776652@N22"
        #       members="3444"
        #       pool_count="59875" […] />
        #
        groups: list[GroupContext] = [
            {
                "id": pool_elem.attrib["id"],
                "title": pool_elem.attrib["title"],
                "url": "https://www.flickr.com" + pool_elem.attrib["url"],
                "count_items": int(pool_elem.attrib["pool_count"]),
                "count_members": int(pool_elem.attrib["members"]),
            }
            for pool_elem in contexts_resp.findall(".//pool")
        ]

        # See https://www.flickr.com/services/api/flickr.galleries.getListForPhoto.html
        galleries_resp = self.call(
            method="flickr.galleries.getListForPhoto",
            params={"photo_id": photo_id, "per_page": "500"},
        )

        # Within the response, the galleries are in XML with the following structure:
        #
        #
        #     <galleries page="1" pages="1" […]>
        #       <gallery
        #         gallery_id="72157721626742458"
        #         url="https://www.flickr.com/photos/72804335@N03/galleries/72157721626742458"
        #         owner="72804335@N03"
        #         username="Josep M.Toset"
        #         date_create="1680980061"
        #         date_update="1714564015"
        #         count_photos="166"
        #         count_videos="0"
        #         count_views="152"
        #         count_comments="4" […]
        #       >
        #         <title>paisatges</title>
        #         <description/>
        #       </gallery>
        #
        galleries_elem = find_required_elem(galleries_resp, path="galleries")

        # TODO: Add supporting for paginating through the list of galleries.
        #
        # I'm not sure there are any photos where this is actually necessary,
        # so for now just throw and we can return to this if we actually see
        # a photo where this is necessary.
        if int(galleries_elem.attrib["pages"]) > 1:  # pragma: no cover
            raise ValueError("Fetching more than one page of galleries is unsupported!")

        galleries: list[GalleryContext] = []

        for gallery_elem in galleries_elem.findall("gallery"):
            gallery_url = gallery_elem.attrib["url"]

            owner_id = gallery_elem.attrib["owner"]

            path_alias = (
                gallery_url.split("/")[4]
                if gallery_url.split("/")[4] != owner_id
                else None
            )

            owner = create_user(
                user_id=owner_id,
                username=gallery_elem.attrib["username"],
                path_alias=path_alias,
                # This doesn't seem to be returned in the <gallery>
                # element even when the user has one set, so we just
                # have to accept we can't set one here.
                realname=None,
            )

            description_elem = find_required_elem(gallery_elem, path="description")
            description = description_elem.text

            galleries.append(
                {
                    "id": gallery_elem.attrib["gallery_id"],
                    "url": gallery_elem.attrib["url"],
                    "owner": owner,
                    "title": find_required_text(gallery_elem, path="title"),
                    "description": description,
                    "date_created": parse_timestamp(gallery_elem.attrib["date_create"]),
                    "date_updated": parse_timestamp(gallery_elem.attrib["date_update"]),
                    "count_photos": int(gallery_elem.attrib["count_photos"]),
                    "count_videos": int(gallery_elem.attrib["count_videos"]),
                    "count_views": int(gallery_elem.attrib["count_views"]),
                    "count_comments": int(gallery_elem.attrib["count_comments"]),
                }
            )

        return {
            "albums": albums,
            "galleries": galleries,
            "groups": groups,
        }

    def get_exif_tags_for_photo(self, photo_id: str) -> list[ExifTag]:
        """
        Return a list of EXIF/TIFF/GPS tags for a given photo.
        """
        # See https://www.flickr.com/services/api/flickr.photos.getExif.html
        resp = self.call(
            method="flickr.photos.getExif",
            params={"photo_id": photo_id},
            exceptions={
                "1": ResourceNotFound(f"Could not find photo with ID: {photo_id!r}")
            },
        )

        # The format of the response will be of the form:
        #
        #   <photo id="4424" secret="06b8e43bc7" server="2">
        #     <exif tagspace="TIFF" tagspaceid="1" tag="271" label="Manufacturer">
        #       <raw>Canon</raw>
        #     </exif>
        #     <exif tagspace="EXIF" tagspaceid="0" tag="33437" label="Aperture">
        #       <raw>90/10</raw>
        #       <clean>f/9</clean>
        #     </exif>
        #     …
        #
        result: list[ExifTag] = []

        for exif_elem in resp.findall("photo/exif"):
            raw_value = find_required_text(exif_elem, path="raw")
            clean_value = find_optional_text(exif_elem, path="clean")

            tag: ExifTag = {
                "tagspace": exif_elem.attrib["tagspace"],
                "tagspaceid": exif_elem.attrib["tagspaceid"],
                "tag": exif_elem.attrib["tag"],
                "label": exif_elem.attrib["label"],
                "raw_value": raw_value,
            }

            if clean_value:
                tag["clean_value"] = clean_value

            result.append(tag)

        return result
