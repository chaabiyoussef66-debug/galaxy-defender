[app]

title = Galaxy Defender 2.4 Test

package.name = galaxydefender24test

package.domain = org.chaabi

source.dir = .

source.include_exts = py,txt,png,jpg,jpeg,wav,ogg,ttf

version = 2.4.1

requirements = python3,pygame

orientation = landscape

fullscreen = 1

android.permissions = INTERNET

android.api = 33

android.minapi = 24

android.ndk = 25b

android.ndk_api = 24

android.archs = arm64-v8a

p4a.bootstrap = sdl2

p4a.branch = v2024.01.21

p4a.local_recipes = ./p4a-recipes

[buildozer]

log_level = 2

warn_on_root = 1
