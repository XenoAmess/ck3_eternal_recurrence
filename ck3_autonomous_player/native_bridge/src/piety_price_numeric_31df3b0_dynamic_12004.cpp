#include "xar_bridge/piety_price_numeric_31df3b0_dynamic_12004.hpp"

#include <limits>

namespace xar::ck3_12004::piety_price_raw_inputs {

Numeric31DF3B0DynamicObservation12004 ReadPietyPriceNumeric31DF3B0Dynamic12004(
    const Numeric31DF3B0DynamicBindings12004 &bindings,
    std::uintptr_t definition, std::uintptr_t current_rite,
    std::uint64_t unchanged_snapshot_revision) {
  Numeric31DF3B0DynamicObservation12004 out;
  out.definition_pointer = definition;
  out.current_rite_pointer = current_rite;
  out.frame_key = unchanged_snapshot_revision;
  if (!bindings.access.exact_12004_bound || !bindings.access.guarded_read) {
    out.reason = "numeric31df3b0_dynamic_exact_read_binding_unavailable";
    return out;
  }
  if (definition > (std::numeric_limits<std::uintptr_t>::max)() -
                       kPietyPrice31DF3B0ExpressionOffset12004) {
    out.reason = "numeric31df3b0_dynamic_expression_pointer_overflow";
    return out;
  }
  const auto selected = definition + kPietyPrice31DF3B0ExpressionOffset12004;
  out.selected_expression_identity = selected;
  out.dynamic_input_copy = CopyPietyPriceNumericDynamicInputs12004(
      bindings, definition, current_rite, selected,
      unchanged_snapshot_revision);
  if ((out.dynamic_input_copy.selected_expression_matches &&
       !*out.dynamic_input_copy.selected_expression_matches) ||
      (out.dynamic_input_copy.unchanged_revision_matches &&
       !*out.dynamic_input_copy.unchanged_revision_matches)) {
    out.reason = out.dynamic_input_copy.input_copy_reason;
    return out;
  }
  out.evaluator.emplace(ProjectSelectedPietyPriceEax12004(
      bindings.access, out.dynamic_input_copy.inputs));
  const auto &child = *out.evaluator;
  if (child.module_base != bindings.access.module_base ||
      child.expression_identity != selected ||
      child.unchanged_snapshot_revision != unchanged_snapshot_revision) {
    out.reason = "numeric31df3b0_dynamic_evaluator_identity_mismatch";
    return out;
  }
  if (!child.unavailable_reason.empty()) {
    out.reason = child.unavailable_reason;
    return out;
  }
  if (!child.eax_raw_i32) {
    out.reason = "numeric31df3b0_dynamic_eax_unavailable";
    return out;
  }
  out.native_eax_raw = child.eax_raw_i32;
  out.source_ready = true;
  out.status = "available";
  out.reason = "actual31df3b0_dynamic_selected_eax_available";
  return out;
}

bool ReadPietyPriceNumeric31DF3B0DynamicAdapter12004(
    void *binding_context,
    const construction_owner_mode3::RawReceiverAccessV1 &access,
    std::uintptr_t definition, std::uintptr_t current_rite,
    std::uint64_t unchanged_snapshot_revision, std::int32_t &out) noexcept {
  try {
    Numeric31DF3B0DynamicBindings12004 bindings;
    if (binding_context)
      bindings = *static_cast<const Numeric31DF3B0DynamicBindings12004 *>(
          binding_context);
    bindings.access = BindPietyPriceNumericRawAccess12004(access);
    const auto result = ReadPietyPriceNumeric31DF3B0Dynamic12004(
        bindings, definition, current_rite, unchanged_snapshot_revision);
    if (!result.source_ready || !result.native_eax_raw ||
        result.definition_pointer != definition ||
        result.current_rite_pointer != current_rite ||
        result.frame_key != unchanged_snapshot_revision ||
        result.source_pin != kPietyPrice31DF3B0SourcePin12004) return false;
    out = *result.native_eax_raw;
    return true;
  } catch (...) {
    return false;
  }
}

} // namespace xar::ck3_12004::piety_price_raw_inputs
