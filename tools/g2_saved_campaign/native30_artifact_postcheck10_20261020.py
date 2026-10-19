"""Independent artifact postcheck. Reuses closed09 tests, never runs them again."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import struct
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ROOT = Path("D:/codex-ck3-demos/2026-10-19-robert-v20261019-native30-camera01")
STAGE = ROOT / "attempt10-artifact-postcheck"
OWNER = ROOT / "owner10-artifact/owner-spec"
F09_PATH = HERE / "native30_functional09_20261020.py"
F09_SHA = "64f9e45fda32e82c7b723ce5aa3948c207be3de6b58d4f8036a48511c1c554d2"
PLAN09 = REPO / "docs/ck3-native-ai/evidence/native30-functional09-plan-2026-10-20.json"
PLAN09_SHA = "3b7a69e787f12c491dff5285d0cef1e509e1f149757b9dfe6ac832e780523aac"
SOURCE = "704bdd3362bdc282ed5f5f8cf31fd3f50b90d747"
SCHEMA = "native30-artifact-postcheck-v1"
SUCCESS = "OFFLINE_ARTIFACT_QUALIFIED_NOT_DEPLOYED"
FUNCTIONS = ("XarCk3BridgeIdentity", "XarCk3BridgePrepareStartup", "XarCk3BridgeStart",
             "XarCk3BridgeStartWithPipe", "XarCk3BridgeStop")
DATA = "XarRefillCoreCarrier12004"
DATA_RVA = 0x1139B50
HEADER = (0x3152303643524158, 1, 20261018, 16, 21, 8, 0x98702F88A547CDE2, 0)
MAP_SHA = "0574064d032790d51099b79fcabc14b83db5ddcee16446a73a39a6a07d711e35"
SOURCE_PINS = {
    "ck3_autonomous_player/native_bridge/src/army_regular_core_passive_12004.cpp":
        "b039f1576e1277cb869003a48e454a6023fbf342ae5b24a6c3f7f5934a972dc3",
    "ck3_autonomous_player/native_bridge/include/xar_bridge/refill_core_carrier_12004.hpp":
        "ee0752d089154a7a342f05e54501da909ae27223d221e81009926b54cc8e9c60",
    "ck3_autonomous_player/native_bridge/cmake/army_natural_connected_phase_12004.cmake":
        "053000ad9eb6f5688cc217cbbb91a318b1ed028813bcf79afa410b3144f7edd6"}
RECORD09 = {
    "result": ("attempt09-functional/RESULT.json", 44290, "1459f738ea8961abc98249043c75d2c28eac51bd052d3bd94d247792c3207ab1"),
    "summary": ("owner09-functional/FINAL-CLOSED-SUMMARY.json", 7610, "a613819afd6e632bd097e21a703ed52d4bb4c56ee29eb390fcca972904c88bc1"),
    "spec": ("owner09-functional/owner-spec/SPEC.json", 2042, "51e859df3a884904a0b0fdda66275d0065e2d07b744b6a151a725c6de673e4e4"),
    "exports": ("attempt09-functional/exports.log", 951, "bab03b66414f42178267be01dc6ce562b121b80cc7416bb4d3611ec298f6f260")}


def require(value, message):
    if not value:
        raise RuntimeError(message)


def module(path, digest):
    require(hashlib.sha256(path.read_bytes()).hexdigest() == digest, "frozen helper SHA")
    spec = importlib.util.spec_from_file_location("artifact10_" + path.stem, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


F09 = module(F09_PATH, F09_SHA)
Q = F09.Q


def inspect_pe_exports(stream):
    """Only this AMD64 DLL's five code exports and fixed DATA directory ABI."""
    def read_at(offset, count):
        require(offset >= 0 and count <= 65536, "bounded PE field")
        stream.seek(offset)
        value = stream.read(count)
        require(len(value) == count, "raw-backed PE bytes required")
        return value
    require(read_at(0, 2) == b"MZ", "PE DOS header")
    pe = struct.unpack("<I", read_at(60, 4))[0]
    require(pe <= 1024 * 1024 and read_at(pe, 4) == b"PE\0\0", "PE signature")
    machine, count, _, _, _, optional_size, characteristics = struct.unpack("<HHIIIHH", read_at(pe + 4, 20))
    require(machine == 0x8664 and characteristics & 0x2000 and 0 < count <= 16, "AMD64 DLL sections")
    opt = read_at(pe + 24, optional_size)
    require(len(opt) >= 120 and struct.unpack_from("<H", opt)[0] == 0x20B, "PE32+ optional header")
    image_base = struct.unpack_from("<Q", opt, 24)[0]
    image_size = struct.unpack_from("<I", opt, 56)[0]
    export_rva, export_size = struct.unpack_from("<II", opt, 112)
    sections = []
    for i in range(count):
        raw = read_at(pe + 24 + optional_size + i * 40, 40)
        name = raw[:8].rstrip(b"\0").decode("ascii")
        virtual, rva, raw_size, raw_offset = struct.unpack_from("<IIII", raw, 8)
        flags = struct.unpack_from("<I", raw, 36)[0]
        sections.append({"name": name, "rva": rva, "size": virtual, "raw_size": raw_size,
                         "raw_offset": raw_offset, "flags": flags})
    def section(rva, size):
        found = [s for s in sections if s["rva"] <= rva and rva + size <= s["rva"] + s["size"]]
        require(rva + size <= image_size and len(found) == 1, "single in-image section extent")
        return found[0]
    def raw(rva, size):
        s = section(rva, size)
        delta = rva - s["rva"]
        require(delta + size <= s["raw_size"], "file-backed RVA required; no virtual zero fill")
        return read_at(s["raw_offset"] + delta, size)
    export = struct.unpack("<IIHHIIIIIII", raw(export_rva, 40))
    base, functions, names, addresses, nameptrs, ordinals = export[5:]
    require(base == 1 and functions == names == 6, "exact six named exports; no ordinal-only entries")
    function_rvas = struct.unpack("<6I", raw(addresses, 24))
    name_rvas = struct.unpack("<6I", raw(nameptrs, 24))
    slots = struct.unpack("<6H", raw(ordinals, 12))
    require(set(slots) == set(range(6)), "unique export ordinal slots")
    exports = []
    for name_rva, slot in zip(name_rvas, slots):
        text = bytearray()
        for i in range(128):
            byte = raw(name_rva + i, 1)
            if byte == b"\0":
                break
            text.extend(byte)
        else:
            raise RuntimeError("bounded export name")
        name = text.decode("ascii")
        rva = function_rvas[slot]
        require(rva != 0 and not export_rva <= rva < export_rva + export_size, "not a forwarder")
        exports.append({"name": name, "ordinal": base + slot, "rva": rva})
    require(len({v["name"] for v in exports}) == 6 and {v["name"] for v in exports} == set(FUNCTIONS) | {DATA},
            "five exact code names plus the one source-bound DATA name")
    for i, name in enumerate(FUNCTIONS, 1):
        row = next(v for v in exports if v["name"] == name)
        require(row["ordinal"] == i and section(row["rva"], 1)["flags"] & 0x20000000, "old function code/ordinal")
    data = next(v for v in exports if v["name"] == DATA)
    require(data["ordinal"] == 6 and data["rva"] == DATA_RVA and DATA_RVA % 8 == 0, "this artifact DATA RVA/ordinal/alignment")
    s = section(DATA_RVA, 2752)
    require(s["flags"] & 0x40000000 and not s["flags"] & 0x20000000, "readable non-executable Directory; write allowed")
    require(struct.unpack("<8Q", raw(DATA_RVA, 64)) == HEADER, "actual raw DATA header ABI1")
    return {"exports": exports, "image_base": image_base, "data_section": s,
            "directory_bytes": 2752, "raw_header": list(HEADER), "DATA_is_not_callable": True}


def verify_closed09(records, expected_args, machine):
    result, spec, closed, unreg = (records[k] for k in ("result", "spec", "closed", "unregister"))
    require(all(v["machine_id"] == machine for v in (result, spec, closed, unreg)), "09 same machine")
    require(result["status"] == "FAILED" and result["error"] == {"type": "RuntimeError", "text": "five exports"}
            and result["owned_active_after"] == 0 and result["future_writes"] == 0, "exact09 failure retained")
    runs = result["fixture_runs"]
    require(result["fixture_executions"] == len(runs) == 9 and result["fixture_builds"] == [], "nine closed runs, no new builds")
    require(all(v["returncode"] == v["owned_active_after"] == 0 and v["argv"] == args
                for v, args in zip(runs, expected_args)), "original nine exact successful argv")
    require(any(v["argv"][2].endswith("check_native_layout_report_v1.py")
                and v["returncode"] == v["owned_active_after"] == 0 for v in result["phases"]
                if len(v["argv"]) >= 3), "actual layout postchecker0")
    require(closed["spec_sha256"] == RECORD09["spec"][2] and closed["nonce"] == spec["nonce"]
            and closed["child_exit_code"] == closed["bootstrap_exit_code"] == 1
            and closed["job_active_after_stage"] == 0 and closed["forced_remaining_cleanup"] is False, "09 failed normally closed")
    require(unreg["task_name"] == spec["task_name"] and unreg["actual"]["last_result"] == 1
            and unreg["actual"]["instances"] == 0 and unreg["actual"]["absent_after"] is True, "09 Task absent")


def closed09(base, state, handles):
    records, refs = {}, {}
    for name, (relative, size, digest) in RECORD09.items():
        current = Q.lease(base, ROOT / relative, handles)
        require(current["bytes"] == size and current["sha256"] == digest, "fixed09 record " + name)
        refs[name] = {k: current[k] for k in ("path", "bytes", "sha256")}
        if name != "exports":
            records[name] = Q.finite_load(current["path"])
    summary = records["summary"]
    for name, field in (("closed", "outer_closed"), ("unregister", "unregister")):
        expected = summary[field]
        actual = Q.lease(base, expected["path"], handles)
        require(all(actual[k] == expected[k] for k in ("path", "bytes", "sha256")), "09 summary binding")
        records[name], refs[name] = Q.finite_load(actual["path"]), expected
    expected_args = []
    for row, fixture in zip(records["result"]["fixture_runs"], state["old_plan"]["fixtures"]):
        args = fixture.get("args", [])
        expected = [str((state["build"] / fixture["artifact"]).resolve())]
        if fixture.get("postcheck"):
            require(len(row["argv"]) == 5 and row["argv"][1:3] == ["--machine-id", base.machine()]
                    and row["argv"][3] == "--observed-at-utc", "original layout metadata argv")
            datetime.fromisoformat(row["argv"][4])
            args = [v.replace("$MACHINE_ID", base.machine()).replace("$OBSERVED_UTC", row["argv"][4]) for v in args]
        expected_args.append(expected + args)
    verify_closed09(records, expected_args, base.machine())
    log = ROOT / "attempt09-functional/production-no-work.log"
    no_work = Q.lease(base, log, handles)
    require(all(no_work[k] == records["result"]["production_no_work"][k] for k in ("path", "bytes", "sha256")), "09 NoWork binding")
    Q.Q.assert_no_work("\n".join(v for v in log.read_text().splitlines() if not v.startswith("ninja: Entering directory")))
    require(len(records["result"]["exe_bindings"]) == 9, "09 nine EXE identities")
    return records, refs


def preflight(plan, card, handles):
    require(plan["schema"] == "native30-artifact-postcheck10-plan-v1" and plan["source_commit"] == SOURCE, "postcheck plan")
    require(hashlib.sha256(PLAN09.read_bytes()).hexdigest() == PLAN09_SHA, "frozen09 plan")
    plan09 = Q.finite_load(PLAN09)
    readonly = F09.derive_readonly_plan(plan09)
    # Same immutable input checks as Q.preflight; only this new phase's reserve
    # is private160/new8 rather than the old08 metadata128/new16 contract.
    ref = readonly["base_readonly_plan"]
    require(ref["path"] == "docs/ck3-native-ai/evidence/native30-fixture07-snapshot-plan-2026-10-20.json", "one prior plan")
    raw = (REPO / ref["path"]).read_bytes()
    require(hashlib.sha256(raw).hexdigest() == ref["sha256"] == readonly["helper_pins"][ref["path"]], "prior plan pin")
    repair = {**readonly, "prior_pins": json.loads(raw)["prior_pins"] + readonly["seed_pins"]}
    state = Q.Q.preflight(repair, handles, card)
    base = state["base"]
    snapshot = Q.verify_seed(base, readonly, state, handles)
    require(state["budget"].last["metadata"] + 8 * base.MIB <= 160 * base.MIB, "new private160/postcheck8 reserve")
    protected = [base.pin(path) for path in (ROOT / "attempt07").rglob("*") if path.is_file()]
    require(plan09["machine_id"] == base.machine() and plan09["fixtures"] == state["old_plan"]["fixtures"], "old machine/fixtures")
    _, original_refs = F09.read_seed(base, plan09, handles)
    _, manifest, bindings = Q.build_closed(base, state, handles)
    phase_guard = F09.FunctionalParentGuard160(base, ROOT, card, base.FileAPI())
    phase_guard()
    state = {**state, "budget": phase_guard}
    records, refs = closed09(state["base"], state, handles)
    require(all(Q.same_file(a, b) for a, b in zip(bindings, records["result"]["exe_bindings"])), "09/build/current nine EXE SHA/FileID")
    for relative, digest in SOURCE_PINS.items():
        identity = Q.lease(state["base"], ROOT / "source" / relative, handles)
        require(identity["sha256"] == digest, "explicit704 DATA source pin")
    return state, snapshot, protected, records, refs, bindings, original_refs


def final_artifacts(state, run, stage):
    base, resume, guard = state["base"], state["resume"], state["guard_module"]
    plan, build, source = state["old_plan"], state["build"], state["source"]
    dll, archive, map_file = (build / plan[k] for k in ("dll_artifact", "runtime_artifact", "map_artifact"))
    with dll.open("rb") as stream:
        pe = inspect_pe_exports(stream)
    symbols = plan["required_map_symbols"] + ["?BindImage@player_heir_candidate_v1@ck3_12004"]
    found, data_rows, digest = set(), [], hashlib.sha256()
    with map_file.open("rb") as stream:
        for line in stream:
            digest.update(line)
            text = line.decode("utf-8", errors="replace")
            found.update(v for v in symbols if v in text)
            if re.match(r"\s*[0-9A-Fa-f]{4}:[0-9A-Fa-f]{8}\s+" + DATA + r"\s", text):
                data_rows.append(text.strip())
    require(digest.hexdigest() == MAP_SHA and set(symbols) <= found, "same frozen map and required component symbols")
    require(len(data_rows) == 1 and ("%016x" % (pe["image_base"] + DATA_RVA)) in data_rows[0].lower()
            and "army_regular_core_passive_12004.cpp.obj" in data_rows[0], "DATA map address and production TU")
    base.write(stage / "exports-and-data.json", {"machine_id": base.machine(), **pe,
        "map_public_row": data_rows[0], "map_sha256": MAP_SHA, "source_pins": SOURCE_PINS})
    log = stage / "runtime-members.log"
    run([state["tools"]["lib"], "/LIST", str(archive)], ROOT, log)
    require(all(s in log.read_text() for s in plan["required_runtime_members"]), "component members")
    payloads, components = resume.archive_payloads(archive), []
    for relative in plan["required_sources"]["xar_ck3_12002_runtime"]:
        path = (source / relative).resolve()
        rows = [r for r in Q.Q.production_rows(state["current"], guard, ["xar_ck3_12002_runtime"])
                if Path(r["file"]).resolve() == path]
        require(len(rows) == 1, "one same-clean component source")
        output = guard.output_from_command(rows[0])
        output = output if output.is_absolute() else Path(rows[0]["directory"]) / output
        identity = base.pin(output)
        members = [r for r in payloads if Path(r["name"]).name.lower() == output.name.lower()]
        require(len(members) == 1 and all(members[0][k] == identity[k] for k in ("bytes", "sha256")), "three unique exact payloads")
        components.append({"source": base.pin(path), "object": identity, "payload": members[0]})
    require(len(components) == 3 and not list(build.rglob("*.pdb")) and not list(build.rglob("*.ilk")), "three components/no PDB or ILK")
    return {"DLL": base.pin(dll), "runtime_archive": base.pin(archive), "map": base.pin(map_file),
        "exports_and_data": base.pin(stage / "exports-and-data.json"), "component_objects": components,
        "source_commit": SOURCE, "fixed_fixture": base.pin(Q.Q.COPY), "native_build_label": Q.LABEL,
        "production_reused_from_attempt02": True, "nine_functional_runs_reused_from_failed09": True,
        "prior_failures_requalified": False, "defender_registration_pending": True,
        "os_qualification": "UNKNOWN", "deployed": False, "Game_camera_H": "NOTRUN"}


def validate_card(base, plan, card, args):
    require(card["status"] == "ADMITTED" and card["machine_id"] == base.machine(), "same-machine card")
    require(card["phase"] == "artifact_postcheck_only" and card["source_commit"] == SOURCE, "exact phase/source")
    for key, expected in (("root", ROOT), ("postcheck_stage_root", STAGE), ("owner_stage_root", OWNER)):
        require(Path(card[key]).resolve() == expected.resolve(), "exact " + key)
    require(card["hard_bytes"] == 1610612736 and card["metadata_charge_cap_bytes"] == 167772160
            and card["source_charge_cap_bytes"] == 100663296 and card["TEMP_cap_bytes"] == 402653184
            and card["new_metadata_upper_bytes"] == 8388608 and card["owner_metadata_cap_bytes"] == 65536,
            "same aggregate/private160/source96/TEMP384/new8M includes owner64")
    require(card["aggregate_includes_prior_retained"] is True and card["new_reservation_bytes"] == 0,
            "all retained and old unknown holds remain")
    require(card["producer_sha256"] == base.digest(Path(__file__)) and card["plan_sha256"] == base.digest(args.plan)
            and base.digest(args.admission) == args.admission_sha256, "own source/plan/card SHA")
    require(card["minimum_free_bytes"] >= 2 * 1024**3 and card["quota_remaining_bytes"] >= card["hard_bytes"], "fresh capacity")
    require(datetime.fromisoformat(card["deadline_utc"]) > datetime.now(timezone.utc), "deadline")
    for relative in plan["source_files"]:
        require(hashlib.sha256(base.git("show", card["implementation_commit"] + ":" + relative)).hexdigest()
                == base.digest(REPO / relative), "committed source " + relative)
    require(not STAGE.exists(), "new postcheck stage absent")


def execute(args):
    handles = []
    try:
        plan, card = Q.finite_load(args.plan), Q.finite_load(args.admission)
        early_name = "tools/g2_saved_campaign/native30_resume_guard_20261019.py"
        guard_plan = F09.derive_readonly_plan(Q.finite_load(PLAN09))
        early = module(REPO / early_name, guard_plan["helper_pins"][early_name]).baseline()
        validate_card(early, plan, card, args)
        for path in (args.plan, args.admission, OWNER / "SPEC.json"):
            Q.lease(early, path, handles)
        spec = Q.finite_load(OWNER / "SPEC.json")
        stage_args = ["--plan", str(args.plan.resolve()), "--admission", str(args.admission.resolve()),
                      "--admission-sha256", args.admission_sha256, "--execute"]
        require(spec["machine_id"] == early.machine() and spec["role"] == "native_build" and spec["sid"] == Q.OWNER_SID
                and Path(spec["root"]).resolve() == OWNER.resolve() and Path(spec["cwd"]).resolve() == REPO
                and Path(spec["stage"]).resolve() == Path(__file__).resolve()
                and spec["stage_sha256"] == early.digest(Path(__file__)) and spec["stage_args"] == stage_args
                and spec["admission_sha256"] == args.admission_sha256
                and Path(spec["admission_path"]).resolve() == args.admission.resolve()
                and re.fullmatch(r"[0-9a-f]{32}", spec["nonce"])
                and spec["task_name"] == "XARG2ManagedOwner-" + spec["nonce"], "actual c0 SPEC binding")
        state, snapshot, protected, records, refs, bindings, original_refs = preflight(plan, card, handles)
        base, budget = state["base"], state["budget"]
        budget()
        STAGE.mkdir(exist_ok=False)
        result = {"schema": SCHEMA, "status": "FAILED", "machine_id": base.machine(), "start_utc": base.utc(),
            "plan": base.pin(args.plan), "admission": base.pin(args.admission), "source_commit": SOURCE,
            "phase": "artifact_postcheck_only", "reused09": refs, "original_build": original_refs,
            "snapshot": snapshot, "phases": [], "command_attempts": [], "project_EXE_executions": 0,
            "fixture_builds": 0, "fixture_runs_reused": 9, "production_recompiled": False,
            "UAC_calls": 0, "system_settings_operations": 0, "Game_calls": 0, "deployed": False,
            "defender_registration_pending": True, "os_qualification": "UNKNOWN"}
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1")
        temporary = STAGE / ".msvc-temp"
        temporary.mkdir()
        env.update(TEMP=str(temporary), TMP=str(temporary))
        for name in ("CL", "_CL_", "LINK", "CMAKE_BUILD_PARALLEL_LEVEL"):
            env.pop(name, None)
        def scope_guard(reserve=0):
            latest = budget(reserve)
            prefixes = tuple(p.relative_to(ROOT).as_posix() + "/" for p in (STAGE, OWNER.parent))
            owned = sum(max(v["eof"], v["allocation"]) for v in latest["files"]
                        if v["path"].replace("\\", "/").startswith(prefixes))
            require(owned + reserve <= 8388608, "new postcheck8M including owner")
            return latest
        def run(command, cwd, log, timeout=1800):
            journal = {}
            result["command_attempts"].append(journal)
            phase = state["auxiliary"].run_owned(base, command, cwd, env, log, scope_guard,
                                               state["binding"], timeout=timeout, state=journal)
            result["phases"].append(phase)
            return phase
        try:
            log = STAGE / "production-no-work.log"
            run([state["tools"]["ninja"], "-C", str(state["build"]), "-f", str(Q.SNAPSHOT),
                 "-n", "-d", "explain", *base.PRODUCTION], state["build"], log)
            Q.Q.assert_no_work("\n".join(v for v in log.read_text().splitlines() if not v.startswith("ninja: Entering directory")))
            delivery = final_artifacts(state, run, STAGE)
            Q.immutable(state, protected)
            _, manifest, final_bindings = Q.build_closed(base, state, handles)
            require(all(Q.same_file(a, b) for a, b in zip(bindings, final_bindings)), "final nine exact EXE identities")
            closed09(base, state, handles)
            base.write(STAGE / "production-delivery.json", {**delivery, "reused09": refs,
                "qualification_kind": "artifact_plus_closed09_functional_only"})
            result.update(status=SUCCESS, delivery=base.pin(STAGE / "production-delivery.json"), exe_bindings=final_bindings)
        except BaseException as error:
            result["error"] = {"type": type(error).__name__, "text": str(error)}
        finally:
            active = [v.get("owned_active_after") for v in result["command_attempts"]]
            result.update(end_utc=base.utc(), owned_active_after=sum(active) if all(type(v) is int for v in active) else None,
                          future_writes=0 if all(v == 0 for v in active) else None)
            base.write(STAGE / "RESULT.json", result)
            base.write(STAGE / "FILES-CLOSED.json", {"machine_id": base.machine(), "closed_utc": base.utc(),
                "future_writes": result["future_writes"], "files_before_this_manifest": base.inventory(ROOT, base.FileAPI())})
            latest = scope_guard()
            print(json.dumps({"result": base.pin(STAGE / "RESULT.json"), "closed": base.pin(STAGE / "FILES-CLOSED.json"),
                "allocation": latest["allocation"], "future_writes": result["future_writes"], "owned_active_after": result["owned_active_after"]}))
        return 0 if result["status"] == SUCCESS else 1
    finally:
        Q.close_handles(handles)


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--admission", type=Path, required=True)
    parser.add_argument("--admission-sha256", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    require(args.execute, "separate exact Task release required")
    return execute(args)


if __name__ == "__main__":
    raise SystemExit(main())
