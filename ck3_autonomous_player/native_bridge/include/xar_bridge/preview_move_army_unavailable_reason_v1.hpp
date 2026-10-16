#pragma once
#include "xar_bridge/game_contract.hpp"

namespace xar::game {
inline const char *PreviewMoveArmyUnavailableReasonTagV1(
    PreviewMoveArmyUnavailableReason reason) noexcept {
  switch (reason) {
    case PreviewMoveArmyUnavailableReason::unspecified: return "unspecified";
    case PreviewMoveArmyUnavailableReason::military_bindings_incomplete: return "military_bindings_incomplete";
    case PreviewMoveArmyUnavailableReason::military_snapshot_unavailable: return "military_snapshot_unavailable";
    case PreviewMoveArmyUnavailableReason::path_constructor_return_mismatch: return "path_constructor_return_mismatch";
    case PreviewMoveArmyUnavailableReason::worker_pre_snapshot_unavailable: return "worker_pre_snapshot_unavailable";
    case PreviewMoveArmyUnavailableReason::worker_frame_not_ready: return "worker_frame_not_ready";
    case PreviewMoveArmyUnavailableReason::worker_submit_failed: return "worker_submit_failed";
    case PreviewMoveArmyUnavailableReason::worker_wait_failed: return "worker_wait_failed";
    case PreviewMoveArmyUnavailableReason::worker_reclaim_failed: return "worker_reclaim_failed";
    case PreviewMoveArmyUnavailableReason::worker_frame_unstable: return "worker_frame_unstable";
    case PreviewMoveArmyUnavailableReason::worker_exception: return "worker_exception";
  }
  return "unknown_reason_enum";
}
} // namespace xar::game
