"""One NEW normal Service compound, authored for Root's sole FIRST run."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))

from xar_autoplayer import current_replenishment_army_selector_v1 as selector
from xar_autoplayer.bridge.war_contract import normalize_army_strengths
from test_gameplay_bridge import _army, _native_war_plan, _snapshot
from test_scoped_ordered_refill_service import row as _typed_refill_row


def _strength(unit: int, fraction: int, current: int = 80) -> dict:
    source = _typed_refill_row(fraction, current, 100)
    source.update(army_id=unit, native_carmy_id=unit + 1000, war_ids=[88])
    persistent = unit + 50000
    regiment = unit + 11000
    source['regiment_strengths'][0]['army_regiment_id'] = regiment
    data = source['regiment_replenishment_records_v1'][0]
    data['army_regiment_id'] = regiment
    for record in data['records']:
        record.update(persistent_regiment_id=persistent, chunk_army_regiment_id=regiment)
    source['scoped_ordered_refill_inputs_v1'].update(
        subject_army_id=unit, subject_carmy_id=unit + 1000)
    inputs = source['scoped_ordered_refill_inputs_v1']
    positions = (1, 3) if unit == 11 else (0, 2)
    inputs['persistent_occurrences'] = [
        {'stored_index': index, 'persistent_regiment_id': persistent} for index in positions]
    inputs['army_refresh_occurrence_indices'] = list(positions)
    inputs['persistent_regiments'][0]['persistent_regiment_id'] = persistent
    for chunk in inputs['persistent_regiments'][0]['chunks']:
        chunk.update(owner_persistent_regiment_id=persistent, owner_resolved_full_id=persistent)
        if chunk['physical_index'] == 0:
            chunk.update(army_regiment_id_raw=regiment, associated_arrg_resolved_full_id=regiment)
        chunk.update(associated_unit_raw_full_id=unit, associated_unit_resolved_full_id=unit,
                     associated_army_raw_full_id=unit + 1000,
                     associated_army_resolved_full_id=unit + 1000)
    # Typed fixture input reuses the pure native arithmetic; it does not invoke
    # or requalify the old whole producer or test method.
    return normalize_army_strengths([source])[0]


class CurrentReplenishmentNormalPlanV1Tests(unittest.TestCase):
    def test_normal_plan_dispatches_equal_force_without_consuming_future_troops(self) -> None:
        outputs = {}

        def plan(name: str, first: dict, second: dict, *, status='available') -> dict:
            sources = [first, second]
            before = deepcopy(sources)
            armies = [
                _army(row['army_id'], soldiers=row['current_soldiers'],
                      province_id=2630 + index, controllable=True,
                      army_state='regular', army_state_code=1, route_province_ids=[])
                for index, row in enumerate(sources)
            ]
            def frame(revision):
                return {**_snapshot(revision), 'snapshot_id': 'normal-refill-frame',
                        'army_strengths_queried_snapshot_id': 'normal-refill-frame',
                        'army_strengths_queried_revision': revision}

            original = selector.project_scoped_observed_prepared_ordered_refill
            with patch('test_gameplay_bridge._snapshot', side_effect=frame), patch.object(
                    selector, 'project_scoped_observed_prepared_ordered_refill', wraps=original) as core:
                returned = _native_war_plan(
                    player=armies[0], players=armies, enemies=[], score=17,
                    date_raw=53216640, objective=2640, army_strengths=sources,
                    army_strengths_status=status,
                    move_route_preview_supported=False,
                    steps=('query-army-strengths-v1', 'life-advance',
                           'move-army-11-to-2640', 'move-army-22-to-2640'))
                expected_calls = 0 if status is None or first['current_soldiers'] != second['current_soldiers'] else 2
                self.assertEqual(core.call_count, expected_calls)
            self.assertEqual(sources, before)
            outputs[name] = returned
            return returned

        positive = plan('current-positive-versus-zero', _strength(11, 10000), _strength(22, 0))
        self.assertEqual(positive['selected_step'], 'move-army-22-to-2640')
        receipt = positive['active_wars'][0]['current_replenishment_selection_v1']
        self.assertEqual(receipt['status'], 'available')
        self.assertEqual([row['native_signed_current_delta'] for row in receipt['candidates']], [40, 0])
        self.assertFalse(receipt['actual_after'])
        self.assertFalse(receipt['full_monthly_ready'])

        stronger = plan('actual-force-stays-primary', _strength(11, 10000, 90), _strength(22, 0))
        self.assertEqual(stronger['selected_step'], 'move-army-11-to-2640')

        missing = _strength(11, 10000)
        missing['scoped_ordered_refill_inputs_v1']['persistent_regiments'][0]['chunks'][0].update(
            unit_position_owner_resolved_full_id=707,
            unit_position_holder_resolved_full_id=808,
            native_unit_position_eligible=None)
        unavailable = plan('missing-current-permission-keeps-legacy', missing, _strength(22, 0))
        self.assertEqual(unavailable['selected_step'], 'move-army-11-to-2640')
        self.assertEqual(unavailable['active_wars'][0]['current_replenishment_selection_v1']['status'],
                         'current_inputs_unavailable')

        query = plan('absent-current-query-is-requested-once', _strength(11, 10000), _strength(22, 0), status=None)
        self.assertEqual(query['selected_step'], 'query-army-strengths-v1')
        self.assertEqual(query['army_strength_scope']['player_army_ids'], [11, 22])
        self.assertEqual(query['army_strength_scope']['enemy_army_ids'], [])

        output = os.environ.get('XAR_CURRENT_REPLENISHMENT_FIRST_OUTPUT')
        if output:
            Path(output).write_text(json.dumps(outputs, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    unittest.main()
