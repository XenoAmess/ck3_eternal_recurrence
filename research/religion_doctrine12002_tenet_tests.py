#!/usr/bin/env python3
"""Compile actual 1.20.0.2 played boolean-parameter reader/serializer fixtures."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output-dir",type=Path,required=True)
    a=p.parse_args()
    root=Path(__file__).resolve().parent.parent
    native=root/"ck3_autonomous_player/native_bridge"
    output=a.output_dir.resolve();output.mkdir(parents=True,exist_ok=True)
    vswhere=Path(os.environ.get("ProgramFiles(x86)",r"C:\Program Files (x86)"))/"Microsoft Visual Studio/Installer/vswhere.exe"
    installed=subprocess.run([str(vswhere),"-latest","-products","*","-requires",
        "Microsoft.VisualStudio.Component.VC.Tools.x86.x64","-property","installationPath"],
        capture_output=True,text=True,check=True).stdout.strip()
    vcvars=Path(installed)/"VC/Auxiliary/Build/vcvars64.bat"
    sources=[native/"src"/n for n in ("ck3_12002.cpp","religion_doctrine12002_tenet.cpp","religion_doctrine12002_tenet_test.cpp")]
    pins=sources+[native/"include/xar_bridge/religion_doctrine12002_tenet.hpp"]
    runs=[]
    for mode in ("Od","O2"):
        target=output/mode;target.mkdir(exist_ok=True)
        temp=target/"tmp";temp.mkdir(exist_ok=True)
        exe=target/"tenet-parameter-test.exe"
        command=subprocess.list2cmdline(["cl.exe","/nologo","/std:c++20","/EHsc","/"+mode,
            "/W4","/WX","/utf-8","/I"+str(native/"include"),*map(str,sources),"/Fe:"+str(exe)])
        batch=target/"build.cmd"
        batch.write_text('@echo off\ncall "'+str(vcvars)+'" >nul\nif errorlevel 1 exit /b %errorlevel%\n'+
                         command+"\nexit /b %errorlevel%\n",encoding="utf-8")
        build=subprocess.run(["cmd.exe","/d","/c",str(batch)],cwd=target,
            env=dict(os.environ,TEMP=str(temp),TMP=str(temp)),capture_output=True,text=True,
            encoding="utf-8",errors="replace")
        (target/"build.log").write_text(build.stdout+build.stderr,encoding="utf-8")
        if build.returncode: raise RuntimeError("Compile failed: "+str(target/"build.log"))
        run=subprocess.run([str(exe),str(target)],cwd=target,capture_output=True,text=True,encoding="utf-8",errors="replace")
        (target/"test.log").write_text(run.stdout+run.stderr,encoding="utf-8")
        if run.returncode: raise RuntimeError("Fixture failed: "+str(target/"test.log"))
        wire={f.name:json.loads(f.read_text(encoding="utf-8")) for f in target.glob("*.json")}
        current=wire["current-versus-main.json"];empty=wire["known-empty-current.json"]
        if not (current["current_rite"]["rite_id"]==0 and current["faith_main_rite"]["rite_id"]==0x82000002 and
                current["faith_id"]==0x83000003 and
                current["current_rite"]["parameters"]==[{"key":'ritual"key',"value":True},{"key":"参数","value":True}] and
                current["faith_main_rite"]["parameters"][1]["key"]=="effective_parameter_with_a_long_key" and
                empty["available"] and empty["current_rite"]["parameters"]==[] and
                wire["legal-absent.json"]["current_rite"] is None and wire["legal-absent.json"]["available"] and
                not wire["key-unavailable.json"]["available"] and not wire["state-changed.json"]["available"]):
            raise ValueError("Actual wire lost source/key/empty/absence/failure distinction")
        runs.append({"mode":mode,"returncode":run.returncode,"stdout":run.stdout.strip(),
                     "actual_wire_cases":len(wire),"exe_sha256":hashlib.sha256(exe.read_bytes()).hexdigest(),
                     "wire_sha256":{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in target.glob("*.json")}})
        print(mode,run.stdout.strip())
    result={"status":"GREEN","readiness":"static-ready","live_verified":False,"local_ck3_touched":False,
            "actual_provider":True,"actual_serializer":True,"compiler":"MSVC /W4 /WX /Od and /O2","runs":runs,
            "source_sha256":{str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in pins}}
    (output/"result.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    return 0
if __name__=="__main__":raise SystemExit(main())
