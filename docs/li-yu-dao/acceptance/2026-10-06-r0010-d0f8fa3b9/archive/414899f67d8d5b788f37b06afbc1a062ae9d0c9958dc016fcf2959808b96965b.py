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
OUT = BASE / "r10-actual-second-consumption-release-lineage-independent-review-20261005-001"
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

if OUT.exists():
    raise FileExistsError("append-only review output exists")
OUT.mkdir()
try:
    proof=BASE/"r10-second-proposal-emitted-evidence-20261005-002"
    proof_index=data(proof/"INDEX.json","30f46194547d574963fdb59494ea2b675f92bbc7368c8f387b464dac9c4b0049")
    need(proof_index["schema"]=="lyd.first-join.emitted-proof-index.v1","new emitted002 proof INDEX actual schema")
    seen=set()
    for row in proof_index["files"]:
        closed(row,["path","bytes","sha256"],"new emitted indexed row")
        target=(proof/row["path"]).resolve()
        need(proof.resolve()in target.parents and row["path"]not in seen,"new emitted row contained/unique")
        seen.add(row["path"]);actual=ref(target)
        need(actual["bytes"]==row["bytes"]and actual["sha256"]==row["sha256"],"actual new emitted payload "+row["path"])
    actual_set={str(p.relative_to(proof)).replace("\\","/")for p in proof.rglob("*")if p.is_file()and p.name!="INDEX.json"}
    need(actual_set==seen and len(seen)==5,"actual emitted002 exact5 payload coverage")
    manifest=data(proof/"CONSUMPTION-MANIFEST.json","d5ba71ebeecac14a5bc8e3d75ee65345a21afa90f9e2e0a8af22d08cd74d8b31")
    facts=data(proof/"INDEPENDENT-FACTS.json","18e7d81eb3addb0163a8178ec1628f95dd91ecab001e22aadcc0924e69c5e7df")
    detail=data(proof/"PRODUCT-DETAIL.json","92136f13ff615fb52851a680acda0f1b64ac3ec9872e2ea25349ab52e8d6f33e")
    emission_request=data(proof/"EMISSION-REQUEST.raw.json","c50218009cf766e940f3ae0eda4d23aa4e1541bb6de406c73d521adefe28b040")
    emission_status=data(proof/"EMISSION-STATUS.json")
    need(emission_request==data(BASE/"r10-second-proposal-proof-inputs-20261005-002/EMIT-REQUEST.actual.json"),"actual emit raw request exact author002 input")
    closed(facts,["schema","claim_request_id","action_identity","packet_sha256","native_result_sha256","unknown_sha256","before_artifact_sha256","after_artifact_sha256","consumption"],"actual emitted closed generic facts")
    expected_identity={"game_pid":13436,"actor_id":31254,"process_create_time":1791196395.7422996,
                      "interaction_key":"lyd_c2_propose_join_interaction","recipient_id":65866,"action":"initiate_ordinary"}
    old_path=Path(emission_request["claim"]["path"])
    old=data(old_path,"7c2d0d36486fc2ec6c0d44fb24319affdce818feb3edb59d6878921e3d00c021")
    need(old["claim_ordinal"]==1 and old["status"]=="claimed_result_unknown_no_retry","ordinal1 immutable old UNKNOWN claim unchanged")
    need(facts["schema"]=="ck3-ordinary-interaction-independent-consumption-v1"and facts["claim_request_id"]==manifest["claim_request_id"]==old["request_id"]=="ordinary-interaction-a50373f260354f6f83c8052eaf837c7f"and facts["action_identity"]==manifest["action_identity"]==old["action_identity"]==expected_identity,"new emit facts exact ordinal1 UUID/full sixidentity")
    need(facts["consumption"]=={"kind":"save_round_delta","field_name":"lyd_c2_callback_nonce","before_value":7,"after_value":8,"actor_id":31254,"recipient_id":65866,"interaction_key":"lyd_c2_propose_join_interaction"},"actual emitted ordinal1 consumption nonce7-to8 only")
    for key,hash_key in [("packet","packet_sha256"),("native_result","native_result_sha256"),("before_artifact","before_artifact_sha256"),("after_artifact","after_artifact_sha256")]:
        actual=read_ref(manifest[key],"emitted "+key)
        need(actual["sha256"]==facts[hash_key],"generic facts exact raw "+key)
    need(manifest["unknown"]is None and facts["unknown_sha256"]is None,"existing actual native pending receipt; no invented UNKNOWN ACK")
    need(manifest["independent_report"]["sha256"]==references[str(proof/"INDEPENDENT-FACTS.json")]["sha256"],"manifest exact frozen independent facts")
    for suffix,expected in [(".packet.bin","909aaa95148773b05c67649cf53e1c98debd4bbcef817d9e65704d0335350ee7"),
                            (".native-result.json","754e1da18c03e60d44981313375f1eef1c0516e63d9c19e89047582c492a78c0"),
                            (".receipt.json","939bbcb4175e98351e80d18e96c7c3d5237fbca14c3fa90fdc94ad539e3100af")]:
        need(ref(old_path.with_suffix(suffix))["sha256"]==expected,"preserved ordinal1 "+suffix)
    before=data(manifest["before_artifact"]["path"]);after=data(manifest["after_artifact"]["path"])
    closed(before["save"],["path","sha256","bytes"],"actual emitted BEFORE saved3ref")
    closed(after["save"],["path","sha256","bytes"],"actual emitted AFTER saved3ref")
    need(type(before["save"]["bytes"])is int and type(after["save"]["bytes"])is int and before["save"]["bytes"]==91531932 and after["save"]["bytes"]==91536022,"correct actual saved39/43 byte sizes")
    need(detail["before_save"]==before["save"]and detail["after_save"]==after["save"],"productdetail exact original39-to43 refs, not new63 reserve")
    c=detail["conditions"]
    need(c["serial_nonce_before"]==[7,7]and c["serial_nonce_after"]==[8,8]and c["wallet_delta"]==["0","0","0"]and c["completed_history_unchanged"]is True,"actual frozen consumption serial/nonce7-to8 wallet0 historysame")
    need(c["source_faith"]=="106"and c["target_faith"]=="104"and c["moving_rite"]=="169"and c["target_main"]=="159"and c["target_rep"]=="65866"and c["actual_source_roles"]==["31254","65865"]and c["actual_target_roles"]==["65866"]and c["actual_human_roles"]==["31254"],"actual positive dynamic graph and full role lists")
    need(c["consumption_mode"]=="PROPOSAL_OPENED"and c["join_business_acceptance_credit"]is False and c["NPC_vote_choice_required"]is False and detail["native_ACK_credit"]is False and detail["actual_release"]is False,"emission historical proposal-only/no JOIN/NPC-force/ACK/release credit")
    need(detail["source_revision"]=="d0f8fa3b9d444828759443aa018bfd7ad31b398d"and detail["parser_sha256"]=="6c1ba1006cd0dd5055c11115701b60a74562b0f23d91b756a3d9322e7d055cb7"and detail["reader_version"]=="lyd-join-save-consumption-verifier-v2","actual frozen source/parser/reader")
    need(emission_status["actual_host_release"]is False and emission_status["registry_enabled"]is False and emission_status["native_ACK_credit"]is False and emission_status["full_C2_cycle_credit"]is False,"emission-time flags unchanged; later actual release separately credited")

    emit_inv=RUN/"root-second-consumption-emit-invocation-001"
    emit_result=data(emit_inv/"RESULT.json","762c900e4c3b52829b5973106e1762b15fa65a6eb4b7f8de8a1ce0f9e7212718")
    emit_argv=data(emit_inv/"argv.json")
    argv_source=data(emit_result["argv_source"],emit_result["argv_source_sha256"])
    need(emit_result["exit_code"]==0 and emit_result["status"]=="INVOCATION_COMPLETED"and emit_argv==argv_source["argv"],"actual ROOT second emit exact argv and exit0")
    need(ref(emit_inv/"stdout.txt")["sha256"]==emit_result["stdout_sha256"]and ref(emit_inv/"stderr.txt")["sha256"]==emit_result["stderr_sha256"]and(emit_inv/"stderr.txt").read_bytes()==b"","actual ROOT second emit exact stdio")

    hostdir=RUN/"root-second-consumption-host-request-001";release_inv=RUN/"root-second-consumption-release-invocation-001"
    request=data(hostdir/"RELEASE-REQUEST.actual.json","e9527ffecc8a63e88ea038a06b45e3fed4bfda043b694854f7dc271ae9746592")
    closed(request,["schema","host_module","claim","consumption_manifest","registry","verifier_id","operator_id","next_intent_id"],"actual second closed release request")
    need(request["schema"]=="ck3-r9-root-ordinary-release-request-v1"and request["claim"]==emission_request["claim"],"actual second request exact old ordinal1 claim")
    need(read_ref(request["host_module"],"actual frozen host")["sha256"]=="f567bff41d03b6c59d195df8ff62ecab1a523962de3217d397c5264d1ed2d89b","actual source host f567 unchanged")
    need(request["consumption_manifest"]["path"]==str(proof/"CONSUMPTION-MANIFEST.json")and request["consumption_manifest"]["sha256"]==references[str(proof/"CONSUMPTION-MANIFEST.json")]["sha256"],"actual host request exact second emitted manifest")
    read_ref(request["registry"],"actual second ROOT registry")
    registry=data(request["registry"]["path"])
    need(registry["schema"]=="ck3-ordinary-interaction-root-verifier-registry-v1","actual second registry schema")
    row=registry["verifiers"][request["verifier_id"]]
    need(row["bundle_index"]==emission_request["bound_verifier_index"]and row["entrypoint"]=="verifier.py:verify_consumption","second registry uses existing actual bound001")
    need(read_ref(row["bundle_index"],"actual bound001 INDEX")["sha256"]=="8945dca159d69dbc8cbb5a6ff849ab4503c5487f2cb20278430b1d2e08090813","bound001 exact existing frozen INDEX")
    release_result=data(release_inv/"RESULT.json","9de88f485750b424f0ee41e8fc1a1b412f6a46e56ef96049b1e58c0aea252bf7")
    release_argv=data(release_inv/"argv.json");release_argv_source=data(hostdir/"release-argv.json","6098d74a7cb32e60e668de49bf317efd4ebe418f78a67f83eb43d34221e9f121")
    need(release_result["exit_code"]==0 and release_result["status"]=="INVOCATION_COMPLETED"and release_argv==release_argv_source["argv"]and release_result["argv_source_sha256"]==references[str(hostdir/"release-argv.json")]["sha256"],"actual ROOT second release exact argv/exit0")
    need(ref(release_inv/"stdout.txt")["sha256"]==release_result["stdout_sha256"]and ref(release_inv/"stderr.txt")["sha256"]==release_result["stderr_sha256"]and(release_inv/"stderr.txt").read_bytes()==b"","actual ROOT second release exact stdio")
    stdout=data(release_inv/"stdout.txt")
    need(stdout["game_command_sent"]is False and stdout["business_acceptance_credit"]is False,"actual release host sends no game command and no business credit")
    permit_path=old_path.with_suffix(".release.json")
    permit=data(permit_path,"61ee8cb86f971acae5f1ecd46f3410e6181389deb42979f1f4e030abec38ed72")
    need(permit["schema"]=="ck3-ordinary-interaction-next-intent-permit-v1"and permit["claim_path"]==str(old_path)and permit["claim_sha256"]==references[str(old_path)]["sha256"]and permit["claim_request_id"]==old["request_id"],"second actual permit immutable ordinal1 parent")
    need(permit["manifest"]==request["consumption_manifest"]and permit["registry"]==request["registry"]and permit["verifier_bundle"]==row["bundle_index"]and permit["action_identity"]==expected_identity,"actual second permit exact manifest/registry/bundle/sixidentity")
    need(all(permit[k]==request[k]for k in ["verifier_id","operator_id","next_intent_id"])and permit["next_intent_id"]=="r10-proposal-003-after-consumed-a503-20261005","actual second permit exact ROOT new third intention")
    need(stdout["permit_path"]==str(permit_path)and stdout["permit_sha256"]==references[str(permit_path)]["sha256"]and permit["scope"]=="operator_verified_consumption_for_one_new_intent"and permit["business_acceptance_credit"]is False,"second permit one new intent; stdout matches; no JOIN credit")
    released=datetime.fromisoformat(permit["released_at_utc"])
    need(datetime.fromisoformat(release_result["started_utc"])<=released<=datetime.fromisoformat(release_result["completed_utc"]),"second permit time inside actual ROOT invocation")

    sdkdir=RUN/"mcp-client-evidence-002"
    query65=sdk(sdkdir/"0065-r10-0066-third-fresh-ready-query.sdk-result.json","55d7158c6c4a23a29203df10be51a5a4751aa9912c1baf451f949783b3418c2f")
    send66=sdk(sdkdir/"0066-r10-0067-third-proposal.sdk-result.json","b70885f660b479a1666218604d1d37931a4038a16e10ac764bed697b4f7c79b1")
    snap67=sdk(sdkdir/"0067-r10-0068-third-post-dispatch-snapshot.sdk-result.json","f7194fca9435093c05ccf6a499e03a565f3ca167fec87c9772555731e835341f")
    current64=sdk(c["current_release_context_sdk"]["path"],c["current_release_context_sdk"]["sha256"])
    frame63=sdk(c["current_release_context_frame_sdk"]["path"],c["current_release_context_frame_sdk"]["sha256"])
    new_path=Path(send66["result"]["action_claim_path"])
    need(new_path.parent.resolve()==CLAIM_DIR.resolve(),"ordinal2 located from actual SDK66 contained path")
    new=data(new_path,"1b2becdcfc4423afaa2a3e5ab8c550cd929425d1034abc23af2fdd0f4cd640c7")
    need(new["claim_ordinal"]==2 and new["status"]=="claimed_result_unknown_no_retry"and new["request_id"]==send66["result"]["action_request_id"]=="ordinary-interaction-909f50b85bf448b9b453a0121efc3835"and new["request_id"]!=old["request_id"],"actual distinct ordinal2 new UUID; immutable UNKNOWN claim")
    closed(new["action_identity"],expected_identity.keys(),"actual ordinal2 sixidentity closed")
    need(new["action_identity"]==expected_identity and new["host_provenance"]==old["host_provenance"],"ordinal2 same sixidentity/PID/create/profile/session/guard; no epoch unlock")
    consumed_path=permit_path.with_suffix(".consumed.json")
    consumed=data(consumed_path,"d2b863b79cfeb69c713208aaf525a33b3db781b4013d4fdb32db7cd266a4e6c5")
    need(consumed["schema"]=="ck3-ordinary-interaction-permit-consumption-v1"and consumed["permit_path"]==str(permit_path)and consumed["permit_sha256"]==references[str(permit_path)]["sha256"],"actual second permit consumed exact")
    need(consumed["new_request_id"]==new["request_id"]and consumed["next_intent_id"]==permit["next_intent_id"]and consumed["action_identity"]==expected_identity and consumed["business_acceptance_credit"]is False,"consumed second permit for one actual909f intention without business credit")
    need(consumed["new_binding"]==new["binding"]and consumed["old_connection_generation"]==consumed["new_connection_generation"]==permit["old_connection_generation"]==old["binding"]["connection_generation"]==new["binding"]["connection_generation"]==1,"exact actual next binding and generation1; no reconnect bypass")
    expected_lineage={"permit_path":str(permit_path),"permit_sha256":references[str(permit_path)]["sha256"],"next_intent_id":permit["next_intent_id"],"parent_claim_path":str(old_path),"parent_claim_sha256":references[str(old_path)]["sha256"]}
    need(new["new_intent_lineage"]==expected_lineage,"actual ordinal2 exact immutable ordinal1 parent/second permit lineage")
    stable=digest(json.dumps(expected_identity,sort_keys=True).encode())
    need(new_path.name==stable+".00000002.claim.json"and old_path.name==stable+".00000001.claim.json","actual same stable identity filename/contiguous ordinal1-to2")
    binding=new["binding"];qr=query65["result"];context=qr["character_interaction_ordinary_context"];fr=frame63["snapshot_after"]
    need(qr["queried_revision"]==binding["revision"]==fr["revision"]==30 and qr["queried_native_revision"]==binding["native_revision"]==fr["native_revision"]==29 and qr["queried_snapshot_id"]==binding["snapshot_id"]==fr["snapshot_id"]=="native:29","fresh SDK65 actual exact frame63 public30/native29")
    need(current64["result"]["queried_revision"]==30 and current64["result"]["queried_native_revision"]==29 and c["actual_release_context"]=={"revision":30,"native_revision":29,"snapshot_id":"native:29","date_raw":53144712},"actual second release context64/frame63 remains exact frame before fresh65")
    need(binding["date_raw"]==context["date_raw"]==fr["date_raw"]==53144712 and binding["episode_run_id"]is None and binding["active_event_present"]is False and binding["incoming_interaction_present"]is False and fr["active_event"]is None and fr["pending_character_interaction"]is None and fr["paused"]is True,"actual new frame date/paused/no event/incoming; no episode release")
    need(context["game_pid"]==13436 and context["connection_generation"]==1 and context["player_character_id"]==31254 and context["recipient_id"]==65866 and context["interaction_key"]==expected_identity["interaction_key"]and all(context[k]is True for k in ["shown","can_send","ready_to_initiate","actor_alive","recipient_alive","source_code_pins_verified","actor_binding_verified","recipient_binding_verified","owner_thread_verified","tls_verified","frame_verified"]),"actual fresh65 full native ready gates and complete IDs")
    need(all(x["profile_sha256"]==new["host_provenance"]["profile_sha256"]and x["session_id"]==new["host_provenance"]["session_id"]and x["pipe_name"]==new["host_provenance"]["pipe_name"]for x in [query65,send66,snap67,current64,frame63]),"actual new SDK same profile/session/pipe")
    need(released<datetime.fromisoformat(query65["recorded_at_utc"])<datetime.fromisoformat(send66["recorded_at_utc"])<datetime.fromisoformat(snap67["recorded_at_utc"]),"actual release then freshquery then send then independent snapshot")
    packet_raw=new_path.with_suffix(".packet.bin").read_bytes()
    need(ref(new_path.with_suffix(".packet.bin"))["sha256"]=="9e75cbcb8c90c53a499d913c60fd21c62712fb76564750ba3ebcbfef5451845c"and len(packet_raw)==363 and struct.unpack("<I",packet_raw[:4])[0]==359,"actual ordinal2 packet exact hash/u32length")
    packet=json.loads(packet_raw[4:])
    expected_packet={"type":"execute_step","protocol_version":1,"request_id":new["request_id"],"step":"initiate-character-interaction-ordinary-v1","expected_revision":29,"interaction_key":expected_identity["interaction_key"],"recipient_id":65866,"expected_player_character_id":31254,"expected_game_pid":13436,"expected_connection_generation":1}
    need(packet==expected_packet and len(packet)==10 and json.dumps(packet,separators=(",",":")).encode()==packet_raw[4:],"ordinal2 exact compact closed10 expectednative29")
    native=data(new_path.with_suffix(".native-result.json"),"dfc6fdda14e23f21c8ec2e648ae242a1fa5034e763cea821fa480bc68aaaf0ae")
    ni=native["result"]["character_interaction_ordinary_initiation"]
    need(native["request_id"]==new["request_id"]and native["ok"]is True and native["result"]["status"]==ni["status"]=="pending"and ni["verification_pending"]is True and ni["postcondition_verified"]is False and ni["business_postcondition_verified"]is False,"actual native ordinal2 dispatch pending only")
    need(ni==send66["result"]["character_interaction_ordinary_initiation"]and send66["business_effects_verified"]is False and send66["full_product_acceptance_credit"]is False,"SDK66 exact original native initiation and false business credit")
    pending=data(new_path.with_suffix(".receipt.json"),"99650627fbd97ecb26056285c5438d1871722617cacfaf85c934d29b6ad94161")
    need(pending["request_id"]==new["request_id"]and pending["result"]==send66["result"]and pending["business_postcondition_verified"]is False,"actual ordinal2 host pending receipt unchanged schema and result")
    snapshot=snap67["snapshot"]
    need(snapshot["revision"]==31 and snapshot["native_revision"]==30 and snapshot["snapshot_id"]=="native:30"and snapshot["date_raw"]==53144712 and snapshot["paused"]is True and snapshot["active_event"]["instance_id"]==58 and snapshot["pending_character_interaction"]is None,"actual independent SDK67 wrapper frame31/native30 active58")
    need(send66["result"]["after_revision"]==30 and send66["result"]["after_native_revision"]==29 and send66["snapshot"]["revision"]==31 and send66["snapshot"]["native_revision"]==30,"actual driveroriginalafter30/29 retained separately from wrapper31/30")
    need(snapshot["played_character"]["character_id"]==31254 and snapshot["played_character"]["alive"]is True,"actual postdispatch full played actor positive")
    # Preserve prior actual chain by exact SHA references; do not rerun prior224 conditions.
    prior=BASE/"r10-actual-first-release-lineage-independent-review-20261005-002"
    need(ref(prior/"REPORT.json")["sha256"]=="6ae69334d8a05f9a769f23afa5944a13fb817c9c8d65341f0bc8699cc5aba0dc"and ref(prior/"INDEX.json")["sha256"]=="98fb96035455b111ce2774c81a0285cf2fd4f5f5c094c11055d73ba5b0a82f20","prior lineage report reused exact; old224 checks not repeated")
    old0=old_path.with_name(stable+".00000000.claim.json")
    need(ref(old0)["sha256"]=="3fae018f1468983c59bb0cf6a8d32704cb6f791d6b25cae69451a82960b495ce"and data(old0)["status"]=="claimed_result_unknown_no_retry","original ordinal0 UNKNOWN parent still preserved")
    need(ref(old0.with_suffix(".release.json"))["sha256"]=="6c7fd772f928041d1d616b77e9d5c00d27441ef6e52e1f030c14fe5b60b77c84"and ref(old0.with_suffix(".release.consumed.json"))["sha256"]=="35287deac29f81d36d3d6978ba16253bac4ae954a4beba9ebd5852f179cea0ea","first actual permit and consumed record preserved")
    rbroot=BASE/"r10-actual-second-open-join-readback-20261005-001"
    need(ref(rbroot/"INDEX.json")["sha256"]=="1f0bf6713c4290bcff506dfe7f9e434835e3e469262f1369feaaaed81708de52"and ref(rbroot/"REPORT.json")["sha256"]=="4846d30c937881b47820c5682a276b170eee4f62a29ee007eeb274a4ec10f2df","existing saved7-to8 AST sealed refs reused without scan")
    report={"schema":"lyd.r10.actual-second-emit-release-ordinal2-independent-review.v1",
        "status":"ACTUAL_SECOND_EMIT_RELEASE_PERMIT_CONSUMED_ORDINAL2_LINEAGE_MATCH",
        "recorded_utc":datetime.now(timezone.utc).isoformat(),"checks_count":len(checks),"checks":checks,
        "actual_ROOT_second_emit":True,"actual_ROOT_second_release":True,"actual_second_permit_consumed":True,
        "emitted_consumption":{"request_id":old["request_id"],"claim_ordinal":1,"serial_nonce_before":[7,7],"serial_nonce_after":[8,8],"save_pair":"immutable39-to43","wallet_delta":["0","0","0"],"completed_history_unchanged":True},
        "next_intent":{"request_id":new["request_id"],"claim_ordinal":2,"binding":binding,"lineage":new["new_intent_lineage"],"action_identity":expected_identity,"native_SDK_status":"pending","independent_snapshot":{"public_revision":31,"native_revision":30,"date_raw":53144712,"active_event_instance":58}},
        "third_proposal_saved_nonce":None,"third_proposal_save_AST_NOT_PROVIDED":True,
        "immutable_ordinal0_and_ordinal1_preserved":True,"both_prior_permits_and_consumed_records_preserved":True,
        "new_final_JOIN_credit":False,"full_cycle_credit":False,"ACK_business_credit":False,"permit_business_credit":False,
        "emission_time_release_flags_remain_false":"Emission artifact records pre-release state; separately later actual ROOT permit/release receipts are true.",
        "prior224_checks_repeated":False,"prior44_checks_repeated":False,"save_AST_reparsed":False,
        "reviewer_operations":{"bind":0,"emit":0,"registry_write":0,"host_release":0,"game":0,"native":0,"MCP":0,"pipe":0,"Client":0,"bus":0,"Git":0,"main":0,"save_AST_parse":0},
        "references":list(references.values())}
    (OUT/"REPORT.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (OUT/Path(__file__).name).write_bytes(Path(__file__).read_bytes())
    ix={"schema":"lyd.external-evidence-index.v1","files":[{"path":p.name,"bytes":len(p.read_bytes()),"sha256":digest(p.read_bytes())}for p in sorted(OUT.iterdir())if p.is_file()]}
    (OUT/"INDEX.json").write_text(json.dumps(ix,indent=2)+"\n",encoding="utf-8")
    for p in OUT.iterdir():
        if p.is_file():os.chmod(p,0o444)
    print(json.dumps({"status":report["status"],"checks_count":len(checks),"REPORT":ref(OUT/"REPORT.json"),"INDEX":ref(OUT/"INDEX.json")},ensure_ascii=True))
except Exception as error:
    (OUT/"FAILURE.json").write_text(json.dumps({"status":"READONLY_REVIEW_REJECTED","reason":str(error),"matched_checks":checks,"live_calls":0},indent=2)+"\n",encoding="utf-8")
    raise
