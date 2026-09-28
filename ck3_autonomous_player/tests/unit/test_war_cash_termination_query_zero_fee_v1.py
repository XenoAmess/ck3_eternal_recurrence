"""Synthetic gates only; this test never approves a real DLL or Robert frame."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer import war_cash_termination_query_zero_fee_v1 as subject


WAR_ID = 16777231
STEP = f"query-war-termination-options-{WAR_ID}"
FRAME = {
    "played_character_id": 29829, "native_revision": 4,
    "date_raw": 53219568, "snapshot_id": "native:4", "revision": 5,
    "episode_run_id": "native-29829-synthetic",
}
SOURCE = {**FRAME, "actor_character_id": FRAME["played_character_id"]}
SOURCE.pop("played_character_id")


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest().upper()


def _bytes(value: dict[str, object]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _snapshot() -> dict[str, object]:
    return {**FRAME, "paused": True, "map_ready": True,
            "played_character": {"character_id": 29829},
            "played_character_gold": {"raw": 120_644_281, "scale": 100_000},
            "active_wars": [{"war_id": WAR_ID}]}


def _planned() -> dict[str, object]:
    return {"snapshot_id": FRAME["snapshot_id"],
            "revision": FRAME["revision"],
            "plan": {
                "policy": "one-life-turn-v1", "selected_step": STEP,
                "priced_command": {"kind": "read_only_query",
                                   "war_id": WAR_ID,
                                   "query_name": "war_termination_options"},
                "construction_wartime_observation": {
                    "source_frame": dict(SOURCE)},
            }}


def _fixture(root: Path) -> tuple[dict[str, object], dict[str, Path], dict[str, str]]:
    paths = {role: root / f"{role}.bin" for role in subject.ARTIFACT_ROLES}
    raw = {}
    for role in ("game_exe", "save", "driver_state", "native_dll",
                 "injector", "driver_source", "bridge_source", "ck3_source"):
        payload = f"synthetic {role}".encode()
        paths[role].write_bytes(payload)
        raw[role] = _sha(payload)
    source_commit = "a" * 40
    binary_audit = {
        "schema": "xar.ck3.war-cash-query-binary-audit.v1",
        "status": "exact_dll_read_only_no_submit_verified",
        "native_dll_sha256": raw["native_dll"],
        "driver_source_sha256": raw["driver_source"],
        "bridge_source_sha256": raw["bridge_source"],
        "ck3_source_sha256": raw["ck3_source"],
        "source_commit": source_commit,
        "bridge_query_gameplay_submit_count": 0,
        "native_query_gameplay_submit_count": 0,
    }
    paths["binary_audit"].write_bytes(_bytes(binary_audit))
    raw["binary_audit"] = _sha(paths["binary_audit"].read_bytes())
    preflight = {
        "kind": "ck3_native_one_generation_preflight",
        "status": "ready", "ok": True, "ck3_launch_attempted": False,
        "expected": {
            "checkpoint_sha256": raw["save"],
            "driver_state_sha256": raw["driver_state"],
            "episode_character_id": FRAME["played_character_id"],
            "episode_run_id": FRAME["episode_run_id"],
        },
        "profile": {"ck3_executable_sha256": raw["game_exe"]},
        "resume_anchor": {
            "checkpoint": {"sha256": raw["save"],
                           "saved_date_raw": FRAME["date_raw"]},
            "driver_state": {"sha256": raw["driver_state"],
                             "episode_character_id": FRAME["played_character_id"],
                             "episode_run_id": FRAME["episode_run_id"]},
        },
    }
    paths["official_no_launch_receipt"].write_bytes(_bytes(preflight))
    raw["official_no_launch_receipt"] = _sha(
        paths["official_no_launch_receipt"].read_bytes())
    query = {"step": STEP, "war_id": WAR_ID, "accepted": True,
             "status": "available", "query_sequence": 7}
    native_query = {
        "step": STEP, "accepted": True, "status": "available",
        "query_sequence": 7,
        "war_termination_options": {"war_id": WAR_ID},
    }
    managed = {
        "schema": "xar.ck3.war-cash-query-managed-session.v1",
        "status": "same_paused_query_postcheck_passed",
        "managed_cleanup": {"ok": True}, "runner_status": "turn_limit",
        "source_commit": source_commit,
        "source_frame_before": dict(FRAME),
        "source_frame_after": dict(FRAME),
        "treasury_before_raw": 120_644_281,
        "treasury_after_raw": 120_644_281,
        "treasury_scale": 100_000,
        "query_result": query,
        "query_request": {
            "protocol_version": 1, "type": "execute_step",
            "request_id": "query-7", "step": STEP,
            "expected_revision": FRAME["native_revision"],
        },
        "query_response_envelope": {
            "protocol_version": 1, "type": "command_result",
            "request_id": "query-7", "ok": True, "result": native_query,
        },
        "process_pid": 2000, "managed_session_pid": 2000,
        "process_created_filetime": 123456,
        "gameplay_submits_before": 3, "gameplay_submits_after": 3,
        "loaded_game_exe_sha256": raw["game_exe"],
        "loaded_native_dll_sha256": raw["native_dll"],
        "launch_injector_sha256": raw["injector"],
        "module_hash_scope": "process_mapped_path_disk_bytes_not_memory_pages",
        "paired_prelaunch_driver_state_sha256": raw["driver_state"],
        "bound_driver_state_sha256": raw["driver_state"],
        "postquery_driver_state_sha256": raw["driver_state"],
        "bound_driver_state_binding": {
            "bridge_pid": 2000,
            "episode_character_id": FRAME["played_character_id"],
            "episode_run_id": FRAME["episode_run_id"],
        },
        "postquery_driver_state_binding": {
            "bridge_pid": 2000,
            "episode_character_id": FRAME["played_character_id"],
            "episode_run_id": FRAME["episode_run_id"],
        },
    }
    paths["managed_session_receipt"].write_bytes(_bytes(managed))
    raw["managed_session_receipt"] = _sha(
        paths["managed_session_receipt"].read_bytes())
    evidence = {
        "schema": subject.EVIDENCE_SCHEMA,
        "status": "receiver_verified_postquery",
        "source_frame_before": dict(FRAME),
        "source_frame_after": dict(FRAME),
        "treasury_before_raw": 120_644_281,
        "treasury_after_raw": 120_644_281,
        "treasury_scale": 100_000,
        "war_id": WAR_ID, "selected_step": STEP,
        "pair": {
            "status": "receiver_official_no_launch_passed",
            "game_exe_sha256": raw["game_exe"],
            "paired_save_sha256": raw["save"],
            "driver_state_sha256": raw["driver_state"],
            "native_dll_sha256": raw["native_dll"],
            "injector_sha256": raw["injector"],
            "official_no_launch_receipt_sha256": raw["official_no_launch_receipt"],
            "source_commit": source_commit,
            "episode_run_id": FRAME["episode_run_id"],
            "actor_character_id": FRAME["played_character_id"],
            "date_raw": FRAME["date_raw"],
        },
        "binary_audit": {
            "status": "exact_dll_read_only_no_submit_verified",
            "native_dll_sha256": raw["native_dll"],
            "audit_sha256": raw["binary_audit"],
            "driver_source_sha256": raw["driver_source"],
            "bridge_source_sha256": raw["bridge_source"],
            "ck3_source_sha256": raw["ck3_source"],
        },
        "run": {
            "status": "managed_paused_postcheck_passed",
            "session_receipt_sha256": raw["managed_session_receipt"],
            "process_pid": 2000, "process_created_filetime": 123456,
            "gameplay_submits_before": 3, "gameplay_submits_after": 3,
        },
        "query_result": query,
    }
    return evidence, paths, raw


class TerminationQueryZeroFeeTests(unittest.TestCase):
    def _run(self, payload: bytes | None, paths: dict[str, Path],
             hashes: dict[str, str], *, approve: bool = True,
             snapshot: dict[str, object] | None = None,
             planned: dict[str, object] | None = None) -> dict[str, object]:
        digest = _sha(payload) if payload is not None else None
        with (mock.patch.object(subject, "EXE_SHA256", hashes["game_exe"]),
              mock.patch.object(subject, "APPROVED_RUNTIME_RECEIPT_SHA256",
                                frozenset({digest}) if approve and digest else frozenset()),
              mock.patch.object(subject, "APPROVED_BINARY_AUDITS",
                                {hashes["native_dll"]: hashes["binary_audit"]})):
            return subject.observe_termination_query_zero_fee_v1(
                snapshot=snapshot or _snapshot(), planned=planned or _planned(),
                war_id=WAR_ID, runtime_evidence_bytes=payload,
                artifact_paths=paths,
            )

    def test_current_build_has_no_approved_receipts(self) -> None:
        self.assertEqual(subject.APPROVED_RUNTIME_RECEIPT_SHA256, frozenset())
        self.assertEqual(subject.APPROVED_BINARY_AUDITS, {})
        with tempfile.TemporaryDirectory() as temporary:
            evidence, paths, hashes = _fixture(Path(temporary))
            self.assertEqual(
                self._run(_bytes(evidence), paths, hashes, approve=False)[
                    "missing_reasons"],
                ["receiver_runtime_receipt_not_promoted"],
            )

    def test_synthetic_fully_cross_checked_path_proves_only_query_zero(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            evidence, paths, hashes = _fixture(Path(temporary))
            # Small receipts must be parsed from the same bytes that were
            # hashed; a second Path.read_bytes would recreate the TOCTOU gap.
            with mock.patch.object(Path, "read_bytes",
                                   side_effect=AssertionError("second read")):
                result = self._run(_bytes(evidence), paths, hashes)
            self.assertEqual(result["status"],
                             "selected_read_only_query_zero_fee_proven")
            self.assertEqual(result["immediate_war_action_cost_raw"]["raw"], 0)
            self.assertEqual(result["observed_treasury_raw"], 120_644_281)
            self.assertIsNone(result["pending_war_cash_raw"])
            self.assertIsNone(result["future_war_cost_upper_raw"])
            self.assertIsNone(result["policy_minimum_gold_reserve_raw"])
            self.assertFalse(result["formal_cash_receipt_eligible"])

    def test_postrestore_driver_bytes_may_differ_from_prelaunch_pair(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            evidence, paths, hashes = _fixture(Path(temporary))
            managed = json.loads(paths["managed_session_receipt"].read_bytes())
            managed["bound_driver_state_sha256"] = "D" * 64
            managed["postquery_driver_state_sha256"] = "E" * 64
            paths["managed_session_receipt"].write_bytes(_bytes(managed))
            evidence["run"]["session_receipt_sha256"] = _sha(
                paths["managed_session_receipt"].read_bytes())
            result = self._run(_bytes(evidence), paths, hashes)
            self.assertEqual(result["status"],
                             "selected_read_only_query_zero_fee_proven")
            self.assertFalse(result["formal_cash_receipt_eligible"])

    def test_postrestore_driver_pid_cannot_switch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            evidence, paths, hashes = _fixture(Path(temporary))
            managed = json.loads(paths["managed_session_receipt"].read_bytes())
            managed["bound_driver_state_binding"]["bridge_pid"] = 3000
            paths["managed_session_receipt"].write_bytes(_bytes(managed))
            evidence["run"]["session_receipt_sha256"] = _sha(
                paths["managed_session_receipt"].read_bytes())
            result = self._run(_bytes(evidence), paths, hashes)
            self.assertEqual(result["missing_reasons"],
                             ["managed_loaded_binary_or_query_postcheck_mismatch"])

    def test_restored_driver_hashes_and_scope_are_required(self) -> None:
        for key in ("bound_driver_state_sha256",
                    "postquery_driver_state_sha256", "module_hash_scope"):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as temporary:
                evidence, paths, hashes = _fixture(Path(temporary))
                managed = json.loads(paths["managed_session_receipt"].read_bytes())
                managed.pop(key)
                paths["managed_session_receipt"].write_bytes(_bytes(managed))
                evidence["run"]["session_receipt_sha256"] = _sha(
                    paths["managed_session_receipt"].read_bytes())
                result = self._run(_bytes(evidence), paths, hashes)
                self.assertEqual(result["missing_reasons"],
                                 ["managed_loaded_binary_or_query_postcheck_mismatch"])

    def test_plan_or_same_frame_mismatch_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            evidence, paths, hashes = _fixture(Path(temporary))
            plan = _planned()
            plan["plan"]["selected_step"] = "move-army-71-to-22"
            self.assertEqual(self._run(_bytes(evidence), paths, hashes,
                                       planned=plan)["missing_reasons"],
                             ["selected_read_only_query_identity_unproven"])
            altered = deepcopy(evidence)
            altered["source_frame_after"]["native_revision"] += 1
            self.assertEqual(self._run(_bytes(altered), paths, hashes)[
                "missing_reasons"],
                ["receiver_runtime_receipt_frame_or_action_mismatch"])

    def test_current_evidence_or_managed_treasury_mismatch_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            evidence, paths, hashes = _fixture(Path(temporary))
            current = _snapshot()
            current["played_character_gold"]["raw"] += 1
            self.assertEqual(self._run(_bytes(evidence), paths, hashes,
                                       snapshot=current)["missing_reasons"],
                             ["receiver_runtime_receipt_frame_or_action_mismatch"])
            current["played_character_gold"]["raw"] -= 1
            altered = deepcopy(evidence)
            altered["treasury_after_raw"] -= 1
            self.assertEqual(self._run(_bytes(altered), paths, hashes)[
                "missing_reasons"],
                ["receiver_runtime_receipt_frame_or_action_mismatch"])
            managed = json.loads(paths["managed_session_receipt"].read_bytes())
            managed["treasury_after_raw"] -= 1
            paths["managed_session_receipt"].write_bytes(_bytes(managed))
            evidence["run"]["session_receipt_sha256"] = _sha(
                paths["managed_session_receipt"].read_bytes())
            self.assertEqual(self._run(_bytes(evidence), paths, hashes)[
                "missing_reasons"],
                ["managed_loaded_binary_or_query_postcheck_mismatch"])

    def test_actual_artifact_or_external_receipt_mismatch_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            evidence, paths, hashes = _fixture(Path(temporary))
            paths["driver_state"].write_bytes(b"tampered driver")
            result = self._run(_bytes(evidence), paths, hashes)
            self.assertEqual(result["missing_reasons"],
                             ["exact_runtime_and_source_artifact_bytes_unverified"])

        with tempfile.TemporaryDirectory() as temporary:
            evidence, paths, hashes = _fixture(Path(temporary))
            managed = json.loads(paths["managed_session_receipt"].read_bytes())
            managed["loaded_native_dll_sha256"] = "0" * 64
            paths["managed_session_receipt"].write_bytes(_bytes(managed))
            evidence["run"]["session_receipt_sha256"] = _sha(
                paths["managed_session_receipt"].read_bytes())
            result = self._run(_bytes(evidence), paths, hashes)
            self.assertEqual(result["missing_reasons"],
                             ["managed_loaded_binary_or_query_postcheck_mismatch"])
        with tempfile.TemporaryDirectory() as temporary:
            evidence, paths, hashes = _fixture(Path(temporary))
            paths["save"] = paths["driver_state"]
            self.assertEqual(self._run(_bytes(evidence), paths, hashes)[
                "missing_reasons"],
                ["exact_runtime_and_source_artifact_bytes_unverified"])

    def test_managed_protocol_version_or_request_identity_blocks(self) -> None:
        for mutation in ("request_version", "response_version", "request_id"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temporary:
                evidence, paths, hashes = _fixture(Path(temporary))
                managed = json.loads(paths["managed_session_receipt"].read_bytes())
                if mutation == "request_version":
                    managed["query_request"].pop("protocol_version")
                elif mutation == "response_version":
                    managed["query_response_envelope"]["protocol_version"] = 0
                else:
                    managed["query_response_envelope"]["request_id"] = "other"
                paths["managed_session_receipt"].write_bytes(_bytes(managed))
                evidence["run"]["session_receipt_sha256"] = _sha(
                    paths["managed_session_receipt"].read_bytes())
                result = self._run(_bytes(evidence), paths, hashes)
                self.assertEqual(result["missing_reasons"],
                                 ["managed_query_protocol_identity_mismatch"])

    def test_unsubmitted_or_duplicate_key_receipt_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            evidence, paths, hashes = _fixture(Path(temporary))
            altered = deepcopy(evidence)
            altered["run"]["gameplay_submits_after"] = 4
            self.assertEqual(self._run(_bytes(altered), paths, hashes)[
                "missing_reasons"], ["managed_no_submit_postcheck_unproven"])
            duplicate = _bytes(evidence).replace(
                b'"status":"receiver_verified_postquery"',
                b'"status":"receiver_verified_postquery",'
                b'"status":"receiver_verified_postquery"',
            )
            self.assertEqual(self._run(duplicate, paths, hashes)[
                "missing_reasons"], ["receiver_runtime_receipt_invalid_json"])

    def test_no_launch_actual_anchor_must_match_claimed_pair(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            evidence, paths, hashes = _fixture(Path(temporary))
            preflight = json.loads(
                paths["official_no_launch_receipt"].read_bytes())
            preflight["resume_anchor"]["driver_state"]["sha256"] = "0" * 64
            paths["official_no_launch_receipt"].write_bytes(_bytes(preflight))
            evidence["pair"]["official_no_launch_receipt_sha256"] = _sha(
                paths["official_no_launch_receipt"].read_bytes())
            result = self._run(_bytes(evidence), paths, hashes)
            self.assertEqual(result["missing_reasons"],
                             ["official_no_launch_pair_receipt_mismatch"])


if __name__ == "__main__":
    unittest.main()
