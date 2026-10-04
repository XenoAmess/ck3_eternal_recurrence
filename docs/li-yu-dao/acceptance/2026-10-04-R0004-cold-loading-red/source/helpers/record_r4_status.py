from pathlib import Path
import json
import subprocess
import sys
BASE=Path(__file__).resolve().parent
RUN=BASE/'live-attempt-004'
REPO=Path('C:/workspace/ck3_eternal_recurrence')
argv=[sys.executable,str(REPO/'tools/ck3_live_run_id.py'),'status','--run-id','bf-202609141645-5434332d4d--li-yu-dao--R0004','--mod','li-yu-dao','--status','completed-red','--reason','R0004-native-loading-errors-normal-window-exit-no-campaign-no-native-attach']
r=subprocess.run(argv,cwd=REPO,capture_output=True,check=False)
for label,data in (('stdout',r.stdout),('stderr',r.stderr)):
    with (RUN/('allocator-completed-red.'+label+'.txt')).open('xb') as stream:
        stream.write(data)
if r.returncode:
    raise RuntimeError('Allocator status failed; retained raw output')
print(r.stdout.decode('utf-8-sig'))
