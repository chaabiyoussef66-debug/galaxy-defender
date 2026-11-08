"""Use SDL's official release archive with a pinned SHA-512 digest.

The archive digest is independently published by NetBSD pkgsrc. The CI
preflight additionally verifies the upstream detached OpenPGP signature.
All upstream python-for-android build logic and patches remain unchanged.
"""
from pythonforandroid.recipes.sdl2_ttf import LibSDL2TTF


class VerifiedSDL2TTFRecipe(LibSDL2TTF):
    url = "https://www.libsdl.org/projects/SDL_ttf/release/SDL2_ttf-{version}.tar.gz"
    sha512sum = "b54e93b100712e3764cd80d4e4b16cd4c2a6853620f675941a4214320b0ee29a583d57ad56cd5fdb5c7a32d7615cbf43bc3fa55337b01623cee7219ebb43667c"


recipe = VerifiedSDL2TTFRecipe()
