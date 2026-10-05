from pathlib import Path
import ast
import ctypes
import hashlib
import json
import stat
from datetime import datetime, timezone

BASE = Path("C:/workspace/ck3_lyd_runtime_20261004")
READY = BASE / "r10-source-ready-007-20261005-001"
INPUTS = BASE / "r10-source007-qualified-inputs-20261005-001"
OLD = BASE / "r9-lyd-claim-consumption-source-author-20261005-001/actual-source-ready-006-001"
DELIVERY = BASE / "r10-source007-qualified-delivery-20261005-001"
HEAD = "d0f8fa3b9d444828759443aa018bfd7ad31b398d"
ALLOWED = {"PINNED_SOURCE_RECORD_REF", "PINNED_SOURCE_SUMMARY", "RUNTIME_ROWS"}
checks = []

def need(ok, label, evidence=None):
    if not ok:
        raise ValueError(label)
    checks.append({"condition": label, "matched": True, "evidence": evidence})

def raw(p):
    return Path(p).read_bytes()

def sha(data):
    return hashlib.sha256(data).hexdigest()

def ref(p):
    p = Path(p)
    data = raw(p)
    return {"path": p.as_posix(), "bytes": len(data), "sha256": sha(data)}

def readj(p):
    return json.loads(raw(p).decode("utf-8"))

def verify_ref(r):
    data = raw(r["path"])
    if len(data) != r["bytes"] or sha(data) != r["sha256"]:
        raise ValueError("immutable reference mismatch: " + r["path"])
    return data

def writej(p, obj):
    with Path(p).open("xb") as f:
        f.write((json.dumps(obj, ensure_ascii=True, indent=2) + "\n").encode("utf-8"))

def indexed(root, expected_sha):
    index = ref(root / "INDEX.json")
    need(index["sha256"] == expected_sha, "exact package INDEX", index)
    j = readj(root / "INDEX.json")
    names = set()
    total = 0
    for row in j["files"]:
        rel = Path(row["path"])
        if rel.is_absolute() or ".." in rel.parts or row["path"] in names:
            raise ValueError("unsafe/duplicate indexed path")
        names.add(row["path"])
        item = ref(root / rel)
        if item["bytes"] != row["bytes"] or item["sha256"] != row["sha256"]:
            raise ValueError("indexed payload mismatch: " + row["path"])
        total += item["bytes"]
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}
    need(actual == names | {"INDEX.json"}, "exact payload coverage", {"files": len(names), "bytes": total})
    return index, j

def assignments(t):
    out = {}
    for n in t.body:
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name) and n.targets[0].id in ALLOWED:
            out[n.targets[0].id] = ast.literal_eval(n.value)
    return out

def normalized_provider(t):
    for n in t.body:
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name) and n.targets[0].id in ALLOWED:
            n.value = ast.Constant(value="SOURCE_PIN_LITERAL")
    return ast.dump(t, include_attributes=False)

def make_index(root, schema):
    rows = []
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.name != "INDEX.json":
            r = ref(p)
            rows.append({"path": p.relative_to(root).as_posix(), "bytes": r["bytes"], "sha256": r["sha256"]})
    writej(root / "INDEX.json", {"schema": schema, "files": rows})
    return ref(root / "INDEX.json")

def freeze(root):
    files = [p for p in root.rglob("*") if p.is_file()]
    for p in files:
        p.chmod(stat.S_IREAD)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetFileAttributesW.argtypes = [ctypes.c_wchar_p]
    kernel.GetFileAttributesW.restype = ctypes.c_uint32
    for p in files:
        attrs = kernel.GetFileAttributesW(str(p))
        if attrs == 0xFFFFFFFF or not attrs & 1:
            raise ValueError("readonly verification failed: " + str(p))
    return len(files)

if DELIVERY.exists():
    raise ValueError("new delivery directory already exists")
DELIVERY.mkdir()
try:
    ready_index, ready_items = indexed(READY, "76e84c70beccf22bda5ab202bb6de571f47f210645fe015b9f8f7628354e1ee2")
    old_index, _ = indexed(OLD, "34b38ce57671182a881e890d822dc8e932a66db36bcfec0a46304b3bfc6705a4")
    new_source = raw(READY / "unbound-bundle-011/verifier.py").decode("utf-8")
    old_source = raw(OLD / "unbound-bundle-010/verifier.py").decode("utf-8")
    new_tree = ast.parse(new_source)
    old_tree = ast.parse(old_source)
    constants = assignments(new_tree)
    need(set(constants) == ALLOWED, "exact three source pin assignments")
    need(normalized_provider(ast.parse(new_source)) == normalized_provider(ast.parse(old_source)), "whole provider AST unchanged except three source pin literals", {"functions": len([n for n in new_tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))])})
    old_binder = raw(OLD / "bind_verifier.py").decode("utf-8")
    new_binder = raw(READY / "bind_verifier.py").decode("utf-8")
    need(new_binder == old_binder.replace("unbound-bundle-010/verifier.py", "unbound-bundle-011/verifier.py"), "binder byte exact except local unbound provider path")
    need(raw(READY / "emit_first_join_evidence.py") == raw(OLD / "emit_first_join_evidence.py"), "emitter original bytes unchanged", ref(READY / "emit_first_join_evidence.py"))
    record_ref = ref(INPUTS / "ROOT-SOURCE-PIN-RECORD.actual.json")
    need(record_ref["bytes"] == 3229 and record_ref["sha256"] == "8784d98ecba357db56811fb2d3c850bc505aae81b076d0cf598cccf0294a770b", "exact actual source record", record_ref)
    need(raw(INPUTS / "ROOT-SOURCE-PIN-RECORD.actual.json") == raw(READY / "unbound-bundle-011/SOURCE-PIN-RECORD.raw.json"), "source record copied exact into provider bundle")
    need(Path(constants["PINNED_SOURCE_RECORD_REF"]["path"]) == Path(record_ref["path"]) and constants["PINNED_SOURCE_RECORD_REF"]["bytes"] == record_ref["bytes"] and constants["PINNED_SOURCE_RECORD_REF"]["sha256"] == record_ref["sha256"], "provider exact source record reference")
    record = readj(INPUTS / "ROOT-SOURCE-PIN-RECORD.actual.json")
    for key, r in record.items():
        if isinstance(r, dict) and set(r) == {"path", "bytes", "sha256"}:
            verify_ref(r)
    need(record["source"]["head"] == HEAD, "all source record artifact references hash matched", {"head": HEAD, "reference_count": 12})
    summary = constants["PINNED_SOURCE_SUMMARY"]
    need(summary == readj(READY / "SOURCE-READBACK.json"), "provider summary equals actual source readback bytes interpretation")
    need(summary["status"] == "ACTUAL_FROZEN_SOURCE_PINS_MATCH" and summary["source"] == record["source"], "source readiness status and exact source four identities")
    manifest = json.loads(verify_ref(record["production_manifest"]).decode("utf-8"))
    rows = manifest["files"]
    need(len(rows) == 70 and constants["RUNTIME_ROWS"] == rows, "provider actual production 70 rows exact")
    stage = BASE / "r10-root-head-export-20261005-001/production/mod_li_yu_dao"
    for row in rows:
        item = ref(stage / row["path"])
        if item["bytes"] != row["size"] or item["sha256"] != row["sha256"]:
            raise ValueError("actual staging mismatch: " + row["path"])
    need({p.relative_to(stage).as_posix() for p in stage.rglob("*") if p.is_file()} == {r["path"] for r in rows}, "production staged file inventory exact 70")
    old_manifest = readj(BASE / "r9-root-head-export-20261005-002/production/mod_li_yu_dao.manifest.json")
    before_rows = {r["path"]: r for r in old_manifest["files"]}
    after_rows = {r["path"]: r for r in rows}
    need(set(before_rows) == set(after_rows), "runtime paths no additions or removals")
    delta = [{"path": p, "before": before_rows[p], "after": after_rows[p]} for p in sorted(after_rows) if before_rows[p] != after_rows[p]]
    approved = readj(BASE / "r10-full-runtime-independent-review-20261005-001/review-package-002/APPROVED-RUNTIME-DELTA-18.json")
    need(len(delta) == 18 and delta == summary["runtime_diff_vs006"] and delta == approved, "all 18 runtime differences exact independently approved; remaining 52 exact", {"changed": 18, "unchanged": 52})
    old_inv = readj(BASE / "r9-root-head-export-20261005-002/SOURCE-INVENTORY.json")
    new_inv = json.loads(verify_ref(record["source_inventory"]).decode("utf-8"))
    old_files = {r["path"]: r for r in old_inv["files"]}
    new_files = {r["path"]: r for r in new_inv["files"]}
    source_diff = [{"path": p, "before": old_files.get(p), "after": new_files.get(p)} for p in sorted(set(old_files) | set(new_files)) if old_files.get(p) != new_files.get(p)]
    need(len(new_files) == 6066 and len(source_diff) == 112 and source_diff == summary["complete_source_diff_vs006"] and summary["complete_source_diff_count_vs006"] == 112, "complete source diff records exact actual 6066 inventory and 112 differences", {"actual_source_files": 6066, "source_differences": 112})
    for k in ("ordinary_contract", "generic_host", "native_launch_parser"):
        need(summary["approved_source_leafs"][k] == record[k], "source leaf exact: " + k, record[k])
    for k in ("root_reviewed_delta", "independent_runtime_review", "full_source_review"):
        verify_ref(summary[k])
    need(readj(summary["independent_runtime_review"]["path"])["status"] == "SOURCE_ONLY_REVIEWED", "independent source-only runtime review frozen ref exact", summary["independent_runtime_review"])
    build = json.loads(verify_ref(record["native_build_result"]).decode("utf-8"))
    inner = json.loads(verify_ref(build["native_msvc_result"]).decode("utf-8"))
    truth = summary["native_build_truth"]
    need(build["status"] == "ACTUAL_RELEASE_BUILD_RED" and build["exit_code"] == 1 and build["actual_compilation_pass"] is True, "outer compilation pass and operational RED both preserved")
    need(inner["status"] == "built_defender_registration_failed" and inner["built"] is True and inner["build_succeeded"] is True, "inner built artifacts and failed Defender registration preserved")
    need(truth["actual_result"] == record["native_build_result"] and truth["overall_status"] == build["status"] and truth["overall_exit_code"] == 1 and truth["compilation_pass"] is True and truth["inner_status"] == inner["status"] and truth["Defender_status"] == "settings_failed" and truth["Defender_Add_calls"] == 1 and truth["Defender_effectiveness_credit"] is False and truth["native_business_acceptance"] == "NOT_RUN", "all summary build boundaries agree with actual native result")
    need(summary["actual_release_targets"] == build["targets"], "Release target refs copied exact from actual build")
    for target in build["targets"].values():
        verify_ref(target)
    need(build["source_revision"] == HEAD and build["native_tree"] == record["source"]["native_tree"] and build["configuration"] == "Release" and build["exported_source_exact_before_after"] is True and build["actual_game_calls"] == 0 and build["actual_pipe_calls"] == 0 and build["runtime_acceptance"] == "NOT_RUN", "build source provenance and NOT_RUN boundary actual")
    need(summary["actual_root_context_binding"] is None and summary["actual_release"] == "NOT_RUN" and summary["game_called"] is False and summary["Git_called"] is False, "no actual root context, claim release, game or Git credit")
    status = readj(READY / "STATUS.json")
    need(status["actual_root_context"] is None and status["actual_claim"] is None and status["actual_release"] == "NOT_RUN" and status["registry_enabled"] is False and status["actual_full_cycle_credit"] is False, "status leaves all future actual identity and full cycle unclaimed")
    bind = readj(READY / "BIND-REQUEST.template.json")
    need(bind["schema"] == "lyd.first-join.verifier-bind-request.v3" and bind["native_profile"] is None and bind["fresh_query_sdk"] is None and bind["fresh_query_frame_sdk"] is None and bind["output"] is None and bind["consumption_mode"] == "PROPOSAL_OPENED", "v3 binder and both observation v2 templates remain unbound")
    need(readj(READY / "BEFORE-OBSERVATION.template.json")["schema"] == "lyd.first-join.actual-observation.v2" and readj(READY / "AFTER-OBSERVATION.template.json")["schema"] == "lyd.first-join.actual-observation.v2", "v2 before and after observation shapes preserved")
    bundle = readj(READY / "unbound-bundle-011/INDEX.json")
    need(bundle["schema"] == "ck3-ordinary-interaction-consumption-verifier-bundle-v1" and bundle["entrypoint"] == "verifier.py:verify_consumption" and {r["path"] for r in bundle["files"]} == {"verifier.py", "SOURCE-PIN-RECORD.raw.json"} and all(sha(raw(READY / "unbound-bundle-011" / r["path"])) == r["sha256"] for r in bundle["files"]), "generic host frozen bundle exact entrypoint and payload coverage")
    if (INPUTS / "INDEX.json").exists():
        raise ValueError("new author input index already exists")
    inputs_index = make_index(INPUTS, "lyd.claim-verifier007.actual-qualified-input-index.v1")
    readonly_ready = freeze(READY)
    readonly_inputs = freeze(INPUTS)
    report = {
        "schema": "lyd.claim-verifier007.final-qualified-source-delivery.v1",
        "utc": datetime.now(timezone.utc).isoformat(),
        "status": "ACTUAL_FROZEN_SOURCE_PINS_MATCH",
        "scope": "SOURCE_ONLY; actual archived source and artifacts, no game or claim execution",
        "source": record["source"], "source_counts": summary["source_counts"],
        "runtime_changed": 18, "runtime_unchanged": 52, "complete_source_differences_vs006": 112,
        "source_ready_index": ready_index, "source_pin_record": record_ref, "author_inputs_index": inputs_index,
        "provider": ref(READY / "unbound-bundle-011/verifier.py"),
        "binder": ref(READY / "bind_verifier.py"), "emitter": ref(READY / "emit_first_join_evidence.py"),
        "source_readback": ref(READY / "SOURCE-READBACK.json"),
        "frozen_readonly_files": {"source_ready": readonly_ready, "actual_inputs": readonly_inputs},
        "checks": checks, "native_build_truth": truth, "actual_release_targets": summary["actual_release_targets"],
        "actual_root_context": None, "actual_claim": None, "actual_registry_enabled": False,
        "actual_host_release": "NOT_RUN", "actual_MCP_calls": 0, "actual_game_calls": 0,
        "native_business_acceptance": "NOT_RUN", "full_cycle_acceptance": False,
        "ROOT_interface": {"source_ready": {"author_index": {"path": ready_index["path"], "sha256": ready_index["sha256"]}, "source_record": record_ref}}
    }
    writej(DELIVERY / "REPORT.json", report)
    writej(DELIVERY / "SOURCE_READY.actual.refs.json", report["ROOT_interface"]["source_ready"])
    with (DELIVERY / "ROOT-OPERATIONS.md").open("x", encoding="utf-8", newline="\n") as f:
        f.write("Use SOURCE_READY.actual.refs.json for consumer source_ready inputs.\n\n")
        f.write("The qualified SOURCE_ONLY bundle pins actual HEAD d0f8fa3b9d444828759443aa018bfd7ad31b398d, 70 production files, exactly 18 reviewed runtime changes and 112 full-source inventory differences versus006. All provider functions are unchanged; binder only selects the new local provider file; emitter bytes are unchanged.\n\n")
        f.write("Actual Release compilation succeeded. The overall build returned RED/exit1 because one Defender Add invocation failed. Exclusion effectiveness and native business acceptance remain false/NOT_RUN. ROOT expressly permitted these exact compiled artifact hashes for this source package.\n\n")
        f.write("Only ROOT may supply a future actual profile, PID/create/FILETIME provenance, fresh query/frame, before/after immutable save observations and new intended interaction. No registry, binding, emission, release, game or MCP action was executed here. ACK remains pending until immutable consumption evidence verifies it.\n")
    with (DELIVERY / "verify_source007_delivery.py").open("xb") as f:
        f.write(Path(__file__).read_bytes())
    delivery_index = make_index(DELIVERY, "lyd.claim-verifier007.final-qualified-delivery-index.v1")
    freeze(DELIVERY)
    print(json.dumps({"status": report["status"], "source_ready_index": ready_index, "source_record": record_ref, "delivery_index": delivery_index, "report": ref(DELIVERY / "REPORT.json"), "author_inputs_index": inputs_index, "matched_conditions": len(checks), "actual_root_context": None, "actual_host_release": "NOT_RUN"}, ensure_ascii=True))
except Exception as exc:
    failure = {"status": "FAILED_CLOSED", "reason": str(exc), "matched_conditions_before_refusal": checks, "actual_game_calls": 0, "actual_MCP_calls": 0}
    writej(DELIVERY / "FAILURE.json", failure)
    raise
