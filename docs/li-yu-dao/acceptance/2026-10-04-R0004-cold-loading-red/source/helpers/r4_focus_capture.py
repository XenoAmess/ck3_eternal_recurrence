"""Focus the actual R4 window semantically, then capture a fresh raw frame."""
from pathlib import Path
import json
import subprocess
import sys
import win32gui
import win32process
import psutil
import win32api

BASE=Path(__file__).resolve().parent
RUN=BASE/'live-attempt-004'
hwnd=2295626
thread,pid=win32process.GetWindowThreadProcessId(hwnd)
if pid!=19184 or not win32gui.IsWindowVisible(hwnd) or psutil.Process(pid).create_time()!=1791105678.3486943:
    raise RuntimeError('R4 target identity changed')
win32gui.ShowWindow(hwnd, 9)
foreground=win32gui.GetForegroundWindow()
foreground_thread,_=win32process.GetWindowThreadProcessId(foreground)
current_thread=win32api.GetCurrentThreadId()
attached=current_thread!=foreground_thread
if attached:
    win32process.AttachThreadInput(current_thread,foreground_thread,True)
try:
    win32gui.SetForegroundWindow(hwnd)
finally:
    if attached:
        win32process.AttachThreadInput(current_thread,foreground_thread,False)
if win32gui.GetForegroundWindow()!=hwnd:
    raise RuntimeError('R4 foreground focus was not established')
with (RUN/(sys.argv[1]+'.focus.json')).open('x',encoding='utf-8') as stream:
    json.dump({'hwnd':hwnd,'pid':pid,'thread':thread,'foreground_hwnd':win32gui.GetForegroundWindow(),'action':'semantic window focus; no keyboard/mouse input'},stream,indent=2)
subprocess.run([sys.executable,str(BASE/'live_control_r0004.py'),'frame',sys.argv[1]],check=True)
