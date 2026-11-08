"""Pinned OpenSSL 1.1.1w recipe using a verified upstream mirror.

The upstream python-for-android recipe remains the source of all build logic.
Only the archive endpoint is changed, and the official SHA-256 is enforced
by python-for-android's standard recipe downloader before extraction.
"""
from pythonforandroid.recipes.openssl import OpenSSLRecipe


class OpenSSL111wMirrorRecipe(OpenSSLRecipe):
    url = "https://mirror.math.princeton.edu/pub/openssl/source/openssl-{url_version}.tar.gz"
    sha256sum = "cf3098950cb4d853ad95c0841f1f9c6d3dc102dccfcacd521d93925208b76ac8"


recipe = OpenSSL111wMirrorRecipe()
