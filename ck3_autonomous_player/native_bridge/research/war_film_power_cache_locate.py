"""Offline exact-build member-write locator. Candidates still require owner tracing."""
from pathlib import Path
import argparse
from bisect import bisect_right
import hashlib
import json
import struct

SHA = '2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86'


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as out:
        out.write((json.dumps(value, ensure_ascii=False, indent=2)+'\n').encode())


def plan(path):
    value = {'schema':'xar.native-research-plan.v1', 'topic':'war-film-power-cache-20260923',
        'question':'Which native producer writes military extension+0x308, and how does its quantity/power and ally/special composition differ from +0x2F0/+0x2F4?',
        'purpose':'npc-choice', 'build':{'version':'1.19.0.6','exe_sha256':SHA},
        'observation':{'mode':'offline-only','actor_kind':'ai','owner_scope':'one actor military extension and declaration assessment; no claim for all wars',
            'identity_kind':'generation-id','identity_lifetime':'future same actor full ID and same producer revision; no raw pointer reuse',
            'producer_trigger':'daily-tick','producer':'unknown writer of military extension+0x308',
            'caller':'unknown update owner/cadence','consumer':'State16 builder 0x18784D0 and network/target declaration assessment',
            'cache_lifetime':'unknown until producer is traced; paused reader must not imply refresh',
            'expected_signal':'offline write chain and component source slots, then separately authorized future same-actor observations',
            'zero_sample_meaning':'not observed or not updated; does not prove a component is excluded',
            'stop_condition':'offline only; freeze one closed producer chain and preserve remaining unknowns; no CK3 execution',
            'runtime_window_ref':None},
        'evidence':[],
        'nodes':[{'id':n,'label':label} for n,label in [('producer','Native military producer'),('cache','military+0x308'),('counts','current/max +0x2F0/+0x2F4'),('special','Special troop and ally sources'),('decision','Actor declaration assessment')]],
        'edges':[{'id':key,'from':source,'to':dest,'label':question,'status':'unknown','evidence':[],'open_question':question} for key,source,dest,question in [
            ('write-chain','producer','cache','Locate exact write and prove Character military owner; do not accept arbitrary +0x308 stores.'),
            ('count-distinction','producer','counts','Trace sibling count writes and units, including current/max modes.'),
            ('composition','special','cache','Trace the actually accumulated source slots; separate direct troops from later relationship-network additions.'),
            ('freshness','cache','decision','Name producer caller/update order without inferring cadence from consumer.')]],
        'cases':[{'id':'same-actor-observation','question':'Future native same-revision current/max/power components and caches, with full actor identity and no external recomputation substituted.','status':'pending','evidence':[]}]
    }
    save(path,value)


def locate(exe, offsets, output):
    import pefile
    import capstone
    from capstone.x86 import X86_OP_MEM
    raw = exe.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SHA:
        raise ValueError('wrong executable build')
    pe = pefile.PE(data=raw,fast_load=True)
    pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_EXCEPTION']])
    funcs=sorted((e.struct.BeginAddress,e.struct.EndAddress) for e in pe.DIRECTORY_ENTRY_EXCEPTION)
    starts=[start for start,end in funcs]
    dis=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64)
    dis.detail=True
    cache={}
    rows={}
    for section in pe.sections:
        if not section.IMAGE_SCN_MEM_EXECUTE:
            continue
        data=section.get_data()
        for offset in offsets:
            needle=struct.pack('<I',offset)
            pos=0
            while (pos:=data.find(needle,pos))>=0:
                for back in range(1,12):
                    begin=pos-back
                    if begin<0:
                        continue
                    rva=section.VirtualAddress+begin
                    j=bisect_right(starts,rva)-1
                    func=funcs[j] if j>=0 and rva<funcs[j][1] else None
                    if func is None:
                        continue
                    if func not in cache:
                        block=pe.get_data(func[0],func[1]-func[0])
                        cache[func]={i.address:i for i in dis.disasm(block,func[0])}
                    ins=cache[func].get(rva)
                    if ins is None or not (begin<=pos and begin+ins.size>=pos+4):
                        continue
                    for operand in ins.operands:
                        if operand.type==X86_OP_MEM and operand.mem.disp==offset and operand.access & capstone.CS_AC_WRITE:
                            rows[rva]={'rva':hex(rva),'member_offset':hex(offset),'bytes':ins.bytes.hex(),
                                'instruction':ins.mnemonic+' '+ins.op_str,'function':[hex(x) for x in func]}
                pos+=1
    result={'schema':'xar.member-write-locator.v1','exe_sha256':SHA,'live':False,
            'boundary':'.pdata instruction-aligned explicit memory writes with disp32 equal to requested offsets; not exhaustive for aliases, bulk copy or computed addresses; owner still unproven',
            'offsets':[hex(x) for x in offsets],'writes':[rows[key] for key in sorted(rows)]}
    save(output,result)
    print(json.dumps({'output':str(output),'writes':len(rows),'functions_decoded':len(cache)}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    pp=sub.add_parser('plan')
    pp.add_argument('--output',required=True,type=Path)
    lp=sub.add_parser('scan-writes')
    lp.add_argument('--exe',type=Path,default=Path('C:/SteamLibrary/steamapps/common/CRUSAD~1/binaries/ck3.exe'))
    lp.add_argument('--offsets',type=lambda x:int(x,0),nargs='+',default=[0x308,0x2F0,0x2F4])
    lp.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    if args.command=='plan':
        plan(args.output)
    else:
        locate(args.exe,args.offsets,args.output)
