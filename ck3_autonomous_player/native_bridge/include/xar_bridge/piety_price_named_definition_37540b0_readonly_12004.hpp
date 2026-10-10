#pragma once

#include "xar_bridge/piety_price_numeric_access_12004.hpp"

#include <cstdint>
#include <optional>
#include <string>

namespace xar::ck3_12004::piety_price_raw_inputs {

struct PietyPriceNamedDefinition37540B0Readonly12004 {
  std::uintptr_t module_base = 0;
  std::uintptr_t named_definition_identity = 0;
  std::uint64_t unchanged_snapshot_revision = 0;
  std::optional<std::uintptr_t> provider_first_raw;
  std::optional<std::uintptr_t> provider_after_raw;
  std::optional<std::uint8_t> enabled_first_raw_u8;
  std::optional<std::uint8_t> enabled_after_raw_u8;
  std::optional<std::int32_t> value_first_raw_i32;
  std::optional<std::int32_t> value_after_raw_i32;
  std::optional<std::int32_t> eax_raw_i32;
  std::string unavailable_reason;
};

// ActualA0F2AF supplies RCX=[expression+A0], RDX=actualpack, R8=0,
// R9=originalnamedtuple. With QWORDnameddef+70NULL, neither pack nor R8/R9
// contributes to the numeric branch. BYTE+7A0 returns the initialized EDI0;
// nonzero reads exact DWORD+60. No value read is demanded by the zero branch.
// The copied operands receive narrow bookends. Equality does not prove an
// atomic snapshot, freshness, profiler effects or actual native consumption.
// Nonnull+70 preserves the virtualproducer/37498A0 numeric frontier.
PietyPriceNamedDefinition37540B0Readonly12004
ReadPietyPriceNamedDefinition37540B0Readonly12004(
    const PietyPriceNumericAccess12004 &access,
    std::uintptr_t actual_named_definition_identity,
    std::uint64_t unchanged_snapshot_revision) noexcept;

} // namespace xar::ck3_12004::piety_price_raw_inputs
