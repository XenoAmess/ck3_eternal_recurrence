"""No game: GUI metadata permits no new native wire identity."""
from pathlib import Path
import hashlib
import json
import sys
import tempfile
import unittest

from ck3_gui_game_identity import identify_gui_game
import ck3_mod_acceptance_prepare as prepare

REPO = Path(__file__).resolve().parents[1]


class GuiGameIdentityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.game = self.root / 'steamapps/common/CK3'
        (self.game / 'binaries').mkdir(parents=True)
        (self.game / 'launcher').mkdir()
        (self.game / 'binaries/ck3.exe').write_bytes(b'synthetic GUI build without native qualification')
        self.settings = self.game / 'launcher/launcher-settings.json'
        self.settings.write_text(json.dumps({'rawVersion': '1.21.0', 'exePath': '../binaries/ck3.exe'}))
        self.manifest = self.root / 'steamapps/appmanifest_1158310.acf'
        self.manifest.write_text('"AppState" { "appid" "1158310" "buildid" "1234" "StateFlags" "4" }')
        self.expected = {'version': '1.21.0', 'steam_build_id': 1234,
                         'exe_sha256': hashlib.sha256((self.game / 'binaries/ck3.exe').read_bytes()).hexdigest()}

    def test_gui_cache_context_identifies_unregistered_build_without_native_admission(self):
        context = {'shared_source_root': str(REPO), 'game_dir': str(self.game),
                   'execution_mode': 'gui_only', 'shared_game': self.expected, 'case_inputs': {}}
        _, identity = prepare._engine(context)
        self.assertEqual(identity, {'game_version': '1.21.0', 'steam_build_id': '1234',
                                    'exe_sha256': self.expected['exe_sha256']})
        native = dict(context)
        native.pop('_selected_engine')
        native.pop('execution_mode')
        with self.assertRaisesRegex(ValueError, 'installed EXE differs'):
            prepare._engine(native)

    def test_executable_tamper_rejected(self):
        (self.game / 'binaries/ck3.exe').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'GUI metadata'):
            identify_gui_game(REPO, self.game, self.expected)

    def test_launcher_version_and_path_must_match(self):
        for value in ({'rawVersion': '1.20.0.4', 'exePath': '../binaries/ck3.exe'},
                      {'rawVersion': '1.21.0', 'exePath': '../binaries/other.exe'}):
            self.settings.write_text(json.dumps(value))
            with self.assertRaises(ValueError):
                identify_gui_game(REPO, self.game, self.expected)

    def test_steam_app_build_and_installed_state_must_match(self):
        for key, value in (('appid', '480'), ('buildid', '5678'), ('StateFlags', '6')):
            fields = {'appid': '1158310', 'buildid': '1234', 'StateFlags': '4'}
            fields[key] = value
            self.manifest.write_text('"AppState" { ' + ' '.join(f'"{k}" "{v}"' for k, v in fields.items()) + ' }')
            with self.assertRaisesRegex(ValueError, 'Steam build'):
                identify_gui_game(REPO, self.game, self.expected)

    def test_missing_manifest_and_unknown_expected_identity_rejected(self):
        self.manifest.unlink()
        with self.assertRaises(FileNotFoundError):
            identify_gui_game(REPO, self.game, self.expected)
        with self.assertRaises(ValueError):
            identify_gui_game(REPO, self.game, {})


if __name__ == '__main__':
    unittest.main()
