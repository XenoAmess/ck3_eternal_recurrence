#include "xar_bridge/player_lifestyle_formal_precondition_v1.hpp"

#include <algorithm>
#include <limits>

namespace xar::ck3_11906 {
namespace {

using Result = PlayerLifestyleFormalPreconditionResultV1;

template <std::size_t N>
std::string_view Fixed(const std::array<char, N> &value) noexcept {
  const auto end = std::find(value.begin(), value.end(), '\0');
  return end == value.end()
             ? std::string_view{}
             : std::string_view(value.data(),
                                static_cast<std::size_t>(end - value.begin()));
}

bool ConvertKey(const game::PlayerLifestyleStableKeyV1 &source,
                game::PlayerLifestyleWindowStableKeyV1 &target) noexcept {
  return AssignPlayerLifestyleWindowStableKeyV1(
      PlayerLifestyleStableKeyViewV1(source), target);
}

bool SameFrame(const game::PlayerLifestyleSnapshotV1 &state,
               const game::PlayerLifestyleWindowCandidatesV1 &candidates) noexcept {
  return Fixed(state.snapshot_id) == Fixed(candidates.snapshot_id) &&
         !Fixed(state.snapshot_id).empty() &&
         state.public_revision == candidates.public_revision &&
         state.native_revision == candidates.native_revision &&
         state.proof_epoch == candidates.proof_epoch &&
         state.date_raw == candidates.date_raw &&
         state.player_character_id >= 0 &&
         static_cast<std::uint32_t>(state.player_character_id) ==
             candidates.player_character_id;
}

} // namespace

Result BuildPlayerLifestyleFormalPreconditionV1(
    const game::PlayerLifestyleSnapshotV1 &state,
    const game::PlayerLifestyleWindowCandidatesV1 &candidates,
    std::string_view episode_run_id,
    game::PlayerLifestyleSelectionPreconditionV1 &output) noexcept {
  output = {};
  if (state.status != game::PlayerLifestyleSnapshotStatusV1::available ||
      candidates.status !=
          game::PlayerLifestyleWindowCandidatesStatusV1::available ||
      !state.readiness.current_focus_ready ||
      !state.readiness.owned_perks_ready ||
      !state.readiness.same_frame_ready ||
      !candidates.readiness.final_legality_ready ||
      !candidates.readiness.same_frame_ready ||
      candidates.focus_status ==
          game::PlayerLifestyleWindowCollectionStatusV1::unavailable ||
      candidates.perk_status ==
          game::PlayerLifestyleWindowCollectionStatusV1::unavailable) {
    return Result::source_unavailable;
  }
  if (!SameFrame(state, candidates) || state.public_revision == 0 ||
      state.native_revision == 0 || state.proof_epoch == 0) {
    return Result::frame_mismatch;
  }
  if (episode_run_id.empty() ||
      episode_run_id.size() >=
          game::kPlayerLifestyleSelectionEpisodeRunIdCapacityV1) {
    return Result::episode_unavailable;
  }
  for (char ch : episode_run_id) {
    if (!((ch >= 'a' && ch <= 'z') || (ch >= 'A' && ch <= 'Z') ||
          (ch >= '0' && ch <= '9') || ch == '-')) {
      return Result::episode_unavailable;
    }
  }
  const auto &source = state.state;
  if (source.current_focus_presence !=
          game::PlayerLifestyleFocusPresenceV1::present ||
      !source.current_lifestyle_progress_present ||
      !state.readiness.lifestyle_progress_ready) {
    return Result::target_progress_unavailable;
  }
  if (source.owned_perk_count >
          game::kPlayerLifestyleWindowMaximumPerksV1 ||
      source.current_lifestyle_progress.xp_total_raw < 0 ||
      source.current_lifestyle_progress.unspent_perk_points < 0 ||
      !ConvertKey(source.current_focus_key,
                  output.state.current_focus_key) ||
      !ConvertKey(source.current_lifestyle_progress.lifestyle_key,
                  output.state.lifestyle_progress[0].lifestyle_key)) {
    output = {};
    return Result::invalid_source;
  }
  for (std::uint32_t i = 0; i < source.owned_perk_count; ++i) {
    if (!ConvertKey(source.owned_perk_keys[i],
                    output.state.owned_perk_keys[i])) {
      output = {};
      return Result::invalid_source;
    }
  }
  output.candidates = candidates;
  auto &target = output.state;
  target.available = true;
  target.paused = true;
  target.snapshot_id = candidates.snapshot_id;
  std::copy(episode_run_id.begin(), episode_run_id.end(),
            target.episode_run_id.begin());
  target.public_revision = candidates.public_revision;
  target.native_revision = candidates.native_revision;
  target.proof_epoch = candidates.proof_epoch;
  target.date_raw = candidates.date_raw;
  target.player_character_id = candidates.player_character_id;
  target.current_focus_known = true;
  target.has_current_focus = true;
  target.owned_perks_fully_materialized = true;
  target.owned_perk_count = source.owned_perk_count;
  target.lifestyle_progress_fully_materialized = true;
  target.lifestyle_progress_count = 1;
  target.lifestyle_progress[0].experience_raw =
      source.current_lifestyle_progress.xp_total_raw;
  target.lifestyle_progress[0].perk_points =
      source.current_lifestyle_progress.unspent_perk_points;
  return Result::ready;
}

std::string_view PlayerLifestyleFormalPreconditionResultKeyV1(
    Result result) noexcept {
  switch (result) {
  case Result::ready: return "ready";
  case Result::source_unavailable: return "source_unavailable";
  case Result::frame_mismatch: return "frame_mismatch";
  case Result::episode_unavailable: return "episode_unavailable";
  case Result::target_progress_unavailable:
    return "target_progress_unavailable";
  case Result::invalid_source: return "invalid_source";
  }
  return "invalid_source";
}

} // namespace xar::ck3_11906
