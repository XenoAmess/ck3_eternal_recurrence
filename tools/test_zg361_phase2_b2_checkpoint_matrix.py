#!/usr/bin/env python3
"""Deterministic tests for the B2 same-checkpoint A/B/C matrix."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from zg361_phase2_b2_action_cell import run_b2_pip_gameplay_action_cell
from zg361_phase2_b2_checkpoint_matrix import (
    B2SameCheckpointMatrixError,
    run_b2_same_checkpoint_matrix,
)


PLAYER = 100
OWNER = 200
CYCLE = 7
CASE = 903
DATE_RAW = 730_121
CHECKPOINT_SHA = "A" * 64
CHECKPOINT_PATH = r"C:\acceptance\xar_checkpoint.ck3"


def _available(value: object) -> dict[str, object]:
    return {
        "status": "available",
        "value": value,
        "unavailable_reason": None,
    }


def _unavailable(reason: str = "variable_absent") -> dict[str, object]:
    return {
        "status": "unavailable",
        "value": None,
        "unavailable_reason": reason,
    }


def _character_scope(character_id: int) -> dict[str, object]:
    return {
        "status": "available",
        "raw_type_index": 4,
        "type_key": "character",
        "subtype": 0,
        "typed_identity": {
            "status": "available",
            "kind": "character",
            "character_id": character_id,
        },
    }


def _scalar_scope() -> dict[str, object]:
    return {
        "status": "available",
        "raw_type_index": 9,
        "type_key": "value",
        "subtype": 0,
        "typed_identity": {
            "status": "unavailable",
            "reason": "generic_scope_payload_identity_not_closed",
        },
    }


class _FakeClock:
    def __init__(self) -> None:
        self.now = 1.0

    def monotonic(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.now += seconds


def _deterministic_action_executor(
    service: object,
    *,
    owner_character_id: int,
    action: str,
    request_nonce_prefix: str,
) -> dict[str, object]:
    clock = _FakeClock()
    return run_b2_pip_gameplay_action_cell(
        service,
        owner_character_id=owner_character_id,
        action=action,
        request_nonce_prefix=request_nonce_prefix,
        timeout_s=0.2,
        poll_interval_s=0.05,
        clock=clock.monotonic,
        sleeper=clock.sleep,
    )


class _FakeLifecycle:
    def __init__(self, starting_pid: int) -> None:
        self.alive: dict[int, bool] = {starting_pid: True}
        self.leak_restore_numbers: set[int] = set()
        self.stop_leak = False
        self.restore_number = 0
        self.proofs: list[tuple[int, str, bool]] = []
        self.stops: list[tuple[int, str]] = []

    def replace(self, previous_pid: int, next_pid: int) -> None:
        self.restore_number += 1
        if self.restore_number not in self.leak_restore_numbers:
            self.alive[previous_pid] = False
        self.alive[next_pid] = True

    def prove_pid_dead(
        self, pid: int, *, reason: str
    ) -> dict[str, object]:
        dead = self.alive.get(pid) is False
        self.proofs.append((pid, reason, dead))
        return {
            "pid": pid,
            "dead": dead,
            "proof_method": "deterministic-fake-process-inventory",
            "reason": reason,
        }

    def stop_session(
        self, pid: int, *, reason: str
    ) -> dict[str, object]:
        self.stops.append((pid, reason))
        if not self.stop_leak:
            self.alive[pid] = False
        dead = self.alive.get(pid) is False
        return {
            "ck3_pid": pid,
            "ok": dead,
            "cleanup_proven": dead,
            "tree_gone": dead,
            "reason": reason,
        }


class _FakeMatrixService:
    option_names = (
        "Accept the plan and its support.",
        "Revise the goal once, then begin.",
        "Refuse, and let only the next cycle judge it.",
    )

    def __init__(self, lifecycle: _FakeLifecycle) -> None:
        self.lifecycle = lifecycle
        self.pid = 4_000
        self.generation = 1
        self.selected_option: int | None = None
        self.save_count = 0
        self.restore_count = 0
        self.select_calls: list[tuple[int, int, int, int]] = []
        self.restore_sha_drift_at: set[int] = set()
        self.restore_case_drift_at: set[int] = set()
        self.restore_disabled_option_at: set[int] = set()
        self.apply_effect = True
        self.current_case = CASE
        self.disabled_option: int | None = None
        self.lifecycle.alive[self.pid] = True

    @property
    def event_instance(self) -> int:
        return 8_000 + self.generation

    @property
    def revision(self) -> int:
        return self.generation * 100 + self.save_count + (
            1 if self.selected_option is not None else 0
        )

    @property
    def native_revision(self) -> int:
        return self.generation * 1_000 + self.save_count + (
            1 if self.selected_option is not None else 0
        )

    def _state_name(self) -> str:
        if self.selected_option is None or not self.apply_effect:
            return "pending"
        return {1: "accept", 2: "negotiate", 3: "refuse"}[
            self.selected_option
        ]

    def snapshot(self) -> dict[str, object]:
        active_event = (
            {
                "instance_id": self.event_instance,
                "option_count": 3,
            }
            if self.selected_option is None
            else None
        )
        return {
            "snapshot_id": (
                f"fake:b2:g{self.generation}:r{self.revision}:"
                f"{self._state_name()}"
            ),
            "revision": self.revision,
            "native_revision": self.native_revision,
            "date_raw": DATE_RAW,
            "paused": True,
            "played_character": {"character_id": PLAYER},
            "episode_run_id": "phase2-b2-frozen-episode",
            "diagnostics": {
                "connected": True,
                "bridge_pid": self.pid,
                "connection_generation": self.generation,
            },
            "active_event": active_event,
        }

    def query_current_event_window_context_v1(
        self, event_instance_id: int, *, expected_revision: int
    ) -> dict[str, object]:
        snapshot = self.snapshot()
        saved_scopes = [
            {
                "name": "zg361_b2_pip_prompt_owner",
                "scope": _character_scope(OWNER),
            },
            {
                "name": "zg361_b2_pip_prompt_subject",
                "scope": _character_scope(PLAYER),
            },
        ]
        saved_scopes.extend(
            {"name": name, "scope": _scalar_scope()}
            for name in (
                "zg361_b2_pip_prompt_cycle",
                "zg361_b2_pip_prompt_case",
                "zg361_b2_pip_prompt_state",
            )
        )
        options = [
            {
                "rendered_index": index,
                "native_option_index": index,
                "shown": True,
                "enabled": self.disabled_option != index + 1,
                "resolved_name": name,
            }
            for index, name in enumerate(self.option_names)
        ]
        return {
            "status": "available",
            "current_event_window_context": {
                "status": "available",
                "event_definition_key": "zg361b2.40",
                "current_event_instance_id": event_instance_id,
                "snapshot_revision": snapshot["native_revision"],
                "date_raw": DATE_RAW,
                "root_scope": _character_scope(PLAYER),
                "saved_scopes": saved_scopes,
                "options": options,
                "readiness": {
                    "event_definition_identity_ready": True,
                    "root_scope_ready": True,
                    "saved_scopes_ready": True,
                    "option_presentation_ready": True,
                },
            },
        }

    def _b2_response(self, nonce: str) -> dict[str, object]:
        snapshot = self.snapshot()
        state_name = self._state_name()
        response_code = {
            "pending": 0,
            "accept": 1,
            "negotiate": 2,
            "refuse": 3,
        }[state_name]
        state_code = {
            "pending": 1,
            "accept": 2,
            "negotiate": 2,
            "refuse": 5,
        }[state_name]
        response_case = 0 if state_name == "pending" else self.current_case
        response_author = (
            _unavailable()
            if state_name == "pending"
            else _available(PLAYER)
        )
        refusal_receipt = (
            self.current_case if state_name == "refuse" else 0
        )
        return {
            "schema_version": 1,
            "status": "available",
            "case_kind": "zhongguo.b2.pip",
            "request_nonce": nonce,
            "snapshot_revision": snapshot["native_revision"],
            "date_raw": DATE_RAW,
            "paused": True,
            "player_character_id": PLAYER,
            "subject_character_id": PLAYER,
            "requested_owner_character_id": OWNER,
            "gate": {
                "owner_character_id": _available(OWNER),
                "subject_character_id": _available(PLAYER),
                "cycle_serial": _available(CYCLE),
                "case_serial": _available(self.current_case),
                "status": _available(1),
            },
            "pip": {
                "owner_character_id": _available(OWNER),
                "subject_character_id": _available(PLAYER),
                "cycle_serial": _available(CYCLE),
                "case_serial": _available(self.current_case),
                "state": _available(state_code),
            },
            "response": {
                "subject_response": _available(response_code),
                "response_case_serial": _available(response_case),
                "response_author_character_id": response_author,
                "acknowledgement_receipt_serial": _available(
                    self.current_case
                ),
                "goal_revision_used": _available(
                    state_name == "negotiate"
                ),
                "refusal_receipt_serial": _available(refusal_receipt),
            },
            "readiness": {
                "player_subject_binding_ready": True,
                "owner_binding_ready": True,
                "gate_ready": True,
                "pip_identity_ready": True,
                "response_ready": True,
                "same_frame_ready": True,
                "ready": True,
            },
            "unavailable_reason": None,
            "binding": {
                "snapshot_id": snapshot["snapshot_id"],
                "revision": snapshot["revision"],
                "native_revision": snapshot["native_revision"],
                "connection_generation": self.generation,
                "date_raw": DATE_RAW,
                "paused": True,
                "player_character_id": PLAYER,
                "subject_character_id": PLAYER,
                "owner_character_id": OWNER,
                "expected_revision": snapshot["revision"],
            },
        }

    def query_zhongguo_b2_pip_snapshot_v1(
        self,
        request_nonce: str,
        *,
        expected_revision: int,
        owner_character_id: int,
    ) -> dict[str, object]:
        return copy.deepcopy(self._b2_response(request_nonce))

    def select_event_option(
        self,
        option_number: int,
        *,
        event_instance_id: int,
        expected_revision: int,
    ) -> dict[str, object]:
        self.select_calls.append(
            (
                option_number,
                event_instance_id,
                expected_revision,
                self.generation,
            )
        )
        self.selected_option = option_number
        return {
            "step": f"select-event-option-{option_number}",
            "accepted": True,
            "status": "submitted",
            "event_instance_id": event_instance_id,
            "option_number": option_number,
            "option_index": option_number - 1,
        }

    def save_checkpoint(
        self, *, expected_revision: int
    ) -> dict[str, object]:
        if expected_revision != self.revision:
            raise RuntimeError("fake save revision drift")
        self.save_count += 1
        return {
            "step": "save-checkpoint",
            "accepted": True,
            "checkpoint": {
                "status": "saved",
                "path": CHECKPOINT_PATH,
                "name": "xar_checkpoint.ck3",
                "size": 12_345,
                "sha256": CHECKPOINT_SHA,
                "date_raw": DATE_RAW,
                "episode_character_id": PLAYER,
                "episode_run_id": "phase2-b2-frozen-episode",
            },
        }

    def restore_checkpoint(
        self, *, expected_revision: int
    ) -> dict[str, object]:
        if expected_revision != self.revision:
            raise RuntimeError("fake restore revision drift")
        previous_pid = self.pid
        previous_generation = self.generation
        self.restore_count += 1
        self.pid += 1
        self.generation += 1
        self.selected_option = None
        self.current_case = (
            CASE + 1
            if self.restore_count in self.restore_case_drift_at
            else CASE
        )
        self.disabled_option = (
            2
            if self.restore_count in self.restore_disabled_option_at
            else None
        )
        self.lifecycle.replace(previous_pid, self.pid)
        restored_sha = (
            "B" * 64
            if self.restore_count in self.restore_sha_drift_at
            else CHECKPOINT_SHA
        )
        return {
            "step": "restore-checkpoint",
            "accepted": True,
            "status": "restored",
            "checkpoint": {
                "status": "restored",
                "path": CHECKPOINT_PATH,
                "name": "xar_checkpoint.ck3",
                "size": 12_345,
                "sha256": restored_sha,
                "date_raw": DATE_RAW,
                "saved_date_raw": DATE_RAW,
            },
            "restored_date": {"date_raw": DATE_RAW},
            "lifecycle": {
                "previous_pid": previous_pid,
                "pid": self.pid,
                "lifecycle_intent": "restore",
                "previous_connection_generation": previous_generation,
                "connection_generation": self.generation,
            },
        }


class B2CheckpointMatrixTests(unittest.TestCase):
    def _run(
        self,
        service: _FakeMatrixService,
        lifecycle: _FakeLifecycle,
        artifacts: Path,
        *,
        executor: object = _deterministic_action_executor,
    ) -> dict[str, object]:
        return run_b2_same_checkpoint_matrix(
            service,
            lifecycle,
            owner_character_id=OWNER,
            artifacts_directory=artifacts,
            action_executor=executor,
        )

    def _fresh(self) -> tuple[_FakeLifecycle, _FakeMatrixService]:
        lifecycle = _FakeLifecycle(4_000)
        service = _FakeMatrixService(lifecycle)
        return lifecycle, service

    def test_three_real_options_restore_independently_and_cleanup(self) -> None:
        lifecycle, service = self._fresh()
        with tempfile.TemporaryDirectory() as temporary:
            artifacts = Path(temporary)
            result = self._run(service, lifecycle, artifacts)
            self.assertEqual(result["result"], "GREEN")
            self.assertEqual(service.save_count, 1)
            self.assertEqual(service.restore_count, 4)
            self.assertEqual(
                [row[0] for row in service.select_calls], [1, 2, 3]
            )
            self.assertEqual(
                [row[3] for row in service.select_calls], [2, 3, 4]
            )
            self.assertEqual(result["pid_lineage"], [4000, 4001, 4002, 4003, 4004])
            self.assertEqual(
                result["connection_generation_lineage"], [1, 2, 3, 4, 5]
            )
            self.assertTrue(all(alive is False for alive in lifecycle.alive.values()))
            self.assertTrue(result["checks"]["final_baseline_restored"])
            self.assertEqual(
                result["final_baseline"]["prechoice"]["identity"]["state"],
                1,
            )
            self.assertTrue(result["mcp_only"])
            self.assertFalse(result["ocr_used"])
            self.assertFalse(result["coordinates_used"])
            self.assertFalse(result["test_decisions_used"])

            expected_files = {
                "00_matrix_contract.json",
                "01_initial_prechoice_raw.json",
                "02_frozen_checkpoint_raw.json",
                "10_accept_restore_raw.json",
                "11_accept_prechoice_raw.json",
                "12_accept_action_raw.json",
                "20_negotiate_restore_raw.json",
                "21_negotiate_prechoice_raw.json",
                "22_negotiate_action_raw.json",
                "30_refuse_restore_raw.json",
                "31_refuse_prechoice_raw.json",
                "32_refuse_action_raw.json",
                "40_final_restore_raw.json",
                "41_final_prechoice_raw.json",
                "42_final_shutdown_raw.json",
                "43_pid_lineage_cleanup_raw.json",
                "99_b2_same_checkpoint_matrix.json",
            }
            self.assertEqual(
                {path.name for path in artifacts.glob("*.json")},
                expected_files,
            )
            for action in ("accept", "negotiate", "refuse"):
                ordinal = 1 + ("accept", "negotiate", "refuse").index(
                    action
                )
                payload = json.loads(
                    (
                        artifacts
                        / f"{ordinal}2_{action}_action_raw.json"
                    ).read_text(encoding="utf-8")
                )
                self.assertEqual(payload["result"], "GREEN")
                self.assertEqual(payload["submit_count"], 1)
                self.assertTrue(payload["checks"]["independent_postcondition"])

    def test_checkpoint_hash_drift_fails_before_second_arm_submission(self) -> None:
        lifecycle, service = self._fresh()
        service.restore_sha_drift_at.add(2)
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(B2SameCheckpointMatrixError) as caught:
                self._run(service, lifecycle, Path(temporary))
            self.assertIn("checkpoint bytes/identity drifted", str(caught.exception))
            self.assertEqual([row[0] for row in service.select_calls], [1])
            self.assertTrue(caught.exception.evidence["recovery"]["baseline_restored"])
            self.assertTrue(caught.exception.evidence["recovery"]["all_tracked_pids_dead"])

    def test_restored_case_drift_fails_before_typed_option(self) -> None:
        lifecycle, service = self._fresh()
        service.restore_case_drift_at.add(2)
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(B2SameCheckpointMatrixError) as caught:
                self._run(service, lifecycle, Path(temporary))
            self.assertIn("checkpoint semantic drift", str(caught.exception))
            self.assertEqual([row[0] for row in service.select_calls], [1])
            self.assertTrue(caught.exception.evidence["recovery"]["baseline_restored"])

    def test_disabled_typed_option_fails_before_any_negotiate_submit(self) -> None:
        lifecycle, service = self._fresh()
        service.restore_disabled_option_at.add(2)
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(B2SameCheckpointMatrixError) as caught:
                self._run(service, lifecycle, Path(temporary))
            self.assertIn("option order/availability changed", str(caught.exception))
            self.assertEqual([row[0] for row in service.select_calls], [1])

    def test_missing_provider_postcondition_is_red_then_restores_baseline(self) -> None:
        lifecycle, service = self._fresh()
        service.apply_effect = False
        with tempfile.TemporaryDirectory() as temporary:
            artifacts = Path(temporary)
            with self.assertRaises(B2SameCheckpointMatrixError) as caught:
                self._run(service, lifecycle, artifacts)
            report = caught.exception.evidence
            self.assertIn("timed out", report["failure_reason"])
            self.assertEqual(len(service.select_calls), 1)
            self.assertTrue(report["recovery"]["baseline_restored"])
            self.assertTrue(report["recovery"]["all_tracked_pids_dead"])
            action = json.loads(
                (artifacts / "12_accept_action_raw.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(action["result"], "RED")
            self.assertEqual(action["submit_count"], 1)
            self.assertFalse(
                action["raw_action_cell_error"]["postcondition_query_green"]
            )

    def test_stale_event_instance_never_reaches_real_submit(self) -> None:
        lifecycle, service = self._fresh()

        def stale_executor(
            proxy: object,
            *,
            owner_character_id: int,
            action: str,
            request_nonce_prefix: str,
        ) -> dict[str, object]:
            snapshot = proxy.snapshot()
            active = snapshot["active_event"]
            proxy.select_event_option(
                1,
                event_instance_id=active["instance_id"] - 1,
                expected_revision=snapshot["revision"],
            )
            return {"result": "GREEN"}

        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(B2SameCheckpointMatrixError) as caught:
                self._run(
                    service,
                    lifecycle,
                    Path(temporary),
                    executor=stale_executor,
                )
            self.assertIn("stale event instance", caught.exception.evidence["failure_reason"])
            self.assertEqual(service.select_calls, [])

    def test_duplicate_submit_attempt_is_red_and_only_one_reaches_service(self) -> None:
        lifecycle, service = self._fresh()

        def duplicate_executor(
            proxy: object,
            *,
            owner_character_id: int,
            action: str,
            request_nonce_prefix: str,
        ) -> dict[str, object]:
            snapshot = proxy.snapshot()
            active = snapshot["active_event"]
            for _ in range(2):
                proxy.select_event_option(
                    1,
                    event_instance_id=active["instance_id"],
                    expected_revision=snapshot["revision"],
                )
            return {"result": "GREEN"}

        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(B2SameCheckpointMatrixError) as caught:
                self._run(
                    service,
                    lifecycle,
                    Path(temporary),
                    executor=duplicate_executor,
                )
            self.assertIn(
                "duplicate option submission",
                caught.exception.evidence["failure_reason"],
            )
            self.assertEqual(len(service.select_calls), 1)

    def test_restore_cleanup_leak_stays_red_after_recovery(self) -> None:
        lifecycle, service = self._fresh()
        lifecycle.leak_restore_numbers.add(1)
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(B2SameCheckpointMatrixError) as caught:
                self._run(service, lifecycle, Path(temporary))
            report = caught.exception.evidence
            self.assertIn("previous_pid_dead", report["failure_reason"])
            self.assertFalse(report["recovery"]["all_tracked_pids_dead"])
            self.assertEqual(report["cleanup"]["result"], "RED")
            self.assertTrue(lifecycle.alive[4000])

    def test_existing_artifact_is_never_overwritten(self) -> None:
        lifecycle, service = self._fresh()
        with tempfile.TemporaryDirectory() as temporary:
            artifacts = Path(temporary)
            (artifacts / "00_matrix_contract.json").write_text(
                "preserve me", encoding="utf-8"
            )
            with self.assertRaises(FileExistsError):
                self._run(service, lifecycle, artifacts)
            self.assertEqual(
                (artifacts / "00_matrix_contract.json").read_text(
                    encoding="utf-8"
                ),
                "preserve me",
            )
            self.assertEqual(service.save_count, 0)


if __name__ == "__main__":
    unittest.main()
