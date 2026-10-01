"""Disk-only selection of the current Steam build and explicit older installs."""
from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import ck3_installation as installation


def make_install(root: Path, version: str) -> Path:
    executable = root / "binaries/ck3.exe"
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"disk-selection-fixture")
    settings = root / "launcher/launcher-settings.json"
    settings.parent.mkdir()
    settings.write_text(json.dumps({"rawVersion": version, "exePath": "../binaries/ck3.exe"}), encoding="utf-8")
    return executable


class InstallationSelectionTests(unittest.TestCase):
    def test_current_steam_install_and_explicit_old_overrides_keep_own_identity(self):
        self.assertEqual(installation.CURRENT_GAME_VERSION, "1.20.0.3")
        self.assertEqual(installation.CURRENT_EXECUTABLE_SHA256, "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6")
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            repo, current, old = base / "repo", base / "steam-current", base / "old-12002"
            current_exe = make_install(current, "1.20.0.3")
            old_exe = make_install(old, "1.20.0.2")
            with patch.object(installation, "CURRENT_STEAM_GAME_DIR", current), patch.dict(os.environ, {}, clear=True):
                selected = installation.configured_game_executable(repo)
                self.assertEqual(selected, current_exe.resolve())
                self.assertEqual(installation.installed_game_version(selected), "1.20.0.3")
                with patch.dict(os.environ, {"XAR_CK3_GAME_DIR": str(old)}):
                    selected = installation.configured_game_executable(repo)
                    self.assertEqual(selected, old_exe.resolve())
                    self.assertEqual(installation.installed_game_version(selected), "1.20.0.2")
                with patch.dict(os.environ, {"XAR_CK3_EXE": str(old_exe)}):
                    selected = installation.configured_game_executable(repo)
                    self.assertEqual(selected, old_exe.resolve())
                    self.assertEqual(installation.installed_game_version(selected), "1.20.0.2")

    def test_missing_steam_install_preserves_repository_reference_fallback(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            repo = base / "repo"
            reference_exe = make_install(repo / "Crusader Kings III", "1.19.0.6")
            with patch.object(installation, "CURRENT_STEAM_GAME_DIR", base / "missing-steam"), patch.dict(os.environ, {}, clear=True):
                selected = installation.configured_game_executable(repo)
                self.assertEqual(selected, reference_exe.resolve())
                self.assertEqual(installation.installed_game_version(selected), "1.19.0.6")


if __name__ == "__main__":
    unittest.main()
