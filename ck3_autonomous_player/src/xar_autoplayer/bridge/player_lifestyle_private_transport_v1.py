"""Exact private LIFE2/stock-focus/perk query and typed slot43 selection.

This transport is deliberately absent from public capabilities.  The bridge
still decides whether its private native executor is installed and whether
the exact source can provide final legal candidates.
"""

from __future__ import annotations

import uuid
from typing import Mapping

from .driver import StepPostconditionError


QUERY_STEP = "private-query-player-lifestyle-formal-v1"
STATE_QUERY_STEP = "private-query-player-lifestyle-current-state-v1"
FOCUS_QUERY_STEP = "private-query-player-lifestyle-stock-focus-v1"
DIPLOMACY_QUERY_STEP = "private-query-player-lifestyle-diplomacy-targets-v1"
MARTIAL_QUERY_STEP = "private-query-player-lifestyle-martial-authority-v1"
PERK_SUBMIT_STEP = "private-select-player-lifestyle-perk-v1"
FOCUS_SUBMIT_STEP = "private-select-player-lifestyle-stock-focus-v1"
RECEIPT_STEP = "private-query-player-lifestyle-receipt-v1"
FOCUS_TARGET = "stewardship_wealth_focus"
FOCUS_LIFESTYLE = "stewardship_lifestyle"
MARTIAL_TARGET = "martial_authority_focus"
MARTIAL_LIFESTYLE = "martial_lifestyle"
PERK_TARGETS = frozenset({
    "cutting_corners_perk", "professional_workforce_perk", "centralization_perk",
    "tax_man_perk",
    "serve_the_crown_perk",
})


def _target_in_final_legal_perks(
    query: Mapping[str, object], target: str, lifestyle: object
) -> bool:
    snapshot = query.get("snapshot")
    if not isinstance(snapshot, Mapping):
        return False
    readiness = snapshot.get("readiness")
    candidates = snapshot.get("legal_perk_candidates")
    if not (
        isinstance(readiness, Mapping)
        and readiness.get("legal_perk_candidates_ready") is True
        and isinstance(candidates, Mapping)
        and candidates.get("status") == "available"
        and isinstance(candidates.get("items"), list)
    ):
        return False
    return any(
        isinstance(row, Mapping)
        and row.get("key") == target
        and row.get("lifestyle_key") == lifestyle
        for row in candidates["items"]
    )


def _positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _nonnegative_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def parse_player_lifestyle_focus_private_v1(
    response: Mapping[str, object] | None,
    *,
    expected_request_id: str,
    source_frame: Mapping[str, object],
    independent_after_frame: Mapping[str, object],
    query_step: str = FOCUS_QUERY_STEP,
    target_key: str = FOCUS_TARGET,
    lifestyle_key: str = FOCUS_LIFESTYLE,
) -> dict[str, object]:
    """Validate the private fixed-focus read; never infer absent XP as zero.

    This is a typed read-only consumer, not a production action registration.
    A later submit must obtain fresh same-transaction native source and
    legality; this result cannot carry a definition pointer across frames.
    """

    expected = (
        "snapshot_id", "native_revision", "date_raw",
        "played_character_id", "episode_run_id",
    )
    if any(
        source_frame.get(key) != independent_after_frame.get(key)
        for key in expected
    ) or not (
        source_frame.get("paused") is True
        and independent_after_frame.get("paused") is True
        and source_frame.get("snapshot_id")
        == f"native:{source_frame.get('native_revision')}"
        and _positive_int(source_frame.get("native_revision"))
        and _nonnegative_int(source_frame.get("date_raw"))
        and _positive_int(source_frame.get("played_character_id"))
        and isinstance(source_frame.get("episode_run_id"), str)
        and source_frame["episode_run_id"].startswith(
            f"native-{source_frame['played_character_id']}-"
        )
    ):
        return {"status": "red", "issue": "paused_focus_frame_drift_or_invalid"}
    if not (
        isinstance(expected_request_id, str)
        and expected_request_id
        and isinstance(response, Mapping)
        and response.get("type") == "command_result"
        and response.get("protocol_version") == 1
        and response.get("request_id") == expected_request_id
        and response.get("ok") is True
    ):
        return {"status": "red", "issue": "native_focus_query_failed"}
    result = response.get("result")
    if not (
        isinstance(result, Mapping)
        and result.get("step") == query_step
        and result.get("private_build") is True
        and result.get("advertised") is False
        and result.get("read_only") is True
        and result.get("policy_scoped") is True
        and result.get("snapshot_id") == source_frame.get("snapshot_id")
        and result.get("episode_run_id") == source_frame.get("episode_run_id")
        and result.get("target_key") == target_key
    ):
        return {"status": "red", "issue": "native_focus_binding_invalid"}
    native_status = result.get("status")
    if isinstance(native_status, str) and native_status.startswith("unavailable_"):
        if "native_legal" in result or "target_lifestyle_progress" in result:
            return {"status": "red", "issue": "native_focus_unavailable_promoted"}
        return {
            "status": "red", "issue": "native_focus_source_unavailable",
            "native_status": native_status,
        }
    if not (
        native_status in {"observed_native_legal", "observed_native_illegal"}
        and result.get("native_legal") is (native_status == "observed_native_legal")
        and _positive_int(result.get("scanned_database_rows"))
        and result.get("target_lifestyle_key") == lifestyle_key
    ):
        return {"status": "red", "issue": "native_focus_legality_untyped"}
    progress = result.get("target_lifestyle_progress")
    if not isinstance(progress, Mapping):
        return {"status": "red", "issue": "target_lifestyle_progress_untyped"}
    if progress.get("presence") == "unavailable":
        if (
            progress.get("reason") != "target_native_getters_unavailable"
            or any(
                key in progress for key in (
                    "xp_total_raw", "xp_within_level_raw", "xp_per_level",
                    "unspent_perk_points", "used_perk_points",
                )
            )
        ):
            return {"status": "red", "issue": "target_progress_unknown_promoted"}
        return {
            "status": "target_progress_unavailable",
            "native_legal": result["native_legal"],
            "target_key": target_key,
            "target_lifestyle_key": lifestyle_key,
        }
    if not (
        progress.get("presence") == "present"
        and progress.get("source") == "exact_native_getters"
        and _nonnegative_int(progress.get("xp_total_raw"))
        and _nonnegative_int(progress.get("xp_within_level_raw"))
        and _positive_int(progress.get("xp_per_level"))
        and _nonnegative_int(progress.get("unspent_perk_points"))
        and _nonnegative_int(progress.get("used_perk_points"))
        and progress["xp_within_level_raw"] < progress["xp_per_level"] * 100000
    ):
        return {"status": "red", "issue": "target_progress_values_invalid"}
    return {
        "status": "observed",
        "native_legal": result["native_legal"],
        "target_key": target_key,
        "target_lifestyle_key": lifestyle_key,
        "target_lifestyle_progress": dict(progress),
        "source_frame": {key: source_frame.get(key) for key in expected},
    }


def query_player_lifestyle_focus_private_v1(
    driver: object, *, expected_revision: int | None = None,
    query_step: str = FOCUS_QUERY_STEP,
) -> dict[str, object]:
    """Run the default-off stock focus read and consume its independent frame.

    This exposes a private typed observation to policy code but neither
    registers a public capability nor submits a focus action.
    """

    if query_step not in {FOCUS_QUERY_STEP, DIPLOMACY_QUERY_STEP,
                          MARTIAL_QUERY_STEP}:
        raise ValueError("unsupported private lifestyle focus query step")
    if getattr(driver, "allow_private_lifestyle_formal_trial", False) is not True:
        return {"status": "trial_off", "step": query_step}
    starting = driver.take_snapshot()
    played = starting.get("played_character")
    player_id = played.get("character_id") if isinstance(played, Mapping) else None
    public_revision = starting.get("revision")
    native_revision = starting.get("native_revision")
    episode_run_id = starting.get("episode_run_id")
    date_raw = starting.get("date_raw")
    if not (
        starting.get("paused") is True
        and starting.get("map_ready") is True
        and _positive_int(public_revision)
        and _positive_int(native_revision)
        and _nonnegative_int(date_raw)
        and _positive_int(player_id)
        and isinstance(episode_run_id, str)
        and episode_run_id.startswith(f"native-{player_id}-")
        and starting.get("snapshot_id") == f"native:{native_revision}"
        and (expected_revision is None or expected_revision == public_revision)
    ):
        return {"status": "paused_frame_unavailable", "step": query_step}
    request_id = f"life-focus-query-{uuid.uuid4().hex}"
    driver.endpoint.send({
        "type": "execute_step", "protocol_version": 1,
        "request_id": request_id, "step": query_step,
        "expected_revision": native_revision,
        "expected_snapshot_id": starting["snapshot_id"],
        "episode_run_id": episode_run_id,
        "expected_date_raw": date_raw,
        "expected_player_character_id": player_id,
    })
    response = driver.state.wait_for_command_result(
        request_id, driver.command_timeout_seconds
    )
    ending = driver.take_snapshot()
    source_frame = {
        "paused": starting["paused"],
        "snapshot_id": starting["snapshot_id"],
        "native_revision": native_revision,
        "date_raw": date_raw,
        "played_character_id": player_id,
        "episode_run_id": episode_run_id,
    }
    after_played = ending.get("played_character")
    after_frame = {
        "paused": ending.get("paused"),
        "snapshot_id": ending.get("snapshot_id"),
        "native_revision": ending.get("native_revision"),
        "date_raw": ending.get("date_raw"),
        "played_character_id": (
            after_played.get("character_id")
            if isinstance(after_played, Mapping) else None
        ),
        "episode_run_id": ending.get("episode_run_id"),
    }
    if query_step == DIPLOMACY_QUERY_STEP:
        parsed = parse_player_lifestyle_diplomacy_targets_private_v1(
            response, expected_request_id=request_id,
            source_frame=source_frame, independent_after_frame=after_frame,
        )
    else:
        parsed = parse_player_lifestyle_focus_private_v1(
            response, expected_request_id=request_id,
            source_frame=source_frame, independent_after_frame=after_frame,
            query_step=query_step,
            target_key=(MARTIAL_TARGET if query_step == MARTIAL_QUERY_STEP
                        else FOCUS_TARGET),
            lifestyle_key=(MARTIAL_LIFESTYLE if query_step == MARTIAL_QUERY_STEP
                           else FOCUS_LIFESTYLE),
        )
    if ending.get("revision") != public_revision or ending.get("map_ready") is not True:
        return {"status": "red", "issue": "paused_focus_public_frame_drift"}
    return {**parsed, "step": query_step, "request_id": request_id}


def query_player_lifestyle_diplomacy_targets_private_v1(
    driver: object, *, expected_revision: int | None = None,
) -> dict[str, object]:
    """Read one named diplomacy focus/perk pair without admitting an action."""
    return query_player_lifestyle_focus_private_v1(
        driver, expected_revision=expected_revision,
        query_step=DIPLOMACY_QUERY_STEP,
    )


def query_player_lifestyle_martial_authority_private_v1(
    driver: object, *, expected_revision: int | None = None,
) -> dict[str, object]:
    """Read exact current-actor focus legality and martial XP; no submit."""
    return query_player_lifestyle_focus_private_v1(
        driver, expected_revision=expected_revision,
        query_step=MARTIAL_QUERY_STEP,
    )


def parse_player_lifestyle_diplomacy_targets_private_v1(
    response: Mapping[str, object] | None, *, expected_request_id: str,
    source_frame: Mapping[str, object],
    independent_after_frame: Mapping[str, object],
) -> dict[str, object]:
    """Keep an unavailable target separate from a native false verdict."""
    bound = ("snapshot_id", "native_revision", "date_raw",
             "played_character_id", "episode_run_id")
    if (any(source_frame.get(key) != independent_after_frame.get(key)
            for key in bound) or not (
        source_frame.get("paused") is True
        and independent_after_frame.get("paused") is True
        and source_frame.get("snapshot_id") ==
            f"native:{source_frame.get('native_revision')}"
        and _positive_int(source_frame.get("native_revision"))
        and _nonnegative_int(source_frame.get("date_raw"))
        and _positive_int(source_frame.get("played_character_id"))
        and isinstance(source_frame.get("episode_run_id"), str)
        and source_frame["episode_run_id"].startswith(
            f"native-{source_frame['played_character_id']}-")
    )):
        return {"status": "red", "issue": "paused_diplomacy_frame_drift_or_invalid"}
    if not (isinstance(response, Mapping)
            and response.get("type") == "command_result"
            and response.get("protocol_version") == 1
            and response.get("request_id") == expected_request_id
            and response.get("ok") is True):
        return {"status": "red", "issue": "native_diplomacy_query_failed"}
    result = response.get("result")
    if not (isinstance(result, Mapping)
            and result.get("step") == DIPLOMACY_QUERY_STEP
            and result.get("private_build") is True
            and result.get("advertised") is False
            and result.get("read_only") is True
            and result.get("policy_scoped") is True
            and all(result.get(key) == source_frame.get(key)
                    for key in bound)):
        return {"status": "red", "issue": "native_diplomacy_binding_invalid"}
    focus, perk = result.get("focus"), result.get("perk")
    if not (isinstance(focus, Mapping) and isinstance(perk, Mapping)
            and focus.get("target_key") == "diplomacy_foreign_affairs_focus"
            and perk.get("target_key") == "thoughtful_perk"):
        return {"status": "red", "issue": "native_diplomacy_target_invalid"}
    if result.get("status") == "unavailable":
        return {"status": "source_unavailable",
                "focus_status": focus.get("status"),
                "perk_status": perk.get("status")}
    progress = focus.get("target_lifestyle_progress")
    if not (result.get("status") == "observed"
            and focus.get("status") in {"observed_native_legal",
                                         "observed_native_illegal"}
            and perk.get("status") in {"observed_native_legal",
                                        "observed_native_illegal"}
            and focus.get("native_legal") is
                (focus["status"] == "observed_native_legal")
            and perk.get("native_legal") is
                (perk["status"] == "observed_native_legal")
            and focus.get("lifestyle_key") == "diplomacy_lifestyle"
            and perk.get("lifestyle_key") == "diplomacy_lifestyle"
            and isinstance(perk.get("target_perk_owned"), bool)
            and isinstance(progress, Mapping)
            and progress.get("presence") == "present"
            and progress.get("source") == "exact_native_getters"
            and _nonnegative_int(progress.get("xp_total_raw"))
            and _nonnegative_int(progress.get("xp_within_level_raw"))
            and _positive_int(progress.get("xp_per_level"))
            and _nonnegative_int(progress.get("unspent_perk_points"))
            and _nonnegative_int(progress.get("used_perk_points"))
            and progress["xp_within_level_raw"] <
                progress["xp_per_level"] * 100000
            and all(perk.get(field) == progress.get(field) for field in (
                "xp_total_raw", "xp_within_level_raw", "xp_per_level",
                "unspent_perk_points", "used_perk_points"))):
        return {"status": "red", "issue": "native_diplomacy_observation_invalid"}
    return {"status": "observed", "focus": dict(focus),
            "perk": dict(perk), "source_frame": {
                key: source_frame.get(key) for key in bound}}


def query_player_lifestyle_private_v1(
    driver: object, *, expected_revision: int | None = None,
    query_step: str = QUERY_STEP,
) -> dict[str, object]:
    """Query one paused frame; preserve an unavailable native result as RED evidence.

    ``expected_revision`` is the Python/public snapshot revision used by the
    caller to reject a stale plan.  The native mailbox is bound separately to
    ``native_revision`` and ``native:<native_revision>``.
    """

    if query_step not in {QUERY_STEP, STATE_QUERY_STEP}:
        raise ValueError("unsupported private lifestyle query step")
    if getattr(driver, "allow_private_lifestyle_formal_trial", False) is not True:
        return {"status": "trial_off", "step": query_step}
    starting = driver.take_snapshot()
    played = starting.get("played_character")
    player_id = played.get("character_id") if isinstance(played, Mapping) else None
    revision = starting.get("revision")
    native_revision = starting.get("native_revision")
    episode_run_id = starting.get("episode_run_id")
    date_raw = starting.get("date_raw")
    if not (
        starting.get("paused") is True
        and starting.get("map_ready") is True
        and _positive_int(revision)
        and _positive_int(native_revision)
        and isinstance(date_raw, int)
        and not isinstance(date_raw, bool)
        and date_raw >= 0
        and _positive_int(player_id)
        and isinstance(episode_run_id, str)
        and episode_run_id.startswith(f"native-{player_id}-")
        and starting.get("snapshot_id") == f"native:{native_revision}"
        and (expected_revision is None or expected_revision == revision)
    ):
        return {"status": "paused_frame_unavailable", "step": query_step}

    request_id = f"life-query-{uuid.uuid4().hex}"
    request = {
        "type": "execute_step",
        "protocol_version": 1,
        "request_id": request_id,
        "step": query_step,
        "expected_revision": native_revision,
        "expected_snapshot_id": starting["snapshot_id"],
        "episode_run_id": episode_run_id,
        "expected_date_raw": date_raw,
        "expected_player_character_id": player_id,
    }
    driver.endpoint.send(request)
    frame = driver.state.wait_for_command_result(
        request_id, driver.command_timeout_seconds
    )
    if not isinstance(frame, dict) or frame.get("request_id") != request_id:
        return {
            "status": "native_query_timeout_or_malformed",
            "step": query_step,
            "request_id": request_id,
        }
    if frame.get("ok") is not True:
        return {
            "status": "native_query_unavailable",
            "step": query_step,
            "request_id": request_id,
            "native_error": frame.get("error"),
        }
    result = frame.get("result")
    life_snapshot = result.get("snapshot") if isinstance(result, dict) else None
    ending = driver.take_snapshot()
    if not (
        isinstance(result, dict)
        and result.get("step") == query_step
        and result.get("private_build") is True
        and result.get("advertised") is False
        and result.get("status") == "available"
        and result.get("episode_run_id") == episode_run_id
        and isinstance(life_snapshot, dict)
        and life_snapshot.get("status") == "available"
        and life_snapshot.get("snapshot_id") == starting["snapshot_id"]
        # The private native formal wire names its published native-frame
        # revision ``public_revision``.  Python's public revision is an
        # independent monotonic publication counter and may be ahead after a
        # cold restore or a semantic republish.
        and life_snapshot.get("public_revision") == native_revision
        and life_snapshot.get("native_revision") == native_revision
        and life_snapshot.get("proof_epoch") == native_revision
        and life_snapshot.get("date_raw") == date_raw
        and life_snapshot.get("player_character_id") == player_id
        and ending.get("paused") is True
        and ending.get("snapshot_id") == starting["snapshot_id"]
        and ending.get("revision") == revision
        and ending.get("native_revision") == native_revision
        and ending.get("date_raw") == date_raw
        and ending.get("episode_run_id") == episode_run_id
    ):
        return {
            "status": "native_query_binding_red",
            "step": query_step,
            "request_id": request_id,
            "native_result": result,
        }
    return {
        "status": "available",
        "step": query_step,
        "request_id": request_id,
        "episode_run_id": episode_run_id,
        "formal_precondition_status": result.get("formal_precondition_status"),
        "snapshot": {**life_snapshot, "episode_run_id": episode_run_id},
        "source_frame": {
            "snapshot_id": starting["snapshot_id"],
            "revision": revision,
            "native_revision": native_revision,
            "date_raw": date_raw,
            "player_character_id": player_id,
        },
    }


def query_player_lifestyle_stock_focus_combined_private_v1(
    driver: object, *, expected_revision: int,
    target_key: str = FOCUS_TARGET,
) -> dict[str, object]:
    """Combine state and one named native-final-legal focus on one frame."""

    if target_key not in {FOCUS_TARGET, MARTIAL_TARGET}:
        raise ValueError("unsupported private lifestyle focus target")
    lifestyle_key = (
        MARTIAL_LIFESTYLE if target_key == MARTIAL_TARGET else FOCUS_LIFESTYLE
    )
    focus_step = (
        MARTIAL_QUERY_STEP if target_key == MARTIAL_TARGET else FOCUS_QUERY_STEP
    )

    state = query_player_lifestyle_private_v1(
        driver, expected_revision=expected_revision,
        query_step=STATE_QUERY_STEP,
    )
    if state.get("status") != "available":
        return {"status": "current_state_unavailable", "state": state}
    focus = query_player_lifestyle_focus_private_v1(
        driver, expected_revision=expected_revision, query_step=focus_step,
    )
    source = state.get("source_frame")
    focus_frame = focus.get("source_frame")
    life = state.get("snapshot")
    if not (
        focus.get("status") == "observed"
        and focus.get("native_legal") is True
        and isinstance(source, Mapping)
        and isinstance(focus_frame, Mapping)
        and isinstance(life, Mapping)
        and source.get("snapshot_id") == focus_frame.get("snapshot_id")
        and source.get("native_revision") == focus_frame.get("native_revision")
        and source.get("date_raw") == focus_frame.get("date_raw")
        and source.get("player_character_id") == focus_frame.get("played_character_id")
        and state.get("episode_run_id") == focus_frame.get("episode_run_id")
        and source.get("revision") == expected_revision
    ):
        return {"status": "stock_focus_readback_red", "state": state, "focus": focus}
    readiness = life.get("readiness")
    if not isinstance(readiness, Mapping):
        return {"status": "current_state_readiness_unavailable"}
    enriched = {
        **life,
        "readiness": {**readiness, "legal_focus_candidates_ready": True},
        "legal_focus_candidates": {
            "status": "available", "policy_scoped": True,
            "items": [{"key": target_key, "lifestyle_key": lifestyle_key}],
        },
        "target_lifestyle_progress": {
            **focus["target_lifestyle_progress"],
            "lifestyle_key": lifestyle_key,
        },
    }
    return {
        "status": "stock_focus_available",
        "step": focus_step,
        "formal_precondition_status": "stock_focus_ready",
        "episode_run_id": state["episode_run_id"],
        "snapshot": enriched,
        "source_frame": dict(source),
        "focus_query": focus,
    }


def _submit_player_lifestyle_selection_private_v1(
    driver: object,
    *,
    query: Mapping[str, object],
    action: Mapping[str, object],
    expected_revision: int,
    kind: str,
) -> dict[str, object]:
    """Submit once after a same-frame final-legal query; persist uncertainty."""

    starting = driver.take_snapshot()
    source = query.get("source_frame")
    expected = action.get("expected")
    target = action.get("target_key")
    focus_action = kind == "focus"
    submit_step = FOCUS_SUBMIT_STEP if focus_action else PERK_SUBMIT_STEP
    if not (
        getattr(driver, "allow_private_lifestyle_formal_trial", False) is True
        and query.get("status") == (
            "stock_focus_available" if focus_action else "available"
        )
        and query.get("formal_precondition_status") == (
            "stock_focus_ready" if focus_action else "ready"
        )
        and isinstance(source, Mapping)
        and isinstance(expected, Mapping)
        and action.get("kind") == kind
        and isinstance(target, str)
        and (target in {FOCUS_TARGET, MARTIAL_TARGET}
             if focus_action else target in PERK_TARGETS)
        and (
            not focus_action
            or (
                isinstance(query.get("focus_query"), Mapping)
                and query["focus_query"].get("target_key") == target
                and query["focus_query"].get("native_legal") is True
                and isinstance(query.get("snapshot"), Mapping)
                and isinstance(query["snapshot"].get("legal_focus_candidates"), Mapping)
                and any(
                    isinstance(row, Mapping)
                    and row.get("key") == target
                    and row.get("lifestyle_key") == action.get("target_lifestyle_key")
                    for row in query["snapshot"]["legal_focus_candidates"].get("items", [])
                )
            )
        )
        and (
            focus_action or _target_in_final_legal_perks(
                query, target, action.get("target_lifestyle_key")
            )
        )
        and starting.get("paused") is True
        and starting.get("snapshot_id") == source.get("snapshot_id")
        and starting.get("revision") == source.get("revision") == expected_revision
        and starting.get("native_revision") == source.get("native_revision")
        and starting.get("date_raw") == source.get("date_raw")
        and starting.get("episode_run_id") == query.get("episode_run_id")
        and expected.get("expected_snapshot_id") == source.get("snapshot_id")
        and expected.get("expected_episode_run_id") == query.get("episode_run_id")
        and expected.get("expected_public_revision") == source.get("native_revision")
        and expected.get("expected_native_revision") == source.get("native_revision")
        and expected.get("expected_proof_epoch") == source.get("native_revision")
        and expected.get("expected_date_raw") == source.get("date_raw")
        and expected.get("expected_player_character_id")
        == source.get("player_character_id")
    ):
        raise StepPostconditionError(
            "private LIFE selection lacks a complete final-legal same-frame binding",
            selected_step=submit_step,
            step_result={"status": "rejected_before_submit"},
        )
    action_id = f"life-{kind}-{uuid.uuid4().hex}"
    intent = {
        "status": "action_state_unknown",
        "action_request_id": action_id,
        "target_key": target,
        "kind": kind,
        "pre_public_revision": expected_revision,
        "episode_run_id": query["episode_run_id"],
        "source_frame": dict(source),
        "native_command_submitted": None,
    }
    # This durable marker precedes the native send.  A timeout or process
    # failure therefore blocks another submit until actual state is checked.
    driver._record_command(submit_step, ok=True, result=intent)
    if getattr(driver, "_driver_state_error", None) is not None:
        raise StepPostconditionError(
            "private LIFE intent was not durably recorded; no native send",
            selected_step=submit_step,
            step_result=intent,
        )
    request = {
        "type": "execute_step",
        "protocol_version": 1,
        "request_id": action_id,
        "step": submit_step,
        "expected_revision": source["native_revision"],
        "expected_snapshot_id": source["snapshot_id"],
        "expected_episode_run_id": query["episode_run_id"],
        "expected_date_raw": source["date_raw"],
        "expected_player_character_id": source["player_character_id"],
        "expected_native_revision": source["native_revision"],
        "expected_proof_epoch": source["native_revision"],
        "kind": kind,
        "target_key": target,
    }
    try:
        driver.endpoint.send(request)
        frame = driver.state.wait_for_command_result(
            action_id, driver.command_timeout_seconds
        )
    except Exception as error:
        raise StepPostconditionError(
            f"private LIFE native submit state unknown: {type(error).__name__}",
            selected_step=submit_step,
            step_result=intent,
        ) from error
    result = frame.get("result") if isinstance(frame, Mapping) else None
    if not (
        isinstance(frame, Mapping)
        and frame.get("request_id") == action_id
        and frame.get("ok") is True
        and isinstance(result, Mapping)
        and result.get("step") == submit_step
        and result.get("private_build") is True
        and result.get("advertised") is False
        and result.get("action_request_id") == action_id
        and result.get("target_key") == target
        and result.get("pre_snapshot_id") == source["snapshot_id"]
        and result.get("episode_run_id") == query["episode_run_id"]
        and result.get("pre_public_revision") == source["native_revision"]
    ):
        raise StepPostconditionError(
            "private LIFE submit ACK unavailable; action state unknown",
            selected_step=submit_step,
            step_result={**intent, "native_frame": frame},
        )
    if result.get("status") != "submitted_verification_pending" or result.get(
        "verification_pending"
    ) is not True:
        raise StepPostconditionError(
            "private LIFE final-legal selection was rejected before submission",
            selected_step=submit_step,
            step_result={**intent, "native_frame": frame},
        )
    pending = {
        **intent,
        "status": "submitted_verification_pending",
        "native_command_submitted": True,
        "native_ack": dict(result),
    }
    driver._record_command(submit_step, ok=True, result=pending)
    return pending


def submit_player_lifestyle_perk_private_v1(
    driver: object, *, query: Mapping[str, object],
    action: Mapping[str, object], expected_revision: int,
) -> dict[str, object]:
    return _submit_player_lifestyle_selection_private_v1(
        driver, query=query, action=action,
        expected_revision=expected_revision, kind="perk",
    )


def submit_player_lifestyle_stock_focus_private_v1(
    driver: object, *, query: Mapping[str, object],
    action: Mapping[str, object], expected_revision: int,
) -> dict[str, object]:
    return _submit_player_lifestyle_selection_private_v1(
        driver, query=query, action=action,
        expected_revision=expected_revision, kind="focus",
    )


def query_player_lifestyle_receipt_private_v1(
    driver: object, *, pending: Mapping[str, object], expected_revision: int
) -> dict[str, object]:
    """Accept only a later independent paused material focus/perk result."""

    starting = driver.take_snapshot()
    played = starting.get("played_character")
    player_id = played.get("character_id") if isinstance(played, Mapping) else None
    action_id = pending.get("action_request_id")
    pre_revision = pending.get("pre_public_revision")
    pre_native_revision = pending.get("source_frame", {}).get("native_revision")
    native_revision = starting.get("native_revision")
    kind = pending.get("kind", "perk")
    if not (
        getattr(driver, "allow_private_lifestyle_formal_trial", False) is True
        and isinstance(action_id, str)
        and kind in {"focus", "perk"}
        and action_id.startswith(f"life-{kind}-")
        and _positive_int(pre_revision)
        and _positive_int(pre_native_revision)
        and _positive_int(expected_revision)
        and expected_revision > pre_revision
        and _positive_int(native_revision)
        and native_revision > pre_native_revision
        and starting.get("paused") is True
        and starting.get("revision") == expected_revision
        and starting.get("snapshot_id") == f"native:{native_revision}"
        and starting.get("episode_run_id") == pending.get("episode_run_id")
        and _positive_int(player_id)
        and player_id == pending.get("source_frame", {}).get("player_character_id")
        and isinstance(starting.get("date_raw"), int)
    ):
        raise StepPostconditionError(
            "private LIFE receipt lacks an independent later paused frame",
            selected_step=RECEIPT_STEP,
            step_result={"status": "receipt_frame_unavailable", "pending": dict(pending)},
        )
    request_id = f"life-receipt-{uuid.uuid4().hex}"
    request = {
        "type": "execute_step",
        "protocol_version": 1,
        "request_id": request_id,
        "step": RECEIPT_STEP,
        "expected_revision": native_revision,
        "expected_snapshot_id": starting["snapshot_id"],
        "expected_episode_run_id": starting["episode_run_id"],
        "expected_date_raw": starting["date_raw"],
        "expected_player_character_id": player_id,
        "action_request_id": action_id,
    }
    driver.endpoint.send(request)
    frame = driver.state.wait_for_command_result(
        request_id, driver.command_timeout_seconds
    )
    result = frame.get("result") if isinstance(frame, Mapping) else None
    if not (
        isinstance(frame, Mapping)
        and frame.get("request_id") == request_id
        and frame.get("ok") is True
        and isinstance(result, Mapping)
        and result.get("step") == RECEIPT_STEP
        and result.get("private_build") is True
        and result.get("advertised") is False
        and result.get("action_request_id") == action_id
        and result.get("post_snapshot_id") == starting["snapshot_id"]
        and result.get("post_public_revision") == native_revision
        and result.get("episode_run_id") == starting["episode_run_id"]
        and result.get("status") == "applied"
        and (
            result.get("post_has_current_focus") is True
            and result.get("post_current_focus_key") == pending.get("target_key")
            if kind == "focus"
            else result.get("post_target_perk_owned") is True
        )
        and result.get("postcondition_verified") is True
    ):
        raise StepPostconditionError(
            "private LIFE independent material receipt did not apply",
            selected_step=RECEIPT_STEP,
            step_result={"status": "postcondition_red", "pending": dict(pending), "native_frame": frame},
        )
    ending = driver.take_snapshot()
    if not (
        ending.get("paused") is True
        and ending.get("snapshot_id") == starting["snapshot_id"]
        and ending.get("revision") == expected_revision
        and ending.get("date_raw") == starting["date_raw"]
    ):
        raise StepPostconditionError(
            "private LIFE receipt frame was not independently published",
            selected_step=RECEIPT_STEP,
            step_result={"status": "postcondition_red", "native_frame": frame},
        )
    applied = {
        "status": "applied",
        "action_request_id": action_id,
        "target_key": pending.get("target_key"),
        "kind": kind,
        "post_snapshot_id": starting["snapshot_id"],
        "post_public_revision": native_revision,
        "post_date_raw": starting["date_raw"],
        "episode_run_id": starting["episode_run_id"],
        "post_target_perk_owned": result.get("post_target_perk_owned"),
        "post_has_current_focus": result.get("post_has_current_focus"),
        "post_current_focus_key": result.get("post_current_focus_key"),
        "postcondition_verified": True,
    }
    driver._record_command(RECEIPT_STEP, ok=True, result=applied)
    return applied
