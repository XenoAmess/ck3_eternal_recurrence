"""Actual authored berserker row value only; native selection stays separate."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from ..bridge.phase_berserker_chance_contract import (
    CHANCE_TRAIT_KEYS, MAIM_TRAIT_KEYS, WOUND_TRAIT_KEYS,
    PHASE_BERSERKER_CHANCE_INPUTS_LEAF,
)
from .battle_phase_events_12003 import load_stock_phase_events_12003
from .combat_core import fixed_mul, trunc_div_toward_zero
from .phase_warmonger_core_12003 import PhaseWarmongerKnightOccurrence12003


@dataclass(frozen=True)
class PhaseBerserkerChanceSource12003:
    occurrence: PhaseWarmongerKnightOccurrence12003
    refs: dict[str, bool | int | None]
    unavailable_reasons: dict[str, str]


@dataclass(frozen=True)
class AuthoredBerserkerChance12003:
    raw_value: int | None
    integer_weight: int | None
    unknown_dependencies: tuple[str, ...]
    unavailable_reasons: dict[str, str]
    operation_trace: tuple[dict[str, object], ...]
    scope: str = "authored_stock_knight_chance_row_value_only"


def _any(values):
    return True if any(value is True for value in values) else None if any(value is None for value in values) else False


def _all(values):
    return False if any(value is False for value in values) else None if any(value is None for value in values) else True


def adapt_phase_berserker_chance_inputs_12003(
    normalized_v2: Mapping[str, object], *, occurrence: PhaseWarmongerKnightOccurrence12003,
) -> PhaseBerserkerChanceSource12003:
    member = None
    for army in normalized_v2["armies"]:
        if army["army_id"] == occurrence.source_army_id:
            rows = army["knights"]["members"] or []
            if occurrence.member_index < len(rows):
                candidate = rows[occurrence.member_index]
                if candidate["character_id"] == occurrence.character_id and candidate["source_regiment_id"] == occurrence.source_regiment_id:
                    member = candidate
            break
    leaf = member.get(PHASE_BERSERKER_CHANCE_INPUTS_LEAF) if member is not None else None
    refs = {}
    reasons = {}
    missing = "chance_leaf_not_published" if member is not None else "knight_occurrence_not_found"
    def assign(path, value, reason):
        refs[path] = value
        if value is None:
            reasons[path] = reason or missing
    heritage = member.get("phase_berserker_validity_inputs_v1") if member is not None else None
    assign("root.culture.heritage_north_germanic",
           heritage["culture"]["heritage_north_germanic"] if heritage is not None else None,
           heritage["culture"]["unavailable_reason"] if heritage is not None else "heritage_leaf_not_published")
    for key in CHANCE_TRAIT_KEYS:
        trait = leaf["traits"][key] if leaf is not None else None
        assign(f"root.traits.{key}", trait["value"] if trait is not None else None,
               trait["unavailable_reason"] if trait is not None else missing)
    ai = leaf["is_ai"] if leaf is not None else None
    stalwart = leaf["stalwart"]["presence"] if leaf is not None else None
    assign("root.is_ai", ai["value"] if ai is not None else None, ai["unavailable_reason"] if ai is not None else missing)
    assign("root.perks.stalwart_leader", stalwart["value"] if stalwart is not None else None,
           stalwart["unavailable_reason"] if stalwart is not None else missing)
    for path, domain, field in (("root.dynasty.perks.warfare_legacy_3", "dynasty", "warfare_legacy_3"),
                               ("root.is_acclaimed", "acclaimed", "is_acclaimed")):
        value = leaf[domain][field] if leaf is not None else None
        if domain == "dynasty" and value is not None:
            value = value["presence"]
        assign(path, value["value"] if value is not None else None, value["unavailable_reason"] if value is not None else missing)
    def derived(path, value, inputs, reason=None):
        unavailable = [reasons[input_path] for input_path in inputs if refs[input_path] is None]
        assign(path, value, reason or "; ".join(dict.fromkeys(unavailable)))
    ai_value, perk = refs["root.is_ai"], refs["root.perks.stalwart_leader"]
    derived("derived.root_player_stalwart", _all([perk, None if ai_value is None else not ai_value]),
            ["root.perks.stalwart_leader", "root.is_ai"])
    derived("derived.root_ai_stalwart", _all([perk, ai_value]), ["root.perks.stalwart_leader", "root.is_ai"])
    wound_paths = [f"root.traits.{key}" for key in WOUND_TRAIT_KEYS]
    wounded = [refs[path] for path in wound_paths]
    derived("derived.root_is_wounded", _any(wounded), wound_paths)
    rank = None if any(value is None for value in wounded) or sum(value is True for value in wounded) > 1 else next(
        (index + 1 for index, value in enumerate(wounded) if value is True), 0)
    factor = None if rank is None else 25000 if rank == 3 else 50000 if rank else 100000
    derived("derived.become_berserker_wound_factor_raw", factor, wound_paths,
            "wounded_traits_multiple_present" if sum(value is True for value in wounded) > 1 else None)
    maim_paths = [f"root.traits.{key}" for key in MAIM_TRAIT_KEYS]
    derived("derived.root_has_any_maim_injury", _any([refs[path] for path in maim_paths]), maim_paths)
    return PhaseBerserkerChanceSource12003(occurrence, refs, reasons)


def evaluate_berserker_stock_chance_12003(source: PhaseBerserkerChanceSource12003, *, stock=None):
    """Read the actual stock AST, preserving source order and truncation steps."""
    stock = load_stock_phase_events_12003() if stock is None else stock
    row = next(row for row in stock.event_rows if row.key == "knight_become_berserker")
    ast = row.chance_ast
    if ast["op"] != "modifier_sequence":
        raise ValueError("unsupported berserker chance AST")
    unknown = []
    def value(node):
        if node["op"] == "const_fixed":
            return node["raw"]
        if node["op"] == "state_ref":
            result = source.refs[node["path"]]
            if result is None and node["path"] not in unknown:
                unknown.append(node["path"])
            return result
        raise ValueError("unsupported berserker chance operand")
    running = value(ast["initial"])
    trace = []
    for index, modifier in enumerate(ast["modifiers"]):
        condition = value(modifier["condition"])
        if condition is not None and type(condition) is not bool:
            raise ValueError("berserker chance condition must be boolean or unknown")
        factor = value(modifier["value"]) if condition is not False else None
        before = running
        if condition is None:
            running = None
        elif condition is True:
            running = fixed_mul(running, factor) if running is not None and factor is not None else None
        trace.append({"ast_index": index + 1, "condition_path": modifier["condition"]["path"],
                      "condition": condition, "factor_raw": factor, "before_raw": before, "after_raw": running,
                      "applied": condition, "mode": modifier["mode"]})
    return AuthoredBerserkerChance12003(running, None if running is None else trunc_div_toward_zero(running, 100000),
        tuple(unknown), {path: source.unavailable_reasons[path] for path in unknown}, tuple(trace))
