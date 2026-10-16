"""Stdlib-only replay of the bounded County receiver source archive; no game input."""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import zipfile

def need(ok,message):
    if not ok:
        raise ValueError(message)

def verify(archive,index):
    catalog=json.loads(Path(index).read_bytes())
    rawzip=Path(archive).read_bytes()
    need(len(rawzip)==catalog['archive']['bytes'] and hashlib.sha256(rawzip).hexdigest()==catalog['archive']['sha256'],'Archive exact pin')
    with zipfile.ZipFile(archive) as z:
        need(z.testzip() is None,'ZIP CRC')
        need(set(z.namelist())=={x['member'] for x in catalog['members']},'Archive member set')
        content={}
        for item in catalog['members']:
            b=z.read(item['member'])
            need(len(b)==item['bytes'] and hashlib.sha256(b).hexdigest()==item['sha256'],'Member exact pin: '+item['member'])
            content[item['member']]=b
    raw=content['actual-function.bin']
    fun=json.loads(content['FUNCTION.actual-a01.json'])
    con=json.loads(content['SOURCE-CONTRACT.actual-a03.json'])
    begin=int(fun['begin_rva'],16);end=int(fun['end_exclusive'],16)
    need(begin==0x24D4ED0 and end==0x24D4F90 and len(raw)==192,'Unique authorized extent')
    need(hashlib.sha256(raw).hexdigest()==fun['sha256']==con['source']['raw_sha256'],'Source raw SHA')
    need(fun['chained_runtime_function'] is None,'No chained function')
    cursor=begin;starts=set();by_pc={}
    for pc,hx,mnemonic,operands in fun['instructions']:
        pc=int(pc,16);b=bytes.fromhex(hx)
        need(pc==cursor and raw[pc-begin:pc-begin+len(b)]==b,'Contiguous instruction/raw mapping')
        starts.add(pc);by_pc[pc]=(b,mnemonic,operands);cursor+=len(b)
    need(cursor==end and len(starts)==49,'Complete49 instructions')
    branches=fun['branches'];contracts={int(x['at_rva'],16):x for x in con['branch_contracts']}
    need(len(branches)==len(contracts)==12,'All12 branches contracted')
    for row in branches:
        pc=int(row['at_rva'],16);b=bytes.fromhex(row['hex'])
        need(row['direct'] is True and row['internal'] is True,'This complete body has only local jumps')
        displacement=struct.unpack('<b',b[-1:])[0] if len(b)==2 else struct.unpack('<i',b[-4:])[0]
        target=pc+len(b)+displacement
        need(target==int(row['target_rva'],16) and target in starts,'Exact relative jump/boundary')
        need(pc in contracts and contracts[pc]['contract'],'Branch semantic coverage')
    calls=fun['calls_unexpanded']
    need(len(calls)==1 and calls[0]['at_rva']=='0x24d4efd' and calls[0]['target_rva']=='0x24d4d20','Unique external callee remains unexpanded')
    b=by_pc[0x24D4EFD][0]
    need(b[0]==0xE8 and 0x24D4EFD+5+struct.unpack('<i',b[1:])[0]==0x24D4D20,'Exact CALL rel32')
    # The archived131B wrapper establishes the real explicit input/forward edge.
    wrapper=content['wrapper-2C09DF0.bin'];off=0x2C09E53-0x2C09DF0
    cb=wrapper[off:off+5]
    need(len(wrapper)==131 and cb[0]==0xE8 and 0x2C09E53+5+struct.unpack('<i',cb[1:])[0]==begin,'Actual wrapper CALL')
    need(con['county_848_direct_access'] is False and con['holder_or_enemy_semantics_closed'] is False,'Do not fabricate business identity')
    need(con['new_callee_reads']==0 and con['runtime_observed'] is False,'Static scope only')
    receipt=json.loads(content['READ-RECEIPT.actual-a01.json'])
    journal=[json.loads(line) for line in content['RAW-READ-ATTEMPTS.actual.ndjson'].splitlines()]
    need(len(journal)==receipt['new_EXE_read_calls']==21,'Persisted read count')
    need(sum(x['actual_bytes'] for x in journal if x['kind']=='metadata')==224,'Actual224 metadata bytes')
    need(sum(x['actual_bytes'] for x in journal if x['kind']=='code')==192,'Actual192 code bytes')
    need(all(x['requested_bytes']==x['actual_bytes']==len(bytes.fromhex(x['hex'])) for x in journal),'All actual read bytes retained')
    need(next(bytes.fromhex(x['hex']) for x in journal if x['kind']=='code')==raw,'Journal code exact bytes')
    return dict(status='PASS',code_bytes=192,metadata_bytes=224,read_calls=21,instructions=49,unique_branches=12,unexpanded_callees=['24D4D20'],archive_members=len(content),runtime_observed=False)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive',type=Path,required=True);p.add_argument('--index',type=Path,required=True)
    a=p.parse_args();print(json.dumps(verify(a.archive,a.index),separators=(',',':')))
