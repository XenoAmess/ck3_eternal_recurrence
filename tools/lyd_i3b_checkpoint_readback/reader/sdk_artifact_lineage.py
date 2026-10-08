"""Read verified SDK source/metadata artifacts without importing or executing them."""
from __future__ import annotations
import ast
import hashlib
import json
import re
from pathlib import Path

FROZEN_CODEC_CONTRACT_SHA256 = 'a8ddde00321b53ec43fa1cebe38cd14f8ffc62407f61fbb95b8636476d044969'
FROZEN_DTO_PRIMITIVES_SHA256 = '39c6b004baf91a79db9beaa991a3a4a462ce81418f58b3a7f78c86805f935944'
FROZEN_BUILD_IDENTITY_SHA256 = '9f7665ed680238f6904bc3ef22e1d67ef9b4ccd047e699542d5dbaff24b01086'
PURE_BUILD_HELPERS = ('_query_build', '_operation_backend')
FROZEN_METADATA_PROJECTION_SHA256 = '422f55005412f68b24ded177e63ba616a35a2c74a2982d0559eb704327e6803a'
PURE_DTO_FUNCTIONS = (
    'integer', 'exact', 'optional', 'full_id', 'nullable_id', 'reason',
    '_common_payload', '_ids', 'normalize_assembly', 'normalize_title',
    'project_native_query', 'normalize_public_query',
)
GRAPH_TOOL_NAME = 'ck3_query_profile_confucian_challenger_graph_v1'
ACTOR_CACHE_TOOL_NAME = 'ck3_query_profile_actor_cached_succession_v1'
GRANT_TOOL_NAMES = (
    'ck3_query_profile_grant_title_picker_v1',
    'ck3_prepare_profile_grant_title_picker_v1',
    'ck3_select_profile_grant_title_picker_v1',
    'ck3_send_profile_grant_title_picker_v1',
)

def need(ok, message):
    if not ok:
        raise ValueError(message)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def _functions(data, label, names=PURE_DTO_FUNCTIONS):
    tree = ast.parse(data.decode('utf-8-sig'), filename=label)
    result = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in names:
            need(node.name not in result, 'duplicate pure DTO function ' + node.name)
            result[node.name] = node
    need(set(result) == set(names), 'missing exact pure DTO functions')
    return result

def verify_codec_artifact(descriptor, declared_sha256):
    """Hash and parse the same bounded source buffer; retain full actual SHA separately."""
    need(type(descriptor) is dict and set(descriptor) == {'path', 'bytes', 'sha256'}, 'closed SDK codec artifact descriptor')
    need(type(descriptor['path']) is str and Path(descriptor['path']).suffix.lower() == '.py', 'SDK codec artifact must be Python source')
    need(type(descriptor['bytes']) is int and 0 < descriptor['bytes'] <= 2 * 1024 * 1024, 'bounded SDK codec bytes')
    need(type(declared_sha256) is str and re.fullmatch('[0-9a-f]{64}', declared_sha256) is not None and descriptor['sha256'] == declared_sha256, 'actual SDK codec descriptor SHA differs')
    path = Path(descriptor['path'])
    need(path.stat().st_size == descriptor['bytes'], 'SDK codec artifact size mismatch')
    raw = path.read_bytes()
    need(len(raw) == descriptor['bytes'] and sha(raw) == declared_sha256, 'SDK codec artifact bytes/SHA mismatch')
    fixed_path = Path(__file__).parent / 'dependencies/confucian_dto_primitives.py'
    fixed_raw = fixed_path.read_bytes()
    need(sha(fixed_raw) == FROZEN_DTO_PRIMITIVES_SHA256, 'frozen DTO projection bytes changed')
    actual, frozen = _functions(raw, 'actual SDK codec'), _functions(fixed_raw, 'frozen DTO projection')
    matches = {name: ast.dump(actual[name], include_attributes=False) == ast.dump(frozen[name], include_attributes=False) for name in PURE_DTO_FUNCTIONS}
    need(all(matches.values()), 'actual SDK pure DTO AST differs: ' + ','.join(name for name, match in matches.items() if not match))
    actual_helpers = _functions(raw, 'actual SDK build helpers', PURE_BUILD_HELPERS)
    frozen_helpers = _functions(fixed_raw, 'frozen build helpers', PURE_BUILD_HELPERS)
    helper_matches = {name: ast.dump(actual_helpers[name], include_attributes=False) == ast.dump(frozen_helpers[name], include_attributes=False) for name in PURE_BUILD_HELPERS}
    need(all(helper_matches.values()), 'actual SDK build helper AST differs')
    build_identity_raw = (fixed_path.parent / 'native_build_identity.py').read_bytes()
    need(sha(build_identity_raw) == FROZEN_BUILD_IDENTITY_SHA256, 'frozen exact build identity bytes changed')
    return {'actual_artifact': dict(descriptor), 'actual_sha256': declared_sha256,
            'frozen_codec_contract_sha256': FROZEN_CODEC_CONTRACT_SHA256,
            'frozen_primitives_sha256': FROZEN_DTO_PRIMITIVES_SHA256,
            'pure_DTO_AST_matches': matches, 'all_12_match': True,
            'pure_build_helper_AST_matches': helper_matches,
            'frozen_build_identity_sha256': FROZEN_BUILD_IDENTITY_SHA256,
            'source_executed': False, 'actual_acceptance_credit': None}

def verify_metadata_artifact(metadata, descriptor, declared_sha256):
    """Keep explicit 23/24/28/29 identities and exact frozen G2/G3 schemas."""
    need(descriptor['sha256'] == declared_sha256, 'actual SDK metadata descriptor SHA differs')
    need(type(metadata) is list and len(metadata) in (23, 24, 28, 29), 'actual SDK metadata must explicitly contain 23, 24, 28 or 29 tools')
    need(all(type(row) is dict and type(row.get('name')) is str for row in metadata), 'SDK Tool metadata rows')
    rows = {row['name']: row for row in metadata}
    need(len(rows) == len(metadata), 'duplicate SDK Tool metadata names')
    reference_path = Path(__file__).parent / 'dependencies/frozen_sdk_g2_g3_metadata.json'
    reference_raw = reference_path.read_bytes()
    need(sha(reference_raw) == FROZEN_METADATA_PROJECTION_SHA256, 'frozen G2/G3 metadata projection bytes changed')
    reference = json.loads(reference_raw)
    names = set(reference['readonly23_tool_names'])
    wanted_names = names if len(metadata) == 23 else names | {GRAPH_TOOL_NAME}
    if len(metadata) in (28, 29):
        wanted_names |= set(GRANT_TOOL_NAMES)
    if len(metadata) == 29:
        wanted_names.add(ACTOR_CACHE_TOOL_NAME)
    need(set(rows) == wanted_names and len(wanted_names) == len(metadata), 'actual SDK metadata tool set differs from declared readonly23/challenger24/grant28/actor-cache29 factory')
    for name, row in reference['G2_G3_tools'].items():
        need(json.dumps(rows[name], sort_keys=True, separators=(',', ':'), allow_nan=False) == json.dumps(row, sort_keys=True, separators=(',', ':'), allow_nan=False), 'actual SDK G2/G3 Tool metadata differs: ' + name)
    if len(metadata) == 29:
        actor_cache = json.loads(json.dumps(reference['G2_G3_tools']['ck3_query_profile_confucian_assembly_predicates_v1']))
        actor_cache['name'] = ACTOR_CACHE_TOOL_NAME
        actor_cache['description'] = "Read the actor's complete native cached successor IDs in original order."
        actor_cache['inputSchema']['title'] = ACTOR_CACHE_TOOL_NAME + 'Arguments'
        actor_cache['outputSchema']['title'] = ACTOR_CACHE_TOOL_NAME + 'DictOutput'
        need(json.dumps(rows[ACTOR_CACHE_TOOL_NAME], sort_keys=True, separators=(',', ':'), allow_nan=False) == json.dumps(actor_cache, sort_keys=True, separators=(',', ':'), allow_nan=False), 'actual SDK actor-cache Tool metadata differs from its closed readonly revision-only schema')
    return {'actual_artifact': dict(descriptor), 'actual_sha256': declared_sha256,
            'actual_tool_count': len(metadata), 'G2_G3_tools_exact': True,
            'readonly23_reference_sha256': reference['readonly23_source_artifact_sha256'],
            'actual_acceptance_credit': None}
