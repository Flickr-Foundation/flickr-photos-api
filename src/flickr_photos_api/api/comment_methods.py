"""
Methods for getting information about comments from the Flickr API.
"""

from .base import FlickrApi
from ..exceptions import ResourceNotFound, InsufficientPermissionsToComment
from ..types import Comment, create_user
from ..utils import parse_date_posted

from nitrate.xml import find_required_elem


class CommentMethods(FlickrApi):
    def list_all_comments(self, *, photo_id: str) -> list[Comment]:
        """
        List all the comments on a photo.

        See https://www.flickr.com/services/api/flickr.photos.comments.getList.htm
        """
        resp = self.call(
            method="flickr.photos.comments.getList",
            params={"photo_id": photo_id},
            exceptions={
                "1": ResourceNotFound(f"Could not find photo with ID: {photo_id!r}")
            },
        )

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
            author = create_user(
                id=comment_elem.attrib["author"],
                username=comment_elem.attrib["authorname"],
                realname=comment_elem.attrib["realname"],
                path_alias=comment_elem.attrib["path_alias"],
            )

            author_is_deleted = comment_elem.attrib["author_is_deleted"] == "1"

            result.append(
                {
                    "id": comment_elem.attrib["id"],
                    "photo_id": photo_id,
                    "author_is_deleted": author_is_deleted,
                    "author": author,
                    "text": comment_elem.text or "",
                    "permalink": comment_elem.attrib["permalink"],
                    "date": parse_date_posted(comment_elem.attrib["datecreate"]),
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
