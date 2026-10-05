from __future__ import annotations

import copy
from dataclasses import FrozenInstanceError
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))

from xar_autoplayer.bridge.battle_control_contract import (
    QUERY_BATTLE_CONTROL_SNAPSHOT_V1_CAPABILITY,
    query_battle_control_snapshot_v1_step,
)
from xar_autoplayer.bridge.battle_transition_contract import (
    QUERY_BATTLE_TRANSITION_V1_CAPABILITY,
    query_battle_transition_v1_step,
)
from xar_autoplayer.bridge.battle_retained_geometry import (
    EXACT_EXECUTABLE_SHA256, EXACT_GAME_VERSION,
)
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.simulation.battle_retained_constructor_geometry import (
    adapt_retained_constructor_geometry,
)

FIXTURES = ROOT / 'tests/fixtures/battle_retained_geometry'


def load_fixture(name):
    return json.loads((FIXTURES / name).read_bytes())


class OfflineProducerDriver:
    """Fake transport for portable compiled production fixture bytes."""
    def __init__(self, frame, *, game_version=EXACT_GAME_VERSION):
        self.frame = frame
        self.game_version = game_version
        self.control = frame['contract_stage'] == 'production_exact_ongoing_combat'
        self.step = (
            query_battle_control_snapshot_v1_step(frame['subject_public_cunit_id'])
            if self.control else query_battle_transition_v1_step(frame['combat_id'])
        )

    def capabilities(self):
        return {
            'format_version': 1, 'backend_id': 'retained-geometry-offline',
            'source': 'named-pipe', 'snapshot': True, 'wait_for_change': False,
            'action_steps': [self.step],
            'bridge_capabilities': [QUERY_BATTLE_CONTROL_SNAPSHOT_V1_CAPABILITY if self.control
                                    else QUERY_BATTLE_TRANSITION_V1_CAPABILITY],
        }

    def take_snapshot(self):
        return {
            'format_version': 1, 'snapshot_id': 'retained-geometry-offline:4',
            'revision': 4, 'native_revision': self.frame['snapshot_revision'],
            'source': 'named-pipe', 'backend_id': 'retained-geometry-offline',
            'date_raw': self.frame['observed_date_raw'], 'paused': True,
            'episode_run_id': 'offline-fixture',
            'diagnostics': {'hello': {'game_version': self.game_version,
                                      'executable_sha256': EXACT_EXECUTABLE_SHA256}},
        }

    def execute_step(self, step, *, expected_revision=None):
        if step != self.step or expected_revision != 4:
            raise RuntimeError('service changed offline query binding')
        output = {
            'step': step, 'accepted': True, 'status': self.frame['status'],
            'query_sequence': 1, 'snapshot_revision': self.frame['snapshot_revision'],
            'backend_id': 'retained-geometry-offline',
            ('battle_control_snapshot' if self.control else 'battle_transition_snapshot'): copy.deepcopy(self.frame),
        }
        mirrors = (
            ('selected_public_cunit_id', 'selected_native_carmy_id', 'selected_owner_character_id',
             'combat_province_id', 'side_index', 'side_scope',
             'affected_public_cunit_ids_in_stored_order', 'unaffected_same_side_public_cunit_ids_in_stored_order',
             'side_flags', 'legality') if self.control else
            ('combat_id', 'province_id', 'phase', 'phase_raw', 'phase_day', 'winner_side', 'winner_raw',
             'forced_winner_side', 'forced_winner_raw', 'finalized', 'battle_result_id',
             'attacker_public_cunit_ids_in_stored_order', 'defender_public_cunit_ids_in_stored_order',
             'battle_transition_ready', 'current_observation', 'actual_geography_v1')
        )
        for key in mirrors:
            if key in self.frame:
                output[key] = copy.deepcopy(self.frame[key])
        return output

    def wait_for_change(self, *args, **kwargs):
        raise RuntimeError('read-only fixture must not advance')


def service_query(frame, **driver_options):
    driver = OfflineProducerDriver(frame, **driver_options)
    service = GameplayBridgeService(driver)
    return (
        service.query_battle_control_snapshot_v1(frame['subject_public_cunit_id'], expected_revision=4)
        if driver.control else service.query_battle_transition_v1(frame['combat_id'], expected_revision=4)
    )


class RetainedConstructorGeometryTests(unittest.TestCase):
    def test_compiled_foreign_zero_false_has_actual_roles_and_no_invented_origin(self):
        frame = load_fixture('foreign-available.json')
        original = copy.deepcopy(frame)
        result = service_query(frame)
        diagnostic = result['retained_constructor_geometry_v1']
        operands = adapt_retained_constructor_geometry(diagnostic)
        self.assertTrue(diagnostic['retained_geometry_ready'])
        self.assertEqual(operands.crossing_kind, 'none')
        self.assertFalse(operands.holding_defender)
        self.assertEqual(operands.terrain_width_multiplier_raw, 0)
        self.assertEqual(operands.sides[0].public_cunit_ids_in_stored_order, (251658381, 473, 474))
        self.assertEqual(operands.sides[1].public_cunit_ids_in_stored_order, (50331920, 83886484))
        self.assertIsNone(operands.sides[1].primary_participant_character_id)
        self.assertNotIn('primary_participant_character_id', diagnostic['actual_sides_in_stored_order'][1])
        self.assertNotIn('attacker_entry_province_id', diagnostic)
        self.assertNotIn('initiator_is_defender', diagnostic)
        self.assertFalse(diagnostic['complete_constructor_ready'])
        self.assertFalse(diagnostic['future_contact_preview'])
        self.assertFalse(diagnostic['constructor_rule_plan']['holding_defender']['enabled'])
        self.assertEqual(operands.combat_id, frame['combat_id'])
        self.assertEqual(frame, original)
        with self.assertRaises(FrozenInstanceError):
            operands.holding_defender = True

    def test_supported_nonzero_kinds_and_retained_holding_choose_closed_rule_slots(self):
        expected = {1: ('strait', 0xF78, 0xFA8), 2: ('river', 0xF80, 0xFB0),
                    3: ('large_river', 0xF88, 0xFB8)}
        for kind, (crossing, attacker_slot, defender_slot) in expected.items():
            for holding in (False, True):
                with self.subTest(kind=kind, holding=holding):
                    frame = load_fixture('owned-available.json')
                    frame['actual_geography_v1']['constructor_adjacency_kind_raw'] = kind
                    frame['actual_geography_v1']['holding_defender'] = holding
                    diagnostic = service_query(frame)['retained_constructor_geometry_v1']
                    operands = adapt_retained_constructor_geometry(diagnostic)
                    self.assertTrue(diagnostic['retained_geometry_ready'])
                    self.assertEqual(operands.constructor_adjacency_kind_raw, kind)
                    self.assertEqual(operands.crossing_kind, crossing)
                    self.assertEqual(operands.holding_defender, holding)
                    self.assertEqual(operands.holding_source, 'retained_combat_6FE')
                    self.assertEqual(operands.terrain_width_multiplier_raw, -123456)
                    self.assertEqual(operands.attacker_adjacency_rules_pointer_offset, attacker_slot)
                    self.assertEqual(operands.defender_adjacency_rules_pointer_offset, defender_slot)
                    self.assertEqual(operands.holding_defender_rules_pointer_offset, 0xF10)
                    self.assertEqual(operands.sides[1].primary_participant_character_id, 16777218)
                    self.assertEqual(diagnostic['constructor_rule_plan']['holding_defender']['enabled'], holding)
                    self.assertFalse(diagnostic['constructor_rule_plan']['effect_values_observed'])

    def test_partial_inputs_keep_actual_readiness_and_retained_raw(self):
        for variant in ('terrain', 'holding', 'kind', 'unsupported_kind', 'build'):
            with self.subTest(variant=variant):
                frame = load_fixture('foreign-unavailable.json' if variant == 'terrain' else 'foreign-available.json')
                options = {}
                if variant in ('holding', 'kind'):
                    frame['actual_geography_v1']['holding_defender' if variant == 'holding'
                                                else 'constructor_adjacency_kind_raw'] = None
                elif variant == 'unsupported_kind':
                    frame['actual_geography_v1']['constructor_adjacency_kind_raw'] = 7
                elif variant == 'build':
                    options['game_version'] = '1.19.0.6'
                result = service_query(frame, **options)
                diagnostic = result['retained_constructor_geometry_v1']
                self.assertTrue(result['battle_transition_ready'])
                self.assertFalse(diagnostic['retained_geometry_ready'])
                self.assertIsNone(adapt_retained_constructor_geometry(diagnostic))
                self.assertEqual(diagnostic['constructor_adjacency_kind_raw'],
                                 frame['actual_geography_v1']['constructor_adjacency_kind_raw'])
                self.assertEqual(diagnostic['holding_defender'], frame['actual_geography_v1']['holding_defender'])
                self.assertTrue(diagnostic['missing_inputs'])

    def test_old_absent_leaf_keeps_existing_service_shape(self):
        frame = load_fixture('foreign-available.json')
        del frame['actual_geography_v1']
        result = service_query(frame)
        self.assertNotIn('retained_constructor_geometry_v1', result)
        self.assertTrue(result['battle_transition_ready'])


if __name__ == '__main__':
    unittest.main()
