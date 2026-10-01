"""Bind an actually allocated new run to its source/build and research plan."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parent
EXE_SHA = '2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86'

def require(condition, message):
    if not condition:
        raise RuntimeError(message)

def identity(path):
    path = Path(path).resolve()
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest().upper()
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': digest}

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def write(path, body):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(body, stream, ensure_ascii=False, indent=2)
        stream.write('\n')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate-manifest', required=True, type=Path)
    parser.add_argument('--launch-plan', required=True, type=Path)
    parser.add_argument('--live-root', required=True, type=Path)
    args = parser.parse_args()
    candidate = read(args.candidate_manifest)
    launch = read(args.launch_plan)
    source = Path(candidate['source']).resolve()
    live = args.live_root.resolve()
    output = live / 'ck3-output'
    require(Path(launch['live_root']).resolve() == live and launch['source_commit'] == candidate['source_commit'], 'Launch/source tuple differs')
    require(subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source, text=True).strip() == candidate['source_commit'], 'Source HEAD changed')
    run_identity = read(output / 'live-run-identity.json')
    require(len(run_identity['identities']) == 1, 'Actual run allocation is not unique')
    run_id = run_identity['identities'][0]['run_id']
    preflight = read(output / 'preflight.json')
    require(preflight['checkpoint_source']['date_raw'] == 53146848 and preflight['checkpoint_source']['actor'] == 29829, 'Wrong D26 run')
    start_path = output / 'native-start-readback.json'
    actual_start = read(start_path)
    require(actual_start.get('postcondition_verified') is True, 'Actual native load is not verified')
    start_snapshot = actual_start['snapshot']
    require(start_snapshot['date_raw'] == 53146848 and start_snapshot['paused'] is True and start_snapshot['played_character']['character_id'] == 29829, 'Wrong actual admitted native start')
    diagnostics = start_snapshot['diagnostics']
    native_session_binding = {'episode_run_id': start_snapshot['episode_run_id'], 'connection_generation': diagnostics['connection_generation'], 'bridge_pid': diagnostics['bridge_pid'], 'native_hello_session_generation': diagnostics['hello']['session_generation']}
    require(isinstance(native_session_binding['episode_run_id'], str) and bool(native_session_binding['episode_run_id']), 'No actual native episode identity')
    for field in ('connection_generation', 'bridge_pid'):
        require(type(native_session_binding[field]) is int and native_session_binding[field] > 0, 'No actual native binding: ' + field)
    require(type(native_session_binding['native_hello_session_generation']) is int and native_session_binding['native_hello_session_generation'] >= 0, 'No actual native hello session generation')
    paths = [start_path, args.candidate_manifest, args.launch_plan, ROOT / 'scoped_ui_research_a07.py',
             source / 'promo/ck3_native_war_ai/integration/capture_session.py',
             source / 'promo/ck3_native_war_ai/episode-02-battle-second-half/remaining_live_step.py',
             source / 'promo/ck3_native_war_ai/episode-02-battle-second-half/pursuit_live_step.py',
             candidate['dll']['path'], candidate['injector']['path'], output / 'preflight.json', output / 'live-run-identity.json',
             preflight['checkpoint_source']['save']['path']]
    # Epoch-nanosecond-derived fresh token, below uint64; never reuse an earlier run token.
    token = (time.time_ns() // 1000 << 8) | (uuid.uuid4().int & 255)
    require(0 < token < 2**64 and token not in {6100103}, 'Invalid/reused trace token')
    monitor_token = (time.time_ns() // 1000 << 8) | (uuid.uuid4().int & 255)
    require(0 < monitor_token < 2**64 and monitor_token != token, 'Independent monitor token invalid')
    config = {'schema': 'ck3.e2.explicit-current-research-binding/v1', 'created_at_utc': datetime.now(timezone.utc).isoformat(),
              'source_root': str(source), 'source_commit': candidate['source_commit'], 'live_root': str(live), 'run_id': run_id,
              'native_session_binding': native_session_binding,
              'bridge_dll': candidate['dll']['path'], 'bridge_injector': candidate['injector']['path'],
              'before_date_raw': 53146848, 'after_date_raw': 53146872, 'actor_id': 29829, 'war_id': 4,
              'public_unit_id': 18, 'combat_id': 16777218, 'victim_id': 33437, 'killer_id': 34120, 'event_load_index': 11,
              'managed_daily_sequence_token': token, 'monitor_sequence_token': monitor_token, 'pins': [identity(path) for path in paths],
              'prior_R0139_is_provenance_only': True, 'no_prior_sample_fills_current_fields': True,
              'video_revision_started': False, 'human_movie_signoff': False}
    config_path = ROOT / 'current-run-bindings.json'
    write(config_path, config)
    labels = [('loaded', 'Current paused D26 source'), ('ui', 'Same-pause original character/combat/roster UI'),
              ('selector', 'Actual candidate/filter/index/return'), ('request', 'Death effect and native request'),
              ('commit', 'Native death queue or immediate commit'), ('notify', 'Death on-action/notification writes'),
              ('casualty', 'Ordered roster/entry/cache/casualty transitions'), ('after', 'Paused next-day UI and full save delta')]
    transitions = [
        ('loaded-ui', 'loaded', 'ui', 'Full-ID native action/readback and actual original pixels', 'Actual UI frames must show the character and complete battle panel; counts/markup alone are not pixels'),
        ('loaded-selector', 'loaded', 'selector', 'Natural original schedule and selector return', 'Capture all candidate scope words/full IDs/filter and selected return in this exact new process'),
        ('selector-request', 'selector', 'request', 'Selected role through actual death effect', 'Correlate invocation/parent identity and exact victim/killer typed request, without filling from R0139'),
        ('request-commit', 'request', 'commit', 'Actual queue or immediate death commit route', 'Count and order all relevant requests/enqueues/commits, with exact date/reason/killer and first death marker'),
        ('commit-notify', 'commit', 'notify', 'Death on-action and notification setter', 'Independently watch the two full character IDs for signature_weapon producer and house relation start guard'),
        ('commit-casualty', 'commit', 'casualty', 'Regiment membership and current/soft/stats/hard ledger', 'Track all actual entry and casualty boundaries, including a legitimate retired RegimentID'),
        ('notify-after', 'notify', 'after', 'Full case write-set and actual next-day state', 'Cover all 13 required domains with explicit timing resolution; do not label unpublished values as live per-write reads'),
        ('casualty-after', 'casualty', 'after', 'Final paused ordered rosters and original UI', 'Match same-run native roster IDs, actual tooltip names/counts, character dead UI and complete lower battle composition'),
    ]
    plan = {'schema': 'xar.native-research-plan.v1', 'topic': 'episode02-six-gap-scoped-causal-ui', 'purpose': 'engine-transition',
            'question': 'What actual complete case-scoped selector, death, notification, roster and casualty chain occurs, and how does it appear in the original UI?',
            'build': {'version': '1.19.0.6', 'exe_sha256': EXE_SHA},
            'observation': {'mode': 'passive-runtime', 'actor_kind': 'engine', 'identity_kind': 'generation-id',
                'producer_trigger': 'daily-tick', 'owner_scope': 'One admitted isolated vanilla process, actor29829/War4/publicUnit18/Combat16777218, victim33437 and related34120',
                'identity_lifetime': 'Every native object and full ID is valid only in this process/generation and current paused revision; native event/node identity expires on reload',
                'producer': 'Unmodified original combat schedule/effects/death-on-action/casualty calls, sampled by default-off private observers',
                'caller': 'Root submits native presentation only and at most one managed life-advance; original engine executes all gameplay writes',
                'consumer': 'Close all six user-requested research gaps before any episode02 video optimization',
                'cache_lifetime': 'Each native result is freshly bound; images have native before/after paused queries; no historical tuple fills new results',
                'expected_signal': 'Actual original UI, ordered candidate and roster identities, nested journal, typed death request/queue/commit, targeted passive variable writes and full same-run native-save deltas',
                'zero_sample_meaning': 'No relevant setter/death/event is a no-hit within this explicit observation lifetime; it does not prove impossibility or an unobserved sender',
                'stop_condition': 'At most one explicit +24 day and one FINISH; preserve ambiguous failures, never advance again, then verify actual cleanup and screen lease release',
                'runtime_window_ref': str(args.launch_plan.resolve())},
            'nodes': [{'id': ident, 'label': label} for ident, label in labels],
            'edges': [{'id': ident, 'from': origin, 'to': target, 'label': label, 'status': 'unknown', 'evidence': [], 'open_question': question}
                      for ident, origin, target, label, question in transitions],
            'cases': [{'id': 'six-gap-D26', 'question': 'All six requested gaps closed from this actual new process?', 'status': 'pending', 'evidence': []}],
            'evidence': []}
    for ident, path, support in [('new-binding', config_path, 'Exact current run/source/build/inputs and new token declaration'),
                                 ('candidate', args.candidate_manifest, 'Fresh exact private-branch build and offline checks; no live semantic proof'),
                                 ('launch', args.launch_plan, 'Actual explicit admitted research window; no video side effects')]:
        pin = identity(path)
        plan['evidence'].append({'id': ident, 'layer': 'source-contract', 'path': pin['path'], 'sha256': pin['sha256'], 'exe_sha256': EXE_SHA, 'supports': support})
    plan_path = ROOT / 'native-research-plan.json'
    write(plan_path, plan)
    argv = [sys.executable, str(source / 'tools/native_research_plan.py'), 'check', str(plan_path), '--for-observation',
            '--output', str(ROOT / 'native-research-plan-check.json')]
    checked = subprocess.run(argv, capture_output=True, text=True, encoding='utf-8')
    write(ROOT / 'native-research-plan-check-process.json', {'argv': argv, 'returncode': checked.returncode,
          'stdout': checked.stdout, 'stderr': checked.stderr})
    require(checked.returncode == 0, 'Current observation plan inconsistent, preserve and inspect')
    print(json.dumps({'result': 'CURRENT_RUN_BOUND_PLAN_CHECKED_SEMANTICS_PENDING', 'run_id': run_id,
                      'bindings': identity(config_path), 'unique_managed_token': token}, ensure_ascii=False))

if __name__ == '__main__':
    main()
