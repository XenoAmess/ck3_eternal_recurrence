#pragma once

#include "xar_bridge/game_contract.hpp"
#include "xar_bridge/ck3_12003_army_combat_roles_phase_inputs.hpp"
#include "xar_bridge/phase_event_commander_side_identity_v1.hpp"
#include <string_view>

namespace xar::ck3_12004 {
inline constexpr std::string_view kCommanderSideIdentityExecutableSha256 =
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
struct PhaseCommanderSideIdentityBindings12004 {
  bool enabled = false;
  ck3_12003::CurrentArmyCombatRolesPhaseBindings12003 roles{};
};
// Borrow the already source-closed actual4 Army bindings. No new RVA/callee.
inline PhaseCommanderSideIdentityBindings12004 BindPhaseCommanderSideIdentity12004(
    const ck3_12003::CurrentArmyCombatRolesPhaseBindings12003 &roles,
    std::string_view executable_sha256) noexcept {
  if (executable_sha256 != kCommanderSideIdentityExecutableSha256 || !roles.common.enabled)
    return {};
  return {true, roles};
}
inline game::PhaseEventCommanderSideIdentityV1 ReadPhaseCommanderSideIdentity12004(
    const PhaseCommanderSideIdentityBindings12004 &bindings,
    const game::CombatSimulationInputsSnapshot &inputs) {
  using namespace ck3_12003;
  using namespace daily_assault_roster_detail;
  game::PhaseEventCommanderSideIdentityV1 output;
  output.commander_side_identity_source_closed = bindings.enabled;
  const auto &b = bindings.roles;
  CurrentPostAdmissionRefreshBindings12003 borrowed{}; borrowed.common = b.common;
  CurrentArmyFlag31Bindings12003 raw{}; raw.common = b.common;
  raw.combat_registry_slot = b.combat_registry_slot;
  raw.combat_fallback_slot = b.combat_fallback_slot;
  std::vector<post_admission_refresh_detail::ResolutionCacheRow> cache;
  std::uint32_t ordinal = 0, comparisons = 0;
  for (const auto &army : inputs.armies) {
    if (army.commander.status == game::CombatObservationStatus::available &&
        army.commander.character_id != -1) {
      game::PhaseEventCommanderSideIdentityOccurrenceV1 row;
      row.occurrence_index = ordinal++;
      row.character_id = static_cast<std::uint32_t>(army.commander.character_id);
      row.source_public_cunit_id = army.army_id;
      if (army.native_carmy_id_observable) row.source_native_carmy_id = army.native_carmy_id;
      row.encounter_role = army.encounter_role;
      const auto observe = [&] {
        const auto fail = [&](std::string_view reason) { row.unavailable_reason = reason; };
        if (!bindings.enabled) { fail("actual4_commander_side_binding_unavailable"); return; }
        if (!row.source_native_carmy_id || *row.source_native_carmy_id == -1) {
          fail("v2_native_carmy_full_id_unavailable"); return;
        }
        const auto requested = static_cast<std::uint32_t>(*row.source_native_carmy_id);
        const auto physical = post_admission_refresh_detail::Selected(borrowed, requested, true, cache);
        row.actual_physical_army_full_id_raw = physical.observation.selected_full_id_u32;
        if (!physical.object || !physical.observation.selected_object_ready ||
            !row.actual_physical_army_full_id_raw) {
          fail("current_physical_army_selection_unavailable"); return;
        }
        // Resolver fallback is observed too; it must still be this V2 CArmy.
        if (*row.actual_physical_army_full_id_raw != requested) {
          fail("current_physical_army_full_id_differs_from_v2"); return;
        }
        game::ArmyCurrentCombatRolesPhaseOccurrenceV1 current;
        const auto combat = combat_roles_phase_detail::ActiveCombat(b, raw, physical.object, current);
        row.actual_selected_combat_full_id_raw = current.selected_combat_full_id_08_raw_u32;
        row.source_active_combat = current.source_active_combat;
        if (!current.active_combat_inputs_ready || !row.source_active_combat) {
          fail("current_combat_identity_operands_unavailable"); return;
        }
        if (!*row.source_active_combat) {
          fail("physical_army_not_in_active_combat"); return;
        }
        if (!combat || !row.actual_selected_combat_full_id_raw) {
          fail("current_combat_full_id_unavailable"); return;
        }
        const auto attacker = combat_roles_phase_detail::Roster(b, At(combat, 0x20), 0x10, 0x18, 0x1C);
        const auto defender = combat_roles_phase_detail::Roster(b, At(combat, 0x368), 0x10, 0x18, 0x1C);
        if (attacker.references_ready)
          row.attacker_membership_count = static_cast<std::uint32_t>(combat_roles_phase_detail::Matches(attacker, requested).size());
        if (defender.references_ready)
          row.defender_membership_count = static_cast<std::uint32_t>(combat_roles_phase_detail::Matches(defender, requested).size());
        if (!row.attacker_membership_count || !row.defender_membership_count) {
          fail("current_side_roster_membership_unavailable"); return;
        }
        const bool attacker_member = *row.attacker_membership_count > 0;
        const bool defender_member = *row.defender_membership_count > 0;
        row.unique_physical_membership = attacker_member != defender_member;
        if (!*row.unique_physical_membership) {
          fail(attacker_member ? "physical_army_matches_both_current_sides"
                               : "physical_army_matches_neither_current_side"); return;
        }
        // Reuse Side's source-closed local operands, without owner/primary70,
        // manager, phase, threshold, or the whole family's readiness gate.
        row.actual_side_index = attacker_member ? 0U : 1U;
        row.actual_side_role = attacker_member ? "attacker" : "defender";
        const auto side = At(combat, attacker_member ? 0x20 : 0x368);
        const auto parent = Read<const void *>(b.common, side, 0xB8);
        if (parent) row.actual_side_parent_matches_selected_combat = *parent == combat;
        row.actual_side_commander_full_id_raw = Read<std::uint32_t>(b.common, side, 0x74);
        if (row.actual_side_commander_full_id_raw)
          row.actual_side_commander_present = *row.actual_side_commander_full_id_raw != 0xFFFFFFFFU;
        if (!row.actual_side_parent_matches_selected_combat ||
            !*row.actual_side_parent_matches_selected_combat) {
          fail("current_side_parent_not_matched_to_selected_combat"); return;
        }
        if (!row.actual_side_commander_full_id_raw) {
          fail("current_side_commander_full_id_unavailable"); return;
        }
        row.full_id_equal = *row.actual_side_commander_full_id_raw == row.character_id;
        row.status = "available"; row.unavailable_reason.clear(); ++comparisons;
      };
      observe(); output.occurrences.push_back(std::move(row));
    }
    for (const auto &knight : army.knights.members)
      if (knight.character_id != -1) ++ordinal;
  }
  if (comparisons == output.occurrences.size()) output.status = "available";
  else {
    output.status = comparisons ? "partial" : "unavailable";
    output.unavailable_reason = "current_side_commander_identity_comparison_incomplete";
  }
  return output;
}
inline void AttachPhaseCommanderSideIdentity12004(
    const PhaseCommanderSideIdentityBindings12004 &bindings,
    game::CombatSimulationInputsSnapshot &inputs) noexcept {
  if (!bindings.enabled) return;
  try {
    inputs.phase_event_commander_side_identity_v1 = ReadPhaseCommanderSideIdentity12004(bindings, inputs);
  } catch (...) { inputs.phase_event_commander_side_identity_v1.reset(); }
}
} // namespace xar::ck3_12004
