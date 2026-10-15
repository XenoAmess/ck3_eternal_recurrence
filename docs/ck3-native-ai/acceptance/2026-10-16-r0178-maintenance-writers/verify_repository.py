"""Portable stdlib replay of retained R0178 bytes, not a new game admission."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import zipfile

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[3]
def need(ok,message):
    if not ok:raise ValueError(message)
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
    manifest=json.loads((HERE/'FILE-MANIFEST.json').read_bytes())
    for item in manifest['files']:
        path=(REPO/item['path']).resolve();path.relative_to(REPO)
        b=path.read_bytes();need(len(b)==item['bytes'] and sha(b)==item['sha256'],'Repository file differs: '+item['path'])
    index=json.loads((HERE/'ARCHIVE-INDEX.json').read_bytes())
    archive=HERE/'originals.zip';b=archive.read_bytes()
    need(len(b)==index['archive']['bytes'] and sha(b)==index['archive']['sha256'],'Original archive differs')
    with zipfile.ZipFile(archive) as z:
        expected={x['member']:x for x in index['members']}
        need(len(z.namelist())==len(expected) and set(z.namelist())==set(expected),'Archive members differ')
        for name,item in expected.items():
            need(not name.startswith('/') and '..' not in Path(name).parts,'Unsafe member')
            b=z.read(name);need(len(b)==item['bytes'] and sha(b)==item['sha256'],'Original member differs: '+name)
        receipt=json.loads(z.read('function/READ-RECEIPT.actual.json'))
        f=receipt['function'];body=z.read('function/actual-function.bin')
        need(f['begin_rva']==0x28A63E0 and f['end_exclusive']==0x28A6697 and len(body)==695,'Exact unique function differs')
        need(body.hex()==f['hex'] and sha(body)==f['sha256'],'Function hex differs')
        need(receipt['new_EXE_metadata_bytes']==220 and receipt['new_EXE_read_calls']==20 and receipt['new_EXE_code_bytes']==695,'Source budget facts differ')
        for at,value in [(0x28A640D,'4c8b89c0010000'),(0x28A6450,'498b4118'),(0x28A6454,'498981c0020000'),(0x28A645B,'498b4120'),(0x28A645F,'498981c8020000')]:
            b=bytes.fromhex(value);off=at-f['begin_rva'];need(body[off:off+len(b)]==b,'Proven source bytes differ')
        rows=[json.loads(x) for x in z.read('window/writer.raw.ndjson').splitlines() if x]
        need(dict(Counter(x['kind'] for x in rows))==dict(start=1,arm=110,thread_exited=1,raw_field_write_trap=2,restore=109,terminal=1),'Actual raw counts differ')
        start,terminal=rows[0],rows[-1]
        need(start['CK3_observed'] is True and start['synthetic'] is False and start['pid']==24740 and start['full_id']==31254,'Historical actual identity differs')
        events=[x for x in rows if x['kind']=='raw_field_write_trap']
        for event,offset,post in zip(events,[0x2C0,0x2C8],[0x28A645B,0x28A6466]):
            need(event['offset']==offset and event['RIP_after_rva']==post and event['address']==start['context']+offset and event['same_value_write'] is True,'Actual physical write differs')
            need(event['RIP_after']-start['module_base']==post and event['writer_instruction_start'] is None,'Raw post-PC contract differs')
        arms={x['thread_id']:x for x in rows if x['kind']=='arm'}
        restores={x['thread_id']:x for x in rows if x['kind']=='restore'}
        exited={x['thread_id'] for x in rows if x['kind']=='thread_exited'}
        need(set(restores)|exited==set(arms) and not set(restores)&exited,'Restore lifecycle coverage differs')
        need(all(x['readback'] is True and x['debug']==arms[tid]['saved_debug'] for tid,x in restores.items()),'Restore readback differs')
        need(terminal['restored'] is True and terminal['detached'] is True and terminal['pending_event'] is False and terminal['reason']=='timeout','Actual terminal differs')
        projection=json.loads(z.read('window/WRITERS.actual.json'))
        need(projection['cleanup_proved'] is True and projection['known_producer'] is False and projection['maintenance_attribution']=='unclosed','Actual reader boundary differs')
    print(json.dumps(dict(result='PORTABLE_BYTES_AND_ACTUAL_FACTS_REPLAY_PASS',function_bytes=695,actual_physical_writes=2,maintenance_attribution='unclosed',new_game_admission=False,SDK_or_EXE_actions=0)))
    return 0
if __name__=='__main__':raise SystemExit(main())
