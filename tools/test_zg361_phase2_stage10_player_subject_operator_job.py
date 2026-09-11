from __future__ import annotations

from pathlib import Path
import sys
from types import SimpleNamespace
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

import zg361_phase2_stage10_player_subject_operator_job as operator


class Stage10PlayerSubjectOperatorTests(unittest.TestCase):
    def test_activation_requires_explicit_stage10_role(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "activation.json"
            with mock.patch.object(
                operator.base, "read_object", return_value={"job_role": "terminal-stages"}
            ):
                with self.assertRaisesRegex(
                    operator.base.Af5JobError,
                    "does not target Stage 10 player-subject",
                ):
                    operator.validate_activation(path, require_empty_slot=False)

    def test_green_action_archives_exact_source_and_terminal(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            tools = root / "tools"
            tools.mkdir()
            module_path = tools / "zg361_phase2_stage10_player_subject_action_cell.py"
            module_path.write_text("# synthetic", encoding="utf-8")
            artifacts = root / "artifacts"
            artifacts.mkdir()
            input_checkpoint = root / "input.ck3"
            input_checkpoint.write_bytes(b"input")
            source_receipt = root / "source-receipt.json"
            source_receipt.write_text("{}", encoding="utf-8")
            source_checkpoint = root / "source.ck3"
            source_checkpoint.write_bytes(b"source")
            terminal_checkpoint = root / "terminal.ck3"
            terminal_checkpoint.write_bytes(b"terminal")
            bridge = root / "bridge.dll"
            bridge.write_bytes(b"bridge")
            bound = {
                "repository_root": root,
                "artifact_directory": artifacts,
                "round": "R440",
                "checkpoint": input_checkpoint,
                "stage10_source_receipt": source_receipt,
                "bridge_dll": bridge,
                "expected_hashes": {
                    "code_commit": "a" * 40,
                    "product_tree_sha256": "B" * 64,
                    "checkpoint_sha256": operator.base.sha256(input_checkpoint),
                },
            }

            def save(path: Path) -> dict[str, object]:
                return {
                    "accepted": True,
                    "checkpoint": {
                        "status": "saved",
                        "path": str(path),
                        "size": path.stat().st_size,
                        "sha256": "C" * 64,
                    },
                }

            action = mock.Mock(return_value={
                "result": "GREEN",
                "source_checkpoint": save(source_checkpoint),
                "terminal_checkpoint": save(terminal_checkpoint),
                "p1_acceptance_evidence": {
                    "central_stage_10_terminal": {
                        "result": "GREEN",
                        "provider_observed": True,
                        "terminal_postcondition_verified": True,
                        "action_ack_is_business_postcondition": False,
                    }
                },
            })
            module = SimpleNamespace(
                __file__=str(module_path),
                run_stage10_player_subject=action,
            )
            runner = mock.Mock()
            runner._phase2_archive_checkpoint.side_effect = [
                {"path": str(artifacts / "source.ck3"), "sha256": "D" * 64},
                {"path": str(artifacts / "terminal.ck3"), "sha256": "E" * 64},
            ]
            job = operator.Stage10PlayerSubjectOperatorJob(root / "activation.json")
            job.bound = bound
            job.binding = {"bridge_pid": 101, "connection_generation": 4}
            job.service = mock.Mock()
            job.runner = runner
            with mock.patch.object(
                operator.importlib, "import_module", return_value=module
            ):
                job._execute_action(bound)

            self.assertEqual(runner._phase2_archive_checkpoint.call_count, 2)
            self.assertEqual(job.state, "AF5_GREEN_PARKED")
            self.assertEqual(job.product_result, "GREEN")
            self.assertEqual(job.status()["controls"], operator.CONTROLS)
            self.assertNotIn("retry-stage10", operator.CONTROLS)
            evidence = operator.base.read_object(
                artifacts / "stage10-player-subject-green.json"
            )
            self.assertEqual(evidence["round"], "R440")
            self.assertTrue(evidence["production_live"])
            self.assertFalse(evidence["video_lock_touched"])

    def test_source_receipt_must_bind_checkpoint_event_selector_and_tree(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            checkpoint = root / "source.ck3"
            checkpoint.write_bytes(b"source")
            receipt_path = root / "source.json"
            receipt = {
                "schema_version": 1,
                "kind": operator.SOURCE_RECEIPT_KIND,
                "result": "GREEN",
                "production_live": True,
                "provider_observed": True,
                "fixture_used": False,
                "console_used": False,
                "selection_attempted": False,
                "source_event_definition_key": operator.SOURCE_EVENT,
                "source_event_instance_id": 390,
                "source_event_context": {
                    "event_definition_key": operator.SOURCE_EVENT,
                    "current_event_instance_id": 390,
                    "root_scope": {
                        "typed_identity": {
                            "status": "available",
                            "kind": "character",
                            "character_id": 100,
                        }
                    },
                },
                "owner_character_id": 100,
                "player_character_id": 100,
                "selected_manager_character_id": 200,
                "selector": {
                    "status": "available",
                    "provider_observed": True,
                    "readiness": {"ready": True},
                    "selection": {"manager_character_id": 200},
                },
                "product_tree_sha256": "B" * 64,
                "checkpoint": operator.base.file_record(checkpoint),
            }
            operator.base.write_object(receipt_path, receipt)
            bound = {
                "checkpoint": checkpoint,
                "expected_hashes": {
                    "product_tree_sha256": "B" * 64,
                    "checkpoint_sha256": operator.base.sha256(checkpoint),
                },
            }
            result = operator._validate_source_receipt(
                operator.base.file_record(receipt_path), bound
            )
            self.assertEqual(result["path"], receipt_path.resolve())

            receipt["source_event_definition_key"] = "zg361cl.389"
            operator.base.write_object(receipt_path, receipt)
            with self.assertRaisesRegex(
                operator.base.Af5JobError, "matching qualified .390"
            ):
                operator._validate_source_receipt(
                    operator.base.file_record(receipt_path), bound
                )

    def test_archive_failure_preserves_green_product_result(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            tools = root / "tools"
            tools.mkdir()
            module_path = tools / "zg361_phase2_stage10_player_subject_action_cell.py"
            module_path.write_text("# synthetic", encoding="utf-8")
            artifacts = root / "artifacts"
            artifacts.mkdir()
            source_checkpoint = root / "source.ck3"
            source_checkpoint.write_bytes(b"source")
            bound = {
                "repository_root": root,
                "artifact_directory": artifacts,
                "round": "R440",
                "expected_hashes": {
                    "code_commit": "a" * 40,
                    "product_tree_sha256": "B" * 64,
                },
            }
            action_evidence = {
                "result": "GREEN",
                "source_checkpoint": {
                    "accepted": True,
                    "checkpoint": {
                        "status": "saved",
                        "path": str(source_checkpoint),
                    },
                },
                "p1_acceptance_evidence": {
                    "central_stage_10_terminal": {
                        "result": "GREEN",
                        "provider_observed": True,
                        "terminal_postcondition_verified": True,
                        "action_ack_is_business_postcondition": False,
                    }
                },
            }
            module = SimpleNamespace(
                __file__=str(module_path),
                run_stage10_player_subject=mock.Mock(return_value=action_evidence),
            )
            job = operator.Stage10PlayerSubjectOperatorJob(root / "activation.json")
            job.bound = bound
            job.binding = {"bridge_pid": 101, "connection_generation": 4}
            job.service = mock.Mock()
            job.runner = mock.Mock()
            job.runner._phase2_archive_checkpoint.side_effect = RuntimeError(
                "archive unavailable"
            )

            with mock.patch.object(
                operator.importlib, "import_module", return_value=module
            ):
                with self.assertRaisesRegex(RuntimeError, "archive unavailable") as caught:
                    job._execute_action(bound)

            self.assertEqual(job.product_result, "GREEN")
            self.assertEqual(job.af5_evidence, action_evidence)
            job.service = None
            job._record_failure(caught.exception)
            self.assertEqual(job.product_result, "GREEN")
            self.assertEqual(job.failure_evidence["product_result"], "GREEN")
            self.assertTrue(
                (artifacts / "stage10-player-subject-red.json").is_file()
            )


if __name__ == "__main__":
    unittest.main()
