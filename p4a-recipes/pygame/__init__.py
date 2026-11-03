from pathlib import Path

from pythonforandroid.recipes.pygame import Pygame2Recipe


class Pygame261Recipe(Pygame2Recipe):
    version = "2.6.1"
    url = "https://github.com/pygame/pygame/archive/{version}.tar.gz"
    hostpython_prerequisites = ["setuptools", "cython>=3.1"]

    def prebuild_arch(self, arch):
        super().prebuild_arch(arch)

        build_dir = Path(self.get_build_dir(arch.arch))

        # Cython already initializes the extension type's __dict__.
        # Assigning to self.__dict__ in pygame 2.6.1 is rejected by
        # current Cython versions, so replace that redundant assignment.
        sprite_file = (
            build_dir
            / "src_c"
            / "cython"
            / "pygame"
            / "_sprite.pyx"
        )
        source = sprite_file.read_text(encoding="utf-8")
        old_line = "        self.__dict__ = {}"
        if old_line not in source:
            raise RuntimeError(
                "Expected pygame 2.6.1 _sprite.pyx line was not found; "
                "refusing to apply an unverified patch."
            )

        sprite_file.write_text(
            source.replace(old_line, "        pass", 1),
            encoding="utf-8",
        )

        # pygame 2.6.1's Android SDL2 template omits the SIMD blitter
        # translation units. surface.so then links with unresolved
        # blitter symbols and fails to load on real ARM devices, even
        # though the APK build itself succeeds.
        setup_file = build_dir / "buildconfig" / "Setup.Android.SDL2.in"
        template = setup_file.read_text(encoding="utf-8")
        old_surface = (
            "surface src_c/surface.c src_c/alphablit.c "
            "src_c/surface_fill.c $(SDL) $(DEBUG)"
        )
        new_surface = (
            "surface src_c/surface.c src_c/alphablit.c "
            "src_c/surface_fill.c src_c/simd_blitters_sse2.c "
            "src_c/simd_blitters_avx2.c $(SDL) $(DEBUG)"
        )
        if new_surface not in template:
            if old_surface not in template:
                raise RuntimeError(
                    "Expected pygame Android surface template line was not "
                    "found; refusing to apply an unverified SIMD patch."
                )
            for source_name in (
                "simd_blitters_sse2.c",
                "simd_blitters_avx2.c",
            ):
                if not (build_dir / "src_c" / source_name).is_file():
                    raise RuntimeError(
                        f"Required pygame SIMD source is missing: {source_name}"
                    )
            setup_file.write_text(
                template.replace(old_surface, new_surface, 1),
                encoding="utf-8",
            )


recipe = Pygame261Recipe()
