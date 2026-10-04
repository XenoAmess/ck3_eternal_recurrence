#pragma once

#include "xar_bridge/game_contract.hpp"

#include <cstdint>
#include <span>
#include <string_view>

namespace xar::ck3_12002 {

inline constexpr std::uintptr_t kUnitStorageSlotRva12002 = 0x5D1E380;
inline constexpr std::uintptr_t kInternalArmyStorageSlotRva12002 = 0x5D1DE48;
inline constexpr std::uintptr_t kRegimentStorageSlotRva12002 = 0x5D1F340;
inline constexpr std::uintptr_t kUnitStateRva12002 = 0xD19140;
inline constexpr std::uintptr_t kArmyCurrentSoldiersRva12002 = 0x2A95740;
inline constexpr std::uintptr_t kArmyMaximumSoldiersRva12002 = 0x24E0450;
inline constexpr std::uintptr_t kArmySupplyCapacityRva12003 = 0x2C53C10;
inline constexpr std::uintptr_t kArmyAttritionFractionRva12003 = 0x24E2E50;
inline constexpr std::uintptr_t kPersistentRegimentStorageSlotRva12003 = 0x5D1EB68;
inline constexpr std::uintptr_t kRegimentCanReplenishRva12003 = 0x262C700;
inline constexpr std::uintptr_t kChunkCanReplenishRva12003 = 0x2657F10;
inline constexpr std::uintptr_t kRegimentMonthlyReplenishmentRva12003 = 0x262CAD0;
inline constexpr std::uintptr_t kArmyMonthlySupplyChangeRva12003 = 0x24E51A0;
inline constexpr std::uintptr_t kArmyGatheringDaysLeftRva12003 = 0x24E9070;
inline constexpr std::uintptr_t kUnitNormalizedEdgeProgressRva12003 = 0x24AB2F0;
inline constexpr std::uintptr_t kUnitFirstRouteEdgeDurationRva12003 = 0x24AB060;
inline constexpr std::uintptr_t kProvinceSupplyLimitRva12003 = 0x247BEC0;
inline constexpr std::uintptr_t kProvinceSupplyUsageRva12003 = 0x247C5A0;

struct ArmyBindings {
  bool enabled = false;
  void **game_state_slot = nullptr;
  void **unit_storage_slot = nullptr;
  void **internal_army_storage_slot = nullptr;
  void **regiment_storage_slot = nullptr;
  std::int32_t (*get_unit_state)(void *) = nullptr;
  std::int32_t (*get_army_current_soldiers)(void *, std::uint8_t) = nullptr;
  std::int32_t (*get_army_maximum_soldiers)(void *) = nullptr;
  // Exact .3 only; the native optional-breakdown argument is always null.
  std::int64_t *(*get_army_supply_capacity)(std::int64_t *, void *, void *) = nullptr;
  std::int64_t *(*get_army_attrition_fraction)(void *, std::int64_t *, void *) = nullptr;
  // Persistent CRegiment (magic Regi), not regiment_storage_slot's CArmyRegiment.
  // Closed only for exact .3; the .2 adapter leaves this subdomain unassigned.
  void **persistent_regiment_storage_slot = nullptr;
  bool (*can_regiment_replenish)(void *, void *) = nullptr;
  bool (*can_chunk_replenish)(void *) = nullptr;
  std::int64_t *(*get_regiment_monthly_replenishment_fraction)(void *, std::int64_t *) = nullptr;
  // Supplies/month, signed Q100000, at the current validated CProvince.
  std::int64_t *(*get_army_monthly_supply_change)(void *, std::int64_t *, void *, void *) = nullptr;
  // Exact .3 native CArmy receiver, integral remaining days (scale 1).
  std::int32_t (*get_army_gathering_days_left)(void *) = nullptr;
  // Exact .3 CUnit route getters; neither requires an army-AI assignment.
  // A missing getter leaves only that operand unknown. The .2 binder omits
  // this subdomain. Positive 0xFFFFFFFF is the native unavailable sentinel.
  bool current_movement_progress_enabled = false;
  std::int64_t *(*get_unit_normalized_edge_progress)(void *, std::int64_t *) = nullptr;
  std::int64_t *(*get_unit_first_route_edge_duration)(void *, std::int64_t *,
                                                   std::int32_t) = nullptr;
  // Exact .3 native whole soldier-equivalent values, scale 1, not Q100000.
  std::int32_t (*get_province_supply_limit)(void *, void *, void *, void *) = nullptr;
  std::int32_t (*get_province_supply_usage)(void *, void *, std::int32_t,
                                          std::int64_t *) = nullptr;
  void **province_supply_character_fallback_slot = nullptr;
  ck3_12003::ArmySupplyTimingBindings timing_bindings{};
};

ArmyBindings BindArmyImage(std::uintptr_t image_base,
                          std::string_view executable_sha256) noexcept;

// Owning-thread native handles. Resolution requires full generation identity.
void *ResolveArmyUnit(const ArmyBindings &bindings,
                      std::int32_t unit_id) noexcept;
void *ResolveInternalArmy(const ArmyBindings &bindings,
                          std::int32_t internal_army_id) noexcept;
bool ReadArmyGathering(const ArmyBindings &bindings, std::int32_t unit_id,
                       bool &gathering) noexcept;

// Called on the owning game thread. An empty owner span requests all units.
// A valid empty storage returns true; unreadable storage returns false.
bool ReadArmiesForCharacters(
    const ArmyBindings &bindings, std::span<const std::int32_t> owners,
    std::vector<game::ArmySnapshot> &output,
    std::int32_t controlled_owner = -1) noexcept;

struct ArmyStrengthScope {
  std::int32_t army_id = -1;
  game::ArmyStrengthScopeRole role = game::ArmyStrengthScopeRole::player;
  std::vector<std::int32_t> war_ids;
};

game::ReadArmyStrengthsResult ReadArmyStrengthsForScope(
    const ArmyBindings &bindings, std::span<const ArmyStrengthScope> scope,
    std::vector<game::ArmyStrengthSnapshot> &output) noexcept;

// The snapshot must have been read in the same paused owning-thread sample.
game::ReadArmyStrengthsResult ReadArmyStrengths(
    const ArmyBindings &bindings, const game::Snapshot &snapshot,
    std::vector<game::ArmyStrengthSnapshot> &output) noexcept;

struct MilitaryWorldAccess;

// Invoked on the same owning thread after the existing paused controllable-army
// move preview succeeds. The subquery never changes the movement result.
game::ArmyProvinceSupplySnapshot ReadArmyProvinceSupplyForPreview(
    const ArmyBindings &, const MilitaryWorldAccess &,
    const game::PreviewMoveArmyResult &) noexcept;

} // namespace xar::ck3_12002
