"""Independent, finite offline execution of the nine frozen Native30 fixtures.

This protocol neither registers exclusions nor qualifies the failed08B protocol.
It never builds, copies, loads or deploys a project binary.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ROOT = Path("D:/codex-ck3-demos/2026-10-19-robert-v20261019-native30-camera01")
STAGE = ROOT / "attempt09-functional"
OWNER = ROOT / "owner09-functional/owner-spec"
COMMON_PATH = HERE / "native30_two_stage_qualification_20261020.py"
COMMON_SHA = "8fff948b9f119a3341b9afc5fa69e094c8a8bea7868812dd20b0579da63a8fef"
BASE_PLAN = REPO / "docs/ck3-native-ai/evidence/native30-08B-two-stage-plan-revision3-2026-10-20.json"
BASE_PLAN_SHA = "6043fd5240c9adbaa90ff3c1d61dd3832550a668382d75af1bf59019a2aa150a"
SOURCE_COMMIT = "704bdd3362bdc282ed5f5f8cf31fd3f50b90d747"
SCHEMA = "native30-functional-qualification-v1"
RUN_ID = "native30-functional09"
SUCCESS = "OFFLINE_FUNCTIONAL_PASS_NOT_DEPLOYED"
FIELDS = {"defender_registration_pending": True,
          "defender_effective_settings_known": False, "os_qualification": "UNKNOWN"}
EXPECTED = {
    "original_build_result": ("attempt08-build/RESULT.json", 68788,
        "847b6b54f7e544315507dd5c0aa91e0d1abf992cecadd73c1a4fe2f9c94d6c85"),
    "project_exe_manifest": ("attempt08-build/project-exe-manifest.json", 10169,
        "f35cf135db1a564bcb55b3b5c932059deb4369d0e06fd4a5ff006b25d80e57a7"),
    "original_build_owner_spec": ("owner08-build/owner-spec/SPEC.json", 2059,
        "58a06b5408b45dc3097e5afc50c31dbc27a9613754596d59bd03d2d8cad27bd6"),
    "original_build_owner_closed": ("owner08-build/owner-spec/CLOSED.json", 745,
        "b73e93e01f6d51309faee52ddee5e0b490e553b0c6e10a449f7f76c632ca9562"),
    "original_build_unregister": ("owner08-build/UNREGISTER.json", 975,
        "c1d64fc3a76ac2b44cc6bb17efd2b7721b94ce9c3bd5204b029668f860f3e093"),
    "prior_failed_admin_launch": ("attempt08-admin/LAUNCH-RESULT.json", 1817,
        "73cae6d2f7e52ccf2c3d0a60b8d367eac443e3b58580ad7a0f4c53ea970ce0a5"),
}
OLD_NONCE = "798aba33848c48a8808b98c7e717bf46"


def require(value, message):
    if not value:
        raise RuntimeError(message)


def load_module(name, path, expected):
    require(hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, "borrowed source pin changed")
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


Q = load_module("native30_functional09_common", COMMON_PATH, COMMON_SHA)


def expected_refs():
    return {name: {"path": str(ROOT / relative), "bytes": size, "sha256": digest}
            for name, (relative, size, digest) in EXPECTED.items()}


def verify_plan(plan):
    require(plan["schema"] == "native30-functional09-plan-v1" and plan["protocol_version"] == 1
            and plan["run_id"] == RUN_ID and plan["source_commit"] == SOURCE_COMMIT,
            "independent functional09 protocol required")
    require(plan["original_records"] == expected_refs(), "exact immutable08B records required")
    require(plan["status"] == "SOURCE_ONLY_NOT_EXECUTION_ADMISSION" and plan["fields"] == FIELDS,
            "functional scope must retain pending/unknown OS state")
    require(plan["phase_metadata_cap_bytes"] == 167772160, "functional phase requires its private metadata160 contract")
    require(plan["common"]["sha256"] == COMMON_SHA and Path(plan["common"]["path"]).resolve() == COMMON_PATH,
            "one frozen common source")
    require(plan["base_plan"]["sha256"] == BASE_PLAN_SHA and Path(plan["base_plan"]["path"]).resolve() == BASE_PLAN,
            "one frozen base plan")
    require(plan["roots"] == {"aggregate": str(ROOT), "functional": str(STAGE), "owner": str(OWNER)},
            "exact independent functional roots")
    nonce = plan["functional_nonce"]
    require(type(nonce) is str and len(nonce) == 32 and all(c in "0123456789abcdef" for c in nonce)
            and nonce != OLD_NONCE, "new frozen functional nonce required")


def derive_readonly_plan(plan):
    verify_plan(plan)
    raw = BASE_PLAN.read_bytes()
    require(len(raw) == plan["base_plan"]["bytes"] and hashlib.sha256(raw).hexdigest() == BASE_PLAN_SHA,
            "frozen base plan changed")
    result = json.loads(raw)
    result["helper_pins"] = dict(result["helper_pins"])
    result["helper_pins"][COMMON_PATH.relative_to(REPO).as_posix()] = COMMON_SHA
    result["helper_pins"][Path(__file__).relative_to(REPO).as_posix()] = plan["producer"]["sha256"]
    return result


def verify_seed_values(records, machine_id):
    built = records["original_build_result"]
    require(built["machine_id"] == machine_id and built["schema"] == Q.SCHEMA
            and built["stage"] == "build_only" and built["status"] == "BUILD_READY_FOR_ADMIN"
            and built["fixture_executions"] == 0 and built["owned_active_after"] == 0
            and built["future_writes"] == 0 and built["production_recompiled"] is False,
            "original build-only closure required")
    require(len(built["fixture_builds"]) == 9 and all(r["returncode"] == 0 and r["owned_active_after"] == 0
            for r in built["fixture_builds"]), "nine successful original builds required")
    spec, closed = records["original_build_owner_spec"], records["original_build_owner_closed"]
    require(spec["machine_id"] == closed["machine_id"] == machine_id and spec["nonce"] == closed["nonce"] == OLD_NONCE,
            "original Task machine/nonce differs")
    require(closed["spec_sha256"] == EXPECTED["original_build_owner_spec"][2]
            and closed["child_exit_code"] == closed["bootstrap_exit_code"] == closed["job_active_after_stage"] == 0
            and closed["forced_remaining_cleanup"] is False, "original Task not normally closed")
    require(spec["role"] == "native_build" and spec["sid"] == Q.OWNER_SID
            and spec["task_name"] == "XARG2ManagedOwner-" + OLD_NONCE
            and Path(spec["stage"]).resolve() == COMMON_PATH and spec["stage_sha256"] == COMMON_SHA
            and spec["stage_args"][:2] == ["--phase", "build"], "original build SPEC differs")
    require(built["plan"]["sha256"] == BASE_PLAN_SHA
            and spec["admission_sha256"] == built["admission"]["sha256"], "original plan/admission binding differs")
    unreg = records["original_build_unregister"]
    require(unreg["machine_id"] == machine_id and unreg["operation"] == "unregister"
            and unreg["task_name"] == spec["task_name"], "original unregister binding differs")
    actual = unreg["actual"]
    require(actual["instances"] == 0 and actual["last_result"] == 0 and actual["absent_after"] is True
            and actual["sid"] == Q.OWNER_SID and actual["run_level"] == 0,
            "original Task unregister not confirmed")
    failed = records["prior_failed_admin_launch"]
    require(failed["machine_id"] == machine_id and failed["status"] == "FAILED_OR_UNKNOWN"
            and failed["settings_success"] is False and failed["future_writes"] is None
            and failed["build_result"] == expected_refs()["original_build_result"],
            "preserve failed08 admin/unknown future; it provides no qualification")


def read_seed(base, plan, handles):
    verify_plan(plan)
    records, refs = {}, {}
    for name, expected in plan["original_records"].items():
        actual = Q.lease(base, expected["path"], handles)
        refs[name] = {key: actual[key] for key in ("path", "bytes", "sha256")}
        require(refs[name] == expected, "original record changed: " + name)
        records[name] = Q.finite_load(expected["path"])
    verify_seed_values(records, base.machine())
    require(refs["project_exe_manifest"] == records["original_build_result"]["project_exe_manifest"],
            "original manifest/result binding differs")
    return records, refs


def validate_card(base, plan, card, args):
    require(card["status"] == "ADMITTED" and card["machine_id"] == base.machine()
            and card["phase"] == "functional_test_only", "same-machine functional execution card required")
    for key, expected in (("root", ROOT), ("functional_stage_root", STAGE), ("owner_stage_root", OWNER),
                          ("original_build_stage_root", Q.BUILD)):
        require(Path(card[key]).resolve() == expected.resolve(), "admitted path differs: " + key)
    require(card["hard_bytes"] == 1610612736 and card["source_charge_cap_bytes"] == 100663296
            and card["metadata_charge_cap_bytes"] == 167772160 and card["TEMP_cap_bytes"] == 402653184,
            "aggregate/source96/private metadata160/TEMP384 caps")
    require(card["aggregate_includes_prior_retained"] is True and card["new_reservation_bytes"] == 0
            and type(card["prior_retained_allocation_bytes"]) is int and card["prior_retained_allocation_bytes"] > 0,
            "all prior retained assets remain charged")
    require(type(card["jobs"]) is int and 1 <= card["jobs"] <= 4
            and card["new_metadata_upper_bytes"] == 16 * base.MIB and card["owner_metadata_cap_bytes"] == 65536,
            "finite metadata/owner allowance")
    require(card["source_commit"] == SOURCE_COMMIT and card["functional_nonce"] == plan["functional_nonce"]
            and card["original_build_result_sha256"] == EXPECTED["original_build_result"][2]
            and card["project_exe_manifest_sha256"] == EXPECTED["project_exe_manifest"][2],
            "new card must bind the original immutable products")
    require(base.digest(args.admission) == args.admission_sha256
            and card["producer_sha256"] == base.digest(Path(__file__)) == plan["producer"]["sha256"]
            and card["plan_sha256"] == base.digest(args.plan), "exact execution source/card pins")
    require(card["minimum_free_bytes"] >= 2 * 1024**3 and card["quota_remaining_bytes"] >= card["hard_bytes"],
            "fresh floor/quota required")
    require(datetime.fromisoformat(card["deadline_utc"].replace("Z", "+00:00")) > datetime.now(timezone.utc),
            "execution admission expired")
    commit = card["implementation_commit"]
    require(type(commit) is str and len(commit) == 40 and all(c in "0123456789abcdef" for c in commit),
            "full implementation commit required")
    readonly = derive_readonly_plan(plan)
    names = [*readonly["helper_pins"], args.plan.resolve().relative_to(REPO).as_posix()]
    for name in names:
        require(hashlib.sha256(base.git("show", commit + ":" + name)).hexdigest() == base.digest(REPO / name),
                "committed source changed: " + name)
    require(not STAGE.exists(), "new functional stage must be absent")


def expected_stage_args(args):
    return ["--plan", str(args.plan.resolve()), "--admission", str(args.admission.resolve()),
            "--admission-sha256", args.admission_sha256, "--execute"]


class FunctionalScopeGuard:
    """Keep the new functional output and complete owner metadata inside their quote."""
    def __init__(self, parent, card):
        self.parent, self.card = parent, card

    def __call__(self, reserve=0):
        data = self.parent(reserve)
        functional = owner = 0
        stage_prefix = STAGE.relative_to(ROOT).as_posix() + "/"
        owner_prefix = OWNER.parent.relative_to(ROOT).as_posix() + "/"
        for row in data["files"]:
            path = row["path"].replace("\\", "/")
            charge = max(row["eof"], row["allocation"])
            if path.startswith(stage_prefix):
                functional += charge
            elif path.startswith(owner_prefix):
                owner += charge
        require(owner <= self.card["owner_metadata_cap_bytes"], "functional owner metadata cap")
        require(functional + owner <= self.card["new_metadata_upper_bytes"], "functional complete new metadata cap")
        return data

    @property
    def peak_eof(self):
        return self.parent.peak_eof

    @property
    def peak_allocation(self):
        return self.parent.peak_allocation


class FunctionalParentGuard160(Q.Q.SnapshotGuard):
    """Private09 phase guard; inherited initialization only, never the old128 call."""
    def __call__(self, reserve=0):
        require(self.contract["metadata_charge_cap_bytes"] == 167772160, "private phase metadata160 required")
        require(datetime.now(timezone.utc) < datetime.fromisoformat(
            self.contract["deadline_utc"].replace("Z", "+00:00")), "admission expired")
        data = self.base.inventory(self.root, self.api)
        self.samples += 1
        self.peak_eof = max(self.peak_eof, data["eof"])
        self.peak_allocation = max(self.peak_allocation, data["allocation"])
        require(max(data["eof"], data["allocation"]) + reserve <= self.contract["hard_bytes"], "aggregate cap/reserve")
        require(shutil.disk_usage(self.root).free >= self.contract["minimum_free_bytes"] + reserve, "global free floor")
        source = metadata = temporary = 0
        for row in data["files"]:
            path, charge = row["path"].replace("\\", "/"), max(row["eof"], row["allocation"])
            if path.startswith("source/"):
                source += charge
            elif "/.msvc-temp/" in path or path.startswith("environment-temp/"):
                temporary += charge
            elif path.startswith("evidence/") or Path(path).suffix.lower() in {
                    ".json", ".log", ".ninja", ".cmake", ".txt", ".pyc"} or ".ninja_" in path:
                metadata += charge
        require(source <= 96*self.base.MIB and metadata <= 160*self.base.MIB and temporary <= 384*self.base.MIB,
                "source96/private metadata160/TEMP384 component cap")
        self.last = {"utc": self.base.utc(), "eof": data["eof"], "allocation": data["allocation"],
                     "source": source, "metadata": metadata, "temporary": temporary, "raced": data["raced"]}
        return data


def verify_owner_spec(spec, plan, args, producer_sha):
    require(spec["machine_id"] == plan["machine_id"] and spec["role"] == "native_build"
            and spec["nonce"] == plan["functional_nonce"]
            and spec["task_name"] == "XARG2ManagedOwner-" + plan["functional_nonce"]
            and spec["sid"] == Q.OWNER_SID, "new functional Task identity differs")
    require(Path(spec["root"]).resolve() == OWNER.resolve() and Path(spec["cwd"]).resolve() == REPO
            and Path(spec["stage"]).resolve() == Path(__file__).resolve() and spec["stage_sha256"] == producer_sha
            and spec["stage_args"] == expected_stage_args(args)
            and spec["admission_sha256"] == args.admission_sha256
            and Path(spec["admission_path"]).resolve() == args.admission.resolve(), "new functional SPEC differs")


def collect_readonly(plan, card, handles):
    verify_plan(plan)
    readonly = derive_readonly_plan(plan)
    state, snapshot, protected07 = Q.preflight(readonly, card, handles)
    base = state["base"]
    require(plan["machine_id"] == base.machine(), "functional plan machine differs")
    require(plan["fixtures"] == state["old_plan"]["fixtures"], "original nine fixture argv/postchecker changed")
    records, refs = read_seed(base, plan, handles)
    _, manifest, bindings = Q.build_closed(base, state, handles)
    # The unmodified borrowed preflight above retains its stricter initial128 gate.
    initial = dict(state["budget"].last)
    phase_guard = FunctionalParentGuard160(base, ROOT, card, base.FileAPI())
    phase_guard()
    state = {**state, "budget": phase_guard, "initial_readonly_charges": initial}
    return state, snapshot, protected07, records, refs, manifest, bindings


def execute(args):
    import win32file
    handles = []
    try:
        plan, card = Q.finite_load(args.plan), Q.finite_load(args.admission)
        verify_plan(plan)
        readonly = derive_readonly_plan(plan)
        guard_name = "tools/g2_saved_campaign/native30_resume_guard_20261019.py"
        require(hashlib.sha256((REPO / guard_name).read_bytes()).hexdigest() == readonly["helper_pins"][guard_name],
                "early baseline loader pin changed")
        early = Q.module("functional09_early_guard", REPO / guard_name).baseline()
        validate_card(early, plan, card, args)
        read_seed(early, plan, handles)
        for path in (args.plan, args.admission, OWNER / "SPEC.json"):
            handles.append(win32file.CreateFile(str(path), 0x80000000, 1, None, 3, 0x80, None))
        spec = Q.finite_load(OWNER / "SPEC.json")
        verify_owner_spec(spec, plan, args, early.digest(Path(__file__)))
        state, snapshot, protected07, records, refs, manifest, bindings = collect_readonly(plan, card, handles)
        base, budget = state["base"], FunctionalScopeGuard(state["budget"], card)
        fixtures = state["old_plan"]["fixtures"]
        require(len(fixtures) == 9 and len(bindings) == 9, "one exact nine-fixture set")
        budget()
        STAGE.mkdir(exist_ok=False)
        result = {"schema": SCHEMA, "protocol_version": 1, "run_id": RUN_ID, "stage": "functional_test_only",
            "machine_id": base.machine(), "source_commit": SOURCE_COMMIT, "start_utc": base.utc(), "status": "FAILED",
            "plan": base.pin(args.plan), "admission": base.pin(args.admission), "phases": [], "command_attempts": [],
            "fixture_builds": [], "fixture_runs": [], "fixture_executions": 0, "exe_bindings": bindings,
            "snapshot": snapshot, **refs, **FIELDS, "prior_admin_future_writes": None,
            "production_recompiled": False, "Game_calls": 0, "DLL_loaded": False,
            "system_settings_operations": 0, "UAC_calls": 0, "new_project_EXE_builds": 0,
            "native_build_label": Q.LABEL, "native_build_label_is_metadata": True}
        result.update(metadata_protocol_revision=2, metadata_charge_cap_bytes=167772160,
                      initial_readonly_metadata_cap_bytes=134217728)
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1")
        for name in ("CL", "_CL_", "LINK", "CMAKE_BUILD_PARALLEL_LEVEL"):
            env.pop(name, None)
        temporary = STAGE / ".msvc-temp/environment"
        temporary.mkdir(parents=True)
        env.update(TEMP=str(temporary), TMP=str(temporary))

        def run(command, cwd, log, timeout=1800):
            journal = {}
            result["command_attempts"].append(journal)
            phase = state["auxiliary"].run_owned(base, command, cwd, env, log, budget,
                                               state["binding"], timeout=timeout, state=journal)
            result["phases"].append(phase)
            return phase

        try:
            log = STAGE / "production-no-work.log"
            run([state["tools"]["ninja"], "-C", str(state["build"]), "-f", str(Q.SNAPSHOT), "-n", "-d", "explain",
                 *base.PRODUCTION], state["build"], log)
            Q.Q.assert_no_work("\n".join(v for v in log.read_text().splitlines()
                                        if not v.startswith("ninja: Entering directory")))
            result["production_no_work"] = base.pin(log)
            base.write(STAGE / "input-summary.json", {"machine_id": base.machine(), "source_count": len(state["rows"]),
                "selected_rows": len(state["current"]["selected_compile_rows"]), "targets": len(state["current"]["targets"]),
                "production_rows": len(state["production"]), "production_leases": len(state["pinned_outputs"]),
                "regen_inputs": len(state["manifest_inputs"]["inputs"]), "snapshot": snapshot,
                "continuous_between_Tasks_lease_claim": False})
            for number, fixture in enumerate(fixtures, 1):
                image = (state["build"] / fixture["artifact"]).resolve()
                arguments = [v.replace("$MACHINE_ID", base.machine()).replace("$OBSERVED_UTC", base.utc())
                             for v in fixture.get("args", [])]
                log = STAGE / ("fixture-%02d.log" % number)
                result["fixture_executions"] += 1
                phase = run([str(image), *arguments], state["build"], log, 120)
                result["fixture_runs"].append(phase)
                if fixture.get("postcheck"):
                    require(fixture["postcheck"] in base.TOOLS, "original frozen postchecker only")
                    run([sys.executable, "-B", str(ROOT / "source" / fixture["postcheck"]), str(log)], ROOT,
                        STAGE / "layout-postcheck.log")
            capture = temporary / "actual-ninja-deps.txt"
            run([state["tools"]["ninja"], "-C", str(state["build"]), "-f", str(Q.SNAPSHOT), "-t", "deps"],
                state["build"], capture)
            base.write(STAGE / "actual-dependencies.json", base.dependencies(state["build"], capture,
                       state["source"], state["old_plan"]["allowed_system_roots"]))
            capture.unlink()
            delivery = Q.final_delivery(state, run, STAGE)
            delivery.update(schema="native30-functional-delivery-v1", qualification_kind="functional_test_only",
                            **refs, **FIELDS, run_result_path=str(STAGE / "RESULT.json"))
            base.write(STAGE / "production-delivery.json", delivery)
            Q.immutable(state, protected07)
            read_seed(base, plan, handles)
            require(all(Q.same_file(a, b) for a, b in zip(bindings, Q.exe_leases(base, manifest, handles))),
                    "fixture bytes/FileID changed during functional execution")
            require(result["fixture_executions"] == len(result["fixture_runs"]) == 9, "all nine actual runs required")
            result["status"] = SUCCESS
        except BaseException as error:
            result.update(status="FAILED", error={"type": type(error).__name__, "text": str(error)})
        finally:
            active = [row.get("owned_active_after") for row in result["command_attempts"]]
            result.update(end_utc=base.utc(), owned_active_after=sum(active) if all(type(v) is int for v in active) else None,
                          future_writes=0 if all(v == 0 for v in active) else None,
                          sampled_peak_eof=budget.peak_eof, sampled_peak_allocation=budget.peak_allocation)
            base.write(STAGE / "RESULT.json", result)
            inventory = base.inventory(ROOT, base.FileAPI())
            base.write(STAGE / "FILES-CLOSED.json", {"machine_id": base.machine(), "closed_utc": base.utc(),
                       "future_writes": result["future_writes"], "files_before_this_manifest": inventory})
            final = budget()
            print(json.dumps({"result": base.pin(STAGE / "RESULT.json"), "closed": base.pin(STAGE / "FILES-CLOSED.json"),
                              "allocation": final["allocation"], "future_writes": result["future_writes"],
                              "owned_active_after": result["owned_active_after"]}))
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
    require(os.name == "nt" and args.execute, "explicit Windows functional operation required")
    return execute(args)


if __name__ == "__main__":
    raise SystemExit(main())
