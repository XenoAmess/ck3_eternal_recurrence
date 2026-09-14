#include "xar_bridge/marriage_matchmaking_observer_v1.hpp"

#include <algorithm>
#include <cstring>
#include <limits>

namespace xar::bridge {
namespace {

template <typename Value>
bool AddRva(std::uintptr_t module_base, std::uintptr_t rva,
            Value &output) noexcept {
  if (module_base == 0 ||
      rva > (std::numeric_limits<std::uintptr_t>::max)() - module_base) {
    output = 0;
    return false;
  }
  output = static_cast<Value>(module_base + rva);
  return true;
}

std::string_view BoundedView(
    const std::array<char, kMarriageMatchmakingSnapshotIdCapacityV1>
        &value) noexcept {
  const auto end = std::find(value.begin(), value.end(), '\0');
  return {value.data(), static_cast<std::size_t>(end - value.begin())};
}

bool ValidSnapshotId(std::string_view value) noexcept {
  if (value.empty() ||
      value.size() >= kMarriageMatchmakingSnapshotIdCapacityV1) {
    return false;
  }
  return std::all_of(value.begin(), value.end(), [](char character) {
    const auto byte = static_cast<unsigned char>(character);
    return byte >= 0x21 && byte <= 0x7E && character != '"' &&
        character != '\\';
  });
}

bool NativeEntryPointsComplete(
    const MarriageMatchmakingNativeEntryPointsV1 &native) noexcept {
  return native.enumerate_candidates != 0 &&
      native.score_filter_candidates != 0 &&
      native.candidate_gate_and_score != 0 && native.complete_can_send != 0 &&
      native.recipient_ai_accept != 0 && native.outer_answer != 0 &&
      native.outcome_dispatch != 0;
}

bool ValidRequest(const MarriageMatchmakingObserverRequestV1 &request) noexcept {
  return ValidSnapshotId(request.expected_snapshot_id) &&
      request.expected_public_revision != 0 &&
      request.expected_native_revision != 0 && request.expected_date_raw > 0 &&
      request.subject_character_id != 0 &&
      request.matchmaker_character_id == request.subject_character_id &&
      request.limit > 0 &&
      request.limit <= kMarriageMatchmakingMaximumCandidatesV1 &&
      request.candidate_character_id != request.subject_character_id;
}

MarriageMatchmakingObserverFailureV1 ValidateInitialFrame(
    const MarriageMatchmakingFrameV1 &frame,
    const MarriageMatchmakingObserverRequestV1 &request) noexcept {
  if (BoundedView(frame.snapshot_id) != request.expected_snapshot_id) {
    return MarriageMatchmakingObserverFailureV1::snapshot_identity_mismatch;
  }
  if (frame.public_revision != request.expected_public_revision ||
      frame.native_revision != request.expected_native_revision) {
    return MarriageMatchmakingObserverFailureV1::revision_drift;
  }
  if (frame.date_raw != request.expected_date_raw) {
    return MarriageMatchmakingObserverFailureV1::date_drift;
  }
  if (!frame.paused) {
    return MarriageMatchmakingObserverFailureV1::not_paused;
  }
  if (!frame.map_ready || !frame.has_played_character ||
      !frame.played_character_alive ||
      !frame.played_character_identity_round_trip ||
      frame.played_character_id != request.subject_character_id) {
    return MarriageMatchmakingObserverFailureV1::player_unavailable;
  }
  return MarriageMatchmakingObserverFailureV1::none;
}

MarriageMatchmakingObserverFailureV1 ClassifyFrameDrift(
    const MarriageMatchmakingFrameV1 &before,
    const MarriageMatchmakingFrameV1 &after) noexcept {
  if (BoundedView(before.snapshot_id) != BoundedView(after.snapshot_id)) {
    return MarriageMatchmakingObserverFailureV1::snapshot_identity_mismatch;
  }
  if (before.public_revision != after.public_revision ||
      before.native_revision != after.native_revision ||
      before.proof_epoch != after.proof_epoch) {
    return MarriageMatchmakingObserverFailureV1::revision_drift;
  }
  if (before.date_raw != after.date_raw) {
    return MarriageMatchmakingObserverFailureV1::date_drift;
  }
  if (!(before == after)) {
    return MarriageMatchmakingObserverFailureV1::revision_drift;
  }
  return MarriageMatchmakingObserverFailureV1::none;
}

bool DirectPairRolesAreValid(
    const MarriageMatchmakingPairRolesV1 &roles,
    std::uint32_t subject_character_id,
    std::uint32_t matchmaker_character_id,
    std::uint32_t candidate_character_id) noexcept {
  return roles.actor_character_id == matchmaker_character_id &&
      roles.recipient_character_id != 0 &&
      roles.secondary_actor_character_id == subject_character_id &&
      roles.secondary_recipient_character_id == candidate_character_id &&
      roles.actor_character_id != roles.recipient_character_id &&
      roles.secondary_actor_character_id !=
          roles.secondary_recipient_character_id;
}

MarriageMatchmakingObserverFailureV1 ReadNativeSample(
    const MarriageMatchmakingObserverEnvironmentV1 &environment,
    const MarriageMatchmakingObserverAccessV1 &access,
    const MarriageMatchmakingObserverRequestV1 &request,
    MarriageMatchmakingNativeSampleV1 &output) noexcept {
  output = {};
  output.subject_character_id = request.subject_character_id;
  output.matchmaker_character_id = request.matchmaker_character_id;

  const auto source_result = access.read_ranked_candidates(
      access.context, environment.native, request.subject_character_id,
      request.limit, output.candidates, output.candidate_count);
  if (source_result ==
      MarriageNativeSourceResultV1::ranked_source_unavailable) {
    return MarriageMatchmakingObserverFailureV1::ranked_source_unavailable;
  }
  if (source_result != MarriageNativeSourceResultV1::available) {
    return MarriageMatchmakingObserverFailureV1::native_ranked_source_failed;
  }
  if (output.candidate_count > request.limit ||
      output.candidate_count > kMarriageMatchmakingMaximumCandidatesV1) {
    return MarriageMatchmakingObserverFailureV1::candidate_collection_invalid;
  }

  for (std::uint32_t index = 0; index < output.candidate_count; ++index) {
    const auto candidate_id = output.candidates[index].candidate_character_id;
    if (candidate_id == 0 || candidate_id == request.subject_character_id) {
      return MarriageMatchmakingObserverFailureV1::
          candidate_collection_invalid;
    }
    for (std::uint32_t prior = 0; prior < index; ++prior) {
      if (output.candidates[prior].candidate_character_id == candidate_id) {
        return MarriageMatchmakingObserverFailureV1::
            candidate_collection_invalid;
      }
    }
    auto &evaluation = output.evaluations[index];
    if (access.evaluate_candidate(
            access.context, environment.native, request.subject_character_id,
            request.matchmaker_character_id, candidate_id, evaluation) !=
        MarriageNativeEvaluationResultV1::available) {
      return MarriageMatchmakingObserverFailureV1::pair_evaluation_failed;
    }
    if (!DirectPairRolesAreValid(evaluation.roles,
                                 request.subject_character_id,
                                 request.matchmaker_character_id,
                                 candidate_id) ||
        evaluation.predicted_outcome ==
            MarriagePredictedOutcomeV1::unavailable) {
      return MarriageMatchmakingObserverFailureV1::pair_roles_invalid;
    }
  }
  return MarriageMatchmakingObserverFailureV1::none;
}

void CopySnapshotId(
    const MarriageMatchmakingFrameV1 &frame,
    std::array<char, kMarriageMatchmakingSnapshotIdCapacityV1>
        &output) noexcept {
  output = frame.snapshot_id;
}

void AppendBool(std::string &output, bool value) {
  output += value ? "true" : "false";
}

} // namespace

MarriageMatchmakingNativeEntryPointsV1
BindMarriageMatchmakingNativeEntryPointsV1(
    std::uintptr_t module_base) noexcept {
  MarriageMatchmakingNativeEntryPointsV1 output{};
  const bool complete =
      AddRva(module_base, kMarriageCandidateEnumeratorRvaV1,
             output.enumerate_candidates) &&
      AddRva(module_base, kMarriageCandidateScoreFilterRvaV1,
             output.score_filter_candidates) &&
      AddRva(module_base, kMarriageCandidateGateAndScoreRvaV1,
             output.candidate_gate_and_score) &&
      AddRva(module_base, kMarriageCompleteCanSendRvaV1,
             output.complete_can_send) &&
      AddRva(module_base, kMarriageRecipientAiAcceptRvaV1,
             output.recipient_ai_accept) &&
      AddRva(module_base, kMarriageOuterAnswerRvaV1,
             output.outer_answer) &&
      AddRva(module_base, kMarriageOutcomeDispatchRvaV1,
             output.outcome_dispatch);
  if (!complete) output = {};
  return output;
}

bool ReadMarriageMatchmakingObserverV1(
    const MarriageMatchmakingObserverEnvironmentV1 &environment,
    const MarriageMatchmakingObserverAccessV1 &access,
    const MarriageMatchmakingObserverRequestV1 &request,
    MarriageMatchmakingObservationV1 &output) noexcept {
  output = {};
  auto fail = [&output](MarriageMatchmakingObserverFailureV1 failure) {
    output = {};
    output.unavailable_reason = failure;
    return false;
  };

  if (!ValidRequest(request) || access.capture_frame == nullptr ||
      access.is_main_thread == nullptr ||
      access.read_ranked_candidates == nullptr ||
      access.evaluate_candidate == nullptr) {
    return fail(MarriageMatchmakingObserverFailureV1::invalid_request);
  }
  if (!environment.exact_build_admitted ||
      environment.admitted_executable_sha256 !=
          kMarriageMatchmakingObserverExecutableSha256V1) {
    return fail(
        MarriageMatchmakingObserverFailureV1::exact_build_not_admitted);
  }
  if (environment.module_base == 0 ||
      !NativeEntryPointsComplete(environment.native) ||
      environment.native !=
          BindMarriageMatchmakingNativeEntryPointsV1(
              environment.module_base)) {
    return fail(MarriageMatchmakingObserverFailureV1::
                    native_entry_points_unavailable);
  }
  if (!access.is_main_thread(access.context)) {
    return fail(MarriageMatchmakingObserverFailureV1::
                    application_main_thread_required);
  }

  MarriageMatchmakingFrameV1 before{};
  if (!access.capture_frame(access.context, before)) {
    return fail(
        MarriageMatchmakingObserverFailureV1::frame_capture_failed);
  }
  const auto initial_failure = ValidateInitialFrame(before, request);
  if (initial_failure != MarriageMatchmakingObserverFailureV1::none) {
    return fail(initial_failure);
  }

  MarriageMatchmakingNativeSampleV1 first{};
  const auto first_failure =
      ReadNativeSample(environment, access, request, first);
  if (first_failure != MarriageMatchmakingObserverFailureV1::none) {
    return fail(first_failure);
  }
  MarriageMatchmakingNativeSampleV1 second{};
  const auto second_failure =
      ReadNativeSample(environment, access, request, second);
  if (second_failure != MarriageMatchmakingObserverFailureV1::none) {
    return fail(second_failure);
  }
  if (first != second) {
    return fail(MarriageMatchmakingObserverFailureV1::native_sample_drift);
  }

  MarriageMatchmakingFrameV1 after{};
  if (!access.capture_frame(access.context, after)) {
    return fail(
        MarriageMatchmakingObserverFailureV1::frame_capture_failed);
  }
  const auto frame_failure = ClassifyFrameDrift(before, after);
  if (frame_failure != MarriageMatchmakingObserverFailureV1::none) {
    return fail(frame_failure);
  }

  output.status = MarriageMatchmakingObserverStatusV1::available;
  output.unavailable_reason = MarriageMatchmakingObserverFailureV1::none;
  CopySnapshotId(before, output.snapshot_id);
  output.public_revision = before.public_revision;
  output.native_revision = before.native_revision;
  output.proof_epoch = before.proof_epoch;
  output.date_raw = before.date_raw;
  output.subject_character_id = first.subject_character_id;
  output.matchmaker_character_id = first.matchmaker_character_id;

  for (std::uint32_t index = 0; index < first.candidate_count; ++index) {
    const auto candidate_id = first.candidates[index].candidate_character_id;
    if (request.candidate_character_id != 0 &&
        request.candidate_character_id != candidate_id) {
      continue;
    }
    auto &candidate = output.candidates[output.candidate_count++];
    candidate.rank = index + 1;
    candidate.subject_character_id = first.subject_character_id;
    candidate.matchmaker_character_id = first.matchmaker_character_id;
    candidate.candidate_character_id = candidate_id;
    candidate.native_candidate_score =
        first.candidates[index].native_candidate_score;
    candidate.evaluation = first.evaluations[index];
  }

  output.readiness.ranked_candidates_ready = true;
  output.readiness.pair_character_ids_ready = true;
  output.readiness.native_score_ready = true;
  output.readiness.complete_can_send_ready = true;
  output.readiness.recipient_ai_accept_ready = true;
  output.readiness.recipient_answer_ready = true;
  output.readiness.predicted_outcome_ready = true;
  output.readiness.same_frame_ready = true;
  return true;
}

std::string_view MarriageMatchmakingObserverFailureKeyV1(
    MarriageMatchmakingObserverFailureV1 failure) noexcept {
  switch (failure) {
  case MarriageMatchmakingObserverFailureV1::none:
    return "none";
  case MarriageMatchmakingObserverFailureV1::invalid_request:
    return "invalid_request";
  case MarriageMatchmakingObserverFailureV1::exact_build_not_admitted:
    return "exact_build_not_admitted";
  case MarriageMatchmakingObserverFailureV1::native_entry_points_unavailable:
    return "native_entry_points_unavailable";
  case MarriageMatchmakingObserverFailureV1::
      application_main_thread_required:
    return "application_main_thread_required";
  case MarriageMatchmakingObserverFailureV1::frame_capture_failed:
    return "frame_capture_failed";
  case MarriageMatchmakingObserverFailureV1::snapshot_identity_mismatch:
    return "snapshot_identity_mismatch";
  case MarriageMatchmakingObserverFailureV1::revision_drift:
    return "revision_drift";
  case MarriageMatchmakingObserverFailureV1::date_drift:
    return "date_drift";
  case MarriageMatchmakingObserverFailureV1::not_paused:
    return "not_paused";
  case MarriageMatchmakingObserverFailureV1::player_unavailable:
    return "player_unavailable";
  case MarriageMatchmakingObserverFailureV1::ranked_source_unavailable:
    return "ranked_source_unavailable";
  case MarriageMatchmakingObserverFailureV1::native_ranked_source_failed:
    return "native_ranked_source_failed";
  case MarriageMatchmakingObserverFailureV1::native_sample_drift:
    return "native_sample_drift";
  case MarriageMatchmakingObserverFailureV1::candidate_collection_invalid:
    return "candidate_collection_invalid";
  case MarriageMatchmakingObserverFailureV1::pair_evaluation_failed:
    return "pair_evaluation_failed";
  case MarriageMatchmakingObserverFailureV1::pair_roles_invalid:
    return "pair_roles_invalid";
  }
  return "unknown";
}

std::string_view MarriagePredictedOutcomeKeyV1(
    MarriagePredictedOutcomeV1 outcome) noexcept {
  switch (outcome) {
  case MarriagePredictedOutcomeV1::unavailable:
    return "unavailable";
  case MarriagePredictedOutcomeV1::marriage:
    return "marriage";
  case MarriagePredictedOutcomeV1::betrothal:
    return "betrothal";
  }
  return "unavailable";
}

std::string SerializeMarriageMatchmakingObservationV1(
    const MarriageMatchmakingObservationV1 &observation) {
  std::string output;
  output.reserve(2048);
  output += "{\"private_build\":true,\"advertised\":false,";
  if (observation.status != MarriageMatchmakingObserverStatusV1::available) {
    output += "\"status\":\"unavailable\",\"unavailable_reason\":\"";
    output += MarriageMatchmakingObserverFailureKeyV1(
        observation.unavailable_reason);
    output += "\"}";
    return output;
  }

  output += "\"status\":\"available\",\"exact_build\":\"1.19.0.6\",";
  output += "\"snapshot_id\":\"";
  output += BoundedView(observation.snapshot_id);
  output += "\",\"public_revision\":";
  output += std::to_string(observation.public_revision);
  output += ",\"native_revision\":";
  output += std::to_string(observation.native_revision);
  output += ",\"proof_epoch\":";
  output += std::to_string(observation.proof_epoch);
  output += ",\"date_raw\":";
  output += std::to_string(observation.date_raw);
  output += ",\"subject_character_id\":";
  output += std::to_string(observation.subject_character_id);
  output += ",\"matchmaker_character_id\":";
  output += std::to_string(observation.matchmaker_character_id);
  output += ",\"religion_projection\":\"native_final_results_only\",";
  output += "\"candidates\":[";
  for (std::uint32_t index = 0; index < observation.candidate_count; ++index) {
    if (index != 0) output += ',';
    const auto &candidate = observation.candidates[index];
    const auto &evaluation = candidate.evaluation;
    output += "{\"rank\":";
    output += std::to_string(candidate.rank);
    output += ",\"subject_character_id\":";
    output += std::to_string(candidate.subject_character_id);
    output += ",\"matchmaker_character_id\":";
    output += std::to_string(candidate.matchmaker_character_id);
    output += ",\"candidate_character_id\":";
    output += std::to_string(candidate.candidate_character_id);
    output += ",\"native_candidate_score\":";
    output += std::to_string(candidate.native_candidate_score);
    output += ",\"pair_roles\":{\"actor_character_id\":";
    output += std::to_string(evaluation.roles.actor_character_id);
    output += ",\"recipient_character_id\":";
    output += std::to_string(evaluation.roles.recipient_character_id);
    output += ",\"secondary_actor_character_id\":";
    output +=
        std::to_string(evaluation.roles.secondary_actor_character_id);
    output += ",\"secondary_recipient_character_id\":";
    output +=
        std::to_string(evaluation.roles.secondary_recipient_character_id);
    output += ",\"intermediary_character_id\":";
    output += std::to_string(evaluation.roles.intermediary_character_id);
    output += "},\"complete_can_send\":";
    AppendBool(output, evaluation.complete_can_send);
    output += ",\"complete_can_send_status_raw\":";
    output += std::to_string(evaluation.complete_can_send_status_raw);
    output += ",\"recipient_ai_accept_raw\":";
    output += std::to_string(evaluation.recipient_ai_accept_raw);
    output += ",\"recipient_ai_accept_scale\":";
    output += std::to_string(kMarriageAiAcceptFixedPointScaleV1);
    output += ",\"recipient_answer_status_raw\":";
    output += std::to_string(evaluation.recipient_answer_status_raw);
    output += ",\"recipient_answer_allows_send\":";
    AppendBool(output, evaluation.recipient_answer_allows_send);
    output += ",\"predicted_outcome\":\"";
    output += MarriagePredictedOutcomeKeyV1(
        evaluation.predicted_outcome);
    output += "\"}";
  }
  output += "],\"readiness\":{";
  output += "\"ranked_candidates_ready\":";
  AppendBool(output, observation.readiness.ranked_candidates_ready);
  output += ",\"pair_character_ids_ready\":";
  AppendBool(output, observation.readiness.pair_character_ids_ready);
  output += ",\"native_score_ready\":";
  AppendBool(output, observation.readiness.native_score_ready);
  output += ",\"complete_can_send_ready\":";
  AppendBool(output, observation.readiness.complete_can_send_ready);
  output += ",\"recipient_ai_accept_ready\":";
  AppendBool(output, observation.readiness.recipient_ai_accept_ready);
  output += ",\"recipient_answer_ready\":";
  AppendBool(output, observation.readiness.recipient_answer_ready);
  output += ",\"predicted_outcome_ready\":";
  AppendBool(output, observation.readiness.predicted_outcome_ready);
  output += ",\"same_frame_ready\":";
  AppendBool(output, observation.readiness.same_frame_ready);
  output += "}}";
  return output;
}

} // namespace xar::bridge
