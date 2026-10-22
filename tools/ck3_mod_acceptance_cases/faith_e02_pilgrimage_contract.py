"""Frozen native identities for the shared pilgrimage filming adapter."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

LegacyCase = Literal["faith-engine-e02-d1-ordinary-pilgrimage-v1"]
MechanismCase = Literal["faith-engine-e02-pilgrimage-mechanism-v2"]
OptionKey = Literal["pilgrimage_type_pious", "pilgrimage_type_worldly", "pilgrimage_type_hajj"]
LEGACY_CASE: LegacyCase = "faith-engine-e02-d1-ordinary-pilgrimage-v1"
MECHANISM_CASE: MechanismCase = "faith-engine-e02-pilgrimage-mechanism-v2"


@dataclass(frozen=True)
class PilgrimageIdentity:
    case: LegacyCase | MechanismCase
    actor_character_id: int
    date_raw: int
    faith_id: int
    rite_id: int | None
    option_key: OptionKey


@dataclass(frozen=True)
class PilgrimagePolicyCaps:
    max_days: int
    max_public_requests: int
    max_day_requests: int = 1024


def pilgrimage_policy_caps(case_id: object) -> PilgrimagePolicyCaps:
    if type(case_id) is not str:
        raise ValueError("pilgrimage finite policy requires an exact case string")
    if case_id == LEGACY_CASE:
        return PilgrimagePolicyCaps(max_days=366, max_public_requests=1024)
    if case_id == MECHANISM_CASE:
        return PilgrimagePolicyCaps(max_days=730, max_public_requests=4096)
    raise ValueError("unknown pilgrimage case for finite policy")


def _integer(value: object, label: str, low: int = 0) -> int:
    if type(value) is not int or not low <= value < 2**32 - 1:
        raise ValueError(label + " must be a frozen exact integer identity")
    return value


def pilgrimage_identity(value: object) -> PilgrimageIdentity:
    if not isinstance(value, Mapping):
        raise ValueError("pilgrimage contract must be an object")
    actor = _integer(value.get("expected_actor_character_id"), "actor", 1)
    date = _integer(value.get("prior_scene_date_raw"), "date", 1)
    if value.get("case") == LEGACY_CASE:
        if value.get("schema") != "faith-engine-e02-d1-ordinary-pilgrimage-case-v1":
            raise ValueError("legacy D1 contract schema differs")
        if any(key in value for key in ("option_key", "expected_faith_id", "expected_rite_id")):
            raise ValueError("legacy D1 contract cannot acquire mechanism overrides")
        return PilgrimageIdentity(LEGACY_CASE, actor, date, 13, 0, "pilgrimage_type_pious")
    if value.get("case") != MECHANISM_CASE or value.get("schema") != "faith-engine-e02-pilgrimage-mechanism-case-v2":
        raise ValueError("unknown pilgrimage case/schema")
    if not {"option_key", "expected_faith_id", "expected_rite_id"} <= value.keys():
        raise ValueError("mechanism contract requires actual faith, nullable rite and option")
    faith = _integer(value["expected_faith_id"], "faith", 1)
    raw_rite = value["expected_rite_id"]
    rite = None if raw_rite is None else _integer(raw_rite, "rite")
    key = value["option_key"]
    if key == "pilgrimage_type_pious":
        option: OptionKey = "pilgrimage_type_pious"
    elif key == "pilgrimage_type_worldly":
        option = "pilgrimage_type_worldly"
    elif key == "pilgrimage_type_hajj":
        option = "pilgrimage_type_hajj"
    else:
        raise ValueError("unsupported original pilgrimage option identity")
    return PilgrimageIdentity(MECHANISM_CASE, actor, date, faith, rite, option)


NaturalAdvanceMode = Literal["one_day", "native_horizon"]
NATURAL_HORIZON_MAX_DAYS = 30
NATURAL_HORIZON_RESERVE_HOURS = 48


def pilgrimage_natural_advance_mode(case_id: object, policy: object) -> NaturalAdvanceMode:
    pilgrimage_policy_caps(case_id)
    if not isinstance(policy, Mapping):
        raise ValueError("Pilgrimage natural-advance policy must be an object")
    if "natural_advance_mode" not in policy:
        return "one_day"
    if case_id != MECHANISM_CASE:
        raise ValueError("Legacy D1 cannot acquire a natural-advance override")
    mode = policy["natural_advance_mode"]
    if type(mode) is not str:
        raise ValueError("Natural-advance mode must be an exact string")
    if mode == "one_day":
        return "one_day"
    if mode == "native_horizon":
        return "native_horizon"
    raise ValueError("Unknown natural-advance mode")


def require_pilgrimage_natural_capabilities(value: object) -> None:
    if not isinstance(value, Mapping):
        raise ValueError("Actual natural-advance capabilities must be an object")
    for field in ("action_steps", "composite_action_steps"):
        rows = value.get(field)
        if not isinstance(rows, list) or not all(type(row) is str for row in rows):
            raise ValueError("Actual native capability list is malformed: " + field)
        if "life-advance" not in rows:
            raise ValueError("Actual shared life-advance composite is unavailable")
    if value.get("current_event_window_context_v1_query_supported") is not True:
        raise ValueError("Natural horizon requires the actual typed event observer")


@dataclass(frozen=True)
class PilgrimageNaturalInterval:
    requested_horizon_days: int
    elapsed_hours: int
    boundary: Literal["event", "interaction", "none"]
    progress_status: str

    def to_json(self) -> dict[str, object]:
        return {"requested_horizon_days": self.requested_horizon_days,
            "elapsed_hours": self.elapsed_hours, "boundary": self.boundary,
            "progress_status": self.progress_status}


def parse_pilgrimage_natural_interval(
        value: object, *, before_date_raw: int, after_date_raw: int,
        has_event: bool, has_interaction: bool, remaining_hours: int,
) -> PilgrimageNaturalInterval:
    if (type(before_date_raw) is not int or type(after_date_raw) is not int
            or type(remaining_hours) is not int or remaining_hours < 1
            or type(has_event) is not bool or type(has_interaction) is not bool):
        raise ValueError("Exact natural interval owner dates, remaining hours and boundary flags required")
    if not isinstance(value, Mapping):
        raise ValueError("Original life-advance result must be an object")
    if not {"active_event", "pending_character_interaction"} <= value.keys():
        raise ValueError("Natural interval must retain explicit nullable native boundaries")
    if (value.get("step") != "life-advance" or value.get("source") != "native-composite"
            or value.get("backend_id") != "native-headless" or value.get("paused") is not True
            or type(value.get("starting_date_raw")) is not int
            or type(value.get("ending_date_raw")) is not int
            or value["starting_date_raw"] != before_date_raw
            or value["ending_date_raw"] != after_date_raw):
        raise ValueError("Original paused natural interval dates/source differ")
    horizon = value.get("requested_horizon_days")
    if type(horizon) is not int or not 1 <= horizon <= NATURAL_HORIZON_MAX_DAYS:
        raise ValueError("Original requested natural horizon must be an exact 1..30 day integer")
    hours = after_date_raw - before_date_raw
    if (horizon * 24 > remaining_hours or not 0 <= hours <= remaining_hours
            or hours > NATURAL_HORIZON_MAX_DAYS * 24 + NATURAL_HORIZON_RESERVE_HOURS):
        raise ValueError("Original requested/actual interval crossed the finite remaining duration")
    elapsed_days = value.get("elapsed_days")
    if type(elapsed_days) is not int or elapsed_days != hours // 24:
        raise ValueError("Natural elapsed-day projection differs from the actual raw-hour interval")
    status = value.get("progress_status")
    if type(status) is not str or status not in {
            "postcondition", "modal_interrupted", "wall_timeout_with_date_progress", "boundary_interrupted"}:
        raise ValueError("Original natural progress status unavailable")
    if value.get("ordinary_events") != []:
        raise ValueError("Natural interval must leave all event choices to the shared journey")
    resolution = value.get("event_resolution")
    raw_event = value.get("active_event")
    if raw_event is not None:
        if not isinstance(raw_event, Mapping) or not has_event or resolution != "typed_query_required":
            raise ValueError("Natural interval event selection was not retained for typed drain")
    elif resolution != "none":
        raise ValueError("Natural interval reports an event outcome without its original event")
    # An event can first appear in the public after-snapshot, after the Driver
    # returned a modal-free result at this same ending date. Drain that fresh
    # window; do not invent another day or require a prior result to know it.
    raw_interaction = value["pending_character_interaction"]
    if raw_interaction is not None and (not isinstance(raw_interaction, Mapping) or not has_interaction):
        raise ValueError("Original native interaction vanished before the journey drained it")
    if status in {"modal_interrupted", "boundary_interrupted"} and not (has_event or has_interaction):
        raise ValueError("Unbound exclusive modal cannot enter another natural interval")
    if hours == 0 and not (has_event or has_interaction):
        raise ValueError("Zero-hour natural interval lacks an actual interruption")
    boundary: Literal["event", "interaction", "none"] = (
        "event" if has_event else "interaction" if has_interaction else "none")
    return PilgrimageNaturalInterval(horizon, hours, boundary, status)
