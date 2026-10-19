"""Production owner ordering and failclosed cases; OS boundary injected."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

import interactive_task_owner_v1 as o


class FakeOS:
    def __init__(self, s):
        self.s, self.order = s, []
        self.w = self
        self.api = self
        self.waits = [258, 0]
        self.terminated = False

    def current(self):
        return {"sid": self.s["sid"], "session": self.s["session"], "image": self.s["pythonw"],
                "image_file_id": self.s["pythonw_file_id"]}

    def job(self):
        self.order.append("job")
        return 10

    def spawn(self, s):
        self.order.append("spawn_suspended")
        return 11, 12

    def assign(self, job, process):
        self.order.append("assign")

    def identity(self, handle):
        return {"pid": 123, "creation_filetime": "134368942073684039", "wait0": 258,
                "image": self.s["python"], "image_file_id": self.s["python_file_id"],
                "session": self.s["session"], "exit_code": None}

    def resume(self, handle):
        self.order.append("resume")

    def close(self, handle):
        self.order.append("close_" + str(handle))

    def WaitForSingleObject(self, handle, milliseconds):
        if self.terminated or milliseconds == 5000:
            return 0
        return self.waits.pop(0)

    def GetExitCodeProcess(self, handle):
        return 0

    def TerminateProcess(self, handle, code):
        self.order.append("terminate_own_suspended")
        self.terminated = True

    def active(self, job):
        return 0


class Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.s = {"root": str(root), "nonce": "a" * 32, "machine_id": "test-only",
                  "sid": "S-1-5-21-1", "session": 2, "python": str(root / "python.exe"),
                  "pythonw": str(root / "pythonw.exe"), "python_file_id": {"id": "p"},
                  "pythonw_file_id": {"id": "w"}, "stop_path": str(root / "fixture-stop"),
                  "stage_sha256": "b" * 64}

    def test_actual_core_job_before_resume_and_original_exit(self):
        api = FakeOS(self.s)
        self.assertEqual(o.run_owner(self.s, "c" * 64, api), 0)
        self.assertLess(api.order.index("assign"), api.order.index("resume"))
        closed = o.read(Path(self.s["root"]) / "CLOSED.json")
        self.assertEqual(closed["child_exit_code"], 0)
        self.assertFalse(closed["forced_remaining_cleanup"])
        self.assertEqual(closed["child"]["creation_filetime"], "134368942073684039")

    def test_foreign_identity_is_rejected_before_spawn(self):
        api = FakeOS(self.s)
        api.current = lambda: {"sid": "S-1-5-18", "session": 0, "image": self.s["pythonw"]}
        self.assertEqual(o.run_owner(self.s, "c" * 64, api), 1)
        self.assertNotIn("spawn_suspended", api.order)

    def test_stop_is_exact_marker_then_original_normal_exit(self):
        api = FakeOS(self.s)
        child = api.identity(11)
        o.once(Path(self.s["root"]) / "STOP.json", {"nonce": self.s["nonce"],
            "spec_sha256": "c" * 64, "child": child})
        self.assertEqual(o.run_owner(self.s, "c" * 64, api), 0)
        self.assertEqual(Path(self.s["stop_path"]).read_text(), self.s["nonce"])

    def test_wrong_stop_does_not_create_stage_marker(self):
        api = FakeOS(self.s)
        o.once(Path(self.s["root"]) / "STOP.json", {"nonce": "foreign"})
        self.assertEqual(o.run_owner(self.s, "c" * 64, api), 1)
        self.assertFalse(Path(self.s["stop_path"]).exists())
        self.assertFalse(o.read(Path(self.s["root"]) / "FAILED.json")["normal_closure_claim"])

    def test_assign_failure_cleans_only_original_suspended_child(self):
        api = FakeOS(self.s)
        api.assign = lambda *_: (_ for _ in ()).throw(RuntimeError("assign refused"))
        self.assertEqual(o.run_owner(self.s, "c" * 64, api), 1)
        self.assertIn("terminate_own_suspended", api.order)
        self.assertNotIn("resume", api.order)

    def test_consumed_attempt_does_not_replay_stage(self):
        o.once(Path(self.s["root"]) / "STARTED.json", {"old": True})
        api = FakeOS(self.s)
        self.assertEqual(o.run_owner(self.s, "c" * 64, api), 1)
        self.assertNotIn("spawn_suspended", api.order)

    def test_production_registration_is_not_implicit(self):
        with self.assertRaisesRegex(ValueError, "separate explicit admission"):
            o.register({"role": "supervisor"}, {}, object())

    def test_actual_task_mismatch_is_not_a_successful_ack(self):
        s = {**self.s, "task_name": "fixture"}
        action = {"path": "p", "arguments": "a", "cwd": "c"}
        actual = {"sid": s["sid"], "logon_type": 3, "run_level": 0, "actions": 1,
                  "triggers": 0, "action_type": 0, "hidden": True, "limit": "PT0S",
                  "demand": True, "multiple": 2, "hard_terminate": False, **action}
        o.require_task(actual, s, action)
        for key, value in [("sid", "S-1-5-18"), ("run_level", 1), ("triggers", 1), ("arguments", "foreign")]:
            changed = {**actual, key: value}
            with self.assertRaises(ValueError):
                o.require_task(changed, s, action)

    def test_wrapped_com_absence_does_not_swallow_access_denied(self):
        class Failure(Exception):
            hresult = -2147352567
            def __init__(self, code):
                self.excepinfo = (0, None, None, None, 0, code)
        scheduler = object.__new__(o.Scheduler)
        class Folder:
            def GetTask(self, name):
                raise Failure(self.code)
        scheduler.folder = Folder()
        scheduler.folder.code = -2147024894
        self.assertTrue(scheduler.absent("exact"))
        scheduler.folder.code = -2147024891
        with self.assertRaises(Failure):
            scheduler.absent("exact")

    def test_native_build_requires_pinned_admission_in_exact_argv(self):
        root = Path(self.s["root"])
        boot, stage, admission = root / "boot.py", root / "stage.py", root / "admission.json"
        for p in (boot, stage, admission):
            p.write_text("{}")
        s = {**self.s, "schema": o.SCHEMA, "role": "native_build", "cwd": str(root),
             "task_name": "XARG2ManagedOwner-" + self.s["nonce"],
             "bootstrap": str(boot), "bootstrap_sha256": o.sha(boot),
             "stage": str(stage), "stage_sha256": o.sha(stage),
             "admission_path": str(admission), "admission_sha256": o.sha(admission),
             "stage_args": ["--admission", str(admission)], "env": {}}
        path = root / "spec.json"
        path.write_text(json.dumps(s))
        self.assertEqual(o.checked_spec(path, o.sha(path))["role"], "native_build")
        s["stage_args"][-1] = str(root / "foreign.json")
        path.write_text(json.dumps(s))
        with self.assertRaisesRegex(ValueError, "exact separate admission"):
            o.checked_spec(path, o.sha(path))

    def test_registration_caller_is_actual_same_user_session_base_image(self):
        actual = {"sid": self.s["sid"], "session": self.s["session"],
                  "image": self.s["python"], "image_file_id": self.s["python_file_id"]}
        o.require_caller(self.s, actual)
        for key, value in [("sid", "S-1-5-18"), ("session", 0),
                           ("image", "redirector.exe"), ("image_file_id", {"id": "foreign"})]:
            with self.assertRaises(ValueError):
                o.require_caller(self.s, {**actual, key: value})


if __name__ == "__main__":
    unittest.main()
