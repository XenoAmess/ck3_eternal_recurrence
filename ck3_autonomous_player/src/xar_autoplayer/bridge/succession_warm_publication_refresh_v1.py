"""Discard a restored derived projection only after a real fresh warm root.

SDK publication revisions are local to that SDK instance. This does not compare
estates across those domains, re-sign old facts, query, or authorize an action.
The original same-domain invalidation guard remains authoritative otherwise.
"""
from __future__ import annotations

from copy import deepcopy

from .succession_transition_contract import (
    freeze_succession_expectation_v1, normalize_succession_expectation_v1,
)
from .turn_bundle_contract import build_turn_bundle_v1


def same_pid_hot_publication_refresh_v1(
    state, *, snapshot, campaign_root_result, restore_kind,
):
    """Return a detached clear decision for an explicitly restored SDK epoch.

    The Driver must supply its original restore kind, own the exact state/frame
    lock, and call only after its actual new root completed all original checks.
    ``None`` delegates to the unchanged original invalidation guard. Current
    complete root material is validated but is not retained by this function.
    """
    if restore_kind != "same_pid_hot" or not isinstance(state, dict):
        return None
    retained = state.get("expectation")
    if retained is None:
        return None
    previous = normalize_succession_expectation_v1(retained)
    if not isinstance(snapshot, dict):
        raise ValueError("warm estate refresh lacks the current snapshot")
    revision = snapshot.get("revision")
    if type(revision) is not int or revision < 0:
        raise ValueError("warm estate refresh lacks a publication revision")
    if previous["binding"]["revision"] <= revision:
        return None
    played = snapshot.get("played_character")
    if (snapshot.get("paused") is not True or snapshot.get("map_ready") is not True
            or snapshot.get("one_life_terminal") is not False
            or snapshot.get("one_life_terminal_reason") is not None
            or not isinstance(played, dict) or played.get("alive") is not True):
        raise ValueError("warm estate refresh requires the current living paused map")
    binding = previous["binding"]
    if (previous["predecessor_character_id"] != played.get("character_id")
            or binding["episode_character_id"] != snapshot.get("episode_character_id")
            or played.get("character_id") != snapshot.get("episode_character_id")
            or binding["episode_run_id"] != snapshot.get("episode_run_id")):
        raise ValueError("warm estate refresh crossed its actor or episode")
    if any(type(snapshot.get(key)) is not int or binding[key] > snapshot[key]
           for key in ("date_raw", "native_revision")):
        raise ValueError("warm estate refresh crossed its native or date sequence")
    root = campaign_root_result.get("campaign_root_context", {}) if isinstance(campaign_root_result, dict) else {}
    if (not isinstance(root, dict) or root.get("status") != "available"
            or not isinstance(root.get("readiness"), dict)
            or root["readiness"].get("held_title_partition_ready") is not True):
        raise ValueError("warm estate refresh requires the original complete estate")
    bundle = build_turn_bundle_v1(snapshot, campaign_root_result)
    observed = freeze_succession_expectation_v1(
        bundle, episode_run_id=snapshot["episode_run_id"],
        episode_character_id=snapshot["episode_character_id"],
    )
    detached = deepcopy(state)
    detached.update(expectation=None, reconciliation=None)
    return {
        "schema": "xar.ck3.succession-estate-invalidation/v1",
        "status": "source_epoch_refresh_required", "invalidated": True,
        "refresh_required": True, "state": detached,
        "previous_source_binding": deepcopy(binding),
        "source_binding": deepcopy(observed["binding"]),
        "source_query_sequence": campaign_root_result["query_sequence"],
        "changed_fields": ["sdk_publication_revision_domain"],
        "estate_change_inferred": False, "queries_performed": 0,
        "submission_authorized": False,
    }
