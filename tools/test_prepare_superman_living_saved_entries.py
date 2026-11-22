"""Saved entry input/default/once boundaries only; never engine/business credit."""
from __future__ import annotations

import ast
from dataclasses import dataclass, field, replace
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any, Callable, cast
import unittest

import fixture_engine_prepare as shared
from extract_auto_upgrade_buildings import Block, parse_clausewitz

HERE = Path(__file__).resolve().parent
REPO = Path(shared.__file__).resolve().parents[1]
HEALTH = HERE.parent / 'mod_superman_qiang/tools/prepare_health_fixture.py'
LIVING = HERE.parent / 'mod_living_artifacts/tools/prepare_fixture.py'
sys.path.insert(0, str(REPO / 'mod_living_artifacts/tools'))
spec = importlib.util.spec_from_file_location('_saved_living_producer_under_test', LIVING)
if spec is None or spec.loader is None:
    raise ImportError('Actual Living source required')
living = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = living
spec.loader.exec_module(living)


def health_files() -> dict[str, str]:
    """Load only the pure new renderer, not the top-level CLI/setup generator."""
    tree = ast.parse(HEALTH.read_text(encoding='utf8'))
    nodes: list[ast.stmt] = [n for n in tree.body if (isinstance(n, ast.FunctionDef) and n.name == 'saved_entry_files')
             or (isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'SAVED_GUARD' for t in n.targets))]
    if len(nodes) != 2:
        raise AssertionError('Expected the real guard and renderer')
    namespace: dict[str, object] = {}
    exec(compile(ast.Module(nodes, []), str(HEALTH), 'exec'), namespace)
    return cast(Callable[[], dict[str, str]], namespace['saved_entry_files'])()


def child(parent: Block, key: str) -> Block:
    values = [e.value for e in parent.entries if e.key == key]
    if len(values) != 1 or not isinstance(values[0], Block):
        raise AssertionError(key)
    return values[0]


def guards(source: str, key: str) -> tuple[Block, Block, Block]:
    gui = child(parse_clausewitz(source), key)
    body = child(child(gui, 'effect'), 'if')
    return child(gui, 'is_shown'), child(body, 'limit'), body


@dataclass
class SourceInputs:
    history: str = '1128'
    ai: bool = False
    alive: bool = True
    date: str = '1066.9.15'
    flags: set[str] = field(default_factory=set)
    variables: set[str] = field(default_factory=set)


def eligible(block: Block, source: SourceInputs) -> bool:
    for item in block.entries:
        key, value = item.key, item.value
        if item.operator != '=':
            raise AssertionError(item)
        if key == 'NOT' and isinstance(value, Block):
            ok = not eligible(value, source)
        elif key == 'this':
            ok = value == 'character:' + source.history
        elif key == 'is_ai':
            ok = value == ('yes' if source.ai else 'no')
        elif key == 'is_alive':
            ok = value == ('yes' if source.alive else 'no')
        elif key == 'current_date':
            ok = value == source.date
        elif key == 'has_variable':
            ok = value in source.variables
        elif key == 'has_character_flag':
            ok = value in source.flags
        else:
            raise AssertionError(f'Unknown entry predicate: {item}')
        if not ok:
            return False
    return True


class SavedEntryTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix='health-living-saved-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def health(self, name: str, *flags: str) -> tuple[Path, dict[str, Any], subprocess.CompletedProcess[bytes]]:
        output = self.root / name
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1',
                   PYTHONPATH=os.pathsep.join((str(HEALTH.parent), str(REPO / 'mod_superman_qiang/tools'), str(REPO / 'tools'))))
        result = subprocess.run([sys.executable, '-B', '-X', 'utf8', str(HEALTH), '--output', str(output), *flags],
                                env=env, capture_output=True)
        manifest = json.loads(output.with_suffix('.fixture.json').read_text(encoding='utf8')) if result.returncode == 0 else {}
        return output, manifest, result

    def test_health_saved_preserves_twenty_cases_all_events_and_original_day_one(self) -> None:
        before, old, first = self.health('health-default')
        after, new, second = self.health('health-saved', '--saved-entry-bridge')
        self.assertEqual((first.returncode, second.returncode), (0, 0), second.stderr)
        old_files = {p.relative_to(before).as_posix(): p.read_bytes() for p in before.rglob('*') if p.is_file()}
        new_files = {p.relative_to(after).as_posix(): p.read_bytes() for p in after.rglob('*') if p.is_file()}
        self.assertEqual(old_files.keys() - new_files.keys(), {'common/on_action/sxat_on_actions.txt'})
        self.assertEqual(new_files.keys() - old_files.keys(), health_files().keys())
        for name in old_files.keys() & new_files.keys():
            self.assertEqual(old_files[name], new_files[name], name)
        for key in old.keys() - {'fixture_root', 'files'}:
            self.assertEqual(old[key], new[key], key)
        self.assertEqual(new['case_count'], 20)
        self.assertEqual(len(new['expected_pass_markers']), 20)
        self.assertEqual(new['total_calendar_days_to_result'], 3)
        _, _, dispatch = guards(health_files()['common/scripted_guis/sxat_health_saved_entry_guis.txt'], 'sxat_health_saved_entry_gui')
        original = child(child(child(parse_clausewitz(old_files['common/on_action/sxat_on_actions.txt'].decode('utf-8-sig')),
                                     'sxat_health_start'), 'effect'), 'every_player')
        self.assertEqual(dispatch.entries[2:], original.entries)

    def test_living_saved_preserves_original_initial_inputs_and_no_feeding(self) -> None:
        before, after = self.root / 'living-default', self.root / 'living-saved'
        old = living.emit_fixture(before)
        new = living.emit_fixture(after, saved_entry_bridge=True)
        self.assertNotIn('saved_entry', old)
        a = {p.relative_to(before).as_posix(): p.read_bytes() for p in before.rglob('*') if p.is_file()}
        b = {p.relative_to(after).as_posix(): p.read_bytes() for p in after.rglob('*') if p.is_file()}
        self.assertEqual(a.keys() - b.keys(), {'common/on_action/xalw_fixture_bootstrap.txt'})
        self.assertEqual(b.keys() - a.keys(), living.saved_entry_files().keys())
        for name in a.keys() & b.keys():
            self.assertEqual(a[name], b[name], name)
        self.assertEqual(new['business_acceptance'], 'NOT_ASSESSED')
        self.assertFalse(new['game_started'])
        _, _, dispatch = guards(living.saved_entry_files()['common/scripted_guis/xalw_fixture_saved_entry_guis.txt'], 'xalw_fixture_saved_entry_gui')
        original = child(child(child(parse_clausewitz(a['common/on_action/xalw_fixture_bootstrap.txt'].decode('utf-8-sig')),
                                     'xalw_fixture_bootstrap'), 'effect'), 'every_player')
        self.assertEqual(dispatch.entries[2:], original.entries)

    def test_duplicate_guards_reject_changed_or_previously_started_source(self) -> None:
        specs = [(health_files(), 'sxat_health', ('sxat_health_baseline_ready', 'sxat_health_matrix_done',
                                                 'sxat_ref_receiver_player_native_health_75', 'sxat_ref_donor_player_native_health_75')),
                 (living.saved_entry_files(), 'xalw_fixture', ('xalw_fixture_target', 'xalw_fixture_initial_day'))]
        for files, prefix, variables in specs:
            shown, executed, dispatch = guards(files[f'common/scripted_guis/{prefix}_saved_entry_guis.txt'], prefix + '_saved_entry_gui')
            self.assertEqual(shown, executed)
            source = SourceInputs()
            self.assertTrue(eligible(shown, source))
            for bad in (replace(source, history='36423'), replace(source, ai=True), replace(source, alive=False),
                        replace(source, date='1066.9.16'), replace(source, flags={prefix + '_saved_entry_dispatched'}),
                        *(replace(source, variables={name}) for name in variables)):
                self.assertFalse(eligible(shown, bad))
                self.assertFalse(eligible(executed, bad))
            self.assertEqual(dispatch.entries[1].key, 'add_character_flag')

    def test_saved_argument_types_cli_bad_value_and_consumed_output_refuse(self) -> None:
        for value in (None, 0, 1, 'true'):
            output = self.root / ('bad-living-' + str(value))
            with self.assertRaises(ValueError):
                living.emit_fixture(output, saved_entry_bridge=value)
            self.assertFalse(output.exists())
        output, _, result = self.health('bad-health', '--saved-entry-bridge=true')
        self.assertEqual(result.returncode, 2)
        self.assertFalse(output.exists())
        output, _, result = self.health('used-health', '--saved-entry-bridge')
        self.assertEqual(result.returncode, 0)
        before = {p: p.read_bytes() for p in output.rglob('*') if p.is_file()}
        _, _, repeated = self.health('used-health', '--saved-entry-bridge')
        self.assertNotEqual(repeated.returncode, 0)
        self.assertEqual(before, {p: p.read_bytes() for p in output.rglob('*') if p.is_file()})
        output = self.root / 'used-living'
        living.emit_fixture(output, saved_entry_bridge=True)
        with self.assertRaises(ValueError):
            living.emit_fixture(output, saved_entry_bridge=True)

    def test_bridge_syntax_references_and_transparency(self) -> None:
        for files, prefix in ((health_files(), 'sxat_health'), (living.saved_entry_files(), 'xalw_fixture')):
            for value in files.values():
                parse_clausewitz(value)
            gui = files[f'gui/{prefix}_saved_entry_bridge.gui']
            self.assertEqual(gui.count('GuiScope.SetRoot( GetPlayer.MakeScope ).End'), 2)
            self.assertEqual(gui.count("GetScriptedGui('" + prefix + "_saved_entry_gui')"), 2)
            self.assertIn('size = { 1 1 }', gui)
            self.assertIn('alwaystransparent = yes', gui)
            self.assertEqual(files[f'gui/scripted_widgets/{prefix}_saved_entry_widgets.txt'],
                             f'gui/{prefix}_saved_entry_bridge.gui = {prefix}_saved_entry_bridge_window\n')

    def test_living_declared_imprint_remains_explicit_input_and_not_feeding_credit(self) -> None:
        imprint = living.InitialFeedingImprint('primary_armament', 90, 'fixture-initial-state', False)
        old = living.render_observer_effects(feeding_imprint=imprint)
        output = self.root / 'living-imprint'
        result = living.emit_fixture(output, feeding_imprint=imprint, saved_entry_bridge=True)
        self.assertEqual((output / 'common/scripted_effects/xalw_fixture_observer.txt').read_text(encoding='utf-8-sig'), old)
        self.assertEqual(result['business_acceptance'], 'NOT_ASSESSED')
        self.assertFalse(result['saved_entry']['business_or_feeding_credit'])


if __name__ == '__main__':
    unittest.main()
