"""Repository help stays ordinary/read-only and does not initialize COM or DLLs."""
from pathlib import Path
import subprocess
import sys
import unittest

ROOT=Path(__file__).parent.parent

class RepositoryCliTests(unittest.TestCase):
    def test_all_repository_entry_help_is_available_without_packaged_runtime(self):
        for name in ('install_project_exe_broker.py','uninstall_project_exe_broker.py',
                     'resume_project_exe_broker.py','assemble_fixed_a06.py','source_guard_a05.py'):
            with self.subTest(entry=name):
                result=subprocess.run([sys.executable,'-B',str(ROOT/name),'--help'],capture_output=True,timeout=30)
                self.assertEqual(result.returncode,0,result.stderr.decode('utf-8',errors='replace'))
                self.assertIn(b'usage:',result.stdout)

if __name__=='__main__':unittest.main()
