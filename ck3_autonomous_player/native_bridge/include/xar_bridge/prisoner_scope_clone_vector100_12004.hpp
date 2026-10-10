#pragma once

#include "xar_bridge/prisoner_quote_readonly_source_12004.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

#define XAR_HAS_PRISONER_SCOPE_CLONE_VECTOR100_12004 1

namespace xar::ck3_12004 {

// Actual 373ADA1 passes fresh out_scope+100 and original_scope+100 to
// 37282B0. The projection is owned source-equivalent bytes; it supplies no
// physical native clone, returned pointer, or completed-cleanup witness.
struct PrisonerScopeCloneVector10012004 {
  PrisonerQuoteSourceFrame12004 frame;
  std::optional<std::uintptr_t> source_member_identity;
  std::optional<std::int32_t> source_count_raw_i32;
  std::optional<std::uintptr_t> source_data_identity;
  std::optional<std::uint64_t> allocation_request_byte_count;
  std::optional<std::uint32_t> allocation_alignment;
  std::vector<std::uintptr_t> ordered_source_record_identities;
  std::array<std::byte, 0x18> header_raw{};
  std::array<bool, 0x18> header_defined_bytes{};
  std::optional<std::uintptr_t> physical_native_clone_identity;
  std::optional<std::uintptr_t> native_return_pointer;
  std::optional<bool> native_cleanup_completed;
  bool source_inputs_ready = false;
  bool ordered_source_records_ready = false;
  bool logical_postimage_ready = false;
  bool native_clone_invoked = false;
  std::string unavailable_reason;
};

// Reads the current selected quote's original scope, using the existing frame
// and full-ID proof. Only count==0 has a complete fresh-header projection in
// this source-closed leaf. Positive/negative inputs remain independently raw.
PrisonerScopeCloneVector10012004 ReadPrisonerScopeCloneVector10012004(
    const PrisonerQuoteReadOnlyAccess12004 &access,
    const PrisonerQuoteSourceFrame12004 &frame);

} // namespace xar::ck3_12004
