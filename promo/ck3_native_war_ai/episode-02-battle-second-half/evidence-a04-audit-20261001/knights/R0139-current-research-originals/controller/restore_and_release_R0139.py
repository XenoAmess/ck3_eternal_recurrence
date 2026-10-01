from pathlib import Path
import json,subprocess,sys
ROOT=Path(__file__).resolve().parent
BUS=Path('D:/workspace/.codex-task-bus/bin/codex_task_bus.py')
BUS_SHA='B3C44B42F7BDF401B593D863E3210106A46412DCD7D89F8596C74F4C27392DEE'
TASK='war-e2-six-gap-screen-20261001-a01'
old=Path('C:/Users/1/ck3-a04-mechanism-evidence-20261001/root-attempt-03/restore_display_mode_after_capture_a01.py')
text=old.read_text(encoding='utf-8').replace("r/'display-align-2560-a01/preflight.json'","r.parent/'root-attempt-01/display-align-2560-a01/preflight.json'")
with (ROOT/'restore_display_mode_after_capture_a01.py').open('x',encoding='utf-8',newline='\n') as f:f.write(text)
task=json.loads(Path('D:/workspace/.codex-task-bus/tasks/'+TASK+'.json').read_text(encoding='utf-8'))
cmd=[sys.executable,'-X','utf8',str(ROOT/'restore_display_mode_after_capture_a01.py'),'--screen-task-id',TASK,'--expected-sequence',str(task['last_sequence'])]
r=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8')
with (ROOT/'display-restore-process.json').open('x',encoding='utf-8') as f:json.dump({'argv':cmd,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr},f,indent=2)
print(r.stdout+r.stderr)
if r.returncode:raise RuntimeError('Display restore failed; preserve and inspect')
cmd=[sys.executable,str(BUS),'--expected-cli-sha256',BUS_SHA,'release-screen-cas','--task',TASK,'--expected-sequence',str(task['last_sequence']),
     '--summary','R0139_research_pair_captured7_zero_flags_cleanup_and_display_restored']
r=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8')
with (ROOT/'screen-release-CAS.json').open('x',encoding='utf-8') as f:json.dump({'argv':cmd,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr},f,indent=2)
print(r.stdout+r.stderr)
raise SystemExit(r.returncode)
