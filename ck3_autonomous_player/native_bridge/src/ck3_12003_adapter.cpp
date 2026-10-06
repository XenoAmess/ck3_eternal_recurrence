#include "xar_bridge/ck3_12003_adapter.hpp"
#include "xar_bridge/ordinary_interaction_request_v1.hpp"
#include "xar_bridge/ck3_12002_campaign.hpp"
#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/ck3_12003_commander_mailbox.hpp"
#if defined(XAR_CK3_ENABLE_CURRENT_ACTOR_STRESS_ADJUSTMENT_PRIVATE_V1)
#include "xar_bridge/current_actor_stress_adjustment_v1_mailbox.hpp"
#endif
#include "xar_bridge/ck3_12003_default_raise_mailbox.hpp"
#include "xar_bridge/ck3_12003_player_mercenary_mailbox.hpp"
#include "xar_bridge/ck3_12003_player_mercenary_hire_mailbox.hpp"
#include "xar_bridge/ck3_12003_player_holy_order_hire_mailbox.hpp"
#include "xar_bridge/ck3_12003_commander_assignment_mailbox.hpp"
#include <windows.h>
#include <utility>
#include <vector>
#include "xar_bridge/frontend_gui_route_v1.hpp"
#include "xar_bridge/steward_develop_county_candidates_v1.hpp"
#include "xar_bridge/projected_contact_scope_v1_serializer.hpp"

namespace xar::game {
namespace {
void ReplaceAll(std::string &value, std::string_view from, std::string_view to) {
  std::size_t at = 0;
  while ((at = value.find(from, at)) != std::string::npos) {
    value.replace(at, from.size(), to);
    at += to.size();
  }
}
} // namespace

const AdapterDescriptor &Ck3_12003AdapterDescriptor() noexcept {
  static const std::vector<std::string_view> capabilities = [] {
    const auto existing = Ck3_12002AdapterDescriptor().capabilities;
    std::vector<std::string_view> result(existing.begin(), existing.end());
#if defined(XAR_CK3_ENABLE_NORMAL_EXIT_MAP_PRIVATE_V1)
    result.push_back(ck3_12003::kNormalExitMapV1Capability);
#endif
    // Existing public UI family is implemented only for Army query/select on
    // exact .3; bridge/provider reject every other role before native dispatch.
    result.push_back(ck3_11906::kIngameUiNavigationV1Capability);
    result.push_back(ck3_11906::kIngameUiWindowQueryV1Capability);
    result.push_back(ck3_11906::kStewardDevelopCountyCandidatesV1Capability);
    result.push_back(ck3_12003::kArmyCommanderCandidatesCapability);
#if defined(XAR_CK3_ENABLE_CURRENT_ACTOR_STRESS_ADJUSTMENT_PRIVATE_V1)
    result.push_back(ck3_12003::kCurrentActorStressAdjustmentV1Capability);
#endif
#if defined(XAR_CK3_ENABLE_ORDINARY_INTERACTION_PRIVATE_V1)
    result.push_back(ck3_12003::kOrdinaryInteractionQueryV1Capability);
    result.push_back(ck3_12003::kOrdinaryInteractionInitiateV1Capability);
#endif
    result.push_back(ck3_12003::kPlayerDefaultRaiseCapabilityV1);
    result.push_back(ck3_12003::kPlayerMercenaryContextCapabilityV1);
    result.push_back(ck3_12003::kMercenaryHireCapabilityV1);
    result.push_back(ck3_12003::kHolyOrderHireCapabilityV1);
    result.push_back(kWarOccupationTargetsV1Capability);
    result.push_back(kTitleHolderV1Capability);
    result.push_back(kProjectedContactScopeV1Capability);
    result.push_back(ck3_12003::kArmyCommanderAssignmentCapability);
#if defined(XAR_CK3_ENABLE_FEUDAL_1066_BOOKMARK_MODEL_PRIVATE_V1) && \
    defined(XAR_CK3_ENABLE_FEUDAL_1066_SELECTED_BOOKMARK_START_PRIVATE_V1)
    // Restore the existing frontend tools for the migrated ordinary-seed route.
    result.push_back(ck3_11906::kFrontendGuiRouteV1Capability);
    result.push_back(ck3_11906::kFrontendGuiTreeInspectionV1Capability);
    result.push_back(ck3_11906::kGuiWindowTreeInspectionV1Capability);
    result.push_back(ck3_11906::kFrontendGuiOpenNewGameV1Capability);
#endif
#if defined(XAR_CK3_ENABLE_FEUDAL_1066_BOOKMARK_MODEL_PRIVATE_V1)
    result.push_back(ck3_11906::kFrontendBookmarkModelProbeV1Capability);
#endif
#if defined(XAR_CK3_ENABLE_FEUDAL_1066_SELECTED_BOOKMARK_START_PRIVATE_V1)
    result.push_back(ck3_11906::kFrontendGuiSelectSupported1066CharacterV1Capability);
    result.push_back(ck3_11906::kFrontendGuiStartSelectedBookmarkV1Capability);
#endif
#if defined(XAR_CK3_ENABLE_FRONTEND_GAME_RULES_PRIVATE_V1)
    result.push_back(ck3_11906::kFrontendGameRulesV1Capability);
    result.push_back(ck3_11906::kFrontendOpenGameRulesV1Capability);
    result.push_back(ck3_11906::kFrontendGameRulesControlV1Capability);
    result.push_back(ck3_11906::kFrontendSelectGameRuleV1Capability);
    result.push_back(ck3_11906::kFrontendApplyGameRulesV1Capability);
    result.push_back(ck3_11906::kFrontendHideGameRulesV1Capability);
    result.push_back(ck3_11906::kFrontendAppliedGameRulesV1Capability);
#endif

#if defined(XAR_CK3_ENABLE_INGAME_DECISIONS_OPEN_PRIVATE_V1)
    result.push_back(ck3_11906::kIngameDecisionsOpenV1Capability);
    result.push_back(ck3_11906::kIngameDecisionItemQueryV1Capability);
#if defined(XAR_CK3_ENABLE_INGAME_DECISION_ITEM_ACTIONS_PRIVATE_V1)
    result.push_back(ck3_11906::kIngameDecisionItemSelectV1Capability);
    result.push_back(ck3_11906::kIngameDecisionItemConfirmV1Capability);
#if defined(XAR_CK3_ENABLE_INGAME_DECISION_OUTCOME_PRIVATE_V1)
    result.push_back(ck3_11906::kIngameDecisionOutcomeConfirmV1Capability);
#endif
#endif
#endif
#if defined(XAR_CK3_ENABLE_WHITE_PLAYER_BUSINESS_VARIABLES_PRIVATE_V1)
    result.push_back(ck3_11906::kWhitePlayerBusinessVariablesV1Capability);
#endif
#if defined(XAR_CK3_ENABLE_AUB_CONFIRM_STATE_PRIVATE_V1)
    result.push_back(ck3_12003::kAubBusinessStateQueryV1Capability);
    result.push_back(ck3_12003::kAubConfirmV1Capability);
#endif
#if defined(XAR_CK3_ENABLE_AUB_POLICY_OPTIONS_PRIVATE_V1)
    result.push_back(ck3_12003::kAubPolicyQueryV1Capability);
    result.push_back(ck3_12003::kAubPolicySelectV1Capability);
#endif
#if defined(XAR_CK3_ENABLE_WHITE_RENDERED_TEXT_PRIVATE_V1)
    result.push_back(ck3_11906::kWhiteRenderedTextV1Capability);
#endif
#if defined(XAR_CK3_ENABLE_WHITE_CONTROL_ACTIONS_PRIVATE_V1)
    result.push_back(ck3_11906::kWhiteControlActionV1Capability);
    result.push_back(ck3_11906::kWhiteNumericControlActionV1Capability);
#endif
    return result;
  }();
  static const AdapterDescriptor descriptor{
      ck3_12003::kAdapterId, ck3_12003::kGameVersion, ck3_12003::kExecutableSha256,
      ck3_12002::kCheckpointSaveName, capabilities};
  return descriptor;
}

Ck3_12003AdapterBindings BindCk3_12003AdapterImage(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept {
  // core-comparison.json proves every production binding against this exact
  // .3 EXE. Reuse the reviewed layout without changing any .2 binder's gate.
  auto result = BindCk3_12002AdapterImage(image_base,
      executable_sha256 == ck3_12003::kExecutableSha256
          ? std::string_view(ck3_12002::kExecutableSha256) : std::string_view{});
  ck3_12002::EnableOrdinaryRegimentStatInputs12003(
      result.combat, image_base, executable_sha256);
  ck3_12002::EnableMaaRegimentStatInputs12003(
      result.combat, image_base, executable_sha256);
  ck3_12002::EnableKnightModelAssociation12003(
      result.combat, image_base, executable_sha256);
  result.combat.phase_rite_parameters = ck3_12003::phase_rite::BindImage(
      image_base, executable_sha256);
  result.phase.combat.phase_rite_parameters = result.combat.phase_rite_parameters;
  result.combat.phase_warmonger_core = ck3_12003::phase_warmonger::BindImage(
      image_base, executable_sha256);
  result.combat.phase_berserker_validity_inputs = ck3_12003::phase_berserker::BindImage(
      image_base, executable_sha256);
  result.combat.phase_berserker_chance_inputs = ck3_12003::phase_berserker_chance::BindImage(
      image_base, executable_sha256);
  // Current cash uses its actual .3 descriptor identity and native getters.
  // The private MCP remains unadvertised; the .2 binder leaves this disabled.
  result.war_cash_current = ck3_12003::war_cash_current::BindImage(
      image_base, ck3_12003::kGameVersion, executable_sha256);
  // Current normal MAA permission and raw prices use the actual .3 identity.
  result.native_maa_recruitment = ck3_12003::BindNativeMaaRecruitmentImage(
      image_base, executable_sha256);
  result.native_maa_create = ck3_12003::BindNativeMaaCreateImage(
      image_base, executable_sha256);
  // These numeric GUI getter ABIs are closed only for exact .3. Do not install
  // them in BindArmyImage: that binder also serves the unchanged .2 adapter.
  if (result.armies.enabled) {
    result.armies.current_daily_assault_loss_inputs_enabled = true;
    result.armies.current_daily_assault_table_bindings =
        ck3_12003::BindCurrentDailyAssaultTable12003(image_base, executable_sha256);
    result.armies.current_daily_assault_roster_admission_bindings =
        ck3_12003::BindCurrentDailyAssaultRosterAdmission12003(image_base, executable_sha256);
    result.armies.current_pre_date_pending_update_bindings =
        ck3_12003::BindCurrentPreDatePendingUpdate12003(image_base, executable_sha256);
    result.armies.current_assault_removal_reference_bindings =
        ck3_12003::BindCurrentAssaultRemovalReference12003(image_base, executable_sha256);
    result.armies.regiment_composition_enabled = true;
    auto &monthly = result.armies.monthly_loss_budget_bindings;
    monthly.enabled = true;
    monthly.is_unit_in_combat = reinterpret_cast<decltype(monthly.is_unit_in_combat)>(
        image_base + 0x24AC3E0);
    monthly.is_unit_gathering = reinterpret_cast<decltype(monthly.is_unit_gathering)>(
        image_base + 0x24AC160);
    monthly.is_army_fleet_supply_active =
        reinterpret_cast<decltype(monthly.is_army_fleet_supply_active)>(image_base + 0x24E8460);
    monthly.fleet_storage_slot = reinterpret_cast<void **>(image_base + 0x5D1F9B8);
    monthly.fleet_fallback_slot = reinterpret_cast<void **>(image_base + 0x5D1F9A8);
    monthly.fleet_date_sentinel = reinterpret_cast<const std::int32_t *>(image_base + 0x5C83A68);
    monthly.supply_state_levels_slot = reinterpret_cast<const std::int32_t **>(image_base + 0x5456498);
    monthly.supply_state_levels_count = reinterpret_cast<const std::int32_t *>(image_base + 0x54564A4);
    monthly.supply_state_fractions_slot = reinterpret_cast<const std::int64_t **>(image_base + 0x5451308);
    monthly.supply_state_fractions_count = reinterpret_cast<const std::int32_t *>(image_base + 0x5451314);
    monthly.character_storage_slot = reinterpret_cast<void **>(image_base + 0x5C67568);
    monthly.character_fallback_slot = reinterpret_cast<void **>(image_base + 0x5C67570);
    monthly.province_fallback_slot = reinterpret_cast<void **>(image_base + 0x5D1E390);
    // Reuse the approved numeric context/getter ABI with the actual province ordinal.
    monthly.get_character_modifier_aggregator =
        reinterpret_cast<decltype(monthly.get_character_modifier_aggregator)>(image_base + 0x28C3AE0);
    monthly.read_character_modifier =
        reinterpret_cast<decltype(monthly.read_character_modifier)>(image_base + 0x2303700);
    auto &caller = result.armies.monthly_caller_effect_bindings;
    caller.enabled = true;
    caller.character_storage_slot = reinterpret_cast<void **>(image_base + 0x5C67568);
    caller.character_fallback_slot = reinterpret_cast<void **>(image_base + 0x5C67570);
    caller.war_storage_slot = reinterpret_cast<void **>(image_base + 0x5D1DE58);
    caller.war_fallback_slot = reinterpret_cast<void **>(image_base + 0x5D1DE40);
    caller.empty_war_ids_descriptor = reinterpret_cast<const void *>(image_base + 0x5459D38);
    caller.contains_war_participant =
        reinterpret_cast<decltype(caller.contains_war_participant)>(image_base + 0x2494B60);
    result.armies.monthly_daily_queue_bindings.enabled = true;
    result.armies.monthly_first_removal_cleanup_inputs_enabled = true;
    result.armies.monthly_current_helper_point_store_inputs_enabled = true;
    result.armies.monthly_current_helper_domain_bindings = {
        true,
        reinterpret_cast<void **>(image_base + 0x5D1EB58),
        reinterpret_cast<void **>(image_base + 0x5D1DAF8),
        reinterpret_cast<void **>(image_base + 0x5D1DAE0),
        reinterpret_cast<void **>(image_base + 0x5C67568),
        reinterpret_cast<void **>(image_base + 0x5C67570),
        reinterpret_cast<void **>(image_base + 0x5D1EB80),
        reinterpret_cast<void **>(image_base + 0x5D1EB38)};
    result.armies.monthly_daily_queue_bindings.army_fallback_slot =
        reinterpret_cast<void **>(image_base + 0x5D1DE50);
    result.armies.is_regiment_supply_loss_eligible =
        reinterpret_cast<decltype(result.armies.is_regiment_supply_loss_eligible)>(
            image_base + ck3_12002::kRegimentSupplyLossEligibleRva12003);
    result.armies.loss_application_inputs_enabled = true;
    result.armies.county_entry_inputs_enabled = true;
    result.armies.county_entry_minimum_soldiers =
        reinterpret_cast<const std::int32_t *>(
            image_base + ck3_12002::kArmyCountyEntryMinimumRva12003);
    result.armies.county_entry_character_storage_slot = reinterpret_cast<void **>(
        image_base + ck3_12002::kArmyCountyEntryCharacterStorageRva12003);
    result.armies.get_county_entry_loss_budget =
        reinterpret_cast<decltype(result.armies.get_county_entry_loss_budget)>(
            image_base + ck3_12002::kArmyCountyEntryLossBudgetRva12003);
    result.armies.get_county_entry_loss_fraction =
        reinterpret_cast<decltype(result.armies.get_county_entry_loss_fraction)>(
            image_base + ck3_12002::kArmyCountyEntryLossFractionRva12003);
    result.armies.get_county_entry_multiplier =
        reinterpret_cast<decltype(result.armies.get_county_entry_multiplier)>(
            image_base + ck3_12002::kArmyCountyEntryMultiplierRva12003);
    result.armies.county_entry_condition =
        reinterpret_cast<decltype(result.armies.county_entry_condition)>(
            image_base + ck3_12002::kArmyCountyEntryPredicateRva12003);
    result.armies.siege_loss_rate_raw = reinterpret_cast<const std::int64_t *>(
        image_base + ck3_12002::kArmySiegeLossRateRva12003);
    result.armies.raid_loss_rate_raw = reinterpret_cast<const std::int64_t *>(
        image_base + ck3_12002::kArmyRaidLossRateRva12003);
    result.armies.get_army_whole_loss_budget =
        reinterpret_cast<decltype(result.armies.get_army_whole_loss_budget)>(
            image_base + ck3_12002::kArmyWholeLossBudgetRva12003);
    result.armies.get_army_supply_loss_budget =
        reinterpret_cast<decltype(result.armies.get_army_supply_loss_budget)>(
            image_base + ck3_12002::kArmySupplyLossBudgetRva12003);
    result.armies.is_army_siege_active =
        reinterpret_cast<decltype(result.armies.is_army_siege_active)>(
            image_base + ck3_12002::kArmySiegeActiveRva12003);
    result.armies.timing_bindings = ck3_12003::BindArmySupplyTimingImage(
        image_base, executable_sha256);
    result.native_owner_recall = ck3_12002::BindBattleImage(
        image_base, ck3_12002::kExecutableSha256);
    ck3_12003::EnableBattleNativeOwnerRecallInputs12003(
        result.native_owner_recall, image_base, executable_sha256);
    result.armies.get_merge_destination_weight_part_a =
        reinterpret_cast<decltype(result.armies.get_merge_destination_weight_part_a)>(
            image_base + 0x24E0160);
    result.armies.get_merge_destination_weight_part_b =
        reinterpret_cast<decltype(result.armies.get_merge_destination_weight_part_b)>(
            image_base + 0x24E02A0);
    result.armies.get_army_supply_capacity =
        reinterpret_cast<decltype(result.armies.get_army_supply_capacity)>(
            image_base + ck3_12002::kArmySupplyCapacityRva12003);
    result.armies.get_army_attrition_fraction =
        reinterpret_cast<decltype(result.armies.get_army_attrition_fraction)>(
            image_base + ck3_12002::kArmyAttritionFractionRva12003);
    result.armies.persistent_regiment_storage_slot = reinterpret_cast<void **>(
        image_base + ck3_12002::kPersistentRegimentStorageSlotRva12003);
    result.owned_regiments.persistent_regiment_storage_slot =
        result.armies.persistent_regiment_storage_slot;
    result.owned_regiments.read_type = ck3_12002::ReadOwnedRegimentTypeV1;
    result.armies.can_regiment_replenish =
        reinterpret_cast<decltype(result.armies.can_regiment_replenish)>(
            image_base + ck3_12002::kRegimentCanReplenishRva12003);
    result.armies.can_chunk_replenish =
        reinterpret_cast<decltype(result.armies.can_chunk_replenish)>(
            image_base + ck3_12002::kChunkCanReplenishRva12003);
    result.armies.get_regiment_monthly_replenishment_fraction =
        reinterpret_cast<decltype(result.armies.get_regiment_monthly_replenishment_fraction)>(
            image_base + ck3_12002::kRegimentMonthlyReplenishmentRva12003);
    result.armies.is_army_regiment_loss_writer_skipped =
        reinterpret_cast<decltype(result.armies.is_army_regiment_loss_writer_skipped)>(
            image_base + ck3_12002::kArmyRegimentLossWriterSkippedRva12003);
    result.armies.get_army_monthly_supply_change =
        reinterpret_cast<decltype(result.armies.get_army_monthly_supply_change)>(
            image_base + ck3_12002::kArmyMonthlySupplyChangeRva12003);
    result.armies.get_army_gathering_days_left =
        reinterpret_cast<decltype(result.armies.get_army_gathering_days_left)>(
            image_base + ck3_12002::kArmyGatheringDaysLeftRva12003);
    result.armies.current_movement_progress_enabled = true;
    // Reuse the exact-.3 reviewed route provider address map. The .2 adapter
    // leaves this additive strengths observer disabled.
    result.movement_routes = ck3_12002::BindRouteImage(
        image_base, ck3_12002::kExecutableSha256);
    result.armies.get_unit_normalized_edge_progress =
        reinterpret_cast<decltype(result.armies.get_unit_normalized_edge_progress)>(
            image_base + ck3_12002::kUnitNormalizedEdgeProgressRva12003);
    result.armies.get_unit_first_route_edge_duration =
        reinterpret_cast<decltype(result.armies.get_unit_first_route_edge_duration)>(
            image_base + ck3_12002::kUnitFirstRouteEdgeDurationRva12003);
    result.armies.get_province_supply_limit =
        reinterpret_cast<decltype(result.armies.get_province_supply_limit)>(
            image_base + ck3_12002::kProvinceSupplyLimitRva12003);
    result.armies.get_province_supply_usage =
        reinterpret_cast<decltype(result.armies.get_province_supply_usage)>(
            image_base + ck3_12002::kProvinceSupplyUsageRva12003);
    result.armies.province_supply_character_fallback_slot =
        reinterpret_cast<void **>(
            image_base + ck3_12002::kCampaignRootCharacterFallbackSlotRva);
    result.armies.current_province_supply_contributor_bindings.enabled = true;
    result.armies.current_province_supply_contributor_bindings.shares_current_war_side =
        reinterpret_cast<decltype(result.armies.current_province_supply_contributor_bindings.shares_current_war_side)>(
            image_base + ck3_12003::kSupplyContributorCommonWarSideRva12003);
    auto &besieging = result.armies.current_province_besieging_bindings;
    besieging.enabled = true;
    besieging.unit_fallback_slot = reinterpret_cast<void **>(image_base + 0x5D1E378);
    besieging.army_fallback_slot = reinterpret_cast<void **>(image_base + 0x5D1DE50);
    besieging.province_fallback_slot = reinterpret_cast<void **>(image_base + 0x5D1E390);
    besieging.siege_storage_slot = reinterpret_cast<void **>(image_base + 0x5D1EC88);
    besieging.army_excluded = reinterpret_cast<decltype(besieging.army_excluded)>(image_base + 0x24E8360);
    besieging.army_province_eligible = reinterpret_cast<decltype(besieging.army_province_eligible)>(image_base + 0x2C16690);
    besieging.besieging_strength = reinterpret_cast<decltype(besieging.besieging_strength)>(image_base + 0x247F1D0);
    besieging.assault_expected_loss = reinterpret_cast<decltype(besieging.assault_expected_loss)>(image_base + 0x25205C0);
    besieging.casualty_percentage_count = reinterpret_cast<const std::int32_t *>(image_base + 0x5452384);
    besieging.casualty_percentage_table_slot = reinterpret_cast<const std::int64_t **>(image_base + 0x54524C8);
    auto &resupply = result.armies.current_land_resupply_bindings;
    resupply.enabled = true;
    resupply.is_resupply_eligible = reinterpret_cast<ck3_12002::IsHoldingDefender>(
        image_base + ck3_12003::kCurrentProvinceResupplyEligibleRva12003);
    resupply.is_army_fleet_supply_active = monthly.is_army_fleet_supply_active;
    resupply.character_storage_slot = monthly.character_storage_slot;
    resupply.loaded_gain_raw = reinterpret_cast<const std::int64_t *>(
        image_base + ck3_12003::kLoadedUnderLimitSupplyGainRva12003);
    auto &rate = result.armies.current_land_supply_rate_bindings;
    rate.enabled = true;
    rate.province_component_condition = reinterpret_cast<decltype(rate.province_component_condition)>(image_base + 0xC6AF20);
    rate.read_province_component = reinterpret_cast<ck3_12002::ReadAdvantageModifierValue>(image_base + 0x2C4D550);
    rate.character_storage_slot = monthly.character_storage_slot;
    rate.character_fallback_slot = monthly.character_fallback_slot;
    rate.get_character_modifier_aggregator = monthly.get_character_modifier_aggregator;
    rate.read_character_modifier = monthly.read_character_modifier;
    rate.loaded_excess_slope_raw = reinterpret_cast<const std::int64_t *>(image_base + 0x5C69A38);
    rate.loaded_min_loss_raw = reinterpret_cast<const std::int64_t *>(image_base + 0x5C69A30);
    rate.loaded_max_loss_raw = reinterpret_cast<const std::int64_t *>(image_base + 0x5C69A40);
    rate.loaded_divisor_floor_raw = reinterpret_cast<const std::int64_t *>(image_base + 0x5C68F68);
    result.armies.scoped_ordered_refill_bindings =
        ck3_12003::BindScopedOrderedRefillInputs12003(image_base, executable_sha256);
    result.armies.ordered_besieging_refill_bindings =
        ck3_12003::BindOrderedBesiegingRefillInputs12003(image_base, executable_sha256);
  }
  if (result.phase.advantage.enabled) {
    // Constructor-faith closure is proven only for exact .3. Keep the .2
    // binder's reviewed nonreligious contract unchanged.
    auto &religion = result.phase.advantage.constructor_religion;
    religion.enabled = true;
    religion.rite_storage_slot = reinterpret_cast<void **>(image_base + 0x5D1E2F8);
    religion.faith_storage_slot = reinterpret_cast<void **>(image_base + 0x5D1E300);
    religion.null_rite_slot = reinterpret_cast<void **>(image_base + 0x5C67670);
    religion.null_faith_slot = reinterpret_cast<void **>(image_base + 0x5D1E2E0);
    religion.target_faith_is_unreformed =
        reinterpret_cast<decltype(religion.target_faith_is_unreformed)>(
            image_base + 0x2BD8960);
  }
  return result;
}

std::unique_ptr<GameAdapter> CreateCk3_12003Adapter(
    std::string_view executable_sha256) noexcept {
  return CreateCk3_12003AdapterFromBindings(BindCk3_12003AdapterImage(
      reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)), executable_sha256));
}

std::string RenderCrozierBuildIdentity(
    std::string serialized, const AdapterDescriptor &descriptor) {
  if (IsCk3_12003Descriptor(descriptor)) {
    serialized = ck3_12002::RenderQueryBuildIdentity(std::move(serialized));
    // Includes typed DTO version fields, backend IDs, and versioned evidence
    // labels. Actual implementation source paths (ck3_12002*.cpp) stay true.
    for (const auto key : {"game_version", "exact_ck3_build", "exact_build",
                           "version", "build_version", "build"}) {
      ReplaceAll(serialized, std::string("\"") + key + "\":\"1.20.0.2\"",
                 std::string("\"") + key + "\":\"1.20.0.3\"");
    }
    for (const auto key : {"backend_id", "campaign_backend_id", "feature_backend_id"}) {
      ReplaceAll(serialized, std::string("\"") + key + "\":\"ck3-1.20.0.2-",
                 std::string("\"") + key + "\":\"ck3-1.20.0.3-");
    }
    ReplaceAll(serialized, "\"adapter_id\":\"ck3-1.20.0.2-msvc-x64\"",
                          "\"adapter_id\":\"ck3-1.20.0.3-msvc-x64\"");
    ReplaceAll(serialized, "\"schema\":\"ck3_12002_", "\"schema\":\"ck3_12003_");
    ReplaceAll(serialized, "\"played-character-event-icon-indicators-1.20.0.2-v1\"",
                          "\"played-character-event-icon-indicators-1.20.0.3-v1\"");
    ReplaceAll(serialized, std::string("\"") + ck3_12002::kExecutableSha256 + "\"",
                          std::string("\"") + ck3_12003::kExecutableSha256 + "\"");
    ReplaceAll(serialized,
        "\"ae1ba6ff060ba603842f6f4a2ded0af4b7d3666b3dd271f75fb01b0da8e81b2d\"",
        "\"94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6\"");
  }
  return serialized;
}
} // namespace xar::game
