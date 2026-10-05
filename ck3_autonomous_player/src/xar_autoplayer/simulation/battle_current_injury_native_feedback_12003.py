"""Compose selected injury requests, explicit outcomes and independent readback.

The existing named-person stage model owns primary writes. This adapter neither
executes SCRIPT again nor derives callback admission from a matching current
person. All observations and the original selected result remain unchanged.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
from typing import Mapping, Sequence

from .battle_current_named_person_outcomes_12003 import (
    NamedPersonOutcome12003, apply_committed_named_person_outcomes_12003,
)


NATIVE_EXECUTOR_SOURCE_API_SHA256_12003 = (
    "E870FACD23B819F8766A28D1D806A80D5CD67E9DF6CFEC2EADF795AA12B5C4C5"
)
DEATH_COMMIT_SOURCE_API_SHA256_12003 = (
    "2BD321F299BDA380527FF41FAC83B5B8DE88A63FA05D6200D473672B12F8ED45"
)


def _token(container, key):
    present = isinstance(container, Mapping) and key in container
    value = container[key] if present else None
    return {"presence": "absent" if not present else "null" if value is None else "value",
            "value": deepcopy(value)}


def _equal_provided(left, right):
    return left == right if left is not None and right is not None else None


def _post_person(observation, character_id):
    candidates = observation.get("character_observations", ()) if observation is not None else ()
    candidates = candidates if isinstance(candidates, (tuple, list)) else ()
    rows = [row for row in candidates
            if isinstance(row, Mapping) and row.get("character_id") == character_id]
    return (rows[0] if len(rows) == 1 else None), len(rows)


def compose_selected_injury_native_feedback_12003(
    selected_execution: Mapping[str, object],
    current_person_observation: Mapping[str, object],
    ordered_outcomes: Sequence[NamedPersonOutcome12003],
    *,
    post_person_observation: Mapping[str, object] | None = None,
    source_context: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Consume explicit stage records once, then report independent field facts.

    A caller may supply actual stage witnesses or source-qualified conditional
    operands. Their provenance is retained verbatim. Neither a requested death
    nor an equal post-query key establishes the compiled child/handler binding.
    Script killer absence, explicit null and native fullID -1 remain distinct.
    """
    outcomes = tuple(ordered_outcomes)
    primary = apply_committed_named_person_outcomes_12003(
        current_person_observation, outcomes, source_context=source_context)
    requests = tuple(deepcopy(selected_execution.get("effect_requests", ())))
    links = []
    postconditions = []
    for request_index, request in enumerate(requests):
        if request.get("operation") != "death":
            continue
        character_id = request.get("target_character_id")
        payload = request.get("payload", {})
        reason = _token(request, "reason_key")
        killer = _token(payload, "killer_character_id")
        comparisons = []
        for outcome_index, outcome in enumerate(outcomes):
            if outcome.operation != "death" or outcome.character_id != character_id:
                continue
            comparisons.append({
                "outcome_index": outcome_index,
                "operation_and_fullID_equal": True,
                "stage": outcome.stage,
                "reason_key": outcome.reason_key,
                "killer_full_character_id_raw": outcome.killer_full_character_id_raw,
                "reason_token_equal": _equal_provided(reason["value"], outcome.reason_key),
                "killer_token_equal": _equal_provided(killer["value"], outcome.killer_full_character_id_raw),
                "source_context": deepcopy(outcome.source_context),
                "causal_binding_inferred": False,
            })
        links.append({
            "request_index": request_index, "operation": "death",
            "target_character_id": character_id,
            "source_event_key": request.get("source_event_key"),
            "requested_stage": request.get("stage"),
            "requested_reason_key": reason,
            "requested_killer_operand": killer,
            "derived_request_killer_character_id": _token(request, "killer_character_id"),
            "outcome_field_comparisons": tuple(comparisons),
            "association_origin": "provided operation/fullID/token field comparison; independent explicit stage provenance",
            "causal_binding_inferred": False,
        })
        row, row_count = _post_person(post_person_observation, character_id)
        person = row.get("current_person_state") if row is not None else None
        person = person if isinstance(person, Mapping) else {}
        death = person.get("death_record")
        death = death if isinstance(death, Mapping) else {}
        modeled = primary["modeled_named_person_state_by_id"].get(character_id, {})
        observed_alive = row.get("alive") if row is not None else None
        observed_reason = death.get("reason_key")
        postconditions.append({
            "request_index": request_index, "character_id": character_id,
            "matched_character_row_count": row_count,
            "independent_post_row": deepcopy(row),
            "alive": _token(row, "alive"),
            "death_record": deepcopy(death) if "death_record" in person else None,
            "injury_traits": deepcopy(person.get("injury_traits")),
            "effective_prowess": deepcopy(person.get("effective_prowess")),
            "modeled_alive": modeled.get("alive"),
            "alive_equals_modeled": _equal_provided(observed_alive, modeled.get("alive")),
            "reason_equals_requested": (
                reason["value"] == observed_reason
                if death.get("status") == "available" and reason["presence"] == "value" else None),
            "reason_equals_modeled": (
                _equal_provided(observed_reason, modeled.get("modeled_death_metadata", {}).get("reason_key"))
                if death.get("status") == "available" else None),
            "readback_establishes_causality": False,
            "readback_grants_callback_admission": False,
        })
    return {
        "scope_kind": "selected_injury_explicit_outcome_and_independent_readback_12003",
        "selected_execution": deepcopy(dict(selected_execution)),
        "origin_current_person_observation": deepcopy(dict(current_person_observation)),
        "independent_post_person_observation": deepcopy(post_person_observation),
        "source_context": deepcopy(source_context),
        "requests_in_order": requests,
        "supplied_outcomes_in_order": tuple(asdict(outcome) for outcome in outcomes),
        "named_person_projection": primary,
        "ordered_request_links": tuple(links),
        "postcondition_observations": tuple(postconditions),
        "source_contracts": {
            "native_executor_api_sha256": NATIVE_EXECUTOR_SOURCE_API_SHA256_12003,
            "death_commit_api_sha256": DEATH_COMMIT_SOURCE_API_SHA256_12003,
        },
        "remaining_native_feedback": (
            "Actual selected Event+160 root/container-to-CCharacterDeathEffect instance binding remains an independent explicit witness; request or 3765780 return does not supply it.",
            "Actual global+C1 request mode, ordered manager queue and request-to-flush history are not published by the current-person query.",
            "Entry detach, backing/roster cleanup and independent preparation setter receivers are not granted by alive/reason readback.",
            "Other selected effect requests and native resource/trait modifiers remain separate from this bounded death-stage composition.",
        ),
        "current_observations_rewritten": False,
        "observed_native_execution": False,
        "native_queue_admission_observed_by_adapter": False,
        "native_callback_admission_observed_by_adapter": False,
        "public_horizon_resumed": False,
        "full_script_feedback_ready": False,
        "complete_transition": False,
        "actual_game_days_advanced": 0,
    }
