#pragma once

#include "xar_bridge/construction_owner_mode3_raw_receiver_12004.hpp"
#include "xar_bridge/piety_price_a0f0b0_dynamic_readonly_12004.hpp"
#include "xar_bridge/piety_price_numeric_access_12004.hpp"

#include <utility>

namespace xar::ck3_12004::piety_price_raw_inputs {

using ReadPietyPriceNumericDynamicInputs12004 = bool (*)(
    void *, const PietyPriceNumericAccess12004 &, std::uintptr_t definition,
    std::uintptr_t current_rite, std::uint64_t unchanged_snapshot_revision,
    PietyPriceA0F0B0DynamicInputs12004 &out) noexcept;

struct PietyPriceNumericDynamicBindings12004 {
  PietyPriceNumericAccess12004 access;
  void *dynamic_context = nullptr;
  ReadPietyPriceNumericDynamicInputs12004 read_dynamic_inputs = nullptr;
};

struct PietyPriceNumericDynamicInputCopy12004 {
  PietyPriceA0F0B0DynamicInputs12004 inputs;
  bool callback_attempted = false;
  bool callback_returned_inputs = false;
  std::optional<bool> selected_expression_matches;
  std::optional<bool> unchanged_revision_matches;
  std::string input_copy_reason;
};

// The source-owned scalar selects the expression and carries the revision.
// The callback copies actual nullable operands; it cannot choose a different
// expression/frame or use equality alone to claim a native provider output.
// Absent/failed copies do not gate branches that consume none of these fields.
inline PietyPriceNumericDynamicInputCopy12004
CopyPietyPriceNumericDynamicInputs12004(
    const PietyPriceNumericDynamicBindings12004 &bindings,
    std::uintptr_t definition, std::uintptr_t current_rite,
    std::uintptr_t selected_expression,
    std::uint64_t unchanged_snapshot_revision) {
  PietyPriceNumericDynamicInputCopy12004 out;
  out.inputs.expression_identity = selected_expression;
  out.inputs.unchanged_snapshot_revision = unchanged_snapshot_revision;
  if (!bindings.read_dynamic_inputs) {
    out.input_copy_reason = "piety_dynamic_operand_callback_absent";
    return out;
  }
  out.callback_attempted = true;
  auto copied = out.inputs;
  if (!bindings.read_dynamic_inputs(
          bindings.dynamic_context, bindings.access, definition, current_rite,
          unchanged_snapshot_revision, copied)) {
    out.input_copy_reason = "piety_dynamic_operand_copy_unavailable";
    return out;
  }
  out.callback_returned_inputs = true;
  out.selected_expression_matches =
      copied.expression_identity == selected_expression;
  out.unchanged_revision_matches =
      copied.unchanged_snapshot_revision == unchanged_snapshot_revision;
  out.inputs = std::move(copied);
  if (!*out.selected_expression_matches || !*out.unchanged_revision_matches)
    out.input_copy_reason = "piety_dynamic_operand_source_identity_mismatch";
  return out;
}

inline bool ReadPietyPriceNumericFromRawAccess12004(
    void *context, const void *source, void *out, std::size_t size) noexcept {
  const auto *access =
      static_cast<const construction_owner_mode3::RawReceiverAccessV1 *>(context);
  if (!access || !access->read_memory) return false;
  try {
    return access->read_memory(access->context, source, out, size);
  } catch (...) {
    return false;
  }
}

// Reads always use the exact RawReceiver access supplied by the current parent.
// No separate reader or native physical pack identity is synthesized here.
inline PietyPriceNumericAccess12004 BindPietyPriceNumericRawAccess12004(
    const construction_owner_mode3::RawReceiverAccessV1 &access) noexcept {
  PietyPriceNumericAccess12004 out;
  out.module_base = access.module_base;
  out.context = const_cast<construction_owner_mode3::RawReceiverAccessV1 *>(&access);
  out.guarded_read = ReadPietyPriceNumericFromRawAccess12004;
  out.exact_12004_bound = access.exact_12004_bound;
  return out;
}

} // namespace xar::ck3_12004::piety_price_raw_inputs
