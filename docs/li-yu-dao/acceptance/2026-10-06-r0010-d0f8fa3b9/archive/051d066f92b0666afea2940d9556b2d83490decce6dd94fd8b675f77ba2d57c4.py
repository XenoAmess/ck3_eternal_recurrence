"""Read-only independent sixth consumption/release to seventh request lineage."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, os, struct
BASE=Path("C:/workspace/ck3_lyd_runtime_20261004")
RUN=BASE/"live-attempt-010"
OUT=BASE/"r10-actual-sixth-consumption-release-lineage-independent-review-20261006-002"
CLAIM_DIR=RUN/"native-state/native-session/ordinary-interaction-actions"
checks=[];references={}
def digest(raw):return hashlib.sha256(raw).hexdigest()
def need(ok,label):
 if not ok:raise ValueError(label)
 checks.append(label)
def ref(path):
 p=Path(path);raw=p.read_bytes();r={"path":str(p),"bytes":len(raw),"sha256":digest(raw)};references[str(p)]=r;return r
def data(path,pin=None):
 r=ref(path)
 if pin:need(r["sha256"]==pin,"pinned actual SHA "+str(path))
 return json.loads(Path(path).read_bytes())
def closed(v,keys,label):need(type(v)is dict and set(v)==set(keys),label)
def read_ref(v,label):
 need(type(v)is dict and set(v)in({"path","sha256"},{"path","sha256","bytes"}),label+" closed ref")
 r=ref(v["path"]);need(r["sha256"]==v["sha256"]and("bytes"not in v or type(v["bytes"])is int and r["bytes"]==v["bytes"]),label+" exact bytes/SHA");return r
def sdk(p,pin):
 v=data(p,pin);need(v["isError"]is False and v["resultType"]=="complete","actual SDK complete "+Path(p).name)
 r=v["structuredContent"];t=[json.loads(x["text"])for x in v["content"]if x.get("type")=="text"];need(t==[r],"SDK structured/text exact "+Path(p).name);return r
def invocation(root,pin):
 r=data(root/"RESULT.json",pin);a=data(root/"argv.json");s=data(r["argv_source"],r["argv_source_sha256"])
 need(r["exit_code"]==0 and r["status"]=="INVOCATION_COMPLETED"and s["argv"]==a,"actual ROOT exit0/exact argv "+root.name)
 need(ref(root/"stdout.txt")["sha256"]==r["stdout_sha256"]and ref(root/"stderr.txt")["sha256"]==r["stderr_sha256"]and(root/"stderr.txt").read_bytes()==b"","actual ROOT stdio exact "+root.name)
 return r,data(root/"stdout.txt")
if OUT.exists():raise FileExistsError("append-only output exists")
OUT.mkdir()
try:
 identity={"game_pid":13436,"actor_id":31254,"process_create_time":1791196395.7422996,"interaction_key":"lyd_c2_propose_join_interaction","recipient_id":65866,"action":"initiate_ordinary"}
 stable=digest(json.dumps(identity,sort_keys=True).encode())
 proof=BASE/"r10-sixth-proposal-emitted-evidence-20261006-002"
 ix=data(proof/"INDEX.json","05e6c52c366832e67d5e780f068ed904bdd401fa340d8efb186efa1486e24f5b")
 seen=set()
 for row in ix["files"]:
  closed(row,["path","bytes","sha256"],"new sixth emit closed INDEX row")
  p=(proof/row["path"]).resolve();need(proof.resolve()in p.parents and row["path"]not in seen,"new sixth emit contained unique row")
  seen.add(row["path"]);r=ref(p);need(r["bytes"]==row["bytes"]and r["sha256"]==row["sha256"],"new sixth emit exact indexed "+row["path"])
 need(len(seen)==5 and seen=={p.name for p in proof.iterdir()if p.is_file()and p.name!="INDEX.json"},"new sixth emit complete five payload coverage")
 manifest=data(proof/"CONSUMPTION-MANIFEST.json","d1d4cf436cd9b2f4c16cdf8713ec84a27385b70d0d1c5ea5c2359d1299c4b286")
 facts=data(proof/"INDEPENDENT-FACTS.json","877c2895fe6d42c719e4f6766a071986cdd390dcd556aa495bcd86ad787a51ed")
 detail=data(proof/"PRODUCT-DETAIL.json","bee80f695969967d85669856ae60a2771e941b00dec51f54afa2d45cb98e30d3")
 emit=data(proof/"EMISSION-REQUEST.raw.json","d99bae5083404b20c4bd7e0c0c146c0ff5afe8afcdd63530025f0df12f81a848")
 closed(facts,["schema","claim_request_id","action_identity","packet_sha256","native_result_sha256","unknown_sha256","before_artifact_sha256","after_artifact_sha256","consumption"],"new sixth emitted facts exact keys")
 oldpath=Path(emit["claim"]["path"]);old=data(oldpath,"47c844c0decce779351f2c5b3f2016dc6aae0b0ac6b3b0fc60bcc3b6d2fea0c8")
 need(old["claim_ordinal"]==5 and old["status"]=="claimed_result_unknown_no_retry"and old["action_identity"]==identity,"ordinal5 immutable UNKNOWN parent preserved")
 need(facts["schema"]=="ck3-ordinary-interaction-independent-consumption-v1"and facts["claim_request_id"]==manifest["claim_request_id"]==old["request_id"]=="ordinary-interaction-1d9cf9c7db6e4ea2be6872d6427cf2a4"and facts["action_identity"]==manifest["action_identity"]==identity,"sixth facts bind actual1d9c ordinal5 sixidentity")
 consume={"kind":"save_round_delta","field_name":"lyd_c2_callback_nonce","before_value":11,"after_value":12,"actor_id":31254,"recipient_id":65866,"interaction_key":identity["interaction_key"]}
 need(facts["consumption"]==consume,"sixth consumption saved nonce11-to12 only")
 for key,field in [("packet","packet_sha256"),("native_result","native_result_sha256"),("before_artifact","before_artifact_sha256"),("after_artifact","after_artifact_sha256")]:
  need(read_ref(manifest[key],"sixth manifest "+key)["sha256"]==facts[field],"sixth facts exact "+key)
 need(manifest["unknown"]is None and facts["unknown_sha256"]is None,"genuine native pending receipt; no fabricated ACK")
 need(manifest["independent_report"]["sha256"]==ref(proof/"INDEPENDENT-FACTS.json")["sha256"],"manifest exact facts report")
 before=data(manifest["before_artifact"]["path"]);after=data(manifest["after_artifact"]["path"]);c=detail["conditions"]
 for v in [before,after]:closed(v["save"],["path","sha256","bytes"],"original sixth saved exact3 reference")
 need(type(before["save"]["bytes"])is int and type(after["save"]["bytes"])is int and before["save"]["bytes"]==91535983 and after["save"]["bytes"]==91540327 and detail["before_save"]==before["save"]and detail["after_save"]==after["save"],"actual original125-to129 save refs; no149 substitution")
 need(c["serial_nonce_before"]==[11,11]and c["serial_nonce_after"]==[12,12]and c["wallet_delta"]==["0","0","0"]and c["completed_history_unchanged"]is True,"sixth saved11-to12 wallet0/history unchanged")
 need(c["source_faith"]=="106"and c["target_faith"]=="104"and c["moving_rite"]=="169"and c["target_main"]=="159"and c["target_rep"]=="65866"and c["actual_source_roles"]==["31254","65865"]and c["actual_target_roles"]==["65866"]and c["actual_human_roles"]==["31254"],"actual sixth dynamic graph and positive full roles")
 need(c["consumption_mode"]=="PROPOSAL_OPENED"and c["join_business_acceptance_credit"]is False and c["NPC_vote_choice_required"]is False and detail["native_ACK_credit"]is False and detail["actual_release"]is False,"sixth emission historical proposal-only flags preserved")
 need(detail["source_revision"]=="d0f8fa3b9d444828759443aa018bfd7ad31b398d"and detail["parser_sha256"]=="6c1ba1006cd0dd5055c11115701b60a74562b0f23d91b756a3d9322e7d055cb7"and detail["reader_version"]=="lyd-join-save-consumption-verifier-v2","sixth source/parser actual pins")
 emitroot=RUN/"root-sixth-proposal-emit-invocation-001"
 er,es=invocation(emitroot,ref(emitroot/"RESULT.json")["sha256"])
 need(es["index_sha256"]==ref(proof/"INDEX.json")["sha256"]and es["manifest_sha256"]==ref(proof/"CONSUMPTION-MANIFEST.json")["sha256"]and es["actual_host_release"]is False,"sixth actual emit stdout exact; emission-time no-release flag")
 h=RUN/"root-sixth-consumption-host-request-001"
 request=data(h/"RELEASE-REQUEST.actual.json","56ff6a0017b758f03f77af56c3006d1c6dd13d84c9b3f97f5fa9f44a9b31392e")
 closed(request,["schema","host_module","claim","consumption_manifest","registry","verifier_id","operator_id","next_intent_id"],"sixth ROOT actual closed host request")
 need(request["claim"]==emit["claim"]and request["consumption_manifest"]=={"path":str(proof/"CONSUMPTION-MANIFEST.json"),"sha256":ref(proof/"CONSUMPTION-MANIFEST.json")["sha256"]},"sixth release parent/manifest exact")
 need(read_ref(request["host_module"],"actual frozen host")["sha256"]=="f567bff41d03b6c59d195df8ff62ecab1a523962de3217d397c5264d1ed2d89b","frozen f567 host unchanged")
 registry=data(request["registry"]["path"],"9ed7f235124bcda7c40c8e78aa6c606a086c8d3270353014326452c9e25a15a0")
 need(read_ref(request["registry"],"actual ROOT registry")["sha256"]==ref(h/"REGISTRY.json")["sha256"],"request registry exact")
 v=registry["verifiers"][request["verifier_id"]]
 need(registry["schema"]=="ck3-ordinary-interaction-root-verifier-registry-v1"and v["entrypoint"]=="verifier.py:verify_consumption"and v["bundle_index"]==emit["bound_verifier_index"],"sixth registry actual bound verifier")
 need(read_ref(v["bundle_index"],"actual existing bound sixth INDEX")["sha256"]=="73a5baa900687050fa6ad0adab5574d0659344144bbae69c6da5c987e858d725","sixth bound INDEX exact no rebind")
 rr,rs=invocation(RUN/"root-sixth-consumption-release-invocation-001","d7f97c8ca0e2b2f8e5448f2001e01f6ccbd93ac26d2222bcc19f2e70d42c5e40")
 need(rs["game_command_sent"]is False and rs["business_acceptance_credit"]is False,"ROOT actual host release no game/business credit")
 permitpath=oldpath.with_suffix(".release.json")
 permit=data(permitpath,"b5bc8f3fc94c25be5b40014d943685bd6e45d3c0dc0e4e5d8d2f196d2072082a")
 closed(permit,["schema","claim_path","claim_sha256","claim_request_id","action_identity","old_connection_generation","manifest","registry","verifier_id","verifier_bundle","operator_id","next_intent_id","released_at_utc","scope","business_acceptance_credit"],"sixth permit closed schema")
 need(permit["schema"]=="ck3-ordinary-interaction-next-intent-permit-v1"and permit["claim_path"]==str(oldpath)and permit["claim_sha256"]==ref(oldpath)["sha256"]and permit["claim_request_id"]==old["request_id"]and permit["action_identity"]==identity,"sixth permit actual immutable ordinal5 parent")
 need(permit["manifest"]==request["consumption_manifest"]and permit["registry"]==request["registry"]and permit["verifier_bundle"]==v["bundle_index"]and all(permit[k]==request[k]for k in ["verifier_id","operator_id","next_intent_id"]),"sixth permit exact proof/registry/bundle/ROOT intent")
 need(permit["next_intent_id"]=="r10-proposal-007-after-consumed-1d9c-20261006"and permit["scope"]=="operator_verified_consumption_for_one_new_intent"and permit["business_acceptance_credit"]is False and rs["permit_path"]==str(permitpath)and rs["permit_sha256"]==ref(permitpath)["sha256"],"sixth permit actual one seventh intent/no JOIN credit")
 released=datetime.fromisoformat(permit["released_at_utc"])
 need(datetime.fromisoformat(rr["started_utc"])<=released<=datetime.fromisoformat(rr["completed_utc"]),"actual sixth permit time within invocation")
 sd=RUN/"mcp-client-evidence-002"
 fresh=sdk(sd/"0151-r10-0152-seventh-fresh-query.sdk-result.json","21721efc900d1b41b2c01664daeb5b0c9d1e6771f581c01a159704193b1ea40c")
 send=sdk(sd/"0152-r10-0153-seventh-new-initiate.sdk-result.json","4d8956229d7f369a1884e0c6a9bdbe92c44522a80741d861f62418b67f630c71")
 current=sdk(c["current_release_context_sdk"]["path"],c["current_release_context_sdk"]["sha256"])
 frame=sdk(c["current_release_context_frame_sdk"]["path"],c["current_release_context_frame_sdk"]["sha256"])
 newpath=Path(send["result"]["action_claim_path"]);need(newpath.parent.resolve()==CLAIM_DIR.resolve(),"actual SDK152 discovered new claim contained")
 new=data(newpath,"27999be4ffebc686a2961528d639886b07712fce5f1578935190448e1f8ded02")
 closed(new["action_identity"],identity.keys(),"ordinal6 exact sixidentity keys")
 need(new["action_identity"]==identity and new["host_provenance"]==old["host_provenance"]and new["claim_ordinal"]==old["claim_ordinal"]+1==6 and new["status"]=="claimed_result_unknown_no_retry","ordinal6 same process/provenance; original UNKNOWN claims unchanged")
 need(new["request_id"]==send["result"]["action_request_id"]=="ordinary-interaction-ce6f9c27e43f4d1c9057fb7746fcb815"and new["request_id"]!=old["request_id"],"actual distinct seventh UUID")
 consumedpath=permitpath.with_suffix(".consumed.json")
 consumed=data(consumedpath,"8bb774876e184adc346fd9a6684ec7b9d23146cac6665d0bdd8f8eea696987bb")
 need(consumed["schema"]=="ck3-ordinary-interaction-permit-consumption-v1"and consumed["permit_path"]==str(permitpath)and consumed["permit_sha256"]==ref(permitpath)["sha256"]and consumed["new_request_id"]==new["request_id"]and consumed["next_intent_id"]==permit["next_intent_id"],"sixth permit actually consumed for seventh ordinal6")
 need(consumed["new_binding"]==new["binding"]and consumed["action_identity"]==identity and consumed["business_acceptance_credit"]is False and consumed["old_connection_generation"]==consumed["new_connection_generation"]==permit["old_connection_generation"]==1,"consumed exact seventh binding/sixidentity/gen1 no business credit")
 lineage={"permit_path":str(permitpath),"permit_sha256":ref(permitpath)["sha256"],"next_intent_id":permit["next_intent_id"],"parent_claim_path":str(oldpath),"parent_claim_sha256":ref(oldpath)["sha256"]}
 need(new["new_intent_lineage"]==lineage and oldpath.name==stable+".00000005.claim.json"and newpath.name==stable+".00000006.claim.json","seventh actual ordinal6 immutable ordinal5/permit parent chain")
 binding=new["binding"];fr=frame["snapshot_after"];qr=fresh["result"];ct=qr["character_interaction_ordinary_context"]
 need(qr["queried_revision"]==binding["revision"]==fr["revision"]==70 and qr["queried_native_revision"]==binding["native_revision"]==fr["native_revision"]==69 and qr["queried_snapshot_id"]==binding["snapshot_id"]==fr["snapshot_id"]=="native:69","first151/frame149 exact public70/native69")
 need(c["actual_release_context"]=={"revision":70,"native_revision":69,"snapshot_id":"native:69","date_raw":53144712}and current["result"]["queried_native_revision"]==69,"later release150/frame149 separate from first query127")
 need(binding["date_raw"]==ct["date_raw"]==fr["date_raw"]==53144712 and binding["episode_run_id"]is None and binding["active_event_present"]is False and binding["incoming_interaction_present"]is False and fr["active_event"]is None and fr["pending_character_interaction"]is None and fr["paused"]is True,"actual seventh before date/paused/no event/incoming")
 need(ct["game_pid"]==13436 and ct["connection_generation"]==1 and ct["player_character_id"]==31254 and ct["recipient_id"]==65866 and ct["interaction_key"]==identity["interaction_key"]and all(ct[k]is True for k in ["shown","can_send","ready_to_initiate","actor_alive","recipient_alive","source_code_pins_verified","actor_binding_verified","recipient_binding_verified","owner_thread_verified","tls_verified","frame_verified"]),"seventh fresh151 actual positive full IDs/ready gates")
 need(ct["effective_roles"]=={"actor_id":31254,"recipient_id":65866,"secondary_actor_id":None,"secondary_recipient_id":None,"intermediary_id":None,"sixth_role_id":31254},"six native roles exact")
 need(all(x["session_id"]==new["host_provenance"]["session_id"]and x["profile_sha256"]==new["host_provenance"]["profile_sha256"]and x["pipe_name"]==new["host_provenance"]["pipe_name"]for x in [fresh,send,current,frame]),"actual new SDK profile/session/pipe exact")
 need(released<datetime.fromisoformat(fresh["recorded_at_utc"])<datetime.fromisoformat(send["recorded_at_utc"]),"sixth release precedes actual seventh fresh query/send")
 raw=newpath.with_suffix(".packet.bin").read_bytes()
 need(ref(newpath.with_suffix(".packet.bin"))["sha256"]=="9a466b607be252ec02f23e6dcfebde8328c919c31d8bac50e24f037aceef7323"and len(raw)==363 and struct.unpack("<I",raw[:4])[0]==359,"seventh actual packet hash/u32 length")
 packet=json.loads(raw[4:])
 expected={"type":"execute_step","protocol_version":1,"request_id":new["request_id"],"step":"initiate-character-interaction-ordinary-v1","expected_revision":69,"interaction_key":identity["interaction_key"],"recipient_id":65866,"expected_player_character_id":31254,"expected_game_pid":13436,"expected_connection_generation":1}
 need(packet==expected and len(packet)==10 and json.dumps(packet,separators=(",",":")).encode()==raw[4:],"seventh compact closed10 packet exact native69")
 native=data(newpath.with_suffix(".native-result.json"),"0d5d723406297f0c7bcf1c97105f5f1ba9653489b531b9e247366b8aabd6a2f3");ni=native["result"]["character_interaction_ordinary_initiation"]
 need(native["request_id"]==new["request_id"]and native["ok"]is True and ni==send["result"]["character_interaction_ordinary_initiation"]and ni["status"]=="pending"and ni["verification_pending"]is True and ni["business_postcondition_verified"]is False and ni["postcondition_verified"]is False,"seventh actual native/SDK pending only")
 receipt=data(newpath.with_suffix(".receipt.json"),"e50cd19d331f6e99d49c82b189b79e2209e7e1653a7c389965f366bf81a53c75")
 need(receipt["request_id"]==new["request_id"]and receipt["result"]==send["result"]and receipt["business_postcondition_verified"]is False and send["business_effects_verified"]is False and send["full_product_acceptance_credit"]is False,"seventh actual receipt no business credit")
 need(send["result"]["after_revision"]==70 and send["result"]["after_native_revision"]==69 and send["snapshot"]["revision"]==71 and send["snapshot"]["native_revision"]==70 and send["snapshot"]["snapshot_id"]=="native:70"and send["snapshot"]["active_event"]["instance_id"]==80,"driver70/69 retained apart from wrapper71/70 event80")
 for k in ["played_character_gold","played_character_piety","played_character_prestige"]:need(send["snapshot"][k]==fr[k],"seventh dispatch wallet unchanged "+k)
 prior=BASE/"r10-actual-fifth-consumption-release-lineage-independent-review-20261006-001"
 need(ref(prior/"REPORT.json")["sha256"]=="99e8a8cddda666b85824107fa968fde0c642b784598853c7ca7ae125e0985e33"and ref(prior/"INDEX.json")["sha256"]=="d9cff47fb7c4539a0ecd9a107fe1f508c3889497b725880555816fd0ce6afb60","earlier lineage summary immutable refs only; no earlier parent files rescan")
 first_failure=ref(BASE/"r10-actual-sixth-consumption-release-lineage-independent-review-20261006-001/FAILURE.json")
 report={"prior_review_expectation_failure_preserved":first_failure,"prior_failure_boundary":"Reviewer adaptation mistakenly renamed fixed sixth_role_id; no product/SDK failure. Original attempt001 unchanged.", "schema":"lyd.r10.actual-sixth-release-ordinal6-independent-review.v1","status":"ACTUAL_SIXTH_EMIT_RELEASE_PERMIT_CONSUMED_ORDINAL6_LINEAGE_MATCH","recorded_utc":datetime.now(timezone.utc).isoformat(),"checks_count":len(checks),"checks":checks,"actual_ROOT_sixth_emit":True,"actual_ROOT_sixth_release":True,"actual_sixth_permit_consumed":True,"released_request_consumption":{"claim_ordinal":5,"request_id":old["request_id"],"save_pair":"125-to129","serial_nonce_delta":[11,12],"wallet_delta":["0","0","0"],"completed_history_unchanged":True},"new_seventh_request":{"claim_ordinal":6,"request_id":new["request_id"],"native_status":"pending","driver_after":[70,69],"wrapper_snapshot":[71,70],"active_event_instance":80},"new_seventh_saved_serial_nonce":None,"seventh_saved_opening_AST_not_consumed_by_this_review":True,"seventh_request_consumption_credit":False,"six_action_identity":identity,"new_binding":binding,"new_parent_lineage":lineage,"actual_native_packet":packet,"immediate_ordinal5_parent_preserved":True,"earlier_parent_preservation_reused_only_from_frozen_summary":True,"old_parent_or_permit_files_rescanned":False,"ROOT_release_truth_separate_from_emission_historical_flags":True,"new_final_JOIN_credit":False,"full_cycle_credit":False,"ACK_business_credit":False,"permit_business_credit":False,"old_whole_payload_revalidation":False,"earlier_cases_tests_or_source_functions_rerun":False,"save_AST_reparsed":False,"reviewer_operations":{k:0 for k in ["bind","emit","registry_write","host_release","game","native","MCP","pipe","Client","bus","Git","main","save_AST_parse"]},"references":list(references.values())}
 (OUT/"REPORT.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 (OUT/Path(__file__).name).write_bytes(Path(__file__).read_bytes())
 ix={"schema":"lyd.external-evidence-index.v1","files":[{"path":p.name,"bytes":len(p.read_bytes()),"sha256":digest(p.read_bytes())}for p in sorted(OUT.iterdir())if p.is_file()]}
 (OUT/"INDEX.json").write_text(json.dumps(ix,indent=2)+"\n",encoding="utf-8")
 for p in OUT.iterdir():
  if p.is_file():os.chmod(p,0o444)
 print(json.dumps({"status":report["status"],"checks_count":len(checks),"REPORT":ref(OUT/"REPORT.json"),"INDEX":ref(OUT/"INDEX.json")}))
except Exception as e:
 (OUT/"FAILURE.json").write_text(json.dumps({"status":"READONLY_REVIEW_REJECTED","reason":str(e),"matched_checks":checks,"live_calls":0},indent=2)+"\n",encoding="utf-8");raise

