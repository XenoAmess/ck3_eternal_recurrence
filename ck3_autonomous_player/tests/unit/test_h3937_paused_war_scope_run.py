from __future__ import annotations

import copy
from contextlib import ExitStack
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import xar_autoplayer.h3937_paused_war_scope_run as producer
import xar_autoplayer.cli as cli
from xar_autoplayer.bridge.succession_transition_contract import (
    ORDINARY_CAMPAIGN_SUCCESSION,
    bind_succession_lifecycle_from_environment_v1,
)


def _army(army_id: int, owner: int, province: int, *, controllable: bool,
          route: list[int] | None = None) -> dict[str, object]:
    route = [] if route is None else route
    return {
        "army_id": army_id, "owner_character_id": owner,
        "current_province_id": province,
        "move_target_province_id": route[-1] if route else None,
        "move_target_observable": bool(route), "route_province_ids": route,
        "army_state": "moving" if route else "regular",
        "army_state_code": 7 if route else 1,
        "in_combat": False, "retreating": False,
        "controllable": controllable,
    }


def _frame() -> dict[str, object]:
    frame = {
        "snapshot_id": "native:4", "revision": 5, "native_revision": 4,
        "date_raw": producer.EXPECTED_DATE_RAW,
        "episode_run_id": producer.EXPECTED_EPISODE_RUN_ID,
        "episode_character_id": 29829, "paused": True, "map_ready": True,
        "played_character": {"character_id": 29829},
        "active_event": None, "pending_character_interaction": None,
        "player_armies": [_army(producer.ARMY_ID, 29829, 2610,
                                 controllable=True)],
        "active_wars": [{
            "war_id": producer.WAR_ID, "player_side": "defender",
            "objective_province_states": [], "allied_armies": [],
            "enemy_armies": [
                _army(50331920, 30097, 2629, controllable=False),
                _army(83886484, 35357, 2630, controllable=False,
                      route=[2631, 2610]),
            ],
        }],
    }
    frame["active_wars"][0]["allied_armies"] = [
        copy.deepcopy(frame["player_armies"][0])]
    return frame


class H3937Phase0Tests(unittest.TestCase):
    def test_real_receipt_bytes_match_real_file_sha(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            receipt = Path(temp_dir) / "ordinary-seed-rebind-v1.json"
            receipt.write_bytes(b'{"source_sha256":"abcdef"}\n')
            parsed, digest = producer._read_rebind_receipt_and_sha(receipt)
            self.assertEqual(parsed, {"source_sha256": "abcdef"})
            self.assertEqual(digest, producer._sha256(receipt))

    def test_actual_validator_return_binds_prepared_ordinary_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state_dir = Path(temp_dir) / "state"
            profile_dir = state_dir / "profile"
            spec = SimpleNamespace(
                state_dir=state_dir, profile_dir=profile_dir,
                manifest_path=profile_dir / "xar-autoplayer-environment.json",
            )
            save = profile_dir / "save games" / "xar_checkpoint.ck3"
            save.parent.mkdir(parents=True)
            save.write_bytes(b"synthetic ordinary phase-0 checkpoint")
            save_sha = hashlib.sha256(save.read_bytes()).hexdigest()
            manifest = {
                "rules": {"profile": [{"rule": "xar_enabled", "setting": "xar_off"}]},
                "environment_sha256": "e" * 64,
            }
            spec.manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            lifecycle = bind_succession_lifecycle_from_environment_v1(
                manifest, lifecycle=ORDINARY_CAMPAIGN_SUCCESSION,
                ordinary_campaign_no_pact=True,
            )
            checkpoint = {
                "name": "xar_checkpoint.ck3", "size": save.stat().st_size,
                "sha256": save_sha, "date_raw": producer.EXPECTED_DATE_RAW,
                "history_index": 1, "episode_character_id": 29829,
                "episode_run_id": producer.EXPECTED_EPISODE_RUN_ID,
                "succession_lifecycle": lifecycle,
            }
            driver = {
                "format_version": 2, "pipe_name": "test",
                "episode_character_id": 29829,
                "episode_run_id": producer.EXPECTED_EPISODE_RUN_ID,
                "succession_lifecycle": lifecycle,
                "last_checkpoint": checkpoint,
                "command_history": [{
                    "index": 1, "command": "save-checkpoint", "ok": True,
                    "result": {"checkpoint": {
                        "size": save.stat().st_size, "sha256": save_sha,
                        "date_raw": producer.EXPECTED_DATE_RAW,
                        "succession_lifecycle": lifecycle,
                    }},
                }],
            }
            driver_path = state_dir / "native-session" / "driver-state.json"
            driver_path.parent.mkdir(parents=True)
            driver_path.write_text(json.dumps(driver), encoding="utf-8")
            validated = producer.validate_cold_start_checkpoint_for_pipe(
                spec, "test",
            )
            self.assertNotIn("episode_run_id", validated)
            self.assertEqual(
                producer._bind_exact_h3937_ordinary_lifecycle(
                    spec, validated, driver,
                ), lifecycle,
            )
            changed = copy.deepcopy(driver)
            changed["succession_lifecycle"] = {
                **lifecycle, "environment_sha256": "f" * 64,
            }
            with self.assertRaisesRegex(producer.AgentError, "prepared ordinary profile"):
                producer._bind_exact_h3937_ordinary_lifecycle(
                    spec, validated, changed,
                )
            manifest["rules"]["profile"][0]["setting"] = "xar_on"
            spec.manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(producer.AgentError, "not runnable"):
                producer._bind_exact_h3937_ordinary_lifecycle(
                    spec, validated, driver,
                )

    def test_cli_refuses_before_make_spec_or_bridge_environment(self) -> None:
        with patch.object(cli, "make_spec") as spec, patch.object(
            cli, "configure_native_bridge_launch_environment"
        ) as configure, patch("builtins.print"):
            self.assertEqual(cli.main([
                "native-observe-h3937-paused-war-scope-v1",
                "--ownership-round-id", "R999",
            ]), 1)
        spec.assert_not_called()
        configure.assert_not_called()

    def test_hard_gate_refuses_before_environment_or_session(self) -> None:
        spec = SimpleNamespace(state_dir=Path("missing"), profile_dir=Path("missing"))
        with patch.object(producer, "native_bridge_launch_config_from_environment") as env, patch.object(
            producer, "native_session"
        ) as session:
            with self.assertRaisesRegex(producer.AgentError, "authorization absent"):
                producer.collect_h3937_paused_war_scope_once(
                    spec, ownership_round_id="R999", cold_start_checkpoint=True)
        env.assert_not_called()
        session.assert_not_called()

    def test_dynamic_roster_does_not_require_old_h3928_positions(self) -> None:
        scope = producer._phase0_scope(_frame())
        self.assertIsNotNone(scope)
        assert scope is not None
        self.assertEqual(scope["all_hostile_army_ids"], [50331920, 83886484])
        self.assertEqual(scope["enemy_armies"][1]["current_province_id"], 2630)
        self.assertEqual(scope["enemy_armies"][1]["route_province_ids"], [2631, 2610])
        self.assertEqual(scope["province_2610_occupation"], "not_observed")
        self.assertFalse(scope["complete_physical_army_inventory_proven"])
        self.assertFalse(scope["route_read_completeness_proven"])
        self.assertFalse(scope["date_advance_authorized"])

    def test_missing_war_roster_or_own_army_fails_closed(self) -> None:
        for mutation in ("no_war", "wrong_war", "no_enemy", "no_player",
                         "extra_war", "wrong_actor", "running"):
            with self.subTest(mutation=mutation):
                frame = _frame()
                if mutation == "no_war":
                    frame["active_wars"] = []
                elif mutation == "wrong_war":
                    frame["active_wars"][0]["war_id"] = 1
                elif mutation == "no_enemy":
                    frame["active_wars"][0]["enemy_armies"] = []
                elif mutation == "no_player":
                    frame["player_armies"] = []
                elif mutation == "extra_war":
                    frame["active_wars"].append(copy.deepcopy(frame["active_wars"][0]))
                elif mutation == "wrong_actor":
                    frame["played_character"]["character_id"] = 1
                else:
                    frame["paused"] = False
                self.assertIsNone(producer._phase0_scope(frame))

    def test_ambiguous_or_unobservable_enemy_fields_fail_closed(self) -> None:
        for mutation in ("duplicate", "missing_province", "missing_route",
                         "invalid_route", "missing_state", "controllable_enemy",
                         "unknown_target", "inconsistent_target",
                         "empty_route_observable"):
            with self.subTest(mutation=mutation):
                frame = _frame()
                enemy = frame["active_wars"][0]["enemy_armies"][1]
                if mutation == "duplicate":
                    enemy["army_id"] = 50331920
                elif mutation == "missing_province":
                    enemy["current_province_id"] = None
                elif mutation == "missing_route":
                    del enemy["route_province_ids"]
                elif mutation == "invalid_route":
                    enemy["route_province_ids"] = [0]
                elif mutation == "missing_state":
                    del enemy["army_state_code"]
                elif mutation == "controllable_enemy":
                    enemy["controllable"] = True
                elif mutation == "inconsistent_target":
                    enemy["move_target_province_id"] = 2614
                elif mutation == "empty_route_observable":
                    enemy["route_province_ids"] = []
                    enemy["move_target_province_id"] = None
                    enemy["move_target_observable"] = True
                    enemy["army_state"] = "regular"
                    enemy["army_state_code"] = 1
                else:
                    del enemy["move_target_province_id"]
                self.assertIsNone(producer._phase0_scope(frame))

    def test_player_ally_duplicate_must_match_and_hostiles_disjoint(self) -> None:
        self.assertIsNotNone(producer._phase0_scope(_frame()))
        for mutation in ("allied_second_controllable", "allied_player_changed",
                         "enemy_cross_group", "duplicate_player", "duplicate_ally"):
            with self.subTest(mutation=mutation):
                frame = _frame()
                war = frame["active_wars"][0]
                if mutation == "allied_second_controllable":
                    war["allied_armies"].append(
                        _army(909090, 29829, 2610, controllable=True))
                elif mutation == "allied_player_changed":
                    war["allied_armies"][0]["current_province_id"] = 2614
                elif mutation == "enemy_cross_group":
                    war["enemy_armies"][0]["army_id"] = producer.ARMY_ID
                elif mutation == "duplicate_player":
                    frame["player_armies"].append(copy.deepcopy(frame["player_armies"][0]))
                else:
                    war["allied_armies"].append(copy.deepcopy(war["allied_armies"][0]))
                self.assertIsNone(producer._phase0_scope(frame))

    def test_mock_managed_session_makes_zero_steps_and_checks_cleanup(self) -> None:
        for outcome in ("green", "changed", "cleanup_red", "receipt_changed",
                         "checkout_changed"):
            with (self.subTest(outcome=outcome),
                  tempfile.TemporaryDirectory() as temp_dir,
                  ExitStack() as stack):
                spec = SimpleNamespace(
                    state_dir=Path("D:/synthetic-h3937-phase0/state"),
                    profile_dir=Path("D:/synthetic-h3937-phase0/state/profile"),
                    manifest_path=Path(temp_dir) / "xar-autoplayer-environment.json",
                )
                manifest = {
                    "rules": {"profile": [{"rule": "xar_enabled", "setting": "xar_off"}]},
                    "environment_sha256": "a" * 64,
                }
                spec.manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
                lifecycle = bind_succession_lifecycle_from_environment_v1(
                    manifest, lifecycle=ORDINARY_CAMPAIGN_SUCCESSION,
                    ordinary_campaign_no_pact=True,
                )
                config = SimpleNamespace(
                    mode="native-headless", pipe_name="test",
                    dll_path=Path("D:/synthetic-h3937-phase0/xar_ck3_bridge.dll"),
                    injector_path=Path("D:/synthetic-h3937-phase0/xar_ck3_bridge_injector.exe"),
                )
                checkpoint = {
                    "saved_date_raw": producer.EXPECTED_DATE_RAW,
                    "history_index": producer.EXPECTED_HISTORY_INDEX,
                    "succession_lifecycle": lifecycle,
                }
                history = [{"command": "restore-checkpoint", "ok": True}]
                prepared_driver = {
                    "episode_run_id": producer.EXPECTED_EPISODE_RUN_ID,
                    "episode_character_id": 29829,
                    "succession_lifecycle": lifecycle,
                    "last_checkpoint": {
                        "episode_run_id": producer.EXPECTED_EPISODE_RUN_ID,
                        "episode_character_id": 29829,
                        "history_index": producer.EXPECTED_HISTORY_INDEX,
                        "sha256": producer.CHECKPOINT_SHA256,
                        "succession_lifecycle": lifecycle,
                    },
                    "command_history": history,
                }
                before = _frame()
                before["connection_generation"] = 1
                before["native_command_history"] = history
                after = copy.deepcopy(before)
                if outcome == "changed":
                    after["active_wars"][0]["enemy_armies"][1]["current_province_id"] = 2610
                readiness = {
                    key: before[key] for key in (
                        "snapshot_id", "revision", "native_revision", "date_raw",
                        "episode_run_id", "paused", "map_ready", "connection_generation")
                }

                receipt_reads = 0
                checkout_reads = 0

                def fake_hash(path: Path) -> str:
                    nonlocal receipt_reads
                    if path.name == "ordinary-seed-rebind-v1.json":
                        receipt_reads += 1
                        if outcome == "receipt_changed" and receipt_reads > 1:
                            return "e" * 64
                    return {
                        "xar_checkpoint.ck3": producer.CHECKPOINT_SHA256,
                        "driver-state.json": "B" * 64,
                        "player-child-matrilineal-formal-v1.json":
                            producer.CHILD_PENDING_SIDECAR_SHA256,
                        "xar_ck3_bridge.dll": producer.DLL_SHA256,
                        "xar_ck3_bridge_injector.exe": producer.INJECTOR_SHA256,
                        "ordinary-seed-rebind-v1.json": "c" * 64,
                        "h3937_paused_war_scope_run.py": "D" * 64,
                    }[path.name]

                def fake_checkout() -> str:
                    nonlocal checkout_reads
                    checkout_reads += 1
                    return ("F" if outcome == "checkout_changed" and checkout_reads > 1
                            else "A") * 40

                stack.enter_context(patch.object(producer, "H3937_PHASE0_LIVE_AUTHORIZED", True))
                stack.enter_context(patch.object(
                    producer, "validate_native_bridge_launch_config", return_value=config))
                stack.enter_context(patch.object(producer, "ensure_state_path_safe"))
                stack.enter_context(patch.object(
                    producer, "validate_cold_start_checkpoint_for_pipe", return_value=checkpoint))
                stack.enter_context(patch.object(
                    producer, "_read_driver_state", return_value=prepared_driver))
                stack.enter_context(patch.object(
                    producer, "_read_rebind_receipt_and_sha",
                    return_value=({}, "c" * 64)))
                stack.enter_context(patch.object(
                    producer, "_exact_prepared_rebind", return_value=True))
                stack.enter_context(patch.object(producer, "_sha256", side_effect=fake_hash))
                stack.enter_context(patch.object(
                    producer, "_checkout_commit", side_effect=fake_checkout))
                stack.enter_context(patch.object(
                    producer, "_wait_for_readiness", return_value=readiness))
                stack.enter_context(patch.object(
                    producer, "_cleanup_report",
                    return_value={"ok": outcome != "cleanup_red"}))
                stack.enter_context(patch.object(
                    producer, "_cold_restore_bookkeeping", return_value={"exact": True}))
                session = stack.enter_context(patch.object(
                    producer, "native_session", return_value={"ok": True}))
                native_driver = stack.enter_context(patch.object(
                    producer, "NativeHeadlessGameplayDriver"))
                service = stack.enter_context(patch.object(producer, "GameplayBridgeService"))
                service.return_value.snapshot.side_effect = [before, after]
                result = producer.collect_h3937_paused_war_scope_once(
                    spec, ownership_round_id="R999", cold_start_checkpoint=True,
                    native_bridge=config)
                session.assert_called_once()
                service.return_value.execute_step.assert_not_called()
                self.assertFalse(result["action_authorized"])
                self.assertFalse(result["date_advance_authorized"])
                self.assertEqual(result["query_actions"], 0)
                self.assertEqual(result["ok"], outcome == "green")
                self.assertEqual(result["source"]["rebind_receipt_sha256"], "c" * 64)
                self.assertEqual(result["source"]["producer_checkout_commit"], "A" * 40)
                self.assertEqual(result["asset_sha256_before"]["producer_module"], "D" * 64)
                native_driver.assert_called_once_with(
                    config.pipe_name, state_dir=spec.state_dir,
                    save_dir=spec.profile_dir / "save games",
                    succession_lifecycle_binding=lifecycle,
                )
                self.assertEqual(result["checks"]["assets_unchanged"],
                                 outcome != "receipt_changed")
                self.assertEqual(result["checks"]["producer_checkout_unchanged"],
                                 outcome != "checkout_changed")
                self.assertEqual(
                    result["checks"]["war_roster_unchanged"], outcome != "changed")
                self.assertEqual(
                    result["checks"]["cleanup_proven"], outcome != "cleanup_red")


if __name__ == "__main__":
    unittest.main()
