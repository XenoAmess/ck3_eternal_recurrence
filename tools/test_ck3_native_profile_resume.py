"""Offline coverage of existing-DLL resume and read-only pending context tools."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from mcp.client import Client
import ck3_native_profile_mcp as native
from test_ck3_native_profile_mcp import Backend, Driver, service_fixture


def resume_fixture(root):
    original, _, old_driver, _, _ = service_fixture(root)
    old_driver.snapshot["diagnostics"]["hello"]["connection_generation"] = 1
    old_driver.snapshot["pending_character_interaction"] = {
        "instance_id": 123, "sender_character_id": 42, "auto_accept_notification": False}
    attached = original.attach()
    original.snapshot()  # Required latest successful paused transport receipt.
    original.close()
    profile = original.profile
    backend, driver = Backend(profile), Driver(profile)
    driver.snapshot = copy.deepcopy(old_driver.snapshot)
    driver.snapshot["diagnostics"]["hello"]["connection_generation"] = 2
    factories = []
    def factory(pipe, **kwargs):
        factories.append((pipe, kwargs))
        return driver
    resumed = native.NativeProfileService(profile, backend=backend, driver_factory=factory)
    resumed._resume_timeout_seconds = 0
    return original, resumed, backend, driver, factories, attached


class ProfileResumeTests(unittest.TestCase):
    def test_resume_retains_original_claim_new_session_generation_and_zero_injection(self):
        with tempfile.TemporaryDirectory() as temporary:
            original, service, backend, driver, factories, attached = resume_fixture(Path(temporary))
            claim = Path(service.profile["evidence_directory"]) / "attach-claim.json"
            claim_bytes = claim.read_bytes()
            attach_bytes = Path(attached["receipt_path"]).read_bytes()
            result = service.resume()
            self.assertEqual(result["status"], "resumed_snapshot_verified")
            self.assertNotEqual(result["session_id"], original.session_id)
            self.assertEqual(result["prior_session_id"], original.session_id)
            self.assertEqual(result["prior_connection_generation"], 1)
            self.assertEqual(result["connection_generation"], 2)
            self.assertEqual(result["pipe_name"], original.pipe_name)
            self.assertEqual(result["native_clock_before"], result["native_clock_after"])
            self.assertEqual(claim.read_bytes(), claim_bytes)
            self.assertEqual(Path(attached["receipt_path"]).read_bytes(), attach_bytes)
            self.assertEqual(backend.injections, [])
            self.assertEqual(factories[0][0], original.pipe_name)
            self.assertEqual(factories[0][1]["episode_projection"], "native_campaign")
            self.assertIs(service.resume(), result)
            self.assertIs(service.attach(), result)
            self.assertEqual(len(factories), 1)
            self.assertFalse(driver.closed)
            self.assertTrue(service.inspect()["attached"])

    def test_claim_attach_and_latest_snapshot_mismatch_open_zero_endpoints(self):
        for mode in ("claim_profile", "claim_target", "claim_pipe", "attach_red", "latest_not_snapshot", "generation"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temporary:
                _, service, backend, _, factories, attached = resume_fixture(Path(temporary))
                evidence = Path(service.profile["evidence_directory"])
                claim_path = evidence / "attach-claim.json"
                claim = json.loads(claim_path.read_text())
                if mode.startswith("claim"):
                    if mode == "claim_profile": claim["profile_sha256"] = "0" * 64
                    elif mode == "claim_target": claim["target"]["pid"] = 999
                    else: claim["pipe_name"] = r"\\.\pipe\other"
                    claim_path.write_text(json.dumps(claim))
                else:
                    path = Path(attached["receipt_path"])
                    if mode != "attach_red": path = next(path.parent.glob("*-snapshot.json"))
                    value = json.loads(path.read_text())
                    if mode in {"attach_red", "latest_not_snapshot"}: value["status"] = "RED"
                    else: value["snapshot"]["diagnostics"]["hello"]["connection_generation"] = None
                    path.write_text(json.dumps(value))
                with self.assertRaises((ValueError, RuntimeError)):
                    service.resume()
                self.assertEqual(factories, [])
                self.assertEqual(backend.injections, [])

    def test_stale_guard_running_clock_or_date_mismatch_open_zero_endpoints(self):
        for mode in ("pid", "offline", "lease", "crash", "running", "date", "speed", "dll"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temporary:
                _, service, backend, _, factories, _ = resume_fixture(Path(temporary))
                if mode == "pid": backend.desktop.overrides["pid"] = 999
                elif mode == "offline": backend.desktop.overrides["steam_offline_flags"] = ["0"]
                elif mode == "lease": backend.desktop.overrides["screen_lease_fresh"] = False
                elif mode == "running": backend.clock["paused"] = False
                elif mode == "date": backend.clock["date_raw"] += 24
                elif mode == "speed": backend.clock["speed"] = 5
                elif mode == "dll": Path(service.profile["dll"]["path"]).write_bytes(b"changed")
                else:
                    crash = Path(service.profile["userdir"]) / "crashes" / "new"
                    crash.mkdir(parents=True)
                with self.assertRaises(RuntimeError): service.resume()
                self.assertEqual(factories, [])
                self.assertEqual(backend.injections, [])

    def test_stale_generation_or_changed_campaign_retains_red_without_reconnecting_again(self):
        for mode in ("generation", "date", "running", "pending", "event", "hello"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temporary:
                _, service, backend, driver, factories, _ = resume_fixture(Path(temporary))
                if mode == "generation": driver.snapshot["diagnostics"]["hello"]["connection_generation"] = 1
                elif mode == "date": driver.snapshot["date_raw"] += 24
                elif mode == "running": driver.snapshot["paused"] = False
                elif mode == "pending": driver.snapshot["pending_character_interaction"]["instance_id"] += 1
                elif mode == "event": driver.snapshot["active_event"] = {"instance_id": 99}
                else: driver.snapshot["diagnostics"]["bridge_pid"] = 999
                result = service.resume()
                self.assertEqual(result["status"], "RED")
                self.assertTrue(driver.closed)
                self.assertIs(service.resume(), result)
                self.assertIs(service.attach(), result)
                self.assertEqual(len(factories), 1)
                self.assertEqual(backend.injections, [])

    def test_late_fresh_snapshot_is_read_only_and_final_guard_or_clock_failure_remains_red(self):
        for mode in ("late", "final_guard", "final_clock"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temporary:
                _, service, backend, driver, factories, _ = resume_fixture(Path(temporary))
                reads = []
                def snapshot():
                    reads.append(1)
                    result = copy.deepcopy(driver.snapshot)
                    if mode == "late" and len(reads) == 1:
                        result["diagnostics"]["hello"]["connection_generation"] = 1
                    elif mode == "final_guard": backend.desktop.overrides["screen_lease_fresh"] = False
                    elif mode == "final_clock": backend.clock["date_raw"] += 24
                    return result
                driver.take_snapshot = snapshot
                service._resume_timeout_seconds = 0.2
                result = service.resume()
                self.assertEqual(result["status"], "resumed_snapshot_verified" if mode == "late" else "RED")
                self.assertEqual(len(factories), 1)
                self.assertEqual(backend.injections, [])
                if mode == "late": self.assertEqual(len(reads), 2)

    def test_pending_query_binds_instance_revision_and_retains_unavailable_context(self):
        with tempfile.TemporaryDirectory() as temporary:
            _, service, backend, driver, _, _ = resume_fixture(Path(temporary))
            service.resume()
            calls = []
            class Gameplay:
                def query_pending_character_interaction_context_v1(self, instance, *, expected_revision):
                    calls.append((instance, expected_revision))
                    return {"status": "unavailable", "reason": "pending_terms_unavailable"}
            service._gameplay = Gameplay()
            result = service.query_pending_interaction(123, 7)
            self.assertEqual(result["status"], "native_pending_query_verified")
            self.assertEqual(result["result"]["status"], "unavailable")
            self.assertEqual(calls, [(123, 7)])
            for instance, revision in [(True, 7), (0, 7), (2**31, 7), (124, 7), (123, True), (123, 8)]:
                with self.assertRaises((ValueError, RuntimeError)):
                    service.query_pending_interaction(instance, revision)
            driver.snapshot["paused"] = False
            with self.assertRaises(RuntimeError): service.query_pending_interaction(123, 7)
            self.assertEqual(calls, [(123, 7)])
            self.assertEqual(backend.injections, [])

    def test_query_rejects_pending_drift_and_post_guard_failure_without_any_reply(self):
        for mode in ("pending", "guard"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temporary:
                _, service, backend, driver, _, _ = resume_fixture(Path(temporary))
                service.resume()
                class Gameplay:
                    def query_pending_character_interaction_context_v1(self, instance, *, expected_revision):
                        if mode == "pending": driver.snapshot["pending_character_interaction"] = None
                        else: backend.desktop.overrides["screen_lease_fresh"] = False
                        return {"status": "available"}
                service._gameplay = Gameplay()
                with self.assertRaises(RuntimeError): service.query_pending_interaction(123, 7)
                self.assertEqual(backend.injections, [])

    def test_reply_submits_one_explicit_instance_then_waits_only_for_real_pending_clear(self):
        for mode in ("late_clear", "timeout", "running", "changed_date", "command_error"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temporary:
                _, service, backend, driver, _, _ = resume_fixture(Path(temporary))
                service.resume()
                calls, reads = [], []
                class Gameplay:
                    def reply_pending_character_interaction(self, **kwargs):
                        calls.append(kwargs)
                        if mode == "command_error": raise RuntimeError("native command denied")
                        return {"status": "ACK", "interaction_instance_id": 123}
                service._gameplay = Gameplay()
                service._postcondition_timeout_seconds = 1.0 if mode == "late_clear" else 0.01
                service._postcondition_poll_seconds = 0.001
                def snapshot():
                    result = copy.deepcopy(driver.snapshot)
                    if calls:
                        reads.append(1)
                        if mode != "timeout" and len(reads) >= 2:
                            result["pending_character_interaction"] = None
                            if mode == "running": result["paused"] = False
                            elif mode == "changed_date": result["date_raw"] += 24
                    return result
                driver.take_snapshot = snapshot
                result = service.reply_pending_interaction(True, 123, 7)
                self.assertEqual(calls, [{"accept": True, "interaction_instance_id": 123, "expected_revision": 7}])
                self.assertEqual(result["status"], "native_gameplay_postcondition_verified" if mode == "late_clear" else "RED")
                self.assertEqual(backend.injections, [])

    def test_reply_invalid_choice_instance_revision_or_guard_sends_zero_actions(self):
        for mode in ("choice", "instance", "revision", "running", "guard"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temporary:
                _, service, backend, driver, _, _ = resume_fixture(Path(temporary))
                service.resume()
                calls = []
                class Gameplay:
                    def reply_pending_character_interaction(self, **kwargs): calls.append(kwargs)
                service._gameplay = Gameplay()
                if mode == "running": driver.snapshot["paused"] = False
                elif mode == "guard": backend.desktop.overrides["screen_lease_fresh"] = False
                with self.assertRaises((ValueError, RuntimeError)):
                    service.reply_pending_interaction(1 if mode == "choice" else False,
                        124 if mode == "instance" else 123, 8 if mode == "revision" else 7)
                self.assertEqual(calls, [])


class ProfileResumeMcpTests(unittest.IsolatedAsyncioTestCase):
    async def test_official_client_closed_schema_resume_and_read_only_query(self):
        with tempfile.TemporaryDirectory() as temporary:
            _, service, backend, driver, factories, _ = resume_fixture(Path(temporary))
            class Gameplay:
                def query_pending_character_interaction_context_v1(self, instance, *, expected_revision):
                    return {"status": "unavailable", "reason": "pending_terms_unavailable"}
                def reply_pending_character_interaction(self, **kwargs):
                    driver.snapshot["pending_character_interaction"] = None
                    return {"status": "ACK", "interaction_instance_id": kwargs["interaction_instance_id"]}
            service._gameplay = Gameplay()
            async with Client(native.create_server(service), cache=None) as client:
                listing = await client.list_tools()
                tools = {tool.name: tool for tool in listing.tools}
                self.assertTrue(tools["ck3_query_profile_pending_interaction_v1"].annotations.read_only_hint)
                self.assertFalse(tools["ck3_reply_profile_pending_interaction_v1"].annotations.read_only_hint)
                self.assertEqual(tools["ck3_resume_profile_bridge_v1"].input_schema["properties"], {})
                denied = await client.call_tool("ck3_resume_profile_bridge_v1", {"pipe_name": "other"})
                self.assertTrue(denied.is_error)
                self.assertEqual(factories, [])
                resumed = await client.call_tool("ck3_resume_profile_bridge_v1", {})
                self.assertEqual(resumed.structured_content["status"], "resumed_snapshot_verified")
                queried = await client.call_tool("ck3_query_profile_pending_interaction_v1",
                    {"pending_interaction_id": 123, "expected_revision": 7})
                self.assertEqual(queried.structured_content["result"]["status"], "unavailable")
                denied = await client.call_tool("ck3_query_profile_pending_interaction_v1",
                    {"pending_interaction_id": 123, "expected_revision": 7, "pid": 999})
                self.assertTrue(denied.is_error)
                replied = await client.call_tool("ck3_reply_profile_pending_interaction_v1",
                    {"accept": False, "pending_interaction_id": 123, "expected_revision": 7})
                self.assertEqual(replied.structured_content["status"], "native_gameplay_postcondition_verified")
                self.assertEqual(backend.injections, [])


if __name__ == "__main__":
    unittest.main()
