from __future__ import annotations

from contextlib import ExitStack
import copy
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT.parent / "tools"))

import xar_autoplayer.h3937_stationary_route_contact_query_run as runner
import g2_preview_operator as operator


PREPARED_SHA256 = "FEA5A02009493465264441EBF6160B139705FECEDE4D177147B2EE8B3690F9E8"
ENVIRONMENT_SHA256 = "6D36B220798396AEB7DF7399B1BC9833583A5260CE6C7313D17E6B05E5086A9A"


def _rebind_receipt(
    prepared: str = PREPARED_SHA256, *, state_dir: Path | None = None,
) -> dict[str, object]:
    state_dir = state_dir or Path.cwd()
    profile_dir = state_dir / "profile"
    save_path = profile_dir / "save games" / "xar_checkpoint.ck3"
    driver_path = state_dir / "native-session" / "driver-state.json"
    return {
        "schema": "xar.ck3.ordinary-seed-rebind/v1",
        "ok": True, "status": "rebound", "ck3_launch_attempted": False,
        "state_dir": str(state_dir.resolve()),
        "profile_dir": str(profile_dir.resolve()),
        "pipe_name": "test",
        "environment": {"target_sha256": ENVIRONMENT_SHA256},
        "driver_state": {
            "path": str(driver_path.resolve()),
            "source_sha256": runner.RAW_SOURCE_DRIVER_SHA256,
            "target_sha256": prepared,
        },
        "save": {
            "bytes_unchanged": True,
            "source": {"path": str(save_path.resolve()), "sha256": runner.CHECKPOINT_SHA256},
            "target": {"path": str(save_path.resolve()), "sha256": runner.CHECKPOINT_SHA256},
        },
        "no_launch_preflight_expectations": {
            "pipe_name": "test", "expected_character_id": 29829,
            "expected_episode_run_id": runner.EXPECTED_EPISODE_RUN_ID,
            "expected_checkpoint_sha256": runner.CHECKPOINT_SHA256,
            "expected_driver_state_sha256": prepared,
            "xar_enabled": "xar_off",
            "succession_lifecycle": "ordinary_campaign_succession",
            "ordinary_campaign_no_pact": True,
        },
        "post_rebind_validation": {
            "native_driver_consumer": "passed",
            "cold_checkpoint_validator": "passed",
            "checkpoint": {
                "path": str(save_path.resolve()),
                "history_index": runner.EXPECTED_HISTORY_INDEX,
                "sha256": runner.CHECKPOINT_SHA256,
            },
        },
    }


def _hash_for_path(path: Path) -> str:
    return {
        "xar_checkpoint.ck3": runner.CHECKPOINT_SHA256,
        "driver-state.json": PREPARED_SHA256,
        "player-child-matrilineal-formal-v1.json": runner.CHILD_PENDING_SIDECAR_SHA256,
        "xar_ck3_bridge.dll": runner.DLL_SHA256,
        "xar_ck3_bridge_injector.exe": runner.INJECTOR_SHA256,
    }.get(path.name, "0" * 64)


class H3937StationaryGateTests(unittest.TestCase):
    def test_metadata_candidate_refuses_before_environment_or_game_access(self) -> None:
        spec = SimpleNamespace(state_dir=Path("missing"), profile_dir=Path("missing"))
        with patch.object(runner, "native_bridge_launch_config_from_environment") as env, patch.object(
            runner, "native_session"
        ) as session:
            with self.assertRaisesRegex(runner.AgentError, "no launch"):
                runner.query_h3937_stationary_route_contact_once(
                    spec, timeout_seconds=390, readiness_timeout_seconds=300,
                    ownership_round_id="R999", cold_start_checkpoint=True,
                )
        env.assert_not_called()
        session.assert_not_called()

    def test_rebind_separates_raw_source_from_prepared_driver(self) -> None:
        state_dir = Path.cwd()
        self.assertNotEqual(runner.RAW_SOURCE_DRIVER_SHA256, PREPARED_SHA256)
        self.assertTrue(runner._exact_prepared_rebind(
            _rebind_receipt(state_dir=state_dir), prepared_driver_sha256=PREPARED_SHA256,
            pipe_name="test", state_dir=state_dir,
            profile_dir=state_dir / "profile", environment_sha256=ENVIRONMENT_SHA256,
        ))
        self.assertFalse(runner._exact_prepared_rebind(
            _rebind_receipt(state_dir=state_dir), prepared_driver_sha256=runner.RAW_SOURCE_DRIVER_SHA256,
            pipe_name="test", state_dir=state_dir,
            profile_dir=state_dir / "profile", environment_sha256=ENVIRONMENT_SHA256,
        ))
        stale = _rebind_receipt(state_dir=state_dir)
        stale["driver_state"]["path"] = str(state_dir / "old-driver.json")
        self.assertFalse(runner._exact_prepared_rebind(
            stale, prepared_driver_sha256=PREPARED_SHA256, pipe_name="test",
            state_dir=state_dir, profile_dir=state_dir / "profile",
            environment_sha256=ENVIRONMENT_SHA256,
        ))

    def test_wrong_abi_or_child_pending_bytes_stop_before_native_session(self) -> None:
        for mismatch in ("dll", "injector", "child_sidecar"):
            with self.subTest(mismatch=mismatch), TemporaryDirectory() as root, ExitStack() as stack:
                root_path = Path(root)
                spec = SimpleNamespace(
                    state_dir=root_path / "state",
                    profile_dir=root_path / "state" / "profile",
                )
                config = SimpleNamespace(
                    mode="native-headless", pipe_name="test",
                    dll_path=root_path / "xar_ck3_bridge.dll",
                    injector_path=root_path / "xar_ck3_bridge_injector.exe",
                )
                checkpoint = {
                    "saved_date_raw": runner.EXPECTED_DATE_RAW,
                    "history_index": runner.EXPECTED_HISTORY_INDEX,
                    "succession_lifecycle": {
                        "environment_sha256": ENVIRONMENT_SHA256,
                        "xar_enabled": "xar_off",
                        "lifecycle": "ordinary_campaign_succession",
                        "pact_contract": "absent_by_fresh_campaign_xar_off_contract",
                    },
                }
                stack.enter_context(patch.object(runner, "RECEIVER_ASSETS_AND_SCOPE_VERIFIED", True))
                stack.enter_context(patch.object(runner, "validate_native_bridge_launch_config", return_value=config))
                stack.enter_context(patch.object(runner, "ensure_state_path_safe"))
                stack.enter_context(patch.object(runner, "validate_cold_start_checkpoint_for_pipe", return_value=checkpoint))
                stack.enter_context(patch.object(runner, "_read_driver_state", return_value={
                    "episode_run_id": runner.EXPECTED_EPISODE_RUN_ID,
                    "episode_character_id": 29829,
                    "last_checkpoint": {
                        "episode_run_id": runner.EXPECTED_EPISODE_RUN_ID,
                        "episode_character_id": 29829,
                        "history_index": runner.EXPECTED_HISTORY_INDEX,
                        "sha256": runner.CHECKPOINT_SHA256,
                    },
                }))
                stack.enter_context(patch.object(runner, "_read_rebind_receipt", return_value=_rebind_receipt(state_dir=spec.state_dir)))

                def wrong_hash(path: Path) -> str:
                    if (mismatch == "dll" and path.name == "xar_ck3_bridge.dll") or (
                        mismatch == "injector" and path.name == "xar_ck3_bridge_injector.exe"
                    ) or (mismatch == "child_sidecar" and path.name == "player-child-matrilineal-formal-v1.json"):
                        return "0" * 64
                    return _hash_for_path(path)

                stack.enter_context(patch.object(runner, "_sha256", side_effect=wrong_hash))
                session = stack.enter_context(patch.object(runner, "native_session"))
                driver = stack.enter_context(patch.object(runner, "NativeHeadlessGameplayDriver"))
                with self.assertRaisesRegex(runner.AgentError, "source pair identity differs"):
                    runner.query_h3937_stationary_route_contact_once(
                        spec, timeout_seconds=390, readiness_timeout_seconds=300,
                        ownership_round_id="R999", cold_start_checkpoint=True,
                        native_bridge=config,
                    )
                session.assert_not_called()
                driver.assert_not_called()

    def test_real_validator_checkpoint_shape_passes_identity_gate_in_mock_session(self) -> None:
        with TemporaryDirectory() as root, ExitStack() as stack:
            root_path = Path(root)
            spec = SimpleNamespace(
                state_dir=root_path / "state",
                profile_dir=root_path / "state" / "profile",
            )
            config = SimpleNamespace(
                mode="native-headless", pipe_name="test",
                dll_path=root_path / "xar_ck3_bridge.dll",
                injector_path=root_path / "xar_ck3_bridge_injector.exe",
            )
            checkpoint = {
                "saved_date_raw": runner.EXPECTED_DATE_RAW,
                "history_index": runner.EXPECTED_HISTORY_INDEX,
                "succession_lifecycle": {
                    "environment_sha256": ENVIRONMENT_SHA256,
                    "xar_enabled": "xar_off",
                    "lifecycle": "ordinary_campaign_succession",
                    "pact_contract": "absent_by_fresh_campaign_xar_off_contract",
                },
            }
            prepared_driver = {
                "episode_run_id": runner.EXPECTED_EPISODE_RUN_ID,
                "episode_character_id": 29829,
                "last_checkpoint": {
                    "episode_run_id": runner.EXPECTED_EPISODE_RUN_ID,
                    "episode_character_id": 29829,
                    "history_index": runner.EXPECTED_HISTORY_INDEX,
                    "sha256": runner.CHECKPOINT_SHA256,
                },
            }
            stack.enter_context(patch.object(runner, "RECEIVER_ASSETS_AND_SCOPE_VERIFIED", True))
            stack.enter_context(patch.object(runner, "validate_native_bridge_launch_config", return_value=config))
            stack.enter_context(patch.object(runner, "ensure_state_path_safe"))
            stack.enter_context(patch.object(runner, "validate_cold_start_checkpoint_for_pipe", return_value=checkpoint))
            stack.enter_context(patch.object(runner, "_read_driver_state", return_value=prepared_driver))
            stack.enter_context(patch.object(runner, "_read_rebind_receipt", return_value=_rebind_receipt(state_dir=spec.state_dir)))
            stack.enter_context(patch.object(runner, "_sha256", side_effect=_hash_for_path))
            stack.enter_context(patch.object(runner, "_wait_for_readiness", return_value={
                "snapshot_id": "native:3", "revision": 4, "native_revision": 3,
                "date_raw": runner.EXPECTED_DATE_RAW,
                "episode_run_id": runner.EXPECTED_EPISODE_RUN_ID,
                "paused": True, "map_ready": True, "connection_generation": 1,
            }))
            stack.enter_context(patch.object(runner, "_cleanup_report", return_value={"ok": True}))
            stack.enter_context(patch.object(runner, "_cold_restore_bookkeeping", return_value={"exact": True}))
            session = stack.enter_context(patch.object(runner, "native_session", return_value={"ok": True}))
            stack.enter_context(patch.object(runner, "NativeHeadlessGameplayDriver"))
            service = stack.enter_context(patch.object(runner, "GameplayBridgeService"))
            service.return_value.snapshot.return_value = {
                "revision": 4, "paused": True, "map_ready": True,
            }
            report = runner.query_h3937_stationary_route_contact_once(
                spec, timeout_seconds=390, readiness_timeout_seconds=300,
                ownership_round_id="R999", cold_start_checkpoint=True,
                native_bridge=config,
            )
            session.assert_called_once()
            service.return_value.execute_step.assert_not_called()
            self.assertFalse(report["ok"])
            self.assertFalse(report["action_authorized"])

    def test_inherited_h3928_scope_cannot_be_assumed_from_h3937_report(self) -> None:
        report_only = {
            "paused": True, "map_ready": True,
            "date_raw": runner.EXPECTED_DATE_RAW,
            "episode_run_id": runner.EXPECTED_EPISODE_RUN_ID,
            "played_character": {"character_id": 29829},
            "episode_character_id": 29829,
            "route_contact_horizon_supported": True,
            "player_armies": [{"army_id": runner.ARMY_ID, "controllable": True}],
            "active_wars": [{"war_id": 16777231}],
        }
        self.assertFalse(runner._exact_h3937_paused_subject(report_only))

    def test_same_frame_metadata_does_not_hide_subject_change(self) -> None:
        before = {
            "played_character": {"character_id": 29829},
            "episode_character_id": 29829,
            "active_wars": [{"war_id": 16777231, "enemy_armies": [
                {"army_id": 50331920, "current_province_id": 2629},
            ]}],
            "player_armies": [{"army_id": runner.ARMY_ID, "current_province_id": 2610}],
            "active_event": None,
            "pending_character_interaction": None,
            "route_contact_horizon_supported": True,
        }
        after = copy.deepcopy(before)
        self.assertTrue(runner._guarded_subject_unchanged(before, after))
        after["active_wars"][0]["enemy_armies"][0]["current_province_id"] = 2610
        self.assertFalse(runner._guarded_subject_unchanged(before, after))


class H3937OperatorGateTests(unittest.TestCase):
    def test_exact_h3937_readonly_check_set_is_accepted(self) -> None:
        checks = {key: True for key in operator.H3937_REQUIRED_CHECKS}
        self.assertIn("guarded_subject_unchanged", checks)
        self.assertTrue(operator.h3937_required_checks_green(checks))

    def test_h3937_check_set_rejects_missing_false_and_extra_fields(self) -> None:
        complete = {key: True for key in operator.H3937_REQUIRED_CHECKS}
        for malformed in (
            {key: value for key, value in complete.items() if key != "guarded_subject_unchanged"},
            {**complete, "guarded_subject_unchanged": False},
            {**complete, "unreviewed_extra": True},
        ):
            with self.subTest(keys=sorted(malformed)):
                self.assertFalse(operator.h3937_required_checks_green(malformed))

    def test_operator_full_report_check_set_positive_and_negative(self) -> None:
        for outcome in ("complete", "missing_guarded", "false_guarded"):
            with self.subTest(outcome=outcome), TemporaryDirectory() as root, ExitStack() as stack:
                root_path = Path(root)
                save = root_path / "profile" / "save games" / "xar_checkpoint.ck3"
                driver = root_path / "native-session" / "driver-state.json"
                child = root_path / "player-child-matrilineal-formal-v1.json"
                dll = root_path / "xar_ck3_bridge.dll"
                injector = root_path / "xar_ck3_bridge_injector.exe"
                for path in (save, driver, child, dll, injector):
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(b"synthetic no-launch fixture")
                args = SimpleNamespace(
                    manifest=root_path / "manifest.json",
                    output=root_path / "attempt",
                    ownership_round_id="R999", timeout=390, readiness_timeout=300,
                )
                manifest = {
                    "state_dir": root, "pipe": "test",
                    "dll": str(dll), "injector": str(injector),
                    "dll_sha256": runner.DLL_SHA256,
                    "injector_sha256": runner.INJECTOR_SHA256,
                    "checkpoint_sha256": runner.CHECKPOINT_SHA256,
                    "raw_source_driver_sha256": runner.RAW_SOURCE_DRIVER_SHA256,
                    "driver_state_sha256": PREPARED_SHA256,
                    "checkpoint_history_index": runner.EXPECTED_HISTORY_INDEX,
                    "date_raw": runner.EXPECTED_DATE_RAW,
                    "environment_sha256": ENVIRONMENT_SHA256,
                }
                checks = {key: True for key in operator.H3937_REQUIRED_CHECKS}
                if outcome == "missing_guarded":
                    del checks["guarded_subject_unchanged"]
                elif outcome == "false_guarded":
                    checks["guarded_subject_unchanged"] = False
                report = {
                    "ok": True, "status": "GREEN_READ_ONLY",
                    "action_authorized": False, "round": "R999",
                    "checks": checks, "cleanup": {"ok": True},
                }
                stack.enter_context(patch.object(operator, "H3937_RECEIVER_ASSETS_AND_SCOPE_VERIFIED", True))
                stack.enter_context(patch.object(operator, "load_manifest", return_value=manifest))
                stack.enter_context(patch.object(operator, "frozen_source_identity", return_value={}))
                stack.enter_context(patch.object(operator, "current_checkpoint_identity", return_value=(
                    save, driver, {"episode_character_id": 29829,
                                   "episode_run_id": runner.EXPECTED_EPISODE_RUN_ID},
                )))
                stack.enter_context(patch.object(operator, "sha256", side_effect=_hash_for_path))
                stack.enter_context(patch.object(operator, "agent_command", return_value=["agent"]))
                stack.enter_context(patch.object(operator, "lifecycle_contract", return_value={}))
                stack.enter_context(patch.object(operator, "preflight_lifecycle_arguments", return_value=[]))
                stack.enter_context(patch("builtins.print"))

                def read_json(path: Path) -> dict[str, object]:
                    return report if path.name == "query-report.json" else _rebind_receipt(state_dir=root_path)

                def run_logged(argv: list[str], stdout: Path, stderr: Path) -> int:
                    if "native-query-h3937-stationary-route-contact-v1" in argv:
                        stdout.write_text(json.dumps(report), encoding="utf-8")
                    return 0

                stack.enter_context(patch.object(operator, "read_json", side_effect=read_json))
                run_mock = stack.enter_context(patch.object(operator, "run_logged", side_effect=run_logged))
                exit_code = operator.command_query_h3937_stationary_route_contact_v1(args)
                self.assertEqual(exit_code, 0 if outcome == "complete" else 1)
                self.assertEqual(run_mock.call_count, 2)
                stored = json.loads((args.output / "operator-receipt.json").read_text())
                self.assertEqual(stored["ok"], outcome == "complete")

    def test_metadata_candidate_refuses_before_manifest_or_output(self) -> None:
        with TemporaryDirectory() as root, patch.object(operator, "load_manifest") as load, patch.object(
            operator, "run_logged"
        ) as run_logged:
            args = SimpleNamespace(
                manifest=Path(root) / "manifest.json", output=Path(root) / "attempt",
                ownership_round_id="R999", timeout=390, readiness_timeout=300,
            )
            with self.assertRaisesRegex(RuntimeError, "no preflight or launch"):
                operator.command_query_h3937_stationary_route_contact_v1(args)
            load.assert_not_called()
            run_logged.assert_not_called()
            self.assertFalse(args.output.exists())

    def test_operator_rejects_each_pair_pin_before_output_or_preflight(self) -> None:
        for mismatch in (
            "save", "raw", "prepared", "dll", "injector", "child",
            "old_state_path", "old_driver_path", "old_environment",
        ):
            with self.subTest(mismatch=mismatch), TemporaryDirectory() as root, ExitStack() as stack:
                root_path = Path(root)
                args = SimpleNamespace(
                    manifest=root_path / "manifest.json", output=root_path / "attempt",
                    ownership_round_id="R999", timeout=390, readiness_timeout=300,
                )
                manifest = {
                    "state_dir": root, "pipe": "test",
                    "dll": str(root_path / "xar_ck3_bridge.dll"),
                    "injector": str(root_path / "xar_ck3_bridge_injector.exe"),
                    "dll_sha256": runner.DLL_SHA256,
                    "injector_sha256": runner.INJECTOR_SHA256,
                    "checkpoint_sha256": runner.CHECKPOINT_SHA256,
                    "raw_source_driver_sha256": runner.RAW_SOURCE_DRIVER_SHA256,
                    "driver_state_sha256": PREPARED_SHA256,
                    "checkpoint_history_index": runner.EXPECTED_HISTORY_INDEX,
                    "date_raw": runner.EXPECTED_DATE_RAW,
                    "environment_sha256": ENVIRONMENT_SHA256,
                }
                receipt = _rebind_receipt(state_dir=root_path)
                if mismatch == "raw":
                    receipt["driver_state"]["source_sha256"] = "0" * 64
                elif mismatch == "prepared":
                    receipt["driver_state"]["target_sha256"] = "0" * 64
                elif mismatch == "old_state_path":
                    receipt["state_dir"] = str(root_path / "old-state")
                elif mismatch == "old_driver_path":
                    receipt["driver_state"]["path"] = str(root_path / "old-driver.json")
                elif mismatch == "old_environment":
                    receipt["environment"]["target_sha256"] = "0" * 64
                elif mismatch in {"dll", "injector"}:
                    manifest[f"{mismatch}_sha256"] = "0" * 64
                stack.enter_context(patch.object(operator, "H3937_RECEIVER_ASSETS_AND_SCOPE_VERIFIED", True))
                stack.enter_context(patch.object(operator, "load_manifest", return_value=manifest))
                stack.enter_context(patch.object(operator, "frozen_source_identity", return_value={}))
                stack.enter_context(patch.object(operator, "read_json", return_value=receipt))
                stack.enter_context(patch.object(
                    operator, "current_checkpoint_identity", return_value=(
                        root_path / "xar_checkpoint.ck3", root_path / "driver-state.json",
                        {"episode_character_id": 29829,
                         "episode_run_id": runner.EXPECTED_EPISODE_RUN_ID},
                    ),
                ))

                def wrong_hash(path: Path) -> str:
                    if mismatch == "save" and path.name == "xar_checkpoint.ck3":
                        return "0" * 64
                    if mismatch == "child" and path.name == "player-child-matrilineal-formal-v1.json":
                        return "0" * 64
                    return _hash_for_path(path)

                stack.enter_context(patch.object(operator, "sha256", side_effect=wrong_hash))
                run_logged = stack.enter_context(patch.object(operator, "run_logged"))
                with self.assertRaisesRegex(ValueError, "source identity differs"):
                    operator.command_query_h3937_stationary_route_contact_v1(args)
                run_logged.assert_not_called()
                self.assertFalse(args.output.exists())


if __name__ == "__main__":
    unittest.main()
