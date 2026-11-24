"""Initial private fixture input only; stock loss effects and live ADD remain unproven."""
from pathlib import Path
import hashlib
import tempfile
import unittest
import prepare_lyd_vanilla_feedback_fixture as lyd
from extract_auto_upgrade_buildings import Block, parse_clausewitz
from test_prepare_ccc_lyd_saved_entries import ActorInput, IDENTITY, child, entry, eligible

LEGACY_FUNDED_TEXT_SHA256 = {'common/scripted_guis/lyd_feedback_saved_entry_guis.txt': 'd5f60eae88793f019c19f76748a026590a193bdaffa1fcab86cc451f297014c7', 'gui/lyd_feedback_saved_entry_bridge.gui': '30d42e29d6272ebe2c37f12eee888b1e7bcf25a6349b75c08d140db690444d87', 'gui/scripted_widgets/lyd_feedback_saved_entry_widgets.txt': 'ec2242685820d563d287b437f77bd53a6726e20c1a8943f6bfa9d6c6069506bc'}

def scalar(body, key):
    values = [e.value for e in body.entries if e.key == key]
    if len(values) != 1 or not isinstance(values[0], str):
        raise AssertionError((key, values))
    return values[0]

def walk(body):
    for item in body.entries:
        yield item
        if isinstance(item.value, Block):
            yield from walk(item.value)

class ApostolicInitialSlotFixtureTests(unittest.TestCase):
    def test_strict_option_requires_explicit_funded_saved_before_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            for n, value in enumerate((None, 0, 1, 'true')):
                out = Path(tmp) / str(n)
                with self.assertRaisesRegex(ValueError, 'strict boolean'):
                    lyd.generate(out, IDENTITY, True, funded_known_tenets=True, clear_apostolic_personal_tenet=value)
                self.assertFalse(out.exists())
            for n, (saved, funded) in enumerate(((False, False), (False, True), (True, False))):
                out = Path(tmp) / ('missing-' + str(n))
                with self.assertRaisesRegex(ValueError, 'explicit controlled funded Saved'):
                    lyd.generate(out, IDENTITY, saved, funded_known_tenets=funded, clear_apostolic_personal_tenet=True)
                self.assertFalse(out.exists())

    def test_only_guarded_exact_apostolic_is_removed_with_original_once_scope(self):
        files = lyd.saved_entry_files(funded_known_tenets=True, clear_apostolic_personal_tenet=True)
        shown, executed, dispatch = entry(files['common/scripted_guis/lyd_feedback_saved_entry_guis.txt'], 'lyd_feedback_saved_entry_gui')
        self.assertEqual(shown, executed)
        branches = [e.value for e in dispatch.entries if e.key == 'if' and any(x.key == 'remove_personal_tenet' for x in e.value.entries)]
        self.assertEqual(len(branches), 1)
        self.assertEqual(scalar(child(branches[0], 'limit'), 'has_personal_tenet'), 'tenet_apostolic_succession')
        self.assertEqual(scalar(branches[0], 'remove_personal_tenet'), 'tenet_apostolic_succession')
        removed = [e.value for e in walk(dispatch) if e.key == 'remove_personal_tenet']
        self.assertEqual(removed, ['tenet_apostolic_succession'])
        for flag in ('lyd_feedback_saved_entry_dispatched', 'lyd_feedback_setup_done'):
            self.assertFalse(eligible(shown, ActorInput(flags={flag}), ActorInput('han_8052', True)))
        forbidden = {'set_personal_tenet', 'force_set_personal_tenet', 'add_personal_tenet_slot', 'clear_personal_tenets', 'remove_all_personal_tenets', 'set_stress', 'change_stress', 'remove_character_modifier', 'remove_secret'}
        self.assertFalse({e.key for e in walk(dispatch)} & forbidden)

    def test_false_preserves_exact_qualified_old_funded_text_and_stress90(self):
        actual = lyd.saved_entry_files(funded_known_tenets=True, clear_apostolic_personal_tenet=False)
        hashes = {path: hashlib.sha256(text.encode('utf-8')).hexdigest() for path, text in actual.items()}
        self.assertEqual(hashes, LEGACY_FUNDED_TEXT_SHA256)
        self.assertEqual(actual, lyd.saved_entry_files(funded_known_tenets=True))
        _, _, dispatch = entry(actual['common/scripted_guis/lyd_feedback_saved_entry_guis.txt'], 'lyd_feedback_saved_entry_gui')
        self.assertEqual(scalar(dispatch, 'add_stress'), '90')
        self.assertFalse([e for e in walk(dispatch) if e.key == 'remove_personal_tenet'])

    def test_true_omits_only_fixture_stress_and_discloses_native_loss_unknown(self):
        with tempfile.TemporaryDirectory() as tmp:
            receipt = lyd.generate(Path(tmp) / 'controlled', IDENTITY, True, funded_known_tenets=True, clear_apostolic_personal_tenet=True)
        self.assertFalse(receipt['business_pass'])
        self.assertEqual(receipt['controlled_prerequisites']['stress_delta'], 0)
        self.assertTrue(receipt['controlled_prerequisites']['fixture_stress_grant_omitted_stock_loss_stress_retained'])
        self.assertFalse(receipt['controlled_personal_slot']['native_available_slot_or_Can_or_ADD_proven'])
        self.assertTrue(receipt['controlled_personal_slot']['stock_loss_stress_fulfillment_modifier_secret_popularity_effects_not_suppressed'])
        text = lyd.saved_entry_files(funded_known_tenets=True, clear_apostolic_personal_tenet=True)['common/scripted_guis/lyd_feedback_saved_entry_guis.txt']
        _, _, dispatch = entry(text, 'lyd_feedback_saved_entry_gui')
        self.assertEqual(scalar(dispatch, 'add_gold'), '1000')
        self.assertEqual(scalar(dispatch, 'add_piety'), '1000')
        self.assertFalse([e for e in walk(dispatch) if e.key == 'add_stress'])
        self.assertEqual([e.value for e in walk(dispatch) if e.key == 'add_known_tenet'], ['lyd_tenet_reverent_heaven', 'lyd_tenet_knowing_acting_support'])

if __name__ == '__main__':
    unittest.main()
