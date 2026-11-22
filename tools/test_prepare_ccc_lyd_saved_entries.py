"""Portable fixture entry tests; no Game, SDK or product-business emulation."""
from __future__ import annotations

import codecs
from dataclasses import dataclass, field, replace
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import fixture_engine_prepare as prep
import prepare_xccc_1_20_fixture as ccc
import prepare_lyd_vanilla_feedback_fixture as lyd
from extract_auto_upgrade_buildings import Block, parse_clausewitz

ROOT = Path(prep.__file__).resolve().parents[1]
IDENTITY = {'game_version': '1.21.0.3', 'steam_build_id': '26785313',
            'exe_sha256': '859f0d380098adcb130eb9d453458222749fcdf6d46126ad0ed99d78f9a0aa28'}


def child(parent: Block, key: str) -> Block:
    values = [item.value for item in parent.entries if item.key == key]
    if len(values) != 1 or not isinstance(values[0], Block):
        raise AssertionError(f'Expected one block {key}')
    return values[0]


def entry(source: str, key: str) -> tuple[Block, Block, Block]:
    gui = child(parse_clausewitz(source), key)
    dispatch = child(child(gui, 'effect'), 'if')
    return child(gui, 'is_shown'), child(dispatch, 'limit'), dispatch


@dataclass
class ActorInput:
    history: str = '1128'
    ai: bool = False
    alive: bool = True
    flags: set[str] = field(default_factory=set)


def eligible(guard: Block, actor: ActorInput, song: ActorInput, date: str = '1066.9.15') -> bool:
    """Evaluate the declared input guards only; unknown syntax is a failure."""
    for item in guard.entries:
        key, value = item.key, item.value
        if item.operator != '=':
            raise AssertionError(item)
        if key == 'NOT' and isinstance(value, Block):
            ok = not eligible(value, actor, song, date)
        elif key == 'character:han_8052' and isinstance(value, Block):
            ok = eligible(value, song, song, date)
        elif key == 'this':
            ok = value == 'character:' + actor.history
        elif key == 'is_ai':
            ok = value == ('yes' if actor.ai else 'no')
        elif key == 'is_alive':
            ok = value == ('yes' if actor.alive else 'no')
        elif key == 'has_character_flag':
            ok = value in actor.flags
        elif key == 'current_date':
            ok = value == date
        else:
            raise AssertionError(f'Unrecognized Saved guard: {item}')
        if not ok:
            return False
    return True


class SavedEntryTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix='ccc-lyd-saved-entry-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        mocked = patch.object(prep, 'engine_identity', return_value=IDENTITY)
        mocked.start()
        self.addCleanup(mocked.stop)

    def test_default_entry_files_and_metadata_stay_original(self) -> None:
        out = self.root / 'ccc-default'
        ccc_receipt = ccc.prepare(ROOT, out)
        self.assertNotIn('saved_entry', ccc_receipt)
        self.assertEqual((out / 'common/on_action/xca120_on_actions.txt').read_bytes(), ccc.ON_ACTION.encode('utf-8-sig'))
        self.assertNotIn('saved_entry', lyd.generate(self.root / 'lyd-default', IDENTITY))
        self.assertEqual((self.root / 'lyd-default/common/on_action/lyd_feedback_setup.txt').read_bytes(), lyd.SETUP.encode('utf-8-sig'))
        self.assertEqual((self.root / 'lyd-default/descriptor.mod').read_bytes(),
                         b'\xef\xbb\xbfname="LYD original Confucian feedback setup"\nversion="1"\nsupported_version="1.20.*"\n')

    def test_ccc_saved_changes_only_bootstrap_not_original_effect_or_event(self) -> None:
        before, after = self.root / 'ccc-before', self.root / 'ccc-after'
        old = ccc.prepare(ROOT, before)
        new = ccc.prepare(ROOT, after, True)
        a = {p.relative_to(before).as_posix(): p.read_bytes() for p in before.rglob('*') if p.is_file()}
        b = {p.relative_to(after).as_posix(): p.read_bytes() for p in after.rglob('*') if p.is_file()}
        self.assertEqual(a.keys() - b.keys(), {'common/on_action/xca120_on_actions.txt'})
        self.assertEqual(b.keys() - a.keys(), ccc.saved_entry_files().keys())
        for name in a.keys() & b.keys():
            self.assertEqual(a[name], b[name], name)
        for key in ('required_markers', 'production_decision_effect', 'real_choice', 'ui_not_executed_by_fixture', 'marker_policy'):
            self.assertEqual(old[key], new[key], key)
        _, _, dispatch = entry(ccc.saved_entry_files()['common/scripted_guis/xca120_saved_entry_guis.txt'], 'xca120_saved_entry_gui')
        original = child(child(child(parse_clausewitz(ccc.ON_ACTION), 'xca120_start'), 'effect'), 'random_player')
        self.assertEqual(dispatch.entries[3:], original.entries)

    def test_lyd_saved_keeps_exact_original_self_setup_and_zero_day_scope(self) -> None:
        out = self.root / 'lyd-saved'
        receipt = lyd.generate(out, IDENTITY, True)
        self.assertFalse((out / 'common/on_action/lyd_feedback_setup.txt').exists())
        _, _, dispatch = entry(lyd.saved_entry_files()['common/scripted_guis/lyd_feedback_saved_entry_guis.txt'], 'lyd_feedback_saved_entry_gui')
        original = child(child(child(parse_clausewitz(lyd.SETUP), 'lyd_feedback_setup'), 'effect'), 'random_player')
        self.assertEqual(dispatch.entries[2:], original.entries)
        self.assertEqual(receipt['setup_changes'], ['self character rite to original jingxue', 'self idempotence flag'])
        self.assertFalse(receipt['business_pass'])
        self.assertFalse(receipt['faith_main_rite_or_NPC_or_title_changes'])
        self.assertIn('supported_version="1.21.0.3"', (out / 'descriptor.mod').read_text(encoding='utf-8-sig'))
        self.assertEqual(set(p.relative_to(out).as_posix() for p in out.rglob('*') if p.is_file()),
                         {'descriptor.mod', 'setup-receipt.json', *lyd.saved_entry_files().keys()})

    def test_duplicate_guards_reject_wrong_source_or_consumed_once(self) -> None:
        actor, song = ActorInput(), ActorInput('han_8052', True)
        for module, prefix, flags in ((ccc, 'xca120', ('xca_fixture_initialized', 'xca_initialize_pending')),
                                       (lyd, 'lyd_feedback', ('lyd_feedback_setup_done',))):
            files = module.saved_entry_files()
            shown, executed, dispatch = entry(files[f'common/scripted_guis/{prefix}_saved_entry_guis.txt'], prefix + '_saved_entry_gui')
            self.assertEqual(shown, executed)
            self.assertTrue(eligible(shown, actor, song))
            for changed in (replace(actor, history='36423'), replace(actor, ai=True), replace(actor, alive=False),
                            replace(actor, flags={prefix + '_saved_entry_dispatched'}),
                            *(replace(actor, flags={name}) for name in flags)):
                self.assertFalse(eligible(shown, changed, song))
                self.assertFalse(eligible(executed, changed, song))
            self.assertFalse(eligible(shown, actor, song, '1066.9.16'))
            self.assertEqual(dispatch.entries[1].key, 'add_character_flag')
            if module is ccc:
                self.assertEqual(dispatch.entries[2].key, 'character:han_8052')
                self.assertFalse(eligible(executed, actor, replace(song, flags={'xca120_saved_entry_dispatched'})))
            for path, source in files.items():
                parse_clausewitz(source)
                self.assertTrue((source.encode('utf-8-sig')).startswith(codecs.BOM_UTF8))
                if path.endswith('.gui'):
                    self.assertEqual(source.count('GuiScope.SetRoot( GetPlayer.MakeScope ).End'), 2)

    def test_strict_flag_bad_descriptor_identity_and_existing_output_refuse(self) -> None:
        for value in (None, 0, 1, 'true'):
            output = self.root / ('invalid-' + str(value))
            with self.assertRaisesRegex(ValueError, 'strict boolean'):
                ccc.prepare(ROOT, output, value)  # type: ignore[arg-type]
            with self.assertRaisesRegex(ValueError, 'strict boolean'):
                lyd.generate(output, IDENTITY, value)  # type: ignore[arg-type]
            self.assertFalse(output.exists())
        for value in ('', '1.21.0.3"\npath="unexpected', 'Florin'):
            output = self.root / ('invalid-version-' + str(len(value)))
            with self.assertRaisesRegex(ValueError, 'exact numeric'):
                lyd.generate(output, {'game_version': value}, True)
            self.assertFalse(output.exists())
        for module in (ccc, lyd):
            output = self.root / ('consumed-' + module.__name__)
            if module is ccc:
                ccc.prepare(ROOT, output, True)
            else:
                lyd.generate(output, IDENTITY, True)
            before = {p: p.read_bytes() for p in output.rglob('*') if p.is_file()}
            with self.assertRaises(ValueError):
                if module is ccc:
                    ccc.prepare(ROOT, output, True)
                else:
                    lyd.generate(output, IDENTITY, True)
            self.assertEqual(before, {p: p.read_bytes() for p in output.rglob('*') if p.is_file()})

    def test_widget_root_and_scripted_gui_references_are_exact_and_transparent(self) -> None:
        for module, prefix in ((ccc, 'xca120'), (lyd, 'lyd_feedback')):
            files = module.saved_entry_files()
            gui = files[f'gui/{prefix}_saved_entry_bridge.gui']
            key = prefix + '_saved_entry_gui'
            self.assertEqual(gui.count("GetScriptedGui('" + key + "')"), 2)
            self.assertIn(key + ' = {', files[f'common/scripted_guis/{prefix}_saved_entry_guis.txt'])
            self.assertIn('size = { 1 1 }', gui)
            self.assertIn('alwaystransparent = yes', gui)
            self.assertEqual(files[f'gui/scripted_widgets/{prefix}_saved_entry_widgets.txt'],
                             f'gui/{prefix}_saved_entry_bridge.gui = {prefix}_saved_entry_bridge_window\n')


if __name__ == '__main__':
    unittest.main()
