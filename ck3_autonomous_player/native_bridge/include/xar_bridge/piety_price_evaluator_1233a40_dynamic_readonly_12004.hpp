#pragma once

#include "xar_bridge/piety_price_evaluator_1233a40_readonly_12004.hpp"
#include "xar_bridge/piety_price_a0f0b0_dynamic_readonly_12004.hpp"

namespace xar::ck3_12004::piety_price_raw_inputs {

// Actual1233A40 preserves the numeric child's EAX through cleanup.
// Keep the owned dynamic operands and result unchanged at this seam.
inline PietyPriceA0F0B0DynamicReadonly12004
ProjectSelectedPietyPriceEax12004(
    const PietyPriceNumericAccess12004 &access,
    const PietyPriceA0F0B0DynamicInputs12004 &inputs) {
  return ReadPietyPriceA0F0B0DynamicReadonly12004(access, inputs);
}

} // namespace xar::ck3_12004::piety_price_raw_inputs
