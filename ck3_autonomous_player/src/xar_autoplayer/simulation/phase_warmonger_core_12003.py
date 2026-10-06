"""One source-shaped knight validity operand, without phase selection or forecast."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from ..bridge.phase_warmonger_core_contract import (
    PHASE_WARMONGER_CORE_LEAF, PhaseWarmongerCoreV1,
)

WARMONGER_VALIDITY_REF_12003 = "root.rite.tenets.warmonger"


@dataclass(frozen=True)
class PhaseWarmongerKnightOccurrence12003:
    source_army_id: int
    source_regiment_id: int
    character_id: int
    member_index: int

    def __post_init__(self) -> None:
        if type(self.member_index) is not int or self.member_index < 0:
            raise ValueError("phase warmonger occurrence requires a native member row index")


@dataclass(frozen=True)
class PhaseWarmongerSource12003:
    occurrence: PhaseWarmongerKnightOccurrence12003
    value: bool | None
    leaf: PhaseWarmongerCoreV1 | None
    unavailable_reason: str | None

    def require_boolean(self) -> bool:
        if self.value is None:
            raise ValueError(f"phase warmonger operand unavailable: {self.unavailable_reason}")
        return self.value


def adapt_phase_warmonger_core_12003(
    normalized_v2: Mapping[str, object], *, occurrence: PhaseWarmongerKnightOccurrence12003
) -> PhaseWarmongerSource12003:
    armies = normalized_v2.get("armies")
    if not isinstance(armies, list):
        raise ValueError("phase warmonger adapter requires normalized V2 armies")
    for army in armies:
        if army["army_id"] != occurrence.source_army_id:
            continue
        members = army["knights"]["members"] or []
        if occurrence.member_index >= len(members):
            break
        member = members[occurrence.member_index]
        if (member["character_id"] != occurrence.character_id
                or member["source_regiment_id"] != occurrence.source_regiment_id):
            break
        leaf = member.get(PHASE_WARMONGER_CORE_LEAF)
        if leaf is None:
            return PhaseWarmongerSource12003(occurrence, None, None, "phase_warmonger_leaf_not_published")
        if leaf["source_character_id"] != occurrence.character_id:
            raise ValueError("phase warmonger leaf differs from its native source occurrence")
        return PhaseWarmongerSource12003(
            occurrence, leaf["warmonger_core_membership"], leaf, leaf["unavailable_reason"],
        )
    return PhaseWarmongerSource12003(occurrence, None, None, "phase_knight_occurrence_unobserved")
