"""Typed contract for one exact-build ongoing CK3 battle control frame."""

from __future__ import annotations


QUERY_BATTLE_CONTROL_SNAPSHOT_V1_CAPABILITY = (
    "game.command.query-battle-control-snapshot-v1-N"
)
QUERY_BATTLE_CONTROL_SNAPSHOT_V1_STEP_PREFIX = (
    "query-battle-control-snapshot-v1-"
)

_SNAPSHOT_KEYS = {
    "schema_version",
    "contract_stage",
    "status",
    "battle_control_ready",
    "snapshot_revision",
    "observed_date_raw",
    "subject_public_cunit_id",
    "subject_native_carmy_id",
    "combat_id",
    "province_id",
    "selected_public_cunit_id",
    "selected_native_carmy_id",
    "selected_owner_character_id",
    "combat_province_id",
    "side_index",
    "side_scope",
    "affected_public_cunit_ids_in_stored_order",
    "unaffected_same_side_public_cunit_ids_in_stored_order",
    "side_flags",
    "legality",
    "phase",
    "phase_raw",
    "phase_day",
    "winner_side",
    "winner_raw",
    "forced_winner_side",
    "forced_winner_raw",
    "finalized",
    "battle_result_id",
    "base_combat_width",
    "final_combat_width",
    "roll_cadence_counter",
    "base_advantage_raw",
    "resolved_advantage_raw",
    "attacker",
    "defender",
}

_SIDE_KEYS = {
    "side_index",
    "role",
    "primary_participant_character_id",
    "selected_commander_character_id",
    "current_roll_points",
    "ordered_armies",
    "levy_entries",
    "men_at_arms_entries",
    "stored_current_fighting_raw",
    "stored_levy_current_fighting_raw",
    "stored_current_matches_derived",
    "stored_levy_current_matches_derived",
    "derived_current_fighting_raw",
    "derived_soft_casualties_raw",
    "derived_main_fighting_entry_hard_casualties_raw",
    "non_main_start_minus_current_minus_soft_raw",
    "participant_hard_ledger",
    "participant_hard_total_raw",
    "side_strength_raw",
    "side_strength_scale",
}

_ARMY_KEYS = {
    "native_carmy_id",
    "public_cunit_id",
    "owner_character_id",
    "combat_backlink_id",
}

_ENTRY_KEYS = {
    "bucket",
    "bucket_index",
    "regiment_id",
    "native_carmy_id",
    "public_cunit_id",
    "owner_character_id",
    "starting_raw",
    "current_fighting_raw",
    "soft_casualties_raw",
    "fights_in_main_phase",
    "hard_casualties_status",
    "hard_casualties_raw",
    "hard_casualties_source",
    "hard_casualties_unavailable_reason",
    "effective_max_size",
    "effective_siege_raw",
    "effective_damage_raw",
    "effective_toughness_raw",
    "effective_pursuit_raw",
    "effective_screen_raw",
    "entry_strength_raw",
}

_PARTICIPANT_HARD_KEYS = {
    "row_index",
    "participant_character_id",
    "hard_casualties_raw",
}

_ACTIVE_RETREAT_SIDE_FLAG_KEYS = {
    "disallow_retreat",
    "allow_early_retreat",
    "skip_pursuit",
}

_ACTIVE_RETREAT_LEGALITY_KEYS = {
    "status",
    "native_boolean",
    "phase_raw",
    "phase",
    "retreat_elapsed_baseline_date_raw",
    "elapsed_whole_days",
    "minimum_elapsed_whole_days_exclusive",
    "landless_gate_allows_retreat",
    "legal_now",
    "reason_codes_in_native_order",
    "native_reason_keys_in_native_order",
    "earliest_day_gate_date_raw",
}

_ACTIVE_RETREAT_REASON_KEY_BY_CODE = {
    "disallowed": "COMBAT_NO_RETREAT_DISALLOWED",
    "too_early": "COMBAT_NO_RETREAT_TOO_EARLY",
    "pursuit_or_done": "COMBAT_NO_RETREAT_PURSUIT",
    "landless": "COMBAT_NO_RETREAT_LANDLESS",
}

_PHASE_BY_RAW = {
    0: "maneuver",
    1: "main",
    2: "pursuit",
    3: "done",
}
_SIDE_BY_RAW = {
    -1: "none",
    0: "attacker",
    1: "defender",
}


def query_battle_control_snapshot_v1_step(
    subject_public_cunit_id: int,
) -> str:
    """Build the canonical query literal for one public CUnitID."""
    subject = _positive_int32(
        subject_public_cunit_id, "subject_public_cunit_id"
    )
    return f"{QUERY_BATTLE_CONTROL_SNAPSHOT_V1_STEP_PREFIX}{subject}"


def parse_query_battle_control_snapshot_v1_step(step: object) -> int | None:
    """Parse only the canonical positive-decimal query spelling."""
    if not isinstance(step, str) or not step.startswith(
        QUERY_BATTLE_CONTROL_SNAPSHOT_V1_STEP_PREFIX
    ):
        return None
    payload = step.removeprefix(
        QUERY_BATTLE_CONTROL_SNAPSHOT_V1_STEP_PREFIX
    )
    if not _canonical_positive_decimal(payload):
        return None
    subject = int(payload)
    return subject if subject <= 2**31 - 1 else None


def normalize_battle_control_snapshot_v1(
    value: object,
    *,
    expected_subject_public_cunit_id: int,
    expected_observed_date_raw: int,
    expected_snapshot_revision: int,
) -> dict[str, object]:
    """Validate one complete, paused, application-main battle frame."""
    expected_subject = _positive_int32(
        expected_subject_public_cunit_id,
        "expected_subject_public_cunit_id",
    )
    expected_date = _signed_int64(
        expected_observed_date_raw, "expected_observed_date_raw"
    )
    expected_revision = _positive_uint64(
        expected_snapshot_revision, "expected_snapshot_revision"
    )
    if not isinstance(value, dict) or set(value) != _SNAPSHOT_KEYS:
        raise ValueError("native battle_control_snapshot has a malformed schema")
    if (
        value.get("schema_version") != 1
        or value.get("contract_stage")
        != "production_exact_ongoing_combat"
        or value.get("status") != "available"
        or value.get("battle_control_ready") is not True
    ):
        raise ValueError("native battle_control_snapshot contract is unavailable")

    revision = _positive_uint64(
        value.get("snapshot_revision"),
        "battle_control_snapshot.snapshot_revision",
    )
    observed_date = _signed_int64(
        value.get("observed_date_raw"),
        "battle_control_snapshot.observed_date_raw",
    )
    subject = _positive_int32(
        value.get("subject_public_cunit_id"),
        "battle_control_snapshot.subject_public_cunit_id",
    )
    subject_native = _positive_int32(
        value.get("subject_native_carmy_id"),
        "battle_control_snapshot.subject_native_carmy_id",
    )
    if (
        revision != expected_revision
        or observed_date != expected_date
        or subject != expected_subject
    ):
        raise ValueError("native battle_control_snapshot binding disagrees")

    combat_id = _positive_int32(
        value.get("combat_id"), "battle_control_snapshot.combat_id"
    )
    province_id = _positive_int32(
        value.get("province_id"), "battle_control_snapshot.province_id"
    )
    selected_public_cunit_id = _positive_int32(
        value.get("selected_public_cunit_id"),
        "battle_control_snapshot.selected_public_cunit_id",
    )
    selected_native_carmy_id = _positive_int32(
        value.get("selected_native_carmy_id"),
        "battle_control_snapshot.selected_native_carmy_id",
    )
    selected_owner_character_id = _positive_int32(
        value.get("selected_owner_character_id"),
        "battle_control_snapshot.selected_owner_character_id",
    )
    combat_province_id = _positive_int32(
        value.get("combat_province_id"),
        "battle_control_snapshot.combat_province_id",
    )
    side_index = _signed_int32(
        value.get("side_index"), "battle_control_snapshot.side_index"
    )
    if side_index not in {0, 1}:
        raise ValueError("battle_control_snapshot.side_index must be 0 or 1")
    side_scope = value.get("side_scope")
    if side_scope not in {"full_side", "owner_subset"}:
        raise ValueError("battle_control_snapshot.side_scope is unknown")
    affected_public_cunit_ids = _positive_int32_list(
        value.get("affected_public_cunit_ids_in_stored_order"),
        "battle_control_snapshot.affected_public_cunit_ids_in_stored_order",
    )
    unaffected_public_cunit_ids = _positive_int32_list(
        value.get("unaffected_same_side_public_cunit_ids_in_stored_order"),
        (
            "battle_control_snapshot."
            "unaffected_same_side_public_cunit_ids_in_stored_order"
        ),
    )
    side_flags = _normalize_active_retreat_side_flags(
        value.get("side_flags")
    )
    phase_raw = _signed_int32(
        value.get("phase_raw"), "battle_control_snapshot.phase_raw"
    )
    if value.get("phase") != _PHASE_BY_RAW.get(phase_raw):
        raise ValueError("battle_control_snapshot phase mapping disagrees")
    legality = _normalize_active_retreat_legality(
        value.get("legality"),
        expected_phase_raw=phase_raw,
        observed_date_raw=observed_date,
        side_flags=side_flags,
    )
    phase_day = _signed_int32(
        value.get("phase_day"), "battle_control_snapshot.phase_day"
    )
    winner_raw = _signed_int32(
        value.get("winner_raw"), "battle_control_snapshot.winner_raw"
    )
    if value.get("winner_side") != _SIDE_BY_RAW.get(winner_raw):
        raise ValueError("battle_control_snapshot winner mapping disagrees")
    forced_winner_raw = _signed_int32(
        value.get("forced_winner_raw"),
        "battle_control_snapshot.forced_winner_raw",
    )
    if value.get("forced_winner_side") != _SIDE_BY_RAW.get(
        forced_winner_raw
    ):
        raise ValueError(
            "battle_control_snapshot forced-winner mapping disagrees"
        )
    finalized = _strict_bool(
        value.get("finalized"), "battle_control_snapshot.finalized"
    )
    battle_result_id = _optional_positive_int32(
        value.get("battle_result_id"),
        "battle_control_snapshot.battle_result_id",
    )
    base_combat_width = _signed_int32(
        value.get("base_combat_width"),
        "battle_control_snapshot.base_combat_width",
    )
    final_combat_width = _signed_int32(
        value.get("final_combat_width"),
        "battle_control_snapshot.final_combat_width",
    )
    roll_cadence_counter = _signed_int32(
        value.get("roll_cadence_counter"),
        "battle_control_snapshot.roll_cadence_counter",
    )
    base_advantage_raw = _signed_int64(
        value.get("base_advantage_raw"),
        "battle_control_snapshot.base_advantage_raw",
    )
    resolved_advantage_raw = _signed_int64(
        value.get("resolved_advantage_raw"),
        "battle_control_snapshot.resolved_advantage_raw",
    )

    attacker = _normalize_side(
        value.get("attacker"),
        expected_side_index=0,
        expected_role="attacker",
        combat_id=combat_id,
    )
    defender = _normalize_side(
        value.get("defender"),
        expected_side_index=1,
        expected_role="defender",
        combat_id=combat_id,
    )
    attacker_native_ids = {
        army["native_carmy_id"] for army in attacker["ordered_armies"]
    }
    defender_native_ids = {
        army["native_carmy_id"] for army in defender["ordered_armies"]
    }
    attacker_public_ids = {
        army["public_cunit_id"] for army in attacker["ordered_armies"]
    }
    defender_public_ids = {
        army["public_cunit_id"] for army in defender["ordered_armies"]
    }
    if attacker_native_ids & defender_native_ids:
        raise ValueError("battle_control_snapshot native side armies overlap")
    if attacker_public_ids & defender_public_ids:
        raise ValueError("battle_control_snapshot public side armies overlap")
    if (subject in attacker_public_ids) == (subject in defender_public_ids):
        raise ValueError(
            "battle_control_snapshot subject must occur on exactly one side"
        )
    subject_side = attacker if subject in attacker_public_ids else defender
    subject_rows = [
        army
        for army in subject_side["ordered_armies"]
        if army["public_cunit_id"] == subject
    ]
    if (
        len(subject_rows) != 1
        or subject_rows[0]["native_carmy_id"] != subject_native
    ):
        raise ValueError("battle_control_snapshot subject Army mapping disagrees")
    selected_side_index = int(subject_side["side_index"])
    selected_row = subject_rows[0]
    expected_affected_public_cunit_ids = [
        int(army["public_cunit_id"])
        for army in subject_side["ordered_armies"]
        if army["owner_character_id"] == selected_row["owner_character_id"]
    ]
    expected_unaffected_public_cunit_ids = [
        int(army["public_cunit_id"])
        for army in subject_side["ordered_armies"]
        if army["owner_character_id"] != selected_row["owner_character_id"]
    ]
    expected_scope = (
        "full_side"
        if not expected_unaffected_public_cunit_ids
        else "owner_subset"
    )
    if (
        selected_public_cunit_id != subject
        or selected_native_carmy_id != subject_native
        or selected_owner_character_id != selected_row["owner_character_id"]
        or combat_province_id != province_id
        or side_index != selected_side_index
    ):
        raise ValueError(
            "battle_control_snapshot active-retreat subject binding disagrees"
        )
    if (
        side_scope != expected_scope
        or affected_public_cunit_ids
        != expected_affected_public_cunit_ids
        or unaffected_public_cunit_ids
        != expected_unaffected_public_cunit_ids
    ):
        raise ValueError(
            "battle_control_snapshot active-retreat stored-order scope disagrees"
        )

    return {
        "schema_version": 1,
        "contract_stage": "production_exact_ongoing_combat",
        "status": "available",
        "battle_control_ready": True,
        "snapshot_revision": revision,
        "observed_date_raw": observed_date,
        "subject_public_cunit_id": subject,
        "subject_native_carmy_id": subject_native,
        "combat_id": combat_id,
        "province_id": province_id,
        "selected_public_cunit_id": selected_public_cunit_id,
        "selected_native_carmy_id": selected_native_carmy_id,
        "selected_owner_character_id": selected_owner_character_id,
        "combat_province_id": combat_province_id,
        "side_index": side_index,
        "side_scope": side_scope,
        "affected_public_cunit_ids_in_stored_order": (
            affected_public_cunit_ids
        ),
        "unaffected_same_side_public_cunit_ids_in_stored_order": (
            unaffected_public_cunit_ids
        ),
        "side_flags": side_flags,
        "legality": legality,
        "phase": _PHASE_BY_RAW[phase_raw],
        "phase_raw": phase_raw,
        "phase_day": phase_day,
        "winner_side": _SIDE_BY_RAW[winner_raw],
        "winner_raw": winner_raw,
        "forced_winner_side": _SIDE_BY_RAW[forced_winner_raw],
        "forced_winner_raw": forced_winner_raw,
        "finalized": finalized,
        "battle_result_id": battle_result_id,
        "base_combat_width": base_combat_width,
        "final_combat_width": final_combat_width,
        "roll_cadence_counter": roll_cadence_counter,
        "base_advantage_raw": base_advantage_raw,
        "resolved_advantage_raw": resolved_advantage_raw,
        "attacker": attacker,
        "defender": defender,
    }


def _normalize_active_retreat_side_flags(value: object) -> dict[str, bool]:
    name = "battle_control_snapshot.side_flags"
    if not isinstance(value, dict) or set(value) != _ACTIVE_RETREAT_SIDE_FLAG_KEYS:
        raise ValueError(f"{name} has a malformed schema")
    return {
        "disallow_retreat": _strict_bool(
            value.get("disallow_retreat"), f"{name}.disallow_retreat"
        ),
        "allow_early_retreat": _strict_bool(
            value.get("allow_early_retreat"), f"{name}.allow_early_retreat"
        ),
        "skip_pursuit": _strict_bool(
            value.get("skip_pursuit"), f"{name}.skip_pursuit"
        ),
    }


def _normalize_active_retreat_legality(
    value: object,
    *,
    expected_phase_raw: int,
    observed_date_raw: int,
    side_flags: dict[str, bool],
) -> dict[str, object]:
    name = "battle_control_snapshot.legality"
    if not isinstance(value, dict) or set(value) != _ACTIVE_RETREAT_LEGALITY_KEYS:
        raise ValueError(f"{name} has a malformed schema")
    if value.get("status") != "available":
        raise ValueError(f"{name} is unavailable")

    native_boolean = _strict_bool(
        value.get("native_boolean"), f"{name}.native_boolean"
    )
    phase_raw = _signed_int32(value.get("phase_raw"), f"{name}.phase_raw")
    phase = value.get("phase")
    if phase_raw != expected_phase_raw or phase != _PHASE_BY_RAW.get(phase_raw):
        raise ValueError(f"{name} phase mapping disagrees")
    baseline_date_raw = _signed_int32(
        value.get("retreat_elapsed_baseline_date_raw"),
        f"{name}.retreat_elapsed_baseline_date_raw",
    )
    elapsed_whole_days = _signed_int64(
        value.get("elapsed_whole_days"), f"{name}.elapsed_whole_days"
    )
    minimum_days = _signed_int32(
        value.get("minimum_elapsed_whole_days_exclusive"),
        f"{name}.minimum_elapsed_whole_days_exclusive",
    )
    if minimum_days != 14:
        raise ValueError(
            f"{name}.minimum_elapsed_whole_days_exclusive must be 14"
        )
    baseline_day_index = _retreat_day_index(baseline_date_raw)
    observed_day_index = _retreat_day_index(observed_date_raw)
    expected_elapsed_whole_days = observed_day_index - baseline_day_index
    if elapsed_whole_days != expected_elapsed_whole_days:
        raise ValueError(f"{name}.elapsed_whole_days disagrees with raw dates")
    landless_allows = _strict_bool(
        value.get("landless_gate_allows_retreat"),
        f"{name}.landless_gate_allows_retreat",
    )
    legal_now = _strict_bool(value.get("legal_now"), f"{name}.legal_now")
    reason_codes = _string_list(
        value.get("reason_codes_in_native_order"),
        f"{name}.reason_codes_in_native_order",
    )
    native_reason_keys = _string_list(
        value.get("native_reason_keys_in_native_order"),
        f"{name}.native_reason_keys_in_native_order",
    )
    expected_reason_codes: list[str] = []
    if side_flags["disallow_retreat"]:
        expected_reason_codes.append("disallowed")
    if not side_flags["allow_early_retreat"] and elapsed_whole_days <= 14:
        expected_reason_codes.append("too_early")
    if phase_raw >= 2:
        expected_reason_codes.append("pursuit_or_done")
    if not landless_allows:
        expected_reason_codes.append("landless")
    expected_native_reason_keys = [
        _ACTIVE_RETREAT_REASON_KEY_BY_CODE[code]
        for code in expected_reason_codes
    ]
    if (
        reason_codes != expected_reason_codes
        or native_reason_keys != expected_native_reason_keys
    ):
        raise ValueError(f"{name} native gate order disagrees")
    expected_legal_now = not expected_reason_codes
    if legal_now != expected_legal_now or native_boolean != expected_legal_now:
        raise ValueError(f"{name} native boolean disagrees")
    earliest_day_gate_date_raw = _signed_int64(
        value.get("earliest_day_gate_date_raw"),
        f"{name}.earliest_day_gate_date_raw",
    )
    expected_earliest_day_gate_date_raw = (
        0x029C55C0 + (baseline_day_index + minimum_days + 1) * 24
    )
    if earliest_day_gate_date_raw != expected_earliest_day_gate_date_raw:
        raise ValueError(f"{name}.earliest_day_gate_date_raw disagrees")
    return {
        "status": "available",
        "native_boolean": native_boolean,
        "phase_raw": phase_raw,
        "phase": phase,
        "retreat_elapsed_baseline_date_raw": baseline_date_raw,
        "elapsed_whole_days": elapsed_whole_days,
        "minimum_elapsed_whole_days_exclusive": 14,
        "landless_gate_allows_retreat": landless_allows,
        "legal_now": legal_now,
        "reason_codes_in_native_order": reason_codes,
        "native_reason_keys_in_native_order": native_reason_keys,
        "earliest_day_gate_date_raw": earliest_day_gate_date_raw,
    }


def _normalize_side(
    value: object,
    *,
    expected_side_index: int,
    expected_role: str,
    combat_id: int,
) -> dict[str, object]:
    name = f"battle_control_snapshot.{expected_role}"
    if not isinstance(value, dict) or set(value) != _SIDE_KEYS:
        raise ValueError(f"{name} has a malformed schema")
    side_index = _signed_int32(value.get("side_index"), f"{name}.side_index")
    role = value.get("role")
    if side_index != expected_side_index or role != expected_role:
        raise ValueError(f"{name} polarity disagrees")
    primary = _positive_int32(
        value.get("primary_participant_character_id"),
        f"{name}.primary_participant_character_id",
    )
    commander = _optional_positive_int32(
        value.get("selected_commander_character_id"),
        f"{name}.selected_commander_character_id",
    )
    current_roll = _signed_int32(
        value.get("current_roll_points"), f"{name}.current_roll_points"
    )
    armies = _normalize_armies(
        value.get("ordered_armies"), name=name, combat_id=combat_id
    )
    if not armies:
        raise ValueError(f"{name}.ordered_armies must be nonempty")
    native_army_ids = [row["native_carmy_id"] for row in armies]
    public_army_ids = [row["public_cunit_id"] for row in armies]
    if len(set(native_army_ids)) != len(native_army_ids) or len(
        set(public_army_ids)
    ) != len(public_army_ids):
        raise ValueError(f"{name}.ordered_armies contains duplicates")
    army_by_native = {row["native_carmy_id"]: row for row in armies}
    levy_entries = _normalize_entries(
        value.get("levy_entries"),
        name=f"{name}.levy_entries",
        bucket="levy",
        army_by_native=army_by_native,
    )
    men_at_arms_entries = _normalize_entries(
        value.get("men_at_arms_entries"),
        name=f"{name}.men_at_arms_entries",
        bucket="men_at_arms",
        army_by_native=army_by_native,
    )
    all_entries = levy_entries + men_at_arms_entries
    regiment_ids = [row["regiment_id"] for row in all_entries]
    if len(set(regiment_ids)) != len(regiment_ids):
        raise ValueError(f"{name} contains a duplicate retained RegimentID")

    stored_current = _signed_int64(
        value.get("stored_current_fighting_raw"),
        f"{name}.stored_current_fighting_raw",
    )
    stored_levy_current = _signed_int64(
        value.get("stored_levy_current_fighting_raw"),
        f"{name}.stored_levy_current_fighting_raw",
    )
    stored_current_matches_derived = _strict_bool(
        value.get("stored_current_matches_derived"),
        f"{name}.stored_current_matches_derived",
    )
    stored_levy_current_matches_derived = _strict_bool(
        value.get("stored_levy_current_matches_derived"),
        f"{name}.stored_levy_current_matches_derived",
    )
    derived_current = _signed_int64(
        value.get("derived_current_fighting_raw"),
        f"{name}.derived_current_fighting_raw",
    )
    derived_soft = _signed_int64(
        value.get("derived_soft_casualties_raw"),
        f"{name}.derived_soft_casualties_raw",
    )
    derived_main_hard = _signed_int64(
        value.get("derived_main_fighting_entry_hard_casualties_raw"),
        f"{name}.derived_main_fighting_entry_hard_casualties_raw",
    )
    non_main_difference = _signed_int64(
        value.get("non_main_start_minus_current_minus_soft_raw"),
        f"{name}.non_main_start_minus_current_minus_soft_raw",
    )

    expected_levy_current = _checked_sum_int64(
        (row["current_fighting_raw"] for row in levy_entries),
        f"{name}.levy current sum",
    )
    expected_current = _checked_sum_int64(
        (row["current_fighting_raw"] for row in all_entries),
        f"{name}.current sum",
    )
    expected_soft = _checked_sum_int64(
        (row["soft_casualties_raw"] for row in all_entries),
        f"{name}.soft sum",
    )
    expected_main_hard = _checked_sum_int64(
        (
            row["hard_casualties_raw"]
            for row in all_entries
            if row["hard_casualties_status"] == "available"
        ),
        f"{name}.main hard sum",
    )
    expected_non_main_difference = _checked_sum_int64(
        (
            _checked_subtract_int64(
                row["starting_raw"],
                row["current_fighting_raw"],
                row["soft_casualties_raw"],
                f"{name}.non-main difference",
            )
            for row in all_entries
            if row["hard_casualties_status"] == "unavailable"
        ),
        f"{name}.non-main difference sum",
    )
    if (
        stored_current_matches_derived != (stored_current == expected_current)
        or stored_levy_current_matches_derived
        != (stored_levy_current == expected_levy_current)
    ):
        raise ValueError(f"{name} stored-cache freshness flags disagree")
    if (
        derived_current != expected_current
        or derived_soft != expected_soft
        or derived_main_hard != expected_main_hard
        or non_main_difference != expected_non_main_difference
    ):
        raise ValueError(f"{name} retained-entry totals disagree")

    participant_hard_ledger = _normalize_participant_hard_ledger(
        value.get("participant_hard_ledger"), name=name
    )
    participant_hard_total = _signed_int64(
        value.get("participant_hard_total_raw"),
        f"{name}.participant_hard_total_raw",
    )
    if participant_hard_total != _checked_sum_int64(
        (row["hard_casualties_raw"] for row in participant_hard_ledger),
        f"{name}.participant hard sum",
    ):
        raise ValueError(f"{name} participant hard ledger total disagrees")
    side_strength_raw = _signed_int32(
        value.get("side_strength_raw"), f"{name}.side_strength_raw"
    )
    if value.get("side_strength_scale") != 100000:
        raise ValueError(f"{name}.side_strength_scale must be 100000")

    return {
        "side_index": side_index,
        "role": role,
        "primary_participant_character_id": primary,
        "selected_commander_character_id": commander,
        "current_roll_points": current_roll,
        "ordered_armies": armies,
        "levy_entries": levy_entries,
        "men_at_arms_entries": men_at_arms_entries,
        "stored_current_fighting_raw": stored_current,
        "stored_levy_current_fighting_raw": stored_levy_current,
        "stored_current_matches_derived": stored_current_matches_derived,
        "stored_levy_current_matches_derived": (
            stored_levy_current_matches_derived
        ),
        "derived_current_fighting_raw": derived_current,
        "derived_soft_casualties_raw": derived_soft,
        "derived_main_fighting_entry_hard_casualties_raw": (
            derived_main_hard
        ),
        "non_main_start_minus_current_minus_soft_raw": non_main_difference,
        "participant_hard_ledger": participant_hard_ledger,
        "participant_hard_total_raw": participant_hard_total,
        "side_strength_raw": side_strength_raw,
        "side_strength_scale": 100000,
    }


def _normalize_armies(
    value: object, *, name: str, combat_id: int
) -> list[dict[str, int]]:
    if not isinstance(value, list):
        raise ValueError(f"{name}.ordered_armies must be a list")
    result: list[dict[str, int]] = []
    for index, row in enumerate(value):
        row_name = f"{name}.ordered_armies[{index}]"
        if not isinstance(row, dict) or set(row) != _ARMY_KEYS:
            raise ValueError(f"{row_name} has a malformed schema")
        normalized = {
            "native_carmy_id": _positive_int32(
                row.get("native_carmy_id"), f"{row_name}.native_carmy_id"
            ),
            "public_cunit_id": _positive_int32(
                row.get("public_cunit_id"), f"{row_name}.public_cunit_id"
            ),
            "owner_character_id": _positive_int32(
                row.get("owner_character_id"),
                f"{row_name}.owner_character_id",
            ),
            "combat_backlink_id": _positive_int32(
                row.get("combat_backlink_id"),
                f"{row_name}.combat_backlink_id",
            ),
        }
        if normalized["combat_backlink_id"] != combat_id:
            raise ValueError(f"{row_name}.combat_backlink_id disagrees")
        result.append(normalized)
    return result


def _normalize_entries(
    value: object,
    *,
    name: str,
    bucket: str,
    army_by_native: dict[int, dict[str, int]],
) -> list[dict[str, object]]:
    if not isinstance(value, list):
        raise ValueError(f"{name} must be a list")
    result: list[dict[str, object]] = []
    for index, row in enumerate(value):
        row_name = f"{name}[{index}]"
        if not isinstance(row, dict) or set(row) != _ENTRY_KEYS:
            raise ValueError(f"{row_name} has a malformed schema")
        if row.get("bucket") != bucket or row.get("bucket_index") != index:
            raise ValueError(f"{row_name} native bucket order disagrees")
        native_carmy_id = _positive_int32(
            row.get("native_carmy_id"), f"{row_name}.native_carmy_id"
        )
        army = army_by_native.get(native_carmy_id)
        if army is None:
            raise ValueError(f"{row_name} belongs to an army on another side")
        public_cunit_id = _positive_int32(
            row.get("public_cunit_id"), f"{row_name}.public_cunit_id"
        )
        owner_character_id = _positive_int32(
            row.get("owner_character_id"), f"{row_name}.owner_character_id"
        )
        if (
            public_cunit_id != army["public_cunit_id"]
            or owner_character_id != army["owner_character_id"]
        ):
            raise ValueError(f"{row_name} Army identity mapping disagrees")
        starting = _signed_int64(
            row.get("starting_raw"), f"{row_name}.starting_raw"
        )
        current = _signed_int64(
            row.get("current_fighting_raw"),
            f"{row_name}.current_fighting_raw",
        )
        soft = _signed_int64(
            row.get("soft_casualties_raw"),
            f"{row_name}.soft_casualties_raw",
        )
        fights_in_main = _strict_bool(
            row.get("fights_in_main_phase"),
            f"{row_name}.fights_in_main_phase",
        )
        difference = _checked_subtract_int64(
            starting, current, soft, f"{row_name}.starting-current-soft"
        )
        if fights_in_main:
            hard_status = "available"
            hard_raw = _signed_int64(
                row.get("hard_casualties_raw"),
                f"{row_name}.hard_casualties_raw",
            )
            if (
                row.get("hard_casualties_status") != hard_status
                or hard_raw != difference
                or row.get("hard_casualties_source")
                != "derived_starting_minus_current_minus_soft"
                or row.get("hard_casualties_unavailable_reason") is not None
            ):
                raise ValueError(f"{row_name} main-fighting hard ledger disagrees")
            hard_source: str | None = (
                "derived_starting_minus_current_minus_soft"
            )
            hard_reason: str | None = None
        else:
            hard_status = "unavailable"
            hard_raw = None
            hard_source = None
            hard_reason = "non_main_reserve_not_distinguishable_from_hard"
            if (
                row.get("hard_casualties_status") != hard_status
                or row.get("hard_casualties_raw") is not None
                or row.get("hard_casualties_source") is not None
                or row.get("hard_casualties_unavailable_reason")
                != hard_reason
            ):
                raise ValueError(f"{row_name} non-main hard ledger disagrees")
        result.append(
            {
                "bucket": bucket,
                "bucket_index": index,
                "regiment_id": _positive_int32(
                    row.get("regiment_id"), f"{row_name}.regiment_id"
                ),
                "native_carmy_id": native_carmy_id,
                "public_cunit_id": public_cunit_id,
                "owner_character_id": owner_character_id,
                "starting_raw": starting,
                "current_fighting_raw": current,
                "soft_casualties_raw": soft,
                "fights_in_main_phase": fights_in_main,
                "hard_casualties_status": hard_status,
                "hard_casualties_raw": hard_raw,
                "hard_casualties_source": hard_source,
                "hard_casualties_unavailable_reason": hard_reason,
                "effective_max_size": _signed_int32(
                    row.get("effective_max_size"),
                    f"{row_name}.effective_max_size",
                ),
                "effective_siege_raw": _signed_int64(
                    row.get("effective_siege_raw"),
                    f"{row_name}.effective_siege_raw",
                ),
                "effective_damage_raw": _signed_int64(
                    row.get("effective_damage_raw"),
                    f"{row_name}.effective_damage_raw",
                ),
                "effective_toughness_raw": _signed_int64(
                    row.get("effective_toughness_raw"),
                    f"{row_name}.effective_toughness_raw",
                ),
                "effective_pursuit_raw": _signed_int64(
                    row.get("effective_pursuit_raw"),
                    f"{row_name}.effective_pursuit_raw",
                ),
                "effective_screen_raw": _signed_int64(
                    row.get("effective_screen_raw"),
                    f"{row_name}.effective_screen_raw",
                ),
                "entry_strength_raw": _signed_int32(
                    row.get("entry_strength_raw"),
                    f"{row_name}.entry_strength_raw",
                ),
            }
        )
    return result


def _normalize_participant_hard_ledger(
    value: object, *, name: str
) -> list[dict[str, int]]:
    if not isinstance(value, list):
        raise ValueError(f"{name}.participant_hard_ledger must be a list")
    result: list[dict[str, int]] = []
    for index, row in enumerate(value):
        row_name = f"{name}.participant_hard_ledger[{index}]"
        if not isinstance(row, dict) or set(row) != _PARTICIPANT_HARD_KEYS:
            raise ValueError(f"{row_name} has a malformed schema")
        if row.get("row_index") != index:
            raise ValueError(f"{row_name} native row order disagrees")
        result.append(
            {
                "row_index": index,
                "participant_character_id": _positive_int32(
                    row.get("participant_character_id"),
                    f"{row_name}.participant_character_id",
                ),
                "hard_casualties_raw": _signed_int64(
                    row.get("hard_casualties_raw"),
                    f"{row_name}.hard_casualties_raw",
                ),
            }
        )
    return result


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


def _signed_int64(value: object, name: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not -(2**63) <= value <= 2**63 - 1
    ):
        raise ValueError(f"{name} must be a signed int64")
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


def _retreat_day_index(date_raw: int) -> int:
    delta = date_raw - 0x029C55C0
    quotient = abs(delta) // 24
    return -quotient if delta < 0 else quotient


def _positive_int32_list(value: object, name: str) -> list[int]:
    if not isinstance(value, list):
        raise ValueError(f"{name} must be a list")
    result = [
        _positive_int32(item, f"{name}[{index}]")
        for index, item in enumerate(value)
    ]
    if len(set(result)) != len(result):
        raise ValueError(f"{name} contains duplicate IDs")
    return result


def _string_list(value: object, name: str) -> list[str]:
    if not isinstance(value, list) or any(
        not isinstance(item, str) for item in value
    ):
        raise ValueError(f"{name} must be a string list")
    return list(value)


def _strict_bool(value: object, name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be a boolean")
    return value


def _checked_subtract_int64(
    starting: int, current: int, soft: int, name: str
) -> int:
    difference = starting - current - soft
    return _signed_int64(difference, name)


def _checked_sum_int64(values: object, name: str) -> int:
    total = 0
    for value in values:
        total = _signed_int64(total + _signed_int64(value, name), name)
    return total
