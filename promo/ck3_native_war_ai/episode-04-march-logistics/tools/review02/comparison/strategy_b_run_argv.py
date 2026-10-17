"""Build explicit B stage argv from pinned current metadata; submit no requests.

The external overlay supplies B stages and the unchanged normal-day helper.
The checkout supplies reviewed Relay, next adapter, common horizon and guard.
The ordinary B baseline still verifies the complete cold-S0 native evidence.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re

PREFIX = 'promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/'
STAGES = ('baseline', 'split-once', 'post-split', 'rest', 'merge-once', 'post-merge', 'route',
          'move-stage-once', 'move-stage-post', 'advance-stage-day', 'recover-stage-day',
          'advance-common-horizon', 'recover-common-horizon-day')
LIMIT = 256 * 1024


def need(ok, why):
    if not ok:
        raise ValueError(why)


def pin(path):
    path = Path(path).resolve()
    need(path.is_file() and 0 < path.stat().st_size <= LIMIT, 'bounded code/metadata input required')
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def metadata(ref):
    need(pin(ref['path']) == ref, 'exact metadata pin differs')
    def pairs(rows):
        result = {}
        for key, value in rows:
            need(key not in result, 'duplicate JSON key in metadata')
            result[key] = value
        return result
    return json.loads(Path(ref['path']).read_text(encoding='utf-8-sig'), object_pairs_hook=pairs)


def module(path, name='B_argv_explicit_runtime_guard'):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def build(binding, stage, attempt, *, previous=None, move_army_id=None, day_start_raw=None,
          arrival=None, days=1, now_utc=None):
    need(stage in STAGES, 'existing B stage required')
    need(type(attempt) is str and re.fullmatch('[A-Za-z][A-Za-z0-9_-]{0,63}', attempt), 'safe unique stage attempt required')
    repo = Path(binding['repo']).resolve()
    overlay = Path(binding.get('overlay_root', Path(__file__).resolve().parents[6])).resolve()
    plan = metadata(binding['plan']); arm = metadata(binding['s0_arm'])
    context = metadata(binding['context']); proof = metadata(binding['runtime_proof'])
    need('prepared' in binding, 'new B runtime requires explicit prepared pin')
    prepared = metadata(binding['prepared'])
    metadata(binding['module_pins'])
    need(pin(binding['request_helper']['path']) == binding['request_helper'], 'request helper pin differs')
    rt = arm['runtime']; source = plan['build']['source_head']
    need(plan.get('status') == 'frozen' and type(source) is str and re.fullmatch('[0-9a-f]{40}', source),
         'canonical frozen PLAN.frozen.json required')
    need(source == rt['source_head'] == context['source_head'] == proof['source_head'],
         'plan/cold-arm/context/proof source differs')
    need(arm['label'] == 'B' and arm['loaded_save_sha256'] == plan['normal_save']['sha256'],
         'B cold load is not the shared opaque S0')
    need(rt['machine_id'] == context['machine_id'] == proof['machine_id'], 'runtime machine differs')
    identity = context['identity']; ids = arm['cold_start']['strategy_army_ids']
    need(type(ids) is list and len(ids) == 1 and type(ids[0]) is int and 0 <= ids[0] < 2**31,
         'one fresh S0 main Army ID required')
    need(identity['run_id'] == proof['run_id'] and type(identity['sequence']) is int,
         'actual allocated run differs')
    paths = {'self': overlay / PREFIX / 'comparison/strategy_b_stages.py',
             'normal-stages': overlay / PREFIX / 'comparison/strategy_b_normal_stages.py',
             'root-relay': repo / PREFIX / 'split_merge/root_relay.py',
             'next-adapter': repo / PREFIX / 'comparison/strategy_b_next.py',
             'comparison-core': repo / PREFIX / 'comparison/r10_compare.py',
             'common-horizon': repo / PREFIX / 'comparison/strategy_b_common_horizon.py'}
    overrides = binding.get('code_overrides', {})
    need(type(overrides) is dict and set(overrides) <= set(paths), 'unknown reviewed code override')
    for name, ref in overrides.items():
        need(pin(ref['path']) == ref, 'reviewed code override differs: ' + name)
        paths[name] = Path(ref['path']).resolve()
    code = {name: pin(path) for name, path in paths.items()}
    # Use exactly the shared guard the reviewed Relay will import. No SDK or
    # Git/HEAD probe is performed; the existing Relay retains those checks.
    guard_path = paths['root-relay'].resolve().parents[1] / 'runtime_binding.py'
    guard_pin = pin(guard_path)
    need('live_binding' in binding, 'new B runtime requires explicit live_binding pin')
    operation = metadata(binding['live_binding'])
    need(operation.get('guard_sha256') == guard_pin['sha256'], 'reviewed shared runtime guard differs')
    guards = module(guard_path)
    total = binding.get('max_runtime_total_bytes', operation['max_runtime_total_bytes'])
    scene = Path(binding['context']['path']).resolve().parent
    guard = guards.OperationGuard(binding['live_binding']['path'], binding['live_binding']['sha256'],
        context=context, runtime=guards.proof_runtime(proof),
        scene_root=scene, source_head=source, machine_id=rt['machine_id'], run_id=identity['run_id'],
        max_runtime_total_bytes=total, normal_save_sha256=plan['normal_save']['sha256'],
        clock=(lambda: now_utc) if now_utc is not None else None)
    need(guards.arm_runtime(rt) == guard.binding['runtime'], 'fresh cold-arm runtime differs from live operation')
    relay = module(paths['root-relay'], 'B_argv_reviewed_root_relay')
    need(callable(getattr(relay, 'prepared_native_session', None)),
         'reviewed Relay prepared metadata support required')
    relay.prepared_native_session(prepared, binding['prepared'], proof, assets=scene,
        machine=rt['machine_id'], normal_save_sha256=plan['normal_save']['sha256'])
    options = guards.runtime_options({'max_runtime_total_bytes': total,
        'runtime_capacity_admission': binding.get('runtime_capacity_admission')}, guard)
    raw_max = binding.get('max_evidence_file_bytes', 16 * 1024 * 1024)
    need(type(raw_max) is int and raw_max in (16 * 1024 * 1024, 32 * 1024 * 1024),
         'explicit evidence limit must be 16MiB or 32MiB')
    admissions = binding.get('evidence_capacity_admissions', [])
    need(type(admissions) is list and (raw_max == 16 * 1024 * 1024 or admissions),
         '32MiB selected raw requires explicit evidence capacity admission')
    argv = [binding['python'], '-B', '-X', 'utf8', code['self']['path'], stage,
            '--repo', str(repo), '--evidence-root', binding['evidence_root'], '--run-id', identity['run_id'],
            '--run-sequence', str(identity['sequence']), '--source-head', source, '--army-id', str(ids[0]),
            '--case-id', binding['case_id'], '--attempt', attempt]
    for name, key in [('context', 'context'), ('runtime-proof', 'runtime_proof'), ('request-helper', 'request_helper'),
                      ('plan', 'plan'), ('s0-arm', 's0_arm'), ('module-pins', 'module_pins'), ('live-binding', 'live_binding'),
                      ('prepared', 'prepared')]:
        ref = binding[key]
        argv += ['--' + name, ref['path'], '--' + name + '-sha256', ref['sha256']]
    for name, ref in code.items():
        if name != 'self':
            argv += ['--' + name, ref['path']]
        argv += ['--' + name + '-sha256', ref['sha256']]
    argv += ['--max-evidence-file-bytes', str(raw_max), '--max-runtime-total-bytes', str(total),
             '--runtime-capacity-admission', *options['runtime_capacity_admission']]
    for admission in admissions:
        need(isinstance(admission, (list, tuple)) and len(admission) == 2,
             'explicit evidence capacity PATH SHA pair required')
        argv += ['--evidence-capacity-admission', *admission]
    if previous:
        need(pin(previous[0])['sha256'] == previous[1], 'previous state pin differs')
        argv += ['--previous-state', previous[0], '--previous-state-sha256', previous[1]]
    need(stage == 'baseline' or previous is not None, 'every continuation needs an exact previous-state pin')
    if stage in ('move-stage-once', 'move-stage-post'):
        need(type(move_army_id) is int and 0 <= move_army_id < 2**31, 'explicit actual B role Army ID required')
    if move_army_id is not None:
        argv += ['--move-army-id', str(move_army_id)]
    if stage in ('recover-stage-day', 'recover-common-horizon-day'):
        need(type(day_start_raw) is int, 'original day start required for read-only recovery')
    if day_start_raw is not None:
        argv += ['--day-start-raw', str(day_start_raw)]
    if stage in ('advance-common-horizon', 'recover-common-horizon-day'):
        need(arrival is not None, 'exact actual first-arrival arm required')
    if arrival:
        need(pin(arrival[0])['sha256'] == arrival[1], 'actual first-arrival arm pin differs')
        argv += ['--arrival-arm', arrival[0], '--arrival-arm-sha256', arrival[1]]
    need(type(days) is int and 1 <= days <= 30, 'bounded common-horizon days1..30 required')
    argv += ['--days', str(days)]
    return {'argv': argv, 'code_pins': code, 'runtime_guard': guard_pin,
            'live_operation': binding['live_binding'], 'source_head': source,
            'qualification': 'pending actual B baseline and full ABC comparison; argv generation gives no gameplay credit',
            'game_or_relay_request_submitted': False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--binding', type=Path, required=True); p.add_argument('--binding-sha256', required=True)
    p.add_argument('--stage', required=True, choices=STAGES); p.add_argument('--attempt', required=True)
    p.add_argument('--out', type=Path, required=True); p.add_argument('--previous', nargs=2)
    p.add_argument('--move-army-id', type=int); p.add_argument('--day-start-raw', type=int)
    p.add_argument('--arrival', nargs=2); p.add_argument('--days', type=int, default=1)
    a = p.parse_args()
    need(pin(a.binding)['sha256'] == a.binding_sha256, 'operator binding pin differs')
    value = build(json.loads(a.binding.read_bytes()), a.stage, a.attempt, previous=a.previous,
                  move_army_id=a.move_army_id, day_start_raw=a.day_start_raw, arrival=a.arrival, days=a.days)
    with a.out.open('x', encoding='utf-8') as out:
        json.dump(value, out, ensure_ascii=False, indent=2); out.write('\n')
    print(json.dumps(pin(a.out)))


if __name__ == '__main__':
    main()
