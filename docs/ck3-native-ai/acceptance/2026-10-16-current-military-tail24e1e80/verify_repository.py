"""Portable source/branch replay; no disassembler or live runtime is called."""
from pathlib import Path
import hashlib
import json
import zipfile

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[3]
def need(ok,m):
    if not ok:raise ValueError(m)
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
    for item in json.loads((HERE/'FILE-MANIFEST.json').read_bytes())['files']:
        p=(REPO/item['path']).resolve();p.relative_to(REPO);b=p.read_bytes()
        need(len(b)==item['bytes'] and sha(b)==item['sha256'],'New repository file differs')
    index=json.loads((HERE/'ARCHIVE-INDEX.json').read_bytes());archive=HERE/'originals.zip';b=archive.read_bytes()
    need(len(b)==index['archive']['bytes'] and sha(b)==index['archive']['sha256'],'Archive differs')
    with zipfile.ZipFile(archive) as z:
        expected={x['member']:x for x in index['members']}
        need(len(z.namelist())==len(expected) and set(z.namelist())==set(expected),'Member set differs')
        for name,item in expected.items():
            need(not name.startswith('/') and '..' not in Path(name).parts,'Unsafe archive member')
            b=z.read(name);need(len(b)==item['bytes'] and sha(b)==item['sha256'],'Original member differs')
        receipt=json.loads(z.read('tail/READ-RECEIPT.actual.json'));f=receipt['function'];body=z.read('tail/actual-function.bin')
        need(f['begin_rva']==0x24E1E80 and f['end_exclusive']==0x24E215C and len(body)==732 and body.hex()==f['hex'],'Unique complete source extent differs')
        need(sha(body)==f['sha256']=='32d27096049217575f2d92104d74cb42198bd53f8cbda90a053703e8810f4a05','Source hash differs')
        lines=z.read('tail/actual-function.asm').decode().splitlines();parts=[x.split(maxsplit=2) for x in lines];starts={int(x[0],16) for x in parts}
        need(len(parts)==f['instruction_count']==211 and b''.join(bytes.fromhex(x[1]) for x in parts)==body,'Whole source instruction-byte coverage differs')
        branches=f['branches'];need(len(branches)==17 and len(f['unique_branch_targets'])==11,'Branch count differs')
        for x in branches:
            at=x['at_rva'];ins=bytes.fromhex(x['bytes_hex'])
            need(body[at-f['begin_rva']:at-f['begin_rva']+len(ins)]==ins,'Branch bytes differ')
            if len(ins)==2 and (ins[0]==0xEB or 0x70<=ins[0]<=0x7F):delta=int.from_bytes(ins[-1:],'little',signed=True)
            elif len(ins)==6 and ins[0]==0x0F and 0x80<=ins[1]<=0x8F:delta=int.from_bytes(ins[-4:],'little',signed=True)
            elif len(ins)==5 and ins[0]==0xE9:delta=int.from_bytes(ins[-4:],'little',signed=True)
            else:raise ValueError('Unrecognized original direct branch')
            need(at+len(ins)+delta==x['target_rva'] in starts,'Branch target/boundary differs')
        contract=json.loads(z.read('tail/SOURCE-CONTRACT.actual.json'))
        need({x['at_rva'] for x in contract['all_branches']}=={x['at_rva'] for x in branches},'Semantic branch coverage differs')
        for at,code in [(0x24E2036,'488913'),(0x24E20B9,'48895330'),(0x24E20E7,'48895338'),(0x24E213B,'48894338')]:
            b=bytes.fromhex(code);off=at-f['begin_rva'];need(body[off:off+len(b)]==b,'Explicit output store differs')
        caller=z.read('caller402/actual-function.bin');off=0x28C451A-0x28C43A0
        need(caller[off]==0xE8 and 0x28C451A+5+int.from_bytes(caller[off+1:off+5],'little',signed=True)==0x24E1E80,'Known source call differs')
        need(contract['actual_new_live_sample'] is False and contract['maintenance_attribution']=='unclosed','Source-only business boundary differs')
    print(json.dumps(dict(result='PORTABLE_SOURCE_AND_ALL_BRANCHES_PASS',source732=True,branches17=True,unique_targets11=True,SDK_or_EXE_actions=0,maintenance_attribution='unclosed')))
    return 0
if __name__=='__main__':raise SystemExit(main())
