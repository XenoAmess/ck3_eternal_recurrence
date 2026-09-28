"""Synthetic formal-query receipt checks; no CK3 or module attachment."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer import war_cash_formal_query_runtime_receipt_v1 as subject


FRAME = {
    "played_character_id": 29829, "native_revision": 4,
    "date_raw": 53219568, "snapshot_id": "native:4", "revision": 5,
    "episode_run_id": "native-29829-synthetic",
}


def _fixture() -> dict[str, object]:
    snapshot = {
        **FRAME, "paused": True, "map_ready": True,
        "active_wars": [{"war_id": subject.WAR_ID}],
    }
    command = {
        "kind": "read_only_query", "war_id": subject.WAR_ID,
        "query_name": "war_termination_options",
    }
    request = {
        "protocol_version": 1, "type": "execute_step", "request_id": "query-1",
        "step": subject.STEP, "expected_revision": 4,
    }
    native = {
        "step": subject.STEP, "accepted": True, "status": "available",
        "query_sequence": 1,
        "war_termination_options": {"war_id": subject.WAR_ID},
    }
    binding = {
        "status": "read_only_process_and_files_sampled",
        "process_pid": 1234, "process_created_filetime": 987654321,
        "game_exe_path": "C:/ck3/ck3.exe",
        "native_dll_path": "C:/bridge/xar_ck3_bridge.dll",
        "injector_path": "C:/bridge/xar_ck3_bridge_injector.exe",
        "game_exe_sha256": subject.EXE_SHA256,
        "native_dll_sha256": "A" * 64,
        "launch_injector_sha256": "B" * 64,
        "driver_state_sha256": "C" * 64,
        "driver_state_binding": {
            "bridge_pid": 1234, "episode_character_id": 29829,
            "episode_run_id": FRAME["episode_run_id"],
        },
    }
    return {
        "before": snapshot, "after": deepcopy(snapshot),
        "outcome": {
            "status": "executed", "selected_step": subject.STEP,
            "snapshot_id": FRAME["snapshot_id"],
            "revision": FRAME["revision"],
            "plan": {
                "policy": "one-life-turn-v1",
                "selected_step": subject.STEP,
                "priced_command": command,
            },
            "result": {**native, "backend_id": "native-headless"},
        },
        "wire": {
            "request": request,
            "response_envelope": {
                "protocol_version": 1, "type": "command_result", "request_id": "query-1",
                "ok": True, "result": native,
            },
            "before": {**FRAME, "paused": True, "map_ready": True,
                       "active_war_ids": [subject.WAR_ID]},
            "after": {**FRAME, "paused": True, "map_ready": True,
                      "active_war_ids": [subject.WAR_ID]},
        },
        "process_before": binding,
        "process_after": deepcopy(binding),
        "gameplay_submits_before": 0,
        "gameplay_submits_after": 0,
        "source_commit": "a" * 40,
        "paired_prelaunch_driver_state_sha256": "C" * 64,
    }


class FormalQueryRuntimeReceiptTests(unittest.TestCase):
    def test_exact_formal_selected_query_emits_diagnostic_without_cash(self) -> None:
        receipt = subject.build_formal_query_session_receipt(**_fixture())
        self.assertEqual(receipt["status"], "same_paused_query_postcheck_passed")
        self.assertEqual(receipt["query_result"]["war_id"], subject.WAR_ID)
        self.assertIsNone(receipt["immediate_war_action_cost_raw"])
        self.assertFalse(receipt["formal_cash_receipt_eligible"])

    def test_direct_query_without_selected_plan_is_blocked(self) -> None:
        sample = _fixture()
        sample["outcome"]["plan"].pop("priced_command")
        receipt = subject.build_formal_query_session_receipt(**sample)
        self.assertEqual(receipt["missing_reasons"],
                         ["actual_auto_turn_selected_typed_query_unproven"])

    def test_cross_frame_or_wrong_war_is_blocked(self) -> None:
        for mutation in ("after_revision", "wire_war", "native_war"):
            with self.subTest(mutation=mutation):
                sample = _fixture()
                if mutation == "after_revision":
                    sample["after"]["native_revision"] += 1
                elif mutation == "wire_war":
                    sample["wire"]["request"]["step"] = "query-other"
                else:
                    sample["wire"]["response_envelope"]["result"][
                        "war_termination_options"]["war_id"] = 1
                receipt = subject.build_formal_query_session_receipt(**sample)
                self.assertEqual(receipt["status"], "blocked")

    def test_missing_protocol_version_or_wrong_request_id_is_blocked(self) -> None:
        for mutation in ("request_version", "response_version", "request_id"):
            with self.subTest(mutation=mutation):
                sample = _fixture()
                if mutation == "request_version":
                    sample["wire"]["request"].pop("protocol_version")
                elif mutation == "response_version":
                    sample["wire"]["response_envelope"]["protocol_version"] = False
                else:
                    sample["wire"]["response_envelope"]["request_id"] = "other"
                receipt = subject.build_formal_query_session_receipt(**sample)
                self.assertEqual(receipt["missing_reasons"],
                                 ["query_request_or_native_envelope_mismatch"])

    def test_module_change_or_submit_is_blocked(self) -> None:
        for mutation in ("dll", "pid", "submit"):
            with self.subTest(mutation=mutation):
                sample = _fixture()
                if mutation == "dll":
                    sample["process_after"]["native_dll_sha256"] = "D" * 64
                elif mutation == "pid":
                    sample["process_after"]["process_created_filetime"] += 1
                else:
                    sample["gameplay_submits_after"] = 1
                receipt = subject.build_formal_query_session_receipt(**sample)
                self.assertEqual(receipt["status"], "blocked")

    def test_driver_state_can_change_on_restore_but_pair_anchor_stays_exact(self) -> None:
        sample = _fixture()
        sample["process_before"]["driver_state_sha256"] = "D" * 64
        sample["process_after"]["driver_state_sha256"] = "E" * 64
        receipt = subject.build_formal_query_session_receipt(**sample)
        self.assertEqual(receipt["status"], "same_paused_query_postcheck_passed")
        self.assertEqual(receipt["paired_prelaunch_driver_state_sha256"],
                         "C" * 64)
        self.assertEqual(receipt["bound_driver_state_sha256"], "D" * 64)
        self.assertEqual(receipt["postquery_driver_state_sha256"], "E" * 64)

    def test_restored_driver_pid_must_match_live_process(self) -> None:
        sample = _fixture()
        sample["process_before"]["driver_state_binding"]["bridge_pid"] = 99
        receipt = subject.build_formal_query_session_receipt(**sample)
        self.assertEqual(receipt["missing_reasons"],
                         ["postrestore_driver_state_actor_or_pid_mismatch"])

    def test_invalid_pid_never_attaches(self) -> None:
        result = subject.capture_query_process_binding(
            pid=0, game_exe=Path("ck3.exe"), native_dll=Path("bridge.dll"),
            injector=Path("injector.exe"), driver_state=Path("driver.json"),
        )
        self.assertEqual(result["status"], "blocked")
