"""Default-off native final realm-law read on one paused current-player frame."""

from __future__ import annotations

import uuid
from collections.abc import Mapping

from .driver import BridgeUnavailableError, UnsupportedStepError
from .nonwar_private_build import private_native_provenance


STEP = "query-realm-law-final-terms-v1-private"
SCHEMA = "realm-law-final-terms-private-read-v1"
SLOTS = (
    "gold", "prestige", "piety", "renown", "influence", "herd",
    "treasury", "treasury_or_gold", "merit", "barter_goods",
)
GROUPS = ("crown_authority", "succession_order_laws")
STATUSES = {
    "candidate_kind_rejected", "already_active", "engine_blocked", "can_enact",
}
SUCCESSION_PROFILE_STATUSES = {"available", "absent", "unavailable"}
SUCCESSION_PROFILE_KEYS = {
    "order", "traversal", "rank", "division",
    "primary_heir_minimum_share_raw", "primary_heir_minimum_share_scale",
    "create_primary_tier_titles",
}
SUCCESSION_ORDERS = {
    "inheritance", "election", "appointment", "theocratic", "company",
    "generate", "generate_from_template", "player_heir", "noble_family",
}
SUCCESSION_TRAVERSALS = {"children", "dynasty_house", "dynasty"}
SUCCESSION_RANKS = {"oldest", "youngest"}
SUCCESSION_DIVISIONS = {"single_heir", "partition"}
ROW_KEYS = {
    "law_key", "active", "final_status", "final_can_enact",
    "native_reason", "cost_raw",
}
SUCCESSION_ROW_KEYS = ROW_KEYS | {
    "succession_profile_status", "succession_profile",
}


def _valid_optional_selector(value: object, choices: set[str]) -> bool:
    # Null is the existing native optional-selector sentinel, not a guess.
    return value is None or (isinstance(value, str) and value in choices)


def _valid_succession_profile(row: Mapping[str, object]) -> bool:
    status = row["succession_profile_status"]
    profile = row["succession_profile"]
    if not isinstance(status, str) or status not in SUCCESSION_PROFILE_STATUSES:
        return False
    if status != "available":
        return profile is None
    if not isinstance(profile, dict) or set(profile) != SUCCESSION_PROFILE_KEYS:
        return False
    share = profile["primary_heir_minimum_share_raw"]
    return (
        _valid_optional_selector(profile["order"], SUCCESSION_ORDERS)
        and _valid_optional_selector(profile["traversal"], SUCCESSION_TRAVERSALS)
        and _valid_optional_selector(profile["rank"], SUCCESSION_RANKS)
        and _valid_optional_selector(profile["division"], SUCCESSION_DIVISIONS)
        and type(share) is int and -(1 << 63) <= share < (1 << 63)
        and type(profile["primary_heir_minimum_share_scale"]) is int
        and profile["primary_heir_minimum_share_scale"] == 100000
        and type(profile["create_primary_tier_titles"]) is bool
    )


COOLDOWN_FIELD = "crown_authority_cooldown"
COOLDOWN_KEYS = {
    "read_available", "present", "timed", "expiry_raw", "current_clock_raw",
    "remaining_raw", "retry_date_raw", "expiry_type", "remaining_unit",
}
COOLDOWN_EXPIRY_TYPE = "signed32_scalar_clock_counter"
COOLDOWN_REMAINING_UNIT = "scalar_clock_step_calendar_unqualified"
COOLDOWN_PROJECTED_REMAINING_UNIT = "scalar_clock_step_calendar_projected"
COOLDOWN_TURN_TICK_FIELD = "crown_authority_cooldown_turn_tick"
COOLDOWN_TURN_TICK_SOURCE = "native_variable_manager_turn_tick_context"
COOLDOWN_TURN_TICK_KEYS = {
    "source", "read_available", "manager_match_count", "manager_contains_context",
    "scalar_tail_allows_tick", "context_tick_eligible", "unavailable_reason",
}


def _signed_integer(value: object, bits: int) -> bool:
    return type(value) is int and -(1 << (bits - 1)) <= value < (1 << (bits - 1))


def normalize_crown_authority_cooldown_raw_v1(
    value: object, *, date_raw: int,
) -> dict[str, object]:
    """Retain native counter timing and an explicitly published projection."""
    if not isinstance(value, dict) or set(value) != COOLDOWN_KEYS:
        raise ValueError("crown cooldown raw object keys differ")
    if (type(value["read_available"]) is not bool
            or value["expiry_type"] != COOLDOWN_EXPIRY_TYPE
            or value["remaining_unit"] not in (
                COOLDOWN_REMAINING_UNIT, COOLDOWN_PROJECTED_REMAINING_UNIT,
            )):
        raise ValueError("crown cooldown raw type or unit differs")
    projected = value["remaining_unit"] == COOLDOWN_PROJECTED_REMAINING_UNIT
    if projected and (
        value["read_available"] is not True or value["present"] is not True
        or value["timed"] is not True
        or not _signed_integer(value["remaining_raw"], 32)
        or value["remaining_raw"] <= 0
        or not _signed_integer(value["retry_date_raw"], 32)
    ):
        raise ValueError("projected crown cooldown requires a positive timed native result")
    nullable = ("present", "timed", "expiry_raw", "current_clock_raw",
                "remaining_raw", "retry_date_raw")
    if value["read_available"] is False:
        if any(value[key] is not None for key in nullable):
            raise ValueError("unavailable crown cooldown must retain null inputs")
        return dict(value)
    if (type(value["present"]) is not bool or type(value["timed"]) is not bool
            or not _signed_integer(value["current_clock_raw"], 32)
            or not _signed_integer(value["remaining_raw"], 32)):
        raise ValueError("available crown cooldown requires native bool/int32 inputs")
    if value["present"] is False:
        if (value["timed"] is not False or value["expiry_raw"] is not None
                or value["remaining_raw"] != -1
                or not _signed_integer(value["retry_date_raw"], 64)
                or value["retry_date_raw"] != date_raw):
            raise ValueError("absent crown cooldown native result differs")
        return dict(value)
    expiry = value["expiry_raw"]
    if not _signed_integer(expiry, 32) or value["timed"] != (expiry >= 0):
        raise ValueError("present crown cooldown native expiry classification differs")
    if not projected and value["retry_date_raw"] is not None:
        raise ValueError("present raw cooldown has no qualified calendar retry date")
    if value["timed"] is False:
        if value["remaining_raw"] != -1:
            raise ValueError("untimed crown cooldown native sentinel differs")
    else:
        native_remaining = (expiry - value["current_clock_raw"]) & 0xFFFFFFFF
        if native_remaining >= 0x80000000:
            native_remaining -= 0x100000000
        if value["remaining_raw"] != native_remaining:
            raise ValueError("timed crown cooldown native signed32 remaining differs")
    return dict(value)


def normalize_crown_authority_cooldown_turn_tick_v1(
    value: object,
) -> dict[str, object]:
    """Retain current native branch inputs without predicting a future tick."""
    if not isinstance(value, dict) or set(value) != COOLDOWN_TURN_TICK_KEYS:
        raise ValueError("crown cooldown turn-tick object keys differ")
    if (value["source"] != COOLDOWN_TURN_TICK_SOURCE
            or type(value["read_available"]) is not bool):
        raise ValueError("crown cooldown turn-tick source or availability differs")
    result_keys = (
        "manager_contains_context", "scalar_tail_allows_tick", "context_tick_eligible",
    )
    if value["read_available"] is False:
        reason = value["unavailable_reason"]
        if (value["manager_match_count"] is not None
                or any(value[key] is not None for key in result_keys)
                or not isinstance(reason, str) or not reason):
            raise ValueError("unavailable crown turn-tick requires null inputs and a reason")
        return dict(value)
    count = value["manager_match_count"]
    if (type(count) is not int or not 0 <= count < (1 << 64)
            or any(type(value[key]) is not bool for key in result_keys)
            or value["unavailable_reason"] is not None):
        raise ValueError("available crown turn-tick requires uint64 count and bool inputs")
    if (value["manager_contains_context"] != (count > 0)
            or value["context_tick_eligible"] != (
                value["manager_contains_context"] and value["scalar_tail_allows_tick"]
            )):
        raise ValueError("crown turn-tick native input relationship differs")
    return dict(value)


def _valid_payload(value: object, *, revision: int, date_raw: int,
                   actor_id: int, exact_ck3_build: str) -> bool:
    if not isinstance(value, dict):
        return False
    payload_keys = {
        "schema", "snapshot_revision", "date_raw", "actor_character_id",
        "cost_scale", "cost_slots", "groups",
    }
    has_cooldown = COOLDOWN_FIELD in value
    has_turn_tick = COOLDOWN_TURN_TICK_FIELD in value
    optional_keys = ({COOLDOWN_FIELD} if has_cooldown else set()) | (
        {COOLDOWN_TURN_TICK_FIELD} if has_turn_tick else set()
    )
    if set(value) != payload_keys | optional_keys:
        return False
    cooldown = None
    turn_tick = None
    if has_cooldown:
        if exact_ck3_build != "1.20.0.4":
            return False
        try:
            cooldown = normalize_crown_authority_cooldown_raw_v1(
                value[COOLDOWN_FIELD], date_raw=date_raw,
            )
        except ValueError:
            return False
    if has_turn_tick:
        if exact_ck3_build != "1.20.0.4":
            return False
        try:
            turn_tick = normalize_crown_authority_cooldown_turn_tick_v1(
                value[COOLDOWN_TURN_TICK_FIELD],
            )
        except ValueError:
            return False
    if cooldown is not None and (
        cooldown["remaining_unit"] == COOLDOWN_PROJECTED_REMAINING_UNIT
    ):
        if (turn_tick is None or turn_tick["read_available"] is not True
                or turn_tick["manager_contains_context"] is not True
                or turn_tick["scalar_tail_allows_tick"] is not True
                or turn_tick["context_tick_eligible"] is not True):
            return False
        # The producer also proves the queried row is in the normalizer's
        # processed timed suffix. The same-query count validates its date math.
        quotient, remainder = divmod(
            cooldown["remaining_raw"], turn_tick["manager_match_count"],
        )
        steps = quotient + (remainder != 0)
        retry_bits = (date_raw + steps * 24) & 0xFFFFFFFF
        retry_raw = retry_bits if retry_bits < 0x80000000 else retry_bits - 0x100000000
        if cooldown["retry_date_raw"] != retry_raw:
            return False
    if (value["schema"] != SCHEMA or value["snapshot_revision"] != revision
            or value["date_raw"] != date_raw
            or value["actor_character_id"] != actor_id
            or value["cost_scale"] != 100000
            or value["cost_slots"] != list(SLOTS)):
        return False
    groups = value["groups"]
    if not isinstance(groups, list) or len(groups) != 2:
        return False
    for group, expected_key in zip(groups, GROUPS, strict=True):
        if not isinstance(group, dict) or set(group) != {
            "group_key", "active_law_key", "candidates",
        } or group["group_key"] != expected_key:
            return False
        rows = group["candidates"]
        if not isinstance(rows, list) or not 1 <= len(rows) <= 8:
            return False
        profile_rows = (
            exact_ck3_build in {"1.20.0.3", "1.20.0.4"}
            and expected_key == "succession_order_laws"
        )
        expected_row_keys = SUCCESSION_ROW_KEYS if profile_rows else ROW_KEYS
        keys: set[str] = set()
        active: list[str] = []
        for row in rows:
            if not isinstance(row, dict) or set(row) != expected_row_keys:
                return False
            if profile_rows and not _valid_succession_profile(row):
                return False
            key = row["law_key"]
            if not isinstance(key, str) or not key or key in keys:
                return False
            keys.add(key)
            if (type(row["active"]) is not bool
                    or not isinstance(row["final_status"], str)
                    or row["final_status"] not in STATUSES):
                return False
            if (type(row["final_can_enact"]) is not bool
                    or row["final_can_enact"] != (row["final_status"] == "can_enact")
                    or not isinstance(row["native_reason"], str)
                    or len(row["native_reason"]) > 4096):
                return False
            costs = row["cost_raw"]
            if (not isinstance(costs, list) or len(costs) != 10
                    or any(type(cost) is not int or not -(1 << 63) <= cost < (1 << 63)
                           for cost in costs)):
                return False
            if row["active"]:
                active.append(key)
                if row["final_status"] != "already_active":
                    return False
        if len(active) > 1 or group["active_law_key"] != (active[0] if active else None):
            return False
    return True


def query_realm_law_final_terms_private_v1(
    driver: object, *, expected_revision: int, timeout_seconds: float = 30.0,
) -> dict[str, object]:
    if getattr(driver, "allow_private_realm_law_paused_query", False) is not True:
        raise UnsupportedStepError("private realm-law query is disabled")
    if type(expected_revision) is not int or expected_revision <= 0:
        raise ValueError("expected_revision must be positive")
    if type(timeout_seconds) not in (int, float) or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    before = driver.take_snapshot()
    actor = before.get("played_character")
    native_revision = before.get("native_revision")
    if (before.get("revision") != expected_revision
            or before.get("paused") is not True
            or before.get("map_ready") is not True
            or not isinstance(actor, Mapping)
            or actor.get("alive") is not True
            or type(actor.get("character_id")) is not int
            or actor["character_id"] <= 0
            or type(native_revision) is not int or native_revision <= 0
            or type(before.get("date_raw")) is not int):
        raise BridgeUnavailableError("private realm-law query requires a living paused actor")
    provenance = private_native_provenance(before)
    request_id = "realm-law-read-" + uuid.uuid4().hex
    driver.endpoint.send({
        "type": "execute_step", "protocol_version": 1,
        "request_id": request_id, "step": STEP,
        "expected_revision": native_revision,
    })
    frame = driver.state.wait_for_command_result(request_id, float(timeout_seconds))
    if (not isinstance(frame, dict) or frame.get("type") != "command_result"
            or frame.get("protocol_version") != 1
            or frame.get("request_id") != request_id):
        raise BridgeUnavailableError("private realm-law command_result unavailable")
    if frame.get("ok") is not True:
        raise BridgeUnavailableError(
            "private realm-law native RED: " + str(frame.get("error", "unknown"))
        )
    envelope = frame.get("result")
    envelope_keys = {
        "step", "accepted", "status", "private_build", "read_only",
        "advertised", "realm_law_final_terms", "backend_id",
    }
    allowed_envelope_keys = (envelope_keys,)
    if provenance["exact_ck3_build"] in {"1.20.0.2", "1.20.0.3", "1.20.0.4"}:
        # The new common ReadOnlyFrame repeats the owning revision outside
        # the unchanged DTO. Legacy eight-key envelopes remain supported.
        allowed_envelope_keys += (envelope_keys | {"snapshot_revision"},)
    if (not isinstance(envelope, dict) or set(envelope) not in allowed_envelope_keys
            or ("snapshot_revision" in envelope and (
                type(envelope["snapshot_revision"]) is not int
                or envelope["snapshot_revision"] != native_revision))
            or envelope.get("step") != STEP or envelope.get("accepted") is not True
            or envelope.get("status") != "available"
            or envelope.get("private_build") is not True
            or envelope.get("read_only") is not True
            or envelope.get("advertised") is not False
            or envelope.get("backend_id") != "native-headless"
            or not _valid_payload(envelope.get("realm_law_final_terms"),
                                  revision=native_revision,
                                  date_raw=before["date_raw"],
                                  actor_id=actor["character_id"],
                                  exact_ck3_build=provenance["exact_ck3_build"])):
        raise BridgeUnavailableError("private realm-law native payload malformed")
    after = driver.take_snapshot()
    if (after.get("paused") is not True or after.get("map_ready") is not True
            or after.get("date_raw") != before["date_raw"]
            or after.get("played_character") != actor):
        raise BridgeUnavailableError("private realm-law read crossed the paused actor/date frame")
    return {
        **envelope["realm_law_final_terms"],
        **provenance,
        "queried_snapshot_id": before.get("snapshot_id"),
        "queried_revision": expected_revision,
        "queried_native_revision": native_revision,
        "post_snapshot_id": after.get("snapshot_id"),
    }
