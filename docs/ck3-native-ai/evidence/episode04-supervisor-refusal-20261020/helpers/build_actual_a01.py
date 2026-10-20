from datetime import datetime,timezone
from pathlib import Path
import hashlib,json,subprocess,sys
root=Path('D:/workspace/ck3_eternal_recurrence')
base=Path('C:/ck3-e04-resume-20261020-a01')
out=base/'r06-resume-a02/supervisor-refusal-fix-a01/builder-exec-a01'
out.mkdir(exist_ok=False)
argv=[str(root/'tools/.venv/Scripts/python.exe'),'-B','-X','utf8',str(root/'tools/ck3_mod_acceptance_supervisor_refusal.py'),
 '--previous-live',str(base/'r06-scene-a02/driver-runs/desktop-3fevhd2-1c74096080--vanilla--R0218'),
 '--keeper-root',str(base/'r06-scene-a02/keeper-a01'),
 '--public-run-wait',str(base/'r06-resume-a02/run-exec-a01/ORIGINAL-WAIT.actual.json'),
 '--public-allocate-wait',str(base/'r06-resume-a02/allocate-exec-a02/ORIGINAL-WAIT.actual.json'),
 '--release',str(base/'r06-scene-a02/SCREEN-RELEASE.actual-a01.json'),
 '--task-bus-root','D:/workspace/.codex-task-bus',
 '--output',str(out/'SUPERVISOR-ADMISSION-REFUSED.actual.json')]
started=datetime.now(timezone.utc).isoformat()
with (out/'stdout.log').open('xb') as stdout,(out/'stderr.log').open('xb') as stderr:
 child=subprocess.Popen(argv,cwd=root,stdout=stdout,stderr=stderr)
 code=child.wait()
row={'machine_id':'desktop-3fevhd2-1c74096080','started_at_utc':started,'observed_at_utc':datetime.now(timezone.utc).isoformat(),
 'argv':argv,'pid':child.pid,'actual_original_popen_wait':True,'returncode':code,'game_or_SDK_action':False}
def pin(path):
 b=path.read_bytes();return {'path':str(path.resolve()),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
row['source_pins']=[pin(root/p) for p in ('tools/ck3_mod_acceptance_supervisor_refusal.py','tools/ck3_mod_acceptance_allocate.py')]
(out/'ORIGINAL-WAIT.actual.json').write_text(json.dumps(row,indent=2)+'\n',encoding='utf-8')
print(json.dumps(row,indent=2));print((out/'stderr.log').read_text(encoding='utf-8-sig'))
sys.exit(code)
