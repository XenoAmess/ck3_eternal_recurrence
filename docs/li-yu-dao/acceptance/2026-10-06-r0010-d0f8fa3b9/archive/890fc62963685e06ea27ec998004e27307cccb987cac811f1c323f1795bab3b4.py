"""Independent static and inert checks for external assembler only."""
from pathlib import Path
from datetime import datetime,timezone
import ast,copy,hashlib,json,os

B=Path("C:/workspace/ck3_lyd_runtime_20261004")
P=B/"lyd-r10-proposal-input-assembler-20261005-002"
O=B/"r10-proposal-assembler-independent-review-20261005-001"
def sha(raw):return hashlib.sha256(raw).hexdigest()
def ref(path):
    path=Path(path);raw=path.read_bytes();return {"path":str(path),"bytes":len(raw),"sha256":sha(raw)}
def j(path):return json.loads(Path(path).read_bytes())
def need(ok,label):
    if not ok:raise ValueError(label)
if O.exists():raise FileExistsError("new review output required")
O.mkdir()
try:
    source=P/"assemble_proposal_inputs.py";source_ref=ref(source)
    need(source_ref["sha256"]=="30437a1dd88a86d99a685323c4b1a635d08b697394ebb895291e8643dff76b55","actual source SHA")
    index_ref=ref(P/"INDEX.json")
    need(index_ref["sha256"]=="465a71a42e98e0d6d86107cb1d9bb0f55fdf624f8c6b0e8dfabcd9183267bf46","actual author INDEX SHA")
    index=j(P/"INDEX.json");seen=set()
    for row in index["files"]:
        target=(P/row["path"]).resolve();need(P.resolve()in target.parents and row["path"]not in seen,"contained unique helper payload")
        seen.add(row["path"]);actual=ref(target);need(actual["bytes"]==row["bytes"]and actual["sha256"]==row["sha256"],"helper indexed actual bytes/SHA")
    actual={str(f.relative_to(P)).replace("\\","/")for f in P.rglob("*")if f.is_file()and f.resolve()!=(P/"INDEX.json").resolve()}
    need(actual==seen and len(seen)==30,"helper exact30 payload coverage")
    tree=ast.parse(source.read_bytes())
    imports=[ast.dump(n,include_attributes=False)for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom))]
    need(not any(s in "\n".join(imports) for s in ["subprocess","ctypes","importlib","socket","multiprocessing"]),"no helper imports for runtime dispatch")
    risky=[]
    for n in ast.walk(tree):
        if isinstance(n,ast.Call):
            name=ast.unparse(n.func)
            if name in ["eval","exec","__import__","os.system"]or any(s in name for s in ["Popen","run_command","call_tool","release_once","verify_consumption"]):risky.append(name)
    need(not risky,"no assembler provider/binder/emitter/release/native invocation calls")
    example=j(P/"ACTUAL-PRESERVED-ORDINAL4.example.json")
    query_ref=example["current_query_sdk"];frame_ref=example["current_query_frame_sdk"]
    qraw=j(query_ref["path"]);fraw=j(frame_ref["path"])
    need(ref(query_ref["path"])["sha256"]==query_ref["sha256"]and ref(frame_ref["path"])["sha256"]==frame_ref["sha256"],"actual preserved current refs")
    q=qraw["structuredContent"];f=fraw["structuredContent"]
    claim=j(example["claim"]["path"]);identity=claim["action_identity"];provenance=claim["host_provenance"]
    query_node=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=="query")
    selected=ast.Module(body=[copy.deepcopy(query_node)],type_ignores=[])
    inert_payloads={}
    def stub_sdk(value,cache):
        # Metadata-only seam; no filesystem, parser, provider or runtime operation.
        return copy.deepcopy(inert_payloads[value["path"]])
    scope={"need":need,"sdk":stub_sdk}
    exec(compile(ast.fix_missing_locations(selected),str(source)+":query-AST","exec"),scope)
    results=[]
    def run_case(name,change,should_reject):
        qq=copy.deepcopy(q);ff=copy.deepcopy(f);change(qq,ff)
        inert_payloads.clear();inert_payloads[query_ref["path"]]=qq;inert_payloads[frame_ref["path"]]=ff
        try:
            scope["query"](query_ref,frame_ref,{},identity,provenance)
            accepted=True;reason=None
        except (ValueError,KeyError)as error:accepted=False;reason=str(error)
        results.append({"case":name,"accepted":accepted,"required_rejection":should_reject,"rejected_reason":reason,"metadata_only":True})
    run_case("actual_preserved_metadata_positive",lambda q,f:None,False)
    run_case("external_frame_foreign_profile_session",lambda q,f:f.update(profile_sha256="0"*64,session_id="f"*32,pipe_name=r"\\.\pipe\xar_profile_"+("f"*32)),True)
    run_case("external_frame_wrong_full_actor",lambda q,f:f["snapshot_after"]["played_character"].update(character_id=65866),True)
    run_case("external_frame_actor_dead",lambda q,f:f["snapshot_after"]["played_character"].update(alive=False),True)
    run_case("context_actor_and_recipient_dead",lambda q,f:q["result"]["character_interaction_ordinary_context"].update(actor_alive=False,recipient_alive=False),True)
    run_case("context_not_ready_rejected_control",lambda q,f:q["result"]["character_interaction_ordinary_context"].update(ready_to_initiate=False),True)
    need(results[0]["accepted"]and not results[-1]["accepted"],"inert actual-positive/control sanity")
    findings=[x for x in results if x["required_rejection"]and x["accepted"]]
    report={
        "schema":"lyd.r10.assembler-static-inert-independent-review.v1",
        "status":"HELPER_QUERY_METADATA_GATES_INCOMPLETE",
        "recorded_utc":datetime.now(timezone.utc).isoformat(),
        "source":source_ref,"author_index":index_ref,"indexed_payload_count":len(seen),
        "scope":"New helper source/immutable inventory and query AST only; no full validate/assemble, saved raw hash or save AST parser.",
        "actual_query_ast":{"function":"query","line":query_node.lineno,"end_line":query_node.end_lineno,"sha256":sha(ast.dump(query_node,include_attributes=False).encode())},
        "inert_cases":results,"accepted_invalid_metadata_case_count":len(findings),
        "findings":[
            {"kind":"EXTERNAL_FRAME_PROVENANCE_NOT_CHECKED","line":89,"evidence_case":"external_frame_foreign_profile_session","detail":"query() reads external same-frame SDK but only checks query receipt profile/session/pipe at line100."},
            {"kind":"CURRENT_FRAME_ACTOR_NOT_CHECKED","line":90,"evidence_cases":["external_frame_wrong_full_actor","external_frame_actor_dead"],"detail":"query() does not require positive played_character.character_id/alive from the chosen same frame."},
            {"kind":"NATIVE_CONTEXT_ALIVE_FLAGS_NOT_REQUIRED","line":93,"evidence_case":"context_actor_and_recipient_dead","detail":"positive guards omit actor_alive/recipient_alive, so contradictory dead context metadata is accepted."},
            {"kind":"OUTPUT_TARGET_ALIAS_NOT_REJECTED_STATIC","line":129,"detail":"Each target is fresh individually; distinct assembly/flow/evidence paths are not required. This can create argv whose output is already occupied by its input assembly."}
        ],
        "boundary":"These are helper metadata eligibility gaps. Actual source007 provider has not been executed or changed; no real claim, permit or business verification failure is inferred.",
        "qualified_for_ROOT_reuse":False,
        "suggested_minimal_append":"Check external same-frame SDK provenance and positive frame actor/alive/ctx alive; reject output target aliases. Preserve author002 and prior actorKeyError history; no verifier schema/API change.",
        "author_source_has_no_runtime_invocation":True,
        "saved3_and_plain2_static_shapes_present":True,
        "source_record_literal_static_gate_present":True,
        "before_query_and_after_release_context_separation_present":True,
        "credit_flags_false":True,
        "query_and_frame_refs":{"query":query_ref,"frame":frame_ref},
        "reviewer_operations":{"full_validate":0,"assemble":0,"provider":0,"binder":0,"emitter":0,"registry":0,"release":0,"MCP":0,"game":0,"native":0,"pipe":0,"Git":0,"main":0,"save_AST":0,"old_tests":0}
    }
    (O/"REPORT.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (O/Path(__file__).name).write_bytes(Path(__file__).read_bytes())
    rows=[{"path":p.name,"bytes":len(p.read_bytes()),"sha256":sha(p.read_bytes())}for p in sorted(O.iterdir())if p.is_file()]
    (O/"INDEX.json").write_text(json.dumps({"schema":"lyd.external-evidence-index.v1","files":rows},indent=2)+"\n",encoding="utf-8")
    for p in O.iterdir():
        if p.is_file():os.chmod(p,0o444)
    print(json.dumps({"status":report["status"],"accepted_invalid_cases":len(findings),"REPORT":ref(O/"REPORT.json"),"INDEX":ref(O/"INDEX.json")},ensure_ascii=True))
except Exception as error:
    (O/"FAILURE.json").write_text(json.dumps({"status":"INDEPENDENT_REVIEW_FAILURE","reason":str(error),"live_calls":0},indent=2)+"\n",encoding="utf-8")
    raise

