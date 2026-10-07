#include "xar_bridge/ck3_12004_army_support.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12004_army.hpp"
#include "xar_bridge/ck3_12004_commands.hpp"
#include "xar_bridge/ck3_12004_military.hpp"
#include "xar_bridge/ck3_12004_routes.hpp"

namespace xar::ck3_12004 {
namespace {
template <class T>
T ImageAddress12004(std::uintptr_t base, std::uintptr_t rva) noexcept {
  return reinterpret_cast<T>(base + rva);
}
} // namespace

ck3_12002::RouteBindings BindRouteImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept {
  ck3_12002::RouteBindings result{};
  if (!image_base || executable_sha256 != kExecutableSha256) return result;
  const auto core = BindCoreImage(image_base, executable_sha256);
  const auto armies = BindArmyImage12004(image_base, executable_sha256);
  const auto commands = BindCommandImage12004(image_base, executable_sha256);
  const auto military = BindMilitaryImage12004(
      image_base, executable_sha256, commands);
  if (!core.enabled || !armies.enabled || !military.enabled) return result;

  result.game_state_slot = core.game_state_slot;
  result.jomini_state_slot = core.jomini_state_slot;
  result.army_storage_slot = armies.unit_storage_slot;
  result.get_army_move_mode = military.move_mode;
  result.read_route_progress = military.read_move_progress;
  result.get_route_front = military.read_route_first;
  result.get_route_tail = military.read_route_last;
  result.movement_locked_threshold = military.move_progress_cutoff;
  result.construct_move_path_context = military.construct_path_context;
  result.construct_army_move_path = military.construct_move_path;
  result.build_army_move_route = military.build_route;
  result.destroy_move_army_command = military.destroy_move;
  result.move_army_primary_vtable = military.move_primary;
  result.move_army_secondary_vtable = military.move_secondary;
  result.read_unit_land_route_speed =
      ImageAddress12004<decltype(result.read_unit_land_route_speed)>(
          image_base, kCommanderLandMovementRateRva12004);
  result.read_unit_naval_route_speed =
      ImageAddress12004<decltype(result.read_unit_naval_route_speed)>(
          image_base, kCommanderNavalMovementRateRva12004);
  result.read_unit_current_edge_speed =
      ImageAddress12004<decltype(result.read_unit_current_edge_speed)>(
          image_base, kCommanderCurrentEdgeMovementRateRva12004);
  result.read_route_travel_duration =
      ImageAddress12004<decltype(result.read_route_travel_duration)>(
          image_base, kRouteTravelDurationRva12004);
  result.enabled = true;
  return result;
}

void PopulateArmySupportBindings12004(
    std::uintptr_t image_base, std::string_view executable_sha256,
    ck3_12002::ArmyBindings &bindings) noexcept {
  if (image_base == 0 || executable_sha256 != kExecutableSha256 ||
      !bindings.enabled) return;
  // The named callback24EA610 calls this complete seven-byte signed32 leaf.
  // The typed registrar and actual CArmy database/header/backlink operands are
  // paired in the .4 source ledger; no route or gathering condition applies.
  bindings.get_army_disembark_penalty_days =
      reinterpret_cast<decltype(bindings.get_army_disembark_penalty_days)>(
          image_base + kArmyDisembarkPenaltyDaysRva12004);
  bindings.current_disembark_penalty_enabled = true;

  // Each entrance is paired in the finite support ledger. Logical functions
  // with multiple unwind records reuse their first captured fragment and the
  // separately captured suffix; no common RVA delta is applied here.
  bindings.get_army_supply_capacity = ImageAddress12004<decltype(bindings.get_army_supply_capacity)>(image_base, 0x2C53BF0);
  bindings.get_army_attrition_fraction = ImageAddress12004<decltype(bindings.get_army_attrition_fraction)>(image_base, 0x24E2E30);
  bindings.get_army_monthly_supply_change = ImageAddress12004<decltype(bindings.get_army_monthly_supply_change)>(image_base, 0x24E5180);
  bindings.get_army_gathering_days_left = ImageAddress12004<decltype(bindings.get_army_gathering_days_left)>(image_base, 0x24E9050);
  bindings.persistent_regiment_storage_slot = ImageAddress12004<void **>(image_base, 0x5D1EB68);
  bindings.can_regiment_replenish = ImageAddress12004<decltype(bindings.can_regiment_replenish)>(image_base, 0x262C6E0);
  bindings.can_chunk_replenish = ImageAddress12004<decltype(bindings.can_chunk_replenish)>(image_base, 0x2657EF0);
  bindings.get_regiment_monthly_replenishment_fraction = ImageAddress12004<decltype(bindings.get_regiment_monthly_replenishment_fraction)>(image_base, 0x262CAB0);
  bindings.is_army_regiment_loss_writer_skipped = ImageAddress12004<decltype(bindings.is_army_regiment_loss_writer_skipped)>(image_base, 0x2634860);
  bindings.is_regiment_supply_loss_eligible = ImageAddress12004<decltype(bindings.is_regiment_supply_loss_eligible)>(image_base, 0x2A956B0);
  bindings.get_merge_destination_weight_part_a = ImageAddress12004<decltype(bindings.get_merge_destination_weight_part_a)>(image_base, 0x24E0140);
  bindings.get_merge_destination_weight_part_b = ImageAddress12004<decltype(bindings.get_merge_destination_weight_part_b)>(image_base, 0x24E0280);
  bindings.get_unit_normalized_edge_progress = ImageAddress12004<decltype(bindings.get_unit_normalized_edge_progress)>(image_base, 0x24AB2D0);
  bindings.get_unit_first_route_edge_duration = ImageAddress12004<decltype(bindings.get_unit_first_route_edge_duration)>(image_base, 0x24AB040);
  bindings.current_movement_progress_enabled = true;
  bindings.get_province_supply_limit = ImageAddress12004<decltype(bindings.get_province_supply_limit)>(image_base, 0x247BEA0);
  bindings.get_province_supply_usage = ImageAddress12004<decltype(bindings.get_province_supply_usage)>(image_base, 0x247C580);
  bindings.province_supply_character_fallback_slot = ImageAddress12004<void **>(image_base, 0x5C67570);
  bindings.current_province_supply_contributor_bindings.shares_current_war_side =
      ImageAddress12004<decltype(bindings.current_province_supply_contributor_bindings.shares_current_war_side)>(image_base, 0x2C090D0);
  bindings.current_province_supply_contributor_bindings.enabled = true;

  bindings.siege_loss_rate_raw = ImageAddress12004<const std::int64_t *>(image_base, 0x5C69618);
  bindings.raid_loss_rate_raw = ImageAddress12004<const std::int64_t *>(image_base, 0x5C69098);
  bindings.get_army_whole_loss_budget = ImageAddress12004<decltype(bindings.get_army_whole_loss_budget)>(image_base, 0x24DD560);
  bindings.get_army_supply_loss_budget = ImageAddress12004<decltype(bindings.get_army_supply_loss_budget)>(image_base, 0x24E32C0);
  bindings.is_army_siege_active = ImageAddress12004<decltype(bindings.is_army_siege_active)>(image_base, 0x24E8540);
  bindings.loss_application_inputs_enabled = true;
  // The actual budget consumer references 5C68C64. The old .3 source constant
  // 5C68B64 does not match that native RIP operand and is not propagated.
  bindings.county_entry_minimum_soldiers = ImageAddress12004<const std::int32_t *>(image_base, 0x5C68C64);
  bindings.county_entry_character_storage_slot = ImageAddress12004<void **>(image_base, kCharacterStorageSlotRva);
  bindings.get_county_entry_loss_budget = ImageAddress12004<decltype(bindings.get_county_entry_loss_budget)>(image_base, 0x24E6650);
  bindings.get_county_entry_loss_fraction = ImageAddress12004<decltype(bindings.get_county_entry_loss_fraction)>(image_base, 0x24E6570);
  bindings.get_county_entry_multiplier = ImageAddress12004<decltype(bindings.get_county_entry_multiplier)>(image_base, 0x24DD9A0);
  bindings.county_entry_condition = ImageAddress12004<decltype(bindings.county_entry_condition)>(image_base, 0x24E2230);
  bindings.county_entry_inputs_enabled = true;
  bindings.timing_bindings.loaded_grace_days = ImageAddress12004<const std::int32_t *>(image_base, 0x5C69AA0);
  bindings.timing_bindings.enabled = true;

  auto &monthly = bindings.monthly_loss_budget_bindings;
  monthly.is_unit_in_combat = ImageAddress12004<decltype(monthly.is_unit_in_combat)>(image_base, 0x24AC3C0);
  monthly.is_unit_gathering = ImageAddress12004<decltype(monthly.is_unit_gathering)>(image_base, 0x24AC140);
  monthly.is_army_fleet_supply_active = ImageAddress12004<decltype(monthly.is_army_fleet_supply_active)>(image_base, 0x24E8440);
  monthly.fleet_storage_slot = ImageAddress12004<void **>(image_base, 0x5D1F9B8);
  monthly.fleet_fallback_slot = ImageAddress12004<void **>(image_base, 0x5D1F9A8);
  monthly.fleet_date_sentinel = ImageAddress12004<const std::int32_t *>(image_base, 0x5C83A68);
  monthly.supply_state_levels_slot = ImageAddress12004<const std::int32_t **>(image_base, 0x5456498);
  monthly.supply_state_levels_count = ImageAddress12004<const std::int32_t *>(image_base, 0x54564A4);
  monthly.supply_state_fractions_slot = ImageAddress12004<const std::int64_t **>(image_base, 0x5451308);
  monthly.supply_state_fractions_count = ImageAddress12004<const std::int32_t *>(image_base, 0x5451314);
  monthly.character_storage_slot = bindings.county_entry_character_storage_slot;
  monthly.character_fallback_slot = bindings.province_supply_character_fallback_slot;
  monthly.province_fallback_slot = ImageAddress12004<void **>(image_base, 0x5D1E390);
  monthly.get_character_modifier_aggregator = ImageAddress12004<decltype(monthly.get_character_modifier_aggregator)>(image_base, 0x28C3AC0);
  monthly.read_character_modifier = ImageAddress12004<decltype(monthly.read_character_modifier)>(image_base, 0x23036E0);
  monthly.enabled = true;

  auto &caller = bindings.monthly_caller_effect_bindings;
  caller.character_storage_slot = monthly.character_storage_slot;
  caller.character_fallback_slot = monthly.character_fallback_slot;
  caller.war_storage_slot = ImageAddress12004<void **>(image_base, 0x5D1DE58);
  caller.war_fallback_slot = ImageAddress12004<void **>(image_base, 0x5D1DE40);
  caller.empty_war_ids_descriptor = ImageAddress12004<const void *>(image_base, 0x5459D38);
  caller.contains_war_participant = ImageAddress12004<decltype(caller.contains_war_participant)>(image_base, 0x2494B40);
  caller.enabled = true;
  bindings.monthly_daily_queue_bindings.army_fallback_slot = ImageAddress12004<void **>(image_base, 0x5D1DE50);
  bindings.monthly_daily_queue_bindings.enabled = true;
  bindings.monthly_first_removal_cleanup_inputs_enabled = true;
  bindings.monthly_current_helper_point_store_inputs_enabled = true;
  bindings.monthly_current_helper_domain_bindings = {
      true, ImageAddress12004<void **>(image_base, 0x5D1EB58),
      ImageAddress12004<void **>(image_base, 0x5D1DAF8),
      ImageAddress12004<void **>(image_base, 0x5D1DAE0),
      monthly.character_storage_slot, monthly.character_fallback_slot,
      ImageAddress12004<void **>(image_base, 0x5D1EB80),
      ImageAddress12004<void **>(image_base, 0x5D1EB38)};

  auto &resupply = bindings.current_land_resupply_bindings;
  resupply.is_resupply_eligible = ImageAddress12004<decltype(resupply.is_resupply_eligible)>(image_base, 0x2C09D10);
  resupply.is_army_fleet_supply_active = monthly.is_army_fleet_supply_active;
  resupply.character_storage_slot = monthly.character_storage_slot;
  resupply.loaded_gain_raw = ImageAddress12004<const std::int64_t *>(image_base, 0x5C69A50);
  resupply.enabled = true;
  auto &rate = bindings.current_land_supply_rate_bindings;
  rate.province_component_condition = ImageAddress12004<decltype(rate.province_component_condition)>(image_base, 0xC6AF20);
  rate.read_province_component = ImageAddress12004<decltype(rate.read_province_component)>(image_base, 0x2C4D530);
  rate.character_storage_slot = monthly.character_storage_slot;
  rate.character_fallback_slot = monthly.character_fallback_slot;
  rate.get_character_modifier_aggregator = monthly.get_character_modifier_aggregator;
  rate.read_character_modifier = monthly.read_character_modifier;
  rate.loaded_excess_slope_raw = ImageAddress12004<const std::int64_t *>(image_base, 0x5C69A38);
  rate.loaded_min_loss_raw = ImageAddress12004<const std::int64_t *>(image_base, 0x5C69A30);
  rate.loaded_max_loss_raw = ImageAddress12004<const std::int64_t *>(image_base, 0x5C69A40);
  rate.loaded_divisor_floor_raw = ImageAddress12004<const std::int64_t *>(image_base, 0x5C68F68);
  rate.enabled = true;
  auto &fleet = bindings.current_fleet_supply_tick_bindings;
  fleet.loaded_fleet_loss_raw = ImageAddress12004<const std::int64_t *>(image_base, 0x5C69A78);
  fleet.loaded_divisor_floor_raw = rate.loaded_divisor_floor_raw;
  fleet.loaded_max_loss_raw = rate.loaded_max_loss_raw;
  fleet.enabled = true;
  bindings.current_daily_supply_dispatch_bindings.enabled = true;
  bindings.current_month_first_refill_call_bindings.enabled = true;

  auto &scoped = bindings.scoped_ordered_refill_bindings;
  scoped.persistent_fallback_slot = bindings.monthly_current_helper_domain_bindings.persistent_regiment_fallback_slot;
  scoped.army_fallback_slot = bindings.monthly_daily_queue_bindings.army_fallback_slot;
  scoped.character_storage_slot = monthly.character_storage_slot;
  scoped.character_fallback_slot = monthly.character_fallback_slot;
  scoped.unit_position_province_fallback_slot = monthly.province_fallback_slot;
  scoped.resolve_arrg_reference = ImageAddress12004<decltype(scoped.resolve_arrg_reference)>(image_base, 0xC171A0);
  scoped.resolve_unit_reference = ImageAddress12004<decltype(scoped.resolve_unit_reference)>(image_base, 0xAEAA20);
  scoped.is_army_in_combat = ImageAddress12004<decltype(scoped.is_army_in_combat)>(image_base, 0x24E8340);
  scoped.is_unit_position_eligible = ImageAddress12004<decltype(scoped.is_unit_position_eligible)>(image_base, 0x24ACAA0);
  scoped.read_province_holder = ImageAddress12004<decltype(scoped.read_province_holder)>(image_base, 0x247D010);
  scoped.enabled = true;
  bindings.ordered_besieging_refill_bindings.arrg_fallback_slot = ImageAddress12004<void **>(image_base, 0x5D1F338);
  bindings.ordered_besieging_refill_bindings.enabled = true;

  // Actual Province/Siege bodies are owned by the Province family; their
  // paired inputs and loaded casualty table are reused in this Army observer.
  auto &besieging = bindings.current_province_besieging_bindings;
  besieging.unit_fallback_slot = ImageAddress12004<void **>(image_base, 0x5D1E378);
  besieging.army_fallback_slot = scoped.army_fallback_slot;
  besieging.province_fallback_slot = monthly.province_fallback_slot;
  besieging.siege_storage_slot = ImageAddress12004<void **>(image_base, 0x5D1EC88);
  besieging.army_excluded = ImageAddress12004<decltype(besieging.army_excluded)>(image_base, 0x24E8340);
  besieging.army_province_eligible = ImageAddress12004<decltype(besieging.army_province_eligible)>(image_base, 0x2C16670);
  besieging.besieging_strength = ImageAddress12004<decltype(besieging.besieging_strength)>(image_base, 0x247F1B0);
  besieging.assault_expected_loss = ImageAddress12004<decltype(besieging.assault_expected_loss)>(image_base, 0x25205A0);
  besieging.casualty_percentage_count = ImageAddress12004<const std::int32_t *>(image_base, 0x5452384);
  besieging.casualty_percentage_table_slot = ImageAddress12004<const std::int64_t **>(image_base, 0x54524C8);
  besieging.enabled = true;
}

ck3_12003::CommanderBindings BindCommanderImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept {
  ck3_12003::CommanderBindings result{};
  if (image_base == 0 || executable_sha256 != kExecutableSha256) return result;
  const auto core = BindCoreImage(image_base, executable_sha256);
  result.armies = BindArmyImage12004(image_base, executable_sha256);
  if (!core.enabled || !result.armies.enabled) return result;
  result.character_storage_slot = core.character_storage_slot;
  result.vector_allocator = ImageAddress12004<void *>(image_base, 0x54DEBB8);
  result.collect_candidates = ImageAddress12004<decltype(result.collect_candidates)>(image_base, 0x2C11BF0);
  result.can_set_commander = ImageAddress12004<decltype(result.can_set_commander)>(image_base, 0x29714F0);
  result.get_native_ai_base_quality = ImageAddress12004<decltype(result.get_native_ai_base_quality)>(image_base, 0x2C0B250);
  result.get_generic_advantage = ImageAddress12004<decltype(result.get_generic_advantage)>(image_base, 0xC6DED0);
  result.get_army_commander = ImageAddress12004<decltype(result.get_army_commander)>(image_base, 0x24E9EB0);
  result.get_character_modifier_aggregator = result.armies.monthly_loss_budget_bindings.get_character_modifier_aggregator;
  result.read_character_modifier = result.armies.monthly_loss_budget_bindings.read_character_modifier;
  result.read_unit_land_movement_rate = ImageAddress12004<decltype(result.read_unit_land_movement_rate)>(image_base, kCommanderLandMovementRateRva12004);
  result.read_unit_naval_movement_rate = ImageAddress12004<decltype(result.read_unit_naval_movement_rate)>(image_base, kCommanderNavalMovementRateRva12004);
  result.read_unit_current_edge_movement_rate = ImageAddress12004<decltype(result.read_unit_current_edge_movement_rate)>(image_base, kCommanderCurrentEdgeMovementRateRva12004);
  result.get_current_total_skill = ImageAddress12004<decltype(result.get_current_total_skill)>(image_base, 0x28B1690);
  result.current_total_martial_observer_enabled = true;
  result.enabled = true;
  return result;
}

ck3_12003::PlayerArmyReserveBindingsV1 BindPlayerArmyReserveImage12004V1(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept {
  ck3_12003::PlayerArmyReserveBindingsV1 result{};
  if (image_base == 0 || executable_sha256 != kExecutableSha256) return result;
  result.construct_empty = ImageAddress12004<decltype(result.construct_empty)>(image_base, 0xC6D5B0);
  result.initialize_owner = ImageAddress12004<decltype(result.initialize_owner)>(image_base, 0x25A7100);
  result.count_all_unraised = ImageAddress12004<decltype(result.count_all_unraised)>(image_base, 0x25A6770);
  result.destroy_contents = ImageAddress12004<decltype(result.destroy_contents)>(image_base, 0xB03250);
  result.enabled = true;
  return result;
}

ck3_12003::CommanderTargetRollBindings BindCommanderTargetRollImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256,
    const ck3_12002::ProvinceBindings &provinces,
    const ck3_12002::CombatBindings &combat) noexcept {
  ck3_12003::CommanderTargetRollBindings result{};
  if (image_base == 0 || executable_sha256 != kExecutableSha256) return result;
  result.provinces = provinces;
  result.combat = combat;
  result.enabled = provinces.enabled && combat.enabled;
  return result;
}

} // namespace xar::ck3_12004
