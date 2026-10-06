#include "xar_bridge/ck3_12003_ordered_besieging_fixed_chunk0_preparation.hpp"
#include "xar_bridge/army_ordered_besieging_refill_inputs_v1.hpp"
#include "xar_bridge/ck3_12002_army.hpp"

namespace xar::ck3_12003 {
game::ArmyOrderedBesiegingFixedChunk0PreparationInputsV1
ReadOrderedBesiegingFixedChunk0PreparationInputs12003(
    const ck3_12002::ArmyBindings &bindings,
    const game::ArmyOrderedBesiegingRefillInputsV1 &scope) noexcept {
  game::ArmyOrderedBesiegingFixedChunk0PreparationInputsV1 result{};
  result.subject_army_id = scope.subject_army_id;
  result.subject_carmy_id = scope.subject_carmy_id;
  result.province_id = scope.province_id;
  result.target_persistent_ids_complete = scope.target_persistent_ids_complete;
  result.source_scope_status = scope.status == "available"
      ? game::FixedChunk0PreparationInputStatusV1::available
      : scope.status == "partial" ? game::FixedChunk0PreparationInputStatusV1::partial
                                  : game::FixedChunk0PreparationInputStatusV1::unavailable;
  if (!bindings.enabled) {
    result.unavailable_reason = "ordered_B_fixed_chunk0_preparation_bindings_unavailable";
    return result;
  }
  bool complete = result.target_persistent_ids_complete;
  result.persistent_regiments.reserve(scope.persistent_regiments.size());
  // The actual B producer already materializes the unique target DATA union.
  // Keep its domain/order; do not scan subject DATA or execution duplicates.
  for (const auto &persistent : scope.persistent_regiments) {
    auto row = ReadFixedChunk0PreparationPersistentInput12003(
        bindings, persistent.persistent_regiment_id);
    complete = complete && row.status == game::FixedChunk0PreparationInputStatusV1::available;
    result.persistent_regiments.push_back(row);
  }
  result.status = complete ? game::FixedChunk0PreparationInputStatusV1::available
      : result.persistent_regiments.empty() && scope.status == "unavailable"
          ? game::FixedChunk0PreparationInputStatusV1::unavailable
          : game::FixedChunk0PreparationInputStatusV1::partial;
  if (!complete) result.unavailable_reason = result.target_persistent_ids_complete
      ? "ordered_B_fixed_chunk0_preparation_operands_partial"
      : "ordered_B_target_persistent_scope_incomplete";
  return result;
}
} // namespace xar::ck3_12003
