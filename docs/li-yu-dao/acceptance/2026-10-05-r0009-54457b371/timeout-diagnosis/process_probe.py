import ctypes
import json
import sys
from ctypes import wintypes
from datetime import datetime, timezone
from pathlib import Path

out = Path(__file__).parent/'process-probe-001.json'
result = {'start_utc':datetime.now(timezone.utc).isoformat(), 'python':sys.executable, 'policy':'read only process, thread, and window queries; no messages, input, pause, kill, attach, pipe connection, or MCP'}
try:
    import psutil
    processes=[]
    for proc in psutil.process_iter(['pid','name','ppid','exe','create_time','cmdline','status','num_threads','cpu_times']):
        info=proc.info
        cmd=' '.join(info.get('cmdline') or [])
        if info['pid']==20264 or any(s in cmd for s in ('persistent_native_mcp_queue_21.py','ck3_native_profile_mcp.py','root_r9_start_mcp_20261005.py')):
            for field,value in list(info.items()):
                if hasattr(value,'_asdict'):
                    info[field]=value._asdict()
            try:
                info['threads']=[v._asdict() for v in proc.threads()]
            except Exception as exc:
                info['thread_query_error']=repr(exc)
            processes.append(info)
    result['processes']=processes
except Exception as exc:
    result['psutil_error']=repr(exc)
user32=ctypes.WinDLL('user32',use_last_error=True)
user32.GetWindowThreadProcessId.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.DWORD)]
user32.GetWindowThreadProcessId.restype=wintypes.DWORD
user32.IsWindow.argtypes=[wintypes.HWND]
user32.IsWindow.restype=wintypes.BOOL
user32.IsWindowVisible.argtypes=[wintypes.HWND]
user32.IsWindowVisible.restype=wintypes.BOOL
user32.IsHungAppWindow.argtypes=[wintypes.HWND]
user32.IsHungAppWindow.restype=wintypes.BOOL
user32.GetForegroundWindow.restype=wintypes.HWND
user32.GetWindowTextW.argtypes=[wintypes.HWND,wintypes.LPWSTR,ctypes.c_int]
user32.GetWindowTextW.restype=ctypes.c_int
user32.GetClassNameW.argtypes=[wintypes.HWND,wintypes.LPWSTR,ctypes.c_int]
user32.GetClassNameW.restype=ctypes.c_int
user32.GetWindowRect.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.RECT)]
user32.GetWindowRect.restype=wintypes.BOOL
hwnd=5637378
owner=wintypes.DWORD()
thread_id=user32.GetWindowThreadProcessId(hwnd,ctypes.byref(owner))
title=ctypes.create_unicode_buffer(1024)
clazz=ctypes.create_unicode_buffer(1024)
rect=wintypes.RECT()
user32.GetWindowTextW(hwnd,title,len(title))
user32.GetClassNameW(hwnd,clazz,len(clazz))
rect_ok=user32.GetWindowRect(hwnd,ctypes.byref(rect))
result['window']={'hwnd':hwnd,'exists':bool(user32.IsWindow(hwnd)),'visible':bool(user32.IsWindowVisible(hwnd)),'owner_pid':owner.value,'owner_thread':thread_id,'is_hung_app_window':bool(user32.IsHungAppWindow(hwnd)),'title':title.value,'class':clazz.value,'foreground_hwnd':user32.GetForegroundWindow(),'rect':[rect.left,rect.top,rect.right,rect.bottom] if rect_ok else None}
result['end_utc']=datetime.now(timezone.utc).isoformat()
with out.open('x',encoding='utf-8') as stream:
    json.dump(result,stream,ensure_ascii=False,indent=2)
    stream.write('\n')
print(json.dumps({'output':str(out),'window':result['window'],'processes':[{k:v for k,v in p.items() if k!='threads'}|{'thread_14852':next((t for t in p.get('threads',[]) if t['id']==14852),None)} for p in result.get('processes',[])],'error':result.get('psutil_error')},ensure_ascii=False,indent=2))
