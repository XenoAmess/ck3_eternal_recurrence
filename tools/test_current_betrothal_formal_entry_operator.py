"""Official pair preparation accepts the new formal fulfillment mode."""

from __future__ import annotations

import copy
import unittest

import g2_preview_operator as operator


def pending_pair():
    manifest = {'episode_character_id': 101, 'episode_run_id': 'family-entry-101'}
    checkpoint = {
        **manifest, 'date_raw': 53220000, 'sha256': 'a' * 64,
        'history_index': 10, 'status': 'saved', 'turn_index': 1,
        'phase': 'current_first_heir_betrothal_submitted_pending',
        'pending_action': {'heir_character_id': 202, 'candidate_character_id': 303,
                           'recipient_character_id': 404,
                           'episode_run_id': manifest['episode_run_id'],
                           'fulfill_existing_betrothal': True},
    }
    pending = {
        'schema': operator.FAMILY_ACTION_V1_SCHEMA,
        'status': 'receipt_pending', 'submission_state': 'receipt_pending',
        'material_result': False, 'accepted': True, 'fulfill_existing_betrothal': True,
        'played_character_id': 101, 'heir_character_id': 202,
        'candidate_character_id': 303, 'recipient_character_id': 404,
        'episode_run_id': manifest['episode_run_id'],
        'source_date_raw': 53220000, 'source_bridge_pid': 9,
    }
    sidecar = {'schema': operator.FAMILY_PENDING_V1_SCHEMA,
               'pending': pending, 'resolved': None}
    report = {'session': {'pid': 9}, 'checkpoints': [checkpoint],
              'auto_run': {'turns': [{
                  'index': 1, 'selected_step': operator.CURRENT_BETROTHAL_SUBMIT_STEP,
                  'result': copy.deepcopy(pending),
                  'plan': {'current_betrothal_fulfillment': True,
                           'current_betrothal_choice': {'candidate_character_id': 303}},
              }]}}
    driver = {**manifest, 'last_checkpoint': copy.deepcopy(checkpoint)}
    return sidecar, driver, manifest, report


class CurrentBetrothalOperatorPairTests(unittest.TestCase):
    def test_official_pending_pair_accepts_new_submit_and_checkpoint(self):
        sidecar, driver, manifest, report = pending_pair()
        self.assertEqual(operator.family_pending_sidecar_pair(
            sidecar, driver, manifest, 'a' * 64, report), 303)
        report['auto_run']['turns'][0]['selected_step'] = operator.FAMILY_SUBMIT_STEP
        with self.assertRaisesRegex(ValueError, 'not proven'):
            operator.family_pending_sidecar_pair(sidecar, driver, manifest, 'a' * 64, report)

    def test_official_pending_pair_continues_new_pid_without_resubmit(self):
        sidecar, driver, manifest, first = pending_pair()
        second_checkpoint = {**first['checkpoints'][0], 'phase': 'current_betrothal_fulfillment_result_pending',
                             'history_index': 15, 'sha256': 'b' * 64}
        second = {
            'ok': True, 'session': {'pid': 11},
            'fixed_seed': {'sha256': 'a' * 64, 'history_index': 10,
                           'saved_date_raw': 53220000},
            'readiness': {'bridge_pid': 11, **manifest},
            'checkpoints': [second_checkpoint],
            'auto_run': {'turns': [{
                'index': 1, 'selected_step': 'query-observed-first-heir-marriage-result-v1-private',
                'result': {'status': 'pending', 'fulfill_existing_betrothal': True,
                           'heir_character_id': 202, 'candidate_character_id': 303},
            }]},
        }
        driver['last_checkpoint'] = copy.deepcopy(second_checkpoint)
        sidecar['pending']['last_checked_bridge_pid'] = 11
        self.assertEqual(operator.family_pending_sidecar_pair(
            sidecar, driver, manifest, 'b' * 64, [first, second]), 303)

    def test_old_betrothal_is_not_material_fulfillment(self):
        sidecar, driver, manifest, _report = pending_pair()
        pending = sidecar['pending']
        sidecar['pending'] = None
        sidecar['resolved'] = {
            'status': 'betrothal', 'material_result': True,
            'fulfill_existing_betrothal': True, 'source_pending': pending,
            'heir_character_id': 202, 'candidate_character_id': 303,
            'episode_run_id': manifest['episode_run_id'],
        }
        with self.assertRaisesRegex(ValueError, 'disagrees'):
            operator.family_resolved_sidecar_pair(sidecar, driver, manifest, 'a' * 64)
        sidecar['resolved']['status'] = 'marriage'
        self.assertEqual(operator.family_resolved_sidecar_pair(
            sidecar, driver, manifest, 'a' * 64), 303)


if __name__ == '__main__':
    unittest.main()
