from pathlib import Path
import json,re,hashlib
R=Path(__file__).parent
P=R/'general-derived-008';P.mkdir(exist_ok=False)
T='d0f8fa3b9d444828759443aa018bfd7ad31b398d'
raw=(R/'general-observation-006/raw/general-logs.stdout').read_bytes()
plain=re.sub(r'\x1b\[[0-9;?]*[A-Za-z]','',raw.decode('utf-8-sig'))
lines=[re.sub(r'^\d{4}-\d{2}-\d{2}T\S+\s','',line) for line in plain.splitlines()];clean='\n'.join(lines)
def dump(path,obj):
 with path.open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
found=[];decoder=json.JSONDecoder()
for m in re.finditer(r'(?m)^\s*\{',clean):
 try:o,end=decoder.raw_decode(clean[m.start():].lstrip())
 except json.JSONDecodeError:continue
 if isinstance(o,dict) and (o.get('result') in ['GREEN','PASS_SOURCE_L0'] or 'runtime_file_count' in o):found.append(o)
for i,o in enumerate(found,1):dump(P/f'report-{i:02d}.json',o)
job=json.loads((R/'general-observation-006/raw/general-jobs.stdout').read_bytes())['jobs'][0]
assert job['head_sha']==T and job['conclusion']=='failure'
marks=[i for i,line in enumerate(lines) if any(x in line for x in ['Traceback (most recent call last)','FAILED (','AssertionError:','##[error]','Error:','FAILED:','[FAIL]'])]
snips=[]
for i in marks:
 snips.append({'line_1based':i+1,'text':'\n'.join(lines[max(0,i-4):min(len(lines),i+16)])})
summary={'schema':'lyd.exactd0.actual-general-stdout.v1','target_commit':T,'job_id':job['id'],'run_id':job['run_id'],'conclusion':job['conclusion'],'completed_at':job['completed_at'],'step_count':len(job['steps']),'conclusion_counts':{k:sum(s.get('conclusion')==k for s in job['steps']) for k in ['success','skipped','failure','cancelled']},
 'failed_steps':[s for s in job['steps'] if s.get('conclusion')=='failure'],'steps':job['steps'],
 'stdout':{'path':'general-observation-006/raw/general-logs.stdout','bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()},
 'actual_unittest_suite_counts':[int(x) for x in re.findall(r'Ran (\d+) tests',plain)],
 'actual_failure_snippets':snips,
 'specific_source_steps':[s for s in job['steps'] if any(x in s['name'].lower() for x in ['broker','history'])],
 'actual_report_objects':[{'path':f'general-derived-008/report-{i:02d}.json','summary':{k:v for k,v in o.items() if 'count' in k or k in ['result','errors','warnings','native','manifest_sha256']}} for i,o in enumerate(found,1)],
 'scope':'Only this exact completed job actual stdout; no future source or game outcome inference.'}
dump(P/'SUMMARY.json',summary)
(P/'TAIL.txt').write_bytes(('\n'.join(lines[-100:])+'\n').encode('utf-8'))
payload=[]
for path in sorted(P.iterdir()):
 if path.is_file():b=path.read_bytes();payload.append({'path':path.name,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
dump(P/'INDEX.json',{'schema':'lyd.external.evidence.index.v1','target_commit':T,'files':payload})
print(json.dumps({k:v for k,v in summary.items() if k not in ['steps','actual_report_objects']},ensure_ascii=False,indent=2))
