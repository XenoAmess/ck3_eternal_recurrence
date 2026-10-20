"""Plan finite A03 display metadata; reuse the exact unrun C23 18-leaf graph.

No Task, process, OBS, desktop or emitter entry point. The sole runtime owner
may install returned bytes after the separate full-capacity and Root review.
The old source, output names and all stop/exit markers remain untouched.
"""
import ast
from datetime import datetime
import hashlib
import json
from pathlib import Path
from tools.g2_saved_campaign.storage_canonical_compat_v1 import storage_binding_v1

MACHINE = 'xenoamess-full-tower-eb9d2c1186'
MANIFEST_SHA = 'e24c6b7eef1f2c32bfd3bb802533275c3cd7a7bfbcf7e28e336c04a06e16b4b6'
OWNER_SHA = '56b649988bda143426a6eca518ed72f0025f0f5ae5df3e8df6e8f236636c96dd'
PROFILE_SHA = 'de07011fb223941ade0527dfefaf81accf1f2b7ef72a79bcc5e96c2ecb584fcf'
SPEC_NAME = 'ROOT-DISPLAY-SPEC-C23-A03.json'
PROFILE_NAME = 'ROOT-OBS-PROFILE-C23-A03.json'
WRAPPER_NAME = 'presentation-c23/start_new_game_display_a03.py'
REVIEW_NAME = 'ROOT-DISPLAY-PREPARE-C23-A03.json'
OUTPUT_HARD_BYTES = 32768
NAMESPACE_KEYS = ('config', 'state', 'text', 'binding', 'requested',
                  'current_recording', 'first_admission', 'map_admission')


def require(ok, why):
    if not ok:
        raise ValueError('A03 display reuse: ' + why)


def pin(raw, path):
    return {'path': str(Path(path).resolve()), 'bytes': len(raw),
            'sha256': hashlib.sha256(raw).hexdigest()}


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


def finite(path, limit=131072):
    raw = Path(path).read_bytes()
    require(len(raw) <= limit, 'finite input required: ' + str(path))
    return raw


def checked(ref, limit=131072):
    raw = finite(ref['path'], limit)
    require(pin(raw, ref['path']) == ref, 'exact input pin differs')
    return raw


def source_spec(raw):
    tree = ast.parse(raw)
    rows = [n.value for n in tree.body if isinstance(n, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == 'SPEC' for t in n.targets)]
    require(len(rows) == 1, 'one frozen owner SPEC required')
    return ast.literal_eval(rows[0])


def existing_graph(runtime):
    """Read exact source graph and prove its first-use namespace is still empty."""
    runtime = Path(runtime).resolve()
    path = runtime / 'presentation-c23/SOURCE-PINS-C23.json'
    raw = finite(path)
    require(len(raw) == 6208 and hashlib.sha256(raw).hexdigest() == MANIFEST_SHA,
            'qualified original manifest required')
    manifest = json.loads(raw)
    require(manifest['machine_id'] == MACHINE and len(manifest['files']) == 17,
            'exact original complete graph required')
    refs = []
    for row in manifest['files']:
        ref = {k: row[k] for k in ('path', 'bytes', 'sha256')}
        require(Path(ref['path']).resolve() == runtime / row['relative_path'],
                'source escaped original runtime')
        checked(ref)
        refs.append(ref)
    refs.append(pin(raw, path))
    owner_path = runtime / 'presentation-c23/start_new_game_display.py'
    owner = finite(owner_path)
    require(len(owner) == 11355 and hashlib.sha256(owner).hexdigest() == OWNER_SHA,
            'qualified retained owner required')
    spec = source_spec(owner)
    require(spec['generation'] == 'C23' and spec['machine_id'] == MACHINE
            and Path(spec['target_runtime']).resolve() == runtime,
            'original owner runtime differs')
    # Successful launch/placement remain the original first-success names.
    # They must still be absent while preparing, but will exist when running.
    absent = [runtime / spec[k] for k in (*NAMESPACE_KEYS, 'launch', 'placement')]
    absent.append(runtime / 'ROOT-DISPLAY-CHILD-IMPORT-PREFLIGHT-C23-A03.json')
    require(not any(p.exists() for p in absent), 'first-use namespace is occupied')
    require(sum(r['bytes'] for r in refs) == 278733, 'complete 18-leaf size differs')
    return refs, spec, [str(p) for p in absent]


def unrun_profile(runtime):
    """Do not print the private profile body or its websocket password."""
    runtime = Path(runtime).resolve()
    path = runtime / 'ROOT-OBS-PROFILE-C23.json'
    raw = finite(path)
    require(len(raw) == 2234 and hashlib.sha256(raw).hexdigest() == PROFILE_SHA,
            'exact previously unrun profile required')
    profile = json.loads(raw)
    require(profile['machine_id'] == MACHINE and profile.get('continuous') is True
            and profile.get('strict_isolation') is True,
            'isolated actual machine profile required')
    root = Path(profile['config_root'])
    name = profile['profile_name']
    require(name == profile['collection_name'], 'paired portable profile required')
    files = [root / 'basic/profiles' / name / 'basic.ini',
             root / 'basic/scenes' / (name + '.json')]
    expected = [(661, '98f64e7734c7daf96bec02b1d297551123561025c59d17c5caa6d4ee15af343f'),
                (596, '2b375d07ab7c987072f5153bd913822377c9f90f025c0fc2c04e00e76a0117e5')]
    refs = []
    for item, (size, digest) in zip(files, expected):
        data = finite(item)
        require(len(data) == size and hashlib.sha256(data).hexdigest() == digest,
                'previously unrun portable configuration changed')
        refs.append(pin(data, item))
    job_count = 0
    for child in Path(profile['recording_root']).iterdir():
        job = child / 'job.json'
        if child.is_dir() and job.exists():
            row = json.loads(finite(job))
            require(str(row.get('profile_path', '')).casefold() != str(path).casefold()
                    and row.get('profile_sha256') != PROFILE_SHA,
                    'profile already referenced by a recording job')
            job_count += 1
    return profile, pin(raw, path), refs, job_count


WRAPPER = '''"""Exact A03 metadata adapter; the retained C23 owner and all 18 leaves stay unchanged."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

META_SHA = '__META_SHA__'
P = Path(__file__).resolve().parent
N = P.parent


def need(ok, why):
    if not ok:
        raise ValueError('A03 display runtime: ' + why)


def checked(ref, limit=131072):
    raw = Path(ref['path']).read_bytes()
    need(len(raw) <= limit and len(raw) == ref['bytes']
         and hashlib.sha256(raw).hexdigest() == ref['sha256'], 'exact pinned input differs')
    return raw


def load_owner():
    raw = (N / '__SPEC_NAME__').read_bytes()
    need(len(raw) <= 32768 and hashlib.sha256(raw).hexdigest() == META_SHA,
         'new immutable SPEC differs')
    meta = json.loads(raw)
    need(meta['schema'] == 'xar.C23-A03-display-reuse-spec/v1'
         and meta['machine_id'] == '__MACHINE__'
         and Path(meta['target_runtime']).resolve() == N,
         'actual metadata machine/runtime differs')
    full = json.loads(checked(meta['full_admission']))
    need(full.get('machine_id') == meta['machine_id'] and full.get('status') == 'ADMITTED',
         'same machine current full admission required')
    need(datetime.now(timezone.utc) < datetime.fromisoformat(full['review_at_utc'].replace('Z', '+00:00')),
         'full admission review expired')
    need(checked(meta['live_canonical']) == checked(meta['full_admission'])
         and full['review_at_utc'] == meta['storage_review_at_utc'],
         'immutable/live full or review differs')
    checked(meta['root_final'], 2097152)
    profile = json.loads(checked(meta['new_profile']))
    storage = profile['storage']
    need(storage['admission_path'] == meta['live_canonical']['path']
         and storage['admission_sha256'] == meta['full_admission']['sha256']
         and storage['approved_output_roots'] == full['approved_output_roots']
         and storage['disk_reserve_bytes'] == full['disk_reserve_bytes']
         and profile['A03_storage_review_at_utc'] == meta['storage_review_at_utc'],
         'profile current full/review binding differs')
    for ref in meta['reused_sources']:
        checked(ref)
    for ref in meta['unrun_portable_config']:
        checked(ref)
    path = Path(meta['retained_owner']['path'])
    spec = importlib.util.spec_from_file_location('_retained_C23_owner_for_A03', path)
    owner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(owner)
    need(owner.SPEC == meta['previous_spec'], 'original owner SPEC differs')
    # Only metadata routing changes. P and N retain the original frozen source
    # location. The actual same-interpreter child re-enters this pinned adapter.
    owner.SPEC = dict(meta['new_spec'])
    owner.__file__ = str(Path(__file__).resolve())
    return owner


if __name__ == '__main__':
    value = load_owner()
    if sys.argv[1:] == ['--child-import-preflight']:
        value.child_import_preflight()
    else:
        value.main()
'''


def plan(runtime, full_path, root_final_path, *, observed_at_utc,
         machine_id=MACHINE):
    """Return four new leaves privately; do not install or print profile bytes."""
    require(machine_id == MACHINE, 'machine-specific prior configuration required')
    observed = datetime.fromisoformat(observed_at_utc.replace('Z', '+00:00'))
    require(observed.tzinfo is not None, 'actual aware observation time required')
    runtime = Path(runtime).resolve()
    paths = [runtime / n for n in (SPEC_NAME, PROFILE_NAME, WRAPPER_NAME, REVIEW_NAME)]
    require(not any(p.exists() for p in paths), 'new A03 output namespace required')
    refs, old_spec, absent = existing_graph(runtime)
    profile, old_profile, config_refs, job_count = unrun_profile(runtime)
    full_raw = finite(full_path)
    full = json.loads(full_raw)
    require(full.get('machine_id') == machine_id and full.get('status') == 'ADMITTED'
            and isinstance(full.get('approved_output_roots'), list)
            and type(full.get('disk_reserve_bytes')) is int
            and full['disk_reserve_bytes'] > 0,
            'actual same-machine full admission required')
    require(observed < datetime.fromisoformat(full['review_at_utc'].replace('Z', '+00:00')),
            'current full admission review has expired')
    canonical_path = runtime / 'STORAGE-ADMISSION.json'
    require(finite(canonical_path) == full_raw, 'new full not yet adopted live')
    storage = storage_binding_v1(full_raw, canonical_path=str(canonical_path))
    final_raw = finite(root_final_path, 2097152)
    require(json.loads(final_raw).get('machine_id') == machine_id,
            'actual same-machine RootFinal required')
    full_ref = pin(full_raw, full_path)
    profile.update(prepared_at_utc=observed_at_utc,
                   storage_review_refreshed_at_utc=observed_at_utc,
                   unrun_profile_config_reused=True, A03_source_profile=old_profile,
                   A03_storage_review_at_utc=full['review_at_utc'])
    profile['storage'] = storage
    profile_raw = encode(profile)
    new_spec = dict(old_spec, generation='C23-A03', profile=PROFILE_NAME)
    owner = next(row for row in refs if row['path'].endswith('start_new_game_display.py'))
    meta = {'schema': 'xar.C23-A03-display-reuse-spec/v1', 'machine_id': machine_id,
            'observed_at_utc': observed_at_utc, 'target_runtime': str(runtime),
            'retained_owner': owner, 'previous_spec': old_spec, 'new_spec': new_spec,
            'full_admission': full_ref, 'live_canonical': pin(full_raw, canonical_path),
            'storage_review_at_utc': full['review_at_utc'],
            'root_final': pin(final_raw, root_final_path),
            'new_profile': pin(profile_raw, runtime / PROFILE_NAME),
            'reused_sources': refs, 'unrun_portable_config': config_refs,
            'fresh_output_paths_absent_at_prepare': absent,
            'actual_Game_publisher_recording_identity': None,
            'first_success_paths_preserved': True,
            'retired_blue_window': 'original constructor tombstone and recorder guard retained',
            'display_content': 'current state, decision, reason, actual result; no film title',
            'new_recording_uuid': 'generated only by actual original capture.launch_recording',
            'old_stop_exit_markers_untouched': True}
    meta_raw = encode(meta)
    wrapper = WRAPPER.replace('__META_SHA__', hashlib.sha256(meta_raw).hexdigest())
    wrapper = wrapper.replace('__SPEC_NAME__', SPEC_NAME).replace('__MACHINE__', machine_id).encode()
    compile(wrapper, str(runtime / WRAPPER_NAME), 'exec')
    values = {runtime / PROFILE_NAME: profile_raw, runtime / SPEC_NAME: meta_raw,
              runtime / WRAPPER_NAME: wrapper}
    review = {'schema': 'xar.C23-A03-display-reuse-review/v1', 'machine_id': machine_id,
              'observed_at_utc': observed_at_utc, 'status': 'RAM_ONLY_NOT_INSTALLED',
              'full_admission': full_ref, 'live_canonical': meta['live_canonical'],
              'storage_review_at_utc': full['review_at_utc'],
              'root_final': meta['root_final'], 'reused_source_leaves': len(refs),
              'reused_source_bytes': sum(r['bytes'] for r in refs),
              'new_output_pins': [pin(raw, p) for p, raw in values.items()],
              'prior_profile': old_profile, 'unrun_portable_config': config_refs,
              'recording_jobs_examined': job_count,
              'prior_profile_recording_references': 0,
              'metadata_delta': ['generation C23 -> C23-A03', 'profile -> ' + PROFILE_NAME],
              'namespace_rule': 'reuse never-created C23 success/publisher outputs create-only',
              'source_or_old_marker_writes': 0, 'Game_OBS_Task_desktop_calls': 0,
              'new_publisher_started': False, 'new_recording_started': False,
              'pixel_admitted': False, 'password_printed': False}
    values[runtime / REVIEW_NAME] = encode(review)
    require(sum(map(len, values.values())) <= OUTPUT_HARD_BYTES,
            'four-leaf runtime metadata peak exceeds finite quote')
    return values, review
