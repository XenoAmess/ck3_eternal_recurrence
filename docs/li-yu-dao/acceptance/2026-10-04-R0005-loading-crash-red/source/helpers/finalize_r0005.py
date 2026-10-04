"""Finish a normally closed R5 loading-RED attempt; stop lease then CAS release."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import subprocess
import sys
import time
import psutil

BASE=Path(__file__).resolve().parent
REPO=Path('C:/workspace/ck3_eternal_recurrence')
RUN=BASE/'live-attempt-005'
LEASE=BASE/'screen-lease-live-r0005'
BUS=Path('C:/workspace/.codex-task-bus/bin/codex_task_bus.py')
TASK='ck3-lyd-live-006-20261004'
def write(name,payload):
    with (RUN/name).open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(payload,stream,ensure_ascii=False,indent=2)
        stream.write('\n')
rows=[p.info for p in psutil.process_iter(['pid','name','exe','create_time']) if (p.info.get('name') or '').lower()=='ck3.exe']
write('normal-exit-processes-001.json',{'utc':datetime.now(timezone.utc).isoformat(),'ck3_processes':rows,'pid_12524_present':psutil.pid_exists(12524),'normal_close_request':'normal-close-request.json','campaign_or_save':'NOT_STARTED'})
if rows or psutil.pid_exists(12524):
    raise RuntimeError('R5 or another CK3 process still exists')
with (LEASE/'STOP.request').open('x',encoding='utf-8') as stream:
    stream.write('Normal window close complete after loading RED; stop keeper before CAS release.\n')
for _ in range(15):
    if (LEASE/'FINAL.json').is_file():
        break
    time.sleep(1)
final=json.loads((LEASE/'FINAL.json').read_text(encoding='utf-8'))
if final.get('failure') or final.get('entry_error') or final.get('thread_exited') is not True:
    raise RuntimeError('Keeper stop is not proven clean; do not release')
write('keeper-final.snapshot.json',final)
argv=[sys.executable,str(BUS),'--expected-cli-sha256',hashlib.sha256(BUS.read_bytes()).hexdigest().upper(), 'release-screen-cas','--task',TASK,'--expected-sequence',str(final['last_sequence']),'--summary','R0005-native-loading-RED-normal-window-exit-no-campaign']
r=subprocess.run(argv,cwd=REPO,capture_output=True,check=False)
(RUN/'release-screen.stdout.json').write_bytes(r.stdout)
(RUN/'release-screen.stderr.txt').write_bytes(r.stderr)
if r.returncode:
    raise RuntimeError('CAS release failed; raw receipts retained')
release=json.loads(r.stdout.decode('utf-8-sig'))
write('screen-release-completed.json',release)
print(json.dumps({'normal_exit':True,'keeper_thread_exited':True,'final_sequence':final['last_sequence'],'release_sequence':release['task']['last_sequence'],'resources':release['task']['resources']}))
