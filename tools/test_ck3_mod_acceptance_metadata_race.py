"""One focused regression for the actual metadata-open disappearance path."""
import types
import unittest
from unittest.mock import Mock
import ck3_mod_acceptance_metadata_race as race


class MetadataRace(unittest.TestCase):
    def test_confirmed_missing_open_only_and_fail_closed_otherwise(self):
        native = types.SimpleNamespace(K=types.SimpleNamespace(CreateFileW=Mock(return_value=-1)),
                                       W=types.SimpleNamespace(HANDLE=lambda value: types.SimpleNamespace(value=value)))
        diagnostics = {'confirmed_vanished_entries': 0, 'examples': []}
        missing = FileNotFoundError('enumerated file disappeared')
        missing.winerror = 2
        gone = Mock(side_effect=FileNotFoundError('confirmed absent'))
        self.assertIsNone(race.open_metadata('scene/volatile.json', native, diagnostics,
                                            gone, lambda: missing))
        native.K.CreateFileW.assert_called_once_with('scene/volatile.json', 0, 7, None, 3, 0x00200080, None)
        self.assertEqual(diagnostics['confirmed_vanished_entries'], 1)
        self.assertEqual(diagnostics['examples'][0]['stage'], 'CreateFileW')
        with self.assertRaisesRegex(RuntimeError, 'present entry.*scene/volatile.json'):
            race.open_metadata('scene/volatile.json', native, diagnostics, Mock(), lambda: missing)
        denied = PermissionError('denied'); denied.winerror = 5
        with self.assertRaisesRegex(RuntimeError, 'Metadata open failed'):
            race.open_metadata('scene/volatile.json', native, diagnostics, gone, lambda: denied)
        entry = types.SimpleNamespace(path='scene/volatile.json', stat=Mock(side_effect=missing))
        self.assertIsNone(race.entry_stat(entry, diagnostics, gone))
        with self.assertRaisesRegex(RuntimeError, 'absence check failed'):
            race.entry_stat(entry, diagnostics, Mock(side_effect=PermissionError('denied')))
        self.assertEqual(diagnostics['confirmed_vanished_entries'], 2)


if __name__ == '__main__':
    unittest.main()
