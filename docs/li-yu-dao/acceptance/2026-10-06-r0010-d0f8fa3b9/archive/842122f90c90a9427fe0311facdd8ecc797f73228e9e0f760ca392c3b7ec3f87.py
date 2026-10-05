from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import argparse,json,subprocess,hashlib
R=Path(__file__).parent
T='d0f8fa3b9d444828759443aa018bfd7ad31b398d'
RUN=37293381666;JOB=111708827682
args=argparse.ArgumentParser();args.add_argument('--observation',required=True);ns=args.parse_args()
assert ns.observation.isalnum() or (ns.observation.replace('-','').isalnum())
P=R/ns.observation;P.mkdir(exist_ok=False);(P/'raw').mkdir();(P/'commands').mkdir()
repo='repos/XenoAmess/ck3_eternal_recurrence';GH='C:/Program Files/GitHub CLI/gh.exe'
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(path,obj):
 with path.open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
def get(item):
 name,endpoint,asjson=item
 argv=[GH,'api','--method','GET',endpoint]
 if asjson:argv+=['-H','Accept: application/vnd.github+json']
 else:argv+=['--allow-escape-sequences']
 start=datetime.now(timezone.utc).isoformat()
 try:p=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=55,check=False);out,err,rc=p.stdout,p.stderr,p.returncode
 except subprocess.TimeoutExpired as e:out,err,rc=e.stdout or b'',e.stderr or b'',None
 (P/'raw'/f'{name}.stdout').write_bytes(out);(P/'raw'/f'{name}.stderr').write_bytes(err)
 record={'argv':argv,'at_utc':start,'finished_at_utc':datetime.now(timezone.utc).isoformat(),'exit_code':rc,'stdout_bytes':len(out),'stdout_sha256':sha(out),'stderr_bytes':len(err),'stderr_sha256':sha(err),'environment':'Inherited current process proxy; no settings changed.'}
 dump(P/'commands'/f'{name}.json',record)
 return name,record,json.loads(out) if rc==0 and asjson else None
def batch(items):
 with ThreadPoolExecutor(max_workers=6) as pool:return dict((name,(record,obj)) for name,record,obj in pool.map(get,items))
first=batch([('general-run',f'{repo}/actions/runs/{RUN}',True),('master-tip',f'{repo}/branches/master',True),('general-jobs',f'{repo}/actions/runs/{RUN}/jobs?per_page=100',True)])
assert all(r['exit_code']==0 for r,o in first.values()),'Read failed; attempt retained.'
run=first['general-run'][1];jobs=first['general-jobs'][1]['jobs'];assert run['head_sha']==T and all(x['head_sha']==T for x in jobs)
assert len(jobs)==1 and jobs[0]['id']==JOB
terminal=run['status']=='completed' and all(x['status']=='completed' for x in jobs)
extra={}
if terminal:
 extra=batch([('runs',f'{repo}/actions/runs?head_sha={T}&per_page=100',True),('checks',f'{repo}/commits/{T}/check-runs?per_page=100',True),('statuses',f'{repo}/commits/{T}/statuses?per_page=100',True),('general-suite',f'{repo}/check-suites/{run["check_suite_id"]}',True),('general-artifacts',f'{repo}/actions/runs/{RUN}/artifacts?per_page=100',True),('general-annotations',f'{repo}/check-runs/{JOB}/annotations?per_page=100',True),('general-logs',f'{repo}/actions/jobs/{JOB}/logs',False)])
 assert all(r['exit_code']==0 for r,o in extra.values()),'Terminal read failed; attempt retained.'
 summaryruns=extra['runs'][1]['workflow_runs'];summarychecks=extra['checks'][1]['check_runs']
 assert all(x['head_sha']==T for x in summaryruns+summarychecks)
else:summaryruns=[];summarychecks=[]
summary={'schema':'lyd.exactd0.general-observation.v1','target_commit':T,'at_utc':datetime.now(timezone.utc).isoformat(),'general':{k:run.get(k) for k in ['id','name','head_sha','status','conclusion','event','run_attempt','updated_at','html_url']},'general_job':jobs[0],'terminal_response_set_complete':terminal,
 'all_runs':[{k:x.get(k) for k in ['id','name','head_sha','status','conclusion','event','run_attempt','updated_at','html_url']} for x in summaryruns],
 'all_checks':[{k:x.get(k) for k in ['id','name','head_sha','status','conclusion','completed_at','html_url']} for x in summarychecks],
 'statuses':extra['statuses'][1] if terminal else None,
 'actual_master_tip':first['master-tip'][1]['commit']['sha'],'target_is_master_tip_at_observation':first['master-tip'][1]['commit']['sha']==T,'runtime_credit':False,'workflow_dispatch_or_rerun':False}
dump(P/'SUMMARY.json',summary)
files=[]
for path in sorted(P.rglob('*')):
 if path.is_file():b=path.read_bytes();files.append({'path':path.relative_to(P).as_posix(),'bytes':len(b),'sha256':sha(b)})
dump(P/'INDEX.json',{'schema':'lyd.external.evidence.index.v1','target_commit':T,'files':files})
display={k:v for k,v in summary.items() if k!='general_job'};display['job_progress']={'id':JOB,'status':jobs[0]['status'],'conclusion':jobs[0]['conclusion'],'step_count':len(jobs[0]['steps']),'step_conclusion_counts':{k:sum(x.get('conclusion')==k for x in jobs[0]['steps']) for k in ['success','skipped','failure','cancelled',None]},'current_steps':[x for x in jobs[0]['steps'] if x['status']!='completed'][:2]}
print(json.dumps(display,ensure_ascii=False,indent=2))
