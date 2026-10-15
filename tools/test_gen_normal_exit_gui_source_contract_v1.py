"""Focused offline tests for generated native GUI dependency data."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import gen_normal_exit_gui_source_contract_v1 as generator


class GuiContractGeneratorTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / 'game'
        for relative in generator.STOCK_GUI_PATHS:
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text('', encoding='utf-8')
        sources = {
            'gui/hud.gui': 'root = { name = "timeline_widget" alpha = {} }',
            'gui/frontend_ingame_menu.gui': 'root = { name = "ingame_pausemenu" }',
            'gui/window_resign_confirmation.gui':
                'root = { name = "ingame_resign_confirmation" }',
            'gui/shared/first.gui': 'type Alpha = widget { beta = {} }',
            'gui/shared/second.gui': 'template Beta { widget = {} }',
            'gui/shared/duplicate.gui': 'type Alpha = widget { gamma = {} }',
            'gui/shared/third.gui': 'type Gamma = widget {}',
            'gui/shared/unrelated.gui': 'type unrelated = widget {}',
        }
        for relative, content in sources.items():
            (self.root / relative).write_text(content, encoding='utf-8')

    def test_transitive_duplicate_providers_and_exact_source_pins(self):
        data = generator.collect_gui_data(self.root)
        self.assertEqual(data['protected_gui_symbols'], ['alpha', 'beta', 'gamma'])
        dependencies = data['stock_gui_dependencies']
        self.assertEqual([row['relative_path'] for row in dependencies], [
            'gui/shared/duplicate.gui', 'gui/shared/first.gui',
            'gui/shared/second.gui', 'gui/shared/third.gui'])
        for row in data['stock_gui'] + dependencies:
            content = (self.root / row['relative_path']).read_bytes()
            self.assertEqual(row['bytes'], len(content))
            self.assertEqual(row['sha256'], hashlib.sha256(content).hexdigest())
            self.assertNotIn(str(self.root), json.dumps(row))

    def test_missing_fixed_root_is_rejected(self):
        (self.root / 'gui/hud.gui').write_text('root = {}', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'not uniquely source-bound'):
            generator.collect_gui_data(self.root)

    def test_wrong_executable_build_is_rejected(self):
        executable = self.root.parent / 'binaries' / 'ck3.exe'
        executable.parent.mkdir()
        executable.write_bytes(b'another build')
        with self.assertRaisesRegex(ValueError, 'not the supported CK3'):
            generator.build_contract(self.root)

    def test_header_is_deterministic_lowercase_data_without_gui_bodies(self):
        contract = {'game_version': generator.GAME_VERSION,
                    'executable_sha256': generator.EXECUTABLE_SHA256,
                    **generator.collect_gui_data(self.root)}
        header = generator.render_header(contract)
        self.assertEqual(header, generator.render_header(json.loads(json.dumps(contract))))
        self.assertIn('std::array<NormalExitGuiStockDependencyV1, 4>', header)
        self.assertIn('std::array<std::string_view, 3> kNormalExitProtectedGuiSymbolsV1', header)
        self.assertNotIn('type Alpha', header)
        self.assertNotIn(str(self.root), header)
        self.assertNotIn('\r', header)
        contract['protected_gui_symbols'].append('Alpha')
        with self.assertRaisesRegex(ValueError, 'unique, lower-case and sorted'):
            generator.render_header(contract)

    def test_committed_contract_and_header_have_matching_exact_build_data(self):
        base = generator.REPOSITORY / 'ck3_autonomous_player' / 'native_bridge'
        contract = json.loads((base / 'research/fixtures/normal_exit_gui_source_contract_12004.json')
                              .read_text(encoding='utf-8'))
        header = (base / 'include/xar_bridge/normal_exit_gui_source_contract_v1.hpp').read_bytes()
        self.assertEqual(contract['schema'], generator.SCHEMA)
        self.assertEqual(contract['game_version'], generator.GAME_VERSION)
        self.assertEqual(contract['executable_sha256'], generator.EXECUTABLE_SHA256)
        self.assertEqual([len(contract[key]) for key in [
            'stock_gui', 'stock_gui_dependencies', 'protected_gui_symbols',
            'protected_gui_paths', 'fixed_gui_roots']], [6, 12, 99, 18, 3])
        self.assertEqual(header, generator.render_header(contract).encode('utf-8'))
        self.assertEqual(set(contract['protected_gui_paths']), {
            row['relative_path'] for row in contract['stock_gui']
            + contract['stock_gui_dependencies']})


if __name__ == '__main__':
    unittest.main()
