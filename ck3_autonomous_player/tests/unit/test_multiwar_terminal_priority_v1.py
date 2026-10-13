from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest


# The external runner supplies these paths; this also runs from tests/unit
# after the sole strategy owner adopts the tested delta.
PROJECT = Path(__file__).resolve().parents[2]
if (PROJECT / 'src/xar_autoplayer').is_dir():
    sys.path.insert(0, str(PROJECT / 'src'))
    sys.path.insert(0, str(PROJECT / 'tests/unit'))

from xar_autoplayer.bridge.driver import CallbackGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService
from test_gameplay_bridge import (
    _ready_white_peace_snapshot,
    _termination_options,
    _war,
)


def _with_terminal(snapshot: dict[str, object], war_id: int = 99) -> dict[str, object]:
    snapshot = copy.deepcopy(snapshot)
    snapshot['map_ready'] = True
    snapshot['active_wars'].append(_war(
        war_id=war_id, score=-100, allied_armies=[], enemy_armies=[],
    ))
    options = _termination_options(war_id, score=-100)
    options.update({
        'queried_snapshot_id': snapshot['snapshot_id'],
        'queried_revision': snapshot['revision'],
        'queried_native_revision': snapshot['native_revision'],
        'queried_connection_generation': snapshot['diagnostics']['connection_generation'],
        'episode_run_id': snapshot['episode_run_id'],
    })
    snapshot['war_termination_options'].append(options)
    return snapshot


def _submission(snapshot: dict[str, object], *, outcome: str, war_id: int) -> dict[str, object]:
    return {
        'index': 1,
        'command': f'surrender-war-{war_id}' if outcome == 'attacker_defeat' else f'offer-white-peace-{war_id}',
        'ok': True,
        'result': {'war_termination_result': {
            'status': 'submitted_pending',
            'war_id': war_id,
            'outcome': outcome,
            'episode_run_id': snapshot['episode_run_id'],
            'submitted_date_raw': snapshot['date_raw'],
        }},
    }


class MultiwarTerminalPriorityV1Tests(unittest.TestCase):
    def plan(self, snapshot: dict[str, object], steps: tuple[str, ...]) -> dict[str, object]:
        sent: list[str] = []

        def execute(step: str, revision: int | None) -> dict[str, object]:
            sent.append(step)
            raise RuntimeError(f'plan must not submit {step}')

        driver = CallbackGameplayDriver(
            backend_id='native-headless',
            snapshot=lambda: copy.deepcopy(snapshot),
            execute=execute,
            action_steps=steps,
        )
        plan = GameplayBridgeService(driver).plan_turn()['plan']
        self.assertEqual(sent, [])
        return plan

    def test_qualified_terminal_precedes_other_war_query_in_either_order(self) -> None:
        snapshot = _with_terminal(_ready_white_peace_snapshot())
        snapshot['war_termination_options'] = [
            row for row in snapshot['war_termination_options'] if row['war_id'] == 99
        ]
        steps = ('query-war-termination-options-88', 'surrender-war-99', 'life-advance')
        for reverse in (False, True):
            with self.subTest(reverse=reverse):
                current = copy.deepcopy(snapshot)
                if reverse:
                    current['active_wars'].reverse()
                plan = self.plan(current, steps)
                self.assertEqual(plan['phase'], 'native_war_terminal_score_surrender')
                self.assertEqual(plan['selected_step'], 'surrender-war-99')
                self.assertEqual(plan['war_id'], 99)

    def test_qualified_terminal_precedes_other_war_white_peace_in_either_order(self) -> None:
        snapshot = _with_terminal(_ready_white_peace_snapshot())
        steps = ('offer-white-peace-88', 'surrender-war-99', 'life-advance')
        for reverse in (False, True):
            with self.subTest(reverse=reverse):
                current = copy.deepcopy(snapshot)
                if reverse:
                    current['active_wars'].reverse()
                plan = self.plan(current, steps)
                self.assertEqual(plan['selected_step'], 'surrender-war-99')
                self.assertEqual(plan['decision']['policy'], 'terminal-score-defeat-receipt-v1')

    def test_qualified_terminal_precedes_other_war_pending_response_advance(self) -> None:
        snapshot = _with_terminal(_ready_white_peace_snapshot())
        snapshot['native_command_history'] = [_submission(snapshot, outcome='white_peace', war_id=88)]
        steps = ('offer-white-peace-88', 'surrender-war-99', 'life-advance')
        for reverse in (False, True):
            with self.subTest(reverse=reverse):
                current = copy.deepcopy(snapshot)
                if reverse:
                    current['active_wars'].reverse()
                plan = self.plan(current, steps)
                self.assertEqual(plan['selected_step'], 'surrender-war-99')

    def test_multiple_qualified_terminals_choose_stable_full_war_id(self) -> None:
        snapshot = _with_terminal(_with_terminal(_ready_white_peace_snapshot(), 101), 99)
        steps = ('offer-white-peace-88', 'surrender-war-99', 'surrender-war-101', 'life-advance')
        for order in ((88, 101, 99), (99, 88, 101), (101, 99, 88)):
            with self.subTest(order=order):
                current = copy.deepcopy(snapshot)
                by_id = {row['war_id']: row for row in current['active_wars']}
                current['active_wars'] = [by_id[war_id] for war_id in order]
                self.assertEqual(self.plan(current, steps)['selected_step'], 'surrender-war-99')

    def test_existing_surrender_readiness_and_missing_literal_are_preserved(self) -> None:
        base = _with_terminal(_ready_white_peace_snapshot())
        for fault in ('missing_response', 'stale_frame', 'defender', 'nonterminal_score'):
            with self.subTest(fault=fault):
                current = copy.deepcopy(base)
                war = current['active_wars'][1]
                option = current['war_termination_options'][1]
                if fault == 'missing_response':
                    option['options']['surrender']['recipient_response'] = {
                        'status': 'unavailable', 'decision_status_raw': None, 'would_accept_now': None,
                    }
                elif fault == 'stale_frame':
                    option['queried_native_revision'] -= 1
                elif fault == 'defender':
                    war['player_side'] = option['player_side'] = 'defender'
                else:
                    war['player_relative_war_score'] = option['player_relative_war_score'] = -99
                    option['attacker_war_score'], option['defender_war_score'] = -99, 99
                plan = self.plan(current, ('offer-white-peace-88', 'surrender-war-99', 'life-advance'))
                self.assertEqual(plan['selected_step'], 'offer-white-peace-88')
        missing = self.plan(base, ('offer-white-peace-88', 'life-advance'))
        self.assertEqual(missing['phase'], 'native_war_terminal_score_surrender_unsupported')
        self.assertIsNone(missing['selected_step'])
        self.assertEqual(missing['required_step'], 'surrender-war-99')

    def test_same_war_submission_latch_and_white_peace_cooldown_are_preserved(self) -> None:
        base = _with_terminal(_ready_white_peace_snapshot())
        base['active_wars'] = [base['active_wars'][1]]
        base['war_termination_options'] = [base['war_termination_options'][1]]
        steps = ('surrender-war-99', 'life-advance')
        for elapsed, phase, selected in (
            (0, 'native_war_surrender_response_advance', 'life-advance'),
            (24, 'native_war_surrender_postcondition_unresolved', None),
        ):
            with self.subTest(surrender_elapsed=elapsed):
                current = copy.deepcopy(base)
                current['native_command_history'] = [_submission(current, outcome='attacker_defeat', war_id=99)]
                current['date_raw'] += elapsed
                plan = self.plan(current, steps)
                self.assertEqual(plan['phase'], phase)
                self.assertEqual(plan['selected_step'], selected)
        pending_wp = copy.deepcopy(base)
        pending_wp['native_command_history'] = [_submission(pending_wp, outcome='white_peace', war_id=99)]
        plan = self.plan(pending_wp, steps)
        self.assertEqual(plan['phase'], 'native_war_white_peace_response_advance')
        self.assertEqual(plan['selected_step'], 'life-advance')

    def test_cross_war_enforce_demands_retains_precedence(self) -> None:
        snapshot = _with_terminal(_ready_white_peace_snapshot())
        snapshot['active_wars'].append(_war(
            war_id=100, score=100, allied_armies=[], enemy_armies=[],
        ))
        steps = ('offer-white-peace-88', 'surrender-war-99', 'enforce-demands-100', 'life-advance')
        for reverse in (False, True):
            with self.subTest(reverse=reverse):
                current = copy.deepcopy(snapshot)
                if reverse:
                    current['active_wars'].reverse()
                plan = self.plan(current, steps)
                self.assertEqual(plan['phase'], 'native_war_enforce_demands')
                self.assertEqual(plan['selected_step'], 'enforce-demands-100')


if __name__ == '__main__':
    unittest.main()
