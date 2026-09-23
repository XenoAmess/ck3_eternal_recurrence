#pragma once

#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "xar_bridge/player_lifestyle_formal_precondition_v1.hpp"
#include "xar_bridge/player_lifestyle_current_state_only_v1.hpp"
#include "xar_bridge/player_lifestyle_selection_native_adapter_v1.hpp"
#include "xar_bridge/player_lifestyle_stock_focus_legality_v1.hpp"
#include "xar_bridge/player_lifestyle_stock_perk_legality_v1.hpp"

#include <memory>
#include <string>
#include <string_view>

namespace xar::ck3_11906 {

enum class PlayerLifestyleFormalWireModeV1 {
  query,
  query_state_only,
  query_focus_only,
  query_professional_workforce_only,
  submit_perk,
  submit_focus,
  verify_receipt,
};

inline constexpr std::string_view kPlayerLifestyleFormalPrivateQueryStepV1 =
    "private-query-player-lifestyle-formal-v1";
inline constexpr std::string_view
    kPlayerLifestyleFormalPrivateCurrentStateStepV1 =
        "private-query-player-lifestyle-current-state-v1";
inline constexpr std::string_view
    kPlayerLifestyleFormalPrivateStockFocusStepV1 =
        "private-query-player-lifestyle-stock-focus-v1";
inline constexpr std::string_view
    kPlayerLifestyleFormalPrivateProfessionalWorkforceStepV1 =
        "private-query-player-lifestyle-professional-workforce-v1";
inline constexpr std::string_view kPlayerLifestyleFormalPrivateSubmitStepV1 =
    "private-select-player-lifestyle-perk-v1";
inline constexpr std::string_view kPlayerLifestyleFormalPrivateSubmitFocusStepV1 =
    "private-select-player-lifestyle-stock-focus-v1";
inline constexpr std::string_view kPlayerLifestyleFormalPrivateReceiptStepV1 =
    "private-query-player-lifestyle-receipt-v1";

inline bool PlayerLifestylePolicyStockPerkTargetAdmittedV1(
    std::string_view target) noexcept {
  return target == kStockPerkLegalityTargetV1 ||
         target == kStockPerkLegalityFollowupTargetV1 ||
         target == kStockPerkLegalityNextTargetV1;
}

// The domain parent chain is cutting_corners -> professional_workforce ->
// centralization. A windowless formal query reads one exact native target for
// the observed ownership state; submit recomputes it on the same paused frame.
inline std::string_view PlayerLifestylePolicyStockPerkTargetV1(
    const game::PlayerLifestyleSnapshotV1 &snapshot) noexcept {
  if (snapshot.status != game::PlayerLifestyleSnapshotStatusV1::available ||
      !snapshot.readiness.owned_perks_ready ||
      snapshot.state.owned_perk_count >
          game::kPlayerLifestyleWindowMaximumPerksV1) {
    return {};
  }
  bool cutting_corners_owned = false;
  bool professional_workforce_owned = false;
  for (std::uint32_t index = 0;
       index < snapshot.state.owned_perk_count; ++index) {
    const auto key = PlayerLifestyleStableKeyViewV1(
        snapshot.state.owned_perk_keys[index]);
    if (key == kStockPerkLegalityFollowupTargetV1)
      professional_workforce_owned = true;
    if (key == kStockPerkLegalityTargetV1) cutting_corners_owned = true;
  }
  if (professional_workforce_owned) return kStockPerkLegalityNextTargetV1;
  return cutting_corners_owned ? kStockPerkLegalityFollowupTargetV1
                               : kStockPerkLegalityTargetV1;
}

// Proof belongs to the published native frame, not the pump that happens to
// execute a read/query/action. This is the bridge's observed state revision.
inline std::uint64_t PlayerLifestyleFormalFrameProofEpochV1(
    std::uint64_t published_revision,
    std::uint64_t verified_main_pump_epoch) noexcept {
  return published_revision != 0 && verified_main_pump_epoch != 0
             ? published_revision
             : 0;
}

// The worker marks an action as possibly submitted when its executor is
// queued. Only a completed typed ACK from an earlier-than-dispatch LIFE6
// failure proves that no native submit happened; dispatch failure stays
// unknown and blocks retry until actual state is queried.
inline bool PlayerLifestyleAckProvesNoNativeSubmitV1(
    const game::PlayerLifestyleSelectionActionAckV1 &ack) noexcept {
  if (ack.status != game::PlayerLifestyleSelectionActionAckStatusV1::
                        rejected_before_submit ||
      ack.verification_pending) {
    return false;
  }
  using Failure = game::PlayerLifestyleSelectionActionFailureClassV1;
  switch (ack.failure_class) {
  case Failure::request_contract:
  case Failure::exact_build_binding:
  case Failure::snapshot_binding:
  case Failure::final_legality:
  case Failure::state_observation:
    return true;
  case Failure::none:
  case Failure::native_command_dispatch:
    return false;
  }
  return false;
}

// A typed submit can change a perk/focus without changing the coarse map
// snapshot. Publish a new real paused snapshot for the independent receipt;
// the ACK alone still does not prove that the selection was applied.
inline bool PlayerLifestyleAckNeedsPostSubmitSnapshotV1(
    const game::PlayerLifestyleSelectionActionAckV1 &ack,
    std::string_view request_id) noexcept {
  return !request_id.empty() && ack.request_id == request_id &&
         ack.status == game::PlayerLifestyleSelectionActionAckStatusV1::
                           submitted_verification_pending &&
         ack.verification_pending;
}

inline std::string PlayerLifestyleFormalStateFailureV1(
    game::PlayerLifestyleSnapshotFailureV1 failure) {
  std::string result{"native_lifestyle_current_state_"};
  result += PlayerLifestyleSnapshotFailureKeyV1(failure);
  return result;
}

inline std::string PlayerLifestyleFormalFinalCandidatesFailureV1(
    game::PlayerLifestyleWindowCandidatesFailureV1 failure) {
  std::string result{"native_lifestyle_final_candidates_"};
  result += PlayerLifestyleWindowCandidatesFailureKeyV1(failure);
  return result;
}

// One controlled candidate transaction. The bridge worker owns this object
// until the fixed application-main mailbox ticket is terminal and reclaimed.
// No public GameAdapter step or capability advertisement is installed.
struct PlayerLifestyleFormalWireContextV1 {
  Bindings bindings{};
  game::Snapshot expected_snapshot{};
  std::uint64_t expected_revision = 0;
  std::uintptr_t module_base = 0;
  std::string episode_run_id;
  std::string snapshot_id;
  std::string action_request_id;
  std::string action_target_key;
  PlayerLifestyleFormalWireModeV1 mode =
      PlayerLifestyleFormalWireModeV1::query;
  MainThreadExecutionStampV1 stamp{};
  PlayerLifestyleWindowSourceAdapterStateV1 source_state{};
  PlayerLifestyleWindowSourceAdapterEnvironmentV1 source_environment{};
  PlayerLifestyleWindowSourceAdapterAccessV1 source_access{};
  PlayerLifestyleSelectionNativeAdapterContextV1 native_submit{};
  StockPerkLegalityResultV1 stock_perk_result{};
  StockFocusLegalityResultV1 stock_focus_result{};
  game::PlayerLifestyleSelectionActionRequestV1 action_request{};
  game::PlayerLifestyleSelectionActionAckV1 pending_ack{};
  game::PlayerLifestyleSelectionActionReceiptV1 receipt{};
  std::unique_ptr<game::PlayerLifestyleSnapshotV1> snapshot;
  std::unique_ptr<game::PlayerLifestyleWindowCandidatesV1> candidates;
  std::unique_ptr<game::PlayerLifestyleSelectionPreconditionV1> precondition;
  PlayerLifestyleFormalPreconditionResultV1 precondition_result =
      PlayerLifestyleFormalPreconditionResultV1::source_unavailable;
  std::string failure;
  bool completed = false;
};

bool InitializePlayerLifestyleFormalWireContextV1(
    PlayerLifestyleFormalWireContextV1 &context,
    const Bindings &bindings,
    const game::Snapshot &expected_snapshot,
    std::uint64_t expected_revision,
    std::string_view episode_run_id,
    PlayerLifestyleFormalWireModeV1 mode) noexcept;

// Narrow fixed slot43 executor. It reads LIFE2 with final perk/stock-focus
// legality and, for a separately admitted request, invokes LIFE6/LIFE7 once.
// Its ACK remains
// pending until a later independently captured paused receipt.
bool ExecutePlayerLifestyleFormalWireMailboxV1(
    void *opaque,
    const MainThreadExecutionStampV1 &stamp) noexcept;

} // namespace xar::ck3_11906
