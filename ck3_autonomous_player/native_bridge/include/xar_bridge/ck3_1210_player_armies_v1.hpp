#pragma once

#include "xar_bridge/ck3_1210.hpp"

#include <array>
#include <cstdint>
#include <optional>
#include <string_view>
#include <vector>

namespace xar::ck3_1210 {

inline constexpr std::uintptr_t kPlayerArmyUnitRegistryRvaV1 = 0x6A667A8;
inline constexpr std::uintptr_t kPlayerArmyUnitRegistryVtableRvaV1 = 0x4EA40C8;
inline constexpr std::uintptr_t kPlayerArmyUnitManagerVtableRvaV1 = 0x4EA4090;
inline constexpr std::uintptr_t kPlayerArmyUnitStateRvaV1 = 0xD39110;
inline constexpr std::size_t kPlayerArmyUnitManagerOffsetV1 = 0x3ABF8;
inline constexpr std::int32_t kPlayerArmyStorageLimitV1 = 1'048'576;
inline constexpr std::size_t kPlayerArmyOwnedLimitV1 = 16'384;
inline constexpr std::int32_t kPlayerArmyRouteLimitV1 = 4'096;
inline constexpr std::size_t kPlayerArmyRouteBudgetV1 = 1'048'576;
inline constexpr std::array<std::uint8_t, 32> kPlayerArmyStateEntryGuardV1{
    0x48,0x89,0x5C,0x24,0x08,0x57,0x48,0x83,0xEC,0x20,0x48,0x8B,0x05,0xCF,0xD5,0xD2,
    0x05,0x48,0x8B,0xF9,0x48,0x85,0xC0,0x74,0x29,0x8B,0x91,0x78,0x01,0x00,0x00,0x8B};

using PlayerArmyNativeStateGetterV1 = std::int32_t (*)(void *unit);
struct PlayerArmiesBindingsV1 {
  bool exact_build_admitted = false;
  // The outer owner must separately establish paused application-main custody.
  // Exact identity/guard alone never permits a native function invocation.
  bool integration_native_calls_permitted = false;
  CoreBindings core{};
  void **unit_registry_slot = nullptr;
  std::uintptr_t unit_registry_vtable = 0;
  std::uintptr_t unit_manager_vtable = 0;
  PlayerArmyNativeStateGetterV1 get_unit_state = nullptr;
};

using PlayerArmiesCopyV1 = bool (*)(void *context, const void *source,
    void *destination, std::size_t size) noexcept;
// Optional exact-value input seam. An outer scoped reader may validate the
// native state dependency before/after a call; existing callers leave it empty.
using PlayerArmyStateInputWordsV1 = std::array<std::uint64_t, 20>;
using PlayerArmyStateInputValidatorV1 = bool (*)(void *context, const void *unit,
    std::int32_t native_army_reference, PlayerArmyStateInputWordsV1 &output) noexcept;
struct PlayerArmiesReadAccessV1 {
  void *context = nullptr;
  PlayerArmiesCopyV1 copy = nullptr;
  void *state_input_context = nullptr;
  PlayerArmyStateInputValidatorV1 validate_state_input = nullptr;
};

enum class PlayerArmyRouteReadStatusV1 { complete_empty, complete_nonempty };
// Independently scoped internal row, not a complete gameplay ArmySnapshot.
struct PlayerArmyObservationRowV1 {
  std::int32_t army_id = -1;
  std::int32_t owner_character_id = -1;
  // Observed input to native state, not a separately qualified CArmy row.
  std::int32_t native_army_reference = -1;
  std::optional<std::int32_t> current_province_id;
  std::vector<std::int32_t> route_province_ids;
  std::int32_t route_source_count = 0;
  PlayerArmyRouteReadStatusV1 route_read_status = PlayerArmyRouteReadStatusV1::complete_empty;
  std::optional<std::int32_t> move_target_province_id;
  std::int32_t army_state_code = 0;
  std::string_view army_state = "unknown";
  std::int32_t retreat_state_raw = 0;
  bool in_combat = false;
  bool retreating = false;
  bool controllable = false;
  // These observations are deliberately outside this proven reader.
  std::optional<std::int32_t> soldiers;
  std::optional<std::int32_t> siege_days_left;
  friend bool operator==(const PlayerArmyObservationRowV1 &,
      const PlayerArmyObservationRowV1 &) = default;
};

struct PlayerArmiesObservationV1 {
  bool available = false;
  bool same_frame_ready = false;
  bool collection_complete = false;
  bool partial = true;
  bool full_snapshot_available = false;
  bool complete_army_snapshot_qualified = false;
  CoreSnapshotPrefix frame{};
  // Missing means unavailable, present empty means a complete native scan
  // found no unit owned by the actual Core actor.
  std::optional<std::vector<PlayerArmyObservationRowV1>> player_armies;
  std::int32_t unit_slots_scanned = 0;
  std::size_t live_unit_rows = 0;
  // Retained on failure too; a failed observation cannot erase actual calls.
  std::size_t native_state_calls_attempted = 0;
  std::string_view unavailable_reason = "player_armies_not_read";
};

PlayerArmiesBindingsV1 BindPlayerArmiesImageV1(std::uintptr_t image_base,
    std::string_view executable_sha256) noexcept;
bool ReadPlayerArmiesV1(const PlayerArmiesBindingsV1 &bindings,
    const CoreSnapshotPrefix &expected, PlayerArmiesObservationV1 &output,
    PlayerArmiesReadAccessV1 access = {}) noexcept;

} // namespace xar::ck3_1210
