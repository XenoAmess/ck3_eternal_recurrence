#include "xar_bridge/ck3_12004_phase.hpp"

#include "xar_bridge/ck3_12004_combat.hpp"
#include "xar_bridge/ck3_12004_family_break_penalty.hpp"
#include "xar_bridge/ck3_12004_phase_character.hpp"
#include "xar_bridge/ck3_12004_religion_profile.hpp"

namespace xar::ck3_12004 {
namespace {

template <class T>
T At(std::uintptr_t base, std::uintptr_t rva) noexcept {
  return reinterpret_cast<T>(base + rva);
}

void **Slot(std::uintptr_t base, std::uintptr_t rva) noexcept {
  return At<void **>(base, rva);
}

// Finite full-body/fragment joins and named RIP operands are retained in
// migration-steam25734779/existing-contact-phase-12004/phase-native.
// These are actual .4 addresses, selected by the direct .4 hash below.
ck3_12002::PhaseDefinitionBindings Definitions(std::uintptr_t base,
    std::string_view sha, const ck3_12002::CombatBindings &combat) noexcept {
  auto b = BindFamilyBreakIdentifiersImage(base, sha);
  b.maa_type_registry = Slot(base, 0x5C67558);
  b.commander_min_roll = combat.commander_min_roll;
  b.commander_max_roll = combat.commander_max_roll;
  b.knight_damage_per_prowess = combat.knight_damage_per_prowess;
  b.knight_toughness_per_prowess = combat.knight_toughness_per_prowess;
  b.minimum_combat_width = combat.minimum_combat_width;
  b.base_combat_width_ratio = combat.base_combat_width_ratio;
  return b;
}

ck3_12002::phase_culture::Bindings Culture(std::uintptr_t base,
    const ck3_12002::CombatBindings &combat,
    const ck3_12002::phase_character::Bindings &traits,
    const ck3_12002::PhaseDefinitionBindings &definitions) noexcept {
  ck3_12002::phase_culture::Bindings b{};
  const auto &nested = combat.phase_berserker_chance_inputs;
  b.enabled = true;
  b.character_store = combat.character_storage_slot;
  b.character_fallback = combat.ordinary_character_fallback_slot;
  b.house_store = const_cast<void **>(nested.house_store);
  b.house_fallback = const_cast<void **>(nested.house_fallback);
  b.dynasty_store = const_cast<void **>(nested.dynasty_store);
  b.dynasty_fallback = const_cast<void **>(nested.dynasty_fallback);
  b.culture_store = combat.maa_culture_storage_slot;
  b.culture_fallback = combat.maa_culture_fallback_slot;
  b.innovation_database = Slot(base, 0x5D1DEE8);
  b.innovation_fallback = Slot(base, 0x5D202C8);
  b.tradition_database = Slot(base, 0x5D1DEE0);
  b.tradition_fallback = Slot(base, 0x5D1FB50);
  b.dynasty_perk_database = const_cast<void **>(nested.dynasty_perk_database);
  b.character_perk_database = const_cast<void **>(nested.character_perk_database);
  b.character_context = traits.knight_context;
  b.character_perks = nested.character_perks;
  b.culture_has_parameter = At<decltype(b.culture_has_parameter)>(base, 0x25497F0);
  b.lookup_script_identifier = At<decltype(b.lookup_script_identifier)>(base, 0x3F4F850);
  b.script_identifier_name = definitions.script_identifier_name;
  return b;
}

ck3_12002::AdvantageBindings Advantage(std::uintptr_t base,
    const ck3_12002::CombatBindings &combat) noexcept {
  ck3_12002::AdvantageBindings b{};
  b.enabled = true;
  // Combat effect definitions live in a different database from the MAA rules
  // returned by combat.get_combat_rules (899E40).
  b.get_rules = At<decltype(b.get_rules)>(base, 0x8FC3E0);
  b.select_supply = At<decltype(b.select_supply)>(base, 0x2587090);
  b.select_debt = At<decltype(b.select_debt)>(base, 0x2BCA600);
  b.resolve_treasury = At<decltype(b.resolve_treasury)>(base, 0x9D6DF0);
  b.get_modifier_aggregator = combat.get_character_modifier_aggregator;
  b.get_terrain = combat.get_province_terrain;
  b.is_holding_defender = combat.is_holding_defender;
  b.province_has_holding = At<decltype(b.province_has_holding)>(base, 0xC6AF20);
  b.get_government = combat.maa_get_government;
  b.has_modifier_flag = At<decltype(b.has_modifier_flag)>(base, 0x2303790);
  b.read_province_modifier = At<decltype(b.read_province_modifier)>(base, 0x2C23340);
  b.read_modifier_value = At<decltype(b.read_modifier_value)>(base, 0x2C4D530);
  b.regiment_storage_slot = combat.regiment_storage_slot;
  b.supply_unit_storage_slot = combat.ordinary_regiment_storage_slot;
  b.supply_thresholds = At<decltype(b.supply_thresholds)>(base, 0x5456498);
  b.supply_threshold_count = At<decltype(b.supply_threshold_count)>(base, 0x54564A4);
  namespace r = religion::profile;
  auto &faith = b.constructor_religion;
  faith.enabled = true;
  faith.rite_storage_slot = Slot(base, r::kRiteStorageSlotRva);
  faith.faith_storage_slot = Slot(base, 0x5D1E300);
  faith.null_rite_slot = const_cast<void **>(combat.phase_warmonger_core.rite_fallback);
  faith.null_faith_slot = Slot(base, 0x5D1E2E0);
  faith.target_faith_is_unreformed = At<decltype(faith.target_faith_is_unreformed)>(
      base, r::kFaithIsUnreformedRva);
  return b;
}

ck3_12002::PhaseMiscBindings Misc(std::uintptr_t base,
    const ck3_12002::CombatBindings &combat,
    const ck3_12002::PhaseDefinitionBindings &definitions) noexcept {
  ck3_12002::PhaseMiscBindings b{};
  b.enabled = true;
  b.identifiers = definitions;
  b.character_store = combat.character_storage_slot;
  b.character_fallback = combat.ordinary_character_fallback_slot;
  b.accolade_store = combat.maa_accolade_storage_slot;
  b.accolade_fallback = combat.maa_accolade_fallback_slot;
  b.court_position_store = Slot(base, 0x5D1DD10);
  b.court_position_fallback = Slot(base, 0x5D1DD08);
  b.court_type_database = Slot(base, 0x5C67330);
  b.court_type_fallback = Slot(base, 0x5D1DD40);
  b.modifier_database = Slot(base, 0x5C670F8);
  b.modifier_fallback = Slot(base, 0x5D1E0B0);
  b.lookup_modifier = At<decltype(b.lookup_modifier)>(base, 0xAB8D20);
  b.can_be_acclaimed = At<decltype(b.can_be_acclaimed)>(base, 0x2B912E0);
  b.accolade_has_parameter = At<decltype(b.accolade_has_parameter)>(base, 0x27BF5C0);
  b.character_government = combat.maa_get_government;
  return b;
}

} // namespace

ck3_12002::PhaseBindings BindPhaseImage12004(std::uintptr_t base,
    std::string_view sha) noexcept {
  ck3_12002::PhaseBindings b{};
  if (!base || sha != kExecutableSha256) return b;
  b.image_base = base;
  b.combat = BindCombatImage12004(base, sha);
  b.traits = phase_character::BindImage(base, sha);
  b.definitions = Definitions(base, sha, b.combat);
  b.culture = Culture(base, b.combat, b.traits, b.definitions);
  b.advantage = Advantage(base, b.combat);
  b.misc = Misc(base, b.combat, b.definitions);
  b.construct_side = At<decltype(b.construct_side)>(base, 0x264CA40);
  b.populate_side = At<decltype(b.populate_side)>(base, 0x264DE10);
  b.select_commander = At<decltype(b.select_commander)>(base, 0x264D770);
  b.refresh_strength = At<decltype(b.refresh_strength)>(base, 0x26505C0);
  b.read_strength = At<decltype(b.read_strength)>(base, 0x26510E0);
  b.destroy_side = At<decltype(b.destroy_side)>(base, 0x2586180);
  b.resolve_advantage = At<decltype(b.resolve_advantage)>(base, 0x258B4F0);
  b.read_dynamic = At<decltype(b.read_dynamic)>(base, 0x258A450);
  b.province_has_holding = At<decltype(b.province_has_holding)>(base, 0xC6AF20);
  b.commander_dynamic = At<decltype(b.commander_dynamic)>(base, 0x2589DF0);
  b.side_modifier = At<decltype(b.side_modifier)>(base, 0x25899A0);
  b.relation_kind = At<decltype(b.relation_kind)>(base, 0x25897F0);
  // Local phase shell ctor258608F/2586099 RIP operands, distinct from the
  // secondary-interface table used by the ongoing Combat manager.
  b.combat_primary_vtable = base + 0x473D148;
  b.combat_secondary_vtable = base + 0x473D110;
  b.commander_army_gate = At<decltype(b.commander_army_gate)>(base, 0x24DFB50);
  b.commander_null_army_slot = Slot(base, 0x5D1DE50);
  b.rite_hostility = At<decltype(b.rite_hostility)>(base, 0x2591CC0);
  b.hostility_factor_count = At<decltype(b.hostility_factor_count)>(base, 0x5451D34);
  b.hostility_factors = At<decltype(b.hostility_factors)>(base, 0x5451D28);
  b.enabled = true;
  return b;
}

} // namespace xar::ck3_12004
