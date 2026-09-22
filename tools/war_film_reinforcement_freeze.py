"""Freeze this bounded offline research package against the exact local CK3 EXE.

Exclusive-create only. Static interpretations below are analyst declarations;
hashes and disassembly bind those declarations to bytes, not to a live result.
"""
import argparse
import hashlib
import json
from pathlib import Path

from war_film_reinforcement_static import EXPECTED_SHA256, default_exe

BLOCKS = [
    ('asking-singleton', 0x1848326, 0x3A, 'parent+0x4C <= 1 jumps to clear path 0x18484F8; otherwise call asking producer 0x1872BF0'),
    ('asking-clear', 0x18484F8, 0x60, 'clear asking/assigned in each subunit for singleton or disabled coordinator'),
    ('same-stack-write', 0x1848471, 0x43, 'exclude requester, busy or asking helpers; write bit1 and valid requester current Province pointer'),
    ('cross-stack-gate', 0x1848797, 0x158, 'same-coordinator bit0/+0x28 vs other-coordinator +0x34/+0x38; CMP required,available at 0x18488A2 then JGE 0x18488EA returns requester: required >= available ACCEPTS, including equality. This corrects the inverse inequality in the historical topic.'),
    ('wanted-registration', 0x18B01F0, 0x1D, 'PLAYER_SUPPORT_WANTED_COMBAT_RATIO registration binds qword slot 0x570DEC0'),
    ('distance-registration', 0x18B0360, 0x1D, 'PLAYER_SUPPORT_ATTACK_TARGET_MAX_DISTANCE binds dword slot 0x570DEBC'),
    ('delay-registration', 0x18B06A0, 0x1D, 'PLAYER_SUPPORT_ATTACK_MAX_ARRIVAL_DELAY binds dword slot 0x570DF28'),
    ('supply-registration', 0x18B09E0, 0x1D, 'PLAYER_SUPPORT_IGNORE_BAD_SUPPLY_WITHIN_STEPS binds dword slot 0x570DFD4'),
    ('enemy-registration', 0x18B0D20, 0x1D, 'PLAYER_SUPPORT_ENEMY_POWER_MULTIPLIER binds qword slot 0x570DEC8'),
    ('siege-registration', 0x18B0E90, 0x1D, 'PLAYER_SUPPORT_MIN_SIEGE_STRENGTH binds qword slot 0x570DED0'),
    ('wanted-consumer', 0x184FDE5, 0x10A, '0x184FE37 loads ratio; +0x48=max(0,fixed_mul(+0x38,ratio)-+0x18); +0x60 is demand>0'),
    ('distance-consumer', 0x184F819, 0x7B, 'compare coordinate distance squared against define squared; JA rejects strictly greater; accepted destination passed to 0x184F9E0 with record+0x58'),
    ('delay-consumer', 0x1857CDB, 0x174, '0x1857E35 adds define*100000 to existing time bound; JLE accepts equality and appends candidate; record time operands +0xE0/+0xE8 need semantic attribution'),
    ('supply-consumer', 0x18722EF, 0x63, 'if target unchanged, parent target valid and +0x79 not 2/3, route_count<=define exits dispatcher; otherwise enters path-supply decision'),
    ('power-siege-consumer', 0x185030C, 0x204, '0x1850375 scales computed deficit by enemy multiplier into record+0x1E0; 0x185041C applies min siege strength to coordinator+0x7C and contributes +0x1F4/+0x1F8'),
    ('support-step-cache', 0x18505A7, 0xC1, 'per-province record+4 is lowered/set to 1/2/3 from three stored Province vectors'),
    ('support-step-score', 0x1869947, 0x7A, 'record+4 ==1/2/3 loads slot 0x570DFA0/0x570DF9C/0x570DF98 and adds score through 0x1869BF0'),
]


def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as out:
        out.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe', type=Path)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    import pefile
    from capstone import Cs, CS_ARCH_X86, CS_MODE_64
    exe = args.exe or default_exe()
    raw = exe.read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXPECTED_SHA256:
        raise ValueError('wrong CK3 executable')
    pe = pefile.PE(data=raw, fast_load=True)
    dis = Cs(CS_ARCH_X86, CS_MODE_64)
    blocks = []
    for name, rva, size, claim in BLOCKS:
        off = pe.get_offset_from_rva(rva)
        code = raw[off:off+size]
        rows = [{'rva': hex(i.address-pe.OPTIONAL_HEADER.ImageBase), 'bytes': i.bytes.hex(), 'mnemonic': i.mnemonic, 'operands': i.op_str} for i in dis.disasm(code, pe.OPTIONAL_HEADER.ImageBase+rva)]
        if sum(len(bytes.fromhex(row['bytes'])) for row in rows) != size:
            raise ValueError(f'{name}: bounded extraction cuts an instruction or contains undecodable bytes')
        blocks.append(dict(id=name, rva=hex(rva), size=size, sha256=hashlib.sha256(code).hexdigest(), analyst_interpretation=claim, instructions=rows))
    defines_path = exe.parent.parent / 'game/common/defines/ai/00_ai.txt'
    defines_raw = defines_path.read_bytes()
    values = [line.strip() for line in defines_raw.decode('utf-8-sig').splitlines() if 'PLAYER_SUPPORT_' in line or 'TARGET_SCORE_SUPPORT_PLAYER_' in line]
    contract = {
        'schema': 'xar.war-film-reinforcement-static-contract.v1',
        'version': '1.19.0.6', 'exe_sha256': EXPECTED_SHA256, 'exe_size': len(raw),
        'evidence_boundary': 'Offline exact-build analyst interpretation; no CK3 process, runtime sampling, assignment or rejoin performed.',
        'defines_sha256': hashlib.sha256(defines_raw).hexdigest(), 'defines_lines': values,
        'blocks': blocks,
        'open_questions': ['PLAYER_SUPPORT record consumers do not establish an alias to CAISubunitStack +0x34/+0x38; producer of those cross-coordinator fields remains unresolved.', 'The three-unit source save still must be materialized and pass native membership preflight after withdrawal.', 'Target candidate competition, exact eligible-power inputs and producer execution timing remain unobserved in this package.'],
    }
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    contract_path = out / 'war_film_reinforcement_static_contract_20260923.json'
    plan_path = out / 'war_film_reinforcement_plan_20260923.json'
    if contract_path.exists() or plan_path.exists():
        raise FileExistsError('new output directory required; existing research records are immutable')
    write(contract_path, contract)
    nodes = [('parent', 'Requester parent native membership'), ('asking', 'Asking bit and demand'), ('assigned', 'Helper assigned Province'), ('eta', 'Aligned route ETA'), ('join', 'Later same CombatID join'), ('defines', 'PLAYER_SUPPORT define slots'), ('demand', 'Player-support demand records'), ('candidate', 'Distance / delay candidate gates'), ('dispatch', 'Movement dispatcher / route count'), ('cross', 'Cross-coordinator +0x34/+0x38')]
    static = [('parent-gate', 'parent', 'asking', 'count>1 before 0x1872BF0; singleton clears'), ('help-match', 'asking', 'assigned', 'stored order; required >= requester available accepts including equality; Province assignment'), ('wanted-read', 'defines', 'demand', 'wanted ratio scales record demand at 0x184FE37'), ('power-siege-read', 'defines', 'demand', 'enemy multiplier / min siege strength consumers 0x1850375 / 0x185041C'), ('distance-read', 'defines', 'candidate', 'squared coordinate distance <= define squared'), ('delay-read', 'defines', 'candidate', 'candidate time <= reference bound + define days'), ('supply-read', 'defines', 'dispatch', 'same-target dispatcher route-count early return')]
    edges = [dict(id=i, **{'from':f,'to':t}, label=label,status='static-confirmed',evidence=['static-contract'],open_question=None) for i,f,t,label in static]
    edges += [dict(id=i, **{'from':f,'to':t},label=label,status='unknown',evidence=[],open_question=q) for i,f,t,label,q in [
        ('record-link', 'demand', 'cross', 'record to cross-coordinator request producer', 'Locate actual writer of CAISubunitStack+0x34/+0x38; do not equate similarly named player records.'),
        ('assignment-eta', 'assigned', 'eta', 'next valid three-unit native assignment and aligned ETA', 'Observe bit1 transition and matching route/ETA under production AI after a qualified >=3-unit fixture.'),
        ('eta-join', 'eta', 'join', 'arrival into the same surviving combat', 'Observe helper CArmy +0x128 and same old CombatID side roster after arrival; predicted contact is not future binding.')]]
    plan = {
        'schema': 'xar.native-research-plan.v1', 'topic': 'war-film-reinforcement-20260923',
        'question': 'Which gates convert asking into native assignment, and which PLAYER_SUPPORT consumers are separate from that signal?',
        'purpose': 'npc-choice', 'build': {'version':'1.19.0.6','exe_sha256':EXPECTED_SHA256},
        'observation': {'mode':'offline-only','actor_kind':'ai','owner_scope':'same-war same-side production AI CUnits; player seed control excluded from observation', 'identity_kind':'generation-id','identity_lifetime':'full CUnit/CArmy/Combat/coordinator IDs bound to one episode; stack ordinals only within the same paused snapshot', 'producer_trigger':'daily-tick','producer':'0x1848310 -> 0x1872BF0; matching 0x1848570', 'caller':'0x18550D0 coordinator update / 0x1846730 stack update', 'consumer':'assignment target and bit consumed by 0x18721B0 / 0x1873AC0', 'cache_lifetime':'asking/assignment are prior producer output until next update; paused queries do not run the AI producer', 'expected_signal':'structurally qualified requester with asking, then helper bit1+Province, aligned ETA, later same CombatID roster', 'zero_sample_meaning':'structural-precondition failure or unobserved candidate/eligibility/timing; never evidence of no reinforcement policy', 'stop_condition':'no live execution in this package; future window stops on combat termination, identity drift, membership loss, or its separately authorized bound', 'runtime_window_ref':None},
        'evidence':[{'id':'static-contract','layer':'source-contract','path':contract_path.name,'sha256':hashlib.sha256(contract_path.read_bytes()).hexdigest(),'exe_sha256':EXPECTED_SHA256,'supports':'Bounded machine-code bytes plus explicit analyst interpretation of parent gates and PLAYER_SUPPORT consumers; not a live confirmation.'}],
        'nodes':[{'id':i,'label':label} for i,label in nodes], 'edges':edges,
        'cases':[{'id':i,'question':q,'status':'pending','evidence':[]} for i,q in [('singleton-negative','Reject two-unit fixture leaving one requester subunit.'),('three-units-merged-negative','Reject three CUnits if remaining two occupy one subunit.'),('native-positive','Observe assignment+ETA+same CombatID join with independently qualified requester parent.'),('player-support-boundaries','Observe equality and one-step-past distance/delay/route limits only in a separately authorized experiment.')]],
    }
    write(plan_path, plan)
    print(json.dumps({'contract':str(contract_path),'plan':str(plan_path),'exe':str(exe),'blocks':len(blocks),'live_execution_performed':False},ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
