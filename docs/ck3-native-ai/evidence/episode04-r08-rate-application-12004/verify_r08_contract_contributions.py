"""Verify retained R08 contribution-chain source; no EXE, SDK or game access."""
from pathlib import Path
from io import BytesIO
import argparse,base64,hashlib,json,re,zipfile,zlib
def need(ok,msg):
 if not ok:raise ValueError(msg)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def load_json(path,member):
 p=Path(path)
 if p.suffix=='.zip':
  with zipfile.ZipFile(p)as z:raw=z.read(member)
 elif p.suffix=='.patch':
  sections=p.read_text(encoding='utf-8').split('diff --git ')[1:];selected=[s for s in sections if any(line.startswith('+++ b/')and line.rstrip().endswith('/'+member)for line in s.splitlines())]
  need(len(selected)==1 and 'new file mode 100644\n'in selected[0],'complete new-file JSON patch target required');raw=''.join(line[1:]for line in selected[0].splitlines(keepends=True)if line.startswith('+')and not line.startswith('+++')).encode()
 else:raw=p.read_bytes()
 return raw,json.loads(raw)
def original(row):
 need(row['encoding']in('base64','zlib+base64'),'unknown encoding');raw=base64.b64decode(row['payload'],validate=True)
 if row['encoding']=='zlib+base64':raw=zlib.decompress(raw)
 need(len(raw)==row['bytes']and sha(raw)==row['sha256'],'original pin changed '+row['id']);return raw
def at(value,keys):
 for key in keys:value=value[key]
 return value
def relative(pc,raw):
 if raw[0]in(0xe8,0xe9,0xeb)or 0x70<=raw[0]<=0x7f:return pc+len(raw)+int.from_bytes(raw[1:],'little',signed=True)
 if raw[:1]==b'\x0f'and 0x80<=raw[1]<=0x8f:return pc+len(raw)+int.from_bytes(raw[2:],'little',signed=True)
 raise ValueError('unsupported relative edge')
def parse_asm(text,begin,body,coverage):
 rows={};previous_end=begin
 for line in text.splitlines():
  m=re.fullmatch(r'([0-9A-Fa-f]+) ([0-9A-Fa-f]+) (\S+)(?: (.*))?',line);need(m is not None,'malformed saved ASM');pc=int(m[1],16);raw=bytes.fromhex(m[2])
  need(pc>=previous_end and begin<=pc and pc+len(raw)<=begin+len(body)and body[pc-begin:pc-begin+len(raw)]==raw,'saved instruction bytes/extent differ')
  if coverage=='contiguous':need(pc==previous_end,'saved ASM gap')
  rows[pc]=(raw,m[3]);previous_end=pc+len(raw)
 if coverage=='contiguous':need(previous_end==begin+len(body),'saved ASM incomplete')
 else:need(coverage=='reachable-capture-prefix','unknown coverage claim')
 need(begin in rows,'entry instruction missing');return rows
def controls(rows):return({pc for pc,(_,mn)in rows.items()if mn.startswith('j')},{pc for pc,(_,mn)in rows.items()if mn=='call'})
def normal_cfg(rows,begin):
 pending=[begin];seen=set();returns=set();traps=set()
 while pending:
  pc=pending.pop()
  if pc in seen:continue
  need(pc in rows,'unclosed reachable instruction edge');seen.add(pc);raw,mn=rows[pc];following=pc+len(raw)
  if mn.startswith('ret'):returns.add(pc)
  elif mn in('int3','ud2'):traps.add(pc)
  elif mn=='jmp':pending.append(relative(pc,raw))
  elif mn.startswith('j'):pending.extend((relative(pc,raw),following))
  else:pending.append(following)
 return returns,traps
def verify_leaf(spec,orig,records):
 source=records[spec['source_id']];archive=orig[spec['archive_id']]
 binding=spec['archive_binding'];need(at(records[binding['record_id']],binding['path'])==sha(archive),'source-to-archive binding differs')
 with zipfile.ZipFile(BytesIO(archive))as z:
  body=z.read(spec['bin_member']);asm=z.read(spec['asm_member']).decode();detail=json.loads(z.read(spec['detail_member']))
 need(len(body)==spec['captured_bytes']and sha(body)==spec['sha256']and body.hex()==spec['hex'],'captured source differs')
 if spec.get('raw_binding'):
  rb=spec['raw_binding'];need(at(records[rb['record_id']],rb['path'])==sha(body),'raw-source record pin differs')
 rows=parse_asm(asm,int(spec['begin_rva'],16),body,spec['coverage']);jumps,calls=controls(rows)
 need(len(rows)==spec['instructions']and len(jumps)==spec['jumps']and len(calls)==spec['calls'],'source control counts differ')
 metadata_jumps=at(detail,spec['jump_path'])if spec['jump_path']is not None else None;metadata_calls=at(detail,spec['call_path']);need({int(e['rva'],16)for e in metadata_calls}==calls,'saved call inventory differs')
 if metadata_jumps is not None:need({int(e['rva'],16)for e in metadata_jumps}==jumps,'saved jump inventory differs')
 for pc in jumps:need(relative(pc,rows[pc][0])in rows,'ordinary jump target outside saved instruction boundaries')
 indirect=0
 for edge in(metadata_jumps or[])+metadata_calls:
  pc=int(edge['rva'],16);raw=bytes.fromhex(edge['raw']if 'raw'in edge else edge['bytes']if 'bytes'in edge else edge['hex']);need(rows[pc][0]==raw,'saved edge bytes differ')
  if raw[:1]==b'\xff':indirect+=1
  else:need(relative(pc,raw)==int(edge['target'],16),'saved relative target differs')
 returns,traps=normal_cfg(rows,int(spec['begin_rva'],16));need(returns=={int(v,16)for v in spec['ordinary_RET_sites']},'normal RET inventory differs')
 return rows,dict(captured_bytes=len(body),instructions=len(rows),jumps=len(jumps),calls=len(calls),indirect_targets_unresolved=indirect,ordinary_RET_sites=spec['ordinary_RET_sites'],boundary_claim=spec['boundary_claim'])
def verify(bundle_path,prior_path):
 _,b=load_json(bundle_path,'descriptor-contribution-a04.json');prior_raw,prior=load_json(prior_path,'descriptor-chain-a03.json');need(len(prior_raw)==b['prior']['bytes']and sha(prior_raw)==b['prior']['sha256'],'frozen a03 data pin changed')
 orig={r['id']:original(r)for r in b['originals']};records={r['id']:json.loads(orig[r['id']])for r in b['originals']if r['kind']=='json'}
 need(all(r['machine_id']==b['source_machine_id']for r in records.values()),'source-machine IDs differ');image=b['image']['sha256'];need(image==prior['image']['sha256']=='98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518','exact image differs')
 rows={};counts={}
 for spec in b['leaves']:
  need(at(records[spec['source_id']],spec['image_sha_path'])==image,'leaf exact image differs');rows[spec['id']],counts[spec['id']]=verify_leaf(spec,orig,records)
 for key,pc,destination in(('shared',0x2BC7958,0x2BD5370),('worker',0x2BD5820,0x2BD58E0)):
  starts={'shared':0x2BC76C0,'worker':0x2BD5530};body=bytes.fromhex(prior['source_bytes'][key]['hex']);code=body[pc-starts[key]:pc-starts[key]+5];need(code[:1]==b'\xe8'and relative(pc,code)==destination,'prior-to-new worker CALL differs')
 joins=(('wrapper',0x2BD5516,0x2BD59C0),('value',0x2BD5A31,0x2BD3320),('value',0x2BD5A5E,0x24C7BB0),('value',0x2BD5A78,0x24C18F0),('loop',0x2BD5945,0x2BD3320),('loop',0x2BD5972,0x24C7BB0),('loop',0x2BD598C,0x24C18F0),('loop',0x2BD59A3,0x2BD36D0))
 for key,pc,destination in joins:
  code=rows[key][pc][0];need(code[:1]==b'\xe8'and relative(pc,code)==destination,'contribution-chain CALL differs')
 correction=records['value-parameter-correction'];need(correction['source_sha256']==sha(orig['value-source']),'24B correction source pin differs')
 need('localparameter16B'in records['value-source']['production']['helper_parameters']and '24B'in correction['correction'],'original16B statement or appended24B correction missing')
 parameter=b['parameter_span'];need(parameter['bytes']==24 and parameter['padding_0xC']=='unknown'and parameter['fields']==[[0,8],[8,4],[16,8]],'parameter span relabelled')
 clamp=records['clamp-source'];need(clamp['first_metadata_ledger_missing_not_reconstructed']is True and clamp['cumulative_metadata_bytes_upper_bound']==444 and clamp['cumulative_physical_reads_upper_bound']==40,'conservative metadata scope changed')
 clamp_spec=next(s for s in b['leaves']if s['id']=='clamp')
 with zipfile.ZipFile(BytesIO(orig[clamp_spec['archive_id']]))as z:prefix=z.read(clamp_spec['bin_member'])
 need(len(prefix)==192 and sha(prefix[:190])==records['clamp-delivery']['logical190_sha256']and clamp_spec['coverage']=='reachable-capture-prefix','192B capture/190B logical distinction changed')
 history=records['clamp-history-manifest'];need(sha(orig['clamp-history-archive'])==history['sha256']and history['first_failed_metadata_ledger_not_reconstructed']is True,'failed-ledger history not retained')
 need(b['business']['maintenance_attribution']=='unclosed'and b['business']['paid_military_amount_raw']is None and b['business']['cadence']is None and b['new_live_credit']==0,'unclosed business scope changed')
 return dict(status='PASS',scope='six-leaf source/original integrity, normal CFG, incoming CALL joins and explicit corrections only',functions=counts,originals_verified=len(orig),inter_leaf_call_joins_verified=len(joins)+2,parameter_span_bytes=24,clamp_capture_bytes=192,clamp_logical_bytes=190,metadata_bytes_upper_bound=444,physical_reads_upper_bound=40,first_metadata_ledger_missing_not_reconstructed=True,semantic_correctness_verified=False,live_execution_performed=False,source_machine_id=b['source_machine_id'],paid_military_amount_raw=None,cadence=None,new_live_credit=0)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bundle',type=Path,default=Path(__file__).with_name('descriptor-contribution-a04.json'));p.add_argument('--prior-bundle',type=Path,default=Path(__file__).with_name('descriptor-chain-a03.json'));p.add_argument('--extract-originals',type=Path);a=p.parse_args();result=verify(a.bundle,a.prior_bundle)
 if a.extract_originals:
  need(not a.extract_originals.exists(),'exclusive new extraction directory required');a.extract_originals.mkdir(parents=True,exist_ok=False);_,b=load_json(a.bundle,'descriptor-contribution-a04.json')
  for row in b['originals']:
   need(re.fullmatch(r'[a-z0-9-]+',row['id'])is not None,'unsafe original ID');suffix={'json':'.json','text':'.md','zip':'.zip'}[row['kind']]
   with(a.extract_originals/(row['id']+suffix)).open('xb')as f:f.write(original(row))
 print(json.dumps(result,ensure_ascii=False,sort_keys=True))
if __name__=='__main__':main()
