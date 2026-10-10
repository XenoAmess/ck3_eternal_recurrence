#pragma once

#include "xar_bridge/construction_owner_mode3_raw_receiver_12004.hpp"
#include "xar_bridge/returned_selector_28c2df0_12004.hpp"
#include <optional>
#include <string_view>
#include <vector>

namespace xar::ck3_12004::construction_owner_mode3 {

inline constexpr std::string_view kCount28B71E0SourcePin12004 =
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
inline constexpr std::int32_t kCount28B71E0ReadonlyOccurrenceLimit12004 = 4096;

enum class Count28B71E0FailureV1 : std::uint8_t {
  none, exact_build, read_callback, collection, negative_source_extent,
  native_copy_budget_exceeded,
  title_resolution, rank, direct_province, province_gate, title_gate,
  interface_source, slots_source, returned_object, returned_member, source_changed,
};

enum class Count28B71E0PathV1 : std::uint8_t {
  incomplete, skip_rank, skip_province_magic, skip_province_byte,
  skip_title_byte, skip_title_sentinel, count_interface_magic_mismatch,
  count_buffer_byte_zero, count_slots_byte_nonzero,
  count_returned_member_equal, skip_returned_member_unequal,
};

struct Count28B71E0OccurrenceV1 {
  std::int32_t ordinal = 0;
  std::optional<std::uint32_t> requested_full_id_u32;
  std::uintptr_t selected_title = 0;
  bool registry_matched = false;
  std::optional<std::int32_t> rank_i32;
  std::uintptr_t province = 0;
  std::optional<std::uint32_t> province_magic_85c;
  std::optional<std::uint8_t> province_byte_628;
  std::optional<std::uint8_t> title_byte_130;
  std::optional<std::uint32_t> title_dword_12c;
  std::optional<std::uint32_t> province_dword_63c;
  std::uintptr_t province_pointer_620 = 0;
  std::optional<std::uintptr_t> buffer_630;
  std::uintptr_t interface_object = 0;
  std::optional<std::uint32_t> interface_magic_38;
  std::optional<std::uint8_t> buffer_byte_8;
  std::optional<std::uint8_t> slots_byte_bc;
  std::optional<ReturnedObject28C2DF0Result12004> returned_object_source;
  std::optional<std::uintptr_t> returned_member_418;
  Count28B71E0PathV1 path = Count28B71E0PathV1::incomplete;
  bool counted = false;
};

struct Count28B71E0ObservationV1 {
  bool observed = false;
  Count28B71E0FailureV1 failure = Count28B71E0FailureV1::none;
  std::string_view source_pin = kCount28B71E0SourcePin12004;
  std::uintptr_t input_receiver = 0;
  std::uint64_t frame_key = 0;
  std::optional<std::uintptr_t> context_1c0;
  std::uintptr_t descriptor = 0;
  std::optional<std::uintptr_t> data_pointer;
  std::optional<std::int32_t> count_raw_i32;
  std::vector<Count28B71E0OccurrenceV1> occurrences;
  std::optional<std::uint32_t> eax_raw_u32;
  std::optional<std::int32_t> eax_signed_i32;
  bool actual_original_consumed_values = false;
};

// Only literal71E0 inputs and the reached04 object-only data path. No native
// getter is called. frame_key is unchanged03 snapshot_revision, not a new clock.
Count28B71E0ObservationV1 ReadConstructionCount28B71E0V1(
    const RawReceiverAccessV1 &, std::uintptr_t actual_original_06receiver,
    std::uint64_t unchanged_snapshot_revision);

//13e callback ABI. Unavailable/exception keeps out unchanged; observed0 is valid.
bool ReadM4Count28B71E0Adapter12004(
    void *, const RawReceiverAccessV1 &, std::uintptr_t actual_original_06receiver,
    std::uint64_t unchanged_snapshot_revision, std::int32_t &out) noexcept;

void VerifyConstructionCount28B71E0OwnedCases12004();

} // namespace xar::ck3_12004::construction_owner_mode3
