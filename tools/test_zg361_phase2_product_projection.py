#!/usr/bin/env python3
"""CK3-free tests for the selectable Phase-2 product projection utility."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

# Support both ``py tools/test_...py`` and unittest module discovery from the
# repository root.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from zg361_phase2_product_projection import (
    ProductProjectionError,
    _formal_overlay_digest,
    _source_tree_digest,
    load_projection,
    materialize_projection,
    write_manifest,
)


ROOT = Path(__file__).resolve().parents[1]
LEGACY_OVERLAY = (
    Path(r"Z:\ck3_mod_rewrite\_runtime\phase2-bisect-source-legacy51-20260903")
    / "mod_zhongguo_style"
)
CANONICAL_SOURCE = ROOT / "mod_zhongguo_style"
CORE_MANIFEST = ROOT / "tools" / "phase2_product_projection_core.json"


class Phase2ProductProjectionTests(unittest.TestCase):
    def make_source(self, root: Path) -> Path:
        source = root / "source"
        (source / "common" / "scripted_effects").mkdir(parents=True)
        (source / "events").mkdir()
        (source / "docs").mkdir()
        (source / "descriptor.mod").write_bytes(b"name=projection-test\n")
        (source / "thumbnail.png").write_bytes(b"not-a-real-image")
        (source / "common" / "scripted_effects" / "example.txt").write_bytes(
            b"\xef\xbb\xbfexample = {}\n"
        )
        (source / "events" / "example.txt").write_bytes(b"event = {}\n")
        # These are deliberately present in the broad source but must never be
        # mounted as product runtime content.
        (source / "README.md").write_text("source notes\n", encoding="utf-8")
        (source / "docs" / "notes.txt").write_text("source notes\n", encoding="utf-8")
        (source / "common" / "ignored.lua").write_text("ignored\n", encoding="utf-8")
        return source

    def test_broad_projection_is_bounded_and_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source = self.make_source(root)
            destination = root / "mount"
            report = materialize_projection(source, destination)
            self.assertEqual(report["mode"], "broad")
            self.assertEqual(report["file_count"], 4)
            self.assertEqual(
                sorted(row["path"] for row in report["files"]),
                [
                    "common/scripted_effects/example.txt",
                    "descriptor.mod",
                    "events/example.txt",
                    "thumbnail.png",
                ],
            )
            self.assertFalse((destination / "README.md").exists())
            self.assertFalse((destination / "docs").exists())
            self.assertFalse((destination / "common" / "ignored.lua").exists())
            self.assertEqual(
                (source / "common" / "scripted_effects" / "example.txt").read_bytes(),
                (destination / "common" / "scripted_effects" / "example.txt").read_bytes(),
            )

    def test_generated_named_manifest_supports_external_source(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source = self.make_source(root)
            manifest = root / "workforce.json"
            payload = write_manifest(source, manifest, projection_name="workforce")
            self.assertEqual(payload["projection"], "workforce")
            self.assertIsInstance(payload["file_list_sha256"], str)
            self.assertEqual(len(payload["file_list_sha256"]), 64)
            self.assertEqual(
                payload["source_tree_sha256"],
                _source_tree_digest(
                    source,
                    load_projection(
                        source,
                        projection_name="workforce",
                        manifest_path=manifest,
                    ).entries,
                ),
            )
            destination = root / "mount"
            report = materialize_projection(
                source,
                destination,
                projection_name="workforce",
                manifest_path=manifest,
            )
            self.assertEqual(report["projection"], "workforce")
            self.assertEqual(report["file_count"], 4)
            self.assertEqual(report["formal_overlay_tree_sha256"], payload["formal_overlay_tree_sha256"])

    def test_catalog_manifest_selects_an_arbitrary_named_group(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source = self.make_source(root)
            manifest = root / "catalog.json"
            manifest.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "kind": "zg361_phase2_product_projection_catalog",
                        "projections": {
                            "workforce": {
                                "description": "small A/B group",
                                "files": [
                                    "descriptor.mod",
                                    "thumbnail.png",
                                    "events/example.txt",
                                ],
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
            report = materialize_projection(
                source,
                root / "mount",
                projection_name="workforce",
                manifest_path=manifest,
            )
            self.assertEqual(report["mode"], "allowlist")
            self.assertEqual(report["file_count"], 3)
            self.assertEqual(report["name"], "workforce")

    def test_manifest_byte_mismatch_is_typed_and_leaves_no_partial_mount(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source = self.make_source(root)
            manifest = root / "mismatch.json"
            write_manifest(source, manifest, projection_name="core")
            (source / "events" / "example.txt").write_bytes(b"changed\n")
            destination = root / "mount"
            with self.assertRaises(ProductProjectionError) as caught:
                materialize_projection(
                    source,
                    destination,
                    projection_name="core",
                    manifest_path=manifest,
                )
            self.assertIn("source tree hash does not match", str(caught.exception))
            self.assertFalse(destination.exists())

    def test_traversal_duplicate_and_required_root_manifests_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source = self.make_source(root)

            counter = 0

            def check(payload: dict[str, object], fragment: str) -> None:
                nonlocal counter
                counter += 1
                path = root / f"bad-{counter}.json"
                path.write_text(json.dumps(payload), encoding="utf-8")
                with self.assertRaises(ProductProjectionError) as caught:
                    load_projection(source, projection_name="named", manifest_path=path)
                self.assertIn(fragment, str(caught.exception))

            base = {
                "schema_version": 1,
                "kind": "zg361_phase2_product_projection",
                "projection": "named",
            }
            check(
                {**base, "files": ["descriptor.mod", "thumbnail.png", "../escape.txt"]},
                "traversal",
            )
            check(
                {**base, "files": ["descriptor.mod", "thumbnail.png", "events/example.txt", "events/example.txt"]},
                "duplicate",
            )
            check({**base, "files": ["descriptor.mod", "events/example.txt"]}, "required root")

    def test_manifest_formal_and_snapshot_hashes_remain_distinct(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source = self.make_source(root)
            manifest = root / "hashes.json"
            payload = write_manifest(source, manifest)
            self.assertNotEqual(
                payload["formal_overlay_tree_sha256"], payload["source_tree_sha256"]
            )
            self.assertEqual(
                payload["formal_overlay_tree_sha256"],
                _formal_overlay_digest(
                    load_projection(source, manifest_path=manifest).entries
                ),
            )

    @unittest.skipUnless(
        LEGACY_OVERLAY.is_dir() and CORE_MANIFEST.is_file(),
        "formal legacy overlay is not present on this machine",
    )
    def test_formal_legacy_overlay_materializes_green(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            report = materialize_projection(
                LEGACY_OVERLAY,
                Path(raw) / "mount",
                projection_name="core",
                manifest_path=CORE_MANIFEST,
            )
            self.assertEqual(report["file_count"], 51)
            self.assertEqual(report["bytes"], 7_137_587)
            self.assertEqual(
                report["source_tree_sha256"],
                "ddac4703d99b7e498e276c37c685af28b2006ad73f4124f9cd77e745aa14a693",
            )
            self.assertEqual(
                report["formal_overlay_tree_sha256"],
                "84e36658728e57b43005300c6e51e398edb6420e3c43dd2f42762c491bc9e36a",
            )

    @unittest.skipUnless(
        CANONICAL_SOURCE.is_dir() and CORE_MANIFEST.is_file(),
        "canonical source is not present on this machine",
    )
    def test_current_canonical_source_mismatch_is_typed_red(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            with self.assertRaises(ProductProjectionError) as caught:
                materialize_projection(
                    CANONICAL_SOURCE,
                    Path(raw) / "mount",
                    projection_name="core",
                    manifest_path=CORE_MANIFEST,
                )
            self.assertIn("projection source tree hash does not match", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
