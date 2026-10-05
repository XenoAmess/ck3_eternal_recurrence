from pathlib import Path
import json,base64,hashlib
R=Path(__file__).parent
for folder in ['general-observation-003','commit-files-004']:
 p=R/folder
 records=list((p/'commands').glob('*.json')) if (p/'commands').exists() else list(p.glob('COMMAND.json'))
 for q in records:
  obj=json.loads(q.read_bytes())
  print(json.dumps({'record':q.relative_to(R).as_posix(),'exit_code':obj.get('exit_code'),'at_utc':obj.get('at_utc'),'finished_at_utc':obj.get('finished_at_utc'),'stdout_bytes':obj.get('stdout_bytes'),'stderr_bytes':obj.get('stderr_bytes')},ensure_ascii=False))
  rawfolder=p/'raw' if (p/'raw').exists() else p
  if obj.get('exit_code')!=0:
   for e in rawfolder.glob('*.stderr'):print(e.name,e.read_bytes().decode('utf-8',errors='replace')[:600])
for name in ['static-ci.yml','li-yu-dao-static.yml','cla.yml']:
 obj=json.loads((R/f'official-observation-001/raw/definition-{name}.stdout').read_bytes());b=base64.b64decode(obj['content'])
 print(json.dumps({'workflow':name,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'git_blob':obj['sha']}))
print('local_inputs_only_no_network_or_tests')
