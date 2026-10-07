"""Bind normalized V2 constructor advantage to the bounded contact model.

This is an optional, hypothetical constructor context frozen for future model
trials. It supplies neither complete encounter advantage nor native parity.
The caller retains the existing input and contact-admission rules.
"""

from __future__ import annotations

from hashlib import sha256
import json
from typing import Any, Mapping

from .combat_input import CombatInputError, FrozenCombatSimulationInput


V2_CONSTRUCTOR_ADVANTAGE_SOURCE = (
    "same_frame_v2_native_constructor_zero_roll_frozen_future"
)

V2ConstructorAdvantage = tuple[
    int, int, int, tuple[int | None, int | None], str, str
]


def _signed_raw(value: object, field: str) -> int:
    if type(value) is not int or not -(2**63) <= value < 2**63:
        raise CombatInputError(f"V2 constructor advantage {field} is malformed")
    return value


def read_v2_constructor_advantage(
    payload: Mapping[str, Any], frozen: FrozenCombatSimulationInput,
) -> V2ConstructorAdvantage | None:
    """Return A/D leader ArmyIDs, signed total, selected IDs, hash and source.

    Consume the same query's strict-normalized schema2 constructor context.
    Older schemas and unavailable optional observations keep the generic
    model. A claimed available context must retain its existing arithmetic
    and participant binding. None-selected commanders use the first army as
    a placeholder; the paired selected IDs disable that side's commander roll.
    """
    if payload.get("schema_version") != 2:
        return None
    base = payload.get("base_inputs")
    if not isinstance(base, Mapping):
        return None
    context = base.get("contextual_advantage")
    if not isinstance(context, Mapping) or context.get("schema_version") != 2:
        return None
    if context.get("status") != "available":
        return None

    scenario = base.get("scenario")
    encounter = frozen.encounter
    if (
        not isinstance(scenario, Mapping)
        or base.get("target_province_id") != encounter.target_province_id
        or context.get("target_province_id") != encounter.target_province_id
        or scenario.get("attacker_entry_province_id") != encounter.attacker_entry_province_id
        or scenario.get("attacker_army_ids") != list(encounter.attacker_army_ids)
        or scenario.get("defender_army_ids") != list(encounter.defender_army_ids)
    ):
        raise CombatInputError("V2 constructor advantage encounter binding differs")
    if (
        context.get("scope") != "hypothetical_constructor_context"
        or type(context.get("scale")) is not int
        or context.get("scale") != 100_000
        or context.get("synthetic_helper_total_match") is not True
    ):
        raise CombatInputError("V2 constructor advantage helper provenance differs")

    sides = context.get("sides")
    if not isinstance(sides, list) or len(sides) != 2:
        raise CombatInputError("V2 constructor advantage side pair is malformed")
    leader_ids: list[int] = []
    selected_ids: list[int | None] = []
    side_totals: list[int] = []
    for index, role in enumerate(("attacker", "defender")):
        side = sides[index]
        armies = tuple(army for army in frozen.armies if army.encounter_role == role)
        ordered_ids = tuple(army.public_army_id for army in armies)
        expected_ids = (
            encounter.attacker_army_ids if index == 0 else encounter.defender_army_ids
        )
        if (
            not isinstance(side, Mapping)
            or type(side.get("side_index")) is not int
            or side.get("side_index") != index
            or not armies
            or ordered_ids != expected_ids
            or side.get("ordered_public_cunit_ids") != list(expected_ids)
        ):
            raise CombatInputError("V2 constructor advantage ordered side differs")

        selected = side.get("selected_commander_character_id")
        if selected is None:
            leader = armies[0]
        else:
            if type(selected) is not int or selected <= 0:
                raise CombatInputError("V2 constructor selected commander is malformed")
            candidates = tuple(
                army for army in armies if army.commander.character_id == selected
            )
            if len(candidates) != 1:
                raise CombatInputError("V2 constructor selected commander army is not unique")
            leader = candidates[0]
        commander = _signed_raw(side.get("commander_dynamic_raw"), "commander_dynamic_raw")
        dynamic = _signed_raw(side.get("side_dynamic_raw"), "side_dynamic_raw")
        residual = _signed_raw(
            side.get("target_conditionals_residual_raw"), "target_conditionals_residual_raw"
        )
        total = _signed_raw(side.get("side_total_raw"), "side_total_raw")
        if total != commander + dynamic + residual:
            raise CombatInputError("V2 constructor advantage side arithmetic differs")
        leader_ids.append(leader.public_army_id)
        selected_ids.append(selected)
        side_totals.append(total)

    base_raw = _signed_raw(
        context.get("base_constructor_accumulator_raw"), "base_constructor_accumulator_raw"
    )
    total_raw = _signed_raw(
        context.get("synthetic_zero_roll_total_raw"), "synthetic_zero_roll_total_raw"
    )
    if total_raw != base_raw + side_totals[0] - side_totals[1]:
        raise CombatInputError("V2 constructor advantage total arithmetic differs")
    model_sha256 = sha256(json.dumps(
        context, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    ).encode("utf-8")).hexdigest().upper()
    return (
        leader_ids[0], leader_ids[1], total_raw,
        (selected_ids[0], selected_ids[1]), model_sha256,
        V2_CONSTRUCTOR_ADVANTAGE_SOURCE,
    )
