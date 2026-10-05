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
OUT = BASE / "r10-actual-third-consumption-release-lineage-independent-review-20261005-001"
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
    proof=BASE/"r10-third-proposal-emitted-evidence-20261005-002"
    index=verify_index(proof,"5b15917dcc4b6122ad2f025b2f252314887b5f6f26298ece41ea628e64ef23b6")
    need(len(index["files"])==5,"actual third emit exact5 payloads")
    manifest=data(proof/"CONSUMPTION-MANIFEST.json","7fa16321b5896ad4fb1f6b978787ace33f3966de90e2028d39058d77c0316ae7")
    facts=data(proof/"INDEPENDENT-FACTS.json","b44d89548fcac3a014c059de5f827fe193751ee27916f7b28a4941f011eee91d")
    detail=data(proof/"PRODUCT-DETAIL.json","47e5ecd520128030189f063c7644efc7fc2a3fad1016c0b2a909a76085d85789")
    emit_request=data(proof/"EMISSION-REQUEST.raw.json","74d98669a3e8c03b33145c9d008b9ca38ba616b9ce7b23b066c2f05fa87f3de3")
    need(emit_request==data(BASE/"r10-third-proposal-proof-inputs-20261005-002/EMIT-REQUEST.actual.json"),"third actual emission request exact captured author002")
    closed(facts,["schema","claim_request_id","action_identity","packet_sha256","native_result_sha256","unknown_sha256","before_artifact_sha256","after_artifact_sha256","consumption"],"third emitted closed facts")
    oldpath=Path(emit_request["claim"]["path"])
    old=data(oldpath,"1b2becdcfc4423afaa2a3e5ab8c550cd929425d1034abc23af2fdd0f4cd640c7")
    need(old["claim_ordinal"]==2 and old["status"]=="claimed_result_unknown_no_retry"and old["action_identity"]==identity,"ordinal2 immutable UNKNOWN parent preserved")
    need(facts["schema"]=="ck3-ordinary-interaction-independent-consumption-v1"and facts["claim_request_id"]==manifest["claim_request_id"]==old["request_id"]=="ordinary-interaction-909f50b85bf448b9b453a0121efc3835"and facts["action_identity"]==manifest["action_identity"]==identity,"actual third proof exactly old909f ordinal2 sixidentity")
    expected_consumption={"kind":"save_round_delta","field_name":"lyd_c2_callback_nonce","before_value":8,"after_value":9,"actor_id":31254,"recipient_id":65866,"interaction_key":identity["interaction_key"]}
    need(facts["consumption"]==expected_consumption,"third consumption nonce8-to9 only")
    for key,field in [("packet","packet_sha256"),("native_result","native_result_sha256"),("before_artifact","before_artifact_sha256"),("after_artifact","after_artifact_sha256")]:
        need(read_ref(manifest[key],"third manifest "+key)["sha256"]==facts[field],"actual third facts exact "+key)
    need(manifest["unknown"]is None and facts["unknown_sha256"]is None,"third uses genuine native pending receipt; no fake ACK")
    need(manifest["independent_report"]["sha256"]==references[str(proof/"INDEPENDENT-FACTS.json")]["sha256"],"third manifest exact independent facts")
    before=data(manifest["before_artifact"]["path"]);after=data(manifest["after_artifact"]["path"]);c=detail["conditions"]
    for obs in [before,after]:closed(obs["save"],["path","sha256","bytes"],"third saved exact3 ref")
    need(type(before["save"]["bytes"])is int and type(after["save"]["bytes"])is int and before["save"]["bytes"]==91533017 and after["save"]["bytes"]==91536994 and detail["before_save"]==before["save"]and detail["after_save"]==after["save"],"third actual original saved63-to68 exact bytes; no82 reserve substitution")
    need(c["serial_nonce_before"]==[8,8]and c["serial_nonce_after"]==[9,9]and c["wallet_delta"]==["0","0","0"]and c["completed_history_unchanged"]is True,"actual emitted third8-to9 wallet0/historysame")
    need(c["source_faith"]=="106"and c["target_faith"]=="104"and c["moving_rite"]=="169"and c["target_main"]=="159"and c["target_rep"]=="65866"and c["actual_source_roles"]==["31254","65865"]and c["actual_target_roles"]==["65866"]and c["actual_human_roles"]==["31254"],"third actual positive dynamic graph/roles")
    need(c["consumption_mode"]=="PROPOSAL_OPENED"and c["join_business_acceptance_credit"]is False and c["NPC_vote_choice_required"]is False and detail["native_ACK_credit"]is False and detail["actual_release"]is False,"third emission proposal-only historical flags preserved")
    need(detail["source_revision"]=="d0f8fa3b9d444828759443aa018bfd7ad31b398d"and detail["parser_sha256"]=="6c1ba1006cd0dd5055c11115701b60a74562b0f23d91b756a3d9322e7d055cb7"and detail["reader_version"]=="lyd-join-save-consumption-verifier-v2","third actual source/parser frozen")
    er,es,ea=invocation(RUN/"root-third-consumption-emit-invocation-001","0a22911fdb9c35a9d00e3aa282bb0199042933feb52ccbb6f872ffdf0cf28ea3")
    need(es["index_sha256"]==references[str(proof/"INDEX.json")]["sha256"]and es["manifest_sha256"]==references[str(proof/"CONSUMPTION-MANIFEST.json")]["sha256"]and es["actual_host_release"]is False,"actual third emit stdout exact output proof and historical no-release flag")

    h=RUN/"root-third-consumption-host-request-001"
    request=data(h/"RELEASE-REQUEST.actual.json","3af4ef3c26b1c6e21c251b478b6fb4ba64f2925fb20a4bdb8e80894636990b36")
    closed(request,["schema","host_module","claim","consumption_manifest","registry","verifier_id","operator_id","next_intent_id"],"third actual closed release request")
    need(request["claim"]==emit_request["claim"]and request["consumption_manifest"]=={"path":str(proof/"CONSUMPTION-MANIFEST.json"),"sha256":references[str(proof/"CONSUMPTION-MANIFEST.json")]["sha256"]},"third release exact parent and proof manifest")
    need(read_ref(request["host_module"],"third actual host")["sha256"]=="f567bff41d03b6c59d195df8ff62ecab1a523962de3217d397c5264d1ed2d89b","actual host unchanged f567")
    registry=data(request["registry"]["path"],"582d3e13e3b78b043874e7db9eae7b77a7061abe3b43d6efcc3684a8600308ae")
    v=registry["verifiers"][request["verifier_id"]]
    need(registry["schema"]=="ck3-ordinary-interaction-root-verifier-registry-v1"and v["entrypoint"]=="verifier.py:verify_consumption"and v["bundle_index"]==emit_request["bound_verifier_index"],"third ROOT registry exact actual bound third001")
    need(read_ref(v["bundle_index"],"third actual bound INDEX")["sha256"]=="05169d085060443ac695c9aedc91da3d2ecebe013e7352365ba1f3d22230e3d3","third existing actual bound INDEX exact")
    rr,rs,ra=invocation(RUN/"root-third-consumption-release-invocation-001","2ce434c55b04d62f3f8e02f85b3de7fa1fd73a29c16e556e1cc19ebce76c1d6e")
    need(rs["game_command_sent"]is False and rs["business_acceptance_credit"]is False,"third host release no game command/business credit")
    permitpath=oldpath.with_suffix(".release.json")
    permit=data(permitpath,"3807abad2ec04820a677612dacc7b1b914222f30473320414fd90e1c1e554d59")
    closed(permit,["schema","claim_path","claim_sha256","claim_request_id","action_identity","old_connection_generation","manifest","registry","verifier_id","verifier_bundle","operator_id","next_intent_id","released_at_utc","scope","business_acceptance_credit"],"third permit actual closed schema")
    need(permit["schema"]=="ck3-ordinary-interaction-next-intent-permit-v1"and permit["claim_path"]==str(oldpath)and permit["claim_sha256"]==references[str(oldpath)]["sha256"]and permit["claim_request_id"]==old["request_id"]and permit["action_identity"]==identity,"third permit exact immutable ordinal2 parent/identity")
    need(permit["manifest"]==request["consumption_manifest"]and permit["registry"]==request["registry"]and permit["verifier_bundle"]==v["bundle_index"]and all(permit[k]==request[k]for k in ["verifier_id","operator_id","next_intent_id"]),"third permit exact proof/registry/bundle/ROOT intent")
    need(permit["next_intent_id"]=="r10-proposal-004-after-consumed-909f-20261005"and permit["scope"]=="operator_verified_consumption_for_one_new_intent"and permit["business_acceptance_credit"]is False and rs["permit_path"]==str(permitpath)and rs["permit_sha256"]==references[str(permitpath)]["sha256"],"third permit single fourth intent/no JOIN credit; actual stdout exact")
    released=datetime.fromisoformat(permit["released_at_utc"])
    need(datetime.fromisoformat(rr["started_utc"])<=released<=datetime.fromisoformat(rr["completed_utc"]),"third permit time inside ROOT release invocation")

    sd=RUN/"mcp-client-evidence-002"
    fresh=sdk(sd/"0086-r10-0087-fourth-fresh-query.sdk-result.json","87e2fdfb02e76bea3755285e6cf4bfcd7ec0588d5652e92bf83e548949e8de20")
    send=sdk(sd/"0087-r10-0088-fourth-proposal.sdk-result.json","b4233638bc7ad06b7d68fa4a70f8a217229af5f0e7a6334b560245b7f09a0d9b")
    save88=sdk(sd/"0088-r10-0089-fourth-open-save.sdk-result.json","4d658405af1e757a445458bb68163204abc9e87ee5887bfb4459fb75408e23b9")
    context84=sdk(c["current_release_context_sdk"]["path"],c["current_release_context_sdk"]["sha256"])
    frame82=sdk(c["current_release_context_frame_sdk"]["path"],c["current_release_context_frame_sdk"]["sha256"])
    newpath=Path(send["result"]["action_claim_path"])
    need(newpath.parent.resolve()==CLAIM_DIR.resolve(),"actual ordinal3 SDK87 discovered path contained")
    new=data(newpath,"ef93faeb5bcaef43a53fa35e98a80d37d675f0f4f4a80e080aea004b17474c03")
    closed(new["action_identity"],identity.keys(),"ordinal3 exact sixidentity keys")
    need(new["action_identity"]==identity and new["host_provenance"]==old["host_provenance"]and new["claim_ordinal"]==old["claim_ordinal"]+1==3 and new["status"]=="claimed_result_unknown_no_retry","ordinal3 same PID/create/profile/session/identity; ordinal2 immutable UNKNOWN preserved")
    need(new["request_id"]==send["result"]["action_request_id"]=="ordinary-interaction-76a5607e59804b76ad5dbe3f98fc126c"and new["request_id"]!=old["request_id"],"actual ordinal3 distinct fourth UUID")
    consumedpath=permitpath.with_suffix(".consumed.json")
    consumed=data(consumedpath,"2f6a17134f49fd9b0120693f355a72d619d0b217162d5c3e5f8495c2c97e3a0d")
    need(consumed["schema"]=="ck3-ordinary-interaction-permit-consumption-v1"and consumed["permit_path"]==str(permitpath)and consumed["permit_sha256"]==references[str(permitpath)]["sha256"]and consumed["new_request_id"]==new["request_id"]and consumed["next_intent_id"]==permit["next_intent_id"],"third permit genuinely consumed once for actual76a5 ordinal3")
    need(consumed["new_binding"]==new["binding"]and consumed["action_identity"]==identity and consumed["business_acceptance_credit"]is False and consumed["old_connection_generation"]==consumed["new_connection_generation"]==permit["old_connection_generation"]==1,"third consumption exact binding/sixidentity/gen1/no business credit")
    lineage={"permit_path":str(permitpath),"permit_sha256":references[str(permitpath)]["sha256"],"next_intent_id":permit["next_intent_id"],"parent_claim_path":str(oldpath),"parent_claim_sha256":references[str(oldpath)]["sha256"]}
    need(new["new_intent_lineage"]==lineage and oldpath.name==stable+".00000002.claim.json"and newpath.name==stable+".00000003.claim.json","actual ordinal3 exact immutable ordinal2/permit parent chain")
    binding=new["binding"];fr=frame82["snapshot_after"];qr=fresh["result"];ct=qr["character_interaction_ordinary_context"]
    need(qr["queried_revision"]==binding["revision"]==fr["revision"]==39 and qr["queried_native_revision"]==binding["native_revision"]==fr["native_revision"]==38 and qr["queried_snapshot_id"]==binding["snapshot_id"]==fr["snapshot_id"]=="native:38","actual fresh86/frame82 public39/native38")
    need(c["actual_release_context"]=={"revision":39,"native_revision":38,"snapshot_id":"native:38","date_raw":53144712}and context84["result"]["queried_native_revision"]==38,"actual release84/frame82 separately matches native38")
    need(binding["date_raw"]==ct["date_raw"]==fr["date_raw"]==53144712 and binding["episode_run_id"]is None and binding["active_event_present"]is False and binding["incoming_interaction_present"]is False and fr["active_event"]is None and fr["pending_character_interaction"]is None and fr["paused"]is True,"actual fourth frame no event/incoming/episode, date paused")
    need(ct["game_pid"]==13436 and ct["connection_generation"]==1 and ct["player_character_id"]==31254 and ct["recipient_id"]==65866 and ct["interaction_key"]==identity["interaction_key"]and all(ct[k]is True for k in ["shown","can_send","ready_to_initiate","actor_alive","recipient_alive","source_code_pins_verified","actor_binding_verified","recipient_binding_verified","owner_thread_verified","tls_verified","frame_verified"]),"actual fourth fresh86 positive full IDs/native ready gates")
    need(ct["effective_roles"]=={"actor_id":31254,"recipient_id":65866,"secondary_actor_id":None,"secondary_recipient_id":None,"intermediary_id":None,"sixth_role_id":31254},"actual fourth six native roles")
    need(all(x["session_id"]==new["host_provenance"]["session_id"]and x["profile_sha256"]==new["host_provenance"]["profile_sha256"]and x["pipe_name"]==new["host_provenance"]["pipe_name"]for x in [fresh,send,save88,context84,frame82]),"fourth raw SDK profile/session/pipe exact")
    need(released<datetime.fromisoformat(fresh["recorded_at_utc"])<datetime.fromisoformat(send["recorded_at_utc"])<datetime.fromisoformat(save88["recorded_at_utc"]),"third release then newfresh then fourth send then saved observation")
    raw=newpath.with_suffix(".packet.bin").read_bytes()
    need(ref(newpath.with_suffix(".packet.bin"))["sha256"]=="857a6dd3b017862ba4bba4f8a3bd600209a5a1e1a443b14ae2cf126bef86f589"and len(raw)==363 and struct.unpack("<I",raw[:4])[0]==359,"fourth actual packet hash/u32length")
    packet=json.loads(raw[4:])
    expected={"type":"execute_step","protocol_version":1,"request_id":new["request_id"],"step":"initiate-character-interaction-ordinary-v1","expected_revision":38,"interaction_key":identity["interaction_key"],"recipient_id":65866,"expected_player_character_id":31254,"expected_game_pid":13436,"expected_connection_generation":1}
    need(packet==expected and len(packet)==10 and json.dumps(packet,separators=(",",":")).encode()==raw[4:],"fourth compact closed10 packet exact expectednative38")
    native=data(newpath.with_suffix(".native-result.json"),"9def02326ab19e51602017c935c48a85ed1d2b13024e3151326f413e5bc9ae61")
    ni=native["result"]["character_interaction_ordinary_initiation"]
    need(native["request_id"]==new["request_id"]and native["ok"]is True and ni==send["result"]["character_interaction_ordinary_initiation"]and ni["status"]=="pending"and ni["verification_pending"]is True and ni["business_postcondition_verified"]is False and ni["postcondition_verified"]is False,"fourth actual native/SDK pending ACK only")
    pending=data(newpath.with_suffix(".receipt.json"),"95a06f8045a8ada7e1a09c4eb91c01ba1bfbb0c1b4e03a7fb00d8ca077ce26fb")
    need(pending["request_id"]==new["request_id"]and pending["result"]==send["result"]and pending["business_postcondition_verified"]is False and send["business_effects_verified"]is False and send["full_product_acceptance_credit"]is False,"fourth host/SDK receipt business credit false")
    need(send["result"]["after_revision"]==39 and send["result"]["after_native_revision"]==38 and send["snapshot"]["revision"]==40 and send["snapshot"]["native_revision"]==39 and send["snapshot"]["active_event"]["instance_id"]==63,"driver original39/38 retained apart from wrapper40/39 active63")

    # Reuse third AST record refs only; no parser or former save reads.
    thirdroot=BASE/"r10-actual-third-open-join-readback-20261005-001"
    data(thirdroot/"INDEX.json","98dd1157870b267cf15ef2b28258e3066c335bfc96f91ccb41c9a32ba3d3f258")
    thirdreport=data(thirdroot/"REPORT.json","ad93e67929c20343d4496b35f583364cf51510abee1fe04bb971f286ac770de3")
    thirdfacts=data(thirdreport["typed_facts"]["path"],thirdreport["typed_facts"]["sha256"])
    need(thirdreport["before_save"]==detail["before_save"]and thirdreport["after_save"]==detail["after_save"]and thirdfacts["new_action"]["UUID"]==old["request_id"]and thirdfacts["new_action"]["ordinal"]==2,"reused third AST actual63-to68 old909f proof binding")
    for name in ["lyd_c2_callback_nonce","lyd_c2_serial"]:
        d=thirdfacts["actual_round_diff"][name]
        need(d["before"]["present"]is True and d["before"]["type"]=="value"and d["before"]["number"]=="8"and d["after"]["present"]is True and d["after"]["type"]=="value"and d["after"]["number"]=="9","third independent typed "+name+"8-to9")
    fourthroot=BASE/"r10-actual-fourth-open-join-readback-20261005-001"
    fourthidx=verify_index(fourthroot,"3c0811d784761325f41e45b327dd3bc949dd95b95e04075a9e6f6e60deff831f",True)
    fourthreport=data(fourthroot/"REPORT.json","f9b9f8513afe6803dbb197b0fde4bd8d5121dde409995e6093b036dc1c4580da")
    fourthfacts=data(fourthreport["typed_facts"]["path"],"86bb9296af72a4cee55e171d040302d33e308882e03251980ea50d493eb46daf")
    action=fourthfacts["new_action"]
    need(action["UUID"]==new["request_id"]and action["ordinal"]==3 and action["claim"]["sha256"]==references[str(newpath)]["sha256"]and action["six_identity"]==identity and action["parent_claim"]["sha256"]==references[str(oldpath)]["sha256"]and action["permit"]["sha256"]==references[str(permitpath)]["sha256"],"fourth sealed saved AST exact new76a5 ordinal3/parent2/permit binding")
    for name in ["lyd_c2_callback_nonce","lyd_c2_serial"]:
        d=fourthfacts["actual_round_diff"][name]
        need(d["before"]["present"]is True and d["before"]["type"]=="value"and d["before"]["number"]=="9"and d["after"]["present"]is True and d["after"]["type"]=="value"and d["after"]["number"]=="10","fourth opening typed "+name+"9-to10 kept separate")
    need(fourthreport["before_save"]["path"]!=detail["before_save"]["path"]and fourthreport["after_save"]["path"]!=detail["after_save"]["path"],"fourth saved82-to88 not substituted into third63-to68 consumption")
    checkpoint=save88["result"]["checkpoint"];snap=save88["snapshot_after"]
    need(checkpoint["status"]=="saved"and checkpoint["strategy"]=="native-autosave-command-v1"and checkpoint["sha256"]==fourthreport["after_save"]["sha256"]=="8615285b73caa1e34364e2a78a351a8f9c2f813d6587a8c7a926f4fe12b3df53"and checkpoint["size"]==fourthreport["after_save"]["bytes"]==91538147,"actual fourth save88 SDK exact saved hash/size")
    need(snap["revision"]==41 and snap["native_revision"]==40 and snap["date_raw"]==53144712 and snap["active_event"]["instance_id"]==63 and snap["played_character"]["character_id"]==31254,"actual fourth saved frame41/native40/event63")
    need(thirdfacts["actual_wallet_Decimal_delta"]==fourthfacts["actual_wallet_Decimal_delta"]=={"gold":"0","piety":"0","prestige":"0"}and fourthfacts["actual_history"]["lyd_c2_completed_joins"]["number"]=="1"and fourthfacts["actual_history"]["lyd_c2_completed_detaches"]["number"]=="2","both nonce facts wallet0/historystillJOIN1DETACH2")
    need(thirdreport["final_JOIN_credit"]is False and fourthreport["final_JOIN_credit"]is False and fourthfacts["final_JOIN_credit"]is False and all(v is True for v in fourthreport["all_binding_and_protection_checks"].values()),"both proposal scopes no final JOIN credit; original fourth scope preserved")
    # Only hashes of earlier actual lineage, claims and permits are checked.
    prior=BASE/"r10-actual-second-consumption-release-lineage-independent-review-20261005-001"
    need(ref(prior/"REPORT.json")["sha256"]=="b28cac6b015c49a4066c4d4e70fbe9f1977ebc2d66d3c5118252ec5980769c20"and ref(prior/"INDEX.json")["sha256"]=="5768eaea896731cb879d4d604c6f79a184ed756aceb93c8745d38fec73beea3b","earlier independent chain reused immutable refs; no cases repeated")
    for ordinal,expectedsha in [(0,"3fae018f1468983c59bb0cf6a8d32704cb6f791d6b25cae69451a82960b495ce"),(1,"7c2d0d36486fc2ec6c0d44fb24319affdce818feb3edb59d6878921e3d00c021"),(2,"1b2becdcfc4423afaa2a3e5ab8c550cd929425d1034abc23af2fdd0f4cd640c7")]:
        p=CLAIM_DIR/(stable+f".{ordinal:08d}.claim.json")
        need(ref(p)["sha256"]==expectedsha,"immutable original ordinal"+str(ordinal)+" exact priorSHA")
    for ordinal,pin,consumepin in [(0,"6c7fd772f928041d1d616b77e9d5c00d27441ef6e52e1f030c14fe5b60b77c84","35287deac29f81d36d3d6978ba16253bac4ae954a4beba9ebd5852f179cea0ea"),(1,"61ee8cb86f971acae5f1ecd46f3410e6181389deb42979f1f4e030abec38ed72","d2b863b79cfeb69c713208aaf525a33b3db781b4013d4fdb32db7cd266a4e6c5")]:
        p=CLAIM_DIR/(stable+f".{ordinal:08d}.claim.release.json")
        need(ref(p)["sha256"]==pin and ref(p.with_suffix(".consumed.json"))["sha256"]==consumepin,"prior ordinal"+str(ordinal)+" permit and consumed original SHA preserved")
    report={"schema":"lyd.r10.actual-third-release-ordinal3-and-fourth-opening-independent-review.v1",
        "status":"ACTUAL_THIRD_EMIT_RELEASE_PERMIT_CONSUMED_ORDINAL3_AND_FOURTH_OPEN_MATCH",
        "recorded_utc":datetime.now(timezone.utc).isoformat(),"checks_count":len(checks),"checks":checks,
        "actual_ROOT_third_emit":True,"actual_ROOT_third_release":True,"actual_third_permit_consumed":True,
        "released_request_consumption":{"claim_ordinal":2,"request_id":old["request_id"],"save_pair":"63-to68","serial_nonce_delta":[8,9],"wallet_delta":["0","0","0"],"completed_history_unchanged":True},
        "new_fourth_opening":{"claim_ordinal":3,"request_id":new["request_id"],"save_pair":"82-to88","serial_nonce_delta":[9,10],"wallet_delta":["0","0","0"],"completed_joins":1,"completed_detaches":2,"final_JOIN_credit":False},
        "six_action_identity":identity,"new_binding":binding,"new_parent_lineage":lineage,
        "actual_newsend_status":"pending","actual_native_packet":packet,
        "immutable_original_ordinal0_1_2_preserved":True,"all_prior_permit_consumption_records_preserved":True,
        "ROOT_release_truth_separate_from_emission_historical_flags":True,
        "new_final_JOIN_credit":False,"full_cycle_credit":False,"ACK_business_credit":False,"permit_business_credit":False,
        "fourth_NPC_YES_credit":"Not asserted by this review; original saved vote identity omission remains as recorded by sealed AST.",
        "earlier_cases_tests_or_source_functions_rerun":False,"save_AST_reparsed":False,
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

