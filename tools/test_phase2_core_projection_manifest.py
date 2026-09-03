#!/usr/bin/env python3
"""Validate the frozen Phase 2 51-file startup projection manifest."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = (
    ROOT / "docs" / "phase2-promo" / "phase2-core-startup-projection-2026-09-03.json"
)
FORMAL_OVERLAY = Path(
    r"Z:\ck3_mod_rewrite\_runtime\formal-phase2-legacy51-currentbridge-20260903"
) / "profile" / "mod-content" / "zhongguo_361"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def load_manifest() -> dict[str, object]:
    payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise AssertionError("manifest root must be an object")
    return payload


def file_rows(root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        data = path.read_bytes()
        rows.append(
            {
                "path": path.relative_to(root).as_posix(),
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    return rows


def list_tree_digest(rows: list[dict[str, object]]) -> str:
    canonical = json.dumps(
        rows, ensure_ascii=True, sort_keys=False, separators=(",", ":")
    ).encode("ascii")
    return hashlib.sha256(canonical).hexdigest()


def snapshot_tree_digest(rows: list[dict[str, object]]) -> str:
    snapshot = {
        str(row["path"]): {
            "size": int(row["bytes"]),
            "sha256": str(row["sha256"]),
        }
        for row in rows
    }
    canonical = json.dumps(
        snapshot, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("ascii")
    return hashlib.sha256(canonical).hexdigest()


class Phase2CoreProjectionManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = load_manifest()
        contract = cls.manifest["projection_contract"]
        if not isinstance(contract, dict):
            raise AssertionError("projection_contract must be an object")
        cls.contract = contract
        files = cls.manifest["files"]
        if not isinstance(files, list):
            raise AssertionError("files must be a list")
        cls.files = files

    def test_schema_and_paths_are_frozen(self) -> None:
        self.assertEqual(self.manifest["schema_version"], 1)
        self.assertEqual(
            self.manifest["kind"], "zg361_phase2_core_startup_projection"
        )
        self.assertEqual(len(self.files), self.contract["exact_file_count"])
        paths = [row["path"] for row in self.files]
        self.assertEqual(paths, sorted(paths))
        self.assertEqual(len(paths), len(set(paths)))
        for path in paths:
            self.assertIsInstance(path, str)
            self.assertNotIn("\\", path)
            self.assertFalse(path.startswith("/"))
            self.assertNotIn("..", Path(path).parts)
        self.assertIn("descriptor.mod", paths)
        self.assertIn("thumbnail.png", paths)

    def test_rows_and_file_list_digest_are_consistent(self) -> None:
        total = 0
        paths = []
        for row in self.files:
            self.assertIsInstance(row, dict)
            self.assertIsInstance(row["bytes"], int)
            self.assertGreaterEqual(row["bytes"], 0)
            self.assertRegex(str(row["sha256"]), SHA256_RE)
            total += int(row["bytes"])
            paths.append(str(row["path"]))
        self.assertEqual(total, self.contract["exact_payload_bytes"])
        digest = hashlib.sha256(
            json.dumps(paths, ensure_ascii=True, separators=(",", ":")).encode(
                "ascii"
            )
        ).hexdigest()
        self.assertEqual(digest, self.contract["file_list_sha256"])

    @unittest.skipUnless(
        FORMAL_OVERLAY.is_dir(),
        "formal currentbridge overlay is not present on this machine",
    )
    def test_formal_overlay_matches_byte_authority(self) -> None:
        rows = file_rows(FORMAL_OVERLAY)
        self.assertEqual(len(rows), 51)
        self.assertEqual(sum(int(row["bytes"]) for row in rows), 7_137_587)
        self.assertEqual(
            list_tree_digest(rows),
            self.contract["formal_overlay_tree_sha256"],
        )
        self.assertEqual(
            snapshot_tree_digest(rows),
            self.contract["baseline_tree_sha256"],
        )
        self.assertEqual(
            rows,
            [
                {
                    "path": row["path"],
                    "bytes": row["bytes"],
                    "sha256": row["sha256"],
                }
                for row in self.files
            ],
        )


if __name__ == "__main__":
    unittest.main()

