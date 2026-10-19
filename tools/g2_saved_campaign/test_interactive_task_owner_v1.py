"""Production owner ordering and failclosed cases; OS boundary injected."""
import copy
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

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

    def test_wal_environment_is_only_exact_sdk_owner_opt_in(self):
        root = Path(self.s["root"])
        boot, stage = root / "boot.py", root / "stage.py"
        for path in (boot, stage):
            path.write_text("{}")
        s = {**self.s, "schema": o.SCHEMA, "role": "sdk_owner", "cwd": str(root),
             "task_name": "XARG2ManagedOwner-" + self.s["nonce"],
             "bootstrap": str(boot), "bootstrap_sha256": o.sha(boot),
             "stage": str(stage), "stage_sha256": o.sha(stage), "stage_args": [], "env": {}}
        path = root / "spec.json"
        def checked():
            path.write_text(json.dumps(s))
            return o.checked_spec(path, o.sha(path))
        self.assertNotIn(o.SDK_WAL_ENV_KEY, checked()["env"])
        s["env"] = {o.SDK_WAL_ENV_KEY: "1"}
        self.assertEqual(checked()["env"][o.SDK_WAL_ENV_KEY], "1")
        admission = root / "admission.json"
        admission.write_text("{}")
        for role in ("supervisor", "display_owner", "feeder", "native_build", "fixture"):
            prefix = "XARG2ManagedOwnerFixture-" if role == "fixture" else "XARG2ManagedOwner-"
            s["task_name"] = prefix + self.s["nonce"]
            if role == "native_build":
                s.update(admission_path=str(admission), admission_sha256=o.sha(admission),
                         stage_args=["--admission", str(admission)])
            with self.subTest(role=role), self.assertRaisesRegex(ValueError, "exact value"):
                s["role"] = role
                checked()
        s["role"] = "sdk_owner"
        s["task_name"] = "XARG2ManagedOwner-" + self.s["nonce"]
        for env in ({o.SDK_WAL_ENV_KEY: "0"}, {o.SDK_WAL_ENV_KEY: "true"},
                    {o.SDK_WAL_ENV_KEY: 1}, {o.SDK_WAL_ENV_KEY: "1\0"},
                    {"XAR_CK3_ENABLE_DRIVER_STATE_WAL_V2": "1"}):
            with self.subTest(env=env), self.assertRaises(ValueError):
                s["env"] = env
                checked()

    def test_prepare_wal_default_and_exact_environment_without_OS_calls(self):
        root = Path(self.s["root"])
        stage, boot = root / "stage.py", root / "boot.py"
        stage.write_text("pass")
        boot.write_text("fixture-frozen-copy")
        (root / "pythonw.exe").write_bytes(b"fixture; never executed")
        real_sha = o.sha
        def fixture_sha(path):
            return real_sha(boot) if Path(path).resolve() == Path(o.__file__).resolve() else real_sha(path)
        fake = FakeOS(self.s)
        fake.current = lambda: {"sid": self.s["sid"], "session": self.s["session"],
                                "loaded_module": self.s["python"]}
        fake.file_id = lambda path: {"fixture": str(path)}
        args = dict(role="sdk_owner", stage=stage, stage_sha256=real_sha(stage),
                    bootstrap_path=boot, cwd=root, machine_id="test-only")
        with patch.object(o, "Windows", return_value=fake), patch.object(o, "sha", side_effect=fixture_sha):
            for enabled in (False, True):
                result = o.prepare_spec(root=root / str(enabled),
                    enable_driver_state_wal=enabled, **args)
                spec = o.read(result["spec"])
                self.assertEqual(spec["env"], {"PYTHONDONTWRITEBYTECODE": "1",
                    **({o.SDK_WAL_ENV_KEY: "1"} if enabled else {})})
            for role, enabled in (("supervisor", True), ("display_owner", True),
                                  ("feeder", True), ("native_build", True), ("sdk_owner", "1")):
                with self.subTest(role=role, enabled=enabled), self.assertRaisesRegex(ValueError, "WAL opt-in"):
                    o.prepare_spec(root=root / "must-not-exist", enable_driver_state_wal=enabled,
                                   **{**args, "role": role})
            self.assertFalse((root / "must-not-exist").exists())

    def test_prepare_cli_wal_flag_is_explicit_and_default_off(self):
        argv = ["prepare", "--root", "unused", "--role", "sdk_owner", "--stage", "unused.py",
                "--stage-sha", "b" * 64, "--bootstrap-path", "boot.py", "--cwd", ".",
                "--machine-id", "test-only"]
        for flags, expected in (([], False), (["--enable-driver-state-wal"], True)):
            with patch.object(o, "prepare_spec", return_value={"fixture": True}) as prepare, redirect_stdout(io.StringIO()):
                self.assertEqual(o.main(argv + flags), 0)
                self.assertIs(prepare.call_args.kwargs["enable_driver_state_wal"], expected)


if __name__ == "__main__":
    unittest.main()
