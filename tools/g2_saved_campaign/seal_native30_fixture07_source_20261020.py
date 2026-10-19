"""Author/seal the explicit byte-identical Ninja snapshot qualification contract."""
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
CODE = [T+n for n in ("qualify_native30_fixture07_20261020.py", "native30_ninja_snapshot_contract_20261020.py",
    "native30_capture_msvc_environment_20261020.py", "preview_native30_fixture07_absolute_manifest_20261020.py",
    "test_native30_fixture07_snapshot_20261020.py", "seal_native30_fixture07_source_20261020.py")]
PLAN = E+"native30-fixture07-snapshot-plan-2026-10-20.json"
PROOF = E+"native30-fixture07-readonly-preflight-2026-10-20.json"
READY = E+"native30-fixture07-source-ready-2026-10-20.json"
LABEL = "Native30 continuous hotspot tracking and idle realm overview"

def pin(path):
    path = Path(path)
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}

def rp(name): return {**pin(REPO/name), "path": name}
def encoded(value): return (json.dumps(value, ensure_ascii=False, indent=2)+"\n").encode()
def write_once(path, raw):
    with Path(path).open("xb") as stream: stream.write(raw)

def author():
    path = REPO/(T+"qualify_native30_fixture06_20261020.py")
    if pin(path)["sha256"] != "7908118294206e46c1c0ca29503f772e5011e5b2bf53253ec94dd9125561ce7c":
        raise RuntimeError("frozen06 producer changed")
    source = path.read_text().replace("attempt06", "attempt07").replace("fixture06", "fixture07")
    source = source.replace("662128560", "670742624")
    current = (REPO/CODE[0]).read_text()
    start, stop = current.index("class SnapshotGuard:"), current.index("def load_module(")
    source = source.replace("import re\n", "import re\nimport shutil\n")
    point = source.index("def load_module(")
    source = source[:point]+current[start:stop]+source[point:]
    source = source.replace('    require(card["aggregate_includes_prior_retained"]',
        '    require(card.get("metadata_charge_cap_bytes") == 134217728, "new07 explicit metadata128 contract")\n    require(card["aggregate_includes_prior_retained"]')
    source = source.replace('budget = base.Guard(ROOT, card, base.FileAPI())',
        'budget = SnapshotGuard(base, ROOT, card, base.FileAPI())')
    point = source.index('    flags = resume.cache_flags(build / "CMakeCache.txt")')
    source = source[:point]+'''    snapshot_contract = load_module("native30_snapshot_contract07", HERE / "native30_ninja_snapshot_contract_20261020.py")
    manifest_inputs = snapshot_contract.configured_inputs(build, source)
    actual_identity = {"manifest": manifest_inputs["manifest"]["sha256"],
        "rules": manifest_inputs["rules"]["sha256"], "inputs": manifest_inputs["inputs_sha256"],
        "glob_script": manifest_inputs["glob"]["script"]["sha256"]}
    require(actual_identity == repair["configured_inputs_expected"], "configured manifest/input identity changed")
    for row in [manifest_inputs["manifest"], manifest_inputs["rules"], manifest_inputs["glob"]["script"], *manifest_inputs["inputs"]]:
        handles.append(win32file.CreateFile(row["path"], 0x80000000, 1, None, 3, 0x80, None))
        require(base.digest(row["path"]) == row["sha256"], "manifest input changed while leasing")
'''+source[point:]
    source = source.replace('        "prior_configuration": prior_configuration,',
        '        "prior_configuration": prior_configuration, "manifest_inputs": manifest_inputs,')
    source = source.replace('ROOT / "attempt02", ROOT / "attempt04")', 'ROOT / "attempt02", ROOT / "attempt04", ROOT / "attempt06")')
    point = source.index('        ATTEMPT.mkdir(exist_ok=False)')
    source = source[:point]+'        manifest_inputs = checked["manifest_inputs"]\n'+source[point:]
    source = source.replace('            "production_recompiled": False, "DLL_loaded": False,',
        '            "native_build_label": "'+LABEL+'", "native_build_label_is_metadata": True,\n            "production_recompiled": False, "DLL_loaded": False,')
    point = source.index('            common = [sys.executable')
    stop = source.index('            after = current', point)
    source = source[:point]+'''            snapshot = ATTEMPT / "production-manifest.ninja"
            snapshot_start = base.utc()
            require(str(snapshot).encode() not in (build / "build.ninja").read_bytes(),
                    "new loader snapshot unexpectedly occurs in original manifest")
            with (build / "build.ninja").open("rb") as original, snapshot.open("xb") as destination:
                while chunk := original.read(1024*1024):
                    destination.write(chunk)
                    destination.flush()
                    budget()
            require(base.digest(snapshot) == manifest_inputs["manifest"]["sha256"], "snapshot bytes differ")
            handles.append(win32file.CreateFile(str(snapshot), 0x80000000, 1, None, 3, 0x80, None))
            base.write(ATTEMPT / "snapshot-identity.json", {"start_utc": snapshot_start, "end_utc": base.utc(),
                "original": manifest_inputs["manifest"], "snapshot": base.pin(snapshot),
                "same_cwd": str(build), "relative_rules": manifest_inputs["rules"], "inputs": manifest_inputs})
            targets = base.PRODUCTION + [row["target"] for row in old_plan["fixtures"]]
            original_commands, snapshot_commands = ATTEMPT / "original-commands.log", ATTEMPT / "snapshot-commands.log"
            for manifest, log in ((build / "build.ninja", original_commands), (snapshot, snapshot_commands)):
                run([tools["ninja"], "-C", str(build), "-f", str(manifest), "-t", "commands", *targets], build, log)
                require(log.stat().st_size <= 8*base.MIB, "bounded selected command metadata")
            require(base.digest(original_commands) == base.digest(snapshot_commands), "snapshot expanded commands differ")
            base.write(ATTEMPT / "snapshot-command-equivalence.json", {"original": base.pin(original_commands),
                "snapshot": base.pin(snapshot_commands), "byte_identical": True, "targets": targets})
'''+source[stop:]
    source = source.replace('run([tools["ninja"], "-C", str(build), "-n", *base.PRODUCTION], ROOT, dry)',
        'run([tools["ninja"], "-C", str(build), "-f", str(snapshot), "-n", "-d", "explain", *base.PRODUCTION], build, dry)')
    point = source.index('            for number, fixture in enumerate(old_plan["fixtures"], 1):')
    source = source[:point]+'''            msvc_stage = ATTEMPT / "msvc-environment"
            msvc_stage.mkdir()
            delta_path = msvc_stage / "environment-delta.json"
            initializer = ROOT / "source/tools/run_native_msvc.py"
            installation = Path(tools["vcvars64"]).parents[3]
            run([sys.executable, "-B", str(HERE / "native30_capture_msvc_environment_20261020.py"),
                "--frozen-tool", str(initializer), "--tool-sha", base.digest(initializer),
                "--installation", str(installation), "--work", str(msvc_stage), "--output", str(delta_path)],
                msvc_stage, msvc_stage / "initializer.log", timeout=180)
            require(delta_path.stat().st_size <= 512*1024, "bounded MSVC delta")
            captured = base.load(delta_path)
            for name, path in captured["tools"].items():
                require(name in tools and base.digest(path) == base.digest(tools[name]), "initialized MSVC tool differs")
            environment.update(captured["environment_delta"])
            require(not any(environment.get(name) for name in ("CL", "_CL_", "LINK", "CMAKE_BUILD_PARALLEL_LEVEL")),
                    "MSVC initialization introduced unadmitted build options")
'''+source[point:]
    source = source.replace('run(common + ["--evidence-dir", str(stage), "--build", "--target", fixture["target"]], ROOT, stage / "producer.log")',
        'run([tools["ninja"], "-C", str(build), "-f", str(snapshot), "-j", str(card["jobs"]), fixture["target"]],\n                    build, stage / "producer.log")')
    source = source.replace('run([tools["ninja"], "-C", str(build), "-t", "deps"], ROOT, capture)',
        'run([tools["ninja"], "-C", str(build), "-f", str(snapshot), "-t", "deps"], build, capture)')
    source = source.replace('"fixed_fixture": base.pin(COPY), "production_reused_from_attempt02": True,',
        '"fixed_fixture": base.pin(COPY), "native_build_label": "'+LABEL+'",\n                "native_build_label_is_metadata": True, "production_reused_from_attempt02": True,')
    source = source.replace('            require(all(base.digest(row["path"]) == row["sha256"] for row in pinned_outputs)',
        '            require(base.digest(build / "build.ninja") == manifest_inputs["manifest"]["sha256"], "original manifest changed")\n            require(all(base.digest(row["path"]) == row["sha256"] for row in pinned_outputs)')
    write_once(REPO/CODE[0], source.encode())
    print(json.dumps({"producer": rp(CODE[0]), "Native_writes": 0}))

def seal():
    if any((REPO/p).exists() for p in (PLAN, PROOF, READY)): raise RuntimeError("preserve old records")
    machine = subprocess.run([sys.executable, "-B", "tools/ck3_live_run_id.py", "machine"], cwd=REPO,
        check=True, capture_output=True, text=True).stdout.strip()
    if machine != "xenoamess-full-tower-eb9d2c1186": raise RuntimeError("wrong machine")
    previous = json.loads((REPO/(E+"native30-fixture06-current-config-plan02-2026-10-20.json")).read_bytes())
    preview = rp(E+"native30-fixture07-absolute-manifest-preview-2026-10-20.json")
    helpers = dict(previous["helper_pins"])
    for name in CODE[1:3]: helpers[name] = rp(name)["sha256"]
    prior = previous["prior_pins"]+[pin(R/name) for name in ("attempt06/RESULT.json", "attempt06/FILES-CLOSED.json")]
    prior += [pin(P/"native30-build-owner06/owner-spec"/name) for name in ("CLOSED.json", "stage.stdout.log")]
    spec = importlib.util.spec_from_file_location("native30_snapshot_contract07_seal", REPO/CODE[1])
    contract = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(contract)
    observed_inputs = contract.configured_inputs(R/"build", R/"source/ck3_autonomous_player/native_bridge")
    expected = {"manifest": observed_inputs["manifest"]["sha256"], "rules": observed_inputs["rules"]["sha256"],
        "inputs": observed_inputs["inputs_sha256"], "glob_script": observed_inputs["glob"]["script"]["sha256"]}
    plan = {"schema": "native30-fixture07-snapshot-plan-v1", "machine_id": machine,
        "observed_at_utc": datetime.now(timezone.utc).isoformat(), "status": "SOURCE_READY_NOT_EXECUTION_ADMISSION",
        "root": str(R), "attempt_root": str(R/"attempt07"), "producer": rp(CODE[0]),
        "files": CODE+[PLAN, PROOF, READY, preview["path"]], "helper_pins": helpers, "prior_pins": prior,
        "inventory": previous["inventory"], "binding": previous["binding"],
        "budget": {**previous["budget"], "prior_retained_allocation_bytes": 670742624,
            "metadata_cap_bytes": 134217728, "old_db51_Guard80_unchanged": True},
        "configured_inputs_expected": expected, "source_commit": previous["source_commit"],
        "native_build_label": LABEL, "label_is_external_pin_metadata_not_compiled_DLL_string": True,
        "readonly_absolute_preview": preview,
        "known_not_generated_contract": previous["unchanged_noPDB_contract"],
        "evaluation": ["Original Ninja startup dry-run cannot test production because the forced VERIFY_GLOBS edge makes manifest regeneration appear successful, then Ninja returns. Original06 remains FAILED.",
            "The explicitly new snapshot is an exact byte copy of current build.ninja. Same original build cwd, relative rules include, builddir/default .ninja_log/.ninja_deps, all commands/targets/deps/flags remain unchanged. Snapshot is a new loader filename with no producer edge; only startup manifest regeneration is avoided. Production compile/link dirty detection remains active.",
            "Before first Native write, the shared full preflight verifies5355/995/12/978objects+5artifacts, failed provenance, all current FileAPI, two exact physical globs,219 actual regeneration inputs including cache/overlays/CMake/toolchain/modules with hashes/mtime and readonly leases. Source preview uses the real absolute original file, not a materialized snapshot; actual snapshot qualification occurs after admission.",
            "Actual07 streaming copy under attempt07; before/after identity while original/snapshot/rules/inputs leased. Original and snapshot -t commands for exact12 targets must hash-identical; actual snapshot production -n -d explain must be literal NoWork. A failed check stops before fixtures.",
            "MSVC initialization runs the unchanged frozen initialize_msvc in a separate owned Python phase and captures only changed/added MSVC environment values, never unchanged ambient secrets; all returned tool identities must match. Root0/Job0/UTC/auxcleanup policy applies. No configure or cmake --build.",
            "All9 actual builds invoke exact pinned Ninja -C originalbuild -f snapshot -j<=4 one target, followed by existing exactDefender actualreadback/fixture execution/layout postcheck. No default ALL or original-manifest build fallback. No debug/PDB/ILK or disabled assertions/WX.",
            "Original final dependency-source roots/5exports/3unique component archivepayload/map/immutable production+source checks remain. Actual loading/provider/camera/H remain separate."],
        "file_peak_quote": {"snapshot_EOF": observed_inputs["manifest"]["bytes"], "snapshot_charge_upper_bytes": 16*1024**2,
            "two_commands_logs_upper_bytes": 16*1024**2, "environment_delta_upper_bytes": 512*1024,
            "same_aggregate_hard_bytes": 1610612736, "source_cap": 100663296, "metadata_cap": 134217728,
            "TEMP_cap": 402653184, "phase_reserve": 268435456, "new_reservation_bytes": 0,
            "copy": "one destination streamed1MiB; original is retained input, no second source/native/archive copy"},
        "Task": {**previous["new_Task"], "owner_spec": str(P/"native30-build-owner07/owner-spec")},
        "execution_argv_after_commit_card_Rootrelease": ["py", "-B", CODE[0], "--plan", PLAN,
            "--admission", "<exact new card>", "--admission-sha256", "<exact SHA>", "--execute"],
        "official_source": "https://raw.githubusercontent.com/ninja-build/ninja/master/src/ninja.cc",
        "new_R_Task_CPP_Game_writes": 0, "future_source_writes_after_seal": 0}
    module_spec = importlib.util.spec_from_file_location("native30_fixture07_sealed", REPO/CODE[0])
    q = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(q)
    if q.ATTEMPT.exists(): raise RuntimeError("attempt07 must remain absent")
    old_card = Path("D:/codex-ck3-demos/2026-10-19-robert-v20261019-storage01/NATIVE30-FIXTURE-ATTEMPT06-ADMITTED01.json")
    require_sha = "0ab44c5845cc805a3448dbd5ad1ab5a4a6da9e000f22f4ed332f2ab6604b6573"
    if pin(old_card)["sha256"] != require_sha: raise RuntimeError("old capacity observation source changed")
    handles, started, clock = [], datetime.now(timezone.utc).isoformat(), time.monotonic()
    try:
        state = q.preflight(plan, handles, json.loads(old_card.read_bytes()))
        observed_budget = state["budget"].last
        # Guard's current metadata classification is authoritative; quote each new component separately.
        metadata_quote = {"existing_charged_bytes": observed_budget["metadata"],
            "snapshot_charged_upper_bytes": 16*1024**2, "two_command_logs_charged_upper_bytes": 16*1024**2,
            "all_other_new_evidence_logs_and_close_upper_bytes": 16*1024**2,
            "cap_bytes": 128*1024**2, "charge": "sum per-file max(EOF,AllocationSize); snapshot upper includes cluster tail"}
        metadata_quote["projected_upper_bytes"] = sum(metadata_quote[name] for name in (
            "existing_charged_bytes", "snapshot_charged_upper_bytes", "two_command_logs_charged_upper_bytes",
            "all_other_new_evidence_logs_and_close_upper_bytes"))
        if metadata_quote["projected_upper_bytes"] > metadata_quote["cap_bytes"]:
            raise RuntimeError("metadata128 quote exceeds cap: "+json.dumps(metadata_quote))
        plan["file_peak_quote"]["metadata_component_quote"] = metadata_quote
        report = {"schema": "native30-fixture07-readonly-preflight-v1", "machine_id": machine,
            "start_utc": started, "end_utc": datetime.now(timezone.utc).isoformat(), "seconds": time.monotonic()-clock,
            "status": "ALL_EXISTING_INPUTS_PASS_SNAPSHOT_NOT_CREATED", "producer": rp(CODE[0]),
            "source_count": len(state["rows"]), "selected_rows": len(state["current"]["selected_compile_rows"]),
            "targets": len(state["current"]["targets"]), "production_rows": len(state["production"]),
            "retained_SHA_FileID_leases": len(state["pinned_outputs"]), "configured_inputs": expected,
            "glob": observed_inputs["glob"], "regeneration_input_count": len(observed_inputs["inputs"]),
            "component_budget_actual": observed_budget, "metadata_component_quote": metadata_quote,
            "absolute_original_Ninja_preview": preview, "preview_is_not_future_snapshot_qualification": True,
            "current_fixture_source": str(q.COPY), "leases_closed_after_check": True,
            "snapshot_copy_commands_NoWork_9fixtures": "NOTRUN; require formal newcard/Task release",
            "prior_budget_seal_RED_preserved": {"tool": "exec e4cbd7", "current_metadata": 78976712,
                "old_cap": 83886080, "projected_metadata": 129308360,
                "fact": "Sealer refused old80 before writing plan/proof; Root then authorized explicit new07 metadata128, total1.5G/source96/TEMP384 unchanged. No R/Task/compiler writes."},
            "R_Task_CPP_Game_writes": 0, "future_writes": 0}
    finally:
        for handle in handles: handle.Close()
    plan_raw, proof_raw = encoded(plan), encoded(report)
    pp = {"path": PLAN, "bytes": len(plan_raw), "sha256": hashlib.sha256(plan_raw).hexdigest()}
    proof_pin = {"path": PROOF, "bytes": len(proof_raw), "sha256": hashlib.sha256(proof_raw).hexdigest()}
    pins = [rp(name) for name in CODE]
    ready = {"schema": "native30-fixture07-source-ready-v1", "machine_id": machine,
        "observed_at_utc": datetime.now(timezone.utc).isoformat(), "status": "SOURCE_READY_CPP_NOTRUN",
        "plan": pp, "readonly_preflight": proof_pin, "sources": pins,
        "tests": {"actual": sys.argv[2]}, "source_cap_bytes": 98304,
        "R_Task_CPP_Game_writes": 0, "future_writes": 0, "allocated_bytes": None, "physical_credit_bytes": 0}
    ready_raw = encoded(ready)
    gross = sum(p["bytes"] for p in pins)+len(plan_raw)+len(proof_raw)+len(ready_raw)+preview["bytes"]
    if gross > 98304: raise RuntimeError("source96KiB bound beforewrite: "+str(gross))
    for name, data in ((PLAN, plan_raw), (PROOF, proof_raw), (READY, ready_raw)): write_once(REPO/name, data)
    print(json.dumps({"plan": pp, "proof": proof_pin, "ready": rp(READY), "gross_bytes": gross, "future_writes": 0}))

if __name__ == "__main__":
    if sys.argv[1] == "--author": author()
    elif sys.argv[1] == "--seal": seal()
    else: raise SystemExit("--author or --seal <actual tests>")
