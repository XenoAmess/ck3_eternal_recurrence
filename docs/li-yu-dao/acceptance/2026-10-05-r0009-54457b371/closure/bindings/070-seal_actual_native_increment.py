"""Seal actual R9 native-save increment facts; no new game operations."""
from pathlib import Path
import json,hashlib,stat,ast
B=Path("C:/workspace/ck3_lyd_runtime_20261004")
R=B/"r9-native-save-receipt-reader-20261005-001/review-package-001"
D=B/"r9-c2-readback-20261005-001"
O=D/"facts-through-0058-native-001"
O.mkdir()
def ref(p):
 raw=p.read_bytes();return {"path":str(p),"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()}
def load(p):return json.loads(p.read_bytes())
def emit(p,d):
 with p.open("x",encoding="utf-8",newline="\n") as f:json.dump(d,f,indent=2);f.write("\n")
corepath=D/"observed-0058-native-002/REPORT.json"
d=load(corepath);a=d["after_state"];z=d["before_state"]
source,destination=d["conditions"]["moving_parent"]
q=load(D/"selected-protections-0058-native-001/REPORT.json")
actor=a["characters"]["31254"]
need=lambda ok: None if ok else (_ for _ in ()).throw(AssertionError("Actual extra graph/role condition differs"))
need(d["status"]=="ACTUAL_NARROW_EXPECTATIONS_MATCH" and d["sdk_success_credit"] is False and d["after_sdk"] is None)
def select(rows,names):return [x for x in rows if x["key"] in names]
checks=[]
def check(name,ok,actual):
 need(ok);checks.append({"name":name,"matches":True,"actual":actual})
parents={k:[z["all_rite_parents"].get(k),v] for k,v in a["all_rite_parents"].items() if z["all_rite_parents"].get(k)!=v}
check("Only moving Rite changed parent",parents=={"169":[source,destination]},parents)
newfaith=[k for k in a["all_faith_mains"] if k not in z["all_faith_mains"]]
check("One new dynamic Faith with main169",newfaith==[destination] and a["all_faith_mains"][destination]=="169",{"created":newfaith,"main":a["all_faith_mains"][destination]})
check("All existing Faith mains retained",all(a["all_faith_mains"].get(k)==v for k,v in z["all_faith_mains"].items()),{"source104":a["all_faith_mains"][source],"old105":a["all_faith_mains"]["105"]})
check("Actual source NPC follows moving Rite into new Faith",a["characters"]["65865"]["alive"] is True and a["characters"]["65865"]["rite"]=="169" and a["characters"]["65865"]["faith"]==destination,{"id":65865,"rite":a["characters"]["65865"]["rite"],"faith":a["characters"]["65865"]["faith"]})
check("Actual recipient remains alive receiving Faith/main",a["characters"]["65866"]["alive"] is True and a["characters"]["65866"]["rite"]=="159" and a["characters"]["65866"]["faith"]==source,{"id":65866,"rite":"159","faith":source})
names=("tenets","tenet","doctrine")
oldteach=select(z["faiths"][source]["entries"],names)
afterteach=select(a["faiths"][source]["entries"],names)
newteach=select(a["faiths"][destination]["entries"],names)
check("Positive source Faith tenets/doctrines retained and copied",bool(oldteach) and oldteach==afterteach==newteach,{"positive_entry_count":len(oldteach)})
heads={}
for fid in (source,destination):
 entries=a["faiths"][fid]["entries"]
 h=[e["value"] for e in entries if e["key"]=="religious_head"]
 title=[e["value"] for e in entries if e["key"]=="religious_head_title"]
 check("Actual Faith "+fid+" head sentinel and title absence",h==["4294967295"] and not title,{"faith_exists":True,"raw_religious_head":h,"religious_head_title_entries":title,"interpretation":"Saved invalid character-ID sentinel; no head title record, never NULL equality"})
 heads[fid]={"raw_religious_head":h[0],"head_title_present":False}
check("Seven real actor titles and actual named protection branches match",q["status"]=="ACTUAL_SELECTED_PROTECTIONS_MATCH" and q["actual_selected_title_count"]==7 and q["actual_selected_title_holders_all_actor"] is True,{"selected_titles":7,"all_holders":31254,"NPC_family_data":"absent on both saves; no equality credit for missing family branches"})
need(a["all_rite_parents"]["186"]=="105")
extra={"moving_source_faith":source,"moving_new_faith":destination,
 "actual_source_rite_counts":{"before":sum(v==source for v in z["all_rite_parents"].values()),"after":sum(v==source for v in a["all_rite_parents"].values())},
 "actual_new_faith_rite_count":sum(v==destination for v in a["all_rite_parents"].values()),
 "source_main":"159","old105_backup_main":{"rite":"186","parent":"105"},"actual_selected_native_heads":heads}
refs={"core_readback":ref(corepath),"core_index":ref(D/"observed-0058-native-002/INDEX.json"),
 "selected_protections":ref(D/"selected-protections-0058-native-001/REPORT.json"),"selected_protections_index":ref(D/"selected-protections-0058-native-001/INDEX.json"),
 "previous_facts":ref(D/"facts-through-0051-001/FACTS.json"),
 "save":d["after_artifact"],"native_save_receipt":d["after_native_save_receipt"],
 "sdk_error":d["after_evidence"]["sdk_failure"],"root_preservation":d["after_evidence"]["preservation"],
 "readonly_correction":ref(B/"live-attempt-009/checkpoints/0058-post-detach-save/READONLY-CORRECTION.json"),
 "first_refusal":ref(D/"observed-0058-native-001/FAILURE.json"),"metadata_tests":ref(R/"METADATA-TESTS.json")}
facts={"schema":"lyd.r9.actual-facts-through-0058-native.v1","status":"ACTUAL_JOIN1_AND_DETACH_SAVED_AST_VERIFIED_FULL_CYCLE_INCOMPLETE",
 "source_head":d["source_head"],"native_profile_sha256":d["native_profile_sha256"],
 "actual_join1_verified":True,"actual_detach_verified_by_preserved_save_AST":True,"actual_join2_verified":None,"full_cycle_credit":False,
 "sdk_success_credit":False,"sdk_status":"ERROR_NO_RETRY","native_save_status":"native_gameplay_postcondition_verified",
 "native_ACK_business_credit":False,"claim_release_called":False,"game_called":False,"reader_native_branch_is_explicit":True,
 "actual_round":{"serial":d["conditions"]["actual_serial"],"nonce":d["conditions"]["actual_nonce"],"joins":d["conditions"]["actual_completed_joins"],"detaches":d["conditions"]["actual_completed_detaches"],"fixture_resets":d["conditions"]["actual_reset_count"]},
 "actual_fee_delta":d["conditions"]["wallet_delta"],"actual_wallet":actor["wallet"],"extra_graph":extra,"additional_checks":checks,"evidence":refs,
 "limits":["No second JOIN or host claim release performed.","SDK timeout retained; actual business comes from genuine preserved checkpoint AST.","Stress is absent in saved actor sourcefields and remains NULL.","Core legacy guard_fields NULL equality is excluded; positive top-level branches and seven actual title ASTs were read separately.","Only three exact characters/current actor domain titles; no entire-world character/title scan.","Prior R8-to-R9 title AST differences remain disclosed in baseline supplement; within-R9 protections match.","Initial readonly refusal was preserved; ROOT corrected only attribute32->33 with unchanged save bytes/SHA."]}
emit(O/"FACTS.json",facts)
emit(O/"INDEX.json",{"schema":"lyd.r9.increment-facts-index.v1","files":[{**ref(O/"FACTS.json"),"path":"FACTS.json"}]})
emit(R/"DELIVERY.json",{"schema":"lyd.r9.native-save-reader-delivery.v1","helper":ref(R/"read_r9_native_c2.py"),"actual_facts":ref(O/"FACTS.json"),"facts_index":ref(O/"INDEX.json"),"native_sdk_separation":True,"full_cycle_credit":False})
readme="""R9 explicit direct-native checkpoint reader (source HEAD54457b371).

Run with the pinned Python313 executable and -B:
read_r9_native_c2.py --request REQUEST.actual-0058-attempt002.json
Supplement: supplement_selected_protections_native.py REQUEST.selected-protections-0058.json

The new request v2 distinguishes SDK_SAVE_RECEIPT from NATIVE_PROFILE_SAVE_RECEIPT. Raw native JSON cannot enter the SDK branch. Native mode requires original direct native receipt, immutable saved bytes, exact metadata, source/profile/guard process identity and frame, ROOT preservation and actual ERROR_NO_RETRY dispatch receipt. It emits after_sdk=null and sdk_success_credit=false. Only the independently parsed saved AST supports business facts.

The saved-state projector, product details, numeric/typed sourcefields, frame and dependency ASTs are unchanged. Legacy cached projection reuse is pinned to cfee520a... original reader plus exact BINDINGS3475ca7a..., actual source HEAD, saved and SDK refs. All artifact hashes are rechecked after analysis.

11 focused actual metadata/negative challenges passed. 20 actual DETACH conditions matched; positive protections checked separately. Attempt001 refused a writable checkpoint, ROOT corrected its attribute with unchanged bytes, and attempt002 parsed the preserved real save. Both attempts remain. This package changes no game/SDK/registry or old package and grants no full cycle or second JOIN credit.
"""
with (R/"README.txt").open("x",encoding="utf-8",newline="\n") as f:f.write(readme)
files=[{**ref(p),"path":p.relative_to(R).as_posix()} for p in sorted(R.rglob("*")) if p.is_file()]
emit(R/"INDEX.json",{"schema":"lyd.r9.native-save-reader-index.v1","files":files})
for p in R.rglob("*"):
 if p.is_file():p.chmod(stat.S_IREAD)
print(json.dumps({"facts":ref(O/"FACTS.json"),"facts_index":ref(O/"INDEX.json"),"reader_index":ref(R/"INDEX.json"),"additional_checks":len(checks)},ensure_ascii=True))
