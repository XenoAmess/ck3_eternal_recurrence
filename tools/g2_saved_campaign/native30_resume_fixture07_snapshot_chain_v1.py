"""Finite actual02 -> snapshot07 closure. Metadata only; no artifact/OS reads.

The prior FAILED result is never promoted. A byte-identical loader snapshot,
the owned initializer and every actual fixture must close independently.
"""
from dataclasses import dataclass
import hashlib
import json
import ntpath

from g2_saved_campaign.native29_to30_export_contract_v1 import (
    NATIVE30_BUILD_LABEL, require, _ref, _path, _sha, _same_ref, _time)
from g2_saved_campaign.native30_resume_fixture_chain_v1 import (
    PRODUCTION, SOURCE_COMMIT, FIXTURE_SOURCE, _commands_closed, _prior)

CHAIN = "resume02_fixture07_snapshot"
RAW_EVIDENCE_NAME = "fixture07_no_work_log"
EXTRA_EVIDENCE = ("attempt02_result", "attempt02_repair_plan", "attempt02_closed",
    "reused_production", "fixture07_plan", "fixture_graph_delta", "fixture07_admission",
    "snapshot_identity", "snapshot_command_equivalence", "msvc_environment", "tool_inventory",
    RAW_EVIDENCE_NAME)
PRODUCER_PATH = "tools/g2_saved_campaign/qualify_native30_fixture07_20261020.py"
PRODUCER_SHA = "b22eb598dbfdc01359dd1e15c65132b0fbb37bab23840df3b15b2e8ce32df4ae"
SNAPSHOT_HELPER = "tools/g2_saved_campaign/native30_ninja_snapshot_contract_20261020.py"
SNAPSHOT_SHA = "5aead409ffebb876f5ac08e50a9131ff3ddc6ef46bc8e011793f9d735b05f1d4"
CAPTURE_HELPER = "tools/g2_saved_campaign/native30_capture_msvc_environment_20261020.py"
CAPTURE_SHA = "b26d675482b7b5aa5cf398f8d08cc381d31c7bd6d9e2db43502986ec4cd42900"
INVENTORY_PATH = "docs/ck3-native-ai/evidence/native30-existing-config-output-inventory-2026-10-19.json"
RAW_LOG_LIMIT = 8192


@dataclass(frozen=True)
class Native07NoWorkLogV1:
    """Pinned text evidence for exactly one log; never a custody token."""
    raw: bytes
    path: str
    sha256: str

    @property
    def reference(self):
        return {"path": self.path, "bytes": len(self.raw), "sha256": self.sha256}


def parse_native07_no_work_log_v1(raw, reference):
    _ref(reference)
    require(type(raw) is bytes and len(raw) <= RAW_LOG_LIMIT
            and len(raw) == reference["bytes"] and hashlib.sha256(raw).hexdigest() == reference["sha256"]
            and ntpath.basename(reference["path"]) == "production-no-work.log",
            "exact bounded07 NoWork log bytes required")
    return Native07NoWorkLogV1(raw, reference["path"], reference["sha256"])


def _zero(value):
    require(type(value) is int and value == 0, "07 original command/Job must be known0")


def _extended_pin(value):
    require(isinstance(value, dict) and set(value) == {"path", "bytes", "sha256", "mtime_ns"}
            and type(value["mtime_ns"]) is int and value["mtime_ns"] >= 0,
            "actual07 configured-input pin with exact mtime required")
    pin = {key: value[key] for key in ("path", "bytes", "sha256")}
    _ref(pin)
    return pin


def _tokens(argv):
    require(isinstance(argv, list) and argv and all(isinstance(arg, str) for arg in argv),
            "actual07 argv required")
    return [_path(arg) if ntpath.splitdrive(arg)[0] and ntpath.isabs(arg) else arg for arg in argv]


def _same_argv(actual, expected):
    require(_tokens(actual) == _tokens(expected), "actual07 command differs from frozen pipeline")


def _source_pin(freeze, relative, root):
    rows = [row for row in freeze.get("files", []) if row.get("path") == relative]
    require(len(rows) == 1, "one original704 source row required")
    return {"path": ntpath.join(root, "source", relative), "bytes": rows[0]["bytes"], "sha256": rows[0]["sha256"]}


def _same_label(value):
    require(value.get("native_build_label") == NATIVE30_BUILD_LABEL
            and value.get("native_build_label_is_metadata") is True,
            "07 Root-authored metadata description required; not DLL-string proof")


def _prior_production(docs, evidence, transition, machine_id, now, root, build):
    prior, repair, closed, reused, plan = [docs[name] for name in (
        "attempt02_result", "attempt02_repair_plan", "attempt02_closed", "reused_production", "fixture07_plan")]
    result, delivery, freeze = docs["build_result"], docs["production_delivery"], docs["source_freeze"]
    require(prior.get("schema") == "native30-resume-result-v1" and prior.get("status") == "FAILED"
            and prior.get("error", {}).get("text") == "original command exit 1",
            "original02 FAILED history must remain")
    require(prior.get("machine_id") == machine_id and prior.get("DLL_loaded") is False,
            "original02 machine/load boundary differs")
    _zero(prior.get("Game_calls"))
    require(repair.get("schema") == "native30-separate-resume-source-plan-v1"
            and prior.get("source_commit") == repair.get("source_commit") == reused.get("source_commit")
            == delivery.get("source_commit") == freeze.get("commit") == plan.get("source_commit") == SOURCE_COMMIT,
            "original704 production provenance differs")
    _same_ref(prior.get("repair_plan"), evidence["attempt02_repair_plan"].reference)
    _same_ref(reused.get("prior_result"), evidence["attempt02_result"].reference)
    for name in ("attempt02_result", "attempt02_closed", "source_freeze"):
        _prior(plan, evidence[name].reference)
    phases, commands = _commands_closed(prior, successful=False)
    require(any(type(row.get("original_root_exit_code")) is int and row["original_root_exit_code"] != 0
                for row in commands), "original02 failed command was erased")
    production = [row for row in phases if "--target" in row.get("argv", [])
                  and row["argv"][row["argv"].index("--target") + 1:] == PRODUCTION]
    require(len(production) == 1, "exact original successful three-target production phase required")
    require(_time(prior.get("start_utc")) <= _time(production[0].get("start_utc"))
            <= _time(production[0].get("end_utc")) <= _time(prior.get("end_utc"))
            <= _time(result.get("start_utc")) <= _time(result.get("end_utc")) <= now,
            "02/07 temporal lineage differs")
    require(closed.get("machine_id") == machine_id, "02 closed inventory machine differs")
    _zero(closed.get("future_writes"))
    rows = closed.get("files_before_this_manifest", {}).get("files")
    require(isinstance(rows, list) and len(rows) <= 30000, "bounded closed02 inventory required")
    indexed = {}
    for row in rows:
        require(isinstance(row, dict) and isinstance(row.get("path"), str)
                and not ntpath.isabs(row["path"]) and not ntpath.splitdrive(row["path"])[0],
                "closed02 relative inventory row required")
        key = ntpath.normcase(ntpath.normpath(row["path"]))
        require(key not in indexed, "case-folded closed02 aliases")
        indexed[key] = row
    outputs = reused.get("outputs")
    require(isinstance(outputs, list) and outputs, "retained02 output leases required")
    out_index = {}
    for row in outputs:
        pin = {key: row.get(key) for key in ("path", "bytes", "sha256")}
        _ref(pin)
        path = _path(pin["path"])
        require(path.startswith(_path(build).rstrip("\\") + "\\") and path not in out_index,
                "retained production output escapes build or aliases")
        identity = row.get("file_id")
        require(row.get("held_share_read_only") is True and isinstance(identity, dict)
                and isinstance(identity.get("volume_serial"), str) and identity["volume_serial"].isdigit()
                and _sha(identity.get("file_id"), 32), "retained production FileID/share required")
        relative = ntpath.normcase(ntpath.relpath(path, _path(root)))
        require(relative in indexed and indexed[relative].get("eof") == pin["bytes"],
                "retained output does not bind exact closed02 EOF")
        out_index[path] = pin
    for name in ("DLL", "runtime_archive", "map"):
        pin = delivery.get(name); _ref(pin)
        require(_path(pin["path"]) in out_index, "delivery not retained from successful02 production")
        _same_ref(pin, out_index[_path(pin["path"])])
    _prior(plan, reused.get("original_graph"))
    frozen = {row["path"]: row for row in freeze.get("files", [])}
    compile_rows = reused.get("compile_rows")
    require(isinstance(compile_rows, list) and compile_rows, "original production compile rows required")
    for row in compile_rows:
        pin = row.get("source"); _ref(pin)
        relative = ntpath.relpath(pin["path"], ntpath.join(root, "source")).replace("\\", "/")
        output = row.get("output")
        require(isinstance(output, str) and output and "\0" not in output, "production object output required")
        # Actual output_from_command can return a relative /Fo path. Resolve only
        # against this same original build cwd, never an ambient cwd or new root.
        resolved = _path(output if ntpath.isabs(output) else ntpath.join(build, output))
        require(relative in frozen and frozen[relative].get("bytes") == pin["bytes"]
                and frozen[relative].get("sha256") == pin["sha256"] and _sha(row.get("argv_sha256"))
                and resolved in out_index, "production object/source/argv binding differs")
    overlay = prior.get("source_overlay"); _ref(overlay)
    _same_ref(overlay, transition.get("source_overlay")); _prior(plan, overlay)
    require(overlay["bytes"] == repair.get("overlay", {}).get("bytes")
            and overlay["sha256"] == repair["overlay"].get("sha256"), "original macro overlay differs")
    fixed = delivery.get("fixed_fixture"); _ref(fixed)
    _same_ref(fixed, transition.get("fixed_fixture")); _prior(plan, fixed)
    require(plan.get("helper_pins", {}).get(FIXTURE_SOURCE) == fixed["sha256"]
            and ntpath.basename(ntpath.dirname(fixed["path"])) == "native30-fixture04",
            "actual configured04 fixture source required")
    overlay04 = transition.get("fixture_overlay"); _ref(overlay04); _prior(plan, overlay04)
    require(ntpath.basename(overlay04["path"]) == "fixture-only-override.cmake"
            and ntpath.basename(ntpath.dirname(overlay04["path"])) == "attempt04", "configured04 override differs")
    delta = docs["fixture_graph_delta"]
    require(delta.get("production_and_other_fixture_argv_identical") is True
            and type(delta.get("selected_commands")) is int and delta["selected_commands"] == 995
            and type(delta.get("semantic_link_target_count")) is int and delta["semantic_link_target_count"] == 12
            and type(delta.get("production_compile_rows")) is int
            and delta["production_compile_rows"] == len(compile_rows), "actual995/12 graph delta required")
    _same_ref(delta.get("fixed_fixture"), fixed)
    _same_ref(delta.get("current_graph"), transition.get("current_graph"))
    left, right = delta.get("old_fixture_argv"), delta.get("new_fixture_argv")
    require(isinstance(left, list) and isinstance(right, list) and len(left) == len(right)
            and all(isinstance(arg, str) for arg in left + right), "actual fixture argv delta required")
    differences = [(a, b) for a, b in zip(left, right) if a != b]
    require(len(differences) == 2
            and sum(_path(b) == _path(fixed["path"]) for a, b in differences if not b.lower().startswith(("/fo", "-fo"))) == 1
            and sum(a.lower().startswith(("/fo", "-fo")) and b.lower().startswith(("/fo", "-fo")) for a, b in differences) == 1,
            "fixture delta exceeds original source/object pair")
    require(reused.get("prior_configuration", {}).get("production_and_other_fixture_argv_identical") is True,
            "configured04 prior delta absent")
    return {"attempt02_result": evidence["attempt02_result"].reference,
            "attempt02_status_preserved": "FAILED", "attempt02_production_phase": production[0],
            "source704": evidence["source_freeze"].reference, "source_overlay": overlay,
            "fixture_overlay04": overlay04, "fixed_fixture04": fixed,
            "current_graph": delta["current_graph"], "production_compile_rows": len(compile_rows),
            "retained_outputs": len(outputs), "prior_failures_requalified": False}


def _snapshot(docs, evidence, plan, result, root, build, attempt):
    identity = docs["snapshot_identity"]
    original, snapshot = identity.get("original"), identity.get("snapshot")
    original_pin = _extended_pin(original); _ref(snapshot)
    require(_path(original["path"]) == _path(ntpath.join(build, "build.ninja"))
            and _path(snapshot["path"]) == _path(ntpath.join(attempt, "production-manifest.ninja"))
            and original["bytes"] == snapshot["bytes"] == plan.get("file_peak_quote", {}).get("snapshot_EOF")
            and 0 < snapshot["bytes"] <= 32*1024**2 and original["sha256"] == snapshot["sha256"],
            "07 snapshot must be exact original manifest bytes at its new loader path")
    require(_path(identity.get("same_cwd")) == _path(build)
            and _time(result["start_utc"]) <= _time(identity.get("start_utc"))
            <= _time(identity.get("end_utc")) <= _time(result["end_utc"]), "snapshot copy cwd/time differs")
    inputs = identity.get("inputs")
    require(isinstance(inputs, dict) and _path(inputs.get("cwd")) == _path(build)
            and inputs.get("relative_include") == "CMakeFiles\\rules.ninja"
            and [_path(path) for path in inputs.get("logs", [])] ==
                [_path(ntpath.join(build, name)) for name in (".ninja_log", ".ninja_deps")],
            "original rules/log/deps cwd must remain")
    require(inputs.get("manifest") == original, "configured original manifest identity differs")
    rules = _extended_pin(inputs.get("rules"))
    require(identity.get("relative_rules") == inputs["rules"]
            and _path(rules["path"]) == _path(ntpath.join(build, "CMakeFiles", "rules.ninja")),
            "relative original rules identity differs")
    rows = inputs.get("inputs")
    require(isinstance(rows, list) and len(rows) == 219, "exact219 regeneration input pins required")
    seen = set()
    for row in rows:
        pin = _extended_pin(row); path = _path(pin["path"])
        require(path not in seen and row["mtime_ns"] <= original["mtime_ns"], "input aliases or newer configured input")
        seen.add(path)
    for pin in (ntpath.join(build, "CMakeCache.txt"), ntpath.join(root, "attempt04", "fixture-only-override.cmake"),
                ntpath.join(root, "attempt02", "runtime-source-macro-restore.cmake")):
        require(_path(pin) in seen, "actual cache/overlay regeneration input absent")
    digest = hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()
    require(inputs.get("inputs_sha256") == digest, "219 ordered input identity hash differs")
    glob = inputs.get("glob")
    require(isinstance(glob, dict) and glob.get("script_executed") is False, "source glob must be readonly")
    script = _extended_pin(glob.get("script"))
    require(_path(script["path"]) == _path(ntpath.join(build, "CMakeFiles", "VerifyGlobs.cmake"))
            and script["bytes"] <= 128*1024, "exact bounded configured glob script required")
    families = glob.get("families")
    require(isinstance(families, list) and len(families) == 2, "exact two physical glob families required")
    for family, pattern in zip(families, ("ck3_12002*.cpp", "ck3_12002_*_test.cpp")):
        require(_path(family.get("pattern")) == _path(ntpath.join(root, "source", "ck3_autonomous_player", "native_bridge", "src", pattern))
                and type(family.get("entries")) is int and 0 <= family["entries"] <= 4096
                and _sha(family.get("ordered_paths_sha256")) and family.get("equal") is True,
                "actual configured physical glob differs")
    expected = {"manifest": original["sha256"], "rules": rules["sha256"], "inputs": digest, "glob_script": script["sha256"]}
    require(plan.get("configured_inputs_expected") == expected, "plan must pin all exact configured input identities")
    equivalent = docs["snapshot_command_equivalence"]
    targets = PRODUCTION + [row["target"] for row in docs["build_plan"]["fixtures"]]
    require(equivalent.get("byte_identical") is True and equivalent.get("targets") == targets,
            "all12 expanded command targets must match")
    for name, filename in (("original", "original-commands.log"), ("snapshot", "snapshot-commands.log")):
        pin = equivalent.get(name); _ref(pin)
        require(_path(pin["path"]) == _path(ntpath.join(attempt, filename)) and pin["bytes"] <= 8*1024**2,
                "exact bounded expanded command log ref required")
    require(equivalent["original"]["bytes"] == equivalent["snapshot"]["bytes"]
            and equivalent["original"]["sha256"] == equivalent["snapshot"]["sha256"],
            "original/snapshot expanded command bytes differ")
    return original_pin, snapshot, equivalent, identity


def validate_resume_fixture07_snapshot_chain_v1(*, docs, evidence, transition, machine_id, now):
    result, delivery, plan, admission = [docs[name] for name in (
        "build_result", "production_delivery", "fixture07_plan", "fixture07_admission")]
    require(result.get("schema") == "native30-fixture07-result-v1"
            and result.get("status") == "OFFLINE_QUALIFIED_NOT_DEPLOYED" and "error" not in result
            and result.get("production_recompiled") is False and result.get("configuration_reused_from_attempt04") is True,
            "actual07 has not closed all fixtures; FAILED/preview is not qualification")
    _same_label(result); _same_label(delivery)
    require(plan.get("schema") == "native30-fixture07-snapshot-plan-v1"
            and plan.get("producer") == {"path": PRODUCER_PATH, "bytes": 37100, "sha256": PRODUCER_SHA}
            and plan.get("native_build_label") == NATIVE30_BUILD_LABEL
            and plan.get("label_is_external_pin_metadata_not_compiled_DLL_string") is True,
            "exact frozen07 producer/plan metadata required")
    helpers = plan.get("helper_pins", {})
    require(helpers.get(SNAPSHOT_HELPER) == SNAPSHOT_SHA and helpers.get(CAPTURE_HELPER) == CAPTURE_SHA
            and helpers.get(INVENTORY_PATH) == evidence["tool_inventory"].sha256,
            "actual07 snapshot/environment/inventory source pins differ")
    _same_ref(result.get("plan"), evidence["fixture07_plan"].reference)
    _same_ref(result.get("admission"), evidence["fixture07_admission"].reference)
    root, attempt = plan.get("root"), plan.get("attempt_root")
    build = ntpath.join(root, "build")
    require(_path(attempt) == _path(ntpath.join(root, "attempt07"))
            and _path(ntpath.dirname(delivery["DLL"]["path"])) == _path(build)
            and admission.get("status") == "ADMITTED" and admission.get("machine_id") == machine_id
            and _path(admission.get("root")) == _path(root) and _path(admission.get("attempt_root")) == _path(attempt)
            and admission.get("source_commit") == SOURCE_COMMIT
            and admission.get("producer_sha256") == PRODUCER_SHA
            and admission.get("plan_sha256") == evidence["fixture07_plan"].sha256
            and _sha(admission.get("implementation_commit"), 40)
            and type(admission.get("jobs")) is int and 1 <= admission["jobs"] <= 4
            and admission.get("hard_bytes") == 1610612736
            and admission.get("source_charge_cap_bytes") == 100663296
            and admission.get("metadata_charge_cap_bytes") == 134217728
            and admission.get("aggregate_includes_prior_retained") is True
            and admission.get("prior_retained_allocation_bytes") == 670742624
            and admission.get("new_reservation_bytes") == 0
            and type(admission.get("minimum_free_bytes")) is int and admission["minimum_free_bytes"] >= 2*1024**3
            and type(admission.get("quota_remaining_bytes")) is int and admission["quota_remaining_bytes"] >= 1610612736
            and _time(result["end_utc"]) <= _time(admission.get("deadline_utc")), "actual07 build admission differs")
    require(delivery.get("production_reused_from_attempt02") is True
            and delivery.get("prior_failures_requalified") is False
            and delivery.get("actual_Game_provider_or_camera_qualification") == "NOTRUN",
            "actual07 delivery cannot requalify history or loaded provider")
    audit = _prior_production(docs, evidence, transition, machine_id, now, root, build)
    original, snapshot, equivalent, identity = _snapshot(docs, evidence, plan, result, root, build, attempt)
    phases, commands = _commands_closed(result, successful=True)
    require(_time(identity["end_utc"]) <= _time(phases[0]["start_utc"]), "snapshot copy must precede command evaluation")
    tools = docs["tool_inventory"].get("tool_pins")
    require(isinstance(tools, dict), "original qualified tool inventory required")
    for name in ("ninja", "cl", "cmake", "vcvars64", "dumpbin", "lib"): _ref(tools.get(name))
    ninja = tools["ninja"]["path"]
    index = 0
    def take(argv, log=None):
        nonlocal index
        require(index < len(phases), "missing actual07 pipeline phase")
        row = phases[index]; _same_argv(row["argv"], argv)
        if log is not None: _same_ref(row.get("log"), log)
        index += 1
        return row
    targets = equivalent["targets"]
    take([ninja, "-C", build, "-f", original["path"], "-t", "commands", *targets], equivalent["original"])
    take([ninja, "-C", build, "-f", snapshot["path"], "-t", "commands", *targets], equivalent["snapshot"])
    raw_log = evidence[RAW_EVIDENCE_NAME]
    require(type(raw_log) is Native07NoWorkLogV1, "typed exact07 NoWork text evidence required")
    parse_native07_no_work_log_v1(raw_log.raw, raw_log.reference)
    require(_path(raw_log.path) == _path(ntpath.join(attempt, "production-no-work.log")), "NoWork log escaped actual07")
    try: text = raw_log.raw.decode("utf-8")
    except UnicodeDecodeError: require(False, "NoWork log must decode exactly")
    require("\0" not in text and "\n".join(line for line in text.splitlines()
            if not line.startswith("ninja: Entering directory")).strip() == "ninja: no work to do.",
            "root0 alone is not production NoWork")
    take([ninja, "-C", build, "-f", snapshot["path"], "-n", "-d", "explain", *PRODUCTION], raw_log.reference)
    require(index < len(phases), "owned MSVC initializer phase missing")
    initializer_argv = phases[index]["argv"]
    require(len(initializer_argv) == 13 and ntpath.basename(initializer_argv[2]) == ntpath.basename(CAPTURE_HELPER),
            "exact owned capture helper command required")
    python, capture = initializer_argv[0], initializer_argv[2]
    _path(python); _path(capture)
    work = ntpath.join(attempt, "msvc-environment")
    delta_ref = evidence["msvc_environment"].reference
    require(_path(delta_ref["path"]) == _path(ntpath.join(work, "environment-delta.json")) and delta_ref["bytes"] <= 512*1024,
            "bounded actual initialized MSVC delta ref required")
    frozen_tool = _source_pin(docs["source_freeze"], "tools/run_native_msvc.py", root)
    installation = tools["vcvars64"]["path"]
    for _ in range(4): installation = ntpath.dirname(installation)
    take([python, "-B", capture, "--frozen-tool", frozen_tool["path"], "--tool-sha", frozen_tool["sha256"],
          "--installation", installation, "--work", work, "--output", delta_ref["path"]])
    environment = docs["msvc_environment"]
    require(set(environment) == {"tools", "environment_delta"} and isinstance(environment["tools"], dict)
            and set(environment["tools"]) == {"vcvars64", "cmake", "ninja", "cl"}, "actual frozen initializer tool set differs")
    for name, path in environment["tools"].items():
        require(_path(path) == _path(tools[name]["path"]), "initialized tool does not bind original qualified image")
    delta = environment["environment_delta"]
    require(isinstance(delta, dict) and len(delta) <= 256 and all(isinstance(key, str) and key == key.upper()
            and isinstance(value, str) and not any(word in key for word in ("PASSWORD", "SECRET", "TOKEN", "API_KEY"))
            for key, value in delta.items()) and not any(delta.get(key) for key in ("CL", "_CL_", "LINK", "CMAKE_BUILD_PARALLEL_LEVEL")),
            "unadmitted or sensitive MSVC environment delta")
    for number, fixture in enumerate(docs["build_plan"]["fixtures"], 1):
        stage = ntpath.join(attempt, "fixture-%02d" % number)
        take([ninja, "-C", build, "-f", snapshot["path"], "-j", str(admission["jobs"]), fixture["target"]])
        take([python, "-B", ntpath.join(root, "source", "tools", "register_project_exe_exclusions.py"),
              "--manifest", ntpath.join(stage, "project-exe-manifest.json"), "--receipt", ntpath.join(stage, "project-exe-receipt.json")])
        require(index < len(phases), "fixture execution missing after registration")
        row = phases[index]
        # The shared contract independently checks the real executable and exact
        # declared argument/observation tuple, including layout postcheck.
        require(_path(row["argv"][0]) == _path(ntpath.join(build, fixture["artifact"])), "actual07 fixture execution order differs")
        index += 1
        if fixture.get("postcheck"):
            take([python, "-B", ntpath.join(root, "source", fixture["postcheck"]), row["log"]["path"]])
    take([ninja, "-C", build, "-f", snapshot["path"], "-t", "deps"])
    take([tools["dumpbin"]["path"], "/exports", delivery["DLL"]["path"]])
    take([tools["lib"]["path"], "/LIST", delivery["runtime_archive"]["path"]])
    require(index == len(phases), "unexpected extra or legacy build/configure phase in actual07")
    return {**audit, "build_chain": CHAIN, "fixture07_result": evidence["build_result"].reference,
        "snapshot_identity": evidence["snapshot_identity"].reference,
        "snapshot_command_equivalence": evidence["snapshot_command_equivalence"].reference,
        "production_no_work_log": raw_log.reference, "msvc_environment": delta_ref,
        "regeneration_inputs": 219, "physical_glob_families": 2,
        "cwd_evidence": "snapshot same_cwd/inputs.cwd + argv-C and frozen producer run(cwd=build); no independent OS cwd field",
        "native_build_label_is_metadata": True}
