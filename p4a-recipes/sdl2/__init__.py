"""Use the official SDL release archive for the pinned SDL2 source.

Keep python-for-android's original SDL2 build logic and checksum; only
redirect the source URL away from the GitHub release endpoint.
"""
from pythonforandroid.recipes.sdl2 import LibSDL2Recipe


class OfficialSDL2Recipe(LibSDL2Recipe):
    url = "https://www.libsdl.org/release/SDL2-{version}.tar.gz"


recipe = OfficialSDL2Recipe()
