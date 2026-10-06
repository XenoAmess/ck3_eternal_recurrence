"""Same-query actual target preparation, one physical core, real B refresh."""
from collections.abc import Mapping, Sequence

from .army_prepare_scoped_ordered_refill_assembly import conditional_prepared_ordered_inputs_v1
from .army_scoped_ordered_refill_projection import project_observed_prepared_ordered_physical_core_v1
from .army_ordered_refill_besieging_assault_projection import (
    project_ordered_refill_besieging_assault_from_physical_v1,
)

_INPUT_BASIS = "same_capture_ordered_B_fixed_chunk0_conditional_preparation_ordered_occurrences"


def project_fixed_chunk0_prepare_ordered_besieging_assault_v1(
    row: Mapping[str, object], preparation: Mapping[str, object],
) -> dict[str, object]:
    inputs = row.get("ordered_besieging_refill_inputs_v1")
    native_preparation = row.get("ordered_besieging_fixed_chunk0_preparation_inputs_v1")
    joins = []
    if isinstance(inputs, dict):
        private_inputs, joins = conditional_prepared_ordered_inputs_v1(
            inputs, preparation, input_name="ordered_besieging_fixed_chunk0_preparation_inputs_v1")
        physical = project_observed_prepared_ordered_physical_core_v1(
            private_inputs, prepared_input_basis=_INPUT_BASIS)
        calls = 1
    else:
        physical = {"input_basis": _INPUT_BASIS, "ordered_core_ready": False,
                    "context_basis": "held_nonphysical_native_army_unit_position_political_context",
                    "missing_inputs": ["ordered_besieging_refill_inputs_v1"],
                    "physical_chunks": [], "occurrences": [], "failed_persistent_ids": []}
        calls = 0
    result = project_ordered_refill_besieging_assault_from_physical_v1(row, physical)
    coverage = (isinstance(inputs, dict) and inputs.get("target_persistent_ids_complete") is True
                and preparation["target_persistent_ids_complete"] is True)
    same_context = (isinstance(native_preparation, dict) and isinstance(inputs, dict)
                    and native_preparation["province_id"] == inputs["province_id"])
    missing = list(result["missing_inputs"])
    failed = set(physical["failed_persistent_ids"])
    missing.extend(f'persistent:{join["persistent_regiment_id"]}:preparation:{key}'
                   for join in joins if join["persistent_regiment_id"] in failed
                   for key in join["missing_inputs"])
    if not coverage:
        missing.append("actual_target_persistent_ids_complete")
    if not same_context:
        missing.append("same_capture_ordered_B_preparation_Province")
    if not coverage or not same_context:
        # Preserve known scalars/physical/target rows, but not a full union sum
        # when the source domain itself is incomplete or not present.
        result.update(status="partial", conditional_besieging_strength_ready=False,
                      conditional_besieging_strength=None,
                      conditional_assault_expected_loss_ready=False,
                      conditional_assault_expected_loss=None)
        assault = result.get("assault_projection")
        if isinstance(assault, dict):
            result["assault_projection"] = {**assault, "ready": False,
                "conditional_expected_loss": None,
                "missing_inputs": list(dict.fromkeys([*assault["missing_inputs"],
                    "actual_target_persistent_ids_complete" if not coverage else
                    "same_capture_ordered_B_preparation_Province"]))}
    result.update(
        projection_kind="conditional_fixed_chunk0_prepare_ordered_besieging_assault",
        ordered_besieging_entry_mode="fixed_chunk0_prepare", input_basis=_INPUT_BASIS,
        context_basis="held_nonphysical_native_army_unit_position_political_context",
        b_context_basis="held_nonphysical_B_context",
        preparation_context_basis="current_frozen_context_preparation",
        conditional_preparation_projected=True,
        preparation_inputs_ready=preparation["preparation_ready"],
        target_persistent_ids_complete=bool(coverage), preparation_join=joins,
        physical_core_invocations=calls, cache_write=False, full_ordered_regular_refill=False,
        missing_inputs=list(dict.fromkeys(missing)))
    return result


def project_fixed_chunk0_prepare_ordered_besieging_assaults_v1(
    rows: Sequence[Mapping[str, object]], preparations: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    return [project_fixed_chunk0_prepare_ordered_besieging_assault_v1(row, prep)
            for row, prep in zip(rows, preparations, strict=True)]
