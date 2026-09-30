"""Regression fixtures for selecting and reporting the updated CK3 installation."""

from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import ck3_installation
from prepare_ck3_12002_offline_plan import render_plan, sha256_file


class InstallationSelectionTests(unittest.TestCase):
    def make_installation(self, root: Path, version: str = "1.20.0.2") -> Path:
        executable = root / "binaries/ck3.exe"
        executable.parent.mkdir(parents=True)
        executable.write_bytes(b"offline-executable-fixture")
        launcher = root / "launcher/launcher-settings.json"
        launcher.parent.mkdir()
        launcher.write_text(json.dumps({
            "rawVersion": version, "exePath": "../binaries/ck3.exe",
        }), encoding="utf-8-sig")
        return executable

    def test_installed_build_is_selected_without_legacy_reference_shadowing_it(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            current = root / "current"
            self.make_installation(current)
            repo = root / "repo"
            self.make_installation(repo / "Crusader Kings III", "1.19.0.6")
            with mock.patch.dict(os.environ, {}, clear=True), mock.patch.object(
                ck3_installation, "CURRENT_STEAM_GAME_DIR", current
            ):
                executable = ck3_installation.configured_game_executable(repo)
                self.assertEqual(executable.parent.parent, current.resolve())
                self.assertEqual(
                    ck3_installation.installed_game_version(executable), "1.20.0.2"
                )

    def test_explicit_old_installation_and_executable_override_remain_reproducible(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            old = self.make_installation(root / "old", "1.19.0.6")
            current = self.make_installation(root / "current")
            with mock.patch.dict(os.environ, {
                "XAR_CK3_GAME_DIR": str(old.parent.parent),
            }, clear=True):
                self.assertEqual(ck3_installation.configured_game_executable(root), old)
                self.assertEqual(ck3_installation.installed_game_version(old), "1.19.0.6")
                os.environ["XAR_CK3_EXE"] = str(current)
                self.assertEqual(ck3_installation.configured_game_executable(root), current)

    def test_launcher_mismatched_executable_does_not_report_another_build(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            executable = self.make_installation(root)
            settings = root / "launcher/launcher-settings.json"
            settings.write_text(json.dumps({
                "rawVersion": "1.20.0.2", "exePath": "../other/ck3.exe",
            }), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "does not match"):
                ck3_installation.installed_game_version(executable)

    def test_offline_plan_freezes_identity_and_never_creates_candidate_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            executable = self.make_installation(root / "game")
            candidate = root / "candidate.json"
            candidate.write_text(json.dumps({
                "game": {"version": "1.20.0.2", "executable_sha256": sha256_file(executable)},
                "bridge_mode": "native-headless", "bridge_pipe": "fixture-pipe",
            }), encoding="utf-8-sig")
            state = root / "not-created-state"
            plan = render_plan(candidate, executable.parent.parent, root / "build", state)
            self.assertFalse(state.exists())
            self.assertFalse(plan["live_validated"])
            self.assertFalse(plan["profile_prepared"])
            self.assertEqual(plan["commands"][0]["argv"][-1], "prepare-profile")
            executable.write_bytes(b"changed-fixture-build")
            with self.assertRaisesRegex(ValueError, "differs from the installed build"):
                render_plan(candidate, executable.parent.parent, root / "build", state)


if __name__ == "__main__":
    unittest.main()
