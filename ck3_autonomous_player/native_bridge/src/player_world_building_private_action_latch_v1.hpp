#pragma once

#include "player_world_building_action_candidate_v1.hpp"

#include <algorithm>

namespace xar::ck3_11906 {

// Private Bridge state only. The already derived candidate binds the current
// unresolved native submit to independent material; it is not another ledger.
struct PlayerWorldBuildingPrivateActionLatchV1 final {
  bool may_have_submitted = false;
  PlayerWorldBuildingActionCandidateV1 submitted{};
};

inline void BeginPlayerWorldBuildingPrivateActionV1(
    PlayerWorldBuildingPrivateActionLatchV1 &latch) noexcept {
  latch = {};
  latch.may_have_submitted = true;
}

inline void RememberPlayerWorldBuildingPrivateActionV1(
    PlayerWorldBuildingPrivateActionLatchV1 &latch,
    const PlayerWorldBuildingActionCandidateV1 &candidate,
    const std::uint32_t materialize_calls,
    const std::uint32_t receiver_calls) noexcept {
  if (!candidate.ready || (materialize_calls == 0 && receiver_calls == 0)) {
    latch = {};
    return;
  }
  latch.submitted = candidate;
}

inline bool ObservePlayerWorldBuildingPrivateActionMaterialV1(
    PlayerWorldBuildingPrivateActionLatchV1 &latch,
    const PlayerWorldBuildingSourceResultV1 &fresh,
    const std::uint64_t proof_epoch) noexcept {
  const auto &candidate = latch.submitted;
  if (!latch.may_have_submitted || !candidate.ready ||
      !fresh.source_available || fresh.failure != PlayerWorldBuildingFailureV1::none ||
      proof_epoch <= candidate.proof_epoch ||
      fresh.snapshot_revision < candidate.snapshot_revision ||
      fresh.date_raw < candidate.date_raw ||
      fresh.player_character_id != candidate.actor_character_id) {
    return false;
  }
  const bool active = ObservePlayerWorldBuildingMaterialResultV1(
      candidate, fresh, proof_epoch);
  const bool completed = fresh.completed_buildings_observed && std::any_of(
      fresh.completed_buildings.begin(), fresh.completed_buildings.end(),
      [&candidate](const auto &row) {
        return row.barony_title_id == candidate.barony_title_id &&
               row.province_id == candidate.province_id &&
               row.building_type_id == candidate.building_type_id &&
               row.slot_index == candidate.slot_index;
      });
  if (!active && !completed) return false;
  latch.may_have_submitted = false;
  return true;
}

} // namespace xar::ck3_11906
