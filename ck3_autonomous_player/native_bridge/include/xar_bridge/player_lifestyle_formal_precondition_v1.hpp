#pragma once

#include "xar_bridge/player_lifestyle_selection_action_v1.hpp"
#include "xar_bridge/player_lifestyle_snapshot_v1.hpp"
#include "xar_bridge/player_lifestyle_stock_focus_legality_v1.hpp"

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
// This window/stock-perk wire admits the perk path with an observed current
// lifestyle progress row. The absent-focus target row has its own exact stock
// source below; neither path fabricates zero from an absent current row.
PlayerLifestyleFormalPreconditionResultV1
BuildPlayerLifestyleFormalPreconditionV1(
    const game::PlayerLifestyleSnapshotV1 &state,
    const game::PlayerLifestyleWindowCandidatesV1 &candidates,
    std::string_view episode_run_id,
    game::PlayerLifestyleSelectionPreconditionV1 &output) noexcept;

// Build the private fixed stock-focus action from independent LIFE2 state and
// the same-frame exact native focus validator/target-lifestyle getters.
PlayerLifestyleFormalPreconditionResultV1
BuildPlayerLifestyleStockFocusPreconditionV1(
    const game::PlayerLifestyleSnapshotV1 &state,
    const StockFocusLegalityResultV1 &focus,
    std::string_view episode_run_id,
    game::PlayerLifestyleSelectionPreconditionV1 &output) noexcept;

// Independent later paused LIFE2 state, with no dependency on a still-bound
// GUI window. The verifier itself checks a distinct native frame and material
// focus/perk change against the pending ACK.
PlayerLifestyleFormalPreconditionResultV1
BuildPlayerLifestyleFormalReceiptObservationV1(
    const game::PlayerLifestyleSnapshotV1 &state,
    std::string_view episode_run_id,
    game::PlayerLifestyleSelectionStateObservationV1 &output) noexcept;

// Add only LIFE4 rows that passed the final native evaluator to the public
// shape of the private LIFE2 JSON. This does not register a capability.
PlayerLifestyleFormalPreconditionResultV1
AttachPlayerLifestyleFinalCandidatesV1(
    const game::PlayerLifestyleWindowCandidatesV1 &candidates,
    game::PlayerLifestyleSnapshotV1 &state) noexcept;

std::string_view PlayerLifestyleFormalPreconditionResultKeyV1(
    PlayerLifestyleFormalPreconditionResultV1 result) noexcept;

} // namespace xar::ck3_11906
