from __future__ import annotations
from copy import deepcopy
import json
import os
from pathlib import Path
import sys
from typing import Literal, NotRequired, TypeGuard, TypedDict
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
from xar_autoplayer.bridge.driver import CallbackGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.army_ordered_besieging_refill_contract import normalize_ordered_besieging_refill_inputs_v1


Status = Literal['available', 'partial', 'unavailable']


class PhysicalChunk(TypedDict):
    physical_index: int
    current_soldiers: int
    maximum_soldiers: int
    owner_persistent_regiment_id: int
    q_ordinal_raw: int
    army_regiment_id_raw: int
    exclusion_byte_14_raw: int
    state_raw: int
    context_unavailable_reason: str | None
    owner_resolved_full_id: int
    owner_guard_138_raw: int
    owner_definition_magic_38_raw: int
    origin_province_id: int
    origin_province_788_raw: int | None
    origin_province_73c_raw: int
    associated_arrg_resolved_full_id: int
    associated_arrg_magic_raw: int
    associated_army_raw_full_id: int
    associated_army_resolved_full_id: int
    army_byte_1d4_raw: int
    army_byte_1ec_raw: int
    native_army_in_combat: bool
    associated_unit_raw_full_id: int
    associated_unit_resolved_full_id: int
    unit_170_raw: int
    unit_position_province_magic_raw: int
    unit_position_owner_resolved_full_id: int
    unit_position_holder_resolved_full_id: int
    native_unit_position_eligible: bool


class ReplenishmentRecord(TypedDict):
    status: Status
    unavailable_reason: str | None
    record_index: int
    persistent_regiment_id: int
    chunk_index: int
    chunk_army_regiment_id: int
    current_soldiers: int
    maximum_soldiers: int
    effective_current_soldiers: int
    state_raw: int
    native_can_replenish: bool
    native_chunk_can_replenish: bool
    persistent_monthly_replenishment_fraction_raw: int
    persistent_monthly_replenishment_fraction_scale: int
    persistent_prepared_replenishment_fraction_raw: int
    persistent_prepared_replenishment_fraction_scale: int


class ReplenishmentRecords(TypedDict):
    source: Literal['native_all_data_records']
    army_regiment_id: int
    status: Status
    ready: bool
    native_data_record_count: int
    unavailable_reason: str | None
    native_loss_writer_skipped: bool
    loss_writer_admission_unavailable_reason: str | None
    records: list[ReplenishmentRecord]


class PersistentOccurrence(TypedDict):
    stored_index: int
    persistent_regiment_id: int


class PersistentRegiment(TypedDict):
    persistent_regiment_id: int
    prepared_fraction_raw: int
    unavailable_reason: str | None
    chunks: list[PhysicalChunk]


class ScopedOrderedRefill(TypedDict):
    source: Literal['native_scoped_observed_prepared_ordered_refill']
    status: Status
    unavailable_reason: str | None
    subject_army_id: int
    subject_carmy_id: int
    native_persistent_occurrence_count: int
    native_army_refresh_occurrence_count: int
    persistent_occurrences: list[PersistentOccurrence]
    army_refresh_occurrence_indices: list[int]
    persistent_regiments: list[PersistentRegiment]


class RegimentStrength(TypedDict):
    army_regiment_id: int
    current_soldiers: int
    maximum_soldiers: int
    scale: int


class BesiegingRegiment(TypedDict):
    stored_index: int
    army_regiment_id: int
    available: bool
    unavailable_reason: str
    current_soldiers: int
    maximum_soldiers: int
    replenishment_records_v1: ReplenishmentRecords | None


class BesiegingOccurrence(TypedDict):
    stored_index: int
    public_unit_id: int
    resolved_unit_id: int
    unit_used_fallback: bool
    current_province_id: int
    current_province_used_fallback: bool
    raw_unit18: int
    raw_unit170: int
    raw_unit44: int
    native_carmy_id: int
    army_used_fallback: bool
    eligible: bool
    available: bool
    unavailable_reason: str
    native_whole_current_soldiers: int
    regiments: list[BesiegingRegiment]


class AssaultContext(TypedDict):
    status: Status
    unavailable_reason: str
    has_active_siege: bool
    siege_id: int
    breach_level_raw: int
    casualty_percentage_count: int
    casualty_percentage_raw: int


class BesiegingContributors(TypedDict):
    status: Status
    unavailable_reason: str
    province_id: int
    native_province_unit_count: int
    native_besieging_strength: int
    contributors_ready: bool
    native_assault_expected_loss: int
    assault_context: AssaultContext
    occurrences: list[BesiegingOccurrence]


class RefreshRegiment(TypedDict):
    stored_index: int
    raw_army_regiment_id: int
    army_regiment_id: int


class RefreshOccurrence(TypedDict):
    manager_stored_index: int
    raw_carmy_id: int
    resolved_carmy_id: int
    army_used_fallback: bool
    native_regiment_occurrence_count: int
    regiments: list[RefreshRegiment]


class OrderedBesiegingInputs(TypedDict):
    source: Literal['native_ordered_besieging_refill_scope']
    status: Status
    unavailable_reason: str | None
    subject_army_id: int
    subject_carmy_id: int
    province_id: int
    refresh_membership_ready: bool
    native_persistent_occurrence_count: int
    native_army_refresh_occurrence_count: int
    target_army_regiment_ids: list[int]
    persistent_occurrences: list[PersistentOccurrence]
    persistent_regiments: list[PersistentRegiment]
    refresh_occurrences: list[RefreshOccurrence]


class ArmyStrengthRow(TypedDict):
    status: Status
    army_id: int
    native_carmy_id: int
    scope_role: Literal['player']
    war_ids: list[int]
    regiment_count: int
    current_soldiers: int
    maximum_soldiers: int
    ai_base_power_raw: int
    ai_base_power_scale: int
    unavailable_reason: str | None
    current_supply_change_monthly_raw: int
    current_supply_change_monthly_scale: int
    regiment_strengths: list[RegimentStrength]
    regiment_replenishment_records_v1: list[ReplenishmentRecords]
    scoped_ordered_refill_inputs_v1: ScopedOrderedRefill
    current_province_besieging_contributors_v1: NotRequired[BesiegingContributors]
    ordered_besieging_refill_inputs_v1: NotRequired[OrderedBesiegingInputs]


def _is_object_map(value: object) -> TypeGuard[dict[str, object]]:
    return isinstance(value, dict) and all(isinstance(key, str) for key in value)


def _object_map(value: object) -> dict[str, object]:
    """Validate the service's dynamic result boundary without changing identity."""
    if not _is_object_map(value):
        raise TypeError('expected an object with string keys')
    return value


def _is_array(value: object) -> TypeGuard[list[object]]:
    return isinstance(value, list)


def _array(value: object) -> list[object]:
    if not _is_array(value):
        raise TypeError('expected an array')
    return value


def _object_rows(value: object) -> list[dict[str, object]]:
    return [_object_map(item) for item in _array(value)]


def _at(value: object, *path: str | int) -> object:
    for part in path:
        value = _object_map(value)[part] if isinstance(part, str) else _array(value)[part]
    return value


def chunk(index: int) -> PhysicalChunk:
    return {
        'physical_index': index, 'current_soldiers': 80 if index == 0 else 20 if index == 1 else 0,
        'maximum_soldiers': 100 if index == 0 else 20 if index == 1 else 0,
        'owner_persistent_regiment_id': 50001, 'q_ordinal_raw': index,
        'army_regiment_id_raw': 11001 if index == 0 else -1,
        'exclusion_byte_14_raw': 0, 'state_raw': 0, 'context_unavailable_reason': None,
        'owner_resolved_full_id': 50001, 'owner_guard_138_raw': 0,
        'owner_definition_magic_38_raw': 0, 'origin_province_id': 1,
        'origin_province_788_raw': -1, 'origin_province_73c_raw': -1,
        'associated_arrg_resolved_full_id': 11001 if index == 0 else -1,
        'associated_arrg_magic_raw': 0x41725267, 'associated_army_raw_full_id': 12,
        'associated_army_resolved_full_id': 12, 'army_byte_1d4_raw': 0, 'army_byte_1ec_raw': 0,
        'native_army_in_combat': False, 'associated_unit_raw_full_id': 11,
        'associated_unit_resolved_full_id': 11, 'unit_170_raw': 0,
        'unit_position_province_magic_raw': 0x50726F76,
        'unit_position_owner_resolved_full_id': 777, 'unit_position_holder_resolved_full_id': 777,
        'native_unit_position_eligible': True,
    }


def row(fraction: int = 10000, current: int = 80, maximum: int = 100) -> ArmyStrengthRow:
    records: list[ReplenishmentRecord] = []
    for index in range(2):
        records.append({
            'status': 'available', 'unavailable_reason': None, 'record_index': index,
            'persistent_regiment_id': 50001, 'chunk_index': 0, 'chunk_army_regiment_id': 11001,
            'current_soldiers': current, 'maximum_soldiers': maximum,
            'effective_current_soldiers': current, 'state_raw': 0,
            'native_can_replenish': True, 'native_chunk_can_replenish': True,
            'persistent_monthly_replenishment_fraction_raw': 90000,
            'persistent_monthly_replenishment_fraction_scale': 100000,
            'persistent_prepared_replenishment_fraction_raw': fraction,
            'persistent_prepared_replenishment_fraction_scale': 100000,
        })
    chunks = [chunk(index) for index in range(7)]
    chunks[0]['current_soldiers'], chunks[0]['maximum_soldiers'] = current, maximum
    return {
        'status': 'available', 'army_id': 11, 'native_carmy_id': 12,
        'scope_role': 'player', 'war_ids': [], 'regiment_count': 1,
        'current_soldiers': 2 * current, 'maximum_soldiers': 2 * maximum,
        'ai_base_power_raw': 0, 'ai_base_power_scale': 100000, 'unavailable_reason': None,
        'current_supply_change_monthly_raw': 700000, 'current_supply_change_monthly_scale': 100000,
        'regiment_strengths': [{'army_regiment_id': 11001, 'current_soldiers': 2 * current,
                               'maximum_soldiers': 2 * maximum, 'scale': 1}],
        'regiment_replenishment_records_v1': [{
            'source': 'native_all_data_records', 'army_regiment_id': 11001, 'status': 'available',
            'ready': True, 'native_data_record_count': 2, 'unavailable_reason': None,
            'native_loss_writer_skipped': False, 'loss_writer_admission_unavailable_reason': None,
            'records': records}],
        'scoped_ordered_refill_inputs_v1': {
            'source': 'native_scoped_observed_prepared_ordered_refill', 'status': 'available',
            'unavailable_reason': None, 'subject_army_id': 11, 'subject_carmy_id': 12,
            'native_persistent_occurrence_count': 5, 'native_army_refresh_occurrence_count': 4,
            'persistent_occurrences': [{'stored_index': index, 'persistent_regiment_id': 50001} for index in (1, 3)],
            'army_refresh_occurrence_indices': [1, 3],
            'persistent_regiments': [{'persistent_regiment_id': 50001, 'prepared_fraction_raw': fraction,
                                     'unavailable_reason': None, 'chunks': chunks}],
        },
    }


class MemoryRoute(GameplayBridgeService):
    def __init__(self, source: ArmyStrengthRow) -> None:
        self.source = source
        self.calls: list[tuple[str, int | None]] = []
        self.driver = CallbackGameplayDriver(
            backend_id="pure-memory-fixture", snapshot=self.snapshot,
            execute=lambda step, revision: self.execute_step(
                step, expected_revision=revision),
            action_steps=("query-army-strengths-v1",),
        )

    def snapshot(self, *, include_native_command_history: bool = True) -> dict[str, object]:
        return {'paused': True, 'revision': 42, 'native_revision': 7, 'date_raw': 10000,
                'snapshot_id': 'offline-ordered-B-assault', 'backend_id': 'pure-memory-fixture',
                'player_armies': [{'army_id': 11}], 'active_wars': [],
                'diagnostics': {'hello': {'game_version': '1.20.0.3'}}}

    def capabilities(self) -> dict[str, object]:
        return {'action_steps': ['query-army-strengths-v1']}

    def execute_step(
        self, step: str, *, expected_revision: int | None = None,
        expected_h2743_frame: dict[str, object] | None = None,
    ) -> dict[str, object]:
        self.calls.append((step, expected_revision))
        return {'status': 'available', 'army_strengths': [deepcopy(self.source)],
                'native_readiness': {'current_strength': True, 'full_monthly': False}}


def composed_row(fraction: int = 10000) -> ArmyStrengthRow:
    army = row(fraction)
    # Subject refresh scope is independent; the B target is refreshed in Army30.
    army['scoped_ordered_refill_inputs_v1']['army_refresh_occurrence_indices'] = []
    regiment: BesiegingRegiment = {'stored_index': 0, 'army_regiment_id': 11001, 'available': True,
                'unavailable_reason': '', 'current_soldiers': 160, 'maximum_soldiers': 200,
                'replenishment_records_v1': deepcopy(army['regiment_replenishment_records_v1'][0])}
    occurrence: BesiegingOccurrence = {'stored_index': 0, 'public_unit_id': 21, 'resolved_unit_id': 21,
        'unit_used_fallback': False, 'current_province_id': 7, 'current_province_used_fallback': False,
        'raw_unit18': 0, 'raw_unit170': 0, 'raw_unit44': 0, 'native_carmy_id': 20,
        'army_used_fallback': False, 'eligible': True, 'available': True, 'unavailable_reason': '',
        'native_whole_current_soldiers': 320,
        'regiments': [regiment, {**deepcopy(regiment), 'stored_index': 1}]}
    army['current_province_besieging_contributors_v1'] = {
        'status': 'available', 'unavailable_reason': '', 'province_id': 7,
        'native_province_unit_count': 3, 'native_besieging_strength': 640,
        'contributors_ready': True, 'native_assault_expected_loss': 64,
        'assault_context': {'status': 'available', 'unavailable_reason': '',
            'has_active_siege': True, 'siege_id': 77, 'breach_level_raw': 1,
            'casualty_percentage_count': 3, 'casualty_percentage_raw': 1000000},
        'occurrences': [occurrence, {**deepcopy(occurrence), 'stored_index': 2}]}
    refresh: RefreshOccurrence = {'manager_stored_index': 1, 'raw_carmy_id': 30, 'resolved_carmy_id': 30,
        'army_used_fallback': False, 'native_regiment_occurrence_count': 3,
        'regiments': [{'stored_index': pos, 'raw_army_regiment_id': 11001,
                      'army_regiment_id': 11001} for pos in (0, 2)]}
    scoped = army['scoped_ordered_refill_inputs_v1']
    army['ordered_besieging_refill_inputs_v1'] = {
        'source': 'native_ordered_besieging_refill_scope', 'status': 'available',
        'unavailable_reason': None, 'subject_army_id': 11, 'subject_carmy_id': 12,
        'province_id': 7, 'refresh_membership_ready': True,
        'native_persistent_occurrence_count': 5, 'native_army_refresh_occurrence_count': 4,
        'target_army_regiment_ids': [11001],
        'persistent_occurrences': deepcopy(scoped['persistent_occurrences']),
        'persistent_regiments': deepcopy(scoped['persistent_regiments']),
        'refresh_occurrences': [refresh, {**deepcopy(refresh), 'manager_stored_index': 3}]}
    return army


class OrderedBesiegingAssaultServiceTests(unittest.TestCase):
    def test_actual_refresh_ordered_core_deltas_and_assault_production_route(self) -> None:
        outputs: dict[str, dict[str, object]] = {}

        def query(name: str, army: ArmyStrengthRow) -> dict[str, object]:
            before = deepcopy(army)
            service = MemoryRoute(army)
            returned = service.query_army_strengths([11], expected_revision=42)
            self.assertEqual(army, before)
            self.assertEqual(service.calls, [('query-army-strengths-v1', 42)])
            self.assertEqual(returned['native_readiness'], {'current_strength': True, 'full_monthly': False})
            self.assertEqual(_at(returned, 'army_strengths', 0, 'current_supply_change_monthly_raw'), 700000)
            result = _object_map(_at(returned, 'same_input_conditional_ordered_refill_besieging_assault_v1', 0))
            for key in ('actual_after', 'actual_replenishment', 'actual_loss', 'actual_effects',
                        'actual_post_stage_observed', 'preparation_replayed', 'full_manager_replayed',
                        'full_daily_assault_ready', 'full_monthly_ready'):
                self.assertFalse(result[key])
            self.assertEqual(result['refill_ADDs_in_adapter'], 0)
            outputs[name] = returned
            return result

        ordered = query('actual-cross-army-repeat', composed_row())
        self.assertTrue(ordered['conditional_besieging_strength_ready'])
        self.assertEqual(ordered['physical_core_invocations'], 1)
        self.assertEqual([_at(o, 'writes', 0, 'after_current') for o in _object_rows(_at(ordered, 'physical_core', 'occurrences'))], [90, 100])
        self.assertEqual(ordered['conditional_besieging_strength'], 800)
        self.assertEqual(ordered['conditional_assault_expected_loss'], 80)
        self.assertEqual([r['manager_stored_index'] for r in _object_rows(ordered['refresh_occurrences'])], [1, 3])
        self.assertEqual(len(_array(ordered['final_refreshed_regiments'])), 1)
        self.assertEqual([d['delta_soldiers'] for d in _object_rows(_at(ordered, 'besieging_occurrences', 0, 'deltas'))], [40, 40])

        absent = composed_row()
        leaf = absent['ordered_besieging_refill_inputs_v1']
        leaf['refresh_occurrences'] = []
        leaf['persistent_occurrences'], leaf['persistent_regiments'] = [], []
        for occurrence in absent['current_province_besieging_contributors_v1']['occurrences']:
            for regiment in occurrence['regiments']:
                regiment['replenishment_records_v1'] = None
        unchanged = query('known-nonmember-no-unused-DATA', absent)
        self.assertTrue(unchanged['conditional_besieging_strength_ready'])
        self.assertEqual(unchanged['conditional_besieging_strength'], 640)
        self.assertEqual(unchanged['conditional_assault_expected_loss'], 64)

        rounded = composed_row(1)
        cleared = query('qualified-q0-clears-unreferenced-pair', rounded)
        self.assertTrue(_at(cleared, 'physical_core', 'occurrences', 0, 'native_core_admitted'))
        self.assertEqual(_at(cleared, 'physical_core', 'occurrences', 0, 'q_buffer'), [0] * 7)
        self.assertEqual(_at(cleared, 'final_physical_chunks', 1, 'current_soldiers'), 0)
        self.assertEqual(cleared['conditional_besieging_strength'], 640)
        self.assertEqual(cleared['conditional_assault_expected_loss'], 64)
        suppressed = deepcopy(rounded)
        suppressed['ordered_besieging_refill_inputs_v1']['persistent_regiments'][0]['prepared_fraction_raw'] = 0
        zero = query('nonpositive-no-clear', suppressed)
        self.assertEqual(_at(zero, 'physical_core', 'occurrences', 0, 'writes'), [])
        self.assertEqual(_at(zero, 'final_physical_chunks', 1, 'current_soldiers'), 20)
        self.assertEqual(zero['conditional_besieging_strength'], 640)

        missing = composed_row()
        leaf = missing['ordered_besieging_refill_inputs_v1']
        leaf['status'], leaf['unavailable_reason'] = 'partial', 'missing_origin'
        leaf['persistent_regiments'][0]['chunks'][0]['origin_province_788_raw'] = None
        partial = query('missing-affected-context', missing)
        self.assertFalse(partial['conditional_besieging_strength_ready'])
        self.assertIsNone(partial['conditional_besieging_strength'])
        self.assertEqual(partial['native_besieging_strength'], 640)
        self.assertEqual(_at(partial, 'final_physical_chunks', 0, 'status'), 'unavailable')
        leaf['persistent_regiments'][0]['prepared_fraction_raw'] = 0
        self.assertEqual(query('known-zero-with-hidden-context-missing', missing)['conditional_besieging_strength'], 640)
        no_membership = composed_row()
        no_membership_leaf = no_membership['ordered_besieging_refill_inputs_v1']
        no_membership_leaf['status'] = 'partial'
        no_membership_leaf['unavailable_reason'] = 'refresh_roster_failed'
        no_membership_leaf['refresh_membership_ready'] = False
        self.assertFalse(query('unknown-is-not-empty-membership', no_membership)['conditional_besieging_strength_ready'])

        signed = composed_row()
        signed_family = signed['current_province_besieging_contributors_v1']
        signed_family['occurrences'] = [signed_family['occurrences'][0]]
        signed_family['native_besieging_strength'] = 2147483640
        signed_family['occurrences'][0]['native_whole_current_soldiers'] = 2147483640
        signed_family['occurrences'][0]['regiments'].append({
            'stored_index': 2, 'army_regiment_id': 11002, 'available': True,
            'unavailable_reason': '', 'current_soldiers': 2147483320,
            'maximum_soldiers': 2147483320, 'replenishment_records_v1': None})
        signed['ordered_besieging_refill_inputs_v1']['target_army_regiment_ids'].append(11002)
        wrapped = query('signed-flags0-delta-wrap', signed)
        self.assertEqual(wrapped['conditional_besieging_strength'], -2147483576)
        self.assertEqual(wrapped['conditional_assault_expected_loss'], 0)
        negative = composed_row()
        negative['current_province_besieging_contributors_v1']['assault_context']['casualty_percentage_raw'] = -100000
        self.assertEqual(query('loaded-negative-percentage-retained', negative)['conditional_assault_expected_loss'], -8)
        legacy = composed_row()
        del legacy['ordered_besieging_refill_inputs_v1']
        self.assertEqual(query('legacy-native-leaves-independent', legacy)['native_besieging_strength'], 640)
        malformed = _object_map(deepcopy(composed_row()['ordered_besieging_refill_inputs_v1']))
        _object_map(_at(malformed, 'refresh_occurrences', 0))['army_used_fallback'] = 0
        with self.assertRaises(ValueError):
            normalize_ordered_besieging_refill_inputs_v1(malformed)
        path = os.environ.get('XAR_ORDERED_B_ASSAULT_CASE_OUTPUT')
        if path:
            Path(path).write_text(json.dumps(outputs, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    unittest.main()
