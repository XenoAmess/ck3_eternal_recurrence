"""Reuse authored .3 event sources under the actual identical .4 data depot.

Executable identity changes independently of script bytes. Prior observations
remain historical and this adapter grants no new native or live qualification.
"""

from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
from importlib import resources
import json
from typing import Mapping


@lru_cache(maxsize=1)
def _compatibility() -> dict[str, object]:
    resource = resources.files(__package__).joinpath(
        "data/source_compatibility_1_20_0_4.json"
    )
    return json.loads(resource.read_text(encoding="utf-8"))


def source_reuse_metadata() -> dict[str, object]:
    """Return detached provenance for the published authored source projection."""
    proof = _compatibility()
    return deepcopy({name: proof[name] for name in (
        "previous_build", "previous_dataset_sha256", "data_depot", "evidence",
        "fresh_source_scan", "runtime_call_chain_revalidated", "new_live_evidence",
    )})


def migrate_event_knowledge(
    event_key: str, *, previous_knowledge: Mapping[str, object],
) -> dict[str, object]:
    """Adapt the genuine public .3 selection, including its current overrides."""
    proof = _compatibility()
    result = deepcopy(dict(previous_knowledge))
    previous_analysis = result.get("analysis")
    analysis = previous_analysis if isinstance(previous_analysis, dict) else {}
    ledger = source_reuse_metadata()
    ledger.update({
        "previous_exact_build": deepcopy(analysis.get("exact_build")),
        "previous_source_sha256": deepcopy(analysis.get("source_sha256")),
        "previous_unavailable_reason": result.get("unavailable_reason"),
        "readiness": "static-ready",
    })
    analysis["migration_1_20_0_4"] = ledger
    analysis["exact_build"] = {
        "game_version": proof["ck3_build"],
        "ck3_executable_sha256": proof["ck3_exe_sha256"],
        "steam_build_id": proof["steam_build_id"],
    }
    result.update(event_definition_key=event_key, ck3_build=proof["ck3_build"],
        ck3_exe_sha256=proof["ck3_exe_sha256"], analysis=analysis)
    previous_observations = result.get("observations")
    if previous_observations is not None:
        result["observations"] = {
            "legacy_build": proof["previous_build"],
            "new_live_evidence": False,
            "legacy_observations": previous_observations,
        }
    if result.get("unavailable_reason") == "event_domain_outside_nonwar_work_package":
        # Authorization was expanded after this historical source package.
        # Retain its old reason in the ledger without restoring its restriction.
        result["unavailable_reason"] = "event_source_migration_pending"
    return result
