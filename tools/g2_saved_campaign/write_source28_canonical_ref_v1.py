"""Default OFF. Source28 finite canonical writer; Root alone executes."""
from __future__ import annotations
import ast
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import TypedDict
sys.dont_write_bytecode = True
OWN = Path(__file__).resolve()
sys.path.insert(0, str(OWN.parent))
import write_source27_canonical_ref_v1 as W
if W.pin(W.read(Path(W.__file__).resolve(), 32768)) != {
    "bytes": 24449, "sha256": "82833c6426defef8e405332f2ed513d8fe9665599019db3ae14305c874382f5c"}:
    raise RuntimeError("Source28: reviewed Source27 Git primitives changed")
MACHINE = W.MACHINE
PARENT = "4b0f3771b51d65af2cd6d576116535237aac7ef0"
MASTER = "43653fc1d1d5afc1df44faa52d2146b8783c4f9c"
REF = "refs/heads/campaign/robert-v20261020-source28-typed-diagnostics-01"
PREFIX = W.PREFIX
S = PREFIX + "xar_autoplayer/"
U = "ck3_autonomous_player/tests/unit/"
D = "docs/ck3-native-ai/evidence/"
T = "tools/g2_saved_campaign/"
SDK = (
"bridge/native_driver.py", "bridge/mcp_server.py", "bridge/driver.py",
"bridge/exact_clock_failure_diagnostic_v1.py", "bridge/exact_clock_wait_progress_v1.py",
"bridge/tactical_clock_diagnostics_v1.py", "bridge/mcp_tool_result_contract_v1.py",
"reused_sway_opportunity_v1.py", "bridge/player_heir_projection_service_contract_v1.py",
"successor_ui_pending_ledger_v1.py", "bridge/native_loaded_provider_origin_v1.py",
"bridge/native_loaded_provider_origin_io_v1.py", "war_strategic_reserve_v1.py",
"cold_checkpoint_validator.py")
ASSETS = (
U+"test_tactical_clock_diagnostics_v1.py",
U+"fixtures/a11_original_failed_route_window_5279.json",
U+"test_step_postcondition_primitive_identity.py",
U+"test_mcp_tool_result_contract_v1.py", U+"test_source27_master_integration_v1.py",
U+"test_cold_checkpoint_type_contract.py",
T+"patch_complete_tool_result_v1.py", U+"test_player_heir_candidate_component_v1.py",
U+"test_player_heir_fixed_dynasty_projection_v1.py",
D+"m6-sway-closed-ledger-2026-10-20.json", D+"m6-sway-closed-schedule-2026-10-20.json",
D+"player-heir-campaign-attachment-wire-fixture-2026-10-19.json",
T+"patch_observed_halt_close_loop_v1.py", T+"test_observed_halt_close_loop_v1.py")
NAMES = tuple(S+p for p in SDK) + ASSETS
ROWS = {"bytes":376075,"sha256":"27fd27a2024fc95614877c45ba435a4dbcb72ea2c8b7d45c40dd73a12e3fe63b"}
class Plan(TypedDict):
    schema: str
    machine_id: str
    observed_at_utc: str
    review_at_utc: str
    base: str
    master: str
    ref: str
    target_tree: str
    patches: list[W.Patch]
    source_file_count: int
    source_bytes: int
    complete_rows_JSON: W.Pin
    source27_anchor: W.FileRef
    source27_BASE: W.FileRef
    qualifications: list[W.FileRef]
    Git_object_quote: W.Quote

def parse_plan(value: object) -> Plan:
    d = W.keys(value, "schema machine_id observed_at_utc review_at_utc base master ref target_tree patches source_file_count source_bytes complete_rows_JSON source27_anchor source27_BASE qualifications Git_object_quote")
    patches: list[W.Patch] = []
    for v in W.sequence(d["patches"]):
        p = W.keys(v,"relative source_commit input_pin before_pin output_pin")
        patches.append({"relative":W.string(p["relative"]),
            "source_commit":None if p["source_commit"] is None else W.hexstr(p["source_commit"],40),
            "input_pin":W.parse_pin(p["input_pin"]),
            "before_pin":None if p["before_pin"] is None else W.parse_pin(p["before_pin"]),
            "output_pin":W.parse_pin(p["output_pin"])})
    q = W.keys(d["Git_object_quote"],"retained_upper largest_temporary_upper peak_upper object_count")
    return {"schema":W.string(d["schema"]),"machine_id":W.string(d["machine_id"]),
        "observed_at_utc":W.string(d["observed_at_utc"]),"review_at_utc":W.string(d["review_at_utc"]),
        "base":W.hexstr(d["base"],40),"master":W.hexstr(d["master"],40),"ref":W.string(d["ref"]),
        "target_tree":W.hexstr(d["target_tree"],40),"patches":patches,
        "source_file_count":W.integer(d["source_file_count"]),"source_bytes":W.integer(d["source_bytes"]),
        "complete_rows_JSON":W.parse_pin(d["complete_rows_JSON"]),
        "source27_anchor":W.parse_ref(d["source27_anchor"]),"source27_BASE":W.parse_ref(d["source27_BASE"]),
        "qualifications":[W.parse_ref(v) for v in W.sequence(d["qualifications"])],
        "Git_object_quote":{"retained_upper":W.integer(q["retained_upper"]),
            "largest_temporary_upper":W.integer(q["largest_temporary_upper"]),
            "peak_upper":W.integer(q["peak_upper"]),"object_count":W.integer(q["object_count"])}}

def node(raw: bytes, name: str) -> ast.FunctionDef:
    ns = [n for n in ast.walk(ast.parse(raw)) if isinstance(n, ast.FunctionDef) and n.name == name]
    W.require(len(ns)==1 and not ns[0].decorator_list,"unique method: "+name)
    return ns[0]

def part(raw: bytes, n: ast.FunctionDef | ast.ClassDef) -> bytes:
    W.require(n.end_lineno is not None,"AST end missing")
    return b"".join(raw.splitlines(keepends=True)[n.lineno-1:n.end_lineno])

def replace_function(old: bytes, new: bytes, name: str) -> bytes:
    a,b = part(old,node(old,name)),part(new,node(new,name))
    W.require(old.count(a)==1,"unique preimage")
    result = old.replace(a,b)
    W.require(result.replace(b,a)==old,"method inverse")
    return result

def top_diff(old: bytes, new: bytes) -> set[str]:
    def mapping(raw: bytes) -> dict[str,str]:
        result: dict[str,str] = {}
        for i,n in enumerate(ast.parse(raw).body):
            if isinstance(n,(ast.FunctionDef,ast.ClassDef)):
                key=n.name
            elif isinstance(n,(ast.Import,ast.ImportFrom)):
                key="import:"+ast.dump(n)
            elif i==0 and isinstance(n,ast.Expr) and isinstance(n.value,ast.Constant) and isinstance(n.value.value,str):
                key="docstring"
            else:
                key="other:"+ast.dump(n)
            W.require(key not in result,"duplicate AST key")
            result[key]=ast.dump(n,include_attributes=False)
        return result
    a,b=mapping(old),mapping(new)
    return {k for k in a.keys()|b.keys() if a.get(k)!=b.get(k)}

MCP_BEFORE = b'            diagnostic_key = "exact_day_clock_failure_v1"\n            if diagnostic is None:\n                diagnostic = construction_transport_diagnostic(error)\n'
MCP_AFTER = b'            diagnostic_key = "exact_day_clock_failure_v1"\n            if diagnostic is None:\n                from .tactical_clock_diagnostics_v1 import tactical_clock_failure_v1\n\n                tactical_diagnostic = tactical_clock_failure_v1(error)\n                diagnostic = dict(tactical_diagnostic) if tactical_diagnostic is not None else None\n                diagnostic_key = "tactical_clock_failure_v1"\n            if diagnostic is None:\n                diagnostic = construction_transport_diagnostic(error)\n'
INTEGRATION_AFTER = b'''def test_nonleading_strategy_and_cash() -> None:
    path = REPO / "ck3_autonomous_player/tests/fixtures/portable_actual_695.json.gz"
    case = json.loads(gzip.decompress(path.read_bytes()))
    snapshot = case["snapshot"]
    war = snapshot["active_wars"][0]
    assert war["war_id"] == 100663323
    war["player_is_primary_war_leader"] = False
    for enemy in war["enemy_armies"]:
        assert {"siege_province_in_player_subrealm", "move_target_province_id",
                "route_province_ids", "route_read_status"}.issubset(enemy)
        enemy.update(siege_province_in_player_subrealm=True,
                     move_target_province_id=None, route_province_ids=[],
                     route_read_status="complete_empty")
    army = snapshot["player_armies"][0]
    plan = strategy._primary_defender_siege_relief_assessment(
        snapshot, commands=case["history_rows"],
        active_wars=snapshot["active_wars"],
        controlled_armies=[army], pursuit_army=army,
    )
    assert plan is not None
    priority = observe_war_spending_priority_v1(snapshot)
    assert priority["nonleading_realm_siege_construction_deferred_v1"] is True
'''

def project(name: str, old: bytes | None, raw: bytes) -> bytes:
    if name == S+"bridge/native_driver.py":
        W.require(old is not None,"Native parent required")
        if old is None: raise ValueError("Native parent absent")
        result=replace_function(old,raw,"_execute_battle_sentinel_advance")
        anchor=[n for n in ast.parse(result).body if isinstance(n,ast.ImportFrom) and n.module=="driver" and n.level==1]
        W.require(len(anchor)==1,"Native import seam")
        lines=result.splitlines(keepends=True)
        lines.insert(anchor[0].end_lineno or 0,b"from .tactical_clock_diagnostics_v1 import TacticalClockObservationV1\n")
        result=b"".join(lines)
        seam=b"        self._arrange_marriage_query_sequence: int | None = None\n"
        init=b"        self._exact_clock_observation_v1: ClockObservationV1 | None = None\n        self._exact_clock_wait_progress_v1: WaitProgressV1 | None = None\n"
        W.require(result.count(seam)==1,"collector initialization seam")
        result=result.replace(seam,seam+init)
        # Every original AST node except this method and the one new import is preserved.
        actual=ast.parse(result.replace(init,b"")); prior=ast.parse(old)
        for tree in (actual,prior):
            for n in ast.walk(tree):
                if isinstance(n,ast.ClassDef):
                    n.body=[v for v in n.body if not isinstance(v,ast.FunctionDef) or v.name!="_execute_battle_sentinel_advance"]
        actual.body=[n for n in actual.body if not isinstance(n,ast.ImportFrom) or n.module!="tactical_clock_diagnostics_v1"]
        W.require(ast.dump(actual)==ast.dump(prior),"Native unrelated AST changed")
        return result
    if name == S+"bridge/mcp_server.py":
        W.require(old is not None and old.count(MCP_BEFORE)==1,"MCP exact parent seam")
        if old is None: raise ValueError("MCP parent absent")
        result=old.replace(MCP_BEFORE,MCP_AFTER)
        W.require(result.replace(MCP_AFTER,MCP_BEFORE)==old,"MCP inverse")
        return result
    if name == U+"test_source27_master_integration_v1.py":
        removed=b"import test_nonleading_siege_priority_v1 as siege\n"
        W.require(raw.count(removed)==1,"portable integration import")
        a=part(raw,node(raw,"test_nonleading_strategy_and_cash"))
        result=raw.replace(removed,b"").replace(a,INTEGRATION_AFTER)
        W.require(result.replace(INTEGRATION_AFTER,a)==raw.replace(removed,b""),
                  "portable test inverse")
        return result
    if old is not None:
        delta=top_diff(old,raw)
        allowed={
            "bridge/driver.py":{"StepPostconditionError"},
            "bridge/exact_clock_failure_diagnostic_v1.py":{"_encode","exact_clock_failure_diagnostic_v1"},
            "bridge/exact_clock_wait_progress_v1.py":{"docstring","project_wait_progress_v1"},
            "successor_ui_pending_ledger_v1.py":{"owner_source_epoch_v1"},
            "war_strategic_reserve_v1.py":{"observe_procurement_package_budget_v1"},
            "cold_checkpoint_validator.py":{"validate_cold_start_checkpoint_payload_for_pipe"}}
        p=name[len(S):]
        if p in allowed: W.require(delta==allowed[p],"whole-leaf AST whitelist: "+name)
        elif p in {"bridge/native_loaded_provider_origin_v1.py","bridge/native_loaded_provider_origin_io_v1.py",
                   "reused_sway_opportunity_v1.py","bridge/player_heir_projection_service_contract_v1.py"}:
            # Source-bound exact input/output pins below additionally freeze these typed contracts.
            W.require(not any(k.startswith("other:") for k in delta),"unlisted module state changed")
        elif name != U+"test_cold_checkpoint_type_contract.py":
            raise ValueError("unexpected pre-existing asset: "+name)
    return raw

def build_sources(git: W.Git, master: str = MASTER) -> dict[str,bytes]:
    W.require(master==MASTER,"unreviewed master input")
    out: dict[str,bytes]={}
    for name in NAMES:
        code,before=git.run("cat-file","blob",PARENT+":"+name,allowed=(0,128))
        raw=git.get("cat-file","blob",master+":"+name)
        body=project(name,before if code==0 else None,raw)
        if name.endswith(".py"): compile(body,name,"exec",dont_inherit=True)
        W.require(code!=0 or body!=before,"unchanged candidate: "+name)
        out[name]=body
    return out

def compose(plan: Plan, git: W.Git, repo: Path) -> tuple[dict[str,bytes],list[W.Row],list[W.Tree],W.Quote]:
    W.require(plan["schema"]=="xar.source28.canonical-plan/v1" and plan["machine_id"]==MACHINE
        and plan["base"]==PARENT and plan["master"]==MASTER and plan["ref"]==REF,"plan identity")
    W.require(W.date(plan["observed_at_utc"])<=W.utc()<W.date(plan["review_at_utc"]),"plan time")
    W.require(len(plan["patches"])==28 and {p["relative"] for p in plan["patches"]}==set(NAMES),"28 canonical paths")
    W.require((plan["source27_anchor"]["bytes"],plan["source27_anchor"]["sha256"])==
        (9235,"390e368a1101d6ab6ac4c311aba0f453859d51276dc825ed352d6340a3378d38"),"actual Source27 anchor pin")
    W.require((plan["source27_BASE"]["bytes"],plan["source27_BASE"]["sha256"])==
        (398331,"c93cc3e4d4d4996a7787d0f4b095ae67b8e4d145e725f2d7e288c8010b64a8fe"),"actual Source27 BASE pin")
    anchor=W.obj(W.load(W.checked(plan["source27_anchor"])))
    base=W.obj(W.load(W.checked(plan["source27_BASE"])))
    W.require(anchor["commit"]==base["business_source_commit"]==PARENT
        and anchor["status"]=="CANONICAL_REF_CREATED_NOT_DEPLOYED"
        and base["machine_id"]==MACHINE and base["runtime_admitted"] is False,"parent authority")
    rows: dict[str,W.Row]={}
    for v in W.sequence(base["files"]):
        r=W.keys(v,"relative bytes sha256 git_blob_sha1 git_mode")
        row:W.Row={"relative":W.string(r["relative"]),"bytes":W.integer(r["bytes"]),
            "sha256":W.hexstr(r["sha256"],64),"git_blob_sha1":W.hexstr(r["git_blob_sha1"],40),"git_mode":W.string(r["git_mode"])}
        W.require(row["relative"] not in rows,"duplicate parent row")
        rows[row["relative"]]=row
    actual:dict[str,tuple[str,str,int]]={}
    for item in git.get("ls-tree","-r","-l","-z",PARENT,"--",PREFIX).split(b"\0"):
        if item:
            h,pathbytes=item.split(b"\t",1);mode,kind,value,size=h.split()
            W.require(kind==b"blob","ordinary SDK blob required")
            actual[pathbytes.decode()[len(PREFIX):]]=(mode.decode(),value.decode(),int(size))
    W.require(len(rows)==1462 and actual=={n:(r["git_mode"],r["git_blob_sha1"],r["bytes"]) for n,r in rows.items()},
              "complete parent Git inventory")
    out=build_sources(git,plan["master"])
    for p in plan["patches"]:
        name=p["relative"]
        code,raw=git.run("cat-file","blob",PARENT+":"+name,allowed=(0,128))
        W.require(p["source_commit"]==MASTER and p["input_pin"]==W.pin(git.get("cat-file","blob",MASTER+":"+name))
            and p["before_pin"]==(W.pin(raw) if code==0 else None) and p["output_pin"]==W.pin(out[name]),"patch pins: "+name)
    for n,b in out.items():
        if n.startswith(PREFIX):
            relative=n[len(PREFIX):]
            rows[relative]={"relative":relative,**W.pin(b),"git_blob_sha1":W.oid("blob",b),"git_mode":"100644"}
    ordered=[rows[n] for n in sorted(rows)]
    W.require(plan["source_file_count"]==len(rows)==1464 and plan["source_bytes"]==sum(r["bytes"] for r in ordered)==59279032
        and plan["complete_rows_JSON"]==W.pin(W.canonical(ordered))==ROWS,"Source28 complete rows")
    for qualification in plan["qualifications"]: W.checked(qualification)
    W.require(len(plan["qualifications"])>=2,"fresh qualification refs required")
    dirs={""}
    for name in out:
        d=name.rpartition("/")[0]
        while d: dirs.add(d);d=d.rpartition("/")[0]
    ids={n:W.oid("blob",b) for n,b in out.items()}
    trees:list[W.Tree]=[]
    amounts=[W.upper("blob",len(b)) for b in out.values()]
    for d in sorted(dirs,key=lambda s:(s.count("/")+bool(s),s),reverse=True):
        code,raw=git.run("ls-tree","-z",PARENT+(":"+d if d else "^{tree}"),allowed=(0,128))
        e=W.entries(raw) if code==0 else {}
        for name in out:
            parent,_,leaf=name.rpartition("/")
            if parent==d:
                W.require(leaf.encode() not in e or e[leaf.encode()][1]==b"blob","tree replacement forbidden")
                e[leaf.encode()]=(b"100644",b"blob",ids[name])
        for child in dirs:
            if child and child.rpartition("/")[0]==d:
                e[child.rpartition("/")[2].encode()]=(b"040000",b"tree",ids[child])
        body=W.tree_body(e);ids[d]=W.oid("tree",body);trees.append((d,body,ids[d]))
        amounts.append(W.upper("tree",len(body)))
    amounts.append(W.upper("commit",8192))
    q:W.Quote={"retained_upper":sum(amounts),"largest_temporary_upper":max(amounts),
        "peak_upper":sum(amounts)+max(amounts)+65536,"object_count":len(amounts)}
    W.require(ids[""]==plan["target_tree"] and q==plan["Git_object_quote"],"tree or quote differs")
    return out,ordered,trees,q

def execute_v1(*, plan_ref: W.FileRef, card_ref: W.FileRef) -> W.FileRef:
    """Single create-only Root execution. Failure consumes its anchor."""
    plan=parse_plan(W.load(W.checked(plan_ref)))
    card=W.obj(W.load(W.checked(card_ref)))
    W.require(card["schema"]=="xar.storage.Source28-root-canonical-Git.v1"
        and card["owner"]=="Root" and card["machine_id"]==MACHINE
        and card["status"]=="ADMITTED" and card["root_direct_execution_release"] is True,"Root release required")
    W.require(0<=(W.utc()-W.date(card["observed_at_utc"])).total_seconds()<=600,"fresh release")
    limit=min(W.date(card["review_at_utc"]),W.date(plan["review_at_utc"]))
    W.require(W.utc()<limit and W.parse_ref(card["writer"])==W.file_ref(OWN)
        and W.parse_ref(card["plan"])==plan_ref,"writer/plan admission")
    source_ref=W.parse_ref(card["source_admission"])
    source=W.obj(W.load(W.checked(source_ref)))
    W.require(source["machine_id"]==MACHINE,"same-machine source admission")
    repo=OWN.parents[2]
    W.require(subprocess.check_output([sys.executable,"-B",str(repo/"tools/ck3_live_run_id.py"),"machine"]).decode().strip()==MACHINE,"actual machine")
    metadata=Path(W.string(card["metadata_root"])).resolve()
    anchor=Path(W.string(card["future_anchor"])).resolve()
    W.require(anchor==metadata/"SOURCE28-CANONICAL-ANCHOR.json"
        and W.integer(card["anchor_hard_bytes"])==65536,"anchor scope")
    W.no_reparse(metadata)
    W.require(not anchor.exists() and not anchor.is_symlink(),"anchor consumed")
    capacity,budget=W.obj(card["capacity"]),W.obj(card["Git"])
    zfloor,dfloor=W.integer(capacity["Z_free_floor_bytes"]),W.integer(capacity["D_free_floor_bytes"])
    def guard() -> None:
        W.require(W.utc()<limit and shutil.disk_usage(repo).free>=zfloor
            and shutil.disk_usage(metadata.parent).free>=dfloor,"capacity/time lost")
    guard()
    git=W.Git(repo,metadata)
    common_raw=Path(os.fsdecode(git.get("rev-parse","--git-common-dir").strip()))
    common=(common_raw if common_raw.is_absolute() else repo/common_raw).resolve()
    W.no_reparse(common/"objects")
    W.require(common==(repo/".git").resolve()==Path(W.string(budget["root"])).resolve()
        and not (common/"objects/info/alternates").exists()
        and git.get("rev-parse","--show-object-format").strip()==b"sha1","Git object store")
    W.require(git.get("rev-parse",PARENT+"^{commit}").strip().decode()==PARENT,"actual parent")
    W.require(git.run("show-ref","--verify","--quiet",REF,allowed=(0,1))[0]==1
        and git.run("symbolic-ref","--quiet",REF,allowed=(0,1))[0]==1,"ref consumed")
    out,rows,trees,quote=compose(plan,git,repo)
    hard=W.integer(budget["hard_bytes"])
    W.require(W.integer(budget["peak_upper_bytes"])==quote["peak_upper"]<=hard
        and budget["prior_holds_retained"] is True,"Git budget")
    W.require(len(git.get("var","GIT_AUTHOR_IDENT"))+len(git.get("var","GIT_COMMITTER_IDENT"))<4096,"identity cap")
    metadata.mkdir(exist_ok=True)
    record:dict[str,object]={"schema":"xar.source28.canonical-git-anchor/v1","machine_id":MACHINE,
        "status":"RUNNING_OR_UNKNOWN","start_utc":W.utc().isoformat(),"execution_owner":"Root",
        "root_direct_execution_release":True,"parent":PARENT,"ref":REF,"writer":W.file_ref(OWN),
        "source_plan":plan_ref,"capacity_card":card_ref,"source_admission":source_ref,
        "actual_Source27_anchor":plan["source27_anchor"],"actual_Source27_BASE":plan["source27_BASE"],
        "Git_object_quote":quote,"runtime_calls":0,"SDK_export_calls":0,"push_calls":0,
        "index_or_tracked_worktree_mutations":0,"actual_loaded_provider":False,
        "canonical_patch_rows":plan["patches"]}
    charged=0
    with anchor.open("xb") as receipt:
        def save() -> None:
            body=W.canonical(record)+b"\n"
            W.require(len(body)<=65536,"anchor cap")
            receipt.seek(0);receipt.truncate();receipt.write(body);receipt.flush();os.fsync(receipt.fileno())
        def write(kind:str,size:int,*argv:str,data:bytes|None=None) -> bytes:
            nonlocal charged
            charge=W.upper(kind,size)
            W.require(charged+charge<=quote["retained_upper"]
                and charged+charge+quote["largest_temporary_upper"]+65536<=hard,"cumulative Git bound")
            guard();charged+=charge
            return git.get(*argv,data=data)
        save()
        try:
            for name,body in sorted(out.items()):
                W.require(write("blob",len(body),"hash-object","-w","--stdin",data=body).strip().decode()==W.oid("blob",body),"blob readback")
            for _,body,expected in trees:
                e=W.entries_tree(body)
                data=b"".join(m+b" "+k+b" "+h.encode()+b"\t"+n+b"\0" for n,(m,k,h) in sorted(e.items()))
                W.require(write("tree",len(body),"mktree","-z",data=data).strip().decode()==expected,"tree readback")
            tree=plan["target_tree"]
            diff={v.decode() for v in git.get("diff-tree","--no-commit-id","--name-only","-r","-z",PARENT,tree).split(b"\0") if v}
            W.require(diff==set(NAMES),"unowned path")
            for n,b in out.items(): W.require(git.get("cat-file","blob",tree+":"+n)==b,"exact content readback")
            commit=write("commit",8192,"commit-tree",tree,"-p",PARENT,
                data=b"Source28: typed diagnostics and portable Core contracts\n").strip().decode()
            commit_body=git.get("cat-file","commit",commit)
            header=commit_body.split(b"\n\n",1)[0].splitlines()
            W.require(len(commit_body)<=8192 and [v for v in header if v.startswith(b"parent ")]==[b"parent "+PARENT.encode()]
                and [v for v in header if v.startswith(b"tree ")]==[b"tree "+tree.encode()],"commit ancestry")
            record.update(commit=commit,tree=tree,output_pins=[r for r in rows if PREFIX+r["relative"] in out],
                source_file_count=len(rows),source_bytes=sum(r["bytes"] for r in rows),
                complete_rows_JSON=W.pin(W.canonical(rows)),charged_retained_objects_upper=charged)
            save()
            W.require(charged==quote["retained_upper"],"retained accounting")
            W.checked(plan["source27_anchor"]);guard()
            git.get("update-ref","--no-deref",REF,commit,"0"*40)
            W.require(git.get("rev-parse",REF).strip().decode()==commit,"ref readback")
            record.update(status="CANONICAL_REF_CREATED_NOT_DEPLOYED",end_utc=W.utc().isoformat(),future_writes=0)
        except BaseException as error:
            record.update(status="FAILED_OR_UNKNOWN_DO_NOT_RETRY",end_utc=W.utc().isoformat(),
                error={"type":type(error).__name__,"text":str(error)[:1024]})
            save();raise
        save()
    return W.file_ref(anchor)
