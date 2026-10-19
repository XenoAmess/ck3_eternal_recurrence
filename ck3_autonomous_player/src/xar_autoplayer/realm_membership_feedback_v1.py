"""Consume an already completed faction query; never request or recover data.

The 2026-10-19 source addition retains the native actor+vassal county set in
the existing two-sample query. This is prospective source, not Native26/27
adoption or a current-game observation. Frozen monthly records stay unchanged.
The caller owns low-frequency retention and normal planner handoff. An older
query cannot be moved to an after-action MET, even if its calendar date agrees.
"""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy

from .bridge.driver import BridgeUnavailableError
from .bridge.nonwar_private_build import private_native_build_identity
from .bridge.player_faction_alerts_contract import (
    SUBREALM_COUNTIES_COMPONENT_V1 as COMPONENT,
    SUBREALM_COUNTIES_SCOPE_V1 as SCOPE,
    _subrealm_counties_component,
    normalize_player_faction_alerts_v1,
)
from .campaign_score_existing_inputs_v1 import _frame_reason, _unknown

OBSERVATION_SCHEMA = "xar.ck3.realm-membership-observation/v1"


def _difference(previous, observation):
    unavailable = {"status": "unavailable", "lost_county_title_ids": None,
                   "gained_county_title_ids": None, "unavailable_reason": "previous_complete_observation_missing"}
    if not isinstance(previous, Mapping) or previous.get("schema") != OBSERVATION_SCHEMA:
        return unavailable
    try:
        old, now = previous["source_frame"], observation["source_frame"]
        if (not isinstance(old, Mapping) or old.get("schema") != now["schema"]
                or old.get("status") != "complete"
                or previous["provenance"] != observation["provenance"]):
            raise ValueError("previous_source_scope_unqualified")
        # Cold rebinds and actor changes require their existing owner/M3 proof;
        # this leaf does not infer continuity from dates, titles or top lieges.
        for key in ("actor_character_id", "episode_run_id", "bridge_pid", "connection_generation"):
            if old.get(key) != now[key]:
                raise ValueError("previous_owner_continuity_unqualified:" + key)
        for key in ("native_revision", "revision", "date_raw"):
            if type(old.get(key)) is not int:
                raise ValueError("previous_frame_incomplete")
        if (not isinstance(old.get("snapshot_id"), str) or not old["snapshot_id"]
                or old["native_revision"] < 1 or old["revision"] < 0):
            raise ValueError("previous_frame_incomplete")
        if (old["date_raw"] > now["date_raw"]
                or old["native_revision"] >= now["native_revision"]
                or old["revision"] >= now["revision"]
                or type(previous.get("query_sequence")) is not int
                or previous["query_sequence"] >= observation["query_sequence"]
                or previous["query_sequence"] < 1):
            raise ValueError("previous_source_not_strictly_earlier")
        if previous.get("status") != "available":
            raise ValueError("previous_observation_unavailable")
        before = _subrealm_counties_component(previous["component"],
            actor=old["actor_character_id"], native_revision=old["native_revision"], date_raw=old["date_raw"])
        if before["complete"] is not True:
            raise ValueError("previous_membership_incomplete")
        a, b = set(before["county_title_ids"]), set(observation["component"]["county_title_ids"])
        return {"status": "available", "lost_county_title_ids": sorted(a-b),
                "gained_county_title_ids": sorted(b-a), "unavailable_reason": None,
                "before_source_frame": deepcopy(dict(old)),
                "after_source_frame": deepcopy(dict(now)), "cause": None}
    except (ValueError, TypeError, KeyError) as error:
        return {**unavailable, "unavailable_reason": str(error)[:256]}


def project_realm_membership_feedback_v1(snapshot, *, faction_result=None,
                                        source_frame=None, previous=None):
    """Qualify the current query against the current MET before any set diff.

    Both full county sets must be available. Partial data, an absent optional
    field, previous episode or old AUTO frame stays unknown, never empty/zero.
    Source/closing capture epochs are not invented; this remains a paused bundle.
    """
    result = {"schema": "xar.ck3.realm-membership-feedback/v1", "status": "unavailable",
              "observation": None, "difference": None,
              "raw_metrics": {"realm_county_count": _unknown("realm_county_count", "existing_faction_DTO_not_obtained")},
              "unavailable_reason": "existing_faction_DTO_not_obtained",
              "new_RPC_calls": 0, "new_SAVE_exports": 0,
              "same_native_capture_with_MET": False, "native_capture_epoch": None}
    if faction_result is None:
        return result
    reason = _frame_reason(snapshot, source_frame)
    try:
        if reason is not None:
            raise ValueError(reason)
        if (any(type(source_frame.get(k)) is not int for k in (
                "revision", "native_revision", "date_raw", "actor_character_id"))
                or source_frame["revision"] < 0 or source_frame["actor_character_id"] < 1
                or not isinstance(source_frame.get("snapshot_id"), str) or not source_frame["snapshot_id"]
                or not isinstance(source_frame.get("episode_run_id"), str) or not source_frame["episode_run_id"]):
            raise ValueError("current_source_frame_incomplete")
        if not isinstance(faction_result, Mapping):
            raise ValueError("faction_result_missing")
        binding = faction_result.get("binding")
        if isinstance(binding, Mapping):
            if any(binding.get(k) != source_frame[k] for k in (
                    "snapshot_id", "revision", "native_revision", "date_raw")):
                raise ValueError("faction_result_binding_changed")
            if binding.get("expected_revision") != source_frame["revision"]:
                raise ValueError("faction_result_expected_revision_changed")
        else:
            # Ordinary AUTO returns the existing NativeDriver queried_* DTO;
            # explicit Service/MCP queries add binding. Check the actual shape,
            # never manufacture a binding from a current snapshot.
            if (faction_result.get("step") != "query-player-faction-alerts-v1"
                    or faction_result.get("accepted") is not True
                    or faction_result.get("snapshot_revision") != source_frame["native_revision"]
                    or any(faction_result.get("queried_"+key) != source_frame[key]
                           for key in ("snapshot_id", "revision", "native_revision"))):
                raise ValueError("faction_original_queried_frame_changed")
        sequence = faction_result.get("query_sequence")
        if type(sequence) is not int or sequence < 1:
            raise ValueError("faction_original_query_sequence_unavailable")
        build = private_native_build_identity(snapshot)
        if build is None:
            raise ValueError("current_exact_build_unavailable")
        normalized = normalize_player_faction_alerts_v1(faction_result.get("player_faction_alerts"),
            expected_date_raw=source_frame["date_raw"],
            expected_snapshot_revision=source_frame["native_revision"],
            expected_game_version=build.game_version, expected_executable_sha256=build.executable_sha256)
        if binding is None and (faction_result.get("status") != normalized["status"]
                or faction_result.get("player_faction_alerts_ready") is not normalized["readiness"]["alert_ready"]):
            raise ValueError("faction_original_envelope_disagrees")
        component = normalized.get(COMPONENT)
        if not isinstance(component, dict) or component["complete"] is not True:
            raise ValueError("complete_subrealm_county_component_unavailable")
        if component["actor_character_id"] != source_frame["actor_character_id"]:
            raise ValueError("subrealm_county_owner_changed")
        observation = {"schema": OBSERVATION_SCHEMA, "status": "available", "scope": SCOPE,
            "component": deepcopy(component), "source_frame": deepcopy(dict(source_frame)),
            "query_sequence": sequence, "provenance": deepcopy(normalized["provenance"])}
        return {**result, "status": "available", "observation": observation,
                "difference": _difference(previous, observation), "unavailable_reason": None,
                "raw_metrics": {"realm_county_count": {"value": str(len(component["county_title_ids"])),
                    "unit": "county", "availability": "observed", "scope": SCOPE,
                    "source_ref": "existing_player_faction_alerts", "locator": COMPONENT}}}
    except (ValueError, TypeError, KeyError, AttributeError, BridgeUnavailableError) as error:
        reason = str(error)[:256]
        return {**result, "unavailable_reason": reason,
                "raw_metrics": {"realm_county_count": _unknown("realm_county_count", reason)}}
