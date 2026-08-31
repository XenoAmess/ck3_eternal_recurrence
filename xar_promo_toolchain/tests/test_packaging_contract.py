from __future__ import annotations

import hashlib
import re
import tomllib
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = PROJECT_ROOT.parent
GPL3_SHA256 = "3972DC9744F6499F0F9B2DBF76696F2AE7AD8AF9B23DDE66D6AF86C9DFB36986"


class PackagingContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with (PROJECT_ROOT / "pyproject.toml").open("rb") as handle:
            cls.pyproject = tomllib.load(handle)

    def test_pep639_license_file_is_explicit_and_verbatim(self) -> None:
        project = self.pyproject["project"]
        self.assertEqual("GPL-3.0-only", project["license"])
        self.assertEqual(["LICENSE"], project["license-files"])
        packaged_license = (PROJECT_ROOT / "LICENSE").read_bytes()
        self.assertEqual(
            GPL3_SHA256,
            hashlib.sha256(packaged_license).hexdigest().upper(),
        )
        repository_license = REPOSITORY_ROOT / "LICENSE"
        if repository_license.is_file():
            self.assertEqual(repository_license.read_bytes(), packaged_license)

    def test_build_backend_minimum_supports_the_declared_pep639_fields(self) -> None:
        requirements = self.pyproject["build-system"]["requires"]
        setuptools_requirements = [
            value for value in requirements if re.match(r"^setuptools(?:[<>=!~].*)?$", value)
        ]
        self.assertEqual(["setuptools>=77"], setuptools_requirements)

    def test_readme_metadata_names_a_real_nonempty_file(self) -> None:
        readme_name = self.pyproject["project"]["readme"]
        self.assertEqual("README.md", readme_name)
        readme = PROJECT_ROOT / readme_name
        self.assertTrue(readme.is_file())
        self.assertTrue(readme.read_text(encoding="utf-8").startswith("# XAR Promo Toolchain"))

    def test_sdist_manifest_includes_open_source_material_but_excludes_junk(self) -> None:
        manifest = (PROJECT_ROOT / "MANIFEST.in").read_text(encoding="utf-8")
        rules = {
            line.strip()
            for line in manifest.splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }
        self.assertTrue(
            {
                "include LICENSE",
                "include README.md",
                "include pyproject.toml",
                "graft src",
                "graft docs",
                "graft examples",
                "graft scripts",
                "graft codex-skill",
                "graft tests",
                "prune build",
                "prune dist",
                "prune artifacts",
                "prune .pytest_cache",
                "prune src/xar_promo_toolchain.egg-info",
                "global-exclude *.py[cod]",
                "global-exclude *.avi *.mkv *.mov *.mp3 *.mp4 *.wav *.webm",
                "global-exclude .DS_Store Thumbs.db",
            }.issubset(rules)
        )
        self.assertNotIn("prune tests", rules)


if __name__ == "__main__":
    unittest.main()
