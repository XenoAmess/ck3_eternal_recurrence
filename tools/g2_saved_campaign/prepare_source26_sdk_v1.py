"""RAM-only Source26 composition over the actual immutable Source25 tree.

The origin recipe names one reviewed pure producer and its exact inputs. Host
outputs stay outside the business SDK. No exporter, runtime or Git writer here.
"""
from __future__ import annotations
import ast
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
import prepare_source25_sdk_v1 as common
REPO, MACHINE, PREFIX = common.REPO, common.MACHINE, common.PREFIX
BASE = "9b791aae9bb1314162aa5cab923e6cca2892e6d8"
BASE_REF = "refs/heads/campaign/robert-v20261019-source25-a03-cold-01"
ANCHOR = REPO / "_runtime/source25-integration16/SOURCE25-CANONICAL-ANCHOR.json"
ANCHOR_PIN = (6848, "a1acba86ae4f31f7716ff6fb0c190102ff97678d19dbe97bb68d3a361ccf48f0")
B = Path("D:/codex-ck3-demos/2026-10-19-robert-v20261019-storage01")
O = Path("D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/p51-fresh1066-v20261019-prepare01/c23-source23-native30-cold100")
BASE_MANIFEST = O / "immutable-source-export-a03/SOURCE-FREEZE.json"
BASE_MANIFEST_PIN = (1838976, "18886f8fd6c1ad76c29353ce922a5df4412a54adcfae85ed928a5ba5a714ac51")
BASE_ROWS_PIN = (375121, "8ad5ba889feef72bf22cb18746894c44dd4d98cdc8d2904427efa3a474e0ac5a")
C = REPO / "tools/g2_saved_campaign/candidates"
M6 = C / "m6_reused_sway_opportunity_20261020"
M7 = C / "m7_root_projection_contract_20261020"
CASH = C / "nonleading_realm_defence_cash_20261020"
PERF = C / "exact_day_private_progress_wait_20261020"
LEDGER = "xar_autoplayer/successor_ui_pending_ledger_v1.py"
ORIGIN = {"xar_autoplayer/bridge/native_loaded_provider_origin_io_v1.py",
          "xar_autoplayer/bridge/native_loaded_provider_origin_v1.py"}
EXTRA = ("ordinary_sway_schedule_v1.py", "sway_formal_consumer.py", "reused_sway_opportunity_v1.py",
    "bridge/player_heir_projection_service_contract_v1.py", "war_reinforcement_tradeoff_v1.py",
    "construction_formal_consumer.py", "nonleading_player_realm_siege_v1.py", "war_strategic_reserve_v1.py")


def require(ok, why):
    if not ok: raise ValueError("Source26: " + why)


pin, canonical, check = common.pin, common.canonical, common.check
file_pin, safe_relative, git_read = common.file_pin, common.safe_relative, common.git_read


def load(name, path, expected):
    check(Path(path).read_bytes(), expected, name)
    spec = importlib.util.spec_from_file_location("source26_" + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def checked_ref(ref):
    path = Path(ref["path"])
    value = file_pin(path)
    require(all(value[k] == ref[k] for k in ("bytes", "sha256")), "reviewed source reference differs")
    return path


def compose(origin_recipe):
    require(sys.dont_write_bytecode, "run -B")
    check(Path(common.__file__).read_bytes(), (17499,"cada65eb23800a8aa746e265eb6795b9718b8f56ed16d2ca592a90c7c8bec063"), "frozen Source25 composition helpers")
    anchor_raw = check(ANCHOR.read_bytes(), ANCHOR_PIN, "actual Source25 anchor")
    anchor = json.loads(anchor_raw)
    require(anchor["machine_id"] == MACHINE and anchor["commit"] == BASE and anchor["future_writes"] == 0
            and anchor["source_file_count"] == 1460 and anchor["source_bytes"] == 59234989,
            "actual Source25 closure differs")
    require(git_read("rev-parse", BASE_REF).decode().strip() == BASE, "actual parent ref differs")
    manifest_raw = check(BASE_MANIFEST.read_bytes(), BASE_MANIFEST_PIN, "Source25 rich inventory")
    manifest = json.loads(manifest_raw)
    require(manifest["machine_id"] == MACHINE and manifest["business_source_commit"] == BASE,
            "same-machine canonical manifest required")
    base_rows = sorted(({k:r[k] for k in ("relative", "bytes", "sha256", "git_blob_sha1", "git_mode")}
                        for r in manifest["files"]), key=lambda r:r["relative"])
    check(canonical(base_rows), BASE_ROWS_PIN, "complete Source25 rows")
    common.verify_tree(BASE, base_rows)
    indexed = {r["relative"]:r for r in base_rows}
    def read(name):
        safe_relative(name)
        row = indexed[name]
        return check(git_read("cat-file", "blob", BASE + ":" + PREFIX + name),
                     (row["bytes"], row["sha256"]), "canonical preimage " + name)
    refs = []
    def frozen(path, size, sha):
        raw = check(path.read_bytes(), (size, sha), str(path)); refs.append(file_pin(path)); return raw
    m6 = load("m6", M6/"transform.py", (3852,"696404ff2ae37faaceefadba036c1f7f9ed00ad02694bde18deec5639660e2a3"))
    refs.append(file_pin(M6/"transform.py"))
    helper = frozen(M6/"reused_sway_opportunity_v1.py",5313,"1aaf008844ded420670a14d1bd7657a6b55ab062c9ee8285591ed6ec66cfe125")
    out = {k[len(PREFIX):]:v for k,v in m6.transform_sources(
        {m6.SCHEDULE:read(m6.SCHEDULE[len(PREFIX):]),m6.FORMAL:read(m6.FORMAL[len(PREFIX):])}, helper).items()}
    frozen(M6/"SOURCE-QUALIFICATION.json",7406,"614c9d478799c360f7a7a6485c275e61d42bef0bfa74eef6fe8932511bcf4888")
    m7 = load("m7",M7/"transform_service_v1.py",(2062,"59bd644957c49289e20e2e56810e287b6c279dbeb0839cbb79f8729c0bb62aa5"))
    refs.append(file_pin(M7/"transform_service_v1.py"))
    out["xar_autoplayer/bridge/service.py"] = m7.transform_service_v1(read("xar_autoplayer/bridge/service.py").decode()).encode()
    out[m7.HELPER_TARGET] = frozen(M7/"player_heir_projection_service_contract_v1.py",6289,"b9ce86b1a220e25f448bddda97cc1993c9d7ebd9f3e7b7e40ec559133d3a66db")
    frozen(M7/"CORE-HOUSE-QUALIFIED.json",3561,"4132fdb2080f33153327cfe9a9fbf05c028dd6b970a4ed96f8a48c26e16d6cc6")
    frozen(B/"G2-PARALLEL-QUALIFICATION0630-01/m7/ROOT-ALIVE-QUALIFIED.json",1704,"571027ffeaeba158c56546122f55de7d82cb325be85ed9878d85ba8f190ac7bf")
    frozen(M7/"SOURCE-CLOSURE-REVIEW.json",4789,"db27fb599cbef654965741f9f1ab6313e9fb6a4a40a7cb0b1c695427616b79b2")
    cash = load("cash",CASH/"transform.py",(5095,"c0caaacc4f9d2e161faef178b430a1626ab5ccf814f198abc2a80448a5a6ef48"))
    refs.append(file_pin(CASH/"transform.py"))
    for name in cash.BASE: out[name] = cash.transform(read(name),name,stage="procurement")
    scope = load("scope",CASH/"package_scope_followup.py",(10894,"f81aafd2c8933581482080285bdd915d2b3dc4a104c92ab19f427122160ae36e"))
    refs.append(file_pin(CASH/"package_scope_followup.py"))
    reserve = "xar_autoplayer/war_strategic_reserve_v1.py"
    out[reserve] = scope.transform_package(read(reserve))
    frozen(CASH/"SOURCE-READY.json",6466,"f02b219999820c1e0d5fd13b5b55550d3cdd45452d1dd6250aa1f10a0155fc5f")
    frozen(CASH/"SOURCE-PACKAGE-FOLLOWUP.json",3792,"415296d526c6be35ceec5de4f578e4595ec4816c3a900948779454cea9da617b")
    # Its imports only declare the prior read-only candidate/qualifier; no main runs.
    for name,size,sha in (("prepare_candidate.py",3405,"d468220882ebe2b898b95f4021d37be09e8edadb737893124ca8a8d8df314ebb"),
                         ("qualify_candidate.py",17962,"3091c1d78974da9817722458f048d8f7dec6b5c81ff5f1f17acc244431146951")):
        frozen(PERF/name,size,sha)
        loaded = sys.modules.get(name[:-3])
        require(loaded is None or Path(loaded.__file__).resolve() == (PERF/name).resolve(), "foreign cached LF dependency")
    sys.path.insert(0,str(PERF))
    try: perf = load("lf",PERF/"encode_lf_once_qualify.py",(8165,"b9916962666080a4d2d2530b1819a8ad69e2b4fd7a9d506a75616a4edc3c2fa2"))
    finally: sys.path.remove(str(PERF))
    refs.append(file_pin(PERF/"encode_lf_once_qualify.py"))
    driver = "xar_autoplayer/bridge/native_driver.py"
    out[driver] = perf.compose(read(driver))
    frozen(B/"G2-PARALLEL-QUALIFICATION0630-01/performance/ENCODE-LF-ONCE-QUALIFICATION.json",1034,"6cb984fa4c4580a31f8b0da7f5e1cd33fe58e56e9c0a49ecbea874933215f2cc")
    # Root's frozen recipe binds SDK preimages to Git, host preimages to exact
    # held source refs, and the callable itself to a reviewed immutable producer.
    require(type(origin_recipe) is dict and origin_recipe["startup_seconds"] == 120,
            "explicit reviewed startup120 recipe required")
    ref = origin_recipe["producer"]; path = checked_ref(ref)
    origin = load("origin",path,(ref["bytes"],ref["sha256"]))
    inputs = {}
    for key, item in origin_recipe["inputs"].items():
        if item["kind"] == "canonical_sdk": inputs[key] = read(item["relative"])
        else:
            require(item["kind"] == "pinned_host_py" and Path(item["path"]).suffix == ".py" and item["bytes"] <= 524288,
                    "only exact held Python host source may accompany SDK inputs")
            inputs[key] = checked_ref(item).read_bytes()
    function = origin_recipe["function"]
    require(function in ("compose_sdk", "transform_sources", "compose"), "unreviewed origin entry point")
    produced = getattr(origin,function)(inputs,**origin_recipe.get("kwargs",{}))
    require(type(produced) is dict and set(origin_recipe["sdk_outputs"]) == ORIGIN, "origin SDK output shape differs")
    for name,key in origin_recipe["sdk_outputs"].items():
        require(type(produced[key]) is bytes and name not in out, "origin output collision/type")
        out[name] = produced[key]
    require(set(produced) == set(origin_recipe["declared_outputs"]), "unowned origin output")
    host_pins = {k:pin(v) for k,v in produced.items() if k not in origin_recipe["sdk_outputs"].values()}
    refs.append(file_pin(path)); checked_ref(origin_recipe["qualification"])
    refs.append(origin_recipe["qualification"])
    # One and only one ledger writer: append to the original tuple, preserving
    # all 23 names/order and every other original ledger byte/function.
    original = read(LEDGER).decode(); lines = original.splitlines(True)
    fn = next(n for n in ast.parse(original).body if isinstance(n,ast.FunctionDef) and n.name == "owner_source_epoch_v1")
    node = next(n for n in fn.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id == "names" for t in n.targets))
    names = ast.literal_eval(node.value)
    require(len(names) == 23 and not set(names)&set(EXTRA), "exact old23 plus new8 required")
    block = "".join(lines[node.lineno-1:node.end_lineno]); end = block.rfind(")")
    changed = block[:end] + ",\n" + ",\n".join("             " + json.dumps(n) for n in EXTRA) + ")" + block[end+1:]
    ledger = original.replace(block,changed,1)
    require(ledger.replace(changed,block,1) == original, "entire ledger inverse differs")
    out[LEDGER] = ledger.encode()
    require(pin(out[LEDGER]) == {"bytes":22343,"sha256":"4701b97da44e01704c459c1b98fe8709f81197b0a0a5037469770960817c6e93"}, "single final ledger differs")
    expected = {"xar_autoplayer/ordinary_sway_schedule_v1.py":(10142,"f61d179fccbcb1b656ebafa9b68a04ed9045c0b0b3e1a61fe11ca39361ad3cd4"),
        "xar_autoplayer/sway_formal_consumer.py":(35251,"99ea0b435442d9b842ebc40cc19601ea03c92a112cb2a8f257550de8ec2d9ad8"),
        driver:(1644166,"30d182d0a4e9ef0df1cd8542075c275574699dea38308f9da4021bd588abd159"),
        "xar_autoplayer/bridge/service.py":(879793,"d532887e030750ba9ef52d6a580a255e9f21f11758dd87eded113bad9a4e3aa4"),
        "xar_autoplayer/war_reinforcement_tradeoff_v1.py":(21099,"d9f32c208fa47a0b2007f4a5194462a9929fac2f636c8e58ba25a8cffb1a089c"),
        "xar_autoplayer/construction_formal_consumer.py":(40508,"90ff70251640abd243bea7a0194f057ab80b719899569e4ca3feaf53c29b9e3e"),
        reserve:(36301,"c9f65308fd29fa57c960a3e942255158c9f3eac2bdfcfce9d4d8b1268b5e98d6")}
    for name,p in expected.items(): check(out[name],p,"qualified output " + name)
    require(len(out) == 12 and all(type(v) is bytes for v in out.values()), "twelve SDK outputs required")
    rows = dict(indexed); delta = []
    for name,value in sorted(out.items()):
        safe_relative(name); compile(value,name,"exec",dont_inherit=True)
        before = rows.get(name)
        row = {"relative":name,**pin(value),"git_blob_sha1":hashlib.sha1(b"blob "+str(len(value)).encode()+b"\0"+value).hexdigest(),
               "git_mode":before["git_mode"] if before else "100644"}
        rows[name] = row; delta.append({"relative":name,"before":before,"after":row,"net_bytes":len(value)-(before["bytes"] if before else 0)})
    stable = [rows[n] for n in sorted(rows)]
    require(len(stable) == len({n.casefold() for n in rows}) == 1462 and sum(r["before"] is None for r in delta) == 2,
            "complete row closure differs")
    epoch_inputs = {n:rows["xar_autoplayer/"+n]["sha256"] for n in (*names,*EXTRA)}
    report = {"schema":"xar.source26.unified-sdk/v1","machine_id":MACHINE,"observed_at_utc":datetime.now(timezone.utc).isoformat(),
        "status":"RAM_SOURCE26_NOT_CANONICAL_NOT_EXPORTED_NOT_RUNTIME_ADOPTED",
        "base":{"commit":BASE,"anchor":file_pin(ANCHOR),"manifest":file_pin(BASE_MANIFEST),"rows":pin(canonical(base_rows))},
        "output":{"files":len(stable),"source_bytes":sum(r["bytes"] for r in stable),"canonical_rows_JSON":pin(canonical(stable))},
        "delta":delta,"producer_and_qualification_refs":refs,"origin_recipe":origin_recipe,"runtime_host_outputs":host_pins,
        "epoch_names":list((*names,*EXTRA)),"epoch_inputs":epoch_inputs,"source_epoch_detached_model":hashlib.sha256(canonical(epoch_inputs)).hexdigest(),
        "source_epoch_actual_filesystem_authority":False,"single_epoch_writer":True,"old23_order_preserved":True,
        "all_package_outputs_in_complete_rows":True,"old_qualifications_reused_not_rerun":True,"actual_H":"unknown",
        "actual_Native30_loaded":False,"new_Gameplay_or_performance_credit":0,"Git_export_runtime_Task_Game_Native_RPC_calls":0}
    return out,stable,report


def quote(outputs, rows):
    objects = [{"kind":"blob","path":n,"payload_bytes":len(v),"upper":common.object_upper("blob",len(v))} for n,v in sorted(outputs.items())]
    directories = {""}
    for name in outputs:
        parent = (PREFIX+name).rpartition("/")[0]
        while parent: directories.add(parent); parent = parent.rpartition("/")[0]
    trees = {}
    for directory in sorted(directories):
        entries = common.tree_entries(BASE+(":"+directory if directory else "^{tree}"))
        for name in outputs:
            parent,_,leaf = (PREFIX+name).rpartition("/")
            if parent == directory: entries[leaf.encode()] = (b"100644",b"blob",b"0"*40)
        size = sum(len(mode.lstrip(b"0"))+1+len(name)+1+20 for name,(mode,kind,child) in entries.items())
        trees[directory or "<root>"] = size
        objects.append({"kind":"tree","path":directory or "<root>","payload_bytes":size,"upper":common.object_upper("tree",size)})
    objects.append({"kind":"commit","payload_cap":8192,"upper":common.object_upper("commit",8192)})
    retained = sum(r["upper"] for r in objects); largest = max(r["upper"] for r in objects)
    data = 2*sum(((len(v)+4095)//4096)*4096 for v in outputs.values())
    return {"Git":{"objects":objects,"tree_payloads":trees,"retained_upper":retained,"largest_temporary_upper":largest,
            "refs_dirs_locks_reserve":65536,"peak_upper":retained+largest+65536,"compression_or_dedup_credit":0},
        "dual_export_from_Source25":{"files_each":len(rows),"changed_paths":len(outputs),"new_unique_files":2*len(outputs),
            "new_data_cluster_upper":data,"metadata_and_FS_reserve":4194304,"peak_upper":data+4194304,
            "unchanged_rows_hardlink_reuse":len(rows)-len(outputs),"base_freeze":str(O/"ROOT-FINAL-SDK-SOURCE25-BASE.json")}}
