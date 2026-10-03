"""Decode an independently melted checkpoint without changing the live game.

The SDK supplies the tested CK3 record reader. Signed fixed-point variables are
decoded as integers; floating point helper output is never used for assertions.
"""
from __future__ import annotations

import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import sys


def inspect(run: Path, save_dir: Path, sdk: Path, player_id: int) -> dict:
    sys.path.insert(0, str(sdk / 'tools'))
    from inspect_ck3_save_player_topology import _numeric_records
    from inspect_ck3_save_character_scope import _anonymous_records, _variable_record

    melted = save_dir / 'melted.ck3'
    manifest_path = run / 'fixture.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))

    def variables(block: str) -> dict:
        result = {}
        for record in _anonymous_records(block):
            parsed = _variable_record(record)
            if not parsed or not parsed[0].startswith(('sxat_', 'sxad_')):
                continue
            value = parsed[1]
            if value.get('type') == 'value':
                identity = value.get('identity') or 0
                signed = identity - (1 << 64) if identity >= (1 << 63) else identity
                value['signed_identity'] = signed
                value['integer_exact'] = signed // 100000
                value['signed_number_decimal'] = str(Decimal(signed) / Decimal(100000))
            result[parsed[0]] = value
        return result

    root_variables = {}
    for level, cid, block in _numeric_records(melted):
        if level == 1 and cid == player_id:
            root_variables = variables(block)
            break
    references = {}
    for contract in manifest['base_skill_contract']:
        for role in ('receiver', 'donor'):
            name = contract.get(f'{role}_root_reference')
            if name:
                value = root_variables.get(name, {})
                if value.get('type') == 'char' and isinstance(value.get('character_id'), int):
                    references[name] = value['character_id']
    characters = []
    for level, cid, block in _numeric_records(melted):
        if level != 1 or ('sxat_' not in block and cid not in references.values()):
            continue
        match = re.search(r'(?m)^\s*(skills?|base_skills?)=\{([^}]+)\}', block)
        base = {'field': match.group(1), 'array': [int(x) for x in re.findall(r'-?\d+', match.group(2))]} if match else None
        modifiers = []
        for item in re.finditer(r'(?m)^\s*modifier=\{([^{}]*)\}', block):
            raw = item.group(1)
            key = re.search(r'modifier="([^"]+)"', raw)
            if not key:
                continue
            scale = re.search(r'\b(scale|multiplier)=(-?\d+(?:\.\d+)?)\b', raw)
            modifiers.append({'key': key.group(1), 'scale_raw': scale.group(2) if scale else None,
                              'scale_source_key': scale.group(1) if scale else None,
                              'scale_default': 1 if scale is None else None,
                              'scale_decimal': str(Decimal(scale.group(2))) if scale else '1',
                              'raw_record': item.group(0)})
        row = {'character_id': cid, 'alive': '\n\t\talive_data={' in block,
               'role_flags': re.findall(r'flag="(sxat_(?:receiver|donor)_[^"]+)"', block),
               'root_reference_names': [name for name, identity in references.items() if identity == cid],
               'base_skill_save_field': base, 'variables': variables(block), 'modifiers': modifiers,
               'raw_character_sha256': hashlib.sha256(block.encode('utf-8')).hexdigest()}
        characters.append(row)
        with (save_dir / f'character-{cid}.txt').open('x', encoding='utf-8') as stream:
            stream.write(block)
    root = next((row for row in characters if row['character_id'] == player_id), None)
    names = ['sxat_case_' + marker.removeprefix('SXAT: PASS ').replace('-', '_') for marker in manifest['expected_pass_markers']]
    results = {name: root['variables'].get(name) if root else None for name in names}
    return {'schema': 'sxad.real-save-fixture-readback.v4', 'run_id': run.name,
            'melted_sha256': hashlib.sha256(melted.read_bytes()).hexdigest(),
            'decoder_script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'helper_sources': {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in
                               (sdk / 'tools/inspect_ck3_save_player_topology.py', sdk / 'tools/inspect_ck3_save_character_scope.py')},
            'fixture_manifest_sha256': hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
            'root_character': root, 'root_references': references, 'case_results': results,
            'characters': characters,
            'pass_count': sum(value is not None and value.get('integer_exact') == 1 for value in results.values()),
            'fail_count': sum(value is not None and value.get('integer_exact') == 0 for value in results.values()),
            'missing_count': sum(value is None for value in results.values())}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True, type=Path)
    parser.add_argument('--save-dir', required=True, type=Path)
    parser.add_argument('--sdk', required=True, type=Path)
    parser.add_argument('--player-id', required=True, type=int)
    parser.add_argument('--output-name', default='fixture-readback-v4.json')
    args = parser.parse_args()
    destination = args.save_dir / args.output_name
    if destination.exists() or any(args.save_dir.glob('character-*.txt')):
        parser.error('new readback output required; retain earlier files')
    result = inspect(args.run, args.save_dir, args.sdk, args.player_id)
    with destination.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'counts': [result['pass_count'], result['fail_count'], result['missing_count']],
                      'actors': len(result['characters']), 'root_references': result['root_references'],
                      'readback_sha256': hashlib.sha256(destination.read_bytes()).hexdigest()}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
