"""Observe a single already queued request; never contacts or retries the game."""
from pathlib import Path
import argparse,json,subprocess,sys,time

RUN=Path('C:/workspace/ck3_lyd_runtime_20261004/live-attempt-010')
OUTPUT=RUN/'mcp-client-evidence-002'
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--request-id',required=True)
p.add_argument('--wait-seconds',type=float,default=20)
a=p.parse_args()
assert 0<=a.wait_seconds<=45
deadline=time.monotonic()+a.wait_seconds
while True:
    paths=list(OUTPUT.glob('*-'+a.request_id+'.response.json'))
    assert len(paths)<=1
    if paths:break
    if time.monotonic()>=deadline:
        print(json.dumps(dict(status='RESPONSE_STILL_PENDING_NO_RETRY',request_id=a.request_id)))
        sys.exit(0)
    time.sleep(.2)
record=json.loads(paths[0].read_bytes())
print(json.dumps(record,ensure_ascii=False,indent=2),flush=True)
if record.get('sdk_result'):
    argv=[sys.executable,'-B','-X','utf8',str(RUN.parent/'root_show_r10_sdk_20261005.py'),str(OUTPUT/record['sdk_result'])]
    result=subprocess.run(argv,shell=False,creationflags=subprocess.CREATE_NO_WINDOW)
    sys.exit(result.returncode)
