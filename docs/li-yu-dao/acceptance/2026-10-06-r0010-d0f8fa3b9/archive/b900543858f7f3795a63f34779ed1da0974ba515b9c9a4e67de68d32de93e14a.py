"""Read-only independent fifth consumption/release to sixth request lineage."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, os, struct
BASE=Path("C:/workspace/ck3_lyd_runtime_20261004")
RUN=BASE/"live-attempt-010"
OUT=BASE/"r10-actual-fifth-consumption-release-lineage-independent-review-20261006-001"
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
 proof=BASE/"r10-fifth-proposal-emitted-evidence-20261005-002"
 ix=data(proof/"INDEX.json","821d0a362327d74ecadda91c2e9d98e63ce3807e68a981fd5dd8c5dacb79b57c")
 seen=set()
 for row in ix["files"]:
  closed(row,["path","bytes","sha256"],"new fifth emit closed INDEX row")
  p=(proof/row["path"]).resolve();need(proof.resolve()in p.parents and row["path"]not in seen,"new fifth emit contained unique row")
  seen.add(row["path"]);r=ref(p);need(r["bytes"]==row["bytes"]and r["sha256"]==row["sha256"],"new fifth emit exact indexed "+row["path"])
 need(len(seen)==5 and seen=={p.name for p in proof.iterdir()if p.is_file()and p.name!="INDEX.json"},"new fifth emit complete five payload coverage")
 manifest=data(proof/"CONSUMPTION-MANIFEST.json","02bb7791d7e248c42db5f91a03259c00e2ea4c5dbf3c251050a9044ebdd69c6e")
 facts=data(proof/"INDEPENDENT-FACTS.json","e60d6ba8e9c30234cdffef662209a14226dbce0c14cbb5c55959450a85dd653a")
 detail=data(proof/"PRODUCT-DETAIL.json","f84542c8bf27491dcda4005405cb66c501205728b34afe820e8e3dca27845fd2")
 emit=data(proof/"EMISSION-REQUEST.raw.json","00a42cf6a09d3a4357563fa60d943a523525eab4280a8de40291694027bafe76")
 closed(facts,["schema","claim_request_id","action_identity","packet_sha256","native_result_sha256","unknown_sha256","before_artifact_sha256","after_artifact_sha256","consumption"],"new fifth emitted facts exact keys")
 oldpath=Path(emit["claim"]["path"]);old=data(oldpath,"be8013203068a19192934c6aebf5491f4c8f8b7483e60799a9df3413c48eff22")
 need(old["claim_ordinal"]==4 and old["status"]=="claimed_result_unknown_no_retry"and old["action_identity"]==identity,"ordinal4 immutable UNKNOWN parent preserved")
 need(facts["schema"]=="ck3-ordinary-interaction-independent-consumption-v1"and facts["claim_request_id"]==manifest["claim_request_id"]==old["request_id"]=="ordinary-interaction-9e0a5f40b68f4b6c826dbdcd422f2dd0"and facts["action_identity"]==manifest["action_identity"]==identity,"fifth facts bind actual9e0a ordinal4 sixidentity")
 consume={"kind":"save_round_delta","field_name":"lyd_c2_callback_nonce","before_value":10,"after_value":11,"actor_id":31254,"recipient_id":65866,"interaction_key":identity["interaction_key"]}
 need(facts["consumption"]==consume,"fifth consumption saved nonce10-to11 only")
 for key,field in [("packet","packet_sha256"),("native_result","native_result_sha256"),("before_artifact","before_artifact_sha256"),("after_artifact","after_artifact_sha256")]:
  need(read_ref(manifest[key],"fifth manifest "+key)["sha256"]==facts[field],"fifth facts exact "+key)
 need(manifest["unknown"]is None and facts["unknown_sha256"]is None,"genuine native pending receipt; no fabricated ACK")
 need(manifest["independent_report"]["sha256"]==ref(proof/"INDEPENDENT-FACTS.json")["sha256"],"manifest exact facts report")
 before=data(manifest["before_artifact"]["path"]);after=data(manifest["after_artifact"]["path"]);c=detail["conditions"]
 for v in [before,after]:closed(v["save"],["path","sha256","bytes"],"original fifth saved exact3 reference")
 need(type(before["save"]["bytes"])is int and type(after["save"]["bytes"])is int and before["save"]["bytes"]==91535016 and after["save"]["bytes"]==91539192 and detail["before_save"]==before["save"]and detail["after_save"]==after["save"],"actual original107-to111 save refs; no125 substitution")
 need(c["serial_nonce_before"]==[10,10]and c["serial_nonce_after"]==[11,11]and c["wallet_delta"]==["0","0","0"]and c["completed_history_unchanged"]is True,"fifth saved10-to11 wallet0/history unchanged")
 need(c["source_faith"]=="106"and c["target_faith"]=="104"and c["moving_rite"]=="169"and c["target_main"]=="159"and c["target_rep"]=="65866"and c["actual_source_roles"]==["31254","65865"]and c["actual_target_roles"]==["65866"]and c["actual_human_roles"]==["31254"],"actual fifth dynamic graph and positive full roles")
 need(c["consumption_mode"]=="PROPOSAL_OPENED"and c["join_business_acceptance_credit"]is False and c["NPC_vote_choice_required"]is False and detail["native_ACK_credit"]is False and detail["actual_release"]is False,"fifth emission historical proposal-only flags preserved")
 need(detail["source_revision"]=="d0f8fa3b9d444828759443aa018bfd7ad31b398d"and detail["parser_sha256"]=="6c1ba1006cd0dd5055c11115701b60a74562b0f23d91b756a3d9322e7d055cb7"and detail["reader_version"]=="lyd-join-save-consumption-verifier-v2","fifth source/parser actual pins")
 er,es=invocation(RUN/"root-fifth-consumption-emit-invocation-001","07087c480129f54a59db88959d2fb2d39ab2223757a0ee2c231d2b0125d7d23f")
 need(es["index_sha256"]==ref(proof/"INDEX.json")["sha256"]and es["manifest_sha256"]==ref(proof/"CONSUMPTION-MANIFEST.json")["sha256"]and es["actual_host_release"]is False,"fifth actual emit stdout exact; emission-time no-release flag")
 h=RUN/"root-fifth-consumption-host-request-001"
 request=data(h/"RELEASE-REQUEST.actual.json","53ab7f79271df5d16a94af61576ad35b06b72499a1247d7d5fd3759cf97a7f9f")
 closed(request,["schema","host_module","claim","consumption_manifest","registry","verifier_id","operator_id","next_intent_id"],"fifth ROOT actual closed host request")
 need(request["claim"]==emit["claim"]and request["consumption_manifest"]=={"path":str(proof/"CONSUMPTION-MANIFEST.json"),"sha256":ref(proof/"CONSUMPTION-MANIFEST.json")["sha256"]},"fifth release parent/manifest exact")
 need(read_ref(request["host_module"],"actual frozen host")["sha256"]=="f567bff41d03b6c59d195df8ff62ecab1a523962de3217d397c5264d1ed2d89b","frozen f567 host unchanged")
 registry=data(request["registry"]["path"],"5dcd23652b90df9a4dc3d336418ea8d661443dd17819e22bdcd9aaa101ed744e")
 need(read_ref(request["registry"],"actual ROOT registry")["sha256"]==ref(h/"REGISTRY.json")["sha256"],"request registry exact")
 v=registry["verifiers"][request["verifier_id"]]
 need(registry["schema"]=="ck3-ordinary-interaction-root-verifier-registry-v1"and v["entrypoint"]=="verifier.py:verify_consumption"and v["bundle_index"]==emit["bound_verifier_index"],"fifth registry actual bound verifier")
 need(read_ref(v["bundle_index"],"actual existing bound fifth INDEX")["sha256"]=="50de10880895b5f86cc0e41cd1686d5f3da56709280b9988afa457d860ea43ed","fifth bound INDEX exact no rebind")
 rr,rs=invocation(RUN/"root-fifth-consumption-release-invocation-001","5ae523b46c4316fc011adc188676a36648f420ca6d8342bb0d80230c0f0f0d0e")
 need(rs["game_command_sent"]is False and rs["business_acceptance_credit"]is False,"ROOT actual host release no game/business credit")
 permitpath=oldpath.with_suffix(".release.json")
 permit=data(permitpath,"350483fb0032e95b83d99e2321e02186f44d3190c2d2e206490517d88295485a")
 closed(permit,["schema","claim_path","claim_sha256","claim_request_id","action_identity","old_connection_generation","manifest","registry","verifier_id","verifier_bundle","operator_id","next_intent_id","released_at_utc","scope","business_acceptance_credit"],"fifth permit closed schema")
 need(permit["schema"]=="ck3-ordinary-interaction-next-intent-permit-v1"and permit["claim_path"]==str(oldpath)and permit["claim_sha256"]==ref(oldpath)["sha256"]and permit["claim_request_id"]==old["request_id"]and permit["action_identity"]==identity,"fifth permit actual immutable ordinal4 parent")
 need(permit["manifest"]==request["consumption_manifest"]and permit["registry"]==request["registry"]and permit["verifier_bundle"]==v["bundle_index"]and all(permit[k]==request[k]for k in ["verifier_id","operator_id","next_intent_id"]),"fifth permit exact proof/registry/bundle/ROOT intent")
 need(permit["next_intent_id"]=="r10-proposal-006-after-consumed-9e0a-20261005"and permit["scope"]=="operator_verified_consumption_for_one_new_intent"and permit["business_acceptance_credit"]is False and rs["permit_path"]==str(permitpath)and rs["permit_sha256"]==ref(permitpath)["sha256"],"fifth permit actual one sixth intent/no JOIN credit")
 released=datetime.fromisoformat(permit["released_at_utc"])
 need(datetime.fromisoformat(rr["started_utc"])<=released<=datetime.fromisoformat(rr["completed_utc"]),"actual fifth permit time within invocation")
 sd=RUN/"mcp-client-evidence-002"
 fresh=sdk(sd/"0127-r10-0128-sixth-fresh-query.sdk-result.json","b233c9ed3ece500c5bc68357de621fea8b6c37ba72142dc3ffb302f4bcf940f6")
 send=sdk(sd/"0128-r10-0129-sixth-proposal.sdk-result.json","63f1313773e6f6187531a7ea58a891483fad8a478043e3371e30aaa1631f1f05")
 current=sdk(c["current_release_context_sdk"]["path"],c["current_release_context_sdk"]["sha256"])
 frame=sdk(c["current_release_context_frame_sdk"]["path"],c["current_release_context_frame_sdk"]["sha256"])
 newpath=Path(send["result"]["action_claim_path"]);need(newpath.parent.resolve()==CLAIM_DIR.resolve(),"actual SDK128 discovered new claim contained")
 new=data(newpath,"47c844c0decce779351f2c5b3f2016dc6aae0b0ac6b3b0fc60bcc3b6d2fea0c8")
 closed(new["action_identity"],identity.keys(),"ordinal5 exact sixidentity keys")
 need(new["action_identity"]==identity and new["host_provenance"]==old["host_provenance"]and new["claim_ordinal"]==old["claim_ordinal"]+1==5 and new["status"]=="claimed_result_unknown_no_retry","ordinal5 same process/provenance; original UNKNOWN claims unchanged")
 need(new["request_id"]==send["result"]["action_request_id"]=="ordinary-interaction-1d9cf9c7db6e4ea2be6872d6427cf2a4"and new["request_id"]!=old["request_id"],"actual distinct sixth UUID")
 consumedpath=permitpath.with_suffix(".consumed.json")
 consumed=data(consumedpath,"f1f337321a3cea71076103700f92ead83104f9e4bf3cca5d823123490fb46aef")
 need(consumed["schema"]=="ck3-ordinary-interaction-permit-consumption-v1"and consumed["permit_path"]==str(permitpath)and consumed["permit_sha256"]==ref(permitpath)["sha256"]and consumed["new_request_id"]==new["request_id"]and consumed["next_intent_id"]==permit["next_intent_id"],"fifth permit actually consumed for sixth ordinal5")
 need(consumed["new_binding"]==new["binding"]and consumed["action_identity"]==identity and consumed["business_acceptance_credit"]is False and consumed["old_connection_generation"]==consumed["new_connection_generation"]==permit["old_connection_generation"]==1,"consumed exact sixth binding/sixidentity/gen1 no business credit")
 lineage={"permit_path":str(permitpath),"permit_sha256":ref(permitpath)["sha256"],"next_intent_id":permit["next_intent_id"],"parent_claim_path":str(oldpath),"parent_claim_sha256":ref(oldpath)["sha256"]}
 need(new["new_intent_lineage"]==lineage and oldpath.name==stable+".00000004.claim.json"and newpath.name==stable+".00000005.claim.json","sixth actual ordinal5 immutable ordinal4/permit parent chain")
 binding=new["binding"];fr=frame["snapshot_after"];qr=fresh["result"];ct=qr["character_interaction_ordinary_context"]
 need(qr["queried_revision"]==binding["revision"]==fr["revision"]==59 and qr["queried_native_revision"]==binding["native_revision"]==fr["native_revision"]==58 and qr["queried_snapshot_id"]==binding["snapshot_id"]==fr["snapshot_id"]=="native:58","first127/frame125 exact public59/native58")
 need(c["actual_release_context"]=={"revision":59,"native_revision":58,"snapshot_id":"native:58","date_raw":53144712}and current["result"]["queried_native_revision"]==58,"later release126/frame125 separate from first query127")
 need(binding["date_raw"]==ct["date_raw"]==fr["date_raw"]==53144712 and binding["episode_run_id"]is None and binding["active_event_present"]is False and binding["incoming_interaction_present"]is False and fr["active_event"]is None and fr["pending_character_interaction"]is None and fr["paused"]is True,"actual sixth before date/paused/no event/incoming")
 need(ct["game_pid"]==13436 and ct["connection_generation"]==1 and ct["player_character_id"]==31254 and ct["recipient_id"]==65866 and ct["interaction_key"]==identity["interaction_key"]and all(ct[k]is True for k in ["shown","can_send","ready_to_initiate","actor_alive","recipient_alive","source_code_pins_verified","actor_binding_verified","recipient_binding_verified","owner_thread_verified","tls_verified","frame_verified"]),"sixth fresh127 actual positive full IDs/ready gates")
 need(ct["effective_roles"]=={"actor_id":31254,"recipient_id":65866,"secondary_actor_id":None,"secondary_recipient_id":None,"intermediary_id":None,"sixth_role_id":31254},"six native roles exact")
 need(all(x["session_id"]==new["host_provenance"]["session_id"]and x["profile_sha256"]==new["host_provenance"]["profile_sha256"]and x["pipe_name"]==new["host_provenance"]["pipe_name"]for x in [fresh,send,current,frame]),"actual new SDK profile/session/pipe exact")
 need(released<datetime.fromisoformat(fresh["recorded_at_utc"])<datetime.fromisoformat(send["recorded_at_utc"]),"fifth release precedes actual sixth fresh query/send")
 raw=newpath.with_suffix(".packet.bin").read_bytes()
 need(ref(newpath.with_suffix(".packet.bin"))["sha256"]=="04b7d5fe01cf4e763e5f7aea29b32090e9e5ac8e39d718b0ec106504b6daf7a7"and len(raw)==363 and struct.unpack("<I",raw[:4])[0]==359,"sixth actual packet hash/u32 length")
 packet=json.loads(raw[4:])
 expected={"type":"execute_step","protocol_version":1,"request_id":new["request_id"],"step":"initiate-character-interaction-ordinary-v1","expected_revision":58,"interaction_key":identity["interaction_key"],"recipient_id":65866,"expected_player_character_id":31254,"expected_game_pid":13436,"expected_connection_generation":1}
 need(packet==expected and len(packet)==10 and json.dumps(packet,separators=(",",":")).encode()==raw[4:],"sixth compact closed10 packet exact native58")
 native=data(newpath.with_suffix(".native-result.json"),"bcf26907299ec49da07e14da0cb1cb04c193ebd852708c678ace4023a8e98b2d");ni=native["result"]["character_interaction_ordinary_initiation"]
 need(native["request_id"]==new["request_id"]and native["ok"]is True and ni==send["result"]["character_interaction_ordinary_initiation"]and ni["status"]=="pending"and ni["verification_pending"]is True and ni["business_postcondition_verified"]is False and ni["postcondition_verified"]is False,"sixth actual native/SDK pending only")
 receipt=data(newpath.with_suffix(".receipt.json"),"d757bcfe5b7f1162369f97b6bf1fd6498597fb3de5a9e9de12d08f1abdcdb25c")
 need(receipt["request_id"]==new["request_id"]and receipt["result"]==send["result"]and receipt["business_postcondition_verified"]is False and send["business_effects_verified"]is False and send["full_product_acceptance_credit"]is False,"sixth actual receipt no business credit")
 need(send["result"]["after_revision"]==59 and send["result"]["after_native_revision"]==58 and send["snapshot"]["revision"]==60 and send["snapshot"]["native_revision"]==59 and send["snapshot"]["snapshot_id"]=="native:59"and send["snapshot"]["active_event"]["instance_id"]==74,"driver59/58 retained apart from wrapper60/59 event74")
 for k in ["played_character_gold","played_character_piety","played_character_prestige"]:need(send["snapshot"][k]==fr[k],"sixth dispatch wallet unchanged "+k)
 savedroot=BASE/"r10-actual-fifth-open-join-readback-20261005-001"
 need(ref(savedroot/"INDEX.json")["sha256"]=="44c0bf5edc6e03c8cf5e1589ee8854842b12359449e5b9862b0d50ee79a20ba0","prior sealed fifth open report INDEX reused")
 sr=data(savedroot/"REPORT.json","5537fd873eeaf3913e1910cab34436c46213dd5b6a6bb5e685eebd052c59e32f")
 need(sr["before_save"]==detail["before_save"]and sr["after_save"]==detail["after_save"]and sr["all_binding_and_protection_checks"]["actual_nonce10_to11"]is True and sr["all_binding_and_protection_checks"]["actual_serial10_to11"]is True and sr["all_binding_and_protection_checks"]["actual_wallet_history_unchanged"]is True and sr["final_JOIN_credit"]is False,"reuse actual107-to111 saved fifth10-to11 no AST scan")
 prior=BASE/"r10-actual-fourth-consumption-release-lineage-independent-review-20261005-001"
 need(ref(prior/"REPORT.json")["sha256"]=="c7865b6563e5f458f6950a0b4c89429f62b1226b932621effd8aba5e7863fc1c"and ref(prior/"INDEX.json")["sha256"]=="ccb5f0c6160af6f6b84c4d547bdd63e0a05397391d810c76e327778eb1935168","prior independent chain exact refs only no old payload scan")
 oldclaims=["3fae018f1468983c59bb0cf6a8d32704cb6f791d6b25cae69451a82960b495ce","7c2d0d36486fc2ec6c0d44fb24319affdce818feb3edb59d6878921e3d00c021","1b2becdcfc4423afaa2a3e5ab8c550cd929425d1034abc23af2fdd0f4cd640c7","ef93faeb5bcaef43a53fa35e98a80d37d675f0f4f4a80e080aea004b17474c03","be8013203068a19192934c6aebf5491f4c8f8b7483e60799a9df3413c48eff22"]
 for n,pin in enumerate(oldclaims):need(ref(CLAIM_DIR/(stable+f".{n:08d}.claim.json"))["sha256"]==pin,"immutable original claim ordinal"+str(n))
 oldpermits=[("6c7fd772f928041d1d616b77e9d5c00d27441ef6e52e1f030c14fe5b60b77c84","35287deac29f81d36d3d6978ba16253bac4ae954a4beba9ebd5852f179cea0ea"),("61ee8cb86f971acae5f1ecd46f3410e6181389deb42979f1f4e030abec38ed72","d2b863b79cfeb69c713208aaf525a33b3db781b4013d4fdb32db7cd266a4e6c5"),("3807abad2ec04820a677612dacc7b1b914222f30473320414fd90e1c1e554d59","2f6a17134f49fd9b0120693f355a72d619d0b217162d5c3e5f8495c2c97e3a0d"),("a2c0a17d6347ccf7fb6178eb92339f7f2811ccdc691b56bca5c69b08e31a76bd","fb3c866dd928345a434098a158e4157f1c77504075efe822aad2e9f75e6967ab")]
 for n,(pin,cpin)in enumerate(oldpermits):
  p=CLAIM_DIR/(stable+f".{n:08d}.claim.release.json");need(ref(p)["sha256"]==pin and ref(p.with_suffix(".consumed.json"))["sha256"]==cpin,"original prior permit/consumed ordinal"+str(n))
 report={"schema":"lyd.r10.actual-fifth-release-ordinal5-independent-review.v1","status":"ACTUAL_FIFTH_EMIT_RELEASE_PERMIT_CONSUMED_ORDINAL5_LINEAGE_MATCH","recorded_utc":datetime.now(timezone.utc).isoformat(),"checks_count":len(checks),"checks":checks,"actual_ROOT_fifth_emit":True,"actual_ROOT_fifth_release":True,"actual_fifth_permit_consumed":True,"released_request_consumption":{"claim_ordinal":4,"request_id":old["request_id"],"save_pair":"107-to111","serial_nonce_delta":[10,11],"wallet_delta":["0","0","0"],"completed_history_unchanged":True},"new_sixth_request":{"claim_ordinal":5,"request_id":new["request_id"],"native_status":"pending","driver_after":[59,58],"wrapper_snapshot":[60,59],"active_event_instance":74},"new_sixth_saved_serial_nonce":None,"sixth_saved_opening_AST_not_consumed_by_this_review":True,"sixth_request_consumption_credit":False,"six_action_identity":identity,"new_binding":binding,"new_parent_lineage":lineage,"actual_native_packet":packet,"immutable_original_ordinal0_1_2_3_4_preserved":True,"all_prior_permit_consumption_records_preserved":True,"ROOT_release_truth_separate_from_emission_historical_flags":True,"new_final_JOIN_credit":False,"full_cycle_credit":False,"ACK_business_credit":False,"permit_business_credit":False,"old_whole_payload_revalidation":False,"earlier_cases_tests_or_source_functions_rerun":False,"save_AST_reparsed":False,"reviewer_operations":{k:0 for k in ["bind","emit","registry_write","host_release","game","native","MCP","pipe","Client","bus","Git","main","save_AST_parse"]},"references":list(references.values())}
 (OUT/"REPORT.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 (OUT/Path(__file__).name).write_bytes(Path(__file__).read_bytes())
 ix={"schema":"lyd.external-evidence-index.v1","files":[{"path":p.name,"bytes":len(p.read_bytes()),"sha256":digest(p.read_bytes())}for p in sorted(OUT.iterdir())if p.is_file()]}
 (OUT/"INDEX.json").write_text(json.dumps(ix,indent=2)+"\n",encoding="utf-8")
 for p in OUT.iterdir():
  if p.is_file():os.chmod(p,0o444)
 print(json.dumps({"status":report["status"],"checks_count":len(checks),"REPORT":ref(OUT/"REPORT.json"),"INDEX":ref(OUT/"INDEX.json")}))
except Exception as e:
 (OUT/"FAILURE.json").write_text(json.dumps({"status":"READONLY_REVIEW_REJECTED","reason":str(e),"matched_checks":checks,"live_calls":0},indent=2)+"\n",encoding="utf-8");raise

