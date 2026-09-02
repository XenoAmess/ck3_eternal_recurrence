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


def _reindex(root: Path) -> None:
    rows = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix()
        if relative == "evidence-index.json":
            continue
        rows.append(
            {
                "path": relative,
                **{
                    key: value
                    for key, value in _record(root, path).items()
                    if key != "path"
                },
            }
        )
    _write_json(
        root / "evidence-index.json",
        {
            "schema_version": 1,
            "result": "GREEN",
            "artifact_root": str(root.resolve()),
            "files": rows,
        },
    )


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
    _reindex(root)


def _upgrade_to_multisession(root: Path) -> None:
    report_path = root / "report.json"
    timeline_path = root / "cell" / "promo" / "capture-timeline.json"
    loaded_path = root / "cell" / "04_phase2_seed_loaded.json"
    outer = json.loads(report_path.read_text(encoding="utf-8"))
    timeline = json.loads(timeline_path.read_text(encoding="utf-8"))
    loaded = json.loads(loaded_path.read_text(encoding="utf-8"))

    canonical_save = root / "cell" / "checkpoints" / "canonical-seed.ck3"
    canonical_save.parent.mkdir(parents=True)
    canonical_save.write_bytes(b"canonical-phase2-seed-save")
    canonical_record = _record(root, canonical_save)
    canonical_record["save_lineage_id"] = "zg361-phase2-seed-lineage-001"
    lineage = {
        "schema_version": 1,
        "phase": "zhongguo_phase2",
        "evidence_class": "real_ck3",
        "fixture_used": False,
        "prior_phase_footage_used": False,
        "seed_lineage_id": "zg361-phase2-seed-lineage-001",
        "canonical_seed_save_sha256": canonical_record["sha256"],
        "source": {
            "git_commit": "1" * 40,
            "tree_sha256": "2" * 64,
        },
        "game": {"version": "1.19.0.6", "exe_sha256": "3" * 64},
        "mod_mount": {"kind": "product-only", "tree_sha256": "4" * 64},
    }
    timeline["capture_lineage"] = lineage
    timeline["source_git_commit"] = lineage["source"]["git_commit"]
    timeline["source_clean_tree_sha256"] = lineage["source"]["tree_sha256"]

    cell = outer["cell"]
    scenario_evidence = cell["scenario_evidence"]
    scenario_evidence["span_session_contract_version"] = (
        intake.SPAN_SESSION_CONTRACT_VERSION
    )
    for index, (scenario, row) in enumerate(
        zip(PHASE2_CAPTURE_SCENARIOS, scenario_evidence["completed_spans"]),
        start=1,
    ):
        pid = 5000 + index
        generation = 10 + index
        pre_revision = 100 + (index * 10)
        pre_native_revision = 200 + (index * 10)
        post_revision = pre_revision + 1
        post_native_revision = pre_native_revision + 1
        checkpoint_dir = root / "cell" / "checkpoints" / scenario.span_id
        start = checkpoint_dir / "start.ck3"
        end = checkpoint_dir / "end.ck3"
        start.parent.mkdir(parents=True)
        start.write_bytes(f"{scenario.span_id}:start".encode())
        end.write_bytes(f"{scenario.span_id}:end".encode())
        start_record = _record(root, start)
        start_record["save_lineage_id"] = lineage["seed_lineage_id"]
        end_record = _record(root, end)
        end_record["save_lineage_id"] = lineage["seed_lineage_id"]
        session_id = f"phase2-span-session-{index:02d}"
        stage_identity = {
            "session_id": session_id,
            "bridge_pid": pid,
            "connection_generation": generation,
        }
        row["postcondition_evidence"]["binding"] = {
            "bridge_pid": pid,
            "connection_generation": generation,
            "revision": post_revision,
            "native_revision": post_native_revision,
        }
        row["session_evidence"] = {
            "schema_version": 1,
            "result": "GREEN",
            "span_id": scenario.span_id,
            "session_id": session_id,
            "bridge_pid": pid,
            "connection_generation": generation,
            "lineage_binding": lineage,
            "start_checkpoint": start_record,
            "end_checkpoint": end_record,
            "pre": {
                **stage_identity,
                "revision": pre_revision,
                "native_revision": pre_native_revision,
                "checkpoint_sha256": start_record["sha256"],
            },
            "action": {
                **stage_identity,
                "pre_revision": pre_revision,
                "pre_native_revision": pre_native_revision,
                "post_revision": post_revision,
                "post_native_revision": post_native_revision,
            },
            "post": {
                **stage_identity,
                "revision": post_revision,
                "native_revision": post_native_revision,
                "checkpoint_sha256": end_record["sha256"],
            },
            "cleanup": {
                "result": "GREEN",
                "process_tree_gone": True,
                "driver_closed": True,
            },
        }

    seed_session = "phase2-seed-generation-load-session"
    seed_pid = 4900
    seed_generation = 9
    generated = {
        "session_id": seed_session,
        "bridge_pid": seed_pid,
        "connection_generation": seed_generation,
        "revision": 90,
        "native_revision": 190,
        "save": canonical_record,
    }
    loaded_chain = {
        "session_id": seed_session,
        "bridge_pid": seed_pid,
        "connection_generation": seed_generation,
        "revision": 91,
        "native_revision": 191,
        "save": canonical_record,
    }
    cell["seed_generation_loaded_chain"] = {
        "schema_version": 1,
        "result": "GREEN",
        "session_id": seed_session,
        "bridge_pid": seed_pid,
        "connection_generation": seed_generation,
        "generated": generated,
        "loaded": loaded_chain,
    }
    loaded["observed"].update(
        {
            "bridge_pid": seed_pid,
            "connection_generation": seed_generation,
            "revision": loaded_chain["revision"],
            "native_revision": loaded_chain["native_revision"],
            "save_sha256": canonical_record["sha256"],
        }
    )
    cell["promo_capture"] = timeline
    _write_json(timeline_path, timeline)
    _write_json(loaded_path, loaded)
    _write_json(report_path, outer)
    _reindex(root)


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
        self.assertEqual(
            report["session_binding"]["mode"], "legacy-single-session-v1"
        )
        self.assertTrue(all(report["checks"].values()))

    def test_legacy_different_span_pid_is_still_footage_pending(self) -> None:
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
        self.assertFalse(report["checks"]["legacy_single_session_contract"])

    def test_lineage_bound_spans_may_use_eight_clean_sessions(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _valid_bundle(root)
            _upgrade_to_multisession(root)
            report = intake.validate_footage_intake(root)
        self.assertEqual(report["result"], "GREEN", report["errors"])
        self.assertEqual(
            report["session_binding"]["mode"],
            "lineage-bound-span-sessions-v2",
        )
        sessions = report["session_binding"]["span_sessions"]
        self.assertEqual(len(sessions), 8)
        self.assertEqual(len({row["bridge_pid"] for row in sessions}), 8)
        self.assertTrue(all(report["checks"].values()))

    def test_same_verified_bundle_is_reusable_by_independent_edit_projects(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _valid_bundle(root)
            _upgrade_to_multisession(root)
            before = {
                path.relative_to(root).as_posix(): hashlib.sha256(
                    path.read_bytes()
                ).hexdigest()
                for path in root.rglob("*")
                if path.is_file()
            }
            first = intake.validate_footage_intake(root)
            second = intake.validate_footage_intake(root)
            after = {
                path.relative_to(root).as_posix(): hashlib.sha256(
                    path.read_bytes()
                ).hexdigest()
                for path in root.rglob("*")
                if path.is_file()
            }
        self.assertEqual(first, second)
        self.assertEqual(first["result"], "GREEN", first["errors"])
        self.assertEqual(before, after)
        self.assertEqual(
            first["reuse_policy"],
            {
                "immutable_source_bundle": True,
                "independent_edit_projects_may_reuse_verified_spans": True,
                "source_copy_or_regeneration_required": False,
                "each_candidate_must_bind_same_verified_hashes": True,
            },
        )

    def test_pid_drift_inside_one_span_is_footage_pending(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _valid_bundle(root)
            _upgrade_to_multisession(root)
            report_path = root / "report.json"
            outer = json.loads(report_path.read_text(encoding="utf-8"))
            session = outer["cell"]["scenario_evidence"]["completed_spans"][0][
                "session_evidence"
            ]
            session["action"]["bridge_pid"] += 100
            _write_json(report_path, outer)
            _reindex(root)
            report = intake.validate_footage_intake(root)
        self.assertEqual(report["result"], "RED")
        self.assertFalse(
            report["checks"]["each_span_pre_action_post_session_continuous"]
        )

    def test_cross_span_source_lineage_drift_is_footage_pending(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _valid_bundle(root)
            _upgrade_to_multisession(root)
            report_path = root / "report.json"
            outer = json.loads(report_path.read_text(encoding="utf-8"))
            outer["cell"]["scenario_evidence"]["completed_spans"][1][
                "session_evidence"
            ]["lineage_binding"]["source"]["tree_sha256"] = "9" * 64
            _write_json(report_path, outer)
            _reindex(root)
            report = intake.validate_footage_intake(root)
        self.assertEqual(report["result"], "RED")
        self.assertFalse(report["checks"]["cross_span_canonical_lineage_exact"])

    def test_seed_generation_and_loaded_proof_cannot_cross_sessions(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _valid_bundle(root)
            _upgrade_to_multisession(root)
            report_path = root / "report.json"
            outer = json.loads(report_path.read_text(encoding="utf-8"))
            outer["cell"]["seed_generation_loaded_chain"]["loaded"][
                "connection_generation"
            ] += 1
            _write_json(report_path, outer)
            _reindex(root)
            report = intake.validate_footage_intake(root)
        self.assertEqual(report["result"], "RED")
        self.assertFalse(
            report["checks"]["seed_generation_to_loaded_proof_continuous"]
        )

    def test_dirty_span_cleanup_is_footage_pending(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _valid_bundle(root)
            _upgrade_to_multisession(root)
            report_path = root / "report.json"
            outer = json.loads(report_path.read_text(encoding="utf-8"))
            outer["cell"]["scenario_evidence"]["completed_spans"][2][
                "session_evidence"
            ]["cleanup"]["process_tree_gone"] = False
            _write_json(report_path, outer)
            _reindex(root)
            report = intake.validate_footage_intake(root)
        self.assertEqual(report["result"], "RED")
        self.assertFalse(
            report["checks"]["each_span_pre_action_post_session_continuous"]
        )

    def test_span_checkpoint_hash_tamper_is_footage_pending(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _valid_bundle(root)
            _upgrade_to_multisession(root)
            report_path = root / "report.json"
            outer = json.loads(report_path.read_text(encoding="utf-8"))
            checkpoint = Path(
                outer["cell"]["scenario_evidence"]["completed_spans"][3][
                    "session_evidence"
                ]["end_checkpoint"]["path"]
            )
            checkpoint.write_bytes(b"tampered-after-checkpoint-receipt")
            _reindex(root)
            report = intake.validate_footage_intake(root)
        self.assertEqual(report["result"], "RED")
        self.assertFalse(
            report["checks"]["each_span_pre_action_post_session_continuous"]
        )
        self.assertTrue(
            any("end_checkpoint_declared_record_mismatch" in error for error in report["errors"])
        )

    def test_phase_one_or_fixture_lineage_is_footage_pending(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _valid_bundle(root)
            _upgrade_to_multisession(root)
            timeline_path = root / "cell" / "promo" / "capture-timeline.json"
            report_path = root / "report.json"
            timeline = json.loads(timeline_path.read_text(encoding="utf-8"))
            timeline["capture_lineage"]["fixture_used"] = True
            outer = json.loads(report_path.read_text(encoding="utf-8"))
            outer["cell"]["promo_capture"] = timeline
            _write_json(timeline_path, timeline)
            _write_json(report_path, outer)
            _reindex(root)
            report = intake.validate_footage_intake(root)
        self.assertEqual(report["result"], "RED")
        self.assertFalse(
            report["checks"]["canonical_phase2_seed_source_game_mount_lineage"]
        )

    def test_old_game_version_lineage_is_footage_pending(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _valid_bundle(root)
            _upgrade_to_multisession(root)
            timeline_path = root / "cell" / "promo" / "capture-timeline.json"
            report_path = root / "report.json"
            timeline = json.loads(timeline_path.read_text(encoding="utf-8"))
            timeline["capture_lineage"]["game"]["version"] = "1.18.2"
            outer = json.loads(report_path.read_text(encoding="utf-8"))
            outer["cell"]["promo_capture"] = timeline
            for row in outer["cell"]["scenario_evidence"]["completed_spans"]:
                row["session_evidence"]["lineage_binding"] = timeline[
                    "capture_lineage"
                ]
            _write_json(timeline_path, timeline)
            _write_json(report_path, outer)
            _reindex(root)
            report = intake.validate_footage_intake(root)
        self.assertEqual(report["result"], "RED")
        self.assertFalse(
            report["checks"]["canonical_phase2_seed_source_game_mount_lineage"]
        )


if __name__ == "__main__":
    unittest.main()
