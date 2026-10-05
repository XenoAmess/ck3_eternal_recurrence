from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,subprocess,sys
R=Path(__file__).parent
T='d0f8fa3b9d444828759443aa018bfd7ad31b398d'
S=R.parent/'root-c3-commit-push-20261005-001'
P=R/'root-push-source-001';P.mkdir(exist_ok=False)
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(path,obj):
 with path.open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
mapping=[]
for s in sorted(S.iterdir()):
 if s.is_file():
  b=s.read_bytes();d=P/s.name;d.write_bytes(b)
  assert sha(s.read_bytes())==sha(b)
  mapping.append({'source':s.as_posix(),'destination':d.relative_to(R).as_posix(),'bytes':len(b),'sha256':sha(b)})
dump(P/'SOURCE-BINDINGS.json',{'schema':'lyd.external.push.source.binding.v1','CI_target':T,'mappings':mapping})
result=json.loads((P/'RESULT.json').read_bytes())
print('ROOT_PUSH_RESULT_KEYS',list(result))
print(json.dumps(result,ensure_ascii=False,indent=2))
collector=R.parent/'ci-next-head-routing-plan-20261005-001/capture_next_head.py'
argv=[sys.executable,'-B',str(collector),'--target',T,'--output',str(R/'official-observation-001'),'--execute-read-only']
start=datetime.now(timezone.utc).isoformat()
p=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=180,check=False)
(R/'collector-001.stdout').write_bytes(p.stdout);(R/'collector-001.stderr').write_bytes(p.stderr)
dump(R/'COLLECTOR-001-COMMAND.json',{'argv':argv,'at_utc':start,'finished_at_utc':datetime.now(timezone.utc).isoformat(),'exit_code':p.returncode,'stdout_bytes':len(p.stdout),'stdout_sha256':sha(p.stdout),'stderr_bytes':len(p.stderr),'stderr_sha256':sha(p.stderr),'source_test_rerun':False,'workflow_dispatch_or_rerun':False})
print(p.stdout.decode('utf-8',errors='replace'))
print(p.stderr.decode('utf-8',errors='replace'))
sys.exit(p.returncode)
