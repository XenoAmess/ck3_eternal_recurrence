"""Resolve repair from a settled AUTO/MET pair, without waiting for FULL.

Frozen v4 remains intact. Root executes this sidecar; preparation performs no
Game/SDK/MCP/OBS calls. Only immutable TURN, AUTO, MET and exact SDK custody
prove calendar progress. Neither an ACK nor an unpaired AUTO can resolve.
"""
from datetime import timedelta
from pathlib import Path
import sys

from . import runtime_repair_status_v4 as v4
core = v4.core
FRAME = ("snapshot_id", "revision", "native_revision", "date_raw", "actor_character_id", "episode_run_id")

_native_reason = v4.diagnostic_reason


def diagnostic_reason(row):
    native = _native_reason(row)
    if native is not None:
        return native
    body = core.decode(row)
    if not isinstance(body, dict):
        return None
    plan = body.get('plan') or {}
    if (row.get('request', {}).get('tool') == 'ck3_auto_turn'
            and body.get('status') == 'blocked'
            and body.get('selected_step') is None
            and plan.get('selected_step') is None
            and plan.get('phase') == 'native_war_counterpolicy_hold'
            and isinstance(plan.get('reason'), str) and plan['reason'].strip()):
        return '\u6218\u540e\u4fdd\u62a4\u7b56\u7565\u6ca1\u6709\u9009\u51fa\u540e\u7eed\u884c\u52a8', {
            'mapping': 'blocked_counterpolicy_no_followup_action',
            'phase': plan['phase'], 'original_plan_reason': plan['reason'],
            'json_pointer': ['result', 'decoded_body', 'plan', 'phase'],
            'Native_error_inferred': False, 'business_action_inferred': False}
    return None


# The subclass supplies its reason mapper through an instance method; importing
# this module leaves the v4 mapper unchanged.


def settled_progress_proof(state, turn, auto, metrics, loop, pair, published, observed_pair):
    if state.get('phase') != 'repair_applied_waiting_for_progress':
        return None
    rows = pair.get('processes') or []
    if (pair.get('status') != 'SDK_PAIR_HANDLES_RETAINED' or len(rows) != 2
            or rows != published.get('processes')
            or {row.get('role') for row in rows} != {'sdk_queue', 'sdk_application'}
            or len(observed_pair) != 2):
        return None
    for row in rows:
        found = [item for item in observed_pair if item.get('role') == row['role']]
        if (len(found) != 1 or found[0].get('pid') != row.get('pid')
                or found[0].get('creation_filetime') != row.get('creation_filetime')
                or type(row.get('pid')) is not int or row['pid'] <= 0
                or type(row.get('creation_filetime')) is not int or row['creation_filetime'] <= 0
                or str(found[0].get('executable', '')).replace('\\', '/').casefold()
                    != str(row.get('executable', '')).replace('\\', '/').casefold()
                or found[0].get('kernel_exit_observed') is not False):
            return None
    body, met = core.decode(auto), core.decode(metrics)
    if body is None or met is None:
        return None
    before, after = turn.get('before') or {}, turn.get('after') or {}
    source = body.get('planning_source_frame') or {}
    result = body.get('result') or {}
    baseline = state.get('observed_frame') or {}
    number, repaired = turn.get('auto_sequence'), state.get('repair_applied_sequence')
    delta = turn.get('date_delta_raw')
    if (turn.get('stage') != 'auto_verified' or type(turn.get('global_turn')) is not int
            or type(loop.get('completed_cycles')) is not int
            or turn['global_turn'] > loop['completed_cycles']
            or type(number) is not int or type(repaired) is not int or number <= repaired
            or turn['global_turn'] <= 0
            or auto.get('request', {}).get('sequence') != number
            or auto.get('request', {}).get('tool') != 'ck3_auto_turn'
            or metrics.get('request', {}).get('sequence') != number + 1
            or metrics.get('request', {}).get('tool') != 'root_current_runtime_metrics'
            or body.get('status') != 'executed'
            or not isinstance(body.get('selected_step'), str) or not body['selected_step']
            or body.get('selected_step') != turn.get('selected_step')
            or type(delta) is not int or delta <= 0
            or type(before.get('date_raw')) is not int or type(after.get('date_raw')) is not int
            or after['date_raw'] - before['date_raw'] != delta
            or result.get('starting_date_raw') != before['date_raw']
            or result.get('ending_date_raw') != after['date_raw']
            or after['date_raw'] <= baseline.get('date_raw', -1)
            or source.get('bridge_pid') != state['binding']['game_pid']
            or any(source.get(key) != before.get(key) for key in FRAME)
            or any(met.get(key) != after.get(key) for key in FRAME)
            or any(type(after.get(key)) is not int or type(before.get(key)) is not int
                   or after[key] < before[key] for key in ('revision', 'native_revision'))
            or met.get('paused') is not True or met.get('map_ready') is not True
            or met.get('actor_alive') is not True
            or met.get('connection_generation') != source.get('connection_generation')
            or type(source.get('connection_generation')) is not int
            or source['connection_generation'] <= 0
            or any(after.get(key) != baseline.get(key) for key in ('actor_character_id', 'episode_run_id'))
            or any(before.get(key) != after.get(key) for key in ('actor_character_id', 'episode_run_id'))
            or turn.get('observation', {}).get('replay_allowed') is not False
            or loop.get('before', {}).get('date_raw', -1) < after['date_raw']
            or any(loop.get('before', {}).get(key) != after.get(key)
                   for key in ('actor_character_id', 'episode_run_id'))):
        return None
    return {'kind': 'actual_settled_AUTO_and_paired_MET_calendar_progress',
        'global_turn': turn['global_turn'], 'auto_sequence': number,
        'actual_end_date_raw': after['date_raw'], 'actual_date_delta_raw': delta,
        'actual_progress_ended_at_utc': auto.get('ended_at_utc'),
        'paired_MET_ended_at_utc': metrics.get('ended_at_utc'),
        'cumulative_cycles': loop['completed_cycles'], 'actual_after_frame': after,
        'Game_pid': state['binding']['game_pid'], 'exact_sdk_pair': rows,
        'new_Game_calls_by_status_sidecar': 0, 'new_business_credit_by_status_sidecar': 0,
        'extra_SEM_or_completed_FULL_required': False}


class SettledPairPublisher(v4.ReasonPublisher):
    def diagnose(self, row):
        return diagnostic_reason(row)

    def resolve_if_proved(self, state, semantic_path=None, batch_path=None):
        if state.get('phase') != 'repair_applied_waiting_for_progress':
            return False
        loop_path = self.queue / 'ROOT-CUMULATIVE-LOOP-STATE.json'
        signature = v4.v3.v2.signature(loop_path)
        marker = (state['incident_id'], signature, state.get('repair_applied_sequence'))
        if marker != getattr(self, '_settled_marker', None):
            self._settled_marker = marker
            loop = core.read(loop_path)
            count = loop.get('completed_cycles')
            if type(count) is int:
                # The initial scan is bounded; later updates inspect only new
                # exact TURN filenames, never the cumulative directory.
                same = state['incident_id'] == getattr(self, '_settled_incident', None)
                first = getattr(self, '_settled_high', count - 64) + 1 if same else max(1, count - 63)
                self._settled_incident, self._settled_high = state['incident_id'], count
                pair_path = self.session / ('ROOT-ACTUAL-SDK-PROCESSES-PINNED-' + self.prefix.upper() + '.json')
                published_path = self.session / ('ROOT-ACTUAL-SDK-PROCESS-GENERATIONS-' + self.prefix.upper() + '.json')
                self.observe_sdk_pair()
                observed = [{**handle.identity(role), **handle.observe()} for role, handle in self._sdk_handles or []]
                pair, published = core.read(pair_path), core.read(published_path)
                for number in range(first, count + 1):
                    path = self.queue / f'CUMULATIVE-TURN-{number:06d}.json'
                    if not path.is_file():
                        continue
                    turn = core.read(path)
                    if not isinstance(turn.get('auto_response'), str) or not isinstance(turn.get('after_metrics_response'), str):
                        continue
                    auto_path, metric_path = Path(turn['auto_response']).resolve(), Path(turn['after_metrics_response']).resolve()
                    if auto_path.parent != self.outbox.resolve() or metric_path.parent != self.outbox.resolve():
                        continue
                    auto, metrics = core.read(auto_path), core.read(metric_path)
                    proof = settled_progress_proof(state, turn, auto, metrics, loop, pair, published, observed)
                    if proof is None:
                        continue
                    proof.update(settled_TURN=core.pin(path), AUTO=core.pin(auto_path), MET=core.pin(metric_path),
                                 queue_state=core.pin(loop_path), pair_pin=core.pin(pair_path))
                    state.update(phase='resolved', recovery_proof=proof,
                        resolved_at_utc=core.utc().isoformat(),
                        expires_at_utc=(core.utc() + timedelta(seconds=30)).isoformat(),
                        recovery_status_version=5)
                    core.atomic(self.store / (state['incident_id'] + '-RESOLVED-SETTLED-PAIR.json'), state)
                    self.emit(state)
                    return True
        return super().resolve_if_proved(state, semantic_path, batch_path)


if __name__ == '__main__':
    if 'refine-current' in sys.argv[1:]:
        v4.main()
    else:
        core.Publisher = SettledPairPublisher
        try:
            core.main()
        finally:
            for publisher in v4.v3.v2.ACTIVE_PUBLISHERS:
                publisher.close()
