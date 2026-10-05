"""Append explicit native-save evidence reader, preserving frozen SDK reader."""
from pathlib import Path
import hashlib,json,shutil,ast
B=Path("C:/workspace/ck3_lyd_runtime_20261004")
OLD=B/"r9-c2-incremental-readback-helper-20261005-001/review-package-002"
OUT=B/"r9-native-save-receipt-reader-20261005-001/review-package-001"
OUT.mkdir(parents=True)
old=(OLD/"read_r8_c2.py").read_bytes()
assert hashlib.sha256(old).hexdigest()=="cfee520abacd426b7b73b1e91da3fa1abe2ad44d67d3e50af758a1dcdeb7b2e4"
s=old.decode()
def replace(a,b):
 global s
 assert s.count(a)==1,a[:80]
 s=s.replace(a,b)
replace('SCHEMA="lyd.r8.c2.actual-increment-readback.v1"','SCHEMA="lyd.r9.c2.actual-increment-readback.v2"\nLEGACY_READER_SHA="cfee520abacd426b7b73b1e91da3fa1abe2ad44d67d3e50af758a1dcdeb7b2e4"\nLEGACY_BINDINGS_SHA="3475ca7a09c1fcc6b33295ccee020a9773ec1d71a9b5bb6fd6e5e0cf41f11e73"')
replace(' if "sdk_result" in d:d=d["sdk_result"]\n need(d.get("isError") is not True,"SDK receipt error")\n d=d.get("structuredContent",d)',
' if "sdk_result" in d:d=d["sdk_result"]\n need(type(d) is dict and type(d.get("isError")) is bool and d["isError"] is False and type(d.get("structuredContent")) is dict,"explicit successful SDK wrapper required; raw native receipt is a separate input kind")\n d=d["structuredContent"]')
start=s.index("def observation(")
end=s.index("\ndef counter(",start)
s=s[:start]+'''def native_gate(d,artifact,binding):
 closed(d,("schema","session_id","profile_sha256","pipe_name","recorded_at_utc","status","result","snapshot_before","snapshot_after","observation_after","uses_ocr","uses_desktop_input","receipt_path"),"direct native save receipt")
 need(d["schema"]=="ck3.native-profile-receipt.v1" and d["status"]=="native_gameplay_postcondition_verified","exact genuine native save receipt status required")
 need(d["uses_ocr"] is False and d["uses_desktop_input"] is False,"native save evidence cannot use desktop/OCR credit")
 need(Path(d["receipt_path"]).resolve()==Path(artifact["path"]).resolve(),"native receipt self-path differs")
 need(Path(artifact["path"]).parent.name==d["session_id"],"actual receipt directory/session differs")
 f=frame(d,binding)
 o=d["observation_after"]
 need(type(o) is dict and o.get("pid")==binding["pid"] and o.get("window_pid")==binding["pid"] and
  o.get("process_create_time")==binding["process_create_time"] and str(o.get("executable_sha256","")).lower()==binding["exe_sha256"],"native observation guarded process identity differs")
 prior=d["snapshot_before"]
 need(type(prior) is dict and type(prior.get("native_revision")) is int and prior["native_revision"]<=f["native_revision"] and
  prior.get("diagnostics",{}).get("bridge_pid")==binding["pid"] and prior.get("diagnostics",{}).get("connection_generation")==f["diagnostics"]["connection_generation"],"native save prior frame identity/order differs")
 return f

def save_gate(d,f,save_ref):
 c=d.get("result",{});saved=c.get("checkpoint",{})
 need(c.get("step")=="save-checkpoint" and c.get("accepted") is True and saved.get("status")=="saved" and
  saved.get("strategy")=="native-autosave-command-v1" and saved.get("sha256")==save_ref["sha256"] and
  saved.get("size")==save_ref["bytes"] and saved.get("date_raw")==f["date_raw"] and
  c.get("submission",{}).get("date_raw")==f["date_raw"] and c.get("materialization",{}).get("available") is True,
  "actual saved metadata does not match preserved save")
 return saved

def preservation_gate(d,f,env,evidence,cache):
 p=jload(bytesref(evidence["preservation"],cache))
 failure=jload(bytesref(evidence["sdk_failure"],cache))
 saved=d["result"]["checkpoint"]
 need(p.get("sdk_status")=="ERROR_NO_RETRY" and p.get("sdk_result") is None and p.get("sdk_success_credit") is False and
  failure.get("schema")=="ck3.lyd.mcp-dispatch.v1" and failure.get("status")=="ERROR_NO_RETRY" and
  failure.get("request_id")==p.get("request_id"),"native evidence must preserve actual SDK failure without success credit")
 need(p.get("sha256")==env["save"]["sha256"] and p.get("bytes")==env["save"]["bytes"] and
  Path(p.get("preserved","")).resolve()==Path(env["save"]["path"]).resolve() and
  Path(p.get("source","")).resolve()==Path(saved.get("path","")).resolve(),"preservation source/save bytes differ")
 need(Path(p.get("native_receipt","")).resolve()==Path(evidence["artifact"]["path"]).resolve() and
  p.get("native_receipt_sha256")==evidence["artifact"]["sha256"] and p.get("native_receipt_status")==d["status"] and
  p.get("recorded_at_utc")==d["recorded_at_utc"] and p.get("actual_actor_id")==ACTOR and
  all(p.get(k)==f[k] for k in ("revision","native_revision","date_raw","paused")),"preservation receipt/frame binding differs")

def observation(env,binding,cache,reader_sha,bindings_sha):
 closed(env,("save","checkpoint_evidence","cached_readback"),"actual observation")
 evidence=closed(env["checkpoint_evidence"],("kind","artifact","preservation","sdk_failure"),"explicit checkpoint evidence")
 raw=bytesref(env["save"],cache,saved=True)
 evidence_raw=bytesref(evidence["artifact"],cache)
 if evidence["kind"]=="SDK_SAVE_RECEIPT":
  need(evidence["preservation"] is None and evidence["sdk_failure"] is None,"successful SDK evidence cannot carry native fallback fields")
  d=sdk(evidence_raw);f=frame(d,binding)
 elif evidence["kind"]=="NATIVE_PROFILE_SAVE_RECEIPT":
  need(evidence["preservation"] is not None and evidence["sdk_failure"] is not None,"actual native preservation and failed SDK refs required")
  d=jload(evidence_raw);f=native_gate(d,evidence["artifact"],binding)
  preservation_gate(d,f,env,evidence,cache)
 else:raise ValueError("unknown explicit save evidence kind")
 save_gate(d,f,env["save"])
 if env["cached_readback"] is not None:
  old=jload(bytesref(env["cached_readback"],cache))
  exact_new=(old.get("schema")==SCHEMA and old.get("reader_sha256")==reader_sha and
   old.get("bindings_sha256")==bindings_sha and old.get("after_evidence")==evidence)
  exact_legacy=(evidence["kind"]=="SDK_SAVE_RECEIPT" and old.get("schema")=="lyd.r8.c2.actual-increment-readback.v1" and
   old.get("reader_sha256")==LEGACY_READER_SHA and old.get("bindings_sha256")==LEGACY_BINDINGS_SHA==bindings_sha and
   old.get("after_sdk")==evidence["artifact"])
  need((exact_new or exact_legacy) and old.get("after_artifact")==env["save"] and
   old.get("native_profile_sha256")==binding["profile_sha256"] and old.get("source_head")=="54457b371e947edb86903c2ebd578034f02695db",
   "cached projection cannot be reinterpreted as current parser/input")
  projection=old["after_state"];used=True
 else:projection=project(raw);used=False
 return projection,{"session_id":d["session_id"],"profile_sha256":d["profile_sha256"],"pipe_name":d["pipe_name"],
  "revision":f["revision"],"native_revision":f["native_revision"],"date_raw":f["date_raw"],"generation":f["diagnostics"]["connection_generation"],
  "active_event":f.get("active_event"),"paused":True,"PID":binding["pid"],"process_create_time":binding["process_create_time"],
  "evidence_kind":evidence["kind"],"sdk_success_credit":evidence["kind"]=="SDK_SAVE_RECEIPT"},used
''' +s[end:]
replace('r["schema"]=="lyd.r8.c2.increment-request.v1"','r["schema"]=="lyd.r9.c2.increment-request.v2"')
replace('   "after_sdk":r["after"]["checkpoint_sdk"],"before_native":bf,"after_native":af,',
'   "after_evidence":r["after"]["checkpoint_evidence"],"after_sdk":r["after"]["checkpoint_evidence"]["artifact"] if r["after"]["checkpoint_evidence"]["kind"]=="SDK_SAVE_RECEIPT" else None,\n   "after_native_save_receipt":r["after"]["checkpoint_evidence"]["artifact"] if r["after"]["checkpoint_evidence"]["kind"]=="NATIVE_PROFILE_SAVE_RECEIPT" else None,\n   "sdk_success_credit":af["sdk_success_credit"],"before_native":bf,"after_native":af,')
replace('   "native_ACK_business_credit":False,"full_cycle_credit":False,"game_called":False,"host_release_called":False}',
'   "native_ACK_business_credit":False,"full_cycle_credit":False,"game_called":False,"host_release_called":False,\n   "legacy_guard_fields_boundary":"NULL equality is not protection proof; separately read actual top-level character branches and positive domain titles"}')
# Same saved projection and product checks. Only envelope/evidence transport changes.
a={x.name:ast.dump(x,include_attributes=False) for x in ast.parse(old.decode()).body if isinstance(x,ast.FunctionDef)}
z={x.name:ast.dump(x,include_attributes=False) for x in ast.parse(s).body if isinstance(x,ast.FunctionDef)}
for name in ("project","details","counter","typed","frame","parse","scalar","section","asthash"):
 assert a[name]==z[name],name+" product/parser drift"
with (OUT/"read_r9_native_c2.py").open("x",encoding="utf-8",newline="\n") as f:f.write(s)
assert hashlib.sha256((OLD/"BINDINGS.json").read_bytes()).hexdigest()=="3475ca7a09c1fcc6b33295ccee020a9773ec1d71a9b5bb6fd6e5e0cf41f11e73"
shutil.copyfile(OLD/"BINDINGS.json",OUT/"BINDINGS.json")
shutil.copytree(OLD/"dependencies",OUT/"dependencies")
with (OUT/"AUTHOR-REPORT.json").open("x",encoding="utf-8") as f:
 json.dump({"status":"EXPLICIT_NATIVE_RECEIPT_READER_AUTHORED","original_reader_sha256":hashlib.sha256(old).hexdigest(),"bindings_sha256":hashlib.sha256((OUT/"BINDINGS.json").read_bytes()).hexdigest(),"identical_function_AST":[n for n in a if n in z and a[n]==z[n]],"sdk_success_credit":False,"actual_detach_business":"PENDING_ACTUAL_SAVE_PARSE","game_called":False},f,indent=2)
print(str(OUT/"read_r9_native_c2.py"))
