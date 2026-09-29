"""Static managed-session checks for the disabled H3937 combined candidate."""

from __future__ import annotations

import copy
from contextlib import ExitStack
import hashlib
import inspect
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import xar_autoplayer.h3937_combined_paused_war_scope_run as producer
import xar_autoplayer.h3937_combined_once_enable as once
from xar_autoplayer.bridge.succession_transition_contract import (
    ORDINARY_CAMPAIGN_SUCCESSION,
    bind_succession_lifecycle_from_environment_v1,
)


class H3937CombinedOuterTests(unittest.TestCase):
    def test_timeout_screenshot_requires_live_lease_check_before_session(self) -> None:
        spec = SimpleNamespace(state_dir=Path("missing"), profile_dir=Path("missing"))
        with patch.object(producer, "H3937_COMBINED_OUTER_LIVE_AUTHORIZED", True), patch.object(
            producer, "native_session") as session:
            with self.assertRaisesRegex(producer.AgentError, "current screen lease check"):
                producer.collect_h3937_combined_paused_war_scope_once(
                    spec, ownership_round_id="R999", cold_start_checkpoint=True,
                    readiness_timeout_screenshot_path=Path("unused.png"))
            session.assert_not_called()

    def test_timeout_desktop_capture_is_bounded_and_never_overwrites(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            image = Path(temp_dir) / "readiness.png"
            with patch.object(producer.subprocess, "run", side_effect=subprocess.TimeoutExpired(
                cmd=["python"], timeout=20)) as capture:
                result = producer._capture_timeout_desktop(image)
            self.assertEqual(result["status"], "RED_CAPTURE_FAILED")
            self.assertFalse(result["desktop_interaction"])
            capture.assert_called_once()
            self.assertEqual(capture.call_args.kwargs["timeout"], 20)
            self.assertEqual(capture.call_args.args[0][1], "-c")
            image.write_bytes(b"historical-original")
            with patch.object(producer.subprocess, "run") as capture:
                refused = producer._capture_timeout_desktop(image)
            self.assertEqual(refused["status"], "RED_CAPTURE_PATH")
            capture.assert_not_called()
            self.assertEqual(image.read_bytes(), b"historical-original")

    def test_a05_time_budgets_remain_bounded_and_ordered(self) -> None:
        parameters = inspect.signature(
            producer.collect_h3937_combined_paused_war_scope_once).parameters
        self.assertEqual(parameters["readiness_timeout_seconds"].default, 600)
        self.assertEqual(parameters["timeout_seconds"].default, 690)
        self.assertEqual(once.SUPERVISOR_TIMEOUT_SECONDS, 840)
        self.assertLess(600, 690)
        self.assertLess(690, once.SUPERVISOR_TIMEOUT_SECONDS)

    def test_dirty_checkout_or_module_blob_drift_refuses_before_launch(self) -> None:
        source = Path(producer.__file__)
        with patch.object(producer, "_checkout_commit", return_value="a" * 40), patch.object(
            producer.subprocess, "run", return_value=subprocess.CompletedProcess(
                args=[], returncode=0, stdout=" M source.py\n")):
            with self.assertRaisesRegex(producer.AgentError, "checkout is dirty"):
                producer._clean_checkout_and_blob_identity({"producer_module": source})
        responses = [
            subprocess.CompletedProcess(args=[], returncode=0, stdout=""),
            subprocess.CompletedProcess(args=[], returncode=0, stdout="a" * 40),
            subprocess.CompletedProcess(args=[], returncode=0, stdout="b" * 40),
        ]
        with patch.object(producer, "_checkout_commit", return_value="a" * 40), patch.object(
            producer.subprocess, "run", side_effect=responses):
            with self.assertRaisesRegex(producer.AgentError, "differs from HEAD"):
                producer._clean_checkout_and_blob_identity({"producer_module": source})

    def test_hard_gate_refuses_before_environment_or_session(self) -> None:
        spec = SimpleNamespace(state_dir=Path("missing"), profile_dir=Path("missing"))
        with patch.object(producer, "native_bridge_launch_config_from_environment") as env, patch.object(
            producer, "native_session"
        ) as session:
            with self.assertRaisesRegex(producer.AgentError, "no live authorization"):
                producer.collect_h3937_combined_paused_war_scope_once(
                    spec, ownership_round_id="R999", cold_start_checkpoint=True)
        env.assert_not_called()
        session.assert_not_called()

    def test_missing_binary_pins_refuses_before_state_or_session(self) -> None:
        spec = SimpleNamespace(state_dir=Path("missing"), profile_dir=Path("missing"))
        config = SimpleNamespace(mode="native-headless")
        with ExitStack() as stack:
            stack.enter_context(patch.object(producer, "H3937_COMBINED_OUTER_LIVE_AUTHORIZED", True))
            stack.enter_context(patch.object(producer, "COMBINED_DLL_SHA256", None))
            stack.enter_context(patch.object(producer, "COMBINED_INJECTOR_SHA256", None))
            stack.enter_context(patch.object(
                producer, "validate_native_bridge_launch_config", return_value=config))
            safe = stack.enter_context(patch.object(producer, "ensure_state_path_safe"))
            session = stack.enter_context(patch.object(producer, "native_session"))
            with self.assertRaisesRegex(producer.AgentError, "binary pins unavailable"):
                producer.collect_h3937_combined_paused_war_scope_once(
                    spec, ownership_round_id="R999", cold_start_checkpoint=True,
                    native_bridge=config)
            safe.assert_not_called()
            session.assert_not_called()

    def test_managed_two_query_history_assets_cleanup_and_lifecycle(self) -> None:
        for outcome in ("green", "inner_red", "inner_contract_red", "history_red", "cleanup_red",
                        "asset_red", "checkout_red", "binary_red",
                        "readiness_timeout", "readiness_timeout_capture_exception",
                        "readiness_timeout_lease_red",
                        "readiness_error"):
            with (self.subTest(outcome=outcome),
                  tempfile.TemporaryDirectory() as temp_dir,
                  ExitStack() as stack):
                spec = SimpleNamespace(
                    state_dir=Path("D:/synthetic-h3937-combined/state"),
                    profile_dir=Path("D:/synthetic-h3937-combined/state/profile"),
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
                    dll_path=Path("D:/synthetic-h3937-combined/xar_ck3_bridge.dll"),
                    injector_path=Path("D:/synthetic-h3937-combined/xar_ck3_bridge_injector.exe"),
                )
                checkpoint = {
                    "saved_date_raw": producer.EXPECTED_DATE_RAW,
                    "history_index": producer.EXPECTED_HISTORY_INDEX,
                    "succession_lifecycle": lifecycle,
                }
                history = [{"command": "restore-checkpoint", "ok": True}]
                steps = ["query-province-local-siege province=2610",
                         "query-route-contact-horizon own=83886367"]
                envelopes = [{"accepted": True, "query": 1},
                             {"accepted": True, "query": 2}]
                appended = [
                    {"command": step, "ok": True, "result": envelope}
                    for step, envelope in zip(steps, envelopes)
                ]
                before_driver = {
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
                after_driver = copy.deepcopy(before_driver)
                after_driver["command_history"] = (
                    history if outcome in {"readiness_timeout", "readiness_timeout_capture_exception",
                                           "readiness_timeout_lease_red",
                                           "readiness_error"}
                    else history + appended)
                if outcome == "history_red":
                    after_driver["command_history"][-1]["command"] = "different"
                first = {
                    "snapshot_id": "native:4", "revision": 5,
                    "native_revision": 4, "date_raw": producer.EXPECTED_DATE_RAW,
                    "episode_run_id": producer.EXPECTED_EPISODE_RUN_ID,
                    "episode_character_id": 29829, "paused": True,
                    "map_ready": True, "connection_generation": 1,
                    "native_command_history": history,
                }
                middle = copy.deepcopy(first)
                middle["native_command_history"] = history + appended[:1]
                last = copy.deepcopy(first)
                last["native_command_history"] = history + appended
                readiness = {key: first[key] for key in (
                    "snapshot_id", "revision", "native_revision", "date_raw",
                    "episode_run_id", "paused", "map_ready", "connection_generation")}
                inner = {
                    "schema": "xar.ck3.h3937-combined-readonly-inner-v1",
                    "observed": outcome != "inner_red",
                    "action_authorized": False, "date_advance_authorized": False,
                    "gameplay_actions": 0,
                    "physical_army_inventory_completeness_proven": False,
                    "outer_session_cleanup_verified": False,
                    "query_attempts": 2, "steps": steps, "envelopes": envelopes,
                    "frames": [first, middle, last], "scope": {"war_id": 16777231},
                }
                if outcome == "inner_contract_red":
                    inner["action_authorized"] = True
                receipt_reads = 0
                checkout_reads = 0

                def fake_hash(path: Path) -> str:
                    nonlocal receipt_reads
                    if outcome == "binary_red" and path.name == "xar_ck3_bridge.dll":
                        return "0" * 64
                    if path.name == "ordinary-seed-rebind-v1.json":
                        receipt_reads += 1
                        if outcome == "asset_red" and receipt_reads > 1:
                            return "e" * 64
                    known = {
                        "xar_checkpoint.ck3": producer.CHECKPOINT_SHA256,
                        "driver-state.json": "B" * 64,
                        "player-child-matrilineal-formal-v1.json":
                            producer.CHILD_PENDING_SIDECAR_SHA256,
                        "xar_ck3_bridge.dll": "1" * 64,
                        "xar_ck3_bridge_injector.exe": "2" * 64,
                        "ordinary-seed-rebind-v1.json": "c" * 64,
                        "h3937_combined_paused_war_scope_run.py": "D" * 64,
                        "h3937_combined_readonly_queries.py": "E" * 64,
                        "h3937_paused_war_scope_run.py": "F" * 64,
                    }
                    return known.get(path.name, hashlib.sha256(
                        path.name.encode("utf-8")).hexdigest())

                def fake_checkout() -> str:
                    nonlocal checkout_reads
                    checkout_reads += 1
                    return ("F" if outcome == "checkout_red" and checkout_reads > 1
                            else "A") * 40

                stack.enter_context(patch.object(producer, "H3937_COMBINED_OUTER_LIVE_AUTHORIZED", True))
                stack.enter_context(patch.object(producer, "COMBINED_DLL_SHA256", "1" * 64))
                stack.enter_context(patch.object(producer, "COMBINED_INJECTOR_SHA256", "2" * 64))
                stack.enter_context(patch.object(
                    producer, "validate_native_bridge_launch_config", return_value=config))
                stack.enter_context(patch.object(producer, "ensure_state_path_safe"))
                stack.enter_context(patch.object(
                    producer, "validate_cold_start_checkpoint_for_pipe", return_value=checkpoint))
                stack.enter_context(patch.object(
                    producer, "_read_driver_state", side_effect=[before_driver, after_driver]))
                stack.enter_context(patch.object(
                    producer, "_read_rebind_receipt_and_sha",
                    return_value=({}, "c" * 64)))
                stack.enter_context(patch.object(
                    producer, "_exact_prepared_rebind", return_value=True))
                stack.enter_context(patch.object(producer, "_sha256", side_effect=fake_hash))
                stack.enter_context(patch.object(
                    producer, "_clean_checkout_and_blob_identity",
                    side_effect=lambda paths: (fake_checkout(), {
                        key: "a" * 40 for key in paths
                        if key == "producer_module" or key.startswith("source_module_")
                    })))
                readiness_failure = None
                if outcome in {"readiness_timeout", "readiness_timeout_capture_exception",
                               "readiness_timeout_lease_red"}:
                    readiness_failure = producer.NativeReadinessTimeoutError(
                        "synthetic no semantic state",
                        readiness_diagnostics={
                            "mode": "native-headless", "backend_id": "native-headless",
                            "transport_ready": True, "snapshot": False,
                            "full_hello": "forbidden-hello",
                            "diagnostics": {
                                "connected": True, "connection_generation": 3,
                                "bridge_pid": 55, "semantic_state_available": False,
                                "last_error": {"code": "loading", "message": "still loading",
                                               "raw_frame": "forbidden-frame"},
                                "hello": {"game_adapter_status": "bound",
                                          "capabilities": "forbidden-capabilities"},
                                "last_heartbeat": {"sequence": 7, "pid": 55,
                                    "main_thread_query_mailbox_v1": {
                                        "installed": True, "ready": False,
                                        "pump_epochs": 4, "raw_history": "forbidden-history"}},
                            },
                        },
                        last_observation={"snapshot_id": "native:4",
                                          "date_raw": producer.EXPECTED_DATE_RAW,
                                          "full_snapshot": "forbidden-snapshot"},
                    )
                elif outcome == "readiness_error":
                    readiness_failure = RuntimeError("synthetic ordinary failure")
                stack.enter_context(patch.object(
                    producer, "_wait_for_readiness", return_value=readiness,
                    side_effect=readiness_failure))
                stack.enter_context(patch.object(
                    producer, "_cleanup_report",
                    return_value={"ok": outcome != "cleanup_red"}))
                screenshot = stack.enter_context(patch.object(
                    producer, "_capture_timeout_desktop",
                    return_value={"status": "CAPTURED_UNREVIEWED", "sha256": "d" * 64},
                    side_effect=(OSError("capture broke")
                                 if outcome == "readiness_timeout_capture_exception"
                                 else None)))
                lease_check = Mock(
                    return_value={"task_id": "synthetic"},
                    side_effect=(ValueError("stale screen lease")
                                 if outcome == "readiness_timeout_lease_red" else None))
                stack.enter_context(patch.object(
                    producer, "_cold_restore_bookkeeping", return_value={"exact": True}))
                stack.enter_context(patch.object(
                    producer, "_bind_exact_h3937_ordinary_lifecycle", return_value=lifecycle))
                session = stack.enter_context(patch.object(
                    producer, "native_session", return_value={"ok": True}))
                native_driver = stack.enter_context(patch.object(
                    producer, "NativeHeadlessGameplayDriver"))
                stack.enter_context(patch.object(producer, "GameplayBridgeService"))
                collector = stack.enter_context(patch.object(
                    producer, "collect_h3937_combined_reads_in_session", return_value=inner))
                if outcome == "binary_red":
                    with self.assertRaisesRegex(producer.AgentError, "launch refused"):
                        producer.collect_h3937_combined_paused_war_scope_once(
                            spec, ownership_round_id="R999", cold_start_checkpoint=True,
                            native_bridge=config)
                    session.assert_not_called()
                    collector.assert_not_called()
                    continue
                result = producer.collect_h3937_combined_paused_war_scope_once(
                    spec, ownership_round_id="R999", cold_start_checkpoint=True,
                    native_bridge=config,
                    readiness_timeout_screenshot_path=Path(temp_dir) / "timeout.png",
                    readiness_timeout_screen_lease_check=lease_check)
                session.assert_called_once()
                if outcome in {"readiness_timeout", "readiness_timeout_capture_exception",
                               "readiness_timeout_lease_red",
                               "readiness_error"}:
                    collector.assert_not_called()
                    self.assertEqual(result["query_actions"], 0)
                    self.assertFalse(result["checks"]["date_unchanged"])
                    self.assertTrue(result["cleanup"]["ok"])
                    if outcome in {"readiness_timeout", "readiness_timeout_capture_exception",
                                   "readiness_timeout_lease_red"}:
                        lease_check.assert_called_once_with()
                        if outcome == "readiness_timeout_lease_red":
                            screenshot.assert_not_called()
                        else:
                            screenshot.assert_called_once_with(Path(temp_dir) / "timeout.png")
                        self.assertEqual(
                            result["readiness_timeout_screenshot"]["status"],
                            "RED_CAPTURE_OR_SCREEN_LEASE" if outcome != "readiness_timeout"
                            else "CAPTURED_UNREVIEWED")
                        diagnostics = result["readiness_timeout_diagnostics"]
                        self.assertTrue(diagnostics["diagnostics"]["connected"])
                        self.assertFalse(diagnostics["diagnostics"]["semantic_state_available"])
                        self.assertEqual(diagnostics["diagnostics"]["last_heartbeat"]["sequence"], 7)
                        self.assertEqual(result["readiness_timeout_last_observation"]["date_raw"],
                                         producer.EXPECTED_DATE_RAW)
                        encoded = json.dumps(result)
                        for forbidden in ("forbidden-hello", "forbidden-frame",
                                          "forbidden-capabilities", "forbidden-history",
                                          "forbidden-snapshot"):
                            self.assertNotIn(forbidden, encoded)
                    else:
                        lease_check.assert_not_called()
                        screenshot.assert_not_called()
                        self.assertIsNone(result["readiness_timeout_diagnostics"])
                        self.assertIsNone(result["readiness_timeout_last_observation"])
                        self.assertIsNone(result["readiness_timeout_screenshot"])
                else:
                    lease_check.assert_not_called()
                    screenshot.assert_not_called()
                    collector.assert_called_once()
                native_driver.assert_called_once_with(
                    config.pipe_name, state_dir=spec.state_dir,
                    save_dir=spec.profile_dir / "save games",
                    succession_lifecycle_binding=lifecycle)
                self.assertEqual(result["ok"], outcome == "green")
                self.assertFalse(result["action_authorized"])
                self.assertFalse(result["date_advance_authorized"])
                self.assertFalse(result["physical_army_inventory_completeness_proven"])
                self.assertEqual(result["gameplay_actions"], 0)
                self.assertEqual(result["query_actions"],
                                 0 if outcome in {"readiness_timeout",
                                                 "readiness_timeout_capture_exception",
                                                  "readiness_timeout_lease_red",
                                                  "readiness_error"} else 2)
                self.assertEqual(result["source"]["rebind_receipt_sha256"], "c" * 64)


if __name__ == "__main__":
    unittest.main()
