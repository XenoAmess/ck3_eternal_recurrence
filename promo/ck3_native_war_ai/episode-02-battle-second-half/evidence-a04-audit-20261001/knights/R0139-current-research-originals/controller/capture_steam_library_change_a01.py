import hashlib
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime, timezone
import psutil
import win32gui
import win32process
ROOT=Path(__file__).resolve().parent
LIB=Path('D:/workspace/ck3_native_war_ai_promo_work/desktop-capture-freeze-static-20260927')
sys.path.insert(0,str(LIB/'wgc-lib'))
from windows_capture import WindowsCapture, Frame, InternalCaptureControl
out=ROOT/'wgc-steam-library-change-a01'
out.mkdir(exist_ok=False)
hwnd=197612
_,pid=win32process.GetWindowThreadProcessId(hwnd)
if pid!=7068 or win32gui.GetWindowText(hwnd)!='Steam':
    raise RuntimeError('Steam identity changed')
if any((p.info['name'] or '').lower() in ('ck3.exe','ffmpeg.exe','obs64.exe') for p in psutil.process_iter(['name'])):
    raise RuntimeError('Game or recorder active')
started=datetime.now(timezone.utc).isoformat()
os.startfile('steam://nav/games/details/1086940')
time.sleep(3)
events=[]
capture=WindowsCapture(cursor_capture=False,draw_border=None,window_hwnd=hwnd)
origin=time.monotonic()
last=-2
@capture.event
def on_frame_arrived(frame:Frame, control:InternalCaptureControl):
    global last
    elapsed=time.monotonic()-origin
    if elapsed-last>=2:
        path=out/f'frame-{len(events)+1:02d}.png'
        frame.save_as_image(str(path))
        events.append({'at_utc':datetime.now(timezone.utc).isoformat(),'elapsed':elapsed,'width':frame.width,'height':frame.height,
                       'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest().upper(),'bytes':path.stat().st_size})
        last=elapsed
    if elapsed>=10:
        control.stop()
@capture.event
def on_closed():
    pass
control=capture.start_free_threaded()
time.sleep(12)
control.stop()
if control.is_finished():
    control.wait()
report={'started_at_utc':started,'at_utc':datetime.now(timezone.utc).isoformat(),'hwnd':hwnd,'pid':pid,
        'process_create_time':psutil.Process(pid).create_time(),'semantic_navigation':'steam://nav/games/details/1086940',
        'events':events,'mode_changed':False,'offline_visual_observed':None}
(out/'receipt.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
