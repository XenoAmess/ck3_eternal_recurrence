from pathlib import Path
import hashlib,json,stat
from datetime import datetime,timezone
B=Path("C:/workspace/ck3_lyd_runtime_20261004")
E=B/"r10-first-proposal-emitted-evidence-20261005-004"
A=B/"r10-first-join-proof-inputs-20261005-004"
BD=B/"r10-first-proposal-bound-verifier-20261005-003"
IV=B/"live-attempt-010/root-first-consumption-emit-invocation-002"
O=B/"r10-first-consumption004-independent-review-20261005-002"
checks=[]
def sha(d):return hashlib.sha256(d).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding="utf-8"))
def ref(p):
    p=Path(p);d=p.read_bytes();return {"path":p.as_posix(),"bytes":len(d),"sha256":sha(d)}
def need(v,label):
    if not v:raise ValueError(label)
    checks.append({"condition":label,"matched":True})
def checked(v):
    p=Path(v["path"]);need(sha(p.read_bytes())==v["sha256"],"actual support hash: "+p.name);return p
def write(p,j):
    with p.open("xb") as f:f.write((json.dumps(j,ensure_ascii=True,indent=2)+"\n").encode("utf-8"))
if O.exists():raise ValueError("append-only output exists")
O.mkdir()
try:
    need(ref(E/"INDEX.json")["sha256"]=="1e87ab45bc0182e2f83ef6a925d9dae83cf35677d77234d2ea75aab1f0fb3664","actual emitted output INDEX exact")
    rows=read(E/"INDEX.json")["files"]
    for row in rows:
        p=E/row["path"];d=p.read_bytes();need(len(d)==row["bytes"] and sha(d)==row["sha256"],"actual indexed emitted payload: "+row["path"])
    need({p.name for p in E.iterdir() if p.is_file()}=={r["path"] for r in rows}|{"INDEX.json"},"exact emitted inventory coverage")
    request=read(A/"EMIT-REQUEST.actual.json")
    need((E/"EMISSION-REQUEST.raw.json").read_bytes()==(A/"EMIT-REQUEST.actual.json").read_bytes(),"original004 emission request exact raw copy")
    inv=read(IV/"RESULT.json")
    need(inv["status"]=="INVOCATION_COMPLETED" and inv["exit_code"]==0,"ROOT actual emitter invocation exit0")
    need(ref(IV/"stdout.txt")["sha256"]==inv["stdout_sha256"]=="c95482d491a0f540206df5f911b6897363eeb8aab8c14d974b354379fa5849a5" and ref(IV/"stderr.txt")["sha256"]==inv["stderr_sha256"],"actual emitter stdio hashes exact")
    need(inv["argv_source_sha256"]==ref(A/"ROOT-EMIT-ARGV.json")["sha256"] and read(IV/"argv.json")==read(A/"ROOT-EMIT-ARGV.json")["argv"],"actual executed argv exact author004 frozen argv")
    manifest=read(E/"CONSUMPTION-MANIFEST.json")
    facts=read(E/"INDEPENDENT-FACTS.json");detail=read(E/"PRODUCT-DETAIL.json");status=read(E/"EMISSION-STATUS.json")
    need(ref(E/"CONSUMPTION-MANIFEST.json")["sha256"]=="5f0ec75c2eaa9dbe3da15f691a49c291594b7f7de388035da5f5becad55f24a7","actual consumed manifest exact root pin")
    need(set(manifest)=={"schema","claim_request_id","action_identity","packet","native_result","unknown","before_artifact","after_artifact","independent_report"} and manifest["schema"]=="ck3-ordinary-interaction-consumption-manifest-v1","closed generic consumption manifest")
    claim=read(checked(request["claim"]))
    identity=claim["action_identity"]
    need(manifest["claim_request_id"]==facts["claim_request_id"]==claim["request_id"] and manifest["action_identity"]==facts["action_identity"]==identity and len(identity)==6,"actual manifest/facts original six identity and request exact")
    need(identity=={"game_pid":13436,"actor_id":31254,"process_create_time":1791196395.7422996,"interaction_key":"lyd_c2_propose_join_interaction","recipient_id":65866,"action":"initiate_ordinary"},"full scoped stable identity actual")
    for k in ("packet","native_result","before_artifact","after_artifact"):
        checked(manifest[k]);need(facts[k+"_sha256"]==manifest[k]["sha256"],"facts exact artifact SHA: "+k)
    need(manifest["unknown"] is None and facts["unknown_sha256"] is None,"no fabricated unknown or receipt")
    checked(manifest["independent_report"])
    need(Path(manifest["independent_report"]["path"]).resolve()==(E/"INDEPENDENT-FACTS.json").resolve(),"independent report actual emitted facts binding")
    need(set(facts)=={"schema","claim_request_id","action_identity","packet_sha256","native_result_sha256","unknown_sha256","before_artifact_sha256","after_artifact_sha256","consumption"} and facts["schema"]=="ck3-ordinary-interaction-independent-consumption-v1","closed provider typed facts schema")
    need(facts["consumption"]=={"kind":"save_round_delta","field_name":"lyd_c2_callback_nonce","before_value":6,"after_value":7,"actor_id":31254,"recipient_id":65866,"interaction_key":"lyd_c2_propose_join_interaction"},"actual frozen provider consumption nonce6->7 with full recipient")
    cond=detail["conditions"]
    need(cond["consumption_mode"]=="PROPOSAL_OPENED" and cond["serial_nonce_before"]==[6,6] and cond["serial_nonce_after"]==[7,7],"actual dynamic opened-proposal serial/nonce result")
    need(cond["source_faith"]=="106" and cond["target_faith"]=="104" and cond["moving_rite"]=="169" and cond["target_main"]=="159" and cond["target_rep"]=="65866","actual typed graph identities retained")
    need(cond["actual_source_roles"]==["31254","65865"] and cond["actual_target_roles"]==["65866"] and cond["actual_human_roles"]==["31254"],"actual positive saved role lists")
    need(cond["wallet_delta"]==["0","0","0"] and cond["completed_history_unchanged"] is True,"opening resource and completed history unchanged")
    need(cond["NPC_vote_choice_required"] is False and cond["join_business_acceptance_credit"] is False,"consumption proof has no forced NPC or JOIN business credit")
    before=read(request["before_artifact"]["path"]);after=read(request["after_artifact"]["path"])
    need(detail["before_save"]==before["save"] and detail["after_save"]==after["save"] and before["save"]["bytes"]==91529730 and after["save"]["bytes"]==91534935,"real13/16 saves exact corrected three-field references")
    need(detail["source_revision"]=="d0f8fa3b9d444828759443aa018bfd7ad31b398d" and detail["parser_sha256"]=="6c1ba1006cd0dd5055c11115701b60a74562b0f23d91b756a3d9322e7d055cb7" and detail["reader_version"]=="lyd-join-save-consumption-verifier-v2","actual source/parser producer frozen")
    need(cond["current_release_context_sdk"]==after["release_context_sdk"] and cond["current_release_context_frame_sdk"]==after["release_context_frame_sdk"] and cond["actual_release_context"]=={"revision":18,"native_revision":17,"snapshot_id":"native:17","date_raw":53144712},"real current40/frame39 release evidence exact")
    for k in ("current_release_context_sdk","current_release_context_frame_sdk","pre_send_query_frame_sdk"):checked(cond[k])
    bound=read(BD/"ROOT-BINDING.json")["actual_binding"]
    need(bound["game_pid"]==identity["game_pid"] and bound["process_create_time"]==identity["process_create_time"] and bound["actor_id"]==31254 and bound["recipient_id"]==65866 and bound["profile_sha256"]==claim["host_provenance"]["profile_sha256"]=="2f7140598909b5f34484ab74941ead7e26c32ad416aca0ebfcabc71b93573db6" and bound["session_id"]==claim["host_provenance"]["session_id"]=="53bd96329c5541f7a403c5cecf61d8ba","bound provider process/profile/session exact original claim")
    need(status["status"]=="FROZEN_SAVE_CONSUMPTION_FACTS_READY_FOR_ROOT_REVIEW" and status["actual_host_release"] is False and status["registry_enabled"] is False and status["native_ACK_credit"] is False and status["full_C2_cycle_credit"] is False and detail["native_ACK_credit"] is False and detail["actual_release"] is False,"actual emitted status retains pending host release and business-credit boundaries")
    need(claim["status"]=="claimed_result_unknown_no_retry","old original once claim remains unchanged UNKNOWN")
    failed=B/"r10-first-consumption004-independent-review-20261005-001/FAILURE.json"
    need(failed.is_file() and read(failed)["reason"]=="fresh004 emitter output; no failed output reuse","first readonly review refusal preserved; concurrent real emitter explains exists")
    report={"schema":"lyd.r10.actual-first-consumption-output-independent-review.v1",
        "utc":datetime.now(timezone.utc).isoformat(),"status":"ACTUAL_ROOT_EMITTED_PROPOSAL_CONSUMPTION_OUTPUT_MATCH",
        "actual_ROOT_execution":ref(IV/"RESULT.json"),"actual_output_INDEX":ref(E/"INDEX.json"),
        "actual_consumption_manifest":ref(E/"CONSUMPTION-MANIFEST.json"),
        "actual_independent_facts":ref(E/"INDEPENDENT-FACTS.json"),"actual_product_detail":ref(E/"PRODUCT-DETAIL.json"),
        "actual_saved_consumption_nonce":[6,7],"source_mode":"PROPOSAL_OPENED","original_action_identity":identity,
        "checks":checks,"actual_ROOT_emitter_executed":True,"actual_emitter_executed_by_reviewer":False,
        "actual_verifier_consumption_report_present":True,"reviewer_save_AST_parse_count":0,
        "JOIN_business_credit":False,"full_cycle_credit":False,
        "registry_or_release_state":"emission artifact records false; future ROOT host actions are outside this reviewed artifact",
        "actual_registry_writes_by_reviewer":0,"actual_host_release_calls_by_reviewer":0,
        "actual_MCP_calls_by_reviewer":0,"actual_game_calls_by_reviewer":0,
        "first_review_refusal_preserved":ref(failed),
        "first_review_refusal_boundary":"The static fresh-output absence check encountered ROOT's concurrent actual successful004 emission; this is not a product failure and no emission was repeated by the reviewer."}
    write(O/"REPORT.json",report)
    with (O/"independent_output_review.py").open("xb") as f:f.write(Path(__file__).read_bytes())
    outrows=[]
    for p in sorted(O.iterdir()):
        if p.is_file():
            z=ref(p);outrows.append({"path":p.name,"bytes":z["bytes"],"sha256":z["sha256"]})
    write(O/"INDEX.json",{"schema":"lyd.r10.actual-first-consumption-output-review-index.v1","files":outrows})
    for p in O.iterdir():
        if p.is_file():p.chmod(stat.S_IREAD)
    print(json.dumps({"report":ref(O/"REPORT.json"),"index":ref(O/"INDEX.json"),"conditions_matched":len(checks),"actual_consumption_nonce":[6,7],"JOIN_business_credit":False,"reviewer_executions":0},ensure_ascii=True))
except Exception as e:
    write(O/"FAILURE.json",{"reason":str(e),"conditions_before_refusal":checks,"actual_calls_by_reviewer":0})
    raise

