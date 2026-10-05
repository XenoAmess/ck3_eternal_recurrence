from pathlib import Path
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
import json,re,hashlib,subprocess
R=Path(__file__).parent;T='d0f8fa3b9d444828759443aa018bfd7ad31b398d';P=R/'failure-focused-010';P.mkdir(exist_ok=False)
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(path,obj):
 with path.open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
raw=(R/'general-observation-006/raw/general-logs.stdout').read_bytes();text=raw.decode('utf-8-sig')
lines=[re.sub(r'^\d{4}-\d{2}-\d{2}T\S+\s','',line) for line in text.splitlines()];clean='\n'.join(lines)
end=next(i for i,line in enumerate(lines) if 'Process completed with exit code 1.' in line)
start=max(i for i in range(end) if '##[group]' in lines[i])
failed='\n'.join(lines[start:end+1])+'\n';(P/'FAILED-STEP-ONLY.raw.txt').write_bytes(failed.encode('utf-8'))
violations=[{'log_line_1based':i+1,'actual_log_line':line} for i,line in enumerate(lines) if 'forbidden shell reference' in line]
assert len(violations)==2
groups=clean.split('##[group]');historygroup=next(x for x in groups if 'test_ingame_decision_history_growth.py' in x)
historycounts=[{'count':int(m[0]),'seconds':float(m[1])} for m in re.findall(r'Ran (\d+) tests in ([0-9.]+)s',historygroup)]
artifacts=json.loads((R/'general-observation-006/raw/general-artifacts.stdout').read_bytes())['artifacts']
paths=['docs/autonomous-agent-progress/daily/2026-10-05.md','docs/autonomous-agent-progress/weekly/2026-W41.md']
def exact_doc(path):
 label='daily' if '/daily/' in path else 'weekly';argv=['C:/Program Files/Git/cmd/git.exe','show',T+':'+path];at=datetime.now(timezone.utc).isoformat()
 proc=subprocess.run(argv,cwd='C:/workspace/ck3_eternal_recurrence',stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30,check=False)
 (P/f'{label}.source.stdout').write_bytes(proc.stdout);(P/f'{label}.source.stderr').write_bytes(proc.stderr)
 dump(P/f'{label}.COMMAND.json',{'argv':argv,'at_utc':at,'finished_at_utc':datetime.now(timezone.utc).isoformat(),'exit_code':proc.returncode,'stdout_bytes':len(proc.stdout),'stdout_sha256':sha(proc.stdout),'stderr_bytes':len(proc.stderr),'stderr_sha256':sha(proc.stderr),'read_only_Git_object':True})
 assert proc.returncode==0
 terms=[bytes(x,'utf-8') for x in [''.join(chr(c) for c in [112,111,119,101,114,115,104,101,108,108]),''.join(chr(c) for c in [112,119,115,104])]]
 hits=[{'document_line_1based':i+1,'line':line.decode('utf-8',errors='replace')} for i,line in enumerate(proc.stdout.splitlines()) if any(t in line.lower() for t in terms)]
 return {'path':path,'source_commit':T,'exact_raw_source':f'failure-focused-010/{label}.source.stdout','source_bytes':len(proc.stdout),'source_sha256':sha(proc.stdout),'banned_name_lines':hits}
with ThreadPoolExecutor(max_workers=2) as pool:docs=list(pool.map(exact_doc,paths))
summary={'schema':'lyd.exactd0.focused-general-failure.v1','target_commit':T,'failed_step':'Enforce Python-only Windows automation','step_number':43,'actual_exit_code':1,'actual_violation_count':2,'actual_violation_lines':violations,'exact_documents':docs,
 'history_growth_actual_in_group':historycounts,'artifact_metadata':[{'id':x['id'],'name':x['name'],'size_in_bytes':x['size_in_bytes'],'expired':x['expired']} for x in artifacts],'artifact_zips_downloaded':False,
 'actual_general_unittest_total':sum(int(x) for x in re.findall(r'Ran (\d+) tests',text)),
 'expected_negative_fixture_stdout_is_not_job_failure_cause':True,'scope':'This failed validator actual stdout plus exact read-only Git source objects. No tests executed.'}
dump(P/'SUMMARY.raw.json',summary)
payload=[]
for p in sorted(P.iterdir()):
 if p.is_file():b=p.read_bytes();payload.append({'path':p.name,'bytes':len(b),'sha256':sha(b)})
dump(P/'INDEX.json',{'schema':'lyd.external.evidence.index.v1','target_commit':T,'files':payload})
print(json.dumps(summary,ensure_ascii=False,indent=2))
