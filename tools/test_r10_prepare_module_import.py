"""Cold-load the actual checkpoint library without a global PYTHONPATH change."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from ck3_mod_acceptance_cases import r10_prepare_adapter as adapter


class CheckpointLibraryImport(unittest.TestCase):
    def test_actual_bootstrap_siblings_and_path_restoration(self):
        repo = Path(__file__).resolve().parents[1]
        source = repo / 'promo/ck3_native_war_ai/episode-04-march-logistics/tools'
        original = list(sys.path)
        cold_path = [entry for entry in original if Path(entry or '.').resolve() != source]
        try:
            sys.path[:] = cold_path
            with patch.dict(sys.modules):
                for name in ('capture_runtime_evidence', 'capture_deadline'):
                    sys.modules.pop(name, None)
                bootstrap = adapter.module(source / 'capture_bootstrap.py', 'r10_actual_checkpoint_import_smoke')
                self.assertEqual(bootstrap.SCHEMA, 'xar.war-episode04.bootstrap.v1')
                self.assertTrue(callable(bootstrap.checkpoint_source))
                self.assertEqual(Path(sys.modules['capture_runtime_evidence'].__file__).resolve(),
                                 source / 'capture_runtime_evidence.py')
                self.assertEqual(sys.path, cold_path)
            with tempfile.TemporaryDirectory(prefix='r10-import-failure-') as directory:
                failure = Path(directory) / 'fail_after_path_insert.py'
                failure.write_text("raise ValueError('module execution failed')\n", encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'module execution failed'):
                    adapter.module(failure, 'r10_failed_module_import_smoke')
                self.assertEqual(sys.path, cold_path)
        finally:
            sys.path[:] = original


if __name__ == '__main__':
    unittest.main()
