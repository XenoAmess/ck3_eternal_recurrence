"""Read-only WAR31 surrender evidence projection; never executes a game step.

This intentionally projects only fields present in the existing rich native
snapshot and typed action result.  A missing field is unavailable, never zero.
"""

from __future__ import annotations

from collections.abc import Mapping


WAR_ID = 16777231
TARGET_TITLE_ID = 2128
PLAYER_CHARACTER_ID = 29829
OPPONENT_CHARACTER_ID = 30097
ACTION_STEP = f"surrender-war-{WAR_ID}"
RESOURCE_SCALE = 100_000


def _integer(value: object, *, minimum: int | None = None) -> bool:
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and (minimum is None or value >= minimum)
    )


def _unavailable(reason: str) -> dict[str, object]:
    return {"status": "unavailable", "value": None, "reason": reason}


def _available(value: object, source: str) -> dict[str, object]:
    return {"status": "available", "value": value, "source": source}


def project_war31_frame(snapshot: Mapping[str, object]) -> dict[str, object]:
    """Project one rich snapshot without guessing absent native domains."""
    if not isinstance(snapshot, Mapping):
        raise ValueError("snapshot must be an object")
    played = snapshot.get("played_character")
    actor = played.get("character_id") if isinstance(played, Mapping) else None
    if actor != PLAYER_CHARACTER_ID or isinstance(actor, bool):
        raise ValueError("WAR31 snapshot is not bound to Robert character 29829")
    episode = snapshot.get("episode_run_id")
    date = snapshot.get("date_raw")
    native_revision = snapshot.get("native_revision")
    if (
        not isinstance(episode, str)
        or not episode
        or not _integer(date)
        or not _integer(native_revision, minimum=0)
        or not isinstance(snapshot.get("snapshot_id"), str)
    ):
        raise ValueError("WAR31 snapshot lacks native frame identity")

    wars = snapshot.get("active_wars")
    if isinstance(wars, list) and all(
        isinstance(row, Mapping) and _integer(row.get("war_id"), minimum=1)
        for row in wars
    ):
        matches = [row for row in wars if row["war_id"] == WAR_ID]
        if len(matches) > 1:
            raise ValueError("WAR31 appears twice in one native snapshot")
        if matches:
            war = matches[0]
            if (
                war.get("player_side") != "defender"
                or war.get("player_is_primary_war_leader") is not True
                or war.get("primary_opponent_character_id")
                != OPPONENT_CHARACTER_ID
                or not isinstance(war.get("targeted_title_ids"), list)
                or TARGET_TITLE_ID not in war["targeted_title_ids"]
            ):
                raise ValueError("WAR31 active-war identity drifted")
        active = _available(bool(matches), "snapshot.active_wars")
    else:
        active = _unavailable("active_wars_missing_or_malformed")

    resources: dict[str, dict[str, object]] = {}
    for name in ("gold", "prestige"):
        row = snapshot.get(f"played_character_{name}")
        raw = row.get("raw") if isinstance(row, Mapping) else None
        if (
            isinstance(row, Mapping)
            and set(row) == {"raw", "scale"}
            and _integer(raw)
            and -(2**63) <= raw <= 2**63 - 1
            and row.get("scale") == RESOURCE_SCALE
        ):
            resources[name] = _available(
                {"character_id": actor, "raw": raw, "scale": RESOURCE_SCALE},
                f"snapshot.played_character_{name}",
            )
        else:
            resources[name] = _unavailable(f"played_character_{name}_missing")
    resources["piety"] = _unavailable("piety_not_in_rich_snapshot")
    resources["opponent"] = _unavailable(
        "opponent_signed_resources_not_in_rich_snapshot"
    )

    return {
        "identity": {
            "episode_run_id": episode,
            "snapshot_id": snapshot["snapshot_id"],
            "native_revision": native_revision,
            "date_raw": date,
            "played_character_id": actor,
        },
        "war_active": active,
        "target_title": {
            "title_id": TARGET_TITLE_ID,
            "holder_character_id": _unavailable(
                "target_title_holder_not_in_rich_snapshot"
            ),
            "liege_character_id": _unavailable(
                "target_title_liege_not_in_rich_snapshot"
            ),
            "vassal_character_ids": _unavailable(
                "target_title_vassals_not_in_rich_snapshot"
            ),
        },
        "resources": resources,
        "persisted_truce": _unavailable(
            "persisted_truce_not_in_rich_snapshot"
        ),
    }


def _resource_delta(
    before: Mapping[str, object], after: Mapping[str, object]
) -> dict[str, object]:
    if before["status"] != "available" or after["status"] != "available":
        return _unavailable("resource_missing_in_before_or_after")
    first = before["value"]
    second = after["value"]
    if not isinstance(first, Mapping) or not isinstance(second, Mapping):
        raise ValueError("resource projection malformed")
    if first["character_id"] != second["character_id"]:
        raise ValueError("resource character identity changed")
    return _available(
        {
            "character_id": first["character_id"],
            "signed_delta_raw": second["raw"] - first["raw"],
            "scale": RESOURCE_SCALE,
        },
        "paired_native_snapshots",
    )


def _action_submission(
    result: Mapping[str, object] | None,
    before: Mapping[str, object],
    after: Mapping[str, object],
) -> dict[str, object]:
    if result is None:
        return _unavailable("typed_action_result_not_supplied")
    if result.get("step") != ACTION_STEP:
        raise ValueError("action result is not the exact WAR31 surrender step")
    if result.get("accepted") is not True or result.get("status") != "submitted":
        return _available(False, "typed_action_result")
    action = result.get("war_termination_result")
    observed_id = action.get("observed_snapshot_id") if isinstance(action, Mapping) else None
    observed_revision = (
        int(observed_id.removeprefix("native:"))
        if isinstance(observed_id, str)
        and observed_id.startswith("native:")
        and observed_id.removeprefix("native:").isdecimal()
        else None
    )
    if not isinstance(action, Mapping) or any(
        (
            action.get("war_id") != WAR_ID,
            action.get("outcome") != "attacker_victory",
            action.get("episode_run_id")
            != before["identity"]["episode_run_id"],
            action.get("starting_snapshot_id")
            != before["identity"]["snapshot_id"],
            observed_revision is None
            or not (before["identity"]["native_revision"]
                    <= observed_revision
                    <= after["identity"]["native_revision"]),
            action.get("submitted_date_raw")
            != before["identity"]["date_raw"],
            action.get("observed_date_raw")
            != after["identity"]["date_raw"],
            action.get("command_acknowledged") is not True,
            action.get("status") not in {"submitted_pending", "applied"},
        )
    ):
        raise ValueError("WAR31 action result lacks exact frame binding")
    absence = after["war_active"]
    if absence["status"] == "available":
        immediately_absent = action.get("war_id_absent_after_ack") is True
        subsequently_absent = not absence["value"]
        if (immediately_absent and not subsequently_absent) or (
            action["status"] == "applied"
            and (not immediately_absent or not subsequently_absent)
        ):
            raise ValueError("WAR31 action result conflicts with observed war state")
    return _available(
        {"submitted": True, "phase": action["status"]},
        "typed_action_result",
    )


def project_war31_postcondition(
    before_snapshot: Mapping[str, object],
    after_snapshot: Mapping[str, object],
    *,
    action_result: Mapping[str, object] | None = None,
    next_turn_snapshot: Mapping[str, object] | None = None,
    recovery_snapshot: Mapping[str, object] | None = None,
    recovery_pair: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Compare exact frames and state remaining proof gaps without closing them."""
    before = project_war31_frame(before_snapshot)
    after = project_war31_frame(after_snapshot)
    first = before["identity"]
    second = after["identity"]
    if first["episode_run_id"] != second["episode_run_id"]:
        raise ValueError("WAR31 before/after episode mismatch")
    if second["date_raw"] < first["date_raw"]:
        raise ValueError("WAR31 after frame predates before frame")
    if second["native_revision"] < first["native_revision"]:
        raise ValueError("WAR31 native revision went backwards")
    if before["war_active"] != _available(True, "snapshot.active_wars"):
        raise ValueError("WAR31 before frame does not prove an active war")

    action = _action_submission(action_result, before, after)
    deltas = {
        name: _resource_delta(before["resources"][name], after["resources"][name])
        for name in ("gold", "prestige")
    }
    deltas["piety"] = _unavailable("piety_not_in_rich_snapshot")
    deltas["opponent"] = _unavailable(
        "opponent_signed_resources_not_in_rich_snapshot"
    )

    if next_turn_snapshot is None:
        next_turn = _unavailable("next_turn_snapshot_not_supplied")
        next_turn_projected = None
    else:
        next_turn_projected = project_war31_frame(next_turn_snapshot)
        ident = next_turn_projected["identity"]
        if ident["episode_run_id"] != first["episode_run_id"]:
            raise ValueError("WAR31 next-turn episode mismatch")
        if ident["date_raw"] <= second["date_raw"]:
            raise ValueError("WAR31 next-turn date did not advance")
        next_turn = _available(
            {"identity": ident, "war_active": next_turn_projected["war_active"]},
            "next_turn_native_snapshot",
        )

    if recovery_snapshot is None or recovery_pair is None:
        recovery = _unavailable("paired_recovery_snapshot_or_receipt_missing")
    else:
        restored = project_war31_frame(recovery_snapshot)
        source_hash = recovery_pair.get("source_save_sha256")
        restored_hash = recovery_pair.get("restored_save_sha256")
        if not (
            isinstance(source_hash, str)
            and len(source_hash) == 64
            and all(character in "0123456789abcdefABCDEF" for character in source_hash)
            and source_hash.upper() == str(restored_hash).upper()
        ):
            raise ValueError("WAR31 recovery lacks exact paired save SHA-256")
        reference_name = "after"
        reference = after
        if (next_turn_projected is not None
                and restored["identity"]["date_raw"]
                == next_turn_projected["identity"]["date_raw"]):
            reference_name = "next_turn"
            reference = next_turn_projected
        comparable = (
            restored["identity"]["episode_run_id"]
            == reference["identity"]["episode_run_id"]
            and restored["identity"]["date_raw"]
            == reference["identity"]["date_raw"]
            and restored["war_active"] == reference["war_active"]
            and restored["resources"] == reference["resources"]
        )
        recovery = _available(
            {"paired_save_sha256": source_hash.upper(),
             "matched_reference": reference_name, "matched": comparable},
            "paired_recovery_native_snapshot",
        )

    gates = {
        "action_submitted": (
            action["status"] == "available"
            and isinstance(action["value"], Mapping)
            and action["value"].get("submitted") is True
        ),
        "war_absent_after": (
            after["war_active"]["status"] == "available"
            and after["war_active"]["value"] is False
        ),
        "war_absent_next_turn": (
            next_turn["status"] == "available"
            and next_turn["value"]["war_active"]
            == _available(False, "snapshot.active_wars")
        ),
        "paired_recovery_matched": (
            recovery["status"] == "available"
            and recovery["value"]["matched"] is True
        ),
        "title_holder_liege_vassals_observed": False,
        "persisted_truce_observed": False,
        "all_signed_resources_observed": False,
    }
    return {
        "schema": "xar.ck3.war31-postcondition-offline.v1",
        "war_id": WAR_ID,
        "target_title_id": TARGET_TITLE_ID,
        "before": before,
        "after": after,
        "action_submission": action,
        "signed_resource_deltas": deltas,
        "target_title_delta": _unavailable(
            "target_title_holder_liege_vassals_not_in_rich_snapshot"
        ),
        "persisted_truce_delta": _unavailable(
            "persisted_truce_not_in_rich_snapshot"
        ),
        "next_turn": next_turn,
        "paired_recovery": recovery,
        "gates": gates,
        "material_outcome_complete": all(gates.values()),
    }
