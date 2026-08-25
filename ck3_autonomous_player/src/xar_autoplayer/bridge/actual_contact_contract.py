"""Typed contract for CK3's exact same-province contact resolver mirror."""

from __future__ import annotations


QUERY_ACTUAL_CONTACT_SCOPE_CAPABILITY = (
    "game.command.query-actual-contact-scope-v1-N"
)
QUERY_ACTUAL_CONTACT_SCOPE_STEP_PREFIX = "query-actual-contact-scope-v1-"

_ACTUAL_CONTACT_SCOPE_KEYS = {
    "schema_version",
    "contract_stage",
    "status",
    "scope_kind",
    "snapshot_revision",
    "date_raw",
    "subject_army_id",
    "subject_native_carmy_id",
    "subject_owner_character_id",
    "target_province_id",
    "province_unit_army_ids",
    "province_combat_ids",
    "stored_order_policy",
    "transition_kind",
    "selected_combat_id",
    "selected_combat_array_index",
    "join_side",
    "defender_seed_character_id",
    "initiator_is_defender",
    "adjacency_kind_raw",
    "loser_excluded_native_carmy_ids",
    "opponent_army_ids",
    "attacker_army_ids",
    "defender_army_ids",
    "actual_contact_scope_ready",
    "combat_v3_participant_scope_ready",
}


def query_actual_contact_scope_step(
    subject_army_id: int, target_province_id: int
) -> str:
    """Build the canonical current-Province contact query literal."""
    subject = _positive_int32(subject_army_id, "subject_army_id")
    target = _positive_int32(target_province_id, "target_province_id")
    return f"{QUERY_ACTUAL_CONTACT_SCOPE_STEP_PREFIX}{subject}-at-{target}"


def parse_query_actual_contact_scope_step(
    step: object,
) -> tuple[int, int] | None:
    if not isinstance(step, str) or not step.startswith(
        QUERY_ACTUAL_CONTACT_SCOPE_STEP_PREFIX
    ):
        return None
    payload = step.removeprefix(QUERY_ACTUAL_CONTACT_SCOPE_STEP_PREFIX)
    subject_text, separator, target_text = payload.partition("-at-")
    if (
        not separator
        or "-at-" in target_text
        or not _canonical_positive_decimal(subject_text)
        or not _canonical_positive_decimal(target_text)
    ):
        return None
    subject = int(subject_text)
    target = int(target_text)
    if subject > 2**31 - 1 or target > 2**31 - 1:
        return None
    return subject, target


def normalize_actual_contact_scope(
    value: object,
    *,
    expected_subject_army_id: int,
    expected_target_province_id: int,
    expected_date_raw: int,
    expected_snapshot_revision: int,
) -> dict[str, object]:
    """Validate one complete, application-main, two-sample contact mirror."""
    if not isinstance(value, dict) or set(value) != _ACTUAL_CONTACT_SCOPE_KEYS:
        raise ValueError("native actual_contact_scope has a malformed schema")
    if (
        value.get("schema_version") != 1
        or value.get("contract_stage")
        != "production_exact_current_province"
        or value.get("status") != "available"
        or value.get("stored_order_policy") != "numeric_full_id"
    ):
        raise ValueError("native actual_contact_scope contract is unavailable")

    scope_kind = value.get("scope_kind")
    if scope_kind not in {
        "pre_contact_prediction",
        "post_contact_observation",
    }:
        raise ValueError("actual_contact_scope scope_kind is unknown")

    subject = _positive_int32(
        value.get("subject_army_id"), "actual_contact_scope.subject_army_id"
    )
    native_subject = _positive_int32(
        value.get("subject_native_carmy_id"),
        "actual_contact_scope.subject_native_carmy_id",
    )
    owner = _positive_int32(
        value.get("subject_owner_character_id"),
        "actual_contact_scope.subject_owner_character_id",
    )
    target = _positive_int32(
        value.get("target_province_id"),
        "actual_contact_scope.target_province_id",
    )
    date_raw = _signed_int32(
        value.get("date_raw"), "actual_contact_scope.date_raw"
    )
    revision = _positive_uint64(
        value.get("snapshot_revision"),
        "actual_contact_scope.snapshot_revision",
    )
    if (
        subject != expected_subject_army_id
        or target != expected_target_province_id
        or date_raw != expected_date_raw
        or revision != expected_snapshot_revision
    ):
        raise ValueError("native actual_contact_scope binding disagrees")

    province_units = _positive_id_list(
        value.get("province_unit_army_ids"),
        "actual_contact_scope.province_unit_army_ids",
        strictly_increasing=True,
    )
    province_combats = _positive_id_list(
        value.get("province_combat_ids"),
        "actual_contact_scope.province_combat_ids",
        strictly_increasing=True,
    )
    if subject not in province_units:
        raise ValueError("actual_contact_scope subject is absent from Province")
    loser_exclusions = _positive_id_list(
        value.get("loser_excluded_native_carmy_ids"),
        "actual_contact_scope.loser_excluded_native_carmy_ids",
    )
    opponents = _positive_id_list(
        value.get("opponent_army_ids"),
        "actual_contact_scope.opponent_army_ids",
    )
    attackers = _positive_id_list(
        value.get("attacker_army_ids"),
        "actual_contact_scope.attacker_army_ids",
    )
    defenders = _positive_id_list(
        value.get("defender_army_ids"),
        "actual_contact_scope.defender_army_ids",
    )
    if len(set(attackers)) != len(attackers) or len(set(defenders)) != len(
        defenders
    ):
        raise ValueError("actual_contact_scope final sides contain duplicates")
    if set(attackers) & set(defenders):
        raise ValueError("actual_contact_scope final sides overlap")

    transition = value.get("transition_kind")
    if transition not in {
        "none",
        "join_existing",
        "create_new",
        "in_combat",
    }:
        raise ValueError("actual_contact_scope transition_kind is unknown")
    selected_combat = _optional_positive_int32(
        value.get("selected_combat_id"),
        "actual_contact_scope.selected_combat_id",
    )
    selected_index = _optional_non_negative_int32(
        value.get("selected_combat_array_index"),
        "actual_contact_scope.selected_combat_array_index",
    )
    join_side = value.get("join_side")
    if join_side not in {None, "attacker", "defender"}:
        raise ValueError("actual_contact_scope join_side is malformed")
    defender_seed = _optional_positive_int32(
        value.get("defender_seed_character_id"),
        "actual_contact_scope.defender_seed_character_id",
    )
    initiator_is_defender = _strict_bool(
        value.get("initiator_is_defender"),
        "actual_contact_scope.initiator_is_defender",
    )
    adjacency_kind = _signed_int32(
        value.get("adjacency_kind_raw"),
        "actual_contact_scope.adjacency_kind_raw",
    )
    scope_ready = _strict_bool(
        value.get("actual_contact_scope_ready"),
        "actual_contact_scope.actual_contact_scope_ready",
    )
    combat_ready = _strict_bool(
        value.get("combat_v3_participant_scope_ready"),
        "actual_contact_scope.combat_v3_participant_scope_ready",
    )
    if not scope_ready or combat_ready != (transition != "none"):
        raise ValueError("actual_contact_scope readiness predicate disagrees")
    if (transition == "in_combat") != (
        scope_kind == "post_contact_observation"
    ):
        raise ValueError("actual_contact_scope phase predicate disagrees")

    if transition == "join_existing":
        if (
            selected_combat is None
            or selected_index is None
            or selected_index >= len(province_combats)
            or province_combats[selected_index] != selected_combat
            or join_side is None
            or defender_seed is not None
            or not attackers
            or not defenders
            or opponents
            or (join_side == "attacker") != (subject in attackers)
            or (join_side == "defender") != (subject in defenders)
            or subject in (defenders if join_side == "attacker" else attackers)
            or (attackers if join_side == "attacker" else defenders)[-1]
            != subject
        ):
            raise ValueError("actual_contact_scope join projection disagrees")
    elif transition == "create_new":
        if (
            selected_combat is not None
            or selected_index is not None
            or join_side is not None
            or defender_seed is None
            or not opponents
            or subject in opponents
            or any(opponent not in province_units for opponent in opponents)
        ):
            raise ValueError("actual_contact_scope creation scope disagrees")
        # The native builder vector intentionally preserves every passing
        # row, while CCombatSide insertion applies first-seen CArmyID
        # deduplication.  Preserve the raw evidence above but validate the
        # predicted sides against the constructor's post-insert shape.
        unique_opponents = list(dict.fromkeys(opponents))
        expected_attackers = (
            unique_opponents if initiator_is_defender else [subject]
        )
        expected_defenders = (
            [subject] if initiator_is_defender else unique_opponents
        )
        if attackers != expected_attackers or defenders != expected_defenders:
            raise ValueError("actual_contact_scope creation sides disagree")
    elif transition == "in_combat":
        subject_is_attacker = subject in attackers
        subject_is_defender = subject in defenders
        if (
            selected_combat is None
            or selected_index is None
            or selected_index >= len(province_combats)
            or province_combats[selected_index] != selected_combat
            or join_side is not None
            or defender_seed is not None
            or initiator_is_defender
            or adjacency_kind != 0
            or loser_exclusions
            or opponents
            or not attackers
            or not defenders
            or subject_is_attacker == subject_is_defender
        ):
            raise ValueError(
                "actual_contact_scope in-combat observation disagrees"
            )
    elif (
        selected_combat is not None
        or selected_index is not None
        or join_side is not None
        or defender_seed is not None
        or opponents
        or attackers
        or defenders
        or initiator_is_defender
        or adjacency_kind != 0
    ):
        raise ValueError("actual_contact_scope no-transition payload disagrees")

    return {
        "schema_version": 1,
        "contract_stage": "production_exact_current_province",
        "status": "available",
        "scope_kind": scope_kind,
        "snapshot_revision": revision,
        "date_raw": date_raw,
        "subject_army_id": subject,
        "subject_native_carmy_id": native_subject,
        "subject_owner_character_id": owner,
        "target_province_id": target,
        "province_unit_army_ids": province_units,
        "province_combat_ids": province_combats,
        "stored_order_policy": "numeric_full_id",
        "transition_kind": transition,
        "selected_combat_id": selected_combat,
        "selected_combat_array_index": selected_index,
        "join_side": join_side,
        "defender_seed_character_id": defender_seed,
        "initiator_is_defender": initiator_is_defender,
        "adjacency_kind_raw": adjacency_kind,
        "loser_excluded_native_carmy_ids": loser_exclusions,
        "opponent_army_ids": opponents,
        "attacker_army_ids": attackers,
        "defender_army_ids": defenders,
        "actual_contact_scope_ready": True,
        "combat_v3_participant_scope_ready": combat_ready,
    }


def _canonical_positive_decimal(value: str) -> bool:
    return bool(value and value.isascii() and value.isdigit() and value[0] != "0")


def _positive_int32(value: object, name: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 < value <= 2**31 - 1
    ):
        raise ValueError(f"{name} must be a positive int32")
    return value


def _signed_int32(value: object, name: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not -(2**31) <= value <= 2**31 - 1
    ):
        raise ValueError(f"{name} must be a signed int32")
    return value


def _positive_uint64(value: object, name: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 < value <= 2**64 - 1
    ):
        raise ValueError(f"{name} must be a positive uint64")
    return value


def _optional_positive_int32(value: object, name: str) -> int | None:
    return None if value is None else _positive_int32(value, name)


def _optional_non_negative_int32(value: object, name: str) -> int | None:
    if value is None:
        return None
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 2**31 - 1
    ):
        raise ValueError(f"{name} must be a non-negative int32 or null")
    return value


def _strict_bool(value: object, name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be a boolean")
    return value


def _positive_id_list(
    value: object, name: str, *, strictly_increasing: bool = False
) -> list[int]:
    if not isinstance(value, list):
        raise ValueError(f"{name} must be a list")
    result = [
        _positive_int32(candidate, f"{name}[{index}]")
        for index, candidate in enumerate(value)
    ]
    if strictly_increasing and any(
        left >= right for left, right in zip(result, result[1:])
    ):
        raise ValueError(f"{name} must be in strict native numeric order")
    return result
