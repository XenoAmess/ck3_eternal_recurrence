#!/usr/bin/env python3
"""Contracts for running the ZhongGuo batch from a verified Workshop cache."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest import mock

import build_mod_zhongguo_style_release as release


def install_optional_desktop_import_stubs() -> None:
    """Keep static contract imports independent from live desktop packages."""
    attributes = {
        "pyautogui": ("FAILSAFE",),
        "numpy": (),
        "cv2": (),
        "win32api": (),
        "win32con": (),
        "win32gui": (),
        "win32process": (),
    }
    for name, names in attributes.items():
        if importlib.util.find_spec(name) is None:
            module = types.ModuleType(name)
            for attribute in names:
                setattr(module, attribute, None)
            sys.modules[name] = module


install_optional_desktop_import_stubs()
import run_zhongguo_acceptance as acceptance


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "mod_zhongguo_style"
REVISION = "a" * 40
ITEM_ID = "4000000001"


class WorkshopRuntimeTests(unittest.TestCase):
    def build_fake_exact_game(self, root: Path) -> Path:
        game = root / "game"
        executable = game / "binaries" / "ck3.exe"
        executable.parent.mkdir(parents=True)
        executable.write_bytes(b"exact-exe")
        for layer, logical_path, expected_sha256 in (
            acceptance.PARTICLE2_STARTUP_SHADER_BUNDLE
        ):
            source = game / layer / "gfx" / "FX" / logical_path
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_bytes(expected_sha256.encode("ascii"))
        return game

    @staticmethod
    def fake_exact_shader_sha256(path: Path) -> str:
        payload = Path(path).read_bytes()
        if payload == b"exact-exe":
            return acceptance.EXPECTED_EXE_SHA256
        try:
            marker = payload.decode("ascii")
        except UnicodeDecodeError:
            return "0" * 64
        if len(marker) == 64 and all(
            character in "0123456789ABCDEF" for character in marker
        ):
            return marker
        return "0" * 64

    def test_particle2_startup_shader_projection_is_offline_without_game(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            profile = root / "profile"
            result = acceptance.project_particle2_startup_shader_bundle(
                profile,
                game_dir=root / "absent-game",
            )

            self.assertEqual(result["result"], "OFFLINE_UNAVAILABLE")
            self.assertFalse(result["projected"])
            self.assertFalse((profile / "gfx").exists())

    def test_particle2_startup_shader_projection_copies_exact_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            game = self.build_fake_exact_game(root)
            profile = root / "profile"
            with mock.patch.object(
                acceptance.isolated,
                "sha256_file",
                side_effect=self.fake_exact_shader_sha256,
            ):
                result = acceptance.project_particle2_startup_shader_bundle(
                    profile,
                    game_dir=game,
                )

            self.assertEqual(result["result"], "GREEN_STATIC")
            self.assertTrue(result["projected"])
            self.assertEqual(
                len(result["files"]),
                len(acceptance.PARTICLE2_STARTUP_SHADER_BUNDLE),
            )
            for _layer, logical_path, expected_sha256 in (
                acceptance.PARTICLE2_STARTUP_SHADER_BUNDLE
            ):
                self.assertEqual(
                    (profile / "gfx" / "FX" / logical_path).read_bytes(),
                    expected_sha256.encode("ascii"),
                )

    def test_particle2_startup_shader_projection_rejects_exe_drift(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            game = root / "game"
            executable = game / "binaries" / "ck3.exe"
            executable.parent.mkdir(parents=True)
            executable.write_bytes(b"drift")

            with self.assertRaisesRegex(Exception, "exact CK3 executable"):
                acceptance.project_particle2_startup_shader_bundle(
                    root / "profile",
                    game_dir=game,
                )

    def test_particle2_shader_drift_leaves_no_partial_projection(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            game = self.build_fake_exact_game(root)
            layer, logical_path, _expected_sha256 = (
                acceptance.PARTICLE2_STARTUP_SHADER_BUNDLE[-1]
            )
            (game / layer / "gfx" / "FX" / logical_path).write_bytes(b"drift")
            profile = root / "profile"

            with (
                mock.patch.object(
                    acceptance.isolated,
                    "sha256_file",
                    side_effect=self.fake_exact_shader_sha256,
                ),
                self.assertRaisesRegex(Exception, "fingerprint differs"),
            ):
                acceptance.project_particle2_startup_shader_bundle(
                    profile,
                    game_dir=game,
                )

            self.assertFalse((profile / "gfx").exists())

    def test_terminal_profile_disables_china_tutorial_prompt(self) -> None:
        settings = acceptance.terminal.render_settings()
        self.assertIn(
            '"prompt_for_china_tutorial"={ version=0 enabled=no }',
            settings,
        )

    def test_source_snapshot_ignores_only_interpreter_bytecode(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            authored = root / "tools" / "source.py"
            authored.parent.mkdir(parents=True)
            authored.write_text("value = 1\n", encoding="utf-8")
            before = acceptance.source_tree_snapshot(root)

            cache = root / "tools" / "__pycache__" / "source.cpython-313.pyc"
            cache.parent.mkdir()
            cache.write_bytes(b"derived")
            (root / "loose.pyc").write_bytes(b"derived")
            self.assertEqual(acceptance.source_tree_snapshot(root), before)

            authored.write_text("value = 2\n", encoding="utf-8")
            self.assertNotEqual(acceptance.source_tree_snapshot(root), before)

    def test_registry_display_counts_only_completed_capture(self) -> None:
        self.assertEqual(
            acceptance.promotion_source_registry_display(False),
            "INCOMPLETE (0/4)",
        )
        self.assertEqual(
            acceptance.promotion_source_registry_display(True),
            "INCOMPLETE (1/4)",
        )

    def build_cache(self, root: Path) -> tuple[Path, Path, Path]:
        userdata = root / "Steam" / "userdata"
        userdata.mkdir(parents=True)
        app_root = root / "library" / "steamapps" / "workshop" / "content" / "1158310"
        cache = app_root / ITEM_ID
        _, manifest, _, _ = release.build_release(
            SOURCE,
            cache,
            revision=REVISION,
            workshop_item_id=ITEM_ID,
            git_tag=release.product_tag(release.descriptor_version(SOURCE)),
        )
        descriptor = cache / "descriptor.mod"
        descriptor.write_bytes(
            descriptor.read_bytes().rstrip(b"\r\n")
            + f'\nremote_file_id="{ITEM_ID}"\n'.encode("ascii")
        )
        return userdata, app_root, manifest

    def verify(self, cache: Path, userdata: Path, app_root: Path, manifest: Path):
        with (
            mock.patch.object(acceptance.terminal, "steam_userdata_root", return_value=userdata),
            mock.patch.object(
                acceptance.isolated,
                "steam_workshop_app_roots",
                return_value=[app_root],
            ),
            mock.patch.object(acceptance, "git_text", return_value=REVISION),
        ):
            return acceptance.verified_workshop_runtime(cache, manifest)

    def test_verified_cache_identity_is_reportable(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            userdata, app_root, manifest = self.build_cache(root)
            cache = app_root / ITEM_ID
            identity = self.verify(cache, userdata, app_root, manifest)
            self.assertTrue(identity["verified_workshop_cache"])
            self.assertEqual(identity["runtime_source_kind"], "verified_workshop_cache")
            self.assertEqual(identity["workshop_item_id"], ITEM_ID)
            self.assertEqual(identity["workshop_manifest_git_sha"], REVISION)
            self.assertEqual(
                identity["verified_file_count"], len(release.release_files(SOURCE))
            )

    def test_bootstrap_projects_id_free_descriptor_without_mutating_cache(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            _, app_root, manifest = self.build_cache(root)
            cache = app_root / ITEM_ID
            cache_descriptor = cache / "descriptor.mod"
            cache_before = cache_descriptor.read_bytes()
            payload = release._load_manifest(manifest, cache)
            expected = next(
                entry for entry in payload["files"] if entry["path"] == "descriptor.mod"
            )

            with mock.patch.object(
                acceptance.acceptance,
                "declared_vanilla_rule_defaults",
                return_value=[("difficulty", "difficulty_normal")],
            ):
                result = acceptance.bootstrap_userdir(
                    root / "profile", cache, workshop_manifest=manifest
                )

            runtime_descriptor = (
                Path(result["targets"]["product"]) / "descriptor.mod"
            )
            self.assertEqual(cache_descriptor.read_bytes(), cache_before)
            self.assertNotIn(b"remote_file_id", runtime_descriptor.read_bytes())
            self.assertEqual(runtime_descriptor.stat().st_size, expected["size"])
            self.assertEqual(
                release.sha256_file(runtime_descriptor), expected["sha256"]
            )
            outer = root / "profile" / "mod" / acceptance.PRODUCT_OUTER
            self.assertIn(
                f'path="{Path(result["targets"]["product"]).as_posix()}"',
                outer.read_text(encoding="utf-8-sig"),
            )

    def test_bootstrap_rejects_noncanonical_workshop_descriptor(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            _, app_root, manifest = self.build_cache(root)
            cache = app_root / ITEM_ID
            descriptor = cache / "descriptor.mod"
            descriptor.write_bytes(
                descriptor.read_bytes().replace(b'name="', b'name="drift ')
            )

            with self.assertRaisesRegex(
                Exception, "exact permitted launcher injection"
            ):
                acceptance.bootstrap_userdir(
                    root / "profile", cache, workshop_manifest=manifest
                )

    def test_cache_leaf_must_match_manifest_item_id(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            userdata, app_root, manifest = self.build_cache(root)
            cache = app_root / ITEM_ID
            renamed = app_root / "4000000002"
            cache.rename(renamed)
            with self.assertRaisesRegex(Exception, "matching the manifest item ID"):
                self.verify(renamed, userdata, app_root, manifest)

    def test_cache_must_match_tagged_git_head(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            userdata, app_root, manifest = self.build_cache(root)
            cache = app_root / ITEM_ID
            with (
                mock.patch.object(
                    acceptance.terminal, "steam_userdata_root", return_value=userdata
                ),
                mock.patch.object(
                    acceptance.isolated,
                    "steam_workshop_app_roots",
                    return_value=[app_root],
                ),
                mock.patch.object(acceptance, "git_text", return_value="b" * 40),
            ):
                with self.assertRaisesRegex(Exception, "does not match HEAD"):
                    acceptance.verified_workshop_runtime(cache, manifest)

    def test_cache_content_drift_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            userdata, app_root, manifest = self.build_cache(root)
            cache = app_root / ITEM_ID
            (cache / "events" / "zg361_events.txt").write_bytes(b"drift")
            with self.assertRaisesRegex(Exception, "manifest verification failed"):
                self.verify(cache, userdata, app_root, manifest)

    def test_cli_exposes_paired_workshop_arguments(self) -> None:
        runner = (ROOT / "tools" / "run_zhongguo_acceptance.py").read_text(
            encoding="utf-8"
        )
        for token in (
            '"--workshop-cache-source"',
            '"--workshop-manifest"',
            '"verified_workshop_cache": True',
            '"runtime_source_tree_unchanged"',
        ):
            self.assertIn(token, runner)


if __name__ == "__main__":
    unittest.main()
