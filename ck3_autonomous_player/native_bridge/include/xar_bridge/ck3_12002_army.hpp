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
inline constexpr std::uintptr_t kArmyWholeLossBudgetRva12003 = 0x24DD580;
inline constexpr std::uintptr_t kArmySupplyLossBudgetRva12003 = 0x24E32E0;
inline constexpr std::uintptr_t kRegimentSupplyLossEligibleRva12003 = 0x2A956D0;
inline constexpr std::uintptr_t kArmySiegeActiveRva12003 = 0x24E8560;
inline constexpr std::uintptr_t kArmySiegeLossRateRva12003 = 0x5C69618;
inline constexpr std::uintptr_t kArmyRaidLossRateRva12003 = 0x5C69098;
inline constexpr std::uintptr_t kArmyCountyEntryLossBudgetRva12003 = 0x24E6670;
inline constexpr std::uintptr_t kArmyCountyEntryLossFractionRva12003 = 0x24E6590;
inline constexpr std::uintptr_t kArmyCountyEntryMultiplierRva12003 = 0x24DD9C0;
inline constexpr std::uintptr_t kArmyCountyEntryMinimumRva12003 = 0x5C68B64;
inline constexpr std::uintptr_t kArmyCountyEntryPredicateRva12003 = 0x24E2250;
inline constexpr std::uintptr_t kArmyCountyEntryCharacterStorageRva12003 = 0x5C67568;
inline constexpr std::uintptr_t kArmyRegimentLossWriterSkippedRva12003 = 0x2634880;

// Complete readonly leaves and loaded state vectors for monthly budget replay.
struct ArmyMonthlyLossBudgetBindings12003 {
  bool enabled = false;
  bool (*is_unit_in_combat)(void *) = nullptr;
  bool (*is_unit_gathering)(void *) = nullptr;
  bool (*is_army_fleet_supply_active)(void *) = nullptr;
  void **fleet_storage_slot = nullptr;
  void **fleet_fallback_slot = nullptr;
  const std::int32_t *fleet_date_sentinel = nullptr;
  const std::int32_t **supply_state_levels_slot = nullptr;
  const std::int32_t *supply_state_levels_count = nullptr;
  const std::int64_t **supply_state_fractions_slot = nullptr;
  const std::int32_t *supply_state_fractions_count = nullptr;
  void **character_storage_slot = nullptr;
  void **character_fallback_slot = nullptr;
  void **province_fallback_slot = nullptr;
  void *(*get_character_modifier_aggregator)(void *) = nullptr;
  std::int64_t *(*read_character_modifier)(void *, std::int64_t *,
                                         std::int32_t) = nullptr;
};

struct ArmyMonthlyCallerEffectBindings12003 {
  bool enabled = false;
  void **character_storage_slot = nullptr;
  void **character_fallback_slot = nullptr;
  void **war_storage_slot = nullptr;
  void **war_fallback_slot = nullptr;
  const void *empty_war_ids_descriptor = nullptr;
  bool (*contains_war_participant)(const void *, std::int32_t) = nullptr;
};

struct ArmyDailyQueueBindings12003 {
  bool enabled = false;
  void **army_fallback_slot = nullptr;
};

struct ArmyCurrentHelperDomainBindings12003 {
  bool enabled = false;
  void **persistent_regiment_fallback_slot = nullptr;
  void **title_storage_slot = nullptr;
  void **title_fallback_slot = nullptr;
  void **character_storage_slot = nullptr;
  void **character_fallback_slot = nullptr;
  void **domain_storage_slot = nullptr;
  void **domain_fallback_slot = nullptr;
};

struct ArmyBindings {
  bool enabled = false;
  void **game_state_slot = nullptr;
  void **unit_storage_slot = nullptr;
  void **internal_army_storage_slot = nullptr;
  void **regiment_storage_slot = nullptr;
  std::int32_t (*get_unit_state)(void *) = nullptr;
  std::int32_t (*get_army_current_soldiers)(void *, std::uint8_t) = nullptr;
  std::int32_t (*get_army_maximum_soldiers)(void *) = nullptr;
  // The GDbo key and signed siege-tier layout are closed for exact .3 only.
  bool regiment_composition_enabled = false;
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
  // Exact .3 readonly monthly loss inputs. Rate is a signed VALUE in RCX;
  // 24DD580 has no output/details pointer. Counts reuse flags0/1/2/3 above.
  bool loss_application_inputs_enabled = false;
  const std::int64_t *siege_loss_rate_raw = nullptr;
  const std::int64_t *raid_loss_rate_raw = nullptr;
  std::int32_t (*get_army_whole_loss_budget)(std::int64_t, void *) = nullptr;
  std::int32_t (*get_army_supply_loss_budget)(void *) = nullptr;
  // Siege predicate; raiding uses the native CArmy+1E8 association.
  bool (*is_army_siege_active)(void *) = nullptr;
  // Exact .3 complete leaf: no calls or stores; actual per-ArRg AL predicate.
  bool (*is_regiment_supply_loss_eligible)(void *) = nullptr;
  // Exact .3 merge destination operand: CArmy receiver, signed Q100000 out.
  // 24E0160 uses flags=0; 24E02A0 has no flags or breakdown argument.
  std::int64_t *(*get_merge_destination_weight_part_a)(void *, std::int64_t *,
                                                      std::uint32_t) = nullptr;
  std::int64_t *(*get_merge_destination_weight_part_b)(void *, std::int64_t *) = nullptr;
  // Exact .3 current hypothetical county-entry inputs, never the entry executor.
  // Budget receives a null breakdown; fraction/multiplier return their out pointer.
  bool county_entry_inputs_enabled = false;
  const std::int32_t *county_entry_minimum_soldiers = nullptr;
  void **county_entry_character_storage_slot = nullptr;
  std::int32_t (*get_county_entry_loss_budget)(void *, void *) = nullptr;
  std::int64_t *(*get_county_entry_loss_fraction)(void *, std::int64_t *) = nullptr;
  std::int64_t *(*get_county_entry_multiplier)(std::int64_t *, void *) = nullptr;
  bool (*county_entry_condition)(void *, void *, void *, std::int32_t) = nullptr;
  // Exact .3 readonly Char FullID predicate used by26341B0 before DATA writes.
  bool (*is_army_regiment_loss_writer_skipped)(void *) = nullptr;
  ArmyMonthlyLossBudgetBindings12003 monthly_loss_budget_bindings{};
  ArmyMonthlyCallerEffectBindings12003 monthly_caller_effect_bindings{};
  ArmyDailyQueueBindings12003 monthly_daily_queue_bindings{};
  bool monthly_first_removal_cleanup_inputs_enabled = false;
  ArmyCurrentHelperDomainBindings12003 monthly_current_helper_domain_bindings{};
  bool monthly_current_helper_point_store_inputs_enabled = false;
};

game::ArmyCurrentHelperDomainInputsV1 ReadCurrentHelperDomainInputs12003(
    const ArmyBindings &, void *current_army);
game::ArmyCurrentHelperPointStoreInputsV1 ReadCurrentHelperPointStoreInputs12003(
    const ArmyBindings &, void *current_army);

// Same GDbo key/tier implementation used by the raised ArRg reader.
void ReadOwnedRegimentTypeV1(
    void *, void *maa_type,
    ck3_12003::OwnedRegimentTypeSnapshotV1 &) noexcept;

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
