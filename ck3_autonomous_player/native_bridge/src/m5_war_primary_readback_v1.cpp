#include "xar_bridge/m5_war_primary_readback_v1.hpp"

#include <algorithm>

namespace xar::ck3_11906 {
namespace {

M5WarPrimaryReadbackStatusV1 Unavailable(M5WarPrimaryReadbackV1 &output,
                                        const char *stage) noexcept {
  output.unavailable_stage = stage;
  return output.status;
}

bool MatchesPublicActorArmy(const game::Snapshot &snapshot,
                            const PrewarRaisedArmyV1 &primary) noexcept {
  const auto found = std::find_if(
      snapshot.player_armies.begin(), snapshot.player_armies.end(),
      [&](const game::ArmySnapshot &army) {
        return army.army_id == primary.army_id;
      });
  if (found == snapshot.player_armies.end() ||
      std::count_if(snapshot.player_armies.begin(), snapshot.player_armies.end(),
                    [&](const game::ArmySnapshot &army) {
                      return army.army_id == primary.army_id;
                    }) != 1) {
    return false;
  }
  return found->owner_character_id == primary.owner_character_id &&
         found->has_current_province == primary.has_current_province &&
         (!primary.has_current_province ||
          found->current_province_id == primary.current_province_id) &&
         found->route_province_ids == primary.route_province_ids;
}

} // namespace

M5WarPrimaryReadbackStatusV1 ReadM5WarPrimaryReadbackV1(
    const M5WarPrimaryReadbackInputsV1 &inputs,
    M5WarPrimaryReadbackV1 &output) noexcept {
  output = {};
  if (inputs.public_snapshot == nullptr ||
      inputs.native_declarable_wars == nullptr ||
      inputs.chosen_declaration == nullptr || inputs.war_entry == nullptr ||
      inputs.prewar_primary_scope == nullptr || inputs.primary_supply == nullptr ||
      inputs.native_revision == 0 ||
      inputs.public_snapshot_native_revision != inputs.native_revision ||
      inputs.native_declarable_wars_revision != inputs.native_revision) {
    return Unavailable(output, "missing_or_mismatched_frame_inputs");
  }
  const auto &snapshot = *inputs.public_snapshot;
  const auto &declaration = *inputs.chosen_declaration;
  const auto &entry = *inputs.war_entry;
  const auto &scope = *inputs.prewar_primary_scope;
  const auto &supply = *inputs.primary_supply;
  if (!snapshot.paused || !snapshot.map_ready ||
      !snapshot.has_played_character || !snapshot.played_character_alive ||
      snapshot.played_character_id <= 0 ||
      snapshot.played_character_gold.scale <= 0) {
    return Unavailable(output, "public_snapshot_not_ready");
  }
  if (std::count(inputs.native_declarable_wars->begin(),
                 inputs.native_declarable_wars->end(), declaration) != 1 ||
      declaration.target_character_id <= 0 ||
      declaration.casus_belli_index < 0 ||
      declaration.casus_belli_key.empty()) {
    return Unavailable(output, "chosen_declaration_not_native_legal");
  }
  if (!entry.available || !entry.readiness.ready ||
      entry.snapshot_revision != inputs.native_revision ||
      entry.date_raw != snapshot.date_raw ||
      entry.actor_character_id != snapshot.played_character_id ||
      entry.requested_target_character_ids.size() != 1 ||
      entry.requested_target_character_ids[0] !=
          declaration.target_character_id ||
      entry.assessments.size() != 1 ||
      entry.assessments[0].target_character_id !=
          declaration.target_character_id ||
      entry.assessments[0].effective_target_character_id <= 0) {
    return Unavailable(output, "war_entry_not_same_native_target");
  }
  const auto effective_target =
      entry.assessments[0].effective_target_character_id;
  if (scope.status != ReadPrewarScopeStatusV1::available_primary_scope ||
      !scope.readiness.exact_build_ready ||
      !scope.readiness.primary_participants_ready ||
      !scope.readiness.primary_raised_armies_ready ||
      scope.snapshot_revision != inputs.native_revision ||
      scope.date_raw != snapshot.date_raw ||
      scope.primary_participants.size() != 2 ||
      scope.primary_participants[0].side != PrewarSideV1::attacker ||
      scope.primary_participants[0].character_id !=
          snapshot.played_character_id ||
      scope.primary_participants[1].side != PrewarSideV1::defender ||
      scope.primary_participants[1].character_id != effective_target) {
    return Unavailable(output, "prewar_primary_scope_not_same_target");
  }
  if (supply.status != M5PrimaryArmySupplyStatusV1::available ||
      supply.snapshot_revision != inputs.native_revision ||
      supply.date_raw != snapshot.date_raw ||
      supply.rows.size() != scope.primary_raised_armies.size()) {
    return Unavailable(output, "primary_supply_not_same_scope");
  }
  for (std::size_t index = 0; index < supply.rows.size(); ++index) {
    const auto &raised = scope.primary_raised_armies[index];
    const auto &supply_row = supply.rows[index];
    if (supply_row.army_id != raised.army_id ||
        supply_row.native_carmy_id != raised.native_carmy_id ||
        supply_row.owner_character_id != raised.owner_character_id ||
        supply_row.side != raised.side ||
        supply_row.current_supply_scale != 100'000) {
      return Unavailable(output, "primary_supply_identity_drift");
    }
    if (raised.side == PrewarSideV1::attacker) {
      if (raised.owner_character_id != snapshot.played_character_id ||
          !MatchesPublicActorArmy(snapshot, raised)) {
        return Unavailable(output, "public_actor_army_readback_drift");
      }
    }
  }
  for (const auto &public_army : snapshot.player_armies) {
    if (public_army.owner_character_id != snapshot.played_character_id) {
      continue;
    }
    if (std::count_if(
            scope.primary_raised_armies.begin(),
            scope.primary_raised_armies.end(),
            [&](const PrewarRaisedArmyV1 &raised) {
              return raised.side == PrewarSideV1::attacker &&
                     raised.army_id == public_army.army_id;
            }) != 1) {
      return Unavailable(output, "public_actor_army_readback_drift");
    }
  }
  output.native_revision = inputs.native_revision;
  output.date_raw = snapshot.date_raw;
  output.actor_character_id = snapshot.played_character_id;
  output.declaration = declaration;
  output.effective_target_character_id = effective_target;
  output.native_power_ratio_raw =
      entry.assessments[0].actual_power_ratio_raw;
  output.current_treasury = snapshot.played_character_gold;
  for (const auto &war : snapshot.active_wars) {
    output.active_war_ids.push_back(war.war_id);
  }
  for (const auto &row : supply.rows) {
    if (row.side == PrewarSideV1::attacker) {
      output.actor_current_raised_supply.push_back(row);
    }
  }
  output.status =
      M5WarPrimaryReadbackStatusV1::available_current_primary_slice;
  return output.status;
}

} // namespace xar::ck3_11906
