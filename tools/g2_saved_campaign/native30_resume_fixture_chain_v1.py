"""Finite actual resume02 -> fixture06 metadata closure; no body/OS reads.

The prior result stays FAILED. Only its exact successful production command is
reused; fixture06 must independently close all commands and all nine fixtures.
Source704, its macro overlay, and the repaired test leaf are distinct evidence.
"""
import ntpath

from g2_saved_campaign.native29_to30_export_contract_v1 import (
    require, _ref, _path, _sha, _same_ref, _time)

CHAIN = "resume02_fixture06"
SOURCE_COMMIT = "704bdd3362bdc282ed5f5f8cf31fd3f50b90d747"
PRODUCTION = ["xar_ck3_bridge", "xar_ck3_12002_runtime", "xar_bridge_protocol"]
EXTRA_EVIDENCE = ("attempt02_result", "attempt02_repair_plan", "attempt02_closed",
                  "reused_production", "fixture06_plan", "fixture_graph_delta")
FIXTURE_SOURCE = "ck3_autonomous_player/native_bridge/src/camera_tracking_v1_test.cpp"


def _zero(value, message):
    require(type(value) is int and value == 0, message)


def _commands_closed(result, *, successful):
    _zero(result.get("owned_active_after"), "actual attempt Job is not closed0")
    _zero(result.get("future_writes"), "actual attempt future writes are not closed0")
    attempts = result.get("command_attempts")
    require(isinstance(attempts, list) and attempts, "actual auxiliary command journals required")
    for attempt in attempts:
        require(isinstance(attempt, dict) and isinstance(attempt.get("argv"), list)
                and attempt["argv"] and type(attempt.get("pid")) is int and attempt["pid"] > 0,
                "actual command journal identity required")
        _zero(attempt.get("owned_active_after"), "command journal Job is not closed0")
        if successful:
            _zero(attempt.get("original_root_exit_code"), "fixture06 actual original command did not exit0")
            require(attempt.get("failure_job_termination") is False and "error" not in attempt,
                    "fixture06 command failed or used failure cleanup")
    phases = result.get("phases")
    require(isinstance(phases, list) and phases, "actual successful phase receipts required")
    require(not successful or len(phases) == len(attempts), "fixture06 phase/journal count differs")
    for phase in phases:
        require(isinstance(phase, dict), "actual phase object required")
        _zero(phase.get("returncode"), "actual successful phase returncode is not0")
        _zero(phase.get("owned_active_after"), "actual successful phase Job is not0")
        matches = [row for row in attempts if row["argv"] == phase.get("argv") and row["pid"] == phase.get("pid")]
        require(len(matches) == 1, "successful phase has no unique actual command journal")
        _zero(matches[0].get("original_root_exit_code"), "successful phase original command is not0")
    return phases, attempts


def _prior(plan, reference):
    pins = plan.get("prior_pins")
    require(isinstance(pins, list) and sum(_ref(pin) == _ref(reference) for pin in pins) == 1,
            "actual fixture06 plan does not pin this exact prior input")


def validate_resume_fixture_chain_v1(*, docs, evidence, transition, machine_id, now):
    result, delivery = docs["build_result"], docs["production_delivery"]
    prior, repair, closed, reused, plan, delta = [docs[name] for name in EXTRA_EVIDENCE]
    require(result.get("schema") == "native30-fixture06-result-v1"
            and result.get("status") == "OFFLINE_QUALIFIED_NOT_DEPLOYED"
            and "error" not in result and result.get("production_recompiled") is False
            and result.get("configuration_reused_from_attempt04") is True,
            "fixture06 has not reached actual offline qualification")
    require(prior.get("schema") == "native30-resume-result-v1" and prior.get("status") == "FAILED"
            and isinstance(prior.get("error"), dict) and prior["error"].get("text") == "original command exit 1",
            "attempt02 original FAILED history must be retained exactly")
    require(prior.get("source_commit") == delivery.get("source_commit") == docs["source_freeze"].get("commit")
            == repair.get("source_commit") == plan.get("source_commit") == SOURCE_COMMIT,
            "original source704 provenance differs")
    for record in (result, prior):
        require(record.get("machine_id") == machine_id and record.get("DLL_loaded") is False,
                "actual attempt machine/load boundary differs")
        _zero(record.get("Game_calls"), "actual attempt used Game")
    require(repair.get("schema") == "native30-separate-resume-source-plan-v1"
            and plan.get("schema") == "native30-fixture06-current-config-plan-v1",
            "actual separate resume/fixture06 plan schema required")
    _same_ref(prior.get("repair_plan"), evidence["attempt02_repair_plan"].reference)
    _same_ref(result.get("plan"), evidence["fixture06_plan"].reference)
    _same_ref(reused.get("prior_result"), evidence["attempt02_result"].reference)
    _prior(plan, evidence["attempt02_result"].reference)
    _prior(plan, evidence["attempt02_closed"].reference)
    _prior(plan, evidence["source_freeze"].reference)
    require(reused.get("source_commit") == SOURCE_COMMIT, "reused production source differs")
    require(delivery.get("production_reused_from_attempt02") is True
            and delivery.get("prior_failures_requalified") is False
            and delivery.get("actual_Game_provider_or_camera_qualification") == "NOTRUN",
            "fixture06 delivery must preserve production reuse and prior failures")
    prior_phases, prior_commands = _commands_closed(prior, successful=False)
    phases, commands = _commands_closed(result, successful=True)
    require(any(type(row.get("original_root_exit_code")) is int and row["original_root_exit_code"] != 0
                for row in prior_commands), "attempt02 failed command was erased")
    production = [row for row in prior_phases if "--target" in row.get("argv", [])
                  and row["argv"][row["argv"].index("--target") + 1:] == PRODUCTION]
    require(len(production) == 1, "one exact successful three-target production command required")
    prior_start, prior_end = _time(prior.get("start_utc")), _time(prior.get("end_utc"))
    start, end = _time(result.get("start_utc")), _time(result.get("end_utc"))
    require(prior_start <= _time(production[0].get("start_utc")) <= _time(production[0].get("end_utc"))
            <= prior_end <= start <= end <= now, "production/fixture06 temporal lineage differs")
    require(isinstance(closed, dict) and closed.get("machine_id") == machine_id,
            "same-machine actual attempt02 inventory required")
    _zero(closed.get("future_writes"), "attempt02 inventory is not closed0")
    inventory = closed.get("files_before_this_manifest", {}).get("files")
    require(isinstance(inventory, list) and len(inventory) <= 30000, "bounded actual attempt02 inventory required")
    indexed = {}
    for row in inventory:
        require(isinstance(row, dict) and isinstance(row.get("path"), str), "actual inventory row required")
        key = row["path"].replace("\\", "/")
        require(key not in indexed, "duplicate prior inventory row")
        indexed[key] = row
    outputs = reused.get("outputs")
    require(isinstance(outputs, list) and outputs, "held production output evidence required")
    build_root = ntpath.dirname(delivery["DLL"]["path"])
    root = ntpath.dirname(build_root)
    out_index = {}
    for row in outputs:
        pin = {key: row.get(key) for key in ("path", "bytes", "sha256")}
        _ref(pin)
        path = _path(pin["path"])
        require(path.startswith(_path(build_root).rstrip("\\") + "\\") and path not in out_index,
                "production output aliases or escapes actual build")
        identity = row.get("file_id")
        require(row.get("held_share_read_only") is True and isinstance(identity, dict)
                and isinstance(identity.get("volume_serial"), str) and identity["volume_serial"].isdigit()
                and _sha(identity.get("file_id"), 32), "actual held production FileID/share proof required")
        relative = ntpath.relpath(path, _path(root)).replace("\\", "/")
        require(relative in indexed and indexed[relative].get("eof") == pin["bytes"],
                "production output does not match attempt02 closed inventory")
        out_index[path] = pin
    for name in ("DLL", "runtime_archive", "map"):
        pin = delivery.get(name)
        _ref(pin)
        require(_path(pin["path"]) in out_index, "delivered artifact was not retained from successful production")
        _same_ref(pin, out_index[_path(pin["path"])])
    _prior(plan, reused.get("original_graph"))
    frozen_rows = {row["path"]: row for row in docs["source_freeze"].get("files", [])}
    compile_rows = reused.get("compile_rows")
    require(isinstance(compile_rows, list) and compile_rows, "retained production compile/source rows required")
    for row in compile_rows:
        source = row.get("source")
        _ref(source)
        relative = ntpath.relpath(source["path"], ntpath.join(root, "source")).replace("\\", "/")
        require(relative in frozen_rows and frozen_rows[relative].get("bytes") == source["bytes"]
                and frozen_rows[relative].get("sha256") == source["sha256"]
                and _sha(row.get("argv_sha256")) and _path(row.get("output")) in out_index,
                "retained production object does not bind original source704")
    overlay = prior.get("source_overlay")
    _ref(overlay); _same_ref(overlay, transition.get("source_overlay"))
    original_overlay = repair.get("overlay")
    require(isinstance(original_overlay, dict) and overlay["bytes"] == original_overlay.get("bytes")
            and overlay["sha256"] == original_overlay.get("sha256"), "macro overlay is not exact admitted repair source")
    _prior(plan, overlay)
    fixed = delivery.get("fixed_fixture")
    _ref(fixed); _same_ref(fixed, transition.get("fixed_fixture"))
    require(plan.get("helper_pins", {}).get(FIXTURE_SOURCE) == fixed["sha256"]
            and ntpath.basename(ntpath.dirname(fixed["path"])) == "native30-fixture04",
            "fixed fixture is not the admitted separate test leaf")
    _prior(plan, fixed)
    fixture_overlay = transition.get("fixture_overlay")
    _ref(fixture_overlay); _prior(plan, fixture_overlay)
    require(ntpath.basename(fixture_overlay["path"]) == "fixture-only-override.cmake"
            and ntpath.basename(ntpath.dirname(fixture_overlay["path"])) == "attempt04",
            "fixture06 must retain actual configured04 overlay")
    require(delta.get("production_and_other_fixture_argv_identical") is True
            and type(delta.get("selected_commands")) is int and delta["selected_commands"] == 995
            and type(delta.get("semantic_link_target_count")) is int and delta["semantic_link_target_count"] == 12
            and type(delta.get("production_compile_rows")) is int
            and delta["production_compile_rows"] == len(compile_rows),
            "actual single-fixture graph comparison absent")
    _same_ref(delta.get("fixed_fixture"), fixed)
    _same_ref(delta.get("current_graph"), transition.get("current_graph"))
    left, right = delta.get("old_fixture_argv"), delta.get("new_fixture_argv")
    require(isinstance(left, list) and isinstance(right, list) and len(left) == len(right)
            and all(isinstance(arg, str) for arg in left + right), "actual fixture argv comparison required")
    differences = [(a, b) for a, b in zip(left, right) if a != b]
    require(len(differences) == 2 and sum(_path(b) == _path(fixed["path"]) for a, b in differences
            if not b.lower().startswith(("/fo", "-fo"))) == 1
            and sum(a.lower().startswith(("/fo", "-fo")) and b.lower().startswith(("/fo", "-fo"))
                    for a, b in differences) == 1, "fixture delta is not only source/object paths")
    require(reused.get("prior_configuration", {}).get("production_and_other_fixture_argv_identical") is True,
            "prior configured fixture lineage missing")
    # The actual06 producer reuses configured04 and only dry-runs production.
    # Its boolean declarations alone cannot substitute for the command trace.
    for row in phases:
        argv = row["argv"]
        require(all(isinstance(arg, str) for arg in argv)
                and "--configure" not in argv
                and not any("CMAKE_PROJECT_INCLUDE" in arg for arg in argv),
                "fixture06 cannot configure a replacement graph")
        if "--build" in argv and "--target" in argv:
            require(not set(argv[argv.index("--target") + 1:]).intersection(PRODUCTION),
                    "fixture06 cannot recompile retained production")
    # The production dry-run is a real successful command, not a boolean field.
    require(any("-n" in row["argv"] and row["argv"][row["argv"].index("-n") + 1:] == PRODUCTION
                for row in phases), "actual production no-work command absent")
    return {"build_chain": CHAIN, "attempt02_result": evidence["attempt02_result"].reference,
            "attempt02_status_preserved": "FAILED", "attempt02_production_phase": production[0],
            "fixture06_result": evidence["build_result"].reference, "source704": evidence["source_freeze"].reference,
            "source_overlay": overlay, "fixture_overlay04": fixture_overlay,
            "fixed_fixture04": fixed, "current_graph": delta["current_graph"],
            "production_compile_rows": len(compile_rows), "retained_outputs": len(outputs),
            "prior_failures_requalified": False}
