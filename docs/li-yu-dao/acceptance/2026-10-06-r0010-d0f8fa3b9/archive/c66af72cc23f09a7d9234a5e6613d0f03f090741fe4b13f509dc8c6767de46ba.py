from pathlib import Path
from datetime import datetime,timezone
import json,re,hashlib,subprocess
R=Path(__file__).parent;T='d0f8fa3b9d444828759443aa018bfd7ad31b398d'
P=R/'failure-focused-009';P.mkdir(exist_ok=False)
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(path,obj):
 with path.open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
raw=(R/'general-observation-006/raw/general-logs.stdout').read_bytes()
text=raw.decode('utf-8-sig');clean='\n'.join(re.sub(r'^\d{4}-\d{2}-\d{2}T\S+\s','',line) for line in text.splitlines())
lines=clean.splitlines();start=next(i for i,x in enumerate(lines) if '##[group]Run python tools/validate_python_only.py' in x)
end=next(i for i in range(start,len(lines)) if 'Process completed with exit code 1.' in lines[i])
(P/'FAILED-STEP-ONLY.raw.txt').write_bytes(('\n'.join(lines[start:end+1])+'\n').encode('utf-8'))
history=next(i for i,x in enumerate(lines) if 'Run python -X utf8 -m unittest discover' in x and 'CUnit' not in x and 'Test public' not in x and 'native' not in x) if False else None
groups=clean.split('##[group]')
historygroup=next(x for x in groups if 'test_ingame_decision_history_growth.py' in x)
historycounts=[{'count':int(m[0]),'seconds':float(m[1])} for m in re.findall(r'Ran (\d+) tests in ([0-9.]+)s',historygroup)]
artifacts=json.loads((R/'general-observation-006/raw/general-artifacts.stdout').read_bytes())['artifacts']
selected=[{'id':x['id'],'name':x['name'],'size_in_bytes':x['size_in_bytes'],'expired':x['expired']} for x in artifacts]
summary={'target_commit':T,'failure':{'failed_step':'Enforce Python-only Windows automation','step_number':43,'exit_code':1,'violation_count':2,'paths':['docs/autonomous-agent-progress/daily/2026-10-05.md','docs/autonomous-agent-progress/weekly/2026-W41.md'],'classification':'Two readable documents contain the banned shell name; actual job reported these exact two references.','source_kind':'This target completed job actual stdout','focused_raw_snippet':'failure-focused-009/FAILED-STEP-ONLY.raw.txt','unrelated_expected_negative_fixture_logs_not_counted_as_job_cause':True},
 'history_growth_actual_in_group':historycounts,'artifact_metadata':selected,'artifact_zips_downloaded':False,'actual_general_unittest_total':sum(int(x) for x in re.findall(r'Ran (\d+) tests',text)),
 'scope':'Source/SDK memory fixtures, no game execution or runtime credit.'}
dump(P/'SUMMARY.json',summary)
payload=[]
for p in sorted(P.iterdir()):
 if p.is_file():b=p.read_bytes();payload.append({'path':p.name,'bytes':len(b),'sha256':sha(b)})
dump(P/'INDEX.json',{'schema':'lyd.external.evidence.index.v1','target_commit':T,'files':payload})
print(json.dumps(summary,ensure_ascii=False,indent=2))
F=R/'commit-files-010';F.mkdir(exist_ok=False)
argv=['C:/Program Files/GitHub CLI/gh.exe','api','--method','GET',f'repos/XenoAmess/ck3_eternal_recurrence/commits/{T}?per_page=100&page=1','--paginate','--slurp','-H','Accept: application/vnd.github+json']
at=datetime.now(timezone.utc).isoformat()
try:p=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=55,check=False);out,err,rc=p.stdout,p.stderr,p.returncode
except subprocess.TimeoutExpired as e:out,err,rc=e.stdout or b'',e.stderr or b'',None
(F/'commit-pages.stdout').write_bytes(out);(F/'commit-pages.stderr').write_bytes(err)
dump(F/'COMMAND.json',{'argv':argv,'at_utc':at,'finished_at_utc':datetime.now(timezone.utc).isoformat(),'exit_code':rc,'stdout_bytes':len(out),'stdout_sha256':sha(out),'stderr_bytes':len(err),'stderr_sha256':sha(err),'environment_policy':'Inherited current process proxy; no settings changed.'})
assert rc==0,'Read failed; attempt retained.'
pages=json.loads(out);assert isinstance(pages,list) and pages and all(p['sha']==T for p in pages)
files=[x for p in pages for x in p.get('files',[])];assert len({x['filename'] for x in files})==len(files)
result={'target_commit':T,'page_count':len(pages),'page_file_counts':[len(p.get('files',[])) for p in pages],'actual_file_records':len(files),'commit_api_maximum_3000_not_reached':len(files)<3000,'parents':[x['sha'] for x in pages[0]['parents']],'product_source_files':[x['filename'] for x in files if x['filename'].startswith('mod_li_yu_dao/')],'relevant_source_files':[x['filename'] for x in files if x['filename'].startswith(('.github/workflows/','ck3_autonomous_player/','mod_li_yu_dao/'))]}
dump(F/'SUMMARY.json',result)
payload=[]
for p in sorted(F.iterdir()):
 if p.is_file():b=p.read_bytes();payload.append({'path':p.name,'bytes':len(b),'sha256':sha(b)})
dump(F/'INDEX.json',{'schema':'lyd.external.evidence.index.v1','target_commit':T,'files':payload})
print(json.dumps({'file_read':result},ensure_ascii=False,indent=2))
