"""Use the official SDL website for the pinned SDL2_image source archive.

The upstream python-for-android recipe is retained for all build and patch logic;
only its source URL is redirected away from the GitHub release endpoint.
"""
from pythonforandroid.recipes.sdl2_image import LibSDL2Image


class OfficialSDL2ImageRecipe(LibSDL2Image):
    url = "https://www.libsdl.org/projects/SDL_image/release/SDL2_image-{version}.tar.gz"


recipe = OfficialSDL2ImageRecipe()
