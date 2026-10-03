"""Verify one immutable fixture manifest against an actual CK3 log.

This is a log-only gate. Persistent character variables, base skills, UI and
save/reload still require their independently retained native/save evidence.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
from decimal import Decimal

SKILLS=('diplomacy','martial','stewardship','intrigue','learning','prowess')


def verify(manifest: Path, log: Path) -> dict:
    source = manifest.read_bytes()
    expected = json.loads(source)
    raw = log.read_bytes()
    content = raw.decode('utf-8', errors='replace')
    observed = re.findall(r'SXAT: (?:PASS|FAIL) [a-z0-9-]+', content)
    counts = Counter(observed)
    required = expected['expected_pass_markers']
    missing = [x for x in required if counts[x] != 1]
    failures = [x for x in observed if x.startswith('SXAT: FAIL ')]
    unexpected = sorted(set(observed) - set(required) - set(failures))
    starts = content.count(expected['required_start'])
    ends = content.count(expected['required_end'])
    ok = not missing and not failures and not unexpected and starts == ends == 1
    return {
        'schema': 'sxad.fixture-log-gate.v1',
        'ok': ok,
        'scope': 'log-markers-only; does not prove native base skills, UI, persistence or clean media',
        'fixture_manifest_sha256': hashlib.sha256(source).hexdigest(),
        'log_sha256': hashlib.sha256(raw).hexdigest(),
        'expected_case_count': len(required),
        'pass_count': sum(counts[x] == 1 for x in required),
        'missing_or_duplicate': missing,
        'failures': failures,
        'unexpected_markers': unexpected,
        'start_count': starts,
        'end_count': ends,
    }


def verify_save(manifest: Path, readback: Path) -> dict:
    """Compare independent real-save arrays and modifier records to the fixture."""
    fixture=json.loads(manifest.read_text(encoding='utf-8'))
    saved=json.loads(readback.read_text(encoding='utf-8'))
    errors=[];cases=[]
    if saved.get('fixture_manifest_sha256')!=hashlib.sha256(manifest.read_bytes()).hexdigest():
        errors.append('save decoder is not bound to this exact fixture manifest')
    for contract in fixture['base_skill_contract']:
        name=contract['case'];flag=name.replace('-','_');actors={};case_errors=[]
        for role in ('receiver','donor'):
            reference=contract.get(f'{role}_root_reference')
            if reference:
                identity=(saved.get('root_references') or {}).get(reference)
                matches=[c for c in saved['characters'] if c['character_id']==identity]
            else:
                matches=[c for c in saved['characters'] if f'sxat_{role}_{flag}' in c['role_flags']]
            if len(matches)!=1:
                case_errors.append(f'{role}: expected one exact role flag, found {len(matches)}');continue
            actor=matches[0];actors[role]=actor
            if contract.get(f'{role}_dead') and actor.get('alive') is not False:
                case_errors.append(f'{role}: saved character is not independently confirmed dead')
            expected=contract[f'{role}_before']
            observed=(actor.get('base_skill_save_field') or {}).get('array')
            if observed!=expected:case_errors.append(f'{role}: base array {observed} != {expected}')
            balance=[]
            for skill in SKILLS:
                variable=actor['variables'].get(f'sxad_{skill}_balance')
                value=variable.get('integer_exact') if variable else 0
                if not isinstance(value,int):
                    case_errors.append(f'{role}/{skill}: invalid balance variable');value=0
                balance.append(value)
                gain=[m for m in actor['modifiers'] if m['key']==f'sxad_{skill}_gain_modifier']
                loss=[m for m in actor['modifiers'] if m['key']==f'sxad_{skill}_loss_modifier']
                selected=gain if value>0 else loss
                opposite=loss if value>0 else gain
                if value==0:
                    if gain or loss:case_errors.append(f'{role}/{skill}: zero balance still has modifier')
                elif len(selected)!=1 or opposite:
                    case_errors.append(f'{role}/{skill}: modifier sign/count differs from balance {value}')
                elif Decimal(selected[0]['scale_decimal'])!=abs(value):
                    case_errors.append(f'{role}/{skill}: raw saved scale {selected[0]["scale_raw"]} != {abs(value)}')
            actor['verified_balance_array']=balance
        ledger=contract['ledger_expected']
        if len(actors)==2:
            receiver=actors['receiver']['verified_balance_array'];donor=actors['donor']['verified_balance_array']
            if ledger['kind']=='exact':
                if receiver!=ledger['receiver'] or donor!=ledger['donor']:
                    case_errors.append(f'ledger arrays {receiver}/{donor} != expected {ledger["receiver"]}/{ledger["donor"]}')
            else:
                amount=ledger['amount'];direction=ledger['direction']
                if any(x!=-y for x,y in zip(receiver,donor)) or sum(receiver)!=amount*direction or any(x*direction<0 for x in receiver):
                    case_errors.append(f'random ledger is not a paired {amount} point transfer: {receiver}/{donor}')
        cases.append({'case':name,'ok':not case_errors,'errors':case_errors,'character_ids':{role:actor['character_id'] for role,actor in actors.items()}})
    errors.extend(f'{c["case"]}: {error}' for c in cases for error in c['errors'])
    return {'schema':'sxad.fixture-save-gate.v1','ok':not errors,'scope':'actual saved base arrays, ledger conservation and raw modifier scales; excludes UI/reload/media','readback_sha256':hashlib.sha256(readback.read_bytes()).hexdigest(),'melted_sha256':saved['melted_sha256'],'fixture_manifest_sha256':hashlib.sha256(manifest.read_bytes()).hexdigest(),'cases':cases,'errors':errors}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixture-manifest', required=True, type=Path)
    parser.add_argument('--log', required=True, type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--save-readback',type=Path)
    args = parser.parse_args()
    result = verify(args.fixture_manifest, args.log)
    if args.save_readback:
        result['independent_save_gate']=verify_save(args.fixture_manifest,args.save_readback)
        result['ok']=result['ok'] and result['independent_save_gate']['ok']
    text = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        with args.output.open('x', encoding='utf-8') as stream:
            stream.write(text)
    print(text, end='')
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
