"""Actual owned-prefix facts; all new final-legal rows/frames are synthetic."""
from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from xar_autoplayer import lifestyle_min_policy as policy
from xar_autoplayer import optional_check_cadence_v1 as cadence
from xar_autoplayer.bridge import player_lifestyle_private_transport_v1 as transport


def snapshot(points: int, legal: list[str], owned: list[str]) -> dict:
    return {
        'status': 'available', 'snapshot_id': 'native:3498',
        'episode_run_id': 'native-40526-c7a6edcc32b8',
        'public_revision': 3498, 'native_revision': 3498,
        'proof_epoch': 3498, 'date_raw': 53410032,
        'player_character_id': 40526,
        'current_focus': {'presence': 'present',
                          'key': 'stewardship_wealth_focus',
                          'lifestyle_key': 'stewardship_lifestyle'},
        'current_lifestyle_progress': {'presence': 'present',
                                       'lifestyle_key': 'stewardship_lifestyle',
                                       'unspent_perk_points': points},
        'owned_perk_keys': owned,
        'legal_perk_candidates': {
            'status': 'available', 'scope': 'policy_target',
            'items': [{'key': key, 'lifestyle_key': 'stewardship_lifestyle'}
                      for key in legal],
        },
        'readiness': {key: True for key in (
            'current_focus_ready', 'lifestyle_progress_ready',
            'owned_perks_ready', 'same_frame_ready',
            'legal_perk_candidates_ready')},
    }


OWNED_AT_P21 = [
    'bellum_justum_perk', 'cutting_corners_perk',
    'professional_workforce_perk', 'tax_man_perk',
    'centralization_perk',
]


def choose(value: dict) -> dict:
    return policy.choose_min_feudal_lifestyle_action(
        value, feudal_scope_admitted=True, at_peace=False,
        allow_wartime_perk=True, collect_taxes_active=False)


def test_actual_owned_prefix_and_synthetic_native_next_frontier_selects_perk():
    result = choose(snapshot(1, ['defensive_measures_perk'], OWNED_AT_P21))
    assert result['status'] == 'recommend_action'
    assert result['selected_action']['target_key'] == 'defensive_measures_perk'
    assert result['selected_action']['expected']['expected_date_raw'] == 53410032
    query = {'snapshot': snapshot(1, ['defensive_measures_perk'], OWNED_AT_P21)}
    assert transport._native_perk_target_token('defensive_measures_perk')
    assert transport._target_in_final_legal_perks(
        query, 'defensive_measures_perk', 'stewardship_lifestyle')


def test_no_candidate_with_positive_point_is_explicit_and_does_not_invent_one():
    result = choose(snapshot(1, [], OWNED_AT_P21))
    assert result['status'] == 'no_legal_minimum'
    assert result['reason'] == 'no_native_final_legal_candidate'
    assert result['unspent_perk_points'] == 1
    assert result['selected_action'] is None


def test_zero_point_is_distinct_and_foreign_or_owned_row_cannot_dispatch():
    zero = choose(snapshot(0, ['defensive_measures_perk'], OWNED_AT_P21))
    assert zero['reason'] == 'no_unspent_points'
    owned = choose(snapshot(1, ['tax_man_perk'], OWNED_AT_P21))
    assert owned['status'] == 'observation_unavailable'
    foreign = snapshot(1, ['defensive_measures_perk'], OWNED_AT_P21)
    foreign['legal_perk_candidates']['items'][0]['lifestyle_key'] = 'martial_lifestyle'
    assert choose(foreign)['reason'] == 'no_native_final_legal_candidate'
    assert not transport._target_in_final_legal_perks(
        {'snapshot': foreign}, 'defensive_measures_perk', 'stewardship_lifestyle')


def test_authored_domain_frontier_precedes_other_legal_management_roots():
    value = snapshot(1, ['golden_obligations_perk', 'defensive_measures_perk'],
                     OWNED_AT_P21)
    assert choose(value)['selected_action']['target_key'] == 'defensive_measures_perk'
    assert not transport._native_perk_target_token('../unsafe_perk')


def test_stewardship_fallback_is_bounded_to_authored_catalogue():
    assert len(policy._STEWARDSHIP_AUTHORED_PERKS) == 27
    assert (transport.PERK_TARGETS - {
        'serve_the_crown_perk', 'thoughtful_perk'
    }) == policy._STEWARDSHIP_AUTHORED_PERKS
    value = snapshot(1, ['tax_man_perk', 'defensive_measures_perk'],
                     [key for key in OWNED_AT_P21 if key != 'tax_man_perk'])
    assert choose(value)['selected_action']['target_key'] == 'tax_man_perk'
    value['legal_perk_candidates']['items'].append({
        'key': 'unreviewed_perk', 'lifestyle_key': 'stewardship_lifestyle'})
    result = choose(value)
    assert result['status'] == 'observation_unavailable'
    assert result['reason'] == 'outside_authored_stewardship_frontier'


def test_other_lifestyles_keep_existing_single_target_policy():
    value = snapshot(1, ['unknown_second_perk'], [])
    value['current_focus']['lifestyle_key'] = 'martial_lifestyle'
    value['current_lifestyle_progress']['lifestyle_key'] = 'martial_lifestyle'
    value['legal_perk_candidates']['items'][0]['lifestyle_key'] = 'martial_lifestyle'
    result = choose(value)
    assert result['status'] == 'no_legal_minimum'
    assert result['selected_action'] is None


def test_native_catalogue_upgrade_requalifies_only_lifestyle_once(tmp_path):
    episode = 'native-40526-c7a6edcc32b8'
    for domain in ('lifestyle', 'council'):
        for date in (53410032, 53410056, 53410080):
            cadence.record(tmp_path, domain, (episode, date, 3498),
                           actual_action=False)
    current = (episode, 53410104, 3499)
    assert cadence.deferred(tmp_path, 'lifestyle', current) is not None
    assert cadence.deferred(tmp_path, 'council', current) is not None
    catalogue = 'game.state.private-lifestyle-stewardship-frontier-v2'
    assert cadence.requalify_lifestyle_frontier_once(
        tmp_path, current, native_catalogue=catalogue)
    assert cadence.deferred(tmp_path, 'lifestyle', current) is None
    assert cadence.deferred(tmp_path, 'council', current) is not None
    assert not cadence.requalify_lifestyle_frontier_once(
        tmp_path, current, native_catalogue=catalogue)
    assert cadence._load(tmp_path, episode)['domains']['lifestyle'][
        'last_actual_action_frame'] is None


def test_public_service_requalifies_only_on_new_native_capability(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from xar_autoplayer.bridge import service
    catalogue = 'game.state.private-lifestyle-stewardship-frontier-v2'
    episode = 'native-40526-c7a6edcc32b8'
    for has_cap in (False, True):
        state_dir = tmp_path / str(has_cap)
        for domain in ('lifestyle', 'council'):
            for date in (53410032, 53410056, 53410080):
                cadence.record(state_dir, domain, (episode, date, 3498), actual_action=False)
        calls = []
        monkeypatch.setattr(service, '_optional_check_lifestyle_original',
                            lambda _self, planned, _steps: calls.append(True) or planned)
        driver = SimpleNamespace(state_dir=state_dir, capabilities=lambda: {
            'bridge_capabilities': [catalogue] if has_cap else []})
        receiver = SimpleNamespace(driver=driver)
        planned = {'plan': {'selected_step': 'life-advance-one-day'},
                   '_private_m5_snapshot_v1': {'episode_run_id': episode, 'paused': True,
                       'date_raw': 53410104, 'native_revision': 3499}}
        result = service._optional_check_lifestyle(receiver, planned, set())
        assert len(calls) == int(has_cap)
        assert ('lifestyle_periodic_review' in result['plan']) is not has_cap
        assert cadence.deferred(state_dir, 'council', (episode, 53410104, 3499)) is not None
        assert cadence._load(state_dir, episode)['domains']['lifestyle'][
            'last_actual_action_frame'] is None
        if has_cap:
            # A later ordinary cooldown must survive the already-seen catalogue.
            for date in (53410128, 53410152):
                cadence.record(state_dir, 'lifestyle', (episode, date, 3499), actual_action=False)
            planned['_private_m5_snapshot_v1']['date_raw'] = 53410176
            result = service._optional_check_lifestyle(receiver, planned, set())
            assert len(calls) == 1
            assert 'lifestyle_periodic_review' in result['plan']


def test_public_service_import_and_new_perk_material_projection():
    from types import SimpleNamespace
    from xar_autoplayer.bridge import service
    assert service.PERK_TARGETS is transport.PERK_TARGETS
    before = {
        "snapshot_id": "native:3498", "revision": 3498,
        "native_revision": 3498, "date_raw": 53410032,
        "episode_run_id": "native-40526-c7a6edcc32b8",
        "played_character": {"character_id": 40526},
    }
    after = {**before, "paused": True}
    query = {
        "status": "available", "episode_run_id": before["episode_run_id"],
        "source_frame": {
            **{key: before[key] for key in (
                "snapshot_id", "revision", "native_revision", "date_raw")},
            "player_character_id": 40526,
        },
        "snapshot": {
            "readiness": {key: True for key in (
                "same_frame_ready", "legal_perk_candidates_ready", "owned_perks_ready")},
            "legal_perk_candidates": {
                "status": "available", "scope": "policy_target",
                "items": [{"key": "defensive_measures_perk",
                           "lifestyle_key": "stewardship_lifestyle"}],
            },
            "owned_perk_keys": ["tax_man_perk"],
            "current_focus": {"key": "stewardship_wealth_focus",
                              "lifestyle_key": "stewardship_lifestyle"},
        },
    }


    class Receiver:
        driver = SimpleNamespace(allow_private_lifestyle_formal_trial=True)

        def snapshot(self, *, include_native_command_history=None):
            assert include_native_command_history in (None, False)
            return after


    observed = service.GameplayBridgeService._observe_opening_lifestyle_perks_v1(
        Receiver(), before=before,
        focus={"key": "stewardship_wealth_focus",
               "lifestyle_key": "stewardship_lifestyle"},
        revision=3498, formal_query=query,
    )
    assert observed["status"] == "observed", observed
    assert observed["policy_target_final_legal"]["defensive_measures_perk"] is True
    assert observed["policy_target_owned"]["defensive_measures_perk"] is False
    assert observed["policy_target_owned"]["tax_man_perk"] is True
    assert len(observed["policy_target_final_legal"]) == 29
