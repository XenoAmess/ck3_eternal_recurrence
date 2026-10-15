"""Replay the bundled exact .4 split/source contracts without a game EXE.

Paths resolve relative to source-index.json. Captured machine identity belongs
to source provenance and never supplies runtime qualification on another host.
"""
from pathlib import Path
import argparse,hashlib,json

EXE_SHA256='98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518'

def _need(value,message):
    if not value:raise ValueError(message)

def _path(root,relative):
    _need(isinstance(relative,str) and '\\' not in relative,'source path must be portable POSIX relative')
    path=Path(relative)
    _need(not path.is_absolute() and ':' not in relative and '..' not in path.parts,
          'source path escapes bundle')
    resolved=(root/path).resolve()
    _need(resolved.is_relative_to(root.resolve()),'source path resolves outside bundle')
    _need(resolved.is_file() and resolved.stat().st_size<=262144,'source input missing or oversized')
    return resolved

def _sha(raw):return hashlib.sha256(raw).hexdigest()

def _relative_target(address,raw):
    if raw[:1] in (b'\xe8',b'\xe9') and len(raw)==5:
        return address+5+int.from_bytes(raw[1:],'little',signed=True)
    if raw[:1]==b'\xeb' and len(raw)==2 or len(raw)==2 and 0x70<=raw[0]<=0x7f:
        return address+2+int.from_bytes(raw[1:],'little',signed=True)
    if len(raw)==6 and raw[0]==0x0f and 0x80<=raw[1]<=0x8f:
        return address+6+int.from_bytes(raw[2:],'little',signed=True)
    return None

def validate_source_index(index_path: Path):
    index_path=index_path.resolve();index_bytes=index_path.read_bytes()
    _need(len(index_bytes)<=262144,'source index oversized')
    packet=json.loads(index_bytes)
    _need(packet['schema']=='xar.episode04.actual4.split-source.v1','source index schema differs')
    _need(packet['exe_sha256']==EXE_SHA256 and packet['game_version']=='1.20.0.4'
          and packet['steam_build']==25734779,'source exact build differs')
    root=index_path.parent;families={};all_edges=[];instruction_count=0
    for family in packet['families']:
        identity=family['id'];_need(identity not in families,'duplicate source family')
        raw=bytes.fromhex(_path(root,family['raw_hex_path']).read_text(encoding='ascii'))
        _need(_sha(raw)==family['raw_sha256'],'source raw SHA differs: '+identity)
        begin=int(family['begin_rva'],16);end=int(family['end_rva_exclusive'],16)
        _need(begin==int(identity,16) and 0<len(raw)<=16384
              and len(raw)==family['bytes']==end-begin,'source family extent differs')
        ins_bytes=_path(root,family['instructions_path']).read_bytes()
        _need(_sha(ins_bytes)==family['instructions_sha256'],'instruction SHA differs: '+identity)
        instructions=json.loads(ins_bytes)['instructions'];cursor=begin;starts=set();edges=[]
        for ins in instructions:
            address=int(ins['rva'],16);encoded=bytes.fromhex(ins['bytes'])
            _need(address==cursor and 0<len(encoded)<=15,'instruction coverage differs')
            _need(raw[cursor-begin:cursor-begin+len(encoded)]==encoded,'instruction bytes differ from raw')
            starts.add(address);cursor+=len(encoded);target=_relative_target(address,encoded)
            if target is not None:
                edges.append({'caller_rva':hex(address),'target_rva':hex(target),
                              'mnemonic':ins['mnemonic']})
        _need(cursor==end and instructions[-1]['mnemonic'] in ('ret','jmp'),
              'source ordinary body has no captured terminal')
        for edge in edges:
            if edge['mnemonic'].startswith('j'):
                target=int(edge['target_rva'],16)
                # Any unconditional external JMP terminates its own branch;
                # a different branch may occupy later bytes of the same body.
                _need(target in starts or edge['mnemonic']=='jmp',
                      'source branch leaves captured body without a terminal tail: '+identity+' '+str(edge))
        instruction_count+=len(instructions);all_edges.extend(edges)
        families[identity]={'raw':raw,'begin':begin,'instructions':instructions}
    for contract in packet['instruction_contracts']:
        family=families[contract['family']];address=int(contract['rva'],16)
        instruction=next((i for i in family['instructions'] if int(i['rva'],16)==address),None)
        _need(instruction is not None and instruction['bytes']==contract['bytes'],
              'critical instruction contract differs: '+contract['id'])
    return {'status':'STATIC_SOURCE_CONTRACT_REPLAYED','source_machine_id':packet['source_machine_id'],
            'source_index_sha256':_sha(index_bytes),'exact_exe_sha256':EXE_SHA256,
            'families':len(families),'raw_bytes':sum(len(f['raw']) for f in families.values()),
            'instructions':instruction_count,'instruction_contracts':len(packet['instruction_contracts']),
            'relative_call_and_jump_edges':all_edges,'game_EXE_read_or_executed':False,
            'runtime_business_credit':None}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source_index',type=Path,nargs='?',default=Path(__file__).resolve().parents[1]/'docs/ck3-native-ai/evidence/episode04-split-source-12004/source-index.json')
    parser.add_argument('--machine-id',default='unknown',help='Replay host identity; never inferred from source machine')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args();result=validate_source_index(args.source_index)
    result['replay_machine_id']=args.machine_id
    text=json.dumps(result,indent=2)+'\n'
    if args.output:
        with args.output.open('x',encoding='utf-8',newline='\n') as handle:handle.write(text)
    else:print(text,end='')
    return 0

if __name__=='__main__':raise SystemExit(main())
