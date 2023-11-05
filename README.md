# flickr-photos-api

This is a library for getting information about photos from the Flickr API.

It's not a general-purpose Flickr API library.
Instead, it focuses on providing information about photos and photo collections.
It tries to abstract away some of the details of the Flickr API -- for example, licenses are returned as complete dictionaries, rather than as the numeric license IDs returned by Flickr API methods.

Examples:

```console
>>> from flickr_photos_api import FlickrPhotosApi
>>> api = FlickrPhotosApi(api_key="…", user_agent="…")

>>> photo = api.get_single_photo(photo_id="14898030836")

>>> photo
{'id': '14898030836', 'title': 'NASA Scientists Says', …}

>>> photo["license"]
{'id': 'cc-by-2.0', 'label': 'CC BY 2.0', 'url': 'https://creativecommons.org/licenses/by/2.0/'}

>>> photo["url"]
'https://www.flickr.com/photos/lassennps/14898030836/'
```

This library was created for use in [Flinumeratr](), [Flickypedia], and other [Flickr Foundation] projects.

[Flinumeratr]: https://github.com/Flickr-Foundation/flinumeratr
[Flickypedia]: https://commons.wikimedia.org/wiki/Commons:Flickypedia
[Flickr Foundation]: https://www.flickr.org/

## Usage

1.  Install flickr-photos-api from PyPI:

    ```console
    $ pip install flickr-photos-api
    ```

2.  Construct an instance of `FlickrPhotosApi`.
    You need to pass a user-agent that identifies you, and a [Flickr API key][key].
    
    ```python
    from flickr_photos_api import FlickrPhotosApi
    
    api = FlickrPhotosApi(api_key="…", user_agent="…")
    ```

3.  Call methods on FlickrPhotosApi.
    The methods meant for public use are:
    
    ```python
    def get_single_photo(photo_id: str) -> SinglePhoto: ...
  
    def get_photos_in_album(user_url: str, album_id: str) -> PhotosInAlbum: ...
  
    def get_photos_in_gallery(gallery_id: str) -> PhotosInGallery: ...
  
    def get_public_photos_by_user(user_url: str) -> CollectionOfPhotos: ...
  
    def get_photos_in_group_pool(group_url: str) -> PhotosInGroup: ...
    
    def get_photos_with_tag(tag: str) -> CollectionOfPhotos: ...
    ```
    
    Methods that return collections of photos also support `page` and `per_page` parameters to control pagination.

[key]: https://www.flickr.com/services/api/misc.api_keys.html

## Development

You can set up a local development environment by cloning the repo and installing dependencies:

```console
$ git clone https://github.com/Flickr-Foundation/flickr-photos-api.git
$ cd flickr-photos-api
$ python3 -m venv .venv
$ source .venv/bin/activate
$ pip install -e .
```

If you want to run tests, install the dev dependencies and run py.test:

```console
$ source .venv/bin/activate
$ pip install -r dev_requirements.txt
$ coverage run -m pytest tests
$ coverage report
```

To make changes to the library:

1.  Create a new branch
2.  Push your changes to GitHub
3.  Open a pull request
4.  Fix any issues flagged by GitHub Actions (including tests, code linting, and type checking)
5.  Ask somebody to review your change
6.  Merge it!

To create a new version on PyPI:

1.  Update the version in `src/flickr_photos_api/__init__.py`
2.  Add release notes in `CHANGELOG.md` and push a new tag to GitHub
3.  Deploy the release using twine:

    ```console
    $ python3 -m build
    $ python3 -m twine upload dist/* --username=__token__
    ```
    
    You will need [a PyPI API token](https://pypi.org/help/#apitoken) to publish packages.
    This token is stored in 1Password.

## License

This project is dual-licensed as Apache-2.0 and MIT.
