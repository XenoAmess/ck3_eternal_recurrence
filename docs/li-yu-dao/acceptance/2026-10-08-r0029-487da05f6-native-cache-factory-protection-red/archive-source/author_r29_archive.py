"""Create-only R29 reference archive. No SDK, process, save-body or MAIN operations."""
from pathlib import Path,PurePosixPath
from datetime import datetime,timezone
import argparse,hashlib,json,re,zipfile

def pin(path):
 path=Path(path);h=hashlib.sha256();size=0
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b);size+=len(b)
 return {'path':path.as_posix(),'bytes':size,'sha256':h.hexdigest()}
def ref(row):
 if not isinstance(row.get('path'),str) or not row['path'] or not re.fullmatch('[0-9a-fA-F]{64}',row.get('sha256','')) or type(row.get('bytes')) is not int or row['bytes']<0:raise ValueError('real ref3 required')
 return {k:row[k] for k in ['path','bytes','sha256']}
def checked(row):
 r=ref(row);actual=pin(r['path'])
 if actual['bytes']!=r['bytes'] or actual['sha256']!=r['sha256'].lower():raise ValueError('source bytes/SHA differ: '+r['path'])
 return actual
def write(path,value):
 with Path(path).open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
def target(value):
 p=PurePosixPath(value)
 if p.is_absolute() or '..'in p.parts or not value.startswith('docs/'):raise ValueError('create-only docs relative target required')
 return value
def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--request',type=Path,required=True);ap.add_argument('--sha256',required=True);ap.add_argument('--output',type=Path,required=True)
 for n in ['closure','closure-verifier','closure-check-result']:
  ap.add_argument('--'+n,type=Path);ap.add_argument('--'+n+'-sha256')
 mode=ap.add_mutually_exclusive_group(required=True);mode.add_argument('--check',action='store_true');mode.add_argument('--create',action='store_true')
 a=ap.parse_args()
 if a.output.exists():raise FileExistsError(a.output)
 request_ref=pin(a.request)
 if request_ref['sha256']!=a.sha256.lower():raise ValueError('request SHA differs')
 q=json.loads(a.request.read_bytes())
 if q.get('schema')!='lyd.r29.original-byte-archive-request.v1' or q['facts'].get('whole_mod')!='NOT_GREEN':raise ValueError('R29 archive/NOT_GREEN contract differs')
 target(q['target_relative'])
 closed_inputs=[a.closure,a.closure_sha256,a.closure_verifier,a.closure_verifier_sha256,a.closure_check_result,a.closure_check_result_sha256]
 if any(v is not None for v in closed_inputs) and not all(v is not None for v in closed_inputs):raise ValueError('three actual closure paths and three SHA pins required together')
 closure=[];closure_status=None
 if a.closure:
  for p,sha,role in [(a.closure,a.closure_sha256,'ROOT verified actual closed boundary'),(a.closure_verifier,a.closure_verifier_sha256,'exact ROOT verifier source; archiver does not rerun it'),(a.closure_check_result,a.closure_check_result_sha256,'ROOT original verifier execution completion')]:
   r=pin(p)
   if r['sha256']!=sha.lower():raise ValueError('closure source SHA differs')
   closure.append(r|{'role':role})
  closure_status=json.loads(a.closure.read_bytes()).get('status')
  if not isinstance(closure_status,str) or not closure_status:raise ValueError('actual closure status missing')
 selected=[];seen={}
 for row in q['files']+closure:
  p=Path(row['path'])
  if p.suffix.lower() in ['.ck3','.exe','.dll','.lib','.dmp','.png','.tar','.bin','.zip']:raise ValueError('body/binary/prior ZIP remains external')
  if a.output.resolve()in p.resolve().parents:raise ValueError('self reference')
  r=checked(row);key=p.resolve().as_posix().casefold()
  if key in seen and seen[key]!=r['sha256']:raise ValueError('conflicting source pins')
  if key not in seen:
   seen[key]=r['sha256'];selected.append(r|{'role':row['role'],'zip_entry':'sha256/'+r['sha256']+'.raw'})
 for row in q['external_reference_only']:ref(row)
 report=checked(q['report']);ci=None
 # ROOT already permanently imported the CI/COM/broker packages; this packet preserves only the runtime and source-repair evidence.
 if a.check:
  print(json.dumps({'status':'R29_CURATED_INPUTS_CHECKED_ONLY','files':len(selected),'request':request_ref,'closure_refs':closure,'CI_inclusion':'already permanently imported by ROOT; no duplicate old ZIP scan','save_body_reads':0,'MAIN_writes':0}));return 0
 a.output.mkdir(parents=True)
 try:
  archive=a.output/'raw-evidence.zip';unique={}
  with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
   for row in selected:
    if row['sha256']in unique:continue
    info=zipfile.ZipInfo(row['zip_entry'],date_time=(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
    with Path(row['path']).open('rb')as src,z.open(info,'w')as dst:
     for b in iter(lambda:src.read(1024*1024),b''):dst.write(b)
    unique[row['sha256']]=row
  with zipfile.ZipFile(archive)as z:
   for sha,row in unique.items():
    h=hashlib.sha256();n=0
    with z.open(row['zip_entry'])as src:
     for b in iter(lambda:src.read(1024*1024),b''):h.update(b);n+=len(b)
    if n!=row['bytes']or h.hexdigest()!=sha:raise ValueError('ZIP original bytes differ')
  facts=q['facts']|{'closed_boundary':closure[0]if closure else None,'closure_verifier':closure[1]if closure else None,'closure_check_result':closure[2]if closure else None,'closure_status_literal':closure_status}
  write(a.output/'FACTS.actual-cutoff.json',facts)
  with (a.output/'REPORT.md').open('x',encoding='utf-8',newline='\n')as f:
   f.write(Path(report['path']).read_text(encoding='utf-8'))
   f.write('\n本包另绑定 ROOT 已验证的闭合原件状态：`'+str(closure_status)+'`。没有传入时仍为 NULL；归档不执行 verifier、不追认 typed/业务资格，也不代替原 HANDLE 或原执行过程事实。\n')
  write(a.output/'ARCHIVE-VALIDATION.actual.json',{'status':'ORIGINAL_BYTES_ZIP_VERIFIED_ONLY','original_files':len(selected),'unique_original_sets':len(unique),'raw_zip':pin(archive),'SDK_size_limit':None,'all_original_bytes_sha_match':True,'save_body_reads':0,'MAIN_SDK_game_process_bus_actions':0})
  write(a.output/'INDEX.json',{'schema':'lyd.r29.original-byte-inventory.v1','created_at_utc':datetime.now(timezone.utc).isoformat(),'request':request_ref,'source_head':q['facts']['source_head'],'original_files':selected,'external_reference_only':q['external_reference_only'],'CI_manifest':ci,'raw_zip':pin(archive),'closure_refs':closure,'closure_status_literal':closure_status,'whole_mod':'NOT_GREEN','archive_status':'ROOT_CLOSED_ORIGINALS_ARCHIVED'if closure else'LIVE_CUTOFF_DRAFT_ONLY'})
  own=[pin(p)|{'target_relative_file':p.name}for p in sorted(a.output.iterdir())if p.is_file()]
  write(a.output/'IMPORT-MANIFEST.source-only.json',{'schema':'lyd.r29.archive-create-only-import-manifest.v1','target_relative':q['target_relative'],'loaded_source_head':q['facts']['source_head'],'archive_is_runtime_closed':bool(closure),'whole_mod':'NOT_GREEN','files':own,'default_MAIN_apply_authorized':False,'MAIN_writes':0})
  combined=[r|{'target_relative':target(q['target_relative']+'/'+r['target_relative_file'])}for r in own]
  write(a.output/'COMBINED-IMPORT-MANIFEST.source-only.json',{'schema':'lyd.r29.combined-create-only-docs-import-manifest.v1','source_head':q['facts']['source_head'],'files':combined,'runtime_closed':bool(closure),'closure_refs':closure,'whole_mod':'NOT_GREEN','default_MAIN_apply_authorized':False,'CI_manifest':ci,'MAIN_writes':0})
  result={'status':'R29_EXTERNAL_ARCHIVE_CREATED_ONLY','INDEX':pin(a.output/'INDEX.json'),'REPORT':pin(a.output/'REPORT.md'),'ZIP':pin(archive),'COMBINED_IMPORT_MANIFEST':pin(a.output/'COMBINED-IMPORT-MANIFEST.source-only.json'),'files':len(selected),'runtime_closed':bool(closure),'whole_mod':'NOT_GREEN','MAIN_writes':0}
  write(a.output/'RESULT.actual.json',result);print(json.dumps(result));return 0
 except Exception as e:
  write(a.output/'FAILURE.actual.json',{'status':'FAILED_PARTIAL_PRESERVED','error':repr(e),'request':request_ref,'MAIN_writes':0});raise
if __name__=='__main__':raise SystemExit(main())
