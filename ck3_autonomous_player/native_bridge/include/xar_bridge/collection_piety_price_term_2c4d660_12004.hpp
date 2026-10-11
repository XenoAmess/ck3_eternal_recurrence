#pragma once

#include "xar_bridge/construction_scaled_key_2c4d530_12004.hpp"
#include "xar_bridge/piety_price_numeric_access_12004.hpp"

#include <cstdint>
#include <optional>
#include <string_view>

namespace xar::ck3_12004::piety_price_raw_inputs {

struct CollectionPietyPriceTerm2C4D660Result12004 {
  std::uint32_t actual_callee_rva = 0x2C4D660;
  std::uint64_t mode_raw_q64 = 0;
  std::uint64_t source_revision_raw_u64 = 0;
  construction_owner_mode3::ScaledCollectionKey12004 selected;
  std::optional<std::int64_t> scaled_term_raw_q64;
  bool source_ready = false;
  std::string_view unavailable_reason;
};

// Actual2C64D27 consumes key223; actual2C62D56 consumes key224. Both supply
// R9=0 and fifth Q64 scale100000. Independent573B source closure proves that
// this mode reaches the existing2438980 keyed reader and identical signed
// Q100000 arithmetic. Other R9 modes have separate audit/string effects.
// Caller owns the actual collection and same-query association; revision is
// carried unchanged and does not manufacture a frame or native observation.
CollectionPietyPriceTerm2C4D660Result12004
ReadCollectionPietyPriceTerm2C4D66012004(
    const PietyPriceNumericAccess12004 &access,
    std::uintptr_t collection_identity, std::uint32_t incoming_key_raw_u32,
    std::int64_t scale_raw_q64, std::uint64_t source_revision_raw_u64);

} // namespace xar::ck3_12004::piety_price_raw_inputs
