"""Pure projection contract for Raiktor-context war-bound regiments.

The underlying native observation is generation-safe but explicitly generic.
This module therefore exposes current soldiers and postwar cleanup while
refusing to label those regiments as the authored ``norman_highwaymen``.
"""

from __future__ import annotations


BACKEND_ID = "ck3-1.19.0.6-native-raiktor-war-bound-regiment-v1"
STATUS = "generic_war_bound_visible_source_unattributed"

_ROOT_KEYS = {
    "schema_version",
    "backend_id",
    "status",
    "failure",
    "active_frame",
    "postwar_frame",
    "owner_character_id",
    "war_id",
    "source_attribution",
    "soldiers",
    "cleanup",
    "regiments",
    "readiness",
}
_ACTIVE_FRAME_KEYS = {
    "snapshot_revision",
    "native_revision",
    "date_raw",
    "paused",
    "war_id",
    "active_casus_belli_database_index",
    "active_casus_belli_key",
    "primary_attacker_character_id",
    "primary_defender_character_id",
}
_POSTWAR_FRAME_KEYS = {
    "snapshot_revision",
    "native_revision",
    "date_raw",
    "paused",
    "frozen_war_id",
    "frozen_war_absent_from_active_wars",
}
_SOURCE_KEYS = {
    "mode",
    "authored_candidate_name",
    "authored_spawn_army_count",
    "authored_soldiers_per_army",
    "authored_total_soldiers",
}
_SOLDIER_KEYS = {
    "current_soldiers_observable",
    "observed_current_soldiers",
    "pre_soldiers_observable",
    "observed_pre_soldiers",
    "proven_soldier_loss_observable",
    "proven_soldiers_lost",
}
_CLEANUP_KEYS = {"observable", "status"}
_REGIMENT_KEYS = {
    "persistent_regiment_id",
    "bound_war_id",
    "war_keep_on_attacker_victory",
    "current_soldiers",
    "postwar_persistent_state",
    "composition_rows",
}
_ROW_KEYS = {
    "composition_ordinal",
    "current_army_regiment_id",
    "raised_carmy_id",
    "current_soldiers",
    "current_army_regiment_state",
    "raised_carmy_state",
    "frozen_carmy_roster_evidence",
}
_READINESS_KEYS = {
    "exact_raiktor_war_context_ready",
    "generic_war_bound_identity_ready",
    "current_soldiers_ready",
    "postwar_cleanup_ready",
    "source_specific_attribution_ready",
    "pre_soldiers_ready",
    "proven_soldier_loss_ready",
    "independently_visible_value_ready",
    "raiktor_source_specific_domain_ready",
}


def normalize_raiktor_war_bound_regiment(
    value: object,
    *,
    expected_war_id: int,
    expected_attacker_character_id: int,
    expected_defender_character_id: int,
    expected_snapshot_revision: int,
    expected_native_revision: int,
    expected_date_raw: int,
) -> dict[str, object]:
    """Validate the honest generic-visible/source-unattributed projection."""
    root = _exact_dict(value, _ROOT_KEYS, "war-bound regiment root")
    if (
        root["schema_version"] != 1
        or root["backend_id"] != BACKEND_ID
        or root["status"] != STATUS
        or root["failure"] is not None
    ):
        raise ValueError("Raiktor war-bound regiment observation unavailable")

    war_id = _full_id(root["war_id"], "war_id")
    owner_id = _full_id(root["owner_character_id"], "owner_character_id")
    expected_war = _full_id(expected_war_id, "expected_war_id")
    expected_attacker = _full_id(
        expected_attacker_character_id, "expected_attacker_character_id"
    )
    expected_defender = _full_id(
        expected_defender_character_id, "expected_defender_character_id"
    )
    if war_id != expected_war or owner_id != expected_attacker:
        raise ValueError("Raiktor war-bound regiment binding disagrees")

    active = _exact_dict(
        root["active_frame"], _ACTIVE_FRAME_KEYS, "active_frame"
    )
    if (
        active["paused"] is not True
        or _full_id(active["war_id"], "active_frame.war_id") != war_id
        or active["active_casus_belli_key"] != "raiktor_claim_cb"
        or _non_negative_int32(
            active["active_casus_belli_database_index"],
            "active_frame.active_casus_belli_database_index",
        )
        < 0
        or _full_id(
            active["primary_attacker_character_id"],
            "active_frame.primary_attacker_character_id",
        )
        != expected_attacker
        or _full_id(
            active["primary_defender_character_id"],
            "active_frame.primary_defender_character_id",
        )
        != expected_defender
        or _positive_uint64(
            active["snapshot_revision"], "active_frame.snapshot_revision"
        )
        != _positive_uint64(
            expected_snapshot_revision, "expected_snapshot_revision"
        )
        or _positive_uint64(
            active["native_revision"], "active_frame.native_revision"
        )
        != _positive_uint64(
            expected_native_revision, "expected_native_revision"
        )
        or _signed_int32(active["date_raw"], "active_frame.date_raw")
        != _signed_int32(expected_date_raw, "expected_date_raw")
    ):
        raise ValueError("Raiktor war-bound active frame disagrees")

    source = _exact_dict(
        root["source_attribution"], _SOURCE_KEYS, "source_attribution"
    )
    if source != {
        "mode": "authored_candidate_only",
        "authored_candidate_name": "norman_highwaymen",
        "authored_spawn_army_count": 6,
        "authored_soldiers_per_army": 500,
        "authored_total_soldiers": 3000,
    }:
        raise ValueError("Raiktor authored source boundary disagrees")

    soldiers = _exact_dict(root["soldiers"], _SOLDIER_KEYS, "soldiers")
    total_current = _non_negative_int64(
        soldiers["observed_current_soldiers"], "observed_current_soldiers"
    )
    if (
        soldiers["current_soldiers_observable"] is not True
        or soldiers["pre_soldiers_observable"] is not False
        or soldiers["observed_pre_soldiers"] is not None
        or soldiers["proven_soldier_loss_observable"] is not False
        or soldiers["proven_soldiers_lost"] is not None
    ):
        raise ValueError("Raiktor soldier observation overclaims evidence")

    cleanup = _exact_dict(root["cleanup"], _CLEANUP_KEYS, "cleanup")
    cleanup_observable = _strict_bool(cleanup["observable"], "cleanup.observable")
    if cleanup_observable:
        if cleanup["status"] not in {"destroyed", "still_alive"}:
            raise ValueError("Raiktor cleanup status is unknown")
        postwar = _exact_dict(
            root["postwar_frame"], _POSTWAR_FRAME_KEYS, "postwar_frame"
        )
        if (
            postwar["paused"] is not True
            or postwar["frozen_war_absent_from_active_wars"] is not True
            or _full_id(postwar["frozen_war_id"], "postwar.frozen_war_id")
            != war_id
        ):
            raise ValueError("Raiktor postwar frame disagrees")
        _positive_uint64(postwar["snapshot_revision"], "postwar.snapshot_revision")
        _positive_uint64(postwar["native_revision"], "postwar.native_revision")
        _signed_int32(postwar["date_raw"], "postwar.date_raw")
    elif root["postwar_frame"] is not None or cleanup["status"] is not None:
        raise ValueError("Raiktor cleanup frame exists without observation")

    regiments = root["regiments"]
    if not isinstance(regiments, list) or not regiments:
        raise ValueError("Raiktor war-bound regiment list is empty")
    persistent_ids: set[int] = set()
    current_ids: set[int] = set()
    computed_total = 0
    any_exact_alive = False
    for regiment_index, raw_regiment in enumerate(regiments):
        regiment = _exact_dict(
            raw_regiment, _REGIMENT_KEYS, f"regiments[{regiment_index}]"
        )
        persistent_id = _full_id(
            regiment["persistent_regiment_id"],
            f"regiments[{regiment_index}].persistent_regiment_id",
        )
        if persistent_id in persistent_ids:
            raise ValueError("duplicate persistent regiment generation")
        persistent_ids.add(persistent_id)
        if (
            _full_id(
                regiment["bound_war_id"],
                f"regiments[{regiment_index}].bound_war_id",
            )
            != war_id
            or regiment["war_keep_on_attacker_victory"] is not False
        ):
            raise ValueError("generic war-bound selector drifted")
        regiment_total = _non_negative_int64(
            regiment["current_soldiers"],
            f"regiments[{regiment_index}].current_soldiers",
        )
        rows = regiment["composition_rows"]
        if not isinstance(rows, list) or len(rows) != 7:
            raise ValueError("war-bound composition must contain seven rows")
        computed_regiment = 0
        persistent_state = regiment["postwar_persistent_state"]
        if cleanup_observable:
            if persistent_state not in {"destroyed", "still_alive"}:
                raise ValueError("postwar persistent state is unknown")
            any_exact_alive |= persistent_state == "still_alive"
        elif persistent_state is not None:
            raise ValueError("active observation invented postwar state")
        for ordinal, raw_row in enumerate(rows):
            row = _exact_dict(
                raw_row,
                _ROW_KEYS,
                f"regiments[{regiment_index}].composition_rows[{ordinal}]",
            )
            if row["composition_ordinal"] != ordinal:
                raise ValueError("war-bound composition ordinal drifted")
            current_id = row["current_army_regiment_id"]
            raised_id = row["raised_carmy_id"]
            current_soldiers = row["current_soldiers"]
            if current_id is None:
                if raised_id is not None or current_soldiers is not None:
                    raise ValueError("absent current regiment row is malformed")
                if cleanup_observable:
                    if (
                        row["current_army_regiment_state"] != "not_present"
                        or row["raised_carmy_state"] != "not_present"
                        or row["frozen_carmy_roster_evidence"] != "not_present"
                    ):
                        raise ValueError("absent cleanup row is malformed")
                elif any(
                    row[key] is not None
                    for key in (
                        "current_army_regiment_state",
                        "raised_carmy_state",
                        "frozen_carmy_roster_evidence",
                    )
                ):
                    raise ValueError("active row invented cleanup state")
                continue
            current = _full_id(current_id, "current_army_regiment_id")
            _full_id(raised_id, "raised_carmy_id")
            if current in current_ids:
                raise ValueError("duplicate current regiment generation")
            current_ids.add(current)
            row_soldiers = _non_negative_int32(
                current_soldiers, "composition current_soldiers"
            )
            computed_regiment += row_soldiers
            if cleanup_observable:
                current_state = row["current_army_regiment_state"]
                army_state = row["raised_carmy_state"]
                roster = row["frozen_carmy_roster_evidence"]
                if current_state not in {"destroyed", "still_alive"}:
                    raise ValueError("current cleanup state is unknown")
                if army_state not in {"destroyed", "still_alive"}:
                    raise ValueError("army cleanup state is unknown")
                if (
                    army_state == "destroyed"
                    and roster != "frozen_army_destroyed"
                ) or (
                    army_state == "still_alive"
                    and roster not in {"detached", "still_attached"}
                ) or (
                    current_state == "destroyed" and roster == "still_attached"
                ):
                    raise ValueError("cleanup roster evidence disagrees")
                any_exact_alive |= current_state == "still_alive"
            elif any(
                row[key] is not None
                for key in (
                    "current_army_regiment_state",
                    "raised_carmy_state",
                    "frozen_carmy_roster_evidence",
                )
            ):
                raise ValueError("active row invented cleanup state")
        if computed_regiment != regiment_total:
            raise ValueError("regiment soldier aggregate disagrees")
        computed_total += regiment_total
    if computed_total != total_current:
        raise ValueError("war-bound soldier aggregate disagrees")
    if cleanup_observable and (
        (cleanup["status"] == "still_alive") != any_exact_alive
    ):
        raise ValueError("aggregate cleanup status disagrees")

    readiness = _exact_dict(root["readiness"], _READINESS_KEYS, "readiness")
    if readiness != {
        "exact_raiktor_war_context_ready": True,
        "generic_war_bound_identity_ready": True,
        "current_soldiers_ready": True,
        "postwar_cleanup_ready": cleanup_observable,
        "source_specific_attribution_ready": False,
        "pre_soldiers_ready": False,
        "proven_soldier_loss_ready": False,
        "independently_visible_value_ready": True,
        "raiktor_source_specific_domain_ready": False,
    }:
        raise ValueError("Raiktor war-bound readiness overclaims evidence")
    return dict(root)


def _exact_dict(value: object, keys: set[str], label: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"{label} has a malformed schema")
    return value


def _strict_bool(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{label} must be a boolean")
    return value


def _full_id(value: object, label: str) -> int:
    result = _signed_int32(value, label)
    if result == -1:
        raise ValueError(f"{label} is the invalid sentinel")
    return result


def _non_negative_int32(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    if value < 0 or value > 2**31 - 1:
        raise ValueError(f"{label} is outside non-negative int32")
    return value


def _signed_int32(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    if value < -(2**31) or value > 2**31 - 1:
        raise ValueError(f"{label} is outside int32")
    return value


def _positive_uint64(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    if value <= 0 or value > 2**64 - 1:
        raise ValueError(f"{label} is outside positive uint64")
    return value


def _non_negative_int64(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    if value < 0 or value > 2**63 - 1:
        raise ValueError(f"{label} is outside non-negative int64")
    return value
