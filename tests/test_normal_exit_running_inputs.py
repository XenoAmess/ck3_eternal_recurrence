"""Reproduce the settings rewrite before normal-exit _prepare reaches native I/O."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'ck3_autonomous_player/src')]
import xar_autoplayer.bridge as bridge
bridge.__path__.insert(0,str(ROOT/'ck3_autonomous_player/src/xar_autoplayer/bridge'))
from xar_autoplayer.bridge import normal_exit_source_inventory_v1 as inventory_module
from xar_autoplayer.bridge.normal_exit_source_inventory_v1 import verify_source_inventory_v1,STOCK_GUI_PATHS
from xar_autoplayer.bridge.runtime_input_contract_v1 import identity
from xar_autoplayer.bridge import normal_exit_map_driver_v1 as map_driver
from xar_autoplayer.bridge.driver import UnsupportedStepError
from build_normal_exit_source_inventory_v1 import build_inventory


class RunningNormalExitTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        root=Path(self.temp.name);self.state=root/'state';self.userdir=self.state/'profile';self.userdir.mkdir(parents=True)
        self.live=root/'live';self.live.mkdir();game=root/'game';game.mkdir()
        exe=root/'ck3.exe';exe.write_bytes(b'fake exact executable')
        self.settings=self.userdir/'pdx_settings.txt';self.settings.write_bytes(b'launch settings')
        self.dlc=self.userdir/'dlc_load.json';self.dlc.write_text('{"enabled_mods":[]}')
        for relative in STOCK_GUI_PATHS:
            path=game/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(relative.encode())
        self.profile={'schema_version':1,'guard_profile':str(root/'guard.json'),'guard_profile_sha256':'d'*64,
            'userdir':str(self.userdir),'evidence_directory':str(self.live),'game_version':'offline-fixture',
            'state_directory':str(self.state),'dll':{'path':str(root/'dll'),'sha256':'e'*64},'injector':{'path':str(root/'injector'),'sha256':'f'*64},
            'guard':{'target':{'executable':str(exe),'executable_sha256':hashlib.sha256(exe.read_bytes()).hexdigest()}}}
        inventory,_=build_inventory(self.profile,game)
        path=self.userdir/'normal-exit-source-inventory-v1.json';path.write_text(json.dumps(inventory))
        self.reference={'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
        self.profile['normal_exit_source_inventory']=self.reference
        snapshot=self.live/'input-snapshots/profile/pdx_settings.txt';snapshot.parent.mkdir(parents=True);snapshot.write_bytes(self.settings.read_bytes());self.snapshot=snapshot
        self.frozen={'run_id':'fixture','state_dir':str(self.state),'files':{str(path.resolve()):{key:identity(path)[key] for key in ('bytes','sha256')} for path in (self.settings,snapshot,self.dlc)}}
        freeze=self.live/'frozen-argv.json';freeze.write_text(json.dumps(self.frozen))
        (self.live/'ready-context.json').write_text(json.dumps({'run_id':'fixture','run_dir':str(self.live),'frozen_argv':identity(freeze)}))
    def test_actual_rewrite_rejected_prelaunch_but_running_passes(self):
        self.settings.write_bytes(b'game normalized settings')
        with self.assertRaisesRegex(ValueError,'actual source bytes changed'):verify_source_inventory_v1(self.reference,self.profile)
        result=verify_source_inventory_v1(self.reference,self.profile,input_phase='running')
        self.assertTrue(result['runtime_settings_observation']['settings']['bytes_changed'])
        self.assertEqual(self.snapshot.read_bytes(),b'launch settings')
    def test_snapshot_and_dlc_remain_strict(self):
        self.settings.write_bytes(b'game normalized settings')
        self.snapshot.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'snapshot'):verify_source_inventory_v1(self.reference,self.profile,input_phase='running')
        self.snapshot.write_bytes(b'launch settings');self.dlc.write_text('{"enabled_mods":[],"changed":true}')
        with self.assertRaisesRegex(ValueError,'Immutable'):verify_source_inventory_v1(self.reference,self.profile,input_phase='running')
    def test_missing_allocation_cannot_authorize_mutable_settings(self):
        (self.live/'ready-context.json').unlink()
        with self.assertRaises(OSError):verify_source_inventory_v1(self.reference,self.profile,input_phase='running')
    def test_real_prepare_gets_past_source_validation_before_snapshot(self):
        self.settings.write_bytes(b'game normalized settings')
        class ReachedSnapshot(Exception):pass
        def snapshot():raise ReachedSnapshot('source validation finished; no native or process call')
        driver=SimpleNamespace(capabilities=lambda:{'bridge_capabilities':['normal-exit-map-v1']},normal_exit_managed_profile=self.profile,take_snapshot=snapshot)
        with self.assertRaises(ReachedSnapshot):map_driver._prepare(driver,1)
    def test_inventory_settings_pin_must_equal_original_allocated_pin(self):
        self.frozen['files'][str(self.settings.resolve())]['sha256']='0'*64
        path=self.live/'frozen-argv.json';path.write_text(json.dumps(self.frozen))
        (self.live/'ready-context.json').write_text(json.dumps({'run_id':'fixture','run_dir':str(self.live),'frozen_argv':identity(path)}))
        with self.assertRaisesRegex(ValueError,'original allocated launch pin'):verify_source_inventory_v1(self.reference,self.profile,input_phase='running')


if __name__=='__main__':unittest.main()
