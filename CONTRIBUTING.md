# CONTRIBUTING

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

1.  Update the version in `src/flickr_api/__init__.py`
2.  Add release notes in `CHANGELOG.md` and push a new tag to GitHub
3.  Deploy the release using twine:

    ```console
    $ python3 -m build
    $ python3 -m twine upload dist/* --username=__token__
    ```

    You will need [a PyPI API token](https://pypi.org/help/#apitoken) to publish packages.
    This token is stored in 1Password.
