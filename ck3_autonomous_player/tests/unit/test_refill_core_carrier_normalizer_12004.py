"""New carrier wire checks through the real full-family normalizer only."""
from copy import deepcopy
import importlib.util
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
REPO = Path(os.environ.get('CK3_R06_BASE_REPO', str(ROOT)))
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO/'ck3_autonomous_player/src'))
PACKAGE = 'xar_autoplayer.bridge.'
NAMES = ('army_observed_phase_contract_12004', 'army_observed_core_validation_12004')


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# Import only the existing fixture factory; no legacy TestCase is executed.
factory = load('carrier_core_fixture_factory', REPO/'ck3_autonomous_player/tests/unit/test_army_subject_physical_coverage_12004.py')
from xar_autoplayer.bridge.army_observed_phase_contract_12004 import normalize_army_observed_phase_family_12004 as legacy_normalize
from xar_autoplayer.bridge.army_observed_phase_consumption_12004 import project_army_observed_phases_12004 as project

CORE, SUBJECT = factory.CORE, factory.SUBJECT
LEGACY = factory.family()
LEGACY_NORMALIZED = legacy_normalize(CORE, LEGACY, expected_carmy_id=SUBJECT)
LEGACY_PROJECTED = project({'army_id': 901, 'native_carmy_id': SUBJECT, CORE: LEGACY_NORMALIZED}, exact_source=True)

for name in reversed(NAMES):
    module = load(PACKAGE+name, REPO/'ck3_autonomous_player/src/xar_autoplayer/bridge'/f'{name}.py')
normalize = sys.modules[PACKAGE+NAMES[0]].normalize_army_observed_phase_family_12004

EXT = {'native_core_invocation_token': (1 << 63)+23, 'parent_invocation_token': None,
       'core_invocation_nesting_depth': 1, 'core_carrier_published': True,
       'core_carrier_source_epoch': 20261018}


def extended(**changes):
    value = deepcopy(LEGACY)
    value['events'][0].update({**EXT, **changes})
    return value


def consume(value):
    normalized = normalize(CORE, value, expected_carmy_id=SUBJECT)
    return normalized, project({'army_id': 901, 'native_carmy_id': SUBJECT, CORE: normalized}, exact_source=True)


class CarrierCoreNormalizerTests(unittest.TestCase):
    def test_all_five_keys_preserved_in_detached_full_family(self):
        value = extended(); before = deepcopy(value)
        normalized, projected = consume(value)
        self.assertEqual(value, before)
        self.assertEqual(normalized, before)
        self.assertIsNot(normalized['events'][0], value['events'][0])
        for key in EXT: self.assertEqual(normalized['events'][0][key], EXT[key])
        self.assertEqual(projected, LEGACY_PROJECTED)

    def test_legacy_normalization_and_projection_remain_exact(self):
        normalized, projected = consume(deepcopy(LEGACY))
        self.assertEqual(normalized, LEGACY_NORMALIZED)
        self.assertEqual(projected, LEGACY_PROJECTED)
        self.assertFalse(set(EXT) & set(normalized['events'][0]))

    def test_partial_extension_and_unknown_extra_rejected(self):
        for key in EXT:
            value = extended(); value['events'][0].pop(key)
            with self.subTest(missing=key), self.assertRaises(ValueError): consume(value)
        for value in (deepcopy(LEGACY), extended()):
            value['events'][0]['unknown_carrier_field'] = 1
            with self.assertRaises(ValueError): consume(value)

    def test_types_and_widths_reject_bool_as_integer_and_integer_as_bool(self):
        bad = [('native_core_invocation_token', True), ('parent_invocation_token', True),
               ('core_invocation_nesting_depth', True), ('core_carrier_source_epoch', True),
               ('core_carrier_published', 1), ('native_core_invocation_token', -1),
               ('native_core_invocation_token', 1 << 64), ('parent_invocation_token', 1 << 64),
               ('core_invocation_nesting_depth', 1 << 32), ('core_carrier_source_epoch', 1 << 64)]
        for key, value in bad:
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                consume(extended(**{key: value}))

    def test_publication_epoch_is_exact_and_unpublished_epoch_zero(self):
        for change in ({'core_carrier_source_epoch': 0}, {'core_carrier_source_epoch': 20261019},
                       {'core_carrier_published': False}):
            with self.subTest(change=change), self.assertRaises(ValueError): consume(extended(**change))
        normalized, projected = consume(extended(core_carrier_published=False, core_carrier_source_epoch=0))
        self.assertFalse(normalized['events'][0]['core_carrier_published'])
        self.assertEqual(projected, LEGACY_PROJECTED)

    def test_published_zero_token_or_depth_rejected_and_exhaustion_retained(self):
        for change in ({'native_core_invocation_token': 0}, {'core_invocation_nesting_depth': 0},
                       {'core_invocation_nesting_depth': 0, 'core_carrier_published': False,
                        'core_carrier_source_epoch': 0}):
            with self.subTest(change=change), self.assertRaises(ValueError): consume(extended(**change))
        for depth in (0, 1, 2):
            value = extended(native_core_invocation_token=0, core_invocation_nesting_depth=depth,
                             core_carrier_published=False, core_carrier_source_epoch=0)
            normalized, projected = consume(value)
            self.assertEqual(normalized, value)
            self.assertEqual(projected, LEGACY_PROJECTED)
            self.assertIsNone(normalized['events'][0]['parent_invocation_token'])

    def test_parent_relationships_rejected_and_valid_nested_literal_retained(self):
        for change in ({'parent_invocation_token': 7},
                       {'core_invocation_nesting_depth': 2},
                       {'core_invocation_nesting_depth': 2, 'parent_invocation_token': 0},
                       {'core_invocation_nesting_depth': 2, 'parent_invocation_token': EXT['native_core_invocation_token']}):
            with self.subTest(change=change), self.assertRaises(ValueError): consume(extended(**change))
        value = extended(core_invocation_nesting_depth=2, parent_invocation_token=19)
        self.assertEqual(consume(value)[0], value)
        exhausted = extended(native_core_invocation_token=0, core_invocation_nesting_depth=2,
                             parent_invocation_token=19, core_carrier_published=False, core_carrier_source_epoch=0)
        self.assertEqual(consume(exhausted)[0], exhausted)

    def test_published_carrier_cannot_waive_natural_entry_provenance(self):
        for key in ('original_called', 'entry_provenance_complete'):
            value = deepcopy(LEGACY); event = value['events'][0]
            event.update(original_returned=False, return_provenance_complete=False,
                         returned=factory.shape('CoreFrame'))
            event[key] = False
            # This retained partial legacy record is legal. Publication adds
            # its own stronger entry requirement without rewriting that record.
            self.assertEqual(consume(value)[0], value)
            event.update(EXT)
            with self.subTest(key=key), self.assertRaises(ValueError): consume(value)
        value = extended(); value['events'][0]['observed'] = False
        with self.assertRaises(ValueError): consume(value)

    def test_invocation_and_event_domains_are_not_inferred_or_promoted(self):
        value = extended(native_core_invocation_token=LEGACY['events'][0]['entry_event']['sequence'])
        normalized, projected = consume(value)
        self.assertEqual(normalized, value)
        self.assertIsNone(normalized['events'][0]['parent_invocation_token'])
        self.assertEqual(projected, LEGACY_PROJECTED)
        self.assertFalse(projected['full_monthly_ready'])
        qualification = projected['ordered_regular_core'][0]['refill_application_qualification_v1']
        self.assertFalse(qualification['actual_ADD_observed'])


if __name__ == '__main__': unittest.main()
