"""Consume UI observations after the owner's complete natural handoff proof.

No queries or actions live here. In particular an event is not permission to
Close or SAVE, and a disappeared event is not an independently cleared modal.
"""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
import hashlib
import json

from ..strategy import normalize_ordinary_campaign_goal_v1
from .succession_ui_observation_v1 import project_successor_ui_observation_v1

SCHEMA = "xar.ck3.verified-successor-ui-service/v1"
FRAME = ("bridge_pid", "connection_generation", "snapshot_id", "revision", "native_revision", "date_raw")
PROOF = ("status", "predecessor_character_id", "successor_character_id", "source_episode_run_id",
         "episode_run_id", "same_campaign_frame", "ck3_command_submitted", "process_restarted",
         "succession_lifecycle", "reconciliation", "predecessor_binding", "successor_episode_binding")


def observe_verified_successor_ui_v1(*, transition, snapshot, timeline_query,
                                    previous_observation=None, event_context=None):
    """Require the original full verifier's proof; retain every native predicate.

The caller must already have passed its original full transition, goal and
driver-persistence gates. This function cannot manufacture that certificate or
replace those gates. A previous observation permits only a later frame of the
same certified successor, never another Continue or a different generation.
"""
    if not isinstance(transition, Mapping) or not isinstance(snapshot, Mapping):
        raise ValueError("successor UI requires a verified transition and snapshot")
    reconciliation = transition.get("reconciliation")
    binding = transition.get("successor_episode_binding")
    lifecycle = transition.get("succession_lifecycle")
    if (transition.get("status") != "verified" or transition.get("same_campaign_frame") is not True
            or transition.get("ck3_command_submitted") is not False
            or transition.get("process_restarted") is not False
            or not isinstance(lifecycle, Mapping)
            or lifecycle.get("lifecycle") != "ordinary_campaign_succession"
            or not isinstance(binding, Mapping) or not isinstance(reconciliation, Mapping)
            or reconciliation.get("status") != "available" or reconciliation.get("verdict") != "matched"
            or reconciliation.get("successor_match") is not True
            or reconciliation.get("title_distribution_match") is not True
            or reconciliation.get("predecessor_character_id") != transition.get("predecessor_character_id")
            or reconciliation.get("actual_successor_character_id") != transition.get("successor_character_id")):
        raise ValueError("successor UI cannot replace the original full handoff verification")
    proof = {key: deepcopy(transition.get(key)) for key in PROOF}
    digest = hashlib.sha256(json.dumps(proof, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    diagnostics = snapshot.get("diagnostics")
    if not isinstance(diagnostics, Mapping):
        raise ValueError("successor UI lacks its process binding")
    current = {key: snapshot.get(key) for key in FRAME}
    current.update({key: diagnostics.get(key) for key in FRAME[:2]})
    if (snapshot.get("episode_character_id") != transition.get("successor_character_id")
            or snapshot.get("episode_run_id") != transition.get("episode_run_id")):
        raise ValueError("successor UI changed the verified episode")
    if previous_observation is None:
        if any(current[key] != binding.get(key) for key in FRAME):
            raise ValueError("successor UI left the original six-field handoff frame")
    else:
        if (not isinstance(previous_observation, Mapping)
                or previous_observation.get("schema") != SCHEMA
                or previous_observation.get("verified_transition_sha256") != digest
                or previous_observation.get("fresh_timeline_read_after_event_required") is not True):
            raise ValueError("successor UI has no retained event recheck obligation")
        old = previous_observation.get("frame")
        if (not isinstance(old, Mapping) or any(current[key] != old.get(key) for key in FRAME[:2])
                or any(type(current[key]) is not int or type(old.get(key)) is not int
                       or current[key] < old[key]
                       for key in ("revision", "native_revision", "date_raw"))):
            raise ValueError("successor UI recheck changed process or regressed its frame")
    goal = normalize_ordinary_campaign_goal_v1(snapshot.get("campaign_goal"))
    if goal["current_character_id"] != transition["successor_character_id"]:
        raise ValueError("successor UI goal is not bound to the verified successor")
    if previous_observation is not None and goal != previous_observation.get("campaign_goal"):
        raise ValueError("successor UI recheck changed the retained campaign intent")
    if (not isinstance(timeline_query, Mapping) or timeline_query.get("accepted") is not True
            or timeline_query.get("private_build") is not True or timeline_query.get("read_only") is not True
            or timeline_query.get("advertised") is not False
            or type(timeline_query.get("query_sequence")) is not int or timeline_query["query_sequence"] <= 0
            or any(timeline_query.get(query) != current[field] for query, field in (
                ("queried_snapshot_id", "snapshot_id"), ("queried_revision", "revision"),
                ("queried_native_revision", "native_revision"), ("snapshot_revision", "native_revision"),
                ("date_raw", "date_raw")))):
        raise ValueError("successor UI timeline lacks the original guarded Service read")
    projection = project_successor_ui_observation_v1(snapshot,
        timeline_context=timeline_query.get("current_timeline_blocker_context"), event_context=event_context)
    return {**projection, "schema": SCHEMA, "verified_transition_sha256": digest,
            "campaign_goal": goal, "initial_handoff_frame": deepcopy(dict(binding)),
            "checkpoint_deferred": projection["ui_clearance"] != "clear",
            "event_disappearance_is_clearance": False, "continue_replay_authorized": False,
            "close_replay_authorized": False}
