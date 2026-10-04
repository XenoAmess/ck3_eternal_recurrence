"""Preserve R5 loading errors and request normal window close, never kill."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import psutil
import win32gui
import win32con
import win32process

BASE=Path(__file__).resolve().parent
RUN=BASE/'live-attempt-005'
OUT=RUN/'loading-red-before-exit'
OUT.mkdir(exist_ok=False)
rows=[]
for path in sorted((RUN/'userdir/logs').glob('*')):
    if not path.is_file():
        continue
    data=path.read_bytes()
    target=OUT/path.name
    target.write_bytes(data)
    rows.append({'name':path.name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
hwnd=7406548
thread,pid=win32process.GetWindowThreadProcessId(hwnd)
process=psutil.Process(pid)
if pid!=12524 or process.create_time()!=1791112663.962027:
    raise RuntimeError('Actual R5 target changed')
before={'utc':datetime.now(timezone.utc).isoformat(),'pid':pid,'hwnd':hwnd,'thread':thread,
        'source_head':'18b1944d1784d3e4ec57189c016335ef135b9b34','logs':rows,
        'campaign_started':False,'native_attach':False,'root_ui_input_sent':False,
        'result':'NATIVE_LOADING_RED','close_action':'WM_CLOSE semantic normal window close; no process kill'}
(OUT/'report.json').write_text(json.dumps(before,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
win32gui.PostMessage(hwnd,win32con.WM_CLOSE,0,0)
with (RUN/'normal-close-request.json').open('x',encoding='utf-8') as stream:
    json.dump({'utc':datetime.now(timezone.utc).isoformat(),'pid':pid,'hwnd':hwnd,'action':'posted WM_CLOSE','business_result':'REQUIRES_ACTUAL_EXIT_READBACK'},stream,indent=2)
print(json.dumps({'result':'NORMAL_CLOSE_REQUESTED_NOT_YET_EXIT_PROVEN','captured_files':len(rows),'evidence':str(OUT)}))
