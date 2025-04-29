"""
Models for fields you get on photo objects.
"""

import typing


# When somebody uploads a photo to Flickr, they can choose to rotate it.
#
# As of April 2025, there are only four rotation options.
Rotation = typing.Literal[0, 90, 180, 270]
