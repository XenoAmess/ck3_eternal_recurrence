#pragma once

#include <cstdint>
#include <optional>
#include <span>
#include <string>

namespace xar::ck3_12004 {

struct PrisonerSupportPredicate3727580Readonly12004 {
  std::optional<std::int32_t> vector10_count_raw_i32;
  std::optional<std::uint64_t> vector30_data_raw_u64;
  std::optional<std::int32_t> vector30_count_raw_i32;
  std::optional<std::uint8_t> al_raw_u8;
  std::string unavailable_reason;
};

// The caller supplies its source-defined copied support and per-byte mask in
// the existing query frame. Nonzero mask bytes mean defined copied bytes.
// Actual81B 3727580..37275D1 is pure: counts10/30 zero return canonical AL0.
// The QWORD+30 load remains required even though an empty loop uses no rows.
// Nonempty paths need element operands outside the copied80-byte header and
// remain unknown here. No physical destination or native call is introduced.
PrisonerSupportPredicate3727580Readonly12004
ProjectPrisonerSupportPredicate3727580FreshEmpty12004(
    std::span<const std::uint8_t> copied_support80,
    std::span<const std::uint8_t> defined_mask80) noexcept;

} // namespace xar::ck3_12004
