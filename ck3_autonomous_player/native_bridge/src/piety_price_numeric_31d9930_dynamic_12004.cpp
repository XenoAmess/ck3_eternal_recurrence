#include "xar_bridge/piety_price_numeric_31d9930_dynamic_12004.hpp"

#include <limits>
#include <utility>

namespace xar::ck3_12004::piety_price_raw_inputs {

Numeric31D9930DynamicObservation12004 ReadPietyPriceNumeric31D9930Dynamic12004(
    const Numeric31D9930DynamicBindings12004 &bindings,
    std::uintptr_t definition, std::uintptr_t current_rite,
    std::uint64_t unchanged_snapshot_revision) {
  Numeric31D9930DynamicObservation12004 out;
  out.definition_pointer = definition;
  out.current_rite_pointer = current_rite;
  out.frame_key = unchanged_snapshot_revision;
  if (!bindings.access.exact_12004_bound || !bindings.access.guarded_read) {
    out.reason = "numeric31d9930_dynamic_exact_read_binding_unavailable";
    return out;
  }
  if (!definition ||
      definition > (std::numeric_limits<std::uintptr_t>::max)() - 0x760) {
    out.reason = "numeric31d9930_dynamic_expression_pointer_unavailable";
    return out;
  }
  out.selected_expression_identity = definition + 0x760;
  out.dynamic_input_copy = CopyPietyPriceNumericDynamicInputs12004(
      bindings, definition, current_rite, *out.selected_expression_identity,
      unchanged_snapshot_revision);
  if ((out.dynamic_input_copy.selected_expression_matches &&
       !*out.dynamic_input_copy.selected_expression_matches) ||
      (out.dynamic_input_copy.unchanged_revision_matches &&
       !*out.dynamic_input_copy.unchanged_revision_matches)) {
    out.reason = out.dynamic_input_copy.input_copy_reason;
    return out;
  }
  auto evaluator = ProjectSelectedPietyPriceEax12004(
      bindings.access, out.dynamic_input_copy.inputs);
  out.native_eax_raw = evaluator.eax_raw_i32;
  out.source_ready = out.native_eax_raw.has_value();
  if (out.source_ready) {
    out.status = "available";
    out.reason = "actual31d9930_dynamic_selected_eax_available";
  } else {
    out.reason = evaluator.unavailable_reason;
  }
  out.evaluator = std::move(evaluator);
  return out;
}

bool ReadPietyPriceNumeric31D9930DynamicAdapter12004(
    void *binding_context,
    const construction_owner_mode3::RawReceiverAccessV1 &access,
    std::uintptr_t definition, std::uintptr_t current_rite,
    std::uint64_t unchanged_snapshot_revision, std::int32_t &out) noexcept {
  try {
    Numeric31D9930DynamicBindings12004 bindings;
    if (binding_context)
      bindings = *static_cast<const Numeric31D9930DynamicBindings12004 *>(
          binding_context);
    bindings.access = BindPietyPriceNumericRawAccess12004(access);
    const auto result = ReadPietyPriceNumeric31D9930Dynamic12004(
        bindings, definition, current_rite, unchanged_snapshot_revision);
    if (!result.source_ready || !result.native_eax_raw) return false;
    out = *result.native_eax_raw;
    return true;
  } catch (...) {
    return false;
  }
}

} // namespace xar::ck3_12004::piety_price_raw_inputs
