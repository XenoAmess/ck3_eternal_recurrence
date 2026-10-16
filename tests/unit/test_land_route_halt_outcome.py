"""Synthetic portable packets; no runtime, SDK, or Native access."""
import copy
import json
from pathlib import Path
import unittest
from tools.g2_saved_campaign.land_route_halt_outcome import classify_land_route_halt_result_v1


def packet(army=7):
    frame = dict(snapshot_id='native:11', native_revision=11, revision=4,
                 date_raw=240, actor_character_id=9, episode_run_id='fixture-episode',
                 bridge_pid=321, connection_generation=2)
    step = 'halt-army-' + str(army)
    route = [12, 13]
    plan = dict(phase='native_war_land_route_timeline_unavailable_halt_submit',
                policy='one-life-turn-v1', selected_step=step,
                halt_intent=dict(army_id=army, original_route_province_ids=route,
                    current_province_id=10, original_move_target_province_id=13,
                    postcondition_required='fresh_route_empty_or_verified_retained_first_edge',
                    contact_free_proven=False),
                contact_query_attempt=dict(scope_status='current_frame', status='unavailable', ok=False))
    observed = dict(frame)
    inner = dict(schema='xar.halt-army-validator-deferred/v1', step=step,
        accepted=False, status='deferred', business_submission=False, replay_allowed=False,
        backend_id='native-headless', snapshot_id=frame['snapshot_id'],
        revision=frame['revision'], native_revision=frame['native_revision'],
        war_action=dict(army_id=army, status='halt_validator_rejected_current_route_retained',
            reason='native_halt_validator_rejected', current_province_id=10,
            move_target_province_id=13, route_province_ids=route, contact_free_proven=False),
        halt_rejection_evidence=dict(native_request_id='fixture-request',
            native_request=dict(type='execute_step', protocol_version=1,
                request_id='fixture-request', step=step, expected_revision=11),
            native_command_result=dict(type='command_result', protocol_version=1,
                request_id='fixture-request', ok=False,
                error='CK3 halt-army command validation failed'),
            observed_frame=observed))
    return dict(status='executed', selected_step=step, plan=plan,
                result=inner, planning_source_frame=frame), dict(frame)


def bind(body, *, initial_frame, game_pid):
    source = body['planning_source_frame']
    if source != initial_frame or source['bridge_pid'] != game_pid:
        raise ValueError('fixture reviewed binding rejected')
    return dict(source)


def classify(body, initial):
    return classify_land_route_halt_result_v1(body, bind_gameplay_frame=bind,
                                            initial_frame=initial, game_pid=initial['bridge_pid'])


def accepted(body):
    source = body['planning_source_frame']
    intent = body['plan']['halt_intent']
    body['result'] = dict(step=body['selected_step'], accepted=True, status='completed',
        war_action=dict(status='halt_submitted', army_id=intent['army_id'],
            postcondition_verified=False, submitted_date_raw=source['date_raw'],
            original_current_province_id=intent['current_province_id'],
            original_move_target_province_id=intent['original_move_target_province_id'],
            original_route_province_ids=list(intent['original_route_province_ids']),
            owner_character_id=source['actor_character_id'],
            submitted_native_revision=source['native_revision'],
            submitted_connection_generation=source['connection_generation'],
            submitted_episode_run_id=source['episode_run_id']))


class HaltOutcomeTests(unittest.TestCase):
    def test_actual_p30_ack_projection_remains_pending(self):
        path = (Path(__file__).resolve().parents[2] / "ck3_autonomous_player" /
                "tests" / "fixtures" / "p30_land_halt_actual_projection.json")
        body = json.loads(path.read_text("utf8"))["halt_body"]
        initial = dict(body["planning_source_frame"])
        credit = classify(body, initial)
        self.assertEqual(credit["category"], "unsafe_route_halt_submitted_pending")
        self.assertTrue(credit["submitted_pending"])
        self.assertEqual(credit["halt_starting_tuple"]["route_province_ids"], [5966, 5969])
        self.assertFalse(credit["halt_postcondition_verified"])
        self.assertFalse(credit["business_success_inferred"])
        self.assertFalse(credit["contact_free_proven"])

    def test_exact_wire_without_result_step_is_zero_credit(self):
        body, initial = packet()
        credit = classify(body, initial)
        self.assertNotIn('step', body['result']['halt_rejection_evidence']['native_command_result'])
        self.assertEqual(credit['category'], 'halt_validator_rejected_route_retained_observed')
        self.assertTrue(credit['typed_nonmaterial_observation'])
        for key in ('accepted', 'business_submission', 'submitted_pending', 'primitive_accepted',
                    'date_advance_observed', 'material_verified', 'ui_action_credit', 'action_credit',
                    'business_success_inferred', 'halt_postcondition_verified', 'stopped_army_inferred',
                    'contact_free_proven', 'replay_allowed'):
            self.assertIs(credit[key], False, key)
        self.assertEqual(credit['actual_date_delta_raw'], 0)
        self.assertEqual(credit['actual_elapsed_days'], 0)
        self.assertTrue(credit['paired_after_metrics_still_required'])

    def test_accepted_ack_remains_pending_with_full_start_tuple(self):
        body, initial = packet()
        accepted(body)
        credit = classify(body, initial)
        self.assertEqual(credit['category'], 'unsafe_route_halt_submitted_pending')
        self.assertTrue(credit['submitted_pending'])
        self.assertTrue(credit['primitive_accepted'])
        self.assertEqual(credit['halt_starting_tuple']['route_province_ids'], [12, 13])
        for key in ('halt_postcondition_verified', 'stopped_army_inferred',
                    'business_success_inferred', 'contact_free_proven', 'replay_allowed'):
            self.assertIs(credit[key], False)
        body['plan']['halt_intent']['original_route_province_ids'][0] = 99
        self.assertEqual(credit['halt_starting_tuple']['route_province_ids'], [12, 13])

    def test_public_cunit_zero_and_maximum_are_legal(self):
        for army in (0, 2**31 - 1):
            for is_ack in (False, True):
                with self.subTest(army=army, accepted=is_ack):
                    body, initial = packet(army)
                    if is_ack:
                        accepted(body)
                    credit = classify(body, initial)
                    self.assertIs(credit.get('business_success_inferred'), False)
                    if is_ack:
                        self.assertEqual(credit['halt_army_id'], army)

    def test_noncanonical_cunit_refused(self):
        for token in ('-1', '01', str(2**31), '1.0', ''):
            with self.subTest(token=token):
                body, initial = packet()
                body['selected_step'] = 'halt-army-' + token
                with self.assertRaises(ValueError):
                    classify(body, initial)

    def test_wire_owner_date_route_and_scope_negatives(self):
        mutations = [
            lambda b: b['result'].update(accepted=True),
            lambda b: b['result'].update(business_submission=True),
            lambda b: b['result']['halt_rejection_evidence']['native_command_result'].update(ok=True),
            lambda b: b['result']['halt_rejection_evidence']['native_command_result'].update(error='other refusal'),
            lambda b: b['result']['halt_rejection_evidence']['native_command_result'].update(request_id='other'),
            lambda b: b['result']['halt_rejection_evidence']['native_request'].update(expected_revision=99),
            lambda b: b['result']['halt_rejection_evidence']['observed_frame'].update(actor_character_id=10),
            lambda b: b['result']['halt_rejection_evidence']['observed_frame'].update(date_raw=264),
            lambda b: b['result']['halt_rejection_evidence']['observed_frame'].update(connection_generation=3),
            lambda b: b['result']['war_action'].update(route_province_ids=[12]),
            lambda b: b['plan']['contact_query_attempt'].update(scope_status='unknown_frame'),
        ]
        for index, mutate in enumerate(mutations):
            with self.subTest(index=index):
                body, initial = packet()
                mutate(body)
                with self.assertRaises(ValueError):
                    classify(body, initial)

    def test_fresher_same_date_observation_allowed(self):
        body, initial = packet()
        observed = body['result']['halt_rejection_evidence']['observed_frame']
        observed.update(native_revision=12, revision=5, snapshot_id='native:12')
        body['result'].update(native_revision=12, revision=5, snapshot_id='native:12')
        credit = classify(body, initial)
        self.assertFalse(credit['date_advance_observed'])
        self.assertEqual(credit['source_gameplay_frame']['native_revision'], 11)

    def test_binding_callback_is_required_and_its_rejection_propagates(self):
        body, initial = packet()
        body['planning_source_frame']['bridge_pid'] += 1
        with self.assertRaises(ValueError):
            classify(body, initial)
        with self.assertRaises(TypeError):
            classify_land_route_halt_result_v1(body)

    def test_unrelated_phase_delegates_without_callback_or_mutation(self):
        body, initial = packet()
        body['plan']['phase'] = 'ordinary-other-phase'
        before = copy.deepcopy(body)
        def forbidden(*args, **kwargs):
            self.fail('unrelated phase must delegate before binding')
        self.assertIsNone(classify_land_route_halt_result_v1(body, bind_gameplay_frame=forbidden))
        self.assertEqual(body, before)


if __name__ == '__main__':
    unittest.main(verbosity=2)
