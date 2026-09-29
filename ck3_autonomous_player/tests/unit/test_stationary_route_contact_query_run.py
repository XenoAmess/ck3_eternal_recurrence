from __future__ import annotations

import copy
from contextlib import ExitStack
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT.parent / "tools"))

from xar_autoplayer.stationary_route_contact_query_run import (
    QUERY_STEP,
    _bound_route_result,
    _exact_h3928_paused_subject,
    _exact_one_appended_query,
    _same_frame,
)
import xar_autoplayer.stationary_route_contact_query_run as runner
import g2_preview_operator as operator


def _snapshot() -> dict[str, object]:
    return {
        "paused": True,
        "map_ready": True,
        "snapshot_id": "native:3",
        "revision": 4,
        "native_revision": 3,
        "diagnostics": {"connection_generation": 1},
        "date_raw": 53219928,
        "episode_run_id": "native-29829-2bc2d599f7f9",
        "played_character": {"character_id": 29829, "alive": True},
        "episode_character_id": 29829,
        "route_contact_horizon_supported": True,
        "active_event": None,
        "pending_character_interaction": None,
        "player_armies": [{
            "army_id": 83886367,
            "controllable": True,
            "current_province_id": 2610,
            "move_target_province_id": None,
            "route_province_ids": [],
            "army_state": "regular",
            "in_combat": False,
            "retreating": False,
        }],
        "active_wars": [{
            "war_id": 16777231,
            "enemy_armies": [
                {"army_id": 50331920, "current_province_id": 2629,
                 "move_target_province_id": None, "route_province_ids": [],
                 "retreating": False, "in_combat": False, "army_state": "sieging"},
                {"army_id": 83886484, "current_province_id": 2629,
                 "move_target_province_id": None, "route_province_ids": [],
                 "retreating": False, "in_combat": False, "army_state": "sieging"},
            ],
        }],
    }


def _result() -> dict[str, object]:
    return {
        "step": QUERY_STEP, "accepted": True, "status": "available",
        "query_sequence": 1, "snapshot_revision": 3,
        "queried_snapshot_id": "native:3", "queried_revision": 4,
        "queried_native_revision": 3, "queried_connection_generation": 1,
        "queried_episode_run_id": "native-29829-2bc2d599f7f9",
        "route_contact_horizon": {
            "status": "available", "date_raw": 53219928,
            "snapshot_revision": 3,
            "subject_army_id": 83886367, "target_province_id": 2610,
            "hostile_army_ids": [50331920, 83886484],
            "subject_route": {
                "army_id": 83886367, "current_province_id": 2610,
                "route_province_ids": [],
            },
            "one_day_contact_free": True,
            "horizon_start_date_raw": 53219928,
            "horizon_end_date_raw": 53219952,
        },
    }


class StationaryRouteContactReadOnlyTests(unittest.TestCase):
    def test_bad_source_pair_refuses_before_native_session(self) -> None:
        checkpoint = {
            "saved_date_raw": 53219928,
            "episode_run_id": "native-29829-2bc2d599f7f9",
            "succession_lifecycle": {
                "xar_enabled": "xar_off",
                "lifecycle": "ordinary_campaign_succession",
                "pact_contract": "absent_by_fresh_campaign_xar_off_contract",
            },
        }
        with TemporaryDirectory() as root, ExitStack() as stack:
            spec = SimpleNamespace(
                state_dir=Path(root) / "state",
                profile_dir=Path(root) / "profile",
            )
            config = SimpleNamespace(mode="native-headless", pipe_name="test")
            stack.enter_context(patch.object(runner, "validate_native_bridge_launch_config", return_value=config))
            stack.enter_context(patch.object(runner, "ensure_state_path_safe"))
            stack.enter_context(patch.object(runner, "validate_cold_start_checkpoint_for_pipe", return_value=checkpoint))
            stack.enter_context(patch.object(runner, "_read_driver_state", return_value={"episode_run_id": checkpoint["episode_run_id"]}))
            stack.enter_context(patch.object(runner, "_sha256", return_value="0" * 64))
            session = stack.enter_context(patch.object(runner, "native_session"))
            driver = stack.enter_context(patch.object(runner, "NativeHeadlessGameplayDriver"))
            with self.assertRaisesRegex(runner.AgentError, "source pair identity differs"):
                runner.query_r0345_stationary_route_contact_once(
                    spec, timeout_seconds=390, readiness_timeout_seconds=300,
                    ownership_round_id="R999", cold_start_checkpoint=True,
                    native_bridge=config,
                )
            session.assert_not_called()
            driver.assert_not_called()

    def test_cleanup_failure_is_red_after_one_mock_read_only_query(self) -> None:
        before = _snapshot()
        before["native_command_history"] = [{"command": "restore-checkpoint"}]
        result = _result()
        after = copy.deepcopy(before)
        after["native_command_history"].append({
            "command": QUERY_STEP, "ok": True, "result": result,
        })
        before_driver = {
            "episode_run_id": "native-29829-2bc2d599f7f9",
            "command_history": [],
        }
        after_driver = {
            **before_driver,
            "command_history": copy.deepcopy(after["native_command_history"]),
        }
        checkpoint = {
            "saved_date_raw": 53219928,
            "episode_run_id": "native-29829-2bc2d599f7f9",
            "succession_lifecycle": {
                "xar_enabled": "xar_off",
                "lifecycle": "ordinary_campaign_succession",
                "pact_contract": "absent_by_fresh_campaign_xar_off_contract",
            },
        }
        readiness = {
            key: before[key] for key in (
                "snapshot_id", "revision", "native_revision", "date_raw",
                "paused", "map_ready", "episode_run_id",
            )
        }
        readiness["connection_generation"] = 1
        with TemporaryDirectory() as root, ExitStack() as stack:
            spec = SimpleNamespace(
                state_dir=Path(root) / "state",
                profile_dir=Path(root) / "profile",
            )
            config = SimpleNamespace(mode="native-headless", pipe_name="test")
            stack.enter_context(patch.object(runner, "validate_native_bridge_launch_config", return_value=config))
            stack.enter_context(patch.object(runner, "ensure_state_path_safe"))
            stack.enter_context(patch.object(runner, "validate_cold_start_checkpoint_for_pipe", return_value=checkpoint))
            stack.enter_context(patch.object(runner, "_read_driver_state", side_effect=[before_driver, after_driver]))
            stack.enter_context(patch.object(runner, "_sha256", side_effect=lambda path: (
                runner.CHECKPOINT_SHA256 if path.suffix == ".ck3" else runner.DRIVER_SHA256
            )))
            stack.enter_context(patch.object(runner, "_wait_for_readiness", return_value=readiness))
            stack.enter_context(patch.object(runner, "_cold_restore_bookkeeping", return_value={"exact": True}))
            stack.enter_context(patch.object(runner, "_cleanup_report", return_value={"ok": False, "reason": "cleanup failed"}))
            stack.enter_context(patch.object(runner, "native_session", return_value={"ok": True}))
            fake_driver = stack.enter_context(patch.object(runner, "NativeHeadlessGameplayDriver"))
            fake_service = stack.enter_context(patch.object(runner, "GameplayBridgeService"))
            fake_service.return_value.snapshot.side_effect = [before, after]
            fake_service.return_value.execute_step.return_value = result
            report = runner.query_r0345_stationary_route_contact_once(
                spec, timeout_seconds=390, readiness_timeout_seconds=300,
                ownership_round_id="R999", cold_start_checkpoint=True,
                native_bridge=config,
            )
            self.assertFalse(report["ok"])
            self.assertEqual(report["status"], "RED")
            self.assertFalse(report["checks"]["cleanup_proven"])
            self.assertTrue(report["checks"]["exact_one_appended_query"])
            self.assertFalse(report["action_authorized"])
            fake_service.return_value.execute_step.assert_called_once_with(
                QUERY_STEP, expected_revision=4,
            )
            fake_driver.return_value.close.assert_called_once()


class StationaryOperatorNegativeTests(unittest.TestCase):
    def test_bad_pair_never_reaches_preflight_or_launch(self) -> None:
        with TemporaryDirectory() as root, ExitStack() as stack:
            args = SimpleNamespace(
                manifest=Path(root) / "operator-manifest.json",
                output=Path(root) / "attempt",
                ownership_round_id="R999", timeout=390,
                readiness_timeout=300,
            )
            stack.enter_context(patch.object(operator, "load_manifest", return_value={}))
            stack.enter_context(patch.object(operator, "frozen_source_identity", return_value={}))
            stack.enter_context(patch.object(
                operator, "current_checkpoint_identity", return_value=(
                    Path(root) / "save.ck3", Path(root) / "driver.json",
                    {"episode_character_id": 29829,
                     "episode_run_id": "native-29829-2bc2d599f7f9"},
                ),
            ))
            stack.enter_context(patch.object(operator, "sha256", return_value="0" * 64))
            run_logged = stack.enter_context(patch.object(operator, "run_logged"))
            with self.assertRaisesRegex(ValueError, "paired H3928 source identity differs"):
                operator.command_query_r0345_stationary_route_contact_v1(args)
            run_logged.assert_not_called()
            self.assertFalse(args.output.exists())

    def test_missing_required_checks_cannot_be_green(self) -> None:
        with TemporaryDirectory() as root, ExitStack() as stack:
            save = Path(root) / "save.ck3"
            driver_path = Path(root) / "driver.json"
            save.write_bytes(b"test")
            driver_path.write_bytes(b"test")
            args = SimpleNamespace(
                manifest=Path(root) / "operator-manifest.json",
                output=Path(root) / "attempt",
                ownership_round_id="R999", timeout=390,
                readiness_timeout=300,
            )
            stack.enter_context(patch.object(operator, "load_manifest", return_value={}))
            stack.enter_context(patch.object(operator, "frozen_source_identity", return_value={}))
            stack.enter_context(patch.object(
                operator, "current_checkpoint_identity", return_value=(
                    save, driver_path,
                    {"episode_character_id": 29829,
                     "episode_run_id": "native-29829-2bc2d599f7f9"},
                ),
            ))
            stack.enter_context(patch.object(
                operator, "sha256", side_effect=lambda path: (
                    runner.CHECKPOINT_SHA256 if path.suffix == ".ck3"
                    else runner.DRIVER_SHA256
                ),
            ))
            stack.enter_context(patch.object(operator, "agent_command", return_value=["agent"] ))
            stack.enter_context(patch.object(operator, "lifecycle_contract", return_value={}))
            stack.enter_context(patch.object(operator, "preflight_lifecycle_arguments", return_value=[]))
            run_logged = stack.enter_context(patch.object(operator, "run_logged", return_value=0))
            stack.enter_context(patch("builtins.print"))
            stack.enter_context(patch.object(
                operator, "read_json", return_value={
                    "ok": True, "status": "GREEN_READ_ONLY",
                    "round": "R999", "action_authorized": False,
                    "checks": {}, "cleanup": {"ok": True},
                },
            ))
            self.assertEqual(operator.command_query_r0345_stationary_route_contact_v1(args), 1)
            self.assertEqual(run_logged.call_count, 2)
            saved = json.loads((args.output / "operator-receipt.json").read_text())
            self.assertFalse(saved["ok"])
            self.assertEqual(saved["status"], "query_failed")

    def test_result_binding_rejects_each_missing_identity(self) -> None:
        before = _snapshot()
        result = _result()
        self.assertTrue(_bound_route_result(before, result))
        for field in (
            "queried_snapshot_id", "queried_revision",
            "queried_native_revision", "queried_connection_generation",
            "queried_episode_run_id",
        ):
            malformed = copy.deepcopy(result)
            malformed.pop(field)
            self.assertFalse(_bound_route_result(before, malformed), field)
        for field in ("snapshot_id", "revision", "native_revision", "diagnostics"):
            malformed = copy.deepcopy(before)
            malformed.pop(field)
            self.assertFalse(_bound_route_result(malformed, result), field)

    def test_readiness_and_snapshot_connection_generation_match(self) -> None:
        frame = {
            "snapshot_id": "native:3", "revision": 4, "native_revision": 3,
            "date_raw": 53219928, "paused": True, "map_ready": True,
            "episode_run_id": "native-29829-2bc2d599f7f9",
        }
        readiness = {**frame, "connection_generation": 1}
        snapshot = {**frame, "diagnostics": {"connection_generation": 1}}
        self.assertTrue(_same_frame(readiness, snapshot))
        snapshot["diagnostics"]["connection_generation"] = 2
        self.assertFalse(_same_frame(readiness, snapshot))
        snapshot["diagnostics"]["connection_generation"] = 1
        for field in ("snapshot_id", "native_revision", "episode_run_id"):
            missing_left = copy.deepcopy(readiness)
            missing_right = copy.deepcopy(snapshot)
            missing_left.pop(field)
            missing_right.pop(field)
            self.assertFalse(_same_frame(missing_left, missing_right))

    def test_fixed_query_and_exact_stationary_scope(self) -> None:
        self.assertEqual(
            QUERY_STEP,
            "query-route-contact-horizon-v1-83886367-to-2610-h-2-50331920-83886484",
        )
        self.assertTrue(_exact_h3928_paused_subject(_snapshot()))
        for field, value in (
            ("date_raw", 53219952),
            ("route_contact_horizon_supported", False),
            ("episode_run_id", "different"),
        ):
            wrong = _snapshot()
            wrong[field] = value
            self.assertFalse(_exact_h3928_paused_subject(wrong))
        moving = _snapshot()
        moving["player_armies"][0]["route_province_ids"] = [2614]
        self.assertFalse(_exact_h3928_paused_subject(moving))
        incomplete = _snapshot()
        incomplete["active_wars"][0]["enemy_armies"].pop()
        self.assertFalse(_exact_h3928_paused_subject(incomplete))
        wrong_province = _snapshot()
        wrong_province["active_wars"][0]["enemy_armies"][0]["current_province_id"] = 2610
        self.assertFalse(_exact_h3928_paused_subject(wrong_province))
        hostile_route = _snapshot()
        hostile_route["active_wars"][0]["enemy_armies"][0]["route_province_ids"] = [2610]
        self.assertFalse(_exact_h3928_paused_subject(hostile_route))
        second_war = _snapshot()
        second_war["active_wars"].append({"war_id": 42, "enemy_armies": []})
        self.assertFalse(_exact_h3928_paused_subject(second_war))
        second_army = _snapshot()
        second_army["player_armies"].append({"army_id": 999, "controllable": True})
        self.assertFalse(_exact_h3928_paused_subject(second_army))
        event = _snapshot()
        event["active_event"] = {"instance_id": 1}
        self.assertFalse(_exact_h3928_paused_subject(event))

    def test_exactly_one_matching_query_row_is_required(self) -> None:
        before = {"native_command_history": [{"command": "restore-checkpoint"}]}
        result = {"step": QUERY_STEP, "accepted": True}
        after = copy.deepcopy(before)
        after["native_command_history"].append({
            "command": QUERY_STEP, "ok": True, "result": result,
        })
        self.assertTrue(_exact_one_appended_query(before, after, result))
        after["native_command_history"].append({
            "command": "advance-route-contact-horizon-v1-...", "ok": True,
        })
        self.assertFalse(_exact_one_appended_query(before, after, result))


if __name__ == "__main__":
    unittest.main()
