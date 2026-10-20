"""Exact accepted A05 eighteen-leaf display -> A06 RAM; no writes/calls."""
from __future__ import annotations

import ast
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from types import FunctionType

OWN = Path(__file__).resolve().parent
if str(OWN) not in sys.path:
    sys.path.insert(0, str(OWN))
import prepare_c23_a05_display_v1 as prior

MACHINE = prior.MACHINE
T5 = prior.T5
T6 = T5.with_name('runtime-a06')
O = prior.O
TASK6 = O / 'tasks/spec-display-a06'
QUOTE5 = O / 'A05-ROOT-QUOTE02.json'
QUOTE5_PIN = (114511, 'fd03557ffc5e7e36551f4216a8ef360d93df58b349d96e162be1e41e63fc591f')
PROFILE5_PIN = (2691, 'de0be81103dd53ba4c41a17c356dd97cf0a8e813e335f1617d92bbf337854b92')
FULL5_SHA = 'cf4e9c9230c75dc0028257cd924d87324efd8e173484a6086b2c8fbd9f7eb8e5'
PREDECESSOR_NONCE = 'deaa29e56c4a46d88d6e813d0b58997e'
REVIEW_AT = '2026-10-20T10:30:00+00:00'
require, sha, encode, pin, finite, checked = (
    prior.require, prior.sha, prior.encode, prior.pin, prior.finite, prior.checked)


def actual_a05_graph():
    raw = finite(QUOTE5)
    require((len(raw), sha(raw)) == QUOTE5_PIN, 'exact actual accepted A05 quote required')
    review = json.loads(raw)['display']
    require(review['machine_id'] == MACHINE and review['display_leaf_count'] == 18
            and review['target_runtime'] == str(T5), 'complete accepted A05 display source required')
    values, inputs = {}, [pin(QUOTE5, raw)]
    for row in review['files']:
        name = row['relative_path']
        require(name not in values and Path(row['path']).resolve() == T5 / name
                and (T5 / name).resolve().is_relative_to(T5), 'confined unique accepted source required')
        ref = {k: row[k] for k in ('path', 'bytes', 'sha256')}
        values[name] = checked(ref)
        inputs.append(ref)
    require(len(values) == 18, 'complete eighteen actual A05 leaves required')
    manifest = json.loads(values[prior.MANIFEST])
    require(manifest['machine_id'] == MACHINE and len(manifest['files']) == 18,
            'accepted A05 seventeen runtime sources plus validator required')
    external = []
    for row in manifest['files']:
        name = row['relative_path']
        ref = {k: row[k] for k in ('path', 'bytes', 'sha256')}
        if name.startswith('@'):
            require(name == '@frozen-host/tools/ck3_capture_closed_receipt.py'
                    and row['sha256'] == prior.closure.VALIDATOR_SHA and row['bytes'] == 8175,
                    'exact frozen external validator required')
            checked(ref)
            inputs.append(ref)
            external.append(row)
        else:
            require(ref == pin(T5 / name, values[name]), 'accepted runtime source row differs')
    require(len(external) == 1, 'one actual frozen validator source required')
    require(sha(values['presentation-c23/hotfix_provider.py']) == prior.closure.NEW_HOTFIX_SHA
            and sha(values['presentation-c23/ck3_obs_capture_png_retry_c23.py']) == prior.closure.CAPTURE_SHA,
            'qualified two-layer H/tools hotfix and paused PNG capture required')
    return values, review, inputs, manifest


def build_sources(*, full_storage_ref, observed_at_utc, display_nonce, machine_id=MACHINE):
    require(machine_id == MACHINE, 'actual same-machine A06 input required')
    prior._nonce(display_nonce)
    require(display_nonce != PREDECESSOR_NONCE, 'fresh A06 display nonce required')
    observed = datetime.fromisoformat(observed_at_utc.replace('Z', '+00:00'))
    require(observed.tzinfo is not None and observed.utcoffset().total_seconds() == 0
            and observed <= datetime.now(timezone.utc), 'actual aware UTC observation required')
    require(not T6.exists() and not TASK6.exists(), 'fresh A06 runtime and Task roots required')
    before, old_review, inputs, manifest = actual_a05_graph()
    values = dict(before)
    full_raw = checked(full_storage_ref, 32768)
    full = json.loads(full_raw)
    require(full['machine_id'] == MACHINE and full['status'] == 'ADMITTED'
            and full['review_at_utc'] == REVIEW_AT
            and observed < datetime.fromisoformat(REVIEW_AT), 'actual current 10:30 complete full required')
    inputs.append(full_storage_ref)
    node, spec = prior.assignment(before[prior.OWNER], 'SPEC')
    old_spec = copy.deepcopy(spec)
    require(spec['generation'] == 'C23-A05' and spec['target_runtime'] == str(T5)
            and spec['display_nonce'] == PREDECESSOR_NONCE
            and spec['previous_Game_tuple'] == list(prior.OLD_GAME), 'actual A05 owner source SPEC differs')
    spec.update(generation='C23-A06', target_runtime=str(T6), display_nonce=display_nonce)
    text = before[prior.OWNER].decode('utf-8')
    segment = ast.get_source_segment(text, node)
    require(text.count(segment) == 1, 'single owner literal SPEC seam required')
    values[prior.OWNER] = text.replace(segment, 'SPEC=' + repr(spec), 1).encode('utf-8')
    require(values[prior.OWNER].decode().replace('SPEC=' + repr(spec), segment, 1).encode()
            == before[prior.OWNER], 'owner changed outside exact literal SPEC')
    provider = json.loads(before[prior.PROVIDER])
    require(provider['machine_id'] == MACHINE and provider['generation'] == 'C23',
            'actual static provider source required')
    for name, ref in provider['sources'].items():
        rel = 'presentation-c23/g2_saved_campaign/' + name + '.py'
        require(ref == pin(T5 / rel, before[rel]), 'old static provider source pin differs')
        provider['sources'][name] = pin(T6 / rel, values[rel])
    values[prior.PROVIDER] = encode(provider)
    rows = []
    for row in manifest['files']:
        rel = row['relative_path']
        rows.append(row if rel.startswith('@') else dict(pin(T6 / rel, values[rel]), relative_path=rel))
    values[prior.MANIFEST] = encode(dict(manifest, files=rows))
    changed = [name for name in values if values[name] != before[name]]
    require(set(changed) == {prior.OWNER, prior.PROVIDER, prior.MANIFEST}
            and len(values) == 18 and len(rows) == 18, 'exact three modified/eighteen complete leaves required')
    require(not any(b'runtime-a05' in raw for raw in values.values()), 'old runtime routing remained')
    for name, raw in values.items():
        if name.endswith('.py'):
            compile(raw, str(T6 / name), 'exec')

    profile_path = T5 / prior.PROFILE
    profile_raw = finite(profile_path)
    require((len(profile_raw), sha(profile_raw)) == PROFILE5_PIN,
            'actual cold-amended A05 profile input required; old quote companion is historical')
    profile = json.loads(profile_raw)
    require(profile['machine_id'] == MACHINE and profile['continuous'] is True
            and profile['strict_isolation'] is True
            and profile['storage']['admission_sha256'] == FULL5_SHA
            and profile['storage_review_at_utc'] == REVIEW_AT,
            'actual accepted A05 profile full binding differs')
    inputs.append(pin(profile_path, profile_raw))
    name = 'ManagedWindowCapture-' + display_nonce
    require(name != profile['profile_name'] and name != profile['collection_name'], 'new private UUID required')
    profile.update(profile_name=name, collection_name=name, recording_root=str(T6 / 'recordings'),
                   prepared_at_utc=observed_at_utc, storage_review_at_utc=full['review_at_utc'],
                   A06_display_nonce=display_nonce)
    profile.pop('A05_display_nonce', None)
    profile['storage'] = prior.storage_binding_v1(full_raw, canonical_path=str(T6 / 'STORAGE-ADMISSION.json'))
    companions = {T6 / prior.PROFILE: encode(profile),
                  **prior._portable_companions(profile, values['presentation-c23/ck3_obs_capture_png_retry_c23.py'])}
    require(not any(path.exists() for path in companions), 'fresh create-only private profile outputs required')
    approved = [Path(p).resolve() for p in full['approved_output_roots']]
    require(all(any(path.resolve().is_relative_to(root) for root in approved)
                for path in [*(T6 / name for name in values), *companions]),
            'new complete full must cover every A06/private profile output')
    global_path = Path(profile['config_root']) / 'global.ini'
    global_raw = finite(global_path)
    conf = prior.configparser.ConfigParser(interpolation=None)
    conf.read_string(global_raw.decode('utf-8-sig'))
    require(conf.getint('OBSWebSocket', 'ServerPort') == profile['port']
            and conf.get('OBSWebSocket', 'ServerPassword') == profile['password']
            and conf.getboolean('OBSWebSocket', 'ServerEnabled')
            and conf.getboolean('OBSWebSocket', 'AuthRequired'), 'actual private websocket input differs')
    inputs.extend([pin(global_path, global_raw), pin(__file__, finite(__file__))])
    env = copy.deepcopy(old_review['Task_environment'])
    roots = env['PYTHONPATH'].split(prior.os.pathsep)
    require(roots[0] == str(T5 / 'presentation-c23') and str(prior.HOST / 'tools') in roots,
            'accepted two-layer Task H/tools environment required')
    roots[0] = str(T6 / 'presentation-c23')
    env['PYTHONPATH'] = prior.os.pathsep.join(roots)
    review = {
        'schema': 'xar.C23-A06-complete-display-RAM-review/v1', 'machine_id': MACHINE,
        'observed_at_utc': observed_at_utc, 'status': 'RAM_ONLY_NOT_INSTALLED',
        'display_nonce': display_nonce, 'source_runtime': str(T5), 'target_runtime': str(T6),
        'inputs': inputs, 'full_storage_ref': full_storage_ref, 'storage_review_at_utc': REVIEW_AT,
        'previous_owner_SPEC': old_spec, 'new_owner_SPEC': spec,
        'files': [pin(T6 / name, raw) | {'relative_path': name} for name, raw in values.items()],
        'display_leaf_count': 18, 'manifest_source_rows': 18, 'changed_exact_three': changed,
        'unchanged_source_leaves': 15,
        'external_validator': next(row for row in rows if row['relative_path'].startswith('@')),
        'Task_environment': env, 'required_Task_root': str(TASK6),
        'Task_SPEC_status': 'DEFERRED_UNTIL_ACTUAL_NEW_GAME_LAUNCH_AND_PLACEMENT',
        'companion_files': [pin(path, raw) for path, raw in companions.items()],
        'profile_name': name, 'collection_name': name, 'portable_obs_root': profile['obs_root'],
        'portable_config_root': profile['config_root'], 'companion_roots': [str(T6), profile['config_root']],
        'profile_password_printed': False, 'prerequisite_directories': [str(T6 / 'recordings')],
        'recordings_parent_required_before_prepare_or_Run': True,
        'static_provider_input': pin(T6 / prior.PROVIDER, values[prior.PROVIDER]),
        'static_provider_is_input_not_attempt_output': True,
        'fresh_output_namespace': [str(T6 / spec[k]) for k in prior.OUTPUT_NAMESPACE_KEYS],
        'source_graph_bytes': sum(map(len, values.values())), 'companion_bytes': sum(map(len, companions.values())),
        'actual_A05_Game_created': False, 'previous_Game_tuple_preserved_without_invention': True,
        'hotfix_and_validator_bytes_unchanged': True, 'old_runtime_writes': 0,
        'Game_OBS_Task_desktop_calls': 0, 'body_hash_bytes_Driver_SAVE_media': 0,
        'runtime_or_import_qualification_granted': False}
    return values, review, companions


def compose(plan):
    require(type(plan) is dict and set(plan) == {
        'schema', 'machine_id', 'full_storage_ref', 'observed_at_utc', 'display_nonce'}
        and plan['schema'] == 'xar.C23-A06-display-prepare-input/v1', 'exact finite A06 display plan required')
    return build_sources(full_storage_ref=plan['full_storage_ref'], observed_at_utc=plan['observed_at_utc'],
                         display_nonce=plan['display_nonce'], machine_id=plan['machine_id'])


def build_task_spec(display_values, display_review, *, task_nonce, game_launch_ref, placement_ref):
    """Reuse exact original Task binder with only private target roots changed."""
    env = dict(prior.build_task_spec.__globals__, T5=T6, TASK5=TASK6)
    binder = FunctionType(prior.build_task_spec.__code__, env)
    return binder(display_values, display_review, task_nonce=task_nonce,
                  game_launch_ref=game_launch_ref, placement_ref=placement_ref)
