#include "xar_bridge/major_decision_found_kingdom_observer_v1.hpp"

#include <algorithm>
#include <type_traits>

namespace xar::bridge {
namespace {

using Failure = MajorDecisionFoundKingdomFailureV1;
using FieldState = MajorDecisionFieldStateV1;
using UnknownReason = MajorDecisionUnknownReasonV1;

template <std::size_t Size>
std::string_view FixedView(const std::array<char, Size> &value) noexcept {
  const auto end = std::find(value.begin(), value.end(), '\0');
  if (end == value.end()) return {};
  return {value.data(), static_cast<std::size_t>(end - value.begin())};
}

bool TypedBoolValid(const MajorDecisionTypedBoolV1 &value) noexcept {
  if (value.state == FieldState::known) {
    return value.unknown_reason == UnknownReason::none;
  }
  return value.state == FieldState::unknown && !value.value &&
         value.unknown_reason != UnknownReason::none;
}

Failure ValidateCost(const MajorDecisionEvaluatedCostV1 &cost) noexcept {
  if (cost.state == FieldState::unknown) {
    if (cost.source != MajorDecisionCostSourceV1::unknown ||
        cost.unknown_reason == UnknownReason::none || cost.gold_q100000 != 0 ||
        cost.treasury_q100000 != 0 || cost.prestige_q100000 != 0 ||
        cost.piety_q100000 != 0) {
      return Failure::evaluated_cost_source_invalid;
    }
    return Failure::none;
  }
  if (cost.state != FieldState::known ||
      cost.source != MajorDecisionCostSourceV1::native_evaluated_cost ||
      cost.unknown_reason != UnknownReason::none) {
    return Failure::evaluated_cost_source_invalid;
  }
  if (cost.gold_q100000 < 0 || cost.treasury_q100000 < 0 ||
      cost.prestige_q100000 < 0 || cost.piety_q100000 < 0) {
    return Failure::evaluated_cost_invalid;
  }
  return Failure::none;
}

bool KnownTrue(const MajorDecisionTypedBoolV1 &value) noexcept {
  return value.state == FieldState::known && value.value;
}

bool EligibilityKnown(
    const MajorDecisionFoundKingdomSourceSampleV1 &sample) noexcept {
  return sample.is_shown.state == FieldState::known &&
         sample.is_valid.state == FieldState::known &&
         sample.is_valid_showing_failures_only.state == FieldState::known;
}

Failure ValidateSample(
    const MajorDecisionFoundKingdomSourceSampleV1 &sample,
    std::int32_t played_character_id) noexcept {
  if (!sample.source_read_complete) {
    return Failure::source_sample_incomplete;
  }
  if (sample.played_character_id != played_character_id) {
    return Failure::played_character_identity_mismatch;
  }
  if (!sample.decision_definition_identity_round_trip) {
    return Failure::decision_definition_identity_mismatch;
  }
  if (sample.eligibility_source !=
      MajorDecisionEligibilitySourceV1::native_decision_evaluator) {
    return Failure::eligibility_source_invalid;
  }
  if (!TypedBoolValid(sample.is_shown) ||
      !TypedBoolValid(sample.is_valid) ||
      !TypedBoolValid(sample.is_valid_showing_failures_only) ||
      !TypedBoolValid(sample.is_affordable) ||
      !TypedBoolValid(sample.can_take)) {
    return Failure::typed_field_invalid;
  }
  const auto cost_failure = ValidateCost(sample.evaluated_cost);
  if (cost_failure != Failure::none) return cost_failure;
  if (KnownTrue(sample.can_take) &&
      (!KnownTrue(sample.is_shown) || !KnownTrue(sample.is_valid) ||
       !KnownTrue(sample.is_valid_showing_failures_only) ||
       sample.evaluated_cost.state != FieldState::known ||
       !KnownTrue(sample.is_affordable))) {
    return Failure::can_take_invariant_failed;
  }
  return Failure::none;
}

void SetUnavailable(MajorDecisionFoundKingdomSnapshotV1 &output,
                    Failure reason) noexcept {
  output = {};
  output.status = MajorDecisionFoundKingdomStatusV1::unavailable;
  output.unavailable_reason = reason;
}

Failure ValidateFrame(
    const MajorDecisionFoundKingdomFrameV1 &frame) noexcept {
  if (!frame.application_main_thread) {
    return Failure::application_main_thread_required;
  }
  if (!frame.paused) return Failure::not_paused;
  if (!frame.map_ready) return Failure::map_not_ready;
  if (!frame.played_character_alive || frame.played_character_id < 0) {
    return Failure::played_character_unavailable;
  }
  if (!frame.played_character_identity_round_trip) {
    return Failure::played_character_identity_mismatch;
  }
  return Failure::none;
}

void Publish(const MajorDecisionFoundKingdomFrameV1 &frame,
             const MajorDecisionFoundKingdomSourceSampleV1 &sample,
             MajorDecisionFoundKingdomSnapshotV1 &output) noexcept {
  output = {};
  output.status = MajorDecisionFoundKingdomStatusV1::available;
  output.unavailable_reason = Failure::none;
  output.snapshot_revision = frame.snapshot_revision;
  output.native_revision = frame.native_revision;
  output.proof_epoch = frame.proof_epoch;
  output.date_raw = frame.date_raw;
  output.played_character_id = frame.played_character_id;
  output.eligibility_source = sample.eligibility_source;
  output.is_shown = sample.is_shown;
  output.is_valid = sample.is_valid;
  output.is_valid_showing_failures_only =
      sample.is_valid_showing_failures_only;
  output.evaluated_cost = sample.evaluated_cost;
  output.is_affordable = sample.is_affordable;
  output.can_take = sample.can_take;
  output.effect_preview = {};

  auto &ready = output.readiness;
  ready.same_frame_ready = true;
  ready.eligibility_ready = EligibilityKnown(sample);
  ready.evaluated_cost_ready =
      sample.evaluated_cost.state == FieldState::known &&
      sample.evaluated_cost.source ==
          MajorDecisionCostSourceV1::native_evaluated_cost;
  ready.affordability_ready =
      sample.is_affordable.state == FieldState::known;
  ready.can_take_ready = sample.can_take.state == FieldState::known;
  ready.semantic_observation_ready =
      ready.same_frame_ready && ready.eligibility_ready &&
      ready.evaluated_cost_ready && ready.affordability_ready &&
      ready.can_take_ready;
  ready.effect_preview_ready = false;
  ready.action_ready = false;
  ready.raw_pointer_fields_persisted = false;
}

void AppendBool(std::string &output, bool value) {
  output += value ? "true" : "false";
}

void AppendTypedBool(std::string &output,
                     const MajorDecisionTypedBoolV1 &value) {
  output += "{\"state\":\"";
  output += value.state == FieldState::known ? "known" : "unknown";
  output += '"';
  if (value.state == FieldState::known) {
    output += ",\"value\":";
    AppendBool(output, value.value);
  } else {
    output += ",\"unavailable_reason\":\"";
    output += MajorDecisionUnknownReasonKeyV1(value.unknown_reason);
    output += '"';
  }
  output += '}';
}

std::string_view EligibilitySourceKey(
    MajorDecisionEligibilitySourceV1 source) noexcept {
  switch (source) {
  case MajorDecisionEligibilitySourceV1::unknown: return "unknown";
  case MajorDecisionEligibilitySourceV1::native_decision_evaluator:
    return "native_decision_evaluator";
  }
  return "unknown";
}

std::string_view CostSourceKey(MajorDecisionCostSourceV1 source) noexcept {
  switch (source) {
  case MajorDecisionCostSourceV1::unknown: return "unknown";
  case MajorDecisionCostSourceV1::native_evaluated_cost:
    return "native_evaluated_cost";
  }
  return "unknown";
}

void AppendCost(std::string &output,
                const MajorDecisionEvaluatedCostV1 &cost) {
  output += "{\"state\":\"";
  output += cost.state == FieldState::known ? "known" : "unknown";
  output += "\",\"source\":\"";
  output += CostSourceKey(cost.source);
  output += '"';
  if (cost.state == FieldState::known) {
    output += ",\"q100000\":{\"gold\":" +
              std::to_string(cost.gold_q100000);
    output += ",\"treasury\":" + std::to_string(cost.treasury_q100000);
    output += ",\"prestige\":" + std::to_string(cost.prestige_q100000);
    output += ",\"piety\":" + std::to_string(cost.piety_q100000) + '}';
  } else {
    output += ",\"unavailable_reason\":\"";
    output += MajorDecisionUnknownReasonKeyV1(cost.unknown_reason);
    output += '"';
  }
  output += '}';
}

} // namespace

static_assert(
    std::is_trivially_copyable_v<MajorDecisionFoundKingdomSourceSampleV1>,
    "private major-decision source samples must own copied values only");
static_assert(
    std::is_trivially_copyable_v<MajorDecisionFoundKingdomSnapshotV1>,
    "private major-decision snapshots must own copied values only");

bool ObserveMajorDecisionFoundKingdomV1(
    const MajorDecisionFoundKingdomCaptureV1 &capture,
    MajorDecisionFoundKingdomSnapshotV1 &output) noexcept {
  try {
    if (!capture.observer_enabled) {
      SetUnavailable(output, Failure::observer_disabled);
      return false;
    }
    if (!capture.exact_build_admitted ||
        FixedView(capture.admitted_executable_sha256) !=
            kMajorDecisionFoundKingdomExecutableSha256V1) {
      SetUnavailable(output, Failure::exact_build_not_admitted);
      return false;
    }
    auto failure = ValidateFrame(capture.frame_before);
    if (failure != Failure::none) {
      SetUnavailable(output, failure);
      return false;
    }
    if (capture.frame_before != capture.frame_after) {
      SetUnavailable(output, Failure::frame_drift);
      return false;
    }
    failure = ValidateSample(capture.first_sample,
                             capture.frame_before.played_character_id);
    if (failure != Failure::none) {
      SetUnavailable(output, failure);
      return false;
    }
    failure = ValidateSample(capture.second_sample,
                             capture.frame_before.played_character_id);
    if (failure != Failure::none) {
      SetUnavailable(output, failure);
      return false;
    }
    if (capture.first_sample != capture.second_sample) {
      SetUnavailable(output, Failure::source_sample_drift);
      return false;
    }
    Publish(capture.frame_before, capture.first_sample, output);
    return true;
  } catch (...) {
    SetUnavailable(output, Failure::source_sample_incomplete);
    return false;
  }
}

std::string SerializeMajorDecisionFoundKingdomV1(
    const MajorDecisionFoundKingdomSnapshotV1 &snapshot) {
  std::string output;
  output.reserve(1800);
  output += "{\"schema\":\"";
  output += kMajorDecisionFoundKingdomSchemaV1;
  output += "\",\"observer_key\":\"";
  output += kMajorDecisionFoundKingdomObserverKeyV1;
  output += "\",\"private_build\":true,\"advertised\":false,";
  output += "\"read_only\":true,\"status\":\"";
  output += snapshot.status == MajorDecisionFoundKingdomStatusV1::available
                ? "available"
                : "unavailable";
  output += "\",\"unavailable_reason\":\"";
  output += MajorDecisionFoundKingdomFailureKeyV1(
      snapshot.unavailable_reason);
  output += "\",\"definition\":{\"decision_id\":\"";
  output += kMajorDecisionFoundKingdomDecisionIdV1;
  output += "\",\"game_version\":\"";
  output += kMajorDecisionFoundKingdomGameVersionV1;
  output += "\",\"executable_sha256\":\"";
  output += kMajorDecisionFoundKingdomExecutableSha256V1;
  output += "\",\"decision_block_sha256\":\"";
  output += kMajorDecisionFoundKingdomDecisionBlockSha256V1;
  output += "\",\"effect_block_sha256\":\"";
  output += kMajorDecisionFoundKingdomEffectBlockSha256V1;
  output += "\",\"evidence_revision\":\"";
  output += kMajorDecisionFoundKingdomEvidenceRevisionV1;
  output += "\"},\"frame\":{\"snapshot_revision\":";
  output += std::to_string(snapshot.snapshot_revision);
  output += ",\"native_revision\":" +
            std::to_string(snapshot.native_revision);
  output += ",\"proof_epoch\":" + std::to_string(snapshot.proof_epoch);
  output += ",\"date_raw\":" + std::to_string(snapshot.date_raw);
  output += ",\"played_character_id\":" +
            std::to_string(snapshot.played_character_id);
  output += "},\"eligibility\":{\"source\":\"";
  output += EligibilitySourceKey(snapshot.eligibility_source);
  output += "\",\"is_shown\":";
  AppendTypedBool(output, snapshot.is_shown);
  output += ",\"is_valid\":";
  AppendTypedBool(output, snapshot.is_valid);
  output += ",\"is_valid_showing_failures_only\":";
  AppendTypedBool(output, snapshot.is_valid_showing_failures_only);
  output += "},\"evaluated_cost\":";
  AppendCost(output, snapshot.evaluated_cost);
  output += ",\"is_affordable\":";
  AppendTypedBool(output, snapshot.is_affordable);
  output += ",\"can_take\":";
  AppendTypedBool(output, snapshot.can_take);
  output += ",\"effect_preview\":{\"state\":\"unavailable\",";
  output += "\"unavailable_reason\":\"effect_preview_not_provided\",";
  output += "\"executable\":false},\"readiness\":{";
  output += "\"same_frame_ready\":";
  AppendBool(output, snapshot.readiness.same_frame_ready);
  output += ",\"eligibility_ready\":";
  AppendBool(output, snapshot.readiness.eligibility_ready);
  output += ",\"evaluated_cost_ready\":";
  AppendBool(output, snapshot.readiness.evaluated_cost_ready);
  output += ",\"affordability_ready\":";
  AppendBool(output, snapshot.readiness.affordability_ready);
  output += ",\"can_take_ready\":";
  AppendBool(output, snapshot.readiness.can_take_ready);
  output += ",\"semantic_observation_ready\":";
  AppendBool(output, snapshot.readiness.semantic_observation_ready);
  output += ",\"effect_preview_ready\":false,\"action_ready\":false,";
  output += "\"raw_pointer_fields_persisted\":false}}";
  return output;
}

std::string_view MajorDecisionFoundKingdomFailureKeyV1(
    MajorDecisionFoundKingdomFailureV1 failure) noexcept {
  switch (failure) {
  case Failure::none: return "none";
  case Failure::observer_disabled: return "observer_disabled";
  case Failure::exact_build_not_admitted:
    return "exact_build_not_admitted";
  case Failure::application_main_thread_required:
    return "application_main_thread_required";
  case Failure::not_paused: return "not_paused";
  case Failure::map_not_ready: return "map_not_ready";
  case Failure::played_character_unavailable:
    return "played_character_unavailable";
  case Failure::played_character_identity_mismatch:
    return "played_character_identity_mismatch";
  case Failure::frame_drift: return "frame_drift";
  case Failure::source_sample_incomplete: return "source_sample_incomplete";
  case Failure::source_sample_drift: return "source_sample_drift";
  case Failure::decision_definition_identity_mismatch:
    return "decision_definition_identity_mismatch";
  case Failure::eligibility_source_invalid:
    return "eligibility_source_invalid";
  case Failure::typed_field_invalid: return "typed_field_invalid";
  case Failure::evaluated_cost_source_invalid:
    return "evaluated_cost_source_invalid";
  case Failure::evaluated_cost_invalid: return "evaluated_cost_invalid";
  case Failure::can_take_invariant_failed:
    return "can_take_invariant_failed";
  }
  return "unknown";
}

std::string_view MajorDecisionUnknownReasonKeyV1(
    MajorDecisionUnknownReasonV1 reason) noexcept {
  switch (reason) {
  case UnknownReason::none: return "none";
  case UnknownReason::not_observed: return "not_observed";
  case UnknownReason::decision_database_unavailable:
    return "decision_database_unavailable";
  case UnknownReason::decision_definition_missing:
    return "decision_definition_missing";
  case UnknownReason::decision_evaluator_unavailable:
    return "decision_evaluator_unavailable";
  case UnknownReason::evaluated_cost_evaluator_unavailable:
    return "evaluated_cost_evaluator_unavailable";
  case UnknownReason::affordability_evaluator_unavailable:
    return "affordability_evaluator_unavailable";
  case UnknownReason::can_take_evaluator_unavailable:
    return "can_take_evaluator_unavailable";
  case UnknownReason::effect_preview_not_provided:
    return "effect_preview_not_provided";
  }
  return "unknown";
}

} // namespace xar::bridge
