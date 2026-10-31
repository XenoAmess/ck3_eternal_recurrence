#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace xar::ck3_12002 { struct FamilyOutboundBindings; }

namespace xar::bridge {

struct FamilyOutgoingOptionCopy12004 {
  std::uint32_t flag = 0;
  std::uint8_t bank_byte = 0;
  friend bool operator==(const FamilyOutgoingOptionCopy12004 &,
                         const FamilyOutgoingOptionCopy12004 &) = default;
};
struct FamilyOutgoingCandidateCopy12004 {
  std::uint32_t pending_full_id = 0;
  std::uint32_t definition_hash = 0;
  // Only the five public roles. UINT32_MAX denotes the native invalid/null ID.
  std::array<std::uint32_t, 5> roles{};
  std::int32_t route_kind = 0;
  std::int32_t age_days = 0;
  std::int32_t ai_reply_cutoff_days = 0;
  // Complete authored order, including duplicate flags and zero-valued bytes.
  std::vector<FamilyOutgoingOptionCopy12004> options{};
  friend bool operator==(const FamilyOutgoingCandidateCopy12004 &,
                         const FamilyOutgoingCandidateCopy12004 &) = default;
};
struct FamilyOutgoingStorageCopy12004 {
  std::uint32_t definition_hash = 0;
  std::uint32_t sender_id = 0;
  std::int32_t scanned_slots = 0;
  std::vector<std::uint32_t> occupied_ids{};
  std::vector<FamilyOutgoingCandidateCopy12004> candidates{};
  friend bool operator==(const FamilyOutgoingStorageCopy12004 &,
                         const FamilyOutgoingStorageCopy12004 &) = default;
};
using FamilyOutgoingMemoryRead12004 = bool (*)(
    void *context, std::uintptr_t address, void *output,
    std::size_t bytes) noexcept;
struct FamilyOutgoingStorageAccess12004 {
  void *context = nullptr;
  FamilyOutgoingMemoryRead12004 read_memory = nullptr;
};
enum class FamilyOutgoingStorageCopyStatus12004 : std::uint8_t {
  complete,
  invalid_request,
  unavailable,
  changed
};

// Called on the actual owning query thread. The caller supplies the real
// arrange_marriage definition pointer and effective sender; this function does
// not construct a context/command or infer a sender from the played actor.
// Copies every occupied slot ID and every selected definition/sender row twice.
// Only the mapped pending-vtable inventory is supported. Any other non-null
// object type fails the entire read unavailable; it is never silently skipped.
// All non-complete paths reset output. Native constructors are never invoked.
FamilyOutgoingStorageCopyStatus12004 ReadFamilyOutgoingStorageCopy12004(
    const ck3_12002::FamilyOutboundBindings &bindings,
    const FamilyOutgoingStorageAccess12004 &access,
    std::uintptr_t actual_definition, std::uint32_t actual_sender,
    FamilyOutgoingStorageCopy12004 &output) noexcept;

// Serializes only the complete FamilyOutgoingCodec v4 GROUP object. The caller
// owns the real query envelope/frame, and must have a complete copy result.
// Throws invalid_argument if a supplied value violates the actual Java codec.
std::string SerializeFamilyOutgoingStorageGroup12004(
    const FamilyOutgoingStorageCopy12004 &copy,
    std::uint32_t actual_played_actor);

} // namespace xar::bridge
