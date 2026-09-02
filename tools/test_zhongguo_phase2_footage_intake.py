from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest


TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import zhongguo_phase2_footage_intake as intake  # noqa: E402
from zhongguo_phase2_capture_choreography import (  # noqa: E402
    PHASE2_CAPTURE_SCENARIOS,
)
from zhongguo_phase2_promo_producer import (  # noqa: E402
    PHASE2_PROMO_CAPTURE_CONTRACT_VERSION,
    PHASE2_PROMO_CAPTURE_MODE,
    canonical_phase2_capture_contract,
)


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _record(root: Path, path: Path) -> dict[str, object]:
    return {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest().upper(),
    }


def _valid_bundle(root: Path) -> None:
    cell = root / "cell"
    promo = cell / "promo"
    promo.mkdir(parents=True)
    raw = promo / "phase2.mkv"
    raw.write_bytes(b"real-capture-placeholder-bytes-used-only-by-static-test")
    marks: list[dict[str, object]] = [
        {"label": "recording_started_after_gameplay_hud", "seconds": 0.0}
    ]
    clean_gates: list[dict[str, object]] = []
    completed: list[dict[str, object]] = []
    seconds = 1.0
    for scenario in PHASE2_CAPTURE_SCENARIOS:
        frames: list[dict[str, object]] = []
        begin = f"{scenario.span_id}_clean_begin"
        end = f"{scenario.span_id}_clean_end"
        for phase in ("begin", "end"):
            image_path = promo / f"{scenario.span_id}_{phase}.png"
            image_path.write_bytes(f"{scenario.span_id}:{phase}".encode())
            image = _record(root, image_path)
            gate_payload = {
                "schema_version": 1,
                "result": "GREEN",
                "span": scenario.span_id,
                "phase": phase,
                "image": image,
            }
            gate_path = promo / f"{scenario.span_id}_{phase}_gate.json"
            _write_json(gate_path, gate_payload)
            frames.append({**gate_payload, "gate": _record(root, gate_path)})
        marks.extend(
            [
                {"label": begin, "seconds": seconds},
                {"label": end, "seconds": seconds + 0.5},
            ]
        )
        seconds += 1.0
        clean_gates.append(
            {
                "span_id": scenario.span_id,
                "result": "GREEN",
                "begin_mark": begin,
                "end_mark": end,
                "frames": frames,
            }
        )
        completed.append(
            {
                "span_id": scenario.span_id,
                "producer_key": scenario.producer_key,
                "handler": scenario.handler,
                "result": "GREEN",
                "surface_visible": True,
                "postcondition_green": True,
                "postcondition_evidence": {
                    "result": "GREEN",
                    "surface_visible": True,
                    "postcondition_green": True,
                    "binding": {
                        "bridge_pid": 4242,
                        "connection_generation": 1,
                        "revision": 100,
                        "native_revision": 200,
                    },
                },
            }
        )
    marks.append({"label": "recording_stop_requested", "seconds": seconds})
    timeline = {
        "schema": 2,
        "exclude_ck3_loading": True,
        "source_kind": "real CK3 1.19.0.6 desktop capture after gameplay HUD",
        "raw_path": str(raw.resolve()),
        "raw_bytes": raw.stat().st_size,
        "raw_sha256": hashlib.sha256(raw.read_bytes()).hexdigest().upper(),
        "marks": marks,
        "clean_frame_gates": clean_gates,
        "clean_capture_complete": True,
        "missing_clean_spans": [],
        "capture_mode": PHASE2_PROMO_CAPTURE_MODE,
        "capture_contract_version": PHASE2_PROMO_CAPTURE_CONTRACT_VERSION,
        "capture_contract": canonical_phase2_capture_contract(),
        "real_character_provenance": {"result": "GREEN"},
    }
    _write_json(promo / "capture-timeline.json", timeline)
    loaded = {
        "schema_version": 2,
        "result": "GREEN",
        "observed": {
            "bridge_pid": 4242,
            "connection_generation": 1,
            "snapshot_id": "snapshot-1",
            "revision": 100,
            "native_revision": 200,
        },
        "span_requirements": [
            {
                "span_id": scenario.span_id,
                "loaded_feature_seed_ready": True,
            }
            for scenario in PHASE2_CAPTURE_SCENARIOS
        ],
    }
    _write_json(cell / "04_phase2_seed_loaded.json", loaded)
    scenario_evidence = {
        "result": "GREEN",
        "capture_mode": PHASE2_PROMO_CAPTURE_MODE,
        "capture_contract_version": PHASE2_PROMO_CAPTURE_CONTRACT_VERSION,
        "capture_contract": canonical_phase2_capture_contract(),
        "scenario_definitions": [
            {
                "span_id": scenario.span_id,
                "producer_key": scenario.producer_key,
                "handler": scenario.handler,
                "postcondition": scenario.postcondition,
            }
            for scenario in PHASE2_CAPTURE_SCENARIOS
        ],
        "completed_spans": completed,
    }
    outer = {
        "schema_version": 1,
        "result": "GREEN",
        "cell": {
            "schema_version": 1,
            "result": "GREEN",
            "phase2_promo_capture": True,
            "phase2_promo_capture_complete": True,
            "gameplay_green_claimed": True,
            "native_launch_sequence": "managed_native_session_supervisor",
            "tracked_full_acceptance_pid": 4242,
            "scenario_evidence": scenario_evidence,
            "promo_capture": timeline,
            "phase2_native_session": {
                "startup": {"bridge_pid": 4242, "connection_generation": 1},
                "final_binding": {
                    "connected": True,
                    "bridge_pid": 4242,
                    "connection_generation": 1,
                },
                "pid_lineage": [4242],
                "connection_generation_lineage": [1],
                "restart_count": 0,
                "cleanup": {"result": "GREEN"},
            },
        },
    }
    _write_json(root / "report.json", outer)
    rows = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix()
        rows.append({"path": relative, **{key: value for key, value in _record(root, path).items() if key != "path"}})
    _write_json(
        root / "evidence-index.json",
        {
            "schema_version": 1,
            "result": "GREEN",
            "artifact_root": str(root.resolve()),
            "files": rows,
        },
    )


class Phase2FootageIntakeTests(unittest.TestCase):
    def test_missing_bundle_remains_typed_footage_pending(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            report = intake.validate_footage_intake(Path(raw) / "missing")
        self.assertEqual(report["result"], "RED")
        self.assertEqual(report["reason_code"], "footage_pending")
        self.assertFalse(report["execution_attestation"]["media_generated"])
        self.assertEqual(
            report["scope"], "phase2_media_entry_only_no_native_observer_schema"
        )

    def test_exact_same_session_eight_span_bundle_is_green(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _valid_bundle(root)
            report = intake.validate_footage_intake(root)
        self.assertEqual(report["result"], "GREEN", report["errors"])
        self.assertIsNone(report["reason_code"])
        self.assertEqual(len(report["spans"]), 8)
        self.assertTrue(all(report["checks"].values()))

    def test_different_span_pid_is_footage_pending(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _valid_bundle(root)
            report_path = root / "report.json"
            outer = json.loads(report_path.read_text(encoding="utf-8"))
            outer["cell"]["scenario_evidence"]["completed_spans"][0][
                "postcondition_evidence"
            ]["binding"]["bridge_pid"] = 9999
            _write_json(report_path, outer)
            index_path = root / "evidence-index.json"
            index = json.loads(index_path.read_text(encoding="utf-8"))
            report_row = next(row for row in index["files"] if row["path"] == "report.json")
            record = _record(root, report_path)
            report_row["bytes"] = record["bytes"]
            report_row["sha256"] = record["sha256"]
            _write_json(index_path, index)
            report = intake.validate_footage_intake(root)
        self.assertEqual(report["result"], "RED")
        self.assertEqual(report["reason_code"], "footage_pending")
        self.assertFalse(report["checks"]["same_managed_session_pid_revision"])


if __name__ == "__main__":
    unittest.main()
