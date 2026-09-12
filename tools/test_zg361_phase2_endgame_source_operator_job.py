from __future__ import annotations

from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import zg361_phase2_endgame_source_operator_job as operator


class EndgameSourceOperatorTests(unittest.TestCase):
    def test_retry_accepts_only_retained_pre_save_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            job = operator.EndgameSourceOperatorJob(root / "activation.json")
            job.bound = {"artifact_directory": root}
            job.state = "AF5_RED_PARKED"
            job.stage = "bounded_endgame_source_action"
            job.service = mock.Mock()
            job.binding = {"bridge_pid": 123, "connection_generation": 1}
            job._run_retry = mock.Mock()
            with mock.patch.object(operator.base, "ck3_pids", return_value=[]):
                response = job.retry()
                assert job.worker is not None
                job.worker.join(timeout=1.0)
            self.assertTrue(response["accepted"])
            self.assertEqual(response["control"], "retry-source")
            job._run_retry.assert_called_once_with()

    def test_validate_activation_binds_prefix_and_focused_route(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            checkpoint = root / "source.ck3"
            checkpoint.write_bytes(b"source")
            prefix = root / "prefix.json"
            prefix.write_text("{}", encoding="utf-8")
            value = {
                "job_role": operator.JOB_ROLE,
                "source_route": {
                    "expected_owner_character_id": 32904,
                    "expected_date_raw": 2000,
                    "max_advance_days": 30,
                    "game_version": "1.19.0.6",
                },
                "phase2_source_checkpoint_prefix": operator.base.file_record(prefix),
            }
            base_bound = {
                "checkpoint": checkpoint,
                "expected_hashes": {
                    "checkpoint_sha256": operator.base.sha256(checkpoint),
                    "product_tree_sha256": "A" * 64,
                    "game_exe_sha256": "E" * 64,
                    "code_commit": "b" * 40,
                },
            }
            capture = mock.Mock()
            with mock.patch.object(operator.base, "read_object", return_value=value), \
                    mock.patch.object(operator.base, "validate_activation", return_value=base_bound), \
                    mock.patch.object(operator.importlib, "import_module", return_value=capture):
                bound = operator.validate_activation(
                    root / "activation.json", require_empty_slot=True
                )
            self.assertEqual(bound["endgame_source_max_advance_days"], 30)
            self.assertEqual(
                bound["phase2_source_checkpoint_prefix"], prefix.resolve()
            )
            lineage = bound["endgame_source_runtime_capture_lineage"]
            self.assertEqual(lineage["mod_mount"]["tree_sha256"], "A" * 64)
            self.assertEqual(
                lineage["game"],
                {"version": "1.19.0.6", "exe_sha256": "E" * 64},
            )
            capture.preflight_endgame_source_capture_prefix.assert_called_once()

    def test_execute_action_publishes_current_product_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            tools = root / "tools"
            tools.mkdir()
            module_path = tools / "zg361_phase2_endgame_source_action_cell.py"
            module_path.write_text("# fixture", encoding="utf-8")
            artifacts = root / "artifacts"
            artifacts.mkdir()
            checkpoint = root / "source.ck3"
            bridge = root / "bridge.dll"
            prefix = root / "prefix.json"
            for path, data in (
                (checkpoint, b"source"),
                (bridge, b"bridge"),
                (prefix, b"{}"),
            ):
                path.write_bytes(data)
            run = mock.Mock(
                return_value={
                    "result": "GREEN",
                    "source_checkpoint_captured": True,
                }
            )
            module = SimpleNamespace(__file__=str(module_path), run_endgame_source_capture=run)
            bound = {
                "repository_root": root,
                "artifact_directory": artifacts,
                "phase2_source_checkpoint_prefix": prefix,
                "endgame_source_expected_owner_character_id": 32904,
                "endgame_source_expected_date_raw": 2000,
                "endgame_source_runtime_capture_lineage": {"seed_lineage_id": "seed"},
                "endgame_source_max_advance_days": 30,
                "endgame_source_timeout_seconds": 1800.0,
                "round": "R506",
                "checkpoint": checkpoint,
                "bridge_dll": bridge,
                "expected_hashes": {
                    "code_commit": "c" * 40,
                    "product_tree_sha256": "D" * 64,
                },
            }
            job = operator.EndgameSourceOperatorJob(root / "activation.json")
            job.bound = bound
            job.binding = {"bridge_pid": 123, "connection_generation": 1}
            job.service = mock.Mock()
            with mock.patch.object(operator.importlib, "import_module", return_value=module):
                job._execute_action(bound)
            self.assertEqual(job.product_result, "GREEN")
            self.assertTrue((artifacts / "endgame-source-green.json").is_file())
            self.assertEqual(
                run.call_args.kwargs["request_nonce"],
                "R506.phase2-endgame-source",
            )


if __name__ == "__main__":
    unittest.main()
