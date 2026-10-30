[app]

title = Galaxy Defender Ultimate
package.name = galaxydefender
package.domain = org.chaabi

source.dir = .
source.include_exts = py,txt,png,jpg,jpeg,wav,ogg

version = 2.0

requirements = python3,kivy,pygame

orientation = landscape
fullscreen = 1

android.permissions = INTERNET

android.api = 35
android.minapi = 23
android.archs = arm64-v8a

p4a.bootstrap = sdl2

[buildozer]

log_level = 2
warn_on_root = 1
