#pragma once

#include "xar_bridge/player_lifestyle_snapshot_v1.hpp"

namespace xar::ck3_11906 {

// LIFE2's current player state is independent of the LIFE4 window-bound
// final candidate collections. An unavailable candidate set is never an
// empty legal set and does not erase observed focus/XP/point/owned-perk state.
inline bool PlayerLifestyleCurrentStateOnlyReadyV1(
    const game::PlayerLifestyleSnapshotV1 &snapshot) noexcept {
  return snapshot.status == game::PlayerLifestyleSnapshotStatusV1::available &&
         snapshot.readiness.current_focus_ready &&
         snapshot.readiness.lifestyle_progress_ready &&
         snapshot.readiness.owned_perks_ready &&
         snapshot.readiness.same_frame_ready;
}

} // namespace xar::ck3_11906
