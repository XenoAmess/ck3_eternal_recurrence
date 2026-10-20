"""Project the complete actual A04 display graph to A05, in RAM only.

The eighteen runtime leaves include the immutable static provider and manifest.
The manifest has eighteen source rows: seventeen runtime inputs and the actual
frozen validator dependency. Private profile/config companions remain explicit
absolute-path outputs for the sole Root union to price and adopt once.
"""
from __future__ import annotations

import ast
import copy
import configparser
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys

OWN = Path(__file__).resolve().parent
if str(OWN) not in sys.path:
    sys.path.insert(0, str(OWN))
import prepare_recording_validator_closure_v1 as closure
from storage_canonical_compat_v1 import storage_binding_v1

MACHINE = closure.MACHINE_ID
PREP = Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep')
T0 = PREP / 'robert30-v20261019-campaign01/runtime'
T4, T5 = T0.with_name('runtime-a04'), T0.with_name('runtime-a05')
HOST = PREP / 'sdk-v20261019-candidate/host-checkout'
O = PREP / 'p51-fresh1066-v20261019-prepare01/c23-source23-native30-cold100'
MANIFEST = 'presentation-c23/SOURCE-PINS-C23.json'
OWNER = 'presentation-c23/start_new_game_display.py'
PROVIDER = 'ROOT-DECISION-TEXT-PROVIDER-C23.json'
PROFILE = 'ROOT-OBS-PROFILE-C23.json'
TASK4 = O / 'tasks/spec-display03-a04/SPEC.json'
TASK5 = O / 'tasks/spec-display-a05'
MANIFEST4_PIN = (6276, '34fb59f6e1bd0e5a67d01fcf5ddaaa85322ab21186d7270cbca02b5f9e206579')
PROFILE4_SHA = 'adcda7597c1a5876d031f1107451a29e743d272bdcb68e2b01ac17c0a08dc5fd'
TASK4_PIN = (3875, 'd904f4c7283c0f3c72a0395eb78f3f73b59e65794d80bf57757f8d9c2ac35e5c')
OWNER4_PIN = (14756, '62dc336b834a5a1fb4d8f8464c4a5517afcefa3992fd9876a8df1bf022353d2b')
OLD_GAME = (182100, 134369407465127587)
OUTPUT_NAMESPACE_KEYS = ('config', 'state', 'text', 'binding', 'requested',
                         'current_recording', 'first_admission', 'map_admission')


def require(ok, why):
    if not ok:
        raise ValueError('A05 complete display projection: ' + why)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def pin(path, raw):
    return {'path': str(Path(path).resolve()), 'bytes': len(raw), 'sha256': sha(raw)}


def finite(path, limit=131072):
    path = Path(path)
    require(path.is_file() and path.stat().st_size <= limit, 'bounded actual file required: ' + str(path))
    raw = path.read_bytes()
    require(len(raw) <= limit, 'complete bounded read required')
    return raw


def checked(ref, limit=131072):
    raw = finite(ref['path'], limit)
    require(pin(ref['path'], raw) == ref, 'actual input pin differs: ' + ref['path'])
    return raw


def assignment(raw, name):
    nodes = [n for n in ast.parse(raw).body if isinstance(n, ast.Assign)
             and any(isinstance(t, ast.Name) and t.id == name for t in n.targets)]
    require(len(nodes) == 1, 'one literal assignment required: ' + name)
    return nodes[0], ast.literal_eval(nodes[0].value)


def _nonce(value):
    require(type(value) is str and re.fullmatch('[a-f0-9]{32}', value) is not None,
            'explicit independent 32-hex nonce required')
    return value


def existing_graph():
    """Pin every leaf of the actual final A04 graph, without reading media."""
    manifest_raw = finite(T4 / MANIFEST)
    require((len(manifest_raw), sha(manifest_raw)) == MANIFEST4_PIN,
            'exact final A04 complete manifest required')
    manifest = json.loads(manifest_raw)
    require(manifest.get('machine_id') == MACHINE and len(manifest['files']) == 17,
            'actual seventeen-source A04 graph required')
    values, inputs = {}, []
    for row in manifest['files']:
        name = row['relative_path']
        require(type(name) is str and not name.startswith('@') and name not in values
                and Path(row['path']).resolve() == (T4 / name).resolve()
                and (T4 / name).resolve().is_relative_to(T4.resolve()), 'unique confined source required')
        ref = {key: row[key] for key in ('path', 'bytes', 'sha256')}
        values[name] = checked(ref)
        inputs.append(ref)
    require((len(values[OWNER]), sha(values[OWNER])) == OWNER4_PIN, 'actual retained-worker owner required')
    require(sha(values['presentation-c23/ck3_obs_capture_png_retry_c23.py']) == closure.CAPTURE_SHA,
            'qualified real paused PNG capture required')
    inputs.append(pin(T4 / MANIFEST, manifest_raw))
    return values, manifest_raw, inputs


def _portable_companions(profile, capture_raw):
    """Evaluate only exact frozen prepare_profile output expressions, no calls."""
    function = next(n for n in ast.parse(capture_raw).body
                    if isinstance(n, ast.FunctionDef) and n.name == 'prepare_profile')
    calls = [n for n in ast.walk(function) if isinstance(n, ast.Call)]
    basic = [n for n in calls if isinstance(n.func, ast.Attribute)
             and n.func.attr == 'write_text' and isinstance(n.func.value, ast.BinOp)
             and isinstance(n.func.value.left, ast.Name) and n.func.value.left.id == 'basic']
    scenes = [n for n in calls if isinstance(n.func, ast.Name) and n.func.id == '_write_new'
              and isinstance(n.args[0], ast.BinOp) and isinstance(n.args[0].left, ast.Name)
              and n.args[0].left.id == 'scenes']
    require(len(basic) == len(scenes) == 1, 'frozen portable output recipe seam differs')
    env = {'name': profile['profile_name'], 'recording_root': Path(profile['recording_root']),
           'bitrate_kbps': profile['bitrate_kbps']}
    def expression(node):
        return eval(compile(ast.Expression(node), '<exact-frozen-profile-expression>', 'eval'),
                    {'__builtins__': {}}, env)
    config = Path(profile['config_root'])
    basic_path = config / 'basic/profiles' / profile['profile_name'] / 'basic.ini'
    scene_path = config / 'basic/scenes' / (profile['profile_name'] + '.json')
    return {basic_path: expression(basic[0].args[0]).encode('utf-8'),
            scene_path: json.dumps(expression(scenes[0].args[1]), ensure_ascii=False, indent=2).encode('utf-8')}


def _task_environment(old_task):
    roots = old_task['env']['PYTHONPATH'].split(os.pathsep)
    require(roots[0] == str(T4 / 'presentation-c23'), 'actual Task presentation root differs')
    roots[0] = str(T5 / 'presentation-c23')
    tools = str(HOST / 'tools')
    require(all(Path(p).is_dir() for p in roots[1:]) and Path(tools).is_dir(),
            'actual inherited dependency root missing')
    require(tools not in roots, 'original Task unexpectedly already amended')
    roots.insert(1, tools)
    return {'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONPATH': os.pathsep.join(roots)}


def build_sources(*, full_storage_ref, observed_at_utc, display_nonce,
                  machine_id=MACHINE):
    """Return (display_values, display_review, companion_values); never write.

    display_values keys are eighteen runtime-relative names. companion_values
    keys are absolute Paths: profile plus new profile/scene configuration. The
    old portable engine and its private WebSocket configuration remain explicit
    inputs; neither global.ini nor an old profile is an output of this plan.
    """
    require(machine_id == MACHINE, 'same observed machine required')
    observed = datetime.fromisoformat(observed_at_utc.replace('Z', '+00:00'))
    require(observed.tzinfo is not None and observed.utcoffset().total_seconds() == 0,
            'actual aware UTC observation required')
    require(observed <= datetime.now(timezone.utc), 'future observation is not actual evidence')
    _nonce(display_nonce)
    require(not T5.exists() and not TASK5.exists(), 'independent A05 runtime/Task namespace required')
    values, manifest_raw, inputs = existing_graph()
    old_task_raw = finite(TASK4)
    require((len(old_task_raw), sha(old_task_raw)) == TASK4_PIN, 'actual final A04 Task SPEC required')
    old_task = json.loads(old_task_raw)
    require(old_task['machine_id'] == MACHINE and display_nonce != old_task['nonce'],
            'independent display nonce required')
    inputs.append(pin(TASK4, old_task_raw))
    launch4_path = T4 / 'ROOT-ACTUAL-GAME-LAUNCH-C23.json'
    launch4_raw = finite(launch4_path)
    launch4 = json.loads(launch4_raw)
    require(launch4.get('machine_id') == MACHINE
            and (launch4.get('pid'), launch4.get('creation_filetime')) == OLD_GAME,
            'actual A04 physical Game source tuple differs')
    inputs.append(pin(launch4_path, launch4_raw))
    full_raw = checked(full_storage_ref, 32768)
    full = json.loads(full_raw)
    require(full.get('machine_id') == MACHINE and full.get('status') == 'ADMITTED'
            and observed < datetime.fromisoformat(full['review_at_utc'].replace('Z', '+00:00')),
            'current same-machine immutable full admission required')
    profile_raw = finite(T4 / PROFILE)
    require(sha(profile_raw) == PROFILE4_SHA, 'exact original private A04 profile required')
    profile = json.loads(profile_raw)
    require(profile['machine_id'] == MACHINE and profile['strict_isolation'] is True
            and profile['continuous'] is True and profile['deadline_utc'] is None
            and profile['max_output_bytes'] is None, 'actual isolated continuous profile required')
    inputs.append(pin(T4 / PROFILE, profile_raw))

    validator_raw = finite(HOST / 'tools/ck3_capture_closed_receipt.py')
    projected = closure.project_v1(values['presentation-c23/hotfix_provider.py'], manifest_raw,
        runtime=T4, frozen_host=HOST, validator_raw=validator_raw, observed_at_utc=observed_at_utc)
    values['presentation-c23/hotfix_provider.py'] = projected['hotfix']
    inputs.append(pin(HOST / 'tools/ck3_capture_closed_receipt.py', validator_raw))
    owner_node, spec = assignment(values[OWNER], 'SPEC')
    old_spec = copy.deepcopy(spec)
    require(spec['machine_id'] == MACHINE and Path(spec['target_runtime']).resolve() == T4,
            'actual retained owner SPEC differs')
    spec.update(generation='C23-A05', target_runtime=str(T5), display_nonce=display_nonce,
                previous_Game_tuple=list(OLD_GAME))
    text = values[OWNER].decode('utf-8')
    segment = ast.get_source_segment(text, owner_node)
    require(text.count(segment) == 1, 'single literal SPEC seam required')
    values[OWNER] = text.replace(segment, 'SPEC=' + repr(spec), 1).encode('utf-8')
    require(values[OWNER].replace(('SPEC=' + repr(spec)).encode(), segment.encode(), 1)
            == text.encode('utf-8'), 'owner changed outside literal SPEC')
    provider = json.loads(values[PROVIDER])
    require(provider['machine_id'] == MACHINE and provider['generation'] == 'C23',
            'actual immutable static provider required')
    for name, ref in provider['sources'].items():
        relative = 'presentation-c23/g2_saved_campaign/' + name + '.py'
        require(ref == pin(T4 / relative, values[relative]), 'static provider source input differs')
        provider['sources'][name] = pin(T5 / relative, values[relative])
    values[PROVIDER] = encode(provider)
    rows = [dict(pin(T5 / name, raw), relative_path=name) for name, raw in values.items()]
    dependency = dict(pin(HOST / 'tools/ck3_capture_closed_receipt.py', validator_raw),
                      relative_path='@frozen-host/tools/ck3_capture_closed_receipt.py')
    rows.append(dependency)
    values[MANIFEST] = encode({'schema': 'xar.display-source-pins-with-frozen-dependency/v1',
                              'machine_id': MACHINE, 'files': rows})
    require(len(values) == len(rows) == 18, 'complete eighteen-leaf graph plus validator row required')
    for name, raw in values.items():
        if name.endswith('.py'):
            compile(raw, str(T5 / name), 'exec')

    name = 'ManagedWindowCapture-' + display_nonce
    require(name != profile['profile_name'] and name != profile['collection_name'],
            'independent private profile UUID required')
    profile.update(profile_name=name, collection_name=name, recording_root=str(T5 / 'recordings'),
                   machine_id=MACHINE, prepared_at_utc=observed_at_utc,
                   storage_review_at_utc=full['review_at_utc'], A05_display_nonce=display_nonce)
    profile['storage'] = storage_binding_v1(full_raw, canonical_path=str(T5 / 'STORAGE-ADMISSION.json'))
    companions = {T5 / PROFILE: encode(profile),
                  **_portable_companions(profile, values['presentation-c23/ck3_obs_capture_png_retry_c23.py'])}
    require(not any(p.exists() for p in companions), 'private profile companions require create-only paths')
    # global.ini carries the existing owned websocket secret. Pin it without
    # exposing its content; its reuse never grants permission to mutate it.
    global_path = Path(profile['config_root']) / 'global.ini'
    global_raw = finite(global_path)
    websocket = configparser.ConfigParser(interpolation=None)
    websocket.read_string(global_raw.decode('utf-8-sig'))
    require(websocket.getint('OBSWebSocket', 'ServerPort') == profile['port']
            and websocket.get('OBSWebSocket', 'ServerPassword') == profile['password']
            and websocket.getboolean('OBSWebSocket', 'ServerEnabled')
            and websocket.getboolean('OBSWebSocket', 'AuthRequired'),
            'owned existing websocket settings differ from actual private profile')
    inputs.append(pin(global_path, global_raw))
    inputs.extend([pin(__file__, finite(__file__)),
                   pin(closure.__file__, finite(closure.__file__))])
    environment = _task_environment(old_task)
    review = {
        'schema': 'xar.C23-A05-complete-display-RAM-review/v1',
        'machine_id': MACHINE, 'observed_at_utc': observed_at_utc,
        'status': 'RAM_ONLY_NOT_INSTALLED', 'display_nonce': display_nonce,
        'source_runtime': str(T4), 'target_runtime': str(T5),
        'inputs': inputs, 'full_storage_ref': full_storage_ref,
        'storage_review_at_utc': full['review_at_utc'],
        'previous_owner_SPEC': old_spec, 'new_owner_SPEC': spec,
        'files': [pin(T5 / name, raw) | {'relative_path': name} for name, raw in values.items()],
        'display_leaf_count': 18, 'manifest_source_rows': 18,
        'external_validator': dependency,
        'closure_projection': projected['review'],
        'Task_environment': environment, 'required_Task_root': str(TASK5),
        'Task_SPEC_status': 'DEFERRED_UNTIL_ACTUAL_NEW_GAME_LAUNCH_AND_PLACEMENT',
        'companion_files': [pin(p, raw) for p, raw in companions.items()],
        'companion_purpose': 'new private profile and fresh profile/scene UUID; old portable engine/global settings are inputs',
        'profile_name': name, 'collection_name': name,
        'portable_obs_root': profile['obs_root'], 'portable_config_root': profile['config_root'],
        'companion_roots': [str(T5), profile['config_root']], 'profile_password_printed': False,
        'prerequisite_directories': [str(T5 / 'recordings')],
        'recordings_parent_required_before_prepare_or_Run': True,
        'static_provider_input': pin(T5 / PROVIDER, values[PROVIDER]),
        'static_provider_is_input_not_attempt_output': True,
        'fresh_output_namespace': [str(T5 / spec[k]) for k in OUTPUT_NAMESPACE_KEYS],
        'source_graph_bytes': sum(map(len, values.values())),
        'companion_bytes': sum(map(len, companions.values())),
        'old_runtime_writes': 0, 'Game_OBS_Task_desktop_calls': 0,
        'body_hash_bytes_Driver_SAVE_media': 0,
        'runtime_or_import_qualification_granted': False,
    }
    return values, review, companions


def compose(plan):
    """Deterministic explicit-plan interface for Root's RAM union/adopter."""
    require(type(plan) is dict and set(plan) == {
        'schema', 'machine_id', 'full_storage_ref', 'observed_at_utc', 'display_nonce'}
        and plan['schema'] == 'xar.C23-A05-display-prepare-input/v1',
        'exact finite display plan schema/fields required')
    return build_sources(full_storage_ref=plan['full_storage_ref'],
                         observed_at_utc=plan['observed_at_utc'],
                         display_nonce=plan['display_nonce'], machine_id=plan['machine_id'])


def build_task_spec(display_values, display_review, *, task_nonce,
                    game_launch_ref, placement_ref):
    """Bind one new Task SPEC after real Game receipts exist; never register it."""
    _nonce(task_nonce)
    require(display_review['machine_id'] == MACHINE
            and display_review['target_runtime'] == str(T5)
            and task_nonce != display_review['display_nonce'] and not TASK5.exists(),
            'independent actual A05 display Task required')
    require(len(display_values) == 18
            and all(pin(T5 / row['relative_path'], display_values[row['relative_path']])
                    == {k: row[k] for k in ('path', 'bytes', 'sha256')}
                    for row in display_review['files']), 'complete reviewed graph differs')
    launch, placement = json.loads(checked(game_launch_ref)), json.loads(checked(placement_ref))
    require(Path(game_launch_ref['path']).resolve() == T5 / 'ROOT-ACTUAL-GAME-LAUNCH-C23.json'
            and Path(placement_ref['path']).resolve() == T5 / 'ROOT-GAME-PLACEMENT-C23.json',
            'actual new Game receipts must use the A05 namespace')
    game = (launch.get('pid'), launch.get('creation_filetime'))
    require(launch.get('machine_id') == placement.get('machine_id') == MACHINE
            and all(type(v) is int and v > 0 for v in game) and game != OLD_GAME
            and game == (placement.get('pid'), placement.get('creation_filetime'))
            and placement.get('status') == 'GREEN'
            and placement.get('foreground_unchanged') is True
            and placement.get('current_desktop_unchanged') is True,
            'actual independent placed Game tuple required')
    old_raw = finite(TASK4)
    require((len(old_raw), sha(old_raw)) == TASK4_PIN, 'original actual Task SPEC differs')
    old = json.loads(old_raw)
    require(task_nonce != old['nonce'], 'old once-only Task nonce cannot recur')
    task = copy.deepcopy(old)
    task.update(nonce=task_nonce, task_name='XARG2ManagedOwner-' + task_nonce,
                root=str(TASK5), cwd=str(T5), stage=str(T5 / OWNER),
                stage_sha256=sha(display_values[OWNER]), env=display_review['Task_environment'])
    args = [arg.replace(str(T4), str(T5)) for arg in task['stage_args']]
    args[args.index('--game-pid') + 1] = str(game[0])
    args[args.index('--game-birth') + 1] = str(game[1])
    task['stage_args'] = args
    return {TASK5 / 'SPEC.json': encode(task)}, {
        'machine_id': MACHINE, 'observed_at_utc': datetime.now(timezone.utc).isoformat(),
        'nonce': task_nonce, 'Game': list(game), 'game_launch': game_launch_ref,
        'placement': placement_ref, 'Task_SPEC': pin(TASK5 / 'SPEC.json', encode(task)),
        'required_environment_H_tools': str(HOST / 'tools'), 'registered_or_run': False,
        'prerequisite_recordings_directory': str(T5 / 'recordings')}
