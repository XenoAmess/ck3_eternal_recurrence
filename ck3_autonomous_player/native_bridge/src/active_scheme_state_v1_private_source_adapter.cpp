#include "xar_bridge/active_scheme_state_v1_private_source_adapter.hpp"

namespace xar::bridge {
namespace {

using Failure = ActiveSchemeStateV1PrivateSourceFailure;
using Result = ActiveSchemeStateV1PrivateSourceResult;
using Row = ActiveSchemeStateV1PrivateCapturedRow;
using Value = ActiveSchemeStateV1PrivateValue<std::int32_t>;

void Fail(Result &output, Failure failure,
          ActiveSchemeStateV1PrivateFailure core_failure =
              ActiveSchemeStateV1PrivateFailure::
                  source_adapter_unavailable) noexcept {
  output = {};
  output.failure = failure;
  output.core_failure = core_failure;
  output.observation.status = ActiveSchemeStateV1PrivateStatus::unavailable;
  output.observation.unavailable_reason = core_failure;
}

bool CallbacksComplete(
    const ActiveSchemeStateV1PrivateSourceAccess &access) noexcept {
  return access.capture_frame != nullptr && access.resolve_root != nullptr &&
         access.resolve_container != nullptr && access.read_row != nullptr;
}

bool ValidRoot(
    const ActiveSchemeStateV1PrivateSourceRoot &root) noexcept {
  return root.identity_round_trip && root.native_address != 0 &&
         root.identity != 0 && root.generation != 0;
}

bool SameRoot(const ActiveSchemeStateV1PrivateSourceRoot &left,
              const ActiveSchemeStateV1PrivateSourceRoot &right) noexcept {
  return left.identity_round_trip == right.identity_round_trip &&
         left.native_address == right.native_address &&
         left.identity == right.identity &&
         left.generation == right.generation;
}

bool ValidContainer(
    const ActiveSchemeStateV1PrivateSourceContainer &container,
    std::int64_t played_character_id) noexcept {
  return container.identity_round_trip && container.native_address != 0 &&
         container.identity != 0 && container.generation != 0 &&
         container.owner_character_id == played_character_id;
}

bool SameContainer(
    const ActiveSchemeStateV1PrivateSourceContainer &left,
    const ActiveSchemeStateV1PrivateSourceContainer &right) noexcept {
  return left.identity_round_trip == right.identity_round_trip &&
         left.native_address == right.native_address &&
         left.identity == right.identity &&
         left.generation == right.generation &&
         left.owner_character_id == right.owner_character_id &&
         left.row_count == right.row_count;
}

bool SameFrame(const ActiveSchemeStateV1PrivateSourceFrame &left,
               const ActiveSchemeStateV1PrivateSourceFrame &right) noexcept {
  return left.capture_epoch == right.capture_epoch &&
         left.date_raw == right.date_raw &&
         left.played_character_id == right.played_character_id &&
         left.paused == right.paused;
}

bool SameValue(const Value &left, const Value &right) noexcept {
  return left.status == right.status && left.value == right.value;
}

bool SameRow(const Row &left, const Row &right) noexcept {
  return left.scheme_identity_round_trip ==
             right.scheme_identity_round_trip &&
         left.scheme_instance_id == right.scheme_instance_id &&
         left.scheme_instance_generation ==
             right.scheme_instance_generation &&
         left.owner_character_id == right.owner_character_id &&
         left.scheme_type_key == right.scheme_type_key &&
         left.category_key == right.category_key &&
         left.target_identity_round_trip ==
             right.target_identity_round_trip &&
         left.target_kind == right.target_kind &&
         left.target_id == right.target_id &&
         left.definition_flags_verified ==
             right.definition_flags_verified &&
         left.is_basic == right.is_basic &&
         left.is_secret == right.is_secret &&
         left.is_exposed == right.is_exposed &&
         left.is_frozen == right.is_frozen &&
         SameValue(left.progress, right.progress) &&
         SameValue(left.progress_goal, right.progress_goal) &&
         SameValue(left.success_chance, right.success_chance) &&
         SameValue(left.maximum_success_chance,
                   right.maximum_success_chance) &&
         SameValue(left.secrecy, right.secrecy) &&
         SameValue(left.opportunity_charges, right.opportunity_charges) &&
         SameValue(left.breaches, right.breaches) &&
         SameValue(left.maximum_breaches, right.maximum_breaches) &&
         SameValue(left.phases_remaining_until_opportunity,
                   right.phases_remaining_until_opportunity);
}

} // namespace

bool ObserveActiveSchemeStateV1PrivateSource(
    const ActiveSchemeStateV1PrivateSourceAccess &access,
    ActiveSchemeStateV1PrivateSourceResult &output) noexcept {
  Fail(output, Failure::callbacks_unavailable);
  if (!access.exact_build_admitted ||
      access.admitted_executable_sha256 !=
          kActiveSchemeStateV1PrivateObserverExecutableSha256) {
    Fail(output, Failure::exact_build_mismatch,
         ActiveSchemeStateV1PrivateFailure::exact_build_mismatch);
    return false;
  }
  if (!CallbacksComplete(access)) return false;
  if (access.current_thread_id == 0 ||
      access.current_thread_id != access.application_main_thread_id) {
    Fail(output, Failure::not_application_main_thread,
         ActiveSchemeStateV1PrivateFailure::not_application_main_thread);
    return false;
  }

  ActiveSchemeStateV1PrivateSourceFrame frame_before{};
  if (!access.capture_frame(access.context, frame_before)) {
    Fail(output, Failure::frame_unavailable);
    return false;
  }
  if (!frame_before.paused) {
    Fail(output, Failure::not_paused,
         ActiveSchemeStateV1PrivateFailure::not_paused);
    return false;
  }
  if (frame_before.capture_epoch == 0 ||
      frame_before.played_character_id <= 0) {
    Fail(output, Failure::frame_invalid,
         ActiveSchemeStateV1PrivateFailure::played_character_unavailable);
    return false;
  }

  ActiveSchemeStateV1PrivateSourceRoot root_before{};
  if (!access.resolve_root(access.context, frame_before.played_character_id,
                           root_before) ||
      !ValidRoot(root_before)) {
    Fail(output, Failure::root_unavailable);
    return false;
  }
  ActiveSchemeStateV1PrivateSourceContainer container_before{};
  if (!access.resolve_container(access.context, root_before,
                                frame_before.played_character_id,
                                container_before) ||
      !ValidContainer(container_before,
                      frame_before.played_character_id)) {
    Fail(output, Failure::container_unavailable,
         ActiveSchemeStateV1PrivateFailure::container_identity_unavailable);
    return false;
  }
  if (container_before.row_count >
      kActiveSchemeStateV1PrivateMaximumRows) {
    Fail(output, Failure::row_count_invalid,
         ActiveSchemeStateV1PrivateFailure::row_count_invalid);
    return false;
  }

  ActiveSchemeStateV1PrivateCapture capture{};
  for (std::size_t index = 0; index < container_before.row_count; ++index) {
    if (!access.read_row(access.context, root_before, container_before,
                         index, capture.rows[index])) {
      Fail(output, Failure::row_unavailable,
           ActiveSchemeStateV1PrivateFailure::enumeration_incomplete);
      return false;
    }
  }

  // Re-resolve both native leases instead of reusing the prior addresses.
  ActiveSchemeStateV1PrivateSourceRoot root_after{};
  if (!access.resolve_root(access.context, frame_before.played_character_id,
                           root_after) ||
      !ValidRoot(root_after)) {
    Fail(output, Failure::root_unavailable);
    return false;
  }
  if (!SameRoot(root_before, root_after)) {
    Fail(output, Failure::root_drift,
         ActiveSchemeStateV1PrivateFailure::container_drift);
    return false;
  }

  ActiveSchemeStateV1PrivateSourceContainer container_after{};
  if (!access.resolve_container(access.context, root_after,
                                frame_before.played_character_id,
                                container_after) ||
      !ValidContainer(container_after,
                      frame_before.played_character_id)) {
    Fail(output, Failure::container_unavailable,
         ActiveSchemeStateV1PrivateFailure::container_identity_unavailable);
    return false;
  }
  if (!SameContainer(container_before, container_after)) {
    Fail(output, Failure::container_drift,
         ActiveSchemeStateV1PrivateFailure::container_drift);
    return false;
  }

  for (std::size_t index = 0; index < container_after.row_count; ++index) {
    ActiveSchemeStateV1PrivateCapturedRow repeated{};
    if (!access.read_row(access.context, root_after, container_after, index,
                         repeated)) {
      Fail(output, Failure::row_unavailable,
           ActiveSchemeStateV1PrivateFailure::enumeration_incomplete);
      return false;
    }
    if (!SameRow(capture.rows[index], repeated)) {
      Fail(output, Failure::row_drift,
           ActiveSchemeStateV1PrivateFailure::scheme_identity_unavailable);
      return false;
    }
  }

  ActiveSchemeStateV1PrivateSourceFrame frame_after{};
  if (!access.capture_frame(access.context, frame_after)) {
    Fail(output, Failure::frame_unavailable);
    return false;
  }
  if (!frame_after.paused) {
    Fail(output, Failure::not_paused,
         ActiveSchemeStateV1PrivateFailure::not_paused);
    return false;
  }
  if (!SameFrame(frame_before, frame_after)) {
    Fail(output, Failure::frame_drift,
         ActiveSchemeStateV1PrivateFailure::frame_drift);
    return false;
  }

  capture.exact_build_admitted = access.exact_build_admitted;
  capture.admitted_executable_sha256 =
      access.admitted_executable_sha256;
  capture.source_adapter_bound = true;
  capture.application_main_thread = true;
  capture.paused = true;
  capture.capture_epoch_before = frame_before.capture_epoch;
  capture.capture_epoch_after = frame_after.capture_epoch;
  capture.date_raw_before = frame_before.date_raw;
  capture.date_raw_after = frame_after.date_raw;
  capture.played_character_id_before = frame_before.played_character_id;
  capture.played_character_id_after = frame_after.played_character_id;
  capture.container_identity_round_trip =
      container_before.identity_round_trip &&
      container_after.identity_round_trip;
  capture.container_identity_before = container_before.identity;
  capture.container_identity_after = container_after.identity;
  capture.container_generation_before = container_before.generation;
  capture.container_generation_after = container_after.generation;
  capture.row_count_before = container_before.row_count;
  capture.row_count_after = container_after.row_count;
  capture.enumeration_complete = true;

  ActiveSchemeStateV1PrivateObservation observation{};
  if (!ObserveActiveSchemeStateV1Private(capture, observation)) {
    const auto core_failure = observation.unavailable_reason;
    Fail(output, Failure::core_rejected, core_failure);
    return false;
  }

  output = {};
  output.failure = Failure::none;
  output.core_failure = ActiveSchemeStateV1PrivateFailure::none;
  output.observation = observation;
  return true;
}

std::string_view ActiveSchemeStateV1PrivateSourceFailureName(
    ActiveSchemeStateV1PrivateSourceFailure failure) noexcept {
  switch (failure) {
  case Failure::none: return "none";
  case Failure::exact_build_mismatch: return "exact_build_mismatch";
  case Failure::callbacks_unavailable: return "callbacks_unavailable";
  case Failure::not_application_main_thread:
    return "not_application_main_thread";
  case Failure::frame_unavailable: return "frame_unavailable";
  case Failure::not_paused: return "not_paused";
  case Failure::frame_invalid: return "frame_invalid";
  case Failure::root_unavailable: return "root_unavailable";
  case Failure::container_unavailable: return "container_unavailable";
  case Failure::row_count_invalid: return "row_count_invalid";
  case Failure::row_unavailable: return "row_unavailable";
  case Failure::root_drift: return "root_drift";
  case Failure::container_drift: return "container_drift";
  case Failure::row_drift: return "row_drift";
  case Failure::frame_drift: return "frame_drift";
  case Failure::core_rejected: return "core_rejected";
  }
  return "unknown";
}

} // namespace xar::bridge
