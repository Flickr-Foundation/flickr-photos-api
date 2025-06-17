"""
Fixtures and utilities to use in the tests.
"""

from flickr_api.fixtures import flickr_api, flickr_oauth_api
from nitrate.cassettes import cassette_name, vcr_cassette


__all__ = ["cassette_name", "flickr_api", "flickr_oauth_api", "vcr_cassette"]
