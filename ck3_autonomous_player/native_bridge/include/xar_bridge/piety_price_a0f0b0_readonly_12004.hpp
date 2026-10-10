#pragma once

#include "xar_bridge/piety_price_numeric_access_12004.hpp"

#include <cstdint>
#include <optional>
#include <string>

namespace xar::ck3_12004::piety_price_raw_inputs {

struct PietyPriceA0F0B0Readonly12004 {
  std::uintptr_t module_base = 0;
  std::uintptr_t expression_identity = 0;
  std::uint64_t unchanged_snapshot_revision = 0;
  std::optional<std::int32_t> mode_raw_i32;
  std::optional<std::int32_t> eax_first_raw_i32;
  std::optional<std::int32_t> mode_after_raw_i32;
  std::optional<std::int32_t> eax_after_raw_i32;
  std::optional<std::int32_t> eax_raw_i32;
  std::string unavailable_reason;
};

// Current1233AB4/31BD3E4 callers supply literalR8=0. ActualA0F0B0 mode+B8
// zero returns DWORD+98 before pack, named tuple, profile or scratch inputs.
// Revision is the caller's unchanged carrier, not a new numeric prerequisite.
// Mode0 recopy of the two reached operands guards this conditional copied
// input; equality does not claim freshness or actual native consumption.
// Nonzero modes preserve the reached child frontier until its operands close.
PietyPriceA0F0B0Readonly12004 ReadPietyPriceA0F0B0Readonly12004(
    const PietyPriceNumericAccess12004 &access,
    std::uintptr_t selected_expression_identity,
    std::uint64_t unchanged_snapshot_revision) noexcept;

} // namespace xar::ck3_12004::piety_price_raw_inputs
