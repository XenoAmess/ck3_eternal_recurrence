"""Synthetic native verdicts plus pinned actual Steam 1.20.0.4 authored keys."""

from pathlib import Path
import json
import sys

_here = Path(__file__).resolve().parent
_candidate_source = _here / 'sdk-candidate/src'
sys.path.insert(0, str(_candidate_source if _candidate_source.is_dir()
                       else Path(__file__).resolve().parents[2] / 'src'))

from xar_autoplayer.all_lifestyle_catalog_v1 import LIFESTYLE_KEYS, authored_perks
from xar_autoplayer.lifestyle_min_policy import choose_min_feudal_lifestyle_action
from xar_autoplayer.bridge.player_lifestyle_private_transport_v1 import PERK_TARGETS
from xar_autoplayer.bridge.player_lifestyle_private_transport_v1 import (
    query_player_lifestyle_private_v1, submit_player_lifestyle_perk_private_v1,
)
from xar_autoplayer.lifestyle_formal_consumer import (
    same_frame_feudal_lifestyle_scope, same_frame_player_lifestyle_perk_scope,
    consume_lifestyle_private_query,
)


EPISODE = 'native-40526-test'
ORDER = sorted(LIFESTYLE_KEYS)


def snapshot(target: str | None, *, current='stewardship_lifestyle',
             positive='stewardship_lifestyle', unknown=None, points=1):
    owners = authored_perks()
    rows = []
    for lifestyle in ORDER:
        unavailable = lifestyle == unknown
        rows.append({
            'status': 'unavailable' if unavailable else 'available',
            'lifestyle_key': lifestyle,
            'xp_total_raw': None if unavailable else 1000,
            'xp_within_level_raw': None if unavailable else 0,
            'xp_per_level': None if unavailable else 1000,
            'unspent_perk_points': None if unavailable else points if lifestyle == positive else 0,
            'used_perk_points': None if unavailable else 2,
            'unavailable_reason': 'native_progress_unavailable' if unavailable else None,
        })
    return {
        'status': 'available', 'snapshot_id': 'native:3498',
        'episode_run_id': EPISODE, 'public_revision': 3498,
        'native_revision': 3498, 'proof_epoch': 3498,
        'date_raw': 53410032, 'player_character_id': 40526,
        'current_focus': {'presence': 'present', 'key': current+'_focus',
                          'lifestyle_key': current},
        'current_lifestyle_progress': {'presence': 'present',
                                       'lifestyle_key': current,
                                       'unspent_perk_points': 0 if current != positive else points},
        'owned_perk_keys': [],
        'legal_perk_candidates': {
            'status': 'available', 'scope': 'policy_target',
            'items': [] if target is None else [{'key': target,
                                                  'lifestyle_key': owners[target]}],
        },
        'readiness': {key: True for key in (
            'current_focus_ready', 'lifestyle_progress_ready',
            'owned_perks_ready', 'same_frame_ready',
            'legal_perk_candidates_ready')},
        'all_lifestyle_progress_v3': {
            'status': 'partial' if unknown else 'complete',
            'snapshot_id': 'native:3498', 'native_revision': 3498,
            'date_raw': 53410032, 'player_character_id': 40526,
            'episode_run_id': EPISODE, 'rows': rows,
        },
    }


def choose(value):
    return choose_min_feudal_lifestyle_action(
        value, feudal_scope_admitted=True, at_peace=False,
        allow_wartime_perk=True)


def test_actual_catalogue_six_lifestyles_162_targets_and_one_native_target_each():
    owners = authored_perks()
    assert len(owners) == len(PERK_TARGETS) == 162
    assert {key: list(owners.values()).count(key) for key in LIFESTYLE_KEYS} == {
        key: 27 for key in LIFESTYLE_KEYS}
    for lifestyle in ORDER:
        target = next(key for key, owner in owners.items() if owner == lifestyle)
        result = choose(snapshot(target, positive=lifestyle))
        assert result['status'] == 'recommend_action', (lifestyle, result)
        assert result['selected_action']['target_key'] == target
        assert result['selected_action']['target_lifestyle_key'] == lifestyle
        assert result['selected_action']['expected']['expected_date_raw'] == 53410032


def test_required_catalogue_is_declared_as_installed_package_data():
    import fnmatch
    import tomllib
    project = Path(__file__).resolve().parents[2]
    config = tomllib.loads((project / 'pyproject.toml').read_text(encoding='utf-8'))
    patterns = config['tool']['setuptools']['package-data']['xar_autoplayer']
    assert any(fnmatch.fnmatch('data/vanilla_lifestyle_catalog_12004.json', pattern)
               for pattern in patterns)


def test_cross_focus_observed_point_spends_target_lifestyle_not_current_focus():
    target = next(key for key, owner in authored_perks().items()
                  if owner == 'martial_lifestyle' and key != 'serve_the_crown_perk')
    value = snapshot(target, current='stewardship_lifestyle',
                     positive='martial_lifestyle')
    assert value['current_lifestyle_progress']['unspent_perk_points'] == 0
    action = choose(value)['selected_action']
    assert action['target_key'] == target
    assert action['target_lifestyle_key'] == 'martial_lifestyle'


def test_unpicked_parent_or_dlc_lock_is_respected_by_empty_native_final_legal():
    value = snapshot(None, positive='intrigue_lifestyle')
    result = choose(value)
    assert result['status'] == 'no_legal_minimum'
    assert result['reason'] == 'native_final_legal_none_with_unspent_points'
    assert result['observed_positive_points'] == {'intrigue_lifestyle': 1}
    assert result['selected_action'] is None


def test_complete_all_zero_is_distinct_from_positive_point_without_legal_target():
    value = snapshot(None, points=0)
    result = choose(value)
    assert result['status'] == 'no_legal_minimum'
    assert result['reason'] == 'no_unspent_points_across_all_lifestyles'
    assert result['observed_positive_points'] == {}


def test_unknown_class_is_not_zero_or_complete_noop():
    value = snapshot(None, positive='learning_lifestyle', unknown='wanderer_lifestyle')
    result = choose(value)
    assert result['status'] == 'observation_unavailable'
    assert result['reason'] == 'progress_partial_no_target'
    target = next(key for key, owner in authored_perks().items()
                  if owner == 'learning_lifestyle')
    value['legal_perk_candidates']['items'] = [{'key': target,
                                                'lifestyle_key': 'learning_lifestyle'}]
    assert choose(value)['status'] == 'recommend_action'


def test_stale_or_foreign_or_owned_native_target_never_authorizes_submit():
    target = next(key for key, owner in authored_perks().items()
                  if owner == 'wanderer_lifestyle')
    value = snapshot(target, positive='wanderer_lifestyle')
    value['all_lifestyle_progress_v3']['date_raw'] += 24
    assert choose(value)['status'] == 'observation_unavailable'
    value['all_lifestyle_progress_v3']['date_raw'] -= 24
    value['legal_perk_candidates']['items'][0]['lifestyle_key'] = 'martial_lifestyle'
    assert choose(value)['status'] == 'observation_unavailable'
    value['legal_perk_candidates']['items'][0]['lifestyle_key'] = 'wanderer_lifestyle'
    value['owned_perk_keys'] = [target]
    assert choose(value)['reason'] == 'native_legal_target_already_owned'
    value['owned_perk_keys'] = []
    for row in value['all_lifestyle_progress_v3']['rows']:
        if row['lifestyle_key'] == 'wanderer_lifestyle':
            row['unspent_perk_points'] = 0
    assert choose(value)['reason'] == 'target_progress_not_positive'


def test_legacy_candidate_readiness_still_required_with_native_v3():
    target = next(key for key, owner in authored_perks().items()
                  if owner == 'diplomacy_lifestyle')
    value = snapshot(target, positive='diplomacy_lifestyle')
    value['readiness']['legal_perk_candidates_ready'] = False
    assert choose(value)['status'] == 'observation_unavailable'


def test_nonfeudal_root_scope_allows_native_gated_perk_but_not_initial_focus():
    frame = {'paused': True, 'active_wars': [], 'snapshot_id': 'native:3498',
             'revision': 3498, 'native_revision': 3498, 'date_raw': 53410032,
             'played_character': {'character_id': 40526}}
    history = [{'command': 'query-campaign-root-context-v1', 'ok': True,
                'result': {'campaign_root_context': {
                    'status': 'available', 'snapshot_revision': 3498,
                    'date_raw': 53410032, 'player_character_id': 40526,
                    'government': {'key': 'landless_adventurer_government',
                                   'flags': ['government_is_landless_adventurer']}}}}]
    assert same_frame_feudal_lifestyle_scope(frame, history)['status'] == 'outside_scene'
    scope = same_frame_player_lifestyle_perk_scope(frame, history)
    assert scope['status'] == 'admitted'
    assert scope['government_key'] == 'landless_adventurer_government'
    from types import SimpleNamespace
    from xar_autoplayer.bridge import service
    for advertised, opening_focus, expected_status in (
        (True, False, 'admitted'), (False, False, 'outside_scene'),
        (True, True, 'outside_scene'),
    ):
        receiver = SimpleNamespace(driver=SimpleNamespace(
            require_initial_lifestyle_focus_before_date_advance=opening_focus,
            capabilities=lambda: {'bridge_capabilities': [
                'game.state.private-lifestyle-all-frontier-v3'] if advertised else []}))
        actual = service._player_lifestyle_perk_scope(receiver, frame, history)
        assert actual['status'] == expected_status
    target = next(key for key, owner in authored_perks().items()
                  if owner == 'wanderer_lifestyle')
    assert choose(snapshot(target, positive='wanderer_lifestyle'))['status'] == 'recommend_action'
    absent = snapshot(None)
    absent['current_focus'] = {'presence': 'absent'}
    absent['current_lifestyle_progress'] = {'presence': 'absent'}
    assert choose_min_feudal_lifestyle_action(
        absent, feudal_scope_admitted=True, at_peace=True,
        focus_scope_admitted=False)['reason'] == 'initial_focus_remains_feudal_scoped'


def test_transport_binds_native_progress_sibling_and_rejects_unadvertised_or_stale():
    from types import SimpleNamespace

    target = next(key for key, owner in authored_perks().items()
                  if owner == 'learning_lifestyle')
    life = snapshot(target, positive='learning_lifestyle')
    native_v3_sibling = life.pop('all_lifestyle_progress_v3')
    before = {'paused': True, 'map_ready': True, 'revision': 4,
              'native_revision': 3498, 'snapshot_id': 'native:3498',
              'date_raw': 53410032, 'episode_run_id': EPISODE,
              'played_character': {'character_id': 40526}}
    native_result = {'step': 'private-query-player-lifestyle-formal-v1',
                     'private_build': True, 'advertised': False,
                     'status': 'available', 'episode_run_id': EPISODE,
                     'formal_precondition_status': 'ready',
                     'snapshot': life,
                     'all_lifestyle_progress_v3': native_v3_sibling}
    class Endpoint:
        request = None
        def send(self, value):
            self.request = value

    endpoint = Endpoint()
    def wait(request_id, _timeout):
        assert endpoint.request['request_id'] == request_id
        return {'request_id': request_id, 'ok': True, 'result': native_result}

    capabilities = {'bridge_capabilities': ['game.state.private-lifestyle-all-frontier-v3']}
    driver = SimpleNamespace(allow_private_lifestyle_formal_trial=True,
                             take_internal_semantic_snapshot=lambda: before,
                             endpoint=endpoint,
                             state=SimpleNamespace(wait_for_command_result=wait),
                             command_timeout_seconds=1,
                             capabilities=lambda: capabilities)
    result = query_player_lifestyle_private_v1(driver, expected_revision=4)
    assert result['status'] == 'available', result
    assert result['snapshot']['all_lifestyle_progress_v3']['status'] == 'complete'
    assert choose(result['snapshot'])['selected_action']['target_key'] == target
    native_result['all_lifestyle_progress_v3'] = {
        **native_v3_sibling, 'date_raw': 53410056}
    assert query_player_lifestyle_private_v1(driver, expected_revision=4)[
        'reason'] == 'all_lifestyle_progress_v3_missing_or_stale'
    native_result['all_lifestyle_progress_v3'] = native_v3_sibling
    capabilities['bridge_capabilities'] = []
    assert query_player_lifestyle_private_v1(driver, expected_revision=4)[
        'reason'] == 'all_lifestyle_progress_v3_unadvertised'


def test_v3_catalogue_requalifies_lifestyle_cd_once_and_unknown_never_counts(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from xar_autoplayer import optional_check_cadence_v1 as cadence
    from xar_autoplayer.bridge import service

    previous = 'game.state.private-lifestyle-stewardship-frontier-v2'
    upgraded = 'game.state.private-lifestyle-all-frontier-v3'
    first = (EPISODE, 53410032, 3498)
    cadence.requalify_lifestyle_frontier_once(tmp_path, first,
                                               native_catalogue=previous)
    for name in ('lifestyle', 'council'):
        for date in (53410032, 53410056, 53410080):
            cadence.record(tmp_path, name, (EPISODE, date, 3498), actual_action=False)
    calls = []
    decision = {'status': 'observation_unavailable'}
    def original(_self, planned, _steps):
        calls.append(True)
        return {**planned, 'plan': {**planned['plan'], 'lifestyle_decision': decision}}
    monkeypatch.setattr(service, '_optional_check_lifestyle_original', original)
    driver = SimpleNamespace(state_dir=tmp_path, capabilities=lambda: {
        'bridge_capabilities': [upgraded]})
    receiver = SimpleNamespace(driver=driver)
    planned = {'plan': {'selected_step': 'life-advance'},
               '_private_m5_snapshot_v1': {'episode_run_id': EPISODE,
                                            'paused': True, 'date_raw': 53410104,
                                            'native_revision': 3499}}
    service._optional_check_lifestyle(receiver, planned, set())
    row = cadence._load(tmp_path, EPISODE)['domains']['lifestyle']
    assert calls == [True]
    assert row['native_catalogue'] == upgraded
    assert row['consecutive_no_action'] == 0
    assert row['last_check_frame'] is None
    assert cadence.deferred(tmp_path, 'council', (EPISODE, 53410104, 3499)) is not None
    # Same unavailable read does not become the first no-op of a new cooldown.
    service._optional_check_lifestyle(receiver, planned, set())
    assert cadence._load(tmp_path, EPISODE)['domains']['lifestyle'][
        'last_check_frame'] is None
    decision = {'status': 'no_legal_minimum', 'reason': 'native_final_legal_none_with_unspent_points'}
    service._optional_check_lifestyle(receiver, planned, set())
    assert cadence._load(tmp_path, EPISODE)['domains']['lifestyle'][
        'consecutive_no_action'] == 1


def test_without_v3_capability_old_stewardship_and_war_martial_policy_remain():
    stewardship = snapshot('defensive_measures_perk')
    stewardship.pop('all_lifestyle_progress_v3')
    assert choose(stewardship)['selected_action']['target_key'] == 'defensive_measures_perk'
    martial = snapshot('serve_the_crown_perk', current='martial_lifestyle',
                       positive='martial_lifestyle')
    martial.pop('all_lifestyle_progress_v3')
    assert choose(martial)['selected_action']['target_key'] == 'serve_the_crown_perk'


def test_consumer_cross_focus_nonfeudal_uses_existing_typed_submit_and_pending_guard():
    target = next(key for key, owner in authored_perks().items()
                  if owner == 'wanderer_lifestyle')
    value = snapshot(target, positive='wanderer_lifestyle')
    baseline = {'selected_step': 'life-advance', 'phase': 'ordinary'}
    scope = {'status': 'admitted', 'at_peace': True,
             'government_key': 'landless_adventurer_government'}
    query = {'status': 'available', 'snapshot': value,
             'formal_precondition_status': 'ready'}
    result = consume_lifestyle_private_query(baseline, scope=scope, query=query)
    assert result['selected_step'] == 'private-select-player-lifestyle-perk-v1'
    assert result['lifestyle_action']['target_key'] == target
    assert result['lifestyle_action']['target_lifestyle_key'] == 'wanderer_lifestyle'
    query['snapshot'] = {**value, 'all_lifestyle_progress_v3': {
        **value['all_lifestyle_progress_v3'], 'native_revision': 3499}}
    stale = consume_lifestyle_private_query(baseline, scope=scope, query=query)
    assert stale['selected_step'] is None
    assert stale['lifestyle_decision']['status'] == 'observation_unavailable'


def test_service_material_projection_includes_all_six_authored_classes():
    from types import SimpleNamespace
    from xar_autoplayer.bridge import service

    target = next(key for key, owner in authored_perks().items()
                  if owner == 'intrigue_lifestyle')
    before = {'snapshot_id': 'native:3498', 'revision': 3498,
              'native_revision': 3498, 'date_raw': 53410032,
              'episode_run_id': EPISODE,
              'played_character': {'character_id': 40526}}
    after = {**before, 'paused': True}
    query = {'status': 'available', 'episode_run_id': EPISODE,
             'source_frame': {'snapshot_id': 'native:3498', 'revision': 3498,
                              'native_revision': 3498, 'date_raw': 53410032,
                              'player_character_id': 40526},
             'snapshot': {'readiness': {key: True for key in (
                 'same_frame_ready', 'legal_perk_candidates_ready',
                 'owned_perks_ready')},
                 'legal_perk_candidates': {'status': 'available',
                                           'scope': 'policy_target',
                                           'items': [{'key': target,
                                                      'lifestyle_key': 'intrigue_lifestyle'}]},
                 'owned_perk_keys': [],
                 'current_focus': {'key': 'stewardship_wealth_focus',
                                   'lifestyle_key': 'stewardship_lifestyle'}}}
    class Receiver:
        driver = SimpleNamespace(allow_private_lifestyle_formal_trial=True)
        def snapshot(self, *, include_native_command_history=None):
            assert include_native_command_history in (None, False)
            return after

    observed = service.GameplayBridgeService._observe_opening_lifestyle_perks_v1(
        Receiver(), before=before,
        focus={'key': 'stewardship_wealth_focus',
               'lifestyle_key': 'stewardship_lifestyle'},
        revision=3498, formal_query=query)
    assert service.PERK_TARGETS is PERK_TARGETS
    assert observed['status'] == 'observed', observed
    assert len(observed['policy_target_final_legal']) == 162
    assert observed['policy_target_final_legal'][target] is True
    assert observed['policy_target_owned'][target] is False


def test_cross_focus_submit_preserves_intent_then_pending_not_applied_credit():
    target = next(key for key, owner in authored_perks().items()
                  if owner == 'learning_lifestyle')
    value = snapshot(target, positive='learning_lifestyle')
    action = choose(value)['selected_action']
    source = {'snapshot_id': 'native:3498', 'revision': 4,
              'native_revision': 3498, 'date_raw': 53410032,
              'player_character_id': 40526}
    query = {'status': 'available', 'formal_precondition_status': 'ready',
             'source_frame': source, 'episode_run_id': EPISODE, 'snapshot': value}
    starting = {'paused': True, 'snapshot_id': 'native:3498',
                'revision': 4, 'native_revision': 3498,
                'date_raw': 53410032, 'episode_run_id': EPISODE}
    recorded = []
    class Endpoint:
        request = None
        def send(self, value): self.request = value
    endpoint = Endpoint()
    def wait(request_id, _timeout):
        return {'request_id': request_id, 'ok': True,
                'result': {'step': 'private-select-player-lifestyle-perk-v1',
                           'private_build': True, 'advertised': False,
                           'action_request_id': request_id, 'target_key': target,
                           'pre_snapshot_id': 'native:3498',
                           'episode_run_id': EPISODE, 'pre_public_revision': 3498,
                           'status': 'submitted_verification_pending',
                           'verification_pending': True}}
    class Driver:
        allow_private_lifestyle_formal_trial = True
        _driver_state_error = None
        command_timeout_seconds = 1
        state = type('State', (), {'wait_for_command_result': staticmethod(wait)})()
        def __init__(self): self.endpoint = endpoint
        def take_snapshot(self): return starting
        def _record_command(self, step, *, ok, result):
            recorded.append((step, ok, result['status']))
    pending = submit_player_lifestyle_perk_private_v1(
        Driver(), query=query, action=action, expected_revision=4)
    assert [row[2] for row in recorded] == [
        'action_state_unknown', 'submitted_verification_pending']
    assert endpoint.request['target_key'] == target
    assert pending['status'] == 'submitted_verification_pending'
    assert 'post_target_perk_owned' not in pending


def test_actual_native21_serializer_cross_focus_query_to_typed_plan():
    """The production C++ serializer, including Attach, reaches the SDK planner."""
    from copy import deepcopy
    from types import SimpleNamespace

    pinned = _here / 'fixture/native21-actual-query-final.json'
    if not pinned.is_file():
        pinned = _here / 'native21-actual-query-final.json'
    import hashlib
    raw = pinned.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == '64e09f8a494e86296daeeb0f8b43ac43442e58046a01030f5f2c63af7e156cc7'
    actual = json.loads(raw)
    result = actual['result']
    assert actual['ok'] is True
    assert result['snapshot']['readiness']['legal_perk_candidates_ready'] is True
    assert result['snapshot']['current_lifestyle_progress']['presence'] == 'absent'
    assert result['snapshot']['current_focus']['lifestyle_key'] == ''
    assert result['all_lifestyle_progress_v3']['status'] == 'complete'
    assert len(result['all_lifestyle_progress_v3']['rows']) == 6

    before = {
        'paused': True, 'map_ready': True, 'revision': 17,
        'native_revision': 7, 'snapshot_id': 'native:7',
        'date_raw': 53411184, 'episode_run_id': 'native-40526-fixture',
        'played_character': {'character_id': 40526},
    }

    class Endpoint:
        request = None

        def send(self, value):
            self.request = value

    endpoint = Endpoint()

    def wait(request_id, _timeout):
        assert endpoint.request['request_id'] == request_id
        answer = deepcopy(actual)
        answer['request_id'] = request_id
        return answer

    driver = SimpleNamespace(
        allow_private_lifestyle_formal_trial=True,
        take_internal_semantic_snapshot=lambda: before,
        endpoint=endpoint,
        state=SimpleNamespace(wait_for_command_result=wait),
        command_timeout_seconds=1,
        capabilities=lambda: {'bridge_capabilities': [
            'game.state.private-lifestyle-all-frontier-v3']},
    )
    query = query_player_lifestyle_private_v1(driver, expected_revision=17)
    assert query['status'] == 'available', query
    life = query['snapshot']
    assert life['all_lifestyle_progress_v3'] == result['all_lifestyle_progress_v3']
    planned = consume_lifestyle_private_query(
        {'selected_step': 'life-advance', 'phase': 'ordinary'},
        scope={'status': 'admitted', 'at_peace': True,
               'government_key': 'landless_adventurer_government'},
        query=query,
    )
    assert planned['selected_step'] == 'private-select-player-lifestyle-perk-v1'
    assert planned['lifestyle_action']['target_key'] == 'thoughtful_perk'
    assert planned['lifestyle_action']['target_lifestyle_key'] == 'diplomacy_lifestyle'
