"""Finite offline Native31 builder. No Game, SDK, injection or deployment operations."""
from pathlib import Path
import argparse,datetime,hashlib,importlib.util,json,os,re,shlex,subprocess,sys,time
ROOT=Path("D:/codex-ck3-demos/2026-10-20-native31-passive-build01")
PREP=Path("D:/codex-ck3-demos/2026-10-20-native31-passive-prepare01")
OLD=Path("D:/codex-ck3-demos/2026-10-19-robert-v20261019-native30-camera01")
SRC=PREP/"source/ck3_autonomous_player/native_bridge"
FROZEN=OLD/"source/ck3_autonomous_player/native_bridge"
BASE=OLD/"build"
REPO=Path("Z:/ck3_mod_rewrite")
MACHINE="xenoamess-full-tower-eb9d2c1186"
HARD=1073741824
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def digest(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
def pin(path):
 s=path.stat()
 return {"path":str(path),"bytes":s.st_size,"sha256":digest(path),"mtime_ns":str(s.st_mtime_ns),"file_id":str(s.st_ino)}
def output(name,data):
 p=ROOT/name;p.parent.mkdir(parents=True,exist_ok=True)
 b=(json.dumps(data,ensure_ascii=True,sort_keys=True,separators=(",",":"))+"\n").encode() if not isinstance(data,bytes) else data
 with p.open("xb") as f:f.write(b)
 return pin(p)
def load_module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def usage():
 return sum((p.stat().st_size+4095)//4096*4096 for p in ROOT.rglob("*") if p.is_file())
def run(name,args,env,limit=8388608):
 assert usage()<HARD-67108864,"insufficient finite guard"
 p=ROOT/"logs"/(name+".log");p.parent.mkdir(parents=True,exist_ok=True)
 command={"command":args,"cwd":str(ROOT),"start":now()}
 with p.open("xb") as f:
  proc=subprocess.Popen(args,cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
  total=0
  while True:
   block=proc.stdout.read(65536)
   if not block:break
   total+=len(block)
   if total>limit:proc.kill();raise RuntimeError("bounded log exceeded")
   f.write(block)
  rc=proc.wait()
 command.update(return_code=rc,end=now(),log=pin(p))
 output("commands/"+name+".json",command)
 if rc:raise RuntimeError(name+" returned "+str(rc))
 return command
def blocks():
 p=OLD/"attempt07/production-manifest.ninja"
 assert p.stat().st_size==15398163 and digest(p)=="08e6c2926dc58c4f103f76d906b86f893f33da489ef996696db9a4bc1543a9f4"
 lines=p.read_text().splitlines()
 def get(prefix):
  matches=[i for i,line in enumerate(lines) if line.startswith(prefix)]
  assert len(matches)==1,(prefix,len(matches))
  i=matches[0];out={"header":lines[i]};i+=1
  while i<len(lines) and (not lines[i] or lines[i].startswith("  ")):
   if " = " in lines[i]:
    key,value=lines[i].strip().split(" = ",1);out[key]=value
   i+=1
  return out
 return get
def environment(phase):
 helper=OLD/"source/tools/run_native_msvc.py"
 assert digest(helper)=="b53409a1ee48098abc3dfce607668a426d8502f5f00c64ad1434fadfb053832e"
 for key in ("CL","_CL_","LINK"):
  assert not os.environ.get(key),"ambient compiler option "+key
 m=load_module("native31_frozen_msvc",helper)
 env=m.child_environment(ROOT)
 env,tools=m.initialize_msvc(Path("C:/Program Files/Microsoft Visual Studio/18/Community"),ROOT,env)
 output("metadata/msvc-tools-"+phase+".json",{"machine_id":MACHINE,"observed_at_utc":now(),"tools":tools,"helper":pin(helper),"environment_values_recorded":False})
 return env,tools
def compile_tu(name,source,flags,env,tools):
 obj=ROOT/"obj"/(name+".obj");obj.parent.mkdir(parents=True,exist_ok=True)
 args=[tools["cl"],"/nologo","/TP",*flags,"/showIncludes","/Fd"+str(obj.with_suffix(".pdb")),"/FS","/c",str(source),"/Fo"+str(obj)]
 result=run(name,args,env);assert obj.is_file();result["object"]=pin(obj)
 return obj,result
def register(exe,command,source_commands):
 helper=REPO/"tools/register_project_exe_exclusions.py"
 assert digest(helper)=="67c6021fcd5af209f409957fe045cfbc890da4eda72baf9a5bdf5b0c58d4701b"
 sys.path.insert(0,str(REPO/"tools"))
 m=load_module("native31_defender_helper",helper)
 result=m.after_successful_command_build(REPO,ROOT/"source",ROOT,command,[exe],external_candidate="Native31 independent passive observer fixture",source_commands=source_commands)
 output("metadata/defender-"+exe.stem+".json",{"machine_id":MACHINE,"observed_at_utc":now(),"result":result,"exclusion_success_not_assumed":True})
 return result
def fixture_phase(env,tools):
 common=["/std:c++20","/O2","/Ob2","/DNDEBUG","/MD","/EHsc","/W4","/WX","/permissive-","/DWIN32_LEAN_AND_MEAN","/DNOMINMAX","/I"+str(SRC/"include"),"/I"+str(FROZEN/"include")]
 core,c1=compile_tu("fixture-core",ROOT/"source/native_time_command_observer_12004.cpp",common,env,tools)
 test,c2=compile_tu("fixture-test",ROOT/"source/native31_core_test.cpp",common,env,tools)
 install,c3=compile_tu("fixture-installer",ROOT/"source/native31_installer_fixture.cpp",common,env,tools)
 linker=str(Path(tools["cl"]).with_name("link.exe"))
 tests=[("native31_core_fixture",[core,test]),("native31_installer_fixture",[core,install])]
 results=[]
 for name,objs in tests:
  exe=ROOT/"bin"/(name+".exe");exe.parent.mkdir(parents=True,exist_ok=True)
  args=[linker,"/nologo","/INCREMENTAL:NO","/OUT:"+str(exe),*[str(p) for p in objs],"kernel32.lib"]
  run(name+"-link",args,env)
  selected=[c1,c2] if name=="native31_core_fixture" else [c1,c3]
  commands=[{"argv":c["command"],"return_code":0} for c in selected]
  defender=register(exe,args,commands)
  if name=="native31_core_fixture":
   cases=["core"]
  else:cases=json.loads((ROOT/"PLAN01.json").read_text())["fixture"]["installer_cases"]
  for case in cases:
   cmd=[str(exe)]+([] if case=="core" else [case,MACHINE])
   r=run(name+"-"+case,cmd,env,1048576)
   if case=="core":
    frame=json.loads(Path(r["log"]["path"]).read_text(encoding="utf-8"))
    journal=frame["result"]
    assert frame["type"]=="command_result" and frame["request_id"]=="journal-fixture" and frame["ok"] is True
    assert journal["observer_schema"]=="xar.ck3.time-command-observer31/v1" and journal["drain_fence"] is False
    assert journal["process_id"]==123 and journal["process_birth"]=="456" and journal["attached"]==1 and journal["readable"]==1
    assert journal["returned_count"]==len(journal["events"])<=64
   results.append({"case":case,"exe":pin(exe),"return_code":r["return_code"],"defender_status":defender["status"],"journal_json_validated":case=="core"})
 output("FIXTURES-RESULT01.json",{"machine_id":MACHINE,"observed_at_utc":now(),"status":"PASS","cases":results,"Game_calls":0,"real_installer_body_tested":True,"runtime_qualification":False})
def inherited(record):
 defines=[x.replace('\\\"','"') for x in record["DEFINES"].split()]
 includes=record["INCLUDES"].split()
 return defines+includes+record["FLAGS"].split()
def production_phase(env,tools):
 assert json.loads((ROOT/"FIXTURES-RESULT01.json").read_text())["status"]=="PASS"
 get=blocks()
 bridge=get("build CMakeFiles\\xar_ck3_bridge.dir\\src\\bridge.cpp.obj:")
 commands=get("build CMakeFiles\\xar_ck3_12002_runtime.dir\\src\\ck3_12002_commands.cpp.obj:")
 main=get("build CMakeFiles\\xar_ck3_12002_runtime.dir\\src\\ck3_12002.cpp.obj:")
 two=["XAR_CK3_ENABLE_G2_PLAYER_RELIGION_CONTEXT_PRIVATE_QUERY_V1","XAR_CK3_ENABLE_G2_PLAYER_RELIGION_PERSONAL_PARAMETERS_PRIVATE_QUERY_V1"]
 assert all("-D"+x+"=1" in main["DEFINES"] and "-D"+x+"=1" not in commands["DEFINES"] for x in two)
 overlay=SRC/"cmake/native30-runtime-source-macro-restore.cmake"
 assert overlay.stat().st_size==807 and digest(overlay)=="e99511202bab46b24e37b9cf4b1e9d31eb6e9ce3612bf8f078dba131f05d2e02"
 common=["/DXAR_CK3_ENABLE_NATIVE_TIME_OBSERVER31=1","/I"+str(SRC/"include")]
 recipe=[("native31-bridge",SRC/"src/bridge.cpp",bridge),("native31-commands",SRC/"src/ck3_12002_commands.cpp",commands),("native31-core",ROOT/"source/native_time_command_observer_12004.cpp",commands),("native31-install",SRC/"src/native_time_command_observer_12004_install.cpp",commands)]
 objects=[];provenance=[]
 for name,source,old in recipe:
  obj,result=compile_tu(name,source,common+inherited(old),env,tools)
  objects.append(obj);provenance.append({"source":pin(source),"object":pin(obj),"inherited_variables":old,"extra_flags":common})
 link=get("build xar_ck3_bridge.dll xar_ck3_bridge.lib:")
 old_objects=link["header"].split(":",1)[1].split("|",1)[0].split()[1:]
 assert len(old_objects)==336 and old_objects.count("CMakeFiles\\xar_ck3_bridge.dir\\src\\bridge.cpp.obj")==1
 actual=[objects[0] if x=="CMakeFiles\\xar_ck3_bridge.dir\\src\\bridge.cpp.obj" else BASE/x for x in old_objects]
 for p in actual:assert p.is_file(),p
 input_objects=[pin(p) for p in actual]
 runtime=BASE/"xar_ck3_12002_runtime.lib";protocol=BASE/"xar_bridge_protocol.lib"
 assert digest(runtime)=="044be220bb4c336bf1a6b814b0838f2671d340f35affc9671ec7eaee6693ab72"
 assert digest(protocol)=="456942eabbbecd08fecd43bdbeac023de857d5a419e59c2bf7447c2560a558d3"
 out=ROOT/"bin/xar_ck3_bridge.dll"
 # Complete replacement commands TU is a direct object before unchanged archive.
 # No /WHOLEARCHIVE, /FORCE or duplicate archive member is used.
 libs=[str(protocol),str(runtime)]+link["LINK_LIBRARIES"].split()[2:]
 args=[*[str(p) for p in actual],*[str(p) for p in objects[1:]],*libs,
       "/DLL","/VERSION:0.0","/INCREMENTAL:NO","/MANIFEST:EMBED","/VERBOSE:LIB",
       "/OUT:"+str(out),"/IMPLIB:"+str(ROOT/"bin/xar_ck3_bridge.lib"),
       "/PDB:"+str(ROOT/"bin/xar_ck3_bridge.pdb"),"/MAP:"+str(ROOT/"bin/xar_ck3_bridge.map")]
 rsp="\n".join(subprocess.list2cmdline([a]) for a in args)+"\n"
 output("native31-link.rsp",rsp.encode())
 linker=str(Path(tools["cl"]).with_name("link.exe"))
 run("native31-production-link",[linker,"/nologo","@"+str(ROOT/"native31-link.rsp")],env,16777216)
 for entry in input_objects:
  s=Path(entry["path"]).stat();assert str(s.st_mtime_ns)==entry["mtime_ns"] and str(s.st_ino)==entry["file_id"] and s.st_size==entry["bytes"],"link input changed"
 maptext=(ROOT/"bin/xar_ck3_bridge.map").read_text(errors="replace")
 assert "native31-commands.obj" in maptext and "native31-core.obj" in maptext and "native31-install.obj" in maptext
 assert not re.search(r"xar_ck3_12002_runtime:ck3_12002_commands",maptext,re.I),"old commands archive member extracted"
 dumpbin=str(Path(tools["cl"]).with_name("dumpbin.exe"))
 run("native31-exports",[dumpbin,"/EXPORTS",str(out)],env)
 run("native31-headers",[dumpbin,"/HEADERS","/LOADCONFIG",str(out)],env)
 export_text=(ROOT/"logs/native31-exports.log").read_text(errors="replace")
 expected={"XarCk3BridgeIdentity","XarCk3BridgePrepareStartup","XarCk3BridgeStart","XarCk3BridgeStartWithPipe","XarCk3BridgeStop","XarRefillCoreCarrier12004"}
 found=set(re.findall(r"^\s+\d+\s+[0-9A-F]+\s+[0-9A-F]+\s+(\w+)",export_text,re.M))
 assert found==expected,(found,expected)
 symbols=["ForwardAppend","ForwardExecute","CommitInsertion","DiagnosticFrame"]
 assert all(x in maptext for x in symbols),"new observer symbols missing"
 output("PRODUCTION-RESULT01.json",{"machine_id":MACHINE,"observed_at_utc":now(),"status":"OFFLINE_ARTIFACT_QUALIFIED_NOT_DEPLOYED","outputs":[pin(out),pin(ROOT/"bin/xar_ck3_bridge.lib"),pin(ROOT/"bin/xar_ck3_bridge.map")],"per_TU":provenance,"unchanged_runtime":pin(runtime),"unchanged_protocol":pin(protocol),"base_direct_objects":len(old_objects),"actual_link_object_pins":input_objects,"replacement_strategy":"new complete commands/core/install direct objects before unchanged runtime archive; old commands member not present in MAP","overlay":pin(overlay),"exports":sorted(found),"Game_calls":0,"injections":0,"currentDLL_replaced":False,"drain_fence":False,"root_runtime_approval_required":True})
def validate_source_inputs():
 plan=json.loads((ROOT/"PLAN02.json").read_text())
 for rel,expected in plan["new_source"].items():
  path=ROOT/rel
  assert path.stat().st_size==expected["bytes"] and digest(path)==expected["sha256"],"new source drift: "+rel
 expected={
  "src/bridge.cpp":"661e73ca1002334e039ad234ae142937cd24f128d3399a9b0ad154adc1c11719",
  "src/ck3_12002_commands.cpp":"d5a18e67954b215d110cc256f26b5577bb7a0c2ea46b8f0122b817a120cc5c74",
  "include/xar_bridge/native_time_command_observer_12004.hpp":"f0beb8ff286bcda8854fcfe74529ae47943f67db206b8b7855d1081ec8254e11",
  "src/native_time_command_observer_12004_install.cpp":"95888a0ca45293704dedc8915edf817c5dabb12af42c93b4f536f080994ed545",
  "cmake/native30-runtime-source-macro-restore.cmake":"e99511202bab46b24e37b9cf4b1e9d31eb6e9ce3612bf8f078dba131f05d2e02"}
 for rel,h in expected.items():assert digest(SRC/rel)==h,"immutable prepare source drift: "+rel
def main():
 parser=argparse.ArgumentParser();parser.add_argument("phase",choices=["fixtures","production"]);args=parser.parse_args()
 assert ROOT.is_dir() and (ROOT/"PLAN01.json").is_file()
 validate_source_inputs()
 env,tools=environment(args.phase)
 try:
  if args.phase=="fixtures":fixture_phase(env,tools)
  else:production_phase(env,tools)
 except BaseException as error:
  output("FAILED-"+args.phase+"-"+str(time.time_ns())+".json",{"machine_id":MACHINE,"observed_at_utc":now(),"error":str(error),"type":type(error).__name__,"phase":args.phase,"usage_bytes":usage()})
  raise
if __name__=="__main__":main()
