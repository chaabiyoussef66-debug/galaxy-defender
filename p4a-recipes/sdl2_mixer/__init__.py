"""Use the official SDL website for the pinned SDL2_mixer source archive.

The upstream python-for-android recipe is retained for all build logic;
only its source URL is redirected away from the GitHub release endpoint.
"""
from pythonforandroid.recipes.sdl2_mixer import LibSDL2Mixer


class OfficialSDL2MixerRecipe(LibSDL2Mixer):
    url = "https://www.libsdl.org/projects/SDL_mixer/release/SDL2_mixer-{version}.tar.gz"


recipe = OfficialSDL2MixerRecipe()
