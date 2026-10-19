"""Finite 08B metadata consumer. No settings, Tasks, artifacts or OS reads.

Only the frozen rev3 producer is understood. Failed07 supplies its exact
snapshot provenance, never qualification. Synthetic models cannot admit export.
"""
from dataclasses import dataclass
import hashlib
import json
import ntpath
import re

from g2_saved_campaign.native29_to30_export_contract_v1 import (
    require, _ref, _path, _sha, _same_ref, _time, _pairs, NATIVE30_BUILD_LABEL)
from g2_saved_campaign import native30_resume_fixture07_snapshot_chain_v1 as seed
from g2_saved_campaign.native30_resume_fixture_chain_v1 import _commands_closed, SOURCE_COMMIT, PRODUCTION

CHAIN = "resume02_snapshot07_two_stage08B"
SCHEMA = "native30-two-stage-qualification-v1"
RUN_ID = "native30-08B"
PRODUCER_PATH = "tools/g2_saved_campaign/native30_two_stage_qualification_20261020.py"
PRODUCER_SHA = "8fff948b9f119a3341b9afc5fa69e094c8a8bea7868812dd20b0579da63a8fef"
ADMIN_PATH = "tools/g2_saved_campaign/native30_two_stage_admin_20261020.py"
ADMIN_SHA = "52561e0d2ae7e3116953168d29154f7c8b1a7cad2a01a6d67058d3eaa4dfae9b"
PLAN_PATH = "docs/ck3-native-ai/evidence/native30-08B-two-stage-plan-revision3-2026-10-20.json"
PLAN_SHA = "6043fd5240c9adbaa90ff3c1d61dd3832550a668382d75af1bf59019a2aa150a"
SEED_PLAN_SHA = "b4af9fa48d48b9c5a982b5bf392a7d6e367de1385fe425f941e389590ad7c006"
C0_SHA = "c0d76a7064996cafd7412f8f39ba2bb5c5cb6271627246b84e946c00bafb864f"
OWNER_SID = "S-1-5-21-2908730481-166481001-1318755029-1001"
ADMIN_JSON_LIMIT = 4 * 1024**2
RAW_NAMES = ("fixture07_no_work_log", "build_only_no_work_log", "run_only_no_work_log")
EXTRA_EVIDENCE = ("attempt02_result", "attempt02_repair_plan", "attempt02_closed",
    "reused_production", "fixture07_plan", "fixture_graph_delta", "fixture07_result",
    "snapshot_identity", "snapshot_command_equivalence", "tool_inventory", *RAW_NAMES,
    "two_stage_plan", "two_stage_admission", "build_only_result", "build_owner_spec",
    "build_owner_closed", "run_owner_spec", "run_owner_closed", "project_exe_manifest",
    "build_input_summary", "run_input_summary", "admin_result", "admin_launch_result",
    "admin_started", "build_msvc_environment")


@dataclass(frozen=True)
class Native08AdminDocumentV1:
    """Only the producer's bounded 4MiB admin RESULT, never a custody token."""
    raw: bytes
    path: str
    sha256: str

    @property
    def reference(self):
        return {"path": self.path, "bytes": len(self.raw), "sha256": self.sha256}

    @property
    def value(self):
        return parse_native08_admin_document_v1(self.raw, self.reference)._value()

    def _value(self):
        return json.loads(self.raw.decode("utf-8"), object_pairs_hook=_pairs,
            parse_constant=lambda value: require(False, "non-finite admin JSON"))


def parse_native08_admin_document_v1(raw, reference):
    _ref(reference)
    require(type(raw) is bytes and len(raw) <= ADMIN_JSON_LIMIT
        and reference["bytes"] == len(raw) and hashlib.sha256(raw).hexdigest() == reference["sha256"]
        and ntpath.basename(reference["path"]) == "RESULT.json", "exact bounded08 admin JSON required")
    doc = Native08AdminDocumentV1(raw, reference["path"], reference["sha256"])
    require(isinstance(doc._value(), dict), "08 admin JSON object required")
    return doc


def _zero(value):
    require(type(value) is int and value == 0, "08 actual terminal root/Job/future must be known0")


def _decimal(value):
    return isinstance(value, str) and re.fullmatch("[1-9][0-9]*", value) is not None


def _file_id(value):
    require(isinstance(value, dict) and set(value) == {"volume_serial", "file_id"}
        and isinstance(value["volume_serial"], str) and re.fullmatch("[0-9]+", value["volume_serial"])
        and _sha(value["file_id"], 32), "08 exact serialized FileID required")
    return value


def _lease(value):
    require(isinstance(value, dict) and set(value) == {"path", "bytes", "sha256", "file_id"},
        "08 complete held-file pin required")
    pin = {key: value[key] for key in ("path", "bytes", "sha256")}
    _ref(pin); _file_id(value["file_id"])
    return pin


def _same_lease(first, second):
    _same_ref(_lease(first), _lease(second))
    require(first["file_id"] == second["file_id"], "08 held FileID changed across stages")


def _at(evidence, name, path):
    require(_path(evidence[name].reference["path"]) == _path(path), "08 evidence path differs: " + name)


def _window(value, now):
    start, end = _time(value.get("start_utc")), _time(value.get("end_utc"))
    require(start <= end <= now, "08 closed observation time differs")
    return start, end


def _no_work(value, path, phase):
    require(type(value) is seed.Native07NoWorkLogV1, "08 exact bounded NoWork bytes required")
    seed.parse_native07_no_work_log_v1(value.raw, value.reference)
    require(_path(value.path) == _path(path), "08 NoWork source escaped its stage")
    _same_ref(phase.get("log"), value.reference)
    text = value.raw.decode("utf-8")
    require("\0" not in text and "\n".join(line for line in text.splitlines()
        if not line.startswith("ninja: Entering directory")).strip() == "ninja: no work to do.",
        "08 root0 alone is not production NoWork")


def _stage(result, stage, evidence, machine_id, now):
    require(result.get("schema") == SCHEMA and type(result.get("protocol_version")) is int
        and result["protocol_version"] == 1 and result.get("run_id") == RUN_ID
        and result.get("stage") == stage + "_only" and "error" not in result
        and result.get("status") == ("BUILD_READY_FOR_ADMIN" if stage == "build" else "OFFLINE_QUALIFIED_NOT_DEPLOYED")
        and result.get("machine_id") == machine_id and result.get("source_commit") == SOURCE_COMMIT
        and result.get("production_recompiled") is False and result.get("DLL_loaded") is False,
        "08 complete exact build/run stage required; build-only/FAILED is not final qualification")
    for key in ("owned_active_after", "future_writes", "Game_calls"): _zero(result.get(key))
    _same_ref(result.get("plan"), evidence["two_stage_plan"].reference)
    _same_ref(result.get("admission"), evidence["two_stage_admission"].reference)
    _same_ref(result.get("prior07_FAILED"), evidence["fixture07_result"].reference)
    start, end = _window(result, now)
    phases, commands = _commands_closed(result, successful=True)
    previous = start
    for row in phases:
        require(previous <= _time(row.get("start_utc")) <= _time(row.get("end_utc")) <= end,
            "08 stage command chronology differs")
        previous = _time(row["end_utc"])
    require(type(result.get("fixture_executions")) is int
        and result["fixture_executions"] == (0 if stage == "build" else 9), "08 exact fixture execution count required")
    return phases, start, end


def _owner(docs, evidence, stage, result, root, repo, machine_id, now):
    spec, closed = docs[stage + "_owner_spec"], docs[stage + "_owner_closed"]
    owner_root = ntpath.join(root, "owner08-" + stage, "owner-spec")
    _at(evidence, stage + "_owner_spec", ntpath.join(owner_root, "SPEC.json"))
    _at(evidence, stage + "_owner_closed", ntpath.join(owner_root, "CLOSED.json"))
    require(spec.get("schema") == "xar.interactive-task-owner/v1" and spec.get("role") == "native_build"
        and spec.get("machine_id") == closed.get("machine_id") == machine_id
        and spec.get("sid") == OWNER_SID and type(spec.get("session")) is int and spec["session"] > 0,
        "08 exact same-machine owned native_build Task SPEC required")
    require(_path(spec.get("root")) == _path(owner_root) and _path(spec.get("cwd")) == _path(repo)
        and _path(spec.get("stage")) == _path(ntpath.join(repo, PRODUCER_PATH))
        and spec.get("stage_sha256") == PRODUCER_SHA and spec.get("bootstrap_sha256") == C0_SHA,
        "08 owned creator/source path differs")
    _path(spec.get("bootstrap")); _path(spec.get("python")); _path(spec.get("pythonw"))
    _file_id(spec.get("python_file_id")); _file_id(spec.get("pythonw_file_id"))
    require(isinstance(spec.get("task_name"), str) and spec["task_name"]
        and isinstance(spec.get("nonce"), str) and spec["nonce"]
        and spec.get("nonce") == closed.get("nonce")
        and closed.get("spec_sha256") == evidence[stage + "_owner_spec"].sha256,
        "08 original Task/nonce/SPEC backlink differs")
    wanted = ["--phase", stage, "--plan", evidence["two_stage_plan"].path,
        "--admission", evidence["two_stage_admission"].path, "--admission-sha256", evidence["two_stage_admission"].sha256]
    if stage == "run": wanted += ["--admin-receipt-sha256", evidence["admin_result"].sha256]
    seed._same_argv(spec.get("stage_args"), wanted + ["--execute"])
    require(spec.get("stop_path") is None and spec.get("env") == {"PYTHONDONTWRITEBYTECODE": "1"},
        "08 unexpected native_build creator environment/control")
    require(_path(spec.get("admission_path")) == _path(evidence["two_stage_admission"].path)
        and spec.get("admission_sha256") == evidence["two_stage_admission"].sha256,
        "08 creator admission differs")
    for key in ("child_exit_code", "bootstrap_exit_code", "job_active_after_stage"): _zero(closed.get(key))
    require(closed.get("forced_remaining_cleanup") is False, "08 forced/unknown owner closure")
    child = closed.get("child")
    require(isinstance(child, dict) and type(child.get("pid")) is int and child["pid"] > 0
        and _decimal(child.get("creation_filetime")) and child.get("session") == spec["session"]
        and _path(child.get("image")) == _path(spec["python"])
        and child.get("image_file_id") == spec["python_file_id"], "08 original owned child identity differs")
    # child.wait0/exit_code are captured at spawn. Only top-level exits above
    # prove termination; never turn spawn STILL_ACTIVE into a terminal claim.
    require(_time(result["end_utc"]) <= _time(closed.get("utc")) <= now, "08 owner closed before stage")
    return child


def _manifest(docs, evidence, fixtures, build):
    manifest = docs["project_exe_manifest"]
    require(manifest.get("schema") == "xar.project-exe-exclusions.v1"
        and manifest.get("configuration") == "Release" and manifest.get("external_candidate") == RUN_ID
        and _path(manifest.get("build_dir")) == _path(build)
        and _path(manifest.get("source_dir")) == _path(ntpath.join(ntpath.dirname(build), "source", "ck3_autonomous_player", "native_bridge"))
        and manifest.get("requested_targets") == [row["target"] for row in fixtures], "08 exact FileAPI EXE manifest required")
    files = manifest.get("files")
    require(isinstance(files, list) and len(files) == 9, "08 all nine manifest EXEs required")
    indexed = {}
    for row in files:
        require(isinstance(row, dict) and type(row.get("size")) is int and row["size"] > 0
            and _sha(row.get("sha256")) and isinstance(row.get("target_id"), str) and row["target_id"],
            "08 original manifest file fingerprint required")
        path = _path(row.get("path")); require(path not in indexed, "08 duplicate manifest EXE")
        indexed[path] = row
    for fixture in fixtures:
        key = _path(ntpath.join(build, fixture["artifact"]))
        require(key in indexed and indexed[key]["target"] == fixture["target"]
            and ntpath.splitext(key)[1] == ".exe", "08 manifest not the exact declared nine targets")
    for value in (docs["build_only_result"], docs["admin_result"], docs["build_result"]):
        bindings = value.get("exe_bindings")
        require(isinstance(bindings, list) and len(bindings) == 9, "08 missing cross-stage EXE bindings")
        seen = set()
        for binding, row in zip(bindings, files):
            pin = _lease(binding); path = _path(pin["path"])
            require(path not in seen and path == _path(row["path"]) and pin["bytes"] == row["size"]
                and pin["sha256"] == row["sha256"], "08 EXE bytes/order differ from original manifest")
            seen.add(path)
    for left, right, current in zip(docs["build_only_result"]["exe_bindings"], docs["admin_result"]["exe_bindings"], docs["build_result"]["exe_bindings"]):
        _same_lease(left, right); _same_lease(left, current)
    _same_ref(docs["build_only_result"].get("project_exe_manifest"), evidence["project_exe_manifest"].reference)
    return manifest


def _admin(docs, evidence, plan, root, repo, machine_id, now):
    receipt, launch, started = [docs[name] for name in ("admin_result", "admin_launch_result", "admin_started")]
    require(all(value.get("machine_id") == machine_id for value in (receipt, launch, started)),
        "08 admin/LAUNCH/STARTED machine binding required")
    build_ref, manifest = evidence["build_only_result"].reference, docs["project_exe_manifest"]
    require(receipt.get("schema") == "native30-exact-nine-admin-registration-v1"
        and receipt.get("status") == "verified" and "error" not in receipt
        and receipt.get("actual_sid") == OWNER_SID and receipt.get("actual_admin") is True
        and receipt.get("allowed_settings_operation") == "ExclusionPath exact nine complete filenames only",
        "08 actual same-owner verified admin required")
    _same_ref(receipt.get("build_result"), build_ref)
    _same_ref(receipt.get("started"), evidence["admin_started"].reference)
    require(receipt.get("manifest_sha256") == evidence["project_exe_manifest"].sha256, "08 admin manifest differs")
    before, after = receipt.get("before_settings"), receipt.get("after_settings")
    for value in (before, after):
        require(isinstance(value, dict) and set(value) == {"ExclusionPath", "ExclusionExtension", "ExclusionProcess"}
            and all(isinstance(rows, list) and all(isinstance(item, str) for item in rows) for rows in value.values()),
            "08 complete actual before/after three-array settings required")
    norm = lambda rows: {ntpath.normcase(ntpath.normpath(value)) for value in rows}
    expected = norm([row["path"] for row in manifest["files"]])
    requested = receipt.get("verified_requested_paths")
    require(isinstance(requested, list) and len(requested) == 9 and all(isinstance(v, str) for v in requested)
        and norm(requested) == expected and norm(before["ExclusionPath"]) <= norm(after["ExclusionPath"])
        and expected <= norm(after["ExclusionPath"])
        and all(set(before[key]) == set(after[key]) for key in ("ExclusionExtension", "ExclusionProcess")),
        "08 nine actual verified paths/prior settings preservation differs")
    inner = receipt.get("helper_receipt")
    require(isinstance(inner, dict) and inner.get("status") == "verified" and inner.get("admin_token") is True
        and inner.get("observed_prior_settings_preserved") is True and inner.get("files") == manifest["files"],
        "08 original helper actual verification missing")
    require(launch.get("schema") == "native30-exact-nine-admin-launch-v1"
        and launch.get("status") == "VERIFIED" and launch.get("settings_success") is True and "error" not in launch
        and type(launch.get("UAC_calls")) is int and launch["UAC_calls"] == 1
        and launch.get("operation") == "one explicit ShellExecuteEx runas", "08 successful original admin LAUNCH required")
    for key in ("actual_exit_code", "future_writes"): _zero(launch.get(key))
    _zero(receipt.get("future_writes"))
    _same_ref(launch.get("build_result"), build_ref); _same_ref(launch.get("admin_result"), evidence["admin_result"].reference)
    _same_lease(launch.get("python"), plan.get("admin_python"))
    seed._same_argv(launch.get("argv"), ["-I", "-B", ntpath.join(repo, ADMIN_PATH), "--elevated",
        "--plan", evidence["two_stage_plan"].path, "--admission", evidence["two_stage_admission"].path,
        "--admission-sha256", evidence["two_stage_admission"].sha256, "--build-result-sha256", build_ref["sha256"], "--execute"])
    identity = started.get("identity")
    require(started.get("schema") == "native30-exact-nine-admin-started-v1"
        and started.get("unknown_future_prohibits_repeat") is True and isinstance(identity, dict)
        and identity.get("sid") == OWNER_SID and type(identity.get("pid")) is int and identity["pid"] > 0
        and identity["pid"] == launch.get("pid") and _decimal(identity.get("creation_filetime"))
        and _path(identity.get("image")) == _path(launch["python"]["path"])
        and identity.get("image_file_id") == launch["python"]["file_id"]
        and type(identity.get("session")) is int and identity["session"] >= 0,
        "08 create-only STARTED actual PID/full FILETIME required")
    _same_ref(started.get("build_result"), build_ref)
    require(started.get("manifest_sha256") == evidence["project_exe_manifest"].sha256, "08 STARTED manifest differs")
    ls, le = _window(launch, now); rs, re_ = _window(receipt, now)
    require(_time(docs["build_only_result"]["end_utc"]) <= ls <= _time(started.get("utc")) <= rs <= re_ <= le
        <= _time(docs["build_result"]["start_utc"]), "08 admin/build/run chronology differs")


def validate_two_stage_export_chain_v1(*, docs, evidence, transition, machine_id, now, source_fixture=False):
    plan, seed_plan, admission = [docs[name] for name in ("two_stage_plan", "fixture07_plan", "two_stage_admission")]
    require(plan.get("schema") == "native30-08B-two-stage-plan-v1" and plan.get("revision") == 3
        and plan.get("producer") == {"path": PRODUCER_PATH, "bytes": 25416, "sha256": PRODUCER_SHA}
        and plan.get("admin_producer") == {"path": ADMIN_PATH, "bytes": 10911, "sha256": ADMIN_SHA}
        and plan.get("source_commit") == SOURCE_COMMIT and plan.get("copy_snapshot_or_commands") is False,
        "08 only frozen rev3 producer/plan is supported")
    require(source_fixture or evidence["two_stage_plan"].sha256 == PLAN_SHA, "08 exact admitted rev3 plan required")
    helpers = plan.get("helper_pins", {})
    for name, sha in ((ADMIN_PATH, ADMIN_SHA), (seed.PRODUCER_PATH, seed.PRODUCER_SHA),
        (seed.SNAPSHOT_HELPER, seed.SNAPSHOT_SHA), (seed.CAPTURE_HELPER, seed.CAPTURE_SHA)):
        require(helpers.get(name) == sha, "08 dependency source differs")
    require(helpers.get(seed.INVENTORY_PATH) == evidence["tool_inventory"].sha256
        and seed_plan.get("producer") == {"path": seed.PRODUCER_PATH, "bytes": 37100, "sha256": seed.PRODUCER_SHA},
        "08 original07 tool/producer source differs")
    require(source_fixture or evidence["fixture07_plan"].sha256 == SEED_PLAN_SHA, "08 original07 plan pin differs")
    require(plan.get("base_readonly_plan", {}).get("sha256") == evidence["fixture07_plan"].sha256
        and plan.get("base_readonly_plan", {}).get("bytes") == len(evidence["fixture07_plan"].raw), "08 readonly seed-plan backlink differs")
    root = plan.get("roots", {}).get("aggregate"); _path(root)
    roots = {key: ntpath.join(root, value) for key, value in (("build", "attempt08-build"), ("run", "attempt08-run"),
        ("admin", "attempt08-admin"), ("owner_build", "owner08-build/owner-spec"), ("owner_run", "owner08-run/owner-spec"))}
    require(set(plan.get("roots", {})) == {"aggregate", *roots}
        and all(_path(plan["roots"][key]) == _path(path) for key, path in roots.items()), "08 exact finite stage roots required")
    build = ntpath.join(root, "build"); attempt07 = ntpath.join(root, "attempt07")
    require(_path(seed_plan.get("root")) == _path(root) and _path(seed_plan.get("attempt_root")) == _path(attempt07), "08 seed root differs")
    refs_at = {"build_only_result": ("build", "RESULT.json"), "build_result": ("run", "RESULT.json"),
        "production_delivery": ("run", "production-delivery.json"), "project_exe_manifest": ("build", "project-exe-manifest.json"),
        "build_input_summary": ("build", "input-summary.json"), "run_input_summary": ("run", "input-summary.json"),
        "admin_result": ("admin", "RESULT.json"), "admin_launch_result": ("admin", "LAUNCH-RESULT.json"),
        "admin_started": ("admin", "STARTED.json")}
    for name, (role, filename) in refs_at.items(): _at(evidence, name, ntpath.join(roots[role], filename))
    _at(evidence, "fixture07_result", ntpath.join(attempt07, "RESULT.json"))
    require(_path(ntpath.dirname(docs["production_delivery"]["DLL"]["path"])) == _path(build), "08 original production build required")
    protocol = plan.get("protocol", {})
    require(all(protocol.get(key) == value for key, value in {"schema": SCHEMA, "protocol_version": 1, "run_id": RUN_ID,
        "build_status": "BUILD_READY_FOR_ADMIN", "run_status": "OFFLINE_QUALIFIED_NOT_DEPLOYED",
        "admin_schema": "native30-exact-nine-admin-registration-v1"}.items()), "08 finite two-stage protocol differs")
    require(admission.get("status") == "ADMITTED" and admission.get("machine_id") == machine_id and admission.get("source_commit") == SOURCE_COMMIT
        and admission.get("producer_sha256") == PRODUCER_SHA and admission.get("plan_sha256") == evidence["two_stage_plan"].sha256
        and _sha(admission.get("implementation_commit"), 40) and _path(admission.get("root")) == _path(root), "08 exact stage admission required")
    constants = {"hard_bytes": 1610612736, "source_charge_cap_bytes": 100663296, "metadata_charge_cap_bytes": 134217728,
        "TEMP_cap_bytes": 402653184, "prior_retained_allocation_bytes": 706251512, "new_reservation_bytes": 0}
    require(all(type(admission.get(key)) is int and admission[key] == value for key, value in constants.items())
        and admission.get("aggregate_includes_prior_retained") is True
        and type(admission.get("jobs")) is int and 1 <= admission["jobs"] <= 4
        and type(admission.get("minimum_free_bytes")) is int and admission["minimum_free_bytes"] >= 2*1024**3
        and type(admission.get("quota_remaining_bytes")) is int and admission["quota_remaining_bytes"] >= constants["hard_bytes"], "08 admitted capacity differs")
    for role in ("build", "run", "admin"):
        require(_path(admission.get(role + "_stage_root")) == _path(roots[role]), "08 admitted stage path differs")
    failed = docs["fixture07_result"]
    require(failed.get("schema") == "native30-fixture07-result-v1" and failed.get("status") == "FAILED"
        and failed.get("error") == {"type": "AuxiliaryContractError", "text": "original command exit 1"}
        and failed.get("owned_active_after") == 0 and failed.get("future_writes") == 0
        and len(failed.get("phases", [])) == 5, "08 may reuse only specified FAILED07 snapshot prefix")
    for row in failed["phases"]: _zero(row.get("returncode")); _zero(row.get("owned_active_after"))
    seed_refs = [evidence[name].reference for name in ("fixture07_result", "snapshot_command_equivalence", "fixture07_no_work_log", "snapshot_identity")]
    require(plan.get("seed_pins") == seed_refs, "08 exact failed07 seed pins differ")
    require(source_fixture or evidence["fixture07_result"].sha256 == "7191c5ac4155bc91e42c9025c429ee4d1846dfc23dcbf68bc9d23a17c079248e", "08 unrecognized FAILED seed")
    audit = seed._prior_production(docs, evidence, transition, machine_id, now, root, build)
    original, snapshot, equivalent, identity = seed._snapshot(docs, evidence, seed_plan, failed, root, build, attempt07)
    _no_work(evidence["fixture07_no_work_log"], ntpath.join(attempt07, "production-no-work.log"), failed["phases"][2])
    require(_path(plan.get("snapshot_reused_readonly")) == _path(snapshot["path"])
        and plan.get("configured_inputs_expected") == seed_plan.get("configured_inputs_expected"), "08 snapshot/configured identity differs")
    build_rows, bs, be = _stage(docs["build_only_result"], "build", evidence, machine_id, now)
    run_rows, rs, re_ = _stage(docs["build_result"], "run", evidence, machine_id, now)
    require(_time(failed["end_utc"]) <= bs <= be <= rs <= re_ <= _time(admission.get("deadline_utc")), "08 original07/build/run/admission time differs")
    repo = ntpath.normpath(ntpath.join(ntpath.dirname(evidence["two_stage_plan"].path), "..", "..", ".."))
    require(_path(evidence["two_stage_plan"].path) == _path(ntpath.join(repo, PLAN_PATH)), "08 canonical plan source path required")
    children = [_owner(docs, evidence, role, docs[name], root, repo, machine_id, now)
        for role, name in (("build", "build_only_result"), ("run", "build_result"))]
    require(docs["build_owner_spec"]["task_name"] != docs["run_owner_spec"]["task_name"]
        and docs["build_owner_spec"]["nonce"] != docs["run_owner_spec"]["nonce"]
        and children[0]["creation_filetime"] != children[1]["creation_filetime"], "08 run must be a new owned Task/process generation")
    fixtures = docs["build_plan"]["fixtures"]
    _manifest(docs, evidence, fixtures, build)
    _admin(docs, evidence, plan, root, repo, machine_id, now)
    for value in (docs["build_result"], docs["production_delivery"]):
        for name in ("admin_result", "admin_launch_result"):
            _same_ref(value.get(name), evidence[name].reference)
        _same_ref(value.get("build_result"), evidence["build_only_result"].reference)
    delivery = docs["production_delivery"]
    seed._same_label(delivery)
    require(_path(delivery.get("run_result_path")) == _path(evidence["build_result"].path)
        and delivery.get("production_reused_from_attempt02") is True and delivery.get("prior_failures_requalified") is False
        and delivery.get("actual_Game_provider_or_camera_qualification") == "NOTRUN", "08 delivery provenance differs")
    for value in (docs["build_only_result"], docs["build_result"]): _same_ref(_lease(value.get("snapshot")), snapshot)
    _same_lease(docs["build_only_result"]["snapshot"], docs["build_result"]["snapshot"])
    tools = docs["tool_inventory"].get("tool_pins", {})
    for name in ("ninja", "cl", "cmake", "vcvars64", "dumpbin", "lib"): _ref(tools.get(name))
    ninja = tools["ninja"]["path"]
    for role, rows in (("build", build_rows), ("run", run_rows)):
        seed._same_argv(rows[0]["argv"], [ninja, "-C", build, "-f", snapshot["path"], "-n", "-d", "explain", *PRODUCTION])
        _no_work(evidence[role + "_only_no_work_log"], ntpath.join(roots[role], "production-no-work.log"), rows[0])
        summary = docs[role + "_input_summary"]
        require(all(type(summary.get(key)) is int and summary[key] == value for key, value in
            {"source_count": 5355, "selected_rows": 995, "targets": 12, "production_rows": 978, "production_leases": 983, "regen_inputs": 219}.items())
            and summary.get("continuous_between_Tasks_lease_claim") is False
            and summary.get("configured_inputs") == plan["configured_inputs_expected"], "08 bounded full-preflight summary differs")
        _same_ref(summary.get("reference_current_graph"), transition.get("current_graph"))
        _same_ref(summary.get("no_work"), evidence[role + "_only_no_work_log"].reference)
        _same_lease(summary.get("snapshot"), docs["build_only_result"]["snapshot"])
    require(len(build_rows) == 11 and docs["build_only_result"].get("fixture_builds") == build_rows[2:]
        and docs["build_only_result"].get("fixture_runs") == []
        and docs["build_result"].get("fixture_builds") == [], "08 build/run rows must remain separated")
    work = ntpath.join(roots["build"], "msvc-environment")
    _at(evidence, "build_msvc_environment", ntpath.join(work, "environment-delta.json"))
    initializer = build_rows[1]["argv"]
    require(len(initializer) == 13, "08 owned MSVC initializer required")
    frozen_tool = seed._source_pin(docs["source_freeze"], "tools/run_native_msvc.py", root)
    install = tools["vcvars64"]["path"]
    for _ in range(4): install = ntpath.dirname(install)
    seed._same_argv(initializer, [docs["build_owner_spec"]["python"], "-B", ntpath.join(repo, seed.CAPTURE_HELPER),
        "--frozen-tool", frozen_tool["path"], "--tool-sha", frozen_tool["sha256"], "--installation", install,
        "--work", work, "--output", evidence["build_msvc_environment"].path])
    require(_path(build_rows[1]["log"]["path"]) == _path(ntpath.join(work, "initializer.log")),
        "08 initializer log path differs")
    environment = docs["build_msvc_environment"]
    require(set(environment) == {"tools", "environment_delta"} and set(environment["tools"]) == {"vcvars64", "cmake", "ninja", "cl"}, "08 initializer tool set differs")
    for key, path in environment["tools"].items(): require(_path(path) == _path(tools[key]["path"]), "08 initialized tool differs")
    delta = environment["environment_delta"]
    require(isinstance(delta, dict) and len(delta) <= 256 and all(isinstance(k, str) and k == k.upper() and isinstance(v, str)
        and not any(word in k for word in ("PASSWORD", "SECRET", "TOKEN", "API_KEY")) for k, v in delta.items())
        and not any(delta.get(k) for k in ("CL", "_CL_", "LINK", "CMAKE_BUILD_PARALLEL_LEVEL")), "08 unadmitted MSVC environment")
    for number, (row, fixture) in enumerate(zip(build_rows[2:], fixtures), 1):
        seed._same_argv(row["argv"], [ninja, "-C", build, "-f", snapshot["path"], "-j", str(admission["jobs"]), fixture["target"]])
        require(_path(row["log"]["path"]) == _path(ntpath.join(roots["build"], "build-%02d.log" % number)),
            "08 exact build log path required")
    index, executed = 1, []
    for number, fixture in enumerate(fixtures, 1):
        require(index < len(run_rows), "08 missing actual fixture run")
        row = run_rows[index]; index += 1; executed.append(row)
        require(_path(row["argv"][0]) == _path(ntpath.join(build, fixture["artifact"])), "08 exact fixture run order differs")
        require(_path(row["log"]["path"]) == _path(ntpath.join(roots["run"], "fixture-%02d.log" % number)),
            "08 exact fixture log path required")
        if fixture.get("postcheck"):
            require(index < len(run_rows), "08 missing layout postcheck phase")
            seed._same_argv(run_rows[index]["argv"], [docs["run_owner_spec"]["python"], "-B", ntpath.join(root, "source", fixture["postcheck"]), row["log"]["path"]]); index += 1
            require(_path(run_rows[index-1]["log"]["path"]) == _path(ntpath.join(roots["run"], "layout-postcheck.log")),
                "08 layout postcheck source path differs")
    require(docs["build_result"].get("fixture_runs") == executed, "08 fixture execution list differs from actual phases")
    ending = ([ninja, "-C", build, "-f", snapshot["path"], "-t", "deps"],
        [tools["dumpbin"]["path"], "/exports", delivery["DLL"]["path"]],
        [tools["lib"]["path"], "/LIST", delivery["runtime_archive"]["path"]])
    require(len(run_rows) == index + 3, "08 extra/missing run/dependency/final delivery phase")
    for row, argv in zip(run_rows[index:], ending): seed._same_argv(row["argv"], argv)
    for row, filename in zip(run_rows[index:], (".msvc-temp/environment/actual-ninja-deps.txt", "exports.log", "runtime-members.log")):
        require(_path(row["log"]["path"]) == _path(ntpath.join(roots["run"], filename)), "08 final phase source path differs")
    return {**audit, "build_chain": CHAIN, "failed07_snapshot_seed": evidence["fixture07_result"].reference,
        "failed07_status_preserved": "FAILED", "snapshot_identity": evidence["snapshot_identity"].reference,
        "snapshot_command_equivalence": evidence["snapshot_command_equivalence"].reference,
        "build_only_result": evidence["build_only_result"].reference, "admin_result": evidence["admin_result"].reference,
        "admin_launch_result": evidence["admin_launch_result"].reference, "run_result": evidence["build_result"].reference,
        "regeneration_inputs": 219, "physical_glob_families": 2, "exact_exe_bindings_compared": 9,
        "continuous_between_Tasks_lease_claim": False, "cross_stage_983_FileID_table_observed": False,
        "cwd_evidence": "snapshot original cwd + exact argv-C and frozen producer cwd; no independent OS cwd field",
        "native_build_label_is_metadata": True, "source_fixture": source_fixture}
