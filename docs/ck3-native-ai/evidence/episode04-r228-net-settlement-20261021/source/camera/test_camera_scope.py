"""Only new directory-binding and unreadable-walk cases; no recorder or media IO."""
from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from capture_budget_monitor import CaptureBudgetFailure, from_capacity

HERE = Path(__file__).resolve().parent


def bound(workdir: Path) -> dict[str, object]:
    return {"capture_budget_monitor": {
        "camera_root": str(workdir), "raw_path": str(workdir / "raw.mkv"),
        "raw_soft_stop_bytes": 64, "aggregate_soft_stop_bytes": 128,
        "raw_ceiling_bytes": 96, "aggregate_ceiling_bytes": 256,
    }}


class ScopeTests(unittest.TestCase):
    def test_absent_workdir_construction_then_owned_files_only(self) -> None:
        with tempfile.TemporaryDirectory(dir=HERE) as directory:
            scene = Path(directory)
            workdir = scene / "raw" / "take01"
            monitor = from_capacity(workdir, workdir / "raw.mkv", 96, bound(workdir))
            self.assertFalse(workdir.exists())
            # Construction before recorder creates its workdir is legal.
            # A reading requested before creation is unknown, never a zero PASS.
            with self.assertRaises(CaptureBudgetFailure) as missing:
                monitor()
            self.assertEqual(missing.exception.facts["reason"], "budget_measurement_unavailable")
            (scene / "profile").mkdir()
            (scene / "driver").mkdir()
            (scene / "profile" / "fixture.bin").write_bytes(b"x" * 1024)
            (scene / "driver" / "fixture.bin").write_bytes(b"x" * 1024)
            (scene / "scene-control.json").write_bytes(b"x" * 512)
            workdir.mkdir(parents=True)
            (workdir / "raw.mkv").write_bytes(b"abc")
            (workdir / "metadata.json").write_bytes(b"12345")
            reading = monitor()
            self.assertEqual(reading["raw_bytes"], 3)
            self.assertEqual(reading["aggregate_bytes"], 8)
            self.assertEqual(reading["reason"], "below_soft_limits")
            # Scene siblings remain charged to the outer scene owner.
            self.assertGreater(sum(p.stat().st_size for p in scene.rglob("*") if p.is_file()), 256)

    def test_capacity_cannot_substitute_whole_scene_root(self) -> None:
        with tempfile.TemporaryDirectory(dir=HERE) as directory:
            scene = Path(directory)
            workdir = scene / "raw" / "take01"
            wrong = bound(scene)
            with self.assertRaises(ValueError):
                from_capacity(workdir, workdir / "raw.mkv", 96, wrong)

    def test_walk_permission_error_is_unknown_not_zero(self) -> None:
        with tempfile.TemporaryDirectory(dir=HERE) as directory:
            workdir = Path(directory)
            (workdir / "raw.mkv").write_bytes(b"abc")
            monitor = from_capacity(workdir, workdir / "raw.mkv", 96, bound(workdir))
            with patch("os.scandir", side_effect=PermissionError("synthetic unreadable camera directory")):
                with self.assertRaises(CaptureBudgetFailure) as denied:
                    monitor()
            facts = denied.exception.facts
            self.assertEqual(facts["reason"], "budget_measurement_unavailable")
            self.assertIn("PermissionError", str(facts["error"]))
            self.assertNotIn("aggregate_bytes", facts)
            self.assertNotIn("raw_bytes", facts)


if __name__ == "__main__":
    unittest.main()
