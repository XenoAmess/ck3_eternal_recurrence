#include "xar_bridge/major_decision_found_kingdom_source_adapter_v1.hpp"

#include <algorithm>
#include <cstring>
#include <type_traits>

namespace xar::bridge {
namespace {

using AdapterFailure = MajorDecisionFoundKingdomSourceAdapterFailureV1;
using CoreFailure = MajorDecisionFoundKingdomFailureV1;
using FieldState = MajorDecisionFieldStateV1;
using UnknownReason = MajorDecisionUnknownReasonV1;

struct ResolvedSourceV1 {
  MajorDecisionFoundKingdomSourcePlayerLeaseV1 player{};
  MajorDecisionFoundKingdomSourceDatabaseLeaseV1 database{};
  MajorDecisionFoundKingdomSourceDefinitionLeaseV1 definition{};
};

void Fail(MajorDecisionFoundKingdomSourceResultV1 &output,
          AdapterFailure failure,
          CoreFailure core_failure =
              CoreFailure::source_sample_incomplete) noexcept {
  output = {};
  output.failure = failure;
  output.core_failure = core_failure;
  output.snapshot.status = MajorDecisionFoundKingdomStatusV1::unavailable;
  output.snapshot.unavailable_reason = core_failure;
}

bool CallbacksComplete(
    const MajorDecisionFoundKingdomSourceAccessV1 &access) noexcept {
  return access.capture_frame != nullptr && access.resolve_player != nullptr &&
         access.resolve_decision_database != nullptr &&
         access.lookup_definition != nullptr &&
         access.evaluate_eligibility != nullptr &&
         access.evaluate_cost != nullptr &&
         access.evaluate_affordability != nullptr &&
         access.evaluate_can_take != nullptr;
}

CoreFailure ValidateFrame(
    const MajorDecisionFoundKingdomFrameV1 &frame) noexcept {
  if (!frame.application_main_thread) {
    return CoreFailure::application_main_thread_required;
  }
  if (!frame.paused) return CoreFailure::not_paused;
  if (!frame.map_ready) return CoreFailure::map_not_ready;
  if (frame.played_character_id < 0 || !frame.played_character_alive) {
    return CoreFailure::played_character_unavailable;
  }
  if (!frame.played_character_identity_round_trip) {
    return CoreFailure::played_character_identity_mismatch;
  }
  if (frame.snapshot_revision == 0 || frame.native_revision == 0 ||
      frame.proof_epoch == 0) {
    return CoreFailure::source_sample_incomplete;
  }
  return CoreFailure::none;
}

bool ValidPlayer(const MajorDecisionFoundKingdomSourcePlayerLeaseV1 &player,
                 std::int32_t expected_character_id) noexcept {
  return player.identity_round_trip && player.native_address != 0 &&
         player.character_id == expected_character_id;
}

bool SamePlayer(const MajorDecisionFoundKingdomSourcePlayerLeaseV1 &left,
                const MajorDecisionFoundKingdomSourcePlayerLeaseV1 &right)
    noexcept {
  return left.identity_round_trip == right.identity_round_trip &&
         left.native_address == right.native_address &&
         left.character_id == right.character_id;
}

bool ValidDatabase(
    const MajorDecisionFoundKingdomSourceDatabaseLeaseV1 &database) noexcept {
  return database.identity_round_trip && database.native_address != 0 &&
         database.identity != 0 && database.generation != 0;
}

bool SameDatabase(
    const MajorDecisionFoundKingdomSourceDatabaseLeaseV1 &left,
    const MajorDecisionFoundKingdomSourceDatabaseLeaseV1 &right) noexcept {
  return left.identity_round_trip == right.identity_round_trip &&
         left.native_address == right.native_address &&
         left.identity == right.identity && left.generation == right.generation;
}

bool ValidDefinition(
    const MajorDecisionFoundKingdomSourceDefinitionLeaseV1 &definition)
    noexcept {
  return definition.identity_round_trip &&
         definition.source_block_sha256_round_trip &&
         definition.native_address != 0 && definition.identity != 0 &&
         definition.generation != 0 &&
         definition.decision_id == kMajorDecisionFoundKingdomDecisionIdV1;
}

bool SameDefinition(
    const MajorDecisionFoundKingdomSourceDefinitionLeaseV1 &left,
    const MajorDecisionFoundKingdomSourceDefinitionLeaseV1 &right) noexcept {
  return left.identity_round_trip == right.identity_round_trip &&
         left.source_block_sha256_round_trip ==
             right.source_block_sha256_round_trip &&
         left.native_address == right.native_address &&
         left.identity == right.identity && left.generation == right.generation &&
         left.decision_id == right.decision_id;
}

bool ResolveSource(const MajorDecisionFoundKingdomSourceAccessV1 &access,
                   std::int32_t played_character_id,
                   ResolvedSourceV1 &output,
                   AdapterFailure &failure) noexcept {
  output = {};
  if (!access.resolve_player(access.context, played_character_id,
                             output.player) ||
      !ValidPlayer(output.player, played_character_id)) {
    failure = AdapterFailure::played_character_unavailable;
    return false;
  }
  if (!access.resolve_decision_database(access.context, output.database) ||
      !ValidDatabase(output.database)) {
    failure = AdapterFailure::decision_database_unavailable;
    return false;
  }
  if (!access.lookup_definition(
          access.context, output.database,
          kMajorDecisionFoundKingdomDecisionIdV1, output.definition)) {
    failure = AdapterFailure::decision_definition_missing;
    return false;
  }
  if (!ValidDefinition(output.definition)) {
    failure = AdapterFailure::decision_definition_identity_mismatch;
    return false;
  }
  return true;
}

MajorDecisionTypedBoolV1 Known(bool value) noexcept {
  return {FieldState::known, value, UnknownReason::none};
}

bool ReadSample(const MajorDecisionFoundKingdomSourceAccessV1 &access,
                const ResolvedSourceV1 &source,
                MajorDecisionFoundKingdomSourceSampleV1 &output,
                AdapterFailure &failure) noexcept {
  output = {};
  MajorDecisionFoundKingdomSourceEligibilityV1 eligibility{};
  if (!access.evaluate_eligibility(access.context, source.definition,
                                   source.player, eligibility)) {
    failure = AdapterFailure::eligibility_evaluation_failed;
    return false;
  }
  MajorDecisionFoundKingdomSourceCostV1 cost{};
  if (!access.evaluate_cost(access.context, source.definition, source.player,
                            cost)) {
    failure = AdapterFailure::evaluated_cost_evaluation_failed;
    return false;
  }
  bool affordable = false;
  if (!access.evaluate_affordability(access.context, source.definition,
                                     source.player, affordable)) {
    failure = AdapterFailure::affordability_evaluation_failed;
    return false;
  }
  bool can_take = false;
  if (!access.evaluate_can_take(access.context, source.definition,
                                source.player, can_take)) {
    failure = AdapterFailure::can_take_evaluation_failed;
    return false;
  }

  output.source_read_complete = true;
  output.played_character_id = source.player.character_id;
  output.decision_definition_identity_round_trip =
      source.definition.identity_round_trip &&
      source.definition.source_block_sha256_round_trip;
  output.eligibility_source =
      MajorDecisionEligibilitySourceV1::native_decision_evaluator;
  output.is_shown = Known(eligibility.is_shown);
  output.is_valid = Known(eligibility.is_valid);
  output.is_valid_showing_failures_only =
      Known(eligibility.is_valid_showing_failures_only);
  output.evaluated_cost.state = FieldState::known;
  output.evaluated_cost.source =
      MajorDecisionCostSourceV1::native_evaluated_cost;
  output.evaluated_cost.gold_q100000 = cost.gold_q100000;
  output.evaluated_cost.treasury_q100000 = cost.treasury_q100000;
  output.evaluated_cost.prestige_q100000 = cost.prestige_q100000;
  output.evaluated_cost.piety_q100000 = cost.piety_q100000;
  output.evaluated_cost.unknown_reason = UnknownReason::none;
  output.is_affordable = Known(affordable);
  output.can_take = Known(can_take);
  return true;
}

} // namespace

static_assert(
    std::is_trivially_copyable_v<MajorDecisionFoundKingdomSourceResultV1>,
    "private source results must retain only copied semantic values");

bool ObserveMajorDecisionFoundKingdomSourceV1(
    const MajorDecisionFoundKingdomSourceAccessV1 &access,
    MajorDecisionFoundKingdomSourceResultV1 &output) noexcept {
  Fail(output, AdapterFailure::callbacks_unavailable);
  if (!access.exact_build_admitted ||
      access.admitted_executable_sha256 !=
          kMajorDecisionFoundKingdomExecutableSha256V1) {
    Fail(output, AdapterFailure::exact_build_mismatch,
         CoreFailure::exact_build_not_admitted);
    return false;
  }
  if (!CallbacksComplete(access)) return false;
  if (access.current_thread_id == 0 ||
      access.current_thread_id != access.application_main_thread_id) {
    Fail(output, AdapterFailure::application_main_thread_required,
         CoreFailure::application_main_thread_required);
    return false;
  }

  MajorDecisionFoundKingdomCaptureV1 capture{};
  if (!access.capture_frame(access.context, capture.frame_before)) {
    Fail(output, AdapterFailure::frame_unavailable);
    return false;
  }
  if (!capture.frame_before.paused) {
    Fail(output, AdapterFailure::not_paused, CoreFailure::not_paused);
    return false;
  }
  const auto frame_failure = ValidateFrame(capture.frame_before);
  if (frame_failure != CoreFailure::none) {
    Fail(output, AdapterFailure::frame_invalid, frame_failure);
    return false;
  }

  AdapterFailure failure = AdapterFailure::none;
  ResolvedSourceV1 first{};
  if (!ResolveSource(access, capture.frame_before.played_character_id, first,
                     failure)) {
    Fail(output, failure,
         failure == AdapterFailure::decision_definition_identity_mismatch
             ? CoreFailure::decision_definition_identity_mismatch
             : CoreFailure::source_sample_incomplete);
    return false;
  }
  if (!ReadSample(access, first, capture.first_sample, failure)) {
    Fail(output, failure);
    return false;
  }

  // Re-resolve all three native leases for the second evaluator pass. No
  // address from the first pass is used to locate a second-pass object.
  ResolvedSourceV1 second{};
  if (!ResolveSource(access, capture.frame_before.played_character_id, second,
                     failure)) {
    Fail(output, failure);
    return false;
  }
  if (!SamePlayer(first.player, second.player)) {
    Fail(output, AdapterFailure::played_character_drift,
         CoreFailure::played_character_identity_mismatch);
    return false;
  }
  if (!SameDatabase(first.database, second.database)) {
    Fail(output, AdapterFailure::decision_database_drift,
         CoreFailure::source_sample_drift);
    return false;
  }
  if (!SameDefinition(first.definition, second.definition)) {
    Fail(output, AdapterFailure::decision_definition_drift,
         CoreFailure::source_sample_drift);
    return false;
  }
  if (!ReadSample(access, second, capture.second_sample, failure)) {
    Fail(output, failure);
    return false;
  }

  if (!access.capture_frame(access.context, capture.frame_after)) {
    Fail(output, AdapterFailure::frame_unavailable);
    return false;
  }
  if (!capture.frame_after.paused) {
    Fail(output, AdapterFailure::not_paused, CoreFailure::not_paused);
    return false;
  }
  if (capture.frame_before != capture.frame_after) {
    Fail(output, AdapterFailure::frame_drift, CoreFailure::frame_drift);
    return false;
  }
  if (capture.first_sample != capture.second_sample) {
    Fail(output, AdapterFailure::source_sample_drift,
         CoreFailure::source_sample_drift);
    return false;
  }

  capture.observer_enabled = true;
  capture.exact_build_admitted = true;
  std::copy(access.admitted_executable_sha256.begin(),
            access.admitted_executable_sha256.end(),
            capture.admitted_executable_sha256.begin());

  MajorDecisionFoundKingdomSnapshotV1 snapshot{};
  if (!ObserveMajorDecisionFoundKingdomV1(capture, snapshot)) {
    const auto core_failure = snapshot.unavailable_reason;
    Fail(output,
         core_failure == CoreFailure::source_sample_drift
             ? AdapterFailure::source_sample_drift
             : AdapterFailure::core_rejected,
         core_failure);
    return false;
  }

  output = {};
  output.failure = AdapterFailure::none;
  output.core_failure = CoreFailure::none;
  output.snapshot = snapshot;
  return true;
}

std::string_view MajorDecisionFoundKingdomSourceAdapterFailureNameV1(
    MajorDecisionFoundKingdomSourceAdapterFailureV1 failure) noexcept {
  switch (failure) {
  case AdapterFailure::none: return "none";
  case AdapterFailure::exact_build_mismatch: return "exact_build_mismatch";
  case AdapterFailure::callbacks_unavailable: return "callbacks_unavailable";
  case AdapterFailure::application_main_thread_required:
    return "application_main_thread_required";
  case AdapterFailure::frame_unavailable: return "frame_unavailable";
  case AdapterFailure::not_paused: return "not_paused";
  case AdapterFailure::frame_invalid: return "frame_invalid";
  case AdapterFailure::played_character_unavailable:
    return "played_character_unavailable";
  case AdapterFailure::played_character_drift:
    return "played_character_drift";
  case AdapterFailure::decision_database_unavailable:
    return "decision_database_unavailable";
  case AdapterFailure::decision_database_drift:
    return "decision_database_drift";
  case AdapterFailure::decision_definition_missing:
    return "decision_definition_missing";
  case AdapterFailure::decision_definition_identity_mismatch:
    return "decision_definition_identity_mismatch";
  case AdapterFailure::decision_definition_drift:
    return "decision_definition_drift";
  case AdapterFailure::eligibility_evaluation_failed:
    return "eligibility_evaluation_failed";
  case AdapterFailure::evaluated_cost_evaluation_failed:
    return "evaluated_cost_evaluation_failed";
  case AdapterFailure::affordability_evaluation_failed:
    return "affordability_evaluation_failed";
  case AdapterFailure::can_take_evaluation_failed:
    return "can_take_evaluation_failed";
  case AdapterFailure::source_sample_drift: return "source_sample_drift";
  case AdapterFailure::frame_drift: return "frame_drift";
  case AdapterFailure::core_rejected: return "core_rejected";
  }
  return "unknown";
}

} // namespace xar::bridge
