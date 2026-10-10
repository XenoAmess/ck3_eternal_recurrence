#pragma once

#include "xar_bridge/prisoner_quote_readonly_source_12004.hpp"
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>

namespace xar::ck3_12004 {

struct PrisonerScopeVectorCopy260E04012004 {
  PrisonerQuoteSourceFrame12004 frame;
  std::uintptr_t source_scope_identity = 0;
  std::uintptr_t source_vector_identity = 0;
  std::optional<std::uintptr_t> source_data_identity;
  std::optional<std::int32_t> count_i32;
  bool copied_shape_ready = false;
  bool allocation_required = false;
  std::string unavailable_reason;

  // Fresh373ACF0 clone after48c8895D0, then the actual260E040 no-allocation
  // copy. These are relations to the logical clone, without a fabricated
  // numeric native clone address. Both data and allocator are known nonnull.
  std::int32_t destination_capacity_i32 = 8;
  std::uint16_t data_clone_relative_offset = 0x38;
  std::uint16_t allocator_clone_relative_offset = 0x30;
  std::array<std::byte, 8 * 24> inline_raw{};
  std::array<std::uint8_t, 8 * 24> source_defined_inline_mask{};
  std::size_t copied_inline_bytes = 0;
};

// Source vector is original scope+18 from the owning current query. Copies
// signed count exactly (including negative), and raw24B cells for count1..8.
// Pointer-looking cell bytes keep their original raw bits; no rebasing occurs.
// Count<=0 defines no inline bytes and preserves the nonnull self relation.
// Count>8 requires an allocator result identity/effect witness and stays
// unavailable here. No native copy, allocator, destructor or initializer call.
PrisonerScopeVectorCopy260E04012004 ReadPrisonerScopeVectorCopy260E04012004(
    const PrisonerQuoteReadOnlyAccess12004 &access,
    const PrisonerQuoteSourceFrame12004 &frame,
    std::uintptr_t source_scope);

} // namespace xar::ck3_12004
