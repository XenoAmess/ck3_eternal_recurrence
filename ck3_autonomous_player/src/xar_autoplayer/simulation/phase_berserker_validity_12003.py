"""Pure authored stock validity only; no native admission, chance or effect."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from ..bridge.phase_berserker_validity_contract import PHASE_BERSERKER_VALIDITY_INPUTS_LEAF
from .battle_phase_events_12003 import load_stock_phase_events_12003
from .phase_warmonger_core_12003 import (
    PhaseWarmongerKnightOccurrence12003, WARMONGER_VALIDITY_REF_12003,
    adapt_phase_warmonger_core_12003,
)


@dataclass(frozen=True)
class PhaseBerserkerValiditySource12003:
    occurrence: PhaseWarmongerKnightOccurrence12003
    refs: dict[str, bool | None]
    unavailable_reasons: dict[str, str]


@dataclass(frozen=True)
class AuthoredBerserkerValidity12003:
    value: bool | None
    unknown_ref_paths: tuple[str, ...]
    unavailable_reasons: dict[str, str]
    scope: str = "authored_stock_knight_validity_only"


def adapt_phase_berserker_validity_inputs_12003(
    normalized_v2: Mapping[str, object], *, occurrence: PhaseWarmongerKnightOccurrence12003,
) -> PhaseBerserkerValiditySource12003:
    warmonger = adapt_phase_warmonger_core_12003(normalized_v2, occurrence=occurrence)
    refs = {WARMONGER_VALIDITY_REF_12003: warmonger.value}
    reasons = {}
    if warmonger.value is None:
        reasons[WARMONGER_VALIDITY_REF_12003] = warmonger.unavailable_reason
    leaf = None
    for army in normalized_v2["armies"]:
        if army["army_id"] != occurrence.source_army_id:
            continue
        members = army["knights"]["members"] or []
        if occurrence.member_index < len(members):
            member = members[occurrence.member_index]
            if member["character_id"] == occurrence.character_id and member["source_regiment_id"] == occurrence.source_regiment_id:
                leaf = member.get(PHASE_BERSERKER_VALIDITY_INPUTS_LEAF)
        break
    fields = [("root.culture.heritage_north_germanic", "culture", "heritage_north_germanic"),
              ("root.religion.germanic", "religion", "germanic")]
    for path, domain, value_key in fields:
        refs[path] = leaf[domain][value_key] if leaf is not None else None
        if refs[path] is None:
            reasons[path] = leaf[domain]["unavailable_reason"] if leaf is not None else "phase_berserker_inputs_leaf_not_published"
    for key in ("craven", "berserker", "calm"):
        path = f"root.traits.{key}"
        refs[path] = leaf["traits"][key]["value"] if leaf is not None else None
        if refs[path] is None:
            reasons[path] = leaf["traits"][key]["unavailable_reason"] if leaf is not None else "phase_berserker_inputs_leaf_not_published"
    return PhaseBerserkerValiditySource12003(occurrence, refs, reasons)


def evaluate_berserker_stock_validity_12003(
    source: PhaseBerserkerValiditySource12003, *, stock=None,
) -> AuthoredBerserkerValidity12003:
    """Consume the actual frozen row AST with nullable observations preserved."""
    stock = load_stock_phase_events_12003() if stock is None else stock
    row = next(row for row in stock.event_rows if row.key == "knight_become_berserker")
    def evaluate(node) -> bool | None:
        op = node["op"]
        if op == "state_ref":
            value = source.refs[node["path"]]
            if value is not None and type(value) is not bool:
                raise ValueError("berserker validity operand must be boolean or unknown")
            return value
        if op == "not":
            value = evaluate(node["arg"])
            return None if value is None else not value
        if op in ("all", "any"):
            values = [evaluate(child) for child in node["args"]]
            decisive = False if op == "all" else True
            if any(value is decisive for value in values):
                return decisive
            return None if any(value is None for value in values) else not decisive
        raise ValueError(f"unsupported authored berserker validity AST operation: {op}")
    value = evaluate(row.validity_ast)
    unknown = tuple(path for path, observed in source.refs.items() if observed is None)
    return AuthoredBerserkerValidity12003(value, unknown, source.unavailable_reasons.copy())
