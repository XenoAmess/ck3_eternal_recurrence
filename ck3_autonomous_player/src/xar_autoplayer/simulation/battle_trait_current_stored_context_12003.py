"""Project the dedicated current stored-model observation, without native calls.

Frozen CK3 1.20.0.3 v86 current-array ABI and direct reset-count source.
Observed storage, the numerical shape and conditional reset effects are
independent results; none supplies a historical completed-reset admission.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Mapping

from .battle_trait_numeric_inputs_12003 import (
    native_wrap32_12003,
    native_wrap64_12003,
)


@dataclass(frozen=True, slots=True)
class CurrentStoredContextProjection12003:
    character_full_id: int | None
    status: str
    observed_state: Mapping[str, object] | None
    raw_context_projection: Mapping[str, object] | None
    numeric_context_ready: bool
    numeric_missing_inputs: tuple[str, ...]
    known_context_components: Mapping[str, object] | None
    reset_input_projection: Mapping[str, object]
    ledger: Mapping[str, object]
    native_write_performed: bool = False
    completed_reset_admission_constructed: bool = False
    historical_pre_prefix_state_ready: bool = False
    full_future_context_ready: bool = False
    actual_game_days_advanced: int = 0

    @property
    def context(self) -> Mapping[str, object] | None:
        return self.raw_context_projection

    @property
    def missing_inputs(self) -> tuple[str, ...]:
        return self.numeric_missing_inputs


def _gap(missing: list[str], path: str) -> None:
    if path not in missing:
        missing.append(path)


def _count(header: object) -> int | None:
    value = header.get("count") if isinstance(header, Mapping) else None
    return native_wrap32_12003(value) if type(value) is int else None


def _active_array(
    header: object, path: str, element_type: str, missing: list[str],
) -> tuple[int | None, list[int] | None]:
    count = _count(header)
    if count is None:
        _gap(missing, path + ".count")
        return None, None
    if count < 0:
        _gap(missing, path + ".negative_active_extent")
        return count, None
    if count == 0:
        return count, []
    items = header.get("items")
    if not isinstance(items, (tuple, list)) or len(items) < count:
        _gap(missing, path + ".items")
        return count, None
    copied: list[int] = []
    valid = True
    for index, value in enumerate(items[:count]):
        if type(value) is not int or (element_type == "U16" and not 0 <= value <= 65535):
            _gap(missing, path + ".items[" + str(index) + "]")
            valid = False
        else:
            copied.append(value if element_type == "U16" else native_wrap64_12003(value))
    return count, copied if valid else None


def _paired_properties(
    block: object, path: str, missing: list[str],
) -> Mapping[str, object] | None:
    if not isinstance(block, Mapping):
        _gap(missing, path)
        return None
    key_count, keys = _active_array(block.get("key_array"), path + ".key_array", "U16", missing)
    value_count, values = _active_array(block.get("value_array"), path + ".value_array", "S64Q", missing)
    if key_count is not None and value_count is not None and key_count != value_count:
        _gap(missing, path + ".paired_key_value_counts")
    if keys is None or values is None or key_count != value_count:
        return None
    return {"keys_u16": keys, "values_q64": values, "count": key_count}


def _direct_reset_projection(raw: Mapping[str, object]) -> Mapping[str, object]:
    before = tuple(_count(raw.get(name)) for name in ("weighted", "key_array", "value_array"))
    weighted = before[0]
    if weighted is None:
        nonzero = None
        after = (None, None, None)
        branch = "weighted_count_unavailable"
    elif weighted != 0:
        nonzero = True
        after = (0, 0, 0)
        branch = "weighted_nonzero_direct_clear_three_counts"
    else:
        nonzero = False
        after = before
        branch = "weighted_zero_direct_preserve_independent_counts"
    return {
        "current_counts_i32": before,
        "weighted_count_nonzero": nonzero,
        "direct_after_counts_i32": after,
        "predicate_ready": weighted is not None,
        "counts_projection_ready": all(value is not None for value in after),
        "branch": branch,
        "missing_inputs": tuple("current_stored_counts[" + str(index) + "]"
                                for index, value in enumerate(after) if value is None),
        "meaning": "Conditional direct count effects if source reset were called with these current operands",
        "native_reset_called": False,
        "cleanup_completion_inferred": False,
        "completed_reset_admission_constructed": False,
        "historical_stage_inferred": False,
    }


def project_current_stored_context_state_12003(
    payload: Mapping[str, object] | None, *,
    source_provenance: Mapping[str, object] | None = None,
) -> CurrentStoredContextProjection12003:
    """Consume current_person_state.current_stored_context_state as supplied.

    Original independent headers/arrays remain intact even when no complete
    paired numerical context can be produced. Capacity and owner mismatch are
    diagnostics rather than numerical gates. This function never substitutes
    the old raw getter's selected fallback for the actual stored model.
    """
    raw = payload if isinstance(payload, Mapping) else {}
    observed = deepcopy(payload) if isinstance(payload, Mapping) else None
    missing: list[str] = []
    reset = _direct_reset_projection(raw)
    aggregate = None
    weighted_count = _count(raw.get("weighted"))
    projected_rows: list[Mapping[str, object]] | None = None
    if observed is None:
        _gap(missing, "current_stored_context_state")
    if raw.get("model_present") is not True:
        _gap(missing, "current_stored_context_state.model_present")
    else:
        aggregate = _paired_properties(raw, "aggregate", missing)
        if weighted_count is None:
            _gap(missing, "weighted.count")
        elif weighted_count < 0:
            _gap(missing, "weighted.negative_active_extent")
        elif weighted_count == 0:
            projected_rows = []
        else:
            weighted_header = raw.get("weighted")
            items = weighted_header.get("items")
            if not isinstance(items, (tuple, list)) or len(items) < weighted_count:
                _gap(missing, "weighted.items")
            else:
                projected_rows = []
                for position, row in enumerate(items[:weighted_count]):
                    path = "weighted.items[" + str(position) + "]"
                    if not isinstance(row, Mapping):
                        _gap(missing, path)
                        projected_rows.append({"native_index": None, "properties": None, "weight_q64": None})
                        continue
                    properties = _paired_properties(row.get("property_block"), path + ".property_block", missing)
                    weight = row.get("weight_raw")
                    if type(weight) is not int:
                        _gap(missing, path + ".weight_raw")
                        weight = None
                    else:
                        weight = native_wrap64_12003(weight)
                    projected_rows.append({
                        "native_index": row.get("native_index"),
                        "properties": properties, "weight_q64": weight,
                    })
    known = ({"aggregate_properties": aggregate, "weighted_rows": projected_rows,
              "weighted_count": weighted_count} if raw.get("model_present") is True else None)
    ready = raw.get("model_present") is True and not missing
    complete = deepcopy(known) if ready else None
    ledger = {
        "source_scope": "dedicated_current_stored_model_observation_and_direct_count_primitive",
        "input_source": deepcopy(source_provenance),
        "carrier_presence": "value" if observed is not None else "null_or_absent",
        "carrier_available_diagnostic": raw.get("available"),
        "carrier_reason": raw.get("reason"),
        "character_full_id": raw.get("character_full_id"),
        "scratch_address": raw.get("scratch_address"),
        "stored_model_address": raw.get("model_address"),
        "inline_context_address": raw.get("context_address"),
        "owner_address": raw.get("owner_address"),
        "owner_character_full_id": raw.get("owner_character_full_id"),
        "bound_to_requested_character": raw.get("bound_to_requested_character"),
        "pending_raw_diagnostic": raw.get("pending_raw"),
        "owned_count_raw_diagnostic": raw.get("owned_count_raw"),
        "producer_reset_input_diagnostic": deepcopy(raw.get("reset_input")),
        "capacities_are_diagnostic": True,
        "independent_header_counts_preserved": True,
        "negative_count_clamped_to_zero": False,
        "native_order_duplicate_FFFF_zero_negative_values_preserved": True,
        "stored_observation_dropped_on_owner_mismatch": False,
        "old_raw_selected_fallback_used_as_stored_model": False,
        "numeric_projection_scope":
            "Stored model arrays only; caller supplies any other actual numerical "
            "operands and their actor association explicitly. Projection completeness "
            "is not requested Character native parity.",
        "reset_projection_uses_array_readiness_as_gate": False,
        "pending_count_pointer_used_as_history_proof": False,
        "current_final_context_renamed_pre_prefix": False,
        "completed_reset_admission_constructed": False,
        "full_future_context_ready": False,
        "Entry_refresh_claim": False,
        "native_write_performed": False,
        "actual_game_days_advanced": 0,
        "source_contracts": {
            "current_ABI": "a977377d3d28e637b0d3c1845c1d49407419a98c5bf17b445f7f86db87e6c1ab",
            "reset_control": "707aa3ad9f7877ffd51f0ef7efe992f33675de19a57a58897b7ddc888ce9a51a",
            "consumer_source_API": "90486b2ea5f133ce316afb1c62faf55fa4f6be39d04199e1d026a452ab6e2b30",
        },
    }
    return CurrentStoredContextProjection12003(
        character_full_id=raw.get("character_full_id"),
        status="computed" if ready else "partial" if observed is not None else "unavailable",
        observed_state=observed, raw_context_projection=complete,
        numeric_context_ready=ready, numeric_missing_inputs=tuple(missing),
        known_context_components=deepcopy(known), reset_input_projection=reset,
        ledger=ledger,
    )
