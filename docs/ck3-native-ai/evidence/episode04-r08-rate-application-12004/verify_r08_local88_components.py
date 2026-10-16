"""Portable saved-source verification of four local88 components; no runtime access."""
from pathlib import Path
from io import BytesIO
import argparse,base64,hashlib,json,re,struct,zipfile,zlib
def need(ok,msg):
 if not ok:raise ValueError(msg)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def load(path,member):
 p=Path(path)
 if p.suffix=='.patch':
  matches=[s for s in p.read_text(encoding='utf-8').split('diff --git ')[1:]if any(l.startswith('+++ b/')and l.rstrip().endswith('/'+member)for l in s.splitlines())]
  need(len(matches)==1 and 'new file mode 100644\n'in matches[0],'complete new-file JSON required');raw=''.join(l[1:]for l in matches[0].splitlines(keepends=True)if l.startswith('+')and not l.startswith('+++')).encode()
 else:raw=p.read_bytes()
 return raw,json.loads(raw)
def original(row):
 need(row['encoding']in('base64','zlib+base64'),'unknown encoding');raw=base64.b64decode(row['payload'],validate=True)
 if row['encoding']=='zlib+base64':raw=zlib.decompress(raw)
 need(len(raw)==row['bytes']and sha(raw)==row['sha256'],'original pin differs '+row['id']);return raw
def relative(pc,raw):
 if raw[0]in(0xe8,0xe9,0xeb)or 0x70<=raw[0]<=0x7f:return pc+len(raw)+int.from_bytes(raw[1:],'little',signed=True)
 if raw[:1]==b'\x0f'and 0x80<=raw[1]<=0x8f:return pc+len(raw)+int.from_bytes(raw[2:],'little',signed=True)
 raise ValueError('unsupported relative edge')
def asm_rows(text,begin,body):
 rows={};cursor=begin
 for line in text.splitlines():
  pieces=line.split(maxsplit=3);need(len(pieces)>=3,'malformed ASM');pc=int(pieces[0],16);raw=bytes.fromhex(pieces[1]);need(pc==cursor and body[pc-begin:pc-begin+len(raw)]==raw,'ASM bytes/coverage differ');rows[pc]=(raw,pieces[2]);cursor+=len(raw)
 need(cursor==begin+len(body),'ASM source coverage differs');return rows
def graph(rows,tables=None):
 tables=tables or{};edges={}
 for pc,(raw,mn)in rows.items():
  if mn.startswith('ret')or mn in('int3','ud2'):targets=[]
  elif pc in tables:targets=tables[pc]
  elif mn=='jmp':targets=[relative(pc,raw)]
  elif mn.startswith('j'):targets=[relative(pc,raw),pc+len(raw)]
  else:targets=[pc+len(raw)]
  need(all(t in rows for t in targets),'ordinary CFG edge outside code');edges[pc]=set(targets)
 return edges
def reachable(edges,begin):
 todo=[begin];seen=set()
 while todo:
  pc=todo.pop()
  if pc not in seen:seen.add(pc);todo.extend(edges[pc]-seen)
 return seen
def verify(bundle_path,prior_path):
 _,b=load(bundle_path,'local88-components-a05.json');praw,prior=load(prior_path,'descriptor-contribution-a04.json');need(len(praw)==b['prior']['bytes']and sha(praw)==b['prior']['sha256'],'prior a04 data pin differs')
 orig={r['id']:original(r)for r in b['originals']};records={r['id']:json.loads(orig[r['id']])for r in b['originals']if r['kind']=='json'};need(all(r['machine_id']==b['source_machine_id']for r in records.values()),'source machine differs')
 image='98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518';need(b['image']['sha256']==prior['image']['sha256']==image,'exact image differs')
 need(records['fieldpair-source']['image']['exe_sha256']==records['classifier-source']['exe_sha256']==records['difference-source']['image_sha256']==records['descriptors-data']['image']['exe_sha256']==image,'component image identities differ')
 rows={};counts={}
 for key,begin,nbytes,nins,nj,nc,detail_name in(('fieldpair',0x24C4150,436,113,9,11,'source-details.json'),('classifier',0x2C6A810,693,187,46,6,'details.json')):
  source=records[key+'-source'];archive=orig[key+'-archive'];expected=source['source_archive_sha256']if key=='fieldpair'else source['source']['sha256'];need(sha(archive)==expected,'source archive binding differs')
  with zipfile.ZipFile(BytesIO(archive))as z:body=z.read('function.bin');text=z.read('function.asm').decode();detail=json.loads(z.read(detail_name))
  rr=asm_rows(text,begin,body);jump_rows=detail.get('jumps',detail.get('branches'));call_rows=detail['calls'];need(len(body)==nbytes and len(rr)==nins and len(jump_rows)==nj and len(call_rows)==nc,'function count differs')
  need({int(e['rva'],16)for e in jump_rows}=={pc for pc,(_,mn)in rr.items()if mn.startswith('j')}and {int(e['rva'],16)for e in call_rows}=={pc for pc,(_,mn)in rr.items()if mn=='call'},'control inventory differs')
  for edge in jump_rows+call_rows:
   pc=int(edge['rva'],16);raw=bytes.fromhex(edge.get('raw',edge.get('bytes',edge.get('hex'))));need(rr[pc][0]==raw,'control raw differs')
   if not(raw[:1]==b'\xff'or len(raw)>1 and 0x40<=raw[0]<=0x4f and raw[1]==0xff):need(relative(pc,raw)==int(edge['target'],16),'relative target differs')
  graph(rr);rows[key]=rr;counts[key]=dict(bytes=nbytes,instructions=nins,jumps=nj,calls=nc)
 correction=records['classifier-width-correction'];need(correction['source_contract_sha256']==sha(orig['classifier-source'])and '32-bit DWORD'in correction['correction'],'width correction missing');need(rows['classifier'][0x2C6AA6A][0].hex()=='3b83cc040000'and rows['classifier'][0x2C6AA70][1]=='jl','DWORD signed-threshold instruction differs')
 ds=records['difference-source'];capture=ds['capture'];need(capture['first_attempt_read_charge_reconstructed_not_original_ledger']is True and capture['cumulative_code_bytes_charged']==1936 and capture['cumulative_metadata_bytes_upper']==440 and capture['cumulative_read_calls_upper']==40,'conservative cumulative read scope differs')
 need(sha(orig['difference-raw-archive'])==capture['archive_sha256']and sha(orig['difference-analysis-archive'])==ds['artifacts']['offline-analysis.zip']['sha256'],'difference archive binding differs')
 with zipfile.ZipFile(BytesIO(orig['difference-raw-archive']))as z:mixed=z.read('function.bin')
 need(len(mixed)==968 and sha(mixed)==capture['body_sha256'],'unique mixed source differs')
 with zipfile.ZipFile(BytesIO(orig['difference-analysis-archive']))as z:code=z.read('function-code.asm').decode();cfg=json.loads(z.read('cfg.json'));saved_edges=json.loads(z.read('cfg-edges.json'))
 rr=asm_rows(code,0x24C4790,mixed[:918]);tables={int(k,16):[int(t,16)for t in vs]for k,vs in cfg['tables'].items()};need(len(rr)==210 and len(tables)==2,'mixed-code count differs')
 for offset,dispatcher in((920,0x24C47F2),(944,0x24C4865)):need(list(struct.unpack('<6I',mixed[offset:offset+24]))==tables[dispatcher],'inline DWORD table differs')
 edges=graph(rr,tables);need({int(k,16):{int(x,16)for x in vs}for k,vs in saved_edges.items()}==edges,'saved mixed CFG differs');seen=reachable(edges,0x24C4790);need(len(seen)==205 and set(rr)-seen=={int(x,16)for x in cfg['unreachable_instruction_rvas']},'secondary-dispatch reachability differs');rows['difference']=rr;counts['difference']=dict(unique_mixed_bytes=968,code_bytes=918,padding_bytes=2,inline_table_bytes=48,instructions=210,entry_reachable_instructions=205,cumulative_bytes_charged=1936,metadata_upper_bound=440,reads_upper_bound=40)
 data=records['descriptors-data'];literal=bytes.fromhex(data['raw64_hex']);need(len(literal)==64 and sha(literal)==data['raw64_sha256']==records['descriptors-source']['raw_source']['raw64_sha256'],'literal64 source differs')
 for i,row in enumerate(data['rows']):
  block=literal[i*32:i*32+32];need(block.hex()==row['raw_hex']and sha(block)==row['sha256']and list(struct.unpack('<4H',block[:8]))==row['literal_WORDs'],'descriptor raw WORDs differ');need(struct.unpack_from('<ii',block,16)==(0,0),'descriptor signed offsets differ')
  for callback in row['callbacks']:
   offset=int(callback['offset'],16);va=struct.unpack_from('<Q',block,offset)[0];need(va-int(data['preferred_image_base'],16)==int(callback['RVA'],16)and callback['runtime_address']is False and callback['body_read']is False,'preferred callback address relabelled')
 for entry in data['read_ledger']:
  offset=int(entry['rva'],16)-0x443A530;chunk=literal[offset:offset+entry['bytes']];need(chunk.hex()==entry['raw_hex']and sha(chunk)==entry['sha256'],'literal read ledger differs')
 rate=next(s for s in prior['leaves']if s['id']=='rate');body=bytes.fromhex(rate['hex']);oldzip=original(next(o for o in prior['originals']if o['id']=='rate-archive'))
 with zipfile.ZipFile(BytesIO(oldzip))as z:oldrows=asm_rows(z.read('function.asm').decode(),0x24C7BB0,body)
 for pc,destination in((0x24C7C42,0x24C4150),(0x24C7C82,0x24C4150),(0x24C7D6E,0x2C6A810),(0x24C801D,0x24C4790)):
  raw=oldrows[pc][0];need(raw[:1]==b'\xe8'and relative(pc,raw)==destination,'incoming local88 CALL differs')
 for pc,destination in((0x24C7C13,0x443A530),(0x24C7C1F,0x443A540),(0x24C7C51,0x443A550),(0x24C7C5D,0x443A560)):
  raw=oldrows[pc][0];need(pc+len(raw)+int.from_bytes(raw[-4:],'little',signed=True)==destination,'RIP literal input join differs')
 need(b['business']['maintenance_attribution']=='unclosed'and b['business']['paid_military_amount_raw']is None and b['business']['cadence']is None and b['new_live_credit']==0,'unclosed scope changed')
 return dict(status='PASS',scope='new local88 code/data provenance and composition only',functions=counts,source_machine_id=b['source_machine_id'],originals_verified=len(orig),literal_data_bytes=64,callbacks_followed=0,incoming_calls_verified=4,RIP_literal_joins_verified=4,signed_threshold_width_bits=32,first_difference_charge_reconstructed_not_original_ledger=True,semantic_correctness_verified=False,live_execution_performed=False,new_live_credit=0,paid_military_amount_raw=None,cadence=None)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bundle',type=Path,default=Path(__file__).with_name('local88-components-a05.json'));p.add_argument('--prior-bundle',type=Path,default=Path(__file__).with_name('descriptor-contribution-a04.json'));p.add_argument('--extract-originals',type=Path);a=p.parse_args();result=verify(a.bundle,a.prior_bundle)
 if a.extract_originals:
  need(not a.extract_originals.exists(),'exclusive extraction directory required');a.extract_originals.mkdir(parents=True,exist_ok=False);_,b=load(a.bundle,'local88-components-a05.json')
  for row in b['originals']:
   need(re.fullmatch(r'[a-z0-9-]+',row['id'])is not None,'unsafe original ID');suffix={'json':'.json','zip':'.zip','tar.xz':'.tar.xz'}[row['kind']]
   with(a.extract_originals/(row['id']+suffix)).open('xb')as f:f.write(original(row))
 print(json.dumps(result,ensure_ascii=False,sort_keys=True))
if __name__=='__main__':main()
