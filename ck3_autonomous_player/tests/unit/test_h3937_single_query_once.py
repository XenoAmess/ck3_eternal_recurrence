"""Offline checks for the real single-query dispatch and native result path."""
from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import threading
from contextlib import ExitStack, redirect_stdout
from unittest.mock import Mock, patch
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from xar_autoplayer import h3937_single_query_once_enable as entry
from xar_autoplayer import h3937_stationary_route_contact_query_run as query
from xar_autoplayer.bridge.native_driver import (
    NativeHeadlessGameplayDriver, NativeProtocolState, _NativeCommandRejectedError,
    QUERY_ROUTE_CONTACT_HORIZON_CAPABILITY,
)
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.war_contract import query_route_contact_horizon_step
from xar_autoplayer.operator_mcp import load_operator_profile, OperatorService, HostIdentity


def snapshot():
    subject = {"army_id": query.ARMY_ID, "controllable": True,
               "current_province_id": 2610, "move_target_province_id": None,
               "route_province_ids": [], "retreating": False, "in_combat": False,
               "army_state": "regular", "army_state_code": 0}
    return {"snapshot_id": "fixture-frame", "revision": 7, "native_revision": 11,
            "date_raw": query.EXPECTED_DATE_RAW, "paused": True, "map_ready": True,
            "episode_run_id": query.EXPECTED_EPISODE_RUN_ID,
            "played_character": {"character_id": 29829}, "episode_character_id": 29829,
            "active_wars": [{"war_id": 16777231, "enemy_armies": [
                {"army_id": 71, "current_province_id": 2629, "retreating": False},
                {"army_id": 81, "current_province_id": 2630, "retreating": True},
                {"army_id": 61, "current_province_id": 2628, "retreating": False},
            ]}], "player_armies": [subject], "active_event": None,
            "pending_character_interaction": None, "route_contact_horizon_supported": True,
            "diagnostics": {"connection_generation": 3}, "native_command_history": []}


def route_result(frame):
    hostiles = query._route_contact_hostile_ids(frame)
    step = query_route_contact_horizon_step(query.ARMY_ID, 2610, hostiles)
    def route(army_id, province):
        return {"timeline_observable": True, "army_id": army_id,
                "current_province_id": province, "effective_origin_province_id": province,
                "route_province_ids": [], "arrival_date_raws": []}
    horizon = {"status": "available", "date_raw": frame["date_raw"],
               "snapshot_revision": frame["native_revision"], "subject_army_id": query.ARMY_ID,
               "target_province_id": 2610, "hostile_army_ids": list(hostiles),
               "subject_route": route(query.ARMY_ID, 2610),
               "hostile_routes": [route(army_id, 2629) for army_id in hostiles],
               "horizon_start_date_raw": frame["date_raw"],
               "horizon_end_date_raw": frame["date_raw"] + 24,
               "one_day_contact_free": True, "conflicts": []}
    return {"step": step, "accepted": True, "status": "available", "query_sequence": 5,
            "snapshot_revision": frame["native_revision"], "route_contact_horizon": horizon,
            "backend_id": "native-headless", "physical_army_inventory": {"fixture_partial": True},
            "physical_army_inventory_diagnostics": {"rejected_slots": [{"slot": 2, "reason": "fixture"}]}}


class SingleQueryTests(unittest.TestCase):
    def test_negative_decoded_frame_sealed_before_reject_and_ascii_cli(self):
        frame = snapshot()
        step = route_result(frame)["step"]
        error = "application-main route-contact query timed out before execution"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "decoded-command-result.json"
            driver = NativeHeadlessGameplayDriver.__new__(NativeHeadlessGameplayDriver)
            driver.state = NativeProtocolState("fixture-not-a-pipe")
            driver.take_internal_semantic_snapshot = lambda: copy.deepcopy(frame)
            driver._request_sequence = 0
            driver.command_timeout_seconds = 1
            driver.route_contact_raw_result_observer = Mock()
            driver.route_contact_command_result_observer = lambda payload: query._seal_decoded_command_result(path, payload)
            sent, received = [], []
            def send(request):
                sent.append(copy.deepcopy(request))
                response = {"type": "command_result", "protocol_version": 1,
                            "request_id": request["request_id"], "ok": False, "error": error,
                            "result": {"physical_army_inventory_diagnostics": {"fixture_only": "拒绝\ufffd"}},
                            "extra_native_field": {"preserve": [1, 2]}}
                received.append(copy.deepcopy(response))
                driver.state.ingest(response)
            driver.endpoint = Mock()
            driver.endpoint.send.side_effect = send
            with patch.object(driver.state, "capabilities", return_value={"bridge_capabilities": [QUERY_ROUTE_CONTACT_HORIZON_CAPABILITY]}):
                with self.assertRaises(_NativeCommandRejectedError) as caught:
                    driver._execute_primitive_step(step, expected_revision=7,
                        required_capability=QUERY_ROUTE_CONTACT_HORIZON_CAPABILITY,
                        internal_semantic_snapshot=True)
            self.assertEqual(caught.exception.native_error, error)
            raw = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(raw, {"request": sent[0], "command_result": received[0]})
            self.assertEqual(sent[0]["expected_revision"], frame["native_revision"])
            self.assertEqual(len(sent), 1)
            self.assertIsNone(driver.state.wait_for_command_result(sent[0]["request_id"], 0))
            driver.route_contact_raw_result_observer.assert_not_called()
            with self.assertRaises(FileExistsError):
                query._seal_decoded_command_result(path, raw)
            unrelated = Mock()
            driver.route_contact_command_result_observer = unrelated
            with patch.object(driver.state, "capabilities", return_value={"bridge_capabilities": ["fixture.other-read"]}):
                with self.assertRaises(_NativeCommandRejectedError):
                    driver._execute_primitive_step("fixture-read", expected_revision=7,
                        required_capability="fixture.other-read", internal_semantic_snapshot=True)
            unrelated.assert_not_called()
            payload = {"ok": False, "status": "RED", "error": error,
                       "original_terminal_text": "拒绝\ufffd", "decoded_command_result_path": str(path)}
            output_bytes = io.BytesIO()
            stdout = io.TextIOWrapper(output_bytes, encoding="cp936", errors="strict")
            with patch.object(entry, "_configure", return_value={}), \
                    patch.object(entry, "run_once", return_value=payload), redirect_stdout(stdout):
                rc = entry.main(["--config", "fixture.json", "--live"])
                stdout.flush()
            encoded = output_bytes.getvalue()
            self.assertEqual(rc, 1)
            encoded.decode("ascii")
            self.assertEqual(json.loads(encoded), payload)

    def test_real_report_inventory_red_and_post_query_failure_retain_raw(self):
        frame = snapshot()
        with tempfile.TemporaryDirectory() as directory:
            primitive = route_result(frame)
            changed = copy.deepcopy(frame)
            changed["native_revision"] += 1
            guarded = NativeHeadlessGameplayDriver.__new__(NativeHeadlessGameplayDriver)
            guarded.take_internal_semantic_snapshot = Mock(side_effect=[frame, changed])
            guarded._execute_primitive_step = Mock(return_value=primitive)
            raw_native_path = Path(directory) / "native-query-result.json"
            def preserve_primitive(result):
                with raw_native_path.open("x", encoding="utf-8") as stream:
                    json.dump({"query_result": result}, stream)
            guarded.route_contact_raw_result_observer = preserve_primitive
            with self.assertRaises(BridgeUnavailableError):
                guarded._execute_native_war_step(primitive["step"], expected_revision=7)
            self.assertEqual(json.loads(raw_native_path.read_text())["query_result"], primitive)
            self.assertEqual(len(primitive), 9)
        native = NativeHeadlessGameplayDriver.__new__(NativeHeadlessGameplayDriver)
        native.take_internal_semantic_snapshot = lambda: copy.deepcopy(frame)
        native._execute_primitive_step = Mock(return_value=route_result(frame))
        envelope = native._execute_native_war_step(route_result(frame)["step"], expected_revision=7)
        after = copy.deepcopy(frame)
        after["native_command_history"].append({"command": envelope["step"], "ok": True, "result": envelope})
        lifecycle = {"environment_sha256": "E" * 64, "xar_enabled": "xar_off",
                     "lifecycle": "ordinary_campaign_succession",
                     "pact_contract": "absent_by_fresh_campaign_xar_off_contract"}
        checkpoint = {"saved_date_raw": query.EXPECTED_DATE_RAW, "history_index": 3937,
                      "succession_lifecycle": lifecycle}
        before_driver = {"episode_run_id": query.EXPECTED_EPISODE_RUN_ID, "episode_character_id": 29829,
                         "last_checkpoint": {"episode_run_id": query.EXPECTED_EPISODE_RUN_ID,
                                             "episode_character_id": 29829, "history_index": 3937,
                                             "sha256": query.CHECKPOINT_SHA256}}
        for failure in (None, "snapshot", "source_hash"):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
                root = Path(directory)
                keeper = Mock()
                keeper.abort = threading.Event()
                keeper.report.return_value = {"failure": None}
                service = Mock()
                service.snapshot.side_effect = [frame, RuntimeError("post-query snapshot fixture") if failure == "snapshot" else after]
                service.execute_step.return_value = envelope
                def file_sha(path):
                    if path.name == "ordinary-seed-rebind-v1.json" and failure == "source_hash":
                        raise OSError("post-query source hash fixture")
                    return {"xar_checkpoint.ck3": query.CHECKPOINT_SHA256,
                            "player-child-matrilineal-formal-v1.json": query.CHILD_PENDING_SIDECAR_SHA256,
                            "fixture.dll": "C" * 64, "fixture.exe": "D" * 64}.get(path.name, "F" * 64)
                for obj, name, value in (
                    (entry, "preflight", Mock(return_value={"admission_sha256": "A" * 64})),
                    (entry, "screen_keeper_for_runner", Mock(return_value=keeper)),
                    (entry.cold, "_require_go", Mock(return_value=({}, "B" * 64))),
                    (entry.cold, "_require_bus_cli_pair", Mock()),
                    (entry.cold, "_require_zero_live_inventory", Mock()),
                    (entry.cold, "_require_pipe_server_absent", Mock()),
                    (entry.cold, "_require_live_screen_lease", Mock(return_value={"last_sequence": 9})),
                    (entry.cold, "_image_inventory", Mock(return_value={"returncode": 0, "found": False})),
                    (entry.cold, "_sha", Mock(return_value="B" * 64)),
                    (entry.cold, "STATE", root / "state"), (entry.cold, "GAME", root / "game"),
                    (entry.cold, "DLL", root / "fixture.dll"), (entry.cold, "INJECTOR", root / "fixture.exe"),
                    (entry.cold, "OUTPUT", root / "new-attempt"), (entry.cold, "ROUND", "R900001"),
                    (entry.cold, "RUN_CONFIG_BYTES", b"fixture"),
                    (query, "validate_native_bridge_launch_config", lambda config: config),
                    (query, "ensure_state_path_safe", Mock()),
                    (query, "validate_cold_start_checkpoint_for_pipe", Mock(return_value=checkpoint)),
                    (query, "_read_driver_state", Mock(side_effect=[before_driver, {"command_history": after["native_command_history"]}])),
                    (query, "_read_rebind_receipt", Mock(return_value={})),
                    (query, "_exact_prepared_rebind", Mock(return_value=True)),
                    (query, "_bind_exact_h3937_ordinary_lifecycle", Mock(return_value=lifecycle)),
                    (query, "_cold_restore_bookkeeping", Mock(return_value={"exact": True})),
                    (query, "_sha256", file_sha),
                    (query, "NativeHeadlessGameplayDriver", Mock()),
                    (query, "GameplayBridgeService", Mock(return_value=service)),
                    (query, "native_session", Mock(return_value={})),
                    (query, "_wait_for_readiness", Mock(return_value=frame)),
                    (query, "_cleanup_report", Mock(return_value={"ok": True})),
                ):
                    stack.enter_context(patch.object(obj, name, value))
                result = entry.run_once({"bridge_dll_sha256": "C" * 64, "bridge_injector_sha256": "D" * 64})
                self.assertFalse(result["ok"])
                self.assertEqual(result["status"], "RED")
                self.assertEqual(result["six_read_contracts_completed"], 0)
                self.assertFalse(result["action_authorized"])
                raw = json.loads(Path(result["raw_query_envelope_path"]).read_text())
                self.assertEqual(raw["query_result"], envelope)
                self.assertEqual(raw["query_result"]["physical_army_inventory_diagnostics"], envelope["physical_army_inventory_diagnostics"])
                service.execute_step.assert_called_once()
                if failure is None:
                    report = json.loads(Path(result["report_path"]).read_text())
                    self.assertFalse(report["checks"]["physical_army_inventory_valid"])
                    self.assertTrue(all(value for key, value in report["checks"].items() if key != "physical_army_inventory_valid"))
                    self.assertEqual(report["status"], "RED")
                if failure == "source_hash":
                    self.assertIsNone(result["report_path"])
                    self.assertIn("source hash fixture", result["error"])

    def test_default_cli_is_no_launch_and_only_explicit_live_dispatches(self):
        with patch.object(entry, "_configure", return_value={}), \
                patch.object(entry, "preflight", return_value={"ok": True}) as preflight, \
                patch.object(entry, "run_once", return_value={"ok": True}) as live, \
                redirect_stdout(io.StringIO()):
            self.assertEqual(entry.main(["--config", "fixture.json"]), 0)
            preflight.assert_called_once()
            live.assert_not_called()
            self.assertEqual(entry.main(["--config", "fixture.json", "--live"]), 0)
            live.assert_called_once()

    def test_default_private_query_gate_stays_closed_before_launch(self):
        with patch.object(query, "native_session") as launch:
            with self.assertRaises(query.AgentError):
                query.query_h3937_stationary_route_contact_once(
                    None, timeout_seconds=1, readiness_timeout_seconds=1,
                    ownership_round_id="R900001", cold_start_checkpoint=True)
            launch.assert_not_called()

    def test_fresh_membership_replaces_historical_ids_and_keeps_frame_guards(self):
        frame = snapshot()
        self.assertFalse(query._exact_h3937_paused_subject(frame))
        self.assertTrue(query._exact_h3937_paused_subject(frame, require_historical_hostiles=False))
        self.assertEqual(query._route_contact_hostile_ids(frame), (61, 71))
        wire = query_route_contact_horizon_step(query.ARMY_ID, 2610, query._route_contact_hostile_ids(frame))
        self.assertEqual(wire, "query-route-contact-horizon-v1-83886367-to-2610-h-2-61-71")
        changed = copy.deepcopy(frame)
        changed["date_raw"] += 24
        self.assertFalse(query._same_frame(frame, changed))
        changed = copy.deepcopy(frame)
        changed["player_armies"][0]["current_province_id"] = 2611
        self.assertFalse(query._guarded_subject_unchanged(frame, changed))

    def test_real_driver_preserves_sibling_and_keeps_inventory_red(self):
        frame = snapshot()
        raw = route_result(frame)
        driver = NativeHeadlessGameplayDriver.__new__(NativeHeadlessGameplayDriver)
        driver.take_internal_semantic_snapshot = lambda: copy.deepcopy(frame)
        driver._execute_primitive_step = Mock(return_value=raw)
        result = driver._execute_native_war_step(raw["step"], expected_revision=frame["revision"])
        self.assertEqual(result["physical_army_inventory_diagnostics"], raw["physical_army_inventory_diagnostics"])
        self.assertEqual(result["physical_army_inventory"], raw["physical_army_inventory"])
        self.assertFalse(result["physical_army_inventory_check"]["valid"])
        self.assertFalse(result["physical_army_inventory_check"]["date_or_action_authorized"])
        self.assertTrue(query._bound_route_result(frame, result, query_step=raw["step"], hostile_army_ids=(61, 71)))
        after = copy.deepcopy(frame)
        after["native_command_history"].append({"command": raw["step"], "ok": True, "result": result})
        self.assertTrue(query._exact_one_appended_query(frame, after, result, query_step=raw["step"]))
        after["native_command_history"].append(copy.deepcopy(after["native_command_history"][-1]))
        self.assertFalse(query._exact_one_appended_query(frame, after, result, query_step=raw["step"]))
        driver._execute_primitive_step.return_value = {**raw, "unexpected_fixture_field": True}
        with self.assertRaises(BridgeUnavailableError):
            driver._execute_native_war_step(raw["step"], expected_revision=frame["revision"])

    def test_live_wrapper_passes_real_keeper_abort_and_process_gate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            abort = threading.Event()
            keeper = Mock()
            keeper.abort = abort
            keeper.report.return_value = {"failure": None, "thread_exited": True}
            cold = entry.cold
            with patch.object(entry, "preflight", return_value={"head": "fixture", "admission_sha256": "A" * 64}), \
                    patch.object(cold, "_require_go", return_value=({}, "B" * 64)), \
                    patch.object(cold, "_require_bus_cli_pair"), \
                    patch.object(cold, "_require_zero_live_inventory"), \
                    patch.object(cold, "_require_pipe_server_absent"), \
                    patch.object(cold, "_require_live_screen_lease", return_value={"last_sequence": 9}), \
                    patch.object(cold, "_image_inventory", return_value={"returncode": 0, "found": False}), \
                    patch.object(cold, "_sha", return_value="B" * 64), \
                    patch.object(cold, "OUTPUT", root / "new-attempt"), \
                    patch.object(cold, "RUN_CONFIG_BYTES", b"fixture"), \
                    patch.object(entry, "screen_keeper_for_runner", return_value=keeper), \
                    patch.object(query, "query_h3937_stationary_route_contact_once", return_value={"ok": True}) as run:
                result = entry.run_once({"bridge_dll_sha256": "C" * 64, "bridge_injector_sha256": "D" * 64})
            self.assertTrue(result["ok"])
            self.assertIs(run.call_args.kwargs["managed_stop_event"], abort)
            self.assertIs(run.call_args.kwargs["before_process_create"], keeper.process_create_gate)
            self.assertEqual(result["six_read_contracts_completed"], 0)
            self.assertFalse(result["action_authorized"])
            self.assertTrue((root / "new-attempt/query-report.json").is_file())

    def test_existing_operator_accepts_single_frozen_live_job_without_server(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            no_launch = root / "no-launch"
            no_launch.mkdir()
            for name in ("admission.json", "operator-manifest.json", "preparation.json"):
                (no_launch / name).write_text("fixture-only", encoding="utf-8")
            config_path = root / "config.json"
            config_path.write_text("fixture-only", encoding="utf-8")
            dll, injector, build = (root / name for name in ("fixture.dll", "fixture.exe", "build.json"))
            for path in (dll, injector, build):
                path.write_bytes(b"fixture-only")
            with patch.object(entry, "preflight", return_value={"ok": True}), \
                    patch.object(entry.cold, "NO_LAUNCH", no_launch), \
                    patch.object(entry.cold, "RUN_CONFIG_PATH", config_path), \
                    patch.object(entry.cold, "DLL", dll), \
                    patch.object(entry.cold, "INJECTOR", injector), \
                    patch.object(entry.cold, "STATE", no_launch / "state"), \
                    patch.object(entry.cold, "OUTPUT", root / "never-created"), \
                    patch.object(entry.cold, "ROUND", "R900001"):
                profile_path = root / "profile.json"
                entry.freeze_profile({"native_build_receipt": str(build)}, profile_path, root / "operator")
            profile = load_operator_profile(profile_path)
            self.assertEqual(set(profile.jobs), {entry.JOB})
            self.assertEqual(profile.jobs[entry.JOB].command[-1], "--live")
            inspector = Mock()
            inspector.pids.return_value = []
            service = OperatorService(profile, process_inspector=inspector,
                                      identity_probe=lambda: HostIdentity("1", "WinSta0\\Default", "DESKTOP-3FEVHD2", 1),
                                      popen_factory=lambda *a, **kw: self.fail("fixture started a worker"))
            result = service.preflight_job(profile.target_id, entry.JOB)
            self.assertEqual(result["result"], "GREEN")
            self.assertFalse((root / "never-created").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
