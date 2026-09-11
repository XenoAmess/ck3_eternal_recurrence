from __future__ import annotations

import copy
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import zg361_phase2_terminal_stages_operator_job as stages


def b1_frame(state=8, agenda=3):
    def fields(**values):
        return {key: {"status": "available", "value": value, "unavailable_reason": None}
                for key, value in values.items()}
    return {"status": "available", "date_raw": 100,
            "cycle": fields(cycle_serial=2, case_serial=2, state=state, active=state < 8),
            "roster": fields(subject_count=3, amendment_count=0, audit_version=1, reopen_required=False),
            "processing": fields(count=3, agenda_count=agenda),
            "quota": fields(rebuild_generation=1, built_case_serial=2,
                            target_top=1, target_middle=1, target_bottom=1,
                            recount_top=1, recount_middle=1, recount_bottom=1),
            "closure": fields(state=4, calibration_finalized=True, rewards_issued=True),
            "pending": fields(open_count=0), "readiness": {"ready": True}, "anomalies": [],
            "invariants": {name: True for name in (
                "active_matches_state", "closed_state_coherent", "quota_target_conserved",
                "quota_recount_conserved", "quota_target_matches_recount",
                "processing_within_roster", "counts_nonnegative")}}


def b1_service(frame):
    service = mock.Mock()
    service.capabilities.return_value = {"bridge_capabilities": [stages.B1_CAPABILITY]}
    service.snapshot.return_value = {"paused": True, "revision": 9}
    service.query_zhongguo_b1_cycle_snapshot_v1.return_value = frame
    return service


class TerminalStagesOperatorTests(unittest.TestCase):
    def test_current_b1_cycle_can_verify_without_historical_cycle_8(self):
        result = stages.observe_b1(b1_service(b1_frame()), "R406.b1")
        self.assertEqual(result["result"], "GREEN")
        self.assertTrue(result["fix_verified"])
        self.assertTrue(result["check_receipt"]["current_cycle_case_bound"])
        self.assertFalse(result["product_red"])

    def test_b1_lifecycle_not_reached_is_pending(self):
        result = stages.observe_b1(b1_service(b1_frame(state=3)), "R406.b1")
        self.assertEqual(result["result"], "PENDING")
        self.assertFalse(result["fix_verified"])
        self.assertEqual(result["reason"], "b1_closure_lifecycle_not_reached")

    def test_actual_final_survivor_mismatch_remains_b1_red(self):
        result = stages.observe_b1(b1_service(b1_frame(agenda=4)), "R406.b1")
        self.assertEqual(result["result"], "RED")
        self.assertTrue(result["product_red"])
        self.assertFalse(result["check_receipt"]["agenda_matches_processing"])

    def test_stage_green_archives_existing_final_save_and_keeps_b1_pending(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifacts = root / "artifacts"
            artifacts.mkdir()
            source, bridge = root / "source.ck3", root / "bridge.dll"
            source.write_bytes(b"source")
            bridge.write_bytes(b"bridge")
            bound = {"repository_root": root, "artifact_directory": artifacts,
                     "round": "R406", "checkpoint": source, "bridge_dll": bridge,
                     "expected_hashes": {"product_tree_sha256": "A" * 64, "code_commit": "b" * 40}}
            checkpoint = {"path": str(root / "checkpoint.ck3"), "status": "saved", "size": 3, "sha256": "C" * 64}
            evidence = {"result": "GREEN", "save_result": {"accepted": True, "checkpoint": checkpoint},
                        "owned_stage_sequence": [9, 11], "independent_stage10_required": True,
                        "p1_acceptance_evidence": {"central_stage_terminals": {str(i): {"result": "GREEN"} for i in (9, 11)}}}
            action = mock.Mock(return_value=evidence)
            module = SimpleNamespace(__file__=str(root / "tools/zg361_phase2_terminal_stages_action_cell.py"),
                                     run_terminal_stages=action)
            job = stages.TerminalStagesOperatorJob(root / "activation.json")
            job.bound = bound
            job.service = mock.Mock()
            job.service.capabilities.return_value = {"bridge_capabilities": []}
            job.service.snapshot.return_value = {"revision": 30, "paused": True}
            job.runner = mock.Mock()
            job.runner._phase2_archive_checkpoint.return_value = {"path": str(artifacts / "representative-terminal.ck3"), "sha256": "C" * 64}
            with mock.patch.object(stages.importlib, "import_module", return_value=module), \
                 mock.patch.object(stages.base, "ck3_pids", return_value=[]):
                job._execute_action(bound)
                status = job.status()
            action.assert_called_once_with(job.service, evidence_directory=artifacts / "stages", request_nonce="R406.terminal-stages")
            job.service.save_checkpoint.assert_not_called()
            self.assertEqual(status["stages_result"], "GREEN")
            self.assertEqual(status["b1_result"], "PENDING")
            self.assertEqual(status["cleanup_result"], "PENDING")
            self.assertEqual(status["controls"], stages.CONTROLS)
            self.assertTrue((artifacts / "representative-terminal-checkpoint.json").is_file())
            job.runner._phase2_archive_checkpoint.assert_called_once_with(
                checkpoint, artifacts / "representative-terminal.ck3",
                save_lineage_id="R406.central-stages-9-and-11",
            )

    def test_partial_stage_failure_preserves_evidence_and_paused_checkpoint(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            job = stages.TerminalStagesOperatorJob(root / "activation.json")
            job.bound = {"artifact_directory": root, "round": "R406"}
            job.stage = "terminal_stages_action"
            job.service = mock.Mock()
            job.service.snapshot.return_value = {"paused": True, "revision": 11}
            job.service.save_checkpoint.return_value = {"accepted": True, "checkpoint": {"status": "saved", "path": "checkpoint"}}
            job.runner = mock.Mock()
            job.runner._phase2_archive_checkpoint.return_value = {"path": "partial.ck3", "sha256": "D" * 64}
            partial = {"current_stage": 11, "p1_acceptance_evidence": {"central_stage_terminals": {"9": {"result": "GREEN"}}}}
            with mock.patch.object(stages.base, "ck3_pids", return_value=[123]):
                job._record_failure(stages.base.Af5JobError("stage 11 wait failed", partial))
            stored = stages.base.read_object(root / "terminal-stages-red-attempt-01.json")
            self.assertEqual(stored["evidence"], partial)
            self.assertEqual(stored["archived_checkpoint"]["path"], "partial.ck3")
            self.assertFalse((root / "af5-red.json").exists())

    def test_hot_retry_keeps_existing_service_and_stage_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            original = {"expected_hashes": {key: "A" * 64 for key in stages.base.HASH_FIELDS},
                        "repository_root": root / "old", "artifact_directory": root, "round": "R406"}
            original.update({key: key for key in ("game_directory", "product_root", "product_projection_manifest", "checkpoint",
                                                "bridge_dll", "bridge_injector", "state_directory", "bridge_pipe", "warmup_bridge_pipe", "rounds")})
            repaired = {**original, "repository_root": root / "new", "activation_record": {"sha256": "C" * 64},
                        "expected_hashes": {**original["expected_hashes"], "code_commit": "b" * 40}}
            job = stages.TerminalStagesOperatorJob(root / "activation.json")
            job.bound = original
            service = mock.Mock()
            job.service = service
            with mock.patch.object(stages, "validate_activation", return_value=repaired), \
                 mock.patch.object(job, "_retained_binding", return_value={"bridge_pid": 123}), \
                 mock.patch.object(stages.base.Af5OperatorJob, "_reload_action_modules"), \
                 mock.patch.object(stages.importlib, "import_module"), \
                 mock.patch.object(stages.importlib, "reload"), \
                 mock.patch.object(job, "_execute") as cold_setup, \
                 mock.patch.object(job, "_execute_action") as action, \
                 mock.patch.object(stages.base, "ck3_pids", return_value=[123]), \
                 mock.patch("builtins.print"):
                job._run_stage_retry()
            cold_setup.assert_not_called()
            action.assert_called_once_with(repaired)
            self.assertIs(job.service, service)
            self.assertTrue((root / "terminal-stages-retry-02.json").is_file())


if __name__ == "__main__":
    unittest.main()
