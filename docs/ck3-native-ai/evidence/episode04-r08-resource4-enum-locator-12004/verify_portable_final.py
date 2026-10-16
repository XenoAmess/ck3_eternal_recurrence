"""Stdlib portable verification of retained bytes/ledgers; never opens CK3."""
from pathlib import Path
import hashlib,json,struct,sys
H=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).parent
def need(ok,msg):
    if not ok:raise ValueError(msg)
def read(name):return json.loads((H/name).read_bytes())
src=read('SOURCE.final-a01.json')
for p in src['files']:
    b=(H/p['path']).read_bytes()
    need(len(b)==p['bytes'] and hashlib.sha256(b).hexdigest()==p['sha256'],'Pin '+p['path'])
import zipfile
with zipfile.ZipFile(H/src['exact_archive']['path']) as z:
    for p in src['archived_members']:
        b=z.read(p['path']);need(len(b)==p['bytes'] and hashlib.sha256(b).hexdigest()==p['sha256'],'Archived pin '+p['path'])
l=read('LITERALS.actual.json');q=read('QWORD-REFS.actual.json');old=read('NAMED-RIP.actual.json')
c=read('NAMED-RIP-COVERAGE-CORRECTION.actual.json');rip=read('NAMED-RIP.overlap-complete.actual.json');d=read('DATA-QWORD-REFS.actual.json')
for r in (l,q,old,rip,d):
    need(r['machine_id']==src['machine_id'],'Machine')
    need(r['exe_sha256_reused']==src['exe_sha256_reused'],'EXE reused pin')
    need(r['stat_before']==r['stat_after']==l['stat_before'],'Historical observed file identity')
    need(r['whole_EXE_hashes']==0,'Unexpected whole hash')
    need(r['resource4_business_name'] is None and r['paid_military_amount_raw'] is None and r['cadence'] is None,'Unsupported business claim')
need(l['literal_counts']=={'GetCurrency/utf-8':1,'GetCurrency/utf-16-le':0,'barter_goods/utf-8':7,'barter_goods/utf-16-le':0,'government_use_barter_goods/utf-8':0,'government_use_barter_goods/utf-16-le':0},'Literal counts')
for h in l['output_hits']:
    ctx=bytes.fromhex(h['context_hex']);offset=h['literal_rva']-h['context_rva'];pat=bytes.fromhex(h['terminated_pattern_hex'])
    need(len(ctx)==h['context_bytes']<=128 and hashlib.sha256(ctx).hexdigest()==h['context_sha256'],'Literal raw context')
    need(ctx[offset:offset+len(pat)]==pat,'Literal exact bytes')
    need(h['preferred_VA']==l['image_base_preferred']+h['literal_rva'],'Preferred VA')
    need(h['preceding_null_or_section_start']==(offset>0 and ctx[offset-1]==0),'Literal preceding NUL')
need(q['counts']=={'GetCurrency':0,'barter_goods':1} and len(q['rows'])==1,'QWORD counts')
row=q['rows'][0];ctx=bytes.fromhex(row['context_hex']);off=int(row['reference_rva'],16)-int(row['context_rva'],16)
need(hashlib.sha256(ctx).hexdigest()==row['context_sha256'] and len(ctx)==128,'QWORD context')
need(ctx[off:off+8]==row['literal_preferredVA'].to_bytes(8,'little'),'Actual QWORD')
need(int.from_bytes(ctx[off+8:off+16],'little')==0x3e2d,'Adjacent raw token ID')
need(old['total_candidates']==0 and rip['total_candidates']==0 and rip['total_tested_mod00_rm101_opcode_starts']==693550,'RIP reported matcher results')
need(c['new_exe_bytes']==0 and c['synthetic']['old_matching_target_starts']==[],'Correction provenance')
syn=c['synthetic'];raw=bytes.fromhex(syn['bytes_hex']);starts=[]
for pos in range(len(raw)-5):
    if raw[pos] in (0x8b,0x8d) and raw[pos+1] in (5,13,21,29,37,45,53,61):
        if int(syn['section_rva'],16)+pos+6+int.from_bytes(raw[pos+2:pos+6],'little',signed=True)==int(syn['target_rva'],16):starts.append(pos)
need(starts==syn['independent_matching_opcode_starts']==[3],'Synthetic overlap reproduction')
need(d['counts']=={'GetCurrency':0,'barter_goods':0} and d['rows']==[],'Data result')
ledger=l['read_ledger']+q['read_ledger']+old['new_scope_read_ledger']+rip['new_scope_read_ledger']+d['read_ledger']
need(len(ledger)==9 and sum(x['bytes'] for x in ledger)==185104480,'All read ledger')
need(sum(x['bytes'] for x in ledger if x['kind']=='metadata')==608,'Metadata ledger')
need(d['cumulative_sections_bytes']==185103872 and d['cumulative_reads']==9,'Final cumulative ledger')
need(src['all_EXE_read_ledger']==ledger,'Manifest ledger')
for chk in H.glob('CHECK*.actual.json'):
    x=json.loads(chk.read_bytes());results=x.get('results',[x])
    need(all(t['exit_code']==0 for t in results),'Plan check '+chk.name)
print(json.dumps(dict(ok=True,portable=True,exe_access=False,files_verified=len(src['files']),machine_id_of_original_observation=src['machine_id'],sections_read_bytes=185103872,metadata_read_bytes=608,read_calls=9,retained_contexts_verified=len(l['output_hits'])+1,negative_scope='Collector receipts only; whole sections not retained and not re-searched by this verifier',business_mapping_confirmed=False)))
