"""Consume actual native wire after Root's independent build/SYSTEM/runtime gate."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
contract_path = Path(__file__).resolve().parents[3] / 'src/xar_autoplayer/bridge/army_instruction_local_refill_add_12004.py'
spec = importlib.util.spec_from_file_location('exact_refill_add_contract_12004', contract_path)
if spec is None or spec.loader is None:
    raise RuntimeError('exact colocated refill ADD contract missing')
contract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contract)
normalize_instruction_local_refill_add_12004 = contract.normalize_instruction_local_refill_add_12004

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--raw', type=Path, required=True)
    p.add_argument('--binding', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--core-observation', type=Path,
                   help='one actual serialized CoreEvent record; required for native v4')
    a = p.parse_args()
    if a.raw.stat().st_size > 131072 or a.binding.stat().st_size > 16384:
        p.error('bounded native raw and owner binding required')
    core = None
    if a.core_observation is not None:
        if not 0 < a.core_observation.stat().st_size <= 4 * 1024 * 1024:
            p.error('bounded actual CoreEvent JSON record required (maximum 4 MiB)')
        core = json.loads(a.core_observation.read_text(encoding='utf-8'),
                          object_pairs_hook=contract._unique_json_object)
    item = normalize_instruction_local_refill_add_12004(
        a.raw.read_bytes(), json.loads(a.binding.read_text(encoding='utf-8'),
                                     object_pairs_hook=contract._unique_json_object),
        core_observation=core)
    with a.output.open('x', encoding='utf-8') as f:
        json.dump(item, f, indent=2); f.write('\n')
    print(json.dumps({'output':str(a.output),'raw_sha256':item['raw_sha256'],
                      'instruction_pair_ready':True,
                      'same_core_invocation_join_ready':item.get('same_core_invocation_join_ready', False),
                      'natural_attribution_ready':item['natural_attribution_ready'],
                      'full_R06_qualified':False}))
