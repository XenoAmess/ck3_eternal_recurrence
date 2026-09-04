from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    ROOT
    / "native_bridge"
    / "research"
    / "analyze_g2_evaluated_days_private_capture.py"
)
ARTIFACT = (
    ROOT.parents[0]
    / "artifacts"
    / "g2"
    / "2026-09-04"
    / "evaluated-days-current-pin-static-ready.json"
)
LIVE_RED_ARTIFACT = (
    ROOT.parents[0]
    / "artifacts"
    / "g2"
    / "2026-09-04"
    / "evaluated-days-current-pin-live-r1-red.json"
)
SPEC = importlib.util.spec_from_file_location(
    "analyze_g2_evaluated_days_private_capture", SCRIPT
)
if SPEC is None or SPEC.loader is None:  # pragma: no cover - import guard
    raise RuntimeError(f"cannot load analyzer: {SCRIPT}")
ANALYZER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ANALYZER)


WAR_ID = 50_331_699
CHARACTER_ID = 29_829
DATE_RAW = 53_223_936


def _runner_report() -> dict[str, object]:
    return {
        # The shared public runner is expected to remain RED because the
        # private result is reset before the public response is serialized.
        "status": "red",
        "ok": False,
        "requested_identity": {
            "war_id": WAR_ID,
            "character_id": CHARACTER_ID,
            "date_raw": DATE_RAW,
        },
        "policy": {
            "mutation_commands": [],
            "time_advanced": False,
        },
        "exact_build_proof": {"ok": True},
        "mcp_sequence": {
            "allowed_gameplay_commands": [
                f"query-war-termination-terms-v1-{WAR_ID}",
                f"query-war-termination-terms-v1-{WAR_ID}",
            ],
            "mutation_commands": [],
            "checks": {
                "official_tools_listed": True,
                "mcp_results_not_errors": True,
                "initial_paused": True,
                "expected_character": True,
                "expected_date": True,
                "between_same_paused_binding": True,
                "after_same_paused_binding": True,
                "query_sequence_successor": True,
                "normalized_payloads_equal": True,
                "binding_matches_revision": True,
                "first_four_domains": False,
                "second_four_domains": False,
                "truce_probe": False,
            },
            "ok": False,
        },
        "cleanup": {
            "ok": True,
            "shutdown_ok": True,
            "tree_gone": True,
            "cleanup_proven": True,
            "driver_closed": True,
        },
        "source_invariant": {"unchanged": True},
    }


def _capture_group(*, base: int, days: int = 1_825) -> list[dict[str, object]]:
    truce = base
    duration = truce + ANALYZER.DURATION_OFFSET
    vtable = base + 0x500
    evaluator = base + 0x900
    effect_context = base + 0x1000
    evaluation_context = base + 0x2000
    shared = {
        "schema": ANALYZER.BOUNDARY_SCHEMA,
        "exact_path": ANALYZER.EXACT_PATH,
        "exact_path_verified": True,
        "truce_effect": f"0x{truce:X}",
        "truce_vtable": f"0x{vtable:X}",
        "truce_vtable_rva": f"0x{ANALYZER.TRUCE_VTABLE_RVA:X}",
        "expected_truce_vtable_rva": f"0x{ANALYZER.TRUCE_VTABLE_RVA:X}",
        "duration_script_value": f"0x{duration:X}",
        "duration_offset_from_truce": ANALYZER.DURATION_OFFSET,
        "duration_is_truce_plus_0x108": True,
        "effect_context": f"0x{effect_context:X}",
        "evaluation_context": f"0x{evaluation_context:X}",
        "evaluator_function": f"0x{evaluator:X}",
        "evaluator_function_rva": f"0x{ANALYZER.EVALUATOR_RVA:X}",
        "expected_evaluator_function_rva": f"0x{ANALYZER.EVALUATOR_RVA:X}",
        "planned_call_count": 2,
    }
    boundaries = []
    for stage, completed, value in (
        ("pre_call", 0, -1),
        ("post_call_1", 1, days),
        ("post_call_2", 2, days),
    ):
        boundaries.append(
            dict(shared, stage=stage, completed_call_count=completed, evaluated_days=value)
        )
    summary = {
        "schema": ANALYZER.CAPTURE_SCHEMA,
        "war_id": WAR_ID,
        "casus_belli_database_index": 27,
        "primary_attacker_character_id": CHARACTER_ID,
        "primary_defender_character_id": 36_769,
        "claimant_character_id": 16_826_697,
        "expiry_observable": False,
        "context_destroyed": True,
        "loaded_tree_shape": {
            "targeted_index7_status": "complete",
            "default_capacity": 4,
            "default_count": 4,
            "hidden_index": 1,
            "hidden_capacity": 1,
            "hidden_child_count": 1,
            "context_capacity": 1,
            "context_child_count": 1,
            "context_scope_count": 1,
            "truce_effect": f"0x{truce:X}",
            "truce_vtable_rva": f"0x{ANALYZER.TRUCE_VTABLE_RVA:X}",
            "expected_truce_vtable_rva": f"0x{ANALYZER.TRUCE_VTABLE_RVA:X}",
            "duration_script_value": f"0x{duration:X}",
            "evaluator_capture_status": "complete",
            "evaluator_function_rva": f"0x{ANALYZER.EVALUATOR_RVA:X}",
            "expected_evaluator_function_rva": f"0x{ANALYZER.EVALUATOR_RVA:X}",
            "evaluator_effect_context": f"0x{effect_context:X}",
            "evaluator_evaluation_context": f"0x{evaluation_context:X}",
            "evaluator_first_days": days,
            "evaluator_second_days": days,
            "evaluator_call_count": 2,
            "evaluator_nonnegative": True,
            "evaluator_stable": True,
        },
    }
    return [*boundaries, summary]


class G2EvaluatedDaysPrivateCaptureAnalyzerTests(unittest.TestCase):
    def test_accepts_two_complete_groups_while_public_runner_stays_red(self) -> None:
        rows = [
            *_capture_group(base=0x100000),
            *_capture_group(base=0x200000),
        ]
        result = ANALYZER.analyze(
            _runner_report(),
            rows,
            war_id=WAR_ID,
            character_id=CHARACTER_ID,
            date_raw=DATE_RAW,
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "green_private_evaluated_days")
        self.assertEqual(result["evaluated_days"], 1_825)
        self.assertIsNone(result["failure"])
        self.assertFalse(result["runner_report_ok"])
        self.assertTrue(
            result["readiness_boundary"]["private_evaluated_days_evidence"]
        )
        self.assertFalse(result["readiness_boundary"]["public_wire_promoted"])
        self.assertFalse(result["readiness_boundary"]["gen034_closed"])

    def test_rejects_process_exit_after_durable_pre_call(self) -> None:
        rows = _capture_group(base=0x100000)[:1]
        report = _runner_report()
        report["session"] = {
            "exit_reason": "process_exit",
            "process_exit_code": 1,
        }
        report["cleanup"]["ok"] = False
        report["error"] = (
            "ExceptionGroup: unhandled errors in a TaskGroup (1 sub-exception)"
        )
        result = ANALYZER.analyze(
            report,
            rows,
            war_id=WAR_ID,
            character_id=CHARACTER_ID,
            date_raw=DATE_RAW,
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["private_row_count"], 1)
        self.assertEqual(result["capture_groups"][0]["stages"], ["pre_call"])
        self.assertFalse(result["checks"]["both_capture_groups_complete"])
        self.assertTrue(result["runner_checks"]["process_tree_cleanup_proven"])
        self.assertFalse(
            result["runner_checks"]["managed_session_stopped_normally"]
        )
        self.assertEqual(
            result["failure"]["classification"],
            "capability_red_process_exit_during_first_evaluator_call",
        )
        self.assertFalse(result["failure"]["harness_red"])
        self.assertTrue(result["failure"]["capability_red"])
        self.assertEqual(result["failure"]["first_durable_stage"], "pre_call")
        self.assertEqual(result["failure"]["completed_call_count"], 0)
        self.assertTrue(result["failure"]["process_tree_cleanup_proven"])

    def test_rejects_unequal_return_and_cross_query_drift(self) -> None:
        first = _capture_group(base=0x100000)
        first[2]["evaluated_days"] = 1_824
        rows = [*first, *_capture_group(base=0x200000, days=1_826)]
        result = ANALYZER.analyze(
            _runner_report(),
            rows,
            war_id=WAR_ID,
            character_id=CHARACTER_ID,
            date_raw=DATE_RAW,
        )
        self.assertFalse(result["ok"])
        self.assertFalse(result["capture_groups"][0]["ok"])
        self.assertFalse(result["checks"]["same_evaluated_days_across_queries"])

    def test_rejects_wrong_pointer_relation(self) -> None:
        rows = [*_capture_group(base=0x100000), *_capture_group(base=0x200000)]
        rows[0]["duration_script_value"] = "0x100109"
        result = ANALYZER.analyze(
            _runner_report(),
            rows,
            war_id=WAR_ID,
            character_id=CHARACTER_ID,
            date_raw=DATE_RAW,
        )
        self.assertFalse(result["ok"])
        self.assertFalse(
            result["capture_groups"][0]["checks"]["duration_pointer_exact"]
        )

    def test_rejects_mutation_or_frame_drift_even_with_valid_sidecar(self) -> None:
        report = _runner_report()
        report["policy"]["mutation_commands"] = ["surrender-war-50331699"]
        report["mcp_sequence"]["checks"]["after_same_paused_binding"] = False
        result = ANALYZER.analyze(
            report,
            [*_capture_group(base=0x100000), *_capture_group(base=0x200000)],
            war_id=WAR_ID,
            character_id=CHARACTER_ID,
            date_raw=DATE_RAW,
        )
        self.assertFalse(result["ok"])
        self.assertFalse(result["runner_checks"]["no_mutation_commands"])
        self.assertFalse(result["runner_checks"]["two_same_frame_public_queries"])

    def test_cli_writes_hash_bound_report_without_launching(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            runner = root / "runner.json"
            sidecar = root / "capture.jsonl"
            output = root / "analysis.json"
            runner.write_text(json.dumps(_runner_report()), encoding="utf-8")
            sidecar.write_text(
                "\n".join(
                    json.dumps(row)
                    for row in (
                        *_capture_group(base=0x100000),
                        *_capture_group(base=0x200000),
                    )
                )
                + "\n",
                encoding="utf-8",
            )
            exit_code = ANALYZER.main(
                [
                    "--runner-report",
                    str(runner),
                    "--private-jsonl",
                    str(sidecar),
                    "--output",
                    str(output),
                    "--expected-war-id",
                    str(WAR_ID),
                    "--expected-character-id",
                    str(CHARACTER_ID),
                    "--expected-date-raw",
                    str(DATE_RAW),
                ]
            )
            self.assertEqual(exit_code, 0)
            written = json.loads(output.read_text(encoding="utf-8"))
            self.assertTrue(written["ok"])
            self.assertRegex(
                written["inputs"]["private_jsonl_sha256"], r"^[0-9A-F]{64}$"
            )
            self.assertEqual(written["evaluated_days"], 1_825)

    def test_loader_rejects_malformed_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            sidecar = Path(raw) / "bad.jsonl"
            sidecar.write_text("{not-json}\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "line 1 is malformed"):
                ANALYZER._load_jsonl(sidecar)

    def test_analyzer_has_no_launcher_or_process_primitives(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        for forbidden in (
            "run_war_termination_terms_live_acceptance",
            "NativeHeadlessGameplayDriver",
            "subprocess",
            "CreateProcess",
            "Start-Process",
            "ck3.exe",
        ):
            self.assertNotIn(forbidden, source)

    def test_current_pin_candidate_stays_static_and_fail_closed(self) -> None:
        evidence = json.loads(ARTIFACT.read_text(encoding="utf-8"))
        self.assertEqual(
            evidence["source"]["commit"],
            "6145be50a1666c2392dd23edef7779507c3043d4",
        )
        self.assertEqual(
            evidence["open_kaishek"]["head"],
            evidence["open_kaishek"]["origin_main"],
        )
        self.assertTrue(evidence["private_candidate"]["private_capture_v3_marker_present"])
        self.assertFalse(evidence["default_control"]["private_capture_v3_marker_present"])
        self.assertEqual(evidence["private_candidate"]["native_fixture"], "GREEN")
        self.assertEqual(evidence["private_candidate"]["game_access_fixture"], "PASS")
        self.assertTrue(all(value is False for value in evidence["boundaries"].values()))

    def test_live_r1_capability_red_evidence_stays_fail_closed(self) -> None:
        evidence = json.loads(LIVE_RED_ARTIFACT.read_text(encoding="utf-8"))
        self.assertEqual(
            evidence["status"], "CAPABILITY_RED_FIRST_EVALUATOR_CALL"
        )
        self.assertTrue(evidence["runner"]["readiness_reached"])
        self.assertTrue(evidence["runner"]["exact_build_proof"])
        self.assertEqual(evidence["private_prefix"]["stage"], "pre_call")
        self.assertEqual(evidence["private_prefix"]["completed_call_count"], 0)
        self.assertEqual(evidence["crash"]["exception_rva"], "0x334C668")
        self.assertEqual(evidence["crash"]["access_address"], "0x12")
        self.assertFalse(evidence["classification"]["harness_red"])
        self.assertTrue(evidence["classification"]["capability_red"])
        self.assertTrue(evidence["cleanup"]["cleanup_proven"])
        self.assertFalse(evidence["next_gate"]["repeat_same_candidate"])
        self.assertTrue(all(value is False for value in evidence["boundaries"].values()))


if __name__ == "__main__":
    unittest.main()
