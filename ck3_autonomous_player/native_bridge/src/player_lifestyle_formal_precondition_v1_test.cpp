#include "xar_bridge/player_lifestyle_formal_precondition_v1.hpp"

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
  value.proof_epoch = 31;
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
  value.proof_epoch = 31;
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
    Require(ck3::BuildPlayerLifestyleFormalPreconditionV1(
                *state, *candidates, episode, *out) ==
            ck3::PlayerLifestyleFormalPreconditionResultV1::ready);
    Require(out->state.public_revision == 711 &&
            out->state.lifestyle_progress_count == 1 &&
            out->state.lifestyle_progress[0].perk_points == 1 &&
            out->candidates.perks[0].can_select);
    ++candidates->public_revision;
    Require(ck3::BuildPlayerLifestyleFormalPreconditionV1(
                *state, *candidates, episode, *out) ==
            ck3::PlayerLifestyleFormalPreconditionResultV1::frame_mismatch);
    candidates->public_revision = 711;
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
    std::cout << "player_lifestyle_formal_precondition_v1_test: 4/4 GREEN\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
