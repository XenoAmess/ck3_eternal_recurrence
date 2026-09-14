#include "xar_bridge/steward_develop_county_candidates_v1.hpp"

#include <algorithm>
#include <cstdint>
#include <limits>
#include <string_view>
#include <unordered_set>

namespace xar::ck3_11906 {
namespace {

constexpr std::size_t kMaximumCandidates = 16'384;
using Failure = game::StewardDevelopCountyFailureReasonV1;
using Result = game::ReadStewardDevelopCountyCandidatesResultV1;

bool PositiveIdentity(std::int32_t value) noexcept { return value > 0; }

bool StableKey(std::string_view value) noexcept {
  if (value.empty()) {
    return false;
  }
  for (const char character : value) {
    if (!((character >= 'a' && character <= 'z') ||
          (character >= '0' && character <= '9') || character == '_')) {
      return false;
    }
  }
  return true;
}

Failure ValidateSample(
    const StewardDevelopCountyCandidatesSourceSampleV1 &sample,
    std::int32_t expected_player) noexcept {
  if (!PositiveIdentity(sample.player_character_id) ||
      !PositiveIdentity(sample.steward_character_id) ||
      sample.player_character_id != expected_player ||
      !sample.player_identity_round_trip ||
      !sample.steward_identity_round_trip) {
    return Failure::identity_round_trip_failed;
  }
  if ((!sample.shown && sample.valid) ||
      (sample.valid && sample.task_failure_reason.has_value()) ||
      (!sample.valid && !sample.task_failure_reason.has_value()) ||
      (sample.task_failure_reason.has_value() &&
       !StableKey(sample.task_failure_reason.value())) ||
      (!sample.valid && !sample.candidates.empty()) ||
      sample.candidates.size() > kMaximumCandidates) {
    return Failure::schema_invariant_failed;
  }
  std::unordered_set<std::int32_t> titles;
  std::unordered_set<std::int32_t> provinces;
  for (const auto &row : sample.candidates) {
    const auto &candidate = row.candidate;
    if (!PositiveIdentity(candidate.county_title_id) ||
        !PositiveIdentity(candidate.capital_province_id) ||
        !PositiveIdentity(candidate.holder_character_id) ||
        !row.county_title_identity_round_trip ||
        !row.capital_province_identity_round_trip ||
        !row.holder_character_identity_round_trip) {
      return Failure::identity_round_trip_failed;
    }
    // P0 enumerates the native legal domain. Illegal rows and partial
    // development observations cannot cross this seam.
    if (!candidate.native_legal || candidate.development_level_raw < 0 ||
        candidate.development_level_raw >
            std::numeric_limits<std::int32_t>::max() ||
        candidate.max_development_level_raw < 0 ||
        candidate.max_development_level_raw >
            std::numeric_limits<std::int32_t>::max() ||
        !StableKey(candidate.terrain_key)) {
      return Failure::schema_invariant_failed;
    }
    if (!titles.insert(candidate.county_title_id).second ||
        !provinces.insert(candidate.capital_province_id).second) {
      return Failure::identity_drift;
    }
  }
  return Failure::none;
}

void Materialize(
    const StewardDevelopCountyCandidatesSourceSampleV1 &sample,
    const game::StewardDevelopCountyCandidatesFrameV1 &frame,
    game::StewardDevelopCountyCandidatesV1 &output) {
  output.status = game::StewardDevelopCountyCandidatesStatusV1::available;
  output.snapshot_revision = frame.snapshot_revision;
  output.observed_date_raw = frame.date_raw;
  output.player_character_id = sample.player_character_id;
  output.steward_character_id = sample.steward_character_id;
  output.task_key.assign(kStewardDevelopCountyCandidatesV1TaskKey);
  output.shown = sample.shown;
  output.valid = sample.valid;
  output.task_failure_reason = sample.task_failure_reason;
  output.steward_increase_development_value_raw =
      sample.steward_increase_development_value_raw;
  output.current_gold_raw = sample.current_gold_raw;
  output.no_ai_increase_development = sample.no_ai_increase_development;
  output.has_active_improve_development_directive =
      sample.has_active_improve_development_directive;
  output.target_selection_mode.assign(
      kStewardDevelopCountyCandidatesV1TargetSelectionMode);
  output.candidates.clear();
  output.candidates.reserve(sample.candidates.size());
  for (const auto &row : sample.candidates) {
    output.candidates.push_back(row.candidate);
  }
  output.same_frame_stable = true;
  output.readiness.ready = true;
  output.unavailable_reason = Failure::none;
}

} // namespace

StewardDevelopCountyCandidatesNativeEnvironmentV1
BindStewardDevelopCountyCandidatesNativeEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept {
  return {module_base, exact_build_admitted, false};
}

game::ReadStewardDevelopCountyCandidatesResultV1
ReadStewardDevelopCountyCandidatesV1(
    const StewardDevelopCountyCandidatesNativeEnvironmentV1 &environment,
    const StewardDevelopCountyCandidatesAccessV1 &access,
    const StewardDevelopCountyCandidatesRequestV1 &request,
    game::StewardDevelopCountyCandidatesV1 &output) noexcept {
  output = {};
  output.snapshot_revision = request.expected_snapshot_revision;
  const auto fail = [&](Failure reason) noexcept {
    output.status = game::StewardDevelopCountyCandidatesStatusV1::unavailable;
    output.player_character_id.reset();
    output.steward_character_id.reset();
    output.shown.reset();
    output.valid.reset();
    output.task_failure_reason.reset();
    output.steward_increase_development_value_raw.reset();
    output.current_gold_raw.reset();
    output.no_ai_increase_development.reset();
    output.has_active_improve_development_directive.reset();
    output.candidates.clear();
    output.same_frame_stable = false;
    output.readiness.ready = false;
    output.unavailable_reason = reason;
    return Result::unavailable;
  };
  try {
    if (request.expected_snapshot_revision == 0) {
      return fail(Failure::invalid_request);
    }
    if (!environment.exact_build_admitted) {
      return fail(Failure::exact_build_not_admitted);
    }
    // The production ABI is intentionally absent at this contract stage.
    if (!environment.offline_fixture_source) {
      return fail(Failure::native_reader_not_frozen);
    }
    // module_base == 0 is part of the explicit offline-only authorization.
    if (environment.module_base != 0 ||
        access.read_offline_fixture_source == nullptr) {
      return fail(Failure::offline_fixture_source_not_authorized);
    }
    if (access.is_main_thread == nullptr ||
        !access.is_main_thread(access.context)) {
      return fail(Failure::application_main_thread_required);
    }
    if (access.capture_frame == nullptr) {
      return fail(Failure::frame_capture_failed);
    }
    game::StewardDevelopCountyCandidatesFrameV1 before{};
    if (!access.capture_frame(access.context, before)) {
      return fail(Failure::frame_capture_failed);
    }
    output.observed_date_raw = before.date_raw;
    if (before.snapshot_revision != request.expected_snapshot_revision) {
      return fail(Failure::snapshot_revision_mismatch);
    }
    if (!before.paused || !before.map_ready ||
        !before.has_played_character || !before.played_character_alive ||
        !PositiveIdentity(before.played_character_id)) {
      return fail(Failure::paused_player_unavailable);
    }

    StewardDevelopCountyCandidatesSourceSampleV1 first{};
    StewardDevelopCountyCandidatesSourceSampleV1 second{};
    if (!access.read_offline_fixture_source(access.context, first) ||
        !access.read_offline_fixture_source(access.context, second)) {
      return fail(Failure::fixture_source_failed);
    }
    const auto first_validation =
        ValidateSample(first, before.played_character_id);
    const auto second_validation =
        ValidateSample(second, before.played_character_id);
    if (first_validation != Failure::none) {
      return fail(first_validation);
    }
    if (second_validation != Failure::none) {
      return fail(second_validation);
    }
    if (first != second) {
      const bool identity_changed =
          first.player_character_id != second.player_character_id ||
          first.steward_character_id != second.steward_character_id ||
          first.candidates.size() != second.candidates.size() ||
          !std::equal(first.candidates.begin(), first.candidates.end(),
                      second.candidates.begin(), second.candidates.end(),
                      [](const auto &left, const auto &right) {
                        return left.candidate.county_title_id ==
                                   right.candidate.county_title_id &&
                               left.candidate.capital_province_id ==
                                   right.candidate.capital_province_id &&
                               left.candidate.holder_character_id ==
                                   right.candidate.holder_character_id;
                      });
      return fail(identity_changed ? Failure::identity_drift
                                   : Failure::native_sample_drift);
    }
    game::StewardDevelopCountyCandidatesFrameV1 after{};
    if (!access.capture_frame(access.context, after)) {
      return fail(Failure::frame_capture_failed);
    }
    if (before != after) {
      return fail(Failure::same_frame_drift);
    }
    Materialize(first, before, output);
    return Result::available;
  } catch (...) {
    return fail(Failure::reader_exception);
  }
}

std::string_view StewardDevelopCountyFailureReasonKeyV1(
    game::StewardDevelopCountyFailureReasonV1 reason) noexcept {
  using enum game::StewardDevelopCountyFailureReasonV1;
  switch (reason) {
  case none: return "none";
  case invalid_request: return "invalid_request";
  case exact_build_not_admitted: return "exact_build_not_admitted";
  case native_reader_not_frozen: return "native_reader_not_frozen";
  case offline_fixture_source_not_authorized:
    return "offline_fixture_source_not_authorized";
  case application_main_thread_required:
    return "application_main_thread_required";
  case frame_capture_failed: return "frame_capture_failed";
  case snapshot_revision_mismatch: return "snapshot_revision_mismatch";
  case paused_player_unavailable: return "paused_player_unavailable";
  case fixture_source_failed: return "fixture_source_failed";
  case task_not_shown: return "task_not_shown";
  case task_invalid: return "task_invalid";
  case candidate_invalid: return "candidate_invalid";
  case identity_round_trip_failed: return "identity_round_trip_failed";
  case identity_drift: return "identity_drift";
  case same_frame_drift: return "same_frame_drift";
  case native_sample_drift: return "native_sample_drift";
  case schema_invariant_failed: return "schema_invariant_failed";
  case reader_exception: return "reader_exception";
  }
  return "reader_exception";
}

} // namespace xar::ck3_11906
