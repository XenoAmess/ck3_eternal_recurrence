from pathlib import Path
from datetime import datetime,timezone
import json,subprocess,hashlib
R=Path(__file__).parent
P=R/'commit-files-004';P.mkdir(exist_ok=False)
T='d0f8fa3b9d444828759443aa018bfd7ad31b398d'
argv=['C:/Program Files/GitHub CLI/gh.exe','api','--method','GET',f'repos/XenoAmess/ck3_eternal_recurrence/commits/{T}?per_page=100&page=1','--paginate','--slurp','-H','Accept: application/vnd.github+json']
start=datetime.now(timezone.utc).isoformat()
try:p=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=55,check=False);out,err,rc=p.stdout,p.stderr,p.returncode
except subprocess.TimeoutExpired as e:out,err,rc=e.stdout or b'',e.stderr or b'',None
(P/'commit-pages.stdout').write_bytes(out);(P/'commit-pages.stderr').write_bytes(err)
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(path,obj):
 with path.open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
dump(P/'COMMAND.json',{'argv':argv,'at_utc':start,'finished_at_utc':datetime.now(timezone.utc).isoformat(),'exit_code':rc,'stdout_bytes':len(out),'stdout_sha256':sha(out),'stderr_bytes':len(err),'stderr_sha256':sha(err),'environment_policy':'Inherited current process proxy; no settings changed.'})
assert rc==0,'Read failed; attempt retained.'
pages=json.loads(out);assert isinstance(pages,list) and pages and all(p['sha']==T for p in pages)
files=[x for p in pages for x in p.get('files',[])];assert len({x['filename'] for x in files})==len(files)
summary={'target_commit':T,'page_count':len(pages),'page_file_counts':[len(p.get('files',[])) for p in pages],'actual_file_records':len(files),'commit_api_maximum_3000_not_reached':len(files)<3000,'parents':[x['sha'] for x in pages[0]['parents']],'product_source_files':[x['filename'] for x in files if x['filename'].startswith('mod_li_yu_dao/')],'relevant_source_files':[x['filename'] for x in files if x['filename'].startswith(('.github/workflows/','ck3_autonomous_player/','mod_li_yu_dao/'))]}
dump(P/'SUMMARY.json',summary)
payload=[]
for path in sorted(P.rglob('*')):
 if path.is_file():b=path.read_bytes();payload.append({'path':path.relative_to(P).as_posix(),'bytes':len(b),'sha256':sha(b)})
dump(P/'INDEX.json',{'schema':'lyd.external.evidence.index.v1','target_commit':T,'files':payload})
print(json.dumps(summary,indent=2))
