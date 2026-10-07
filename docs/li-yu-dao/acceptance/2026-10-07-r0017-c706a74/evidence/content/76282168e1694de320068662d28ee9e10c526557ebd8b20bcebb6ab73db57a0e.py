"""Read-only ROOT-bound file verification; no process, client, guard or pipe call."""
from pathlib import Path
import ast
import hashlib
import json
import math
import re

FIELDS = {'schema', 'epoch_id', 'source_revision', 'run_root', 'profile', 'guard', 'dll',
          'metadata', 'source_inventory', 'normal_exit_source_inventory', 'server',
          'native_build', 'normal_exit_cpp_sha256',
          'target', 'queue_directory', 'client_output_directory', 'root_prepared', 'source_ready', 'attempt_id', 'source_export', 'root_screen_task'}

PROFILE_FIELDS = {'schema_version', 'guard_profile', 'guard_profile_sha256', 'userdir',
                  'evidence_directory', 'game_version', 'state_directory', 'dll', 'injector'}
REPO = Path('C:/lr17s1').resolve()
EXTERNAL_BASE = Path('C:/workspace/ck3_lyd_runtime_20261004').resolve()
ORDINARY_CONTRACT_PATH = 'ck3_autonomous_player/src/xar_autoplayer/bridge/ordinary_interaction_contract.py'
ORDINARY_CONTRACT_SHA256 = 'e0a96aa39626df166270d3d5467a8e4d57cec77d7577cebcced03983feba5fa3'
EXPECTED_SOURCE_REVISION = 'c706a74f9d00dd842b7edce8901fb3417344fd9c'
EXPECTED_NORMAL_EXIT_CPP_SHA256 = '7e6ad9dac329838fca84f1b81790f6a5737d4a44475edf61cbdff68868267c2d'
EXPECTED_SERVER_SHA256 = 'b2022b3afbe6c82d3455bdea10b2e4a4560492f32b00c0f87d29fda524253882'
NORMAL_EXIT_CPP_PATH = 'ck3_autonomous_player/native_bridge/src/normal_exit_map_source_v1.cpp'
CONFUCIAN_READONLY_PATH = 'ck3_autonomous_player/src/xar_autoplayer/bridge/confucian_readonly_private_v1.py'
CONFUCIAN_READONLY_SHA256 = '9b9e87e1c6981f6b74382d291ad1f9c33c10f1f1e0002e1bfd704ec11e800681'
PRIVATE_QUERY_TOOLS = frozenset(['ck3_query_profile_confucian_assembly_predicates_v1', 'ck3_query_profile_confucian_religious_title_v1'])
REQUIRED_BUILD_FLAGS = {'XAR_CK3_ENABLE_INGAME_DECISION_ITEM_ACTIONS_PRIVATE_V1', 'XAR_CK3_ENABLE_CONFUCIAN_RELIGIOUS_TITLE_PRIVATE_QUERY_V1', 'XAR_CK3_ENABLE_FEUDAL_1066_SELECTED_BOOKMARK_START_PRIVATE_V1', 'XAR_CK3_ENABLE_NORMAL_EXIT_MAP_PRIVATE_V1', 'XAR_CK3_ENABLE_INGAME_DECISION_OUTCOME_PRIVATE_V1', 'XAR_CK3_ENABLE_ORDINARY_INTERACTION_PRIVATE_V1', 'XAR_CK3_ENABLE_INGAME_DECISIONS_OPEN_PRIVATE_V1', 'XAR_CK3_ENABLE_CURRENT_ACTOR_STRESS_ADJUSTMENT_PRIVATE_V1', 'XAR_CK3_ENABLE_FEUDAL_1066_BOOKMARK_MODEL_PRIVATE_V1', 'XAR_CK3_ENABLE_GRANT_TITLE_PICKER_PRIVATE_V1', 'XAR_CK3_ENABLE_CONFUCIAN_ASSEMBLY_PREDICATES_PRIVATE_QUERY_V1', 'XAR_CK3_ENABLE_CONFUCIAN_CHALLENGER_GRAPH_PRIVATE_QUERY_V1'}
PREVIOUS_SOURCE_REVISION = '54457b371e947edb86903c2ebd578034f02695db'
RETIRED_SOURCE_REVISIONS = {'632f0a57a07aa6299052004589ed6f7632e7d8f7', 'd0f8fa3b9d444828759443aa018bfd7ad31b398d', PREVIOUS_SOURCE_REVISION, 'b09983782670e0646e5c911bb4a385d30750ab01', '3bd0ed926fef86f2660f2ed80c231dd9682ee877', '8f5b0f0a12eacf683bbd7e9b3f182cc977424ed1'}
PREVIOUS_TARGET = {'pid': 13436, 'process_create_time': 1791196395.7422996}
R11_TARGET = {'pid': 15684, 'process_create_time': 1791253039.4638472}
def run_namespace(binding):
    attempt=binding['attempt_id']
    if type(attempt) is not str or not re.fullmatch('R[0-9]{4}',attempt) or int(attempt[1:])<=14:
        raise ValueError('Explicit newly allocated attempt after R14 required')
    number=int(attempt[1:])
    if Path(binding['run_root']).resolve()!=EXTERNAL_BASE/('live-attempt-'+str(number).zfill(3)):
        raise ValueError('Run directory must match actual allocated attempt')
    if Path(binding['source_export']).resolve()!=REPO:
        raise ValueError('Actual new clean export path differs')
    if type(binding['root_screen_task']) is not str or not re.fullmatch('[A-Za-z0-9_.:-]{6,160}',binding['root_screen_task']):
        raise ValueError('Actual root screen task required')
    return 'lyd.r'+str(number)+'.'


def validate_profile_shape(profile, normal_exit_reference):
    if not isinstance(profile, dict) or set(profile) not in (PROFILE_FIELDS, PROFILE_FIELDS | {'normal_exit_source_inventory'}):
        raise ValueError('profile must have the original nine fields or only the known tenth exit inventory')
    if type(profile['schema_version']) is not int or profile['schema_version'] != 1:
        raise ValueError('profile schema_version must be integer 1')
    if set(profile) == PROFILE_FIELDS:
        if normal_exit_reference is not None:
            raise ValueError('nine-field profile requires null exit inventory binding')
    elif normal_exit_reference is None or profile['normal_exit_source_inventory'] != normal_exit_reference:
        raise ValueError('tenth profile field must equal the explicit exit inventory binding')
    return profile


def validate_build_report(report, binding, profile):
    # A new clean-source private23 native qualification is still pending.
    # Never apply the historical 632/eight-flag gate to the new build.
    from consumer_native_build_adapter import validate_actual_r14_build
    return validate_actual_r14_build(report, binding, profile)



def sized_reference(row):
    exact(row, {'path','bytes','sha256'}, 'sized immutable reference')
    path,raw = reference({key:row[key] for key in ('path','sha256')})
    if type(row['bytes']) is not int or row['bytes'] != len(raw):
        raise ValueError('actual sized reference byte count differs')
    return path,raw


def short_reference(row):
    sized_reference(row)
    return {'path':Path(row['path']).resolve().as_posix(),'sha256':row['sha256']}


def validate_root_prepared(binding, profile, target):
    _,raw = reference(binding['root_prepared'])
    prepared = json.loads(raw)
    if (prepared.get('schema') != run_namespace(binding)+'root-profile-bound-preparation.v1'
            or prepared.get('status') != 'PREPARED_FILES_AND_ROOT_LIVE_PROFILE_ONLY'
            or prepared.get('source_revision') != binding['source_revision']
            or prepared.get('consumer_created') is not False or prepared.get('native_attached') is not False):
        raise ValueError('actual R14 PREPARED live-profile receipt is required')
    selected_name = 'profile' if 'normal_exit_source_inventory' in profile else 'original_profile'
    if (not same_reference(short_reference(prepared.get(selected_name)), binding['profile'])
            or not same_reference(short_reference(prepared.get('guard')), binding['guard'])
            or ('normal_exit_source_inventory' in profile and
                not same_reference(prepared.get('normal_exit_source_inventory'), binding['normal_exit_source_inventory']))):
        raise ValueError('PREPARED profile/guard/inventory differs from binding')
    review = prepared.get('root_actual_live_binding',{})
    if (review.get('schema') != run_namespace(binding)+'root-live-guard-review.v1'
            or review.get('status') != 'ROOT_REVIEWED_ACTUAL_LIVE_BINDING'
            or review.get('source_head') != binding['source_revision']
            or review.get('root_screen_task') != binding['root_screen_task']
            or type(review.get('process_id')) is not int or review['process_id'] != target['pid']
            or type(review.get('process_create_time')) is not type(target['process_create_time'])
            or review['process_create_time'] != target['process_create_time']):
        raise ValueError('ROOT actual live profile identity differs')
    original = json.loads(sized_reference(prepared.get('original_profile'))[1])
    validate_profile_shape(original, None)
    for name in PROFILE_FIELDS:
        if original[name] != profile[name]:
            raise ValueError('original nine-field profile changed during tenth-field binding')
    for name in ('fresh_steam_offline_review','fresh_sole_owner_receipt','launch_receipt'):
        sized_reference(review.get(name))


def source_ready_files(index_path, index):
    exact(index, {'schema','files'}, 'actual source007 ready INDEX')
    if (index['schema'] != 'lyd.claim-verifier007.source-ready-index.v1'
            or type(index['files']) is not list or not index['files']):
        raise ValueError('prepared source-author cannot replace a nonempty actual source007 ready INDEX')
    root = index_path.parent.resolve()
    indexed = {}
    seen_paths = set()
    for row in index['files']:
        exact(row, {'path','bytes','sha256'}, 'source007 indexed file')
        name = row['path']
        if (type(name) is not str or not name or '\\' in name
                or name.startswith('/') or ':' in name
                or any(part in ('', '.', '..') for part in name.split('/'))
                or type(row['bytes']) is not int or row['bytes'] <= 0):
            raise ValueError('source007 row requires normalized relative path and positive integer bytes')
        path = (root / name).resolve()
        if root not in path.parents or path in seen_paths:
            raise ValueError('source007 indexed path escapes or is duplicate')
        seen_paths.add(path)
        _,raw = sized_reference({'path':str(path),'bytes':row['bytes'],'sha256':row['sha256']})
        indexed[str(path)] = raw
    required = ('SOURCE-READBACK.json', 'unbound-bundle-011/verifier.py',
                'bind_verifier.py', 'emit_first_join_evidence.py',
                'unbound-bundle-011/SOURCE-PIN-RECORD.raw.json',
                'unbound-bundle-011/INDEX.json')
    if any(str((root / name).resolve()) not in indexed for name in required):
        raise ValueError('canonical source007 provider/binder/emitter/readback/bundle files are not indexed')
    bundle_root = root / 'unbound-bundle-011'
    local = exact(json.loads(indexed[str((bundle_root / 'INDEX.json').resolve())]),
                  {'schema','verifier_id','entrypoint','files'}, 'source007 unbound bundle INDEX')
    if (local['schema'] != 'ck3-ordinary-interaction-consumption-verifier-bundle-v1'
            or local['verifier_id'] != 'lyd-first-join-actual-save-v1'
            or local['entrypoint'] != 'verifier.py:verify_consumption'
            or type(local['files']) is not list or len(local['files']) != 2):
        raise ValueError('canonical unbound source007 bundle metadata differs')
    local_seen = set()
    for row in local['files']:
        exact(row, {'path','sha256'}, 'source007 unbound bundle file')
        name = row['path']
        if name not in ('SOURCE-PIN-RECORD.raw.json','verifier.py') or name in local_seen:
            raise ValueError('unbound source007 bundle files must be exact distinct basenames')
        local_seen.add(name)
        raw = indexed[str((bundle_root / name).resolve())]
        if row['sha256'] != hashlib.sha256(raw).hexdigest():
            raise ValueError('unbound source007 bundle file hash differs from outer verified bytes')
    return indexed


def validate_source_ready(binding, profile):
    ready = exact(binding['source_ready'], {'metadata_capture_result'}, 'actual clean-source ready binding')
    metadata = json.loads(sized_reference(ready['metadata_capture_result'])[1])
    if not same_reference(ready['metadata_capture_result'], EXPECTED_METADATA_RESULT):
        raise ValueError('consumer must use the actual immutable metadata author result')
    if (metadata.get('head') != binding['source_revision']
            or metadata.get('status') != 'ACTUAL_OFFICIAL_CLIENT_METADATA_AND_FRESH_CODE_INVENTORY'
            or metadata.get('tool_count') != 28 or metadata.get('default_tool_count') != 21
            or metadata.get('factory_opt_in') != {'confucian_readonly_tools': False, 'confucian_challenger_tools': True, 'player_control_tools': False, 'grant_title_picker_tools': True}
            or not same_reference(short_reference(metadata['metadata']), binding['metadata'])
            or not same_reference(short_reference(metadata['source_inventory']), binding['source_inventory'])
            or not same_reference(short_reference(metadata['native_clean_qualification']), binding['native_build'])):
        raise ValueError('actual metadata/source/native qualification differs from this consumer')
    for name in ('actual_export_report', 'actual_imported_origins', 'default_metadata'):
        sized_reference(metadata[name])


def exact(value, fields, label):
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError(label + ' requires exact fields')
    return value


def reference(row):
    exact(row, {'path', 'sha256'}, 'immutable file reference')
    if (not isinstance(row['path'], str) or not Path(row['path']).is_absolute()
            or not isinstance(row['sha256'], str) or not re.fullmatch('[0-9a-f]{64}', row['sha256'])):
        raise ValueError('immutable file needs absolute path and exact lower-case SHA-256')
    path = Path(row['path']).resolve()
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != row['sha256']:
        raise ValueError('immutable file SHA changed: ' + str(path))
    return path, raw


def validate_private_query_arguments(arguments):
    exact(arguments, {'expected_revision'}, 'private readonly tool arguments')
    revision = arguments['expected_revision']
    if type(revision) is not int or not 0 < revision < 2**64:
        raise ValueError('private readonly expected_revision must be a strict positive uint64')
    return arguments


def qualified_source_pins():
    if (type(EXPECTED_SOURCE_REVISION) is not str
            or not re.fullmatch('[0-9a-f]{40}', EXPECTED_SOURCE_REVISION)
            or any(type(value) is not str or not re.fullmatch('[0-9a-f]{64}', value)
                   for value in (EXPECTED_NORMAL_EXIT_CPP_SHA256, EXPECTED_SERVER_SHA256))):
        raise ValueError('R14 clean-source author qualification is PENDING; template cannot bind')


def checked_inventory(rows, tools):
    if not isinstance(rows, list) or any(not isinstance(row, dict) or not isinstance(row.get('name'), str) for row in rows):
        raise ValueError('actual metadata must be a serialized tool list')
    mapping = {row['name']: row for row in rows}
    if len(mapping) != len(rows) or set(mapping) != set(tools):
        raise ValueError('actual tools differ from this consumer exact allowlist')
    if any(row.get('inputSchema', {}).get('additionalProperties') is not False for row in rows):
        raise ValueError('profile tools must have closed input schemas')
    observer = mapping['ck3_observe_profile_normal_exit_v1']
    if observer['inputSchema'].get('properties') != {} or observer['inputSchema'].get('required', []) != []:
        raise ValueError('retained-handle observer must have no arguments')
    if observer.get('annotations', {}).get('readOnlyHint') is not True:
        raise ValueError('exit observer must be declared read-only')
    for name in PRIVATE_QUERY_TOOLS:
        tool = mapping[name]
        schema = tool['inputSchema']
        if (schema.get('required') != ['expected_revision']
                or set(schema.get('properties', {})) != {'expected_revision'}
                or tool.get('annotations', {}).get('readOnlyHint') is not True):
            raise ValueError('private readonly tools require one closed revision argument and readonly annotation')
        revision = schema['properties']['expected_revision']
        if (revision.get('type') != 'integer'
                or type(revision.get('exclusiveMinimum')) is not int or revision['exclusiveMinimum'] != 0
                or type(revision.get('exclusiveMaximum')) is not int or revision['exclusiveMaximum'] != 2**64):
            raise ValueError('private readonly revision schema must preserve strict positive uint64 bounds')
    for name in PRIVATE_QUERY_TOOLS:
        check_readonly_tool(mapping[name])
    check_readonly_tool(mapping[CHALLENGER_TOOL], challenger=True)
    for name in GRANT_TOOLS:check_grant_tool(mapping[name])
    return mapping


def load_binding(path, expected_sha256, *, profile, queue, output, tools):
    qualified_source_pins()
    _, raw = reference({'path': str(Path(path).resolve()), 'sha256': expected_sha256})
    value = exact(json.loads(raw), FIELDS, 'ROOT R14 binding')
    if value['schema'] != 'ck3-root-official-mcp-consumer-binding-v1':
        raise ValueError('wrong R14 binding schema')
    if not isinstance(value['epoch_id'], str) or not re.fullmatch('[A-Za-z0-9][A-Za-z0-9._-]{1,95}', value['epoch_id']):
        raise ValueError('ROOT must assign a new R14 epoch ID')
    if not isinstance(value['source_revision'], str) or not re.fullmatch('[0-9a-f]{40}', value['source_revision']):
        raise ValueError('ROOT must bind the actual new source revision')
    if value['source_revision'] in RETIRED_SOURCE_REVISIONS:
        raise ValueError('retired R7/R8/R9 revision cannot bind the R14 consumer')
    if value['source_revision'] != EXPECTED_SOURCE_REVISION:
        raise ValueError('actual final R14 source revision differs')
    target = exact(value['target'], {'pid', 'process_create_time'}, 'actual process identity')
    if type(target['pid']) is not int or not 0 < target['pid'] < 2**32:
        raise ValueError('actual target PID is required')
    if (type(target['process_create_time']) not in (int, float)
            or not math.isfinite(target['process_create_time']) or target['process_create_time'] <= 0):
        raise ValueError('actual process creation time is required')
    if target == PREVIOUS_TARGET or target['pid'] == R11_TARGET['pid'] or target['process_create_time'] == R11_TARGET['process_create_time']:
        raise ValueError('historical R10 process identity cannot bind a new R14 epoch')
    if (not isinstance(value['normal_exit_cpp_sha256'], str)
            or not re.fullmatch('[0-9a-f]{64}', value['normal_exit_cpp_sha256'])):
        raise ValueError('ROOT must explicitly pin the actual new normal-exit source bytes')
    if value['normal_exit_cpp_sha256'] != EXPECTED_NORMAL_EXIT_CPP_SHA256:
        raise ValueError('actual final R14 normal-exit CPP differs')
    paths = {}
    for key in ('run_root', 'queue_directory', 'client_output_directory'):
        if not isinstance(value[key], str) or not Path(value[key]).is_absolute():
            raise ValueError('ROOT must provide absolute fresh run paths')
        paths[key] = Path(value[key]).resolve()
    run_root = paths['run_root']
    base = EXTERNAL_BASE
    run_namespace(value)
    if base not in run_root.parents:
        raise ValueError('R14 run root must stay inside the external work package')
    if Path(queue).resolve() != paths['queue_directory'] or Path(output).resolve() != paths['client_output_directory']:
        raise ValueError('CLI queue/output must match this immutable ROOT binding')
    if any(run_root not in paths[key].parents for key in ('queue_directory', 'client_output_directory')):
        raise ValueError('queue and output must belong to this new run root')
    if paths['queue_directory'] == paths['client_output_directory']:
        raise ValueError('queue and output must be distinct')
    refs = {key: reference(value[key]) for key in ('profile', 'guard', 'dll', 'metadata', 'source_inventory', 'native_build', 'server')}
    if Path(profile).resolve() != refs['profile'][0]:
        raise ValueError('CLI profile differs from this immutable ROOT binding')
    if run_root not in refs['profile'][0].parents or run_root not in refs['guard'][0].parents:
        raise ValueError('profile and guard must belong to the new R14 run root')
    profile_data = validate_profile_shape(json.loads(refs['profile'][1]), value['normal_exit_source_inventory'])
    if value['normal_exit_source_inventory'] is not None:
        refs['normal_exit_source_inventory'] = reference(value['normal_exit_source_inventory'])
    validate_build_report(json.loads(refs['native_build'][1]), value, profile_data)
    validate_root_prepared(value, profile_data, target)
    validate_source_ready(value, profile_data)
    guard_data = json.loads(refs['guard'][1])
    if (Path(profile_data['guard_profile']).resolve() != refs['guard'][0]
            or profile_data['guard_profile_sha256'].lower() != value['guard']['sha256']
            or profile_data['dll'] != value['dll']
            or profile_data.get('normal_exit_source_inventory') != value['normal_exit_source_inventory']):
        raise ValueError('profile guard/DLL/exit inventory does not match ROOT binding')
    if any(guard_data['target'].get(key) != target[key] for key in target):
        raise ValueError('actual guard process identity differs from ROOT binding')
    for key in ('userdir', 'state_directory', 'evidence_directory'):
        location = Path(profile_data[key]).resolve()
        if run_root not in location.parents:
            raise ValueError('profile directories must belong to the new run root')
    if value['normal_exit_source_inventory'] is not None and refs['normal_exit_source_inventory'][0] != (Path(profile_data['userdir']) / 'normal-exit-source-inventory-v1.json').resolve():
        raise ValueError('normal exit inventory must be the fixed userdir source file')
    repo = REPO
    if refs['server'][0] != repo / 'tools/ck3_native_profile_mcp.py':
        raise ValueError('use the actual integrated profile server')
    if value['server']['sha256'] != EXPECTED_SERVER_SHA256:
        raise ValueError('actual final R14 profile server differs')
    source_rows = json.loads(refs['source_inventory'][1])
    if not isinstance(source_rows, list) or not source_rows:
        raise ValueError('ROOT source inventory must be an actual nonempty frozen file list')
    seen = set()
    source_hashes = {}
    for row in source_rows:
        exact(row, {'path', 'bytes', 'sha256'}, 'actual source inventory row')
        if not isinstance(row['path'], str) or '\\' in row['path']:
            raise ValueError('source inventory paths must be normalized relative paths')
        relative = Path(row['path'])
        actual = (repo / relative).resolve()
        if relative.is_absolute() or repo not in actual.parents or row['path'] in seen:
            raise ValueError('source inventory path is duplicate or escapes the source tree')
        seen.add(row['path'])
        source_hashes[row['path']] = row['sha256']
        _, data = reference({'path': str(actual), 'sha256': row['sha256']})
        if type(row['bytes']) is not int or len(data) != row['bytes']:
            raise ValueError('actual source inventory byte count changed')
    if source_hashes.get(CONFUCIAN_READONLY_PATH) != CONFUCIAN_READONLY_SHA256:
        raise ValueError('new source inventory must pin the formal private Confucian reader')
    if source_hashes.get(CONFUCIAN_CHALLENGER_PATH) != CONFUCIAN_CHALLENGER_SHA256:
        raise ValueError('new source inventory must pin the exact challenger graph codec')
    if 'tools/ck3_native_profile_mcp.py' not in seen:
        raise ValueError('source inventory must bind the profile server source')
    if source_hashes.get(ORDINARY_CONTRACT_PATH) != ORDINARY_CONTRACT_SHA256:
        raise ValueError('new source inventory must pin the integrated e0a96 ordinary normalizer')
    if NORMAL_EXIT_CPP_PATH is None or source_hashes.get(NORMAL_EXIT_CPP_PATH) != value['normal_exit_cpp_sha256']:
        raise ValueError('new source inventory must pin the exact production normal-exit CPP')
    if source_hashes['tools/ck3_native_profile_mcp.py'] != value['server']['sha256']:
        raise ValueError('profile server inventory and binding SHA differ')
    checked_inventory(json.loads(refs['metadata'][1]), tools)
    return value


def verify_live_inventory(payload, binding, *, tools):
    if not isinstance(payload, dict) or payload.get('nextCursor') not in (None, ''):
        raise ValueError('actual Client list_tools must be a complete single inventory')
    live = checked_inventory(payload.get('tools'), tools)
    _, frozen = reference(binding['metadata'])
    expected = checked_inventory(json.loads(frozen), tools)
    if live != expected:
        raise ValueError('actual started Client tool metadata differs from ROOT frozen metadata')

EXPECTED_METADATA_RESULT = {'path': 'C:/workspace/ck3_lyd_runtime_20261004/r17-actual-sdk-metadata-20261007-001/RESULT.json', 'bytes': 7124, 'sha256': '31503d1314a6502fdc46890f12859f35e22085872ec448ac338e7b45d982ec26'}

from consumer_metadata_semantics import CHALLENGER_TOOL, check_readonly_tool, validate_challenger_arguments
CONFUCIAN_CHALLENGER_PATH = 'ck3_autonomous_player/src/xar_autoplayer/bridge/confucian_challenger_graph_v1.py'
CONFUCIAN_CHALLENGER_SHA256 = '0cbe8e39a61f5f283361786184328985c3e7b6b8963357a48dabd1a8c94d4002'

def same_reference(left, right):
    if left is None or right is None: return left is right
    if type(left) is not dict or type(right) is not dict or set(left) != set(right): return False
    return Path(left['path']).resolve() == Path(right['path']).resolve() and all(left[key] == right[key] for key in left if key != 'path')

from grant_metadata_semantics import GRANT_TOOLS, check_grant_tool
