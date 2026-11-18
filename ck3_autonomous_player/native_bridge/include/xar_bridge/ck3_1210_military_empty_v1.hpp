#pragma once

#include "xar_bridge/ck3_1210.hpp"

#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::ck3_1210 {

// Internal observation only. These limits bound work, not engine capacities.
inline constexpr std::int32_t kMilitaryEmptyStorageLimitV1 = 1'048'576;
inline constexpr std::int32_t kMilitaryEmptySideLimitV1 = 65'536;
inline constexpr std::size_t kMilitaryEmptyParticipantBudgetV1 = 1'048'576;
inline constexpr std::uintptr_t kMilitaryUnitRegistryRvaV1 = 0x6A667A8;
inline constexpr std::uintptr_t kMilitaryWarRegistryRvaV1 = 0x6A666D0;
inline constexpr std::uintptr_t kMilitaryUnitRegistryVtableRvaV1 = 0x4EA40C8;
inline constexpr std::uintptr_t kMilitaryWarRegistryVtableRvaV1 = 0x4E9C188;
inline constexpr std::uintptr_t kMilitaryUnitManagerVtableRvaV1 = 0x4EA4090;
inline constexpr std::uintptr_t kMilitaryWarManagerVtableRvaV1 = 0x4E9C2C0;
inline constexpr std::size_t kMilitaryUnitManagerOffsetV1 = 0x3ABF8;
inline constexpr std::size_t kMilitaryWarManagerOffsetV1 = 0x3F2D8;

struct MilitaryEmptyBindingsV1 {
  bool exact_build_admitted = false;
  CoreBindings core{};
  void **unit_registry_slot = nullptr;
  void **war_registry_slot = nullptr;
  std::uintptr_t unit_registry_vtable = 0;
  std::uintptr_t war_registry_vtable = 0;
  std::uintptr_t unit_manager_vtable = 0;
  std::uintptr_t war_manager_vtable = 0;
};

// Optional bounded read adapter for deterministic NoGame fixtures and owners
// with an existing checked-memory channel. Null uses the guarded local copier.
// A custom copier cannot supply Core truth: actual Core is read independently.
using MilitaryEmptyCopyV1 = bool (*)(void *context, const void *source,
    void *destination, std::size_t size) noexcept;
struct MilitaryEmptyReadAccessV1 {
  void *context = nullptr;
  MilitaryEmptyCopyV1 copy = nullptr;
};

struct MilitaryEmptyObservationV1 {
  bool available = false;
  bool same_frame_ready = false;
  bool player_armies_empty_proven = false;
  bool active_wars_empty_proven = false;
  // This narrow proof never upgrades itself to a complete gameplay Snapshot.
  bool partial = true;
  bool full_snapshot_available = false;
  CoreSnapshotPrefix frame{};
  std::int32_t unit_slots_scanned = 0;
  std::int32_t war_slots_scanned = 0;
  std::size_t live_unit_rows = 0;
  std::size_t active_war_rows = 0;
  std::size_t participant_records = 0;
  std::string_view unavailable_reason = "military_empty_not_read";
};

MilitaryEmptyBindingsV1 BindMilitaryEmptyImageV1(std::uintptr_t image_base,
    std::string_view executable_sha256) noexcept;

// True only after two complete, identical native collection/actor transcripts
// and three matching paused Core reads. A nonempty collection, inaccessible
// read, stale generation or malformed graph returns explicit unavailable.
// No native score/state/Province/command getter is called. No output arrays
// exist before proof; a later complete Snapshot owner may then append []/[].
// Application-main custody and live qualification remain the outer owner's.
bool ReadMilitaryEmptyV1(const MilitaryEmptyBindingsV1 &bindings,
    const CoreSnapshotPrefix &expected, MilitaryEmptyObservationV1 &output,
    MilitaryEmptyReadAccessV1 access = {}) noexcept;

} // namespace xar::ck3_1210
