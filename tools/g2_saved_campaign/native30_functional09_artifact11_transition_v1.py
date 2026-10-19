"""Finite metadata transition from closed09 subfacts plus artifact11.

No binary, OS, Task or runtime reads. The old08B protocol remains independent.
Only these exact closed attempts are understood; FAILED09 is never renamed PASS.
"""
import hashlib
import json
import ntpath
import re
from datetime import datetime, timezone

from g2_saved_campaign.native29_to30_export_contract_v1 import (
    NativeTransitionV1, NATIVE30_BUILD_LABEL, TRANSITION_SCHEMA, CARD_SCHEMA,
    FIXTURE_TARGETS, ROOT_FIELDS, require, _doc, _ref, _same_ref, _path, _sha, _time)
from g2_saved_campaign.native30_resume_fixture_chain_v1 import _commands_closed

CHAIN = "resume02_snapshot07_functional09_artifact11"
SOURCE = "704bdd3362bdc282ed5f5f8cf31fd3f50b90d747"
MACHINE = "xenoamess-full-tower-eb9d2c1186"
OWNER_SID = "S-1-5-21-2908730481-166481001-1318755029-1001"
C0_SHA = "c0d76a7064996cafd7412f8f39ba2bb5c5cb6271627246b84e946c00bafb864f"
ROOT = "D:/codex-ck3-demos/2026-10-19-robert-v20261019-native30-camera01"
EVIDENCE_NAMES = ("target_native_pin", "source_freeze", "native_plan", "native_readonly_plan", "snapshot07_plan", "compatibility",
    "base_exe_binding", "target_exe_binding", "functional09_result", "functional09_summary",
    "functional09_plan", "functional09_spec", "functional09_closed", "functional09_unregister",
    "artifact11_result", "artifact11_delivery", "artifact11_summary", "artifact11_plan",
    "artifact11_spec", "artifact11_closed", "artifact11_unregister", "exports_and_data",
    "build08_result", "build08_manifest", "build08_spec", "build08_closed", "build08_unregister",
    "prior08_admin_launch")
# Production metadata must be the already closed owner receipts, not an arbitrary
# caller status dictionary. Source-fixture models are explicitly unadmitted.
FIXED = {
    "functional09_result": ("attempt09-functional/RESULT.json", 44290, "1459f738ea8961abc98249043c75d2c28eac51bd052d3bd94d247792c3207ab1"),
    "functional09_summary": ("owner09-functional/FINAL-CLOSED-SUMMARY.json", 7610, "a613819afd6e632bd097e21a703ed52d4bb4c56ee29eb390fcca972904c88bc1"),
    "functional09_plan": (None, 10735, "3b7a69e787f12c491dff5285d0cef1e509e1f149757b9dfe6ac832e780523aac"),
    "functional09_spec": ("owner09-functional/owner-spec/SPEC.json", 2042, "51e859df3a884904a0b0fdda66275d0065e2d07b744b6a151a725c6de673e4e4"),
    "functional09_closed": ("owner09-functional/owner-spec/CLOSED.json", 745, "73d428bd16f972b4228f6ac23709490fe34ea3ed893693b529524a1ea6774318"),
    "functional09_unregister": ("owner09-functional/UNREGISTER.json", 980, "921fe6d69bb07ef60134388cb3ab6d8b759a2f4b8b65fe045b0b8fda05013833"),
    "artifact11_result": ("attempt11-artifact-postcheck/RESULT.json", 13662, "95c29ce88b131f2f480b4a3ac83d4ee5f76ea8975be8b5f72a07849a1a166f67"),
    "artifact11_delivery": ("attempt11-artifact-postcheck/production-delivery.json", 6167, "ee1d97afec5e31a8137a6728110830d1da340032272a4c283f676fd397d4abb8"),
    "artifact11_summary": ("owner11-artifact/FINAL-CLOSED-SUMMARY.json", 8828, "ed443ce2c1c7e5659be3e7fd870becc497c0c986389d25721be6f4d82a7a1905"),
    "artifact11_plan": (None, 5504, "f778024583d94a27a3590e366219aa3f07a35ae060021af6d7ba3c68588ff338"),
    "artifact11_spec": ("owner11-artifact/owner-spec/SPEC.json", 2052, "91005c55efad447e20d0c7339700948f1ba54789ad6b6b418cf0b7e2b45a64ab"),
    "artifact11_closed": ("owner11-artifact/owner-spec/CLOSED.json", 744, "2f9439efb6b510692e4562cf50111bb3b9771e6669b73b89364bd36c8f5bec2d"),
    "artifact11_unregister": ("owner11-artifact/UNREGISTER.json", 978, "03bcc51fda82875b47ef46b6c07f80f83e35f07674b0e02df6b9ac0525710a1b"),
    "exports_and_data": ("attempt11-artifact-postcheck/exports-and-data.json", 1783, "073073c0d63d29f90e319726b4617363f8caa400102b17f7d459f9e92a680db7"),
    "build08_result": ("attempt08-build/RESULT.json", 68788, "847b6b54f7e544315507dd5c0aa91e0d1abf992cecadd73c1a4fe2f9c94d6c85"),
    "build08_manifest": ("attempt08-build/project-exe-manifest.json", 10169, "f35cf135db1a564bcb55b3b5c932059deb4369d0e06fd4a5ff006b25d80e57a7"),
    "build08_spec": ("owner08-build/owner-spec/SPEC.json", 2059, "58a06b5408b45dc3097e5afc50c31dbc27a9613754596d59bd03d2d8cad27bd6"),
    "build08_closed": ("owner08-build/owner-spec/CLOSED.json", 745, "b73e93e01f6d51309faee52ddee5e0b490e553b0c6e10a449f7f76c632ca9562"),
    "build08_unregister": ("owner08-build/UNREGISTER.json", 975, "c1d64fc3a76ac2b44cc6bb17efd2b7721b94ce9c3bd5204b029668f860f3e093"),
    "prior08_admin_launch": ("attempt08-admin/LAUNCH-RESULT.json", 1817, "73cae6d2f7e52ccf2c3d0a60b8d367eac443e3b58580ad7a0f4c53ea970ce0a5")}
PRODUCERS = {
    "functional09": ("native30_functional09_20261020.py", "64f9e45fda32e82c7b723ce5aa3948c207be3de6b58d4f8036a48511c1c554d2"),
    "artifact11": ("native30_artifact_postcheck11_20261020.py", "bd3b72694121f96f5bcad08c2fb0bfc0c3f780bc40d0fba06d48fb7603571d5a")}
BUILD_KEYS = {"original_build_result": "build08_result", "project_exe_manifest": "build08_manifest",
    "original_build_owner_spec": "build08_spec", "original_build_owner_closed": "build08_closed",
    "original_build_unregister": "build08_unregister", "prior_failed_admin_launch": "prior08_admin_launch"}
REUSED_KEYS = {"result": "functional09_result", "summary": "functional09_summary", "spec": "functional09_spec",
    "closed": "functional09_closed", "unregister": "functional09_unregister"}


def _zero(value):
    require(type(value) is int and value == 0, "09+11 known actual0 required")


def _owner(docs, evidence, prefix, expected_exit, now):
    spec, closed, unreg = [docs[prefix + name] for name in ("_spec", "_closed", "_unregister")]
    nonce = spec.get("nonce")
    require(isinstance(nonce, str) and re.fullmatch("[0-9a-f]{32}", nonce)
        and nonce == closed.get("nonce") and spec.get("task_name") == "XARG2ManagedOwner-" + nonce
        and spec.get("role") == "native_build" and spec.get("sid") == OWNER_SID,
        "09+11 exact owned Task identity required")
    require(closed.get("spec_sha256") == evidence[prefix + "_spec"].sha256
        and type(closed.get("child_exit_code")) is int and closed["child_exit_code"] == expected_exit
        and type(closed.get("bootstrap_exit_code")) is int and closed["bootstrap_exit_code"] == expected_exit
        and closed.get("forced_remaining_cleanup") is False, "09+11 original parent exit must remain exact")
    _zero(closed.get("job_active_after_stage"))
    child = closed.get("child", {})
    require(type(child.get("pid")) is int and child["pid"] > 0
        and isinstance(child.get("creation_filetime"), str) and re.fullmatch("[1-9][0-9]*", child["creation_filetime"])
        and _path(child.get("image")) == _path(spec.get("python"))
        and child.get("image_file_id") == spec.get("python_file_id"), "09+11 full birth/image/FileID binding differs")
    require(unreg.get("operation") == "unregister" and unreg.get("task_name") == spec["task_name"], "09+11 unregister Task differs")
    actual = unreg.get("actual", {})
    require(actual.get("sid") == OWNER_SID and actual.get("absent_after") is True,
        "09+11 Task absence must be observed")
    _zero(actual.get("instances"))
    require(type(actual.get("last_result")) is int and actual["last_result"] == expected_exit,
        "09+11 scheduler result differs from original failed/successful parent")
    require(_time(closed.get("utc")) <= _time(unreg.get("utc")) <= now, "09+11 closure chronology differs")
    if prefix in PRODUCERS:
        filename, sha = PRODUCERS[prefix]
        require(ntpath.basename(spec.get("stage", "")) == filename and spec.get("stage_sha256") == sha
            and spec.get("bootstrap_sha256") == C0_SHA, "09+11 actual producer/bootstrap source differs")
        result = docs[prefix + "_result"]
        _same_ref(result.get("plan"), evidence[prefix + "_plan"].reference)
        argv = spec.get("stage_args")
        require(isinstance(argv, list) and len(argv) == 7 and argv[0] == "--plan"
            and _path(argv[1]) == _path(result["plan"]["path"]) and argv[2] == "--admission"
            and _path(argv[3]) == _path(result.get("admission", {}).get("path"))
            and argv[4:] == ["--admission-sha256", result["admission"]["sha256"], "--execute"], "09+11 exact source/admission argv differs")
        require(_time(result.get("end_utc")) <= _time(closed["utc"]), "09+11 parent closed before result")
    return nonce, child


def _bindings(docs):
    files = docs["build08_manifest"].get("files")
    require(isinstance(files, list) and len(files) == 9, "09+11 exact original nine EXEs required")
    paths = set()
    vectors = [docs[name].get("exe_bindings") for name in ("build08_result", "functional09_result", "artifact11_result")]
    require(all(isinstance(v, list) and len(v) == 9 for v in vectors), "09+11 complete nine identity vectors required")
    for file, a, b, c in zip(files, *vectors):
        require(isinstance(file, dict) and ntpath.splitext(file.get("path", ""))[1].lower() == ".exe", "09+11 manifest EXE path required")
        path = _path(file["path"]); require(path not in paths, "09+11 aliased EXE path"); paths.add(path)
        for value in (a, b, c):
            require(isinstance(value, dict) and set(value) == {"path", "bytes", "sha256", "file_id"}, "09+11 full serialized EXE identity required")
            _ref({k: value[k] for k in ("path", "bytes", "sha256")})
            identity = value["file_id"]
            require(isinstance(identity, dict) and set(identity) == {"volume_serial", "file_id"}
                and isinstance(identity["volume_serial"], str) and identity["volume_serial"].isascii()
                and identity["volume_serial"].isdigit() and _sha(identity["file_id"], 32), "09+11 FileID missing")
        require(a == b == c and _path(a["path"]) == path and a["bytes"] == file.get("size")
            and a["sha256"] == file.get("sha256"), "09+11 EXE drift between actual stages")
    require({row.get("target") for row in files} == set(FIXTURE_TARGETS), "09+11 original target set differs")


def _native_facts(docs, evidence, now):
    nine, artifact, delivery = [docs[n] for n in ("functional09_result", "artifact11_result", "artifact11_delivery")]
    require(nine.get("schema") == "native30-functional-qualification-v1" and nine.get("status") == "FAILED"
        and nine.get("stage") == "functional_test_only" and nine.get("run_id") == "native30-functional09"
        and nine.get("error") == {"type": "RuntimeError", "text": "five exports"}, "09+11 only actual09 failed export gate subfacts are reusable")
    require(artifact.get("schema") == "native30-artifact-postcheck-v1"
        and artifact.get("status") == "OFFLINE_ARTIFACT_QUALIFIED_NOT_DEPLOYED"
        and artifact.get("phase") == "artifact_postcheck_only" and "error" not in artifact,
        "09+11 complete artifact11 protocol required")
    for value in (nine, artifact, delivery):
        require(value.get("source_commit") == SOURCE and value.get("defender_registration_pending") is True
            and value.get("os_qualification") == "UNKNOWN", "09+11 source/unknown OS boundary differs")
    require(nine.get("defender_effective_settings_known") is False and nine.get("prior_admin_future_writes") is None,
        "09+11 old08 administrative unknown must remain")
    require(nine.get("DLL_loaded") is False and nine.get("production_recompiled") is False,
        "09+11 original functional stage must not load/recompile Native")
    failed_admin = docs["prior08_admin_launch"]
    require(failed_admin.get("status") == "FAILED_OR_UNKNOWN" and failed_admin.get("settings_success") is False
        and failed_admin.get("future_writes") is None, "09+11 must not repair prior admin status")
    build = docs["build08_result"]
    require(build.get("status") == "BUILD_READY_FOR_ADMIN" and build.get("stage") == "build_only"
        and build.get("fixture_executions") == 0 and len(build.get("fixture_builds", [])) == 9,
        "09+11 original build-only facts differ")
    _same_ref(build.get("project_exe_manifest"), evidence["build08_manifest"].reference)
    for row in build["fixture_builds"]: _zero(row.get("returncode")); _zero(row.get("owned_active_after"))
    for key, name in BUILD_KEYS.items():
        _same_ref(nine.get(key), evidence[name].reference)
        _same_ref(artifact.get("original_build", {}).get(key), evidence[name].reference)
    for key, name in REUSED_KEYS.items():
        _same_ref(artifact.get("reused09", {}).get(key), evidence[name].reference)
        _same_ref(delivery.get("reused09", {}).get(key), evidence[name].reference)
    _same_ref(artifact.get("delivery"), evidence["artifact11_delivery"].reference)
    require(nine.get("snapshot") == artifact.get("snapshot") and isinstance(artifact.get("snapshot"), dict),
        "09+11 retained snapshot identity differs")
    _ref({key: artifact["snapshot"].get(key) for key in ("path", "bytes", "sha256")})
    for prefix, exit_code in (("build08", 0), ("functional09", 1), ("artifact11", 0)):
        _owner(docs, evidence, prefix, exit_code, now)
    for prefix in ("functional09", "artifact11"):
        summary = docs[prefix + "_summary"]
        for key, suffix in (("result", "_result"), ("spec", "_spec"), ("outer_closed", "_closed"), ("unregister", "_unregister")):
            _same_ref(summary.get(key), evidence[prefix + suffix].reference)
        require(summary.get("status") == docs[prefix + "_result"]["status"], "09+11 summary/result status differs")
    _same_ref(docs["artifact11_summary"].get("delivery"), evidence["artifact11_delivery"].reference)
    require(len({docs[n + "_spec"]["nonce"] for n in ("build08", "functional09", "artifact11")}) == 3,
        "09+11 distinct owned attempts required")
    _bindings(docs)
    phases, journals = _commands_closed(nine, successful=True)
    # All command children were successful; only the enclosing Python guard
    # failed. This does not promote the 09 parent to exit0 or whole PASS.
    require(nine.get("fixture_executions") == 9 and nine.get("fixture_builds") == []
        and len(nine.get("fixture_runs", [])) == 9 and len(phases) == 13, "09+11 complete original09 subchain required")
    fixtures = docs["native_plan"].get("fixtures")
    require(docs["native_plan"].get("schema") == "native30-wholeclean-plan-v1"
        and isinstance(fixtures, list) and tuple(v.get("target") for v in fixtures) == FIXTURE_TARGETS
        and docs["functional09_plan"].get("fixtures") == fixtures,
        "09+11 original nine fixture contract required")
    for prefix, schema in (("functional09", "native30-functional09-plan-v1"), ("artifact11", "native30-artifact-postcheck11-plan-v1")):
        plan, spec = docs[prefix + "_plan"], docs[prefix + "_spec"]
        require(plan.get("schema") == schema and plan.get("source_commit") == SOURCE
            and _path(plan.get("producer", {}).get("path")) == _path(spec["stage"])
            and plan["producer"].get("sha256") == spec["stage_sha256"], "09+11 frozen plan/producer differs")
    start, end = _time(nine.get("start_utc")), _time(nine.get("end_utc"))
    require(start <= end <= _time(artifact.get("start_utc")) <= _time(artifact.get("end_utc")) <= now,
        "09+11 stage chronology differs")
    for fixture, row in zip(fixtures, nine["fixture_runs"]):
        matches = [p for p in phases if p == row]
        require(len(matches) == 1 and _path(row["argv"][0]) == _path(ntpath.join(ntpath.dirname(delivery["DLL"]["path"]), fixture["artifact"])), "09+11 original actual fixture executable/order differs")
        wanted, actual = fixture.get("args", []), row["argv"][1:]
        require(len(wanted) == len(actual), "09+11 original fixture args differ")
        for w, a in zip(wanted, actual):
            if w == "$OBSERVED_UTC": require(start <= _time(a) <= _time(row["start_utc"]), "09+11 fixture UTC differs")
            else: require(a == (nine["machine_id"] if w == "$MACHINE_ID" else w), "09+11 original fixture args differ")
        if fixture.get("postcheck"):
            post = [p for p in phases if len(p["argv"]) == 4 and ntpath.basename(p["argv"][2]) == ntpath.basename(fixture["postcheck"])
                and p["argv"][-1] == row["log"]["path"]]
            require(len(post) == 1, "09+11 original layout postcheck missing")
    current, commands = _commands_closed(artifact, successful=True)
    require(len(current) == 2 and artifact.get("project_EXE_executions") == 0 and artifact.get("fixture_builds") == 0
        and artifact.get("fixture_runs_reused") == 9 and artifact.get("production_recompiled") is False,
        "09+11 only the two postcheck commands may execute")
    for value in (nine, artifact):
        for name in ("owned_active_after", "future_writes", "Game_calls", "UAC_calls", "system_settings_operations"): _zero(value.get(name))
    argv = current[0]["argv"]; root = ntpath.dirname(ntpath.dirname(delivery["DLL"]["path"]))
    require(len(argv) == 11 and ntpath.basename(argv[0]).lower() == "ninja.exe"
        and argv[1:2] == ["-C"] and _path(argv[2]) == _path(ntpath.join(root, "build"))
        and argv[3] == "-f" and _path(argv[4]) == _path(ntpath.join(root, "attempt07", "production-manifest.ninja"))
        and argv[5:] == ["-n", "-d", "explain", "xar_ck3_bridge", "xar_ck3_12002_runtime", "xar_bridge_protocol"],
        "09+11 retained snapshot NoWork command differs")
    require(current[1]["argv"][1:] == ["/LIST", delivery["runtime_archive"]["path"]]
        and ntpath.basename(current[1]["argv"][0]).lower() == "lib.exe", "09+11 exact archive postcheck differs")
    require(delivery.get("qualification_kind") == "artifact_plus_closed09_functional_only"
        and delivery.get("native_build_label") == NATIVE30_BUILD_LABEL
        and delivery.get("production_reused_from_attempt02") is True
        and delivery.get("nine_functional_runs_reused_from_failed09") is True
        and delivery.get("prior_failures_requalified") is False and delivery.get("Game_camera_H") == "NOTRUN"
        and delivery.get("deployed") is False and artifact.get("deployed") is False, "09+11 artifact scope differs")
    _same_ref(delivery.get("exports_and_data"), evidence["exports_and_data"].reference)
    export = docs["exports_and_data"]; rows = export.get("exports", [])
    expected = ["XarCk3BridgeIdentity", "XarCk3BridgePrepareStartup", "XarCk3BridgeStart", "XarCk3BridgeStartWithPipe", "XarCk3BridgeStop"]
    require(len(rows) == 6 and [r.get("name") for r in rows[:5]] == expected
        and rows[5].get("name") == "XarRefillCoreCarrier12004" and export.get("DATA_is_not_callable") is True,
        "09+11 exact five bridge code exports plus one non-callable DATA required")
    section = export.get("data_section", {})
    require(section.get("name") == ".data" and type(section.get("rva")) is int and type(section.get("size")) is int
        and section["rva"] <= rows[5].get("rva", -1) < section["rva"] + section["size"]
        and all(type(row.get("rva")) is int and not section["rva"] <= row["rva"] < section["rva"] + section["size"] for row in rows[:5])
        and "army_regular_core_passive_12004.cpp.obj" in export.get("map_public_row", "")
        and export.get("map_sha256") == delivery.get("map", {}).get("sha256"), "09+11 DATA section/map classification differs")
    components = delivery.get("component_objects")
    require(isinstance(components, list) and len(components) == 3
        and len({c.get("payload", {}).get("name") for c in components}) == 3, "09+11 three unique archive component payloads required")
    frozen = {r["path"]: r for r in docs["source_freeze"].get("files", [])}
    for row in components:
        for key in ("source", "object"): _ref(row.get(key))
        relative = ntpath.relpath(row["source"]["path"], ntpath.join(root, "source")).replace("\\", "/")
        require(relative in frozen and frozen[relative]["bytes"] == row["source"]["bytes"]
            and frozen[relative]["sha256"] == row["source"]["sha256"], "09+11 component does not bind source704 freeze")
        require(row["object"]["bytes"] == row.get("payload", {}).get("bytes")
            and row["object"]["sha256"] == row["payload"].get("sha256"), "09+11 archive payload/object differs")
    return {"build_chain": CHAIN, "functional09_status_preserved": "FAILED", "functional09_parent_exit_preserved": 1,
        "closed09_fixture_nodes": 9, "closed09_layout_postcheck": True,
        "artifact11_status": artifact["status"], "artifact11_parent_exit": 0,
        "nine_identities_equal_original_build": True, "nine_nodes_reexecuted": False,
        "OS_qualification": "UNKNOWN", "Defender_registration_pending": True,
        "prior08_admin_future_writes_preserved": None, "loaded_provider_issued": False, "H": "NOTRUN"}


def validate_functional_artifact_transition_v1(*, base_freeze, base_native_pin, capacity, evidence,
        machine_id, source_fixture=False, now=None):
    require(type(source_fixture) is bool and isinstance(machine_id, str) and machine_id not in ("", "unknown"),
        "09+11 explicit fixture boundary and known machine required")
    require(isinstance(evidence, dict) and set(evidence) == set(EVIDENCE_NAMES), "09+11 complete fixed evidence set required")
    base, old, card = _doc(base_freeze), _doc(base_native_pin), _doc(capacity)
    docs = {name: _doc(evidence[name]) for name in EVIDENCE_NAMES}
    for value in (base, old, card, *docs.values()):
        if "machine_id" in value: require(value["machine_id"] == machine_id, "09+11 foreign machine")
        require(source_fixture or value.get("source_fixture") is not True, "09+11 synthetic evidence cannot admit export")
    require(base.get("machine_id") == old.get("machine_id") == card.get("machine_id") == machine_id
        and (source_fixture or machine_id == MACHINE), "09+11 original closed machine required")
    require(base.get("status") == "FINAL_SOURCE_FROZEN" and base.get("native_build_label") == old.get("native_build_label")
        and base.get("native_dll_sha256") == old.get("native_dll_sha256") and _sha(old.get("native_dll_sha256")),
        "09+11 original Native29 base must remain unchanged")
    require(card.get("schema") == CARD_SCHEMA and card.get("status") == "ADMITTED"
        and card.get("native_pin_sha256") == base_native_pin.sha256 and card.get("base_freeze_sha256") == base_freeze.sha256,
        "09+11 original old29 capacity fields differ")
    now = datetime.now(timezone.utc) if now is None else now
    require(now.tzinfo is not None and now < _time(card.get("review_at_utc")), "09+11 capacity review expired")
    transition = card.get("native_transition", {})
    require(transition.get("schema") == TRANSITION_SCHEMA and transition.get("build_chain") == CHAIN
        and transition.get("from_generation") == 29 and transition.get("to_generation") == 30,
        "09+11 explicit independent metadata protocol required")
    for name in EVIDENCE_NAMES: _same_ref(transition.get(name), evidence[name].reference)
    for name, (relative, size, sha) in FIXED.items():
        if not source_fixture:
            require(evidence[name].sha256 == sha and len(evidence[name].raw) == size, "09+11 unrecognized original closed receipt: " + name)
            if relative is not None:
                # Root's byte-identical promoted summary is an allowed source
                # alias; every backlink inside it still points to the original.
                original = _path(ntpath.join(ROOT, relative))
                promoted = name == "artifact11_summary" and ntpath.basename(evidence[name].path) == "native30-artifact11-actual-closed-2026-10-20.json"
                require(_path(evidence[name].path) == original or promoted, "09+11 original receipt path differs")
    target, delivery, freeze = [docs[n] for n in ("target_native_pin", "artifact11_delivery", "source_freeze")]
    require(target.get("machine_id") == machine_id and target.get("native_build_label") == NATIVE30_BUILD_LABEL
        and transition.get("target_native_build_label") == NATIVE30_BUILD_LABEL
        and target.get("defender_registration_pending") is True and target.get("os_qualification") == "UNKNOWN",
        "09+11 target description/OS unknown metadata required")
    require(transition.get("source_commit") == freeze.get("commit") == SOURCE, "09+11 exact source704 required")
    # These are source-only plans; they supply no08B administrator success.
    readonly, snapshot_plan = docs["native_readonly_plan"], docs["snapshot07_plan"]
    _same_ref(docs["functional09_plan"].get("base_plan"), evidence["native_readonly_plan"].reference)
    path07 = "docs/ck3-native-ai/evidence/native30-fixture07-snapshot-plan-2026-10-20.json"
    ref07 = readonly.get("base_readonly_plan", {})
    require(readonly.get("schema") == "native30-08B-two-stage-plan-v1" and readonly.get("source_commit") == SOURCE
        and ref07.get("path") == path07 and ref07.get("bytes") == len(evidence["snapshot07_plan"].raw)
        and ref07.get("sha256") == evidence["snapshot07_plan"].sha256
        and readonly.get("helper_pins", {}).get(path07) == ref07["sha256"], "09+11 fixed readonly plan lineage differs")
    prior = [row for row in snapshot_plan.get("prior_pins", []) if ntpath.basename(row.get("path", "")) == "source-freeze.json"]
    require(snapshot_plan.get("schema") == "native30-fixture07-snapshot-plan-v1" and snapshot_plan.get("source_commit") == SOURCE
        and len(prior) == 1 and _ref(prior[0]) == _ref(evidence["source_freeze"].reference),
        "09+11 complete native source freeze provenance differs")
    require(snapshot_plan.get("helper_pins", {}).get("docs/ck3-native-ai/evidence/native30-wholeclean-producer-plan-2026-10-19.json")
        == evidence["native_plan"].sha256, "09+11 native whole plan provenance differs")
    _ref(delivery.get("DLL"))
    require(target.get("native_dll_sha256") == delivery["DLL"]["sha256"]
        and target["native_dll_sha256"] != old["native_dll_sha256"], "09+11 target DLL must match artifact11 and differ from old29")
    if not source_fixture:
        require(target["native_dll_sha256"] == "39350bd933549ff11e7a79e1b1e0340664bf87ee129a2aa8cdb7b0e9be269f56", "09+11 actual closed DLL pin differs")
    compat = docs["compatibility"]
    require(compat.get("schema") == "xar.ck3.native29-to30-compatibility/v1"
        and compat.get("machine_id") == machine_id, "09+11 explicit EXE/ABI compatibility evidence required")
    bindings = []
    for name, native in (("base_exe_binding", base_native_pin), ("target_exe_binding", evidence["target_native_pin"])):
        binding = docs[name]; _same_ref(binding.get("native_pin"), native.reference)
        require(binding.get("schema") == "xar.ck3.native-executable-binding/v1" and binding.get("machine_id") == machine_id,
            "09+11 exact same-machine EXE binding required")
        image = binding.get("game_executable", {})
        require(_sha(image.get("sha256")) and type(image.get("bytes")) is int and image["bytes"] > 0
            and image.get("version") == "1.20.0.4" and image.get("architecture") == "x64"
            and binding.get("wire_contract") == {"protocol_version": 1, "campaign_root_envelope_fields": list(ROOT_FIELDS)}
            and binding.get("native_layout_id") == "ck3-1.20.0.4", "09+11 unsupported EXE/ABI/wire transition")
        _same_ref(compat.get(name), evidence[name].reference); bindings.append(image)
    require(bindings[0] == bindings[1], "09+11 cross-build transition is not supported")
    for name in ("source_freeze", "artifact11_result", "artifact11_delivery", "functional09_result"):
        _same_ref(compat.get(name), evidence[name].reference)
    _same_ref(docs["target_exe_binding"].get("source_freeze"), evidence["source_freeze"].reference)
    rows = freeze.get("files"); seen = set()
    require(isinstance(rows, list) and rows, "09+11 source freeze rows required")
    for row in rows:
        path = row.get("path")
        require(isinstance(path, str) and path not in seen and not ntpath.isabs(path) and not ntpath.splitdrive(path)[0]
            and "\\" not in path and all(x not in ("", ".", "..") for x in path.split("/"))
            and type(row.get("bytes")) is int and row["bytes"] >= 0 and _sha(row.get("sha256")) and _sha(row.get("git_blob"), 40),
            "09+11 unsafe/incomplete source freeze row")
        seen.add(path)
    audit = _native_facts(docs, evidence, now)
    metadata = {"schema": TRANSITION_SCHEMA, "build_chain": CHAIN, "machine_id": machine_id,
        "base_freeze": base_freeze.reference, "base_native_pin": base_native_pin.reference,
        "base_native_build_label": old["native_build_label"], "base_native_dll_sha256": old["native_dll_sha256"],
        **{name: evidence[name].reference for name in EVIDENCE_NAMES}, "build_chain_provenance": audit,
        "target_native_build_label": NATIVE30_BUILD_LABEL, "qualification_kind": "artifact_plus_closed09_functional_only",
        "defender_registration_pending": True, "os_qualification": "UNKNOWN", "source_fixture": source_fixture,
        "runtime_admitted": False, "actual_loaded_provider_issued": False, "H": "NOTRUN"}
    return NativeTransitionV1(json.dumps({"native_build_label": NATIVE30_BUILD_LABEL,
        "native_dll_sha256": target["native_dll_sha256"]}).encode(), json.dumps(metadata).encode(), source_fixture)
