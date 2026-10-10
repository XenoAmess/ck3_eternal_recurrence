#pragma once

#include "xar_bridge/piety_price_evaluator_1233a40_dynamic_readonly_12004.hpp"
#include "xar_bridge/piety_price_numeric_dynamic_inputs_12004.hpp"

namespace xar::ck3_12004::piety_price_raw_inputs {

using Numeric31D9930DynamicBindings12004 = PietyPriceNumericDynamicBindings12004;

struct Numeric31D9930DynamicObservation12004 {
  bool source_ready = false;
  const char *status = "unavailable";
  std::string reason;
  std::optional<std::int32_t> native_eax_raw;
  std::uintptr_t definition_pointer = 0;
  std::uintptr_t current_rite_pointer = 0;
  std::uint64_t frame_key = 0;
  const char *source_pin =
      "73f026b43bd7ba74cb7f3ea915c281f247b955cbd978cd9f1262bea6c2e77d8b";
  std::optional<std::uintptr_t> selected_expression_identity;
  PietyPriceNumericDynamicInputCopy12004 dynamic_input_copy;
  std::optional<PietyPriceA0F0B0DynamicReadonly12004> evaluator;
  bool actual_original_consumed_values = false;
};

// Independent dynamic successor. Actual31D9945/31D99C5 select definition+760.
// The unique11 dynamic overload and unique40 core retain all reached operands,
// nullable pack/provider/R9 and full revision. No native call is made.
Numeric31D9930DynamicObservation12004 ReadPietyPriceNumeric31D9930Dynamic12004(
    const Numeric31D9930DynamicBindings12004 &bindings,
    std::uintptr_t definition, std::uintptr_t current_rite,
    std::uint64_t unchanged_snapshot_revision);

// Context may point to the new binding/resolver. The supplied parent RawAccess
// owns the current reads. Output changes only when the raw EAX is available.
bool ReadPietyPriceNumeric31D9930DynamicAdapter12004(
    void *binding_context,
    const construction_owner_mode3::RawReceiverAccessV1 &access,
    std::uintptr_t definition, std::uintptr_t current_rite,
    std::uint64_t unchanged_snapshot_revision, std::int32_t &out) noexcept;

} // namespace xar::ck3_12004::piety_price_raw_inputs
