"""Ordered, caller-conditioned .3 named-person primary consequences.

Selection and enqueue records retain current state. Only explicit committed
primary writes or an admitted, source-qualified death flush change this model.
The module neither executes event scripts nor performs knight entry cleanup.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Mapping, Sequence


@dataclass(frozen=True, slots=True)
class NamedPersonOutcome12003:
    character_id: int | None
    operation: str
    stage: str
    writeback: Mapping[str, object] | None = None
    victim_pointer_present: bool | None = None
    death_data_pointer_is_null: bool | None = None
    commit_writes_selected: bool | None = None
    date_object_raw_u64: int | None = None
    reason_key: str | None = None
    killer_full_character_id_raw: int | None = None
    artifact_full_id_raw: int | None = None
    cleanup_reference: object | None = None
    source_context: Mapping[str, object] | None = None


_STAGES = frozenset({"selected_effect", "admitted_effect", "request_direct",
                     "enqueued_pending", "flush", "committed_primary"})
_PENDING = frozenset({"selected_effect", "admitted_effect", "enqueued_pending"})
_OPERATIONS = frozenset({"injury_traits", "effective_prowess", "death"})


def _full_id(value: object, name: str, *, allow_none: bool = False) -> None:
    if value is None and allow_none:
        return
    if type(value) is not int or not -(1 << 31) <= value < (1 << 31):
        raise ValueError(f"{name} must retain its signed int32 full-ID value")


def apply_committed_named_person_outcomes_12003(
    current_person_observation: Mapping[str, object],
    ordered_outcomes: Sequence[NamedPersonOutcome12003],
    *,
    source_context: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Apply explicit primary outcomes while preserving the original query.

    A flush uses the actual victim-pointer/marker predicate. A duplicate victim
    whose marker was installed by an earlier modeled row is skipped. Direct
    calls require an explicit selected-write witness: 28FAAF0 also has a branch
    that returns without primary writes. Missing metadata remains null.
    """
    origin = copy.deepcopy(dict(current_person_observation))
    rows = current_person_observation.get("character_observations")
    state: dict[int, dict[str, object]] = {}
    if rows is not None:
        for row in rows:
            person = copy.deepcopy(dict(row))
            character_id = person["character_id"]
            _full_id(character_id, "observed character_id")
            state[character_id] = person
    ledger: list[dict[str, object]] = []
    affected: list[int] = []
    modeled_dead: set[int] = set()
    cleanup_references: list[object] = []
    gaps: list[str] = []

    def missing(record: dict[str, object], reason: str) -> None:
        record.update(result="partial", missing_operand=reason)
        gaps.append(f"callback[{record['index']}]:{reason}")

    for index, outcome in enumerate(ordered_outcomes):
        if outcome.stage not in _STAGES or outcome.operation not in _OPERATIONS:
            raise ValueError("unsupported named-person stage or primary operation")
        if outcome.stage in {"request_direct", "flush"} and outcome.operation != "death":
            raise ValueError("native request/flush stage applies to death only")
        _full_id(outcome.character_id, "callback character_id", allow_none=True)
        record: dict[str, object] = {
            "index": index, "character_id": outcome.character_id,
            "operation": outcome.operation, "stage": outcome.stage,
            "source_context": copy.deepcopy(outcome.source_context),
            "applied": False, "result": "pending",
        }
        ledger.append(record)
        if outcome.stage in _PENDING:
            continue
        character_id = outcome.character_id
        if outcome.operation == "death" and outcome.stage == "flush":
            # This guard belongs to the queue consumer, not every direct call.
            record["supplied_flush_record_destructor_intent"] = True
            if outcome.victim_pointer_present is False:
                record["result"] = "flush_skipped_null_victim"
                continue
            if outcome.victim_pointer_present is None:
                missing(record, "victim_pointer_present")
                continue
            if character_id is None:
                missing(record, "actual_victim_full_character_id")
                continue
            if character_id in modeled_dead:
                record["result"] = "flush_skipped_already_dead"
                continue
            if outcome.death_data_pointer_is_null is False:
                record["result"] = "flush_skipped_already_dead"
                continue
            if outcome.death_data_pointer_is_null is None:
                missing(record, "death_data_pointer_is_null_at_flush")
                continue
        else:
            if outcome.commit_writes_selected is False:
                record["result"] = "no_primary_writeback"
                continue
            if outcome.commit_writes_selected is None:
                missing(record, "actual_primary_writeback_selected")
                continue
            if character_id is None:
                missing(record, "actual_victim_full_character_id")
                continue
        if character_id == -1:
            missing(record, "actual_victim_full_character_id")
            continue
        person = state.get(character_id)
        if outcome.operation != "death" and outcome.writeback is None:
            missing(record, "explicit_primary_writeback")
            continue
        if person is None:
            # An explicit full-ID callback need not have appeared in the bounded
            # requested character list. Its other current facts stay unknown.
            person = {"character_id": character_id, "alive": None,
                      "status": "unavailable", "actual_jailer_character_id": None,
                      "current_person_state": None}
            state[character_id] = person
        if outcome.operation == "death":
            raw_date = outcome.date_object_raw_u64
            if raw_date is not None and (
                type(raw_date) is not int or not 0 <= raw_date < (1 << 64)
            ):
                raise ValueError("date_object_raw_u64 must preserve all 64 copied bits")
            _full_id(outcome.killer_full_character_id_raw, "killer fullID", allow_none=True)
            _full_id(outcome.artifact_full_id_raw, "artifact fullID", allow_none=True)
            person["alive"] = False
            person["modeled_death_metadata"] = {
                "date_object_raw_u64": raw_date,
                "reason_key": outcome.reason_key,
                "killer_full_character_id_raw": outcome.killer_full_character_id_raw,
                "artifact_full_id_raw": outcome.artifact_full_id_raw,
            }
            modeled_dead.add(character_id)
            record["result"] = "committed_death"
            if outcome.cleanup_reference is not None:
                reference_id = (outcome.cleanup_reference.get("character_id")
                    if isinstance(outcome.cleanup_reference, Mapping)
                    else getattr(outcome.cleanup_reference, "character_id", None))
                if reference_id == character_id:
                    # Forward only. Existing entry-event code owns the branch
                    # premises, mapping, count debits and actual cleanup model.
                    cleanup_references.append(outcome.cleanup_reference)
                else:
                    gaps.append(f"callback[{index}]:cleanup_reference_character_id")
        else:
            current = copy.deepcopy(person.get("current_person_state") or {})
            current[outcome.operation] = copy.deepcopy(dict(outcome.writeback))
            person["current_person_state"] = current
            record["result"] = "committed_primary_writeback"
        record["applied"] = True
        if character_id not in affected:
            affected.append(character_id)

    return {
        "scope_kind": "caller_conditional_named_person_primary_outcomes_12003",
        "origin_character_observation": origin,
        "source_context": copy.deepcopy(source_context),
        "modeled_named_person_state_by_id": state,
        "ordered_outcome_ledger": tuple(ledger),
        "affected_character_ids_in_order": tuple(affected),
        "cleanup_references_to_existing_owner": tuple(cleanup_references),
        "alive_for_terminal_candidate_by_id": {
            character_id: person.get("alive") for character_id, person in state.items()
        },
        "missing_consequences": tuple(gaps),
        "observed_native_execution": False,
        "normal_terminal_or_capture_selected": None,
        "actual_game_days_advanced": 0,
        "complete_transition": False,
        "complete_monte_carlo": False,
    }
