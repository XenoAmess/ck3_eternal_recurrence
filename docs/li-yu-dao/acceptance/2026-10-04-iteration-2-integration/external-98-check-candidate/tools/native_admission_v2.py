"""Validate exact R0002 primitive/save bindings; never manufacture live signoff."""

import hashlib
import json
from pathlib import Path

from school_consent_data import BASELINE_COMMIT, GAME_VERSION

BINDING_SCHEMA = "lyd.native-primitive-admitted-projection-binding.v1"


def validate_binding(path: Path, record: dict) -> dict:
    if record.get("scope") != "native-primitives-only" or record.get("baseline_commit") != BASELINE_COMMIT:
        raise ValueError("Admission binding scope/baseline mismatch")
    if record.get("authorized_by") != "/root" or record.get("prepared_by") != "/root/confucian_history_plan":
        raise ValueError("Missing delegated primitive-only projection authorization")
    if set(record.get("primitives", ())) != {"set_parent_faith", "detach_rite_to_new_faith"}:
        raise ValueError("Both native primitives require binding")
    refs = {}
    for item in record.get("evidence_refs", []):
        reference = Path(item["path"])
        if not reference.is_absolute():
            reference = path.parent / reference
        reference = reference.resolve()
        digest = hashlib.sha256(reference.read_bytes()).hexdigest()
        if digest != item["sha256"]:
            raise ValueError(f"Native evidence hash mismatch: {reference}")
        if item["role"] in refs:
            raise ValueError("Duplicate native evidence role")
        refs[item["role"]] = {"path": str(reference), "sha256": digest}
    required = {"native_attestation_v2", "saved_graph_summary", "saved_artifact", "saved_projection",
                "native_probe_effects", "native_probe_triggers", "native_title_factory_source"}
    if not required <= refs.keys():
        raise ValueError("Primitive binding lacks required artifacts")
    proof = json.loads(Path(refs["native_attestation_v2"]["path"]).read_text(encoding="utf-8-sig"))
    if (proof.get("schema") != "lyd.native-primitive-three-rounds-attestation-candidate.v2"
            or proof.get("primitive_verdict") != "ACCEPTED_SCRIPTED_ENGINE_THREE_ROUND_ATTESTATION"
            or proof.get("build", {}).get("version") != GAME_VERSION
            or proof.get("build", {}).get("build_id") != "25652598"
            or proof.get("build", {}).get("executable_sha256") != "94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6"
            or proof.get("hard_failure_markers") != [] or proof.get("cold_payload_unchanged") is not True):
        raise ValueError("R0002 does not establish required bounded primitive evidence")
    expected_counts = {"LYD_NP_INITIALIZE_PASS": 1, "LYD_NP_JOIN_APPLIED": 3, "LYD_NP_DETACH_APPLIED": 3,
                       "LYD_NP_JOIN_D1_PASS": 3, "LYD_NP_JOIN_D30_PASS": 3,
                       "LYD_NP_DETACH_D1_PASS": 3, "LYD_NP_DETACH_D30_PASS": 3, "LYD_NP_THREE_ROUNDS_PASS": 1}
    for marker, total in expected_counts.items():
        check = proof.get("count_checks", {}).get(marker, {})
        if check != {"expected": total, "actual": total, "match": True}:
            raise ValueError(f"Primitive marker counts differ: {marker}")
    for frozen in proof.get("frozen_files", {}).values():
        digest = hashlib.sha256(Path(frozen["frozen_path"]).read_bytes()).hexdigest()
        if digest != frozen["sha256"]:
            raise ValueError("Frozen primitive log/report hash mismatch")
    fixture_hashes = {item["relative_path"]: item["sha256"] for item in proof["source_payloads"] if item["product"] == "fixture"}
    for role, relative in (("native_probe_effects", "common/scripted_effects/lyd_np_effects.txt"),
                           ("native_probe_triggers", "common/scripted_triggers/lyd_np_triggers.txt")):
        if fixture_hashes.get(relative) != refs[role]["sha256"]:
            raise ValueError("Loaded primitive source differs from bound source")
    graph = json.loads(Path(refs["saved_graph_summary"]["path"]).read_text(encoding="utf-8-sig"))
    if graph.get("schema") != "ck3.lyd.final-three-rounds-concrete-save-summary.v1" or graph.get("status") != "SAVED_OBJECT_GRAPH_VERIFIED":
        raise ValueError("Saved graph is not verified")
    if graph.get("artifact", {}).get("sha256") != refs["saved_artifact"]["sha256"] or graph.get("projection_sha256") != refs["saved_projection"]["sha256"]:
        raise ValueError("Saved graph does not bind the actual checkpoint/projection")
    if not graph.get("checks") or not all(value is True for value in graph["checks"].values()):
        raise ValueError("Saved graph has failed checks")
    if str(graph.get("branch", {}).get("faith")) != "108" or graph.get("metadata", {}).get("version") != GAME_VERSION:
        raise ValueError("Unexpected terminal graph")
    return {"admitted": True, "status": "R0002_PRIMITIVES_ATTESTED_AND_SAVED_GRAPH_BOUND",
            "receipt": str(path), "receipt_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "evidence_refs": list(refs.values()), "consent_flow_live": "NOT_RUN",
            "shared_narrow_head_factory_live": "NOT_RUN",
            "zero_error_acceptance": proof.get("overall_zero_error_acceptance"),
            "not_admitted": ["authority/consent event graph", "natural cooldown expiry", "save/reload",
                             "main/last direct detach", "shared narrowed factory", "all doctrine/head combinations"]}
