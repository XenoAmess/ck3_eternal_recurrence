from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest


ROOT = Path('Z:/ck3_mod_rewrite/ck3_autonomous_player')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'tests/unit'))

# The candidate is the complete production module plus the external delta.
candidate_path = HERE / 'strategy_candidate.py'
if not candidate_path.is_file():
    candidate_path = ROOT / 'src/xar_autoplayer/strategy.py'
spec = importlib.util.spec_from_file_location('xar_autoplayer.strategy', candidate_path)
if spec is None or spec.loader is None:
    raise RuntimeError('candidate strategy module unavailable')
strategy = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = strategy
spec.loader.exec_module(strategy)

import test_gameplay_bridge as tactical
import test_defender_white_peace_native_wire_g54 as wire
from xar_autoplayer.bridge.mcp_server import create_server


def planning_options(native_options, *, score=7):
    result = copy.deepcopy(native_options)
    result['player_relative_war_score'] = score
    result.update({
        'queried_snapshot_id': 'session:90',
        'queried_revision': 90,
        'queried_native_revision': 90,
        'queried_connection_generation': 1,
        'episode_run_id': None,
    })
    return result


def exhausted_plan(options, *, history=None, score=7, steps=None):
    return tactical._native_war_plan(
        player=tactical._army(
            11, soldiers=396, province_id=52, controllable=True,
            army_state='sieging', route_province_ids=[],
        ),
        enemies=[tactical._army(
            21, soldiers=400, province_id=54, controllable=False,
            move_target_province_id=52, army_state='moving',
            route_province_ids=[16, 52],
        )],
        war_id=options['war_id'], player_side='defender',
        player_is_primary_war_leader=True, score=score,
        date_raw=wire.DATE_RAW, history=history, objectives=[52],
        objective_states=[tactical._objective_state(
            52, garrison_size=400, besieging_strength=396,
            active_siege=tactical._active_siege(
                siege_id=6, army_id=11, days_left=None,
            ),
        )],
        occupation_supported=True, garrison_supported=True,
        siege_progress_supported=True, targeted_title_ids=[2128],
        steps=steps or (f"offer-white-peace-{options['war_id']}", 'life-advance'),
        termination_options=[options],
    )


class DefenderWhitePeaceOrdinaryComposite(unittest.IsolatedAsyncioTestCase):
    async def test_new_selection_service_and_registered_submission_compound(self):
        from mcp import Client

        phases = []
        for key, index in (
            ('individual_county_de_jure_cb', 17),
            ('minor_religious_war', 41),
        ):
            driver, endpoint = wire._driver()
            try:
                # CB17 is unchanged genuine producer wire; CB41 is an explicitly
                # synthetic identity variant exercising the existing SDK branch.
                if index == 41:
                    endpoint.options_packet = copy.deepcopy(endpoint.options_packet)
                    wire._inner(endpoint.options_packet)['war_termination_options'][
                        'active_casus_belli_identity'
                    ] = {'canonical_key': key, 'database_index': index}
                server = create_server(driver)
                async with Client(server) as client:
                    queried = await client.call_tool('ck3_query_war_termination_options', {
                        'war_id': wire._inner(endpoint.options_packet)['war_termination_options']['war_id'],
                        'expected_revision': driver.take_snapshot()['revision'],
                    })
                    self.assertFalse(queried.is_error)
                    native_options = queried.structured_content['war_termination_options']
                    options = planning_options(native_options)
                    plan = exhausted_plan(options)
                    self.assertEqual(plan['phase'], 'native_war_defender_no_safe_route_white_peace')
                    self.assertEqual(plan['selected_step'], f"offer-white-peace-{options['war_id']}")
                    self.assertEqual(plan['decision']['recipient_ai_acceptance_raw'], 163736)
                    self.assertIsNone(plan['decision']['recipient_response']['would_accept_now'])
                    self.assertFalse(plan['decision']['full_campaign_utility_ready'])
                    sent = await client.call_tool('ck3_offer_white_peace', {
                        'war_id': plan['war_id'],
                        'expected_revision': driver.take_snapshot()['revision'],
                    })
                    self.assertFalse(sent.is_error)
                    result = sent.structured_content['war_termination_result']
                    self.assertEqual(result['status'], 'submitted_pending')
                    self.assertIsNone(result['recipient_would_accept_now'])
                    self.assertEqual([row['step'] for row in wire._commands(endpoint)], [
                        f"query-war-termination-options-{options['war_id']}",
                        f"offer-white-peace-{options['war_id']}",
                    ])

                # New ordinary consumer respects the existing same-WarID cooldown.
                submitted = [{
                    'command': plan['selected_step'], 'ok': True,
                    'result': {'war_termination_result': {
                        **result, 'episode_run_id': None,
                    }},
                }]
                cooldown_plan = exhausted_plan(options, history=submitted)
                self.assertEqual(cooldown_plan['selected_step'], 'life-advance')
                self.assertEqual(cooldown_plan['phase'], 'native_war_white_peace_response_advance')

                # Safe objective continuation remains ahead of the new proposal.
                safe = tactical._native_war_plan(
                    player=tactical._army(11, soldiers=900, province_id=20,
                        controllable=True, army_state='regular', route_province_ids=[]),
                    enemies=[], war_id=options['war_id'], player_side='defender',
                    score=7, date_raw=wire.DATE_RAW,
                    history=[tactical._preview_row(1, origin=20, target=2585,
                        date_raw=wire.DATE_RAW, route=[30, 2585])],
                    objectives=[2585], targeted_title_ids=[2128],
                    steps=('move-army-11-to-2585', plan['selected_step'], 'life-advance'),
                    termination_options=[options],
                )
                self.assertEqual(safe['selected_step'], 'move-army-11-to-2585')

                victory_options = planning_options(native_options, score=100)
                victory = exhausted_plan(victory_options, score=100,
                    steps=(f"enforce-demands-{options['war_id']}", plan['selected_step'], 'life-advance'))
                self.assertEqual(victory['selected_step'], f"enforce-demands-{options['war_id']}")

                # Direct production proposal boundary, because earlier planner
                # branches may legitimately request fresher input for negatives.
                snapshot = {
                    'paused': True, 'snapshot_id': 'session:90', 'revision': 90,
                    'native_revision': 90, 'diagnostics': {'connection_generation': 1},
                    'episode_run_id': None, 'date_raw': wire.DATE_RAW,
                    'active_wars': [{'war_id': options['war_id'], 'player_side': 'defender',
                        'player_is_primary_war_leader': True, 'player_relative_war_score': 7}],
                    'war_termination_options': [options],
                }
                def proposed(frame):
                    return strategy._defender_no_safe_route_white_peace_plan(
                        frame, war_id=options['war_id'], commands=[],
                        available_steps={plan['selected_step']},
                        active_war_summary=[], route_rejections=[{'status': 'unsafe'}],
                    )
                self.assertIsNotNone(proposed(snapshot))
                negatives = {
                    'stale': lambda frame: frame['war_termination_options'][0].update(queried_revision=89),
                    'nonprimary': lambda frame: frame['active_wars'][0].update(player_is_primary_war_leader=False),
                    'zero_quote': lambda frame: frame['war_termination_options'][0]['options']['white_peace']['ai_acceptance'].update(raw=0),
                    'native_false': lambda frame: frame['war_termination_options'][0]['options']['white_peace'].update(native_validator_passed=False, available=False),
                }
                for name, mutate in negatives.items():
                    frame = copy.deepcopy(snapshot)
                    mutate(frame)
                    self.assertIsNone(proposed(frame), name)
                phases.append({'cb': key, 'database_index': index,
                    'native_wire': 'genuine_unchanged' if index == 17 else 'synthetic_identity_variant',
                    'selection': plan['phase'], 'submission': result['status'],
                    'negative_branches': list(negatives), 'safe_continuation': True,
                    'victory_priority': True, 'cooldown': True})
            finally:
                driver.close()
        receipt = {'status': 'GREEN', 'test_count': 1, 'phases': phases,
            'strategy_path': str(candidate_path),
            'strategy_sha256': hashlib.sha256(candidate_path.read_bytes()).hexdigest(),
            'scope': 'new ordinary selection and existing Service/Driver/registered MCP fixture composite',
            'live': False, 'new_native_qualification': False}
        (HERE / 'FOCUSED-RESULT.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')


if __name__ == '__main__':
    unittest.main(verbosity=2)
