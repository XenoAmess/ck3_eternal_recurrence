"""Verify retained R08 descriptor-chain bytes and joins; no EXE or runtime access."""
from pathlib import Path
from io import BytesIO
import argparse,base64,hashlib,json,re,zipfile,zlib
def need(ok,message):
 if not ok:raise ValueError(message)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def original(row):
 need(row['encoding']in('base64','zlib+base64'),'unknown encoding')
 raw=base64.b64decode(row['payload'],validate=True)
 if row['encoding']=='zlib+base64':raw=zlib.decompress(raw)
 need(len(raw)==row['bytes']and sha(raw)==row['sha256'],'original pin changed '+row['id']);return raw
def relative(pc,raw):
 if raw[0]in(0xe8,0xe9,0xeb)or 0x70<=raw[0]<=0x7f:return pc+len(raw)+int.from_bytes(raw[1:],'little',signed=True)
 if raw[:1]==b'\x0f'and 0x80<=raw[1]<=0x8f:return pc+len(raw)+int.from_bytes(raw[2:],'little',signed=True)
 raise ValueError('not a supported relative edge')
def decode_asm(text,begin,raw):
 rows={};cursor=begin
 for line in text.splitlines():
  m=re.fullmatch(r'([0-9A-Fa-f]+) ([0-9A-Fa-f]+) (\S+)(?: (.*))?',line);need(m is not None,'malformed saved ASM')
  pc=int(m[1],16);code=bytes.fromhex(m[2]);need(pc==cursor and raw[pc-begin:pc-begin+len(code)]==code,'saved instruction coverage differs')
  rows[pc]=(code,m[3]);cursor+=len(code)
 need(cursor==begin+len(raw),'incomplete saved ASM');return rows
def verify(bundle_path,prior_dir):
 b=json.loads(Path(bundle_path).read_bytes());orig={v['id']:original(v)for v in b['originals']};records={v['id']:json.loads(orig[v['id']])for v in b['originals']if v['kind']=='json'}
 need(len(orig)==15,'new original set differs');need(all(v['machine_id']==b['source_machine_id']for v in records.values()),'source machine mismatch')
 image='98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518';need(b['image']['sha256']==image,'image mismatch')
 parents={}
 for row in b['parents']:
  need(row['path']in('sources.json','scalar-leaves-a02.json'),'parent path outside fixed evidence scope')
  raw=(Path(prior_dir)/row['path']).read_bytes();need(len(raw)==row['bytes']and sha(raw)==row['sha256'],'parent data pin changed');parents[row['path']]=json.loads(raw)
 need(len(parents)==2,'parent data set differs');need(parents['sources.json']['image']['sha256']==image,'parent image mismatch')
 all_rows={};counts={}
 for key,begin,nbytes,nins,njump,ncall in [('second',0x2BD2DE0,665,173,17,11),('third',0x2BD3080,665,173,17,11),('shared',0x2BC76C0,1670,364,25,26),('worker',0x2BD5530,781,189,20,18),('convert',0x2BD47E0,420,121,11,6)]:
  source=records[key+'-source'];need((source.get('image')or{}).get('sha256',source.get('image_sha256'))==image,'leaf image mismatch')
  archive=orig[key+'-archive'];need(sha(archive)==source['source_archive_sha256'],'leaf archive mismatch')
  with zipfile.ZipFile(BytesIO(archive))as z:
   if key=='convert':
    detail=json.loads(z.read('continuation-details.json'));parts=[]
    need(len(detail['physical_spans'])==3,'logical source fragment count differs')
    for span in detail['physical_spans']:
     raw=z.read(span['begin']+'-'+span['end']+'.bin');need(len(raw)==span['bytes']and sha(raw)==span['sha256'],'fragment bytes differ');parts.append(raw)
    body=b''.join(parts);asm=z.read('logical-source.asm').decode();controls=detail['controls'];jumps=[e for e in controls if e['mnemonic'].startswith('j')];calls=[e for e in controls if e['mnemonic']=='call']
    need(detail['unresolved_frontier']==[]and detail['normal_ret_sites']==['2BD4983'],'logical frontier or RET changed')
   else:
    body=z.read('function.bin');asm=z.read('function.asm').decode();detail=json.loads(z.read('source-details.json'if key in('second','shared')else'metadata.json'));jumps=detail.get('jumps',detail.get('direct_branches'));calls=detail.get('calls',detail.get('direct_calls'))
  visible=b['source_bytes'][key];need(body.hex()==visible['hex']and len(body)==visible['bytes']==nbytes and sha(body)==visible['sha256'],'visible full source differs')
  function=source['logical_function']if key=='convert'else source['function'];need(function['bytes']==nbytes and function['sha256']==sha(body),'source raw pin differs')
  rows=decode_asm(asm,begin,body);need(len(rows)==nins and len(jumps)==njump and len(calls)==ncall,'instruction/control counts differ')
  need({pc for pc,(_,mn)in rows.items()if mn.startswith('j')}=={int(e['rva'],16)for e in jumps},'jump inventory differs')
  need({pc for pc,(_,mn)in rows.items()if mn=='call'}=={int(e['rva'],16)for e in calls},'call inventory differs')
  indirect=0
  for edge in jumps+calls:
   pc=int(edge['rva'],16);code=bytes.fromhex(edge['raw']if 'raw'in edge else edge['bytes']);need(rows[pc][0]==code,'edge raw changed')
   if code[:1]==b'\xff':need(edge['target']is None or str(edge['target']).startswith('qword ptr'),'indirect target relabelled');indirect+=1
   else:need(relative(pc,code)==int(edge['target'],16),'relative target differs')
  groups=source.get('branch_groups')
  if groups:
   grouped=[int(pc,16)for group in(groups.values()if isinstance(groups,dict)else[g['rvas']for g in groups])for pc in group]
   need(len(grouped)==len(set(grouped))==njump and set(grouped)=={int(e['rva'],16)for e in jumps},'branch group partition differs')
  all_rows[key]=rows;counts[key]=dict(bytes=nbytes,instructions=nins,branches=njump,calls=ncall,indirect_targets_unresolved=indirect)
 for key in('third','worker'):need(records[key+'-semantics']['source_record_sha256']==sha(orig[key+'-source']),'semantics source pin differs')
 old=records['convert-initial-read'];cont=records['convert-continuation-read'];conversion=records['convert-source'];newbody=bytes.fromhex(b['source_bytes']['convert']['hex'])
 need(old['status']=='FULL_SOLE_UNCHAINED_FUNCTION_CAPTURED'and old['bytes']==155 and cont['cumulative_code_bytes']==420,'historical physical/logical correction missing')
 need(conversion['physical_fragments']==[['2BD47E0','2BD487B',155],['2BD487B','2BD496B',240],['2BD496B','2BD4984',25]]and bool(conversion['first_receipt_correction']),'logical three-span correction differs')
 need(sha(orig['convert-initial-archive'])==old['source_archive_sha256']and sha(orig['convert-archive'])==cont['source_archive_sha256'],'historical archive pin differs')
 with zipfile.ZipFile(BytesIO(orig['convert-initial-archive']))as z:need(z.read('function.bin')==newbody[:155]and sha(z.read('function.bin'))==old['raw_sha256'],'retained initial physical bytes differ')
 parent_body=bytes.fromhex(parents['sources.json']['source_bytes']['scalar_2BD3320']['hex'])
 for pc,dest in((0x2BD35B6,0x2BD2DE0),(0x2BD35C9,0x2BD3080)):
  raw=parent_body[pc-0x2BD3320:pc-0x2BD3320+5];need(raw[:1]==b'\xe8'and relative(pc,raw)==dest,'parent addend join differs')
 for key,pc,dest in(('second',0x2BD2EF3,0x2BC76C0),('third',0x2BD3193,0x2BC76C0),('shared',0x2BC778D,0x2BD47E0),('shared',0x2BC7958,0x2BD5370),('shared',0x2BC7C5A,0x2BD5530),('worker',0x2BD5820,0x2BD58E0)):
  raw=all_rows[key][pc][0];need(raw[:1]==b'\xe8'and relative(pc,raw)==dest,'new inter-leaf join differs')
 need(b['business']['maintenance_attribution']=='unclosed'and b['business']['paid_military_amount_raw']is None and b['business']['cadence']is None and b['new_live_credit']==0,'unclosed business scope differs')
 return dict(status='PASS',scope='five-leaf saved-byte, instruction/control inventory, historical correction and inter-leaf join integrity only',functions=counts,source_bytes=4201,originals_verified=len(orig),inter_leaf_call_joins_verified=8,logical_conversion=dict(bytes=420,physical_fragments=[155,240,25],historical155_FULL_scope='physical .pdata span only'),semantic_correctness_verified=False,live_execution_performed=False,source_machine_id=b['source_machine_id'],paid_military_amount_raw=None,cadence=None,new_live_credit=0)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bundle',type=Path,default=Path(__file__).with_name('descriptor-chain-a03.json'));p.add_argument('--prior-dir',type=Path,default=Path(__file__).parent);p.add_argument('--extract-originals',type=Path);a=p.parse_args();result=verify(a.bundle,a.prior_dir)
 if a.extract_originals:
  need(not a.extract_originals.exists(),'exclusive new extraction directory required');a.extract_originals.mkdir(parents=True,exist_ok=False)
  for row in json.loads(a.bundle.read_bytes())['originals']:
   need(re.fullmatch(r'[a-z0-9-]+',row['id'])is not None,'unsafe original ID');suffix='.zip'if row['kind']=='zip'else'.json'
   with(a.extract_originals/(row['id']+suffix)).open('xb')as f:f.write(original(row))
 print(json.dumps(result,ensure_ascii=False,sort_keys=True))
if __name__=='__main__':main()
