"""Covered stock terminal-person guards from two existing model outputs.

This joins normal finalizer intent with named-person state without changing
those producers. Passing a guard selects neither a random branch nor a capture
or death write. The .1002 prisoner context is supplied independently by caller.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Mapping, Sequence


@dataclass(frozen=True, slots=True)
class TerminalPersonCandidate12003:
    character_id: int
    role: str
    branch: str
    is_imprisoned: bool | None = None
    prisoner_install_context_selected: bool | None = None
    source_context: Mapping[str, object] | None = None


def _and(operands):
    """Source boolean conjunction; known false resolves unreached unknowns."""
    if any(value is False for _, value in operands):
        return False, ()
    missing = tuple(name for name, value in operands if value is not True)
    return (None, missing) if missing else (True, ())


def _not(value):
    return False if value is True else True if value is False else None


def _bound(full_id):
    return None if full_id is None or full_id == -1 else True


def project_named_person_terminal_eligibility_12003(
    named_person_outcomes: Mapping[str, object],
    normal_finalizer_projection: Mapping[str, object],
    *,
    winner_primary_character_id: int | None,
    loser_primary_character_id: int | None,
    primary_participants_really_at_war: bool | None,
    war_tutorial: bool | None,
    candidates: Sequence[TerminalPersonCandidate12003],
    source_context: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Join covered .1001/.1002 conditions on explicit script candidates.

    Candidates are caller-supplied losing commander/knight iterator members,
    not every requested current Character. Really-at-war is the stock primary
    relation, not the manager's broader hostility predicate. Overall numeric
    partial status supplies no additional condition. Raw winner -1 alone does
    not exclude native fallback envelope contexts; their primary IDs are explicit.
    """
    dispatch = normal_finalizer_projection.get("dispatch") or {}
    normal_intent = dispatch.get("normal_result_intent")
    envelope, envelope_missing = _and((
        ("normal_result_intent", normal_intent),
        ("winner_primary_context", _bound(winner_primary_character_id)),
        ("loser_primary_context", _bound(loser_primary_character_id)),
        ("primary_participants_really_at_war", primary_participants_really_at_war),
        ("not_war_tutorial", _not(war_tutorial)),
    ))
    alive_by_id = named_person_outcomes.get("alive_for_terminal_candidate_by_id") or {}
    rows = []
    gaps = list(envelope_missing)
    for index, candidate in enumerate(candidates):
        if candidate.role not in {"losing_commander", "losing_knight"}:
            raise ValueError("candidate role requires a supplied losing-side script member")
        if candidate.branch not in {"capture", "death"}:
            raise ValueError("candidate branch requires capture or death")
        alive = alive_by_id.get(candidate.character_id)
        if alive is not True and alive is not False:
            alive = None
        supported = not (candidate.role == "losing_commander" and candidate.branch == "death")
        candidate_guard, missing = _and((
            ("normal_envelope", envelope), ("candidate_is_alive", alive),
            ("stock_branch_present", supported),
        ))
        # .1002 is a separately selected relevant-prisoner event context. Its
        # alive/not-imprisoned conditions do not repeat the .1001 war trigger.
        prisoner_guard, prisoner_missing = _and((
            ("prisoner_install_context_selected", candidate.prisoner_install_context_selected),
            ("prisoner_is_alive", alive),
            ("prisoner_is_not_imprisoned", _not(candidate.is_imprisoned)),
        ))
        rows.append({
            "source_order_index": index, "character_id": candidate.character_id,
            "role": candidate.role, "branch": candidate.branch,
            "modeled_alive": alive, "covered_normal_candidate_guards_passed": candidate_guard,
            "normal_candidate_missing_operands": missing,
            "covered_prisoner_install_guards_passed": prisoner_guard,
            "prisoner_install_missing_operands": prisoner_missing,
            "source_context": copy.deepcopy(candidate.source_context),
        })
        gaps.extend(f"candidate[{index}]:{name}" for name in missing)
        gaps.extend(f"prisoner[{index}]:{name}" for name in prisoner_missing)
    return {
        "scope_kind": "caller_conditional_terminal_person_guard_composition_12003",
        "normal_finalizer_projection": normal_finalizer_projection,
        "named_person_outcomes": named_person_outcomes,
        "origin_character_observation": named_person_outcomes.get("origin_character_observation"),
        "modeled_person_state": named_person_outcomes.get("modeled_named_person_state_by_id"),
        "normal_envelope_covered_guards_passed": envelope,
        "normal_envelope_missing_operands": envelope_missing,
        "winner_primary_character_id": winner_primary_character_id,
        "loser_primary_character_id": loser_primary_character_id,
        "ordered_candidate_guard_results": tuple(rows),
        "missing_operands": tuple(gaps),
        "source_context": copy.deepcopy(source_context),
        "event_selected_or_dispatched": None,
        "capture_or_death_writeback_selected": None,
        "actual_native_effects_executed": False,
        "actual_game_days_advanced": 0,
        "complete_native_finalizer": False,
        "complete_monte_carlo": False,
    }
