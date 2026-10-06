"""Current-player native mercenary candidates, independent hire terms and location."""
from __future__ import annotations

from collections.abc import Mapping
from .timeline_blocker_private_transport import _binding
from .nonwar_private_build import private_native_build_identity
from .version_identity import CK3_12003, CK3_12004, require_exact_native_build

STEP = "query-player-mercenary-context-v1"
CAPABILITY = "game.command." + STEP
SCHEMA = "ck3_12003_player_mercenary_context_v1"
_SCHEMAS_BY_BUILD = {
    CK3_12003: SCHEMA,
    CK3_12004: "ck3_12004_player_mercenary_context_v1",
}


def player_mercenary_context_frame_binding(snapshot: Mapping[str, object]) -> tuple[object, ...]:
    return _binding(snapshot)


def _integer(value: object, minimum: int, maximum: int, name: str, *, nullable: bool = False) -> None:
    if value is None and nullable:
        return
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"native mercenary {name} is malformed")


def _availability(value: Mapping[str, object], name: str) -> bool:
    ready = value.get("available")
    reason = value.get("unavailable_reason")
    if (type(ready) is not bool
            or ready and reason is not None
            or not ready and (not isinstance(reason, str) or not reason)):
        raise ValueError(f"native mercenary {name} availability is malformed")
    return ready


def _terms(value: object) -> None:
    if not isinstance(value, Mapping):
        raise ValueError("native mercenary final terms are malformed")
    ready = _availability(value, "final terms")
    for name in ("can_hire", "can_afford"):
        flag = value.get(name)
        if not (type(flag) is bool or flag is None and not ready):
            raise ValueError(f"native mercenary {name} is malformed")
    payment = value.get("payment_status")
    if not (type(payment) is int and payment in (0, 1, 2) or payment is None and not ready):
        raise ValueError("native mercenary native payment status is malformed")
    scale = value.get("resource_scale")
    if type(scale) is not int or scale != 100000:
        raise ValueError("native mercenary resource scale is malformed")
    costs = value.get("resource_costs_raw")
    if costs is not None:
        if (not isinstance(costs, list) or len(costs) != 10
                or any(type(raw) is not int or not -(2**63) <= raw <= 2**63-1 for raw in costs)):
            raise ValueError("native mercenary ten-resource costs are malformed")
    elif ready:
        raise ValueError("native mercenary available final terms lost costs")
    _integer(value.get("hire_duration_months"), 0, 2**63-1, "duration", nullable=True)
    for prefix in ("can_hire", "can_afford"):
        sampled = value.get(prefix + "_reasons_available")
        literal = value.get(prefix + "_reason_literal")
        if (type(sampled) is not bool or sampled and not isinstance(literal, str)
                or not sampled and literal is not None or ready and not sampled):
            raise ValueError(f"native mercenary {prefix} source reason is malformed")
    # Native payment_status=1 permits debt. Preserve it and the independent
    # CanAfford answer; do not turn CanAfford=false into a CanHire rejection.


def _strength(value: object) -> None:
    if not isinstance(value, Mapping):
        raise ValueError("native mercenary current troop strength is malformed")
    ready = _availability(value, "troop strength")
    soldiers = value.get("current_soldiers")
    if ready:
        _integer(soldiers, 0, 2**31-1, "current soldiers")
    elif soldiers is not None:
        raise ValueError("native mercenary unavailable current soldiers is malformed")



def _composition(value: object, company_id: object) -> bool:
    if not isinstance(value, Mapping):
        raise ValueError("native mercenary composition is malformed")
    ready = _availability(value, "composition")
    _integer(value.get("company_id"), 0, 2**32-1, "composition company full ID")
    if value["company_id"] != company_id:
        raise ValueError("native mercenary composition differs from candidate company")
    holder_ready = value.get("holder_available")
    holder_reason = value.get("holder_unavailable_reason")
    if (type(holder_ready) is not bool
            or holder_ready and holder_reason is not None
            or not holder_ready and (not isinstance(holder_reason, str) or not holder_reason)):
        raise ValueError("native mercenary holder availability is malformed")
    _integer(value.get("holder_character_id"), 0, 2**32-1, "holder full ID",
             nullable=not holder_ready)
    if not holder_ready and value.get("holder_character_id") is not None:
        raise ValueError("native mercenary unavailable holder ID is malformed")
    # Holder and current employer are separate native identities.
    _integer(value.get("regiment_count"), 0, 2**32-1, "regiment count",
             nullable=not ready)
    _integer(value.get("covered_regiment_count"), 0, 2**32-1, "covered regiment count")
    for name in ("current_regiment_soldiers", "maximum_regiment_soldiers",
                 "positive_siege_tier_current_soldiers"):
        _integer(value.get(name), 0, 2**63-1, name, nullable=not ready)
        if not ready and value.get(name) is not None:
            raise ValueError("native mercenary incomplete composition has aggregate soldiers")
    _integer(value.get("maximum_siege_tier_raw"), 0, 2**31-1,
             "maximum company siege tier", nullable=not ready)
    if not ready and value.get("maximum_siege_tier_raw") is not None:
        raise ValueError("native mercenary incomplete composition has aggregate siege tier")
    regiments = value.get("regiments")
    if not isinstance(regiments, list) or len(regiments) != value["covered_regiment_count"]:
        raise ValueError("native mercenary covered regiment collection is malformed")
    if ready and value["covered_regiment_count"] != value["regiment_count"]:
        raise ValueError("native mercenary complete composition lost regiments")
    for regiment in regiments:
        if not isinstance(regiment, Mapping):
            raise ValueError("native mercenary regiment row is malformed")
        _integer(regiment.get("ordinal"), 0, 2**32-1, "regiment ordinal")
        _integer(regiment.get("persistent_regiment_id"), 0, 2**32-1,
                 "persistent regiment full ID")
        for name in ("current_soldiers", "maximum_soldiers"):
            _integer(regiment.get(name), 0, 2**31-1, name)
        status = regiment.get("type_status")
        key = regiment.get("maa_type_key")
        tier = regiment.get("siege_tier_raw")
        if status == "available":
            if not isinstance(key, str) or not key:
                raise ValueError("native mercenary regiment type key is malformed")
            _integer(tier, -(2**31), 2**31-1, "signed regiment siege tier")
        elif status == "not_maa":
            if key is not None or tier is not None:
                raise ValueError("native mercenary non-MAA regiment invented type values")
        else:
            raise ValueError("native mercenary regiment type status is malformed")
    # Preserve all partial rows, signed per-type tiers and copied native totals.
    # The inventory maximum starts at zero; it is not an observed province K.
    # Regiment sums exclude holder knights included in company current_soldiers.
    return ready


def _location(value: object) -> None:
    if not isinstance(value, Mapping):
        raise ValueError("native mercenary location is malformed")
    _integer(value.get("company_home_title_id"), -(2**31), 2**31-1, "home title", nullable=True)
    for field in ("company_home_province_id", "hire_auto_raise_province_id"):
        _integer(value.get(field), 1, 2**31-1, field, nullable=True)
    _integer(value.get("actor_active_war_count"), 0, 2**31-1, "active war count", nullable=True)
    attempted = value.get("hire_auto_raise_attempted_in_active_war")
    if attempted is not None and type(attempted) is not bool:
        raise ValueError("native mercenary auto-raise attempted status is malformed")
    for prefix in ("company_home", "hire_auto_raise_position"):
        if type(value.get(prefix + "_ready")) is not bool:
            raise ValueError(f"native mercenary {prefix} readiness is malformed")
        if any(not isinstance(value.get(prefix + suffix), str) or not value[prefix + suffix]
               for suffix in ("_failure", "_source")):
            raise ValueError(f"native mercenary {prefix} native source/failure is malformed")
    # A war-free player can legitimately have no auto-raise attempt/location.
    # Home location and the native hire selector remain separate observations.


def normalize_player_mercenary_context_v1(value: object, *, snapshot: Mapping[str, object]) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("native mercenary context schema is malformed")
    build = require_exact_native_build(value.get("game_version"), value.get("executable_sha256"))
    if build not in _SCHEMAS_BY_BUILD or value.get("schema") != _SCHEMAS_BY_BUILD[build]:
        raise ValueError("native mercenary context schema is malformed")
    if build == CK3_12004 and build != private_native_build_identity(snapshot):
        raise ValueError("native mercenary context belongs to another build")
    player = snapshot.get("played_character")
    if (not isinstance(player, Mapping)
            or type(value.get("actor_character_id")) is not int
            or value["actor_character_id"] != player.get("character_id")
            or type(value.get("date_raw")) is not int
            or value["date_raw"] != snapshot.get("date_raw")
            or type(value.get("capture_epoch")) is not int or value["capture_epoch"] <= 0
            or value.get("read_only") is not True
            or type(value.get("native_hire_mode")) is not int or value["native_hire_mode"] != 1):
        raise ValueError("native mercenary identity differs from current player frame")
    _availability(value, "collection")
    rows = value.get("rows")
    if not isinstance(rows, list):
        raise ValueError("native mercenary candidate collection is malformed")
    normalized_rows = []
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError("native mercenary candidate row is malformed")
        _integer(row.get("company_id"), 0, 2**32-1, "company full ID")
        _integer(row.get("employer_id"), 0, 2**32-1, "employer full ID", nullable=True)
        _integer(row.get("manager_slot_index"), 0, 2**32-1, "manager slot index")
        _strength(row.get("troop_strength"))
        _terms(row.get("final_terms"))
        _location(row.get("location"))
        composition_ready = (
            _composition(row["composition_v1"], row["company_id"])
            if "composition_v1" in row else False
        )
        terms_ready = row["final_terms"]["available"] is True
        normalized_rows.append({
            **row,
            "readiness_v1": {
                "composition_ready": composition_ready,
                "hire_terms_ready": terms_ready,
                "hire_ready": composition_ready and terms_ready
                and row["final_terms"]["can_hire"] is True,
            },
        })
    return {**value, "rows": normalized_rows}
