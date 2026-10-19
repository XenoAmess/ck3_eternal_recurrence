"""RAM-only 08B models derived from frozen producer vocabulary, never CPP proof."""
import ast
import copy
from datetime import datetime, timedelta, timezone
import hashlib
import io
import json
import ntpath
from pathlib import Path
import sys
import unittest
from unittest import mock

TOOLS = Path(__file__).resolve().parents[1]
if str(TOOLS) not in sys.path: sys.path.insert(0, str(TOOLS))
from g2_saved_campaign import native30_two_stage_export_contract_v1 as chain
from g2_saved_campaign import native29_to30_export_contract_v1 as common
from g2_saved_campaign import export_native30_immutable_sdk_views_v1 as loader
from g2_saved_campaign import native30_export_adapter_v1 as adapter_module
from g2_saved_campaign.test_native30_export_transition_v1 import document, qualify, MACHINE
from g2_saved_campaign.test_native30_resume_fixture_chain_v1 import at, phase
from g2_saved_campaign.test_native30_resume_fixture07_snapshot_chain_v1 import snapshot_corpus

ROOT = "Z:/native30"
BUILD = ROOT + "/build"
REPO = "Z:/repo"
PLAN = REPO + "/" + chain.PLAN_PATH
PATHS = {role: ROOT + "/attempt08-" + role for role in ("build", "run", "admin")}
FILE_ID = {"volume_serial": "1234", "file_id": "1" * 32}


def leased(pin, index=1):
    return {**pin, "file_id": {"volume_serial": "1234", "file_id": "%032x" % index}}


def text(path, raw=b"ninja: no work to do.\r\n"):
    ref = {"path": path, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
    return chain.seed.parse_native07_no_work_log_v1(raw, ref)


def two_stage_corpus(change=None):
    base, old, original, old_card, args = snapshot_corpus()
    evidence = {name: value for name, value in original.items()
        if name not in ("fixture07_admission", "msvc_environment")}
    failed = original["build_result"].value
    failed.update(status="FAILED", error={"type": "AuxiliaryContractError", "text": "original command exit 1"})
    failed["phases"] = failed["phases"][:5]
    failed["command_attempts"] = failed["command_attempts"][:5]
    # The registration failure journal is retained. It is not a successful phase.
    failure = copy.deepcopy(failed["command_attempts"][-1])
    failure.update(argv=["Z:/python.exe", "-B", "Z:/register.py"], original_root_exit_code=1)
    failed["command_attempts"].append(failure)
    failed_doc = at(ROOT + "/attempt07/RESULT.json", failed)
    evidence["fixture07_result"] = failed_doc
    seed_plan = evidence["fixture07_plan"].value
    fixtures = evidence["build_plan"].value["fixtures"]
    inventory = evidence["tool_inventory"].value["tool_pins"]
    snapshot = leased(evidence["snapshot_identity"].value["snapshot"], 55)
    plan = {"schema": "native30-08B-two-stage-plan-v1", "revision": 3, "machine_id": MACHINE,
        "source_fixture": True, "source_commit": chain.SOURCE_COMMIT,
        "producer": {"path": chain.PRODUCER_PATH, "bytes": 25416, "sha256": chain.PRODUCER_SHA},
        "admin_producer": {"path": chain.ADMIN_PATH, "bytes": 10911, "sha256": chain.ADMIN_SHA},
        "helper_pins": {chain.ADMIN_PATH: chain.ADMIN_SHA, chain.seed.PRODUCER_PATH: chain.seed.PRODUCER_SHA,
            chain.seed.SNAPSHOT_HELPER: chain.seed.SNAPSHOT_SHA, chain.seed.CAPTURE_HELPER: chain.seed.CAPTURE_SHA,
            chain.seed.INVENTORY_PATH: evidence["tool_inventory"].sha256},
        "base_readonly_plan": {"path": "docs/ck3-native-ai/evidence/native30-fixture07-snapshot-plan-2026-10-20.json",
            "bytes": len(evidence["fixture07_plan"].raw), "sha256": evidence["fixture07_plan"].sha256},
        "roots": {"aggregate": ROOT, **PATHS, "owner_build": ROOT + "/owner08-build/owner-spec",
            "owner_run": ROOT + "/owner08-run/owner-spec"}, "snapshot_reused_readonly": snapshot["path"],
        "copy_snapshot_or_commands": False, "configured_inputs_expected": seed_plan["configured_inputs_expected"],
        "seed_pins": [evidence[name].reference for name in ("fixture07_result", "snapshot_command_equivalence", "fixture07_no_work_log", "snapshot_identity")],
        "protocol": {"schema": chain.SCHEMA, "protocol_version": 1, "run_id": chain.RUN_ID,
            "build_status": "BUILD_READY_FOR_ADMIN", "run_status": "OFFLINE_QUALIFIED_NOT_DEPLOYED",
            "admin_schema": "native30-exact-nine-admin-registration-v1"},
        "admin_python": leased({"path": "Z:/python.exe", "bytes": 10, "sha256": "1" * 64})}
    admission = {"machine_id": MACHINE, "status": "ADMITTED", "root": ROOT, "source_commit": chain.SOURCE_COMMIT,
        "producer_sha256": chain.PRODUCER_SHA, "implementation_commit": "a" * 40, "jobs": 2,
        "deadline_utc": "2026-10-20T00:00:00Z", "hard_bytes": 1610612736, "source_charge_cap_bytes": 100663296,
        "metadata_charge_cap_bytes": 134217728, "TEMP_cap_bytes": 402653184,
        "aggregate_includes_prior_retained": True, "prior_retained_allocation_bytes": 706251512,
        "new_reservation_bytes": 0, "minimum_free_bytes": 2*1024**3, "quota_remaining_bytes": 1610612736,
        **{role + "_stage_root": path for role, path in PATHS.items()}}
    files = sorted([{"path": BUILD + "/" + f["artifact"], "size": 20, "sha256": "%064x" % (i + 1),
        "target": f["target"], "target_id": f["target"] + "::id"} for i, f in enumerate(fixtures)], key=lambda row: row["path"])
    manifest = {"schema": "xar.project-exe-exclusions.v1", "configuration": "Release", "external_candidate": chain.RUN_ID,
        "repo": REPO, "source_dir": ROOT + "/source/ck3_autonomous_player/native_bridge", "build_dir": BUILD,
        "requested_targets": [row["target"] for row in fixtures], "files": files}
    bindings = [leased({"path": row["path"], "bytes": row["size"], "sha256": row["sha256"]}, i + 1) for i, row in enumerate(files)]
    no_work = {role: text(path + "/production-no-work.log") for role, path in PATHS.items() if role != "admin"}
    results = {}
    for role, hour in (("build", 12), ("run", 14)):
        rows, states = [], []
        def run(argv, log):
            row, state = phase(argv, log, len(rows) + 1)
            moment = datetime(2026, 10, 19, hour, tzinfo=timezone.utc) + timedelta(seconds=2*len(rows))
            for value in (row, state): value.update(start_utc=moment.isoformat(), end_utc=(moment+timedelta(seconds=1)).isoformat())
            row["log"]["path"] = PATHS[role] + "/" + log
            rows.append(row); states.append(state)
            return row
        ninja = inventory["ninja"]["path"]
        run([ninja, "-C", BUILD, "-f", snapshot["path"], "-n", "-d", "explain", *chain.PRODUCTION], "production-no-work.log")["log"] = no_work[role].reference
        if role == "build":
            work = PATHS[role] + "/msvc-environment"
            run(["Z:/python.exe", "-B", REPO + "/" + chain.seed.CAPTURE_HELPER,
                "--frozen-tool", ROOT + "/source/tools/run_native_msvc.py", "--tool-sha", "e" * 64,
                "--installation", "Z:/VisualStudio", "--work", work, "--output", work + "/environment-delta.json"], "msvc-environment/initializer.log")
            for i, fixture in enumerate(fixtures, 1):
                run([ninja, "-C", BUILD, "-f", snapshot["path"], "-j", "2", fixture["target"]], "build-%02d.log" % i)
        else:
            fixture_runs = []
            for i, fixture in enumerate(fixtures, 1):
                argv = [v.replace("$MACHINE_ID", MACHINE).replace("$OBSERVED_UTC", "2026-10-19T14:00:00Z") for v in fixture.get("args", [])]
                row = run([BUILD + "/" + fixture["artifact"], *argv], "fixture-%02d.log" % i); fixture_runs.append(row)
                if fixture.get("postcheck"):
                    run(["Z:/python.exe", "-B", ROOT + "/source/" + fixture["postcheck"], row["log"]["path"]], "layout-postcheck.log")
            run([ninja, "-C", BUILD, "-f", snapshot["path"], "-t", "deps"], ".msvc-temp/environment/actual-ninja-deps.txt")
            delivery = original["production_delivery"].value
            run([inventory["dumpbin"]["path"], "/exports", delivery["DLL"]["path"]], "exports.log")
            run([inventory["lib"]["path"], "/LIST", delivery["runtime_archive"]["path"]], "runtime-members.log")
        results[role] = {"schema": chain.SCHEMA, "protocol_version": 1, "run_id": chain.RUN_ID, "stage": role + "_only",
            "machine_id": MACHINE, "source_commit": chain.SOURCE_COMMIT, "status": "BUILD_READY_FOR_ADMIN" if role == "build" else "OFFLINE_QUALIFIED_NOT_DEPLOYED",
            "source_fixture": True, "phases": rows, "command_attempts": states, "fixture_builds": rows[2:] if role == "build" else [],
            "fixture_runs": [] if role == "build" else fixture_runs, "fixture_executions": 0 if role == "build" else 9,
            "snapshot": snapshot, "prior07_FAILED": failed_doc.reference, "production_recompiled": False,
            "Game_calls": 0, "DLL_loaded": False, "owned_active_after": 0, "future_writes": 0,
            "start_utc": "2026-10-19T%02d:00:00Z" % hour, "end_utc": "2026-10-19T%02d:10:00Z" % hour,
            "exe_bindings": copy.deepcopy(bindings)}
    summary = {"source_count": 5355, "selected_rows": 995, "targets": 12, "production_rows": 978,
        "production_leases": 983, "regen_inputs": 219, "configured_inputs": plan["configured_inputs_expected"],
        "snapshot": snapshot, "reference_current_graph": evidence["fixture_graph_delta"].value["current_graph"],
        "continuous_between_Tasks_lease_claim": False}
    summaries = {role: {**summary, "no_work": no_work[role].reference} for role in ("build", "run")}
    environment = {"tools": {key: inventory[key]["path"] for key in ("vcvars64", "cmake", "ninja", "cl")}, "environment_delta": {"PATH": "Z:/tools"}}
    started = {"schema": "native30-exact-nine-admin-started-v1", "machine_id": MACHINE, "utc": "2026-10-19T13:00:01Z",
        "identity": {"pid": 3000, "creation_filetime": "134368909000000009", "sid": chain.OWNER_SID,
            "image": "Z:/python.exe", "image_file_id": plan["admin_python"]["file_id"], "session": 1,
            "wait0": 258, "exit_code": 259}, "unknown_future_prohibits_repeat": True}
    settings = {"ExclusionPath": ["Z:/prior.exe"], "ExclusionExtension": [], "ExclusionProcess": ["prior.exe"]}
    after = copy.deepcopy(settings); after["ExclusionPath"] += [row["path"] for row in files]
    admin = {"schema": "native30-exact-nine-admin-registration-v1", "machine_id": MACHINE,
        "status": "verified", "actual_sid": chain.OWNER_SID, "actual_admin": True, "exe_bindings": copy.deepcopy(bindings),
        "before_settings": settings, "after_settings": after, "verified_requested_paths": [row["path"] for row in files],
        "allowed_settings_operation": "ExclusionPath exact nine complete filenames only",
        "helper_receipt": {"status": "verified", "admin_token": True, "observed_prior_settings_preserved": True, "files": files},
        "start_utc": "2026-10-19T13:00:02Z", "end_utc": "2026-10-19T13:00:10Z", "future_writes": 0}
    launch = {"schema": "native30-exact-nine-admin-launch-v1", "machine_id": MACHINE,
        "status": "VERIFIED", "settings_success": True, "UAC_calls": 1, "actual_exit_code": 0, "future_writes": 0,
        "operation": "one explicit ShellExecuteEx runas", "pid": 3000, "python": plan["admin_python"],
        "start_utc": "2026-10-19T13:00:00Z", "end_utc": "2026-10-19T13:00:11Z"}
    specs, closes = {}, {}
    for i, role in enumerate(("build", "run")):
        specs[role] = {"schema": "xar.interactive-task-owner/v1", "role": "native_build", "machine_id": MACHINE,
            "nonce": "synthetic-" + role, "task_name": "Synthetic08-" + role, "sid": chain.OWNER_SID, "session": 1,
            "root": plan["roots"]["owner_" + role], "cwd": REPO, "stage": REPO + "/" + chain.PRODUCER_PATH,
            "stage_sha256": chain.PRODUCER_SHA, "bootstrap": "Z:/c0.py", "bootstrap_sha256": chain.C0_SHA,
            "python": "Z:/python.exe", "pythonw": "Z:/pythonw.exe", "python_file_id": FILE_ID, "pythonw_file_id": FILE_ID,
            "stop_path": None, "env": {"PYTHONDONTWRITEBYTECODE": "1"}}
        closes[role] = {"machine_id": MACHINE, "nonce": specs[role]["nonce"],
            "utc": "2026-10-19T%02d:10:01Z" % (12 + 2*i), "child": {"pid": 2000 + i,
                "creation_filetime": str(134368900000000009 + i), "image": "Z:/python.exe", "image_file_id": FILE_ID,
                "session": 1, "wait0": 258, "exit_code": 259}, "child_exit_code": 0, "bootstrap_exit_code": 0,
            "job_active_after_stage": 0, "forced_remaining_cleanup": False, "normal_stop_forwarded": False}
    raw = {"plan": plan, "admission": admission, "build": results["build"], "run": results["run"],
        "manifest": manifest, "started": started, "admin": admin, "launch": launch, "specs": specs, "closes": closes,
        "environment": environment, "summaries": summaries, "no_work": no_work, "delivery": delivery,
        "failed": failed, "evidence": evidence}
    if change: change(raw)
    # Re-pin each honest producer backlink in order. Mutations reach semantic
    # guards rather than failing on an unrelated stale outer digest.
    evidence["two_stage_plan"] = at(PLAN, plan)
    admission["plan_sha256"] = evidence["two_stage_plan"].sha256
    evidence["two_stage_admission"] = at("Z:/admission08.json", admission)
    for role, result in results.items():
        result.update(plan=evidence["two_stage_plan"].reference, admission=evidence["two_stage_admission"].reference)
    evidence["project_exe_manifest"] = at(PATHS["build"] + "/project-exe-manifest.json", manifest)
    results["build"]["project_exe_manifest"] = evidence["project_exe_manifest"].reference
    evidence["build_only_result"] = at(PATHS["build"] + "/RESULT.json", results["build"])
    started.update(build_result=evidence["build_only_result"].reference, manifest_sha256=evidence["project_exe_manifest"].sha256)
    evidence["admin_started"] = at(PATHS["admin"] + "/STARTED.json", started)
    admin.update(started=evidence["admin_started"].reference, build_result=evidence["build_only_result"].reference,
        manifest_sha256=evidence["project_exe_manifest"].sha256)
    admin_doc = at(PATHS["admin"] + "/RESULT.json", admin)
    evidence["admin_result"] = chain.parse_native08_admin_document_v1(admin_doc.raw, admin_doc.reference)
    launch.update(build_result=evidence["build_only_result"].reference, admin_result=evidence["admin_result"].reference)
    launch["argv"] = ["-I", "-B", REPO + "/" + chain.ADMIN_PATH, "--elevated", "--plan", PLAN,
        "--admission", evidence["two_stage_admission"].path, "--admission-sha256", evidence["two_stage_admission"].sha256,
        "--build-result-sha256", evidence["build_only_result"].sha256, "--execute"]
    evidence["admin_launch_result"] = at(PATHS["admin"] + "/LAUNCH-RESULT.json", launch)
    for value in (results["run"], delivery):
        value.update(build_result=evidence["build_only_result"].reference, admin_result=evidence["admin_result"].reference,
            admin_launch_result=evidence["admin_launch_result"].reference)
    evidence["build_result"] = at(PATHS["run"] + "/RESULT.json", results["run"])
    delivery["run_result_path"] = evidence["build_result"].path
    evidence["production_delivery"] = at(PATHS["run"] + "/production-delivery.json", delivery)
    for role in ("build", "run"):
        evidence[role + "_only_no_work_log"] = no_work[role]
        evidence[role + "_input_summary"] = at(PATHS[role] + "/input-summary.json", summaries[role])
        spec = specs[role]
        spec.update(admission_path=evidence["two_stage_admission"].path, admission_sha256=evidence["two_stage_admission"].sha256)
        spec["stage_args"] = ["--phase", role, "--plan", PLAN, "--admission", spec["admission_path"],
            "--admission-sha256", spec["admission_sha256"]]
        if role == "run": spec["stage_args"] += ["--admin-receipt-sha256", evidence["admin_result"].sha256]
        spec["stage_args"] += ["--execute"]
        evidence[role + "_owner_spec"] = at(plan["roots"]["owner_" + role] + "/SPEC.json", spec)
        closes[role]["spec_sha256"] = evidence[role + "_owner_spec"].sha256
        evidence[role + "_owner_closed"] = at(plan["roots"]["owner_" + role] + "/CLOSED.json", closes[role])
    evidence["build_msvc_environment"] = at(PATHS["build"] + "/msvc-environment/environment-delta.json", environment)
    compatible = evidence["compatibility"].value
    for name in ("base_exe_binding", "target_exe_binding", "build_result", "production_delivery", "source_freeze"):
        compatible[name] = evidence[name].reference
    evidence["compatibility"] = document("compatible08", compatible)
    card = old_card.value
    card["native_transition"] = {key: value for key, value in card["native_transition"].items() if key not in original}
    card["native_transition"].update({name: doc.reference for name, doc in evidence.items()})
    card["native_transition"].update(build_chain=chain.CHAIN)
    card = document("export-card08", card)
    args.capacity_card, args.capacity_card_sha256 = card.path, card.sha256
    return base, old, evidence, card, args


class TwoStage08ConsumerTests(unittest.TestCase):
    def test_complete_ram_protocol_preserves_failed_history_and_unknown_H(self):
        values = two_stage_corpus(); before = {k: v.raw for k, v in values[2].items()}
        result = qualify(values, fixture=True); audit = result.manifest_metadata["build_chain_provenance"]
        self.assertEqual(audit["build_chain"], chain.CHAIN)
        self.assertEqual((audit["attempt02_status_preserved"], audit["failed07_status_preserved"]), ("FAILED", "FAILED"))
        self.assertEqual((audit["regeneration_inputs"], audit["physical_glob_families"], audit["exact_exe_bindings_compared"]), (219, 2, 9))
        self.assertFalse(audit["cross_stage_983_FileID_table_observed"])
        self.assertFalse(result.manifest_metadata["actual_loaded_provider_issued"])
        self.assertEqual(before, {k: v.raw for k, v in values[2].items()})
        with self.assertRaises(ValueError): qualify(values)
        adapter = adapter_module.FrozenExporterAdapterV1()
        with self.assertRaises(ValueError): adapter.prepare(values[4], {}, result)

    def test_actual_cancelled_launch_and_late_child_verification_refuse(self):
        def cancelled(r):
            r["launch"].update(status="FAILED_OR_UNKNOWN", settings_success=False, future_writes=None,
                error={"type": "error", "text": "ShellExecuteEx1223 cancelled"})
            r["launch"].pop("actual_exit_code")
        for change in (cancelled, lambda r: r["launch"].update(actual_exit_code=1),
                lambda r: r["launch"].update(UAC_calls=True), lambda r: r["launch"].update(future_writes=None),
                lambda r: r["admin"].update(status="settings_failed")):
            with self.subTest(change=change), self.assertRaises(ValueError): qualify(two_stage_corpus(change), fixture=True)

    def test_complete_settings_and_exact_exe_FileIDs_required(self):
        changes = [lambda r: r["admin"]["after_settings"].update(ExclusionPath=[]),
            lambda r: r["admin"]["after_settings"]["ExclusionExtension"].append("exe"),
            lambda r: r["admin"]["before_settings"].pop("ExclusionProcess"),
            lambda r: r["admin"]["verified_requested_paths"].pop(),
            lambda r: r["admin"].update(actual_admin=False), lambda r: r["admin"].update(actual_sid="other"),
            lambda r: r["admin"]["exe_bindings"][0]["file_id"].update(file_id="f" * 32),
            lambda r: r["run"]["exe_bindings"][0].update(sha256="e" * 64),
            lambda r: r["manifest"]["files"].pop(),
            lambda r: r["started"]["identity"].update(creation_filetime=134368900000000009),
            lambda r: r["started"]["identity"].update(image="Z:/wrong-python.exe"),
            lambda r: r["admin"].pop("machine_id")]
        for i, change in enumerate(changes):
            with self.subTest(i=i), self.assertRaises(ValueError): qualify(two_stage_corpus(change), fixture=True)

    def test_tasks_are_new_owned_generations_with_actual_terminal_zero(self):
        changes = [lambda r: r["closes"]["build"].update(child_exit_code=None),
            lambda r: r["closes"]["run"].update(job_active_after_stage=1),
            lambda r: r["closes"]["run"].update(forced_remaining_cleanup=True),
            lambda r: r["specs"]["run"].update(nonce=r["specs"]["build"]["nonce"]),
            lambda r: r["specs"]["run"].update(task_name=r["specs"]["build"]["task_name"]),
            lambda r: r["closes"]["run"]["child"].update(creation_filetime=r["closes"]["build"]["child"]["creation_filetime"]),
            lambda r: r["closes"]["run"]["child"].update(creation_filetime="0134368900000000009"),
            lambda r: r["closes"]["run"]["child"].update(image="Z:/other.exe"),
            lambda r: r["specs"]["run"].update(stage_sha256="f" * 64)]
        for i, change in enumerate(changes):
            with self.subTest(i=i), self.assertRaises(ValueError): qualify(two_stage_corpus(change), fixture=True)

    def test_build_run_pipeline_snapshot_and_fixture_boundaries(self):
        def no_work(r):
            r["no_work"]["run"] = text(PATHS["run"] + "/production-no-work.log", b"[0/2] Re-running CMake...\n")
            r["run"]["phases"][0]["log"] = r["no_work"]["run"].reference
            r["summaries"]["run"]["no_work"] = r["no_work"]["run"].reference
        changes = [lambda r: r["run"].update(status="FAILED"), lambda r: r["run"].update(stage="build_only"),
            lambda r: r["build"].update(fixture_executions=1), lambda r: r["run"].update(fixture_executions=8),
            lambda r: r["run"]["phases"][0]["argv"].__setitem__(4, BUILD + "/build.ninja"),
            lambda r: r["build"]["phases"][2]["argv"].__setitem__(6, "9"),
            lambda r: r["run"]["command_attempts"][1].update(original_root_exit_code=1),
            lambda r: r["summaries"]["run"].update(continuous_between_Tasks_lease_claim=True),
            lambda r: r["summaries"]["run"].update(production_leases=982),
            lambda r: r["environment"]["environment_delta"].update(CL="/DOTHER"), no_work]
        for i, change in enumerate(changes):
            with self.subTest(i=i), self.assertRaises(ValueError): qualify(two_stage_corpus(change), fixture=True)

    def test_four_ref_loader_keeps_special_bounds_and_canonical_API(self):
        values = two_stage_corpus(); base, old, evidence, card, _ = values
        indexed = {v.path: v for v in [base, old, card, *evidence.values()]}
        def read(ref):
            result = indexed[ref["path"]]; common._same_ref(ref, result.reference); return result
        with mock.patch.object(loader, "_read_document", side_effect=read), mock.patch.object(loader, "_read_fixture07_no_work_log", side_effect=read), mock.patch.object(loader, "_read_08_admin_result", side_effect=read):
            result = loader.read_native_transition_v1(base_freeze_ref=base.reference, base_native_ref=old.reference,
                capacity_ref=card.reference, machine_id=MACHINE, source_fixture=True)
        self.assertTrue(result.source_fixture)
        bad = {"path": "Z:/admin/RESULT.json", "bytes": chain.ADMIN_JSON_LIMIT + 1, "sha256": "a" * 64}
        with mock.patch.object(loader.Path, "open", side_effect=AssertionError("opened before bound")):
            with self.assertRaises(ValueError): loader._read_08_admin_result(bad)
        raw = b'{"schema":"a","schema":"b"}'
        with self.assertRaises(ValueError): chain.parse_native08_admin_document_v1(raw,
            {"path": "Z:/admin/RESULT.json", "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
        large = json.dumps({"padding": "x" * common.MAX_JSON}).encode()
        large_doc = chain.parse_native08_admin_document_v1(large,
            {"path": "Z:/admin/RESULT.json", "bytes": len(large), "sha256": hashlib.sha256(large).hexdigest()})
        self.assertEqual(len(large_doc.value["padding"]), common.MAX_JSON)
        with self.assertRaises(ValueError): common.parse_document_v1(large, large_doc.reference)
        self.assertEqual(loader.export_native30_views_v1(None)["status"], "DISABLED")

    def test_vocabulary_is_actual_rev3_source_not_an_invented_result(self):
        repo = TOOLS.parent
        for relative, sha in ((chain.PRODUCER_PATH, chain.PRODUCER_SHA), (chain.ADMIN_PATH, chain.ADMIN_SHA), (chain.PLAN_PATH, chain.PLAN_SHA)):
            self.assertEqual(hashlib.sha256((repo/relative).read_bytes()).hexdigest(), sha)
        producer = (repo/chain.PRODUCER_PATH).read_text()
        admin = (repo/chain.ADMIN_PATH).read_text()
        for literal in (chain.SCHEMA, "BUILD_READY_FOR_ADMIN", "OFFLINE_QUALIFIED_NOT_DEPLOYED", "input-summary.json", "admin_launch_result", "fixture_builds", "exe_bindings"):
            self.assertIn(literal, producer)
        for literal in ("native30-exact-nine-admin-started-v1", "native30-exact-nine-admin-registration-v1", "native30-exact-nine-admin-launch-v1", "actual_exit_code", "before_settings", "after_settings"):
            self.assertIn(literal, admin)
        plan = json.loads((repo/chain.PLAN_PATH).read_text())
        self.assertEqual(plan["producer"], {"path": chain.PRODUCER_PATH, "bytes": 25416, "sha256": chain.PRODUCER_SHA})
        self.assertEqual(plan["revision"], 3)
        self.assertEqual(plan["protocol"]["schema"], chain.SCHEMA)
        self.assertEqual(plan["birth_interface"]["source_sha256"], chain.C0_SHA)

    def test_source_inverse_preserves_old_branches_and_exporter_bytes(self):
        root = TOOLS / "g2_saved_campaign"
        s = (root/"native29_to30_export_contract_v1.py").read_text()
        a = s.index('    if chain == "resume02_snapshot07_two_stage08B":')
        b = s.index('    require(chain ==', a); s = s[:a] + s[b:]
        a = s.index('    chain = card.get("native_transition", {}).get("build_chain")')
        b = s.index('    all_docs =', a)
        s = s[:a] + '    raw_name = "fixture07_no_work_log" if card.get("native_transition", {}).get("build_chain") == "resume02_fixture07_snapshot" else None\n    docs = {name: _doc(evidence[name]) for name in evidence_names if name != raw_name}\n' + s[b:]
        a = s.index('    elif transition.get("build_chain") == "resume02_fixture07_snapshot":')
        b = s.index('    require(plan.get("schema")', a)
        s = s[:a] + s[a:b].split('    else:\n')[0].replace('    elif transition.get("build_chain") == "resume02_fixture07_snapshot":', '    else:') + s[b:]
        self.assertEqual(hashlib.sha256(s.encode()).hexdigest(), "d8b624eaba54b355c4fe7c199e33ff21b818b9d1dcc2def9f5a8398c4cea8090")
        s = (root/"export_native30_immutable_sdk_views_v1.py").read_text()
        a = s.index('    reader = _read_document'); b = s.index('    return validate_native_transition_v1', a)
        s = s[:a] + '    evidence = {name: (_read_fixture07_no_work_log if name == "fixture07_no_work_log" else _read_document)(transition.get(name))\n                for name in native_transition_evidence_names_v1(capacity.value)}\n' + s[b:]
        a = s.index('\ndef _read_08_admin_result'); b = s.index('\ndef export_native30_views_v1', a); s = s[:a] + s[b:]
        self.assertEqual(hashlib.sha256(s.encode()).hexdigest(), "f65bd5a175caa37a3ae78cd8cb12565488baa249aae5d78ca08d014fa15ed4a7")
        for name, sha in (("native30_resume_fixture_chain_v1.py", "d9e5dc3c22f3b1fc58f1ab7b93de4f7ccb480c3ed938fdc6b2375d11a814f555"),
            ("native30_resume_fixture07_snapshot_chain_v1.py", "ceddbbfcf4daec435fd19326b3ad446936b2f4384d88e6277c205e3663a49ac3"),
            ("native30_export_adapter_v1.py", "2d4074379371ed91bc38ff0fc532521e277ba2795faad1fd8e9c6dd2593c5298"),
            ("export_immutable_sdk_views_v1.py", "8b6972ac2a82b30c92b531c640df0eb9aa6e43cc205ab9d7d23796d5739da432")):
            self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(), sha)


if __name__ == "__main__": unittest.main()
