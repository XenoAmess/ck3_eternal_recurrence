"""Freeze bounded relationship-network semantics from the pinned EXE, offline.

Creates a new directory with UTF-8 LF JSON. No process access, game invocation,
MCP change, original ABI rewrite, or live-success inference.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
from war_film_relationship_network_extract import SHA, EXE, save

ROOT=Path(__file__).resolve().parents[3]
SPANS=[
    ('collector',0x1879850,0x187A7AF),
    ('shared-candidate-filter',0x18758C0,0x18759BA),
    ('common-script-predicate',0x1B35DF0,0x1B35ED6),
    ('spouse-array-getter',0x2608380,0x2608399),
    ('betrothed-getter',0x26090E0,0x2609129),
    ('relation-map-getter',0x2610840,0x26108F0),
    ('is-allied',0x2661E00,0x2661F06),
    ('confederation-registration',0x506360,0x506554),
    ('confederation-callback',0x2621B50,0x2621BB2),
    ('confederation-getter',0x2601D20,0x2601D42),
    ('same-confederation',0x28B00D0,0x28B0115),
    ('at-war-registration',0x50CF20,0x50D08E),
    ('at-war-callback',0x2622F10,0x2622F48),
    ('at-war-getter',0x2610510,0x2610539),
    ('suzerain-registration',0x504930,0x504A0C),
    ('suzerain-callback',0x2620F30,0x2620F7E),
    ('suzerain-helper',0x2613520,0x261356E),
    ('suzerain-guarantee-predicate',0x22552E0,0x2255357),
    ('tributary-obligation-predicate',0x2255360,0x22553D7),
    ('contract-term-registration',0x2D594A0,0x2D595FF),
    ('human-player-predicate',0x28BCEB0,0x28BCF10),
]
LITERALS=[
    (0x4100BF8,'GetConfederation'),(0x4304B68,'IsAtWar'),
    (0x43254B8,'GetSuzerain'),
    (0x44149F8,'tributary_war_participation_obligation'),
    (0x4414A60,'suzerain_war_participation_guarantee'),
    (0x522F780,'.?AVCSubjectContract@@'),
]
CLAIMS={
    'family-and-alliance-sources':'0x1879850 first visits the complete FamilyData spouse vector (+0x20), then its betrothed ID (+0x10), then relation-map rows (Character+0x1A8->+0x20, stride0x10). The latter excludes spouse/betrothed duplicates, requires relation+0x94 != 0 and +0x1A9 == 0, matching the established native IsAlliedTo predicate 0x2661E00.',
    'contract-sources':'The fourth source is military+0x248 CSubjectContract IDs: subject+0x20 qualifies only with an explicitly present tributary_war_participation_obligation whose level is not its native default. The fifth source is the root own contract+0x28 suzerain when explicitly present suzerain_war_participation_guarantee is non-default. These names are independently bound by 0x2D59578/0x2D595B1 to database+0xF18/+0xF28.',
    'confederation-source':'The final source resolves Character+0x1C0->+0x80 as ConfederationID and enumerates that Confederation+0x18 full CharacterID vector (count+0x24), skipping the root itself and IDs already seen. GetConfederation registration/callback/getter independently names that exact ID field.',
    'actor-at-war-filter':'Actor configuration enables filter_a: candidates whose military+0x318 vector count+0x0C is nonzero are excluded. IsAtWar registration 0x50CF7D -> callback 0x2622F10 -> getter 0x2610510 independently names this condition. Target configuration disables this extra filter.',
    'actor-human-filter':'Actor filter_b excludes candidates recognized by 0x28BCEB0 in the human-player CharacterID set; target configuration disables this extra filter. This affects estimated actor network contribution, not the legality of sending an actual call to war.',
    'actor-confederation-suzerain-filter':'Actor filter_c first excludes candidates with the same valid non--1 ConfederationID. It then excludes the root native GetSuzerain result when the root own subject contract has an explicitly non-default suzerain_war_participation_guarantee. The older same-realm/government labels are not supported names for these instructions. Target configuration disables both extra exclusions.',
    'accumulation-and-seen-order':'Every admitted contributor adds military+0x308 without a percentage discount in this collector. The first sources populate a local seen vector even after common-filter rejection; later contract/confederation sources check it. This is ordered duplicate suppression across sources, not a claim that the first spouse vector is generically deduplicated by this function.',
    'common-predicate-boundary':'The shared filter calls 0x1B35DF0(root,candidate) and requires true before accumulation. That function constructs root scope, binds the candidate CharacterID into a named scope slot, and evaluates the singleton+0xF08 object subobject+0x1960. Its exact authored rule-name binding remains unresolved in this package.',
}
UNKNOWN={
    'common-rule-name':'The current vanilla can_potentially_call_ally rule and its WARRIOR/JOINER trigger are a strong source candidate, but a string/token match did not close its loader binding to the +0x1960 object. Do not present its full script exclusions as instruction-confirmed here.',
    'relationship-lifecycle':'Creation/removal and suspended-state lifecycle of relation+0x94/+0x1A9, malformed source duplicates, and every wider relationship producer remain outside this bounded reader audit.',
    'live-outcome':'No live contributor list, cache freshness, refreshed assessment ratio, call acceptance, actual declaration, or same-war joining was observed. These static exclusions do not mean a candidate can never join an actual war.',
}
SOURCE_EXCERPTS=[
    ('common/scripted_rules/00_rules.txt',[(846,856)]),
    ('common/scripted_triggers/00_war_and_peace_triggers.txt',[(166,221)]),
    ('common/subject_contracts/contracts/special_contracts.txt',[(786,810),(839,895)]),
]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--exe',type=Path,default=EXE)
    p.add_argument('--game',type=Path)
    p.add_argument('--initial-plan',type=Path,default=ROOT/'docs/ck3-native-ai/research-plans/war-film-relationship-network-20260923-r1/plan.json')
    p.add_argument('--output-dir',type=Path,required=True)
    a=p.parse_args()
    if a.output_dir.exists():raise FileExistsError(a.output_dir)
    import pefile
    from capstone import Cs,CS_ARCH_X86,CS_MODE_64
    raw=a.exe.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=SHA:raise ValueError('wrong executable')
    pe=pefile.PE(data=raw,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase
    decoder=Cs(CS_ARCH_X86,CS_MODE_64)
    blocks=[]
    for ident,begin,end in SPANS:
        data=pe.get_data(begin,end-begin)
        instructions=list(decoder.disasm(data,base+begin))
        if len(data)!=end-begin or sum(i.size for i in instructions)!=len(data):raise ValueError('incomplete span '+ident)
        blocks.append({'id':ident,'start_rva':hex(begin),'end_rva_exclusive':hex(end),'sha256':hashlib.sha256(data).hexdigest(),'bytes_hex':data.hex(),'instructions':[f'{i.address-base:#x}: {i.mnemonic} {i.op_str}' for i in instructions]})
    literals=[]
    for rva,text in LITERALS:
        data=pe.get_data(rva,len(text)+1)
        if data!=text.encode()+b'\0':raise ValueError('literal mismatch '+text)
        literals.append({'rva':hex(rva),'text':text,'sha256':hashlib.sha256(data).hexdigest()})
    game=a.game or a.exe.parent.parent/'game'
    sources=[]
    for rel,ranges in SOURCE_EXCERPTS:
        data=(game/rel).read_bytes()
        sources.append({'game_relative_path':rel,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'excerpts':[{'line':i,'text':line} for i,line in enumerate(data.decode('utf-8-sig').splitlines(),1) if any(b<=i<=e for b,e in ranges)]})
    initial_raw=a.initial_plan.read_bytes();initial=json.loads(initial_raw)
    if initial['build']['exe_sha256']!=SHA:raise ValueError('initial plan identity differs')
    prerequisites=[]
    for rel in ['ck3_autonomous_player/native_bridge/research/marriage_proposal_native_binder_v1_abi.json','ck3_autonomous_player/native_bridge/research/war_entry_assessments_v1_abi.json','docs/ck3-native-ai/prewar-encounter-inputs.md']:
        data=(ROOT/rel).read_bytes();prerequisites.append({'repo_path':rel,'sha256':hashlib.sha256(data).hexdigest()})
    contract={'schema':'xar.war-film-relationship-network.static.v1','build':'1.19.0.6','exe_sha256':SHA,'exe_bytes':len(raw),'scope':'offline-only','initial_plan_sha256':hashlib.sha256(initial_raw).hexdigest(),'claims':CLAIMS,'unknown':UNKNOWN,'code_blocks':blocks,'literal_anchors':literals,'source_files':sources,'prior_contracts':prerequisites}
    a.output_dir.mkdir(parents=True,exist_ok=False)
    save(a.output_dir/'static.json',contract)
    digest=hashlib.sha256((a.output_dir/'static.json').read_bytes()).hexdigest()
    plan=dict(initial)
    plan['nodes']=[{'id':key,'label':label} for key,label in [('root','Actor/effective target'),('sources','Spouses, betrothed, active alliance relations, subject contracts, suzerain and confederation'),('filtered','Common predicate then actor-only extra filters'),('sum','Ordered network +308 sum'),('future','Unobserved runtime behavior')]]
    specs=[('family-and-alliance-sources','root','sources'),('contract-sources','root','sources'),('confederation-source','root','sources'),('actor-at-war-filter','sources','filtered'),('actor-human-filter','sources','filtered'),('actor-confederation-suzerain-filter','sources','filtered'),('accumulation-and-seen-order','filtered','sum'),('common-predicate-boundary','sources','filtered')]
    plan['edges']=[{'id':key,'from':start,'to':end,'label':CLAIMS[key],'status':'static-confirmed','evidence':['static-contract'],'open_question':None} for key,start,end in specs]
    plan['edges'] += [{'id':key,'from':'sum','to':'future','label':label,'status':'unknown','evidence':[],'open_question':label} for key,label in UNKNOWN.items()]
    plan['evidence']=[{'id':'static-contract','layer':'source-contract','path':'static.json','sha256':digest,'exe_sha256':SHA,'supports':'Pinned instructions, independent named getter/term bindings and prior contract provenance; analyst-interpreted static semantics only.'}]
    save(a.output_dir/'result-plan.json',plan)
    print(json.dumps({'output':str(a.output_dir),'static_edges':len(specs),'unknown_edges':len(UNKNOWN),'live_edges':0,'sha256':digest}))

if __name__=='__main__':main()
