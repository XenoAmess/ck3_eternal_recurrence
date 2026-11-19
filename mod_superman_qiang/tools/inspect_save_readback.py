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
from typing import TYPE_CHECKING, Literal, NotRequired, TypedDict

if TYPE_CHECKING:
    from inspect_ck3_save_player_topology import SaveInputIdentity


class VariableReadback(TypedDict):
    present: bool
    type: str | None
    identity: int | None
    number: NotRequired[float]
    character_id: NotRequired[int | None]
    signed_identity: NotRequired[int]
    integer_exact: NotRequired[int | None]
    signed_number_decimal: NotRequired[str]


class BaseSkillReadback(TypedDict):
    field: str
    array: list[int]


class ModifierReadback(TypedDict):
    key: str
    scale_raw: str | None
    scale_source_key: str | None
    scale_default: int | None
    scale_decimal: str
    raw_record: str


class CharacterReadback(TypedDict):
    character_id: int
    alive: bool
    save_record_level: int
    role_flags: list[str]
    root_reference_names: list[str]
    base_skill_save_field: BaseSkillReadback | None
    variables: dict[str, VariableReadback]
    modifiers: list[ModifierReadback]
    raw_character_sha256: str


class SavedReadback(TypedDict):
    schema: Literal['sxad.real-save-fixture-readback.v6']
    run_id: str
    melted_sha256: str
    save_input: SaveInputIdentity
    decoder_script_sha256: str
    helper_sources: dict[str, str]
    fixture_manifest_sha256: str
    root_character: CharacterReadback | None
    root_references: dict[str, int]
    case_results: dict[str, VariableReadback | None]
    characters: list[CharacterReadback]
    pass_count: int
    fail_count: int
    missing_count: int


def inspect(run: Path, save_dir: Path | None, sdk: Path, player_id: int, output_dir: Path,
            *, native_save: Path | None = None) -> SavedReadback:
    sys.path.insert(0, str(sdk / 'tools'))
    from inspect_ck3_save_player_topology import _numeric_records, _save_input_identity, _sha256
    from inspect_ck3_save_character_scope import _anonymous_records, _variable_record

    if (save_dir is None) == (native_save is None):
        raise ValueError('exactly one plaintext save directory or native save is required')
    if native_save is not None:
        melted = native_save
    else:
        assert save_dir is not None
        melted = save_dir / 'melted.ck3'
    native_zip = native_save is not None
    identity = _save_input_identity(melted, native_zip=native_zip)
    manifest_path = run / 'fixture.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))

    def variables(block: str) -> dict[str, VariableReadback]:
        result: dict[str, VariableReadback] = {}
        for record in _anonymous_records(block):
            parsed = _variable_record(record)
            if not parsed or not parsed[0].startswith(('sxat_', 'sxad_')):
                continue
            raw_value = parsed[1]
            kind, raw_identity = raw_value.get('type'), raw_value.get('identity')
            if kind is not None and not isinstance(kind, str):
                raise ValueError('saved variable type must be a string or null')
            if raw_identity is not None and (not isinstance(raw_identity, int) or isinstance(raw_identity, bool)):
                raise ValueError('saved variable identity must be an exact integer or null')
            value: VariableReadback = {'present': True, 'type': kind, 'identity': raw_identity}
            if kind == 'value':
                number = raw_value.get('number')
                if not isinstance(number, float):
                    raise ValueError('retained numeric variable projection is missing')
                value['number'] = number
                # Retain the existing derived-zero semantics without rewriting
                # raw identity=null or manufacturing a missing variable.
                identity = raw_identity if raw_identity is not None else 0
                signed = identity - (1 << 64) if identity >= (1 << 63) else identity
                value['signed_identity'] = signed
                value['integer_exact'] = signed // 100000 if signed % 100000 == 0 else None
                value['signed_number_decimal'] = str(Decimal(signed) / Decimal(100000))
            elif kind == 'char':
                value['character_id'] = raw_identity
            result[parsed[0]] = value
        return result

    root_variables = {}
    for level, cid, block in _numeric_records(melted, native_zip=native_zip):
        if level == 1 and cid == player_id:
            root_variables = variables(block)
            break
    references: dict[str, int] = {}
    for contract in manifest['base_skill_contract']:
        for role in ('receiver', 'donor'):
            name = contract.get(f'{role}_root_reference')
            if name:
                value = root_variables.get(name)
                character_id = value.get('character_id') if value is not None else None
                if value is not None and value['type'] == 'char' and isinstance(character_id, int):
                    references[name] = character_id
    characters: list[CharacterReadback] = []
    for level, cid, block in _numeric_records(melted, native_zip=native_zip):
        # Living characters are level 1; dead characters are stored under a
        # nested dead-character section at level 2. Select those only through
        # the independently saved typed root reference and character fields.
        dead_reference = level == 2 and cid in references.values() and 'first_name=' in block and 'dead_data={' in block
        if (level != 1 and not dead_reference) or ('sxat_' not in block and cid not in references.values()):
            continue
        match = re.search(r'(?m)^\s*(skills?|base_skills?)=\{([^}]+)\}', block)
        base: BaseSkillReadback | None = {'field': match.group(1), 'array': [int(x) for x in re.findall(r'-?\d+', match.group(2))]} if match else None
        modifiers: list[ModifierReadback] = []
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
        row: CharacterReadback = {'character_id': cid, 'alive': bool(re.search(r'(?m)^\s*alive_data=\{', block)),
               'save_record_level': level,
               'role_flags': re.findall(r'flag="(sxat_(?:receiver|donor)_[^"]+)"', block),
               'root_reference_names': [name for name, identity in references.items() if identity == cid],
               'base_skill_save_field': base, 'variables': variables(block), 'modifiers': modifiers,
               'raw_character_sha256': hashlib.sha256(block.encode('utf-8')).hexdigest()}
        characters.append(row)
        with (output_dir / f'character-{cid}.txt').open('x', encoding='utf-8') as stream:
            stream.write(block)
    root = next((row for row in characters if row['character_id'] == player_id), None)
    names = ['sxat_case_' + marker.removeprefix('SXAT: PASS ').replace('-', '_') for marker in manifest['expected_pass_markers']]
    results = {name: root['variables'].get(name) if root else None for name in names}
    if _sha256(melted).lower() != identity['sha256']:
        raise ValueError('save source changed while being inspected')
    return {'schema': 'sxad.real-save-fixture-readback.v6', 'run_id': run.name,
            'melted_sha256': identity['content_sha256'], 'save_input': identity,
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
    parser.add_argument('--output-name', default='fixture-readback-v6.json')
    parser.add_argument('--output-dir', type=Path, help='New directory for another decoder attempt against the same immutable save')
    args = parser.parse_args()
    output_dir = args.output_dir or args.save_dir
    if args.output_dir:
        args.output_dir.mkdir(exist_ok=False)
    destination = output_dir / args.output_name
    if destination.exists() or any(output_dir.glob('character-*.txt')):
        parser.error('new readback output required; retain earlier files')
    result = inspect(args.run, args.save_dir, args.sdk, args.player_id, output_dir)
    with destination.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'counts': [result['pass_count'], result['fail_count'], result['missing_count']],
                      'actors': len(result['characters']), 'root_references': result['root_references'],
                      'readback_sha256': hashlib.sha256(destination.read_bytes()).hexdigest()}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
