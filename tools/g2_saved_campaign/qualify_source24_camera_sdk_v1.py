"""Three Source24 integration checks using private RAM modules and wire memory."""
from __future__ import annotations

import argparse
import ast
from contextlib import contextmanager
import copy
import ctypes as C
import io
import json
from pathlib import Path
import sys
import threading
import time
import types
import unittest

import prepare_source24_camera_sdk_v1 as source


@contextmanager
def private_modules(changed):
    """Isolated fixture package; never import or replace installed SDK modules."""
    prefix = "_source24_camera_fixture"
    assert not any(k == prefix or k.startswith(prefix + ".") for k in sys.modules)
    def load(name, payload):
        full = prefix + ".bridge." + name
        module = types.ModuleType(full)
        module.__package__ = prefix + ".bridge"
        module.__file__ = "<RAM Source24/" + name + ">"
        sys.modules[full] = module
        exec(compile(payload, module.__file__, "exec", dont_inherit=True), module.__dict__)
        return module
    for name in (prefix, prefix + ".bridge"):
        package = types.ModuleType(name)
        package.__path__ = []
        sys.modules[name] = package
    try:
        modules = {}
        for name in ("camera_tracking_v1", "realm_overview_camera", "auto_camera_follow"):
            modules[name] = load(name, changed[source.BRIDGE + name + ".py"])
        # The unchanged index/selector consumes fixture dictionaries only; its
        # installation file reader is never called.
        raw = source.prior.git_read("show", source.BASE_COMMIT + ":" + source.prior.PREFIX + source.BRIDGE + "war_hotspot_camera.py")
        modules["war_hotspot_camera"] = load("war_hotspot_camera", raw)
        driver = types.ModuleType(prefix + ".bridge.native_driver")
        driver.NativeHeadlessGameplayDriver = type("NativeHeadlessGameplayDriver", (), {})
        sys.modules[driver.__name__] = driver
        modules["native_driver"] = driver
        modules["auto_camera_pre_advance_v1"] = load("auto_camera_pre_advance_v1", changed[source.BRIDGE + "auto_camera_pre_advance_v1.py"])
        tree = ast.parse(changed[source.BRIDGE + "service.py"])
        original = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "GameplayBridgeService")
        wanted = {"_auto_camera_hotspot_input", "_camera_presentation_owner", "_sync_camera_presentation_owner",
                  "_camera_presentation_target_key", "_bound_camera_presentation_actual", "_select_auto_camera_hotspot",
                  "_publish_camera_presentation_v1"}
        methods = [copy.deepcopy(n) for n in original.body if isinstance(n, ast.FunctionDef) and n.name in wanted]
        assert len(methods) == len(wanted)
        cls = ast.ClassDef(name="GameplayBridgeService", bases=[], keywords=[], body=methods, decorator_list=[])
        subset = ast.fix_missing_locations(ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), cls], type_ignores=[]))
        service = load("service_camera_subset", b"")
        service.start_army_timing = lambda *a, **k: None
        service.finish_army_timing = lambda *a, **k: None
        exec(compile(subset, "<exact Source24 Service camera methods>", "exec"), service.__dict__)
        modules["service"] = service
        yield modules
    finally:
        for name in list(sys.modules):
            if name == prefix or name.startswith(prefix + "."):
                del sys.modules[name]


def memory_client(modules):
    realm, track = modules["realm_overview_camera"], modules["camera_tracking_v1"]
    memory = C.create_string_buffer(realm.MAPPING_BYTES)
    address = C.addressof(memory)
    header = realm._Shared.from_address(address)
    header.magic, header.version, header.pid = realm.MAGIC, 1, 77
    cap = track.Shared.from_address(address + track.OFFSET)
    cap.magic, cap.version, cap.byte_size, cap.provider_pid = track.MAGIC, track.VERSION, C.sizeof(track.Shared), 77
    cap.capability_sequence, cap.active, cap.owner_epoch = 2, 1, 99
    realm.desktop1_game_window = lambda pid, cached=None: 123
    client = realm.NativeCameraPresentationClient.__new__(realm.NativeCameraPresentationClient)
    client.pid, client._view, client._handle, client._hwnd = 77, address, None, None
    client._last_result_sequence, client._latest, client._tracking_binding = -1, None, None
    client._lock = threading.Lock()
    client._kernel = types.SimpleNamespace(GetTickCount64=lambda: 1000, FlushProcessWriteBuffers=lambda: None,
                                          UnmapViewOfFile=lambda view: None)
    client._open = lambda: None
    return client, memory, header, cap


def service_fixture(modules):
    client, memory, header, cap = memory_client(modules)
    service = modules["service"].GameplayBridgeService.__new__(modules["service"].GameplayBridgeService)
    index = modules["war_hotspot_camera"].LandedProvinceIndex(
        {1: "b_one", 2: "b_two", 3: "b_three"}, {1: "c_one", 2: "c_one", 3: "c_three"}, ())
    service.driver = modules["native_driver"].NativeHeadlessGameplayDriver()
    service._war_hotspot_camera_index, service._war_hotspot_camera_index_error = index, None
    service._camera_presentation_client = client
    service._camera_presentation_owner_key, service._camera_presentation_request_context = None, None
    service._peace_realm_camera_policy = modules["realm_overview_camera"].PeaceRealmCameraPolicy()
    frame = {"status": "complete", "snapshot_id": "fixture-current", "revision": 4, "native_revision": 5,
             "date_raw": 1000, "actor_character_id": 7, "episode_run_id": "fixture-only",
             "bridge_pid": 77, "connection_generation": 1}
    service._observed_planning_source_frame = lambda current: dict(frame)
    army = {"army_id": 10, "current_province_id": 1, "move_target_province_id": 3,
            "route_province_ids": [2], "controllable": True, "retreating": False,
            "in_combat": False, "army_state": "moving"}
    snapshot = {"paused": True, "played_character": {"alive": True}, "map_ready": True,
                "active_wars": [{"war_id": 1, "allied_armies": [army]}], "player_armies": [army],
                "diagnostics": {"hello": {"expected_ck3_version": "1.20.0.4",
                                           "expected_ck3_sha256": modules["realm_overview_camera"].EXACT_SHA}}}
    captured = []
    def schedule(payload, *, urgent=False):
        captured.append(payload)
        return service._select_auto_camera_hotspot(payload)
    service._auto_camera_worker = types.SimpleNamespace(schedule=schedule)
    return service, frame, snapshot, captured, client, memory, header, cap


class Source24CameraIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.changed, cls.rows, cls.report = source.compose(verify_all_base=True)

    def test_source23_inverse_and_every_other_inventory_row_preserve_all_recovery_and_custody(self):
        report = self.report
        self.assertEqual((report["output"]["files"], len(report["delta"])), (1457, 6))
        self.assertEqual(report["output"]["actual_Source22_changed_outputs"], 17)
        self.assertEqual(report["output"]["unchanged_Source23_rows"], 1451)
        self.assertTrue(all(x["entire_original_inverse"] for x in report["exact_inverse_hunks"]))
        self.assertTrue(report["unowned_function_ASTs_preserved"])
        self.assertEqual(set(report["changed_function_ASTs"][source.BRIDGE + "native_driver.py"]), source.ALLOWED["native_driver.py"])
        self.assertNotIn(source.BRIDGE + "mcp_server.py", self.changed)
        self.assertTrue(report["inherited_M7_WAL_fullinverse_and_commutativity_preserved"])
        self.assertNotEqual(report["source_epoch_detached_model"], "8176ef4e9a24f48dc9b3185f7316396e5be4f455425a2b03fc96b24c20c8f48e")
        for row in report["delta"]:
            if row["before"] is not None:
                self.assertEqual(row["before"]["git_mode"], row["after"]["git_mode"])
        self.assertEqual(sum(x["before"] is None for x in report["delta"]), 1)

    def test_arm_scope_crosses_pre_resume_service_route_projection_and_mode4_tail(self):
        with private_modules(self.changed) as modules:
            service, frame, snapshot, captured, client, memory, header, cap = service_fixture(modules)
            scope = {"state": "armed", "generation": 5, "starting_date_raw": 1000,
                     "target_date_raw": 1024, "watch_army_ids": [10]}
            planned = {"planning_source_frame": dict(frame)}
            callback_module = modules["auto_camera_pre_advance_v1"]
            with callback_module.camera_pre_advance_scope_v1(service, planned):
                result = getattr(service.driver, callback_module._HOOK)(step="battle-sentinel-advance", current=snapshot, tracking_scope=scope)
                self.assertEqual(result["status"], "queued_native_presentation")
            self.assertFalse(hasattr(service.driver, callback_module._HOOK))
            self.assertIsNot(captured[0]["tracking_scope"], scope)
            snapshot["active_wars"][0]["allied_armies"][0]["route_province_ids"].append(4)
            self.assertEqual(captured[0]["active_wars"][0]["allied_armies"][0]["route_province_ids"], [2])
            self.assertEqual(header.request.mode, 4)
            self.assertEqual(header.request.expires_uptime_ms, 121000)
            self.assertEqual((cap.request.owner_epoch, cap.request.scope_generation, cap.request.fullarmy_id), (99, 5, 10))
            self.assertEqual([cap.request.provinces[i].id for i in range(cap.request.province_count)], [1, 2, 3])
            before = header.request_sequence
            with callback_module.camera_pre_advance_scope_v1(service, planned):
                missing = getattr(service.driver, callback_module._HOOK)(step="battle-sentinel-advance", current=snapshot, tracking_scope={})
                self.assertEqual(missing["status"], "unavailable")
            self.assertEqual(header.request_sequence, before)
            cap.active = 0
            bad = client.submit({"mode": "tracked_hotspot"}, frame, captured[0]["source_build"])
            self.assertEqual(bad["reason"], "native_tracking_capability_unavailable")
            self.assertEqual(header.request_sequence, before)
            self.assertFalse(bad["camera_postcondition_verified"])

    def test_legacy_thirty_day_realm_policy_and_tracked_receipt_expiry_remain_separate(self):
        with private_modules(self.changed) as modules:
            service, frame, snapshot, captured, client, memory, header, cap = service_fixture(modules)
            payload = service._auto_camera_hotspot_input(snapshot, frame)
            scope = {"state": "armed", "generation": 5, "starting_date_raw": 1000,
                     "target_date_raw": 1024, "watch_army_ids": [10]}
            payload["tracking_scope"] = scope
            service._select_auto_camera_hotspot(payload)
            request = cap.request
            for name in ("request_sequence", "owner_epoch", "scope_generation", "actor", "fullarmy_id"):
                setattr(cap.result, name, getattr(request, name))
            cap.result.state, cap.result.date_raw, cap.result.province_id, cap.result.target_updates = 1, 1001, 2, 1
            cap.result_sequence = 2
            actual = service._bound_camera_presentation_actual({**frame, "date_raw": 1001})
            self.assertEqual(actual["province_id"], 2)
            self.assertFalse(actual["camera_postcondition_verified"])
            cap.result.owner_epoch += 1
            self.assertIsNone(client.latest())
            cap.result.owner_epoch -= 1
            cap.result.date_raw = 1025
            self.assertIsNone(service._bound_camera_presentation_actual({**frame, "date_raw": 1025}))
            compact = modules["auto_camera_follow"].LatestCameraFollowWorker._reference(
                {"request_id": "fixture", "status": "completed", "receipt": {"native_actual": actual}})
            self.assertEqual(compact["receipt"]["native_actual"]["scope_generation"], 5)
            self.assertEqual(compact["receipt"]["native_actual"]["target_updates"], 1)
            self.assertNotIn("settle_diagnostics", compact["receipt"]["native_actual"])
            policy = modules["realm_overview_camera"].PeaceRealmCameraPolicy()
            quiet = {"source_frame": dict(frame), "map_ready": True, "has_player_armies": False}
            self.assertEqual((policy.quiet_days, policy.refresh_days), (30, 30))
            self.assertEqual(policy.observe(quiet, None)["mode"], "hold")
            quiet["source_frame"]["date_raw"] += 30 * 24 - 1
            self.assertEqual(policy.observe(quiet, None)["mode"], "hold")
            quiet["source_frame"]["date_raw"] += 1
            realm_intent = policy.observe(quiet, None)
            self.assertEqual(realm_intent["mode"], "realm")
            client.submit(realm_intent, quiet["source_frame"], payload["source_build"])
            self.assertEqual((header.request.mode, header.request.expires_uptime_ms), (1, 11000))
            self.assertIsNone(client._tracking_binding)
            legacy = header.result
            legacy.request_sequence, legacy.status, legacy.actor, legacy.date_raw = header.request_sequence, 2, 7, 1720
            legacy.county_count, legacy.zoom_index, legacy.coverage_verified = 3, 2, 0
            for i in range(6):
                legacy.target[i] = legacy.current[i] = i
            header.result_sequence = 2
            result = client.latest()
            self.assertEqual(result["status"], "settled")
            self.assertFalse(result["coverage_verified"])


def qualify():
    out = io.StringIO()
    started = time.perf_counter()
    result = unittest.TextTestRunner(stream=out, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Source24CameraIntegration))
    source.exact.require(result.wasSuccessful(), "Source24 focused qualification failed: " + out.getvalue())
    report = dict(Source24CameraIntegration.report)
    report["qualification"] = {"new_tests": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
                               "seconds": round(time.perf_counter()-started, 6), "runner": out.getvalue(),
                               "old_M7_57_or_camera9_or147_repeated": False,
                               "fixture_scope": "Private temporary module namespace; exact candidate camera methods/helper/client, RAM ctypes channel, fake HWND/kernel/driver class identity and typed arm input. No real Arm, Desktop, Native or OS capability qualification.",
                               "observed_behavior": "Route copies include intermediate province; scope crosses original context manager and exact Service methods into Mode4/tail; missing scope/capability does not queue; exact epoch and expiry receipt guards; legacy quiet30/mode1/coverageFalse retained.",
                               "children_or_live_calls": 0, "new_scratch_files": 0,
                               "source_inheritance": {"continuous_source": "native30-continuous-camera-source-ready-2026-10-19.json:15648/79faadc9d82634141549441531a3582967fcc7b76a2aa7c4f3a5905fb924a63f",
                                                      "scalar_delta": "native30-camera-scalar-reference-delta-2026-10-19.json:687/8a1c434a5b1917ff2770c133aeba4b59154db848e625cc207aea57489ef3c508",
                                                      "limits": "Old147/oldscalar case remain at old source pins; no newly claimed live tracking/realm coverage or H."}}
    report["source_package"] = {"card": {"path": "D:/codex-ck3-demos/2026-10-19-robert-v20261019-storage01/COMPOSER-SOURCE24-CAMERA-NEW-SOURCE96KiB-COMMITMENT01.json",
                                         "bytes": 1972, "sha256": "e7117352fc02a2261c28a0b78ba1055fa46f23ef950386ce70603ccf4a568239"},
                                "new_three_hard_bytes": 98304, "files": [], "new_file_count": 3,
                                "new_three_gross_bytes": 0, "full_participating_logical_gross_bytes": 0,
                                "new_production_tree_copies": 0, "scratch_bytes": 0}
    for path in source.OWNED[:2]:
        report["source_package"]["files"].append({"path": str(path), **source.exact.pin(path.read_bytes())})
    report["plan_path"], report["plan_bytes"] = str(source.OWNED[2]), 0
    other = sum(r["bytes"] for r in report["source_package"]["files"])
    for _ in range(12):
        raw = (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode()
        total = other + len(raw)
        full = report["output"]["actual_Source22_changed_logical_bytes_each"] + total
        if (report["plan_bytes"], report["source_package"]["new_three_gross_bytes"], report["source_package"]["full_participating_logical_gross_bytes"]) == (len(raw), total, full):
            break
        report["plan_bytes"] = len(raw)
        report["source_package"]["new_three_gross_bytes"] = total
        report["source_package"]["full_participating_logical_gross_bytes"] = full
    else:
        raise ValueError("source accounting failed to converge")
    source.exact.require(total <= 98304 and full <= 3407872, "complete Source24 source quote exceeds caps")
    return report, raw


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-plan", action="store_true")
    args = parser.parse_args()
    report, raw = qualify()
    if args.write_plan:
        with source.OWNED[2].open("xb") as stream:
            stream.write(raw)
    print(json.dumps({"plan_written": args.write_plan,
                      "plan": {"path": str(source.OWNED[2]), **source.exact.pin(raw)},
                      "output": report["output"], "source_package": report["source_package"],
                      "qualification": report["qualification"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
