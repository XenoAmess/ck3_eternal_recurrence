#pragma once

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace xar::ck3_12004 {

struct PersonInstalledTransferStage12004;

inline constexpr std::uintptr_t kPersonTransferBlock248Offset12004 = 0x248;
inline constexpr std::uintptr_t kPersonTransferBlock248TailRva12004 = 0x2922A10;

using PersonTransferBlock248Read12004 = bool (*)(
    void *, std::uintptr_t, void *, std::size_t) noexcept;

struct PersonTransferBlock248Bindings12004 {
  void *read_context = nullptr;
  PersonTransferBlock248Read12004 read = nullptr;
};

struct PersonTransferBlock248Snapshot12004 {
  std::uintptr_t model_identity = 0;
  std::optional<std::uintptr_t> block_identity;
  std::optional<std::uintptr_t> data_identity;
  std::optional<std::int32_t> capacity_i32;
  std::optional<std::int32_t> count_i32;
  // Model+258 is this block+10 allocator identity. It is not the separate
  // Character+1B0 -> carrier+258 installed-Model slot.
  std::optional<std::uintptr_t> allocator_identity;
  std::optional<std::uintptr_t> allocator_dispatch_vtable_identity;
  std::optional<std::vector<std::uint64_t>> ordered_payload_raw64;
  bool payload_ready = false;
  std::string reason;
};

struct PersonTransferBlock248Postimage12004 {
  bool original_transfer_returned = false;
  bool copied_model_pair_matches_transfer = false;
  // Continuation13's clock/thread and order proof are preserved separately
  // from copied values. Equality of empty payloads is not an event witness.
  std::optional<bool> completion_event_order_proven;
  std::optional<bool> post_a_equals_pre_b;
  std::optional<bool> post_b_equals_pre_a;
  std::optional<bool> two_way_payload_equality;
  bool payload_comparison_ready = false;
  std::string reason;
};

// Root uses its existing exact4 guarded copy around the same original-once
// transfer wrapper. This reader never invokes a native function or allocator.
PersonTransferBlock248Snapshot12004 ReadPersonTransferBlock24812004(
    const PersonTransferBlock248Bindings12004 &bindings,
    std::uintptr_t actual_model);

// Consumes the actual13 DTO rather than accepting a naked success Boolean.
// Does not grant installed-Model, aggregate-PC, FullPerson, or Entry lineage.
PersonTransferBlock248Postimage12004 ComparePersonTransferBlock24812004(
    const PersonInstalledTransferStage12004 &transfer,
    const PersonTransferBlock248Snapshot12004 &pre_a,
    const PersonTransferBlock248Snapshot12004 &pre_b,
    const PersonTransferBlock248Snapshot12004 &post_a,
    const PersonTransferBlock248Snapshot12004 &post_b);

} // namespace xar::ck3_12004
