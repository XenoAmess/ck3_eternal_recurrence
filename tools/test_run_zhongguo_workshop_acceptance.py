#!/usr/bin/env python3
"""Contracts for running the ZhongGuo batch from a verified Workshop cache."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest import mock

import build_mod_zhongguo_style_release as release
import run_zhongguo_acceptance as acceptance


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "mod_zhongguo_style"
REVISION = "a" * 40
ITEM_ID = "4000000001"


class WorkshopRuntimeTests(unittest.TestCase):
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
