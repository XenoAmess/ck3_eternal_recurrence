"""Read-only review of actual ROOT release and next-intent lineage; no host calls."""
from pathlib import Path
from datetime import datetime, timezone
import ast
import hashlib
import json
import os
import struct

BASE = Path("C:/workspace/ck3_lyd_runtime_20261004")
RUN = BASE / "live-attempt-010"
OUT = BASE / "r10-actual-fourth-consumption-release-lineage-independent-review-20261005-001"
CLAIM_DIR = RUN / "native-state/native-session/ordinary-interaction-actions"
checks = []
references = {}

def digest(data):
    return hashlib.sha256(data).hexdigest()

def ref(path):
    path = Path(path)
    raw = path.read_bytes()
    result = {"path": str(path), "bytes": len(raw), "sha256": digest(raw)}
    references[str(path)] = result
    return result

def data(path, expected=None):
    path = Path(path)
    item = ref(path)
    if expected is not None:
        need(item["sha256"] == expected, "actual SHA " + path.name)
    return json.loads(path.read_bytes())

def need(condition, label):
    if not condition:
        raise ValueError(label)
    checks.append(label)

def closed(value, keys, label):
    need(type(value) is dict and set(value) == set(keys), label)

def read_ref(value, label):
    need(type(value) is dict and set(value) in ({"path", "sha256"}, {"path", "sha256", "bytes"}), label + " ref schema")
    actual = ref(value["path"])
    need(actual["sha256"] == value["sha256"] and ("bytes" not in value or actual["bytes"] == value["bytes"]), label + " exact bytes/SHA")
    return actual

def sdk(path, sha):
    path = Path(path)
    value = data(path, sha)
    need(value["isError"] is False and value["resultType"] == "complete", path.name + " actual SDK complete")
    receipt = value["structuredContent"]
    texts = [json.loads(item["text"]) for item in value["content"] if item.get("type") == "text"]
    need(len(texts) == 1 and texts[0] == receipt, path.name + " structured/text equality")
    return receipt

def same_path(a, b):
    return Path(a).resolve() == Path(b).resolve()

def source_function(path, function_name):
    raw = Path(path).read_bytes()
    tree = ast.parse(raw.decode("utf-8"))
    functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == function_name]
    need(len(functions) == 1, function_name + " actual source function")
    node = functions[0]
    return {"path": str(path), "source_sha256": digest(raw), "function": function_name,
            "line": node.lineno, "end_line": node.end_lineno,
            "AST_sha256": digest(ast.dump(node, include_attributes=False).encode())}

def verify_index(root, pin, allow_seal=False):
    index=data(root/"INDEX.json",pin);seen=set()
    for row in index["files"]:
        closed(row,["path","bytes","sha256"],"new indexed exact row")
        target=(root/row["path"]).resolve()
        need(root.resolve()in target.parents and row["path"]not in seen,"new indexed contained/unique path")
        seen.add(row["path"]);a=ref(target)
        need(a["bytes"]==row["bytes"]and a["sha256"]==row["sha256"],"new payload exact "+row["path"])
    actual={str(p.relative_to(root)).replace("\\","/")for p in root.rglob("*")if p.is_file()and p.name!="INDEX.json"}
    extras=actual-seen
    need(not(seen-actual)and (not extras or allow_seal and extras=={"SEALED.json"}),"new INDEX full payload coverage; only explicit sealing sidecar allowed")
    if extras:
        seal=data(root/"SEALED.json");closed(seal,["REPORT","INDEX","typed_facts","files"],"new explicit SEALED schema")
        need(seal["files"]==len(seen),"new SEALED exact payload count")
        for name,filename in [("REPORT","REPORT.json"),("INDEX","INDEX.json"),("typed_facts","PROPOSAL-OPENED-FACTS.json")]:
            need(same_path(seal[name]["path"],root/filename),"SEALED contained exact "+name)
            read_ref(seal[name],"SEALED "+name)
    return index

def invocation(root, pin):
    result=data(root/"RESULT.json",pin);argv=data(root/"argv.json");source=data(result["argv_source"],result["argv_source_sha256"])
    need(result["exit_code"]==0 and result["status"]=="INVOCATION_COMPLETED"and source["argv"]==argv,"actual ROOT "+root.name+" exit0 and exact argv")
    need(ref(root/"stdout.txt")["sha256"]==result["stdout_sha256"]and ref(root/"stderr.txt")["sha256"]==result["stderr_sha256"]and(root/"stderr.txt").read_bytes()==b"","actual ROOT "+root.name+" exact stdio")
    return result,data(root/"stdout.txt"),argv

if OUT.exists():raise FileExistsError("append-only review output exists")
OUT.mkdir()
try:
    identity={"game_pid":13436,"actor_id":31254,"process_create_time":1791196395.7422996,
              "interaction_key":"lyd_c2_propose_join_interaction","recipient_id":65866,"action":"initiate_ordinary"}
    stable=digest(json.dumps(identity,sort_keys=True).encode())
    proof=BASE/"r10-fourth-proposal-emitted-evidence-20261005-002"
    index=verify_index(proof,"467d16c5d3d27e2aeb91b175dccba93a8585f06aa38df297f08925536037e0c1")
    need(len(index["files"])==5,"actual fourth emit exact5 payloads")
    manifest=data(proof/"CONSUMPTION-MANIFEST.json","94b4b4a78b0a63e830bccc72fbc4e66af730ec288bb86cbc6b0a032ab0772640")
    facts=data(proof/"INDEPENDENT-FACTS.json","d412e8fc26e1d8d57d75794c3834ec88a95cd46fd9c33eebfd523e5047a79064")
    detail=data(proof/"PRODUCT-DETAIL.json","89e70e4e027e4811a2f088dcc4e4507b0afc75f5e478cc8346529bf71d06a3e9")
    emit_request=data(proof/"EMISSION-REQUEST.raw.json","a01aed3eee14ca4c1cde5e9d0c141d246ca0fd7387e98694451dde9ef183833b")
    need(emit_request==data(BASE/"r10-fourth-proposal-proof-inputs-20261005-002/EMIT-REQUEST.actual.json"),"fourth actual emission request exact captured author002")
    closed(facts,["schema","claim_request_id","action_identity","packet_sha256","native_result_sha256","unknown_sha256","before_artifact_sha256","after_artifact_sha256","consumption"],"third emitted closed facts")
    oldpath=Path(emit_request["claim"]["path"])
    old=data(oldpath,"ef93faeb5bcaef43a53fa35e98a80d37d675f0f4f4a80e080aea004b17474c03")
    need(old["claim_ordinal"]==3 and old["status"]=="claimed_result_unknown_no_retry"and old["action_identity"]==identity,"ordinal3 immutable UNKNOWN parent preserved")
    need(facts["schema"]=="ck3-ordinary-interaction-independent-consumption-v1"and facts["claim_request_id"]==manifest["claim_request_id"]==old["request_id"]=="ordinary-interaction-76a5607e59804b76ad5dbe3f98fc126c"and facts["action_identity"]==manifest["action_identity"]==identity,"actual fourth proof exactly old76a5 ordinal3 sixidentity")
    expected_consumption={"kind":"save_round_delta","field_name":"lyd_c2_callback_nonce","before_value":9,"after_value":10,"actor_id":31254,"recipient_id":65866,"interaction_key":identity["interaction_key"]}
    need(facts["consumption"]==expected_consumption,"fourth consumption nonce9-to10 only")
    for key,field in [("packet","packet_sha256"),("native_result","native_result_sha256"),("before_artifact","before_artifact_sha256"),("after_artifact","after_artifact_sha256")]:
        need(read_ref(manifest[key],"third manifest "+key)["sha256"]==facts[field],"actual third facts exact "+key)
    need(manifest["unknown"]is None and facts["unknown_sha256"]is None,"fourth uses genuine native pending receipt; no fake ACK")
    need(manifest["independent_report"]["sha256"]==references[str(proof/"INDEPENDENT-FACTS.json")]["sha256"],"fourth manifest exact independent facts")
    before=data(manifest["before_artifact"]["path"]);after=data(manifest["after_artifact"]["path"]);c=detail["conditions"]
    for obs in [before,after]:closed(obs["save"],["path","sha256","bytes"],"third saved exact3 ref")
    need(type(before["save"]["bytes"])is int and type(after["save"]["bytes"])is int and before["save"]["bytes"]==91533790 and after["save"]["bytes"]==91538147 and detail["before_save"]==before["save"]and detail["after_save"]==after["save"],"fourth actual original saved82-to88 exact bytes; no107 reserve substitution")
    need(c["serial_nonce_before"]==[9,9]and c["serial_nonce_after"]==[10,10]and c["wallet_delta"]==["0","0","0"]and c["completed_history_unchanged"]is True,"actual emitted fourth9-to10 wallet0/historysame")
    need(c["source_faith"]=="106"and c["target_faith"]=="104"and c["moving_rite"]=="169"and c["target_main"]=="159"and c["target_rep"]=="65866"and c["actual_source_roles"]==["31254","65865"]and c["actual_target_roles"]==["65866"]and c["actual_human_roles"]==["31254"],"fourth actual positive dynamic graph/roles")
    need(c["consumption_mode"]=="PROPOSAL_OPENED"and c["join_business_acceptance_credit"]is False and c["NPC_vote_choice_required"]is False and detail["native_ACK_credit"]is False and detail["actual_release"]is False,"fourth emission proposal-only historical flags preserved")
    need(detail["source_revision"]=="d0f8fa3b9d444828759443aa018bfd7ad31b398d"and detail["parser_sha256"]=="6c1ba1006cd0dd5055c11115701b60a74562b0f23d91b756a3d9322e7d055cb7"and detail["reader_version"]=="lyd-join-save-consumption-verifier-v2","fourth actual source/parser frozen")
    er,es,ea=invocation(RUN/"root-fourth-consumption-emit-invocation-001","c61508375c8318557b59579aa98a201a8bdc7748ac053a27c21bfb34e9cffd13")
    need(es["index_sha256"]==references[str(proof/"INDEX.json")]["sha256"]and es["manifest_sha256"]==references[str(proof/"CONSUMPTION-MANIFEST.json")]["sha256"]and es["actual_host_release"]is False,"actual fourth emit stdout exact output proof and historical no-release flag")

    h=RUN/"root-fourth-consumption-host-request-001"
    request=data(h/"RELEASE-REQUEST.actual.json","d103275bbd5202ccc38e8ebd48d3d8af2be618c3eefffa94549e0416398aaf67")
    closed(request,["schema","host_module","claim","consumption_manifest","registry","verifier_id","operator_id","next_intent_id"],"third actual closed release request")
    need(request["claim"]==emit_request["claim"]and request["consumption_manifest"]=={"path":str(proof/"CONSUMPTION-MANIFEST.json"),"sha256":references[str(proof/"CONSUMPTION-MANIFEST.json")]["sha256"]},"fourth release exact parent and proof manifest")
    need(read_ref(request["host_module"],"third actual host")["sha256"]=="f567bff41d03b6c59d195df8ff62ecab1a523962de3217d397c5264d1ed2d89b","actual host unchanged f567")
    registry=data(request["registry"]["path"],"68244f333571e260be8b1a26dfdae984d04859ea30745c63702a609a78231df6")
    v=registry["verifiers"][request["verifier_id"]]
    need(registry["schema"]=="ck3-ordinary-interaction-root-verifier-registry-v1"and v["entrypoint"]=="verifier.py:verify_consumption"and v["bundle_index"]==emit_request["bound_verifier_index"],"fourth ROOT registry exact actual bound fourth001")
    need(read_ref(v["bundle_index"],"third actual bound INDEX")["sha256"]=="c4d04103c04a179c0f81cfdab9d6d4531b46a50c48e544f757398849ec3b60f6","fourth existing actual bound INDEX exact")
    rr,rs,ra=invocation(RUN/"root-fourth-consumption-release-invocation-001","50046db7c981f507adacaa24d721bd7b43a8d3eb6a700340fcf4a609176a6883")
    need(rs["game_command_sent"]is False and rs["business_acceptance_credit"]is False,"fourth host release no game command/business credit")
    permitpath=oldpath.with_suffix(".release.json")
    permit=data(permitpath,"a2c0a17d6347ccf7fb6178eb92339f7f2811ccdc691b56bca5c69b08e31a76bd")
    closed(permit,["schema","claim_path","claim_sha256","claim_request_id","action_identity","old_connection_generation","manifest","registry","verifier_id","verifier_bundle","operator_id","next_intent_id","released_at_utc","scope","business_acceptance_credit"],"third permit actual closed schema")
    need(permit["schema"]=="ck3-ordinary-interaction-next-intent-permit-v1"and permit["claim_path"]==str(oldpath)and permit["claim_sha256"]==references[str(oldpath)]["sha256"]and permit["claim_request_id"]==old["request_id"]and permit["action_identity"]==identity,"fourth permit exact immutable ordinal3 parent/identity")
    need(permit["manifest"]==request["consumption_manifest"]and permit["registry"]==request["registry"]and permit["verifier_bundle"]==v["bundle_index"]and all(permit[k]==request[k]for k in ["verifier_id","operator_id","next_intent_id"]),"fourth permit exact proof/registry/bundle/ROOT intent")
    need(permit["next_intent_id"]=="r10-proposal-005-after-consumed-76a5-20261005"and permit["scope"]=="operator_verified_consumption_for_one_new_intent"and permit["business_acceptance_credit"]is False and rs["permit_path"]==str(permitpath)and rs["permit_sha256"]==references[str(permitpath)]["sha256"],"fourth permit single fifth intent/no JOIN credit; actual stdout exact")
    released=datetime.fromisoformat(permit["released_at_utc"])
    need(datetime.fromisoformat(rr["started_utc"])<=released<=datetime.fromisoformat(rr["completed_utc"]),"fourth permit time inside ROOT release invocation")

    sd=RUN/"mcp-client-evidence-002"
    fresh=sdk(sd/"0109-r10-0110-fifth-fresh-query.sdk-result.json","929e9d361ac0c3903fb1822248cf50b5d1a3a13d80d3c901310bc6422e29e62d")
    send=sdk(sd/"0110-r10-0111-fifth-proposal.sdk-result.json","cd573e3bb5c22dad81d03ad083cd606fcd60b268b80d9accec62a149f72e1f8d")
    context84=sdk(c["current_release_context_sdk"]["path"],c["current_release_context_sdk"]["sha256"])
    frame82=sdk(c["current_release_context_frame_sdk"]["path"],c["current_release_context_frame_sdk"]["sha256"])
    newpath=Path(send["result"]["action_claim_path"])
    need(newpath.parent.resolve()==CLAIM_DIR.resolve(),"actual ordinal4 SDK110 discovered path contained")
    new=data(newpath,"be8013203068a19192934c6aebf5491f4c8f8b7483e60799a9df3413c48eff22")
    closed(new["action_identity"],identity.keys(),"ordinal3 exact sixidentity keys")
    need(new["action_identity"]==identity and new["host_provenance"]==old["host_provenance"]and new["claim_ordinal"]==old["claim_ordinal"]+1==4 and new["status"]=="claimed_result_unknown_no_retry","ordinal4 same PID/create/profile/session/identity; ordinal3 immutable UNKNOWN preserved")
    need(new["request_id"]==send["result"]["action_request_id"]=="ordinary-interaction-9e0a5f40b68f4b6c826dbdcd422f2dd0"and new["request_id"]!=old["request_id"],"actual ordinal4 distinct fifth UUID")
    consumedpath=permitpath.with_suffix(".consumed.json")
    consumed=data(consumedpath,"fb3c866dd928345a434098a158e4157f1c77504075efe822aad2e9f75e6967ab")
    need(consumed["schema"]=="ck3-ordinary-interaction-permit-consumption-v1"and consumed["permit_path"]==str(permitpath)and consumed["permit_sha256"]==references[str(permitpath)]["sha256"]and consumed["new_request_id"]==new["request_id"]and consumed["next_intent_id"]==permit["next_intent_id"],"fourth permit genuinely consumed once for actual9e0a ordinal4")
    need(consumed["new_binding"]==new["binding"]and consumed["action_identity"]==identity and consumed["business_acceptance_credit"]is False and consumed["old_connection_generation"]==consumed["new_connection_generation"]==permit["old_connection_generation"]==1,"fourth consumption exact binding/sixidentity/gen1/no business credit")
    lineage={"permit_path":str(permitpath),"permit_sha256":references[str(permitpath)]["sha256"],"next_intent_id":permit["next_intent_id"],"parent_claim_path":str(oldpath),"parent_claim_sha256":references[str(oldpath)]["sha256"]}
    need(new["new_intent_lineage"]==lineage and oldpath.name==stable+".00000003.claim.json"and newpath.name==stable+".00000004.claim.json","actual ordinal4 exact immutable ordinal3/permit parent chain")
    binding=new["binding"];fr=frame82["snapshot_after"];qr=fresh["result"];ct=qr["character_interaction_ordinary_context"]
    need(qr["queried_revision"]==binding["revision"]==fr["revision"]==50 and qr["queried_native_revision"]==binding["native_revision"]==fr["native_revision"]==49 and qr["queried_snapshot_id"]==binding["snapshot_id"]==fr["snapshot_id"]=="native:49","actual fresh109/frame107 public50/native49")
    need(c["actual_release_context"]=={"revision":50,"native_revision":49,"snapshot_id":"native:49","date_raw":53144712}and context84["result"]["queried_native_revision"]==49,"actual release108/frame107 separately matches native49")
    need(binding["date_raw"]==ct["date_raw"]==fr["date_raw"]==53144712 and binding["episode_run_id"]is None and binding["active_event_present"]is False and binding["incoming_interaction_present"]is False and fr["active_event"]is None and fr["pending_character_interaction"]is None and fr["paused"]is True,"actual fifth frame no event/incoming/episode, date paused")
    need(ct["game_pid"]==13436 and ct["connection_generation"]==1 and ct["player_character_id"]==31254 and ct["recipient_id"]==65866 and ct["interaction_key"]==identity["interaction_key"]and all(ct[k]is True for k in ["shown","can_send","ready_to_initiate","actor_alive","recipient_alive","source_code_pins_verified","actor_binding_verified","recipient_binding_verified","owner_thread_verified","tls_verified","frame_verified"]),"actual fifth fresh109 positive full IDs/native ready gates")
    need(ct["effective_roles"]=={"actor_id":31254,"recipient_id":65866,"secondary_actor_id":None,"secondary_recipient_id":None,"intermediary_id":None,"sixth_role_id":31254},"actual fifth six native roles")
    need(all(x["session_id"]==new["host_provenance"]["session_id"]and x["profile_sha256"]==new["host_provenance"]["profile_sha256"]and x["pipe_name"]==new["host_provenance"]["pipe_name"]for x in [fresh,send,context84,frame82]),"fifth raw SDK profile/session/pipe exact")
    need(released<datetime.fromisoformat(fresh["recorded_at_utc"])<datetime.fromisoformat(send["recorded_at_utc"]),"fourth release then newfresh then fifth send")
    raw=newpath.with_suffix(".packet.bin").read_bytes()
    need(ref(newpath.with_suffix(".packet.bin"))["sha256"]=="38266364358e58c0bcf95ba042649b42971f29bddfdcb7180f124d6e50116369"and len(raw)==363 and struct.unpack("<I",raw[:4])[0]==359,"fifth actual packet hash/u32length")
    packet=json.loads(raw[4:])
    expected={"type":"execute_step","protocol_version":1,"request_id":new["request_id"],"step":"initiate-character-interaction-ordinary-v1","expected_revision":49,"interaction_key":identity["interaction_key"],"recipient_id":65866,"expected_player_character_id":31254,"expected_game_pid":13436,"expected_connection_generation":1}
    need(packet==expected and len(packet)==10 and json.dumps(packet,separators=(",",":")).encode()==raw[4:],"fifth compact closed10 packet exact expectednative49")
    native=data(newpath.with_suffix(".native-result.json"),"57c5fb39376355a73c1ef907b7da8d6149fe949686e7aae9dc1d541b9906d405")
    ni=native["result"]["character_interaction_ordinary_initiation"]
    need(native["request_id"]==new["request_id"]and native["ok"]is True and ni==send["result"]["character_interaction_ordinary_initiation"]and ni["status"]=="pending"and ni["verification_pending"]is True and ni["business_postcondition_verified"]is False and ni["postcondition_verified"]is False,"fifth actual native/SDK pending ACK only")
    pending=data(newpath.with_suffix(".receipt.json"),"fbb289aceca106534a23a635d5ddf137dd1257ba53539a3d679b4f7814eccc5a")
    need(pending["request_id"]==new["request_id"]and pending["result"]==send["result"]and pending["business_postcondition_verified"]is False and send["business_effects_verified"]is False and send["full_product_acceptance_credit"]is False,"fifth host/SDK receipt business credit false")
    need(send["result"]["after_revision"]==50 and send["result"]["after_native_revision"]==49 and send["snapshot"]["revision"]==51 and send["snapshot"]["native_revision"]==50 and send["snapshot"]["active_event"]["instance_id"]==69,"driver original50/49 retained apart from wrapper51/50 active69")

    # Reuse the prior sealed fourth-opening report; no old payload scan or parser.
    savedroot=BASE/"r10-actual-fourth-open-join-readback-20261005-001"
    need(ref(savedroot/"INDEX.json")["sha256"]=="3c0811d784761325f41e45b327dd3bc949dd95b95e04075a9e6f6e60deff831f","prior saved9-to10 report INDEX frozen reference")
    savedreport=data(savedroot/"REPORT.json","f9b9f8513afe6803dbb197b0fde4bd8d5121dde409995e6093b036dc1c4580da")
    need(savedreport["before_save"]==detail["before_save"]and savedreport["after_save"]==detail["after_save"]and savedreport["all_binding_and_protection_checks"]["actual_nonce9_to10"]is True and savedreport["all_binding_and_protection_checks"]["actual_serial9_to10"]is True and savedreport["all_binding_and_protection_checks"]["actual_wallet_history_unchanged"]is True and savedreport["final_JOIN_credit"]is False,"prior actual saved82-to88 nonce9-to10 and wallet/history scope reused")
    need(send["snapshot"]["revision"]==51 and send["snapshot"]["native_revision"]==50 and send["snapshot"]["snapshot_id"]=="native:50"and send["snapshot"]["active_event"]["instance_id"]==69,"new fifth SDK110 wrapper51/native50/event69; no savednonce claim")
    for key in ["played_character_gold","played_character_piety","played_character_prestige"]:
        need(send["snapshot"][key]==fr[key],"new fifth dispatch wallet equals freshbefore "+key)
    # Only hashes of earlier actual lineage, claims and permits are checked.
    prior=BASE/"r10-actual-third-consumption-release-lineage-independent-review-20261005-001"
    need(ref(prior/"REPORT.json")["sha256"]=="ba88adf7ffbd79800576d391bc6442dd43d222c279374c644c9195afd5610f63"and ref(prior/"INDEX.json")["sha256"]=="dca4616739c4ffb97d6b021a6f4d2da71eafcc75bf6986f37575f348170f9d0b","earlier independent chain reused immutable refs; no cases repeated")
    for ordinal,expectedsha in [(0,"3fae018f1468983c59bb0cf6a8d32704cb6f791d6b25cae69451a82960b495ce"),(1,"7c2d0d36486fc2ec6c0d44fb24319affdce818feb3edb59d6878921e3d00c021"),(2,"1b2becdcfc4423afaa2a3e5ab8c550cd929425d1034abc23af2fdd0f4cd640c7"),(3,"ef93faeb5bcaef43a53fa35e98a80d37d675f0f4f4a80e080aea004b17474c03")]:
        p=CLAIM_DIR/(stable+f".{ordinal:08d}.claim.json")
        need(ref(p)["sha256"]==expectedsha,"immutable original ordinal"+str(ordinal)+" exact priorSHA")
    for ordinal,pin,consumepin in [(0,"6c7fd772f928041d1d616b77e9d5c00d27441ef6e52e1f030c14fe5b60b77c84","35287deac29f81d36d3d6978ba16253bac4ae954a4beba9ebd5852f179cea0ea"),(1,"61ee8cb86f971acae5f1ecd46f3410e6181389deb42979f1f4e030abec38ed72","d2b863b79cfeb69c713208aaf525a33b3db781b4013d4fdb32db7cd266a4e6c5"),(2,"3807abad2ec04820a677612dacc7b1b914222f30473320414fd90e1c1e554d59","2f6a17134f49fd9b0120693f355a72d619d0b217162d5c3e5f8495c2c97e3a0d")]:
        p=CLAIM_DIR/(stable+f".{ordinal:08d}.claim.release.json")
        need(ref(p)["sha256"]==pin and ref(p.with_suffix(".consumed.json"))["sha256"]==consumepin,"prior ordinal"+str(ordinal)+" permit and consumed original SHA preserved")
    report={"schema":"lyd.r10.actual-fourth-release-ordinal4-independent-review.v1",
        "status":"ACTUAL_FOURTH_EMIT_RELEASE_PERMIT_CONSUMED_ORDINAL4_LINEAGE_MATCH",
        "recorded_utc":datetime.now(timezone.utc).isoformat(),"checks_count":len(checks),"checks":checks,
        "actual_ROOT_fourth_emit":True,"actual_ROOT_fourth_release":True,"actual_fourth_permit_consumed":True,
        "released_request_consumption":{"claim_ordinal":3,"request_id":old["request_id"],"save_pair":"82-to88","serial_nonce_delta":[9,10],"wallet_delta":["0","0","0"],"completed_history_unchanged":True},
        "new_fifth_request":{"claim_ordinal":4,"request_id":new["request_id"],"native_status":"pending","driver_after":[50,49],"wrapper_snapshot":[51,50],"active_event_instance":69},
        "new_fifth_saved_serial_nonce":None,"new_fifth_opening_saved_AST_not_consumed_by_this_review":True,
        "six_action_identity":identity,"new_binding":binding,"new_parent_lineage":lineage,
        "actual_native_packet":packet,
        "immutable_original_ordinal0_1_2_3_preserved":True,"all_prior_permit_consumption_records_preserved":True,
        "ROOT_release_truth_separate_from_emission_historical_flags":True,
        "new_final_JOIN_credit":False,"full_cycle_credit":False,"ACK_business_credit":False,"permit_business_credit":False,
        "old_whole_payload_revalidation":False,"earlier_cases_tests_or_source_functions_rerun":False,"save_AST_reparsed":False,
        "reviewer_operations":{"bind":0,"emit":0,"registry_write":0,"host_release":0,"game":0,"native":0,"MCP":0,"pipe":0,"Client":0,"bus":0,"Git":0,"main":0,"save_AST_parse":0},
        "references":list(references.values())}
    (OUT/"REPORT.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (OUT/Path(__file__).name).write_bytes(Path(__file__).read_bytes())
    own={"schema":"lyd.external-evidence-index.v1","files":[{"path":p.name,"bytes":len(p.read_bytes()),"sha256":digest(p.read_bytes())}for p in sorted(OUT.iterdir())if p.is_file()]}
    (OUT/"INDEX.json").write_text(json.dumps(own,indent=2)+"\n",encoding="utf-8")
    for p in OUT.iterdir():
        if p.is_file():os.chmod(p,0o444)
    print(json.dumps({"status":report["status"],"checks_count":len(checks),"REPORT":ref(OUT/"REPORT.json"),"INDEX":ref(OUT/"INDEX.json")},ensure_ascii=True))
except Exception as error:
    (OUT/"FAILURE.json").write_text(json.dumps({"status":"READONLY_REVIEW_REJECTED","reason":str(error),"matched_checks":checks,"live_calls":0},indent=2)+"\n",encoding="utf-8")
    raise
