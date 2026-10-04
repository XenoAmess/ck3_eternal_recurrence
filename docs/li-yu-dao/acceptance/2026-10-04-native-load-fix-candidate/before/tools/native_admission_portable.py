"""Validate permanent tracked R0002 proof only; never follow archived raw paths."""

import hashlib
import json
from pathlib import Path, PureWindowsPath
import re

from school_consent_data import BASELINE_COMMIT, GAME_VERSION

SCHEMA = "lyd.native-primitive-tracked-proof-admission.v1"


def validate_portable(path: Path, record: dict, checkout: Path) -> dict:
    if (record.get("scope") != "native-primitives-only"
            or record.get("baseline_commit") != BASELINE_COMMIT
            or record.get("authorized_by") != "/root"
            or set(record.get("primitives", [])) != {"set_parent_faith", "detach_rite_to_new_faith"}):
        raise ValueError("Portable primitive admission policy mismatch")
    checkout = checkout.resolve()
    refs = {}
    for item in record.get("evidence_refs", []):
        relative = item["path"]
        if Path(relative).is_absolute() or PureWindowsPath(relative).is_absolute() or ":" in relative:
            raise ValueError("Portable proof path must be checkout-relative")
        target = (checkout / relative).resolve()
        if checkout not in target.parents:
            raise ValueError("Portable proof path escaped checkout")
        actual = hashlib.sha256(target.read_bytes()).hexdigest()
        if actual != item["sha256"]:
            raise ValueError(f"Portable proof hash mismatch: {relative}")
        if item["role"] in refs:
            raise ValueError("Duplicate portable proof role")
        refs[item["role"]] = {"path": target, "relative": relative, "sha256": actual}
    required = {"attestation", "saved_graph_summary", "markers", "probe_effects", "probe_triggers",
                "error_classification", "saved_actor", "saved_rite", "saved_faith", "saved_head"}
    if not required <= refs.keys():
        raise ValueError("Portable proof lacks a required permanent report/excerpt")
    proof = json.loads(refs["attestation"]["path"].read_text(encoding="utf-8-sig"))
    graph = json.loads(refs["saved_graph_summary"]["path"].read_text(encoding="utf-8-sig"))
    if (proof.get("schema") != "lyd.native-primitive-three-rounds-attestation-candidate.v2"
            or proof.get("primitive_verdict") != "ACCEPTED_SCRIPTED_ENGINE_THREE_ROUND_ATTESTATION"
            or proof.get("build", {}).get("version") != GAME_VERSION
            or proof.get("build", {}).get("build_id") != "25652598"
            or proof.get("build", {}).get("executable_sha256") != "94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6"
            or proof.get("hard_failure_markers") != [] or proof.get("cold_payload_unchanged") is not True):
        raise ValueError("Permanent R0002 primitive proof does not match the bounded build")
    counts = {"LYD_NP_INITIALIZE_PASS": 1, "LYD_NP_JOIN_APPLIED": 3, "LYD_NP_DETACH_APPLIED": 3,
              "LYD_NP_JOIN_D1_PASS": 3, "LYD_NP_JOIN_D30_PASS": 3,
              "LYD_NP_DETACH_D1_PASS": 3, "LYD_NP_DETACH_D30_PASS": 3, "LYD_NP_THREE_ROUNDS_PASS": 1}
    markers = refs["markers"]["path"].read_text(encoding="utf-8-sig")
    for marker, total in counts.items():
        if (proof.get("count_checks", {}).get(marker) != {"expected": total, "actual": total, "match": True}
                or len(re.findall(r"\b" + marker + r"\b", markers)) != total):
            raise ValueError(f"Permanent primitive marker count mismatch: {marker}")
    fixture = {item["relative_path"]: item["sha256"]
               for item in proof["source_payloads"] if item["product"] == "fixture"}
    for role, name in (("probe_effects", "common/scripted_effects/lyd_np_effects.txt"),
                       ("probe_triggers", "common/scripted_triggers/lyd_np_triggers.txt")):
        if refs[role]["sha256"] != fixture.get(name):
            raise ValueError("Permanent loaded primitive source mismatch")
    if (graph.get("schema") != "ck3.lyd.final-three-rounds-concrete-save-summary.v1"
            or graph.get("status") != "SAVED_OBJECT_GRAPH_VERIFIED"
            or graph.get("artifact", {}).get("sha256") != record.get("original_save_sha256")
            or graph.get("projection_sha256") != record.get("original_projection_sha256")
            or graph.get("metadata", {}).get("version") != GAME_VERSION
            or str(graph.get("branch", {}).get("faith")) != "108"
            or not graph.get("checks") or not all(value is True for value in graph["checks"].values())):
        raise ValueError("Permanent saved graph proof does not match original bound artifact")
    return {"admitted": True, "status": "R0002_PRIMITIVES_PERMANENT_TRACKED_PROOF_BOUND",
            "receipt": str(path), "receipt_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "evidence_refs": [{"path": item["relative"], "sha256": item["sha256"]} for item in refs.values()],
            "consent_flow_live": "NOT_RUN", "shared_narrow_head_factory_live": "NOT_RUN",
            "zero_error_acceptance": proof["overall_zero_error_acceptance"],
            "revalidation_level": "TRACKED_REPORT_AND_EXCERPTS_ONLY",
            "raw_save_rehashed_this_run": False,
            "boundary": "Original bound artifact/projection hashes are preserved facts; no new raw-save or native execution claim."}
