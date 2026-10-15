"""Source-bound support for GUI mods after the actual R0016 prelaunch refusal."""
from pathlib import Path
import hashlib
import importlib.util
import json
import tempfile
import unittest

from xar_autoplayer.bridge.normal_exit_source_inventory_v1 import STOCK_GUI_PATHS, verify_source_inventory_v1

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('_exit_gui_inventory_builder', ROOT/'tools/build_normal_exit_source_inventory_v1.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class NormalExitGuiSourcesTests(unittest.TestCase):
    def fixture(self, root, gui=b'types Religion {type religion_card=button_standard{}} window={name="faith_window" religion_card={}}', relative='gui/religion.gui'):
        userdir=root/'userdir'; userdir.mkdir(); game=root/'game'; game.mkdir()
        (userdir/'mod').mkdir(); mod=root/'mod'; mod.mkdir()
        (mod/'descriptor.mod').write_bytes(b'name="GUI fixture"')
        path=mod/relative; path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(gui)
        (userdir/'mod/example.mod').write_text('path="'+mod.as_posix()+'"',encoding='utf-8')
        (userdir/'pdx_settings.txt').write_bytes(b'fixture settings')
        (userdir/'dlc_load.json').write_text(json.dumps({'enabled_mods':['mod/example.mod']}),encoding='utf-8')
        contents={
            'gui/hud.gui':b'widget={name="timeline_widget" button_menu={name="pause_menu_button" onclick="[OnPauseMenu]"}}',
            'gui/frontend_ingame_menu.gui':b'window={name="ingame_pausemenu" exit_wrapper={}}',
            'gui/window_resign_confirmation.gui':b'window={name="ingame_resign_confirmation" button_standard={}}',
            'gui/shared/buttons.gui':b'types Buttons {type button_standard=button{} type button_menu=button{}}',
            'gui/shared/exit_helpers.gui':b'types Exit {type exit_wrapper=button_standard{using=Exit_Template}}',
            'gui/shared/exit_templates.gui':b'template Exit_Template {using=Exit_Background}',
            'gui/shared/exit_background.gui':b'template Exit_Background {alpha=1}',
        }
        for relative in set(STOCK_GUI_PATHS)|contents.keys():
            path=game/relative; path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(contents.get(relative,b''))
        executable=root/'ck3.exe'; executable.write_bytes(b'fixture exact build')
        profile={'schema_version':1,'guard_profile':str(root/'guard.json'),'guard_profile_sha256':'d'*64,
            'userdir':str(userdir),'evidence_directory':str(root/'evidence'),'game_version':'1.20.0.4',
            'state_directory':str(root/'state'),'dll':{'path':str(root/'dll'),'sha256':'e'*64},
            'injector':{'path':str(root/'injector'),'sha256':'f'*64},
            'guard':{'target':{'executable':str(executable),'executable_sha256':hashlib.sha256(executable.read_bytes()).hexdigest()}}}
        inventory,_=builder.build_inventory(profile,game)
        path=userdir/builder.INVENTORY_BASENAME
        path.write_bytes(json.dumps(inventory).encode('utf-8'))
        return profile,{'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()},inventory,game

    def test_unrelated_gui_uses_protected_widgets_without_overriding_their_definitions(self):
        with tempfile.TemporaryDirectory() as temporary:
            profile,reference,inventory,_=self.fixture(Path(temporary))
            self.assertEqual(len(inventory['stock_gui_dependencies']),3)
            self.assertTrue(verify_source_inventory_v1(reference,profile)['static_sources_verified'])

    def test_related_global_overrides_roots_callbacks_and_dependency_paths_stay_unsupported(self):
        cases=[(b'types Other {type button_standard=button{}}','gui/unrelated_name.gui'),
               (b'template Exit_Background {alpha=0}','gui/unrelated_name.gui'),
               (b'window={name="ingame_pausemenu"}','gui/unrelated_name.gui'),
               (b'window={onclick="[PauseMenu.ExitGame]"}','gui/unrelated_name.gui'),
               (b'window={onclick="[OnPauseMenu]"}','gui/unrelated_name.gui'),
               (b'window={name="different"}','gui/shared/exit_helpers.gui'),
               (b'window={name="different"}','gui/hud.gui')]
        for content,relative in cases:
            with self.subTest(content=content,relative=relative),tempfile.TemporaryDirectory() as temporary:
                profile,reference,_,_=self.fixture(Path(temporary),content,relative)
                with self.assertRaises(ValueError):verify_source_inventory_v1(reference,profile)

    def test_gui_dependency_bytes_are_bound_after_inventory_creation(self):
        with tempfile.TemporaryDirectory() as temporary:
            profile,reference,_,game=self.fixture(Path(temporary))
            (game/'gui/shared/exit_background.gui').write_bytes(b'template Exit_Background {alpha=0}')
            with self.assertRaisesRegex(ValueError,'actual source bytes changed'):
                verify_source_inventory_v1(reference,profile)

    def test_legacy_inventory_does_not_silently_admit_gui_without_dependency_sources(self):
        with tempfile.TemporaryDirectory() as temporary:
            profile,reference,inventory,_=self.fixture(Path(temporary))
            del inventory['stock_gui_dependencies']
            path=Path(reference['path']);path.write_bytes(json.dumps(inventory).encode('utf-8'))
            reference['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
            with self.assertRaisesRegex(ValueError,'requires a stock dependency source inventory'):
                verify_source_inventory_v1(reference,profile)


if __name__=='__main__': unittest.main()
