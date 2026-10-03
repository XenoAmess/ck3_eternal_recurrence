#pragma once

#include "xar_bridge/ck3_12002.hpp"
#include "xar_bridge/ck3_12002_routes.hpp"
#include "xar_bridge/ck3_12002_combat.hpp"
#include "xar_bridge/game_contract.hpp"

namespace xar::ck3_12002 {

inline constexpr std::uintptr_t kBattleCombatStorageRva = 0x5D1DE70;
inline constexpr std::uintptr_t kBattleResultStorageRva = 0x5D1FFE0;
inline constexpr std::uintptr_t kBattleResultFallbackRva = 0x5D1FFD8;
inline constexpr std::uintptr_t kBattleSideStrengthRva = 0x2651100;
inline constexpr std::uintptr_t kBattleEntryStrengthRva = 0x2657B50;
inline constexpr std::uintptr_t kBattleCanRetreatRva = 0x258AA10;
inline constexpr std::uintptr_t kBattleRetreatRuleRva = 0x28C2E10;
inline constexpr std::uintptr_t kBattleMinimumRetreatDaysRva = 0x5C699B4;
inline constexpr std::size_t kBattleMainPhaseTypeFlag = 0x98A;
inline constexpr std::size_t kBattleArmyRegimentTypeOffset = 0x18;
inline constexpr std::size_t kBattleArmyRegimentArmyOffset = 0x140;
inline constexpr std::size_t kBattleAttackerSideOffset = 0x20;
inline constexpr std::size_t kBattleDefenderSideOffset = 0x368;
inline constexpr std::size_t kBattlePhaseOffset = 0x6B0;
inline constexpr std::size_t kBattlePhaseDayOffset = 0x6B4;
inline constexpr std::size_t kBattleFinalizedOffset = 0x704;
inline constexpr std::size_t kBattleDailyGuardOffset = 0x705;
inline constexpr std::size_t kBattleLandStatusOffset = 0x1C0;
inline constexpr std::size_t kBattleRuleFlagsOffset = 0x40;
inline constexpr std::size_t kBattleSubunitParentOffset = 0x38;
inline constexpr std::size_t kBattleSubunitTargetOffset = 0x40;
inline constexpr std::size_t kBattleSubunitFlagsOffset = 0x48;
inline constexpr std::size_t kBattleSubunitCrossValidityOffset = 0x54;
inline constexpr std::size_t kBattleSubunitCrossPowerOffset = 0x30;

struct BattleBindings {
  bool enabled = false;
  void **game_state_slot = nullptr;
  void **jomini_state_slot = nullptr;
  void **army_storage_slot = nullptr;
  void **army_internal_storage_slot = nullptr;
  void **regiment_storage_slot = nullptr;
  void **character_storage_slot = nullptr;
  void **combat_storage_slot = nullptr;
  void **battle_result_storage_slot = nullptr;
  void **battle_result_fallback_slot = nullptr;
  void **ai_war_coordinator_storage_slot = nullptr;
  std::uintptr_t ai_unit_stack_vtable = 0;
  std::uintptr_t ai_subunit_stack_vtable = 0;
  std::uintptr_t ai_war_coordinator_vtable = 0;
  const std::int32_t *minimum_days_before_manual_retreat = nullptr;
  std::int32_t (*get_combat_side_strength)(void *) = nullptr;
  std::int32_t (*get_combat_regiment_strength)(void *) = nullptr;
  bool (*can_order_combat_retreat)(void *, void *, void *) = nullptr;
  void *(*get_combat_retreat_rule_state)(void *owner_character) = nullptr;
  // BindBattleImage supplies the version-specific GameData province resolver.
  void *province_context = nullptr;
  void *(*resolve_province)(void *context, std::int32_t full_id) = nullptr;
  std::int64_t *(*read_route_edge_duration)(void *, std::int64_t *,
                                            std::int32_t) = nullptr;
  RouteBindings route_bindings{};
  // Independently nullable leaf: existing control observations remain useful
  // when selected next-roll inputs were not bound in a fixture or build.
  CombatBindings commander_roll_context{};
};

BattleBindings BindBattleImage(std::uintptr_t image_base,
                               std::string_view executable_sha256) noexcept;

game::BattleControlSnapshotStatus ReadBattleControlSnapshot(
    const BattleBindings &, const game::Snapshot &paused_scope,
    const game::BattleControlRequest &, game::BattleControlSnapshot &) noexcept;
game::BattleTransitionSnapshotStatus
ReadBattleTransitionSnapshot(const BattleBindings &,
                             const game::Snapshot &paused_scope,
                             const game::BattleTransitionRequest &,
                             game::BattleTransitionSnapshot &) noexcept;
game::BattleReinforcementAssignmentStatus ReadBattleReinforcementAssignmentV1(
    const BattleBindings &, const game::Snapshot &paused_scope,
    const game::BattleReinforcementAssignmentRequest &,
    game::BattleReinforcementAssignmentSnapshot &) noexcept;
game::BattleTerminalTransitionStatusV1 ReadBattleTerminalTransitionV1(
    const BattleBindings &, const game::Snapshot &paused_scope,
    const game::BattleTerminalTransitionRequestV1 &,
    game::BattleTerminalTransitionSnapshotV1 &) noexcept;

} // namespace xar::ck3_12002
