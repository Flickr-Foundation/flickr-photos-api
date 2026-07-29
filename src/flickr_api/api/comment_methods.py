"""
Code to read/write comments on Flickr.
"""

import logging
from xml.etree import ElementTree as ET

from flickr_url_parser import looks_like_flickr_photo_id
from nitrate.xml import find_required_elem
from tenacity import RetryError

from .base import FlickrApi
from ..exceptions import (
    InsufficientPermissionsToComment,
    InvalidXmlException,
    ResourceNotFound,
)
from ..models import Comment
from ..parsers import create_user, parse_timestamp
from ..xml_helpers import attrib_flag, attrib_str, sanitize_xml_text

logger = logging.getLogger(__name__)


class CommentMethods(FlickrApi):
    """
    Methods for listing and posting comments on Flickr.
    """

    def _get_comments_list_response(self, *, photo_id: str) -> ET.Element | None:
        """
        Fetch and parse a ``flickr.photos.comments.getList`` response.

        If Flickr returns malformed XML, retry once with illegal characters stripped.
        """
        exceptions: dict[str, Exception] = {
            "1": ResourceNotFound(f"Could not find photo with ID: {photo_id!r}")
        }
        params = {"photo_id": photo_id}

        try:
            return self.call(
                method="flickr.photos.comments.getList",
                params=params,
                exceptions=exceptions,
            )
        except RetryError as err:
            cause = err.last_attempt.exception()
            if not isinstance(cause, InvalidXmlException):
                raise
            logger.warning(
                "Malformed XML fetching comments for photo %s; retrying with sanitized XML",
                photo_id,
            )
        except InvalidXmlException:
            logger.warning(
                "Malformed XML fetching comments for photo %s; retrying with sanitized XML",
                photo_id,
            )

        raw_xml = self.fetch_raw_api_response(
            method="flickr.photos.comments.getList",
            params=params,
        )
        try:
            xml = ET.fromstring(sanitize_xml_text(raw_xml))
        except ET.ParseError:
            logger.warning(
                "Comments XML for photo %s still invalid after sanitization",
                photo_id,
            )
            return None

        if xml.attrib.get("stat") == "fail":
            errors = find_required_elem(xml, path=".//err").attrib
            try:
                raise exceptions[errors["code"]]
            except KeyError:
                logger.warning(
                    "Flickr comments API failed for photo %s after XML sanitization: %s",
                    photo_id,
                    errors,
                )
                return None

        return xml

    def list_all_comments(self, *, photo_id: str) -> list[Comment]:
        """
        List all the comments on a photo.

        See https://www.flickr.com/services/api/flickr.photos.comments.getList.htm
        """
        if not looks_like_flickr_photo_id(photo_id):
            raise ValueError(f"Not a Flickr photo ID: {photo_id!r}")

        resp = self._get_comments_list_response(photo_id=photo_id)
        if resp is None:
            return []

        result: list[Comment] = []

        # The structure of the response is something like:
        #
        #     <comment
        #       id="6065-109722179-72057594077818641"
        #       author="35468159852@N01"
        #       authorname="Rev Dan Catt"
        #       realname="Daniel Catt"
        #       datecreate="1141841470"
        #       permalink="http://www.flickr.com/photos/…"
        #     >
        #       Umm, I'm not sure, can I get back to you on that one?
        #     </comment>
        #
        for comment_elem in resp.findall(".//comment"):
            author_is_deleted = attrib_flag(comment_elem, "author_is_deleted")

            author = create_user(
                user_id=attrib_str(comment_elem, "author"),
                username=attrib_str(comment_elem, "authorname"),
                realname=attrib_str(comment_elem, "realname") or None,
                path_alias=attrib_str(comment_elem, "path_alias") or None,
                is_deleted=author_is_deleted,
            )

            result.append(
                {
                    "id": attrib_str(comment_elem, "id"),
                    "photo_id": photo_id,
                    "author": author,
                    "text": comment_elem.text or "",
                    "permalink": attrib_str(comment_elem, "permalink"),
                    "date": parse_timestamp(attrib_str(comment_elem, "datecreate")),
                }
            )

        return result

    def post_comment(self, *, photo_id: str, comment_text: str) -> str:
        """
        Post a comment to Flickr.

        Returns the ID of the newly created comment.

        Note that Flickr comments are idempotent, so we don't need to worry
        too much about double-posting in this method.  If somebody posts
        the same comment twice, Flickr silently discards the second and
        returns the ID of the original comment.
        """
        if not looks_like_flickr_photo_id(photo_id):
            raise ValueError(f"Not a Flickr photo ID: {photo_id!r}")

        xml = self.call(
            http_method="POST",
            method="flickr.photos.comments.addComment",
            params={"photo_id": photo_id, "comment_text": comment_text},
            exceptions={
                "1": ResourceNotFound(f"Could not find photo with ID: {photo_id!r}"),
                "99": InsufficientPermissionsToComment(photo_id=photo_id),
            },
        )

        return find_required_elem(xml, path=".//comment").attrib["id"]
