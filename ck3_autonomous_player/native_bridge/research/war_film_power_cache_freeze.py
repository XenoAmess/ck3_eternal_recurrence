"""Freeze an exact-build, offline military power-cache producer contract.

Uses the explicitly selected interpreter's pefile/capstone. Creates a new output
directory, writes UTF-8 LF, never opens CK3 or replaces earlier evidence.
"""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path

from war_film_power_cache_locate import SHA, save

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_EXE = Path('C:/SteamLibrary/steamapps/common/CRUSAD~1/binaries/ck3.exe')
SPANS = [
    ('producer', 0x2971090, 0x29713D1),
    ('publish-one-character', 0x2617F80, 0x2617FED),
    ('publish-batch', 0x264D590, 0x264D6C6),
    ('scratch-update-without-publication', 0x26478F0, 0x264793B),
    ('conditional-change-publication', 0x28ADE4F, 0x28ADEC0),
    ('batch-caller', 0x264D27E, 0x264D2C9),
    ('character-buckets', 0x292FC40, 0x293084E),
    ('regiment-bucket', 0x2930850, 0x2930A8C),
    ('mercenary-bucket', 0x2930A90, 0x2930D2C),
    ('order-bucket', 0x2930D30, 0x2930FCC),
    ('composition-power', 0x2394EE0, 0x23950F9),
    ('title-membership', 0x28AB770, 0x28AB879),
    ('knight-membership', 0x28FDD40, 0x28FE087),
    ('levy-selector', 0x290E410, 0x290E6BA),
    ('actor-declaration-builder', 0x18784D0, 0x18789F8),
    ('knight-damage-registration', 0x2121850, 0x212186D),
    ('knight-toughness-registration', 0x2121B90, 0x2121BAD),
    ('knight-average-registration', 0x2121ED0, 0x2121EED),
    ('levy-stat-a-registration', 0x211F300, 0x211F31D),
    ('levy-stat-b-registration', 0x211F470, 0x211F48D),
]
REGISTRATIONS = [
    (0x2121850, 0x570EDF8, 'KNIGHT_DAMAGE_PER_PROWESS'),
    (0x2121B90, 0x570EDFC, 'KNIGHT_TOUGHNESS_PER_PROWESS'),
    (0x2121ED0, 0x570EE00, 'KNIGHT_AVERAGE_PROWESS_FOR_AI_POWER_CALCULATION'),
    (0x211F300, 0x570EF68, 'LEVY_TOUGHNESS'),
    (0x211F470, 0x570EF70, 'LEVY_ATTACK'),
]
CLAIMS = {
    'mode-three': '0x2971090 calls 0x292FC40 with R8b=3: bit0 CURRENT and bit1 MAX are both enabled; this differs from the battle-score caller mode2.',
    'publish-power': 'Producer sums eight int64 bucket+0x08 values into military+0x78, then 0x2617F80 / 0x264D590 publish +0x78 to +0x308. The conditional 0x28AD550 tail uses the same copy sequence.',
    'publish-counts': 'Eight bucket+0x04 int32 values sum into +0x60 and publish to +0x2F0; eight bucket+0x00 int32 values sum into +0x64 and publish to +0x2F4. Counts and power are different fields and units.',
    'current-power': 'Eight int64 bucket+0x10 values sum into military+0x80 and publish to +0x310. +0x308 is the MAX-side power channel, not the CURRENT-side channel.',
    'special-not-full-strength': 'Event/special groups at military+0x290 use composition quantity and 0x2394EE0 power for both CURRENT and MAX slots. Ordinary regiment MAX uses +0x128 times type(+0x290+0x298), except kind+0x138==1 uses composition power too.',
    'direct-membership': 'The eight buckets come from levy selector, military regiment/company/order/event containers, knight helper, qualifying held-title regiments, and nomadic conversion. The builder does not traverse the later declaration relationship network.',
    'declaration-after-cache': '0x18784D0 reads military+0x308 before its separate administrative addition and government clearing rule. Target/network use of the same cache is established by the preceding declaration-input package, not a promise that allies will join.',
    'knight-comment-correction': '0x29300A9..0x2930119 computes knight count times (damage+ toughness) times assumed prowess in Q100000. The current vanilla definitions 50,10,10 give 600 per knight, despite their stale comment saying 1100.',
}
UNKNOWN = {
    'natural-refresh': 'Natural update scheduling, coherence between scratch and published fields, and age at a particular declaration attempt remain unobserved. A call to 0x2971090 alone does not establish publication.',
    'network-membership': 'The complete relationship-source names, overlap with administrative additions, and actual acceptance/join behavior of every contributor remain outside this bounded cache-producer package.',
    'runtime-components': 'No live per-character bucket values, modified define values, full special kind/state lifecycle, or real declaration outcome were observed.',
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe', type=Path, default=DEFAULT_EXE)
    parser.add_argument('--game', type=Path)
    parser.add_argument('--initial-plan', type=Path, default=ROOT/'docs/ck3-native-ai/research-plans/war-film-power-cache-20260923-r1/war_film_power_cache_plan_20260923.json')
    parser.add_argument('--output-dir', required=True, type=Path)
    args = parser.parse_args()
    import pefile
    from capstone import Cs, CS_ARCH_X86, CS_MODE_64
    from capstone.x86 import X86_OP_MEM, X86_REG_RIP

    if args.output_dir.exists():
        raise FileExistsError(args.output_dir)
    raw = args.exe.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SHA:
        raise ValueError('wrong executable build')
    image = pefile.PE(data=raw, fast_load=True)
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.detail = True
    base = image.OPTIONAL_HEADER.ImageBase

    def get(rva, size):
        offset = image.get_offset_from_rva(rva)
        data = raw[offset:offset+size]
        if len(data) != size:
            raise ValueError('incomplete file-backed span')
        return data

    blocks = []
    for name, begin, end in SPANS:
        data = get(begin, end-begin)
        instructions = list(decoder.disasm(data, base+begin))
        if sum(i.size for i in instructions) != len(data):
            raise ValueError('undecoded span: '+name)
        blocks.append({'id':name, 'start_rva':hex(begin), 'end_rva_exclusive':hex(end),
                       'sha256':hashlib.sha256(data).hexdigest(), 'bytes_hex':data.hex(),
                       'instructions':[f'{i.address-base:#x}: {i.mnemonic} {i.op_str}' for i in instructions]})

    definitions = []
    for begin, slot, key in REGISTRATIONS:
        pointers = {}
        for ins in decoder.disasm(get(begin, 0x1D), base+begin):
            if ins.mnemonic == 'lea' and len(ins.operands) == 2:
                operand = ins.operands[1]
                if operand.type == X86_OP_MEM and operand.mem.base == X86_REG_RIP:
                    pointers[ins.reg_name(ins.operands[0].reg)] = ins.address+ins.size+operand.mem.disp-base
        if pointers.get('r9') != slot:
            raise ValueError('registration slot mismatch: '+key)
        literal = get(pointers['r8'], len(key)+1)
        if literal != key.encode()+b'\0':
            raise ValueError('registration key mismatch: '+key)
        definitions.append({'key':key, 'slot_rva':hex(slot), 'registration_rva':hex(begin),
                            'literal_rva':hex(pointers['r8']), 'literal_sha256':hashlib.sha256(literal).hexdigest()})

    game = args.game or args.exe.parent.parent/'game'
    source = game/'common/defines/00_defines.txt'
    source_raw = source.read_bytes()
    if hashlib.sha256(source_raw).hexdigest() != 'c1eca141c71ec1e741ca5336e01bb538eefaec05b0684edec477cfc9053c3807':
        raise ValueError('wrong frozen vanilla defines source')
    source_text = source_raw.decode('utf-8-sig')
    for item in definitions:
        matches = re.findall(r'^\s*'+re.escape(item['key'])+r'\s*=\s*([0-9]+)\b', source_text, re.MULTILINE)
        if len(matches) != 1:
            raise ValueError('nonunique source define: '+item['key'])
        item['vanilla_source_value'] = int(matches[0])
    values = {d['key']:d['vanilla_source_value'] for d in definitions}
    knight_power = (values['KNIGHT_DAMAGE_PER_PROWESS']+values['KNIGHT_TOUGHNESS_PER_PROWESS'])*values['KNIGHT_AVERAGE_PROWESS_FOR_AI_POWER_CALCULATION']
    initial_raw = args.initial_plan.read_bytes()
    initial = json.loads(initial_raw)
    if initial['build']['exe_sha256'] != SHA:
        raise ValueError('initial plan build mismatch')
    previous = ROOT/'docs/ck3-native-ai/research-plans/war-film-declaration-inputs-20260923-r1/war_film_declaration_inputs_static_20260923.json'
    previous_digest = hashlib.sha256(previous.read_bytes()).hexdigest()
    try:
        previous_reference = Path(os.path.relpath(previous, args.output_dir.resolve())).as_posix()
    except ValueError:  # Windows cross-drive path cannot be relative.
        previous_reference = previous.as_posix()
    contract = {'schema':'xar.war-film-power-cache.static.v1', 'build':'1.19.0.6',
                'exe_sha256':SHA, 'exe_bytes':len(raw), 'scope':'offline-only; no CK3 launch or live observation',
                'initial_plan_sha256':hashlib.sha256(initial_raw).hexdigest(),
                'prior_declaration_contract':{'repo_path':previous.relative_to(ROOT).as_posix(),'sha256':previous_digest},
                'claims':CLAIMS, 'unknown':UNKNOWN, 'code_blocks':blocks, 'registered_definitions':definitions,
                'source_file':{'game_relative_path':'common/defines/00_defines.txt', 'bytes':len(source_raw),
                               'sha256':hashlib.sha256(source_raw).hexdigest(),
                               'excerpts':[{'line':n,'text':line} for n,line in enumerate(source_text.splitlines(),1) if 588<=n<=589 or 610<=n<=624]},
                'computed_from_current_vanilla_source':{'knight_power_per_knight':knight_power,'raw_q100000':knight_power*100000,
                                                        'not_a_runtime_define_sample':True},
                'cache_mapping':[
                    {'bucket_field':'0x04','type':'int32 count','scratch':'0x60','published':'0x2F0'},
                    {'bucket_field':'0x00','type':'int32 count','scratch':'0x64','published':'0x2F4'},
                    {'bucket_field':'0x08','type':'int64 Q100000 power','scratch':'0x78','published':'0x308'},
                    {'bucket_field':'0x10','type':'int64 Q100000 power','scratch':'0x80','published':'0x310'}]}
    args.output_dir.mkdir(parents=True, exist_ok=False)
    contract_name = 'war_film_power_cache_static_20260923.json'
    save(args.output_dir/contract_name, contract)
    digest = hashlib.sha256((args.output_dir/contract_name).read_bytes()).hexdigest()
    nodes = [('producer','2971090 mode3 producer'), ('buckets','Eight quantity/power buckets'),
             ('cache','Published military+308'), ('counts','Published +2F0/+2F4 counts'),
             ('current','Published +310 CURRENT power'), ('special','Special/regiment composition'),
             ('sources','Direct troop containers'), ('decision','Declaration builder/network'),
             ('knight','Knight define arithmetic'), ('future','Future same-revision live observation')]
    specs = [('mode-three','producer','buckets'), ('publish-power','buckets','cache'),
             ('publish-counts','buckets','counts'), ('current-power','buckets','current'),
             ('special-not-full-strength','special','buckets'), ('direct-membership','sources','buckets'),
             ('declaration-after-cache','cache','decision'), ('knight-comment-correction','knight','buckets')]
    edges = [{'id':key,'from':start,'to':end,'label':CLAIMS[key],'status':'static-confirmed',
              'evidence':['static-contract'],'open_question':None} for key,start,end in specs]
    edges.extend({'id':key,'from':start,'to':'future','label':UNKNOWN[key], 'status':'unknown',
                  'evidence':[],'open_question':UNKNOWN[key]} for key,start in [('natural-refresh','producer'),('network-membership','decision'),('runtime-components','special')])
    plan = dict(initial)
    plan['observation'] = dict(initial['observation'], producer_trigger='unknown',
        producer='0x2971090 scratch producer; 0x2617F80/0x264D590/conditional 0x28AD550 publish caches',
        caller='0x264D590 selected character batch, 0x2617F80 direct character wrapper; natural cadence not established',
        cache_lifetime='Scratch refresh and published cache update are distinct; natural phase and age at declaration remain unknown')
    plan['evidence'] = [{'id':'static-contract','layer':'source-contract','path':contract_name,'sha256':digest,
                         'exe_sha256':SHA,'supports':'Exact native bytes and source define arithmetic; analyst-interpreted static edges only, no live success.'},
                        {'id':'prior-declaration-contract','layer':'source-contract',
                         'path':previous_reference,
                         'sha256':previous_digest,'exe_sha256':SHA,
                         'supports':'Previously frozen declaration builder/admin/network separation; not actual ally acceptance.'}]
    next(e for e in edges if e['id']=='declaration-after-cache')['evidence'].append('prior-declaration-contract')
    plan['nodes'] = [{'id':key,'label':label} for key,label in nodes]
    plan['edges'] = edges
    save(args.output_dir/'war_film_power_cache_result_plan_20260923.json', plan)
    print(json.dumps({'output_dir':str(args.output_dir),'static_edges':len(specs),'unknown_edges':len(UNKNOWN),
                      'live_edges':0,'contract_sha256':digest,'knight_power_per_knight':knight_power}))


if __name__ == '__main__':
    main()
