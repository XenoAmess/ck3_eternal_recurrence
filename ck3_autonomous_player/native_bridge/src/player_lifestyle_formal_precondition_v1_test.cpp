#include "xar_bridge/player_lifestyle_formal_precondition_v1.hpp"
#include "xar_bridge/player_lifestyle_formal_wire_v1.hpp"

#include <algorithm>
#include <array>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string_view>

namespace ck3 = xar::ck3_11906;
namespace game = xar::game;

namespace {

template <std::size_t N>
void Fixed(std::array<char, N> &out, std::string_view value) {
  if (value.size() >= N) throw std::runtime_error("fixture string too long");
  std::copy(value.begin(), value.end(), out.begin());
}

void Require(bool value) {
  if (!value) throw std::runtime_error("formal precondition check failed");
}

void FillState(game::PlayerLifestyleSnapshotV1 &value) {
  value = {};
  value.status = game::PlayerLifestyleSnapshotStatusV1::available;
  Fixed(value.snapshot_id, "native:711");
  value.public_revision = 711;
  value.native_revision = 711;
  value.proof_epoch = 711;
  value.date_raw = 53178312;
  value.player_character_id = 29829;
  value.readiness.current_focus_ready = true;
  value.readiness.owned_perks_ready = true;
  value.readiness.lifestyle_progress_ready = true;
  value.readiness.same_frame_ready = true;
  value.state.current_focus_presence =
      game::PlayerLifestyleFocusPresenceV1::present;
  Require(ck3::AssignPlayerLifestyleStableKeyV1(
      "stewardship_wealth_focus", value.state.current_focus_key));
  value.state.current_lifestyle_progress_present = true;
  auto &progress = value.state.current_lifestyle_progress;
  Require(ck3::AssignPlayerLifestyleStableKeyV1(
      "stewardship_lifestyle", progress.lifestyle_key));
  progress.xp_total_raw = 150000;
  progress.unspent_perk_points = 1;
}

void FillCandidates(game::PlayerLifestyleWindowCandidatesV1 &value) {
  value = {};
  value.status = game::PlayerLifestyleWindowCandidatesStatusV1::available;
  Fixed(value.snapshot_id, "native:711");
  value.public_revision = 711;
  value.native_revision = 711;
  value.proof_epoch = 711;
  value.date_raw = 53178312;
  value.player_character_id = 29829;
  value.readiness.final_legality_ready = true;
  value.readiness.same_frame_ready = true;
  value.focus_status =
      game::PlayerLifestyleWindowCollectionStatusV1::known_empty;
  value.perk_status =
      game::PlayerLifestyleWindowCollectionStatusV1::available;
  value.perk_count = 1;
  Require(ck3::AssignPlayerLifestyleWindowStableKeyV1(
      "cutting_corners_perk", value.perks[0].key));
  Require(ck3::AssignPlayerLifestyleWindowStableKeyV1(
      "stewardship_lifestyle", value.perks[0].lifestyle_key));
  value.perks[0].can_select = true;
}

} // namespace

int main() {
  try {
    auto state = std::make_unique<game::PlayerLifestyleSnapshotV1>();
    auto candidates =
        std::make_unique<game::PlayerLifestyleWindowCandidatesV1>();
    auto out =
        std::make_unique<game::PlayerLifestyleSelectionPreconditionV1>();
    FillState(*state);
    FillCandidates(*candidates);
    const auto episode = "native-29829-ee172aa720db";
    const std::uint64_t query_pump = 31;
    const std::uint64_t action_pump = 32;
    Require(action_pump > query_pump);
    Require(ck3::PlayerLifestyleFormalFrameProofEpochV1(711, query_pump) ==
            ck3::PlayerLifestyleFormalFrameProofEpochV1(711, action_pump));
    Require(ck3::PlayerLifestyleFormalStateFailureV1(
                game::PlayerLifestyleSnapshotFailureV1::invalid_request) ==
            "native_lifestyle_current_state_invalid_request");
    Require(ck3::PlayerLifestyleFormalFinalCandidatesFailureV1(
                game::PlayerLifestyleWindowCandidatesFailureV1::
                    invalid_request) ==
            "native_lifestyle_final_candidates_invalid_request");
    Require(ck3::PlayerLifestyleFormalFinalCandidatesFailureV1(
                game::PlayerLifestyleWindowCandidatesFailureV1::
                    owner_path_unavailable) ==
            "native_lifestyle_final_candidates_owner_path_unavailable");
    Require(ck3::PlayerLifestyleFormalFrameProofEpochV1(711, action_pump) ==
            711);
    game::PlayerLifestyleSelectionActionAckV1 safe_reject{};
    safe_reject.failure_class =
        game::PlayerLifestyleSelectionActionFailureClassV1::final_legality;
    Require(ck3::PlayerLifestyleAckProvesNoNativeSubmitV1(safe_reject));
    safe_reject.failure_class = game::
        PlayerLifestyleSelectionActionFailureClassV1::
            native_command_dispatch;
    Require(!ck3::PlayerLifestyleAckProvesNoNativeSubmitV1(safe_reject));
    safe_reject.status = game::
        PlayerLifestyleSelectionActionAckStatusV1::
            submitted_verification_pending;
    Require(!ck3::PlayerLifestyleAckProvesNoNativeSubmitV1(safe_reject));
    Require(ck3::BuildPlayerLifestyleFormalPreconditionV1(
                *state, *candidates, episode, *out) ==
            ck3::PlayerLifestyleFormalPreconditionResultV1::ready);
    Require(out->state.public_revision == 711 &&
            out->state.lifestyle_progress_count == 1 &&
            out->state.lifestyle_progress[0].perk_points == 1 &&
            out->candidates.perks[0].can_select);
    Require(ck3::AttachPlayerLifestyleFinalCandidatesV1(
                *candidates, *state) ==
            ck3::PlayerLifestyleFormalPreconditionResultV1::ready);
    Require(state->state.legal_perk_candidate_count == 1 &&
            state->readiness.legal_perk_candidates_ready);
    ++candidates->public_revision;
    Require(ck3::PlayerLifestyleFormalFrameProofEpochV1(
                candidates->public_revision, action_pump) !=
            state->proof_epoch);
    Require(ck3::BuildPlayerLifestyleFormalPreconditionV1(
                *state, *candidates, episode, *out) ==
            ck3::PlayerLifestyleFormalPreconditionResultV1::frame_mismatch);
    candidates->public_revision = 711;
    Fixed(state->snapshot_id, "native:712");
    state->public_revision = 712;
    state->native_revision = 712;
    state->proof_epoch = 712;
    game::PlayerLifestyleSelectionStateObservationV1 later{};
    Require(ck3::BuildPlayerLifestyleFormalReceiptObservationV1(
                *state, episode, later) ==
            ck3::PlayerLifestyleFormalPreconditionResultV1::ready);
    Require(later.public_revision == 712 &&
            later.episode_run_id[0] == 'n');
    Fixed(state->snapshot_id, "native:711");
    state->public_revision = 711;
    state->native_revision = 711;
    state->proof_epoch = 711;
    state->state.current_focus_presence =
        game::PlayerLifestyleFocusPresenceV1::absent;
    state->state.current_lifestyle_progress_present = false;
    Require(ck3::BuildPlayerLifestyleFormalPreconditionV1(
                *state, *candidates, episode, *out) ==
            ck3::PlayerLifestyleFormalPreconditionResultV1::
                target_progress_unavailable);
    Require(ck3::BuildPlayerLifestyleFormalPreconditionV1(
                *state, *candidates, "", *out) ==
            ck3::PlayerLifestyleFormalPreconditionResultV1::
                episode_unavailable);
    std::cout << "player_lifestyle_formal_precondition_v1_test: 7/7 GREEN\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
