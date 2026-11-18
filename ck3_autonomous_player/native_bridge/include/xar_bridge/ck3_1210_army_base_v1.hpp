#pragma once

#include "xar_bridge/ck3_1210_player_armies_v1.hpp"
#include "xar_bridge/game_contract.hpp"

namespace xar::ck3_1210 {
inline constexpr std::uintptr_t kArmyBaseNativeRegistryRvaV1 = 0x6A666F0;
inline constexpr std::uintptr_t kArmyBaseNoArmyFallbackRvaV1 = 0x6A66698;
inline constexpr std::uintptr_t kArmyBaseNativeRegistryVtableRvaV1 = 0x4E9DEF0;
inline constexpr std::uintptr_t kArmyBaseManagerVtableRvaV1 = 0x4E9E148;
inline constexpr std::uintptr_t kArmyBaseNativeArmyVtableRvaV1 = 0x4E481A8;
inline constexpr std::size_t kArmyBaseManagerOffsetV1 = 0x3AC38;
inline constexpr std::size_t kArmyBaseManagerRegistryOffsetV1 = 0x48;

struct ArmyBaseBindingsV1 {
  bool exact_build_admitted = false;
  // Native state permission stays false until the outer paused main owner
  // explicitly permits it. This component never grants Full/capability credit.
  PlayerArmiesBindingsV1 player_armies{};
  void **native_army_registry_slot = nullptr;
  void **no_army_fallback_slot = nullptr;
  std::uintptr_t native_army_registry_vtable = 0;
  std::uintptr_t native_army_manager_vtable = 0;
  std::uintptr_t native_army_vtable = 0;
};
struct ArmyBaseReadAccessV1 {
  void *context = nullptr;
  PlayerArmiesCopyV1 copy = nullptr;
};
struct ArmyBaseObservationV1 {
  bool available = false;
  bool same_frame_ready = false;
  bool collection_complete = false;
  bool army_base_qualified = false;
  bool full_snapshot_available = false;
  bool complete_active_wars_qualified = false;
  CoreSnapshotPrefix frame{};
  std::optional<std::vector<xar::game::ArmySnapshot>> player_armies;
  std::int32_t unit_slots_scanned = 0;
  std::size_t live_unit_rows = 0;
  std::size_t native_state_calls_attempted = 0;
  std::string_view unavailable_reason = "army_base_not_read";
};

ArmyBaseBindingsV1 BindArmyBaseImageV1(std::uintptr_t image_base,
    std::string_view executable_sha256) noexcept;
// Reuses the complete Unit reader and adds exact native-state dependency
// identity before/after every call, retained in both full scan transcripts.
// A -1 CArmy reference is proven no-CArmy/regular; any other unresolved
// generation is unavailable, rather than the native getter's default regular.
bool ReadArmyBaseV1(const ArmyBaseBindingsV1 &bindings,
    const CoreSnapshotPrefix &expected, ArmyBaseObservationV1 &output,
    ArmyBaseReadAccessV1 access = {}) noexcept;
} // namespace xar::ck3_1210
