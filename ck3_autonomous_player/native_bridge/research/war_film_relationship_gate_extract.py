"""Bounded, offline exact-build loader mapping for the network common gate."""
from pathlib import Path
import argparse
import hashlib
import json
import struct

SHA='2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86'
ROOT=Path(__file__).resolve().parents[3]
EXE=Path('C:/SteamLibrary/steamapps/common/CRUSAD~1/binaries/ck3.exe')
SPANS=[
    ('ally-scope-registration',0xC060,0xC0B9),
    ('common-predicate',0x1B35DF0,0x1B35ED6),
    ('rules-singleton-accessor',0x1B36670,0x1B366C7),
    ('game-rule-registration-table',0x1B34610,0x1B350F3),
    ('registration-vector-builder',0x1B36E10,0x1B36FAB),
    ('game-script-system-setup',0x203D290,0x203D63F),
    ('registration-vector-move',0x2043010,0x2043159),
    ('script-system-registration-owner',0x332C380,0x332C869),
    ('registration-vector-copy',0x332F590,0x332F65D),
    ('rules-singleton-constructor',0x3335FF0,0x3336141),
    ('rules-base-directory',0x33EDE20,0x33EE157),
    ('rules-load-order',0x33ED7E0,0x33ED830),
    ('rules-directory-enumeration',0x33EF390,0x33EF6BD),
    ('rule-file-parser',0x33EE960,0x33EEAAB),
    ('rule-entry-parser',0x33EF0D0,0x33EF38F),
    ('rule-entry-key-lookup',0x33EFA10,0x33EFEB4),
    ('rules-postload-index-copy',0x33EDB00,0x33EDE1D),
    ('token-catalog-initializer',0x3B57BA0,0x3B58324),
    ('token-to-string-lookup',0x3B58970,0x3B58A94),
]
CLAIMS={
    'rule-name-registration':'0x1B34610 registers index 29 with token 0x3529 and scope kind 4. The token catalog row at 0x42C7830 is {token, string-pointer}; 0x3B580E2/0x3B580E9 and 0x3B58279..0x3B58294 prove this layout. Its string is can_potentially_call_ally. The following 0x352A belongs to the next row.',
    'registration-transfer':'0x203D340 builds the table, 0x203D34D moves it to setup+0xD0, and 0x203D51D calls 0x332C380. That function copies setup+0xD0 into global 0x576AF88 owner+0xD0 and then owner+0xF0. 0x33ED7E0 copies owner+0xF0 into rules singleton+0x2B30 before reading rule files.',
    'loaded-rule-to-array':'0x33ED7E0 reads common/scripted_rules through 0x33EF390 and 0x33EE960, then 0x33EDB00 resolves each registered token to its name, hashes it and looks up the parsed entry using 0x33EEF90. A valid entry with nonnegative +0x78 copies its trigger data from entry+0x38 into singleton+0xF08 array[index*0xE0]. Thus index 29 reaches offset 0x1960. Missing definitions have a distinct logged/default-construction path; no runtime success is inferred.',
    'exact-scope-direction':'0xC060 registers the literal ally at slot 0x57EB86C. 0x1B35DF0 constructs root from its first character argument, binds the second character full ID (kind 4) using that slot via 0x3358160, and evaluates rules[index 29] via 0x334C510. The authored rule passes WARRIOR=root and JOINER=scope:ally.',
    'authored-gate-boundary':'The hash-bound vanilla trigger rejects ordinary vassal-to-root and root-to-liege calls subject to its explicit diarch, same-confederation and vassal_contract_liege_forced_war_override exceptions. Its body contains no CombatID, war-side, accepted-call or joining observation. Comments about defensive wars cannot add an absent war-side test to this predicate.',
}
UNKNOWN={
    'runtime-rule-and-outcome':'No live rules object, actual predicate result, override set, contributor sum, call acceptance or joined war was observed. This is a static default-source binding for the pinned executable and files.',
    'nested-trigger-implementation':'The loaded script text is preserved; the native implementations and complete semantics of every nested relationship/contract trigger are outside this bounded loader audit.',
}
EXCLUSIONS=[
    {'path':'Catalog pointer 0x42C7838 followed by qword 0x352A','outcome':'Rejected adjacent-row association; actual row token is preceding 0x3529. Previous bounded scan for 0x352A cannot prove absence of the real registration.'},
    {'path':'Raw 0x352A at 0x99CF02 and data near 0x43CBC74','outcome':'The first is inside a call displacement; the second is an unrelated modifier descriptor. Neither is this rule registration.'},
    {'path':'Hardcoded +0x1960 writes in unrelated UI/modifier functions','outcome':'Rejected as unrelated owners. Actual producer addresses a generic 0xE0 array by registered index 29.'},
    {'path':'Substring scripted_rules at 0x44C91BF or 0x44DAEA7','outcome':'Suffixes of common/scripted_rules and jomini_scripted_rules, not standalone class-name or field bindings.'},
]

def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())

def initial_plan(output):
    old=ROOT/'docs/ck3-native-ai/research-plans/war-film-relationship-network-20260923-r1/plan.json'
    plan=json.loads(old.read_bytes())
    plan['topic']='war-film-relationship-gate-20260923'
    plan['question']='Does the native loader bind can_potentially_call_ally to scripted-rules singleton+0xF08->+0x1960 used by 0x1B35DF0, and what is the exact scope direction?'
    plan['observation'].update({'producer':'Unknown native rule registration/loader into the +0x1960 trigger subobject','caller':'0x1879850 and 0x18758C0 -> 0x1B35DF0','consumer':'Boolean eligibility gate for one actor or target network contribution','expected_signal':'Exact symbol/string/registration or loader-index proof reaching the same consumed object and scope binding','stop_condition':'No live access. One bounded pass over literal/registration and singleton-owner loading plus its trigger-array addressing. If no exact binding closes, freeze ruled-out matches and precise remaining edge; do not repeat broad scans.'})
    plan['nodes']=[{'id':key,'label':label} for key,label in [('name','Authored can_potentially_call_ally'),('loader','Native loader registration'),('field','Rules object +0x1960'),('gate','0x1B35DF0 with root/candidate scopes')]]
    plan['edges']=[{'id':key,'from':start,'to':end,'label':label,'status':'unknown','evidence':[],'open_question':label} for key,start,end,label in [('name-to-loader','name','loader','Locate actual loading registration; catalog string similarity is not a binding.'),('loader-to-field','loader','field','Trace exact field offset or array index into singleton+0xF08 object.'),('scope-direction','field','gate','Bind caller root and candidate to their actual authored scope names.')]]
    plan['cases']=[{'id':'loaded-rule-runtime','question':'No live evaluation or current rule-object contents observed.','status':'pending','evidence':[]}]
    save(output,plan)

def freeze(args):
    if args.output_dir.exists():
        raise FileExistsError(args.output_dir)
    import pefile
    from capstone import Cs, CS_ARCH_X86, CS_MODE_64
    from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RSP
    raw=args.exe.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=SHA:
        raise ValueError('wrong executable')
    pe=pefile.PE(data=raw,fast_load=True)
    base=pe.OPTIONAL_HEADER.ImageBase
    decoder=Cs(CS_ARCH_X86,CS_MODE_64)
    decoder.detail=True
    blocks=[]
    decoded={}
    for ident,begin,end in SPANS:
        data=pe.get_data(begin,end-begin)
        instructions=list(decoder.disasm(data,base+begin))
        if len(data)!=end-begin or sum(i.size for i in instructions)!=len(data):
            raise ValueError('incomplete span '+ident)
        decoded[ident]=instructions
        blocks.append({'id':ident,'start_rva':hex(begin),'end_rva_exclusive':hex(end),'sha256':hashlib.sha256(data).hexdigest(),'bytes_hex':data.hex(),'instructions':[f'{i.address-base:#x}: {i.mnemonic} {i.op_str}' for i in instructions]})
    # Derive this slot from actual MOV operands, then resolve its actual catalog row.
    table=decoded['game-rule-registration-table']
    matches=[]
    for current,following in zip(table,table[1:]):
        def stack_immediate(ins,disp):
            return ins.mnemonic=='mov' and len(ins.operands)==2 and ins.operands[0].type==X86_OP_MEM and ins.operands[0].mem.base==X86_REG_RSP and ins.operands[0].mem.disp==disp and ins.operands[1].type==X86_OP_IMM
        if stack_immediate(current,0x20) and current.operands[1].imm==29 and stack_immediate(following,0x24):
            matches.append((current.address-base,following.address-base,following.operands[1].imm))
    if len(matches)!=1:
        raise ValueError('index 29 registration is not unique')
    index_rva,token_rva,token=matches[0]
    catalog_matches=[]
    for rva in range(0x42B4AA0,0x42D48F0,16):
        key,pointer=struct.unpack('<QQ',pe.get_data(rva,16))
        if key==token:
            text=pe.get_data(pointer-base,256).split(b'\0')[0].decode('ascii')
            catalog_matches.append((rva,pointer-base,text))
    if len(catalog_matches)!=1 or catalog_matches[0][2]!='can_potentially_call_ally':
        raise ValueError('registered token does not uniquely map to the expected rule')
    row_rva,name_rva,name=catalog_matches[0]
    literals=[]
    for rva,value in [(name_rva,name),(0x4095988,'ally'),(0x44C91B8,'common/scripted_rules')]:
        data=pe.get_data(rva,len(value)+1)
        if data!=value.encode()+b'\0':
            raise ValueError('literal mismatch '+value)
        literals.append({'rva':hex(rva),'text':value,'sha256':hashlib.sha256(data).hexdigest()})
    # Include the exact virtual dispatch bindings used by the loader.
    vtable=pe.get_data(0x44DB020,0x48)
    pointers=list(struct.unpack('<9Q',vtable))
    if pointers[1]!=base+0x33ED7E0 or pointers[7]!=base+0x33EE960:
        raise ValueError('loader vtable differs')
    prior_path=ROOT/'docs/ck3-native-ai/research-plans/war-film-relationship-network-20260923-r2/static.json'
    prior_raw=prior_path.read_bytes()
    prior=json.loads(prior_raw)
    old_sources={source['game_relative_path']:source for source in prior['source_files']}
    game=args.game or args.exe.parent.parent/'game'
    sources=[]
    for rel,start,end in [('common/scripted_rules/00_rules.txt',846,856),('common/scripted_triggers/00_war_and_peace_triggers.txt',166,221)]:
        data=(game/rel).read_bytes()
        digest=hashlib.sha256(data).hexdigest()
        if digest!=old_sources[rel]['sha256']:
            raise ValueError('source differs from frozen default-source identity: '+rel)
        sources.append({'game_relative_path':rel,'bytes':len(data),'sha256':digest,'excerpts':[{'line':i,'text':line} for i,line in enumerate(data.decode('utf-8-sig').splitlines(),1) if start<=i<=end]})
    initial_path=ROOT/'docs/ck3-native-ai/research-plans/war-film-relationship-gate-20260923-r1/plan.json'
    initial_raw=initial_path.read_bytes()
    initial=json.loads(initial_raw)
    if initial['build']['exe_sha256']!=SHA:
        raise ValueError('initial plan identity differs')
    contract={'schema':'xar.war-film-relationship-gate.static.v1','build':'1.19.0.6','exe_sha256':SHA,'exe_bytes':len(raw),'scope':'offline-only','initial_plan_sha256':hashlib.sha256(initial_raw).hexdigest(),'claims':CLAIMS,'unknown':UNKNOWN,'excluded_paths':EXCLUSIONS,'registration':{'index':29,'stride':224,'offset':hex(29*224),'index_instruction_rva':hex(index_rva),'token_instruction_rva':hex(token_rva),'token':hex(token),'catalog_row_rva':hex(row_rva),'catalog_row_bytes_hex':pe.get_data(row_rva,16).hex(),'name_rva':hex(name_rva),'name':name,'candidate_scope_name':'ally','candidate_scope_slot_rva':'0x57eb86c','rules_singleton_slot_rva':'0x57c2060'},'code_blocks':blocks,'literal_anchors':literals,'loader_vtable':{'rva':'0x44db020','bytes_hex':vtable.hex(),'function_rvas':[hex(x-base) for x in pointers]},'source_files':sources,'prior_contract':{'repo_path':prior_path.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(prior_raw).hexdigest()}}
    args.output_dir.mkdir(parents=True,exist_ok=False)
    save(args.output_dir/'static.json',contract)
    digest=hashlib.sha256((args.output_dir/'static.json').read_bytes()).hexdigest()
    result=dict(initial)
    result['nodes']=[{'id':key,'label':label} for key,label in [('name','Rule name and token'),('registration','Native index registration'),('loaded','Loaded rule array'),('scope','root / scope:ally'),('gate','Common eligibility result'),('future','Unobserved runtime behavior')]]
    specs=[('rule-name-registration','name','registration'),('registration-transfer','registration','loaded'),('loaded-rule-to-array','loaded','gate'),('exact-scope-direction','scope','gate'),('authored-gate-boundary','name','gate')]
    result['edges']=[{'id':key,'from':start,'to':end,'label':CLAIMS[key],'status':'static-confirmed','evidence':['static-contract'],'open_question':None} for key,start,end in specs]
    result['edges']+=[{'id':key,'from':'gate','to':'future','label':label,'status':'unknown','evidence':[],'open_question':label} for key,label in UNKNOWN.items()]
    result['evidence']=[{'id':'static-contract','layer':'source-contract','path':'static.json','sha256':digest,'exe_sha256':SHA,'supports':'Exact registration operands, catalog layout and loading instructions, scope binding, and pinned authored text. Static interpretation only; no live success.'}]
    save(args.output_dir/'result-plan.json',result)
    print(json.dumps({'output':str(args.output_dir),'sha256':digest,'registered_name':name,'token':hex(token),'index':29,'static_edges':len(specs),'unknown_edges':len(UNKNOWN),'live_edges':0}))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--plan',type=Path,help='Create a new initial plan without opening the game executable.')
    mode.add_argument('--output-dir',type=Path,help='Create a new frozen static contract and result plan.')
    p.add_argument('--exe',type=Path,default=EXE)
    p.add_argument('--game',type=Path)
    args=p.parse_args()
    if args.plan:
        initial_plan(args.plan)
    else:
        freeze(args)
