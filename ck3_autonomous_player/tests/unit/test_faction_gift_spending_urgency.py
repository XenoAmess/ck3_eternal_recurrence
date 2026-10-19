"""Actual narrow gift projection; source-only planner tests, never Native IO."""
from copy import deepcopy
import json
from pathlib import Path
import threading

import pytest

from xar_autoplayer.bridge import faction_gift_formal_route_v1 as route
from xar_autoplayer.faction_gift_policy_v1 import choose_faction_gift_v1
from xar_autoplayer.faction_gift_pending_v1 import begin_faction_gift_submission_v1

PROJECTION = json.loads((Path(__file__).parent / 'fixtures' /
                       'faction_gift_actual_0515_0531_projection.json').read_text(encoding='utf-8'))


def data():
    candidate = deepcopy(PROJECTION['actual_candidate'])
    actual = PROJECTION['planning_source_frame']
    frame = {
        'snapshot_id': actual['snapshot_id'], 'revision': actual['revision'],
        'native_revision': actual['native_revision'], 'date_raw': actual['date_raw'],
        'episode_run_id': actual['episode_run_id'], 'paused': True, 'map_ready': True,
        'played_character': {'character_id': actual['actor_character_id'], 'alive': True},
    }
    # Root/readiness envelopes are explicitly synthetic, populated by actual
    # source-Faction/recipient/frame/metrics; no original Native packet is forged.
    root = {'command': 'query-campaign-root-context-v1', 'ok': True, 'result': {
        'status': 'available', 'campaign_root_context': {
            'status': 'available', 'snapshot_revision': frame['native_revision'],
            'date_raw': frame['date_raw'], 'player_character_id': 31254,
            'player_character_alive': True, 'government': {'key': 'feudal_government'},
            'player_targeting_faction_count': 1, 'direct_landed_vassal_character_ids': [33946],
        }}}
    row = deepcopy(PROJECTION['war_entry_faction_context']['factions'][0])
    row.update({'target_character_id': 31254, 'leader_character_id': 33946,
                'character_member_ids': [33946]})
    alert = {'command': 'query-player-faction-alerts-v1', 'ok': True, 'result': {
        'player_faction_alerts': {
            'status': 'available', 'snapshot_revision': frame['native_revision'],
            'date_raw': frame['date_raw'], 'player_character_id': 31254,
            'readiness': {'targeting_rows_ready': True, 'stock_dangerous_predicate_ready': True,
                          'same_frame_ready': True}, 'targeting_factions': [row],
        }}}
    return candidate, frame, [root, alert], deepcopy(PROJECTION['base_plan_for_replay'])


class Driver:
    def __init__(self, state_dir, frame, candidate):
        self.state_dir = state_dir
        self.current = frame
        self.candidate = candidate
        self._driver_state_lock = threading.RLock()
        self._last_checkpoint = {'status': 'saved', 'sha256': 'a' * 64,
                                 'date_raw': frame['date_raw'],
                                 'episode_run_id': frame['episode_run_id']}
        self._session_bridge_pid = 111  # Synthetic, never queried without a mock.
        self.candidate_reads = 0
        self.readonly_calls = []

    def query_faction_gift_private_candidate_v1(self, **kwargs):
        self.candidate_reads += 1
        return deepcopy(self.candidate)

    def capabilities(self):
        return {'bridge_capabilities': []}

    def take_internal_semantic_snapshot(self):
        return deepcopy(self.current)


def run(tmp_path, *, alter=None, checkpoint=True):
    candidate, frame, history, planned = data()
    if alter:
        alter(candidate, frame, history, planned)
    driver = Driver(tmp_path, frame, candidate)
    if not checkpoint:
        driver._last_checkpoint = None
    out = route.plan_faction_gift_private_v1(driver, planned, frame, history, {'save-checkpoint'})
    return out, driver


def test_actual_515_watch_stays_ordinary_despite_legal_funded_gift(tmp_path):
    observation = PROJECTION['actual_candidate']['observation']
    original_choice = choose_faction_gift_v1(
        [observation], complete_native_enumeration=True, minimum_gold_reserve_raw=10000000)
    if original_choice.status != 'selected':
        raise ValueError('actual former legal/budget selection was not reproduced')
    out, driver = run(tmp_path)
    if out['plan']['selected_step'] != 'life-advance':
        raise ValueError('watch faction wrongly creates new gift/checkpoint')
    if out['plan']['faction_gift_stock_threat_v1']['dangerous_response_ready'] is not False:
        raise ValueError('actual stock non-danger flag changed')
    if out['plan']['prewar_force_query']['status'] != 'unsupported':
        raise ValueError('unsupported prewar was promoted to ready')
    if any(tmp_path.iterdir()) or driver.candidate_reads != 1:
        raise ValueError('read-only watch fixture created state or replayed query')
    receipt = PROJECTION['actual_receipt_0531']
    if (receipt['post_player_gold_raw'] != 15810153 or receipt['post_recipient_opinion_of_player'] != 7
            or receipt['threat_resolved'] is not False or receipt['faction_dissolved'] is not False):
        raise ValueError('actual 531 material receipt changed')


@pytest.mark.parametrize('checkpoint,expected', [(True, route.SUBMIT_STEP), (False, 'save-checkpoint')])
def test_synthetic_same_scope_danger_keeps_original_checkpoint_submit_gate(tmp_path, checkpoint, expected):
    def dangerous(candidate, frame, history, planned):
        history[1]['result']['player_faction_alerts']['targeting_factions'][0]['dangerous_by_stock_rule'] = True
    out, driver = run(tmp_path, alter=dangerous, checkpoint=checkpoint)
    if out['plan']['selected_step'] != expected or driver.candidate_reads != 1:
        raise ValueError('same-source dangerous candidate lost original gate')
    if any(tmp_path.iterdir()):
        raise ValueError('planner created a spending ledger')


@pytest.mark.parametrize('field', ['snapshot_revision', 'date_raw', 'player_character_id'])
def test_wrong_alert_frame_does_not_authorize_spend(tmp_path, field):
    def stale(candidate, frame, history, planned):
        raw = history[1]['result']['player_faction_alerts']
        raw[field] += 1
        raw['targeting_factions'][0]['dangerous_by_stock_rule'] = True
    out, _ = run(tmp_path, alter=stale)
    if out['plan']['selected_step'] != 'life-advance':
        raise ValueError('stale alert authorized a new gift')


@pytest.mark.parametrize('different', ['recipient', 'source_faction', 'at_war'])
def test_danger_does_not_cross_selected_recipient_faction_or_war(tmp_path, different):
    def wrong(candidate, frame, history, planned):
        row = history[1]['result']['player_faction_alerts']['targeting_factions'][0]
        row['dangerous_by_stock_rule'] = True
        if different == 'recipient':
            row['leader_character_id'] = 999
            row['character_member_ids'] = [999]
        elif different == 'source_faction':
            row['faction_id'] = 55
        else:
            row['faction_at_war'] = True
    out, _ = run(tmp_path, alter=wrong)
    if out['plan']['selected_step'] != 'life-advance':
        raise ValueError('unrelated or war faction authorized peaceful gift')


def test_unavailable_alert_keeps_ordinary_plan_and_records_unknown(tmp_path):
    def missing(candidate, frame, history, planned):
        history.pop()
    out, _ = run(tmp_path, alter=missing)
    if (out['plan']['selected_step'] != 'life-advance'
            or out['plan']['faction_gift_stock_threat_v1']['status'] != 'unavailable'):
        raise ValueError('unknown was blocked or mislabeled as known safe/no-op')


@pytest.mark.parametrize('same_process,expected', [(True, route.RECEIPT_STEP), (False, route.COLD_RECOVERY_STEP)])
def test_pending_is_verified_before_new_spending_filter(tmp_path, monkeypatch, same_process, expected):
    candidate, frame, history, planned = data()
    observation = candidate['observation']
    # Synthetic Windows birth identities preserve the same/new process cases.
    source_birth = '20261019131054.525692+480'
    observed_birth = source_birth if same_process else '20261019051054.525693+000'
    begin_faction_gift_submission_v1(
        tmp_path, request_id='faction-gift-existing-515', episode_run_id=frame['episode_run_id'],
        source_round_id='R515', source_bridge_pid=111,
        source_bridge_creation_date=source_birth, observation=observation,
        minimum_gold_reserve_raw=10000000, checkpoint_sha256_before_submit='a' * 64)
    frame['native_revision'] += 1
    driver = Driver(tmp_path, frame, candidate)
    if not same_process:
        driver._session_bridge_pid = 222
    monkeypatch.setattr(route, '_process_identity', lambda pid: {'creation_date': observed_birth})
    out = route.plan_faction_gift_private_v1(driver, planned, frame, [], set())
    if out['plan']['selected_step'] != expected or driver.candidate_reads != 0:
        raise ValueError('existing pending was subjected to new-spend policy or resubmitted')
    if 'faction_gift_stock_threat_v1' in out['plan']:
        raise ValueError('pending incorrectly reclassified by urgency gate')


def test_mandatory_plan_is_unchanged(tmp_path):
    candidate, frame, history, planned = data()
    planned['plan']['selected_step'] = 'choose-event-option-0'
    driver = Driver(tmp_path, frame, candidate)
    out = route.plan_faction_gift_private_v1(driver, planned, frame, history, set())
    if out is not planned or driver.candidate_reads:
        raise ValueError('mandatory choice was displaced by gift policy')
