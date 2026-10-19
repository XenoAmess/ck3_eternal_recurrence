"""Seal the separately admitted path-identity repair; never write Native output."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

REPO = Path(__file__).resolve().parents[2]
T, E = "tools/g2_saved_campaign/", "docs/ck3-native-ai/evidence/"
R = Path("D:/codex-ck3-demos/2026-10-19-robert-v20261019-native30-camera01")
P = Path("D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/p51-fresh1066-v20261019-prepare01")
CODE = [T+n for n in ("qualify_native30_fixture05_20261020.py", "native30_fixture05_override_20261020.cmake",
    "test_native30_fixture05_paths_20261020.py", "seal_native30_fixture05_source_20261020.py")]
PLAN = E+"native30-fixture05-path-identity-plan-2026-10-20.json"
READY = E+"native30-fixture05-path-identity-source-ready-2026-10-20.json"
FIXTURE = "ck3_autonomous_player/native_bridge/src/camera_tracking_v1_test.cpp"

def pin(path):
    path = Path(path)
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}

def rp(name): return {**pin(REPO/name), "path": name}
def encode(value): return (json.dumps(value, ensure_ascii=False, indent=2)+"\n").encode()
def exclusive(path, data):
    with Path(path).open("xb") as stream: stream.write(data)

def seal():
    if any((REPO/name).exists() for name in (PLAN, READY)): raise RuntimeError("never overwrite records")
    machine = subprocess.run([sys.executable, "-B", "tools/ck3_live_run_id.py", "machine"], cwd=REPO,
                             check=True, capture_output=True, text=True).stdout.strip()
    if machine != "xenoamess-full-tower-eb9d2c1186": raise RuntimeError("wrong machine")
    old = json.loads((REPO/(E+"native30-fixture04-nopdb-plan-2026-10-19.json")).read_bytes())
    helpers = dict(old["helper_pins"])
    del helpers[T+"native30_fixture04_override_20261019.cmake"]
    helpers[CODE[1]] = rp(CODE[1])["sha256"]
    prior = [p for p in old["prior_pins"] if "native30-build-owner03" not in p["path"]]
    prior += [pin(R/name) for name in ("attempt04/RESULT.json", "attempt04/FILES-CLOSED.json",
        "attempt04/fixture-only-override.cmake", "build/native30-fixture04/camera_tracking_v1_test.cpp")]
    prior += [pin(P/"native30-build-owner04/owner-spec"/name) for name in ("CLOSED.json", "argv-difference02.json")]
    now = datetime.now(timezone.utc).isoformat()
    spec = importlib.util.spec_from_file_location("fixture05_sealed", REPO/CODE[0])
    q = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(q)
    if q.ATTEMPT.exists() or q.COPY.parent.exists(): raise RuntimeError("new05 roots must remain absent")
    g = q.load_module("fixture05_guard", REPO/(T+"native30_resume_guard_20261019.py"))
    observed = []
    for path in (R/"attempt02/selected-fileapi-graph.json", R/"build/compile_commands.json"):
        if path.stat().st_size > 16*1024**2: raise RuntimeError("finite named compile metadata bound")
        value = json.loads(path.read_bytes())
        rows = value["selected_compile_rows"] if isinstance(value, dict) else value
        selected = [r for r in rows if Path(r["file"]).name == "camera_tracking_v1_test.cpp"]
        if len(selected) != 1: raise RuntimeError("one actual fixture metadata row")
        observed.append(selected[0])
    if q.normalize_fixture_row(observed[0], g, R/"source"/FIXTURE) != q.normalize_fixture_row(observed[1], g, q.PRIOR_COPY):
        raise RuntimeError("actual closed04 path-only pair is not equivalent")
    plan = {"schema": "native30-fixture05-path-identity-plan-v1", "machine_id": machine, "observed_at_utc": now,
        "status": "SOURCE_READY_NOT_EXECUTION_ADMISSION", "root": str(R), "attempt_root": str(R/"attempt05"),
        "producer": rp(CODE[0]), "files": CODE+[PLAN, READY], "helper_pins": helpers, "prior_pins": prior,
        "inventory": old["inventory"], "binding": old["binding"], "overlay": CODE[1],
        "04_failure": {"status": "FAILED_PRESERVED", "error": "fixture flags/includes/tool changed beyond source/object paths",
            "configure_root_exit": 0, "owned_active_after": 0, "fixture_builds": 0, "production_recompiled": False,
            "unregistered_at_utc": "2026-10-19T18:56:20.067052+00:00", "Task": "XARG2ManagedOwner-2fd22e9a31ef43c29407323d7f8b5cfa",
            "actual_projection": pin(P/"native30-build-owner04/owner-spec/argv-difference02.json"),
            "cause": "Both row.output are absolute and both /Fo command tokens relative;04 normalized string spellings instead of resolving the token under row.directory. Exactly one token differed; other27 were identical."},
        "scope": ["No C++ or Native source change. Same5355 Git704 source and977 clean production objects, DLL/lib/map are immutable inputs.",
            "Only newattempt05 labels and exact fixture path semantics; canonicalize source/Fo/output with the actual row.directory, require exact build, known source and its exact target/source object. Exactly one nonempty Fo and one source; all other tokens remain byte-for-byte ordered.",
            "Current04 is a real root0 configured tree but FAILED qualification. Validate original02→current04 with the same strict graphdelta before anynewwrite; lease fixedCOPY04/overlay04/RESULT04 readonly and preserve all04 evidence. Only the exact expected fixture source/object transition is allowed.",
            "The immutable original02 graph already contains its historical link_contract. Original fixture FileAPI may have been superseded; that one historical target is validated via its pinned graph and full actual link/artifact equality. Other11 original FileAPI files remain exact pinned inputs.",
            "Reconfigure via one new05 deferred fixture overlay preserving original02 two-macro overlay; original02→new05 strict delta. Other production/8fixture argv, source sets, all12 link/archive/artifact contracts unchanged. Explicit production Ninja -n must say no work."],
        "unchanged_noPDB_contract": rp(E+"native30-fixture04-nopdb-plan-2026-10-19.json"),
        "original_source_and_success": {"Native_commit": old["original_source_and_success"]["Native_commit"],
            "frozen_files": 5355, "production_objects": 977, "immutable": [str(R/n) for n in ("source", "evidence", "attempt02")]},
        "pipeline": old["pipeline"][4:],
        "budget": {**old["budget"], "prior_retained_allocation_bytes": 662128560},
        "qualification": "Focused path/graph/software tests only; no05 configure/compiler/Defender/fixture execution or Game qualification. Nine actual namedfixtures plus unchanged final artifacts/deps/exports/archive/map and all exactDefender readbacks remain mandatory.",
        "execution_argv_after_commit_card_Rootrelease": ["py", "-B", CODE[0], "--plan", PLAN, "--admission", "<new card>",
            "--admission-sha256", "<exact SHA>", "--execute"],
        "new_Task": {**old["new_Task"], "owner_spec": str(P/"native30-build-owner05/owner-spec")},
        "source_commit": "704bdd3362bdc282ed5f5f8cf31fd3f50b90d747", "new_reservation_bytes": 0,
        "Native_Task_Game_started": False, "future_source_writes_after_seal": 0}
    plan["original_source_and_success"]["new_copy"] = str(R/"build/native30-fixture05/camera_tracking_v1_test.cpp")
    plan["original_source_and_success"]["immutable"].extend([str(R/"attempt04"), str(R/"build/native30-fixture04")])
    plan["pipeline"] = [s.replace("attempt04", "attempt05").replace("under04", "under05") for s in plan["pipeline"]]
    plan["new_Task"]["contract"] = plan["new_Task"]["contract"].replace("owner04", "owner05")
    plan_data = encode(plan)
    pp = {"path": PLAN, "bytes": len(plan_data), "sha256": hashlib.sha256(plan_data).hexdigest()}
    pins = [rp(name) for name in CODE]
    ready = {"schema": "native30-fixture05-source-ready-v1", "machine_id": machine, "observed_at_utc": now,
        "identity_source": "fresh tools/ck3_live_run_id.py machine", "status": "SOURCE_READY_CPP_NOTRUN", "plan": pp,
        "sources": pins, "tests": {"command": "py -B -m unittest tools.g2_saved_campaign.test_native30_fixture05_paths_20261020 -q",
            "actual": sys.argv[2], "scope": "Only new path/graph negative tests and retained-guard AST checks; no C++ or real auxiliary cleanup credit."},
        "actual_closed04_path_pair_software_check": "PASS: same newly strict normalizer on the two exact fixture rows from named original02 graph and current compile_commands; no configuration/build executed",
        "04_failed_preserved": pin(R/"attempt04/RESULT.json"), "source64KiB_cap": 65536,
        "new_CPP_changes": 0, "old_sources_modified": 0, "external_Native_Task_writes": 0,
        "future_writes": 0, "allocated_bytes": None, "physical_credit_bytes": 0}
    data = encode(ready)
    gross = sum(p["bytes"] for p in pins)+len(plan_data)+len(data)
    if gross > 65536: raise RuntimeError("new64KiB source bound beforewrites: "+str(gross))
    exclusive(REPO/PLAN, plan_data)
    exclusive(REPO/READY, data)
    print(json.dumps({"plan": pp, "ready": rp(READY), "gross_bytes": gross, "new_files": 6, "future_writes": 0}))

if __name__ == "__main__":
    if sys.argv[1] == "--seal": seal()
    else: raise SystemExit("--seal <actual focused test result>")
