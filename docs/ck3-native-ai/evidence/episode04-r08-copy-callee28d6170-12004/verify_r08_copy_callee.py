"""Stdlib frozen copy-callee source verification; never reads game files."""
from pathlib import Path
from io import BytesIO
import argparse, base64, hashlib, json, re, struct, zipfile, zlib

MEMBER='docs/ck3-native-ai/evidence/episode04-r08-copy-callee28d6170-12004/portable-source-a07.json'
def need(ok,message):
    if not ok:raise ValueError(message)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def pin(raw,row,label):
    need(len(raw)==row['bytes'] and sha(raw)==row['sha256'],'Pin differs: '+label)
def load(path):
    p=Path(path)
    if p.suffix=='.patch':
        parts=[s for s in p.read_text(encoding='utf-8').split('diff --git ')[1:] if '+++ b/'+MEMBER in s.splitlines()]
        need(len(parts)==1 and 'new file mode 100644\n'in parts[0],'Complete new-file bundle required')
        raw=''.join(l[1:]for l in parts[0].splitlines(keepends=True)if l.startswith('+')and not l.startswith('+++')).encode()
    else:raw=p.read_bytes()
    return json.loads(raw)
def original(row):
    need(row['encoding']=='zlib+base85','Encoding differs')
    raw=zlib.decompress(base64.b85decode(row['payload']));pin(raw,row,row['id']);return raw
def archive(raw):
    with zipfile.ZipFile(BytesIO(raw))as z:
        names=z.namelist();need(len(names)==len(set(names)),'Duplicate ZIP member');need(z.testzip()is None,'ZIP CRC')
        return {n:z.read(n)for n in names}
def verify(path):
    b=load(path);need(b['schema']=='xar.e04.r08.copy-callee.portable-a07.v1','Schema differs')
    orig={r['id']:original(r)for r in b['originals']};need(len(orig)==len(b['originals']),'Duplicate originals')
    index=json.loads(orig['PORTABLE-INDEX.json']);source=json.loads(orig['SOURCE.actual.json']);correction=json.loads(orig['ROOT-DELIVERY.actual-a02.json'])
    for row in index['files']:pin(orig[row['path']],row,row['path'])
    prior=json.loads(orig['ROOT-DELIVERY.actual.json'])
    need(sha(orig['ROOT-DELIVERY.actual.json'])==correction['prior_receipt_sha256'],'Copyplan correction prior differs')
    need(set(correction['omitted_paths'])=={'ROOT-DELIVERY.actual.json','archive_source.py','seal.py'} and correction['required_index_inputs_covered'] is True,'Omitted dependency correction missing')
    need({r['source']for r in correction['copy_plan']} <= set(orig),'Final copyplan input absent')
    for key in ('source','knowledge','archive','portable_index','portable_verification'):
        row=prior[key];pin(orig[row['path']],row,row['path'])
    pin(orig['source-originals.zip'],source['raw_archive'],'Source archive')
    pin(orig['known-caller-originals.zip'],source['retained_caller_archive'],'Caller archive')
    image='98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518'
    need(source['machine_id']==index['machine_id']==correction['machine_id']==b['source_machine_id'],'Source machine differs')
    need(source['exe_sha256']==b['image']['sha256']==image,'Exact image differs')
    src=archive(orig['source-originals.zip']);caller_arc=archive(orig['known-caller-originals.zip'])
    originals_index=json.loads(orig['ORIGINALS-INDEX.actual.json']);pin(orig['source-originals.zip'],dict(bytes=originals_index['archive_bytes'],sha256=originals_index['archive_sha256']),'Archive originals index')
    need(set(src)=={r['path']for r in originals_index['members']},'Source member set differs')
    for row in originals_index['members']:pin(src[row['path']],row,row['path'])
    prior_index=json.loads(orig['d05-R0178-ARCHIVE-INDEX.json'])
    member_pins={r['member']:r for r in prior_index['members']}
    need(set(caller_arc)==set(b['caller_member_map']),'Caller member set differs')
    for local,old in b['caller_member_map'].items():pin(caller_arc[local],member_pins[old],old)
    raw=src['function.bin'];detail=json.loads(src['details.json']);cap=json.loads(src['CAPTURE.actual.json'])
    reads=[json.loads(s)for s in src['READS.actual.ndjson'].splitlines()if s.strip()]
    need(len(raw)==625 and sha(raw)==source['body_sha256']==cap['body_sha256'],'625B source differs')
    need(cap['machine_id']==b['source_machine_id']and cap['exe_sha256']==image and cap['stat_before']==cap['stat_after']and cap['error']is None,'Capture identity/stability differs')
    need(cap['full_per_read_ledger_durable'] is True and cap['new_code_bytes']==625 and cap['new_metadata_bytes']==220 and cap['read_calls']==20,'Durable bounded capture differs')
    need(len(reads)==20 and sum(r['actual_bytes']for r in reads if r['kind']=='metadata')==220 and sum(r['actual_bytes']for r in reads if r['kind']=='code')==625,'Actual ledger totals differ')
    for row in reads:
        if row['kind']=='metadata':need(len(bytes.fromhex(row['hex']))==row['actual_bytes']and sha(bytes.fromhex(row['hex']))==row['sha256'],'Ledger exact metadata differs')
    need(detail['extent']==cap['extent']==source['extent'],'Extent differs')
    need(source['extent']['unwind_flags']==0 and source['extent']['bytes']==625,'Normal unchained extent differs')
    begin=0x28D6170;cursor=begin;starts=set();jumps=[];calls=[]
    for row in detail['instructions']:
        pos=int(row['rva'],16);chunk=bytes.fromhex(row['bytes']);need(pos==cursor and raw[pos-begin:pos-begin+len(chunk)]==chunk,'Saved instruction coverage differs')
        starts.add(pos);cursor+=len(chunk)
        if row['mnemonic']=='call':
            need(chunk[:1]==b'\xe8'and len(chunk)==5,'Direct CALL shape differs');target=pos+5+struct.unpack('<i',chunk[1:])[0];need(target==int(row['operands'],16),'CALL target differs');calls.append((pos,target))
        if row['mnemonic'].startswith('j'):
            if len(chunk)==2 and (chunk[0]==0xeb or 0x70<=chunk[0]<=0x7f):disp=int.from_bytes(chunk[1:],'little',signed=True)
            elif len(chunk)==6 and chunk[0]==0x0f and 0x80<=chunk[1]<=0x8f:disp=int.from_bytes(chunk[2:],'little',signed=True)
            else:raise ValueError('Unsupported source branch')
            target=pos+len(chunk)+disp;need(target==int(row['operands'],16),'Branch literal target differs');jumps.append(target)
    need(cursor==0x28D63E1 and len(starts)==183 and len(jumps)==34 and all(t in starts for t in jumps),'Complete ordinary CFG differs')
    need(calls==[(0x28D6259,0x2A500F0),(0x28D634E,0x2A500F0),(0x28D63C1,0x4226860)],'Opaque CALL targets differ')
    need([int(r['rva'],16)for r in detail['instructions']if r['mnemonic']=='ret']==[0x28D63E0],'Sole RET differs')
    for pos,hx in {0x28D636A:'42890431',0x28D63C6:'41295e0c'}.items():
        chunk=bytes.fromhex(hx);need(raw[pos-begin:pos-begin+len(chunk)]==chunk,'Own-body fixed store differs')
    caller=caller_arc['caller.bin'];need(len(caller)==695 and sha(caller)=='ffebf7d960edb76b71d2456b7f8722cc09092952b41c565f648410b42a47dede','Held caller695 differs')
    at=0x28A6535;chunk=caller[at-0x28A63E0:at-0x28A63E0+5]
    need(chunk.hex()=='e836fc0200'and at+5+int.from_bytes(chunk[1:],'little',signed=True)==begin,'Actual source CALL differs')
    receipt=json.loads(caller_arc['original-source-receipt.json']);need(bytes.fromhex(receipt['function']['hex'])==caller and receipt['qualified_EXE_SHA_reused_not_rehashed']==image and receipt['machine_id']==b['source_machine_id'],'Historical caller identity differs')
    need(source['direct_fixed_context_28_30_or_wallet_store']is False and source['transitive_or_dynamic_alias_effects_excluded']is False,'Ownbody versus transitive scope differs')
    need(source['unexpanded_helpers']==['2A500F0','4226860']and source['military_c_d_producer']=='unknown'and source['payer']=='unknown','Unknown dependency scope elevated')
    need(b['new_live_credit']==0 and b['business']['maintenance_attribution']=='unclosed'and all(b['business'][k]is None for k in ('paid_military_amount_raw','cadence','currency')),'Business credit elevated')
    return dict(status='PASS',scope='exact frozen bytes and declared source edges; not semantic/live proof',source_machine_id=b['source_machine_id'],original_files_verified=len(orig),body_bytes=625,instructions=183,internal_branches=34,opaque_calls=3,durable_metadata_bytes=220,source_read_calls=20,caller_bytes=695,canonical_R0178_members_compared=4,incoming_source_CALL=True,copyplan_correction_preserved=True,semantic_correctness_verified=False,live_execution_performed=False,new_EXE_reads=0,new_live_credit=0,maintenance_attribution='unclosed',paid_military_amount_raw=None,cadence=None)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bundle',type=Path,default=Path(__file__).with_name('portable-source-a07.json'));p.add_argument('--extract-originals',type=Path);a=p.parse_args();result=verify(a.bundle)
    if a.extract_originals:
        need(not a.extract_originals.exists(),'Exclusive new extraction directory required');a.extract_originals.mkdir(parents=True,exist_ok=False)
        for row in load(a.bundle)['originals']:
            need(re.fullmatch(r'[A-Za-z0-9_.-]+',row['id'])is not None,'Unsafe original name')
            with(a.extract_originals/row['id']).open('xb')as f:f.write(original(row))
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))
if __name__=='__main__':main()
