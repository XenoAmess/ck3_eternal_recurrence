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
OUT = BASE / "r10-actual-first-release-lineage-independent-review-20261005-002"
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
    raise FileExistsError("append-only output exists")
OUT.mkdir()
try:
    hostdir = RUN / "root-first-consumption-host-request-001"
    invocation = RUN / "root-first-consumption-release-invocation-001"
    request = data(hostdir / "RELEASE-REQUEST.actual.json", "7e3778ab904a74414b725be51a0b30e5954ad5cd26e3be3fc2fa137303680027")
    closed(request, ["schema", "host_module", "claim", "consumption_manifest", "registry",
                     "verifier_id", "operator_id", "next_intent_id"], "ROOT actual closed release request")
    need(request["schema"] == "ck3-r9-root-ordinary-release-request-v1", "actual ROOT wrapper schema")
    hostref = read_ref(request["host_module"], "actual host module")
    need(hostref["sha256"] == "f567bff41d03b6c59d195df8ff62ecab1a523962de3217d397c5264d1ed2d89b", "frozen host f567 unchanged")
    oldpath = Path(request["claim"]["path"])
    old = data(oldpath, request["claim"]["sha256"])
    need(request["claim"]["sha256"] == "3fae018f1468983c59bb0cf6a8d32704cb6f791d6b25cae69451a82960b495ce", "immutable old claim prior SHA preserved")
    need(old["claim_ordinal"] == 0 and old["new_intent_lineage"] is None and old["status"] == "claimed_result_unknown_no_retry", "old UNKNOWN claim unchanged; no fabricated ACK or lineage")
    for suffix, expected in [
        (".packet.bin", "1eda105a6c7511a0d9d18ab552140e2d9ee8147c39d2abec6bb3e0e1e0732460"),
        (".native-result.json", "b114530f95018bbb6617282faf5888547f6a2776f1e2f701b257f86549e05277"),
        (".receipt.json", "623431eaae7e851c1f544f30fd893c0e3ca420901dd845a573f59465bea35e79")]:
        path = oldpath.with_suffix(suffix)
        need(ref(path)["sha256"] == expected, "immutable old " + suffix + " prior SHA preserved")
    manifest_ref = read_ref(request["consumption_manifest"], "existing emit004 manifest")
    need(manifest_ref["sha256"] == "5f0ec75c2eaa9dbe3da15f691a49c291594b7f7de388035da5f5becad55f24a7", "release uses actual reviewed emitted004 manifest")
    registry_ref = read_ref(request["registry"], "ROOT actual registry")
    registry = data(request["registry"]["path"])
    closed(registry, ["schema", "verifiers"], "actual closed registry")
    need(registry["schema"] == "ck3-ordinary-interaction-root-verifier-registry-v1", "registry actual schema")
    verifier = registry["verifiers"][request["verifier_id"]]
    closed(verifier, ["bundle_index", "entrypoint"], "actual verifier registry row")
    need(verifier["entrypoint"] == "verifier.py:verify_consumption", "frozen verifier entrypoint")
    bundle_ref = read_ref(verifier["bundle_index"], "existing ROOT bound003 INDEX")
    need(bundle_ref["sha256"] == "b6bd15f678df586b06403de8c05db692ef5fdf35583638347e853fc0e757ee68", "registry binds real bound003; no new provider binding")

    rootargv = data(hostdir / "release-argv.json", "a425459d717a848255dc07a307b6c8ce5e876ccc36bd61c85bfb56ed614b714c")
    actualargv = data(invocation / "argv.json")
    result = data(invocation / "RESULT.json", "675b923cab432cb663da734be303608dc3d332be142a078994642316c3a92266")
    need(actualargv == rootargv["argv"], "actual ROOT invoked exact captured release argv")
    need(result["exit_code"] == 0 and result["status"] == "INVOCATION_COMPLETED", "actual ROOT host release exit0")
    need(result["argv_source_sha256"] == references[str(hostdir / "release-argv.json")]["sha256"] and same_path(result["argv_source"], hostdir / "release-argv.json"), "invocation exact structured argv source")
    need(ref(invocation / "stdout.txt")["sha256"] == result["stdout_sha256"] and ref(invocation / "stderr.txt")["sha256"] == result["stderr_sha256"], "actual stdout/stderr exact recorded SHA")
    need((invocation / "stderr.txt").read_bytes() == b"", "actual release stderr empty")
    stdout = data(invocation / "stdout.txt")
    need(stdout["game_command_sent"] is False and stdout["business_acceptance_credit"] is False and stdout["scope"] == "one_independent_next_intent_only", "host release reports one intent, no game command/business credit")

    permit_path = oldpath.with_suffix(".release.json")
    permit = data(permit_path, "6c7fd772f928041d1d616b77e9d5c00d27441ef6e52e1f030c14fe5b60b77c84")
    closed(permit, ["schema", "claim_path", "claim_sha256", "claim_request_id", "action_identity",
                   "old_connection_generation", "manifest", "registry", "verifier_id", "verifier_bundle",
                   "operator_id", "next_intent_id", "released_at_utc", "scope", "business_acceptance_credit"], "actual closed permit")
    need(permit["schema"] == "ck3-ordinary-interaction-next-intent-permit-v1", "permit schema")
    need(permit["claim_path"] == str(oldpath) and permit["claim_sha256"] == request["claim"]["sha256"] and permit["claim_request_id"] == old["request_id"], "permit exact immutable parent path/SHA/request")
    need(permit["manifest"] == request["consumption_manifest"] and permit["registry"] == request["registry"] and permit["verifier_bundle"] == verifier["bundle_index"], "permit exact manifest/registry/bundle refs")
    need(all(permit[key] == request[key] for key in ["verifier_id", "operator_id", "next_intent_id"]), "permit exact verifier/operator/new intent")
    need(stdout["permit_path"] == str(permit_path) and stdout["permit_sha256"] == references[str(permit_path)]["sha256"], "actual release stdout exact permit")
    need(permit["scope"] == "operator_verified_consumption_for_one_new_intent" and permit["business_acceptance_credit"] is False, "actual permit no JOIN business credit")
    release_time = datetime.fromisoformat(permit["released_at_utc"])
    need(datetime.fromisoformat(result["started_utc"]) <= release_time <= datetime.fromisoformat(result["completed_utc"]), "permit actual time within ROOT host invocation")

    sd = RUN / "mcp-client-evidence-002"
    query41 = sdk(sd / "0041-r10-0042-new-intent-ready-query.sdk-result.json", "25f1988bddbaa71ea475df2abdd8fd278218b70c536a08e474cd3f737e8a6496")
    send42 = sdk(sd / "0042-r10-0043-new-join-proposal.sdk-result.json", "7ca0c41afd76f00b7254d74aadf1fb1ec64ba21556034ed491f0abe5e71fada6")
    frame39 = sdk(sd / "0039-r10-0040-before-new-intent-save.sdk-result.json", "bd42ed433479028fe1970d0d8afa7a7ddd4dea67f0eec21117f3c60112653d22")
    newpath = Path(send42["result"]["action_claim_path"])
    need(newpath.parent.resolve() == CLAIM_DIR.resolve(), "new claim located by actual SDK42; expected contained claim directory")
    new = data(newpath, "7c2d0d36486fc2ec6c0d44fb24319affdce818feb3edb59d6878921e3d00c021")
    closed(new, ["schema", "request_id", "binding", "action_identity", "claim_ordinal", "host_provenance", "new_intent_lineage", "status"], "actual closed new claim")
    need(new["schema"] == old["schema"] == "ck3-ordinary-interaction-once-claim-v1" and new["status"] == "claimed_result_unknown_no_retry", "new immutable UNKNOWN claim; no ACK rewritten into claim")
    expected_identity = {"game_pid": 13436, "actor_id": 31254, "process_create_time": 1791196395.7422996,
                         "interaction_key": "lyd_c2_propose_join_interaction", "recipient_id": 65866, "action": "initiate_ordinary"}
    closed(new["action_identity"], expected_identity.keys(), "six identity closed")
    need(old["action_identity"] == permit["action_identity"] == new["action_identity"] == expected_identity, "same full six identity; no episode/PID/recipient bypass")
    need(type(new["claim_ordinal"]) is int and new["claim_ordinal"] == old["claim_ordinal"] + 1 == 1, "new ordinal1 follows original ordinal0")
    expected_stem = digest(json.dumps(expected_identity, sort_keys=True).encode())
    need(oldpath.name == expected_stem + ".00000000.claim.json" and newpath.name == expected_stem + ".00000001.claim.json", "actual stable identity filename hash and contiguous ordinals")
    need(new["host_provenance"] == old["host_provenance"] and new["binding"]["episode_run_id"] is None == old["binding"]["episode_run_id"], "same host provenance/session/episode; no epoch unlock")
    need(new["request_id"] == send42["result"]["action_request_id"] == "ordinary-interaction-a50373f260354f6f83c8052eaf837c7f" and new["request_id"] != old["request_id"], "actual distinct new request UUID")
    consumed_path = permit_path.with_suffix(".consumed.json")
    consumed = data(consumed_path, "35287deac29f81d36d3d6978ba16253bac4ae954a4beba9ebd5852f179cea0ea")
    closed(consumed, ["schema", "permit_path", "permit_sha256", "new_request_id", "next_intent_id",
                      "old_connection_generation", "new_connection_generation", "new_binding",
                      "action_identity", "business_acceptance_credit"], "actual closed permit consumption")
    need(consumed["schema"] == "ck3-ordinary-interaction-permit-consumption-v1", "actual consumption schema")
    need(consumed["permit_path"] == str(permit_path) and consumed["permit_sha256"] == references[str(permit_path)]["sha256"], "consumed receipt exact released permit")
    need(consumed["new_request_id"] == new["request_id"] and consumed["next_intent_id"] == permit["next_intent_id"], "consumed one permit for actual new request/intent")
    need(consumed["action_identity"] == expected_identity and consumed["business_acceptance_credit"] is False, "consumption unchanged six identity and no business credit")
    need(consumed["old_connection_generation"] == permit["old_connection_generation"] == old["binding"]["connection_generation"] == 1 and consumed["new_connection_generation"] == new["binding"]["connection_generation"] == 1, "same actual connection generation1; no reconnect unlock")
    need(consumed["new_binding"] == new["binding"], "consumed exact new claim binding")
    lineage = new["new_intent_lineage"]
    closed(lineage, ["permit_path", "permit_sha256", "next_intent_id", "parent_claim_path", "parent_claim_sha256"], "actual new claim closed lineage")
    need(lineage == {"permit_path": str(permit_path), "permit_sha256": references[str(permit_path)]["sha256"],
                     "next_intent_id": permit["next_intent_id"], "parent_claim_path": str(oldpath), "parent_claim_sha256": request["claim"]["sha256"]}, "new claim exact consumed permit/immutable parent lineage")

    binding = new["binding"]
    frame = frame39["snapshot_after"]
    qr = query41["result"]
    context = qr["character_interaction_ordinary_context"]
    need(binding["revision"] == qr["queried_revision"] == frame["revision"] == 18 and binding["native_revision"] == qr["queried_native_revision"] == frame["native_revision"] == 17 and binding["snapshot_id"] == qr["queried_snapshot_id"] == frame["snapshot_id"] == "native:17", "fresh query41 actual before39 frame public18/native17")
    need(binding["date_raw"] == context["date_raw"] == frame["date_raw"] == 53144712 and context["game_pid"] == binding["game_pid"] == 13436 and context["player_character_id"] == binding["played_character_id"] == 31254, "actual date/PID/full actor frame binding")
    need(context["recipient_id"] == 65866 and context["interaction_key"] == expected_identity["interaction_key"] and all(context[k] is True for k in ["shown", "can_send", "ready_to_initiate", "source_code_pins_verified", "actor_binding_verified", "recipient_binding_verified", "owner_thread_verified", "tls_verified", "frame_verified"]), "actual fresh41 full recipient/key and all ordinary ready gates")
    need(context["active_event_present"] is False and context["incoming_interaction_present"] is False and frame["active_event"] is None and frame["pending_character_interaction"] is None and frame["paused"] is True, "actual new-intent frame no event/incoming and paused")
    need(context["effective_roles"] == {"actor_id":31254, "recipient_id":65866, "secondary_actor_id":None, "secondary_recipient_id":None, "intermediary_id":None, "sixth_role_id":31254}, "actual six effective roles")
    need(all(p["session_id"] == new["host_provenance"]["session_id"] and p["profile_sha256"] == new["host_provenance"]["profile_sha256"] and p["pipe_name"] == new["host_provenance"]["pipe_name"] for p in [query41, frame39, send42]), "actual SDKs same pinned profile/session/pipe")
    need(release_time < datetime.fromisoformat(query41["recorded_at_utc"]) < datetime.fromisoformat(send42["recorded_at_utc"]), "actual fresh query occurs after release and before new send")

    packet_path = newpath.with_suffix(".packet.bin")
    packet_raw = packet_path.read_bytes()
    packet_ref = ref(packet_path)
    need(packet_ref["sha256"] == "909aaa95148773b05c67649cf53e1c98debd4bbcef817d9e65704d0335350ee7" and len(packet_raw) == 363 and struct.unpack("<I",packet_raw[:4])[0] == len(packet_raw)-4, "actual new packet exact SHA/u32 length")
    packet = json.loads(packet_raw[4:].decode("utf-8"))
    expected_packet = {"type":"execute_step", "protocol_version":1, "request_id":new["request_id"],
                       "step":"initiate-character-interaction-ordinary-v1", "expected_revision":17,
                       "interaction_key":expected_identity["interaction_key"], "recipient_id":65866,
                       "expected_player_character_id":31254, "expected_game_pid":13436, "expected_connection_generation":1}
    need(packet == expected_packet and len(packet) == 10, "actual new packet exact closed10 native17/player/PID/gen/fullrecipient/request")
    native = data(newpath.with_suffix(".native-result.json"), "754e1da18c03e60d44981313375f1eef1c0516e63d9c19e89047582c492a78c0")
    nr = native["result"]
    ni = nr["character_interaction_ordinary_initiation"]
    need(native["request_id"] == new["request_id"] and native["ok"] is True and nr["status"] == ni["status"] == "pending" and ni["verification_pending"] is True and ni["business_postcondition_verified"] is False and ni["postcondition_verified"] is False, "actual native initiation ACK pending, no postcondition business success")
    need(send42["result"]["character_interaction_ordinary_initiation"] == ni, "SDK42 preserves actual native initiation receipt")
    receipt = data(newpath.with_suffix(".receipt.json"), "939bbcb4175e98351e80d18e96c7c3d5237fbca14c3fa90fdc94ad539e3100af")
    need(receipt["request_id"] == new["request_id"] and receipt["business_postcondition_verified"] is False and receipt["result"] == send42["result"], "actual host pending receipt exact SDK result; no invented success")
    need(send42["business_effects_verified"] is False and send42["full_product_acceptance_credit"] is False and send42["result"]["business_effects_verified"] is False and send42["result"]["full_product_acceptance_credit"] is False, "new SDK pending credit remains false")
    need(send42["result"]["after_revision"] == 18 and send42["result"]["after_native_revision"] == 17 and send42["snapshot"]["revision"] == 19 and send42["snapshot"]["native_revision"] == 18, "driver originalafter retained separately from later wrapper frame")

    readback_root = BASE / "r10-actual-second-open-join-readback-20261005-001"
    rb_index = data(readback_root / "INDEX.json", "1f0bf6713c4290bcff506dfe7f9e434835e3e469262f1369feaaaed81708de52")
    need(rb_index["schema"] == "lyd.external-evidence-index.v1", "reused sealed second-open INDEX schema")
    rows = rb_index["files"]
    seen = set()
    for row in rows:
        closed(row, ["path","bytes","sha256"], "second-open indexed payload row")
        target = (readback_root / row["path"]).resolve()
        need(readback_root.resolve() in target.parents and row["path"] not in seen, "second-open index contained and unique")
        seen.add(row["path"])
        actual = ref(target)
        need(actual["bytes"] == row["bytes"] and actual["sha256"] == row["sha256"], "second-open indexed bytes/SHA " + row["path"])
    actual_files = {str(p.relative_to(readback_root)).replace("\\","/") for p in readback_root.rglob("*") if p.is_file() and p.name != "INDEX.json"}
    need(actual_files == seen | {"SEALED.json"} and len(rows) == 36, "sealed second-open36 payload exact coverage plus explicit known sealing sidecar")
    sealing = data(readback_root / "SEALED.json", "c03e2e181ef522ad59e4f814652d6c604e396bd4d630ae66eee45a62eb284573")
    closed(sealing, ["REPORT", "INDEX", "typed_facts", "files"], "actual known SEALED sidecar schema")
    need(sealing["files"] == 36, "SEALED exact indexed payload count")
    for name, filename in [("REPORT","REPORT.json"),("INDEX","INDEX.json"),("typed_facts","PROPOSAL-OPENED-FACTS.json")]:
        need(same_path(sealing[name]["path"], readback_root / filename), "SEALED exact " + name + " path")
        read_ref(sealing[name], "SEALED exact " + name)
    prior_failure_path = BASE / "r10-actual-first-release-lineage-independent-review-20261005-001/FAILURE.json"
    prior_failure = data(prior_failure_path)
    need(prior_failure["reason"] == "sealed second-open 36 payload exact coverage; no save AST reparse", "prior reviewer sidecar expectation rejection preserved")
    rb = data(readback_root / "REPORT.json", "4846d30c937881b47820c5682a276b170eee4f62a29ee007eeb274a4ec10f2df")
    facts = data(readback_root / "PROPOSAL-OPENED-FACTS.json", "d43ee38000ecceced01626dba772f434dee76659ecae1c17cdc3bdda84fc5855")
    need(rb["status"] == facts["status"] == "ACTUAL_SECOND_PROPOSAL_OPENED_ROUND8_BOUND_NOT_FINAL_JOIN" and rb["final_JOIN_credit"] is False and facts["final_JOIN_credit"] is False, "reused actual AST report bounded opened round8, not final JOIN")
    need(facts["source_HEAD"] == "d0f8fa3b9d444828759443aa018bfd7ad31b398d" and facts["actual_actionUUID"] == new["request_id"] and facts["actual_claim_ordinal"] == 1 and facts["actual_claim_six_identity"] == expected_identity, "actual independent round8 report exact HEAD/new UUID/ordinal/sixidentity")
    for name in ["lyd_c2_callback_nonce", "lyd_c2_serial"]:
        change = facts["actual_round_change"][name]
        need(change["before"]["present"] is True and change["before"]["type"] == "value" and change["before"]["number"] == "7" and change["after"]["present"] is True and change["after"]["type"] == "value" and change["after"]["number"] == "8", "actual saved " + name + " positive typed7-to8")
    need(facts["actual_wallet_Decimal_delta"] == {"gold":"0","piety":"0","prestige":"0"} and facts["actual_history"]["lyd_c2_completed_joins"]["number"] == "1" and facts["actual_history"]["lyd_c2_completed_detaches"]["number"] == "2" and facts["fixture_reset_count"]["number"] == "4", "actual saved wallet0/historyJOIN1DETACH2/reset4; no new JOIN credit")
    need(facts["fresh41_before39_original_SDK"]["sha256"] == references[str(sd / "0041-r10-0042-new-intent-ready-query.sdk-result.json")]["sha256"] and facts["new42_original_SDK"]["sha256"] == references[str(sd / "0042-r10-0043-new-join-proposal.sdk-result.json")]["sha256"], "actual AST facts reuse exact original new query/send SDK references")
    need(all(value is True for value in rb["binding_and_protection_checks"].values()) and facts["before39_or_other_old_save_reparsed"] is False, "sealed AST scope honest; no repeated old save parse by independent lineage review")

    host_source = Path(request["host_module"]["path"])
    contract_source = Path("C:/lr10s1/ck3_autonomous_player/src/xar_autoplayer/bridge/ordinary_interaction_contract.py")
    need(ref(contract_source)["sha256"] == "e0a96aa39626df166270d3d5467a8e4d57cec77d7577cebcced03983feba5fa3", "canonical contract source exact e0")
    source_contracts = [source_function(host_source,"consume_next_intent_permit"),
                        source_function(contract_source,"create_once_claim"),
                        source_function(contract_source,"claim_identity")]
    parent_review = BASE / "r10-first-consumption004-independent-review-20261005-002"
    need(ref(parent_review / "INDEX.json")["sha256"] == "49da23f7b82b6cc6f47272efd5f5652faa3b0143f99a74f2c17aaf9828bcb8a3" and ref(parent_review / "REPORT.json")["sha256"] == "3a8164ae966d6ca167d4be3873442600113e3a3b62300b984ca08a4062cf450a", "previous44 emit review sealed refs reused, checks not repeated")

    report = {
        "schema":"lyd.r10.actual-host-release-next-intent-lineage-independent-review.v1",
        "status":"ACTUAL_ROOT_RELEASE_PERMIT_CONSUMED_NEW_ORDINAL1_LINEAGE_MATCH",
        "recorded_utc":datetime.now(timezone.utc).isoformat(),
        "scope":"Actual immutable host release/permit-consumption/claim packet/SDK lineage and reused sealed round8 save AST; no live calls or save reparse.",
        "actual_root_host_release":True, "actual_permit_consumed":True,
        "immutable_parent_preserved":True,
        "actual_release_request":references[str(hostdir / "RELEASE-REQUEST.actual.json")],
        "actual_release_result":references[str(invocation / "RESULT.json")],
        "parent_claim":references[str(oldpath)],
        "permit":references[str(permit_path)], "permit_consumed":references[str(consumed_path)],
        "new_claim":references[str(newpath)], "new_intent_lineage":lineage,
        "action_identity":expected_identity, "new_request_id":new["request_id"],
        "claim_ordinal_before":0, "claim_ordinal_after":1, "actual_connection_generation":1,
        "new_intent_frame":{"public_revision":18,"native_revision":17,"snapshot_id":"native:17","date_raw":53144712},
        "packet":packet, "native_and_SDK_initiation_status":"pending",
        "actual_saved_round_delta":{"serial":[7,8],"callback_nonce":[7,8]},
        "actual_completed_history":{"joins":1,"detaches":2},
        "actual_wallet_delta":{"gold":"0","piety":"0","prestige":"0"},
        "new_final_JOIN_credit":False, "full_cycle_credit":False,
        "sdk_ACK_business_credit":False, "permit_business_credit":False,
        "save_AST_readback_reused":{
            "index":references[str(readback_root / "INDEX.json")],
            "report":references[str(readback_root / "REPORT.json")],
            "facts":references[str(readback_root / "PROPOSAL-OPENED-FACTS.json")],
            "checked_payload_count":len(rows),"save_AST_reparsed_by_this_review":False},
        "source_contracts":source_contracts,
        "source_interpretation":"Frozen consume_next_intent_permit x-writes the consumed sidecar before new claim/send; create_once_claim returns contiguous ordinal1 with exact immutable parent/permit lineage. Actual files/packet/SDK match this path. No epoch, generation or identity field changed.",
        "previous_emit004_44_checks_repeated":False,
        "prior_review_expectation_rejection":{"ref":references[str(prior_failure_path)],"reason":"Reviewer001 expected no sealing sidecar. Actual SEALED.json matches REPORT/INDEX/facts/count; reviewed explicitly here. No host/product rejection."},
        "reviewer_operations":{"game":0,"MCP":0,"native":0,"pipe":0,"Client":0,"bus":0,"main":0,"Git":0,
                               "bind":0,"emit":0,"registry_write":0,"host_release":0,"save_AST_parse":0},
        "checks_count":len(checks),"checks":checks,
        "references":list(references.values())
    }
    (OUT / "REPORT.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    source_bytes = Path(__file__).read_bytes()
    (OUT / Path(__file__).name).write_bytes(source_bytes)
    index = {"schema":"lyd.external-evidence-index.v1","files":[]}
    for target in sorted(OUT.iterdir()):
        if target.is_file():
            raw=target.read_bytes()
            index["files"].append({"path":target.name,"bytes":len(raw),"sha256":digest(raw)})
    (OUT / "INDEX.json").write_text(json.dumps(index,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    for target in OUT.iterdir():
        if target.is_file():os.chmod(target,0o444)
    print(json.dumps({"status":report["status"],"checks_count":len(checks),
                     "REPORT":ref(OUT/"REPORT.json"),"INDEX":ref(OUT/"INDEX.json")},ensure_ascii=True))
except Exception as error:
    (OUT/"FAILURE.json").write_text(json.dumps({"status":"REVIEW_REJECTED","reason":str(error),"matched_checks":checks,
           "live_operations":0},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    raise

