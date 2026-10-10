#pragma once

#include "xar_bridge/piety_price_a0f0b0_readonly_12004.hpp"
#include "xar_bridge/source_defined_scratch3736040_12004.hpp"

#include <cstdint>
#include <optional>

namespace xar::ck3_12004::piety_price_raw_inputs {

inline constexpr std::uint32_t kPietyPriceEvaluatorWrapperRva12004 = 0x1233A40;
inline constexpr std::uint32_t kPietyPriceEvaluatorNumericCallRva12004 = 0x1233AB4;
inline constexpr std::uint32_t kPietyPriceEvaluatorReturnRva12004 = 0x1233B37;

// Actual1233A40 saves the numeric child's EAX in EBX and restores it after
// cleanup. Scalar fields retain the child's exact result. The independent
// masked initializer record is source provenance, without a physical call
// or pointer claim, and never qualifies or rejects the numeric result.
struct PietyPriceEvaluator1233A40Readonly12004
    : PietyPriceA0F0B0Readonly12004 {
  std::optional<SourceDefinedScratch373604012004> scratch_source;
};

// The original create/edit callers select definition+760/definition+2A8.
// This software projection keeps that selected operand unchanged. Numeric
// mode0 does not demand a Rite context, scratch initializer or name tuple.
inline PietyPriceEvaluator1233A40Readonly12004
ProjectSelectedPietyPriceEax12004(
    const PietyPriceNumericAccess12004 &access,
    std::uintptr_t selected_expression_identity,
    std::uint64_t unchanged_snapshot_revision) noexcept {
  PietyPriceEvaluator1233A40Readonly12004 out{};
  static_cast<PietyPriceA0F0B0Readonly12004 &>(out) =
      ReadPietyPriceA0F0B0Readonly12004(
      access, selected_expression_identity, unchanged_snapshot_revision);
  if (access.exact_12004_bound) {
    out.scratch_source.emplace();
    ProjectSourceDefinedScratch373604012004(
        access.module_base, kSourceDefinedScratch3736040ExecutableSha25612004,
        *out.scratch_source);
  }
  return out;
}

} // namespace xar::ck3_12004::piety_price_raw_inputs
