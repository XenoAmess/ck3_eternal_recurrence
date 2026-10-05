"""Identity source allowlist security tests; no native process or callback credit."""
from pathlib import Path
import hashlib,json,sys,tempfile,unittest

import test_player_control_inventory_v1 as inventory_fixtures
from xar_autoplayer.bridge.player_control_source_inventory_v1 import IMPLEMENTATION_PATHS,verify_source_inventory_v1

IDENTITY_PATHS=(
 'ck3_autonomous_player/native_bridge/include/xar_bridge/player_control_identity_source_v1.hpp',
 'ck3_autonomous_player/native_bridge/src/player_control_identity_source_v1.cpp',
 'ck3_autonomous_player/native_bridge/src/player_control_identity_pins_v1.inc',
)


class IdentityInventoryTests(unittest.TestCase):
    def fixture(self,root):return inventory_fixtures.InventoryTests().fixture(root)
    def save(self,reference,inventory):
        path=Path(reference['path']);path.write_text(json.dumps(inventory,separators=(',',':')))
        reference['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    def test_three_actual_identity_source_paths_are_required_in_exact_order(self):
        self.assertEqual(IMPLEMENTATION_PATHS[14:17],IDENTITY_PATHS)
        self.assertEqual(len(IMPLEMENTATION_PATHS),20)
        with tempfile.TemporaryDirectory() as temp:
            profile,reference,inventory,implementation,game=self.fixture(Path(temp))
            result=verify_source_inventory_v1(reference,profile)
            self.assertTrue(result['static_sources_verified'])
            self.assertEqual([Path(row['path']).relative_to(implementation).as_posix()
                               for row in inventory['implementation_sources'][14:17]],list(IDENTITY_PATHS))
    def test_predecessor_inventory_and_each_missing_identity_file_are_refused(self):
        for missing in ('all',*IDENTITY_PATHS):
            with tempfile.TemporaryDirectory() as temp:
                profile,reference,inventory,*_=self.fixture(Path(temp))
                count=3 if missing=='all' else 1
                if missing=='all':inventory['implementation_sources']=[row for i,row in enumerate(inventory['implementation_sources']) if i not in range(14,17)]
                else:inventory['implementation_sources'].pop(IMPLEMENTATION_PATHS.index(missing))
                self.save(reference,inventory)
                with self.subTest(missing=missing),self.assertRaisesRegex(ValueError,'implementation source inventory is incomplete'):
                    verify_source_inventory_v1(reference,profile)
    def test_unknown_identity_source_alias_and_extra_entry_do_not_receive_source_credit(self):
        for mode in ('unknown','alias','extra'):
            with tempfile.TemporaryDirectory() as temp:
                profile,reference,inventory,implementation,_=self.fixture(Path(temp))
                if mode=='unknown':
                    path=implementation/'unknown-native-source.cpp';path.write_bytes(b'unknown source')
                    inventory['implementation_sources'][-1]={'path':str(path),'bytes':len(path.read_bytes()),
                        'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
                elif mode=='alias':inventory['implementation_sources'][-1]=dict(inventory['implementation_sources'][-2])
                else:inventory['implementation_sources'].append(dict(inventory['implementation_sources'][-1]))
                self.save(reference,inventory)
                with self.subTest(mode=mode),self.assertRaises(ValueError):verify_source_inventory_v1(reference,profile)
    def test_each_pinned_identity_source_byte_change_is_refused_even_with_unchanged_profile(self):
        for relative in IDENTITY_PATHS:
            with tempfile.TemporaryDirectory() as temp:
                profile,reference,inventory,implementation,_=self.fixture(Path(temp))
                (implementation/relative).write_bytes(b'changed actual controller / AI source bytes')
                with self.subTest(relative=relative),self.assertRaisesRegex(ValueError,'actual source bytes changed'):
                    verify_source_inventory_v1(reference,profile)


if __name__=='__main__':unittest.main()
