"""Saved fixture entry boundaries only; no engine or business emulation."""
from __future__ import annotations

import codecs
from contextlib import ExitStack
from dataclasses import dataclass, field, replace
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import fixture_engine_prepare as prep
import prepare_reclaim_the_motherland_1_20_fixture as rmtm
import prepare_tributary_expansion_1_20_fixture as ted
from extract_auto_upgrade_buildings import Block, parse_clausewitz

ROOT = Path(prep.__file__).resolve().parents[1]
ENGINE = {'game_version': '1.21.0.3', 'steam_build_id': '26785313',
          'exe_sha256': '859f0d380098adcb130eb9d453458222749fcdf6d46126ad0ed99d78f9a0aa28'}


def child(parent: Block, key: str) -> Block:
    values = [entry.value for entry in parent.entries if entry.key == key]
    if len(values) != 1 or not isinstance(values[0], Block):
        raise AssertionError(f'Expected one block {key}')
    return values[0]


def guards(source: str, key: str) -> tuple[Block, Block, Block]:
    gui = child(parse_clausewitz(source), key)
    shown = child(gui, 'is_shown')
    dispatch = child(child(gui, 'effect'), 'if')
    return shown, child(dispatch, 'limit'), dispatch


@dataclass
class ActorInput:
    history: str
    ai: bool = False
    alive: bool = True
    flags: set[str] = field(default_factory=set)
    titles: set[str] = field(default_factory=set)
    dynastic_situation: bool = False
    group: str | None = None


@dataclass
class SavedInputs:
    date: str = '1066.9.15'
    rules: set[str] = field(default_factory=lambda: {'rmtm_reclaim_the_motherland', 'rmtm_divided_hearts'})
    globals: set[str] = field(default_factory=set)
    song: ActorInput = field(default_factory=lambda: ActorInput('han_8052', True, titles={'title:h_china'},
                                                              dynastic_situation=True, group='hegemon_ruler'))


def eligible(guard: Block, actor: ActorInput, source: SavedInputs) -> bool:
    """Evaluate only declared entry-input predicates; unknown nodes fail closed."""
    for entry in guard.entries:
        key, value = entry.key, entry.value
        if entry.operator != '=':
            raise AssertionError(f'Unexpected entry operator: {entry}')
        if key == 'NOT' and isinstance(value, Block):
            ok = not eligible(value, actor, source)
        elif key == 'character:han_8052' and isinstance(value, Block):
            ok = eligible(value, source.song, source)
        elif key == 'any_character_situation' and isinstance(value, Block):
            ok = actor.dynastic_situation and len(value.entries) == 1 and value.entries[0].value == 'dynastic_cycle'
        elif key == 'top_participant_group:dynastic_cycle' and isinstance(value, Block):
            ok = actor.group is not None and eligible(value, actor, source)
        elif key == 'participant_group_type':
            ok = value == actor.group
        elif key == 'this':
            ok = value == 'character:' + actor.history
        elif key == 'is_ai':
            ok = value == ('yes' if actor.ai else 'no')
        elif key == 'is_alive':
            ok = value == ('yes' if actor.alive else 'no')
        elif key == 'current_date':
            ok = value == source.date
        elif key == 'has_character_flag':
            ok = value in actor.flags
        elif key == 'has_game_rule':
            ok = value in source.rules
        elif key == 'has_title':
            ok = value in actor.titles
        elif key == 'exists' and isinstance(value, str) and value.startswith('global_var:'):
            ok = value.removeprefix('global_var:') in source.globals
        elif key == 'exists' and value == 'top_participant_group:dynastic_cycle':
            ok = actor.group is not None
        else:
            raise AssertionError(f'Unsupported entry predicate: {entry}')
        if not ok:
            return False
    return True


class SavedProductEntryTests(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory(prefix='saved-product-entry-')
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        patches = ExitStack()
        patches.enter_context(patch.object(prep, 'engine_identity', return_value=ENGINE))
        patches.enter_context(patch.object(ted, 'engine_identity', return_value=ENGINE))
        patches.enter_context(patch.object(rmtm, 'project_stock_observers', return_value=('observed = {}\n', {'test_fixture_only': True})))
        self.addCleanup(patches.close)

    def test_ted_default_payload_is_original_for_both_modes(self) -> None:
        original = ROOT / 'tools/fixtures/tributary_expansion_directives_acceptance'
        for ui in (False, True):
            output = self.root / ('default-ui' if ui else 'default-core')
            receipt = ted.prepare(ROOT, output, ui)
            self.assertNotIn('saved_entry', receipt)
            for relative in ('descriptor.mod', 'common/scripted_effects/tea_effects.txt'):
                self.assertEqual((output / relative).read_bytes(), (original / relative).read_bytes())
            if ui:
                for path in (original / 'ui').rglob('*'):
                    if path.is_file():
                        self.assertEqual((output / path.relative_to(original / 'ui')).read_bytes(), path.read_bytes())
            else:
                self.assertEqual((output / 'common/on_action/tea120_on_actions.txt').read_bytes(), ted.START.encode('utf-8-sig'))
                self.assertEqual((output / 'events/tea120_events.txt').read_bytes(), ted.EVENTS.encode('utf-8-sig'))

    def test_ted_saved_payload_changes_entry_only_and_keeps_schedule(self) -> None:
        for ui in (False, True):
            before, after = self.root / f'old-{ui}', self.root / f'saved-{ui}'
            old = ted.prepare(ROOT, before, ui)
            new = ted.prepare(ROOT, after, ui, True)
            old_files = {p.relative_to(before).as_posix(): p.read_bytes() for p in before.rglob('*') if p.is_file()}
            new_files = {p.relative_to(after).as_posix(): p.read_bytes() for p in after.rglob('*') if p.is_file()}
            startup = 'common/on_action/teaui_on_actions.txt' if ui else 'common/on_action/tea120_on_actions.txt'
            self.assertEqual(old_files.keys() - new_files.keys(), {startup})
            self.assertEqual(new_files.keys() - old_files.keys(), ted.saved_entry_files(ui).keys())
            for name in old_files.keys() & new_files.keys():
                self.assertEqual(new_files[name], old_files[name], name)
            self.assertEqual(new['advance_game_days'], old['advance_game_days'])
            self.assertEqual(new['coverage'], old['coverage'])
            for name in ted.saved_entry_files(ui):
                self.assertTrue(new_files[name].startswith(codecs.BOM_UTF8))

    def test_both_actual_guards_reject_changed_source_and_preexisting_once(self) -> None:
        actor, source = ActorInput('1128'), SavedInputs()
        for module, key, leaf in ((ted, 'tea120_saved_entry_gui', 'tea120'), (rmtm, 'rqa120_saved_entry_gui', 'rqa120')):
            texts = ted.saved_entry_files(False) if module is ted else rmtm.saved_entry_files()
            shown, executed, dispatch = guards(texts[f'common/scripted_guis/{leaf}_saved_entry_guis.txt'], key)
            self.assertEqual(shown, executed)
            self.assertTrue(eligible(shown, actor, source))
            for changed in (replace(actor, history='han_8052'), replace(actor, ai=True), replace(actor, alive=False),
                            replace(actor, flags={leaf + '_saved_entry_dispatched'})):
                self.assertFalse(eligible(executed, changed, source))
            self.assertFalse(eligible(shown, actor, replace(source, date='1066.9.16')))
            self.assertFalse(eligible(shown, actor, replace(source, song=replace(source.song, flags={leaf + '_saved_entry_dispatched'}))))
            # A state change after IsShown must also fail the independent effect guard.
            self.assertFalse(eligible(executed, replace(actor, flags={leaf + '_saved_entry_dispatched'}), source))
            keys = [n.key for n in dispatch.entries]
            self.assertLess(keys.index('add_character_flag'), keys.index('character:han_8052'))

    def test_rmtm_requires_real_membership_and_loaded_rules(self) -> None:
        shown, executed, _ = guards(rmtm.saved_entry_files()['common/scripted_guis/rqa120_saved_entry_guis.txt'], 'rqa120_saved_entry_gui')
        actor, source = ActorInput('1128'), SavedInputs()
        for changed in (replace(source, rules={'rmtm_divided_hearts'}), replace(source, rules={'rmtm_reclaim_the_motherland'}),
                        replace(source, song=replace(source.song, dynastic_situation=False)),
                        replace(source, song=replace(source.song, group=None)),
                        replace(source, song=replace(source.song, group='ordinary_ruler')),
                        replace(source, globals={'rqa120_stock_join_dispatched'}),
                        replace(source, globals={'rqa120_stock_join_dispatch_armed'})):
            self.assertFalse(eligible(shown, actor, changed))
            self.assertFalse(eligible(executed, actor, changed))

    def test_rmtm_original_dispatch_body_driver_stock_and_predicates_remain_exact(self) -> None:
        old_root, new_root = self.root / 'rmtm-old', self.root / 'rmtm-saved'
        old = rmtm.prepare(ROOT, old_root, True, 10,
                           formal_product_dir=ROOT / 'mod_reclaim_the_motherland', focused_keypaths=True)
        new = rmtm.prepare(ROOT, new_root, True, 10, saved_entry_bridge=True,
                           formal_product_dir=ROOT / 'mod_reclaim_the_motherland', focused_keypaths=True)
        old_files = {p.relative_to(old_root).as_posix(): p.read_bytes() for p in old_root.rglob('*') if p.is_file()}
        new_files = {p.relative_to(new_root).as_posix(): p.read_bytes() for p in new_root.rglob('*') if p.is_file()}
        self.assertEqual(old_files.keys() - new_files.keys(), {'common/on_action/rqa120_on_actions.txt'})
        self.assertEqual(new_files.keys() - old_files.keys(), rmtm.saved_entry_files().keys())
        for name in old_files.keys() & new_files.keys():
            self.assertEqual(old_files[name], new_files[name], name)
        for key in ('required_markers', 'reject_markers', 'expected_game_days', 'max_game_days', 'game_rules', 'coverage'):
            self.assertEqual(old[key], new[key], key)
        _, _, dispatch = guards(rmtm.saved_entry_files()['common/scripted_guis/rqa120_saved_entry_guis.txt'], 'rqa120_saved_entry_gui')
        original = child(child(parse_clausewitz(rmtm.START), 'rqa120_start'), 'effect')
        self.assertEqual(dispatch.entries[3:], original.entries)
        for name in rmtm.saved_entry_files():
            self.assertTrue(new_files[name].startswith(codecs.BOM_UTF8))

    def test_nonboolean_saved_mode_and_consumed_output_refuse_before_new_writes(self) -> None:
        for value in (None, 0, 1, 'true'):
            out = self.root / ('bad-' + str(value))
            with self.assertRaisesRegex(ValueError, 'strict boolean'):
                ted.prepare(ROOT, out, saved_entry_bridge=value)  # type: ignore[arg-type]
            self.assertFalse(out.exists())
            with self.assertRaisesRegex(ValueError, 'strict boolean'):
                rmtm.prepare(ROOT, out, True, 10, saved_entry_bridge=value)  # type: ignore[arg-type]
            self.assertFalse(out.exists())
        out = self.root / 'consumed'
        ted.prepare(ROOT, out, saved_entry_bridge=True)
        before = {p: p.read_bytes() for p in out.rglob('*') if p.is_file()}
        with self.assertRaisesRegex(ValueError, 'new output'):
            ted.prepare(ROOT, out, saved_entry_bridge=True)
        self.assertEqual(before, {p: p.read_bytes() for p in out.rglob('*') if p.is_file()})


if __name__ == '__main__':
    unittest.main()
