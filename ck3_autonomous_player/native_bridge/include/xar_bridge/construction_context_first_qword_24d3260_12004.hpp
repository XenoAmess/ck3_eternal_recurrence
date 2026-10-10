#pragma once

#include "xar_bridge/construction_context_factor_2c399c0_12004.hpp"

namespace xar::ck3_12004::construction_owner_mode3 {

inline constexpr std::uintptr_t kContextFirstQword24D3260EntryRvaV1 = 0x24D3260;
inline constexpr std::uintptr_t kContextFirstQword24D3260OverrideSlotRvaV1 = 0x5C69698;

enum class ContextFirstQword24D3260FailureV1 : std::uint8_t {
  none, exact_build, frame_key, read_callback, image_base, context_object,
  source_read, source_changed,
};

enum class ContextFirstQword24D3260PathV1 : std::uint8_t {
  unavailable, below_signed_threshold, null_link, zero_gate_byte, loaded_override,
};

// These are the literal fields visited by one actual resolution branch.
// A failed read remains unknown; only a known null/out-of-range/full-ID
// mismatch selects the native fallback. No object registry is enumerated.
struct ContextFirstQword24D3260RegistryV1 {
  bool visited = false, resolved_by_full_id = false, used_fallback = false;
  std::optional<std::uintptr_t> registry_pointer, entries_pointer;
  std::optional<std::uint32_t> requested_full_id_u32, index_low24_u32;
  std::optional<std::uint32_t> unsigned_capacity_u32, object_full_id_u32;
  std::optional<std::uintptr_t> slot_object, selected_object;
};

struct ContextFirstQword24D3260ObservationV1 {
  ContextFactorProviderFirstQwordV1 provider{};
  ContextFirstQword24D3260FailureV1 failure = ContextFirstQword24D3260FailureV1::none;
  ContextFirstQword24D3260PathV1 path = ContextFirstQword24D3260PathV1::unavailable;
  std::uintptr_t image_base = 0, failed_address = 0;
  std::size_t failed_bytes = 0, scalar_source_reads = 0;
  bool copied_sources_unchanged = false;
  std::optional<std::int64_t> context_398_qword_raw, override_qword_raw;
  ContextFirstQword24D3260RegistryV1 first_registry{}, second_registry{};
  std::optional<std::uintptr_t> second_object_link;
  std::optional<std::uint8_t> linked_object_gate_byte;
};

// Same paused-frame source reader only. It copies through03's existing exact4
// memory API, mirrors the closed native branches, and verifies the visited
// scalar copies. No call to24D3260, output store, getter, initializer or tax
// name is introduced. frame_key is CampaignRootFrameV1.snapshot_revision.
ContextFirstQword24D3260ObservationV1 ReadContextFirstQword24D3260V1(
    const LoadedInputAccessV1 &, std::uintptr_t image_base,
    std::uintptr_t already_qualified_context_object, std::uint64_t frame_key) noexcept;

// Export for03/10's sole new connected compound. This file has no main.
void VerifyContextFirstQword24D3260ConnectedCasesV1();

} // namespace xar::ck3_12004::construction_owner_mode3
