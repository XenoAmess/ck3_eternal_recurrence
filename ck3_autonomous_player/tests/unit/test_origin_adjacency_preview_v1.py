"""Four new behaviors through the existing production preview Driver/contract.

Only the transport endpoint is authored. No native fixture or game is executed.
"""
from __future__ import annotations
from copy import deepcopy
from datetime import datetime, timezone
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def require(value, message):
    if not value:
        raise AssertionError(message)


def leaf(count=3):
    ids = [2645, 2634, 2645] if count == 3 else [2700 + i for i in range(min(count, 64))]
    return {"schema_version": 1, "source": "native_origin_province_map_node_rows_12004",
            "input_basis": "preview_origin_province_native_adjacency_rows",
            "status": "truncated" if count > 64 else "available",
            "unavailable_reason": "origin_adjacency_row_budget_exhausted" if count > 64 else None,
            "source_province_id": 2635, "source_province_identity": "native:3000",
            "source_map_node_identity": "native:4000", "adjacency_data_identity": "native:5000" if count else None,
            "native_count": count, "published_row_limit": 64, "observed_count": min(count, 64),
            "collection_complete": count <= 64, "truncated": count > 64,
            "identity_before_after_match": True,
            "rows": [{"occurrence_index": i, "target_province_id": p} for i, p in enumerate(ids)],
            "native_condition_evaluated_for_rows": False, "route_legality_evaluated_for_rows": False}


def run(source, candidate):
    sys.path.insert(0, str(source / 'ck3_autonomous_player/src'))
    import xar_autoplayer.bridge
    bridge = candidate / 'ck3_autonomous_player/src/xar_autoplayer/bridge'
    load('xar_autoplayer.bridge.army_origin_adjacency_contract', bridge / 'army_origin_adjacency_contract.py')
    helper = load('_existing_county_preview_test', source / 'ck3_autonomous_player/tests/unit/test_county_entry_preview_condition_v1.py')
    Driver, contract, driver_sha = helper.load_candidate(source, candidate)
    def query(value):
        county = helper.child()
        county['origin_adjacency_v1'] = value
        return helper.query(Driver, county)['route_preview']['county_entry_condition_v1']
    def rejected(value, part):
        try:
            query(value)
        except Exception as error:
            require(type(error).__name__ == 'BridgeUnavailableError' and part in str(error), str(error))
        else:
            raise AssertionError('production Driver accepted contradictory origin adjacency')
    checks = []
    actual = query(leaf())
    require(actual['native_condition_passes'] is False, 'graph rows must not turn native false into true')
    require([r['target_province_id'] for r in actual['origin_adjacency_v1']['rows']] == [2645, 2634, 2645],
            'raw order and duplicate occurrences survive production Driver')
    require(not actual['origin_adjacency_v1']['route_legality_evaluated_for_rows'], 'no Move eligibility')
    checks.append('complete adjacency preserves raw order and duplicate occurrences independently of county false')
    truncated = query(leaf(65))['origin_adjacency_v1']
    require(truncated['status'] == 'truncated' and len(truncated['rows']) == 64
            and not truncated['collection_complete'], '65 source rows remain bounded/unknown tail')
    malformed = leaf(65); malformed['collection_complete'] = True
    rejected(malformed, 'completeness')
    checks.append('64/65 prefix stays truncated; real Driver rejects forged complete collection')
    empty = query(leaf(0))['origin_adjacency_v1']
    require(empty['rows'] == [] and empty['native_count'] == 0, 'observed empty is complete')
    failed = leaf(0)
    failed.update(status='unavailable', unavailable_reason='origin_adjacency_count_read_failed',
                  native_count=None, rows=None, collection_complete=False, identity_before_after_match=False)
    failed_result = query(failed)
    require(failed_result['status'] == 'available' and failed_result['origin_adjacency_v1']['native_count'] is None,
            'independent failed graph read preserves actual county result and unknown count')
    checks.append('observed zero and failed unknown stay distinct without erasing native county false')
    wrong = leaf(); wrong['source_province_id'] = 2644
    rejected(wrong, 'origin')
    stale = leaf(); stale['identity_before_after_match'] = False
    rejected(stale, 'stable identities')
    legacy = helper.query(Driver, helper.child())['route_preview']['county_entry_condition_v1']
    require('origin_adjacency_v1' not in legacy, 'old exact4 leaf absence remains absence')
    checks.append('production Driver rejects wrong-origin or unstable rows; old child absence is retained')
    return {'status': 'GREEN', 'new_focused_cases': 4, 'checks': checks,
            'candidate_driver_text_sha256_without_bom': driver_sha,
            'boundary': 'Authored endpoint through existing production Driver/strictconsumer; native collector/serializer fixture not executed, no live observation.',
            'game_sdk_calls': 0, 'native_builds': 0, 'native_executions': 0}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--candidate-root', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    args = parser.parse_args()
    if args.receipt.exists():
        raise SystemExit('exclusive receipt already exists')
    try:
        result, code = run(args.source_root, args.candidate_root), 0
    except Exception as error:
        import traceback
        result, code = {'status': 'RED', 'error': str(error), 'traceback': traceback.format_exc()}, 1
    result.update(machine_id='desktop-3fevhd2-1c74096080', at_utc=datetime.now(timezone.utc).isoformat(), run_exit=code,
                  test_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    args.receipt.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
