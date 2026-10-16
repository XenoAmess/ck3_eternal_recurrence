"""Run the production startup method with a fake clock and no OS/socket calls."""
import ast
import copy
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


SOURCE = Path(__file__).with_name("ck3_obs_capture.py")


def run_start(*, ready_at=None, occupied=False, wrong_sha=False,
              generation_drift_at=None, legacy_bound=False):
    tree = ast.parse(SOURCE.read_text(encoding="utf-8-sig"))
    cls = next(node for node in tree.body if isinstance(node, ast.ClassDef)
               and node.name == "OwnedEngine")
    method = copy.deepcopy(next(node for node in cls.body if isinstance(node, ast.FunctionDef)
                               and node.name == "start"))
    if legacy_bound:
        loop = next(node for node in method.body if isinstance(node, ast.For))
        loop.iter.args[0].value = 40
    clock = SimpleNamespace(now=0, launches=0, connects=0, argv=None)

    def listeners(port):
        return [object()] if occupied or (clock.launches and ready_at is not None
                                          and clock.now >= ready_at) else []

    def sleep(seconds):
        clock.now += seconds

    def popen(argv, **ignored):
        clock.launches += 1
        clock.argv = argv
        return SimpleNamespace(pid=12345)

    class Generation:
        creation_filetime = 999

        def __init__(self, *ignored):
            pass

        def check(self):
            if generation_drift_at is not None and clock.now >= generation_drift_at:
                raise RuntimeError("synthetic process generation changed")

    class RequestError(Exception):
        pass

    def connect():
        clock.connects += 1
        return "synthetic_ready_client"

    env = {
        "Path": Path, "_listeners": listeners,
        "_sha": lambda path: "wrong" if wrong_sha else "synthetic_exact_sha",
        "time": SimpleNamespace(sleep=sleep),
        "subprocess": SimpleNamespace(STARTUPINFO=lambda: SimpleNamespace(dwFlags=0),
            STARTF_USESHOWWINDOW=1, DEVNULL=None, Popen=popen),
        "_generation_helpers": lambda: (Generation, None, None, None),
        "_write_new": lambda path, value: None,
    }
    exec(compile(ast.Module(body=[method], type_ignores=[]), str(SOURCE), "exec"), env)
    with tempfile.TemporaryDirectory() as directory:
        executable = Path(directory) / "synthetic_obs.exe"
        executable.write_bytes(b"synthetic identity; never executed")
        owner = SimpleNamespace(profile={"executable": str(executable),
            "executable_sha256": "synthetic_exact_sha", "port": 4483,
            "profile_name": "synthetic", "collection_name": "synthetic"},
            job={"receipt_root": directory}, connect=connect)
        modules = {"psutil": SimpleNamespace(Process=lambda pid:
            SimpleNamespace(cmdline=lambda: clock.argv)),
            "obsws_python.error": SimpleNamespace(OBSSDKRequestError=RequestError)}
        with patch.dict(sys.modules, modules):
            try:
                result = env["start"](owner)
            except Exception as error:
                return clock, type(error).__name__
    return clock, result


class StartupReadinessTests(unittest.TestCase):
    def test_delayed_listener_reproduces_old_timeout_and_now_starts(self):
        old, status = run_start(ready_at=41.5, legacy_bound=True)
        self.assertEqual((status, old.now, old.connects), ("TimeoutError", 40, 0))
        new, status = run_start(ready_at=41.5)
        self.assertEqual((status, new.now, new.connects, new.launches),
                         ("synthetic_ready_client", 42, 1, 1))

    def test_never_ready_remains_bounded_without_relaunch(self):
        clock, status = run_start()
        self.assertEqual((status, clock.now, clock.launches, clock.connects),
                         ("TimeoutError", 120, 1, 0))

    def test_fast_ready_has_no_added_delay(self):
        clock, status = run_start(ready_at=1)
        self.assertEqual((status, clock.now, clock.connects), ("synthetic_ready_client", 1, 1))

    def test_occupied_port_rejects_before_launch(self):
        clock, status = run_start(occupied=True)
        self.assertEqual((status, clock.launches), ("RuntimeError", 0))

    def test_changed_executable_rejects_before_launch(self):
        clock, status = run_start(wrong_sha=True)
        self.assertEqual((status, clock.launches), ("RuntimeError", 0))

    def test_generation_change_during_wait_rejects_without_connecting(self):
        clock, status = run_start(ready_at=41.5, generation_drift_at=10)
        self.assertEqual((status, clock.now, clock.connects), ("RuntimeError", 10, 0))


if __name__ == "__main__":
    unittest.main()
