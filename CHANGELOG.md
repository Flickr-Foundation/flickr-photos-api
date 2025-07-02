# CHANGELOG

## v3.11.2 - 2025-07-02

Refactor the retrying logic to make it more consistent between "API calls" and "downloading media files".

## v3.11.1 - 2025-06-20

When connecting to the Flickr API, retry `httpx.ConnectTimeout` exceptions.

## v3.11 - 2025-06-19

Add support for Creative Commons 4.0 licenses, which are [now supported on Flickr.com](https://blog.flickr.net/en/2025/06/18/creative-commons-4-0-has-arrived-on-flickr/).

## v3.10.1 - 2025-06-18

When downloading files with `download_file()`, retry HTTP 502 and other 5xx errors from Flickr.com.

## v3.10 - 2025-06-17

Add a new method `get_profile()` which returns profile information about a user.

If you are using an API client authenticated as that user, this includes their email address.

## v3.9.1 - 2025-06-17

Fix the instructions for using the new fixtures.

## v3.9 - 2025-06-17

This adds a new subpackage `flickr-photos-api[fixtures]` which has two pytest fixtures to use in tests:

*   `flickr_api` returns an instance of `FlickrApi` which authenticates using an API key
*   `flickr_oauth_api` returns an instance of `FlickrApi` which authenticates using OAuth

These fixtures record the request/response as "cassettes" using [vcrpy](https://vcrpy.readthedocs.io/en/latest/).
These cassettes can be checked into a Git repo, so you can replay the tests offline or when you don't have credentials available (e.g. in CI).

To use the new fixtures, add the following lines to your `conftest.py`:

```python
from flickr_api.fixtures import flickr_api, flickr_oauth_api
from nitrate.cassettes import cassette_name

__all__ = ["cassette_name", "flickr_api", "flickr_oauth_api"]
```

These fixtures have instructions explaining how to set up credentials when you want to record new Flickr API interactions.

## v3.8.4 - 2025-06-09

Fix a bug in the data returned from `list_commons_institutions()`.

## v3.8.3 - 2025-06-07

Fix a bug when getting EXIF data for photos with no "raw" EXIF value -- this is now returned as `None` rather than throwing an exception.

## v3.8.2 - 2025-06-02

Make sure all the models are described in `flickr_api.models.__all__`.

## v3.8.1 - 2025-05-23

Fix a bug where looking up people in a photo where a tagged person had a private realname would throw an error `KeyError: 'realname'`.

## v3.8 - 2025-05-20

Return information about the "editability" of a photo -- that is, whether you're allowed to add comments or metadata.

## v3.7.2 - 2025-05-07

Add a `PermissionDenied` exception for cases where users have chosen to hide their EXIF data.
See <https://www.flickrhelp.com/hc/en-us/articles/4404078521108-EXIF-data-FAQ>

## v3.7.1 - 2025-05-07

Tweak the `SinglePhotoInfo` model to make it more compatible with Pydantic.

## v3.7 - 2025-05-07

The new `get_exif_tags_for_photo()` method returns a list of EXIF tags for a photo.

## v3.6.1 - 2025-05-06

If you call `list_people_in_photo()` with a non-existent photo, it now throws a `ResourceNotFound` exception instead of `UnrecognisedFlickrApiException`.

## v3.6 - 2025-05-06

Return notes on photos from the `get_single_photo()` method.

## v3.5 - 2025-05-06

Return information about people tagged in photos:

*   The `get_single_photo()` method returns a new field: `has_people`
*   The new `list_people_in_photo()` returns a list of people tagged in a photo

There's also a small tweak to the way `list_all_comments()` works: rather than returning an `author_is_deleted` bool, there's now an optional `is_deleted` field on `author`.

## v3.4 - 2025-05-02

Return information about photo permissions: can you download, share, or print a photo.

## v3.3.1 - 2025-05-02

If you call `get_single_photo_sizes()` for a photo that doesn't exist, you now get a `ResourceNotFound` exception instead of `UnrecognisedFlickrApiException`.

## v3.3 - 2025-05-01

Add a new method `get_license_history(photo_id)`, which returns the license history of a photo with our nicely-typed `License` model.

## v3.2 - 2025-04-30

Return more information about photo locations.

*   The `LocationInfo` type has been replaced with `NumericLocation`, `NamedLocation`, and `Location`.
*   The `parse_location` function has been replaced with `parse_numeric_location` and `parse_named_location`.

## v3.1 - 2025-04-29

Expose the rotation of a photo in our `SinglePhoto` model (0°, 90°, 180°, 270°).

## v3.0 - 2025-04-29

This is a major refactor that splits the package into a couple of namespaces.

*   `flickr_api` contains the main API client, `download_file`, and the exceptions that the API client might throw
*   `flickr_api.models` contains type definitions for the data structures returned by the API
*   `flickr_api.parsers` contains functions that can convert raw values from the Flickr API into nicely-typed values. This is useful if you're calling the Flickr API in ways not handled by this library (e.g. to get collections of photos).

This library has grown organically and a lot of the stuff added in v2.x wasn't consistent -- it was a collection of code rammed together, but not always in the most ergonomic or useful way.
This major update is a bit of a reset, trying to make it easier to understand again.

## v2.21.0 - 2025-04-28

Remove the functions for getting a collection of photos:

* `get_photos_in_album`
* `get_photos_in_gallery`
* `get_photos_in_group_pool`
* `get_photos_in_user_photostream`
* `get_photos_with_tag`

In practice, it isn't actually useful to share code between projects -- these methods are too flexible for reuse to be sensible, e.g. each project needs a different set of `extras` to fetch.

## v2.20.0 - 2025-04-28

Remove the `get_photos_from_parsed_flickr_url()` method, which is no longer used in our projects.

## v2.19.0 - 2025-04-28

Remove the `get_photos_from_flickr_url()` method, which is no longer used in our projects.

## v2.18.0 - 2025-04-09

A couple of license-related improvements:

*   There's a new type `LicenseId` which is all the human-readable license IDs returned by this library.
*   You can now call `lookup_license_by_id()` with one of the human-readable license IDs returned by this library, not just the numeric ID.

## v2.17.2 - 2025-04-08

*   Tweak the type hint introduced in v2.17.0 to use a `Mapping` rather than a `dict`, which is a bit more flexible.

## v2.17.1 - 2025-04-08

*   Retry flaky errors *"Sorry, the Flickr API service is not currently available"* for any error code, not just error code 201.

## v2.17.0 - 2025-04-07

*   Change the type hint on `FlickrApi.call`, so now `params` can take `str` or `int` values, not just `str`.

    This means you can pass numeric values directly to the API, rather than casting them to `str` first -- for example:

    ```python
    FlickrApi.call(method="…", params={"page": 1, …})
    ```

    rather than:

    ```python
    FlickrApi.call(method="…", params={"page": str(1), …})
    ```

## v2.16.2 - 2025-02-28

*   Add an optional `client` argument to `download_file`, so you can supply your own `httpx.Client` if, for example, you want to override the User-Agent header.

## v2.16.1 - 2025-02-21

*   Retry transient `httpx.ConnectError` errors in `download_file()`.

## v2.16.0 - 2025-02-07

*   Replace the `download_photo()` function with `download_file()`, which:

    - Automatically chooses an appropriate extension based on the Content-Type header
    - Returns the Content-Type as part of the result

## v2.15.1 - 2025-02-07

*   Improve the type hints for `Size`, so now type checkers know that any photo size always has width/height.

## v2.15.0 - 2025-02-07

*   Add the `media` type to results (i.e. photo or video).

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
