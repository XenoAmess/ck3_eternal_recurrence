"""Synthetic07 source receipts only; real core runs on the private memory FS.

No actual Native snapshot, output, log or operating-system object is opened.
The checked-in producer/plan are read solely to check the fixture vocabulary.
"""
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
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from g2_saved_campaign import native30_resume_fixture07_snapshot_chain_v1 as chain
from g2_saved_campaign import native30_export_adapter_v1 as adapter_module
from g2_saved_campaign import export_native30_immutable_sdk_views_v1 as loader
from g2_saved_campaign.test_native30_export_transition_v1 import document, qualify, MemoryFS, MACHINE
from g2_saved_campaign.test_native30_resume_fixture_chain_v1 import resume_corpus, at, phase

ROOT = "Z:/native30"
BUILD = ROOT + "/build"
ATTEMPT = ROOT + "/attempt07"


def extended(path, size, sha, mtime=1000):
    return {"path": path, "bytes": size, "sha256": sha, "mtime_ns": mtime}


def snapshot_corpus(change=None):
    base, old, evidence, card, args = resume_corpus()
    original_freeze = evidence["source_freeze"].value
    original_freeze["files"].append({"path": "tools/run_native_msvc.py", "bytes": 12,
        "sha256": "e" * 64, "git_blob": "1" * 40})
    prior = evidence["attempt02_result"].value
    closed = evidence["attempt02_closed"].value
    reused = evidence["reused_production"].value
    # Real guard.output_from_command may return a relative /Fo and original
    # closed inventory preserves mixed case. Never depend on host path rules.
    first = reused["compile_rows"][0]["output"]
    replacement = BUILD + "/CMakeFiles/Actor.DIR/First.OBJ"
    for row in reused["outputs"]:
        if row["path"] == first: row["path"] = replacement
    for row in closed["files_before_this_manifest"]["files"]:
        if row["path"] == first.split(ROOT + "/")[1]: row["path"] = replacement.split(ROOT + "/")[1]
    reused["compile_rows"][0]["output"] = "CMakeFiles/Actor.DIR/First.OBJ"
    fixed = evidence["production_delivery"].value["fixed_fixture"]
    overlay = prior["source_overlay"]
    overlay04 = card.value["native_transition"]["fixture_overlay"]
    fixtures = evidence["build_plan"].value["fixtures"]
    targets = chain.PRODUCTION + [row["target"] for row in fixtures]
    tools = {name: {"path": "Z:/tools/" + name + ".exe", "bytes": 10, "sha256": "1" * 64}
        for name in ("ninja", "cl", "cmake", "dumpbin", "lib")}
    tools["vcvars64"] = {"path": "Z:/VisualStudio/VC/Auxiliary/Build/vcvars64.bat", "bytes": 39, "sha256": "2" * 64}
    inventory = {"machine_id": MACHINE, "tool_pins": tools}
    inputs = [extended(BUILD + "/CMakeCache.txt", 10, "3" * 64),
        extended(overlay04["path"], overlay04["bytes"], overlay04["sha256"]),
        extended(overlay["path"], overlay["bytes"], overlay["sha256"])]
    inputs += [extended("Z:/CMake/modules/input%03d.cmake" % i, 9, "4" * 64) for i in range(216)]
    manifest = extended(BUILD + "/build.ninja", 15398163, "e" * 64, 2000)
    rules = extended(BUILD + "/CMakeFiles/rules.ninja", 500, "8" * 64)
    glob = {"script": extended(BUILD + "/CMakeFiles/VerifyGlobs.cmake", 1234, "9" * 64),
        "families": [{"pattern": ROOT + "/source/ck3_autonomous_player/native_bridge/src/" + pattern,
            "entries": 10, "ordered_paths_sha256": "2" * 64, "equal": True}
            for pattern in ("ck3_12002*.cpp", "ck3_12002_*_test.cpp")], "script_executed": False}
    digest = hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest()
    snapshot = {"path": ATTEMPT + "/production-manifest.ninja", "bytes": manifest["bytes"], "sha256": manifest["sha256"]}
    identity = {"start_utc": "2026-10-19T09:50:00Z", "end_utc": "2026-10-19T09:51:00Z",
        "original": manifest, "snapshot": snapshot, "same_cwd": BUILD, "relative_rules": rules,
        "inputs": {"manifest": manifest, "rules": rules, "glob": glob, "inputs": inputs, "inputs_sha256": digest,
            "cwd": BUILD, "relative_include": "CMakeFiles\\rules.ninja",
            "logs": [BUILD + "/.ninja_log", BUILD + "/.ninja_deps"],
            "snapshot_evaluation": "Synthetic model of the original producer literal; no Native evaluation."}}
    equivalent = {"original": {"path": ATTEMPT + "/original-commands.log", "bytes": 5650086, "sha256": "c" * 64},
        "snapshot": {"path": ATTEMPT + "/snapshot-commands.log", "bytes": 5650086, "sha256": "c" * 64},
        "byte_identical": True, "targets": targets}
    environment = {"tools": {name: tools[name]["path"] for name in ("vcvars64", "cmake", "ninja", "cl")},
        "environment_delta": {"PATH": "Z:/tools;Z:/Windows", "TEMP": ATTEMPT + "/msvc-environment/.msvc-temp"}}
    plan = {"schema": "native30-fixture07-snapshot-plan-v1", "machine_id": MACHINE,
        "source_commit": chain.SOURCE_COMMIT, "root": ROOT, "attempt_root": ATTEMPT,
        "producer": {"path": chain.PRODUCER_PATH, "bytes": 37100, "sha256": chain.PRODUCER_SHA},
        "helper_pins": {chain.SNAPSHOT_HELPER: chain.SNAPSHOT_SHA, chain.CAPTURE_HELPER: chain.CAPTURE_SHA,
            chain.FIXTURE_SOURCE: fixed["sha256"]}, "prior_pins": [],
        "configured_inputs_expected": {"manifest": manifest["sha256"], "rules": rules["sha256"],
            "inputs": digest, "glob_script": glob["script"]["sha256"]},
        "file_peak_quote": {"snapshot_EOF": manifest["bytes"]},
        "native_build_label": chain.NATIVE30_BUILD_LABEL, "label_is_external_pin_metadata_not_compiled_DLL_string": True}
    admission = {"machine_id": MACHINE, "status": "ADMITTED", "root": ROOT, "attempt_root": ATTEMPT,
        "source_commit": chain.SOURCE_COMMIT, "producer_sha256": chain.PRODUCER_SHA,
        "implementation_commit": "a" * 40, "jobs": 2, "deadline_utc": "2026-10-20T00:00:00Z",
        "hard_bytes": 1610612736, "source_charge_cap_bytes": 100663296, "metadata_charge_cap_bytes": 134217728,
        "aggregate_includes_prior_retained": True, "prior_retained_allocation_bytes": 670742624,
        "new_reservation_bytes": 0, "minimum_free_bytes": 2*1024**3, "quota_remaining_bytes": 1610612736}
    delta = evidence["fixture_graph_delta"].value
    delta["current_graph"]["path"] = ATTEMPT + "/current-configured-graph.json"
    reused["prior_configuration"] = {key: delta[key] for key in (
        "selected_commands", "production_and_other_fixture_argv_identical", "old_fixture_argv", "new_fixture_argv")}
    delivery = evidence["production_delivery"].value
    delivery.update(native_build_label=chain.NATIVE30_BUILD_LABEL, native_build_label_is_metadata=True)
    phases, states = [], []
    def run(argv, log):
        row, state = phase(argv, log, len(phases) + 1)
        moment = datetime(2026, 10, 19, 10, tzinfo=timezone.utc) + timedelta(seconds=2*len(phases))
        for value in (row, state):
            value.update(start_utc=moment.isoformat(), end_utc=(moment+timedelta(seconds=1)).isoformat())
        row["log"]["path"] = ATTEMPT + "/" + log
        phases.append(row); states.append(state)
        return row
    ninja, snap, python = tools["ninja"]["path"], snapshot["path"], "Z:/python.exe"
    run([ninja, "-C", BUILD, "-f", manifest["path"], "-t", "commands", *targets], "original-commands.log")["log"] = equivalent["original"]
    run([ninja, "-C", BUILD, "-f", snap, "-t", "commands", *targets], "snapshot-commands.log")["log"] = equivalent["snapshot"]
    run([ninja, "-C", BUILD, "-f", snap, "-n", "-d", "explain", *chain.PRODUCTION], "production-no-work.log")
    work = ATTEMPT + "/msvc-environment"
    run([python, "-B", "Z:/repo/" + chain.CAPTURE_HELPER, "--frozen-tool", ROOT + "/source/tools/run_native_msvc.py",
        "--tool-sha", "e" * 64, "--installation", "Z:/VisualStudio", "--work", work,
        "--output", work + "/environment-delta.json"], "msvc-environment/initializer.log")
    for i, fixture in enumerate(fixtures, 1):
        stage = "fixture-%02d/" % i
        run([ninja, "-C", BUILD, "-f", snap, "-j", str(admission["jobs"]), fixture["target"]], stage + "producer.log")
        run([python, "-B", ROOT + "/source/tools/register_project_exe_exclusions.py",
            "--manifest", ATTEMPT + "/" + stage + "project-exe-manifest.json",
            "--receipt", ATTEMPT + "/" + stage + "project-exe-receipt.json"], stage + "registration.log")
        argv = [v.replace("$MACHINE_ID", MACHINE).replace("$OBSERVED_UTC", "2026-10-19T09:59:59Z")
                for v in fixture.get("args", [])]
        executed = run([BUILD + "/" + fixture["artifact"], *argv], stage + "fixture.log")
        if fixture.get("postcheck"):
            run([python, "-B", ROOT + "/source/" + fixture["postcheck"], executed["log"]["path"]], stage + "postcheck.log")
    run([ninja, "-C", BUILD, "-f", snap, "-t", "deps"], ".msvc-temp/environment/actual-ninja-deps.txt")
    run([tools["dumpbin"]["path"], "/exports", delivery["DLL"]["path"]], "exports.log")
    run([tools["lib"]["path"], "/LIST", delivery["runtime_archive"]["path"]], "runtime-members.log")
    result = {"schema": "native30-fixture07-result-v1", "machine_id": MACHINE,
        "status": "OFFLINE_QUALIFIED_NOT_DEPLOYED", "production_recompiled": False,
        "configuration_reused_from_attempt04": True, "native_build_label": chain.NATIVE30_BUILD_LABEL,
        "native_build_label_is_metadata": True, "phases": phases, "command_attempts": states,
        "Game_calls": 0, "DLL_loaded": False, "owned_active_after": 0, "future_writes": 0,
        "start_utc": "2026-10-19T09:45:00Z", "end_utc": "2026-10-19T11:00:00Z"}
    raw = {"result": result, "delivery": delivery, "prior": prior, "closed": closed, "reused": reused,
        "delta": delta, "freeze": original_freeze, "identity": identity, "equivalent": equivalent,
        "environment": environment, "plan": plan, "admission": admission, "inventory": inventory,
        "no_work_raw": b"ninja: Entering directory 'Z:/native30/build'\r\nninja: no work to do.\r\n"}
    if change: change(raw)
    freeze_doc = at(ROOT + "/evidence/source-freeze.json", raw["freeze"])
    prior_doc = at(ROOT + "/attempt02/RESULT.json", raw["prior"])
    closed_doc = at(ROOT + "/attempt02/FILES-CLOSED.json", raw["closed"])
    inventory_doc = document("inventory07", raw["inventory"])
    plan["helper_pins"][chain.INVENTORY_PATH] = inventory_doc.sha256
    plan["prior_pins"] = [prior_doc.reference, closed_doc.reference, freeze_doc.reference, overlay, overlay04,
                          fixed, reused["original_graph"]]
    plan_doc = document("plan07", raw["plan"])
    admission["plan_sha256"] = plan_doc.sha256
    admission_doc = document("native-admission07", raw["admission"])
    result.update(plan=plan_doc.reference, admission=admission_doc.reference)
    reused["prior_result"] = prior_doc.reference
    raw_ref = {"path": ATTEMPT + "/production-no-work.log", "bytes": len(raw["no_work_raw"]),
               "sha256": hashlib.sha256(raw["no_work_raw"]).hexdigest()}
    # Repair the actual log reference for content-negative cases, ensuring the
    # literal-NoWork guard rather than an unrelated stale outer hash refuses.
    phases[2]["log"] = raw_ref
    text_doc = chain.parse_native07_no_work_log_v1(raw["no_work_raw"], raw_ref)
    evidence.pop("fixture06_plan")
    evidence.update(source_freeze=freeze_doc, build_result=at(ATTEMPT + "/RESULT.json", raw["result"]),
        production_delivery=at(ATTEMPT + "/production-delivery.json", raw["delivery"]),
        attempt02_result=prior_doc, attempt02_closed=closed_doc,
        reused_production=at(ATTEMPT + "/reused-production.json", raw["reused"]), fixture07_plan=plan_doc,
        fixture_graph_delta=at(ATTEMPT + "/prior-current-graph-delta.json", raw["delta"]),
        fixture07_admission=admission_doc, snapshot_identity=at(ATTEMPT + "/snapshot-identity.json", raw["identity"]),
        snapshot_command_equivalence=at(ATTEMPT + "/snapshot-command-equivalence.json", raw["equivalent"]),
        msvc_environment=at(work + "/environment-delta.json", raw["environment"]), tool_inventory=inventory_doc)
    evidence[chain.RAW_EVIDENCE_NAME] = text_doc
    binding = evidence["target_exe_binding"].value; binding["source_freeze"] = freeze_doc.reference
    evidence["target_exe_binding"] = document("target-binding07", binding)
    compatible = evidence["compatibility"].value
    for name in ("base_exe_binding", "target_exe_binding", "build_result", "production_delivery", "source_freeze"):
        compatible[name] = evidence[name].reference
    evidence["compatibility"] = document("compatible07", compatible)
    admitted = card.value
    admitted["native_transition"].pop("fixture06_plan")
    admitted["native_transition"].update({name: doc.reference for name, doc in evidence.items()})
    admitted["native_transition"].update(build_chain=chain.CHAIN, current_graph=delta["current_graph"])
    card = document("export-card07", admitted)
    args.capacity_card, args.capacity_card_sha256 = card.path, card.sha256
    return base, old, evidence, card, args


class Snapshot07ChainTests(unittest.TestCase):
    def test_positive_snapshot_pipeline_preserves_FAILED_and_all_original_bytes(self):
        values = snapshot_corpus(); evidence = values[2]
        before = {name: doc.raw for name, doc in evidence.items()}
        result = qualify(values, fixture=True)
        audit = result.manifest_metadata["build_chain_provenance"]
        self.assertEqual(audit["build_chain"], chain.CHAIN)
        self.assertEqual(audit["attempt02_status_preserved"], "FAILED")
        self.assertEqual((audit["regeneration_inputs"], audit["physical_glob_families"]), (219, 2))
        self.assertEqual((audit["production_compile_rows"], audit["retained_outputs"]), (978, 983))
        self.assertIn("no independent OS cwd field", audit["cwd_evidence"])
        self.assertTrue(result.source_fixture)
        self.assertFalse(result.manifest_metadata["actual_loaded_provider_issued"])
        self.assertEqual(before, {name: doc.raw for name, doc in evidence.items()})

    def test_07_full_unchanged_memory_exporter_core_preserves_base29(self):
        values = snapshot_corpus(); adapter = adapter_module.FrozenExporterAdapterV1()
        fs = MemoryFS(adapter, values); context = adapter.validate_base(values[4])
        ready = adapter.prepare(values[4], context, qualify(values))
        self.assertEqual(fs.operations, [])
        adapter.export(values[4], ready)
        audit = fs.json["SOURCE-FREEZE.json"]["native_transition"]["build_chain_provenance"]
        self.assertEqual(audit["build_chain"], chain.CHAIN)
        self.assertEqual(context["native"]["native_build_label"], "native29-synthetic")
        self.assertEqual(fs.json["REFERENCE-FREEZE.json"]["native_build_label"], chain.NATIVE30_BUILD_LABEL)
        self.assertFalse(fs.json["REFERENCE-FREEZE.json"]["runtime_admitted"])

    def test_snapshot_input_and_prior_boundaries_refuse(self):
        changes = [lambda r: r["result"].update(status="FAILED", error={"text": "registration exit 1"}),
            lambda r: r["result"].update(schema="native30-fixture06-result-v1"),
            lambda r: r["prior"].update(status="OFFLINE_QUALIFIED_NOT_DEPLOYED"),
            lambda r: r["identity"]["snapshot"].update(sha256="a" * 64),
            lambda r: r["identity"].update(same_cwd="Z:/wrong-build"),
            lambda r: r["identity"]["inputs"].update(relative_include="foreign/rules.ninja"),
            lambda r: r["identity"]["inputs"]["inputs"].pop(),
            lambda r: r["identity"]["inputs"]["inputs"][0].update(mtime_ns=999999),
            lambda r: r["identity"]["inputs"].update(inputs_sha256="f" * 64),
            lambda r: r["identity"]["inputs"]["glob"]["families"][0].update(equal=False),
            lambda r: r["equivalent"]["snapshot"].update(sha256="b" * 64),
            lambda r: r["equivalent"]["targets"].pop(),
            lambda r: r["reused"]["compile_rows"][0].update(output="../../foreign.obj"),
            lambda r: r["result"].update(owned_active_after=None),
            lambda r: r["delivery"].update(prior_failures_requalified=True)]
        for index, change in enumerate(changes):
            with self.subTest(index=index), self.assertRaises(ValueError): qualify(snapshot_corpus(change))

    def test_commands_environment_and_root0_fake_NoWork_refuse(self):
        def wrong_build(r): r["result"]["phases"][4]["argv"][4] = BUILD + "/build.ninja"
        def no_work(r): r["no_work_raw"] = b"ninja: Entering directory 'Z:/native30/build'\n[0/2] Re-running CMake...\n"
        changes = [wrong_build, no_work,
            lambda r: r["result"]["phases"][2]["argv"].__setitem__(2, "Z:/wrong-build"),
            lambda r: r["result"]["phases"][4]["argv"].__setitem__(6, "5"),
            lambda r: r["result"]["phases"][4]["argv"].__setitem__(0, "Z:/foreign/ninja.exe"),
            lambda r: r["result"]["command_attempts"][3].update(original_root_exit_code=1),
            lambda r: r["environment"]["environment_delta"].update(CL="/DNDEBUG"),
            lambda r: r["environment"]["environment_delta"].update(API_TOKEN="synthetic secret"),
            lambda r: r["environment"]["tools"].update(cl="Z:/foreign/cl.exe"),
            lambda r: r["result"]["phases"].pop(6),
            lambda r: r["result"]["command_attempts"][6].update(owned_active_after=None)]
        for index, change in enumerate(changes):
            with self.subTest(index=index), self.assertRaises(ValueError): qualify(snapshot_corpus(change))

    def test_bounded_raw_NoWork_type_and_default_OFF_have_no_IO(self):
        values = snapshot_corpus(); raw = values[2][chain.RAW_EVIDENCE_NAME]
        with self.assertRaises(ValueError): chain.parse_native07_no_work_log_v1(raw.raw, {**raw.reference, "sha256": "0" * 64})
        with self.assertRaises(ValueError): chain.parse_native07_no_work_log_v1(b"x" * 8193, {**raw.reference, "bytes": 8193})
        with self.assertRaises(ValueError): chain.parse_native07_no_work_log_v1(raw.raw, {**raw.reference, "path": ATTEMPT + "/arbitrary.bin"})
        with mock.patch.object(loader, "_read_document", side_effect=AssertionError("disabled IO")), mock.patch.object(
                loader, "_read_fixture07_no_work_log", side_effect=AssertionError("disabled raw IO")):
            self.assertEqual(loader.export_native30_views_v1(None)["status"], "DISABLED")

    def test_actual_failed_registration_prefix_and_absent_delivery_cannot_export(self):
        def stopped(r):
            r["result"].update(status="FAILED", error={"text": "registration exit 1"})
            r["result"]["phases"][:] = r["result"]["phases"][:5]
            r["result"]["command_attempts"][:] = r["result"]["command_attempts"][:6]
            r["result"]["command_attempts"][-1].update(original_root_exit_code=1, failure_job_termination=True)
        values = snapshot_corpus(stopped)
        with self.assertRaises(ValueError): qualify(values)
        values[2].pop("production_delivery")
        with self.assertRaises(ValueError): qualify(values)

    def test_fixed_text_reader_checks_bound_before_open_and_keeps_original_bytes(self):
        text = snapshot_corpus()[2][chain.RAW_EVIDENCE_NAME]
        class InputPath:
            def __init__(self, path): self.name = ntpath.basename(path)
            def is_absolute(self): return True
            def open(self, mode):
                if mode != "rb": raise AssertionError("readonly log")
                return io.BytesIO(text.raw)
        with mock.patch.object(loader, "Path", InputPath):
            self.assertEqual(loader._read_fixture07_no_work_log(text.reference), text)
        with mock.patch.object(loader, "Path", side_effect=AssertionError("must reject before open")):
            with self.assertRaises(ValueError):
                loader._read_fixture07_no_work_log({**text.reference, "bytes": 8193})

    def test_public_four_ref_loader_uses_only_07_fixed_text_reader(self):
        values = snapshot_corpus()
        documents = {doc.path: doc for doc in (values[0], values[1], values[3], *values[2].values())}
        text = values[2][chain.RAW_EVIDENCE_NAME]
        with mock.patch.object(loader, "_read_document", side_effect=lambda ref: documents[ref["path"]]), mock.patch.object(
                loader, "_read_fixture07_no_work_log", return_value=text) as read_text:
            result = loader.read_native_transition_v1(base_freeze_ref=values[0].reference,
                base_native_ref=values[1].reference, capacity_ref=values[3].reference,
                machine_id=MACHINE, source_fixture=True)
        read_text.assert_called_once_with(text.reference)
        self.assertTrue(result.source_fixture)
        self.assertEqual(result.manifest_metadata["build_chain_provenance"]["build_chain"], chain.CHAIN)

    def test_literal_fixture_vocabulary_matches_the_frozen_real_producer_and_plan(self):
        root = Path(__file__).resolve().parents[2]
        producer = (root / chain.PRODUCER_PATH).read_bytes()
        self.assertEqual(hashlib.sha256(producer).hexdigest(), chain.PRODUCER_SHA)
        literals = {n.value for n in ast.walk(ast.parse(producer)) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
        for value in ("native30-fixture07-result-v1", "OFFLINE_QUALIFIED_NOT_DEPLOYED", "snapshot-identity.json",
                "snapshot-command-equivalence.json", "same_cwd", "environment-delta.json", "native_build_label_is_metadata"):
            self.assertIn(value, literals)
        plan = json.loads((root / "docs/ck3-native-ai/evidence/native30-fixture07-snapshot-plan-2026-10-20.json").read_bytes())
        self.assertEqual(plan["schema"], "native30-fixture07-snapshot-plan-v1")
        self.assertEqual(plan["producer"]["sha256"], chain.PRODUCER_SHA)
        self.assertEqual(plan["native_build_label"], chain.NATIVE30_BUILD_LABEL)


if __name__ == "__main__": unittest.main()
