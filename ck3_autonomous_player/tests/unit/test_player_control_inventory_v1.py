"""Inventory policy fixtures are synthetic files, never CK3 source ABI proof."""
from pathlib import Path
import hashlib
import json
import sys
import tempfile
import unittest

TOOLS=Path(__file__).resolve().parents[3]/'tools'
if str(TOOLS) not in sys.path: sys.path.insert(0,str(TOOLS))
from build_player_control_source_inventory_v1 import build_inventory
from xar_autoplayer.bridge.player_control_source_inventory_v1 import (
    INVENTORY_BASENAME,STOCK_GUI_PATHS,IMPLEMENTATION_PATHS,canonical_profile_projection,verify_source_inventory_v1,
)


class InventoryTests(unittest.TestCase):
    def fixture(self,root):
        user=root/'userdir';user.mkdir(); game=root/'game';game.mkdir(); implementation=root/'implementation';implementation.mkdir()
        exe=root/'fixture.exe';exe.write_bytes(b'SYNTHETIC OFFLINE EXECUTABLE FIXTURE')
        (user/'pdx_settings.txt').write_bytes(b'fixture settings');(user/'dlc_load.json').write_text('{"enabled_mods":[]}')
        for directory,relatives in [(game,STOCK_GUI_PATHS),(implementation,IMPLEMENTATION_PATHS)]:
            for relative in relatives:
                p=directory/relative;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'OFFLINE SYNTHETIC SOURCE '+relative.encode())
        profile={'schema_version':1,'guard_profile':str(root/'guard.json'),'guard_profile_sha256':'d'*64,
                 'userdir':str(user),'evidence_directory':str(root/'evidence'),'game_version':'1.20.0.3',
                 'state_directory':str(root/'state'),'dll':{'path':str(root/'dll'),'sha256':'e'*64},
                 'injector':{'path':str(root/'injector'),'sha256':'f'*64},
                 'guard':{'target':{'executable':str(exe),'executable_sha256':hashlib.sha256(exe.read_bytes()).hexdigest()}}}
        inventory,projection=build_inventory(profile,game,implementation)
        path=user/INVENTORY_BASENAME;path.write_text(json.dumps(inventory,separators=(',',':')))
        reference={'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
        return profile,reference,inventory,implementation,game
    def test_builder_inventory_and_opt_in_profile_projection_match_exact_file_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            profile,reference,inventory,implementation,game=self.fixture(Path(temp))
            projection=canonical_profile_projection(profile);profile['player_control_source_inventory']=reference
            self.assertEqual(canonical_profile_projection(profile),projection)
            verified=verify_source_inventory_v1(reference,profile)
            self.assertTrue(verified['static_sources_verified']);self.assertEqual(verified['stock_gui_count'],8)
            self.assertIn('gui/multiplayer_types.gui',STOCK_GUI_PATHS);self.assertIn('gui/multiplayer_lobby.gui',STOCK_GUI_PATHS)
    def test_code_stock_source_profile_and_missing_allowlist_entries_each_fail_closed(self):
        for mode in ('code','stock','profile','missing','reordered'):
            with tempfile.TemporaryDirectory() as temp:
                profile,reference,inventory,implementation,game=self.fixture(Path(temp))
                if mode=='code':(implementation/IMPLEMENTATION_PATHS[-1]).write_bytes(b'changed native production gate')
                elif mode=='stock':(game/'gui/multiplayer_types.gui').write_bytes(b'changed stock chooser')
                elif mode=='profile':profile['state_directory']=str(Path(temp)/'replacement-state')
                elif mode=='missing':inventory['implementation_sources'].pop()
                else:inventory['implementation_sources'].reverse()
                if mode in ('missing','reordered'):
                    Path(reference['path']).write_text(json.dumps(inventory));reference['sha256']=hashlib.sha256(Path(reference['path']).read_bytes()).hexdigest()
                with self.subTest(mode=mode),self.assertRaises(ValueError):verify_source_inventory_v1(reference,profile)
    def test_inventory_reference_cannot_select_an_arbitrary_file_or_old_exit_inventory(self):
        with tempfile.TemporaryDirectory() as temp:
            profile,reference,*_=self.fixture(Path(temp));reference['path']=str(Path(temp)/'normal-exit-source-inventory-v1.json')
            with self.assertRaises(ValueError):verify_source_inventory_v1(reference,profile)


if __name__=='__main__':unittest.main()
