from pathlib import Path

from pythonforandroid.recipes.pygame import Pygame2Recipe


class Pygame261Recipe(Pygame2Recipe):
    version = "2.6.1"
    url = "https://github.com/pygame/pygame/archive/{version}.tar.gz"
    hostpython_prerequisites = ["setuptools", "cython>=3.1"]

    def prebuild_arch(self, arch):
        super().prebuild_arch(arch)

        # Cython already initializes the extension type's __dict__.
        # Assigning to self.__dict__ in pygame 2.6.1 is rejected by
        # current Cython versions, so replace that redundant assignment.
        sprite_file = (
            Path(self.get_build_dir(arch.arch))
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


recipe = Pygame261Recipe()
