"""Qualify a retained common CaseClient G4 row; never execute a tool or read SAVE.

The selected frozen DTO performs all graph validation. This module supplies the
missing common CaseClient plan/row/frame seam, without manufacturing a profile
receipt or qualifying any C3 business transition.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib
import json
from pathlib import Path
import re
import sys

TOOL = 'ck3_query_confucian_challenger_graph_v1'
SOURCE_SCHEMA = 'lyd.c3.common-g4-source-binding.v1'
REQUEST_SCHEMA = 'lyd.c3.common-g4-observation-request.v1'
RESULT_SCHEMA = 'lyd.c3.common-g4-native-observation.v1'


def need(value, message):
    if not value:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')


def read_ref(reference, cap):
    need(type(reference) is dict and set(reference) == {'path', 'bytes', 'sha256'}, 'Exact file reference required')
    path = Path(reference['path'])
    need(path.is_absolute() and path.suffix.lower() == '.json' and type(reference['bytes']) is int and
         0 < reference['bytes'] <= cap and type(reference['sha256']) is str and
         re.fullmatch('[0-9a-f]{64}', reference['sha256']), 'Bounded absolute JSON reference required')
    need(path.stat().st_size == reference['bytes'], 'Referenced JSON size changed')
    raw = path.read_bytes()
    need(len(raw) == reference['bytes'] and hashlib.sha256(raw).hexdigest() == reference['sha256'],
         'Referenced JSON bytes changed')
    return json.loads(raw.decode('utf-8-sig'))


def load_selected_dto(source):
    """Import actual frozen DTOs, not MCP/service/driver instances or endpoints."""
    need(type(source) is dict and set(source) == {'schema', 'source_head', 'source_root', 'source_index',
         'python_successor', 'manifest', 'game', 'native_basis'}, 'Exact source binding required')
    need(source['schema'] == SOURCE_SCHEMA and type(source['source_head']) is str and
         re.fullmatch('[0-9a-f]{40}', source['source_head']), 'Actual source commit required')
    root = Path(source['source_root']).resolve()
    need(root.is_absolute(), 'Actual frozen source root required')
    receipt = read_ref(source['python_successor'], 128 * 1024)
    need(receipt.get('source_commit') == source['source_head'] and Path(receipt['source_root']).resolve() == root and
         receipt.get('source_index') == source['source_index'], 'Source receipt/index identity differs')
    index = read_ref(source['source_index'], 4 * 1024**2)
    manifest = read_ref(source['manifest'], 256 * 1024)
    features = manifest.get('host_features', {})
    need(type(features) is dict and features.get('confucian_challenger_readonly') is True and
         all(type(v) is bool for v in features.values()), 'Shared G4 permission is not explicitly enabled')
    need(manifest.get('capabilities', {}).get(TOOL, {}).get('source_build_ready') is True,
         'Selected manifest has no declared source-ready G4 capability')
    src = root / 'ck3_autonomous_player/src'
    sys.path.insert(0, str(src))
    graph = importlib.import_module('xar_autoplayer.bridge.confucian_challenger_graph_v1')
    private = importlib.import_module('xar_autoplayer.bridge.confucian_readonly_private_v1')
    modules = (graph, private,
        importlib.import_module('xar_autoplayer.bridge.nonwar_private_build'),
        importlib.import_module('xar_autoplayer.bridge.version_identity'))
    pins = []
    for module in modules:
        path = Path(module.__file__).resolve()
        need(path.is_relative_to(src), 'Previously imported DTO belongs to another source')
        relative = path.relative_to(root).as_posix()
        declared = index['files'][relative]
        raw = path.read_bytes()
        pin = {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
        need({k: pin[k] for k in ('bytes', 'sha256')} == declared, 'Selected frozen DTO bytes changed: ' + relative)
        pins.append(pin)
    need(source['game'] == {'version': private.CK3_12004.game_version,
         'executable_sha256': private.CK3_12004.executable_sha256}, 'This current C3 seam requires exact .4')
    return graph, private, pins


def one_completed_row(packet):
    need(type(packet) is dict and set(packet) == {'rows', 'business_PASS_inferred'} and
         packet['business_PASS_inferred'] is False and type(packet['rows']) is list and len(packet['rows']) == 1,
         'One original CaseClient actual-results packet required; profile receipts are a different contract')
    row = packet['rows'][0]
    need(type(row) is dict and row.get('ok') is True and row.get('error') is None and
         type(row.get('started_at')) is str and row['started_at'] and
         type(row.get('finished_at')) is str and row['finished_at'], 'One completed successful common tool row required')
    return row


def qualify_observation(frame, plan, packet, graph, private):
    """Pure retained-observation seam. No grant, mutation, retry or business PASS."""
    need(type(plan) is dict and set(plan) == {'steps'} and type(plan['steps']) is list and len(plan['steps']) == 1,
         'One explicitly authored G4 plan required')
    step = plan['steps'][0]
    need(type(step) is dict and set(step) == {'id', 'tool', 'args', 'fresh_revision'} and
         type(step['id']) is str and step['id'] and step['tool'] == TOOL and step['fresh_revision'] is False,
         'Public G4 identity and explicit snapshot revision required')
    args = step['args']
    need(type(args) is dict and set(args) == {'expected_revision', 'faith_full_ids'}, 'Exact G4 arguments required')
    selectors = graph.validate_faith_ids(args['faith_full_ids'])
    binding = private.query_binding(frame, args['expected_revision'])
    hello = frame['diagnostics']['hello']
    need(private._query_build({'game_version': hello.get('expected_ck3_version'),
         'executable_sha256': hello.get('expected_ck3_sha256')}) == private.CK3_12004,
         'Current common C3 observation requires the exact .4 build')
    need(frame.get('source') == 'injected-dll-named-pipe' and frame.get('backend_id') == 'native-headless' and
         frame.get('episode_projection') == 'native_campaign' and
         type(frame['diagnostics'].get('bridge_pid')) is int and frame['diagnostics']['bridge_pid'] == binding['game_pid'] and
         type(hello.get('connection_generation')) is int and hello['connection_generation'] == binding['connection_generation'],
         'Actual common native owner frame differs')
    row = one_completed_row(packet)
    need(row.get('id') == step['id'] and row.get('plan') == step, 'Actual row differs from its original explicit G4 plan')
    normalized = graph.normalize_public_graph_query(row.get('result'), binding, selectors)
    native = normalized['native_result']['confucian_challenger_graph']
    need(native['available'] is True and native['graph_complete'] is True,
         'Unavailable or unknown collection cannot qualify a complete observation')
    collections = [{'faith_full_id': f['requested_faith_full_id'], 'native_count': f['native_count'],
         'complete_native_challenger_title_ids': deepcopy(f['complete_native_challenger_title_ids'])} for f in native['faiths']]
    return {'schema': RESULT_SCHEMA, 'status': 'COMPLETE_NATIVE_COLLECTION_OBSERVED',
         'tool': TOOL, 'step_id': step['id'], 'binding': binding, 'faith_full_ids': selectors,
         'capture_epoch': native['capture_epoch'], 'complete_native_collections': collections,
         'native_graph_sha256_canonical_json': hashlib.sha256(canonical(native)).hexdigest(),
         'retained_graph_json_pointer': '/rows/0/result/native_result/confucian_challenger_graph',
         'sponsor_scope_rule': 'challenger_holder_current_faith',
         'saved_owner_faith_qualification': None, 'saved_collection_serialization_qualification': None,
         'new_title_full_id': None, 'formal_C3_business_credit': None, 'full_product_acceptance_credit': False}


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', type=Path, required=True)
    args = parser.parse_args()
    need(args.request.stat().st_size <= 32768, 'Bounded authored request required')
    raw = args.request.read_bytes()
    request = json.loads(raw.decode('utf-8-sig'))
    need(type(request) is dict and set(request) == {'schema', 'source_binding', 'run_root', 'case_once',
         'snapshot_result', 'query_plan', 'query_result', 'output'} and request['schema'] == REQUEST_SCHEMA,
         'Exact common G4 request required; unknown inputs cannot be guessed')
    root, output = Path(request['run_root']).resolve(), Path(request['output']).resolve()
    need(root.is_absolute() and output.is_absolute() and not output.exists(), 'Actual run and unused output required')
    for name in ('case_once', 'snapshot_result', 'query_plan', 'query_result'):
        need(Path(request[name]['path']).resolve().is_relative_to(root / 'case-output'),
             'Retained common input crossed the declared original run: ' + name)
    source = read_ref(request['source_binding'], 32768)
    graph, private, dto_pins = load_selected_dto(source)
    case = read_ref(request['case_once'], 8 * 1024**2)
    need(case.get('run_id') == root.name and Path(case['runtime_manifest']).resolve() == Path(source['manifest']['path']).resolve(),
         'Original CaseClient run/runtime differs from selected source')
    snapshot_row = one_completed_row(read_ref(request['snapshot_result'], 64 * 1024**2))
    need(snapshot_row.get('plan', {}).get('tool') == 'ck3_take_snapshot', 'Original snapshot result required')
    plan = read_ref(request['query_plan'], 32768)
    result = read_ref(request['query_result'], 64 * 1024**2)
    observation = qualify_observation(snapshot_row['result'], plan, result, graph, private)
    observation.update({'at_utc': datetime.now(timezone.utc).isoformat(), 'source_head': source['source_head'],
         'source_root': source['source_root'], 'run_id': root.name, 'request_sha256': hashlib.sha256(raw).hexdigest(),
         'inputs': {name: request[name] for name in ('source_binding', 'case_once', 'snapshot_result', 'query_plan', 'query_result')},
         'selected_dto_actual_pins': dto_pins, 'SDK_calls': 0, 'SAVE_body_reads': 0,
         'qualification_scope': 'retained_public_G4_native_observation_only'})
    payload = (json.dumps(observation, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    need(len(payload) <= 1024**2, 'Bounded observation summary exceeded 1MiB; retained original graph remains unchanged')
    with output.open('xb') as stream:
        stream.write(payload)
    print(json.dumps({'path': str(output), 'bytes': len(payload), 'sha256': hashlib.sha256(payload).hexdigest(),
         'status': observation['status'], 'formal_C3_business_credit': None}))


if __name__ == '__main__':
    main()
