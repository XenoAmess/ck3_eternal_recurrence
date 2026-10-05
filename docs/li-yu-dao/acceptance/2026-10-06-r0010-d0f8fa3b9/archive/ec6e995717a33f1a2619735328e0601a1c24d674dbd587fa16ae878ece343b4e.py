from pathlib import Path
import json,re,hashlib
R=Path(__file__).parent
T='d0f8fa3b9d444828759443aa018bfd7ad31b398d'
P=R/'lyd-derived-002';P.mkdir(exist_ok=False)
raw=(R/'official-observation-001/raw/job-111708826451-logs.stdout').read_bytes()
plain=re.sub(r'\x1b\[[0-9;?]*[A-Za-z]','',raw.decode('utf-8-sig'))
clean='\n'.join(re.sub(r'^\d{4}-\d{2}-\d{2}T\S+\s','',line) for line in plain.splitlines())
found=[];decoder=json.JSONDecoder()
for m in re.finditer(r'(?m)^\s*\{',clean):
 try:o,end=decoder.raw_decode(clean[m.start():].lstrip())
 except json.JSONDecodeError:continue
 if isinstance(o,dict) and (o.get('result') in ['GREEN','PASS_SOURCE_L0'] or 'runtime_file_count' in o):found.append(o)
def dump(path,obj):
 with path.open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
for i,o in enumerate(found,1):dump(P/f'report-{i:02d}.json',o)
job=json.loads((R/'official-observation-001/raw/run-37293381416-jobs.stdout').read_bytes())['jobs'][0]
assert job['head_sha']==T and job['conclusion']=='success'
counts=[int(x) for x in re.findall(r'Ran (\d+) tests',plain)]
push=[]
for p in sorted((R/'root-push-source-001').glob('*stderr.bin')):
 for line in p.read_bytes().decode('utf-8',errors='replace').splitlines():
  if any(w in line for w in ['Bypassed','signed','master -> master']):push.append({'path':p.relative_to(R).as_posix(),'line':line})
summary={'schema':'lyd.exactd0.actual-stdout.derivation.v1','target_commit':T,'job_id':job['id'],'run_id':job['run_id'],'status':job['status'],'conclusion':job['conclusion'],'started_at':job['started_at'],'completed_at':job['completed_at'],'step_count':len(job['steps']),'conclusion_counts':{k:sum(s.get('conclusion')==k for s in job['steps']) for k in ['success','skipped','failure','cancelled']},'steps':job['steps'],
 'log':{'path':'official-observation-001/raw/job-111708826451-logs.stdout','bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()},
 'actual_unittest_counts':counts,'actual_unittest_total':sum(counts),'failures':re.findall(r'FAILED[^\r\n]*',plain),
 'reports':[{'path':f'lyd-derived-002/report-{i:02d}.json','summary':{k:v for k,v in o.items() if 'count' in k or k in ['result','errors','warnings','native','manifest_sha256','defined_case_full_trigger_AST_exact','event_effect_AST_exact_after_hidden_wrapper','effect_files_byte_identical']}} for i,o in enumerate(found,1)],
 'selected_actual_log_lines':[line for line in clean.splitlines() if any(w in line for w in ['Ran ','manifest_sha256','C3','I3b','optional'])][:80],
 'raw_push_selected_lines':push,'CLA_signature_credit':False,'runtime_credit':False,'product_tests_locally_rerun':False}
dump(P/'SUMMARY.json',summary)
payload=[]
for p in sorted(P.iterdir()):
 if p.is_file():b=p.read_bytes();payload.append({'path':p.name,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
dump(P/'INDEX.json',{'schema':'lyd.external.evidence.index.v1','target_commit':T,'files':payload})
display={k:v for k,v in summary.items() if k not in ['steps']}
print(json.dumps(display,ensure_ascii=False,indent=2))
