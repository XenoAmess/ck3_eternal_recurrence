"""Invented fixtures with the actual resume02/fixture06 producer field names.

No Native receipt or artifact is read. All purported successful phases are
synthetic, and any export goes only through the existing private memory FS.
"""
import ast
import copy
from pathlib import Path
import unittest

from g2_saved_campaign import native30_resume_fixture_chain_v1 as chain
from g2_saved_campaign import native30_export_adapter_v1 as adapter_module
from g2_saved_campaign.test_native30_export_transition_v1 import (
    corpus, document, qualify, MemoryFS, MACHINE)


def at(path, value):
    value = document("temporary", value)
    return type(value)(value.raw, path, value.sha256)


def phase(argv, name, number):
    state = {"argv": argv, "pid": 500 + number, "start_utc": "2026-10-19T10:00:00Z",
        "end_utc": "2026-10-19T10:00:01Z", "original_root_exit_code": 0,
        "owned_active_after": 0, "failure_job_termination": False, "auxiliary_forced_cleanup": []}
    return {"argv": argv, "pid": state["pid"], "start_utc": state["start_utc"],
        "end_utc": state["end_utc"], "returncode": 0, "owned_active_after": 0,
        "auxiliary_cleanup": state, "log": {"path": "Z:/native30/attempt06/" + name,
            "bytes": 4, "sha256": "5" * 64}}, state


def resume_corpus(change=None):
    base, old, evidence, old_card, args = corpus()
    commit = chain.SOURCE_COMMIT
    freeze = at("Z:/native30/evidence/source-freeze.json", {
        **evidence["source_freeze"].value, "commit": commit})
    fixed = {"path": "Z:/native30/build/native30-fixture04/camera_tracking_v1_test.cpp", "bytes": 2647, "sha256": "8" * 64}
    overlay = {"path": "Z:/native30/attempt02/runtime-source-macro-restore.cmake", "bytes": 807, "sha256": "9" * 64}
    fixture_overlay = {"path": "Z:/native30/attempt04/fixture-only-override.cmake", "bytes": 1277, "sha256": "a" * 64}
    graph = {"path": "Z:/native30/attempt02/selected-fileapi-graph.json", "bytes": 6186111, "sha256": "b" * 64}
    repair = document("repair02", {"schema": "native30-separate-resume-source-plan-v1", "machine_id": MACHINE,
        "source_commit": commit, "overlay": {**overlay, "path": "tools/native30_runtime_source_macro_restore.cmake"}})
    production, prod_state = phase(["Z:/python.exe", "-B", "Z:/native30/source/tools/run_native_msvc.py",
        "--build", "--target", *chain.PRODUCTION], "unused-production.log", 0)
    for value in (production, prod_state):
        value["start_utc"], value["end_utc"] = "2026-10-19T09:00:01Z", "2026-10-19T09:20:00Z"
    failed_state = {**prod_state, "argv": ["Z:/python.exe", "--build", "--target", "failed_fixture"],
        "pid": 499, "original_root_exit_code": 1, "failure_job_termination": True,
        "error": "original command exit 1"}
    prior = {"schema": "native30-resume-result-v1", "machine_id": MACHINE, "status": "FAILED",
        "error": {"type": "AuxiliaryContractError", "text": "original command exit 1"},
        "phases": [production], "command_attempts": [prod_state, failed_state], "source_commit": commit,
        "repair_plan": repair.reference, "source_overlay": overlay, "Game_calls": 0, "DLL_loaded": False,
        "owned_active_after": 0, "future_writes": 0, "start_utc": "2026-10-19T09:00:00Z", "end_utc": "2026-10-19T09:30:00Z"}
    artifacts = {"DLL": {"path": "Z:/native30/build/bridge.dll", "bytes": 1234, "sha256": "2" * 64},
        "runtime_archive": {"path": "Z:/native30/build/runtime.lib", "bytes": 2345, "sha256": "3" * 64},
        "map": {"path": "Z:/native30/build/bridge.map", "bytes": 3456, "sha256": "4" * 64}}
    object_pins = [{"path": "Z:/native30/build/native-%04d.obj" % i, "bytes": 10, "sha256": "6" * 64} for i in range(978)]
    extra_artifacts = [{"path": "Z:/native30/build/extra-%d.lib" % i, "bytes": 8, "sha256": "7" * 64} for i in range(2)]
    outputs = [{**pin, "file_id": {"volume_serial": "1", "file_id": "%032x" % i}, "held_share_read_only": True}
        for i, pin in enumerate([*artifacts.values(), *extra_artifacts, *object_pins], 1)]
    inventory = {"machine_id": MACHINE, "future_writes": 0, "files_before_this_manifest": {"files": [
        {"path": pin["path"].split("Z:/native30/")[1], "eof": pin["bytes"]} for pin in outputs]}}
    current_graph = {"path": "Z:/native30/attempt06/current-configured-graph.json", "bytes": 6186222, "sha256": "d" * 64}
    delta = {"selected_commands": 995, "production_and_other_fixture_argv_identical": True,
        "current_graph": current_graph, "fixed_fixture": fixed, "semantic_link_target_count": 12, "production_compile_rows": 978,
        "old_fixture_argv": ["Z:/cl.exe", "Z:/native30/source/" + chain.FIXTURE_SOURCE, "/FoCMakeFiles/test.dir/src/test.obj", "/O2"],
        "new_fixture_argv": ["Z:/cl.exe", fixed["path"], "/FoCMakeFiles/test.dir/native30-fixture04/test.obj", "/O2"]}
    plan = {"schema": "native30-fixture06-current-config-plan-v1", "machine_id": MACHINE,
        "source_commit": commit, "helper_pins": {chain.FIXTURE_SOURCE: fixed["sha256"]}, "prior_pins": []}
    reused = {"source_commit": commit, "compile_rows": [{"source": {"path": "Z:/native30/source/native/source.cpp",
        "bytes": 3, "sha256": "4" * 64}, "argv_sha256": "c" * 64, "output": item["path"]} for item in object_pins],
        "outputs": outputs, "original_graph": graph, "known_not_generated": [], "prior_configuration": delta}
    phases, states = [], []
    def run(argv, name):
        row, state = phase(argv, name, len(phases) + 1); phases.append(row); states.append(state)
    run(["Z:/ninja.exe", "-C", "Z:/native30/build", "-n", *chain.PRODUCTION], "production-no-work.log")
    for i, fixture in enumerate(evidence["build_plan"].value["fixtures"], 1):
        stage = "fixture-%02d/" % i
        run(["Z:/python.exe", "-B", "Z:/native30/source/tools/run_native_msvc.py", "--build", "--target", fixture["target"]], stage + "producer.log")
        run(["Z:/python.exe", "-B", "Z:/native30/source/tools/register_project_exe_exclusions.py",
            "--manifest", "Z:/native30/attempt06/" + stage + "project-exe-manifest.json",
            "--receipt", "Z:/native30/attempt06/" + stage + "project-exe-receipt.json"], stage + "registration.log")
        arguments = [value.replace("$MACHINE_ID", MACHINE).replace("$OBSERVED_UTC", "2026-10-19T09:59:59Z")
            for value in fixture.get("args", [])]
        run(["Z:/native30/build/" + fixture["artifact"], *arguments], stage + "fixture.log")
        if fixture.get("postcheck"):
            run(["Z:/python.exe", "-B", "Z:/native30/source/" + fixture["postcheck"], phases[-1]["log"]["path"]], stage + "postcheck.log")
    run(["Z:/ninja.exe", "-C", "Z:/native30/build", "-t", "deps"], "deps.log")
    run(["Z:/dumpbin.exe", "/exports", artifacts["DLL"]["path"]], "exports.log")
    run(["Z:/lib.exe", "/LIST", artifacts["runtime_archive"]["path"]], "members.log")
    result = {"schema": "native30-fixture06-result-v1", "machine_id": MACHINE,
        "status": "OFFLINE_QUALIFIED_NOT_DEPLOYED", "production_recompiled": False,
        "configuration_reused_from_attempt04": True, "phases": phases, "command_attempts": states,
        "Game_calls": 0, "DLL_loaded": False, "owned_active_after": 0, "future_writes": 0,
        "start_utc": "2026-10-19T09:45:00Z", "end_utc": "2026-10-19T11:00:00Z"}
    delivery = {**artifacts, "deployed": False, "source_commit": commit, "fixed_fixture": fixed,
        "production_reused_from_attempt02": True, "prior_failures_requalified": False,
        "actual_Game_provider_or_camera_qualification": "NOTRUN"}
    raw = {"prior": prior, "inventory": inventory, "result": result, "delivery": delivery,
        "reused": reused, "delta": delta, "plan": plan, "fixed": fixed, "overlay": overlay, "fixture_overlay": fixture_overlay}
    if change: change(raw)
    prior_doc = at("Z:/native30/attempt02/RESULT.json", prior)
    closed_doc = at("Z:/native30/attempt02/FILES-CLOSED.json", inventory)
    plan["prior_pins"] = [prior_doc.reference, closed_doc.reference, freeze.reference, overlay, fixed, fixture_overlay, graph]
    plan_doc = document("plan06", plan)
    result["plan"] = plan_doc.reference
    result_doc = at("Z:/native30/attempt06/RESULT.json", result)
    reused["prior_result"] = prior_doc.reference
    evidence.update(source_freeze=freeze, build_result=result_doc,
        production_delivery=at("Z:/native30/attempt06/production-delivery.json", delivery),
        attempt02_result=prior_doc, attempt02_closed=closed_doc, attempt02_repair_plan=repair,
        reused_production=at("Z:/native30/attempt06/reused-production.json", reused), fixture06_plan=plan_doc,
        fixture_graph_delta=at("Z:/native30/attempt06/prior-current-graph-delta.json", delta))
    target_binding = evidence["target_exe_binding"].value; target_binding["source_freeze"] = freeze.reference
    evidence["target_exe_binding"] = document("target-binding", target_binding)
    compat = evidence["compatibility"].value
    for name in ("base_exe_binding", "target_exe_binding", "build_result", "production_delivery", "source_freeze"):
        compat[name] = evidence[name].reference
    evidence["compatibility"] = document("compat", compat)
    card = old_card.value
    card["native_transition"].update({name: doc.reference for name, doc in evidence.items()})
    card["native_transition"].update(build_chain=chain.CHAIN, source_commit=commit,
        source_overlay=overlay, fixed_fixture=fixed, fixture_overlay=fixture_overlay, current_graph=current_graph)
    capacity = document("card", card); args.capacity_card_sha256 = capacity.sha256
    return base, old, evidence, capacity, args


class ResumeFixtureChainTests(unittest.TestCase):
    def test_actual_schema_positive_preserves_FAILED_and_no_synthetic_wholeclean_fields(self):
        values = resume_corpus(); evidence = values[2]
        before = {name: doc.raw for name, doc in evidence.items()}
        transition = qualify(values, fixture=True)
        audit = transition.manifest_metadata["build_chain_provenance"]
        self.assertEqual(audit["attempt02_status_preserved"], "FAILED")
        self.assertEqual(evidence["build_result"].value["schema"], "native30-fixture06-result-v1")
        self.assertEqual(evidence["attempt02_result"].value["schema"], "native30-resume-result-v1")
        self.assertNotIn("plan", evidence["attempt02_result"].value)
        self.assertNotIn("source_freeze", evidence["production_delivery"].value)
        self.assertFalse(audit["prior_failures_requalified"])
        self.assertEqual(before, {name: doc.raw for name, doc in evidence.items()})
        self.assertTrue(transition.source_fixture)

    def test_each_real_boundary_refuses_instead_of_requalifying_prior_failure(self):
        changes = [lambda r: r["prior"].update(status="BUILT_FIXTURES_PASS_NOT_DEPLOYED"),
            lambda r: r["prior"]["phases"][0].update(returncode=1),
            lambda r: r["prior"]["command_attempts"][0].update(owned_active_after=None),
            lambda r: r["result"].update(status="FAILED"),
            lambda r: r["result"].update(schema="native30-fixture05-result-v1"),
            lambda r: r["result"].update(configuration_reused_from_attempt04=False),
            lambda r: r["result"]["command_attempts"][0].update(original_root_exit_code=1),
            lambda r: r["result"].update(future_writes=None),
            lambda r: r["delivery"].update(prior_failures_requalified=True),
            lambda r: r["delivery"].update(source_commit="f" * 40),
            lambda r: r["reused"]["outputs"][0].update(held_share_read_only=False),
            lambda r: r["inventory"]["files_before_this_manifest"]["files"][0].update(eof=0),
            lambda r: r["delta"]["new_fixture_argv"].__setitem__(-1, "/Od"),
            lambda r: r["result"]["phases"].pop(0),
            lambda r: r["result"]["phases"][1]["argv"].append("--configure"),
            lambda r: r["result"]["phases"][1]["argv"].__setitem__(-1, chain.PRODUCTION[0])]
        for number, change in enumerate(changes):
            with self.subTest(number=number), self.assertRaises(ValueError): qualify(resume_corpus(change))

    def test_actual_schema_reaches_unchanged_validator_and_complete_memory_core(self):
        values = resume_corpus(); adapter = adapter_module.FrozenExporterAdapterV1()
        fs = MemoryFS(adapter, values); context = adapter.validate_base(values[4])
        ready = adapter.prepare(values[4], context, qualify(values))
        self.assertEqual(fs.operations, [])
        adapter.export(values[4], ready)
        audit = fs.json["SOURCE-FREEZE.json"]["native_transition"]["build_chain_provenance"]
        self.assertEqual(audit["build_chain"], chain.CHAIN)
        self.assertEqual(audit["attempt02_status_preserved"], "FAILED")
        self.assertEqual(context["native"]["native_build_label"], "native29-synthetic")
        self.assertFalse(fs.json["REFERENCE-FREEZE.json"]["runtime_admitted"])

    def test_producer_literal_schemas_and_success_status_match_the_fixture(self):
        root = Path(__file__).resolve().parent
        for name, schema in (("build_native30_resume_20261019.py", "native30-resume-result-v1"),
                             ("qualify_native30_fixture06_20261020.py", "native30-fixture06-result-v1")):
            tree = ast.parse((root / name).read_bytes())
            literals = {node.value for node in ast.walk(tree) if isinstance(node, ast.Constant) and isinstance(node.value, str)}
            self.assertIn(schema, literals)
            self.assertIn("command_attempts", literals)
            if "fixture06" in name:
                self.assertIn("OFFLINE_QUALIFIED_NOT_DEPLOYED", literals)
                self.assertIn("configuration_reused_from_attempt04", literals)
                self.assertIn("production_reused_from_attempt02", literals)


if __name__ == "__main__":
    unittest.main()
