import httpx
import pytest

from flickr_photos_api import (
    FlickrApi,
    FlickrApiException,
    InvalidApiKey,
    InvalidXmlException,
    ResourceNotFound,
    UnrecognisedFlickrApiException,
)


@pytest.mark.parametrize(
    ["method", "params"],
    [
        pytest.param(
            "get_user",
            {"user_url": "https://www.flickr.com/photos/DefinitelyDoesNotExist"},
            id="get_user_by_url",
        ),
        pytest.param(
            "get_user",
            {"user_id": "1234567@N00"},
            id="get_user_by_id",
        ),
        pytest.param(
            "get_single_photo",
            {"photo_id": "12345678901234567890"},
            id="get_single_photo",
        ),
        pytest.param(
            "get_single_photo",
            {"photo_id": "DefinitelyDoesNotExist"},
            id="get_single_photo_with_non_numeric_id",
        ),
        pytest.param(
            "get_photos_in_album",
            {
                "user_id": "-1",
                "album_id": "1234",
            },
            id="get_photos_in_album_with_missing_user",
        ),
        pytest.param(
            "get_photos_in_album",
            {
                "user_url": "https://www.flickr.com/photos/DefinitelyDoesNotExist",
                "album_id": "1234",
            },
            id="get_photos_in_album_with_missing_user_url",
        ),
        pytest.param(
            "get_photos_in_album",
            {
                "user_id": "12403504@N02",
                "album_id": "12345678901234567890",
            },
            id="get_photos_in_album_with_missing_album",
        ),
        pytest.param(
            "get_photos_in_gallery",
            {"gallery_id": "12345678901234567890"},
            id="get_photos_in_gallery",
        ),
        pytest.param(
            "get_photos_in_user_photostream",
            {"user_id": "-1"},
            id="get_public_photos_by_non_existent_user",
        ),
        pytest.param(
            "get_photos_in_group_pool",
            {"group_url": "https://www.flickr.com/groups/doesnotexist/pool/"},
            id="get_photos_in_non_existent_group_pool",
        ),
    ],
)
def test_methods_fail_if_not_found(
    api: FlickrApi, method: str, params: dict[str, str]
) -> None:
    api_method = getattr(api, method)

    with pytest.raises(ResourceNotFound):
        api_method(**params)


def test_it_throws_if_bad_auth(vcr_cassette: str, user_agent: str) -> None:
    api = FlickrApi(api_key="doesnotexist", user_agent=user_agent)

    with pytest.raises(FlickrApiException):
        api.get_user(user_url="https://www.flickr.com/photos/flickr/")


def test_empty_api_key_is_error(user_agent: str) -> None:
    with pytest.raises(
        ValueError, match="Cannot create a client with an empty string as the API key"
    ):
        FlickrApi(api_key="", user_agent=user_agent)


def test_invalid_api_key_is_error(user_agent: str) -> None:
    api = FlickrApi(api_key="<bad key>", user_agent=user_agent)

    with pytest.raises(InvalidApiKey) as err:
        api.get_single_photo(photo_id="52578982111")

    assert (
        err.value.args[0]
        == "Flickr API rejected the API key as invalid (Key has invalid format)"
    )

    # Note: we need to explicitly close the httpx client here,
    # or we get a warning in the 'setup' of the next test:
    #
    #     ResourceWarning: unclosed <ssl.SSLSocket fd=13, family=2,
    #     type=1, proto=0, laddr=('…', 58686), raddr=('…', 443)>
    #
    api.client.close()


def test_a_timeout_is_retried(api: FlickrApi) -> None:
    # This client throws a timeout error on the first GET request,
    # and then makes regular HTTP requests after that.
    class FlakyClient:
        def __init__(self, underlying: httpx.Client):
            self.underlying = underlying
            self.get_request_count = 0

        def get(self, url: str, params: dict[str, str], timeout: int) -> httpx.Response:
            self.get_request_count += 1

            if self.get_request_count == 1:
                raise httpx.ReadTimeout("The read operation timed out")
            else:
                return self.underlying.get(url=url, params=params, timeout=timeout)

    api.client = FlakyClient(underlying=api.client)  # type: ignore

    resp = api.get_photos_in_user_photostream(user_id="61270229@N05")

    assert len(resp["photos"]) == 10


def test_retries_5xx_error(api: FlickrApi) -> None:
    # The cassette for this test was constructed manually: I edited
    # an existing cassette to add a 500 response as the first response,
    # then we want to see it make a second request to retry it.
    resp = api.get_photos_in_user_photostream(user_id="61270229@N05")

    assert len(resp["photos"]) == 10


def test_a_persistent_5xx_error_is_raised(api: FlickrApi) -> None:
    # The cassette for this test was constructed manually: I copy/pasted
    # the 500 response from the previous test so that there were more
    # than it would retry.
    with pytest.raises(httpx.HTTPStatusError) as err:
        api.get_photos_in_user_photostream(user_id="61270229@N05")

    assert err.value.response.status_code == 500


def test_retries_invalid_xml_error(api: FlickrApi) -> None:
    # The cassette for this test was constructed manually: I edited
    # an existing cassette to add the invalid XML as the first response,
    # then we want to see it make a second request to retry it.
    resp = api.get_photos_in_user_photostream(user_id="61270229@N05")

    assert len(resp["photos"]) == 10


def test_a_persistent_invalid_xml_error_is_raised(api: FlickrApi) -> None:
    # The cassette for this test was constructed manually: I copy/pasted
    # the invalid XML from the previous test so that there were more
    # than it would retry.
    with pytest.raises(InvalidXmlException):
        api.get_photos_in_user_photostream(user_id="61270229@N05")


def test_retries_error_code_201(api: FlickrApi) -> None:
    # The cassette for this test was constructed manually: I edited
    # an existing cassette to add the invalid XML as the first response,
    # then we want to see it make a second request to retry it.
    resp = api.get_photos_in_user_photostream(user_id="61270229@N05")

    assert len(resp["photos"]) == 10


def test_a_persistent_error_201_is_raised(api: FlickrApi) -> None:
    # The cassette for this test was constructed manually: I edited
    # an existing cassette to add the invalid XML as the first response,
    # then we want to see it make a second request to retry it.
    with pytest.raises(UnrecognisedFlickrApiException) as exc:
        api.get_photos_in_user_photostream(user_id="61270229@N05")

    assert exc.value.args[0] == {
        "code": "201",
        "msg": "Sorry, the Flickr API service is not currently available.",
    }


def test_an_unrecognised_error_is_generic_exception(api: FlickrApi) -> None:
    with pytest.raises(UnrecognisedFlickrApiException) as exc:
        api.call(method="flickr.test.null")

    assert exc.value.args[0]["code"] == "99"


def test_error_code_1_is_unrecognised_if_not_found(api: FlickrApi) -> None:
    """
    This is a regression test for an old mistake, where we were mapping
    error code ``1`` a bit too broadly, and this call was throwing a
    ``ResourceNotFound`` exception, which is wrong.
    """
    with pytest.raises(UnrecognisedFlickrApiException) as exc:
        api.call(method="flickr.galleries.getListForPhoto")

    assert exc.value.args[0] == {"code": "1", "msg": "Required parameter missing"}
