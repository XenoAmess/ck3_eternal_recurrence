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
            self.assertIn("retry-stage10", operator.CONTROLS)
            evidence = operator.base.read_object(
                artifacts / "stage10-player-subject-green.json"
            )
            self.assertEqual(evidence["round"], "R440")
            self.assertTrue(evidence["production_live"])
            self.assertFalse(evidence["video_lock_touched"])

    def test_hot_retry_passes_failed_progress_to_action(self) -> None:
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
            bridge = root / "bridge.dll"
            bridge.write_bytes(b"bridge")
            source_checkpoint = root / "source.ck3"
            source_checkpoint.write_bytes(b"source")
            terminal_checkpoint = root / "terminal.ck3"
            terminal_checkpoint.write_bytes(b"terminal")
            progress = {
                "timeline_origin_date_raw": 9000,
                "absolute_end_date_raw": 11880,
                "timeline_interrupt_drains": [],
                "unexpected_event": {
                    "event_definition_key": "travel_completion_event.1000"
                },
            }
            bound = {
                "repository_root": root,
                "artifact_directory": artifacts,
                "round": "R504",
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

            def saved(path: Path) -> dict[str, object]:
                return {
                    "accepted": True,
                    "checkpoint": {"status": "saved", "path": str(path)},
                }

            action = mock.Mock(return_value={
                "result": "GREEN",
                "source_checkpoint": saved(source_checkpoint),
                "terminal_checkpoint": saved(terminal_checkpoint),
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
            job.attempt = 2
            job.failure_evidence = {"evidence": {"progress": progress}}

            with mock.patch.object(
                operator.importlib, "import_module", return_value=module
            ):
                job._execute_action(bound)

            action.assert_called_once_with(
                job.service,
                evidence_directory=artifacts / "stage10",
                request_nonce="R504.stage10.player-subject.retry-02",
                expected_player_manager_character_id=200,
                expected_owner_character_id=100,
                resume_progress=progress,
            )

    def test_retry_refuses_after_event_input_was_attempted(self) -> None:
        job = operator.Stage10PlayerSubjectOperatorJob(Path("activation.json"))
        job.state = "AF5_RED_PARKED"
        job.stage = "stage10_player_subject_action"
        job.service = mock.Mock()
        job.binding = {"bridge_pid": 101, "connection_generation": 4}
        job.failure_evidence = {
            "evidence": {
                "progress": {
                    "unexpected_event": {
                        "event_definition_key": "travel_completion_event.1000"
                    }
                },
                "selection": {"accepted": False},
            }
        }

        result = job.retry()

        self.assertFalse(result["accepted"])
        self.assertIn("input already attempted", result["reason"])

    def test_source_receipt_must_bind_player_manager_topology_and_tree(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            checkpoint = root / "source.ck3"
            checkpoint.write_bytes(b"source")
            receipt_path = root / "source.json"
            live_path = root / "live-source.json"
            near_path = root / "near-boundary-red.json"
            extended_path = root / "extended-boundary-red.json"
            full_path = root / "full-boundary-product-red.json"
            debug_path = root / "r492-debug.log"
            roster_path = root / "exact-roster.json"
            schedule_path = root / "scheduled-events.json"
            live = {
                "schema_version": 1,
                "kind": operator.LIVE_SOURCE_KIND,
                "result": "GREEN",
                "production_live": True,
                "mcp_native_save": True,
                "fixture_used": False,
                "console_used": False,
                "product_tree_sha256": "A" * 64,
                "target_checkpoint": operator.base.file_record(checkpoint),
                "target_binding": {
                    "player_character_id": 200,
                    "paused": True,
                    "map_ready": True,
                    "date_raw": 9000,
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
            operator.base.write_object(
                near_path,
                {
                    "schema_version": 1,
                    "result": "RED",
                    "product_result": "RED",
                    "red_preserved": True,
                    "evidence": {
                        "schema_version": 2,
                        "kind": operator.NEAR_BOUNDARY_KIND,
                        "result": "RED",
                        "max_advance_days": 30,
                        "expected_player_manager_character_id": 200,
                        "expected_owner_character_id": 100,
                        "source_binding": {
                            "player_character_id": 200,
                            "date_raw": 9000,
                        },
                        "progress": {
                            "initial_progress_observation": {
                                "date_raw": 9000,
                                "review_now_eligible": False,
                                "b1_active": True,
                                "central_active": False,
                                "pp_active": False,
                            }
                        },
                    },
                },
            )
            operator.base.write_object(
                extended_path,
                {
                    "schema_version": 1,
                    "result": "RED",
                    "product_result": "RED",
                    "red_preserved": True,
                    "evidence": {
                        "schema_version": 2,
                        "kind": operator.NEAR_BOUNDARY_KIND,
                        "result": "RED",
                        "max_advance_days": 45,
                        "expected_player_manager_character_id": 200,
                        "expected_owner_character_id": 100,
                        "source_binding": {
                            "player_character_id": 200,
                            "date_raw": 9000,
                        },
                        "progress": {
                            "initial_progress_observation": {
                                "date_raw": 9000,
                                "review_now_eligible": False,
                                "b1_active": True,
                                "central_active": False,
                                "pp_active": False,
                            }
                        },
                    },
                },
            )
            full_observations = [
                {
                    "date_raw": 9000 + index,
                    "review_now_eligible": False,
                    "b1_active": True,
                    "central_active": False,
                    "pp_active": False,
                }
                for index in range(1, 41)
            ]
            operator.base.write_object(
                full_path,
                {
                    "schema_version": 1,
                    "result": "RED",
                    "product_result": "RED",
                    "red_preserved": True,
                    "evidence": {
                        "schema_version": 2,
                        "kind": operator.NEAR_BOUNDARY_KIND,
                        "result": "RED",
                        "reason_code": "stage10_slice_failed",
                        "max_advance_days": 120,
                        "expected_player_manager_character_id": 200,
                        "expected_owner_character_id": 100,
                        "source_binding": {
                            "player_character_id": 200,
                            "date_raw": 9000,
                        },
                        "progress": {
                            "initial_progress_observation": {
                                "date_raw": 9000,
                                "review_now_eligible": False,
                                "b1_active": True,
                                "central_active": False,
                                "pp_active": False,
                            },
                            "absolute_end_date_raw": 9040,
                            "progress_observations": full_observations,
                        },
                    },
                },
            )
            debug_path.write_text(
                (operator.PUBLICATION_LOG + "\n") * 7
                + (operator.COMPACTION_FAILURE_LOG + "\n") * 10,
                encoding="utf-8",
            )

            def variable(value_type: str, identity: int) -> dict[str, object]:
                return {
                    "present": True,
                    "type": value_type,
                    "identity": identity,
                }

            subject_ids = list(range(1000, 1029))
            exact_ids = subject_ids[:6]
            roster_rows = []
            for character_id in subject_ids:
                exact = character_id in exact_ids
                roster_rows.append(
                    {
                        "character_id": character_id,
                        "found": True,
                        "alive": True,
                        "variables": {
                            "zg361_b1_case_owner": variable(
                                "char", 200 if exact else 400
                            ),
                            "zg361_b1_case_subject": variable("char", character_id),
                            "zg361_b1_cycle_serial": variable(
                                "value", 1700000 if exact else 1900000
                            ),
                            "zg361_b1_case_serial": variable(
                                "value", 1700000 if exact else 1900000
                            ),
                            "zg361_b1_case_state": variable("value", 300000),
                            "zg361_b1_case_active": variable("value", 100000),
                            "zg361_b1_roster_included": variable("value", 100000),
                        },
                        "lists": {},
                    }
                )
            roster = {
                "schema_version": 1,
                "kind": operator.ROSTER_KIND,
                "result": "GREEN",
                "game_version": "1.19.0.6",
                "root_character_id": 200,
                "requested_root_variables": [
                    "zg361_b1_manager_cycle_serial",
                    "zg361_b1_manager_case_serial",
                ],
                "requested_lists": [
                    "zg361_b1_subjects",
                    "zg361_b1_processing_subjects",
                ],
                "requested_referenced_variables": [
                    "zg361_b1_case_owner",
                    "zg361_b1_case_subject",
                    "zg361_b1_cycle_serial",
                    "zg361_b1_case_serial",
                    "zg361_b1_case_state",
                    "zg361_b1_case_active",
                    "zg361_b1_roster_included",
                ],
                "root": {
                    "found": True,
                    "alive": True,
                    "variables": {
                        "zg361_b1_manager_cycle_serial": variable("value", 1700000),
                        "zg361_b1_manager_case_serial": variable("value", 1700000),
                    },
                    "lists": {
                        "zg361_b1_subjects": {
                            "present": True,
                            "item_count": 29,
                            "duration": 29,
                            "items": [
                                {"type": "char", "identity": value}
                                for value in subject_ids
                            ],
                        },
                        "zg361_b1_processing_subjects": {
                            "present": False,
                            "item_count": 0,
                            "duration": None,
                            "items": [],
                        },
                    },
                },
                "unique_referenced_character_count": 29,
                "referenced_characters": roster_rows,
                "melted_sha256": "C" * 64,
            }
            operator.base.write_object(roster_path, roster)
            operator.base.write_object(
                schedule_path,
                {
                    "schema_version": 1,
                    "kind": operator.SCHEDULE_KIND,
                    "result": "GREEN",
                    "event_prefix": "zg361b1.",
                    "root_character_id": 200,
                    "matches": [
                        {
                            "event": "zg361b1.102",
                            "root_character_id": 200,
                            "days_from_current": 1,
                        }
                    ],
                    "source": operator.base.file_record(checkpoint),
                },
            )
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
                "offline_evidence": {"melted_sha256": "C" * 64},
                "source_product_tree_sha256": "A" * 64,
                "product_tree_sha256": "B" * 64,
                "checkpoint": operator.base.file_record(checkpoint),
                "live_source_provenance": operator.base.file_record(live_path),
                "near_boundary_live_evidence": operator.base.file_record(near_path),
                "extended_boundary_live_evidence": operator.base.file_record(
                    extended_path
                ),
                "full_boundary_product_red_evidence": operator.base.file_record(
                    full_path
                ),
                "r492_live_debug_log": operator.base.file_record(debug_path),
                "exact_roster_evidence": operator.base.file_record(roster_path),
                "scheduled_event_evidence": operator.base.file_record(schedule_path),
                "fixed_tail_contract": {
                    "source_b1_stage": "D+299",
                    "first_pending_event": "zg361b1.102",
                    "first_pending_event_days": 1,
                    "shadow_close_days": 30,
                    "common_bank_close_latest_cycle_day": 335,
                    "manager_calibration_latest_cycle_day": 336,
                    "pending_watchdog_days": 31,
                    "post_seal_reopen_days": 30,
                    "player_publication_callback_days": 1,
                    "manager_f_ticket_days": 5,
                    "latest_stage10_cycle_day": 403,
                    "maximum_required_tail_days": 104,
                    "maximum_action_days": 120,
                },
                "product_fix_contract": {
                    "root_commit": operator.PRODUCT_FIX_COMMIT,
                    "source_product_tree_sha256": "A" * 64,
                    "repaired_product_tree_sha256": "B" * 64,
                    "manager_cycle_identity": 1700000,
                    "manager_case_identity": 1700000,
                    "observed_subject_count": 29,
                    "exact_case_subject_count": 6,
                    "foreign_subject_count": 23,
                    "exact_case_character_ids": exact_ids,
                    "foreign_owner_character_id": 400,
                    "foreign_cycle_identity": 1900000,
                    "foreign_case_identity": 1900000,
                    "r492_observation_count": 40,
                    "publication_log_count": 7,
                    "compaction_failure_log_count": 10,
                },
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

            roster["referenced_characters"][0]["variables"][
                "zg361_b1_case_owner"
            ]["identity"] = 999
            operator.base.write_object(roster_path, roster)
            receipt["exact_roster_evidence"] = operator.base.file_record(roster_path)
            operator.base.write_object(receipt_path, receipt)
            with self.assertRaisesRegex(
                operator.base.Af5JobError, "matching player-publication source"
            ):
                operator._validate_source_receipt(
                    operator.base.file_record(receipt_path), bound
                )
            roster["referenced_characters"][0]["variables"][
                "zg361_b1_case_owner"
            ]["identity"] = 200
            operator.base.write_object(roster_path, roster)
            receipt["exact_roster_evidence"] = operator.base.file_record(roster_path)

            schedule = operator.base.read_object(schedule_path)
            schedule["matches"][0]["days_from_current"] = 2
            operator.base.write_object(schedule_path, schedule)
            receipt["scheduled_event_evidence"] = operator.base.file_record(
                schedule_path
            )
            operator.base.write_object(receipt_path, receipt)
            with self.assertRaisesRegex(
                operator.base.Af5JobError, "matching player-publication source"
            ):
                operator._validate_source_receipt(
                    operator.base.file_record(receipt_path), bound
                )

            schedule["matches"][0]["days_from_current"] = 1
            operator.base.write_object(schedule_path, schedule)
            receipt["scheduled_event_evidence"] = operator.base.file_record(
                schedule_path
            )

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

            topology_path = root / "topology.json"
            cleanup_path = root / "cleanup.json"
            for row in roster_rows:
                variables = row["variables"]
                variables["zg361_b1_case_owner"] = variable("char", 200)
                variables["zg361_b1_cycle_serial"] = variable("value", 1700000)
                variables["zg361_b1_case_serial"] = variable("value", 1700000)
                variables["zg361_b1_case_state"] = variable("value", 700000)
            roster["root"]["lists"]["zg361_b1_processing_subjects"] = {
                "present": True,
                "item_count": len(subject_ids),
                "duration": len(subject_ids),
                "items": [
                    {"type": "char", "identity": value} for value in subject_ids
                ],
            }
            roster["source"] = operator.base.file_record(checkpoint)
            operator.base.write_object(roster_path, roster)
            topology_report = {
                "schema_version": 1,
                "kind": operator.TOPOLOGY_KIND,
                "result": "GREEN",
                "game_version": "1.19.0.6",
                "meta_number_of_players": 1,
                "played_character_records": [
                    {"character_id": 200, "player_id": 1}
                ],
                "currently_played_character_ids": [200],
                "offline_single_player_ready": True,
                "player_manager_candidates": [
                    {
                        "player_manager_character_id": 200,
                        "immediate_liege_character_id": 100,
                        "player_primary_title_tier": 3,
                        "player_government": "celestial_government",
                        "direct_landed_vassal_character_ids": [300],
                    }
                ],
                "source": operator.base.file_record(checkpoint),
                "melted_sha256": "C" * 64,
            }
            operator.base.write_object(topology_path, topology_report)
            live.update(
                product_tree_sha256="B" * 64,
                game_time_advanced=False,
                source_admission_kind="managed-autosave",
            )
            operator.base.write_object(live_path, live)
            operator.base.write_object(
                cleanup_path,
                {
                    "schema_version": 1,
                    "kind": operator.SOURCE_CLEANUP_KIND,
                    "result": "GREEN",
                    "cleanup_proven": True,
                    "ck3_pids_after": [],
                    "canonical_cleanup": {
                        "result": "GREEN",
                        "failed_checks": [],
                    },
                },
            )
            schedule = {
                "schema_version": 1,
                "kind": operator.SCHEDULE_KIND,
                "result": "GREEN",
                "game_version": "1.19.0.6",
                "event_prefix": "zg361b1.",
                "root_character_id": 200,
                "matched_count": len(subject_ids),
                "matches": [
                    {
                        "event": "zg361b1.122",
                        "root_character_id": 200,
                        "days_from_current": 30,
                    }
                    for _ in subject_ids
                ],
                "source": operator.base.file_record(checkpoint),
                "melted_sha256": "C" * 64,
            }
            operator.base.write_object(schedule_path, schedule)
            receipt = {
                "schema_version": 1,
                "kind": operator.SOURCE_RECEIPT_KIND_V7,
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
                "offline_topology": topology_report["player_manager_candidates"][0],
                "offline_evidence": {
                    "report": operator.base.file_record(topology_path),
                    "melted_sha256": "C" * 64,
                },
                "product_tree_sha256": "B" * 64,
                "checkpoint": operator.base.file_record(checkpoint),
                "live_source_provenance": operator.base.file_record(live_path),
                "source_cleanup_provenance": operator.base.file_record(cleanup_path),
                "exact_roster_evidence": operator.base.file_record(roster_path),
                "scheduled_event_evidence": operator.base.file_record(schedule_path),
                "fixed_tail_contract": {
                    "source_b1_state": 7,
                    "first_pending_event": "zg361b1.122",
                    "first_pending_event_days": 30,
                    "maximum_action_days": 120,
                },
                "product_fix_contract": {
                    "root_commit": operator.PRODUCT_FIX_COMMIT,
                    "repaired_product_tree_sha256": "B" * 64,
                    "exact_subject_count": len(subject_ids),
                },
            }
            operator.base.write_object(receipt_path, receipt)
            result = operator._validate_source_receipt(
                operator.base.file_record(receipt_path), bound
            )
            self.assertEqual(result["player_manager_character_id"], 200)
            self.assertEqual(result["owner_character_id"], 100)

            schedule["matches"][0]["days_from_current"] = 31
            operator.base.write_object(schedule_path, schedule)
            receipt["scheduled_event_evidence"] = operator.base.file_record(
                schedule_path
            )
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
