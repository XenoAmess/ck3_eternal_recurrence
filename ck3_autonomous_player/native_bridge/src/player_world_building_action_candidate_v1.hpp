#pragma once

#include "player_world_building_definition_source_v1.hpp"

#include <array>
#include <cstdint>

namespace xar::ck3_11906 {

// Private standard-feudal action candidate from a real paused stock-player
// source. This selector does not advertise construction or issue a command.
enum class PlayerWorldBuildingActionFailureV1 : std::uint8_t {
  none = 0,
  source_unavailable,
  frame_binding,
  resource_unknown,
  economic_value_unknown,
  active_construction,
  no_budget_safe_candidate,
};

struct PlayerWorldBuildingActionCandidateV1 final {
  bool ready = false;
  PlayerWorldBuildingActionFailureV1 failure =
      PlayerWorldBuildingActionFailureV1::source_unavailable;
  std::uint64_t snapshot_revision = 0;
  std::uint64_t proof_epoch = 0;
  std::int32_t date_raw = 0;
  std::int32_t actor_character_id = -1;
  std::int32_t barony_title_id = -1;
  std::int32_t province_id = -1;
  std::int32_t building_type_id = -1;
  std::int32_t slot_index = -1;
  std::int64_t player_gold_before_raw = 0;
  std::int64_t stock_gold_cost_raw = 0;
  std::int64_t gold_reserve_after_raw = 0;
  std::array<std::int64_t, 10> stock_cost_raw_native{};
};

[[nodiscard]] PlayerWorldBuildingActionCandidateV1
SelectPlayerWorldBuildingActionCandidateV1(
    const PlayerWorldBuildingSourceResultV1 &source,
    std::uint64_t proof_epoch, std::int64_t minimum_gold_reserve_raw) noexcept;

// Fresh stock Province+0x620 material state, independently read after a
// native receiver ACK. The newer application-main proof epoch is supplied by
// the paused mailbox; a same-frame cached tuple is insufficient.
[[nodiscard]] bool ObservePlayerWorldBuildingMaterialResultV1(
    const PlayerWorldBuildingActionCandidateV1 &submitted,
    const PlayerWorldBuildingSourceResultV1 &fresh,
    std::uint64_t fresh_proof_epoch) noexcept;

} // namespace xar::ck3_11906
