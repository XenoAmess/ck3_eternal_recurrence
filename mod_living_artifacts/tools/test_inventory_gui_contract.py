"""Authored geometry/response boundaries, never real screenshots or SDK facts."""
from __future__ import annotations

from pathlib import Path
import struct
import tempfile
import unittest
import zlib

from acceptance_contract import Frame, Object, Pin, json_value, pin, write_once
from inventory_gui_contract import parse_opening, pre_intent_source


def png(path: Path, width: int, height: int) -> None:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)) +
        chunk(b"IDAT", zlib.compress((b"\0" + b"\0" * width * 3) * height)) + chunk(b"IEND", b""))


def response_fixture(root: Path, *, pid: int = 124, generation: str = "9", actor: int = 91,
                     date_raw: int = 123456, target: str = "12", refusal: Pin | None = None) -> tuple[Object, Frame, Object]:
    source, after = root / "before.png", root / "after.png"
    png(source, 80, 40)
    png(after, 80, 40)
    original = write_once(root / "original-failure.json", {"authored_test_error": True}) if refusal is None else refusal
    receipt = write_once(root / "mapping.json", {"action": "click", "status": "guarded-click-readback-matched", "click_completed": True,
        "failures": [], "screen_size_before": [80, 40], "screen_size_after": [80, 40], "live_screen_size": [80, 40],
        "source_image_size": [80, 40], "receipt_image_size": [80, 40], "source_image": str(source), "receipt_path": str(after),
        "expected_foreground_hwnd": 456, "focus_before": {"foreground_pid": pid, "foreground_hwnd": 456},
        "focus_after": {"foreground_pid": pid, "foreground_hwnd": 456}, "preview_bounds": [10, 20, 160, 80],
        "observed_point": [50, 40], "screen_point": [20, 10]})
    response: Object = {"schema": "living-artifacts-inventory-gui-open-result-v1", "schema_version": 1, "run_id": "unit-run", "machine_id": "unit-machine",
        "reviewer": "unit-root", "pid": pid, "connection_generation": generation, "actor_character_id": actor, "date_raw": date_raw,
        "target_artifact_id": target, "status": "completed", "submitted": True, "reason": None, "business_pass": False,
        "native_refusal": json_value(original), "mapping_receipt": json_value(receipt), "source_screenshot": json_value(pin(source)), "after_screenshot": json_value(pin(after))}
    return response, Frame(3, 2, date_raw, actor, pid, generation), {key: json_value(value) for key, value in original.items()}


class InventoryGuiTests(unittest.TestCase):
    def test_source_mapping_is_reproduced_without_fixed_ratio(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            response, frame, refusal = response_fixture(Path(directory))
            actual = parse_opening(response, frame=frame, run_id="unit-run", machine_id="unit-machine", reviewer="unit-root", target="12", refusal=pin(Path(directory) / "original-failure.json"))
            self.assertEqual(actual.status, "completed")
            self.assertEqual(len(actual.evidence), 4)
            self.assertEqual(actual.evidence[0], refusal)

    def test_wrong_types_scene_missing_fields_and_fake_ack_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            original, frame, _ = response_fixture(Path(directory))
            for key, value in (("schema_version", True), ("pid", 124.0), ("date_raw", 123457), ("target_artifact_id", 12),
                               ("status", "acknowledged"), ("submitted", 1), ("mapping_receipt", None)):
                changed: dict[str, object] = dict(original)
                changed[key] = value
                with self.subTest(key=key), self.assertRaises(ValueError):
                    parse_opening(changed, frame=frame, run_id="unit-run", machine_id="unit-machine", reviewer="unit-root", target="12", refusal=pin(Path(directory) / "original-failure.json"))
            missing = {key: value for key, value in original.items() if key != "source_screenshot"}
            with self.assertRaises(ValueError):
                parse_opening(missing, frame=frame, run_id="unit-run", machine_id="unit-machine", reviewer="unit-root", target="12", refusal=pin(Path(directory) / "original-failure.json"))

    def test_changed_png_geometry_is_not_accepted_as_same_desktop(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            response, frame, _ = response_fixture(root)
            png(root / "after.png", 81, 40)
            response["after_screenshot"] = json_value(pin(root / "after.png"))
            with self.assertRaisesRegex(ValueError, "dimensions"):
                parse_opening(response, frame=frame, run_id="unit-run", machine_id="unit-machine", reviewer="unit-root", target="12", refusal=pin(root / "original-failure.json"))

    def test_blocked_and_submitted_unknown_remain_distinct(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            response, frame, _ = response_fixture(root)
            for key in ("mapping_receipt", "source_screenshot", "after_screenshot"):
                response[key] = None
            response.update(status="outcome_unknown", submitted=True, reason="Actual click outcome is unavailable")
            unknown = parse_opening(response, frame=frame, run_id="unit-run", machine_id="unit-machine", reviewer="unit-root", target="12", refusal=pin(root / "original-failure.json"))
            self.assertTrue(unknown.submitted)
            response.update(status="blocked", submitted=False, reason="No input sent")
            blocked = parse_opening(response, frame=frame, run_id="unit-run", machine_id="unit-machine", reviewer="unit-root", target="12", refusal=pin(root / "original-failure.json"))
            self.assertFalse(blocked.submitted)

    def test_pre_intent_classification_requires_exact_actual_shared_source(self) -> None:
        root = Path(__file__).resolve().parents[2]
        actual = pre_intent_source({"source_root": str(root)})
        self.assertGreater(actual["bytes"], 0)
        with tempfile.TemporaryDirectory() as directory, self.assertRaises(OSError):
            pre_intent_source({"source_root": directory})


if __name__ == "__main__":
    unittest.main()
