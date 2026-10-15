"""Stdlib integrity/source replay only; no allocator or game is executed."""
from pathlib import Path
import hashlib
import json
import zipfile

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[3]
def need(ok,m):
    if not ok:raise ValueError(m)
def digest(b):return hashlib.sha256(b).hexdigest()
def main():
    manifest=json.loads((HERE/'FILE-MANIFEST.json').read_bytes())
    for item in manifest['files']:
        p=(REPO/item['path']).resolve();p.relative_to(REPO);b=p.read_bytes()
        need(len(b)==item['bytes'] and digest(b)==item['sha256'],'New repository file changed')
    index=json.loads((HERE/'ARCHIVE-INDEX.json').read_bytes())
    archive=HERE/'originals.zip';b=archive.read_bytes()
    need(len(b)==index['archive']['bytes'] and digest(b)==index['archive']['sha256'],'Archive differs')
    with zipfile.ZipFile(archive) as z:
        expected={x['member']:x for x in index['members']}
        need(len(z.namelist())==len(expected) and set(z.namelist())==set(expected),'Archive member set differs')
        for name,item in expected.items():
            need(not name.startswith('/') and '..' not in Path(name).parts,'Unsafe archive member')
            b=z.read(name);need(len(b)==item['bytes'] and digest(b)==item['sha256'],'Original member differs')
        receipt=json.loads(z.read('allocator/READ-RECEIPT.actual.json'));f=receipt['function']
        body=z.read('allocator/actual-function.bin')
        need(f['begin_rva']==0x28A6B50 and f['end_exclusive']==0x28A6D03 and len(body)==435,'Unique allocator extent differs')
        need(body.hex()==f['hex'] and digest(body)==f['sha256']=='207a688234652f7f48cde77604ce85381bc310787c9a3a37c6e4c7be65698a6b','Exact allocator bytes differ')
        need(f['chained_runtime_function'] is None and receipt['new_EXE_metadata_bytes']==220 and receipt['new_EXE_read_calls']==20,'Actual source scope differs')
        need(all(x['kind']=='jmp' and f['begin_rva']<=x['target_rva']<f['end_exclusive'] for x in f['direct_calls_and_jumps']),'Unexpected external direct edge')
        need(body[0x28A6C05-f['begin_rva']:0x28A6C0D-f['begin_rva']]==bytes.fromhex('b8ffffffff488903'),'Zero denominator sentinel bytes differ')
        caller=json.loads(z.read('caller574/SOURCE-CONTRACT.actual.json'))['complete_source']
        c=bytes.fromhex(caller['raw_hex']);need(len(c)==574 and digest(c)==caller['sha256'],'Original574B differs')
        for at in [0x28A6DCA,0x28A6E8E]:
            off=at-0x28A6D10;need(c[off]==0xE8,'Caller is not direct CALL')
            target=at+5+int.from_bytes(c[off+1:off+5],'little',signed=True)
            need(target==0x28A6B50,'Exact caller target differs')
        contract=json.loads(z.read('allocator/SOURCE-CONTRACT.actual.json'))
        need(contract['live_allocator_callback_observed'] is False and contract['maintenance_attribution']=='unclosed' and contract['component_c_semantics'] is None and contract['component_d_semantics'] is None,'Source-only boundary differs')
    print(json.dumps(dict(result='PORTABLE_SOURCE_BYTES_PASS',allocator435=True,caller574=True,new_live_sample=False,maintenance_attribution='unclosed',SDK_or_EXE_actions=0)))
    return 0
if __name__=='__main__':raise SystemExit(main())
