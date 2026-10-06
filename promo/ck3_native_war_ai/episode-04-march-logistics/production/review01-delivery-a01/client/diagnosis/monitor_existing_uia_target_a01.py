"""One bounded, read-only sample of existing OneDrive UIA target/statusText."""
import argparse
import datetime
import json
from pathlib import Path
import re
import uiautomation as auto

TARGET="CK3-War-AI-Episode04-March-Logistics-Review01.mp4"
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("--sample",required=True)
args=parser.parse_args()
if not re.fullmatch(r"[0-9]{2}",args.sample):
    raise ValueError("Require two-digit append-only sample number")
out=Path(__file__).parent/("monitor-"+args.sample+"-existing-uia-status.json")
if out.exists():
    raise FileExistsError(out)
result={"utc":datetime.datetime.now(datetime.UTC).isoformat(),"scope":"only existing OneDrive UIA target/statusText; no invocation/focus/input","metadata_query_performed":False,"target":TARGET,"windows":[],"classification":"UIA_SAMPLE_ONLY"}

def safe(text):
    text=re.sub(r"[A-Za-z0-9_.+%-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}","[redacted-account]",str(text))
    text=re.sub(r"https?://\S+","[redacted-url]",text)
    return text[:1000]

visited=0
def walk(ctrl,depth=0):
    global visited
    if depth>10 or visited>=2000:
        return
    visited+=1
    yield ctrl
    for child in ctrl.GetChildren():
        yield from walk(child,depth+1)

try:
    for window in auto.GetRootControl().GetChildren():
        if window.ClassName!="OneDriveReactNativeWin32WindowClass":
            continue
        rec={"hwnd":window.NativeWindowHandle,"statusText":[],"target_rows":[]}
        for ctrl in walk(window):
            name=ctrl.Name or ""
            aid=ctrl.AutomationId or ""
            if aid=="statusText":
                rec["statusText"].append({"name":safe(name),"type":ctrl.ControlTypeName})
            if TARGET in name:
                match={"name":safe(name),"automation_id":aid,"type":ctrl.ControlTypeName}
                if aid=="progressItem":
                    match["target_action_text"]=[safe(c.Name or "") for c in ctrl.GetChildren() if c.AutomationId=="itemAction"]
                rec["target_rows"].append(match)
        if rec["statusText"] or rec["target_rows"]:
            result["windows"].append(rec)
    text="\n".join(s["name"] for w in result["windows"] for s in w["statusText"])
    low=text.lower()
    errors=[word for word in ["error","错误","需要登录","sign in","暂停","paused","离线","offline","无法同步","can't sync","无法连接"] if word in low]
    if errors:
        result["classification"]="ACTUAL_UIA_ERROR_OR_PAUSE_MARKER"
        result["markers"]=errors
    elif re.search(r"(?<!\d)100\s*%",text):
        result["classification"]="ACTUAL_UIA_100_PERCENT_CLIENT_METADATA_STILL_REQUIRED"
    elif any(word in low for word in ["文件已同步","文件已全部同步","已是最新","up to date"]):
        result["classification"]="ACTUAL_UIA_UP_TO_DATE_CLIENT_METADATA_STILL_REQUIRED"
    elif any(word in low for word in ["正在上传","uploading"]):
        result["classification"]="ACTUAL_UIA_UPLOAD_IN_PROGRESS"
except Exception as exc:
    result["classification"]="READONLY_UIA_QUERY_ERROR"
    result["error_type"]=type(exc).__name__
result["nodes_visited"]=visited
result["end_utc"]=datetime.datetime.now(datetime.UTC).isoformat()
with out.open("x",encoding="utf-8") as f:
    json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps(result,ensure_ascii=False,indent=2))
