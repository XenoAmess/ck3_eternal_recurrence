#include "xar_bridge/m5_war_primary_readback_v1.hpp"

#include <iostream>
#include <string_view>

namespace {

constexpr std::int32_t kActor = 29'829;
constexpr std::int32_t kTarget = 29'097;
constexpr std::int32_t kActorUnit = 0x01000001;
constexpr std::int32_t kActorCArmy = 0x04000001;
constexpr std::int32_t kTargetUnit = 0x02000002;
constexpr std::int32_t kTargetCArmy = 0x05000002;

int Fail(std::string_view message) {
  std::cerr << message << '\n';
  return 1;
}

} // namespace

int main() {
  using namespace xar;
  game::Snapshot snapshot{};
  snapshot.date_raw = 53'178'264;
  snapshot.paused = true;
  snapshot.map_ready = true;
  snapshot.has_played_character = true;
  snapshot.played_character_alive = true;
  snapshot.played_character_id = kActor;
  snapshot.played_character_gold = {0, 100'000};
  snapshot.active_wars.push_back({.war_id = 0x02000009});
  snapshot.player_armies.push_back({
      .army_id = kActorUnit,
      .owner_character_id = kActor,
      .has_current_province = true,
      .current_province_id = 2619,
      .route_province_ids = {2630, 2631},
  });

  std::vector<game::DeclarableWarSnapshot> legal{{
      .target_character_id = kTarget,
      .casus_belli_index = 11,
      .casus_belli_key = "claim_cb",
      .configuration_index = 0,
      .claimant_character_id = kActor,
      .target_title_ids = {2121},
  }};
  auto chosen = legal[0];
  game::WarEntryAssessmentsV1 entry{};
  entry.available = true;
  entry.snapshot_revision = 74;
  entry.date_raw = snapshot.date_raw;
  entry.actor_character_id = kActor;
  entry.requested_target_character_ids = {kTarget};
  entry.assessments = {{.target_character_id = kTarget,
                        .effective_target_character_id = kTarget,
                        .actual_power_ratio_raw = 72'000}};
  entry.readiness.ready = true;

  ck3_11906::PrewarScopeObservationV1 scope{};
  scope.status =
      ck3_11906::ReadPrewarScopeStatusV1::available_primary_scope;
  scope.snapshot_revision = 74;
  scope.date_raw = snapshot.date_raw;
  scope.primary_participants = {
      {kActor, ck3_11906::PrewarSideV1::attacker,
       "declaration_primary_actor"},
      {kTarget, ck3_11906::PrewarSideV1::defender,
       "declaration_effective_target"},
  };
  scope.readiness.exact_build_ready = true;
  scope.readiness.primary_participants_ready = true;
  scope.readiness.primary_raised_armies_ready = true;
  scope.primary_raised_armies = {
      {.army_id = kActorUnit,
       .native_carmy_id = kActorCArmy,
       .owner_character_id = kActor,
       .side = ck3_11906::PrewarSideV1::attacker,
       .has_current_province = true,
       .current_province_id = 2619,
       .route_province_ids = {2630, 2631}},
      {.army_id = kTargetUnit,
       .native_carmy_id = kTargetCArmy,
       .owner_character_id = kTarget,
       .side = ck3_11906::PrewarSideV1::defender},
  };
  ck3_11906::M5PrimaryArmySupplyObservationV1 supply{};
  supply.status = ck3_11906::M5PrimaryArmySupplyStatusV1::available;
  supply.snapshot_revision = 74;
  supply.date_raw = snapshot.date_raw;
  supply.rows = {
      {kActorUnit, kActorCArmy, kActor,
       ck3_11906::PrewarSideV1::attacker, 0, 100'000},
      {kTargetUnit, kTargetCArmy, kTarget,
       ck3_11906::PrewarSideV1::defender, 6'500'000, 100'000},
  };

  ck3_11906::M5WarPrimaryReadbackInputsV1 inputs{
      .native_revision = 74,
      .public_snapshot = &snapshot,
      .public_snapshot_native_revision = 74,
      .native_declarable_wars = &legal,
      .native_declarable_wars_revision = 74,
      .chosen_declaration = &chosen,
      .war_entry = &entry,
      .prewar_primary_scope = &scope,
      .primary_supply = &supply,
  };
  ck3_11906::M5WarPrimaryReadbackV1 output{};
  if (ck3_11906::ReadM5WarPrimaryReadbackV1(inputs, output) !=
          ck3_11906::M5WarPrimaryReadbackStatusV1::
              available_current_primary_slice ||
      output.current_treasury.raw != 0 ||
      output.current_treasury.scale != 100'000 ||
      output.active_war_ids != std::vector<std::int32_t>{0x02000009} ||
      output.actor_current_raised_armies != snapshot.player_armies ||
      output.actor_current_raised_supply.size() != 1 ||
      output.actor_current_raised_supply[0].current_supply_raw != 0 ||
      output.native_power_ratio_raw != 72'000 ||
      output.effective_target_character_id != kTarget) {
    return Fail("same-frame war current slice or legitimate zeros were lost");
  }

  inputs.native_declarable_wars_revision = 75;
  if (ck3_11906::ReadM5WarPrimaryReadbackV1(inputs, output) !=
          ck3_11906::M5WarPrimaryReadbackStatusV1::unavailable ||
      output.unavailable_stage != "missing_or_mismatched_frame_inputs") {
    return Fail("different native legal-list revision was accepted");
  }
  inputs.native_declarable_wars_revision = 74;
  chosen.target_title_ids = {9999};
  if (ck3_11906::ReadM5WarPrimaryReadbackV1(inputs, output) !=
          ck3_11906::M5WarPrimaryReadbackStatusV1::unavailable ||
      output.unavailable_stage != "chosen_declaration_not_native_legal") {
    return Fail("non-native declaration tuple was accepted");
  }
  chosen = legal[0];
  supply.rows[0].native_carmy_id = 0x06000001;
  if (ck3_11906::ReadM5WarPrimaryReadbackV1(inputs, output) !=
          ck3_11906::M5WarPrimaryReadbackStatusV1::unavailable ||
      output.unavailable_stage != "primary_supply_identity_drift") {
    return Fail("stale supply CArmyID was accepted");
  }
  supply.rows[0].native_carmy_id = kActorCArmy;
  snapshot.player_armies[0].route_province_ids = {2630};
  if (ck3_11906::ReadM5WarPrimaryReadbackV1(inputs, output) !=
          ck3_11906::M5WarPrimaryReadbackStatusV1::unavailable ||
      output.unavailable_stage != "public_actor_army_readback_drift") {
    return Fail("public actor route drift was accepted");
  }
  snapshot.player_armies.clear();
  scope.primary_raised_armies.clear();
  supply.rows.clear();
  if (ck3_11906::ReadM5WarPrimaryReadbackV1(inputs, output) !=
          ck3_11906::M5WarPrimaryReadbackStatusV1::
              available_current_primary_slice ||
      !output.actor_current_raised_armies.empty() ||
      !output.actor_current_raised_supply.empty()) {
    return Fail("no currently raised primary army was not available empty");
  }
  snapshot.player_armies.push_back({.army_id = kActorUnit,
                                   .owner_character_id = kActor});
  if (ck3_11906::ReadM5WarPrimaryReadbackV1(inputs, output) !=
          ck3_11906::M5WarPrimaryReadbackStatusV1::unavailable ||
      output.unavailable_stage != "public_actor_army_readback_drift") {
    return Fail("false-empty primary supply ignored an observed actor army");
  }
  std::cout << "m5 war primary current readback GREEN\n";
  return 0;
}
