"""Freeze reviewed holy-site value JSON as portable runtime constants."""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from pprint import pformat
import re


ROOT = Path(__file__).resolve().parents[1]
ADOPTION = "docs/ck3-native-ai/faith-and-power-adoption-value-12004.knowledge-payload.json"
SHARED = "docs/ck3-native-ai/evidence/holy-site-shared-relic-value12004/planning-supplement.json"
TARGET = "ck3_autonomous_player/src/xar_autoplayer/holy_site_decision_value_knowledge.py"
BUILD = "1.20.0.4"


def load(relative: str) -> dict:
    data = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected object: {relative}")
    return data


def reference(relative: str) -> dict:
    return {"ref": relative, "sha256": hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()}


def repository_path(value: str) -> str | None:
    value = value.replace("\\", "/")
    if value.startswith("docs/"):
        return value
    if "/docs/" in value:
        return "docs/" + value.split("/docs/", 1)[1]
    return None


def adoption_sources(payload: dict) -> tuple[dict, dict]:
    manifest_path = str(Path(ADOPTION).parent / payload["integration"]["source_manifest"]).replace("\\", "/")
    manifest = load(manifest_path)
    refs = {}
    for row in manifest["static_sources"]:
        refs[row["id"]] = {
            "id": row["id"], "game_relative_path": row["path"], "sha256": row["sha256"],
            "line_ranges": row["lines"], "source_kind": row["origin"],
            "machine_id": row["machine_id"], "observed_utc": row["read_back_at_utc"],
        }
    for index, row in enumerate(manifest["historical_sources"]):
        relative = repository_path(row["path"])
        ref = reference(relative) if relative else {**reference(manifest_path), "json_pointer": f"/historical_sources/{index}"}
        refs[row["id"]] = {"id": row["id"], **ref, "source_kind": "scoped_historical_native_observation",
                            "machine_id": row["machine_id"], "historical_receipt_sha256": row["sha256"]}
    row = manifest["native_consumer_review"]
    refs[row["id"]] = {"id": row["id"], **reference(row["repository_path_owned_by_faith_research"]),
                       "source_kind": "exact_build_native_static", "machine_id": row["machine_id"],
                       "observed_utc": row["observed_utc"], "original_external_sha256": row["sha256"],
                       "rvas": row["rvas"], "actual_live_attribute_observation": False}
    return refs, reference(manifest_path)


def enrich_sources(value, refs: dict):
    """Retain author IDs and attach resolvable provenance to source-bearing specs."""
    if isinstance(value, list):
        return [enrich_sources(item, refs) for item in value]
    if not isinstance(value, dict):
        return value
    result = {key: enrich_sources(item, refs) for key, item in value.items()}
    labels = value.get("sources", [])
    if isinstance(value.get("source"), str):
        labels = [*labels, value["source"]] if isinstance(labels, list) else [value["source"]]
    resolved = []
    for label in labels if isinstance(labels, list) else []:
        if not isinstance(label, str):
            continue
        match = re.fullmatch(r"([A-Z]+\d+)(?::(\d+)-(\d+))?", label)
        if match is None:
            continue
        if match[1] not in refs:
            raise ValueError(f"Unresolved source ID: {label}")
        ref = deepcopy(refs[match[1]])
        if match[2]:
            ref["selected_lines"] = [int(match[2]), int(match[3])]
        resolved.append(ref)
    if resolved:
        result["source_refs"] = resolved
    return result


def render() -> str:
    adoption, shared = load(ADOPTION), load(SHARED)
    if adoption["game_version"] != BUILD or shared["supported_build"] != BUILD:
        raise ValueError("Revalidate exact-build value inputs before generation")
    if adoption["state_observed"] is not False or adoption["native_legality"] is not None or adoption["action_ready"] is not False:
        raise ValueError("Value inputs must not grant current state, native legality or readiness")
    refs, manifest = adoption_sources(adoption)
    decision = {"qualification": "source_reviewed_static", "supported_build": BUILD,
                "state_observed": False, "native_legality": None, "action_ready": False,
                "source_payload": reference(ADOPTION), "source_manifest": manifest,
                "source_refs": refs, "shared": enrich_sources(adoption["shared"], refs),
                "actions": enrich_sources(adoption["actions"], refs),
                "historical_cases_are_not_current_state": True, "production_or_whole_product_pass": False}
    root = deepcopy(shared["shared_relic_value"])
    root["source_refs"] = {key: reference(relative) for key, relative in root["source_refs"].items()}
    root["state_model"]["source_refs"] = [root["source_refs"][key] for key in ("native", "recognition_and_cache", "actual_consumer")]
    actions = deepcopy(shared["actions"])
    for spec in actions.values():
        spec["source_refs"] = [root["source_refs"][key] for key in ("scripts", "native", "actual_consumer", "recognition_and_cache")]
    relic = {"qualification": "source_reviewed_static", "supported_build": BUILD,
             "state_observed": False, "native_legality": None, "action_ready": False,
             "source_payload": reference(SHARED), "shared": root, "actions": actions,
             "source_kind": shared["source_kind"], "new_policy_or_gate": False,
             "new_action_tool": False, "new_live_qualification": False}
    if re.search(r"[A-Za-z]:[\\/]", json.dumps([decision, relic])):
        raise ValueError("Generated constants must not depend on machine-absolute paths")
    return (
        '# GENERATED FILE: run py tools/gen_holy_site_value_knowledge.py; do not edit.\n'
        '"""Portable reviewed value inputs; no documentation or local-path runtime reads."""\n\n'
        'HOLY_SITE_DECISION_VALUE_KNOWLEDGE = ' + pformat(decision, width=100, sort_dicts=False) + '\n\n'
        'HOLY_SITE_SHARED_RELIC_VALUE_KNOWLEDGE = ' + pformat(relic, width=100, sort_dicts=False) + '\n'
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Check generated bytes without writing")
    args = parser.parse_args()
    rendered = render().encode("utf-8")
    target = ROOT / TARGET
    if args.check:
        if not target.exists() or target.read_bytes() != rendered:
            parser.exit(1, "Holy-site value constants need regeneration\n")
        print("Holy-site value constants match reviewed inputs")
    else:
        target.write_bytes(rendered)
        print(f"Generated {TARGET} ({len(rendered)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
