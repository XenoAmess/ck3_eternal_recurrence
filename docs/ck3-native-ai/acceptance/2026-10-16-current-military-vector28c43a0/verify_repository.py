"""Portable bytes and bounded source facts only; no CK3/capstone required."""
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
        need(len(b)==item['bytes'] and sha(b)==item['sha256'],'New file differs')
    index=json.loads((HERE/'ARCHIVE-INDEX.json').read_bytes());archive=HERE/'originals.zip';b=archive.read_bytes()
    need(len(b)==index['archive']['bytes'] and sha(b)==index['archive']['sha256'],'Archive differs')
    with zipfile.ZipFile(archive) as z:
        expected={x['member']:x for x in index['members']}
        need(len(z.namelist())==len(expected) and set(z.namelist())==set(expected),'Member set differs')
        for name,item in expected.items():
            need(not name.startswith('/') and '..' not in Path(name).parts,'Unsafe member')
            b=z.read(name);need(len(b)==item['bytes'] and sha(b)==item['sha256'],'Member differs')
        receipt=json.loads(z.read('source/READ-RECEIPT.actual.json'));f=receipt['function'];body=z.read('source/actual-function.bin')
        need(f['begin_rva']==0x28C43A0 and f['end_exclusive']==0x28C4532 and len(body)==402 and body.hex()==f['hex'],'Complete sole source extent differs')
        need(sha(body)==f['sha256']=='47a076981a8f92c4ae53c2da28c81b44a8ed90ffca55b593dfa17108c97a9a81','Source hash differs')
        need(receipt['new_EXE_metadata_bytes']==220 and receipt['new_EXE_read_calls']==20 and f['chained_runtime_function'] is None,'Bounded metadata facts differ')
        caller=z.read('caller/current_military.bin');off=0x2C141D7-0x2C13F60
        need(caller[off]==0xE8 and 0x2C141D7+5+int.from_bytes(caller[off+1:off+5],'little',signed=True)==0x28C43A0,'Held caller edge differs')
        at=0x28C451A;off=at-0x28C43A0
        need(body[off]==0xE8 and at+5+int.from_bytes(body[off+1:off+5],'little',signed=True)==0x24E1E80,'Only tail call edge differs')
        need(json.loads(z.read('failed-a01/FAILED-PREPARE.actual.json'))['new_EXE_bytes']==0,'Preparation failure boundary differs')
    print(json.dumps(dict(result='PORTABLE_SOURCE_FACTS_PASS',source402=True,currentrate_caller_edge=True,new_live_observation=False,maintenance_attribution='unclosed',SDK_or_EXE_actions=0)))
    return 0
if __name__=='__main__':raise SystemExit(main())
