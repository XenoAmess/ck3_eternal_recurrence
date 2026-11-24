"""Controlled Saved fixture structure only; no CK3 or business emulation."""
from pathlib import Path
import tempfile
import unittest

import prepare_lyd_vanilla_feedback_fixture as lyd
from extract_auto_upgrade_buildings import Block, parse_clausewitz
from test_prepare_ccc_lyd_saved_entries import ActorInput, IDENTITY, child, entry, eligible


def scalar(body, key):
    values = [e.value for e in body.entries if e.key == key]
    if len(values) != 1 or not isinstance(values[0], str):
        raise AssertionError((key, values))
    return values[0]


def walk(body):
    for e in body.entries:
        yield e
        if isinstance(e.value, Block):
            yield from walk(e.value)


class ControlledLydSavedPrerequisitesTests(unittest.TestCase):
    def test_funded_option_is_strict_and_saved_only_before_output_creation(self):
        with tempfile.TemporaryDirectory() as tmp:
            for index, bad in enumerate((None, 0, 1, 'true')):
                out = Path(tmp) / str(index)
                with self.assertRaisesRegex(ValueError, 'strict boolean'):
                    lyd.generate(out, IDENTITY, True, funded_known_tenets=bad)
                self.assertFalse(out.exists())
            out = Path(tmp) / 'not-saved'
            with self.assertRaisesRegex(ValueError, 'explicit Saved'):
                lyd.generate(out, IDENTITY, False, funded_known_tenets=True)
            self.assertFalse(out.exists())

    def test_default_newgame_and_default_saved_receive_no_controlled_resources(self):
        self.assertNotIn('add_gold', lyd.SETUP)
        ordinary = lyd.saved_entry_files()['common/scripted_guis/lyd_feedback_saved_entry_guis.txt']
        self.assertNotIn('add_gold', ordinary)
        self.assertNotIn('add_known_tenet', ordinary)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'default'
            receipt = lyd.generate(out, IDENTITY)
            self.assertNotIn('controlled_prerequisites', receipt)
            self.assertEqual((out / 'common/on_action/lyd_feedback_setup.txt').read_bytes(), lyd.SETUP.encode('utf-8-sig'))

    def test_controlled_payload_is_self_only_once_and_only_knows_two_exact_tenets(self):
        text = lyd.saved_entry_files(funded_known_tenets=True)['common/scripted_guis/lyd_feedback_saved_entry_guis.txt']
        shown, executed, dispatch = entry(text, 'lyd_feedback_saved_entry_gui')
        self.assertEqual(shown, executed)
        self.assertEqual(scalar(dispatch, 'add_gold'), '1000')
        self.assertEqual(scalar(dispatch, 'add_piety'), '1000')
        self.assertEqual(scalar(dispatch, 'add_stress'), '90')
        learned = [e.value for e in dispatch.entries if e.key == 'if' and any(x.key == 'add_known_tenet' for x in e.value.entries)]
        self.assertEqual(len(learned), 2)
        keys = ['lyd_tenet_reverent_heaven', 'lyd_tenet_knowing_acting_support']
        for branch, key in zip(learned, keys):
            self.assertEqual(scalar(child(child(branch, 'limit'), 'NOT'), 'knows_tenet'), key)
            self.assertEqual(scalar(branch, 'add_known_tenet'), key)
        for flag in ('lyd_feedback_saved_entry_dispatched', 'lyd_feedback_setup_done'):
            self.assertFalse(eligible(shown, ActorInput(flags={flag}), ActorInput('han_8052', True)))
        forbidden = {'set_personal_tenet', 'force_set_personal_tenet', 'set_character_faith', 'set_main_rite', 'set_religious_head_title', 'trigger_event', 'create_character'}
        self.assertFalse({e.key for e in walk(dispatch)} & forbidden)
        self.assertEqual([e.value for e in walk(dispatch) if e.key == 'set_character_rite'], ['rite:jingxue'])
        self.assertIn(lyd.SAVED_PREDICATE_OBSERVATIONS, text)

    def test_receipt_discloses_new_prerequisites_and_never_claims_learning_or_business(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'funded'
            receipt = lyd.generate(out, IDENTITY, True, funded_known_tenets=True)
            self.assertFalse(receipt['business_pass'])
            data = receipt['controlled_prerequisites']
            self.assertFalse(data['learning_decision_or_knowledge_acquisition_validated'])
            self.assertFalse(data['personal_adoption_or_payment_or_cooldown_or_business_flags_written'])
            self.assertEqual(data['gold_delta'], 1000)
            self.assertEqual(data['piety_delta'], 1000)
            self.assertEqual(data['stress_delta'], 90)
            self.assertEqual(set(p.relative_to(out).as_posix() for p in out.rglob('*') if p.is_file()),
                {'descriptor.mod', 'setup-receipt.json', *lyd.saved_entry_files(funded_known_tenets=True)})


if __name__ == '__main__':
    unittest.main()
