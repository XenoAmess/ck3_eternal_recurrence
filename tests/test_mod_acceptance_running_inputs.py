"""Normal runtime settings must not invalidate retained launch snapshots."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import ck3_mod_acceptance_launcher as launcher
from ck3_mod_acceptance_runtime_inputs import identity


class RunningInputTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        root=Path(self.temp.name);self.live=root/'live';self.live.mkdir()
        self.profile=root/'state/profile';self.profile.mkdir(parents=True)
        self.settings=self.profile/'pdx_settings.txt';self.settings.write_text('launch settings')
        self.snapshot=self.live/'input-snapshots/profile/pdx_settings.txt';self.snapshot.parent.mkdir(parents=True);self.snapshot.write_bytes(self.settings.read_bytes())
        self.mod=self.profile/'mod-content/fixture.txt';self.mod.parent.mkdir();self.mod.write_text('immutable mod')
        host=root/'host.py';host.write_text('# fixture; not executed')
        manifest=root/'runtime.json';manifest.write_text('{}')
        paths=[self.settings,self.snapshot,self.mod,host,manifest]+[ROOT/'tools'/name for name in
            ('ck3_mod_acceptance_launcher.py','ck3_mod_acceptance_keeper.py','ck3_mod_acceptance_queue.py','ck3_mod_acceptance_runtime_inputs.py')]
        paths.append(ROOT/'ck3_autonomous_player/src/xar_autoplayer/bridge/runtime_input_contract_v1.py')
        frozen={'run_id':'portable-fixture','argv':['python',str(host),'--agent-source-root','fixture'],
                'launch_requires_fresh_owned_cas_and_offline_direct_review':True,'previous_session_closed':True,'previous_screen_released':True,
                'state_dir':str(self.profile.parent),'runtime_manifest':identity(manifest),
                'files':{str(path.resolve()):{key:identity(path)[key] for key in ('bytes','sha256')} for path in paths}}
        path=self.live/'frozen-argv.json';path.write_text(json.dumps(frozen))
        (self.live/'ready-context.json').write_text(json.dumps({'run_id':frozen['run_id'],'run_dir':str(self.live),'frozen_argv':identity(path)}))
    def test_launch_mode_still_rejects_changed_settings(self):
        self.settings.write_text('game normalized settings')
        with self.assertRaisesRegex(ValueError,'Pinned input changed'):launcher.frozen_run(self.live)
    def test_running_mode_observes_settings_and_preserves_snapshot(self):
        original=self.snapshot.read_bytes();self.settings.write_text('game normalized settings')
        frozen,_=launcher.frozen_run(self.live,input_phase='running')
        self.assertTrue(frozen['_runtime_input_observation']['mutable_profile_observations'][0]['bytes_changed'])
        self.assertEqual(self.snapshot.read_bytes(),original)
    def test_running_mode_rejects_mod_change(self):
        self.mod.write_text('changed')
        with self.assertRaisesRegex(ValueError,'Immutable'):launcher.frozen_run(self.live,input_phase='running')
    def test_running_mode_rejects_snapshot_change(self):
        self.snapshot.write_text('changed')
        with self.assertRaisesRegex(ValueError,'snapshot'):launcher.frozen_run(self.live,input_phase='running')
    def test_unknown_input_phase_rejected(self):
        with self.assertRaisesRegex(ValueError,'Unknown frozen input phase'):launcher.frozen_run(self.live,input_phase='anything')


if __name__=='__main__':unittest.main()
