#pragma once

#include "xar_bridge/source_read_leaf_frame_12004.hpp"

#include <vector>

namespace xar::ck3_12004 {
inline constexpr std::uintptr_t kTriggerScopeTableProviderRva3795A6012004 = 0x3795A60;
inline constexpr std::uintptr_t kTriggerScopeTableInlineRva3795A6012004 = 0x54F2AF0;
inline constexpr std::uintptr_t kTriggerScopeTableGuardRva3795A6012004 = 0x5D7A1D4;
inline constexpr std::uintptr_t kTriggerScopeFallbackRva3795A6012004 = 0x54F5310;
inline constexpr std::size_t kTriggerScopeDescriptorStride3795A6012004 = 80; // 0x50.

struct TriggerScopeTableProviderRaw3795A6012004 {
  SourceReadFrame12004 frame;
  std::optional<std::uint16_t> caller_copied_root_kind_raw_u16;
  std::optional<std::uintptr_t> source_provider_entry_identity;
  std::optional<std::uintptr_t> source_return_table_identity;
  std::optional<std::int32_t> initialization_guard_raw_i32;
  std::optional<std::uintptr_t> table_data_identity;
  std::optional<std::int32_t> capacity_raw_i32, count_raw_i32;
  std::optional<bool> caller_root_zero_bypasses_descriptor;
  std::optional<bool> selected_source_fallback;
  std::optional<std::uintptr_t> selected_descriptor_identity;
  std::optional<std::uintptr_t> descriptor_validator_pointer10;
  bool query_frame_ready = false;
  bool return_pointer_on_returning_native_paths_source_closed = false;
  bool any_native_field_read_attempted = false;
  bool all_attempted_native_reads_complete = false;
  bool table_header_copy_complete = false;
  bool descriptor_selection_inputs_copied = false;
  bool descriptor_validator_pointer_copied = false;
  std::optional<bool> copied_fields_unchanged;
  std::size_t source_scalar_reads = 0;
  std::vector<std::string> missing_fields;
  std::string unavailable_reason;
  // The complete getter span includes an unexpanded initialization path.
  // Raw copied pointers/header bytes grant none of these independent facts.
  bool initializer_semantics_source_closed = false;
  bool native_provider_return_observed = false;
  std::optional<bool> initialized_state;
  std::optional<std::uint8_t> descriptor_validator_returned_raw_u8;
  bool descriptor_validator_result_source_ready = false;
  bool native_callback_executed = false;
};

// Copies a bounded raw table/header and one selected descriptor+10. The kind
// is the caller's original copied WORD; it is never inferred from a class.
// Known kind0 mirrors42's bypass without reading the unused table. Unknown
// kind still exposes header facts but does not select a descriptor.
TriggerScopeTableProviderRaw3795A6012004 ReadTriggerScopeTableProvider3795A6012004(
    const SourceLeafReadOnlyAccess12004 &, const SourceReadFrame12004 &,
    std::optional<std::uint16_t> caller_copied_root_kind_raw_u16);

// No standalone main. One new shared42/35/09 compound is owned by10.
void VerifyTriggerScopeTableProvider3795A60ConnectedCases12004();
} // namespace xar::ck3_12004
