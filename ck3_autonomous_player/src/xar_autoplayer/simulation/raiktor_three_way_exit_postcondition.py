"""Verify one authorized Raiktor three-way action from later observations.

The verifier is pure: it never executes a command, saves a game, restores a
checkpoint, or touches CK3.  A command acknowledgement proves only that the
authorized literal was submitted.  Termination becomes GREEN only when the
six expectations frozen into that authorization are independently observed.
"""

from __future__ import annotations

from copy import deepcopy
import re

from xar_autoplayer.simulation.raiktor_continue_vs_surrender_policy import (
    canonical_policy_input_sha256,
)
from xar_autoplayer.simulation.raiktor_three_way_exit_action_gate import (
    CONTRACT as ACTION_GATE_CONTRACT,
    PROVIDER_ID as ACTION_GATE_PROVIDER_ID,
    PROVIDER_SCHEMA as ACTION_GATE_PROVIDER_SCHEMA,
)
from xar_autoplayer.simulation.raiktor_three_way_exit_recommendation import (
    CONTINUE_POSTCONDITIONS,
    TERMINATION_POSTCONDITIONS,
)


CONTRACT = "raiktor-three-way-exit-postcondition-v1"
PROVIDER_SCHEMA = "xar.ck3.raiktor_three_way_exit_postcondition.v1"
PROVIDER_ID = "raiktor-three-way-exit-postcondition-provider-v1"
POSTWAR_EVIDENCE_SCHEMA = "xar.ck3.raiktor_three_way_exit_postwar_evidence.v1"

_SHA256 = re.compile(r"[0-9a-fA-F]{64}")


class ThreeWayExitPostconditionError(ValueError):
    """An authorization or supplied evidence envelope is malformed."""


def provide_raiktor_three_way_exit_postcondition(
    action_gate_value: object | None,
    action_result_value: object | None,
    post_snapshot_value: object | None,
    postwar_evidence_value: object | None = None,
    checkpoint_restore_value: object | None = None,
) -> dict[str, object]:
    """Return a receipt for one action without performing any operation."""

    if action_gate_value is None:
        return _result(blockers=["action_authorization_unavailable"])
    authorization = normalize_raiktor_three_way_exit_authorization(
        action_gate_value
    )
    action = _object(authorization["action"], "authorization.action")
    plan = _object(
        authorization["postcondition_plan"], "authorization.postcondition_plan"
    )
    route = action.get("semantic_action")
    requirements = plan.get("requirements")
    expected_requirements = (
        CONTINUE_POSTCONDITIONS
        if route == "continue"
        else TERMINATION_POSTCONDITIONS
        if route in {"white_peace", "surrender"}
        else None
    )
    if expected_requirements is None or requirements != list(expected_requirements):
        raise ThreeWayExitPostconditionError(
            "authorization postcondition route or requirements drifted"
        )
    expectations = _object(plan.get("expectations"), "postcondition expectations")

    missing = [
        reason
        for value, reason in (
            (action_result_value, "action_result_unavailable"),
            (post_snapshot_value, "post_snapshot_unavailable"),
        )
        if value is None
    ]
    if route in {"white_peace", "surrender"}:
        if postwar_evidence_value is None:
            missing.append("postwar_evidence_unavailable")
        if checkpoint_restore_value is None:
            missing.append("checkpoint_restore_evidence_unavailable")
    if missing:
        return _result(
            blockers=missing,
            route=route,
            authorization=authorization,
        )

    action_result = _object(action_result_value, "action result")
    post = _snapshot(post_snapshot_value, "post snapshot")
    submission_ready = _action_submission_matches(
        action_result, authorization=authorization, post=post
    )

    if route == "continue":
        checks = _continue_checks(
            authorization=authorization,
            expectations=expectations,
            action_result=action_result,
            post=post,
        )
        blockers = _failed(checks)
        return _result(
            blockers=blockers,
            route=route,
            authorization=authorization,
            checks=checks,
            action_submitted=submission_ready,
            postcondition_verified=not blockers,
        )

    postwar = _postwar_evidence(postwar_evidence_value)
    checkpoint_restore = _checkpoint_restore(checkpoint_restore_value)
    checks = _termination_checks(
        authorization=authorization,
        expectations=expectations,
        action_result=action_result,
        post=post,
        postwar=postwar,
        checkpoint_restore=checkpoint_restore,
    )
    blockers = _failed(checks)
    verified = not blockers
    return _result(
        blockers=blockers,
        route=route,
        authorization=authorization,
        checks=checks,
        action_submitted=submission_ready,
        postcondition_verified=verified,
        checkpoint_cold_restore_verified=checks[
            "postwar_checkpoint_cold_restore_rebinds_identity"
        ],
        gen034_closed=verified,
        evidence={
            "post_snapshot_id": post.get("snapshot_id"),
            "postwar_evidence_sha256": canonical_policy_input_sha256(postwar),
            "checkpoint_sha256": _object(
                _object(
                    checkpoint_restore["save_result"], "save result"
                ).get("checkpoint"),
                "saved checkpoint",
            ).get("sha256"),
        },
    )


def normalize_raiktor_three_way_exit_authorization(
    value: object,
) -> dict[str, object]:
    """Validate and return one exact action-gate authorization."""
    gate = _object(value, "action gate")
    if (
        gate.get("schema") != ACTION_GATE_PROVIDER_SCHEMA
        or gate.get("provider") != ACTION_GATE_PROVIDER_ID
        or gate.get("status") != "authorized"
        or gate.get("action_ready") is not True
        or gate.get("blockers") != []
    ):
        raise ThreeWayExitPostconditionError("action gate is not authorized")
    authorization = _object(gate.get("authorization"), "authorization")
    if (
        authorization.get("schema_version") != 1
        or authorization.get("contract") != ACTION_GATE_CONTRACT
        or authorization.get("status") != "authorized"
    ):
        raise ThreeWayExitPostconditionError("authorization identity drifted")
    digest = authorization.get("authorization_sha256")
    unhashed = {
        key: item
        for key, item in authorization.items()
        if key != "authorization_sha256"
    }
    if not _is_sha256(digest) or digest != canonical_policy_input_sha256(unhashed):
        raise ThreeWayExitPostconditionError("authorization hash drifted")
    action = _object(authorization.get("action"), "authorization.action")
    frame = _object(authorization.get("frame"), "authorization.frame")
    if (
        action.get("single_action_only") is not True
        or action.get("war_id") != frame.get("war_id")
        or action.get("expected_revision") != frame.get("snapshot_revision")
    ):
        raise ThreeWayExitPostconditionError("authorization action binding drifted")
    return authorization


def _action_submission_matches(
    result: dict[str, object],
    *,
    authorization: dict[str, object],
    post: dict[str, object],
) -> bool:
    action = _object(authorization["action"], "authorization.action")
    frame = _object(authorization["frame"], "authorization.frame")
    if not (
        result.get("step") == action.get("literal")
        and result.get("accepted") is True
        and result.get("status") in {"submitted", "applied"}
        and result.get("backend_id") == "native-headless"
    ):
        return False
    termination = result.get("war_termination_result")
    if termination is None:
        return True
    if not isinstance(termination, dict):
        raise ThreeWayExitPostconditionError(
            "war_termination_result must be an object"
        )
    termination_status = termination.get("status")
    observed_id = termination.get("observed_snapshot_id")
    observation_bound = bool(
        observed_id == post.get("snapshot_id")
        if termination_status == "applied"
        else termination_status == "submitted_pending"
        and isinstance(observed_id, str)
        and bool(observed_id)
        and termination.get("war_id_absent_after_ack") is False
    )
    return bool(
        termination_status in {"applied", "submitted_pending"}
        and termination.get("war_id") == action.get("war_id")
        and termination.get("outcome") == action.get("semantic_action")
        and termination.get("episode_run_id") == frame.get("episode_id")
        and termination.get("starting_snapshot_id") == frame.get("snapshot_id")
        and observation_bound
        and termination.get("command_acknowledged") is True
    )


def _continue_checks(
    *,
    authorization: dict[str, object],
    expectations: dict[str, object],
    action_result: dict[str, object],
    post: dict[str, object],
) -> dict[str, bool]:
    frame = _object(authorization["frame"], "authorization.frame")
    diagnostics = _object(post.get("diagnostics"), "post diagnostics")
    played = _object(post.get("played_character"), "post played_character")
    return {
        "authorized_action_submitted": _action_submission_matches(
            action_result, authorization=authorization, post=post
        ),
        "same_full_generation_war_id_remains_active": _war_present(
            post, expectations.get("war_id")
        ),
        "same_played_character_and_episode_remain_bound": bool(
            played.get("character_id") == expectations.get("played_character_id")
            and post.get("episode_run_id") == expectations.get("episode_id")
            and diagnostics.get("bridge_pid") == frame.get("ck3_pid")
            and diagnostics.get("connection_generation")
            == _connection_generation(frame.get("connection_id"))
        ),
        "map_resume_is_observed_on_a_successor_revision": bool(
            post.get("revision") > frame.get("snapshot_revision")
            and post.get("native_revision") > frame.get("native_revision")
            and post.get("date_raw") > frame.get("date_raw")
            and post.get("active_event") is None
        ),
    }


def _termination_checks(
    *,
    authorization: dict[str, object],
    expectations: dict[str, object],
    action_result: dict[str, object],
    post: dict[str, object],
    postwar: dict[str, object],
    checkpoint_restore: dict[str, object],
) -> dict[str, bool]:
    frame = _object(authorization["frame"], "authorization.frame")
    resources = _object(expectations.get("resources"), "resource expectations")
    gold = _object(resources.get("gold"), "gold expectations")
    prestige = _object(resources.get("prestige"), "prestige expectations")
    truce_expected = _object(expectations.get("truce"), "truce expectations")
    loss_expected = _object(
        expectations.get("source_specific_loss"), "loss expectations"
    )
    truce = _object(postwar.get("truce"), "postwar truce")
    loss = _object(postwar.get("source_specific_loss"), "postwar loss")
    post_identity = _same_hot_session(post, frame=frame)
    post_successor = bool(
        post.get("revision") > frame.get("snapshot_revision")
        and post.get("native_revision") > frame.get("native_revision")
        and post.get("date_raw") >= frame.get("date_raw")
        and post.get("paused") is True
        and post.get("active_event") is None
    )
    authorization_sha256 = authorization["authorization_sha256"]
    evidence_binding = bool(
        postwar.get("authorization_sha256") == authorization_sha256
        and postwar.get("post_snapshot_id") == post.get("snapshot_id")
        and postwar.get("war_id") == expectations.get("war_id")
    )
    queried_date = truce.get("queried_at_date_raw")
    evaluated_days = truce.get("evaluated_days")
    expiry = truce.get("expiry_date_raw")
    exact_expiry = bool(
        _is_int(queried_date)
        and _is_int(evaluated_days)
        and _is_int(expiry)
        and expiry == queried_date + evaluated_days * 24
    )
    return {
        "authorized_action_submitted": _action_submission_matches(
            action_result, authorization=authorization, post=post
        ),
        "old_full_generation_war_id_absent": bool(
            post_identity
            and post_successor
            and not _war_present(post, expectations.get("war_id"))
        ),
        "gold_matches_frozen_terms": bool(
            evidence_binding
            and _fixed_point(post.get("played_character_gold"))
            == (gold.get("post_raw"), resources.get("scale"))
        ),
        "attacker_prestige_matches_frozen_terms": bool(
            evidence_binding
            and _fixed_point(post.get("played_character_prestige"))
            == (prestige.get("post_raw"), resources.get("scale"))
        ),
        "directional_truce_days_and_expiry_observed": bool(
            evidence_binding
            and truce.get("source") == "persisted_native_truce_row"
            and truce.get("formula_derived") is False
            and truce.get("from_character_id")
            == truce_expected.get("owner_character_id")
            and truce.get("to_character_id")
            == truce_expected.get("toward_character_id")
            and evaluated_days == truce_expected.get("evaluated_days")
            and queried_date == post.get("date_raw")
            and exact_expiry
            and _is_sha256(truce.get("evidence_sha256"))
        ),
        "source_specific_war_bound_regiments_absent": bool(
            evidence_binding
            and loss.get("war_id") == loss_expected.get("war_id")
            and loss.get("status") == loss_expected.get("required_cleanup_status")
            and loss.get("source_specific_attribution_ready") is True
            and _positive_int(loss.get("frozen_generation_count"))
            and loss.get("post_termination_soldiers") == 0
            and _is_sha256(loss.get("source_set_sha256"))
            and _is_sha256(loss.get("evidence_sha256"))
        ),
        "postwar_checkpoint_cold_restore_rebinds_identity": bool(
            evidence_binding
            and _checkpoint_restore_matches(
                checkpoint_restore,
                post=post,
                expectations=expectations,
            )
        ),
    }


def _same_hot_session(
    snapshot: dict[str, object], *, frame: dict[str, object]
) -> bool:
    diagnostics = snapshot.get("diagnostics")
    played = snapshot.get("played_character")
    return bool(
        isinstance(diagnostics, dict)
        and isinstance(played, dict)
        and diagnostics.get("bridge_pid") == frame.get("ck3_pid")
        and diagnostics.get("connection_generation")
        == _connection_generation(frame.get("connection_id"))
        and snapshot.get("episode_run_id") == frame.get("episode_id")
        and played.get("character_id")
        == frame.get("primary_attacker_character_id")
    )


def _checkpoint_restore_matches(
    value: dict[str, object],
    *,
    post: dict[str, object],
    expectations: dict[str, object],
) -> bool:
    save = _object(value.get("save_result"), "save result")
    restore = _object(value.get("restore_result"), "restore result")
    restored = _snapshot(value.get("restored_snapshot"), "restored snapshot")
    saved_checkpoint = _object(save.get("checkpoint"), "saved checkpoint")
    restored_checkpoint = _object(
        restore.get("checkpoint"), "restored checkpoint"
    )
    lifecycle = _object(restore.get("lifecycle"), "restore lifecycle")
    restored_diagnostics = _object(
        restored.get("diagnostics"), "restored diagnostics"
    )
    restored_player = _object(
        restored.get("played_character"), "restored played_character"
    )
    post_diagnostics = _object(post.get("diagnostics"), "post diagnostics")
    resources = _object(expectations.get("resources"), "resource expectations")
    gold = _object(resources.get("gold"), "gold expectations")
    prestige = _object(resources.get("prestige"), "prestige expectations")
    digest = saved_checkpoint.get("sha256")
    return bool(
        save.get("step") == "save-checkpoint"
        and save.get("accepted") is True
        and save.get("status") == "submitted"
        and save.get("backend_id") == "native-headless"
        and saved_checkpoint.get("status") == "saved"
        and _is_sha256(digest)
        and saved_checkpoint.get("date_raw") == post.get("date_raw")
        and saved_checkpoint.get("episode_run_id") == post.get("episode_run_id")
        and saved_checkpoint.get("episode_character_id")
        == expectations.get("played_character_id")
        and isinstance(save.get("materialization"), dict)
        and save["materialization"].get("available") is True
        and restore.get("step") == "restore-checkpoint"
        and restore.get("accepted") is True
        and restore.get("status") == "restored"
        and restore.get("backend_id") == "native-headless"
        and restore.get("source") == "native-session-lifecycle-queue"
        and restore.get("map_ready") is True
        and restored_checkpoint.get("status") == "restored"
        and restored_checkpoint.get("sha256") == digest
        and restored_checkpoint.get("saved_date_raw") == post.get("date_raw")
        and restored_checkpoint.get("date_raw") == post.get("date_raw")
        and restore.get("restored_date_raw") == post.get("date_raw")
        and restore.get("paused") is True
        and restore.get("snapshot_id") == restored.get("snapshot_id")
        and restore.get("revision") == restored.get("revision")
        and lifecycle.get("previous_pid") == post_diagnostics.get("bridge_pid")
        and _positive_int(lifecycle.get("pid"))
        and lifecycle.get("pid") != post_diagnostics.get("bridge_pid")
        and lifecycle.get("previous_connection_generation")
        == post_diagnostics.get("connection_generation")
        and lifecycle.get("connection_generation")
        == restored_diagnostics.get("connection_generation")
        and restored_diagnostics.get("bridge_pid") == lifecycle.get("pid")
        and restored.get("paused") is True
        and restored.get("active_event") is None
        and restored.get("date_raw") == post.get("date_raw")
        and restored.get("episode_run_id") == post.get("episode_run_id")
        and restored_player.get("character_id")
        == expectations.get("played_character_id")
        and not _war_present(restored, expectations.get("war_id"))
        and _fixed_point(restored.get("played_character_gold"))
        == (gold.get("post_raw"), resources.get("scale"))
        and _fixed_point(restored.get("played_character_prestige"))
        == (prestige.get("post_raw"), resources.get("scale"))
    )


def _postwar_evidence(value: object) -> dict[str, object]:
    result = _object(value, "postwar evidence")
    if set(result) != {
        "schema",
        "authorization_sha256",
        "war_id",
        "post_snapshot_id",
        "source_specific_loss",
        "truce",
    } or result.get("schema") != POSTWAR_EVIDENCE_SCHEMA:
        raise ThreeWayExitPostconditionError("postwar evidence schema drifted")
    if not _is_sha256(result.get("authorization_sha256")):
        raise ThreeWayExitPostconditionError(
            "postwar authorization hash is malformed"
        )
    return result


def _checkpoint_restore(value: object) -> dict[str, object]:
    result = _object(value, "checkpoint restore evidence")
    if set(result) != {"save_result", "restore_result", "restored_snapshot"}:
        raise ThreeWayExitPostconditionError(
            "checkpoint restore evidence schema drifted"
        )
    return result


def _snapshot(value: object, name: str) -> dict[str, object]:
    result = _object(value, name)
    for field in ("revision", "native_revision", "date_raw"):
        if not _is_int(result.get(field)):
            raise ThreeWayExitPostconditionError(f"{name} {field} is malformed")
    snapshot_id = result.get("snapshot_id")
    if not isinstance(snapshot_id, str) or not snapshot_id:
        raise ThreeWayExitPostconditionError(f"{name} snapshot_id is malformed")
    wars = result.get("active_wars")
    if not isinstance(wars, list):
        raise ThreeWayExitPostconditionError(f"{name} active_wars is malformed")
    return result


def _war_present(snapshot: dict[str, object], war_id: object) -> bool:
    return any(
        isinstance(row, dict) and row.get("war_id") == war_id
        for row in snapshot["active_wars"]
    )


def _fixed_point(value: object) -> tuple[object, object] | None:
    if not isinstance(value, dict):
        return None
    raw = value.get("raw")
    scale = value.get("scale")
    if not _is_int(raw) or not _is_int(scale):
        return None
    return raw, scale


def _connection_generation(value: object) -> int | None:
    prefix = "connection-generation:"
    if not isinstance(value, str) or not value.startswith(prefix):
        return None
    suffix = value.removeprefix(prefix)
    return int(suffix) if suffix.isascii() and suffix.isdecimal() else None


def _object(value: object, name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ThreeWayExitPostconditionError(f"{name} must be an object")
    return value


def _is_int(value: object) -> bool:
    return not isinstance(value, bool) and isinstance(value, int)


def _positive_int(value: object) -> bool:
    return _is_int(value) and value > 0


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and _SHA256.fullmatch(value) is not None


def _failed(checks: dict[str, bool]) -> list[str]:
    return [f"postcondition_failed:{name}" for name, ready in checks.items() if not ready]


def _result(
    *,
    blockers: list[str],
    route: object | None = None,
    authorization: dict[str, object] | None = None,
    checks: dict[str, bool] | None = None,
    action_submitted: bool = False,
    postcondition_verified: bool = False,
    checkpoint_cold_restore_verified: bool = False,
    gen034_closed: bool = False,
    evidence: dict[str, object] | None = None,
) -> dict[str, object]:
    receipt = {
        "schema_version": 1,
        "contract": CONTRACT,
        "status": "green" if postcondition_verified else "red",
        "route": route,
        "authorization_sha256": (
            authorization.get("authorization_sha256")
            if authorization is not None
            else None
        ),
        "checks": deepcopy(checks) if checks is not None else {},
        "evidence": deepcopy(evidence) if evidence is not None else {},
        "action_submitted": action_submitted,
        "postcondition_verified": postcondition_verified,
        "checkpoint_cold_restore_verified": checkpoint_cold_restore_verified,
        "gen034_closed": gen034_closed,
    }
    receipt["receipt_sha256"] = canonical_policy_input_sha256(receipt)
    return {
        "schema": PROVIDER_SCHEMA,
        "provider": PROVIDER_ID,
        "status": (
            "verified"
            if postcondition_verified
            else "evidence_required"
            if any(item.endswith("_unavailable") for item in blockers)
            else "red"
        ),
        "route": route,
        "action_submitted": action_submitted,
        "postcondition_verified": postcondition_verified,
        "checkpoint_cold_restore_verified": checkpoint_cold_restore_verified,
        "gen034_closed": gen034_closed,
        "blockers": blockers,
        "postcondition_receipt": receipt,
        "boundaries": [
            "command_acknowledgement_is_submission_only",
            "termination_requires_all_six_frozen_observations",
            "continue_postcondition_does_not_close_gen034",
            "this_provider_performs_no_ck3_or_filesystem_operation",
        ],
    }


__all__ = [
    "CONTRACT",
    "POSTWAR_EVIDENCE_SCHEMA",
    "PROVIDER_ID",
    "PROVIDER_SCHEMA",
    "ThreeWayExitPostconditionError",
    "normalize_raiktor_three_way_exit_authorization",
    "provide_raiktor_three_way_exit_postcondition",
]
