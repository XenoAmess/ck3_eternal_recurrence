#include "xar_bridge/ck3_12004_combat.hpp"

#include "xar_bridge/ck3_12004_family_abi.hpp"
#include "xar_bridge/ck3_12004_phase_character.hpp"
#include "xar_bridge/ck3_12004_religion_profile.hpp"

namespace xar::ck3_12004 {

ck3_12002::CombatBindings BindCombatImage12004(
    std::uintptr_t base, std::string_view sha) noexcept {
  ck3_12002::CombatBindings b{};
  if (base == 0 || sha != kExecutableSha256) return b;

  // Independent actual .4 bindings; shared software readers retain their ABI.
  b.game_state_slot = reinterpret_cast<decltype(b.game_state_slot)>(base + 0x5C68C50);
  b.army_storage_slot = reinterpret_cast<decltype(b.army_storage_slot)>(base + 0x5D1E380);
  b.army_internal_storage_slot = reinterpret_cast<decltype(b.army_internal_storage_slot)>(base + 0x5D1DE48);
  b.regiment_storage_slot = reinterpret_cast<decltype(b.regiment_storage_slot)>(base + 0x5D1F340);
  b.character_storage_slot = reinterpret_cast<decltype(b.character_storage_slot)>(base + 0x5C67568);
  b.combat_storage_slot = reinterpret_cast<decltype(b.combat_storage_slot)>(base + 0x5D1DE70);
  b.get_army_commander = reinterpret_cast<decltype(b.get_army_commander)>(base + 0x24E9EB0);
  b.get_commander_advantage = reinterpret_cast<decltype(b.get_commander_advantage)>(base + 0xC6DED0);
  b.get_province_terrain = reinterpret_cast<decltype(b.get_province_terrain)>(base + 0x247E570);
  b.evaluate_regiment_stats_at_province = reinterpret_cast<decltype(b.evaluate_regiment_stats_at_province)>(base + 0x26344A0);
  b.is_special_combat_regiment = reinterpret_cast<decltype(b.is_special_combat_regiment)>(base + 0x2634860);
  b.get_character_modifier_aggregator = reinterpret_cast<decltype(b.get_character_modifier_aggregator)>(base + 0x28C3AC0);
  b.read_character_modifier = reinterpret_cast<decltype(b.read_character_modifier)>(base + 0x23036E0);
  b.get_combat_rules = reinterpret_cast<decltype(b.get_combat_rules)>(base + 0x899E40);
  b.read_counter_current_chunk = reinterpret_cast<decltype(b.read_counter_current_chunk)>(base + 0x2657950);
  b.resolve_counter_classes = reinterpret_cast<decltype(b.resolve_counter_classes)>(base + 0x2653EF0);
  b.get_counter_context_scale = reinterpret_cast<decltype(b.get_counter_context_scale)>(base + 0x2C533C0);
  b.get_knight_effectiveness_context = reinterpret_cast<decltype(b.get_knight_effectiveness_context)>(base + 0x28BFC50);
  b.read_knight_effectiveness = reinterpret_cast<decltype(b.read_knight_effectiveness)>(base + 0x2C06AE0);
  b.is_holding_defender = reinterpret_cast<decltype(b.is_holding_defender)>(base + 0x2C09D10);
  b.commander_min_roll = reinterpret_cast<decltype(b.commander_min_roll)>(base + 0x5C699BC);
  b.commander_max_roll = reinterpret_cast<decltype(b.commander_max_roll)>(base + 0x5C699B8);
  b.knight_damage_per_prowess = reinterpret_cast<decltype(b.knight_damage_per_prowess)>(base + 0x5C699A8);
  b.knight_toughness_per_prowess = reinterpret_cast<decltype(b.knight_toughness_per_prowess)>(base + 0x5C699B0);
  b.minimum_combat_width = reinterpret_cast<decltype(b.minimum_combat_width)>(base + 0x5C699C8);
  b.base_combat_width_ratio = reinterpret_cast<decltype(b.base_combat_width_ratio)>(base + 0x5C69BA8);
  b.ordinary_regiment_storage_slot = reinterpret_cast<decltype(b.ordinary_regiment_storage_slot)>(base + 0x5D1EB68);
  b.ordinary_regiment_fallback_slot = reinterpret_cast<decltype(b.ordinary_regiment_fallback_slot)>(base + 0x5D1EB58);
  b.ordinary_selector_storage_slot = reinterpret_cast<decltype(b.ordinary_selector_storage_slot)>(base + 0x5D1DAF8);
  b.ordinary_selector_fallback_slot = reinterpret_cast<decltype(b.ordinary_selector_fallback_slot)>(base + 0x5D1DAE0);
  b.ordinary_character_fallback_slot = reinterpret_cast<decltype(b.ordinary_character_fallback_slot)>(base + 0x5C67570);
  b.maa_culture_storage_slot = reinterpret_cast<decltype(b.maa_culture_storage_slot)>(base + 0x5D1E2F0);
  b.maa_culture_fallback_slot = reinterpret_cast<decltype(b.maa_culture_fallback_slot)>(base + 0x5D1E2E8);
  b.maa_army_regiment_fallback_slot = reinterpret_cast<decltype(b.maa_army_regiment_fallback_slot)>(base + 0x5D1F338);
  b.maa_accolade_storage_slot = reinterpret_cast<decltype(b.maa_accolade_storage_slot)>(base + 0x5D1ECA0);
  b.maa_accolade_fallback_slot = reinterpret_cast<decltype(b.maa_accolade_fallback_slot)>(base + 0x5D1EC40);
  b.maa_get_piety_rank = reinterpret_cast<decltype(b.maa_get_piety_rank)>(base + 0x28BE0B0);
  b.maa_get_government = reinterpret_cast<decltype(b.maa_get_government)>(base + 0x28C2DF0);
  b.maa_get_actual_army = reinterpret_cast<decltype(b.maa_get_actual_army)>(base + 0x262D030);
  b.maa_get_title_holder = reinterpret_cast<decltype(b.maa_get_title_holder)>(base + 0x2C42930);
  b.maa_get_tier = reinterpret_cast<decltype(b.maa_get_tier)>(base + 0x2B8FCD0);
  b.maa_get_selector_factor = reinterpret_cast<decltype(b.maa_get_selector_factor)>(base + 0x2B9CBA0);
  constexpr std::array<std::uintptr_t, 5> stat_bases{
      0x5C69BD0, 0x5C69BC0, 0x5C69BC8, 0x5C69BE0, 0x5C69BD8};
  for (std::size_t i = 0; i != stat_bases.size(); ++i)
    b.ordinary_stat_loaded_bases[i] =
        reinterpret_cast<const std::int64_t *>(base + stat_bases[i]);

  constexpr std::array<std::uintptr_t, 3> type_rvas{
      0x30BDC60, 0x30BDD00, 0x30BDDA0};
  constexpr std::array<std::uintptr_t, 3> linked_rvas{
      0x2B91E80, 0x2B92140, 0x2B924A0};
  for (std::size_t i = 0; i != type_rvas.size(); ++i) {
    b.maa_get_type_environment[i] =
        reinterpret_cast<ck3_12002::MaaGetTypeEnvironment>(base + type_rvas[i]);
    b.maa_get_linked_environment[i] =
        reinterpret_cast<ck3_12002::MaaGetLinkedEnvironment>(base + linked_rvas[i]);
  }

  namespace religion_profile = ck3_12004::religion::profile;
  const auto character = ck3_12004::phase_character::BindImage(base, sha);
  auto &rite = b.phase_rite_parameters;
  rite.character_rite = reinterpret_cast<decltype(rite.character_rite)>(
      base + religion_profile::kCharacterRiteRva);
  rite.character_faith = reinterpret_cast<decltype(rite.character_faith)>(
      base + religion_profile::kCharacterFaithRva);
  rite.rite_faith = reinterpret_cast<decltype(rite.rite_faith)>(
      base + religion_profile::kRiteFaithRva);
  rite.parameters.enabled = true;
  rite.parameters.contains_boolean_parameter =
      reinterpret_cast<decltype(rite.parameters.contains_boolean_parameter)>(
          base + religion_profile::kBooleanParameterMembershipRva);
  rite.parameters.parameter_key =
      reinterpret_cast<decltype(rite.parameters.parameter_key)>(
          base + religion_profile::kParameterTokenKeyRva);
  rite.enabled = true;

  auto &warmonger = b.phase_warmonger_core;
  warmonger.character_rite = rite.character_rite;
  warmonger.tenet_database = reinterpret_cast<void *const *>(
      base + religion_profile::kTenetDatabaseSlotRva);
  warmonger.rite_fallback = reinterpret_cast<void *const *>(base + 0x5C67670);
  warmonger.contains = reinterpret_cast<decltype(warmonger.contains)>(
      base + religion_profile::kActualDefinitionPointerContainsRva);
  warmonger.enabled = true;

  auto &validity = b.phase_berserker_validity_inputs;
  validity.culture_store = reinterpret_cast<void *const *>(base + 0x5D1E2F0);
  validity.culture_fallback = reinterpret_cast<void *const *>(base + 0x5D1E2E8);
  validity.trait_database = reinterpret_cast<void *const *>(
      base + ck3_12004::phase_character::kTraitDatabaseSlotRva);
  validity.rite_fallback = warmonger.rite_fallback;
  validity.traits = character;
  validity.character_rite = rite.character_rite;
  validity.character_faith = rite.character_faith;
  validity.rite_faith = rite.rite_faith;
  validity.faith_religion = reinterpret_cast<decltype(validity.faith_religion)>(
      base + religion_profile::kFaithReligionRva);
  validity.enabled = true;

  auto &chance = b.phase_berserker_chance_inputs;
  chance.character = character;
  chance.trait_database = validity.trait_database;
  chance.character_perk_database = reinterpret_cast<void *const *>(
      base + religion_profile::kPerkDatabaseSlotRva);
  chance.dynasty_perk_database = reinterpret_cast<void *const *>(base + 0x5D1FC00);
  chance.house_store = reinterpret_cast<void *const *>(base + kFamilyHouseStoreSlotRva);
  chance.house_fallback = reinterpret_cast<void *const *>(base + kFamilyHouseFallbackSlotRva);
  chance.dynasty_store = reinterpret_cast<void *const *>(base + kFamilyDynastyStoreSlotRva);
  chance.dynasty_fallback = reinterpret_cast<void *const *>(base + kFamilyDynastyFallbackSlotRva);
  chance.accolade_store = reinterpret_cast<void *const *>(base + 0x5D1ECA0);
  chance.accolade_fallback = reinterpret_cast<void *const *>(base + 0x5D1EC40);
  chance.character_perks = reinterpret_cast<decltype(chance.character_perks)>(
      base + religion_profile::kCharacterActualPerksRva);
  chance.enabled = true;

  b.ordinary_stat_inputs_enabled = true;
  b.maa_stat_inputs_enabled = true;
  b.knight_model_association_enabled = true;
  b.enabled = true;
  return b;
}

} // namespace xar::ck3_12004
