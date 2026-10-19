"""Pure invalidation from an already completed, current complete root read.

The caller owns the Driver lock, identity checks and durable persistence. This
module does not query, mutate a Driver, retain a new prediction or authorize a
game action. Same published revision is deliberately not an estate epoch.
"""
from __future__ import annotations

from copy import deepcopy

from .succession_transition_contract import (
    freeze_succession_expectation_v1, normalize_succession_expectation_v1,
)
from .turn_bundle_contract import build_turn_bundle_v1


def _shape(expectation):
    return {"primary_title_id": next(row["title"]["title_id"] for row in expectation["title_expectations"] if row["primary"]),
            "expected_successor_character_id": expectation["expected_successor_character_id"],
            "title_expectations": expectation["title_expectations"]}


def invalidate_succession_state_from_root_v1(state, *, snapshot, campaign_root_result):
    """Return a detached state with both derived fields cleared only on change.

    ``campaign_root_result`` is the completed Service-normalized root envelope,
    including its original complete binding and query_sequence. Rejected,
    partial-estate, terminal and mixed actor/episode sources never clear state.
    Apply only if the caller still holds the exact input state/frame under its
    original lock; the returned decision is not a cross-process CAS authority.
    """
    if not isinstance(state, dict):
        raise ValueError("succession state must be an object")
    retained = state.get("expectation")
    output = {"schema": "xar.ck3.succession-estate-invalidation/v1", "status": "not_applicable",
              "invalidated": False, "refresh_required": False, "state": deepcopy(state),
              "source_binding": None, "source_query_sequence": None, "changed_fields": [],
              "queries_performed": 0, "submission_authorized": False}
    if retained is None:
        return output
    if not isinstance(snapshot, dict):
        raise ValueError("current estate snapshot is missing")
    played = snapshot.get("played_character")
    if (snapshot.get("paused") is not True or snapshot.get("map_ready") is not True
            or snapshot.get("one_life_terminal") is not False
            or snapshot.get("one_life_terminal_reason") is not None
            or not isinstance(played, dict) or played.get("alive") is not True
            or played.get("character_id") != snapshot.get("episode_character_id")):
        raise ValueError("estate invalidation requires the current living paused episode")
    previous = normalize_succession_expectation_v1(retained)
    if (previous["predecessor_character_id"] != played["character_id"]
            or previous["binding"]["episode_run_id"] != snapshot.get("episode_run_id")
            or any(previous["binding"][key] > snapshot.get(key, -1)
                   for key in ("date_raw", "revision", "native_revision"))):
        raise ValueError("retained estate differs from the current actor/episode sequence")
    bundle = build_turn_bundle_v1(snapshot, campaign_root_result)
    observed = freeze_succession_expectation_v1(bundle,
        episode_run_id=snapshot["episode_run_id"], episode_character_id=snapshot["episode_character_id"])
    old, new = _shape(previous), _shape(observed)
    changed = [key for key in old if old[key] != new[key]]
    output.update(status="unchanged" if not changed else "invalidated",
        source_binding=deepcopy(observed["binding"]),
        source_query_sequence=campaign_root_result["query_sequence"], changed_fields=changed)
    if changed:
        output["state"].update(expectation=None, reconciliation=None)
        output.update(invalidated=True, refresh_required=True)
    return output
