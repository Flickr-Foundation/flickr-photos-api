"""
Methods for getting information about comments from the Flickr API.
"""

from .base import FlickrApi
from ..types import Comment, User
from ..utils import parse_date_posted


class CommentMethods(FlickrApi):
    def list_all_comments(self, *, photo_id: str) -> list[Comment]:
        """
        List all the comments on a photo.

        See https://www.flickr.com/services/api/flickr.photos.comments.getList.htm
        """
        resp = self.call(
            method="flickr.photos.comments.getList", params={"photo_id": photo_id}
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
            author_id = comment_elem.attrib["author"]
            author_path_alias = comment_elem.attrib["path_alias"] or None

            author: User = {
                "id": author_id,
                "username": comment_elem.attrib["authorname"],
                "realname": comment_elem.attrib["realname"] or None,
                "path_alias": author_path_alias,
                "photos_url": f"https://www.flickr.com/photos/{author_path_alias or author_id}/",
                "profile_url": f"https://www.flickr.com/people/{author_path_alias or author_id}/",
            }

            result.append(
                {
                    "id": comment_elem.attrib["id"],
                    "photo_id": photo_id,
                    "author_is_deleted": comment_elem.attrib["author_is_deleted"]
                    == "1",
                    "author": author,
                    "text": comment_elem.text or "",
                    "permalink": comment_elem.attrib["permalink"],
                    "date": parse_date_posted(comment_elem.attrib["datecreate"]),
                }
            )

        return result
