#include "xar_bridge/player_prisoner_management_snapshot_v1.hpp"

#if defined(NDEBUG)
#undef NDEBUG
#endif

#include <algorithm>
#include <cassert>
#include <iostream>
#include <memory>
#include <string_view>
#include <type_traits>

namespace {

namespace bridge = xar::bridge;
using Capture = bridge::PlayerPrisonerCaptureV1;
using Failure = bridge::PlayerPrisonerSnapshotFailureV1;
using FieldState = bridge::PlayerPrisonerFieldStateV1;
using NativeReasonSource = bridge::PlayerPrisonerNativeReasonSourceV1;
using PreviewSource = bridge::PlayerPrisonerPreviewSourceV1;
using Snapshot = bridge::PlayerPrisonerManagementSnapshotV1;
using UnknownReason = bridge::PlayerPrisonerUnknownReasonV1;

bridge::PlayerPrisonerTypedKeyV1 Key(std::string_view value) {
  const auto output = bridge::PlayerPrisonerKnownKeyV1(value);
  assert(output.state == FieldState::known);
  assert(bridge::PlayerPrisonerKeyViewV1(output.value) == value);
  return output;
}

bridge::PlayerPrisonerTypedKeyV1 UnknownKey(UnknownReason reason) {
  const auto output = bridge::PlayerPrisonerUnknownKeyV1(reason);
  assert(output.state == FieldState::unknown);
  assert(output.unknown_reason == reason);
  return output;
}

bridge::PlayerPrisonerOpaqueFinalBoolV1 KnownFinal(bool value) {
  return {FieldState::known, value, UnknownReason::none,
          NativeReasonSource::native_opaque_final};
}

bridge::PlayerPrisonerOpaqueFinalBoolV1 UnknownFinal(
    UnknownReason reason) {
  return {FieldState::unknown, false, reason,
          NativeReasonSource::unknown};
}

bridge::PlayerPrisonerInteractionPreviewV1 KnownPreview(
    bool can_send, std::string_view failure = {}) {
  bridge::PlayerPrisonerInteractionPreviewV1 output{};
  output.state = FieldState::known;
  output.unknown_reason = UnknownReason::none;
  output.source =
      PreviewSource::native_finalized_character_interaction;
  output.shown = true;
  output.valid = can_send;
  output.can_send = can_send;
  output.failure_reason_key =
      can_send ? UnknownKey(UnknownReason::not_applicable) : Key(failure);
  return output;
}

bridge::PlayerPrisonerInteractionPreviewV1 UnknownPreview(
    UnknownReason reason) {
  bridge::PlayerPrisonerInteractionPreviewV1 output{};
  output.unknown_reason = reason;
  output.failure_reason_key = UnknownKey(reason);
  return output;
}

bridge::PlayerPrisonerRansomPreviewV1 KnownRansom(
    std::int32_t payer, bool can_send, bool would_accept,
    std::string_view option, std::string_view resource,
    std::int64_t amount_raw, std::string_view failure = {}) {
  bridge::PlayerPrisonerRansomPreviewV1 output{};
  output.interaction = KnownPreview(can_send, failure);
  output.payer_character_id = payer;
  output.selected_option_key = Key(option);
  output.resource_key = Key(resource);
  output.resource_amount_raw = amount_raw;
  output.acceptance_required = true;
  output.would_accept_now = KnownFinal(would_accept);
  return output;
}

bridge::PlayerPrisonerRowV1 Prisoner(
    std::int32_t player, std::int32_t prisoner, bool ransom_available) {
  bridge::PlayerPrisonerRowV1 output{};
  output.prisoner_character_id = prisoner;
  output.jailer_character_id = player;
  output.prisoner_identity_round_trip = true;
  output.prisoner_alive = true;
  output.custody = ransom_available
                       ? bridge::PlayerPrisonerCustodyKindV1::house_arrest
                       : bridge::PlayerPrisonerCustodyKindV1::dungeon;
  output.time_imprisoned_days = ransom_available ? 420 : 25;
  output.has_imprisonment_reason = KnownFinal(!ransom_available);
  output.has_banish_reason = KnownFinal(false);
  output.has_execute_reason = KnownFinal(!ransom_available);
  if (ransom_available) {
    output.ransom =
        KnownRansom(prisoner, true, true, "gold", "gold",
                    50 * bridge::kPlayerPrisonerFixedPointOneV1);
    output.release_unconditional = KnownPreview(true);
    output.execute =
        KnownPreview(false, "no_execute_reason");
    output.move_to_dungeon = KnownPreview(true);
    output.move_to_house_arrest =
        KnownPreview(false, "already_in_house_arrest");
    output.torture = KnownPreview(true);
  } else {
    output.ransom =
        KnownRansom(prisoner, false, false, "current_gold", "gold",
                    10 * bridge::kPlayerPrisonerFixedPointOneV1,
                    "payer_cannot_afford");
    output.release_unconditional = KnownPreview(true);
    output.execute = KnownPreview(true);
    output.move_to_dungeon =
        KnownPreview(false, "already_in_dungeon");
    output.move_to_house_arrest = KnownPreview(true);
    output.torture =
        KnownPreview(false, "torture_currently_invalid");
  }
  return output;
}

std::unique_ptr<Capture> StableCapture() {
  auto capture = std::make_unique<Capture>();
  capture->exact_build_admitted = true;
  const auto hash =
      bridge::kPlayerPrisonerManagementSnapshotV1ExecutableSha256;
  std::copy(hash.begin(), hash.end(),
            capture->admitted_executable_sha256.begin());
  capture->source_adapter_bound = true;
  capture->application_main_thread = true;

  auto &frame = capture->frame_before;
  frame.public_revision = 700;
  frame.native_revision = 19'006;
  frame.proof_epoch = 81;
  frame.date_raw = 56'010'015;
  frame.paused = true;
  frame.map_ready = true;
  frame.played_character_id = 12'345;
  frame.played_character_alive = true;
  frame.played_character_identity_round_trip = true;
  capture->frame_after = frame;

  auto &sample = capture->first_sample;
  sample.source_read_complete = true;
  sample.played_character_id = frame.played_character_id;
  sample.played_character_identity_round_trip = true;
  sample.prisoner_collection_complete = true;
  sample.total_prisoner_count = 2;
  sample.prisoner_count = 2;
  // Source order is deliberately not lexical; publication is deterministic.
  sample.prisoners[0] =
      Prisoner(frame.played_character_id, 30'002, true);
  sample.prisoners[1] =
      Prisoner(frame.played_character_id, 20'001, false);
  capture->second_sample = sample;
  return capture;
}

void ExpectFailure(const Capture &capture, Failure expected) {
  auto output = std::make_unique<Snapshot>();
  assert(!bridge::ObservePlayerPrisonerManagementSnapshotV1(
      capture, *output));
  assert(output->status ==
         bridge::PlayerPrisonerSnapshotStatusV1::unavailable);
  assert(output->unavailable_reason == expected);
  assert(output->played_character_id == -1);
  assert(output->prisoner_count == 0);
  assert(!output->readiness.same_frame_ready);
  assert(bridge::PlayerPrisonerSnapshotFailureNameV1(expected) !=
         "unknown");
}

void TestAvailableRansomCandidateAndOpaqueReasons() {
  static_assert(std::is_trivially_copyable_v<
                bridge::PlayerPrisonerSourceSampleV1>);
  static_assert(std::is_trivially_copyable_v<Snapshot>);
  static_assert(!std::is_pointer_v<
                decltype(Snapshot::prisoners)>);

  const auto capture = StableCapture();
  auto output = std::make_unique<Snapshot>();
  assert(bridge::ObservePlayerPrisonerManagementSnapshotV1(
      *capture, *output));
  assert(output->status ==
         bridge::PlayerPrisonerSnapshotStatusV1::available);
  assert(output->unavailable_reason == Failure::none);
  assert(output->played_character_id == 12'345);
  assert(output->total_prisoner_count == 2);
  assert(output->prisoner_count == 2);
  assert(output->prisoners[0].prisoner_character_id == 20'001);
  assert(output->prisoners[1].prisoner_character_id == 30'002);
  const auto &candidate = output->prisoners[1];
  assert(candidate.ransom.interaction.can_send);
  assert(candidate.ransom.would_accept_now.value);
  assert(bridge::PlayerPrisonerKeyViewV1(
             candidate.ransom.selected_option_key.value) == "gold");
  assert(candidate.ransom.resource_amount_raw == 5'000'000);
  assert(candidate.release_unconditional.can_send);
  assert(!candidate.execute.can_send);
  assert(candidate.has_execute_reason.source ==
         NativeReasonSource::native_opaque_final);
  assert(!output->religious_details_exposed);
  assert(output->readiness.collection_ready);
  assert(output->readiness.crime_reasons_ready);
  assert(output->readiness.ransom_previews_ready);
  assert(output->readiness.ransom_candidate_available);
  assert(output->readiness.release_previews_ready);
  assert(output->readiness.punishment_legality_ready);
  assert(output->readiness.same_frame_ready);
  assert(output->readiness.semantic_ready);
}

void TestTypedUnknownRemainsAvailableButNotReady() {
  auto capture = StableCapture();
  auto &row = capture->first_sample.prisoners[0];
  row.has_banish_reason =
      UnknownFinal(UnknownReason::native_final_evaluator_unresolved);
  row.ransom = {};
  row.ransom.interaction =
      UnknownPreview(UnknownReason::native_role_binding_unresolved);
  capture->second_sample = capture->first_sample;

  Snapshot output{};
  assert(bridge::ObservePlayerPrisonerManagementSnapshotV1(
      *capture, output));
  assert(output.status ==
         bridge::PlayerPrisonerSnapshotStatusV1::available);
  assert(output.prisoners[1].has_banish_reason.state ==
         FieldState::unknown);
  assert(output.prisoners[1].has_banish_reason.unknown_reason ==
         UnknownReason::native_final_evaluator_unresolved);
  assert(output.prisoners[1].ransom.interaction.state ==
         FieldState::unknown);
  assert(!output.readiness.crime_reasons_ready);
  assert(!output.readiness.ransom_previews_ready);
  assert(!output.readiness.ransom_candidate_available);
  assert(!output.readiness.semantic_ready);
  assert(bridge::PlayerPrisonerUnknownReasonNameV1(
             UnknownReason::native_role_binding_unresolved) ==
         "native_role_binding_unresolved");
}

void TestDefaultOffAndBuildAdmission() {
  auto capture = StableCapture();
  capture->source_adapter_bound = false;
  ExpectFailure(*capture, Failure::source_adapter_unavailable);

  capture = StableCapture();
  capture->admitted_executable_sha256[0] = '0';
  ExpectFailure(*capture, Failure::exact_build_mismatch);
}

void TestPausedApplicationMainAndFrameGates() {
  auto capture = StableCapture();
  capture->application_main_thread = false;
  ExpectFailure(*capture, Failure::application_main_thread_required);

  capture = StableCapture();
  capture->frame_before.paused = false;
  capture->frame_after = capture->frame_before;
  ExpectFailure(*capture, Failure::not_paused);

  capture = StableCapture();
  ++capture->frame_after.proof_epoch;
  ExpectFailure(*capture, Failure::frame_drift);
}

void TestCollectionCompletenessAndIdentityGates() {
  auto capture = StableCapture();
  capture->first_sample.prisoner_collection_complete = false;
  capture->second_sample = capture->first_sample;
  ExpectFailure(*capture, Failure::prisoner_collection_incomplete);

  capture = StableCapture();
  capture->first_sample.total_prisoner_count = 3;
  capture->second_sample = capture->first_sample;
  ExpectFailure(*capture, Failure::prisoner_count_invalid);

  capture = StableCapture();
  capture->first_sample.prisoners[1].prisoner_character_id =
      capture->first_sample.prisoners[0].prisoner_character_id;
  capture->second_sample = capture->first_sample;
  ExpectFailure(*capture, Failure::duplicate_prisoner_identity);

  capture = StableCapture();
  capture->first_sample.prisoners[0].jailer_character_id = 99'999;
  capture->second_sample = capture->first_sample;
  ExpectFailure(*capture, Failure::jailer_identity_mismatch);
}

void TestNativeFinalSourcesCannotBeSubstituted() {
  auto capture = StableCapture();
  capture->first_sample.prisoners[0].has_execute_reason.source =
      NativeReasonSource::unknown;
  capture->second_sample = capture->first_sample;
  ExpectFailure(*capture, Failure::native_reason_source_invalid);

  capture = StableCapture();
  capture->first_sample.prisoners[0].execute.source =
      PreviewSource::unknown;
  capture->second_sample = capture->first_sample;
  ExpectFailure(*capture, Failure::native_preview_source_invalid);
}

void TestPreviewAndRansomTermInvariants() {
  auto capture = StableCapture();
  capture->first_sample.prisoners[0].execute.can_send = true;
  capture->second_sample = capture->first_sample;
  ExpectFailure(*capture, Failure::preview_invariant_failed);

  capture = StableCapture();
  capture->first_sample.prisoners[0].ransom.payer_character_id = -1;
  capture->second_sample = capture->first_sample;
  ExpectFailure(*capture, Failure::ransom_terms_invalid);

  capture = StableCapture();
  capture->first_sample.prisoners[0].ransom.resource_amount_raw = -1;
  capture->second_sample = capture->first_sample;
  ExpectFailure(*capture, Failure::ransom_terms_invalid);
}

void TestDoubleSampleDriftStaysRed() {
  auto capture = StableCapture();
  ++capture->second_sample.prisoners[0].ransom.resource_amount_raw;
  ExpectFailure(*capture, Failure::source_sample_drift);
}

void TestStableKeyVocabulary() {
  bridge::PlayerPrisonerKeyV1 key{};
  assert(bridge::AssignPlayerPrisonerKeyV1(
      "release_from_prison_interaction", key));
  assert(bridge::PlayerPrisonerKeyViewV1(key) ==
         "release_from_prison_interaction");
  assert(!bridge::AssignPlayerPrisonerKeyV1(
      "faith-derived-detail", key));
  assert(bridge::PlayerPrisonerKeyViewV1(key).empty());
}

} // namespace

int main() {
  TestAvailableRansomCandidateAndOpaqueReasons();
  TestTypedUnknownRemainsAvailableButNotReady();
  TestDefaultOffAndBuildAdmission();
  TestPausedApplicationMainAndFrameGates();
  TestCollectionCompletenessAndIdentityGates();
  TestNativeFinalSourcesCannotBeSubstituted();
  TestPreviewAndRansomTermInvariants();
  TestDoubleSampleDriftStaysRed();
  TestStableKeyVocabulary();
  std::cout
      << "player_prisoner_management_snapshot_v1_test: 9/9 GREEN\n";
  return 0;
}
