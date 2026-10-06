#pragma once
#include "xar_bridge/ck3_12003_army_flag31_inputs.hpp"
namespace xar::game {
#include "xar_bridge/army_current_combat_roles_phase_inputs_v1.inc.hpp"
}
namespace xar::ck3_12003 {
struct CurrentArmyCombatRolesPhaseBindings12003 {
  CurrentDailyAssaultRosterAdmissionBindings12003 common{};
  const void *combat_registry_slot = nullptr, *combat_fallback_slot = nullptr;
  const void *expected_secondary_vtable = nullptr, *maneuver_threshold_slot = nullptr;
};
inline CurrentArmyCombatRolesPhaseBindings12003 BindCurrentArmyCombatRolesPhaseInputs12003(
    std::uintptr_t base, std::string_view sha) noexcept {
  CurrentArmyCombatRolesPhaseBindings12003 out{};
  out.common = BindCurrentDailyAssaultRosterAdmission12003(base, sha);
  if (!out.common.enabled) return out;
  out.combat_registry_slot = reinterpret_cast<const void *>(base + 0x5D1DE70);
  out.combat_fallback_slot = reinterpret_cast<const void *>(base + 0x5D1DE18);
  out.expected_secondary_vtable = reinterpret_cast<const void *>(base + 0x477F178);
  out.maneuver_threshold_slot = reinterpret_cast<const void *>(base + 0x5C69BB0);
  return out;
}
namespace combat_roles_phase_detail {
using namespace daily_assault_roster_detail;
using Bindings = CurrentArmyCombatRolesPhaseBindings12003;
template <class T> inline void FinishInputs(T &out, bool complete, const char *reason) {
  out.status = complete ? "available" : "partial";
  out.unavailable_reason = complete ? "" : reason;
}
inline game::ArmyCurrentCombatRawRosterV1 Roster(const Bindings &b, const void *object,
    std::size_t data_offset, std::size_t capacity_offset, std::size_t count_offset) {
  game::ArmyCurrentCombatRawRosterV1 out{};
  const auto data = Read<const void *>(b.common, object, data_offset);
  if (data) out.data_identity = Identity(*data);
  out.capacity_raw_u32 = Read<std::uint32_t>(b.common, object, capacity_offset);
  out.count_raw_i32 = Read<std::int32_t>(b.common, object, count_offset);
  bool complete = data.has_value() && out.capacity_raw_u32.has_value() &&
      out.count_raw_i32.has_value() && *out.count_raw_i32 >= 0;
  if (out.count_raw_i32 && *out.count_raw_i32 >= 0) {
    for (std::int32_t i = 0; i < *out.count_raw_i32; ++i) {
      game::ArmyCurrentCombatRawReferenceV1 row{}; row.native_index = i;
      if (data && *data) row.raw_full_id_u32 = Read<std::uint32_t>(b.common, *data, static_cast<std::size_t>(i) * 4);
      complete = complete && row.raw_full_id_u32.has_value();
      out.references.push_back(std::move(row));
    }
  }
  out.references_ready = complete;
  FinishInputs(out, complete, "combat_roster_inputs_unavailable"); return out;
}
inline game::ArmyCurrentCombatManagerInputsV1 Manager(const Bindings &b) {
  game::ArmyCurrentCombatManagerInputsV1 out{};
  const auto fail = [&](const char *reason) { FinishInputs(out, false, reason); return out; };
  const auto state = Read<const void *>(b.common, b.common.game_state_slot);
  if (!state || !*state) return fail("combat_manager_game_state_unavailable");
  out.game_state_identity = Identity(*state);
  const auto domain = Read<const void *>(b.common, *state, 0xA0);
  if (!domain || !*domain) return fail("combat_manager_domain_unavailable");
  out.domain_identity = Identity(*domain);
  const auto manager = At(*domain, 0x2E9D0); out.manager_identity = Identity(manager);
  const auto vtable = Read<const void *>(b.common, manager, 8);
  if (vtable) {
    out.secondary_vtable_identity = Identity(*vtable);
    out.secondary_vtable_matched = *vtable == b.expected_secondary_vtable;
  }
  // 2AD8000 uses the secondary receiver manager+8: +20/+28/+2C.
  out.roster = Roster(b, manager, 0x28, 0x30, 0x34);
  out.manager_inputs_ready = vtable.has_value() && out.roster.references_ready;
  FinishInputs(out, out.manager_inputs_ready, "combat_manager_inputs_unavailable"); return out;
}
inline std::vector<std::int32_t> Matches(const game::ArmyCurrentCombatRawRosterV1 &roster, std::uint32_t target) {
  std::vector<std::int32_t> out;
  for (const auto &row : roster.references)
    if (row.raw_full_id_u32 && *row.raw_full_id_u32 == target) out.push_back(row.native_index);
  return out;
}
inline game::ArmyCurrentCombatSideInputsV1 Side(const Bindings &b, const void *combat,
    std::size_t offset, std::optional<std::uint32_t> army, std::optional<std::uint32_t> owner) {
  game::ArmyCurrentCombatSideInputsV1 out{}; const auto side = At(combat, offset);
  const auto parent = Read<const void *>(b.common, side, 0xB8);
  if (parent) { out.parent_identity = Identity(*parent); out.parent_matches_selected_combat = *parent == combat; }
  out.armies = Roster(b, side, 0x10, 0x18, 0x1C);
  if (army) out.matching_army_indices = Matches(out.armies, *army);
  out.matching_membership_ready = army.has_value() && out.armies.references_ready;
  out.primary_70_raw_u32 = Read<std::uint32_t>(b.common, side, 0x70);
  out.commander_74_raw_u32 = Read<std::uint32_t>(b.common, side, 0x74);
  if (owner && out.primary_70_raw_u32) out.owner_matches_primary = *owner == *out.primary_70_raw_u32;
  out.side_inputs_ready = parent.has_value() && out.matching_membership_ready &&
      out.primary_70_raw_u32.has_value() && out.commander_74_raw_u32.has_value() && out.owner_matches_primary.has_value();
  FinishInputs(out, out.side_inputs_ready, "combat_side_inputs_unavailable"); return out;
}
inline const void *ActiveCombat(const Bindings &b, const CurrentArmyFlag31Bindings12003 &raw,
    const void *army, game::ArmyCurrentCombatRolesPhaseOccurrenceV1 &out) {
  const auto store = Read<const void *>(b.common, b.combat_registry_slot);
  if (!store) {
    out.combat_resolution.unavailable_reason = "combat_registry_slot_unavailable";
    daily_assault_roster_detail::Finish(out.combat_resolution, false);
    out.unavailable_reason = out.combat_resolution.unavailable_reason; return nullptr;
  }
  if (*store) out.army_128_raw_u32 = Read<std::uint32_t>(b.common, army, 0x128);
  const auto combat = army_flag31_detail::Select(raw, *store, b.combat_fallback_slot,
      out.army_128_raw_u32, 8, "combat", out.combat_resolution);
  if (!combat) { out.unavailable_reason = out.combat_resolution.unavailable_reason; return nullptr; }
  out.selected_combat_magic_0c_raw_u32 = Read<std::uint32_t>(b.common, combat, 0xC);
  if (!out.selected_combat_magic_0c_raw_u32) { out.unavailable_reason = "combat_magic0c_unavailable"; return nullptr; }
  if (*out.selected_combat_magic_0c_raw_u32 != 0x436F6D62U) {
    out.source_active_combat = false; out.active_combat_inputs_ready = true; return combat;
  }
  out.selected_combat_full_id_08_raw_u32 = Read<std::uint32_t>(b.common, combat, 8);
  if (!out.selected_combat_full_id_08_raw_u32) { out.unavailable_reason = "combat_full_id08_unavailable"; return nullptr; }
  out.source_active_combat = *out.selected_combat_full_id_08_raw_u32 != 0xFFFFFFFFU;
  out.active_combat_inputs_ready = true; return combat;
}
inline game::ArmyCurrentCombatRolesPhaseOccurrenceV1 Observe(const Bindings &b, const void *army,
    const game::ArmyPostAdmissionRefreshOccurrenceV1 &source, game::ArmyCurrentCombatManagerInputsV1 &manager,
    bool &manager_captured) {
  game::ArmyCurrentCombatRolesPhaseOccurrenceV1 out{};
  out.native_index = source.native_index; out.raw_full_id_u32 = source.raw_full_id_u32;
  out.original_army_resolution = source.original_army_resolution; out.same_query_army_selection_matched = true;
  CurrentArmyFlag31Bindings12003 raw{}; raw.common = b.common;
  raw.combat_registry_slot = b.combat_registry_slot; raw.combat_fallback_slot = b.combat_fallback_slot;
  const auto combat = ActiveCombat(b, raw, army, out);
  if (!out.active_combat_inputs_ready) {
    const auto reason = out.unavailable_reason; FinishInputs(out, false, reason.c_str()); return out;
  }
  if (!*out.source_active_combat) {
    out.current_combat_roles_phase_inputs_ready = true; FinishInputs(out, true, ""); return out;
  }
  out.actual_army_10_raw_u32 = Read<std::uint32_t>(b.common, army, 0x10);
  game::ArmyFlag31OccurrenceV1 owner{};
  const auto unit = army_flag31_detail::Unit(raw, army, owner);
  const auto character = unit ? army_flag31_detail::Character(raw, unit, owner) : nullptr;
  out.army_124_raw_u32 = owner.army_124_raw_u32; out.unit_owner_174_raw_u32 = owner.unit_owner_174_raw_u32;
  out.unit_resolution = std::move(owner.unit_resolution); out.character_resolution = std::move(owner.character_resolution);
  if (character) out.selected_character_18_raw_u32 = Read<std::uint32_t>(b.common, character, 0x18);
  out.owner_inputs_ready = out.unit_resolution.selected_object_ready && out.character_resolution.selected_object_ready &&
      out.selected_character_18_raw_u32.has_value();
  if (!manager_captured) { manager = Manager(b); manager_captured = true; }
  if (out.selected_combat_full_id_08_raw_u32) out.manager_match_indices = Matches(manager.roster, *out.selected_combat_full_id_08_raw_u32);
  out.combat_manager_membership_ready = manager.manager_inputs_ready && out.selected_combat_full_id_08_raw_u32.has_value();
  out.attacker_side = Side(b, combat, 0x20, out.actual_army_10_raw_u32, out.selected_character_18_raw_u32);
  out.defender_side = Side(b, combat, 0x368, out.actual_army_10_raw_u32, out.selected_character_18_raw_u32);
  out.phase_6b0_raw_i32 = Read<std::int32_t>(b.common, combat, 0x6B0);
  out.day_6b4_raw_i32 = Read<std::int32_t>(b.common, combat, 0x6B4);
  out.forced_winner_700_raw_i32 = Read<std::int32_t>(b.common, combat, 0x700);
  out.finalized_704_raw_u8 = Read<std::uint8_t>(b.common, combat, 0x704);
  out.processing_705_raw_u8 = Read<std::uint8_t>(b.common, combat, 0x705);
  out.phase_inputs_ready = out.phase_6b0_raw_i32.has_value() && out.day_6b4_raw_i32.has_value() &&
      out.forced_winner_700_raw_i32.has_value() && out.finalized_704_raw_u8.has_value() && out.processing_705_raw_u8.has_value();
  out.threshold_required = out.phase_6b0_raw_i32 == std::int32_t{0} && out.forced_winner_700_raw_i32 == std::int32_t{-1};
  if (out.threshold_required) out.maneuver_threshold_raw_i32 = Read<std::int32_t>(b.common, b.maneuver_threshold_slot);
  out.threshold_inputs_ready = !out.threshold_required || out.maneuver_threshold_raw_i32.has_value();
  out.current_combat_roles_phase_inputs_ready = out.actual_army_10_raw_u32.has_value() && out.owner_inputs_ready &&
      out.combat_manager_membership_ready && out.attacker_side.side_inputs_ready && out.defender_side.side_inputs_ready &&
      out.phase_inputs_ready && out.threshold_inputs_ready;
  FinishInputs(out, out.current_combat_roles_phase_inputs_ready, "combat_roles_phase_demanded_inputs_unavailable"); return out;
}
}
inline game::ArmyCurrentCombatRolesPhaseInputsV1 ReadCurrentArmyCombatRolesPhaseInputs12003(
    const CurrentArmyCombatRolesPhaseBindings12003 &b,
    const game::ArmyCurrentPostAdmissionRefreshInputsV1 &same_query_refresh) noexcept {
  using namespace combat_roles_phase_detail;
  game::ArmyCurrentCombatRolesPhaseInputsV1 out{};
  try {
    out.original_army_manager_loaded = same_query_refresh.manager_loaded;
    out.original_army_manager_identity = same_query_refresh.manager_identity;
    out.original_roster = same_query_refresh.original_roster;
    out.raw_roster_references_ready = out.original_roster.references_ready;
    CurrentPostAdmissionRefreshBindings12003 borrowed{}; borrowed.common = b.common;
    std::vector<post_admission_refresh_detail::ResolutionCacheRow> cache; bool manager_captured = false;
    for (const auto &raw : out.original_roster.occurrences) {
      game::ArmyCurrentCombatRolesPhaseOccurrenceV1 row{};
      row.native_index = raw.native_index; row.raw_full_id_u32 = raw.raw_full_id_u32;
      const auto source = std::find_if(same_query_refresh.occurrences.begin(), same_query_refresh.occurrences.end(),
          [&](const auto &p) { return p.native_index == raw.native_index && p.raw_full_id_u32 == raw.raw_full_id_u32; });
      if (source != same_query_refresh.occurrences.end()) row.original_army_resolution = source->original_army_resolution;
      if (!b.common.enabled) FinishInputs(row, false, "combat_roles_phase_unbound");
      else {
        const auto selected = post_admission_refresh_detail::Selected(borrowed, raw.raw_full_id_u32, true, cache);
        if (source == same_query_refresh.occurrences.end() ||
            !post_admission_refresh_detail::SameSelected(source->original_army_resolution, selected, raw.raw_full_id_u32))
          FinishInputs(row, false, "combat_same_query_army_selection_unavailable");
        else row = Observe(b, selected.object, *source, out.combat_manager, manager_captured);
      }
      out.occurrences.push_back(std::move(row));
    }
    const bool covered = b.common.enabled && post_admission_refresh_detail::Covered(out.original_roster, out.occurrences.size());
    out.original_army_selections_ready = covered && std::all_of(out.occurrences.begin(), out.occurrences.end(),
        [](const auto &p) { return p.same_query_army_selection_matched; });
    out.current_combat_roles_phase_inputs_ready = out.original_army_selections_ready &&
        std::all_of(out.occurrences.begin(), out.occurrences.end(), [](const auto &p) { return p.current_combat_roles_phase_inputs_ready; });
    FinishInputs(out, out.current_combat_roles_phase_inputs_ready, "combat_roles_phase_current_inputs_incomplete");
  } catch (...) { FinishInputs(out, false, "combat_roles_phase_collection_unavailable"); }
  return out;
}
}
