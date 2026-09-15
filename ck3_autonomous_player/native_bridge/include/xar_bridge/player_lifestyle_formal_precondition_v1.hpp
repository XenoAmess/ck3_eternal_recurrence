#pragma once

#include "xar_bridge/player_lifestyle_selection_action_v1.hpp"
#include "xar_bridge/player_lifestyle_snapshot_v1.hpp"

#include <string_view>

namespace xar::ck3_11906 {

enum class PlayerLifestyleFormalPreconditionResultV1 {
  ready,
  source_unavailable,
  frame_mismatch,
  episode_unavailable,
  target_progress_unavailable,
  invalid_source,
};

// LIFE2 and LIFE4 must have been captured independently in one paused
// application-main transaction. A per-frame native:<revision> ID is retained;
// the official driver's episode_run_id is a separate continuity binding.
// This first wire admits the perk path with an observed current lifestyle
// progress row. Absent-focus target progress requires a later exact source
// read and remains unavailable rather than being fabricated as zero.
PlayerLifestyleFormalPreconditionResultV1
BuildPlayerLifestyleFormalPreconditionV1(
    const game::PlayerLifestyleSnapshotV1 &state,
    const game::PlayerLifestyleWindowCandidatesV1 &candidates,
    std::string_view episode_run_id,
    game::PlayerLifestyleSelectionPreconditionV1 &output) noexcept;

std::string_view PlayerLifestyleFormalPreconditionResultKeyV1(
    PlayerLifestyleFormalPreconditionResultV1 result) noexcept;

} // namespace xar::ck3_11906
