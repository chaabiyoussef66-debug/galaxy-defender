from pathlib import Path
import subprocess
import sys

from pythonforandroid.recipes.pygame import Pygame2Recipe


class Pygame261Recipe(Pygame2Recipe):
    version = "2.6.1"
    url = "https://github.com/pygame/pygame/archive/{version}.tar.gz"

    def prebuild_arch(self, arch):
        build_dir = Path(self.get_build_dir(arch.arch))

        # Generate the Android Setup file from the patched SDL2 template.
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

        # Generate Setup using the patched template.
        super().prebuild_arch(arch)

        # Cython already initializes the extension type's __dict__.
        # Assigning to self.__dict__ is rejected by current Cython.
        sprite_file = (
            build_dir / "src_c" / "cython" / "pygame" / "_sprite.pyx"
        )
        source = sprite_file.read_text(encoding="utf-8")
        old_line = "        self.__dict__ = {}"
        if old_line in source:
            sprite_file.write_text(
                source.replace(old_line, "        pass", 1),
                encoding="utf-8",
            )

        # IMPORTANT:
        # p4a builds pygame using its private HostPython. Cython installed
        # on the GitHub runner is NOT installed in that private interpreter.
        # Compile the .pyx sources now with the runner Python (which has
        # Cython 3.1.2), so pygame's later HostPython build uses generated
        # C sources and does not try to import Cython again.
        subprocess.run(
            [sys.executable, "setup.py", "cython_only"],
            cwd=str(build_dir),
            check=True,
        )


recipe = Pygame261Recipe()
