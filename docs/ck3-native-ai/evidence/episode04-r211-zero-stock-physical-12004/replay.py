"""Offline replay of one preserved R211 target day; no game/SDK/process actions."""
from pathlib import Path
import argparse
from datetime import datetime, timezone
import hashlib
import json
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--repo', type=Path, required=True)
parser.add_argument('--evidence', type=Path, required=True)
parser.add_argument('--consumer-pins', type=Path, required=True)
parser.add_argument('--machine-id', required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
if args.output.exists():
    raise RuntimeError('refuse to overwrite a replay receipt')
raw = args.evidence.read_bytes()
if hashlib.sha256(raw).hexdigest() != '69bfd6991396120dedb63ffe26442dfd2334184820901da890ed19d23d611d66':
    raise RuntimeError('preserved R211 evidence exact SHA mismatch')
for pin in json.loads(args.consumer_pins.read_bytes())['files']:
    data = (args.repo / pin['repository_path']).read_bytes()
    if len(data) != pin['bytes'] or hashlib.sha256(data).hexdigest() != pin['sha256']:
        raise RuntimeError('reviewed production consumer source mismatch: ' + pin['repository_path'])
sys.path.insert(0, str(args.repo / 'ck3_autonomous_player/src'))
from xar_autoplayer.bridge.army_zero_stock_clock_12004 import select_actual_zero_stock_supply_preferred_12004
from xar_autoplayer.bridge.army_actual_supply_parent_join_summary import join_actual_supply_parent_writer_observations_v1
from xar_autoplayer.bridge.army_periodic_loss_component_12004 import classify_actual_loss_component_12004

q = json.loads(raw)
a = q['army0']
kwargs = q['actual_fences']
joined = join_actual_supply_parent_writer_observations_v1(a, **kwargs)
zero = select_actual_zero_stock_supply_preferred_12004(a, **kwargs)
if joined != q['production_parent_join'] or zero != q['production_zero_stock_selector']:
    raise RuntimeError('production replay differs from retained actual result')
by_sequence = {x['writer_sequence']: x for x in joined['events']}
groups = {}
for w in a['actual_loss_writer_observations_v1']['events']:
    kind = classify_actual_loss_component_12004(w)
    key = kind['component'] + '/' + kind['phase']
    debit = by_sequence[w['sequence']]['physical_debit_soldiers']
    if type(debit) is not int:
        raise RuntimeError('physical debit coverage incomplete')
    row = groups.setdefault(key, {'writers': 0, 'positive_writers': 0, 'physical_debit': 0})
    row['writers'] += 1
    row['positive_writers'] += debit > 0
    row['physical_debit'] += debit
if not zero['positive_physical_debit_observed'] or zero['selected_invocation_debit_sum'] != 337:
    raise RuntimeError('R211 exact-zero supply preferred witness absent')
result = {'schema': 'xar.e04.r211-zero-stock-physical-replay.v1',
    'machine_id': args.machine_id, 'source_machine_id': q['machine_id'],
    'observed_at_utc': datetime.now(timezone.utc).isoformat(),
    'status': 'PASS_PRESERVED_PRODUCTION_ZERO_STOCK_PHYSICAL_WITNESS',
    'evidence_sha256': hashlib.sha256(raw).hexdigest(), 'components': groups,
    'source_run_id': q['query_frame']['queried_episode_run_id'],
    'source_date_raw': q['query_frame']['queried_date_raw'],
    'joined_writer_count': joined['joined_writer_count'],
    'unknown_reasons': joined['unknown_reasons'],
    'initialized_low_stock_case': True, 'natural_depletion_claimed': False,
    'complete16day_total_claimed': False, 'SDK_used': False,
    'new_game_or_deployment_qualification_granted': False}
args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, indent=2))
