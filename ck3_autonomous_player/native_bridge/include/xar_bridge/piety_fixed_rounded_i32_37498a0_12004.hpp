#pragma once

#include "xar_bridge/piety_price_numeric_access_12004.hpp"

#include <cstdint>
#include <optional>

namespace xar::ck3_12004::piety_price_raw_inputs {

struct PietyFixedRoundedI3237498A012004 {
  std::uintptr_t module_base = 0;
  std::uintptr_t original_named_tuple_identity = 0;
  std::uint64_t unchanged_snapshot_revision = 0;
  std::optional<std::int64_t> raw_q64_i64;
  std::optional<bool> native_non_diagnostic_branch;
  std::optional<std::int32_t> eax_raw_i32;
  bool source_ready = false;
  const char *unavailable_reason = "piety_fixed_round_37498a0_raw_q64_unavailable";
};

// Actual A0F18B loads a signed Q64 value, then A0F18F passes that value in
// RCX and the original parent named tuple in RDX. The operand must come from
// the caller's actual provider-output witness. This pure projection neither
// obtains that witness nor evaluates the provider. The exact native guard
// bypasses every tuple read and child call. Revision zero and a null tuple
// remain valid carriers for that source-closed branch.
PietyFixedRoundedI3237498A012004 ProjectPietyFixedRoundedI3237498A012004(
    const PietyPriceNumericAccess12004 &access,
    std::optional<std::int64_t> actual_raw_q64_i64,
    std::uintptr_t original_named_tuple_identity,
    std::uint64_t unchanged_snapshot_revision) noexcept;

} // namespace xar::ck3_12004::piety_price_raw_inputs
