#pragma once

#include "xar_bridge/construction_owner_mode3_raw_receiver_12004.hpp"

#include <optional>

namespace xar::ck3_12004 {

inline constexpr std::uintptr_t kM4SubobjectPredicateEntry12004 = 0x2C39EE0;

struct M4SubobjectPredicateSource12004 {
  std::uintptr_t original_subobject_identity = 0;
  std::uint64_t unchanged_snapshot_revision = 0;
  std::optional<std::uint32_t> count_1c_raw_u32;
  std::optional<std::uintptr_t> first_data_identity;
  std::optional<std::uintptr_t> selected_object_identity;
  std::optional<std::uint32_t> selected_magic_38_raw_u32;
  std::optional<std::uintptr_t> flag_data_identity;
  std::optional<std::uint8_t> flag_08_raw_u8;
  std::optional<std::uint8_t> output_al;
  bool source_complete = false;
};

// Actual RCX is the Province+620 subobject, not the parent's RDI=[RCX].
// Only AL0/AL1 is defined by2C39EE0. A successful AL0 differs from unavailable
// copied inputs; failure preserves out. Revision is retained as full64 caller
// metadata without creating another native branch or revision validity gate.
bool ReadM4SubobjectPredicate12004(
    const construction_owner_mode3::RawReceiverAccessV1 &access,
    std::uintptr_t actual_subobject, std::uint64_t unchanged_snapshot_revision,
    bool &out, M4SubobjectPredicateSource12004 *source = nullptr) noexcept;

// Matches13e's source-owned read_2c39ee0 binding. Context is unused.
bool ReadM4SubobjectPredicateAdapter12004(
    void *context, const construction_owner_mode3::RawReceiverAccessV1 &access,
    std::uintptr_t actual_subobject, std::uint64_t unchanged_snapshot_revision,
    bool &out) noexcept;

} // namespace xar::ck3_12004
