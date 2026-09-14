#include "xar_bridge/realm_law_governance_source_adapter_v1.hpp"

#include <algorithm>
#include <array>
#include <cstring>
#include <memory>
#include <new>
#include <type_traits>

namespace xar::bridge {
namespace {

using CoreFailure = RealmLawGovernanceSnapshotV1Failure;
using Failure = RealmLawGovernanceSourceAdapterFailureV1;
using Result = RealmLawGovernanceSourceResultV1;

struct ResolvedLeaseV1 {
  RealmLawGovernanceSourcePlayerLeaseV1 player{};
  RealmLawGovernanceSourceContainerLeaseV1 container{};
};

struct GroupFingerprintV1 {
  std::uintptr_t native_address = 0;
  std::uint64_t identity = 0;
  std::uint64_t generation = 0;
  RealmLawGovernanceKeyV1 group_key{};
  std::size_t candidate_count = 0;

  friend bool operator==(const GroupFingerprintV1 &,
                         const GroupFingerprintV1 &) = default;
};

void Fail(Result &output, Failure failure,
          CoreFailure core_failure =
              CoreFailure::source_adapter_unavailable) noexcept {
  static_assert(std::is_trivially_copyable_v<Result>);
  std::memset(&output, 0, sizeof(output));
  output.failure = failure;
  output.core_failure = core_failure;
  output.snapshot.status = RealmLawGovernanceSnapshotV1Status::unavailable;
  output.snapshot.unavailable_reason = core_failure;
  output.snapshot.played_character_id = -1;
  output.snapshot.title_baseline.primary_title_presence =
      RealmLawGovernancePresenceV1::unknown;
  output.snapshot.title_baseline.primary_title_id = -1;
}

bool CallbacksComplete(
    const RealmLawGovernanceSourceAccessV1 &access) noexcept {
  return access.capture_frame != nullptr && access.resolve_player != nullptr &&
      access.resolve_container != nullptr && access.read_group != nullptr &&
      access.read_candidate != nullptr &&
      access.read_title_baseline != nullptr;
}

bool ValidFrame(const RealmLawGovernanceFrameV1 &frame) noexcept {
  return frame.public_revision != 0 && frame.native_revision != 0 &&
      frame.proof_epoch != 0 && frame.paused && frame.map_ready &&
      frame.played_character_id != -1 && frame.played_character_alive &&
      frame.played_character_identity_round_trip;
}

bool ValidPlayer(const RealmLawGovernanceSourcePlayerLeaseV1 &player,
                 std::int32_t expected_character_id) noexcept {
  return player.identity_round_trip && player.native_address != 0 &&
      player.character_id == expected_character_id;
}

bool SamePlayer(const RealmLawGovernanceSourcePlayerLeaseV1 &left,
                const RealmLawGovernanceSourcePlayerLeaseV1 &right) noexcept {
  return left.identity_round_trip == right.identity_round_trip &&
      left.native_address == right.native_address &&
      left.character_id == right.character_id;
}

bool ValidContainer(
    const RealmLawGovernanceSourceContainerLeaseV1 &container,
    std::int32_t expected_owner) noexcept {
  return container.identity_round_trip && container.native_address != 0 &&
      container.identity != 0 && container.generation != 0 &&
      container.owner_character_id == expected_owner;
}

bool SameContainer(
    const RealmLawGovernanceSourceContainerLeaseV1 &left,
    const RealmLawGovernanceSourceContainerLeaseV1 &right) noexcept {
  return left.identity_round_trip == right.identity_round_trip &&
      left.native_address == right.native_address &&
      left.identity == right.identity && left.generation == right.generation &&
      left.owner_character_id == right.owner_character_id &&
      left.group_count == right.group_count;
}

CoreFailure ResolveCoreFailure(Failure failure) noexcept {
  if (failure == Failure::player_unavailable) {
    return CoreFailure::player_identity_mismatch;
  }
  if (failure == Failure::group_count_invalid) {
    return CoreFailure::group_count_invalid;
  }
  return CoreFailure::source_adapter_unavailable;
}

bool ValidGroup(const RealmLawGovernanceSourceGroupLeaseV1 &group) noexcept {
  return group.identity_round_trip && group.native_address != 0 &&
      group.identity != 0 && group.generation != 0;
}

GroupFingerprintV1 Fingerprint(
    const RealmLawGovernanceSourceGroupLeaseV1 &group) noexcept {
  return {group.native_address, group.identity, group.generation,
          group.group_key, group.candidate_count};
}

bool ResolveLease(const RealmLawGovernanceSourceAccessV1 &access,
                  std::int32_t played_character_id,
                  ResolvedLeaseV1 &output, Failure &failure) noexcept {
  output = {};
  if (!access.resolve_player(access.context, played_character_id,
                             output.player) ||
      !ValidPlayer(output.player, played_character_id)) {
    failure = Failure::player_unavailable;
    return false;
  }
  if (!access.resolve_container(access.context, output.player,
                                output.container) ||
      !ValidContainer(output.container, played_character_id)) {
    failure = Failure::container_unavailable;
    return false;
  }
  if (output.container.group_count == 0 ||
      output.container.group_count > kRealmLawGovernanceMaximumGroupsV1) {
    failure = Failure::group_count_invalid;
    return false;
  }
  return true;
}

bool ReadSample(
    const RealmLawGovernanceSourceAccessV1 &access,
    const ResolvedLeaseV1 &lease,
    RealmLawGovernanceSourceSampleV1 &sample,
    std::array<GroupFingerprintV1,
               kRealmLawGovernanceMaximumGroupsV1> &fingerprints,
    bool require_matching_fingerprints, Failure &failure) noexcept {
  sample = {};
  sample.played_character_id = lease.player.character_id;
  sample.played_character_identity_round_trip =
      lease.player.identity_round_trip;
  sample.group_count = static_cast<std::uint32_t>(lease.container.group_count);

  for (std::size_t group_index = 0;
       group_index < lease.container.group_count; ++group_index) {
    RealmLawGovernanceSourceGroupLeaseV1 source_group{};
    if (!access.read_group(access.context, lease.player, lease.container,
                           group_index, source_group) ||
        !ValidGroup(source_group)) {
      failure = Failure::group_unavailable;
      return false;
    }
    const auto fingerprint = Fingerprint(source_group);
    if (require_matching_fingerprints) {
      if (fingerprints[group_index] != fingerprint) {
        failure = Failure::group_drift;
        return false;
      }
    } else {
      fingerprints[group_index] = fingerprint;
    }
    if (source_group.candidate_count == 0 ||
        source_group.candidate_count >
            kRealmLawGovernanceMaximumCandidatesV1) {
      failure = Failure::candidate_count_invalid;
      return false;
    }

    auto &group = sample.groups[group_index];
    group.group_key = source_group.group_key;
    group.active_law_key = source_group.active_law_key;
    group.can_change_evaluated = source_group.can_change_evaluated;
    group.can_change = source_group.can_change;
    group.candidate_count =
        static_cast<std::uint32_t>(source_group.candidate_count);
    for (std::size_t candidate_index = 0;
         candidate_index < source_group.candidate_count; ++candidate_index) {
      if (!access.read_candidate(
              access.context, lease.player, lease.container, source_group,
              candidate_index, group.candidates[candidate_index])) {
        failure = Failure::candidate_unavailable;
        return false;
      }
    }
    group.candidates_complete = true;
  }
  sample.groups_complete = true;

  if (!access.read_title_baseline(access.context, lease.player,
                                  sample.title_baseline)) {
    failure = Failure::title_baseline_unavailable;
    return false;
  }
  sample.title_baseline_complete = true;
  sample.source_read_complete = true;
  return true;
}

} // namespace

bool ObserveRealmLawGovernanceSourceV1(
    const RealmLawGovernanceSourceAccessV1 &access,
    RealmLawGovernanceSourceResultV1 &output) noexcept {
  Fail(output, Failure::callbacks_unavailable);
  if (!access.exact_build_admitted ||
      access.admitted_executable_sha256 !=
          kRealmLawGovernanceSnapshotV1ExecutableSha256) {
    Fail(output, Failure::exact_build_mismatch,
         CoreFailure::exact_build_mismatch);
    return false;
  }
  if (!CallbacksComplete(access)) return false;
  if (access.current_thread_id == 0 ||
      access.current_thread_id != access.application_main_thread_id) {
    Fail(output, Failure::application_main_thread_required,
         CoreFailure::application_main_thread_required);
    return false;
  }

  std::unique_ptr<RealmLawGovernanceCaptureV1> capture{
      new (std::nothrow) RealmLawGovernanceCaptureV1{}};
  if (!capture) {
    Fail(output, Failure::working_storage_unavailable);
    return false;
  }
  if (!access.capture_frame(access.context, capture->frame_before)) {
    Fail(output, Failure::frame_unavailable);
    return false;
  }
  if (!capture->frame_before.paused) {
    Fail(output, Failure::not_paused, CoreFailure::not_paused);
    return false;
  }
  if (!ValidFrame(capture->frame_before)) {
    Fail(output, Failure::frame_invalid,
         CoreFailure::played_character_unavailable);
    return false;
  }

  Failure failure = Failure::none;
  ResolvedLeaseV1 first_lease{};
  if (!ResolveLease(access, capture->frame_before.played_character_id,
                    first_lease, failure)) {
    Fail(output, failure, ResolveCoreFailure(failure));
    return false;
  }
  std::array<GroupFingerprintV1,
             kRealmLawGovernanceMaximumGroupsV1>
      group_fingerprints{};
  if (!ReadSample(access, first_lease, capture->first_sample,
                  group_fingerprints, false, failure)) {
    Fail(output, failure);
    return false;
  }

  // Resolve the player and law container again. No first-pass native address
  // is reused to locate the second sample.
  ResolvedLeaseV1 second_lease{};
  if (!ResolveLease(access, capture->frame_before.played_character_id,
                    second_lease, failure)) {
    Fail(output, failure, ResolveCoreFailure(failure));
    return false;
  }
  if (!SamePlayer(first_lease.player, second_lease.player)) {
    Fail(output, Failure::player_drift,
         CoreFailure::player_identity_mismatch);
    return false;
  }
  if (!SameContainer(first_lease.container, second_lease.container)) {
    Fail(output, Failure::container_drift,
         CoreFailure::source_sample_drift);
    return false;
  }
  if (!ReadSample(access, second_lease, capture->second_sample,
                  group_fingerprints, true, failure)) {
    Fail(output, failure,
         failure == Failure::group_drift
             ? CoreFailure::source_sample_drift
             : CoreFailure::source_adapter_unavailable);
    return false;
  }

  if (!access.capture_frame(access.context, capture->frame_after)) {
    Fail(output, Failure::frame_unavailable);
    return false;
  }
  if (!capture->frame_after.paused) {
    Fail(output, Failure::not_paused, CoreFailure::not_paused);
    return false;
  }
  if (capture->frame_before != capture->frame_after) {
    Fail(output, Failure::frame_drift, CoreFailure::frame_drift);
    return false;
  }

  capture->exact_build_admitted = true;
  std::copy(access.admitted_executable_sha256.begin(),
            access.admitted_executable_sha256.end(),
            capture->admitted_executable_sha256.begin());
  capture->source_adapter_bound = true;
  capture->application_main_thread = true;

  std::unique_ptr<RealmLawGovernanceSnapshotV1> snapshot{
      new (std::nothrow) RealmLawGovernanceSnapshotV1{}};
  if (!snapshot) {
    Fail(output, Failure::working_storage_unavailable);
    return false;
  }
  if (!ObserveRealmLawGovernanceSnapshotV1(*capture, *snapshot)) {
    const auto core_failure = snapshot->unavailable_reason;
    Fail(output,
         core_failure == CoreFailure::source_sample_drift
             ? Failure::source_sample_drift
             : Failure::core_rejected,
         core_failure);
    return false;
  }

  output.failure = Failure::none;
  output.core_failure = CoreFailure::none;
  output.snapshot = *snapshot;
  return true;
}

std::string_view RealmLawGovernanceSourceAdapterFailureNameV1(
    RealmLawGovernanceSourceAdapterFailureV1 failure) noexcept {
  switch (failure) {
  case Failure::none: return "none";
  case Failure::exact_build_mismatch: return "exact_build_mismatch";
  case Failure::callbacks_unavailable: return "callbacks_unavailable";
  case Failure::application_main_thread_required:
    return "application_main_thread_required";
  case Failure::frame_unavailable: return "frame_unavailable";
  case Failure::not_paused: return "not_paused";
  case Failure::frame_invalid: return "frame_invalid";
  case Failure::player_unavailable: return "player_unavailable";
  case Failure::player_drift: return "player_drift";
  case Failure::container_unavailable: return "container_unavailable";
  case Failure::container_drift: return "container_drift";
  case Failure::group_count_invalid: return "group_count_invalid";
  case Failure::group_unavailable: return "group_unavailable";
  case Failure::group_drift: return "group_drift";
  case Failure::candidate_count_invalid: return "candidate_count_invalid";
  case Failure::candidate_unavailable: return "candidate_unavailable";
  case Failure::title_baseline_unavailable:
    return "title_baseline_unavailable";
  case Failure::source_sample_drift: return "source_sample_drift";
  case Failure::frame_drift: return "frame_drift";
  case Failure::working_storage_unavailable:
    return "working_storage_unavailable";
  case Failure::core_rejected: return "core_rejected";
  }
  return "unknown";
}

} // namespace xar::bridge
