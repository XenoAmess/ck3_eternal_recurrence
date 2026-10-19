"""Seal small prospective fixture03 sources; does not configure/build/prepare a Task."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[2]
E = "docs/ck3-native-ai/evidence/"
T = "tools/g2_saved_campaign/"
R = Path("D:/codex-ck3-demos/2026-10-19-robert-v20261019-native30-camera01")
P = Path("D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/p51-fresh1066-v20261019-prepare01")
PLAN = E+"native30-fixture03-qualification-plan-2026-10-19.json"
READY = E+"native30-fixture03-source-ready-2026-10-19.json"
FIXTURE = "ck3_autonomous_player/native_bridge/src/camera_tracking_v1_test.cpp"
CODE = [T+name for name in ("qualify_native30_fixture03_20261019.py", "native30_fixture03_override_20261019.cmake",
    "test_native30_fixture03_contract_20261019.py", "seal_native30_fixture03_source_20261019.py")]

def pin(path):
    path = Path(path)
    body = path.read_bytes()
    return {"path": str(path), "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()}

def relative_pin(relative):
    return {**pin(REPO/relative), "path": relative}

def body(value): return (json.dumps(value, ensure_ascii=False, indent=2)+"\n").encode()

def main():
    if any((REPO/name).exists() for name in (PLAN, READY)): raise RuntimeError("preserve existing source records")
    machine = subprocess.run([sys.executable, "-B", "tools/ck3_live_run_id.py", "machine"], cwd=REPO,
                             capture_output=True, text=True, check=True).stdout.strip()
    if machine != "xenoamess-full-tower-eb9d2c1186": raise RuntimeError("wrong machine")
    now = datetime.now(timezone.utc).isoformat()
    helper_paths = [CODE[1], FIXTURE] + [T+name for name in (
        "build_native30_resume_20261019.py", "native30_resume_guard_20261019.py",
        "native30_msvc_auxiliary_policy_20261019.py", "build_native30_wholeclean_20261019.py")] + [E+name for name in (
        "native30-wholeclean-producer-plan-2026-10-19.json", "native29-production-compile-macro-provenance-2026-10-19.json",
        "native30-existing-config-output-inventory-2026-10-19.json", "native30-msvc-auxiliary-file-binding-2026-10-19.json")]
    prior = [R/name for name in ("attempt02/RESULT.json", "attempt02/FILES-CLOSED.json",
        "attempt02/selected-fileapi-graph.json", "attempt02/runtime-source-macro-restore.cmake",
        "evidence/FILES-CLOSED.json", "evidence/source-freeze.json")]
    old_fixture = subprocess.run(["git", "show", "704bdd3362bdc282ed5f5f8cf31fd3f50b90d747:"+FIXTURE], cwd=REPO,
                                 capture_output=True, check=True).stdout
    fixed = (REPO/FIXTURE).read_bytes()
    old = b'std::strcpy(r.provinces[0].title_key, "b_fixture")'
    new = b'std::memcpy(r.provinces[0].title_key, "b_fixture", sizeof("b_fixture"))'
    if old_fixture.count(old) != 1 or fixed != old_fixture.replace(old, new): raise RuntimeError("fixture delta exceeded")
    plan = {"schema": "native30-fixture03-plan-v1", "machine_id": machine, "observed_at_utc": now,
        "status": "SOURCE_READY_NOT_NEW_HEAVY_ADMISSION", "root": str(R), "attempt_root": str(R/"attempt03"),
        "producer": relative_pin(CODE[0]), "files": CODE+[FIXTURE, PLAN, READY],
        "helper_pins": {name: relative_pin(name)["sha256"] for name in helper_paths},
        "prior_pins": [pin(path) for path in prior],
        "inventory": E+"native30-existing-config-output-inventory-2026-10-19.json",
        "binding": E+"native30-msvc-auxiliary-file-binding-2026-10-19.json", "overlay": CODE[1],
        "source": {"Native_and_tools_commit": "704bdd3362bdc282ed5f5f8cf31fd3f50b90d747", "frozen_files": 5355,
            "immutable_roots": [str(R/"source"), str(R/"evidence"), str(R/"attempt02")],
            "patched_fixture": relative_pin(FIXTURE), "patched_fixture_Git_commit": "new implementation commit; checked via git show at runtime",
            "delta": "Only strcpy -> memcpy with sizeof literal including NUL. All asserts/W4/WX/C4996 guards remain. No production source/header/ABI edits."},
        "reuse_production": {"prior_result": "attempt02 root0/Job0 production command; whole attempt remainsFAILED at fixture1",
            "original_production_window": ["2026-10-19T17:12:48.953768+00:00", "2026-10-19T17:26:03.216880+00:00"],
            "checks": ["All5355 Git blobs/SHAs intact and original fullmacro/FileAPI source guards enforced",
                "Actual pre-reuse selected argv matches exact immutable attempt02 graph; all production source and object paths retained",
                "Every production object plus DLL/runtime/protocol library/map: prior closed inventory name+EOF, last-write within successful production window(1s boundary tolerance), fresh FileID128+SHA while a read-only/no-delete lease is retained",
                "SHA/FileID are first freshly observed here, not fabricated as historical attempt02 hash receipts; prior command/closed inventory and protected custody bind provenance",
                "After configure all production and other8fixture source/argv unchanged; same semantic link/archive/artifacts. Only test1 source/object paths may change",
                "Explicit production Ninja dry-run must say no work. Existing production output read-only leases prevent implicit rewriting during fixture runs; final bytes rechecked"],
            "no_production_build_or_relink": True},
        "override": {"old_two_macro_overlay": str(R/"attempt02/runtime-source-macro-restore.cmake"),
            "fixed_copy": str(R/"build/native30-fixture03/camera_tracking_v1_test.cpp"),
            "mechanism": "Root-owned exactGit-pinned copy generated before configure; CMake GENERATED=TRUE truthfully marks that build-local TU. Deferred override replaces exactly the one old fixture1 source. Existing original graph permits generated build-local TUs; no path/source-guard bypass or mutable old source."},
        "pipeline": ["Pin new implementation and exact new card; require absent attempt03/copy directory",
            "Revalidate old production root0/Job0 plus failed-root evidence;5355source and all production argv/source/output identities",
            "Retain read-only production outputs, capture reuse identities, generate one small fixed fixture copy/newoverlay",
            "Configure only fixture source override and retained old2macros; unchangedXAR/Release/options, full graph/argv comparison",
            "Require production no-work; only fixture1 plus remaining8 named fixture targets in original order",
            "Exact existing Defender EXE provenance+SYSTEM readback before each real fixture; layoutreport postchecker; no ALL/duplicateBridge",
            "Actual Ninja dependency closure,5exports,3component unique archive payloads equal reused clean objects,required Read/BindImage/campaign map symbols,noPDB/ILK",
            "Recheck production bytes/source/oldfailed evidence; new RESULT/FILES-CLOSED under attempt03. Any failure stops/no replay"],
        "budget": {"same_aggregate_hard_bytes": 1610612736, "prior_retained_allocation_bytes": 659564464,
            "new_reservation_bytes": 0, "source_cap_bytes": 100663296, "metadata_cap_bytes": 83886080,
            "TEMP_cap_bytes": 402653184, "charge": "max(aggregateEOF,AllocationSize)",
            "old_retained_plus_all_new_writes_count_together": True, "jobs": "integer1..4 BELOW_NORMAL/noMP",
            "phase_reserve_bytes": 268435456, "sampled_peak_is_lower_bound": True, "physical_credit_bytes": 0},
        "new_card_contract": ["statusADMITTED/same machine/root/attempt_root", "hard_bytes1610612736/source_charge_cap_bytes100663296",
            "aggregate_includes_prior_retained=true/prior_retained_allocation_bytes659564464/new_reservation_bytes0",
            "source_commit704bdd3362bdc282ed5f5f8cf31fd3f50b90d747; implementation_commit fullnewcommit containing patchedfixture+code",
            "producer_sha256/plan_sha256/jobs1..4/deadline_utc/fresh minimum_free_bytes>=2GiB/quota_remaining_bytes>=hard"],
        "execute_after_Root_commit_card_and_release": ["py", "-B", CODE[0], "--plan", PLAN,
            "--admission", "<new exact card>", "--admission-sha256", "<new SHA>", "--execute"],
        "Task": {"new_metadata_root": str(P/"native30-build-owner03/owner-spec"),
            "reuse_bootstrap": str(P/"native30-build-owner01/interactive_task_owner_v1.py"),
            "bootstrap_sha256": "c0d76a7064996cafd7412f8f39ba2bb5c5cb6271627246b84e946c00bafb864f",
            "role": "native_build", "prepare": "create-only owner03 container then absentowner-spec; absolute admission argv must use same canonical backslash spelling as admission_path",
            "release": "Separate bounded metadata card+Root exactSPEC read before register/definitionreadback/run once. No TaskStop. Unregister only actual stage/bootstrap exit and ownJob0. All logs/TEMP stay admitted scopes."},
        "qualification_limits": "Patch29finite checks are software only. Old production root0 is actual compilation/linking, not complete DLL qualification. Need all9 actual fixtures+artifact checks before offline candidate; actual loaded camera/provider/H separate. No Game/OBS/MCP/inject/load/current SDK/flags or speed changes.",
        "configure_build_Task_started": False, "future_source_writes_after_seal": 0}
    plan_data = body(plan)
    plan_pin = {"path": PLAN, "bytes": len(plan_data), "sha256": hashlib.sha256(plan_data).hexdigest()}
    pins = [relative_pin(name) for name in CODE+[FIXTURE]]
    ready = {"schema": "native30-fixture03-source-ready-v1", "machine_id": machine, "observed_at_utc": now,
        "machine_id_source": "Fresh tools/ck3_live_run_id.py machine", "status": "SOURCE_READY_PATCH_CPP_NOTRUN",
        "plan": plan_pin, "sources": pins,
        "source_tests": {"command": "py -B -m unittest tools.g2_saved_campaign.test_native30_fixture03_contract_20261019 -q",
            "actual_result": "29PASS/0.088s", "tool_exec": "6a8352", "earlier": "25PASS/0.097s/daf3a9",
            "limits": "Pure admission/source-literal/argv/no-work/prior-output finite tests. Not MSVC/CMake/Defender/real fixture qualification."},
        "old_attempt02": {"status": "FAILED", "result": pin(R/"attempt02/RESULT.json"),
            "rootcause": "fixture1 C4996 strcpy underWX; production command completed root0/Job0, all9fixtures notpassed",
            "Task_unregistered": "Actual17:26:46.395858Z tool9375db absent_aftertrue; no TaskStop or buildretry"},
        "retained_original_fixture": {"bytes": len(old_fixture), "sha256": hashlib.sha256(old_fixture).hexdigest()},
        "modified_existing_fixture_net_bytes": len(fixed)-len(old_fixture),
        "unrelated_CPP_or_production_changes": 0, "configure_or_build": "NOTRUN", "Task_prepared": False,
        "new_external_files": 0, "future_writes": 0, "allocated_bytes": None, "physical_credit_bytes": 0}
    ready_data = body(ready)
    gross = sum(row["bytes"] for row in pins)+len(plan_data)+len(ready_data)
    if gross > 65536: raise RuntimeError("source64KiB exceeded before seal writes: "+str(gross))
    for name, content in ((PLAN, plan_data), (READY, ready_data)):
        with (REPO/name).open("xb") as output: output.write(content)
    print(json.dumps({"plan": plan_pin, "ready": relative_pin(READY), "gross_including_full_existing_fixture_bytes": gross,
        "new_files": len(CODE)+2, "modified_existing_files": 1, "future_writes": 0, "CPP": "NOTRUN"}))

if __name__ == "__main__": main()
