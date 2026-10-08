"""R30 create-only archive request preparation. Requires ROOT's actual typed-closed refs.

Does not run the collector, validators, SDK, game, processes, Git or MAIN operations.
Saved bodies, native binaries, source archives and prior ZIPs remain external refs.
"""
from pathlib import Path,PurePosixPath
import argparse,ast,difflib,hashlib,json,re
B=Path('C:/workspace/ck3_lyd_runtime_20261004')
TEXT={'.json','.jsonl','.py','.md','.diff','.patch','.txt','.log','.cpp','.h','.hpp','.cmake','.ini','.cfg','.info','.yml','.yaml','.toml','.csv'}
BODY={'.ck3','.exe','.dll','.lib','.obj','.pdb','.dmp','.png','.jpg','.jpeg','.dds','.tar','.bin','.zip','.mp4','.wav','.ogg'}
ROOTCOLLECTOR=B/'r29-business-permanent-archive-sourceonly-20261008-001/author_r29_archive.py'
ROOTCOLLECTOR_SHA='facd03d6b79e78dbf62088b9a984a805cfd0a3aebcca7cb3a76865f6c48c06cd'
RUN='C:/workspace/ck3_lyd_runtime_20261004/live-attempt-030'
PY='C:/Users/Administrator/AppData/Local/Programs/Python/Python313/python.exe'
def text_file(p):return p.suffix.lower()in TEXT or p.name in ['stdout','stderr','screen-lease.jsonl','CMakeLists.txt']
def pin(p):
 p=Path(p).resolve()
 if not text_file(p):raise ValueError('only declared text/JSON sources may be opened: '+str(p))
 h=hashlib.sha256();n=0
 with p.open('rb')as f:
  for x in iter(lambda:f.read(1024*1024),b''):h.update(x);n+=len(x)
 return {'path':p.as_posix(),'bytes':n,'sha256':h.hexdigest()}
def checked(p,sha):
 r=pin(p)
 if r['sha256']!=sha.lower():raise ValueError('actual source SHA differs: '+r['path'])
 return r
def read(p):return json.loads(Path(p).read_bytes())
def put(p,v):
 with Path(p).open('x',encoding='utf-8',newline='\n')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def write(p,v):
 with Path(p).open('x',encoding='utf-8',newline='\n')as f:f.write(v)
def main():
 ap=argparse.ArgumentParser(description=__doc__)
 for n in ['source-head','export-report','export-report-sha256','report','report-sha256','facts','facts-sha256','packroots','packroots-sha256','closure','closure-sha256','closure-verifier','closure-verifier-sha256','closure-check-result','closure-check-result-sha256','closure-create-result','closure-create-result-sha256','output-source','archive-output','target-relative']:
  ap.add_argument('--'+n,required=True)
 a=ap.parse_args();out=Path(a.output_source);arc=Path(a.archive_output)
 if out.exists()or arc.exists():raise FileExistsError('create-only output already exists')
 if not re.fullmatch('[0-9a-f]{40}',a.source_head):raise ValueError('actual source HEAD required')
 if not a.target_relative.startswith('docs/')or '..'in PurePosixPath(a.target_relative).parts:raise ValueError('explicit docs create-only target required')
 refs={}
 for n in ['export_report','report','facts','packroots','closure','closure_verifier','closure_check_result','closure_create_result']:
  refs[n]=checked(getattr(a,n),getattr(a,n+'_sha256'))
 ex=read(a.export_report);facts=read(a.facts);closure=read(a.closure)
 if ex['source']['head']!=a.source_head or ex.get('source_root')!='C:/lr30s2':raise ValueError('actual clean R30 source/export binding required')
 if closure.get('source_head')!=a.source_head or closure.get('status')!='ROOT_REVIEWED_ACTUAL_CLOSED_RELEASED_BOUNDARY':raise ValueError('actual ROOT verified closed R30 boundary required before archive freeze')
 if facts.get('source_head')!=a.source_head or facts.get('whole_mod')!='NOT_GREEN':raise ValueError('actual source/NOT_GREEN facts required')
 for n in ['formal_mandate_credit','whole_product_pass','C3_credit','I4_credit','cold_new_T_credit']:
  if facts.get(n)is not None:raise ValueError('staged diagnostic cannot claim formal/product/C3/I4/cold newT credit')
 for n in ['closure_check_result','closure_create_result']:
  if read(getattr(a,n)).get('exit_code')!=0:raise ValueError('ROOT original typed closure check/create actual0 required')
 roots=read(a.packroots)
 if roots.get('schema')!='lyd.r30.explicit-archive-packroots.v1' or not isinstance(roots.get('packroots'),list):raise ValueError('explicit finite selected packroots required')
 files=[];seen=set();external=[];extseen=set();skipped=[]
 def add(p,role):
  p=Path(p)
  if not p.is_file():raise FileNotFoundError(p)
  if not text_file(p):return
  k=p.resolve().as_posix().casefold()
  if k not in seen:seen.add(k);files.append(pin(p)|{'role':role})
 def external_refs(v):
  if isinstance(v,dict):
   if isinstance(v.get('path'),str)and Path(v['path']).suffix.lower()in BODY and all(k in v for k in ['path','bytes','sha256']):
    k=v['path'].casefold()
    if k not in extseen:extseen.add(k);external.append({x:v[x]for x in ['path','bytes','sha256']}|{'role':'permanent original external body/binary/image/source tar/prior ZIP; never opened by this archiver'})
   for x in v.values():external_refs(x)
  elif isinstance(v,list):
   for x in v:external_refs(x)
 def tree(folder,role):
  folder=Path(folder)
  if not folder.is_dir():raise FileNotFoundError(folder)
  for p in sorted(folder.rglob('*')):
   if p.is_file()and text_file(p):
    add(p,role)
    if p.suffix.lower()=='.json':external_refs(read(p))
 run=Path(RUN)
 for p in sorted(run.iterdir()):
  if p.is_file()and text_file(p):add(p,'actual immediate R30 runtime/source/profile/identity/spec/stdio original')
  elif p.is_dir()and re.match(r'^(?:D[0-6]-|ROOT-|root-request-|persistent-client-|native-evidence$|official-mcp-queue-|official-mcp-binding-|game-original-handle-holder-|root-launch-|root-profile-request-|root-live-|root-preflight-)',p.name):tree(p,'actual R30 staged SDK/native/request/author/STATE/TYPED/comparison/host original evidence')
  elif p.is_dir():skipped.append({'path':p.as_posix(),'reason':'not in closed curated runtime subtree allowlist; saved bodies/content/cache and desktop media not traversed'})
 for value in roots['packroots']:
  p=Path(value).resolve()
  if p.parent!=B.resolve()or not re.match(r'^(?:r30[-_]|root-r30[-_])',p.name):raise ValueError('only explicit actual R30 top-level packroots accepted')
  if out.resolve()==p or arc.resolve()==p:raise ValueError('self/output source not eligible')
  if p.is_dir():tree(p,'explicit selected actual R30 source/runtime wrapper/original execution/closure pack')
  elif p.is_file():add(p,'explicit actual ROOT R30 source/argv file')
  else:raise FileNotFoundError(p)
 for row in roots.get('original_files',[]):
  if not isinstance(row,dict)or not all(k in row for k in ['path','bytes','sha256','role']):raise ValueError('explicit additional original ref3 and role required')
  actual=checked(row['path'],row['sha256'])
  if actual['bytes']!=row['bytes']:raise ValueError('explicit original additional size differs')
  add(row['path'],row['role'])
 for row in refs.values():add(row['path'],'actual ROOT late-bound report/facts/export/closure source')
 external_refs(ex)
 parent=checked(ROOTCOLLECTOR,ROOTCOLLECTOR_SHA);old=ROOTCOLLECTOR.read_text(encoding='utf-8');source=old.replace('R29','R30').replace('r29','r30')
 if ast.dump(ast.parse(source.replace('R30','R29').replace('r30','r29')),include_attributes=False)!=ast.dump(ast.parse(old),include_attributes=False):raise ValueError('original collector inverse full AST differs')
 out.mkdir(parents=True)
 write(out/'author_r30_archive.py',source)
 write(out/'COLLECTOR-LABEL-ONLY.diff',''.join(difflib.unified_diff(old.splitlines(True),source.splitlines(True),fromfile=ROOTCOLLECTOR.as_posix(),tofile=(out/'author_r30_archive.py').as_posix())))
 put(out/'COLLECTOR-PROJECTION.actual.json',{'original':parent,'successor':pin(out/'author_r30_archive.py'),'inverse_full_AST_equal':True,'change':'R29/r29 literal run labels only','new_tests_verifiers_SDK_game_body_MAIN_calls':0})
 for p in [out/'author_r30_archive.py',out/'COLLECTOR-PROJECTION.actual.json',out/'COLLECTOR-LABEL-ONLY.diff',Path(__file__)]:add(p,'finite original collector projection and file-only preparation source')
 request={'schema':'lyd.r30.original-byte-archive-request.v1','target_relative':a.target_relative,'facts':facts,'report':refs['report'],'files':files,'external_reference_only':external}
 put(out/'REQUEST.actual.json',request)
 argv=[PY,'-B','-X','utf8',(out/'author_r30_archive.py').as_posix(),'--request',(out/'REQUEST.actual.json').as_posix(),'--sha256',pin(out/'REQUEST.actual.json')['sha256'],'--output',arc.as_posix()]
 for n in ['closure','closure-verifier','closure-check-result']:argv+=['--'+n,getattr(a,n.replace('-','_')),'--'+n+'-sha256',getattr(a,n.replace('-','_')+'_sha256')]
 argv+=['--create']
 put(out/'ROOT-CREATE-ARGV.actual.json',{'argv':argv,'author':pin(out/'author_r30_archive.py'),'request':pin(out/'REQUEST.actual.json'),'ROOT_only':True,'archive_execution_pending':True,'MAIN_writes':0})
 put(out/'INDEX.json',{'status':'ACTUAL_TYPED_CLOSED_R30_CURATED_SOURCE_READY_ROOT_ARCHIVE_CREATE_PENDING','source_head':a.source_head,'collector':pin(out/'author_r30_archive.py'),'request':pin(out/'REQUEST.actual.json'),'argv':pin(out/'ROOT-CREATE-ARGV.actual.json'),'closure_refs':refs,'files':len(files),'external_reference_only':len(external),'skipped_unselected_run_trees':skipped,'whole_mod':'NOT_GREEN','diagnostic_formal_credit':None,'archive_body_binary_SDK_process_MAIN_calls':0})
 print(json.dumps({'INDEX':pin(out/'INDEX.json'),'argv':pin(out/'ROOT-CREATE-ARGV.actual.json'),'files':len(files),'external_refs':len(external),'archive_executed':False}));return 0
if __name__=='__main__':raise SystemExit(main())
