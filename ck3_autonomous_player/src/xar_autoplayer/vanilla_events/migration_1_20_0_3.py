"""Apply the reviewed patch source delta after the historical 1.20 migration."""

from copy import deepcopy
from functools import lru_cache
from importlib import resources
import json
from typing import Mapping

from .builds import SUPPORTED_CK3_EXE_SHA256
from .migration_1_20_0_2 import (
    _replace_reviewed_hashes, migrate_event_knowledge as migrate_previous,
)


@lru_cache(maxsize=1)
def load_compatibility() -> dict[str, object]:
    resource = resources.files(__package__).joinpath("data/source_compatibility_1_20_0_3.json")
    return json.loads(resource.read_text(encoding="utf-8"))


def migrate_event_knowledge(
    event_key: str, *, contract: Mapping[str, object],
    analysis: Mapping[str, object] | None, observations: Mapping[str, object] | None,
) -> dict[str, object]:
    previous = migrate_previous(
        event_key, contract=contract, analysis=analysis, observations=observations,
    )
    if previous["status"] != "available":
        return previous
    row = load_compatibility()["events"].get(event_key)
    if not isinstance(row, dict):
        return {"status": "unavailable", "unavailable_reason": "event_migration_not_reviewed"}
    if row.get("status") == "owner-deferred":
        # Historical aliases never impose the revoked religion restriction.
        # The war package exclusion remains a separate execution boundary.
        reason = ("event_domain_outside_nonwar_work_package"
                  if row.get("reason") == "war-domain-outside-nonwar-work-package"
                  else "event_source_migration_pending")
        return {"status": "unavailable", "unavailable_reason": reason}
    if row.get("status") != "unchanged":
        return {"status": "unavailable", "unavailable_reason": "event_source_migration_pending"}
    updated = deepcopy(previous["analysis"])
    prior_sources = updated.get("source_sha256", {})
    definition = row["new_definition"]
    sources = {**row.get("source_file_sha256", {}), definition["relative_path"]: definition["file_sha256"]}
    updated["exact_build"] = {
        "game_version": "1.20.0.3",
        "ck3_executable_sha256": SUPPORTED_CK3_EXE_SHA256["1.20.0.3"],
        "steam_build_id": 25652598,
    }
    updated["source_sha256"] = sources
    updated["definition_lines"] = f"{definition['line']}-{definition['end_line']}"
    # Patch reviews can publish a current profile after the earlier migration
    # deliberately retained its historical form under legacy_*.
    if isinstance(row.get("analysis_updates"), dict):
        updated.update(deepcopy(row["analysis_updates"]))
    replacements = {digest: sources[path] for path, digest in prior_sources.items() if path in sources}
    for key in ("selected_choice_effect_profile", "selected_choice_campaign_utility_profile"):
        if key in updated and key in row.get("reviewed_profile_keys", []):
            updated[key] = _replace_reviewed_hashes(updated[key], replacements)
            updated[key]["migration_source_review"] = "reviewed static 1.20.0.3 dependency delta; no new live outcome"
    updated["migration_1_20_0_3"] = {
        "previous_build": "1.20.0.2", "previous_source_sha256": prior_sources,
        "definition_review": deepcopy(row), "readiness": "static-ready",
        "runtime_call_chain_revalidated": False, "new_live_evidence": False,
        "boundary": "unchanged patch source and narrowly reviewed dependency; inherited exemplars remain historical",
    }
    return {**previous, "analysis": updated}
