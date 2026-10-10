#pragma once

#include "xar_bridge/construction_owner_mode3_raw_receiver_12004.hpp"

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string_view>
#include <vector>

namespace xar::ck3_12004::construction_owner_mode3 {

inline constexpr std::uint32_t kMode3M4ActualEntryRva12004 = 0x28B9300;
inline constexpr std::size_t kMode3M4MaximumListOccurrencesV1 = 4096;

// These callbacks project source-closed memory paths. They are not native
// function ABIs. The request's uint64 revision is passed through unchanged.
struct Mode3M4ReadBindingsV1 {
  void *count_context = nullptr;
  bool (*read_count_28b71e0)(void *, const RawReceiverAccessV1 &,
                           std::uintptr_t, std::uint64_t,
                           std::int32_t &) noexcept = nullptr;
  bool count_71e0_source_closed = false;
  void *predicate_context = nullptr;
  bool (*read_subobject_2c39ee0)(void *, const RawReceiverAccessV1 &,
                                std::uintptr_t, std::uint64_t,
                                bool &) noexcept = nullptr;
  bool subobject_predicate_source_closed = false;
};

struct Mode3M4OccurrenceV1 {
  std::uint32_t stored_index = 0;
  std::uint32_t raw_full_id = 0;
  std::uintptr_t selected_title = 0;
  bool title_registry_matched = false;
  std::uintptr_t selected_character = 0;
  bool character_registry_matched = false;
  std::uintptr_t province = 0;
  std::optional<bool> subobject_predicate;
  std::optional<std::uint8_t> raw_predicate_byte;
  std::optional<bool> counted;
  std::string_view unavailable_reason;
};

struct Mode3M4Count7450V1 {
  std::uintptr_t actual_receiver = 0;
  std::uint64_t snapshot_revision = 0;
  std::optional<std::uintptr_t> nested_1c0;
  std::optional<std::uintptr_t> list_descriptor;
  std::optional<std::uintptr_t> list_data;
  std::optional<std::int32_t> declared_count;
  std::vector<Mode3M4OccurrenceV1> occurrences;
  std::optional<std::int32_t> signed_eax;
  bool source_ready = false;
  std::string_view unavailable_reason;
};

struct Mode3M4ReductionV1 {
  std::uintptr_t actual_receiver = 0;
  std::uint64_t snapshot_revision = 0;
  std::uint8_t actual_dl = 1;
  Mode3M4Count7450V1 count_7450;
  std::optional<std::int32_t> count_71e0_signed_eax;
  std::optional<std::uintptr_t> minimum_nested_1c0;
  std::optional<std::int32_t> minimum_raw_3d8;
  std::optional<std::int32_t> minimum_signed;
  std::optional<std::int32_t> difference_signed;
  std::optional<std::int32_t> after_minimum_signed;
  std::optional<std::int32_t> signed_eax;
  bool source_ready = false;
  std::string_view unavailable_reason;
  bool native_function_invoked = false;
};

Mode3M4ReadBindingsV1 BindMode3M4ReadonlyChildrenV1() noexcept;

// Actual 28B7450 traverses the ordered raw FullID list and counts each AL!=0
// occurrence, including duplicates. Negative/over-budget descriptors remain
// unavailable in the bounded copied-input model; no native validity gate is
// inferred from that implementation limit.
Mode3M4Count7450V1 ReadMode3M4Count7450V1(
    const RawReceiverAccessV1 &, std::uintptr_t actual_receiver,
    std::uint64_t unchanged_snapshot_revision,
    const Mode3M4ReadBindingsV1 &,
    std::size_t maximum_occurrences = kMode3M4MaximumListOccurrencesV1) noexcept;

// Only the actual mode3 DL=1 path is modeled. Both subtracts wrap in 32 bits,
// followed by the literal signed max(1,field) and signed max(0,result).
Mode3M4ReductionV1 ReadMode3M4ReductionV1(
    const RawReceiverAccessV1 &, std::uintptr_t actual_receiver,
    std::uint64_t unchanged_snapshot_revision,
    const Mode3M4ReadBindingsV1 &) noexcept;

Mode3M4ReductionV1 ReadMode3M4ReductionV1(
    const RawReceiverAccessV1 &, std::uintptr_t actual_receiver,
    std::uint64_t unchanged_snapshot_revision) noexcept;

// Directly matches 03d's Mode3SignedEaxChildV1.read. Optional context borrows
// Mode3M4ReadBindingsV1 for focused compound use; null uses production owners.
// A false status preserves out. A successful signed EAX of zero is known.
bool ReadMode3M4SignedEaxChildV1(
    void *, const RawReceiverAccessV1 &, std::uintptr_t actual_receiver,
    std::uint64_t unchanged_snapshot_revision, std::int32_t &out) noexcept;

} // namespace xar::ck3_12004::construction_owner_mode3
