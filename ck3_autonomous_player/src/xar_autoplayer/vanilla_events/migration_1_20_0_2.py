"""Consume reviewed 1.20 source deltas without relabelling legacy live evidence."""

from copy import deepcopy
from functools import lru_cache
from importlib import resources
import json
from typing import Mapping

from .builds import CURRENT_CK3_BUILD, CURRENT_CK3_EXE_SHA256


@lru_cache(maxsize=1)
def load_compatibility() -> dict[str, object]:
    resource = resources.files(__package__).joinpath("data/source_compatibility_1_20_0_2.json")
    return json.loads(resource.read_text(encoding="utf-8"))


def _replace_reviewed_hashes(value: object, replacements: Mapping[str, str]) -> object:
    if isinstance(value, dict):
        return {key: _replace_reviewed_hashes(item, replacements) for key, item in value.items()}
    if isinstance(value, list):
        return [_replace_reviewed_hashes(item, replacements) for item in value]
    if isinstance(value, tuple):
        return tuple(_replace_reviewed_hashes(item, replacements) for item in value)
    if isinstance(value, str):
        return replacements.get(value, value)
    return value


def migrate_event_knowledge(
    event_key: str, *, contract: Mapping[str, object],
    analysis: Mapping[str, object] | None, observations: Mapping[str, object] | None,
) -> dict[str, object]:
    row = load_compatibility()["events"].get(event_key)
    if not isinstance(row, dict):
        return {"status": "unavailable", "unavailable_reason": "event_migration_not_reviewed"}
    if row.get("status") == "owner-deferred":
        return {"status": "unavailable", "unavailable_reason": "event_domain_owner_deferred"}
    compatible = (
        row.get("status") == "unchanged"
        or row.get("policy_contract_compatible") is True
        or row.get("policy_reuse_eligible_by_manual_review") is True
        or (
            isinstance(row.get("manual_review"), dict)
            and row["manual_review"].get("policy_reuse_eligible_by_manual_review") is True
        )
    )
    if not compatible:
        return {"status": "unavailable", "unavailable_reason": "event_source_migration_pending"}

    legacy = deepcopy(dict(analysis or {}))
    definition = row["new_definition"]
    legacy_sources = legacy.get("source_sha256", {})
    current_sources = row.get("source_file_sha256", {})
    updated = deepcopy(legacy)
    updated["exact_build"] = {
        "game_version": CURRENT_CK3_BUILD,
        "ck3_executable_sha256": CURRENT_CK3_EXE_SHA256,
        "steam_build_id": 25588574,
    }
    updated["source_sha256"] = {
        **current_sources,
        definition["relative_path"]: definition["file_sha256"],
    }
    updated["definition_lines"] = f"{definition['line']}-{definition['end_line']}"
    updated["migration_1_20_0_2"] = {
        "policy_contract_compatible": True,
        "legacy_build": "1.19.0.6",
        "legacy_source_sha256": legacy_sources,
        "definition_review": deepcopy(row),
        "runtime_call_chain_revalidated": False,
        "readiness": "static-ready",
        "new_live_evidence": False,
        "boundary": "source compatibility and bounded policy replay; legacy exemplars are not 1.20 live evidence",
    }
    # The current displayed-option review does not re-prove an old caller's
    # line numbers, natural cadence or hidden trigger description.
    for key in tuple(updated):
        if key == "source_sha256" or key == "definition_lines":
            continue
        if key.endswith("_lines") or any(token in key for token in (
            "caller", "frequency", "trigger_boundary", "story_entry", "repeatability",
        )):
            updated["migration_1_20_0_2"][f"legacy_{key}"] = updated.pop(key)
    # Legacy source anchors and forecasts are not silently promoted when the
    # new stress/fulfillment or called-value chain has changed. The generator's
    # narrow review identifies the profiles which can be carried forward.
    reviewed_profiles = row.get("reviewed_profile_keys", [])
    replacements = {
        digest: current_sources[path]
        for path, digest in legacy_sources.items() if path in current_sources
    } if isinstance(legacy_sources, Mapping) else {}
    for key in ("selected_choice_effect_profile", "selected_choice_campaign_utility_profile"):
        if key in updated:
            if key in reviewed_profiles:
                updated[key] = _replace_reviewed_hashes(updated[key], replacements)
                updated[key]["migration_source_review"] = "reviewed static 1.20 dependency delta; no new live outcome"
            else:
                updated["migration_1_20_0_2"][f"legacy_{key}"] = updated.pop(key)
    notice = updated.get("source_reviewed_effectless_notice")
    if isinstance(notice, dict):
        notice["definition_path"] = definition["relative_path"]
        notice["definition_sha256"] = definition["file_sha256"]
        notice["source_lines"] = updated["definition_lines"]
    if isinstance(row.get("analysis_updates"), dict):
        updated.update(deepcopy(row["analysis_updates"]))
    current_contract = deepcopy(dict(contract))
    if isinstance(row.get("timeline_contract_updates"), dict):
        current_contract.update(deepcopy(row["timeline_contract_updates"]))
    return {
        "status": "available", "contract": current_contract, "analysis": updated,
        "observations": {
            "legacy_build": "1.19.0.6", "new_live_evidence": False,
            "legacy_observations": deepcopy(observations),
        } if observations else None,
        "unavailable_reason": None,
    }


def current_migrated_catalogs() -> tuple[dict, dict, dict]:
    from . import DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS
    from .registry import query_vanilla_event_knowledge_v1

    contracts, analysis, observations = {}, {}, {}
    for key in DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS:
        knowledge = query_vanilla_event_knowledge_v1(key, CURRENT_CK3_BUILD)
        if knowledge["status"] == "available":
            contracts[key] = knowledge["contract"]
            analysis[key] = knowledge["analysis"]
            # Current-build discovery counts current live observations only.
    return contracts, analysis, observations
