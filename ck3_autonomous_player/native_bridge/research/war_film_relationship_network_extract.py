"""Offline exact-build relationship-network research; never opens CK3."""
from pathlib import Path
import argparse
import hashlib
import json

SHA = '2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86'
EXE = Path('C:/SteamLibrary/steamapps/common/CRUSAD~1/binaries/ck3.exe')

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as handle:
        handle.write((json.dumps(value, ensure_ascii=False, indent=2)+'\n').encode())

def plan(path):
    questions = [
        ('containers', 'root', 'candidates', 'Name each source CharacterID container with independent native string/getter/producer anchors.'),
        ('common-filter', 'candidates', 'eligible', 'Resolve common predicate 0x1B35DF0 and actor versus target exclusion branches.'),
        ('contribution', 'eligible', 'sum', 'Prove contribution and deduplication order without claiming future call-to-war acceptance.'),
        ('runtime', 'sum', 'decision', 'No live sample: preserve runtime cache freshness, actual call acceptance and join as unknown.')]
    save(path, {'schema':'xar.native-research-plan.v1','topic':'war-film-relationship-network-20260923',
        'question':'Which relationship sources and filters enter declaration network power at 0x1879850?',
        'purpose':'npc-choice','build':{'version':'1.19.0.6','exe_sha256':SHA},
        'observation':{'mode':'offline-only','actor_kind':'ai','owner_scope':'One declaration assessment actor and effective target; not all diplomacy or wars',
            'identity_kind':'generation-id','identity_lifetime':'Synchronous collector locals and full CharacterID only; no pointer reuse',
            'producer_trigger':'not-applicable','producer':'Native collector 0x1879850','caller':'Declaration assessment 0x1878A00',
            'consumer':'Actor/target strategic power before final ratio','cache_lifetime':'Military+0x308 freshness remains separate; no runtime age observed',
            'expected_signal':'Instruction-backed source container naming and exact filtering differences',
            'zero_sample_meaning':'No live samples are taken; an excluded branch is not proof that the relationship cannot join a war',
            'stop_condition':'Freeze bounded native membership and filtering contract, preserve unsupported names unknown; no live execution','runtime_window_ref':None},
        'evidence':[],'nodes':[{'id':key,'label':label} for key,label in [('root','Actor/effective target'),('candidates','Relationship source members'),('eligible','Eligible unique contributors'),('sum','Network power sum'),('decision','Declaration assessment')]],
        'edges':[{'id':key,'from':source,'to':target,'label':question,'status':'unknown','evidence':[],'open_question':question} for key,source,target,question in questions],
        'cases':[{'id':'future-network-sample','question':'Separately authorized same-revision actor/target contributors and actual joining remain pending.','status':'pending','evidence':[]}]})

def dump(exe, specs, output):
    import pefile
    from capstone import Cs, CS_ARCH_X86, CS_MODE_64
    raw=exe.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=SHA:
        raise ValueError('wrong executable')
    image=pefile.PE(data=raw,fast_load=True)
    decoder=Cs(CS_ARCH_X86,CS_MODE_64)
    base=image.OPTIONAL_HEADER.ImageBase
    output.mkdir(parents=True,exist_ok=False)
    records=[]
    for spec in specs:
        name,begin,end=spec.split(':')
        begin,end=int(begin,0),int(end,0)
        data=image.get_data(begin,end-begin)
        instructions=list(decoder.disasm(data,base+begin))
        if sum(i.size for i in instructions)!=len(data):
            raise ValueError('undecoded span '+name)
        rows=[f'{i.address-base:#x}: {i.mnemonic} {i.op_str}' for i in instructions]
        (output/(name+'.asm.txt')).write_bytes(('\n'.join(rows)+'\n').encode())
        records.append({'id':name,'start_rva':hex(begin),'end_rva_exclusive':hex(end),'bytes_hex':data.hex(),'sha256':hashlib.sha256(data).hexdigest(),'instructions':rows})
    save(output/'extract.json',{'schema':'xar.relationship-network-extract.v1','exe_sha256':SHA,'live':False,'spans':records})
    print(json.dumps({'output':str(output),'spans':len(records)}))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('plan'); p.add_argument('--output',type=Path,required=True)
    p=sub.add_parser('dump'); p.add_argument('--exe',type=Path,default=EXE); p.add_argument('--span',action='append',required=True); p.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.command=='plan': plan(args.output)
    else: dump(args.exe,args.span,args.output)
