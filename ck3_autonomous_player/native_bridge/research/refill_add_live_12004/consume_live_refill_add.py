"""Consume source-bound instruction evidence; legacy full-manager path stays strict."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import stat
import sys

sys.dont_write_bytecode = True
source_root = Path(__file__).resolve().parents[3] / 'src'
contract_path = source_root / 'xar_autoplayer/bridge/army_instruction_local_refill_add_12004.py'
spec = importlib.util.spec_from_file_location('exact_refill_add_contract_12004', contract_path)
if spec is None or spec.loader is None:
    raise RuntimeError('exact colocated refill ADD contract missing')
contract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contract)
normalize_instruction_local_refill_add_12004 = contract.normalize_instruction_local_refill_add_12004


def read_full_parent_range(meta):
    """Read only the exact response line already pinned by the original full query."""
    path = Path(meta['path'])
    expected = meta['file_identity']
    span = meta['response_line']
    begin, end = span['begin'], span['end']
    if (type(begin) is not int or type(end) is not int or begin < 0
            or not 0 < end - begin <= 32 * 1024 * 1024
            or type(expected) is not list or len(expected) != 2
            or any(type(x) is not int for x in expected) or path.is_symlink()):
        raise ValueError('bounded pinned original native response range required')
    with path.open('rb') as stream:
        before = os.fstat(stream.fileno())
        if (not stat.S_ISREG(before.st_mode) or [before.st_dev, before.st_ino] != expected
                or before.st_size < end):
            raise ValueError('original response file identity or extent differs')
        stream.seek(begin)
        response = stream.read(end - begin)
        after = os.fstat(stream.fileno())
    if ([after.st_dev, after.st_ino] != expected or after.st_size < end or len(response) != end - begin):
        raise ValueError('original response replaced or truncated during read')
    return response


def bounded_json(path, maximum, parser):
    if not 0 < path.stat().st_size <= maximum:
        parser.error('bounded JSON input required: ' + str(path))
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=contract._unique_json_object)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--raw', type=Path, required=True)
    parser.add_argument('--binding', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--core-observation', type=Path,
                        help='one original complete-manager CoreEvent, maximum4MiB; legacy v4 only')
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--target-core-proof', type=Path,
                        help='explicit selected-target proof, maximum64KiB; needs original parent range')
    target.add_argument('--create-target-core-proof', type=Path,
                        help='save a new derived selected-target proof from original parent RAM')
    parser.add_argument('--full-parent-proof', type=Path,
                        help='existing full-wire-proof with exact response path/identity/range/SHA, maximum16KiB')
    args = parser.parse_args(argv)
    if args.raw.stat().st_size > 131072 or args.binding.stat().st_size > 16384:
        parser.error('bounded native raw and owner binding required')
    scoped = args.target_core_proof is not None or args.create_target_core_proof is not None
    if (scoped and (args.core_observation is not None or args.full_parent_proof is None)
            or not scoped and args.full_parent_proof is not None):
        parser.error('target proof needs its original parent proof and cannot mix legacy CoreEvent')
    raw = args.raw.read_bytes()
    binding = json.loads(args.binding.read_text(encoding='utf-8'), object_pairs_hook=contract._unique_json_object)
    if scoped:
        sys.path.insert(0, str(source_root))
        from xar_autoplayer.bridge.army_target_instruction_core_proof_12004 import (
            build_target_instruction_core_proof_12004,
            normalize_target_instruction_core_proof_12004,
        )
        parent_proof = bounded_json(args.full_parent_proof, 16384, parser)
        parent = read_full_parent_range(parent_proof)
        if args.create_target_core_proof is not None:
            proof = build_target_instruction_core_proof_12004(
                parent_response=parent, parent_proof=parent_proof, binding=binding, raw=raw)
            encoded = (json.dumps(proof, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
            if len(encoded) > 65536:
                parser.error('derived target proof exceeds64KiB')
            with args.create_target_core_proof.open('xb') as stream:
                stream.write(encoded)
        else:
            proof = bounded_json(args.target_core_proof, 65536, parser)
        item = normalize_target_instruction_core_proof_12004(
            raw, binding, target_core_proof=proof, parent_response=parent, parent_proof=parent_proof)
    else:
        # This remains the original complete-manager4MiB contract.
        core = None
        if args.core_observation is not None:
            if not 0 < args.core_observation.stat().st_size <= 4 * 1024 * 1024:
                parser.error('bounded actual CoreEvent JSON record required (maximum 4 MiB)')
            core = json.loads(args.core_observation.read_text(encoding='utf-8'),
                              object_pairs_hook=contract._unique_json_object)
        item = normalize_instruction_local_refill_add_12004(raw, binding, core_observation=core)
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(item, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'output': str(args.output), 'raw_sha256': item['raw_sha256'],
        'instruction_pair_ready': True,
        'same_core_invocation_join_ready': item.get('same_core_invocation_join_ready', False),
        'natural_attribution_ready': item['natural_attribution_ready'], 'full_R06_qualified': False}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
