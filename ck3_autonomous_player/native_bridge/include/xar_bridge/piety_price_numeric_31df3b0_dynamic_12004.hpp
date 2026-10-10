#pragma once

#include "xar_bridge/piety_price_evaluator_1233a40_dynamic_readonly_12004.hpp"
#include "xar_bridge/piety_price_numeric_31df3b0_12004.hpp"
#include "xar_bridge/piety_price_numeric_dynamic_inputs_12004.hpp"

namespace xar::ck3_12004::piety_price_raw_inputs {

using Numeric31DF3B0DynamicBindings12004 = PietyPriceNumericDynamicBindings12004;

struct Numeric31DF3B0DynamicObservation12004 {
  bool source_ready = false;
  const char *status = "unavailable";
  std::string reason = "not_read";
  std::uintptr_t definition_pointer = 0;
  std::uintptr_t current_rite_pointer = 0;
  std::uint64_t frame_key = 0;
  std::string_view source_pin = kPietyPrice31DF3B0SourcePin12004;
  std::optional<std::uintptr_t> selected_expression_identity;
  std::optional<std::int32_t> native_eax_raw;
  PietyPriceNumericDynamicInputCopy12004 dynamic_input_copy;
  std::optional<PietyPriceA0F0B0DynamicReadonly12004> evaluator;
  bool actual_original_consumed_values = false;
};

// Actual31DF3C5 selects definition+2A8, forwarded as1233A40 RCX at31DF445.
// Shared22 copies nullable operands; unique11/40 own reached numeric reads.
// The native pack and R9 identity are never constructed from software bytes.
Numeric31DF3B0DynamicObservation12004 ReadPietyPriceNumeric31DF3B0Dynamic12004(
    const Numeric31DF3B0DynamicBindings12004 &bindings,
    std::uintptr_t definition, std::uintptr_t current_rite,
    std::uint64_t unchanged_snapshot_revision);

// Context points to const shared bindings, or nullptr for absent operands.
// Current reads use the actual parent RawReceiverAccess; false preserves out.
bool ReadPietyPriceNumeric31DF3B0DynamicAdapter12004(
    void *binding_context,
    const construction_owner_mode3::RawReceiverAccessV1 &access,
    std::uintptr_t definition, std::uintptr_t current_rite,
    std::uint64_t unchanged_snapshot_revision, std::int32_t &out) noexcept;

} // namespace xar::ck3_12004::piety_price_raw_inputs
