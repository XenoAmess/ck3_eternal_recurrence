#pragma once

#include "xar_bridge/ck3_1210.hpp"
#include "xar_bridge/ck3_1210_pending_hotfix26757580_v1.hpp"
#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::ck3_1210 {
inline constexpr char kPendingSnapshotSchemaV1[] = "ck3_1210_pending_snapshot_v1";
inline constexpr std::uintptr_t kPendingSnapshotStorageSlotRvaV1 = 0x6A67190;
inline constexpr std::uintptr_t kPendingSnapshotDatabaseVtableRvaV1 = 0x4E98050;
inline constexpr std::uintptr_t kPendingSnapshotObjectVtableRvaV1 = 0x4E76878;
inline constexpr std::uintptr_t kPendingSnapshotPredicateRvaV1 = 0x14DEB60;
inline constexpr std::uintptr_t kPendingSnapshotValidatorRvaV1 = 0x2E4F9B0;
inline constexpr std::uintptr_t kPendingSnapshotReplyPrimaryRvaV1 = 0x4AF48D0;
inline constexpr std::uintptr_t kPendingSnapshotReplySecondaryRvaV1 = 0x4AF4898;
// Adapter work/stack availability bound, NOT an engine collection-size limit.
inline constexpr std::size_t kPendingSnapshotMaxSlotsV1 = 4096;
inline constexpr std::uint32_t kPendingSnapshotTypeV1 = 0x4368496E;
inline constexpr std::size_t kPendingSnapshotIdOffsetV1 = 0x10;
inline constexpr std::size_t kPendingSnapshotTypeOffsetV1 = 0x14;
inline constexpr std::size_t kPendingSnapshotActorOffsetV1 = 0x300;
inline constexpr std::size_t kPendingSnapshotRecipientOffsetV1 = 0x304;
inline constexpr std::size_t kPendingSnapshotAlternateRecipientOffsetV1 = 0x310;
inline constexpr std::size_t kPendingSnapshotKindOffsetV1 = 0x5D0;
inline constexpr std::size_t kPendingSnapshotNotificationOffsetV1 = 0x5D6;
// Exact new-EXE entry pins for the owning integration's mapped-image checks.
inline constexpr std::array<std::uint8_t, 32> kPendingPredicateEntry32V1 = {
  0x48,0x83,0xEC,0x28,0x81,0x79,0x14,0x6E,0x49,0x68,0x43,0x75,0x1E,0x83,0x79,0x10,
  0xFF,0x74,0x18,0x44,0x8B,0x81,0xD0,0x05,0x00,0x00,0x45,0x85,0xC0,0x74,0x1E,0x41};
inline constexpr std::array<std::uint8_t, 32> kPendingValidatorEntry32V1 = {
  0x48,0x89,0x5C,0x24,0x10,0x57,0x48,0x83,0xEC,0x20,0x48,0x8B,0xF9,0x83,0x79,0x24,
  0x04,0x0F,0x84,0xF5,0x00,0x00,0x00,0x48,0x8B,0x05,0xC2,0x77,0xC1,0x03,0x48,0x85};

struct alignas(8) PendingReplyValidationCommandV1 {
  std::uintptr_t primary_vtable = 0;
  std::uint8_t flags = 0;
  std::array<std::byte, 15> reserved{};
  std::uintptr_t secondary_vtable = 0;
  std::int32_t instance_id = -1;
  std::int32_t choice = 0;
};
static_assert(sizeof(PendingReplyValidationCommandV1) == 0x28);
static_assert(offsetof(PendingReplyValidationCommandV1, flags) == 8);
static_assert(offsetof(PendingReplyValidationCommandV1, secondary_vtable) == 0x18);
static_assert(offsetof(PendingReplyValidationCommandV1, instance_id) == 0x20);
static_assert(offsetof(PendingReplyValidationCommandV1, choice) == 0x24);
using PendingForCharacterV1 = bool (*)(void *pending, void *character);
using PendingReplyValidatorV1 = bool (*)(void *command);
struct PendingSnapshotBindingsV1 {
  bool exact_build_admitted = false;
  CoreBindings core{};
  void **pending_storage_slot = nullptr;
  PendingForCharacterV1 is_pending_for_character = nullptr;
  PendingReplyValidatorV1 validate_reply = nullptr;
  std::uintptr_t database_vtable = 0;
  std::uintptr_t pending_vtable = 0;
  std::uintptr_t reply_primary_vtable = 0;
  std::uintptr_t reply_secondary_vtable = 0;
  // bb3 only: typed current GameStateData owner must hold this same registry.
  std::uintptr_t owner_manager_vtable = 0;
  std::size_t owner_manager_data_offset = 0;
};
struct PendingSnapshotObservationV1 {
  std::string_view schema = kPendingSnapshotSchemaV1;
  bool available = false;
  bool found = false;
  bool same_frame_ready = false;
  bool partial = true;
  bool full_snapshot_available = false;
  CoreSnapshotPrefix frame{};
  std::int32_t pending_character_interaction_id = -1;
  std::int32_t pending_sender_character_id = -1;
  bool pending_auto_accept_notification = false; // Native is_notification.
  std::uint32_t slots_scanned = 0;
  std::uint32_t occupied_slots = 0;
  std::string_view unavailable_reason = "pending_snapshot_not_read";
};
// Address calculation only, no mapped-image read/process discovery. Owner must
// admit exact mapped-image entry pins and actual main-thread/TLS paused custody.
PendingSnapshotBindingsV1 BindPendingSnapshotImageV1(std::uintptr_t image_base,
    std::string_view executable_sha256) noexcept;
// Complete bounded scan, then field-by-field confirmation; first eligible slot
// wins. Any failure invalidates absence and clears all selected fields. Native
// calls only test eligibility/validate a stack DTO. No queue interface exists.
bool ReadPendingSnapshotV1(const PendingSnapshotBindingsV1 &bindings,
    const CoreSnapshotPrefix &expected, PendingSnapshotObservationV1 &output) noexcept;
} // namespace xar::ck3_1210
