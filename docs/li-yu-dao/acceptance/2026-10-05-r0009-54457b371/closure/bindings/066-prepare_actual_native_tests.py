"""Read only actual metadata tests; build one real saved-AST request."""
from pathlib import Path
import importlib.util,json,hashlib,sys
sys.dont_write_bytecode=True
B=Path("C:/workspace/ck3_lyd_runtime_20261004")
R=B/"r9-native-save-receipt-reader-20261005-001/review-package-001"
spec=importlib.util.spec_from_file_location("native_reader",R/"read_r9_native_c2.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
RUN=B/"live-attempt-009"
native=RUN/"native-evidence/8ffcb8420953481eade4610f3ff61781/0057-checkpoint.json"
profile=RUN/"native-profile-with-exit-inventory.json"
p=m.jload(profile.read_bytes());g=m.jload(Path(p["guard_profile"]).read_bytes())["target"]
binding={"profile_sha256":m.sha(profile.read_bytes()),"pid":g["pid"],"process_create_time":g["process_create_time"],"exe_sha256":g["executable_sha256"]}
artifact=m.ref(native);d=m.jload(native.read_bytes())
save=m.ref(RUN/"checkpoints/0058-post-detach-save/checkpoint.ck3")
env={"save":save,"checkpoint_evidence":{"kind":"NATIVE_PROFILE_SAVE_RECEIPT","artifact":artifact,
 "preservation":m.ref(RUN/"checkpoints/0058-post-detach-save/PRESERVED.json"),
 "sdk_failure":m.ref(RUN/"mcp-client-evidence-001/0058-0058-post-detach-save.response.json")},"cached_readback":None}
tests=[]
def accept(name,call):
 call();tests.append({"name":name,"actual_metadata_accepted":True})
def refuse(name,call):
 try:call()
 except ValueError as e:tests.append({"name":name,"malformed_metadata_refused":True,"reason":str(e)})
 else:raise AssertionError(name+" accepted")
accept("real raw native receipt exact identity",lambda:m.native_gate(d,artifact,binding))
f=m.native_gate(d,artifact,binding)
accept("real saved hash size and native metadata",lambda:m.save_gate(d,f,save))
accept("real SDK timeout and ROOT immutable preservation",lambda:m.preservation_gate(d,f,env,env["checkpoint_evidence"],{}))
refuse("raw native receipt cannot claim successful SDK",lambda:m.sdk(native.read_bytes()))
for name,key,value in (("wrong PID","pid",1),("wrong process creation","process_create_time",1)):
 bad={**d,"observation_after":{**d["observation_after"],key:value}}
 refuse(name,lambda bad=bad:m.native_gate(bad,artifact,binding))
for name,bad in (("snapshot-only status",{**d,"status":"native_snapshot_verified"}),("caller success extra field",{**d,"caller_success":True}),("SDK wrapper in native branch",{"structuredContent":d,"isError":False})):
 refuse(name,lambda bad=bad:m.native_gate(bad,artifact,binding))
for name,bad in (("wrong save hash",{**save,"sha256":"0"*64}),("wrong save size",{**save,"bytes":save["bytes"]+1})):
 refuse(name,lambda bad=bad:m.save_gate(d,f,bad))
m.emit(R/"METADATA-TESTS.json",{"schema":"lyd.r9.native-save-metadata-tests.v1","scope":"Actual immutable native save metadata plus deliberate invalid metadata challenges; no game/release and no AST business credit from these tests","native_artifact":artifact,"saved_artifact":save,"tests":tests,"test_count":len(tests),"sdk_success_credit":False,"business_credit":False,"game_called":False})
old=m.jload((B/"r9-c2-readback-20261005-001/observed-0051/REQUEST.frozen.json").read_bytes())
after0051=m.ref(B/"r9-c2-readback-20261005-001/observed-0051/REPORT.json")
before={"save":old["after"]["save"],"checkpoint_evidence":{"kind":"SDK_SAVE_RECEIPT","artifact":old["after"]["checkpoint_sdk"],"preservation":None,"sdk_failure":None},"cached_readback":after0051}
req={"schema":"lyd.r9.c2.increment-request.v2","phase":"detach-result","label":"R9 actual0058 DETACH saved AST; SDK timeout preserved, direct native receipt","native_profile":m.ref(profile),"before":before,"after":env,"ordinary_query_sdk":None,"output":str(B/"r9-c2-readback-20261005-001/observed-0058-native-001")}
m.emit(R/"REQUEST.actual-0058.json",req)
print(json.dumps({"metadata_checks":len(tests),"request":str(R/"REQUEST.actual-0058.json"),"game_called":False}))
