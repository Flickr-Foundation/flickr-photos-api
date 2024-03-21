# CHANGELOG

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
