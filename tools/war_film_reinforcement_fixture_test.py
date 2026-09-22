"""Synthetic negative controls for the offline fixture qualifier; no live claims."""
import copy
import unittest

from war_film_reinforcement_fixture import EXE_SHA256, SCHEMA, qualify


def synthetic():
    stamp = dict(snapshot_id='synthetic-frame', revision=3, native_revision=7,
                 date_raw=240, episode_run_id='synthetic-only', paused=True)
    battle = dict(status='available', battle_transition_ready=True, combat_id=88,
                  province_id=9, attacker_public_cunit_ids_in_stored_order=[99],
                  defender_public_cunit_ids_in_stored_order=[2, 3])
    baseline = copy.deepcopy(battle)
    baseline['defender_public_cunit_ids_in_stored_order'] = [1, 2, 3]
    parent = [{'public_cunit_ids_in_stored_order': [2]}, {'public_cunit_ids_in_stored_order': [3]}]
    rows = []
    for ident in (1, 2, 3):
        frame = dict(status='available', unavailable_reason=None,
                     battle_reinforcement_assignment_ready=True,
                     selected_public_cunit_id=ident, selected_native_carmy_id=ident+20,
                     coordinator_id=10, unit_stack_stored_index=1 if ident == 1 else 0,
                     subunit_stored_index=0 if ident == 1 else ident-2,
                     observed_date_raw=240,
                     native_order={'parent_subunits_in_stored_order': copy.deepcopy(parent) if ident != 1 else [{'public_cunit_ids_in_stored_order': [1]}], 'support_search_province_ids_in_stored_order': [9]},
                     signal={'asking_for_help': False, 'assigned_to_help': False},
                     assignment={'active_combat_id': 88 if ident != 1 else None,
                                 'combat_binding_status': 'already_in_active_combat' if ident != 1 else 'unbound_until_contact',
                                 'assignment_target_province_id': None})
        response = dict(query_sequence=1, queried_snapshot_id='synthetic-frame',
                        queried_revision=3, queried_native_revision=7, snapshot_revision=3,
                        battle_reinforcement_assignment=frame)
        second = copy.deepcopy(response)
        second['query_sequence'] = 2
        rows.append(dict(public_cunit_id=ident,
                         semantic_army={'unit_id': ident, 'controllable': False, 'in_combat': ident != 1, 'retreating': False, 'current_province_id': 9 if ident != 1 else 8},
                         first=response, second=second))
    return dict(schema=SCHEMA, evidence_kind='synthetic-offline-test', exe_sha256=EXE_SHA256,
                roles={'withdrawn_helper': 1, 'requester_anchor': 2, 'requester_partner': 3},
                combat_id=88, province_id=9, side='defender', snapshot_before=stamp,
                snapshot_after=copy.deepcopy(stamp), baseline_battle_transition=baseline,
                battle_transition=battle, units=rows)


def change_frames(bundle, index, fn):
    for name in ('first', 'second'):
        fn(bundle['units'][index][name]['battle_reinforcement_assignment'])


class FixtureBoundaryTests(unittest.TestCase):
    def test_three_units_can_qualify_structure_without_proving_native_outcomes(self):
        result = qualify(synthetic())
        self.assertEqual(result['result'], 'structural-preconditions-met')
        self.assertFalse(result['live_execution_performed'])
        self.assertFalse(result['native_assignment_proven'])
        self.assertFalse(result['eta_proven'])
        self.assertFalse(result['same_combat_join_proven'])

    def test_three_cunits_in_two_total_subunits_is_rejected(self):
        data = synthetic()
        def merge(frame):
            frame['subunit_stored_index'] = 0
            frame['native_order']['parent_subunits_in_stored_order'] = [{'public_cunit_ids_in_stored_order': [2, 3]}]
        change_frames(data, 1, merge)
        change_frames(data, 2, merge)
        with self.assertRaisesRegex(ValueError, 'one subunit'):
            qualify(data)

    def test_two_requester_units_in_different_parents_is_rejected(self):
        data = synthetic()
        change_frames(data, 2, lambda f: f.update(unit_stack_stored_index=2))
        with self.assertRaisesRegex(ValueError, 'share coordinator'):
            qualify(data)

    def test_cross_frame_stitching_is_rejected(self):
        data = synthetic()
        data['units'][1]['second']['queried_revision'] = 4
        with self.assertRaisesRegex(ValueError, 'different snapshot'):
            qualify(data)

    def test_control_handoff_ack_cannot_replace_membership(self):
        data = synthetic()
        change_frames(data, 0, lambda f: f.update(status='unavailable', unavailable_reason='subunit_backlink_mismatch'))
        with self.assertRaisesRegex(ValueError, 'membership unavailable'):
            qualify(data)

    def test_recycled_or_different_combat_is_rejected(self):
        data = synthetic()
        data['battle_transition']['combat_id'] += 0x1000000
        with self.assertRaisesRegex(ValueError, 'combat identity'):
            qualify(data)

    def test_outside_candidate_search_is_rejected(self):
        data = synthetic()
        change_frames(data, 0, lambda f: f['native_order'].update(support_search_province_ids_in_stored_order=[]))
        with self.assertRaisesRegex(ValueError, 'absent'):
            qualify(data)


if __name__ == '__main__':
    unittest.main()
