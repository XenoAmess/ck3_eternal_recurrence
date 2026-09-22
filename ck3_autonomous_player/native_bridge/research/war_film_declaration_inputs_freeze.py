"""Freeze the bounded W1 offline declaration-input contract and research plan.

Requires pefile and capstone in the explicitly selected interpreter. Never opens
a process or modifies the game. Output directory must not already exist.
"""
import argparse
import hashlib
import json
from pathlib import Path

from war_film_declaration_inputs_extract import DEFAULT_EXE, SHA

SPANS = [
    ('normal-entry-preparation', 0x187ACBD, 0x187AD11),
    ('periodic-selector-call', 0x187B3C6, 0x187B3F6),
    ('preparation-builder', 0x18408F0, 0x1840CD5),
    ('war-chest-define-registration', 0x18939E0, 0x18939FD),
    ('maintenance-months-registration', 0x1893AB0, 0x1893ACD),
    ('gold-key-registration', 0x548B00, 0x548B98),
    ('treasury-key-registration', 0x548D80, 0x548E18),
    ('gold-value-factory-thunk', 0x28719F0, 0x28719F5),
    ('treasury-value-factory-thunk', 0x2871A30, 0x2871A35),
    ('gold-value-factory', 0x2876400, 0x2876463),
    ('treasury-value-factory', 0x28765C0, 0x2876623),
    ('gold-war-chest-reader', 0x28756D0, 0x2875784),
    ('treasury-war-chest-reader', 0x2875180, 0x2875226),
    ('actor-state-builder', 0x18784D0, 0x18789F8),
    ('admin-boldness-define', 0x18A0C30, 0x18A0C4D),
    ('admin-liege-define', 0x18A2CC0, 0x18A2CDD),
    ('admin-vassal-define', 0x18A2EE0, 0x18A2EFD),
    ('network-callers', 0x1878B36, 0x1878BFE),
    ('target-assessment-before-config', 0x18BE0E3, 0x18BE14C),
    ('config-generation', 0x18BE5FD, 0x18BE62A),
    ('candidate-filter-before-score', 0x18BE80E, 0x18BE86D),
    ('candidate-cansend-call', 0x18BD1D1, 0x18BD1F2),
    ('candidate-direct-cansend-call', 0x18BD423, 0x18BD462),
    ('title-score-and-script-add', 0x18BED0C, 0x18BEE1F),
    ('cansend', 0x2C43F00, 0x2C44070),
    ('special-validator-dispatch', 0x2C431B4, 0x2C431E5),
    ('war-declaration-special-validator', 0x24D76F0, 0x24D7807),
    ('cb-start-validator', 0x2D96600, 0x2D966E8),
    ('cb-cost', 0x2D92F20, 0x2D9305B),
    ('generic-interaction-cost', 0x2CD9C70, 0x2CD9D1C),
    ('payability-comparison', 0x2CDD5EF, 0x2CDD694),
]
POINTERS = {
    'gold_factory_slots': (0x439E748, 3),
    'treasury_factory_slots': (0x439E6C8, 3),
    'gold_value_eval_slot': (0x439C008, 1),
    'treasury_value_eval_slot': (0x439D320, 1),
    'war_declaration_special_vtable': (0x411DAA0, 13),
}
STRINGS = {
    'gold': (0x439EDC0, 'war_chest_gold'),
    'treasury': (0x439F4C8, 'war_chest_treasury'),
    'minimum': (0x4194070, 'MIN_WAR_CHEST'),
    'months': (0x4194048, 'MONTHS_OF_MAINTENANCE_IN_WAR_CHEST'),
    'admin_boldness': (0x4195520, 'AI_BOLDNESS_ADJUSTMENT_FACTOR_ADMIN_REALM_POWER'),
    'admin_liege': (0x4195968, 'ADMIN_REALM_TOTAL_POWER_ADJUSTMENT_TOP_LIEGE'),
    'admin_vassal': (0x4195938, 'ADMIN_REALM_TOTAL_POWER_ADJUSTMENT_VASSAL'),
}
CLAIMS = {
    'reserve-before-choice': 'Normal periodic entry R8d=0 requires war_chest_gold >= computed slot0 and war_chest_treasury >= computed slot6 before chance, cooldown and candidate selection; R8d!=0 bypasses these two comparisons.',
    'reserve-identities': 'Literal registration -> factory -> value vtable+0x100 -> readers name AI strategy+0x20 budget offsets +0x168 gold war chest and +0x1A8 treasury war chest. They are not the ordinary character gold balance.',
    'reserve-demand': '0x18408F0 consumes tier-indexed MIN_WAR_CHEST and MONTHS_OF_MAINTENANCE_IN_WAR_CHEST, constructs a 0x50 bundle, and writes demand slots0 and6. Two-resource minimum splitting follows the exact code, not an invented burn-rate simulation.',
    'actor-admin-addition': 'State16+0 begins at military+0x308; government bit9 enables title-derived administrative addition weighted by clamped boldness and registered liege/vassal defines. The final government bit1 branch can replace the result with zero.',
    'network-addition': '0x1878A00 conditionally calls 0x1879850 for target with three zero filters and actor with three one filters; additions are distinct from actor State16 construction.',
    'power-before-cb': 'Normal target loop performs assessment 0x1878A00 and ratio bound 0x18C1F90 before per-CB config generation 0x2D95D00.',
    'candidate-validator-before-score': '0x18BE860 calls 0x18BCC30 using AI interaction slot +0x1070; candidate branches call final CanSend 0x2C43F00 before later title/ai_score scoring.',
    'cb-cost-before-generic-cost': 'Final CanSend invokes prevalidation, whose special vtable+0x60 resolves CWarDeclaration -> 0x24D76F0 -> 0x2D96600 -> 0x2D92F20. CB+0xB68 is evaluated by 0x2CDB7B0, passes additional 0x2D92AD0 then native affordability 0x2CDCFF0. Empty compiled costs return true. Later final CanSend separately checks generic interaction definition+0x38 costs via 0x2CD9C70.',
}
UNKNOWN = {
    'base-cache-producer': 'Producer and composition of military extension+0x308, including special/event troops, are not closed here; a separate soldier-count/MAX bucket result cannot substitute for it.',
    'network-callability': 'All source container identities and whether each contributor would actually accept a future call are not closed by the accumulator. No all-allies-join claim.',
    'extra-cost-and-live': '0x2D92AD0 additional cost-dependent status gates, all generic resource exceptions, and runtime observations are not fully named/tested in this package.',
}


def dump(path, value):
    data = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    with path.open('xb') as stream:
        stream.write(data)
    return hashlib.sha256(data).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--exe', type=Path, default=DEFAULT_EXE)
    p.add_argument('--game', type=Path)
    p.add_argument('--output-dir', type=Path, required=True)
    args = p.parse_args()
    import pefile
    from capstone import Cs, CS_ARCH_X86, CS_MODE_64
    raw = args.exe.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SHA:
        raise ValueError('wrong executable build')
    if args.output_dir.exists():
        raise FileExistsError(args.output_dir)
    image = pefile.PE(data=raw, fast_load=True)
    base = image.OPTIONAL_HEADER.ImageBase
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    def get(rva, size):
        off = image.get_offset_from_rva(rva)
        data = raw[off:off+size]
        if len(data) != size:
            raise ValueError('incomplete file-backed range')
        return data
    blocks = []
    for name, begin, end in SPANS:
        data = get(begin, end-begin)
        ins = list(decoder.disasm(data, base+begin))
        if sum(i.size for i in ins) != len(data):
            raise ValueError(f'undecoded bytes: {name}')
        blocks.append({'id': name, 'start_rva': hex(begin), 'end_rva_exclusive': hex(end),
                       'sha256': hashlib.sha256(data).hexdigest(), 'bytes_hex': data.hex(),
                       'instructions': [f'{i.address-base:#x}: {i.mnemonic} {i.op_str}' for i in ins]})
    strings = []
    for name, (rva, expected) in STRINGS.items():
        data = get(rva, len(expected)+1)
        if data != expected.encode()+b'\0':
            raise ValueError(f'literal mismatch: {name}')
        strings.append({'id': name, 'rva': hex(rva), 'value': expected, 'sha256': hashlib.sha256(data).hexdigest()})
    pointers = []
    for name, (rva, count) in POINTERS.items():
        data = get(rva, count*8)
        pointers.append({'id': name, 'rva': hex(rva), 'sha256': hashlib.sha256(data).hexdigest(),
                         'target_rvas': [hex(int.from_bytes(data[n:n+8], 'little')-base) for n in range(0,len(data),8)]})
    game = args.game or args.exe.parent.parent/'game'
    sources = []
    for name in ('common/defines/ai/00_ai.txt', 'common/casus_belli_types/_casus_belli.info'):
        data = (game/name).read_bytes()
        sources.append({'game_relative_path': name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
    if sources[0]['sha256'] != 'c78f9cd8df9938cc9f38e817bcb6e32cd13720b5bd9de077b85e3e1c6f030293':
        raise ValueError('wrong ai defines')
    if sources[1]['sha256'] != 'e3bacd9f3360837f6ed7d5f22b937ab7e79cb675ad804819a627cb73970ce699':
        raise ValueError('wrong CB source contract')
    contract = {'schema': 'xar.war-film-declaration-inputs.static.v1', 'build': '1.19.0.6',
                'exe_sha256': SHA, 'exe_bytes': len(raw), 'scope': 'offline-only; no process execution or observed decision',
                'claims': CLAIMS, 'unknown': UNKNOWN, 'source_files': sources,
                'registered_literals': strings, 'pointer_bindings': pointers, 'code_blocks': blocks}
    args.output_dir.mkdir(parents=True, exist_ok=False)
    name = 'war_film_declaration_inputs_static_20260923.json'
    digest = dump(args.output_dir/name, contract)
    nodes = [('entry','Normal periodic AI entry'), ('reserve','Gold and treasury war chest'),
             ('demand','Tier and maintenance demand'), ('choice','Chance and cooldown'),
             ('base','Actor military cache'), ('admin','State16 administrative addition'),
             ('network','Asymmetric relationship network'), ('power','Target power gate'),
             ('configs','CB and configuration candidates'), ('cbcost','Special CB cost'),
             ('generic','Generic interaction cost'), ('score','Candidate scoring'),
             ('special','Special troop cache production'), ('live','Future live callability / decision')]
    specs = [('reserve-identities','entry','reserve'), ('reserve-demand','demand','reserve'),
             ('reserve-before-choice','reserve','choice'), ('actor-admin-addition','base','admin'),
             ('network-addition','admin','network'), ('power-before-cb','power','configs'),
             ('candidate-validator-before-score','configs','score'), ('cb-cost-before-generic-cost','cbcost','generic')]
    edges = [{'id': key, 'from': start, 'to': end, 'label': CLAIMS[key], 'status':'static-confirmed',
              'evidence':['static-contract'], 'open_question': None} for key,start,end in specs]
    for key,start,end in [('base-cache-producer','special','base'), ('network-callability','network','live'), ('extra-cost-and-live','cbcost','live')]:
        edges.append({'id':key,'from':start,'to':end,'label':UNKNOWN[key],'status':'unknown','evidence':[],'open_question':UNKNOWN[key]})
    plan = {'schema':'xar.native-research-plan.v1','topic':'war-film-declaration-inputs-20260923',
            'question':'What exactly precedes C01-C02 military, CB cost, and score choices in the ordinary AI declaration path?',
            'purpose':'npc-choice','build':{'version':'1.19.0.6','exe_sha256':SHA},
            'observation':{'mode':'offline-only','actor_kind':'ai','owner_scope':'ordinary periodic actor-specific declaration attempt, R8d=0; not all declaration callers',
                'identity_kind':'generation-id','identity_lifetime':'Actor, target, title and selected CB bound to one future attempt; no pointer reuse across revisions',
                'producer_trigger':'daily-tick','producer':'0x187AB90 with native caller scheduling',
                'caller':'AI strategy periodic context; nonzero R8d is separately scoped',
                'consumer':'0x18BDDA0 candidate validator then scoring; final chosen interaction',
                'cache_lifetime':'military+0x308 and war-chest budget are prior native producer outputs; paused reads do not refresh them',
                'expected_signal':'future same-attempt entry mode, reserve demand/actuals, State16, assessment, cost vectors and rejection/selection',
                'zero_sample_meaning':'no attempt or earlier gate rejection; never proof that all CBs or war inputs were examined',
                'stop_condition':'offline package only; no live execution is authorized here; future run must stop on identity drift or its frozen window',
                'runtime_window_ref':None},
            'evidence':[{'id':'static-contract','layer':'source-contract','path':name,'sha256':digest,'exe_sha256':SHA,
                         'supports':'Exact native bytes and registration chains with bounded analyst interpretations; not a live observation.'}],
            'nodes':[{'id':key,'label':label} for key,label in nodes], 'edges':edges,
            'cases':[{'id':key,'question':question,'status':'pending','evidence':[]} for key,question in [
                ('reserve-boundary','Future ordinary entry: below/equal/above both native computed requirements, preserving the other gates.'),
                ('cb-payability','Future same candidate/config: record actual CB and generic cost vectors and their own validator result.'),
                ('network-admin','Future same-frame native base/admin/network terms; never substitute UI soldier counts.')]]}
    plan_hash = dump(args.output_dir/'war_film_declaration_inputs_plan_20260923.json', plan)
    print(json.dumps({'output_dir':str(args.output_dir),'contract_sha256':digest,'plan_sha256':plan_hash,'static_edges':len(specs),'unknown_edges':len(UNKNOWN),'live_edges':0}))


if __name__ == '__main__':
    main()
