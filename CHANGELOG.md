# CHANGELOG

## v2.14.5 - 2025-02-06

*   Improve the error messages from `UserMethods`, so if you try to look up an unrecognized URL, they actually include the URL in the error text.

## v2.14.4 - 2025-01-16

*   Expose a couple more methods on `SinglePhotoMethods` as part of the public API, for easier reuse and extension.

## v2.14.3 - 2025-01-16

*   Internal refactoring to expose a `parse_single_photo_info` method, for callers who want to customise their calls to `flickr.photos.getInfo`.

## v2.14.2 - 2025-01-15

*   The `download_photo` function can retry more types of timeout.
    It also uses a shared HTTP client for all downloads, which should make it a bit faster and more reliable.

## v2.14.1 - 2025-01-14

*   The `download_photo` function will now retry if the request times out.

## v2.14.0 - 2024-12-16

*   Add a new function `download_photo` for actually downloading a photo from Flickr.
    This includes some logic for retrying downloads if they fail due to e.g. Flickr's rate limits.

## v2.13.0 - 2024-12-16

*   Change a license ID from `in-copyright` to `all-rights-reserved`, which is a better description of what it means.

## v2.12.0 - 2024-10-31

*   The `url` of a `CommonsInstitution` is now optional rather than required.

## v2.11.2 - 2024-09-02

*   Change the `UserInfo` type so it can be subclassed again (this broke in v2.10.0).
    This doesn't change the output/behaviour of the library.

## v2.11.1 - 2024-09-02

*   Internal refactoring for Flickr Foundation purposes; no public-facing changes.

## v2.11.0 - 2024-08-30

*   Add a `location: str | None` to the `UserInfo` type.

    When you look up a user with `get_user(user_id)` and that user has a public location, it will be returned in the response.

    If you look up a user who doesn't have a location, or their location is private, this value will be `None`.

## v2.10.0 - 2024-08-28

*   Add a `pro_account_expires: datetime.datetime` to the `UserInfo` type.

    When you look up a user with `get_user(user_id)` and that user has Flickr Pro, you'll be able to see when their Flickr Pro subscription expires.

    If you look up a user who doesn't have Flickr Pro, you won't get the `pro_account_expires` field.

## v2.9.0 - 2024-08-13

*   Remove the `get_buddy_icon_url(user_id)` method.

    Instead, call `get_user(user_id)` and read the `buddy_icon_url` parameter from the response.

    If you already have a result from `get_user(user_id)`, use that to save yourself an API call.

## v2.8.1 - 2024-08-07

*   Internal refactoring to make it slightly easier to "override" user `realname` values that get returned from the API.

## v2.8.0 - 2024-07-25

*   Add support for visibility.

    When you look up a single photo with `get_single_photo()`, it now returns information about the photo's visibility (is it public, private, friends/family only).

## v2.7.0 - 2024-07-24

*   Add support for raw tags.

    When you look up a single photo with `get_single_photo()`, it now returns the raw tag values and other tag information in the `raw_tags` field.

## v2.6.2 - 2024-07-23

*   Fix the name of the Stockholm Transport Museum when looked up using this library.

## v2.6.1 - 2024-07-05

*   Don't throw an `AssertionError` when looking up photos with a tag which is the empty string.

## v2.6.0 - 2024-07-02

*   Add a custom exception for private photos

    If you try to look up a private photo with `get_single_photo()`, it throws a new `PhotoIsPrivate` exception rather than a `UnrecognisedFlickrApiException`.

## v2.5.2 - 2024-06-28

*   Flatten the definition of `MachineTags`, to simplify queries for a namespace/predicate pair.

## v2.5.1 - 2024-06-28

*   Export the new `MachineTags` type as a top-level type.
    It can be imported as `from flickr_photos_api import MachineTags`.

## v2.5.0 - 2024-06-28

*   Add support for machine tags

    Machine tags will now be parsed in the list of tags, and presented as a structured object in the `machine_tags` field.
    This does not change the existing `tags` field, just provide a convenient way to query machine tags.

## v2.4.1 - 2024-06-13

*   Fix a bug in the new `post_comment()` method.

    If you try to post a comment on a photo that doesn't exist, you now get a `ResourceNotFound` exception rather than an `UnrecognisedFlickrApiException`.

## v2.4.0 - 2024-06-13

*   The constructor on `FlickrApi` has changed.

    Previously:

    ```
    from flickr_photos_api import FlickrApi

    FlickrApi(api_key: str, user_agent: str)
    ```

    Now:

    ```
    from flickr_photos_api import FlickrApi

    FlickrApi(client: httpx.Client)
    FlickrApi.with_api_key(api_key: str, user_agent: str)
    ```

    This is to make the underlying HTTP client a bit more flexible.

*   There's a new method on `FlickrApi`: `post_comment(photo_id: str, comment_text: str)`.

    This allows you to post comments on Flickr photos, if you pass an HTTPX client that has OAuth 1.0a set up with Flickr.
    See the tests for an example of how this works.

## v2.3.4 - 2024-05-24

*   Retry every error that returns a 5xx status code, not just 500.

    For example, a `502 Bad Gateway` error will now be retried where previously it would fail immediately.

## v2.3.3 - 2024-05-23

*   Retry "Server disconnected without sending a response" errors from the Flickr API.

## v2.3.2 - 2024-05-23

*   Retry "connection reset by peer" errors from the Flickr API.

## v2.3.1 - 2024-05-21

*   Remove irrelevant information from the traceback shown when the library throws a `UnrecognisedFlickrApiException`.
    [#64](https://github.com/Flickr-Foundation/flickr-photos-api/issues/64)

## v2.3.0 - 2024-05-01

*   Add a new method `get_photo_contexts(photo_id)` which returns information about all the contexts where this photo appears -- albums, galleries, and groups.
*   Improve the way error codes from the Flickr API are handled. If you're calling the library, this means you'll get more human-readable error messages. If you're working on the library, you have more flexibility in how error codes are mapped to Python exceptions.
*   Fix a bug where getting photos from the photostream of a user who didn't have a `realname` set would throw a `KeyError`.

## v2.2.0 - 2024-05-01

This adds a new method `list_commons_institutions()` which returns a list of all the institutions in [the Flickr Commons](https://commons.flickr.org).

## v2.1.2 - 2024-05-01

Get rid of the `SinglePhotoWithSizes` type and roll back to the `SinglePhoto` type, which maintains better back-compatibility.

## v2.1.1 - 2024-04-30

Export the `SinglePhotoInfoWithSizes` type.

## v2.1.0 - 2024-04-30

This changes the way you specify a user.  The following methods now take a `user_id` or `user_url` parameter:

-   `get_user()` (replacing `lookup_user_by_id()` and `lookup_user_by_url()`)
-   `get_photos_in_album()`
-   `get_photos_in_user_photostream()`

This makes things a bit simpler for callers, which can specify a user in either form.

## v2.0.1 - 2024-04-30

This slightly refines the list of available exceptions:

-   The `lookup_user_by_id()` and `lookup_user_by_url()` methods can now throw a new `UserDeleted` exception if you try to look up a Flickr user who's deleted their account.
-   An error with an unrecognised code will now throw `UnrecognisedFlickrApiException` instead of `FlickrApiException`.
    This should make it easier to distinguish and handle unrecognised errors.

## v2.0.0 - 2024-04-30

This is a fairly major internal refactor to make the library easier to work on.
The `FlickrPhotosApi` class has been renamed to `FlickrApi` and split up to make it easier to extend with new methods in future.

I've also removed some of the worst over-abstraction, trading code simplicity for slightly less efficiency.

## v1.14.1 - 2024-04-29

*   The `lookup_user_by_url()` function is slightly faster when the URL contains a Flickr user ID rather than a path alias.
    The function behaves the same as before, but now it avoids an unnecessary lookup.
*   The `get_photos_in_album()` function is slightly faster, because it skips an unnecessary lookup to get the album title.

## v1.14.0 - 2024-04-29

*   More internal refactoring.

## v1.13.0 - 2024-04-29

*   Add a new method `get_single_photo_sizes()` which wraps all the information returned by the `flickr.photos.getSizes` API.

## v1.12.0 - 2024-04-29

*   Add a new method `get_single_photo_info()` which wraps all the information returned by the `flickr.photos.getInfo` API.

## v1.11.0 - 2024-04-23

*   Refactor the internals to expose a couple of new methods for getting a single page or a continuous stream of photos.

    This should eventually allow callers to be much more specific about what `extras` and fields they want to retrieve.

## v1.10.1 - 2024-04-17

*   Fix a bug in `list_all_comments()` for comments where the commenter has no realname set in their profile – it now returns `None` for `authorname` instead of an empty string.

## v1.10.0 - 2024-04-09

*   Add a new method `list_all_comments(photo_id: str) -> list[Comment]` which returns a list of all the comments on a photo.

## v1.9.2 - 2024-04-02

*   Tweak the retrying on flaky API calls to (i) retry up to 5 times, up from 1 and (ii) use an exponential backoff to wait between retries.  Both of these should make it more likely that a flaky API call will eventually succeed.

## v1.9.1 - 2024-03-26

*   Remember to expose the `UserInfo` type at the top level.
    Now you can import it as `from flickr_photos_api import UserInfo`.

## v1.9.0 - 2024-03-26

*   Return more information from the `lookup_user_by_id()` and `lookup_user_by_url()` methods.

    In particular, they now return a new type `UserInfo` which includes three new fields:

    - `count_photos` (int)
    - `description` (str or None)
    - `has_pro_account` (bool)

## v1.8.2 - 2024-03-26

*   Retry errors with code 201 from the Flickr API, which usually indicates a transient issue rather than a permanent failure.
    This should make using the API slightly more reliable.

## v1.8.1 - 2024-03-21

*   Fix a bug where looking up videos could throw a ValueError.

## v1.8.0 - 2024-01-09

*   Fix a bug where some photos would be returned with location information, even though the location accuracy is `0`, which means it's so vague as to be unusable.
*   Reshuffle some of the internal utility methods to make them slightly easier to reuse in downstream code.

## v1.7.0 - 2024-01-04

*   Add a new exception `InvalidXmlException` which is thrown when the Flickr API returns a response which isn't valid XML.  The error will be retried up to three times in case it's a transient error, and if not, the offending XML is included in the error message.

## v1.6.0 - 2023-12-27

*   Add a new method `lookup_user_by_id` for looking up users with their NSID.
    This allows for slightly faster lookups in cases where you already have the user's NSID, compared to `lookup_user_by_url`.

## v1.5.7 - 2023-12-22

*   Slightly improve the error message you get if you pass an invalid API key.

## v1.5.6 - 2023-12-22

*   Fix another bug in the handling of "date taken" when the value returned by the Flickr API is unusable, e.g. `0000-01-01 00:00:00`.

## v1.5.5 - 2023-12-21

*   Expand the retrying logic, so read timeouts will also be retried up to three times before failing.

## v1.5.4 - 2023-12-21

*   Add some basic retrying logic to the client.
    If you get a 500 Internal Server Error from the Flickr API, the request will now be retried up to three times before failing.

    All other errors will raise immediately.

## v1.5.3 - 2023-12-21

*   Provide a better error when you pass an empty string as a Flickr API key.
    Now it will fail when you create the client, whereas previously it would fail with an `Invalid API Key` error when you tried to call the Flickr API.

## v1.5.2 - 2023-12-19

*   Fix a bug in the handling of "date taken" when the value returned by the Flickr API is `0000-00-00 00:00:00`.

## v1.5.1 - 2023-12-19

*   Discard location information with an accuracy level of `0`, which seems to mean "so vague as to be meaningless".

## v1.5.0 - 2023-12-19

*   Add a method `get_buddy_icon_url(user_id: str)` for retrieving the buddy icon of a user.

## v1.4.0 - 2023-12-18

*   Bump the minimum Python version to 3.12.
*   Slightly rejig the "date_taken" field – it now returns `None` if the taken date is unknown, rather than `{"unknown": True}`.

## v1.3.1 - 2023-11-15

Expose the `LocationInfo` type introduced in v1.3.0 as part of the top-level module.

## v1.3.0 - 2023-11-15

Fetch user tags and location data from the Flickr APi.

## v1.2.0 - 2023-11-10

Add a `path_alias` field to the `User` model.

## v1.1.0 - 2023-11-09

Add a method `get_photos_from_flickr_url()` which can get all the photos from behind a particular URL on Flickr.com.

## v1.0.4 - 2023-11-07

Export a few additional types as part of the top-level module.

## v1.0.3 - 2023-11-06

Export a few additional types as part of the top-level module.

## v1.0.2 - 2023-11-05

Export the exceptions and types as part of the top-level module.

## v1.0.1 - 2023-11-05

Fix a bug with the type definitions on Python 3.7.

## v1.0.0 - 2023-11-05

Initial public release.
