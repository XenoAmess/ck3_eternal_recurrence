#include "xar_bridge/ck3_12004_army.hpp"
#include "xar_bridge/ck3_12004_army_support.hpp"

namespace xar::ck3_12004 {
namespace {
// Actual finite paired instructions and operands are recorded in
// army-world-family/native-main/BASE-READER-SOURCE-CLOSED.json.
constexpr std::uintptr_t kUnitRegistryRva = 0x5D1E380;
constexpr std::uintptr_t kArmyRegistryRva = 0x5D1DE48;
constexpr std::uintptr_t kArRgRegistryRva = 0x5D1F340;
constexpr std::uintptr_t kUnitStateRva = 0xD19140;
constexpr std::uintptr_t kArmyCurrentRva = 0x2A95720;
constexpr std::uintptr_t kArmyMaximumRva = 0x24E0430;

// These are actual .4 source-use targets, not inherited executable bindings.
// Maps01..12 close the independent current input branches. The mutating
// source producers are never installed as observer callbacks.
void PopulateClosedCurrentInputs(std::uintptr_t base, ArmyBindings &out) noexcept {
  const auto at = [base](std::uintptr_t rva) {
    return reinterpret_cast<const void *>(base + rva);
  };
  auto &common = out.current_daily_assault_roster_admission_bindings;
  common.enabled = true;
  common.game_state_slot = at(kGameStateSlotRva);
  common.army_registry_slot = at(0x5D1DE48);
  common.army_fallback_slot = at(0x5D1DE50);
  common.unit_registry_slot = at(0x5D1E380);
  common.unit_fallback_slot = at(0x5D1E378);
  common.character_registry_slot = at(kCharacterStorageSlotRva);
  common.character_fallback_slot = at(0x5C67570);
  common.war_registry_slot = at(0x5D1DE58);
  common.war_fallback_slot = at(0x5D1DE40);
  common.siege_registry_slot = at(0x5D1EC88);
  common.siege_fallback_slot = at(0x5D1EC60);
  common.province_fallback_slot = at(0x5D1E390);
  common.relationship_fallback_slot = at(0x5D27B70);
  common.get_current_province73c_classification =
      reinterpret_cast<decltype(common.get_current_province73c_classification)>(base + 0x2C099D0);
  auto &table = out.current_daily_assault_table_bindings;
  table.enabled = true;
  table.game_state_slot = common.game_state_slot;
  table.siege_registry_slot = common.siege_registry_slot;
  table.siege_fallback_slot = common.siege_fallback_slot;
  table.army_registry_slot = common.army_registry_slot;
  table.army_fallback_slot = common.army_fallback_slot;
  table.arrg_registry_slot = at(0x5D1F340);
  table.arrg_fallback_slot = at(0x5D1F338);
  table.expected_army_allocator = at(0x54E0570);
  table.expected_arrg_allocator = at(0x54DEB68);
  out.current_daily_assault_loss_inputs_enabled = true;
  out.regiment_composition_enabled = true;
  auto &dated = out.current_pre_date_dated_append_bindings;
  dated.common = common;
  dated.combat_registry_slot = at(0x5D1DE70);
  dated.combat_fallback_slot = at(0x5D1DE18);
  auto &refresh = out.current_post_admission_refresh_bindings;
  refresh.common = common;
  refresh.arrg_registry_slot = table.arrg_registry_slot;
  refresh.arrg_fallback_slot = table.arrg_fallback_slot;
  auto &condition = out.current_army_condition30_bindings;
  condition.common = common;
  condition.construct_actor_scope = reinterpret_cast<decltype(condition.construct_actor_scope)>(base + 0x9F9E20);
  condition.destroy_scope = reinterpret_cast<decltype(condition.destroy_scope)>(base + 0x87E0E0);
  condition.evaluate_condition = reinterpret_cast<decltype(condition.evaluate_condition)>(base + 0x372DF10);
  auto &flag20 = out.current_army_flag20_bindings;
  flag20.common = common;
  flag20.get_current_flag20 = reinterpret_cast<decltype(flag20.get_current_flag20)>(base + 0x2C4B820);
  auto &flag21 = out.current_army_flag21_bindings;
  flag21.common = common;
  flag21.default_header = at(0x5459D38);
  flag21.get_current_shared_tail = reinterpret_cast<decltype(flag21.get_current_shared_tail)>(base + 0x24E3FC0);
  auto &flag31 = out.current_army_flag31_bindings;
  flag31.common = common;
  flag31.combat_registry_slot = dated.combat_registry_slot;
  flag31.combat_fallback_slot = dated.combat_fallback_slot;
  flag31.rule_provider_slot = at(0x5D21DC8);
  flag31.rule_source_mode_slot = at(0x5D1DADC);
  flag31.rule_source_module_base = base;
  flag31.rule_source_image_size = 102518784;
  flag31.construct_actor_scope = condition.construct_actor_scope;
  flag31.destroy_scope = condition.destroy_scope;
  flag31.evaluate_condition = condition.evaluate_condition;
  auto &prefix = out.current_pre_date_character_prefix_bindings;
  prefix.common = common;
  prefix.membership = reinterpret_cast<decltype(prefix.membership)>(base + 0x2C12150);
  prefix.basic_rule = reinterpret_cast<decltype(prefix.basic_rule)>(base + 0x1D63160);
  prefix.availability = reinterpret_cast<decltype(prefix.availability)>(base + 0x2C12980);
  auto &relation = out.current_selected_title_holder_owner_relation_bindings;
  relation.common = common;
  relation.title_registry_slot = at(0x5D1DAF8);
  relation.title_fallback_slot = at(0x5D1DAE0);
  relation.get_relation = reinterpret_cast<decltype(relation.get_relation)>(base + 0x28B2800);
  auto &candidate = out.current_candidate_detachment_mapper_bindings;
  candidate.enabled = true;
  candidate.lookup = table;
  candidate.regi_registry_slot = at(0x5D1EB68);
  candidate.regi_fallback_slot = at(0x5D1EB58);
  auto &detachment = out.current_detachment_data_bindings;
  detachment.common = table;
  detachment.regi_registry_slot = candidate.regi_registry_slot;
  detachment.regi_fallback_slot = candidate.regi_fallback_slot;
  detachment.unit_registry_slot = common.unit_registry_slot;
  detachment.unit_fallback_slot = common.unit_fallback_slot;
  detachment.character_registry_slot = common.character_registry_slot;
  detachment.character_fallback_slot = common.character_fallback_slot;
  detachment.province_fallback_slot = common.province_fallback_slot;
  detachment.static_context = flag21.default_header;
  detachment.canonical_pending_vtable = at(0x44DEFB8);
  detachment.ready_pending_callback = at(0x8863D0);
  detachment.get_capital = reinterpret_cast<decltype(detachment.get_capital)>(base + 0x28B1CB0);
  detachment.compute_date = reinterpret_cast<decltype(detachment.compute_date)>(base + 0x2C54320);
  auto &pending = out.current_pre_date_pending_update_bindings;
  pending.common = common;
  pending.combat_registry_slot = dated.combat_registry_slot;
  pending.combat_fallback_slot = dated.combat_fallback_slot;
  pending.arrg_registry_slot = table.arrg_registry_slot;
  pending.arrg_fallback_slot = table.arrg_fallback_slot;
  pending.contract_registry_slot = at(0x5D1EB88);
  pending.contract_fallback_slot = at(0x5D1EB40);
  pending.persistent_registry_slot = candidate.regi_registry_slot;
  pending.persistent_fallback_slot = candidate.regi_fallback_slot;
  pending.native_empty_pending_buffer = at(0x5D68BA0);
  pending.expected_pending_vector_allocator = table.expected_arrg_allocator;
  auto &roles = out.current_army_combat_roles_phase_bindings;
  roles.common = common;
  roles.combat_registry_slot = dated.combat_registry_slot;
  roles.combat_fallback_slot = dated.combat_fallback_slot;
  // This is the actual CombatManager secondary receiver, not CCombat.
  roles.expected_secondary_vtable = at(0x477F188);
  roles.maneuver_threshold_slot = at(0x5C69BB0);
  auto &removal = out.current_assault_removal_reference_bindings;
  removal.enabled = true;
  removal.lookup = table;
}
} // namespace

ArmyBindings BindArmyImage12004(std::uintptr_t image_base,
    std::string_view executable_sha256) noexcept {
  ArmyBindings result{};
  if (!image_base || executable_sha256 != kExecutableSha256) return result;
  result.game_state_slot =
      reinterpret_cast<void **>(image_base + kGameStateSlotRva);
  result.unit_storage_slot =
      reinterpret_cast<void **>(image_base + kUnitRegistryRva);
  result.internal_army_storage_slot =
      reinterpret_cast<void **>(image_base + kArmyRegistryRva);
  result.regiment_storage_slot =
      reinterpret_cast<void **>(image_base + kArRgRegistryRva);
  result.get_unit_state = reinterpret_cast<decltype(result.get_unit_state)>(
      image_base + kUnitStateRva);
  result.get_army_current_soldiers =
      reinterpret_cast<decltype(result.get_army_current_soldiers)>(
          image_base + kArmyCurrentRva);
  result.get_army_maximum_soldiers =
      reinterpret_cast<decltype(result.get_army_maximum_soldiers)>(
          image_base + kArmyMaximumRva);
  result.enabled = true;
  PopulateClosedCurrentInputs(image_base, result);
  PopulateArmySupportBindings12004(image_base, executable_sha256, result);
  return result;
}

void *ResolveArmyUnit12004(const ArmyBindings &bindings,
    std::int32_t army_id) noexcept {
  return ck3_12002::ResolveArmyUnit(bindings, army_id);
}
void *ResolveInternalArmy12004(const ArmyBindings &bindings,
    std::int32_t internal_army_id) noexcept {
  return ck3_12002::ResolveInternalArmy(bindings, internal_army_id);
}
bool ReadArmyGathering12004(const ArmyBindings &bindings, std::int32_t unit_id,
    bool &gathering) noexcept {
  return ck3_12002::ReadArmyGathering(bindings, unit_id, gathering);
}
bool ReadArmiesForCharacters12004(const ArmyBindings &bindings,
    std::span<const std::int32_t> owner_character_ids,
    std::vector<game::ArmySnapshot> &out,
    std::int32_t controlled_owner_character_id) noexcept {
  return ck3_12002::ReadArmiesForCharacters(
      bindings, owner_character_ids, out, controlled_owner_character_id);
}
game::ReadArmyStrengthsResult ReadArmyStrengthsForScope12004(
    const ArmyBindings &bindings, std::span<const ArmyStrengthScope> scope,
    std::vector<game::ArmyStrengthSnapshot> &out) noexcept {
  return ck3_12002::ReadArmyStrengthsForScope(bindings, scope, out);
}
game::ReadArmyStrengthsResult ReadArmyStrengths12004(
    const ArmyBindings &bindings, const game::Snapshot &world,
    std::vector<game::ArmyStrengthSnapshot> &out) noexcept {
  return ck3_12002::ReadArmyStrengths(bindings, world, out);
}
game::ArmyProvinceSupplySnapshot ReadArmyProvinceSupplyForPreview12004(
    const ArmyBindings &bindings, const ck3_12002::MilitaryWorldAccess &access,
    const game::PreviewMoveArmyResult &preview) noexcept {
  return ck3_12002::ReadArmyProvinceSupplyForPreview(bindings, access, preview);
}

} // namespace xar::ck3_12004
