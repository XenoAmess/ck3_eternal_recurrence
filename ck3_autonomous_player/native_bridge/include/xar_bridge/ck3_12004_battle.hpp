#pragma once

#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12002_battle.hpp"

namespace xar::ck3_12004 {

// The software contract is shared. Every native address below belongs to the
// frozen Steam 25734779 image; this profile never calls an older image binder.
using BattleBindings = ck3_12002::BattleBindings;

inline constexpr std::uintptr_t kBattleCombatStorageRva = 0x5D1DE70;
inline constexpr std::uintptr_t kBattleResultStorageRva = 0x5D1FFE0;
inline constexpr std::uintptr_t kBattleResultFallbackRva = 0x5D1FFD8;
inline constexpr std::uintptr_t kBattleSideStrengthRva = 0x26510E0;
inline constexpr std::uintptr_t kBattleEntryStrengthRva = 0x2657B30;
inline constexpr std::uintptr_t kBattleCanRetreatRva = 0x258A9F0;
inline constexpr std::uintptr_t kBattleRetreatRuleRva = 0x28C2DF0;
inline constexpr std::uintptr_t kBattleMinimumRetreatDaysRva = 0x5C699B4;
inline constexpr std::uintptr_t kBattleRollCadenceIntervalRva = 0x5C69B48;
inline constexpr std::uintptr_t kBattleAdvantageScalingRva = 0x5C6A230;
inline constexpr std::uintptr_t kBattleCommanderMinRollRva = 0x5C699BC;
inline constexpr std::uintptr_t kBattleCommanderMaxRollRva = 0x5C699B8;
inline constexpr std::uintptr_t kBattleCharacterModifierAggregatorRva = 0x28C3AC0;
inline constexpr std::uintptr_t kBattleCharacterModifierReadRva = 0x23036E0;
inline constexpr std::uintptr_t kBattleProvinceModifierRva = 0x2C4D530;
inline constexpr std::uintptr_t kBattleProvinceHasHoldingRva = 0xC6AF20;
inline constexpr std::uintptr_t kBattleFinalizerManagerSecondaryVtableRva =
    0x477F188;
inline constexpr std::size_t kBattleFinalizerManagerGameStateDomainOffset = 0xA0;
inline constexpr std::size_t kBattleFinalizerManagerDomainOffset = 0x2E9D0;

// GeneralCombat and Province have separate native profiles and proof owners.
// Supply those actual .4 bindings here, instead of nesting BindCombatImage for
// an older executable. The resolver retains its owning profile's context.
struct BattleImageDependencies {
  ck3_12002::CombatBindings combat_context{};
  void **army_internal_fallback_slot = nullptr;
  void *province_context = nullptr;
  void *(*resolve_province)(void *, std::int32_t) = nullptr;
};

BattleBindings BindBattleImage(
    std::uintptr_t image_base, std::string_view executable_sha256,
    const BattleImageDependencies &dependencies) noexcept;

void EnableBattleCurrentFinalizerManagerInputs(
    BattleBindings &, std::uintptr_t image_base,
    std::string_view executable_sha256) noexcept;

std::optional<game::BattleControlCurrentFinalizerManagerInputsV1>
ReadCurrentFinalizerManagerInputs(
    const BattleBindings &, const void *strict_actual_combat,
    std::int32_t requested_full_combat_id) noexcept;

game::BattleControlSnapshotStatus ReadBattleControlSnapshot(
    const BattleBindings &, const game::Snapshot &paused_scope,
    const game::BattleControlRequest &, game::BattleControlSnapshot &) noexcept;

game::BattleTransitionSnapshotStatus ReadBattleTransitionSnapshot(
    const BattleBindings &, const game::Snapshot &paused_scope,
    const game::BattleTransitionRequest &, game::BattleTransitionSnapshot &) noexcept;

} // namespace xar::ck3_12004
