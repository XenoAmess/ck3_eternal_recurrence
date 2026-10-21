"""Self-owned direct-child identity checks, including a Windows venv caller."""
import json
import os
import subprocess
import sys
import unittest
from unittest.mock import patch
from typing import Protocol, runtime_checkable

from tools.g2_saved_campaign import owned_python_launch_v1 as launch

RUNS: list[dict[str, object]] = []


@runtime_checkable
class WindowsProcessHandleV1(Protocol):
    def Close(self) -> None: ...


@unittest.skipUnless(os.name=="nt","Windows forwarding launcher semantics")
class DirectOwnedPythonTests(unittest.TestCase):
    def test_image_mismatch_refuses_instead_of_following_a_foreign_launcher(self) -> None:
        with patch.object(launch,"_loaded_image_v1",return_value=sys.executable), \
             patch.object(sys,"_base_executable",__file__):
            with self.assertRaisesRegex(ValueError,"differs from declared base"):
                launch.owned_python_launch_v1()

    def test_direct_child_exact_pid_birth_and_same_dependency_origin(self) -> None:
        import mcp
        from tools.g2_saved_campaign.sdk_process_custody import RetainedProcessGeneration
        executable,env=launch.owned_python_launch_v1()
        # The base executable keeps current venv dependencies through explicit
        # fixture paths; it is not allowed to resolve a different MCP install.
        program="import os,sys,json,mcp; print(json.dumps({'pid':os.getpid(),'mcp':mcp.__file__,'exe':sys.executable}),flush=True); sys.stdin.readline()"
        child=subprocess.Popen([executable,"-B","-c",program],env=env,
            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW)
        retained=None
        try:
            assert child.stdout is not None and child.stdin is not None
            decoded: object = json.loads(child.stdout.readline())
            if not isinstance(decoded, dict):
                raise AssertionError("child report object required")
            value: dict[str, object] = {key: decoded.get(key) for key in ("pid", "exe", "mcp")}
            if type(value["pid"]) is not int or not isinstance(value["exe"], str) or not isinstance(value["mcp"], str):
                raise AssertionError("exact child report fields required")
            self.assertEqual(value["pid"],child.pid)
            child_exe, child_mcp = value["exe"], value["mcp"]
            assert isinstance(child_exe, str) and isinstance(child_mcp, str)
            self.assertTrue(os.path.samefile(child_exe,executable))
            self.assertTrue(os.path.samefile(child_mcp,mcp.__file__))
            retained=RetainedProcessGeneration.capture(child.pid,expected_executable=executable)
            self.assertEqual(retained.pid,child.pid)
            child.stdin.write(b"close\n");child.stdin.flush()
            stdout,stderr=child.communicate(timeout=10)
            self.assertEqual(child.returncode,0,stderr)
            self.assertEqual(retained._api.wait_zero(retained._handle),0)
            RUNS.append({"returned_pid":child.pid,"actual_pid":value["pid"],
                "exact_creation_filetime":str(retained.creation_filetime),"direct_executable":executable,
                "caller_sys_executable":sys.executable,"same_dependency_origin":True,"exit_code":0})
        finally:
            if child.poll() is None:child.terminate();child.wait(timeout=10)
            for stream in (child.stdin,child.stdout,child.stderr):
                if stream:stream.close()
            handle: object = getattr(child, "_handle", None)
            if not isinstance(handle, WindowsProcessHandleV1):
                raise AssertionError("actual Windows Popen handle required")
            handle.Close()
            if retained is not None:retained.close()


class FixtureSearchPathTests(unittest.TestCase):
    def test_empty_sys_path_is_explicit_caller_directory(self) -> None:
        from pathlib import Path
        with patch.object(launch, "_loaded_image_v1", return_value=sys.executable), \
             patch.object(sys, "_base_executable", sys.executable), \
             patch.object(sys, "path", [""]), \
             patch.dict(os.environ, {}, clear=True):
            _, env = launch.owned_python_launch_v1()
        self.assertEqual(env["PYTHONPATH"].split(os.pathsep), [str(Path.cwd())])

    def test_pythonpath_empty_value_and_internal_empty_item_match_python(self) -> None:
        from pathlib import Path
        dependency = str(Path(sys.executable).parent)
        for inherited in (None, "", os.pathsep):
            entries = {} if inherited is None else {"PYTHONPATH": inherited}
            with self.subTest(pythonpath=inherited), \
                 patch.object(launch, "_loaded_image_v1", return_value=sys.executable), \
                 patch.object(sys, "_base_executable", sys.executable), \
                 patch.object(sys, "path", [dependency]), \
                 patch.dict(os.environ, entries, clear=True):
                _, env = launch.owned_python_launch_v1()
            expected = [dependency] if not inherited else [dependency, str(Path.cwd())]
            self.assertEqual(env["PYTHONPATH"].split(os.pathsep), expected)

    @unittest.skipUnless(os.name == "nt", "actual direct interpreter image")
    def test_fresh_child_imports_caller_project_after_cwd_change(self) -> None:
        from pathlib import Path
        caller_root = Path.cwd()
        expected = Path(launch.__file__).resolve()
        with patch.object(sys, "path", [""]), \
             patch.dict(os.environ, {"PYTHONPATH": ""}):
            executable, env = launch.owned_python_launch_v1()
        program = ("from pathlib import Path; "
                   "from tools.g2_saved_campaign import owned_python_launch_v1 as m; "
                   "print(Path(m.__file__).resolve())")
        child = subprocess.run([executable, "-B", "-c", program],
            env=env, cwd=caller_root.parent, capture_output=True, text=True,
            timeout=15, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        self.assertEqual(child.returncode, 0, child.stderr)
        self.assertEqual(Path(child.stdout.strip()), expected)


if __name__=="__main__":unittest.main()
