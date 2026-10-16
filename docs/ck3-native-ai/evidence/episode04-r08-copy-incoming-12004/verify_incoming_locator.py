"""Stdlib packet/ledger verification; full .text negative scan is not embedded/replayed."""
from pathlib import Path
from io import BytesIO
import argparse,base64,hashlib,json,re,zipfile,zlib
MEMBER='docs/ck3-native-ai/evidence/episode04-r08-copy-incoming-12004/portable-source.json'
def need(ok,msg):
 if not ok:raise ValueError(msg)
def sha(b):return hashlib.sha256(b).hexdigest()
def load(path):
 p=Path(path)
 if p.suffix=='.patch':
  parts=re.split(br'(?m)^diff --git ',p.read_bytes())[1:];found=[s for s in parts if ('+++ b/'+MEMBER).encode()in s.splitlines()];need(len(found)==1,'Bundle target missing');inside=False;rows=[]
  for line in found[0].splitlines(keepends=True):
   if line.startswith(b'@@ '):inside=True;continue
   if inside and line.startswith(b'+'):rows.append(line[1:])
  raw=b''.join(rows)
 else:raw=p.read_bytes()
 return json.loads(raw)
def decode(row):
 need(row['encoding']=='zlib+base85','Encoding differs');raw=zlib.decompress(base64.b85decode(row['payload']));need(len(raw)==row['bytes']and sha(raw)==row['sha256'],'Original differs '+row['id']);return raw
def verify(path):
 b=load(path);o={r['id']:decode(r)for r in b['originals']};need(len(o)==len(b['originals']),'Original IDs duplicated')
 loc=json.loads(o['LOCATOR.actual.json']);inv=json.loads(o['INVENTORY.actual-a01.json']);before=json.loads(o['PLAN.before-locator.json']);final=json.loads(o['PLAN.final.json']);red=json.loads(o['FOR-OBSERVATION-RED.actual.json']);static=json.loads(o['CHECK.static-before-locator.actual.json']);checked=json.loads(o['CHECK.final.actual.json']);summary=json.loads(o['SOURCE-SUMMARY.actual.json'])
 need(loc['machine_id']==inv['machine_id']==final['machine_id']==b['machine_id'],'Machine differs')
 image='98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518';need(loc['EXE_SHA_reused_not_rehashed']==before['build']['exe_sha256']==final['build']['exe_sha256']==b['image']['sha256']==image,'Exact source image differs')
 need(loc['target_rva']==0x28A63E0 and loc['hits']==[]and loc['error']is None,'Recorded finite locator result differs')
 need(loc['stat_before']==loc['stat_after']=={k:inv['exe_stat_only'][k]for k in loc['stat_before']},'Source stat binding differs')
 need(loc['section']['name']=='.text'and loc['section']['va']==4096 and loc['section']['raw']==1024 and loc['section']['virtual_size']==71141448,'Exact section scope differs')
 rows=[json.loads(s)for s in o['LOCATOR-READS.actual.ndjson'].splitlines()if s.strip()];cursor=0
 need(len(rows)==loc['locator_read_calls']==17,'Read count differs')
 for i,row in enumerate(rows,1):
  expected=min(4194304,71141448-cursor);need(row['read_ordinal']==i and row['kind']=='locator_text_only'and row['file_offset']==1024+cursor and row['rva']==4096+cursor and row['requested_bytes']==row['actual_bytes']==expected,'Contiguous exact read charge differs');need(re.fullmatch('[0-9a-f]{64}',row['sha256'])is not None,'Chunk digest shape differs');cursor+=expected
 need(cursor==loc['locator_actual_bytes']==loc['locator_requested_bytes']==71141448,'Total locator byte charge differs')
 need(loc['locator_byte_charge_distinct_from_newbody']and loc['new_body_bytes']==loc['new_metadata_bytes']==loc['full_EXE_hashes']==0,'Locator was hidden as small body scope')
 need(loc['full_section_not_embedded']is True and b['portable_limits']['full_text_negative_scan_replayed']is False,'Negative scan replay scope elevated')
 need(red['exit_code']==2 and red['new_EXE_bytes']==0 and not red['live_sampling_authorized_by_this_record'],'Original for-observation RED missing')
 need(before['observation']['mode']==final['observation']['mode']=='offline-only','Static plan relabelled live')
 need(static['result']==checked['result']=='plan-consistent'and static['live_execution_performed']is False and checked['live_execution_performed']is False,'Static check scope differs')
 need(sha(o['PLAN.before-locator.json'])==static['plan_sha256']and sha(o['PLAN.final.json'])==checked['plan_sha256'],'Plan/check pins differ')
 for edge in final['edges']:need(edge['status']in('unknown','inference'),'Unproved edge promoted')
 with zipfile.ZipFile(BytesIO(o['held-source-originals.zip']))as z:
  need(z.testzip()is None,'Source ZIP CRC');source={n:z.read(n)for n in z.namelist()}
 need(set(source)==set(b['held_members']),'Held source member set differs')
 for n,pin in b['held_members'].items():need(len(source[n])==pin['bytes']and sha(source[n])==pin['sha256'],'Held member differs')
 body=source['caller.bin'];receipt=json.loads(source['original-source-receipt.json']);need(len(body)==695 and sha(body)==receipt['function']['sha256']=='ffebf7d960edb76b71d2456b7f8722cc09092952b41c565f648410b42a47dede'and body==bytes.fromhex(summary['held_function']['hex']),'Existing695B source differs')
 # Independent positive rel32 arithmetic on a known held CALL; no EXE rescan.
 hits=[0x28A63E0+i for i in range(len(body)-4)if body[i]==0xe8 and 0x28A63E0+i+5+int.from_bytes(body[i+1:i+5],'little',signed=True)==0x28D6170]
 need(hits==[0x28A6535],'Known positive E8 relation differs')
 need(summary['new_source']['new_caller_code_bytes']==summary['new_source']['new_caller_metadata_bytes']==0 and summary['new_source']['candidates']==0,'Source acquisition expanded')
 need(b['business']['maintenance_attribution']=='unclosed'and b['business']['military_c_d_producer']is None and b['business']['paid_military_amount_raw']is None and b['business']['cadence']is None,'Business unknown elevated')
 return dict(status='PASS',scope='saved locator receipt/ledger and held source integrity only',machine_id=b['machine_id'],originals_verified=len(o),recorded_locator_bytes=71141448,recorded_locator_reads=17,recorded_E8_target_candidates=0,new_caller_body_bytes=0,new_metadata_bytes=0,held_source_bytes=695,positive_held_CALL_checked=True,full_text_negative_scan_replayed=False,semantic_correctness_verified=False,live_execution_performed=False,paid_military_amount_raw=None,cadence=None,maintenance_attribution='unclosed')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bundle',type=Path,default=Path(__file__).with_name('portable-source.json'));p.add_argument('--extract-originals',type=Path);a=p.parse_args();result=verify(a.bundle)
 if a.extract_originals:
  need(not a.extract_originals.exists(),'Exclusive new extraction directory required');a.extract_originals.mkdir(parents=True,exist_ok=False)
  for row in load(a.bundle)['originals']:
   need(re.fullmatch(r'[A-Za-z0-9_.-]+',row['id'])is not None,'Unsafe original name')
   with(a.extract_originals/row['id']).open('xb')as f:f.write(decode(row))
 print(json.dumps(result,ensure_ascii=False,sort_keys=True))
if __name__=='__main__':main()
