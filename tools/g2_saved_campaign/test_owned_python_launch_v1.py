"""Self-owned direct-child identity checks, including a Windows venv caller."""
import json
import os
import subprocess
import sys
import unittest
from unittest.mock import patch

from tools.g2_saved_campaign import owned_python_launch_v1 as launch

RUNS=[]


@unittest.skipUnless(os.name=="nt","Windows forwarding launcher semantics")
class DirectOwnedPythonTests(unittest.TestCase):
    def test_image_mismatch_refuses_instead_of_following_a_foreign_launcher(self):
        with patch.object(launch,"_loaded_image_v1",return_value=sys.executable), \
             patch.object(sys,"_base_executable",__file__):
            with self.assertRaisesRegex(ValueError,"differs from declared base"):
                launch.owned_python_launch_v1()

    def test_direct_child_exact_pid_birth_and_same_dependency_origin(self):
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
            value=json.loads(child.stdout.readline())
            self.assertEqual(value["pid"],child.pid)
            self.assertTrue(os.path.samefile(value["exe"],executable))
            self.assertTrue(os.path.samefile(value["mcp"],mcp.__file__))
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
            child._handle.Close()
            if retained is not None:retained.close()


if __name__=="__main__":unittest.main()
