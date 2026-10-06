"""Bounded read-only OneDrive process/config/window diagnosis; never cloud content."""
import ctypes
from ctypes import wintypes
import datetime
import json
import os
from pathlib import Path
import subprocess
import winreg

def stamp():
    return datetime.datetime.now(datetime.UTC).isoformat()

result = {"utc": stamp(), "scope": "read-only local client process/config/window; no cloud content and no input", "metadata_query_performed": False}
task = subprocess.run(["tasklist.exe", "/FI", "IMAGENAME eq OneDrive.exe", "/FO", "CSV", "/NH"], capture_output=True, timeout=15)
import csv, io
rows = list(csv.reader(io.StringIO(task.stdout.decode("mbcs", errors="replace"))))
pids = [int(r[1]) for r in rows if len(r)>1 and r[0].lower()=="onedrive.exe" and r[1].isdigit()]
result["onedrive_process_ids"] = pids
result["tasklist_returncode"] = task.returncode
try:
    import psutil
    result["psutil_available"] = True
    processes = []
    for pid in pids:
        p = psutil.Process(pid)
        rec = {"pid":pid, "status":p.status(), "created_utc":datetime.datetime.fromtimestamp(p.create_time(),datetime.UTC).isoformat(), "executable":p.exe()}
        try:
            conn = p.net_connections(kind="inet")
            rec["inet_connections_by_status"] = {s:sum(c.status==s for c in conn) for s in sorted({c.status for c in conn})}
        except Exception as exc:
            rec["connection_query_error_type"] = type(exc).__name__
        processes.append(rec)
    result["processes"] = processes
except ImportError:
    result["psutil_available"] = False

u32 = ctypes.WinDLL("user32",use_last_error=True)
u32.GetWindowThreadProcessId.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.DWORD)]
u32.GetWindowTextLengthW.argtypes=[wintypes.HWND]
u32.GetWindowTextW.argtypes=[wintypes.HWND,wintypes.LPWSTR,ctypes.c_int]
u32.GetClassNameW.argtypes=[wintypes.HWND,wintypes.LPWSTR,ctypes.c_int]
u32.IsWindowVisible.argtypes=[wintypes.HWND]
windows=[]
@ctypes.WINFUNCTYPE(wintypes.BOOL,wintypes.HWND,wintypes.LPARAM)
def visit(hwnd, param):
    pid = wintypes.DWORD()
    u32.GetWindowThreadProcessId(hwnd,ctypes.byref(pid))
    if pid.value in pids:
        text=ctypes.create_unicode_buffer(2048)
        cls=ctypes.create_unicode_buffer(256)
        u32.GetWindowTextW(hwnd,text,len(text))
        u32.GetClassNameW(hwnd,cls,len(cls))
        # Do not print arbitrary titles: classify status words only.
        title=text.value.lower()
        flags=[s for s in ["onedrive","paused","sign in","signed out","error","sync","暂停","登录","错误","同步"] if s in title]
        windows.append({"hwnd":int(hwnd),"pid":pid.value,"class":cls.value,"visible":bool(u32.IsWindowVisible(hwnd)),"title_status_markers":flags})
    return True
u32.EnumWindows.argtypes=[ctypes.c_void_p,wintypes.LPARAM]
u32.EnumWindows(visit,0)
result["onedrive_windows"] = windows

keys=[r"Software\Microsoft\OneDrive",r"Software\Microsoft\OneDrive\Accounts\Personal"]
reg=[]
safe_names={"userfolder","paused","pausesync","pausestarttime","pausetimeseconds","pauseendtime","lastsignintime","disablepersonalSync".lower(),"onedriveautostart","configuredtenantid"}
for path in keys:
    rec={"key":path,"exists":False}
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,path,0,winreg.KEY_READ) as key:
            rec["exists"]=True
            count=winreg.QueryInfoKey(key)[1]
            values=[]
            for i in range(min(count,100)):
                name,value,typ=winreg.EnumValue(key,i)
                low=name.lower()
                if low in safe_names:
                    if low=="configuredtenantid":
                        values.append({"name":name,"nonempty":bool(value)})
                    elif low=="userfolder":
                        values.append({"name":name,"matches_expected_root":str(value).replace("\\","/").rstrip("/").lower()=="c:/users/1/onedrive"})
                    else:
                        values.append({"name":name,"value":value})
            rec["safe_values"]=values
            rec["all_value_names"]=sorted(winreg.EnumValue(key,i)[0] for i in range(min(count,100)))
    except OSError as exc:
        rec["error_winerror"]=getattr(exc,"winerror",None)
    reg.append(rec)
result["registry"] = reg

local=Path(os.environ.get("LOCALAPPDATA",r"C:\Users\1\AppData\Local"))/"Microsoft"/"OneDrive"
entries=[]
for rel in ["settings/Personal","logs/Personal","logs/Common"]:
    directory=local/rel
    rec={"directory":rel,"exists":directory.is_dir()}
    if directory.is_dir():
        stats=[]
        for entry in directory.iterdir():
            if entry.is_file():
                s=entry.stat()
                # Filename may contain CID/account IDs; expose only fixed/generic stem.
                name=entry.name if not any(ch.isdigit() for ch in entry.stem) or entry.name in {"SyncDiagnostics.log","global.ini","ClientPolicy.ini"} else "[redacted-id]"+entry.suffix
                stats.append({"name":name,"bytes":s.st_size,"modified_utc":datetime.datetime.fromtimestamp(s.st_mtime,datetime.UTC).isoformat(),"mtime":s.st_mtime})
        stats.sort(key=lambda x:x["mtime"],reverse=True)
        for s in stats[:10]:
            s.pop("mtime")
        rec["recent_entries"] = stats[:10]
    entries.append(rec)
result["local_client_files"] = entries

# Only bounded local plaintext status logs/configs; no account values or filename paths.
texts=[]
for rel in ["settings/Personal/global.ini","logs/Personal/SyncDiagnostics.log","logs/Common/SyncDiagnostics.log"]:
    p=local/rel
    if p.is_file():
        size=p.stat().st_size
        if size<=1_000_000:
            data=p.read_bytes()
            decoded=data.decode("utf-16" if data.startswith((b"\xff\xfe",b"\xfe\xff")) else "utf-8",errors="replace")
            safe=[]
            for line in decoded.splitlines():
                if "=" in line:
                    key,value=line.split("=",1)
                    key=key.strip()
                    if key.lower() in {"paused","pausesync","pausestarttime","pauseendtime","pauseforbattery","pauseonmeterednetwork","status","syncstatus","clientversion","version","errors","errorcount","numfilesuploading","numfilespending","uploadcount","downloadcount"}:
                        if len(value.strip())<120 and not any(t in value.lower() for t in ["@","token","password","http","\\","/"]):
                            safe.append({"key":key,"value":value.strip()})
            texts.append({"local_file":rel,"bytes":size,"safe_state_fields":safe[:100],"status_words_counts":{w:decoded.lower().count(w) for w in ["paused","pause","resum","error","offline","upload","download","authenticated","signed out"]}})
        else:
            texts.append({"local_file":rel,"bytes":size,"read_skipped":"bounded limit"})
result["bounded_local_plaintext"] = texts
out=Path(__file__).parent/"01-readonly-client-state.json"
with out.open("x",encoding="utf-8") as f:
    json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps(result,ensure_ascii=False,indent=2))
