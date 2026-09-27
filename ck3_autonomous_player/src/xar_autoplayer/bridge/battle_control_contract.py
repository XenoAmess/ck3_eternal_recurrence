"""Typed contract for one exact-build ongoing CK3 battle control frame."""

from __future__ import annotations


QUERY_BATTLE_CONTROL_SNAPSHOT_V1_CAPABILITY = (
    "game.command.query-battle-control-snapshot-v1-N"
)
QUERY_BATTLE_CONTROL_SNAPSHOT_V1_STEP_PREFIX = (
    "query-battle-control-snapshot-v1-"
)
BATTLE_CONTROL_IDENTITY_PENDING_STATUS = "identity_pending"
BATTLE_CONTROL_IDENTITY_PENDING_DIAGNOSTIC = (
    "active_combat_identity_subject_combat_id_invalid"
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
_OPTIONAL_SNAPSHOT_KEYS = {
    "actual_hard_casualty_sides",
    "pursuit_modifier_sides",
    "active_counter_inputs_v1",
}
_ACTIVE_COUNTER_KEYS = {
    "schema_version", "status", "operand_census_complete", "source_combat_id",
    "source_target_province_id", "scale", "class_count", "sides", "contexts",
    "unavailable_reason",
}
_ACTIVE_COUNTER_SIDE_KEYS = {
    "side_index", "primary_owner_character_id", "counter_efficiency_raw",
    "counter_resistance_raw", "men_at_arms_entries",
}
_ACTIVE_COUNTER_ENTRY_KEYS = {
    "bucket_index", "regiment_id", "native_carmy_id", "current_fighting_raw",
    "status", "class_index", "stack_size_soldiers", "current_chunk_raw",
    "targets",
}
_ACTIVE_COUNTER_TARGET_KEYS = {"class_index", "effectiveness_raw"}
_ACTIVE_COUNTER_CONTEXT_KEYS = {
    "countered_side_index", "countering_side_index",
    "countered_primary_owner_character_id", "countering_primary_owner_character_id",
    "context_scale_raw",
}
_ACTIVE_RESUME_KEYS = {
    "schema_version",
    "status",
    "input_observation_ready",
    "unavailable_reason",
    "missing_required_domains",
    "source",
    "observed",
}
_ACTIVE_RESUME_SOURCE_KEYS = {
    "snapshot_revision",
    "observed_date_raw",
    "subject_public_cunit_id",
    "subject_native_carmy_id",
    "combat_id",
    "province_id",
}
_ACTIVE_RESUME_OBSERVED_KEYS = {
    "phase",
    "phase_day",
    "elapsed_whole_days",
    "roll_cadence_counter",
    "final_combat_width",
    "side_0_current_roll_points",
    "side_1_current_roll_points",
    "side_0_selected_commander_character_id",
    "side_1_selected_commander_character_id",
    "side_0_selected_commander_next_roll_bounds",
    "side_1_selected_commander_next_roll_bounds",
    "side_0_ordered_public_cunit_ids",
    "side_1_ordered_public_cunit_ids",
    "side_0_entry_count",
    "side_1_entry_count",
}
_ACTIVE_RESUME_OBSERVED_KEYS_WITH_MAPPING = _ACTIVE_RESUME_OBSERVED_KEYS | {
    "battle_side_mapping"
}
_ACTIVE_RESUME_OBSERVED_KEYS_WITH_COUNTER = _ACTIVE_RESUME_OBSERVED_KEYS | {
    "active_counter_inputs_v1"
}
_ACTIVE_RESUME_OBSERVED_KEYS_WITH_MAPPING_AND_COUNTER = (
    _ACTIVE_RESUME_OBSERVED_KEYS_WITH_MAPPING | {"active_counter_inputs_v1"}
)
_ACTIVE_RESUME_BATTLE_SIDE_MAPPING_KEYS = {
    "status",
    "subject_side_index",
    "opposing_side_index",
    "subject_owner_character_id",
    "side_scope",
    "same_side_public_cunit_ids_in_stored_order",
    "opposing_side_public_cunit_ids_in_stored_order",
    "affected_public_cunit_ids_in_stored_order",
    "unaffected_same_side_public_cunit_ids_in_stored_order",
}
_ACTUAL_HARD_KEYS = {
    "status",
    "source_combat_id",
    "source_target_province_id",
    "scale",
    "sides",
    "unavailable_reason",
}
_ACTUAL_HARD_SIDE_KEYS = {
    "side_index",
    "encounter_role",
    "ordered_army_ids",
    "commander_character_id",
    "own_modifier_raw",
    "enemy_modifier_raw",
}
_PURSUIT_MODIFIER_KEYS = _ACTUAL_HARD_KEYS
_PURSUIT_MODIFIER_SIDE_KEYS = {
    "side_index",
    "encounter_role",
    "pursuit_efficiency_raw",
    "retreat_losses_raw",
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
_SIDE_KEYS_WITH_TERMINAL_BASELINE = _SIDE_KEYS | {
    "stored_terminal_loss_baseline_raw"
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
    if (
        not isinstance(value, dict)
        or not _SNAPSHOT_KEYS <= set(value)
        or set(value) - _SNAPSHOT_KEYS - _OPTIONAL_SNAPSHOT_KEYS
    ):
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

    combat_id = _full_component_id(
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
    battle_result_id = _optional_full_component_id(
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

    actual_hard = None
    if "actual_hard_casualty_sides" in value:
        actual_hard = _normalize_actual_hard_sides(
            value["actual_hard_casualty_sides"],
            combat_id=combat_id,
            province_id=province_id,
            attacker=attacker,
            defender=defender,
        )
    pursuit_modifiers = None
    if "pursuit_modifier_sides" in value:
        pursuit_modifiers = _normalize_pursuit_modifier_sides(
            value["pursuit_modifier_sides"],
            combat_id=combat_id,
            province_id=province_id,
        )
    active_counter = None
    if "active_counter_inputs_v1" in value:
        active_counter = _normalize_active_counter_inputs_v1(
            value["active_counter_inputs_v1"],
            combat_id=combat_id,
            province_id=province_id,
            attacker=attacker,
            defender=defender,
        )

    result = {
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
    if actual_hard is not None:
        result["actual_hard_casualty_sides"] = actual_hard
    if pursuit_modifiers is not None:
        result["pursuit_modifier_sides"] = pursuit_modifiers
    if active_counter is not None:
        result["active_counter_inputs_v1"] = active_counter
    return result


def _normalize_active_counter_inputs_v1(
    value: object, *, combat_id: int, province_id: int,
    attacker: dict[str, object], defender: dict[str, object],
) -> dict[str, object]:
    """Admit only a complete same-battle counter operand census.

    This current-frame observation never grants resumed-trial readiness.
    """
    name = "battle_control_snapshot.active_counter_inputs_v1"
    if not isinstance(value, dict) or set(value) != _ACTIVE_COUNTER_KEYS:
        raise ValueError(f"{name} has a malformed schema")
    if value["schema_version"] != 1 or isinstance(value["schema_version"], bool):
        raise ValueError(f"{name} has an invalid version")
    if (
        _full_component_id(value["source_combat_id"], f"{name}.source_combat_id")
        != combat_id
        or _positive_int32(
            value["source_target_province_id"],
            f"{name}.source_target_province_id",
        ) != province_id
        or value["scale"] != 100_000
        or isinstance(value["scale"], bool)
    ):
        raise ValueError(f"{name} identity or scale disagrees")
    if value["status"] == "unavailable":
        if (
            value["operand_census_complete"] is not False
            or value["class_count"] is not None
            or value["sides"] is not None
            or value["contexts"] is not None
            or not isinstance(value["unavailable_reason"], str)
            or not value["unavailable_reason"]
        ):
            raise ValueError(f"{name} unavailable result contains partial operands")
        return dict(value)
    if (
        value["status"] != "available"
        or value["operand_census_complete"] is not True
        or value["unavailable_reason"] is not None
    ):
        raise ValueError(f"{name} claims an incomplete operand census")
    class_count = _positive_int32(value["class_count"], f"{name}.class_count")
    if class_count > 4096:
        raise ValueError(f"{name}.class_count exceeds the native bound")
    sides = value["sides"]
    contexts = value["contexts"]
    if not isinstance(sides, list) or len(sides) != 2:
        raise ValueError(f"{name} requires two actual sides")
    if not isinstance(contexts, list) or len(contexts) != 2:
        raise ValueError(f"{name} requires two directional contexts")
    parents = (attacker, defender)
    normalized_sides: list[dict[str, object]] = []
    for index, (side, parent) in enumerate(zip(sides, parents, strict=True)):
        side_name = f"{name}.sides[{index}]"
        if not isinstance(side, dict) or set(side) != _ACTIVE_COUNTER_SIDE_KEYS:
            raise ValueError(f"{side_name} has a malformed schema")
        if (
            _signed_int32(side["side_index"], f"{side_name}.side_index") != index
            or _positive_int32(
                side["primary_owner_character_id"],
                f"{side_name}.primary_owner_character_id",
            ) != parent["primary_participant_character_id"]
        ):
            raise ValueError(f"{side_name} does not match the actual side")
        entries = side["men_at_arms_entries"]
        source_entries = parent["men_at_arms_entries"]
        if not isinstance(entries, list) or len(entries) != len(source_entries):
            raise ValueError(f"{side_name} has an incomplete MAA census")
        normalized_entries: list[dict[str, object]] = []
        for entry_index, (entry, source) in enumerate(
            zip(entries, source_entries, strict=True)
        ):
            entry_name = f"{side_name}.men_at_arms_entries[{entry_index}]"
            if not isinstance(entry, dict) or set(entry) != _ACTIVE_COUNTER_ENTRY_KEYS:
                raise ValueError(f"{entry_name} has a malformed schema")
            for key, checker in (
                ("bucket_index", _signed_int32),
                ("regiment_id", _full_component_id),
                ("native_carmy_id", _full_component_id),
                ("current_fighting_raw", _signed_int64),
            ):
                if checker(entry[key], f"{entry_name}.{key}") != source[key]:
                    raise ValueError(f"{entry_name}.{key} disagrees with battle entry")
            if entry["status"] == "absent":
                if any(
                    entry[key] is not None
                    for key in ("class_index", "stack_size_soldiers", "current_chunk_raw")
                ) or entry["targets"] != []:
                    raise ValueError(f"{entry_name} has malformed absent operands")
            elif entry["status"] == "available":
                class_index = _signed_int32(
                    entry["class_index"], f"{entry_name}.class_index"
                )
                stack = _positive_int32(
                    entry["stack_size_soldiers"],
                    f"{entry_name}.stack_size_soldiers",
                )
                chunk = _signed_int64(
                    entry["current_chunk_raw"],
                    f"{entry_name}.current_chunk_raw",
                )
                if (
                    not 0 <= class_index < class_count
                    or chunk < 0
                    or chunk != source["current_fighting_raw"] // stack
                ):
                    raise ValueError(f"{entry_name} native chunk or class disagrees")
                targets = entry["targets"]
                if not isinstance(targets, list) or len(targets) > 4096:
                    raise ValueError(f"{entry_name} target list is malformed")
                for target_index, target in enumerate(targets):
                    target_name = f"{entry_name}.targets[{target_index}]"
                    if not isinstance(target, dict) or set(target) != _ACTIVE_COUNTER_TARGET_KEYS:
                        raise ValueError(f"{target_name} has a malformed schema")
                    target_class = _signed_int32(
                        target["class_index"], f"{target_name}.class_index"
                    )
                    _signed_int64(
                        target["effectiveness_raw"],
                        f"{target_name}.effectiveness_raw",
                    )
                    if not 0 <= target_class < class_count:
                        raise ValueError(f"{target_name} class is outside the native table")
            else:
                raise ValueError(f"{entry_name} status is unavailable")
            normalized_entries.append(dict(entry))
        normalized_sides.append({
            **side,
            "counter_efficiency_raw": _signed_int64(
                side["counter_efficiency_raw"],
                f"{side_name}.counter_efficiency_raw",
            ),
            "counter_resistance_raw": _signed_int64(
                side["counter_resistance_raw"],
                f"{side_name}.counter_resistance_raw",
            ),
            "men_at_arms_entries": normalized_entries,
        })
    normalized_contexts: list[dict[str, object]] = []
    for index, context in enumerate(contexts):
        context_name = f"{name}.contexts[{index}]"
        if not isinstance(context, dict) or set(context) != _ACTIVE_COUNTER_CONTEXT_KEYS:
            raise ValueError(f"{context_name} has a malformed schema")
        if (
            _signed_int32(context["countered_side_index"],
                          f"{context_name}.countered_side_index") != index
            or _signed_int32(context["countering_side_index"],
                             f"{context_name}.countering_side_index") != 1 - index
            or _positive_int32(
                context["countered_primary_owner_character_id"],
                f"{context_name}.countered_primary_owner_character_id",
            ) != normalized_sides[index]["primary_owner_character_id"]
            or _positive_int32(
                context["countering_primary_owner_character_id"],
                f"{context_name}.countering_primary_owner_character_id",
            ) != normalized_sides[1 - index]["primary_owner_character_id"]
            or _signed_int64(
                context["context_scale_raw"], f"{context_name}.context_scale_raw"
            ) < 0
        ):
            raise ValueError(f"{context_name} does not match the actual sides")
        normalized_contexts.append(dict(context))
    return {**value, "sides": normalized_sides, "contexts": normalized_contexts}


def normalize_active_combat_resume_inputs_v1(
    value: object, *, parent: dict[str, object]
) -> dict[str, object]:
    """Validate the same-sample observation without granting resume readiness.

    V1 intentionally has no available form: the native producer reports the
    observed battle state and explicit missing operands. A future complete
    producer must introduce and validate its full operator census before a
    planner may construct ``ActiveMainResumeState``.
    """
    name = "battle_control_snapshot.active_combat_resume_inputs_v1"
    if not isinstance(value, dict) or set(value) != _ACTIVE_RESUME_KEYS:
        raise ValueError(f"{name} has a malformed schema")
    if (
        value["schema_version"] != 1
        or isinstance(value["schema_version"], bool)
        or value["status"] != "unavailable"
        or value["input_observation_ready"] is not False
        or value["unavailable_reason"]
        != "same_frame_resume_operands_incomplete"
    ):
        raise ValueError(f"{name} cannot claim complete active-combat inputs")
    missing = value["missing_required_domains"]
    if (
        not isinstance(missing, list)
        or not missing
        or any(not isinstance(item, str) or not item for item in missing)
        or len(set(missing)) != len(missing)
    ):
        raise ValueError(f"{name} missing domains are malformed")

    source = value["source"]
    if not isinstance(source, dict) or set(source) != _ACTIVE_RESUME_SOURCE_KEYS:
        raise ValueError(f"{name}.source has a malformed schema")
    source_checks = {
        "snapshot_revision": _positive_uint64,
        "observed_date_raw": _signed_int64,
        "subject_public_cunit_id": _positive_int32,
        "subject_native_carmy_id": _positive_int32,
        "combat_id": _full_component_id,
        "province_id": _positive_int32,
    }
    for key, check in source_checks.items():
        actual = check(source[key], f"{name}.source.{key}")
        if actual != parent[key]:
            raise ValueError(f"{name}.source.{key} disagrees with battle frame")

    observed = value["observed"]
    if not isinstance(observed, dict) or set(observed) not in (
        _ACTIVE_RESUME_OBSERVED_KEYS,
        _ACTIVE_RESUME_OBSERVED_KEYS_WITH_MAPPING,
        _ACTIVE_RESUME_OBSERVED_KEYS_WITH_COUNTER,
        _ACTIVE_RESUME_OBSERVED_KEYS_WITH_MAPPING_AND_COUNTER,
    ):
        raise ValueError(f"{name}.observed has a malformed schema")
    if observed["phase"] != parent["phase"]:
        raise ValueError(f"{name}.observed.phase disagrees with battle frame")
    integer_checks = {
        "phase_day": (parent["phase_day"], _signed_int32),
        "elapsed_whole_days": (parent["legality"]["elapsed_whole_days"], _signed_int32),
        "roll_cadence_counter": (parent["roll_cadence_counter"], _signed_int32),
        "final_combat_width": (parent["final_combat_width"], _signed_int32),
        "side_0_current_roll_points": (parent["attacker"]["current_roll_points"], _signed_int32),
        "side_1_current_roll_points": (parent["defender"]["current_roll_points"], _signed_int32),
        "side_0_entry_count": (
            len(parent["attacker"]["levy_entries"])
            + len(parent["attacker"]["men_at_arms_entries"]),
            _signed_int32,
        ),
        "side_1_entry_count": (
            len(parent["defender"]["levy_entries"])
            + len(parent["defender"]["men_at_arms_entries"]),
            _signed_int32,
        ),
    }
    for key, (expected, check) in integer_checks.items():
        actual = check(observed[key], f"{name}.observed.{key}")
        if actual != expected:
            raise ValueError(f"{name}.observed.{key} disagrees with battle frame")
    for index, role in enumerate(("attacker", "defender")):
        commander_key = f"side_{index}_selected_commander_character_id"
        commander = _optional_positive_int32(
            observed[commander_key], f"{name}.observed.{commander_key}"
        )
        if commander != parent[role]["selected_commander_character_id"]:
            raise ValueError(f"{name}.observed.{commander_key} disagrees")
        bounds_key = f"side_{index}_selected_commander_next_roll_bounds"
        bounds = observed[bounds_key]
        bounds_name = f"{name}.observed.{bounds_key}"
        if not isinstance(bounds, dict) or set(bounds) != {
            "status", "effective_min_roll", "effective_max_roll",
            "unavailable_reason",
        }:
            raise ValueError(f"{bounds_name} has a malformed schema")
        if bounds["status"] == "available":
            _signed_int32(bounds["effective_min_roll"], f"{bounds_name}.effective_min_roll")
            _signed_int32(bounds["effective_max_roll"], f"{bounds_name}.effective_max_roll")
            if bounds["unavailable_reason"] is not None:
                raise ValueError(f"{bounds_name} available result has a reason")
        elif bounds["status"] == "unavailable":
            if (
                bounds["effective_min_roll"] is not None
                or bounds["effective_max_roll"] is not None
                or not isinstance(bounds["unavailable_reason"], str)
                or not bounds["unavailable_reason"]
            ):
                raise ValueError(f"{bounds_name} unavailable result has endpoints")
        else:
            raise ValueError(f"{bounds_name} has an invalid status")
        armies_key = f"side_{index}_ordered_public_cunit_ids"
        armies = _positive_int32_list(
            observed[armies_key], f"{name}.observed.{armies_key}"
        )
        expected_armies = [
            army["public_cunit_id"] for army in parent[role]["ordered_armies"]
        ]
        if armies != expected_armies:
            raise ValueError(f"{name}.observed.{armies_key} disagrees")
    both_bounds_available = all(
        observed[f"side_{index}_selected_commander_next_roll_bounds"]["status"]
        == "available" for index in (0, 1)
    )
    if ("selected_commander_next_roll_bounds" in missing) == both_bounds_available:
        raise ValueError(f"{name} roll bounds completeness disagrees")
    has_mapping = "battle_side_mapping" in observed
    if has_mapping == ("active_coalition_side_mapping" in missing):
        raise ValueError(f"{name} coalition side mapping completeness disagrees")
    if has_mapping:
        mapping = observed["battle_side_mapping"]
        mapping_name = f"{name}.observed.battle_side_mapping"
        if not isinstance(mapping, dict) or set(mapping) != _ACTIVE_RESUME_BATTLE_SIDE_MAPPING_KEYS:
            raise ValueError(f"{mapping_name} has a malformed schema")
        if mapping["status"] != "available":
            raise ValueError(f"{mapping_name} cannot claim unavailable operands")
        subject_side_index = _signed_int32(
            mapping["subject_side_index"], f"{mapping_name}.subject_side_index"
        )
        opposing_side_index = _signed_int32(
            mapping["opposing_side_index"], f"{mapping_name}.opposing_side_index"
        )
        owner = _positive_int32(
            mapping["subject_owner_character_id"],
            f"{mapping_name}.subject_owner_character_id",
        )
        if (
            subject_side_index != parent["side_index"]
            or opposing_side_index != 1 - subject_side_index
            or owner != parent["selected_owner_character_id"]
            or mapping["side_scope"] != parent["side_scope"]
        ):
            raise ValueError(f"{mapping_name} subject binding disagrees")
        same = parent["attacker" if subject_side_index == 0 else "defender"]
        opposing = parent["defender" if subject_side_index == 0 else "attacker"]
        expected_lists = {
            "same_side_public_cunit_ids_in_stored_order": [
                army["public_cunit_id"] for army in same["ordered_armies"]
            ],
            "opposing_side_public_cunit_ids_in_stored_order": [
                army["public_cunit_id"] for army in opposing["ordered_armies"]
            ],
            "affected_public_cunit_ids_in_stored_order": parent[
                "affected_public_cunit_ids_in_stored_order"
            ],
            "unaffected_same_side_public_cunit_ids_in_stored_order": parent[
                "unaffected_same_side_public_cunit_ids_in_stored_order"
            ],
        }
        for key, expected in expected_lists.items():
            actual = _positive_int32_list(mapping[key], f"{mapping_name}.{key}")
            if actual != expected:
                raise ValueError(f"{mapping_name}.{key} disagrees with battle frame")
    has_counter = "active_counter_inputs_v1" in observed
    if has_counter:
        parent_counter = parent.get("active_counter_inputs_v1")
        if not isinstance(parent_counter, dict) or observed["active_counter_inputs_v1"] != parent_counter:
            raise ValueError(f"{name}.observed.active_counter_inputs_v1 disagrees with battle frame")
    # This copies a current-frame census only. Its next-day retention and
    # dynamic-entry transition have not been validated against the native call.
    if "active_regiment_counter_class_stack_context" not in missing:
        raise ValueError(f"{name} next-day counter domain is not complete")
    return {
        "schema_version": 1,
        "status": "unavailable",
        "input_observation_ready": False,
        "unavailable_reason": "same_frame_resume_operands_incomplete",
        "missing_required_domains": list(missing),
        "source": dict(source),
        "observed": dict(observed),
    }


def _normalize_actual_hard_sides(
    value: object,
    *,
    combat_id: int,
    province_id: int,
    attacker: dict[str, object],
    defender: dict[str, object],
) -> dict[str, object]:
    name = "battle_control_snapshot.actual_hard_casualty_sides"
    if not isinstance(value, dict) or set(value) != _ACTUAL_HARD_KEYS:
        raise ValueError(f"{name} has a malformed schema")
    source_combat_id = _full_component_id(
        value["source_combat_id"], f"{name}.source_combat_id"
    )
    source_province_id = _positive_int32(
        value["source_target_province_id"],
        f"{name}.source_target_province_id",
    )
    if (
        source_combat_id != combat_id
        or source_province_id != province_id
        or value["scale"] != 100_000
        or isinstance(value["scale"], bool)
    ):
        raise ValueError(f"{name} identity or scale disagrees")
    status = value["status"]
    if status == "unavailable":
        reason = value["unavailable_reason"]
        if value["sides"] is not None or not isinstance(reason, str) or not reason:
            raise ValueError(f"{name} unavailable result has raw sides")
        return dict(value)
    if status != "available" or value["unavailable_reason"] is not None:
        raise ValueError(f"{name} status disagrees")
    sides = value["sides"]
    if not isinstance(sides, list) or len(sides) != 2:
        raise ValueError(f"{name} requires both actual sides")
    normalized_sides = []
    for index, (row, battle_side) in enumerate(
        zip(sides, (attacker, defender), strict=True)
    ):
        row_name = f"{name}.sides[{index}]"
        if not isinstance(row, dict) or set(row) != _ACTUAL_HARD_SIDE_KEYS:
            raise ValueError(f"{row_name} has a malformed schema")
        side_index = _signed_int32(row["side_index"], f"{row_name}.side_index")
        role = "attacker" if index == 0 else "defender"
        commander = _signed_int32(
            row["commander_character_id"],
            f"{row_name}.commander_character_id",
        )
        army_ids = _positive_int32_list(
            row["ordered_army_ids"], f"{row_name}.ordered_army_ids"
        )
        expected_army_ids = [
            army["public_cunit_id"] for army in battle_side["ordered_armies"]
        ]
        expected_commander = (
            battle_side["selected_commander_character_id"] or -1
        )
        if (
            side_index != index
            or row["encounter_role"] != role
            or commander != expected_commander
            or army_ids != expected_army_ids
        ):
            raise ValueError(f"{row_name} actual CCombat identity disagrees")
        normalized_sides.append(
            {
                "side_index": side_index,
                "encounter_role": role,
                "ordered_army_ids": army_ids,
                "commander_character_id": commander,
                "own_modifier_raw": _signed_int64(
                    row["own_modifier_raw"], f"{row_name}.own_modifier_raw"
                ),
                "enemy_modifier_raw": _signed_int64(
                    row["enemy_modifier_raw"], f"{row_name}.enemy_modifier_raw"
                ),
            }
        )
    return {
        "status": "available",
        "source_combat_id": source_combat_id,
        "source_target_province_id": source_province_id,
        "scale": 100_000,
        "sides": normalized_sides,
        "unavailable_reason": None,
    }


def _normalize_pursuit_modifier_sides(
    value: object, *, combat_id: int, province_id: int
) -> dict[str, object]:
    name = "battle_control_snapshot.pursuit_modifier_sides"
    if not isinstance(value, dict) or set(value) != _PURSUIT_MODIFIER_KEYS:
        raise ValueError(f"{name} has a malformed schema")
    source_combat_id = _full_component_id(
        value["source_combat_id"], f"{name}.source_combat_id"
    )
    source_province_id = _positive_int32(
        value["source_target_province_id"], f"{name}.source_target_province_id"
    )
    if (
        source_combat_id != combat_id
        or source_province_id != province_id
        or value["scale"] != 100_000
        or isinstance(value["scale"], bool)
    ):
        raise ValueError(f"{name} identity or scale disagrees")
    status = value["status"]
    if status == "unavailable":
        reason = value["unavailable_reason"]
        if value["sides"] is not None or not isinstance(reason, str) or not reason:
            raise ValueError(f"{name} unavailable result has raw sides")
        return dict(value)
    if status != "available" or value["unavailable_reason"] is not None:
        raise ValueError(f"{name} status disagrees")
    sides = value["sides"]
    if not isinstance(sides, list) or len(sides) != 2:
        raise ValueError(f"{name} requires both actual sides")
    normalized_sides = []
    for index, row in enumerate(sides):
        row_name = f"{name}.sides[{index}]"
        if not isinstance(row, dict) or set(row) != _PURSUIT_MODIFIER_SIDE_KEYS:
            raise ValueError(f"{row_name} has a malformed schema")
        side_index = _signed_int32(row["side_index"], f"{row_name}.side_index")
        role = "attacker" if index == 0 else "defender"
        if side_index != index or row["encounter_role"] != role:
            raise ValueError(f"{row_name} actual CCombat side disagrees")
        normalized_sides.append(
            {
                "side_index": side_index,
                "encounter_role": role,
                "pursuit_efficiency_raw": _signed_int64(
                    row["pursuit_efficiency_raw"],
                    f"{row_name}.pursuit_efficiency_raw",
                ),
                "retreat_losses_raw": _signed_int64(
                    row["retreat_losses_raw"],
                    f"{row_name}.retreat_losses_raw",
                ),
            }
        )
    return {
        "status": "available",
        "source_combat_id": source_combat_id,
        "source_target_province_id": source_province_id,
        "scale": 100_000,
        "sides": normalized_sides,
        "unavailable_reason": None,
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
    if not isinstance(value, dict) or set(value) not in (
        _SIDE_KEYS,
        _SIDE_KEYS_WITH_TERMINAL_BASELINE,
    ):
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
    stored_terminal_baseline = (
        _signed_int64(
            value["stored_terminal_loss_baseline_raw"],
            f"{name}.stored_terminal_loss_baseline_raw",
        )
        if "stored_terminal_loss_baseline_raw" in value
        else None
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

    normalized = {
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
    if stored_terminal_baseline is not None:
        normalized["stored_terminal_loss_baseline_raw"] = stored_terminal_baseline
    return normalized


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
            "combat_backlink_id": _full_component_id(
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


def _full_component_id(value: object, name: str) -> int:
    result = _signed_int32(value, name)
    if result == -1:
        raise ValueError(f"{name} must not be the missing-ID sentinel")
    return result


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


def _optional_full_component_id(value: object, name: str) -> int | None:
    return None if value is None else _full_component_id(value, name)


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
