#pragma once

#include "xar_bridge/game_contract.hpp"
#include "xar_bridge/m5_primary_army_supply_v1.hpp"
#include "xar_bridge/war_entry_assessments_v1.hpp"

#include <cstdint>
#include <string>
#include <vector>

namespace xar::ck3_11906 {

// A read-only join of already-existing exact-build observations for one
// native-legal declaration. No native helper, command or world write occurs.
// The caller must capture each input on the same published paused revision.
struct M5WarPrimaryReadbackInputsV1 {
  std::uint64_t native_revision = 0;
  const game::Snapshot *public_snapshot = nullptr;
  std::uint64_t public_snapshot_native_revision = 0;
  const std::vector<game::DeclarableWarSnapshot> *native_declarable_wars =
      nullptr;
  std::uint64_t native_declarable_wars_revision = 0;
  const game::DeclarableWarSnapshot *chosen_declaration = nullptr;
  const game::WarEntryAssessmentsV1 *war_entry = nullptr;
  const PrewarScopeObservationV1 *prewar_primary_scope = nullptr;
  const M5PrimaryArmySupplyObservationV1 *primary_supply = nullptr;
};

enum class M5WarPrimaryReadbackStatusV1 : std::uint8_t {
  available_current_primary_slice = 0,
  unavailable = 1,
};

struct M5WarPrimaryReadbackV1 {
  M5WarPrimaryReadbackStatusV1 status =
      M5WarPrimaryReadbackStatusV1::unavailable;
  std::string unavailable_stage;
  std::uint64_t native_revision = 0;
  std::int32_t date_raw = 0;
  std::int32_t actor_character_id = -1;
  game::DeclarableWarSnapshot declaration;
  std::int32_t effective_target_character_id = -1;
  std::int64_t native_power_ratio_raw = 0;
  game::FixedPointValue current_treasury;
  std::vector<std::int32_t> active_war_ids;
  std::vector<game::ArmySnapshot> actor_current_raised_armies;
  std::vector<M5PrimaryArmySupplyRowV1> actor_current_raised_supply;
};

// Only the actor's currently raised CUnit rows are independently read back
// against public player_armies. An empty actor_current_raised_supply vector is
// a positive observation of no currently raised actor primary armies, not a
// future supply or campaign-cost forecast.
M5WarPrimaryReadbackStatusV1 ReadM5WarPrimaryReadbackV1(
    const M5WarPrimaryReadbackInputsV1 &inputs,
    M5WarPrimaryReadbackV1 &output) noexcept;

} // namespace xar::ck3_11906
