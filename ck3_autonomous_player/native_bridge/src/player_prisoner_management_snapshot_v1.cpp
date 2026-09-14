#include "xar_bridge/player_prisoner_management_snapshot_v1.hpp"

#include <algorithm>
#include <type_traits>

namespace xar::bridge {
namespace {

using Failure = PlayerPrisonerSnapshotFailureV1;
using FieldState = PlayerPrisonerFieldStateV1;
using NativeReasonSource = PlayerPrisonerNativeReasonSourceV1;
using PreviewSource = PlayerPrisonerPreviewSourceV1;
using UnknownReason = PlayerPrisonerUnknownReasonV1;

template <std::size_t Size>
std::string_view FixedView(const std::array<char, Size> &value) noexcept {
  const auto end = std::find(value.begin(), value.end(), '\0');
  if (end == value.end()) return {};
  return {value.data(), static_cast<std::size_t>(end - value.begin())};
}

bool EmptyKey(const PlayerPrisonerKeyV1 &value) noexcept {
  return value.size == 0 && value.bytes[0] == '\0';
}

bool ValidKey(const PlayerPrisonerKeyV1 &value) noexcept {
  if (value.size == 0 || value.size >= value.bytes.size() ||
      value.bytes[value.size] != '\0') {
    return false;
  }
  const auto view = PlayerPrisonerKeyViewV1(value);
  if (view.size() != value.size) return false;
  for (const char character : view) {
    if (!((character >= 'a' && character <= 'z') ||
          (character >= '0' && character <= '9') || character == '_')) {
      return false;
    }
  }
  return true;
}

bool ValidUnknownReason(UnknownReason reason) noexcept {
  return reason != UnknownReason::none;
}

bool ValidTypedKey(const PlayerPrisonerTypedKeyV1 &value) noexcept {
  if (value.state == FieldState::known) {
    return value.unknown_reason == UnknownReason::none &&
           ValidKey(value.value);
  }
  return value.state == FieldState::unknown &&
         ValidUnknownReason(value.unknown_reason) && EmptyKey(value.value);
}

Failure ValidateOpaqueFinalBool(
    const PlayerPrisonerOpaqueFinalBoolV1 &value) noexcept {
  if (value.state == FieldState::known) {
    if (value.source != NativeReasonSource::native_opaque_final) {
      return Failure::native_reason_source_invalid;
    }
    return value.unknown_reason == UnknownReason::none
               ? Failure::none
               : Failure::typed_value_invalid;
  }
  if (value.state != FieldState::unknown ||
      value.source != NativeReasonSource::unknown) {
    return Failure::native_reason_source_invalid;
  }
  return !value.value && ValidUnknownReason(value.unknown_reason)
             ? Failure::none
             : Failure::typed_value_invalid;
}

Failure ValidatePreview(
    const PlayerPrisonerInteractionPreviewV1 &preview) noexcept {
  if (!ValidTypedKey(preview.failure_reason_key)) {
    return Failure::typed_value_invalid;
  }
  if (preview.state == FieldState::unknown) {
    if (preview.source != PreviewSource::unknown) {
      return Failure::native_preview_source_invalid;
    }
    if (!ValidUnknownReason(preview.unknown_reason) || preview.shown ||
        preview.valid || preview.can_send ||
        preview.failure_reason_key.state != FieldState::unknown) {
      return Failure::preview_invariant_failed;
    }
    return Failure::none;
  }
  if (preview.state != FieldState::known ||
      preview.source !=
          PreviewSource::native_finalized_character_interaction) {
    return Failure::native_preview_source_invalid;
  }
  if (preview.unknown_reason != UnknownReason::none ||
      (preview.can_send && (!preview.shown || !preview.valid)) ||
      (!preview.shown && (preview.valid || preview.can_send))) {
    return Failure::preview_invariant_failed;
  }
  if (preview.can_send) {
    return preview.failure_reason_key.state == FieldState::unknown &&
                   preview.failure_reason_key.unknown_reason ==
                       UnknownReason::not_applicable
               ? Failure::none
               : Failure::preview_invariant_failed;
  }
  return preview.failure_reason_key.state == FieldState::known
             ? Failure::none
             : Failure::preview_invariant_failed;
}

Failure ValidateRansom(
    const PlayerPrisonerRansomPreviewV1 &preview) noexcept {
  const auto interaction_failure = ValidatePreview(preview.interaction);
  if (interaction_failure != Failure::none) return interaction_failure;
  if (!ValidTypedKey(preview.selected_option_key) ||
      !ValidTypedKey(preview.resource_key)) {
    return Failure::typed_value_invalid;
  }
  const auto acceptance_failure =
      ValidateOpaqueFinalBool(preview.would_accept_now);
  if (acceptance_failure != Failure::none) return acceptance_failure;

  if (preview.interaction.state == FieldState::unknown) {
    return preview.payer_character_id == -1 &&
                   preview.selected_option_key.state == FieldState::unknown &&
                   preview.resource_key.state == FieldState::unknown &&
                   preview.resource_amount_raw == 0 &&
                   !preview.acceptance_required &&
                   preview.would_accept_now.state == FieldState::unknown
               ? Failure::none
               : Failure::ransom_terms_invalid;
  }
  if (preview.payer_character_id <= 0 ||
      preview.selected_option_key.state != FieldState::known ||
      preview.resource_key.state != FieldState::known ||
      preview.resource_amount_raw < 0) {
    return Failure::ransom_terms_invalid;
  }
  if (preview.acceptance_required) {
    return preview.would_accept_now.state == FieldState::known
               ? Failure::none
               : Failure::ransom_terms_invalid;
  }
  return preview.would_accept_now.state == FieldState::unknown &&
                 preview.would_accept_now.unknown_reason ==
                     UnknownReason::not_applicable
             ? Failure::none
             : Failure::ransom_terms_invalid;
}

Failure ValidateRow(const PlayerPrisonerRowV1 &row,
                    std::int32_t expected_jailer) noexcept {
  if (row.prisoner_character_id <= 0 ||
      !row.prisoner_identity_round_trip ||
      row.prisoner_character_id == expected_jailer) {
    return Failure::prisoner_identity_invalid;
  }
  if (!row.prisoner_alive) return Failure::prisoner_not_alive;
  if (row.jailer_character_id != expected_jailer) {
    return Failure::jailer_identity_mismatch;
  }
  if (row.custody == PlayerPrisonerCustodyKindV1::unknown) {
    return Failure::custody_invalid;
  }
  if (row.time_imprisoned_days < 0) {
    return Failure::imprisonment_duration_invalid;
  }
  for (const auto *reason :
       {&row.has_imprisonment_reason, &row.has_banish_reason,
        &row.has_execute_reason}) {
    const auto failure = ValidateOpaqueFinalBool(*reason);
    if (failure != Failure::none) return failure;
  }
  auto failure = ValidateRansom(row.ransom);
  if (failure != Failure::none) return failure;
  for (const auto *preview :
       {&row.release_unconditional, &row.execute, &row.move_to_dungeon,
        &row.move_to_house_arrest, &row.torture}) {
    failure = ValidatePreview(*preview);
    if (failure != Failure::none) return failure;
  }
  return Failure::none;
}

Failure ValidateSample(const PlayerPrisonerSourceSampleV1 &sample,
                       std::int32_t expected_player) noexcept {
  if (!sample.source_read_complete) {
    return Failure::source_sample_incomplete;
  }
  if (!sample.played_character_identity_round_trip ||
      sample.played_character_id != expected_player) {
    return Failure::player_identity_mismatch;
  }
  if (!sample.prisoner_collection_complete) {
    return Failure::prisoner_collection_incomplete;
  }
  if (sample.prisoner_count > sample.prisoners.size() ||
      sample.total_prisoner_count != sample.prisoner_count) {
    return Failure::prisoner_count_invalid;
  }
  const auto count = static_cast<std::size_t>(sample.prisoner_count);
  for (std::size_t index = 0; index < count; ++index) {
    const auto failure =
        ValidateRow(sample.prisoners[index], expected_player);
    if (failure != Failure::none) return failure;
    for (std::size_t prior = 0; prior < index; ++prior) {
      if (sample.prisoners[prior].prisoner_character_id ==
          sample.prisoners[index].prisoner_character_id) {
        return Failure::duplicate_prisoner_identity;
      }
    }
  }
  return Failure::none;
}

Failure ValidateFrame(const PlayerPrisonerFrameV1 &frame) noexcept {
  if (!frame.paused) return Failure::not_paused;
  if (!frame.map_ready || frame.public_revision == 0 ||
      frame.native_revision == 0 || frame.proof_epoch == 0 ||
      frame.played_character_id <= 0 || !frame.played_character_alive ||
      !frame.played_character_identity_round_trip) {
    return Failure::played_character_unavailable;
  }
  return Failure::none;
}

void SetUnavailable(PlayerPrisonerManagementSnapshotV1 &output,
                    Failure failure) noexcept {
  output = {};
  output.status = PlayerPrisonerSnapshotStatusV1::unavailable;
  output.unavailable_reason = failure;
  output.played_character_id = -1;
}

bool OpaqueFinalKnown(
    const PlayerPrisonerOpaqueFinalBoolV1 &value) noexcept {
  return value.state == FieldState::known &&
         value.source == NativeReasonSource::native_opaque_final;
}

bool PreviewKnown(
    const PlayerPrisonerInteractionPreviewV1 &value) noexcept {
  return value.state == FieldState::known &&
         value.source ==
             PreviewSource::native_finalized_character_interaction;
}

bool RansomKnown(
    const PlayerPrisonerRansomPreviewV1 &value) noexcept {
  if (!PreviewKnown(value.interaction) ||
      value.selected_option_key.state != FieldState::known ||
      value.resource_key.state != FieldState::known ||
      value.payer_character_id <= 0) {
    return false;
  }
  return value.acceptance_required
             ? OpaqueFinalKnown(value.would_accept_now)
             : value.would_accept_now.state == FieldState::unknown &&
                   value.would_accept_now.unknown_reason ==
                       UnknownReason::not_applicable;
}

void ComputeReadiness(PlayerPrisonerManagementSnapshotV1 &output) noexcept {
  auto &readiness = output.readiness;
  readiness.collection_ready = true;
  readiness.same_frame_ready = true;
  readiness.crime_reasons_ready = true;
  readiness.ransom_previews_ready = true;
  readiness.release_previews_ready = true;
  readiness.punishment_legality_ready = true;

  const auto count = static_cast<std::size_t>(output.prisoner_count);
  for (std::size_t index = 0; index < count; ++index) {
    const auto &row = output.prisoners[index];
    readiness.crime_reasons_ready &=
        OpaqueFinalKnown(row.has_imprisonment_reason) &&
        OpaqueFinalKnown(row.has_banish_reason) &&
        OpaqueFinalKnown(row.has_execute_reason);
    readiness.ransom_previews_ready &= RansomKnown(row.ransom);
    readiness.ransom_candidate_available |=
        PreviewKnown(row.ransom.interaction) &&
        row.ransom.interaction.can_send &&
        (!row.ransom.acceptance_required ||
         (OpaqueFinalKnown(row.ransom.would_accept_now) &&
          row.ransom.would_accept_now.value));
    readiness.release_previews_ready &=
        PreviewKnown(row.release_unconditional);
    readiness.punishment_legality_ready &=
        PreviewKnown(row.execute) && PreviewKnown(row.move_to_dungeon) &&
        PreviewKnown(row.move_to_house_arrest) && PreviewKnown(row.torture);
  }
  readiness.semantic_ready =
      readiness.collection_ready && readiness.crime_reasons_ready &&
      readiness.ransom_previews_ready &&
      readiness.ransom_candidate_available &&
      readiness.release_previews_ready &&
      readiness.punishment_legality_ready && readiness.same_frame_ready;
}

} // namespace

static_assert(std::is_trivially_copyable_v<PlayerPrisonerSourceSampleV1>,
              "prisoner source sample must own value copies only");
static_assert(std::is_trivially_copyable_v<
                  PlayerPrisonerManagementSnapshotV1>,
              "prisoner snapshot must own value copies only");

bool AssignPlayerPrisonerKeyV1(
    std::string_view value, PlayerPrisonerKeyV1 &output) noexcept {
  output = {};
  if (value.empty() || value.size() >= output.bytes.size()) return false;
  for (const char character : value) {
    if (!((character >= 'a' && character <= 'z') ||
          (character >= '0' && character <= '9') || character == '_')) {
      return false;
    }
  }
  output.size = static_cast<std::uint16_t>(value.size());
  std::copy(value.begin(), value.end(), output.bytes.begin());
  return true;
}

std::string_view PlayerPrisonerKeyViewV1(
    const PlayerPrisonerKeyV1 &value) noexcept {
  if (value.size >= value.bytes.size() || value.bytes[value.size] != '\0') {
    return {};
  }
  return {value.bytes.data(), value.size};
}

PlayerPrisonerTypedKeyV1 PlayerPrisonerKnownKeyV1(
    std::string_view value) noexcept {
  PlayerPrisonerTypedKeyV1 output{};
  if (!AssignPlayerPrisonerKeyV1(value, output.value)) return output;
  output.state = FieldState::known;
  output.unknown_reason = UnknownReason::none;
  return output;
}

PlayerPrisonerTypedKeyV1 PlayerPrisonerUnknownKeyV1(
    PlayerPrisonerUnknownReasonV1 reason) noexcept {
  PlayerPrisonerTypedKeyV1 output{};
  output.unknown_reason =
      reason == UnknownReason::none ? UnknownReason::provider_unavailable
                                    : reason;
  return output;
}

bool ObservePlayerPrisonerManagementSnapshotV1(
    const PlayerPrisonerCaptureV1 &capture,
    PlayerPrisonerManagementSnapshotV1 &output) noexcept {
  SetUnavailable(output, Failure::source_adapter_unavailable);
  if (!capture.exact_build_admitted ||
      FixedView(capture.admitted_executable_sha256) !=
          kPlayerPrisonerManagementSnapshotV1ExecutableSha256) {
    SetUnavailable(output, Failure::exact_build_mismatch);
    return false;
  }
  if (!capture.source_adapter_bound) return false;
  if (!capture.application_main_thread) {
    SetUnavailable(output, Failure::application_main_thread_required);
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

  output = {};
  output.status = PlayerPrisonerSnapshotStatusV1::available;
  output.unavailable_reason = Failure::none;
  output.public_revision = capture.frame_before.public_revision;
  output.native_revision = capture.frame_before.native_revision;
  output.proof_epoch = capture.frame_before.proof_epoch;
  output.date_raw = capture.frame_before.date_raw;
  output.played_character_id =
      capture.frame_before.played_character_id;
  output.total_prisoner_count =
      capture.first_sample.total_prisoner_count;
  output.prisoner_count = capture.first_sample.prisoner_count;
  std::copy_n(capture.first_sample.prisoners.begin(),
              output.prisoner_count, output.prisoners.begin());
  std::sort(output.prisoners.begin(),
            output.prisoners.begin() + output.prisoner_count,
            [](const auto &left, const auto &right) {
              return left.prisoner_character_id <
                     right.prisoner_character_id;
            });
  output.religious_details_exposed = false;
  ComputeReadiness(output);
  return true;
}

std::string_view PlayerPrisonerSnapshotFailureNameV1(
    PlayerPrisonerSnapshotFailureV1 failure) noexcept {
  switch (failure) {
  case Failure::none: return "none";
  case Failure::exact_build_mismatch: return "exact_build_mismatch";
  case Failure::source_adapter_unavailable:
    return "source_adapter_unavailable";
  case Failure::application_main_thread_required:
    return "application_main_thread_required";
  case Failure::not_paused: return "not_paused";
  case Failure::frame_drift: return "frame_drift";
  case Failure::played_character_unavailable:
    return "played_character_unavailable";
  case Failure::source_sample_incomplete:
    return "source_sample_incomplete";
  case Failure::player_identity_mismatch:
    return "player_identity_mismatch";
  case Failure::prisoner_collection_incomplete:
    return "prisoner_collection_incomplete";
  case Failure::prisoner_count_invalid: return "prisoner_count_invalid";
  case Failure::source_sample_drift: return "source_sample_drift";
  case Failure::prisoner_identity_invalid:
    return "prisoner_identity_invalid";
  case Failure::duplicate_prisoner_identity:
    return "duplicate_prisoner_identity";
  case Failure::prisoner_not_alive: return "prisoner_not_alive";
  case Failure::jailer_identity_mismatch:
    return "jailer_identity_mismatch";
  case Failure::custody_invalid: return "custody_invalid";
  case Failure::imprisonment_duration_invalid:
    return "imprisonment_duration_invalid";
  case Failure::typed_value_invalid: return "typed_value_invalid";
  case Failure::native_reason_source_invalid:
    return "native_reason_source_invalid";
  case Failure::native_preview_source_invalid:
    return "native_preview_source_invalid";
  case Failure::preview_invariant_failed:
    return "preview_invariant_failed";
  case Failure::ransom_terms_invalid: return "ransom_terms_invalid";
  }
  return "unknown";
}

std::string_view PlayerPrisonerUnknownReasonNameV1(
    PlayerPrisonerUnknownReasonV1 reason) noexcept {
  switch (reason) {
  case UnknownReason::none: return "none";
  case UnknownReason::not_observed: return "not_observed";
  case UnknownReason::not_applicable: return "not_applicable";
  case UnknownReason::native_final_evaluator_unresolved:
    return "native_final_evaluator_unresolved";
  case UnknownReason::native_role_binding_unresolved:
    return "native_role_binding_unresolved";
  case UnknownReason::native_option_unresolved:
    return "native_option_unresolved";
  case UnknownReason::native_resource_term_unresolved:
    return "native_resource_term_unresolved";
  case UnknownReason::provider_unavailable: return "provider_unavailable";
  }
  return "unknown";
}

} // namespace xar::bridge
