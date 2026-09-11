#!/usr/bin/env python3
"""Synthetic service tests for the production readback/restore composition."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import zg361_phase2_terminal_cold_restore as cold

ROOT = Path(__file__).resolve().parents[1]


def typed(value: object) -> dict[str, object]:
    return {"status": "available", "value": value, "unavailable_reason": None}


def fields(**values: object) -> dict[str, object]:
    return {key: typed(value) for key, value in values.items()}


class TerminalService:
    def __init__(self, root: Path, *, workforce_na: bool = False) -> None:
        self.pid = 101
        self.generation = 3
        self.revision = 50
        self.date = 800
        self.restore_count = 0
        self.queries = []
        self.after_query_failure = False
        self.change_domain = None
        self.generation_step = 1
        self.restore_same_pid = False
        self.fail_after_restore = False
        self.native_command_history = []
        self.af5_terminal = True
        self.af5_tombstone = False
        self.b1_closed = True
        self.b1_anomalies = []
        self.path = root / "profile" / "save games" / "xar_checkpoint.ck3"
        self.path.parent.mkdir(parents=True)
        self.path.write_bytes(b"synthetic terminal save, not a CK3 fixture")
        self.save = {"accepted": True, "checkpoint": {
            "status": "saved", "path": str(self.path), "size": self.path.stat().st_size,
            "sha256": hashlib.sha256(self.path.read_bytes()).hexdigest().upper(), "date_raw": self.date,
        }}
        self.af5 = list(json.loads((ROOT / "ck3_autonomous_player/tests/fixtures/zhongguo_compensation_af5_snapshot_v1.json").read_text())["frames"].values())[-1]
        wf_frames = json.loads((ROOT / "ck3_autonomous_player/tests/fixtures/zhongguo_workforce_owner_snapshot_v1.json").read_text())["frames"]
        self.workforce = wf_frames["not_applicable_without_m360_source" if workforce_na else "history_accruing"]
        self.workforce["workforce"]["central"]["stage11_status"] = typed(3 if workforce_na else 2)

    def snapshot(self) -> dict[str, object]:
        return {"paused": True, "map_ready": True, "revision": self.revision,
                "native_revision": self.revision, "date_raw": self.date,
                "played_character": {"character_id": 147},
                "diagnostics": {"bridge_pid": self.pid, "connection_generation": self.generation},
                "native_command_history": copy.deepcopy(self.native_command_history)}

    def capabilities(self) -> dict[str, object]:
        return {"diagnostics": {"connected": True, "bridge_pid": self.pid,
                                "connection_generation": self.generation}}

    def query_frame(self, name: str, nonce: str, revision: int, frame: dict[str, object]) -> dict[str, object]:
        if revision != self.revision:
            raise AssertionError("aggregate reused a stale public query revision")
        self.queries.append(name)
        self.revision += 1
        response = copy.deepcopy(frame)
        response.update(request_nonce=nonce, snapshot_revision=self.revision, date_raw=self.date,
                        player_character_id=147, source={"connection_generation": self.generation,
                                                        "bridge_pid": self.pid})
        if self.restore_count and self.after_query_failure and name == "af5":
            self.after_query_failure = False
            raise RuntimeError("synthetic post-restore query interruption")
        if self.restore_count and self.change_domain == name:
            if name == "af5":
                response["af5"]["case"]["last_route"] = typed(2)
            elif name == "workforce":
                response["workforce"]["portfolio"]["history_cycle_count"] = typed(2)
        return response

    def query_zhongguo_b1_cycle_snapshot_v1(self, nonce: str, *, expected_revision: int) -> dict[str, object]:
        return self.query_frame("b1", nonce, expected_revision, {
            "status": "available", "player_character_id": 147, "manager_character_id": 147,
            "readiness": {"ready": True}, "cycle": fields(cycle_serial=9, case_serial=9, state=8 if self.b1_closed else 6, active=not self.b1_closed),
            "roster": fields(subject_count=8), "processing": fields(count=8),
            "closure": fields(state=4, calibration_finalized=True, rewards_issued=True),
            "pending": fields(open_count=0, rewards_committed=True),
            "quota": fields(rebuild_generation=1, built_case_serial=9, target_top=2, target_middle=5, target_bottom=1),
            "invariants": {"closed_state_coherent": True},
            "anomalies": copy.deepcopy(self.b1_anomalies),
        })

    def query_zhongguo_compensation_af5_snapshot_v1(self, nonce: str, *, expected_revision: int) -> dict[str, object]:
        response = self.query_frame("af5", nonce, expected_revision, self.af5)
        response["terminal"] = self.af5_terminal
        if self.af5_tombstone:
            def clear(node: object) -> None:
                if isinstance(node, dict):
                    if {"status", "value", "unavailable_reason"} <= set(node):
                        node.update(status="unavailable", value=None,
                                    unavailable_reason="variable_absent")
                        return
                    for child in node.values():
                        clear(child)
                elif isinstance(node, list):
                    for child in node:
                        clear(child)
            clear(response["af5"])
            response.update(
                status="unavailable",
                unavailable_reason="subject_projection_read_failed",
                terminal=False,
                subject_character_id=361,
            )
            response["readiness"] = {
                key: False for key in response["readiness"]
            }
        return response

    def query_zhongguo_workforce_owner_snapshot_v1(self, nonce: str, *, expected_revision: int) -> dict[str, object]:
        return self.query_frame("workforce", nonce, expected_revision, self.workforce)

    def query_zhongguo_promotion_source_progress_v1(self, nonce: str, *, expected_revision: int) -> dict[str, object]:
        frame = {
            "status": "available", "readiness": {"query_ready": True}, "player_character_id": 147,
            "widgets": [{"stable_identity": "zg361_promotion_source_central_active",
                         "instance_pointer": typed(f"0x{self.pid:X}"), "vtable_pointer": typed(f"0x{self.pid + 1:X}"),
                         "exists": typed(True), "effective_visible": typed(False), "enabled": typed(False)}],
        }
        return {"status": "available", "zhongguo_promotion_source_progress": self.query_frame("central", nonce, expected_revision, frame)}

    def restore_checkpoint(self, *, expected_revision: int) -> dict[str, object]:
        if expected_revision != self.revision:
            raise AssertionError("restore used a stale public revision")
        old_pid, old_generation = self.pid, self.generation
        self.restore_count += 1
        if not self.restore_same_pid:
            self.pid += 100
        self.generation += self.generation_step
        self.revision = 1
        result = {"accepted": True, "status": "restored", "source": "native-session-lifecycle-queue",
                  "checkpoint": {**self.save["checkpoint"], "status": "restored"},
                  "restored_date_raw": self.date, "map_ready": True,
                  "lifecycle": {"status": "relaunched", "lifecycle_intent": "restore",
                                "request_id": "synthetic-restore-1", "pipe": "synthetic-pipe",
                                "previous_pid": old_pid, "pid": self.pid,
                                "previous_connection_generation": old_generation,
                                "connection_generation": self.generation}}
        if self.fail_after_restore:
            recovered = copy.deepcopy(result)
            recovered["source"] = "native-session-cold-start"
            recovered["checkpoint"]["status"] = "saved"
            recovered["lifecycle"] = {"previous_pid": old_pid, "pid": self.pid}
            self.native_command_history.append(
                {"index": 1, "command": "restore-checkpoint", "ok": True,
                 "result": recovered}
            )
            outbox = self.path.parents[2] / "native-session" / "bridge" / "outbox"
            outbox.mkdir(parents=True)
            payload = {
                "protocol_version": 1, "request_id": "restore-synthetic",
                "ok": True, "error": None,
                "result": {
                    "status": "relaunched", "lifecycle_intent": "restore",
                    "previous_pid": old_pid, "pid": self.pid,
                    "pipe": "synthetic-pipe", "checkpoint": {
                        "name": "xar_checkpoint.ck3",
                        "size": self.save["checkpoint"]["size"],
                        "sha256": self.save["checkpoint"]["sha256"],
                    },
                },
            }
            (outbox / "restore-synthetic.json").write_text(
                json.dumps(payload), encoding="utf-8"
            )
            raise RuntimeError("synthetic timeout after completed restore")
        return result


class TerminalColdRestoreTests(unittest.TestCase):
    def run_restore(self, service: TerminalService, directory: Path) -> dict[str, object]:
        return cold.run_terminal_cold_restore(service, evidence_directory=directory,
                                             request_nonce="synthetic.cold", save_result=service.save)

    def test_same_supervisor_restore_matches_four_domains_and_existing_gate(self) -> None:
        import run_zhongguo_acceptance as acceptance

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            service = TerminalService(root)
            result = self.run_restore(service, root / "evidence")
            self.assertEqual(result["result"], "GREEN")
            self.assertEqual(service.restore_count, 1)
            self.assertEqual(service.queries, list(cold.DOMAINS) * 2)
            gate = result["p1_acceptance_evidence"]["representative_terminal_cold_restore"]
            self.assertEqual(gate["pid_lineage"], [101, 201])
            self.assertEqual(gate["connection_generation_lineage"], [3, 4])
            self.assertEqual(set(gate["before_readback"]), set(cold.DOMAINS))
            self.assertEqual(gate["before_readback"], gate["after_readback"])
            self.assertTrue(acceptance._phase2_full_tree_completion_gate(result)["checks"]["representative_terminal_cold_restore"])
            self.assertTrue(acceptance.phase2_restore_queue_required(result["cleanup_handoff"]["scenario_evidence"]))
            lineage = result["save_restore_lineage"]
            self.assertTrue(lineage["checks"]["final_capabilities_bind_second_pid"])
            self.assertEqual(result["cleanup_handoff"]["supervisor_initial_pid"], 101)
            self.assertEqual(result["cleanup_handoff"]["current_pid"], 201)
            self.assertEqual(self.run_restore(service, root / "evidence"), result)
            self.assertEqual(service.restore_count, 1)

    def test_projection_ignores_new_native_pointers_and_query_bindings(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            service = TerminalService(Path(temporary))
            before_evidence, after_evidence = {}, {}
            before = cold.read_terminal_domains_v1(service, evidence_out=before_evidence)
            service.pid += 1
            service.generation += 1
            after = cold.read_terminal_domains_v1(service, evidence_out=after_evidence)
            self.assertEqual(before, after)
            self.assertNotEqual(before_evidence["queries"]["central"], after_evidence["queries"]["central"])

    def test_handoff_passes_the_existing_managed_cleanup_contract(self) -> None:
        import run_zhongguo_acceptance as acceptance
        from test_zg361_phase2_formal_live_session_lineage import _shutdown

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            result = self.run_restore(TerminalService(root), root / "evidence")
            handoff = result["cleanup_handoff"]
            # Existing cleanup consumer with a synthetic supervisor report;
            # no supervisor, process shutdown or CK3 is run in this test.
            report = {
                "kind": "ck3_native_headless_session", "mode": "native-headless",
                "pipe": "synthetic-pipe", "pid": 201, "exit_reason": "stop",
                "process_exit_code": None, "shutdown": _shutdown(201),
                "restart_count": 1, "restart_shutdowns": [_shutdown(101)], "ok": True,
            }
            proof = acceptance.prove_phase2_native_session_cleanup(
                report, root, initial_pid=handoff["supervisor_initial_pid"],
                initial_generation=handoff["supervisor_initial_generation"],
                expected_pipe="synthetic-pipe", scenario_evidence=handoff["scenario_evidence"],
                final_capabilities=handoff["final_capabilities"], supervisor_stopped=True,
                managed_stop_requested=True,
            )
            self.assertEqual(proof["result"], "GREEN", proof.get("contract_errors"))

    def test_real_na_representation_keeps_unavailable_m360_source_and_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            result = self.run_restore(TerminalService(root, workforce_na=True), root / "evidence")
            workforce = result["after_readback"]["workforce"]
            self.assertEqual(workforce["state"]["terminal_kind"], "not_applicable")
            self.assertEqual(workforce["receipt"]["m360_receipt"]["choice"]["status"], "unavailable")

    def test_changed_business_receipt_is_red_even_with_good_restore_ack(self) -> None:
        for domain in ("af5", "workforce"):
            with self.subTest(domain=domain), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                service = TerminalService(root)
                service.change_domain = domain
                with self.assertRaises(cold.TerminalColdRestoreError) as raised:
                    self.run_restore(service, root / "evidence")
                self.assertIn("terminal readback differs", str(raised.exception))
                self.assertEqual(raised.exception.evidence["result"], "RED")
                self.assertEqual(service.restore_count, 1)

    def test_requires_new_pid_and_positive_process_local_generation(self) -> None:
        for same_pid, step in ((True, 1), (False, -3)):
            with self.subTest(same_pid=same_pid, step=step), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                service = TerminalService(root)
                service.restore_same_pid, service.generation_step = same_pid, step
                with self.assertRaises(cold.TerminalColdRestoreError) as raised:
                    self.run_restore(service, root / "evidence")
                self.assertTrue(str(raised.exception))
                self.assertEqual(service.queries, list(cold.DOMAINS))

    def test_replacement_process_may_restart_native_generation_at_one(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            service = TerminalService(root)
            service.generation_step = -2
            result = self.run_restore(service, root / "evidence")
            self.assertEqual(result["result"], "GREEN")
            self.assertEqual(
                result["save_restore_lineage"]["connection_generation_lineage"],
                [3, 1],
            )

    def test_retry_recovers_completed_restore_without_third_process(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            service = TerminalService(root)
            service.generation_step = -2
            service.fail_after_restore = True
            directory = root / "evidence"
            with self.assertRaises(cold.TerminalColdRestoreError):
                self.run_restore(service, directory)
            self.assertEqual(service.restore_count, 1)
            service.fail_after_restore = False
            result = self.run_restore(service, directory)
            self.assertEqual(result["result"], "GREEN")
            self.assertEqual(service.restore_count, 1)
            self.assertEqual(
                result["restore_recovery"]["status"],
                "recovered_completed_restore",
            )
            self.assertEqual(result["save_restore_lineage"]["pid_lineage"], [101, 201])
            self.assertEqual(
                result["save_restore_lineage"]["connection_generation_lineage"],
                [3, 1],
            )

    def test_post_restore_query_retry_preserves_transition_and_previous_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            service = TerminalService(root)
            service.after_query_failure = True
            directory = root / "evidence"
            with self.assertRaises(cold.TerminalColdRestoreError):
                self.run_restore(service, directory)
            first_attempt = (directory / "attempt-001.json").read_bytes()
            result = self.run_restore(service, directory)
            self.assertEqual(result["result"], "GREEN")
            self.assertEqual(service.restore_count, 1)
            self.assertEqual(result["attempt"], 2)
            self.assertEqual((directory / "attempt-001.json").read_bytes(), first_attempt)

    def test_independent_b1_and_af5_business_states_do_not_block_restore(self) -> None:
        for field in ("af5_terminal", "b1_closed"):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                service = TerminalService(root)
                setattr(service, field, False)
                result = self.run_restore(service, root / "evidence")
                self.assertEqual(result["result"], "GREEN")
                self.assertEqual(service.restore_count, 1)
                self.assertEqual(
                    result["before_readback"], result["after_readback"]
                )

    def test_representative_workforce_terminal_is_still_required(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            service = TerminalService(root)
            service.workforce["terminal"] = False
            with self.assertRaises(cold.TerminalColdRestoreError):
                self.run_restore(service, root / "evidence")
            self.assertEqual(service.restore_count, 0)

    def test_existing_b1_anomaly_is_preserved_without_becoming_a_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            service = TerminalService(root)
            service.b1_anomalies = ["quota_target_processing_mismatch"]
            result = self.run_restore(service, root / "evidence")
            self.assertEqual(result["result"], "GREEN")
            before = result["before_readback"]["b1"]["receipt"]["anomalies"]
            after = result["after_readback"]["b1"]["receipt"]["anomalies"]
            self.assertEqual(before, ["quota_target_processing_mismatch"])
            self.assertEqual(after, before)

    def test_destroyed_af5_subject_tombstone_is_compared_across_restore(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            service = TerminalService(root)
            service.af5_tombstone = True
            result = self.run_restore(service, root / "evidence")
            af5 = result["after_readback"]["af5"]
            self.assertFalse(af5["state"]["terminal"])
            self.assertEqual(
                af5["receipt"]["observation_status"], "unavailable"
            )
            self.assertEqual(
                af5["receipt"]["unavailable_reason"],
                "subject_projection_read_failed",
            )
            self.assertEqual(
                result["before_readback"], result["after_readback"]
            )

    def test_other_af5_unavailable_reason_stops_before_restore(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            service = TerminalService(root)
            service.af5_tombstone = True
            original = service.query_zhongguo_compensation_af5_snapshot_v1

            def query(nonce: str, *, expected_revision: int) -> dict[str, object]:
                response = original(nonce, expected_revision=expected_revision)
                response["unavailable_reason"] = "different_failure"
                return response

            service.query_zhongguo_compensation_af5_snapshot_v1 = query
            with self.assertRaises(cold.TerminalColdRestoreError):
                self.run_restore(service, root / "evidence")
            self.assertEqual(service.restore_count, 0)


if __name__ == "__main__":
    unittest.main()
