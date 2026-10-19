"""Author/seal the configured-tree qualification repair; no Native output writes."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time

REPO = Path(__file__).resolve().parents[2]
T, E = "tools/g2_saved_campaign/", "docs/ck3-native-ai/evidence/"
R = Path("D:/codex-ck3-demos/2026-10-19-robert-v20261019-native30-camera01")
P = Path("D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/p51-fresh1066-v20261019-prepare01")
CODE = [T+n for n in ("qualify_native30_fixture06_20261020.py", "test_native30_fixture06_current_graph_20261020.py",
                      "seal_native30_fixture06_source_20261020.py")]
HISTORY = [E+name+"-2026-10-20.json" for name in ("native30-fixture06-current-config-plan",
    "native30-fixture06-current-config-source-ready", "native30-fixture06-actual-readonly-preflight")]
PLAN = E+"native30-fixture06-current-config-plan02-2026-10-20.json"
READY = E+"native30-fixture06-current-config-source-ready02-2026-10-20.json"
PROOF = E+"native30-fixture06-actual-readonly-preflight02-2026-10-20.json"

def pin(path):
    path = Path(path)
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}

def rp(name): return {**pin(REPO/name), "path": name}
def encode(value): return (json.dumps(value, ensure_ascii=False, indent=2)+"\n").encode()
def exclusive(path, data):
    with Path(path).open("xb") as stream: stream.write(data)

def author():
    path = REPO/(T+"qualify_native30_fixture05_20261020.py")
    if pin(path)["sha256"] != "e9693fa104cbc845816477cbba0aa46c9a7234de4914f7cbddcebcf44611a1bb":
        raise RuntimeError("frozen05 source changed")
    source = path.read_text().replace("attempt05", "attempt06").replace("fixture05", "fixture06")
    source = source.replace('COPY = ROOT / "build/native30-fixture06/camera_tracking_v1_test.cpp"',
                            'COPY = ROOT / "build/native30-fixture04/camera_tracking_v1_test.cpp"')
    source = source.replace('str(PRIOR_COPY.resolve()): "native30-fixture04", str(COPY.resolve()): "native30-fixture06"',
                            'str(COPY.resolve()): "native30-fixture04"')
    source = source.replace('not ATTEMPT.exists() and not COPY.parent.exists(), "new attempt/copy must be absent; no replay"',
                            'not ATTEMPT.exists() and COPY.is_file(), "new attempt absent; fixed configured04 source required"')
    start = source.index('        for relative, expected in repair["helper_pins"].items():')
    end = source.index('        ATTEMPT.mkdir(exist_ok=False)', start)
    prefix = source[start:end]
    prefix = prefix.replace('        card = base.load(args.admission)\n        validate_card(base, card, repair, args)\n',
        '        if args is not None: validate_card(base, card, repair, args)\n')
    begin = prefix.index('        for target in before["targets"]:')
    stop = prefix.index('        require(bool(before.get("link_contract"))', begin)
    prefix = prefix[:begin]+prefix[stop:]
    prefix = prefix.replace('        for target in before["targets"]:', '        for target in current["targets"]:')
    prefix = prefix.replace('        protected = [base.pin(path)', '''        for target in current["targets"]:
            path = target["fileapi"]["path"]
            handles.append(win32file.CreateFile(str(path), 0x80000000, 1, None, 3, 0x80, None))
            require(base.digest(path) == target["fileapi"]["sha256"], "current FileAPI changed during preflight")
        protected = [base.pin(path)''')
    names = ("base", "resume", "guard_module", "auxiliary", "source", "build", "before", "current", "old_plan",
             "rows", "fixed", "tools", "binding", "budget", "production", "pinned_outputs", "source_identities",
             "protected", "flags", "known_not_generated", "prior_configuration")
    function = 'def preflight(repair, handles, card, args=None):\n    """All read-only gates before the first Native output write; caller owns leases."""\n    import win32file\n'
    function += "\n".join(line[4:] for line in prefix.splitlines())+"\n"
    function += '    return {\n'+"".join('        "'+n+'": '+n+',\n' for n in names)+'    }\n\n'
    replacement = '''        card = json.loads(args.admission.read_bytes())
        checked = preflight(repair, handles, card, args)
'''+"".join('        '+n+' = checked["'+n+'"]\n' for n in names)
    source = source[:start]+replacement+source[end:]
    insertion = source.index('def execute(args):')
    source = source[:insertion]+function+source[insertion:]
    begin = source.index('            COPY.parent.mkdir(exist_ok=False)')
    stop = source.index('            common =', begin)
    source = source[:begin]+source[stop:]
    begin = source.index('            stage = ATTEMPT / "configure"')
    stop = source.index('            dry = ATTEMPT / "production-no-work.log"', begin)
    source = source[:begin]+'''            after = current
            base.write(ATTEMPT / "current-configured-graph.json", after)
            base.write(ATTEMPT / "prior-current-graph-delta.json", prior_configuration)
            require(resume.cache_flags(build / "CMakeCache.txt") == flags, "XAR/options/Release changed")
'''+source[stop:]
    source = source.replace('            "production_recompiled": False, "DLL_loaded": False,',
        '            "production_recompiled": False, "DLL_loaded": False, "configuration_reused_from_attempt04": True,')
    exclusive(REPO/CODE[0], source.encode())
    print(json.dumps({"new_source": rp(CODE[0]), "Native_Task_calls": 0}))

def seal():
    if any((REPO/name).exists() for name in (PLAN, READY, PROOF)): raise RuntimeError("never overwrite records")
    machine = subprocess.run([sys.executable, "-B", "tools/ck3_live_run_id.py", "machine"], cwd=REPO,
        check=True, capture_output=True, text=True).stdout.strip()
    if machine != "xenoamess-full-tower-eb9d2c1186": raise RuntimeError("wrong machine")
    old = json.loads((REPO/(E+"native30-fixture05-path-identity-plan-2026-10-20.json")).read_bytes())
    helpers = dict(old["helper_pins"])
    del helpers[T+"native30_fixture05_override_20261020.cmake"]
    prior = list(old["prior_pins"])
    prior += [pin(P/"native30-build-owner05/owner-spec"/name) for name in ("CLOSED.json", "stage.stderr.log")]
    plan = {"schema": "native30-fixture06-current-config-plan-v1", "machine_id": machine,
        "observed_at_utc": datetime.now(timezone.utc).isoformat(), "status": "SOURCE_READY_NOT_EXECUTION_ADMISSION",
        "root": str(R), "attempt_root": str(R/"attempt06"), "producer": rp(CODE[0]),
        "files": CODE+HISTORY+[PLAN, PROOF, READY], "helper_pins": helpers, "prior_pins": prior,
        "inventory": old["inventory"], "binding": old["binding"], "budget": old["budget"],
        "source_commit": old["source_commit"], "new_reservation_bytes": 0,
        "old_failure_preserved": {"04": old["04_failure"], "05": "FAILED before mkdir/configure/fixture: obsolete original FileAPI basename; stage1/bootstrap1/Job0, exactunregister19:14:21.443104Z, Native attempt05 absent"},
        "scope": ["No configure, new generated fixture or override. Use actual04 root0 configured tree and fixed COPY04/overlay04. Only newattempt06 evidence/TEMP; no production rebuild or relink.",
            "Historical authority is the pinned original02 graph995 selected rows/12 semantic link contracts, exact production output provenance and closed metadata. Do not reopen obsolete FileAPI reply names from that historical graph.",
            "Fresh base.graph is the only current FileAPI/targets/artifacts authority. Full source/include/system/mandatory/macros/assertions graph validation and strict original02→current04 all995 ordered argv/all12 link/artifact equality remain; only the admitted camera fixture source/object paths normalize.",
            "Same exact5355 Git704 blobs and977 production objects plus DLL/lib/map SHA/FileID/read-only/no-delete leases; current FileAPI files leased too. Failed04 fixed source,overlay,RESULT protected; failed05 metadata preserved. Input unknown or drift fails closed.",
            "One shared preflight function is run to the first Native write boundary both during source qualification and final execution. Source preflight uses the still-valid old05 card for capacity observation only; it does not admit06 or bypass final newcard/commit validation.",
            "Actual execution first Ninja production -n must report no work, then all9 named fixtures sequentially, actual exactDefender verified_requested_paths, retained assertions/WX, layoutreport postchecker, dependency paths,5exports,unique3component archivepayloads/required map symbols,whole noPDB/ILK and final immutable inputs."],
        "unchanged_noPDB_contract": old["unchanged_noPDB_contract"],
        "execution_argv_after_commit_card_Rootrelease": ["py", "-B", CODE[0], "--plan", PLAN,
            "--admission", "<new exact card>", "--admission-sha256", "<new exact SHA>", "--execute"],
        "new_Task": {**old["new_Task"], "owner_spec": str(P/"native30-build-owner06/owner-spec")},
        "qualification": "Read-only actual preflight and focused software tests only; no06 compiler/fixture/Defender/Game qualification. Old02/04/05 FAILED remain unchanged.",
        "Native_Task_Game_started": False, "future_source_writes_after_seal": 0}
    plan["new_Task"]["contract"] = plan["new_Task"]["contract"].replace("owner05", "owner06")
    spec = importlib.util.spec_from_file_location("fixture06_sealed", REPO/CODE[0])
    q = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(q)
    card_path = Path("D:/codex-ck3-demos/2026-10-19-robert-v20261019-storage01/NATIVE30-FIXTURE-ATTEMPT05-ADMITTED01.json")
    if pin(card_path)["sha256"] != "9a2378abc3d4b69016422c17f2af162c5815c711be3b15688fe9873bb190eba4":
        raise RuntimeError("old capacity observation card changed")
    if q.ATTEMPT.exists(): raise RuntimeError("new06 attempt must remain absent")
    start, started, handles = time.monotonic(), datetime.now(timezone.utc).isoformat(), []
    try:
        checked = q.preflight(plan, handles, json.loads(card_path.read_bytes()))
        base, actual = checked["base"], checked["current"]
        report = {"schema": "native30-fixture06-actual-readonly-preflight-v1", "machine_id": machine,
            "start_utc": started, "end_utc": datetime.now(timezone.utc).isoformat(), "elapsed_seconds": time.monotonic()-start,
            "status": "PASS_TO_FIRST_NATIVE_WRITE_BOUNDARY", "producer": rp(CODE[0]),
            "source_commit": plan["source_commit"], "capacity_observation_only_not_new_admission": pin(card_path),
            "frozen_source_files": len(checked["rows"]), "selected_compile_rows": len(actual["selected_compile_rows"]),
            "current_target_count": len(actual["targets"]), "production_compile_rows": len(checked["production"]),
            "production_by_target": {name: len(q.production_rows(checked["before"], checked["guard_module"], [name]))
                                     for name in base.PRODUCTION},
            "retained_output_SHA_FileID_count": len(checked["pinned_outputs"]),
            "retained_obj_count": sum(p["path"].lower().endswith(".obj") for p in checked["pinned_outputs"]),
            "strict_graph_delta": checked["prior_configuration"],
            "current_FileAPI": [t["fileapi"] for t in actual["targets"]],
            "known_not_generated": checked["known_not_generated"],
            "protected_failed_evidence_files": len(checked["protected"]), "readonly_leases_closed_after_check": True,
            "first_Native_write": "ATTEMPT.mkdir follows shared preflight only in execute; NOTRUN here",
            "configure_build_Task_Game_calls": 0, "R_writes": 0, "future_writes": 0}
    finally:
        for handle in handles: handle.Close()
    plan_data, proof_data = encode(plan), encode(report)
    pp = {"path": PLAN, "bytes": len(plan_data), "sha256": hashlib.sha256(plan_data).hexdigest()}
    pf = {"path": PROOF, "bytes": len(proof_data), "sha256": hashlib.sha256(proof_data).hexdigest()}
    pins = [rp(name) for name in CODE]
    ready = {"schema": "native30-fixture06-source-ready-v1", "machine_id": machine,
        "observed_at_utc": datetime.now(timezone.utc).isoformat(), "status": "SOURCE_READY_CPP_NOTRUN",
        "plan": pp, "actual_readonly_preflight": pf, "sources": pins,
        "earlier_readonly_records_preserved": [rp(name) for name in HISTORY],
        "tests": {"command": "py -B -m unittest tools.g2_saved_campaign.test_native30_fixture06_current_graph_20261020 -q",
            "actual": sys.argv[2]}, "source_cap_bytes": 98304, "CPP_changes": 0, "R_Task_Game_writes": 0,
        "future_writes": 0, "allocated_bytes": None, "physical_release_credit_bytes": 0}
    ready_data = encode(ready)
    gross = sum(p["bytes"] for p in pins)+sum((REPO/p).stat().st_size for p in HISTORY)+len(plan_data)+len(proof_data)+len(ready_data)
    if gross > 98304: raise RuntimeError("source96KiB bound beforewrite: "+str(gross))
    for name, data in ((PLAN, plan_data), (PROOF, proof_data), (READY, ready_data)): exclusive(REPO/name, data)
    print(json.dumps({"plan": pp, "proof": pf, "ready": rp(READY), "gross_bytes": gross, "newfiles": 9, "future_writes": 0}))

if __name__ == "__main__":
    if sys.argv[1] == "--author": author()
    elif sys.argv[1] == "--seal": seal()
    else: raise SystemExit("--author or --seal <actual focused test result>")
