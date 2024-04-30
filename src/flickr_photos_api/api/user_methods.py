"""
Methods for getting information about users from the Flickr API.
"""

import functools

from flickr_url_parser import NotAFlickrUrl, UnrecognisedUrl, parse_flickr_url
from nitrate.xml import find_optional_text, find_required_elem, find_required_text

from .base import FlickrApi
from ..exceptions import UnrecognisedFlickrApiException, UserDeleted
from ..types import UserInfo


class UserMethods(FlickrApi):
    def _ensure_user_id(
        self, *, user_id: str | None = None, user_url: str | None = None
    ) -> str:
        """
        This is a bit of syntactic sugar to help functions take user ID
        in two forms:

        -   As a ``user_id`` parameter, with a user's NSID
        -   As a ``user_url`` parameter, with a link to a user's profile picture

        This function will resolve the two parameters down to a single
        unambiguous ID which can be passed to the Flickr API.
        """
        # Check we got exactly one of `user_id` and `user_url`
        if user_id is None and user_url is None:
            raise TypeError("You must pass one of `user_id` or `user_url`!")

        if user_id is not None and user_url is not None:
            raise TypeError("You can only pass one of `user_id` and `user_url`!")

        # If we got a `user_id`, we're done
        if user_id is not None:
            return user_id

        assert user_url is not None

        # Try to parse the user URL as a Flickr URL.  What we're looking
        # to see is whether the URL contains the NSID already, e.g.
        # https://www.flickr.com/photos/51979177@N02
        #
        # If it does, we're done.  If not, we can pass the whole URL to
        # Flickr to see what the NSID is.
        try:
            parsed_user_url = parse_flickr_url(user_url)

            if parsed_user_url["type"] != "user":
                raise ValueError(
                    "user_url was not the URL for a Flickr user: {user_url!r}"
                )
        except (NotAFlickrUrl, UnrecognisedUrl):
            raise ValueError("user_url was not the URL for a Flickr user: {user_url!r}")

        assert parsed_user_url["type"] == "user"

        if parsed_user_url["user_id"]:
            return parsed_user_url["user_id"]
        else:
            return self._lookup_user_id_for_user_url(user_url=user_url)

    def get_user(
        self, *, user_id: str | None = None, user_url: str | None = None
    ) -> UserInfo:
        """
        Given the ID of a user or a link to their profile, return their info.

            >>> api.get_user(user_id="12403504@N02")
            {
                "id": "12403504@N02",
                "username": "The British Library",
                "realname": "British Library",
                "photos_url": "https://www.flickr.com/photos/britishlibrary/",
                "profile_url": "https://www.flickr.com/people/britishlibrary/",
                "pathalias": "britishlibrary",
                "description": "The British Library’s collections…",
                "has_pro_account": True,
                "count_photos": 1234,
            }

            >>> api.get_user(user_url="https://www.flickr.com/people/britishlibrary/")
            {
                "id": "12403504@N02",
                ...
            }

        See https://www.flickr.com/services/api/flickr.people.getInfo.htm
        """
        user_id = self._ensure_user_id(user_id=user_id, user_url=user_url)

        return self._get_user(user_id=user_id)

    def _get_user(self, *, user_id: str) -> UserInfo:
        """
        Given the link to a user's photos or profile, return their info.

            >>> api.lookup_user_by_id(user_id="12403504@N02")
            {
                "id": "12403504@N02",
                "username": "The British Library",
                "realname": "British Library",
                "photos_url": "https://www.flickr.com/photos/britishlibrary/",
                "profile_url": "https://www.flickr.com/people/britishlibrary/",
                "pathalias": "britishlibrary",
                "description": "The British Library’s collections…",
                "has_pro_account": True,
                "count_photos": 1234,
            }

        See https://www.flickr.com/services/api/flickr.people.getInfo.htm

        """
        # The getInfo response is of the form:
        #
        #     <person id="12403504@N02" path_alias="britishlibrary" …>
        #       <username>The British Library</username>
        #       <realname>British Library</realname>
        #       <description>The British Library’s collections…</description>
        #       <photosurl>flickr.com/photos/britishlibrary/</photosurl>
        #       <profileurl>flickr.com/people/britishlibrary/</profileurl>
        #       <photos>
        #         <count>1234</count>
        #       </photos>
        #       …
        #     </person>
        #
        try:
            info_resp = self.call(
                method="flickr.people.getInfo", params={"user_id": user_id}
            )
        except UnrecognisedFlickrApiException as exc:
            if exc.args[0]["code"] == "5":
                raise UserDeleted(user_id)
            else:
                raise

        person_elem = find_required_elem(info_resp, path="person")

        username = find_required_text(person_elem, path="username")
        photos_url = find_required_text(person_elem, path="photosurl")
        profile_url = find_required_text(person_elem, path="profileurl")
        description = find_optional_text(person_elem, path="description")

        path_alias = person_elem.attrib["path_alias"] or None

        photos_elem = find_required_elem(person_elem, path="photos")
        count_photos = int(find_required_text(photos_elem, path="count"))

        # This is a 0/1 boolean attribute
        has_pro_account = person_elem.attrib["ispro"] == "1"

        # If the user hasn't set a realname in their profile, the element
        # will be absent from the response.
        realname_elem = person_elem.find(path="realname")

        if realname_elem is None:
            realname = None
        else:
            realname = realname_elem.text

        return {
            "id": user_id,
            "username": username,
            "realname": realname,
            "description": description,
            "has_pro_account": has_pro_account,
            "path_alias": path_alias,
            "photos_url": photos_url,
            "profile_url": profile_url,
            "count_photos": count_photos,
        }

    def _lookup_user_id_for_user_url(self, *, user_url: str) -> str:
        """
        Given the URL to a user's profile page, return their user ID.

            >>> api._lookup_user_id_for_user_url(
            ...     user_url="https://www.flickr.com/photos/britishlibrary/")
            "12403504@N02"

        See https://www.flickr.com/services/api/flickr.urls.lookupUser.htm

        This method is only meant for internal use.
        """
        # The lookupUser response is of the form:
        #
        #       <user id="12403504@N02">
        #       	<username>The British Library</username>
        #       </user>
        #
        lookup_resp = self.call(
            method="flickr.urls.lookupUser", params={"url": user_url}
        )
        user_id = find_required_elem(lookup_resp, path=".//user").attrib["id"]

        return user_id

    # We cache these because they're unlikely to change that often, and showing
    # a stale user icon occasionally isn't a big deal.
    #
    # TODO: We already use the ``flickr.people.getInfo`` method elsewhere -- could we
    # cache the buddy icon URL there, and delete this method?
    @functools.lru_cache(maxsize=128)
    def get_buddy_icon_url(self, *, user_id: str) -> str:
        """
        Returns the URL of a user's "buddy icon".

        See https://www.flickr.com/services/api/misc.buddyicons.html
        """
        resp = self.call(method="flickr.people.getInfo", params={"user_id": user_id})

        person_elem = find_required_elem(resp, path="person")

        iconserver = int(person_elem.attrib["iconserver"])
        iconfarm = int(person_elem.attrib["iconfarm"])

        if iconserver > 0:
            return f"https://farm{iconfarm}.staticflickr.com/{iconserver}/buddyicons/{user_id}.jpg"
        else:
            return "https://www.flickr.com/images/buddyicon.gif"
