"""Only read existing OneDrive controls; no invocation, focus, input or cloud content."""
import datetime
import json
import re
from pathlib import Path
import uiautomation as auto

TARGET="CK3-War-AI-Episode04-March-Logistics-Review01.mp4"
out=Path(__file__).parent/"02-existing-uia-status.json"
result={"utc":datetime.datetime.now(datetime.UTC).isoformat(),"scope":"existing OneDrive UIA read-only; no invoke or focus","metadata_query_performed":False,"target":TARGET,"onedrive_window_status":[],"tray_status":[]}

def safe(value):
    text=str(value)
    text=re.sub(r"[A-Za-z0-9_.+%-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}","[redacted-account]",text)
    text=re.sub(r"https?://\S+","[redacted-url]",text)
    return text[:1000]

def rows(control,depth=0):
    if depth>10:
        return
    yield control
    for child in control.GetChildren():
        yield from rows(child,depth+1)

root=auto.GetRootControl()
for win in root.GetChildren():
    cls=win.ClassName
    if cls=="OneDriveReactNativeWin32WindowClass":
        rec={"hwnd":win.NativeWindowHandle,"statusText":[],"target_rows":[],"status_markers":[]}
        for ctrl in rows(win):
            name=ctrl.Name or ""
            aid=ctrl.AutomationId or ""
            if aid=="statusText":
                rec["statusText"].append({"name":safe(name),"type":ctrl.ControlTypeName})
            if TARGET in name:
                rec["target_rows"].append({"name":safe(name),"automation_id":aid,"type":ctrl.ControlTypeName})
            low=name.lower()
            markers=[m for m in ["暂停同步","恢复同步","同步已暂停","paused","resume syncing","正在同步","正在上传","uploading","up to date","最新","没有连接","not connected","脱机","offline","需要登录","sign in","同步错误","sync error","存储空间已满","storage is full","处理更改","processing changes"] if m in low]
            if markers:
                rec["status_markers"].append({"markers":markers,"automation_id":aid,"type":ctrl.ControlTypeName})
        result["onedrive_window_status"].append(rec)
    elif cls=="Shell_TrayWnd":
        for ctrl in rows(win,depth=5):
            name=ctrl.Name or ""
            if "onedrive" in name.lower():
                result["tray_status"].append({"name":safe(name),"automation_id":ctrl.AutomationId,"type":ctrl.ControlTypeName})

local=Path(r"C:/Users/1/AppData/Local/Microsoft/OneDrive")
diag=local/"logs/Personal/SyncDiagnostics.log"
if diag.is_file() and diag.stat().st_size<100000:
    data=diag.read_bytes()
    text=data.decode("utf-16" if data.startswith((b"\xff\xfe",b"\xfe\xff")) else "utf-8",errors="replace")
    states=[]
    for line in text.splitlines():
        if "=" in line:
            key,value=line.split("=",1)
            if re.fullmatch(r"[\w .-]{1,100}",key.strip()) and re.fullmatch(r"[-+0-9., %]+|true|false",value.strip(),flags=re.I):
                if any(w in key.lower() for w in ["upload","download","error","pause","pending","sync","state","status","connection","scan","bytes","filecount"]):
                    states.append({"key":key.strip(),"value":value.strip()})
    result["local_diagnostics_numeric_status"] = {"mtime_utc":datetime.datetime.fromtimestamp(diag.stat().st_mtime,datetime.UTC).isoformat(),"fields":states}
uploads=local/"settings/Personal/uploads.txt"
if uploads.is_file() and uploads.stat().st_size<100000:
    data=uploads.read_bytes()
    variants=[data.decode(e,errors="ignore") for e in ["utf-8","utf-16le"]]
    result["local_uploads_record"]={"bytes":len(data),"mtime_utc":datetime.datetime.fromtimestamp(uploads.stat().st_mtime,datetime.UTC).isoformat(),"exact_target_name_present":any(TARGET in t for t in variants)}
with out.open("x",encoding="utf-8") as f:
    json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps(result,ensure_ascii=False,indent=2))
