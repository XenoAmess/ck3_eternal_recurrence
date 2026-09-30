"""An instance-bound H2743 query; it exposes no war action constructor."""
from __future__ import annotations

from .defender_dejure_exit_terms_v1 import CAPABILITY, normalize_defender_dejure_exit_terms_v1
from .driver import BridgeUnavailableError

BASELINE_STEP = 'query-defender-de-jure-exit-terms-v1-16777231'
OPTIONS_STEP = 'query-war-termination-options-16777231'
FRAME_FIELDS = ('snapshot_id', 'revision', 'native_revision', 'date_raw', 'episode_run_id')


def frame_key(frame: dict) -> tuple:
    diagnostics = frame.get('diagnostics', {})
    return tuple(frame.get(key) for key in FRAME_FIELDS) + (diagnostics.get('connection_generation'),)


def target_frame(frame: dict) -> dict | None:
    if type(frame.get('map_ready')) is not bool:
        raise BridgeUnavailableError('H2743 map readiness is malformed')
    if not frame['map_ready']:
        return None
    played = frame.get('played_character')
    wars = frame.get('active_wars')
    if frame.get('date_raw') is None or played is None or not wars:
        return None
    if (frame.get('paused') is not True or frame.get('date_raw') != 53217264
            or frame.get('episode_run_id') != 'native-29829-2bc2d599f7f9'
            or not isinstance(played, dict) or played.get('character_id') != 29829):
        raise BridgeUnavailableError('H2743 current paused actor/date/episode differs')
    matching = [row for row in wars if isinstance(row, dict) and row.get('war_id') == 16777231]
    if len(matching) != 1:
        raise BridgeUnavailableError('H2743 target war is absent or duplicated')
    war = matching[0]
    if (war.get('player_side') != 'defender' or war.get('player_is_primary_war_leader') is not True
            or war.get('primary_opponent_character_id') != 30097
            or war.get('targeted_title_ids') != [2128]):
        raise BridgeUnavailableError('H2743 target primary-defender war differs')
    if (type(frame.get('revision')) is not int or frame['revision'] <= 0
            or type(frame.get('native_revision')) is not int or frame['native_revision'] <= 0
            or not isinstance(frame.get('snapshot_id'), str)
            or type(frame.get('diagnostics', {}).get('connection_generation')) is not int
            or frame['diagnostics']['connection_generation'] <= 0):
        raise BridgeUnavailableError('H2743 native frame binding is incomplete')
    return war


def query_h2743_exit_baseline(self, *, expected_frame: dict) -> dict:
    starting = self.take_internal_semantic_snapshot()
    war = target_frame(starting)
    if war is None or frame_key(starting) != frame_key(expected_frame):
        raise BridgeUnavailableError('H2743 baseline query crossed the admitted paused frame')
    result = self._execute_primitive_step(
        BASELINE_STEP, expected_revision=starting['revision'],
        required_capability=CAPABILITY, internal_semantic_snapshot=True)
    expected_keys = {'step', 'accepted', 'status', 'query_sequence', 'defender_de_jure_exit_terms_v1', 'backend_id'}
    if (set(result) != expected_keys or result.get('step') != BASELINE_STEP
            or result.get('accepted') is not True or result.get('status') != 'baseline_only'
            or type(result.get('query_sequence')) is not int or not 0 < result['query_sequence'] <= 2**64 - 1):
        raise BridgeUnavailableError('H2743 native baseline envelope is malformed')
    baseline = normalize_defender_dejure_exit_terms_v1(
        result['defender_de_jure_exit_terms_v1'], expected_war_id=16777231,
        expected_native_revision=starting['native_revision'], expected_date_raw=53217264,
        expected_defender_id=29829, expected_attacker_id=30097, expected_target_title_ids=[2128])
    current = self.take_internal_semantic_snapshot()
    if target_frame(current) != war or frame_key(current) != frame_key(starting):
        raise BridgeUnavailableError('H2743 native baseline changed its paused war frame')
    storage = baseline.get('border_raid_storage_candidate_v1')
    if not isinstance(storage, dict) or storage.get('status') != 'structural_candidate_only':
        raise BridgeUnavailableError('H2743 full storage scan is unavailable')
    return {**result, 'defender_de_jure_exit_terms_v1': baseline,
            'queried_snapshot_id': starting['snapshot_id'], 'queried_revision': starting['revision'],
            'queried_native_revision': starting['native_revision'],
            'queried_episode_run_id': starting['episode_run_id'],
            'queried_connection_generation': starting['diagnostics']['connection_generation']}
