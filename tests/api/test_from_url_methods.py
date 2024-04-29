import typing

import pytest

from flickr_photos_api import (
	FlickrApi as FlickrPhotosApi,

)
from flickr_photos_api.types import (
	CollectionOfPhotos2,
	PhotosInAlbum2,
	PhotosInGallery2,
	PhotosInGroup2,
	SinglePhoto,
)
from utils import get_fixture


T = typing.TypeVar("T")


@pytest.mark.parametrize(
	["url", "filename", "model"],
	[
		pytest.param(
			"https://www.flickr.com/photos/coast_guard/32812033543",
			"32812033543.json",
			SinglePhoto,
			id="single_photo",
		),
		pytest.param(
			"https://www.flickr.com/photos/joshuatreenp/albums/72157640898611483",
			"album-72157640898611483.json",
			PhotosInAlbum2,
			id="album",
		),
		pytest.param(
			"https://www.flickr.com/photos/joshuatreenp/albums/72157640898611483/page2",
			"album-72157640898611483-page2.json",
			PhotosInAlbum2,
			id="album-page2",
		),
		pytest.param(
			"https://www.flickr.com/photos/spike_yun/",
			"user-spike_yun.json",
			CollectionOfPhotos2,
			id="user",
		),
		pytest.param(
			"https://www.flickr.com/photos/meldaniel/galleries/72157716953066942/",
			"gallery-72157716953066942.json",
			PhotosInGallery2,
			id="gallery",
		),
		pytest.param(
			"https://www.flickr.com/groups/geologists/",
			"group-geologists.json",
			PhotosInGroup2,
			id="group",
		),
		pytest.param(
			"https://www.flickr.com/photos/tags/botany",
			"tag-botany.json",
			CollectionOfPhotos2,
			id="tag",
		),
	],
)
def test_get_photos_from_flickr_url(
	api: FlickrPhotosApi, url: str, filename: str, model: type[T]
) -> None:
	photos = api.get_photos_from_flickr_url(url)

	from nitrate.json import DatetimeEncoder
	import json

	with open(f"tests/fixtures/api_responses/{filename}", "w") as of:
		of.write(json.dumps(photos, indent=2, sort_keys=True, cls=DatetimeEncoder))

	assert photos == get_fixture(filename, model=model)


@pytest.mark.parametrize(
	"url",
	[
		pytest.param(
			"https://www.flickr.com/photos/joshuatreenp/albums/72157640898611483",
			id="album",
		),
		pytest.param("https://www.flickr.com/photos/spike_yun", id="user"),
		pytest.param(
			"https://www.flickr.com/photos/meldaniel/galleries/72157716953066942",
			id="gallery",
		),
		pytest.param("https://www.flickr.com/groups/geologists/pool", id="group"),
		pytest.param("https://www.flickr.com/photos/tags/botany", id="tag"),
	],
)
def test_get_photos_from_flickr_url_is_paginated(
	api: FlickrPhotosApi, url: str
) -> None:
	first_resp = api.get_photos_from_flickr_url(url)
	second_resp = api.get_photos_from_flickr_url(url + "/page2")

	assert first_resp["photos"] != second_resp["photos"]  # type: ignore


def test_unrecognised_url_type_is_error(api: FlickrPhotosApi) -> None:
	with pytest.raises(TypeError, match="Unrecognised URL type"):
		api.get_photos_from_parsed_flickr_url(parsed_url={"type": "unknown"})  # type: ignore
