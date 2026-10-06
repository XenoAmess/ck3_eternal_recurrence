"""Source-shaped adopted Rite operands from normalized V2 roster occurrences.

These operands cover six stock injury/death chance modifiers and the selected
enemy knight's two Rite reward predicates. They do not admit candidates,
select events, or establish whole V2/V3 or future forecast readiness.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Mapping

from ..bridge.phase_rite_parameters_contract import (
    PHASE_RITE_PARAMETERS_LEAF,
    PhaseRiteParametersV1,
)
from .combat_core import fixed_mul


ROOT_DEATH_IS_GLORY_REF = "root.rite.parameters.death_is_glory"
DEATH_IS_GLORY_EVENT_ROLES_12003 = {
    "commander_wounded": "commander",
    "commander_maimed": "commander",
    "commander_killed": "commander",
    "knight_wounded": "knight",
    "knight_maimed": "knight",
    "knight_killed": "knight",
}
_SOURCE_KEYS = {
    "root": {ROOT_DEATH_IS_GLORY_REF: "death_is_glory"},
    "selected_enemy_knight": {
        "selected_enemy_knight.rite.killing_bestows_heads": "killing_bestows_heads",
        "selected_enemy_knight.rite.decapitation_steals_prestige_as_piety": "decapitation_steals_prestige_as_piety",
    },
}


@dataclass(frozen=True)
class PhaseRiteOccurrence12003:
    """A roster source occurrence; source Army is public CUnit, not CArmy."""

    role: Literal["commander", "knight"]
    source_army_id: int
    source_regiment_id: int | None
    character_id: int

    def __post_init__(self) -> None:
        if self.role not in ("commander", "knight"):
            raise ValueError("phase Rite occurrence requires commander or knight role")
        if self.role == "commander" and self.source_regiment_id is not None:
            raise ValueError("commander Rite occurrence has no source Regiment")
        if self.role == "knight" and self.source_regiment_id is None:
            raise ValueError("knight Rite occurrence requires a source Regiment")


@dataclass(frozen=True)
class PhaseRiteParameterSource12003:
    occurrence: PhaseRiteOccurrence12003
    scope: Literal["root", "selected_enemy_knight"]
    status: Literal["available", "absent", "unavailable"]
    refs: Mapping[str, bool | None]
    leaf: PhaseRiteParametersV1 | None
    unavailable_reason: str | None

    def require_boolean(self, path: str) -> bool:
        value = self.refs[path]
        if value is None:
            raise ValueError(f"phase Rite operand {path} unavailable: {self.unavailable_reason}")
        return value


def _occurrence_leaf(
    inputs: Mapping[str, object], occurrence: PhaseRiteOccurrence12003
) -> tuple[PhaseRiteParametersV1 | None, str | None]:
    armies = inputs.get("armies")
    if not isinstance(armies, list):
        raise ValueError("phase Rite adapter requires normalized V2 armies")
    for army in armies:
        if army["army_id"] != occurrence.source_army_id:
            continue
        if occurrence.role == "commander":
            commander = army["commander"]
            if commander["status"] == "available" and commander["character_id"] == occurrence.character_id:
                return commander.get(PHASE_RITE_PARAMETERS_LEAF), None
        else:
            for member in army["knights"]["members"] or []:
                if (member["character_id"] == occurrence.character_id
                        and member["source_regiment_id"] == occurrence.source_regiment_id):
                    return member.get(PHASE_RITE_PARAMETERS_LEAF), None
    return None, "phase_role_occurrence_unobserved"


def adapt_phase_rite_parameters_12003(
    normalized_v2: Mapping[str, object], *, occurrence: PhaseRiteOccurrence12003,
    scope: Literal["root", "selected_enemy_knight"] = "root",
) -> PhaseRiteParameterSource12003:
    """Project one exact role/Army/Regiment/Character occurrence.

    An observed absent Rite makes the script Rite scope false. An available
    complete set makes absent keys known false. Unavailable/unpublished sets
    stay ``None``. The Faith main Rite and constructor religion inputs are not
    part of this source lookup. Selected enemy membership is caller supplied;
    this function establishes no native candidate admission or ordering.
    """

    if scope not in _SOURCE_KEYS:
        raise ValueError("phase Rite adapter scope is malformed")
    if scope == "selected_enemy_knight" and occurrence.role != "knight":
        raise ValueError("selected enemy Rite scope requires a knight occurrence")
    leaf, reason = _occurrence_leaf(normalized_v2, occurrence)
    if leaf is None:
        status = "unavailable"
        reason = reason or "phase_rite_parameters_leaf_not_published"
    else:
        if leaf["source_character_id"] != occurrence.character_id:
            raise ValueError("phase Rite leaf differs from its source occurrence")
        status = leaf["status"]
        reason = leaf["unavailable_reason"]
    if status == "available":
        parameters = set(leaf["boolean_parameter_keys"])
        refs = {path: key in parameters for path, key in _SOURCE_KEYS[scope].items()}
    elif status == "absent":
        refs = {path: False for path in _SOURCE_KEYS[scope]}
    else:
        refs = {path: None for path in _SOURCE_KEYS[scope]}
    return PhaseRiteParameterSource12003(occurrence, scope, status, refs, leaf, reason)


def apply_death_is_glory_modifier_12003(
    chance_raw: int, *, event_key: str, source: PhaseRiteParameterSource12003
) -> int:
    """Apply only this row's authored 1.1 factor at its source-order position.

    The caller supplies the running Q100000 value immediately before the
    Rite modifier. Other modifiers, validity and selection remain separate.
    """

    if (event_key not in DEATH_IS_GLORY_EVENT_ROLES_12003 or source.scope != "root"
            or source.occurrence.role != DEATH_IS_GLORY_EVENT_ROLES_12003[event_key]):
        raise ValueError("phase event does not consume this root Rite occurrence")
    if isinstance(chance_raw, bool) or not isinstance(chance_raw, int) or not -(2**63) <= chance_raw < 2**63:
        raise ValueError("phase Rite modifier requires signed int64 Q100000")
    return fixed_mul(chance_raw, 110_000) if source.require_boolean(ROOT_DEATH_IS_GLORY_REF) else chance_raw
