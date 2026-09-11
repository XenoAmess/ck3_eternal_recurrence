from __future__ import annotations

from pathlib import Path
import sys
from types import SimpleNamespace
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

import zg361_phase2_terminal_cold_restore_operator_job as operator


class TerminalColdRestoreOperatorTests(unittest.TestCase):
    def test_activation_requires_explicit_cold_restore_role(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "activation.json"
            with mock.patch.object(
                operator.base, "read_object", return_value={"job_role": "af5-terminal"}
            ):
                with self.assertRaisesRegex(
                    operator.base.Af5JobError, "does not target terminal cold restore"
                ):
                    operator.validate_activation(path, require_empty_slot=False)

    def test_activation_requires_next_round_for_restore_pid(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "activation.json"
            for value, accepted in (("R410", True), ("R409", False), (None, False)):
                with self.subTest(value=value), mock.patch.object(
                    operator.base,
                    "read_object",
                    return_value={
                        "job_role": "terminal-cold-restore",
                        "cold_restore_round": value,
                    },
                ), mock.patch.object(
                    operator.base,
                    "validate_activation",
                    return_value={"round": "R409"},
                ):
                    if accepted:
                        result = operator.validate_activation(
                            path, require_empty_slot=False
                        )
                        self.assertEqual(result["cold_restore_round"], "R410")
                    else:
                        with self.assertRaisesRegex(
                            operator.base.Af5JobError,
                            "must immediately follow the gameplay round",
                        ):
                            operator.validate_activation(
                                path, require_empty_slot=False
                            )

    def test_green_action_saves_once_and_hands_lineage_to_cleanup(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            tools = root / "tools"
            tools.mkdir()
            module_path = tools / "zg361_phase2_terminal_cold_restore.py"
            module_path.write_text("# synthetic", encoding="utf-8")
            artifacts = root / "artifacts"
            artifacts.mkdir()
            checkpoint = root / "terminal.ck3"
            checkpoint.write_bytes(b"terminal")
            bridge = root / "bridge.dll"
            bridge.write_bytes(b"bridge")
            bound = {
                "repository_root": root,
                "artifact_directory": artifacts,
                "round": "R408",
                "rounds": {"frontend_warmup": "R407", "gameplay": "R408"},
                "cold_restore_round": "R409",
                "checkpoint": checkpoint,
                "bridge_dll": bridge,
                "bridge_pipe": r"\\.\pipe\xar_ck3_bridge_zg361_00000000000000000000000000000000",
                "activation": {
                    "known_red": ["synthetic-preserved-red"],
                },
                "expected_hashes": {
                    "code_commit": "a" * 40,
                    "product_tree_sha256": "B" * 64,
                    "game_exe_sha256": "D" * 64,
                },
            }
            save_result = {
                "accepted": True,
                "checkpoint": {
                    "status": "saved",
                    "path": str(checkpoint),
                    "size": checkpoint.stat().st_size,
                    "sha256": "C" * 64,
                },
            }
            cold_result = {
                "result": "GREEN",
                "save_restore_lineage": {
                    "result": "GREEN",
                    "first_pid": 101,
                    "second_pid": 202,
                    "first_connection_generation": 4,
                    "second_connection_generation": 5,
                },
                "cleanup_handoff": {
                    "current_pid": 202,
                    "current_generation": 5,
                    "scenario_evidence": {
                        "save_restore_lineage": {"result": "GREEN"}
                    },
                },
                "p1_acceptance_evidence": {
                    "representative_terminal_cold_restore": {"result": "GREEN"}
                },
            }
            cold = mock.Mock(return_value=cold_result)
            module = SimpleNamespace(
                __file__=str(module_path), run_terminal_cold_restore=cold
            )
            service = mock.Mock()
            service.snapshot.return_value = {
                "paused": True,
                "map_ready": True,
                "revision": 33,
            }
            service.save_checkpoint.return_value = save_result
            job = operator.TerminalColdRestoreOperatorJob(root / "activation.json")
            job.bound = bound
            job.binding = {"bridge_pid": 101, "connection_generation": 4}
            job.service = service
            with mock.patch.object(
                operator.importlib, "import_module", return_value=module
            ):
                job._execute_action(bound)
                job._execute_action(bound)
            service.save_checkpoint.assert_called_once_with(expected_revision=33)
            self.assertEqual(cold.call_count, 2)
            self.assertEqual(job.state, "AF5_GREEN_PARKED")
            self.assertEqual(job.product_result, "GREEN")
            self.assertEqual(
                job.af5_evidence,
                {"save_restore_lineage": {"result": "GREEN"}},
            )
            status = job.status()
            self.assertEqual(status["bridge_pid"], 202)
            self.assertEqual(status["connection_generation"], 5)
            self.assertEqual(status["cold_restore_round"], "R409")
            self.assertEqual(status["controls"], operator.CONTROLS)
            self.assertTrue(
                (artifacts / "terminal-cold-restore-green.json").is_file()
            )
            evidence = operator.base.read_object(
                artifacts / "terminal-cold-restore-green.json"
            )
            self.assertEqual(
                evidence["rounds"],
                {
                    "frontend_warmup": "R407",
                    "gameplay": "R408",
                    "cold_restore": "R409",
                },
            )
            self.assertEqual(evidence["restart_record"]["old_pid"], 101)
            self.assertEqual(evidence["restart_record"]["new_pid"], 202)
            self.assertEqual(
                evidence["restart_record"]["known_red"],
                ["synthetic-preserved-red"],
            )

    def test_retry_requires_a_saved_retained_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            job = operator.TerminalColdRestoreOperatorJob(
                Path(temporary) / "activation.json"
            )
            job.state = "AF5_RED_PARKED"
            job.stage = "terminal_cold_restore"
            job.service = mock.Mock()
            response = job.retry()
            self.assertFalse(response["accepted"])
            self.assertIn("no completed retained", response["reason"])


if __name__ == "__main__":
    unittest.main()
