from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest import mock

import zg361_stage10_player_source_capture_operator_job as capture


def snapshot(player: int, revision: int) -> dict[str, object]:
    return {
        "snapshot_id": f"native:{revision}",
        "revision": revision,
        "native_revision": revision,
        "date_raw": 1000,
        "paused": True,
        "map_ready": True,
        "played_character": {"character_id": player},
        "active_event": None,
        "diagnostics": {"bridge_pid": 50, "connection_generation": 2},
    }


def campaign(player: int, owner: int | None) -> dict[str, object]:
    return {
        "status": "available",
        "campaign_root_context_ready": True,
        "readiness": {"ready": True},
        "player_character_id": player,
        "player_character_alive": True,
        "selected_game_rule_tokens": ["zg361_on"],
        "independent": owner is None,
        "immediate_liege_character_id": owner,
        "primary_title": {"tier_raw": 4},
        "government": {"flags": ["government_is_celestial"]},
    }


class Stage10PlayerSourceCaptureTests(unittest.TestCase):
    def test_worker_revalidates_with_source_specific_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            bound = {
                "source_player_character_id": 100,
                "artifact_directory": Path(temporary),
            }
            job = capture.Stage10PlayerSourceCaptureOperatorJob(Path("activation.json"))
            with (
                mock.patch.object(capture, "validate_activation", return_value=bound) as validate,
                mock.patch.object(job, "_execute") as execute,
            ):
                job._run()

            validate.assert_called_once_with(job.activation_path, require_empty_slot=True)
            execute.assert_called_once_with(bound)
            self.assertIs(job.bound, bound)

    def test_capture_switches_qualifies_and_archives_without_time_advance(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifacts = root / "artifacts"
            artifacts.mkdir()
            for name in ("topology.json", "qualification.json", "provenance.json"):
                (root / name).write_text("{}", encoding="utf-8")
            source_save = root / "source.ck3"
            source_save.write_bytes(b"source")
            target_save = root / "target.ck3"
            target_save.write_bytes(b"target")
            service = mock.Mock()
            service.snapshot.side_effect = [
                snapshot(100, 3),
                snapshot(100, 3),
                snapshot(200, 4),
                snapshot(200, 4),
                snapshot(200, 4),
            ]
            service.query_campaign_root_context_v1.side_effect = [
                campaign(100, None),
                campaign(200, 100),
            ]
            service.set_player_character_v1.return_value = {
                "accepted": True,
                "status": "switched",
                "step": "set-played-character-v1-200",
                "from_character_id": 100,
                "to_character_id": 200,
                "postcondition_verified": True,
                "episode_rebind_performed": True,
                "paused": True,
                "map_ready": True,
            }
            service.save_checkpoint.return_value = {
                "accepted": True,
                "checkpoint": {
                    "status": "saved",
                    "path": str(target_save),
                    "size": target_save.stat().st_size,
                    "sha256": "C" * 64,
                },
            }
            runner = mock.Mock()
            archive = artifacts / "stage10-player-manager-source.ck3"
            archive.write_bytes(b"target")
            runner._phase2_archive_checkpoint.return_value = {
                "path": str(archive),
                "bytes": archive.stat().st_size,
                "sha256": "C" * 64,
                "save_lineage_id": "R484.stage10.player-manager-source",
            }
            bound = {
                "artifact_directory": artifacts,
                "round": "R484",
                "source_player_character_id": 100,
                "target_player_manager_character_id": 200,
                "target_owner_character_id": 100,
                "checkpoint": source_save,
                "stage10_topology_report": root / "topology.json",
                "source_live_qualification": root / "qualification.json",
                "source_checkpoint_provenance": root / "provenance.json",
                "expected_hashes": {
                    "code_commit": "A" * 40,
                    "product_tree_sha256": "B" * 64,
                },
            }
            job = capture.Stage10PlayerSourceCaptureOperatorJob(root / "activation.json")
            job.bound = bound
            job.service = service
            job.runner = runner
            job._execute_action(bound)

            self.assertEqual(job.state, "AF5_GREEN_PARKED")
            self.assertEqual(job.status()["state"], "SOURCE_GREEN_PARKED")
            self.assertEqual(job.product_result, "GREEN")
            service.set_player_character_v1.assert_called_once_with(
                200, expected_revision=3
            )
            evidence = capture.base.read_object(
                artifacts / "stage10-player-source-green.json"
            )
            self.assertTrue(evidence["mcp_native_save"])
            self.assertFalse(evidence["game_time_advanced"])
            self.assertEqual(evidence["target_checkpoint"]["sha256"], "C" * 64)

    def test_activation_inputs_reject_multiplayer_topology(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            checkpoint = root / "source.ck3"
            checkpoint.write_bytes(b"source")
            expected = {
                "checkpoint_sha256": capture.base.sha256(checkpoint),
                "product_tree_sha256": "B" * 64,
            }
            topology = {
                "schema_version": 1,
                "kind": capture.TOPOLOGY_KIND,
                "result": "GREEN",
                "authority": "offline-prelaunch-only-live-exact-build-mcp-remains-authoritative",
                "game_version": "1.19.0.6",
                "meta_number_of_players": 5,
                "played_character_records": [{"character_id": 100, "player_id": 1}],
                "currently_played_character_ids": [100],
                "source": capture.base.file_record(checkpoint),
                "player_manager_candidates": [{
                    "player_manager_character_id": 200,
                    "immediate_liege_character_id": 100,
                    "player_primary_title_tier": 4,
                    "player_government": "celestial_government",
                    "direct_landed_vassal_count": 2,
                }],
            }
            qualification = {
                "result": "GREEN",
                "game_time_advanced": False,
                "before_snapshot": snapshot(100, 3),
            }
            provenance = {
                "result": "GREEN",
                "checkpoint": {"sha256": expected["checkpoint_sha256"]},
                "source_contract_binding": {"played_manager_character_id": 100},
            }
            paths = {}
            for name, value in (
                ("topology", topology),
                ("qualification", qualification),
                ("provenance", provenance),
            ):
                path = root / f"{name}.json"
                capture.base.write_object(path, value)
                paths[name] = path
            activation = {
                "source_player_character_id": 100,
                "target_player_manager_character_id": 200,
                "target_owner_character_id": 100,
                "stage10_topology_report": capture.base.file_record(paths["topology"]),
                "source_live_qualification": capture.base.file_record(paths["qualification"]),
                "source_checkpoint_provenance": capture.base.file_record(paths["provenance"]),
            }
            bound = {"checkpoint": checkpoint, "expected_hashes": expected}
            with self.assertRaisesRegex(
                capture.base.Af5JobError, "matching offline/live provenance"
            ):
                capture._validate_activation_inputs(activation, bound)

    def test_activation_accepts_exact_managed_autosave_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = root / "session-state"
            artifacts = root / "session-artifacts"
            checkpoint = state / "profile" / "last_save.ck3"
            checkpoint.parent.mkdir(parents=True)
            artifacts.mkdir()
            checkpoint.write_bytes(b"SAV0101-source")
            expected = {
                "checkpoint_sha256": capture.base.sha256(checkpoint),
                "product_tree_sha256": "B" * 64,
                "game_exe_sha256": "E" * 64,
            }
            topology = {
                "schema_version": 1,
                "kind": capture.TOPOLOGY_KIND,
                "result": "GREEN",
                "authority": "offline-prelaunch-only-live-exact-build-mcp-remains-authoritative",
                "game_version": "1.19.0.6",
                "meta_number_of_players": 1,
                "played_character_records": [{"character_id": 100, "player_id": 1}],
                "currently_played_character_ids": [100],
                "source": capture.base.file_record(checkpoint),
                "player_manager_candidates": [{
                    "player_manager_character_id": 200,
                    "immediate_liege_character_id": 100,
                    "player_primary_title_tier": 4,
                    "player_government": "celestial_government",
                    "direct_landed_vassal_count": 2,
                }],
            }

            def number(value: int) -> dict[str, object]:
                return {"present": True, "number": value}

            def character(value: int) -> dict[str, object]:
                return {"present": True, "character_id": value}

            discovery = {
                "schema_version": 1,
                "kind": capture.DISCOVERY_KIND,
                "result": "GREEN",
                "game_version": "1.19.0.6",
                "source": capture.base.file_record(checkpoint),
                "roots": [{
                    "root_character_id": 200,
                    "variables": {
                        "zg361_b1_manager_cycle_serial": number(5),
                        "zg361_b1_manager_case_serial": number(5),
                    },
                    "lists": {
                        "zg361_b1_subjects": {
                            "present": True,
                            "items": [{"type": "char", "identity": 300}],
                        },
                        "zg361_b1_processing_subjects": {
                            "present": True,
                            "items": [{"type": "char", "identity": 300}],
                        },
                    },
                }],
                "referenced_characters": [{
                    "character_id": 300,
                    "alive": True,
                    "variables": {
                        "zg361_b1_case_owner": character(200),
                        "zg361_b1_case_subject": character(300),
                        "zg361_b1_cycle_serial": number(5),
                        "zg361_b1_case_serial": number(5),
                        "zg361_b1_case_state": number(7),
                        "zg361_b1_case_active": number(1),
                        "zg361_b1_roster_included": number(1),
                    },
                }],
            }
            scheduled = {
                "schema_version": 1,
                "kind": capture.SCHEDULED_EVENT_KIND,
                "result": "GREEN",
                "game_version": "1.19.0.6",
                "event_prefix": "zg361b1.",
                "root_character_id": 200,
                "matched_count": 1,
                "matches": [{
                    "event": "zg361b1.122",
                    "root_character_id": 200,
                    "days_from_current": 30,
                }],
                "source": capture.base.file_record(checkpoint),
            }
            session = {
                "job_role": "stage10-player-subject",
                "state_directory": str(state),
                "artifact_directory": str(artifacts),
                "expected_hashes": {
                    "game_exe_sha256": expected["game_exe_sha256"],
                    "product_tree_sha256": expected["product_tree_sha256"],
                },
            }
            loader = {
                "result": "GREEN",
                "tracked_ck3_pid": 50,
                "last_snapshot": snapshot(100, 3),
            }
            red = {
                "result": "RED",
                "failure_stage": "stage10_player_subject_action",
                "ck3_pids": [50],
                "evidence": {
                    "source_binding": {"player_character_id": 100},
                    "progress": {
                        "result": "SCENARIO_INVALID",
                        "player_character_id": 100,
                        "scenario_invalidating_interrupt": {
                            "classification": "scenario-invalidating-interrupt",
                            "handling": "fail-closed-no-selection",
                            "recipient_character_id": 100,
                            "selection_attempted": False,
                        },
                    },
                },
            }
            objects = {
                "topology": topology,
                "discovery": discovery,
                "scheduled": scheduled,
                "session": session,
                "loader": loader,
                "red": red,
            }
            paths = {}
            for name, value in objects.items():
                directory = artifacts if name in {"loader", "red"} else root
                path = directory / f"{name}.json"
                capture.base.write_object(path, value)
                paths[name] = path
            provenance = {
                "schema_version": 1,
                "kind": capture.MANAGED_AUTOSAVE_KIND,
                "result": "GREEN",
                "source_player_character_id": 100,
                "target_player_manager_character_id": 200,
                "checkpoint": capture.base.file_record(checkpoint),
                "source_session_activation": capture.base.file_record(paths["session"]),
                "loader_native_readiness": capture.base.file_record(paths["loader"]),
                "managed_scenario_red": capture.base.file_record(paths["red"]),
                "b1_discovery_report": capture.base.file_record(paths["discovery"]),
                "scheduled_event_report": capture.base.file_record(paths["scheduled"]),
            }
            provenance_path = root / "provenance.json"
            capture.base.write_object(provenance_path, provenance)
            activation = {
                "source_player_character_id": 100,
                "target_player_manager_character_id": 200,
                "target_owner_character_id": 100,
                "stage10_topology_report": capture.base.file_record(paths["topology"]),
                "source_managed_autosave_provenance": capture.base.file_record(
                    provenance_path
                ),
            }
            bound = {"checkpoint": checkpoint, "expected_hashes": expected}
            validated = capture._validate_activation_inputs(activation, bound)

        self.assertEqual(validated["source_admission_kind"], "managed-autosave")
        self.assertEqual(validated["managed_source_exact_subject_count"], 1)
        self.assertEqual(validated["managed_source_cycle"], 5)

    def test_control_surface_has_no_retry(self) -> None:
        self.assertEqual(capture.CONTROLS, ["status", "capture-source", "cleanup"])
        self.assertNotIn("retry", " ".join(capture.CONTROLS))


if __name__ == "__main__":
    unittest.main()
