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
                "stage10_player_manager_character_id": 200,
                "stage10_owner_character_id": 100,
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
            action.assert_called_once_with(
                job.service,
                evidence_directory=artifacts / "stage10",
                request_nonce="R440.stage10.player-subject",
                expected_player_manager_character_id=200,
                expected_owner_character_id=100,
            )
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

    def test_source_receipt_must_bind_player_manager_topology_and_tree(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            checkpoint = root / "source.ck3"
            checkpoint.write_bytes(b"source")
            receipt_path = root / "source.json"
            live_path = root / "live-source.json"
            live = {
                "schema_version": 1,
                "kind": operator.LIVE_SOURCE_KIND,
                "result": "GREEN",
                "production_live": True,
                "mcp_native_save": True,
                "fixture_used": False,
                "console_used": False,
                "product_tree_sha256": "B" * 64,
                "target_checkpoint": operator.base.file_record(checkpoint),
                "target_binding": {
                    "player_character_id": 200,
                    "paused": True,
                    "map_ready": True,
                },
                "target_campaign_root": {
                    "status": "available",
                    "campaign_root_context_ready": True,
                    "player_character_id": 200,
                    "immediate_liege_character_id": 100,
                    "independent": False,
                    "primary_title": {"tier_raw": 3},
                    "government": {
                        "flags": ["government_is_celestial"],
                    },
                },
            }
            operator.base.write_object(live_path, live)
            receipt = {
                "schema_version": 1,
                "kind": operator.SOURCE_RECEIPT_KIND,
                "result": "GREEN",
                "offline_topology_observed": True,
                "offline_single_player_observed": True,
                "fixture_used": False,
                "console_used": False,
                "selection_attempted": False,
                "source_container_header": "SAV0101",
                "game_version": "1.19.0.6",
                "offline_player_state": {
                    "meta_number_of_players": 1,
                    "played_character_records": [
                        {"character_id": 200, "player_id": 1}
                    ],
                    "currently_played_character_ids": [200],
                },
                "offline_topology": {
                    "player_manager_character_id": 200,
                    "immediate_liege_character_id": 100,
                    "direct_landed_vassal_character_ids": [300],
                    "player_primary_title_tier": 3,
                    "player_government": "celestial_government",
                },
                "product_tree_sha256": "B" * 64,
                "checkpoint": operator.base.file_record(checkpoint),
                "live_source_provenance": operator.base.file_record(live_path),
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
            self.assertEqual(result["player_manager_character_id"], 200)
            self.assertEqual(result["owner_character_id"], 100)

            receipt["offline_topology"]["immediate_liege_character_id"] = 200
            operator.base.write_object(receipt_path, receipt)
            with self.assertRaisesRegex(
                operator.base.Af5JobError, "matching player-publication source"
            ):
                operator._validate_source_receipt(
                    operator.base.file_record(receipt_path), bound
                )

            receipt["offline_topology"]["immediate_liege_character_id"] = 100
            receipt["offline_player_state"]["meta_number_of_players"] = 5
            operator.base.write_object(receipt_path, receipt)
            with self.assertRaisesRegex(
                operator.base.Af5JobError, "matching player-publication source"
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
                "stage10_player_manager_character_id": 200,
                "stage10_owner_character_id": 100,
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
