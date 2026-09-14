#include "xar_bridge/realm_law_governance_snapshot_v1.hpp"

#include <algorithm>

namespace xar::bridge {
namespace {

using Failure = RealmLawGovernanceSnapshotV1Failure;
using Presence = RealmLawGovernancePresenceV1;
using Snapshot = RealmLawGovernanceSnapshotV1;

template <std::size_t Size>
std::string_view FixedView(const std::array<char, Size> &value) noexcept {
  const auto end = std::find(value.begin(), value.end(), '\0');
  if (end == value.end()) return {};
  return {value.data(), static_cast<std::size_t>(end - value.begin())};
}

bool EmptyKey(const RealmLawGovernanceKeyV1 &value) noexcept {
  return value.size == 0 && value.bytes[0] == '\0';
}

bool ValidKey(const RealmLawGovernanceKeyV1 &value) noexcept {
  if (value.size == 0 || value.size >= value.bytes.size() ||
      value.bytes[value.size] != '\0') {
    return false;
  }
  const auto view = RealmLawGovernanceKeyViewV1(value);
  if (view.size() != value.size) return false;
  for (const char character : view) {
    if (!((character >= 'a' && character <= 'z') ||
          (character >= '0' && character <= '9') || character == '_')) {
      return false;
    }
  }
  return true;
}

bool KeyLess(const RealmLawGovernanceKeyV1 &left,
             const RealmLawGovernanceKeyV1 &right) noexcept {
  const auto left_view = RealmLawGovernanceKeyViewV1(left);
  const auto right_view = RealmLawGovernanceKeyViewV1(right);
  return std::lexicographical_compare(
      left_view.begin(), left_view.end(), right_view.begin(), right_view.end(),
      [](char left_byte, char right_byte) {
        return static_cast<unsigned char>(left_byte) <
            static_cast<unsigned char>(right_byte);
      });
}

bool ValidReason(const RealmLawGovernanceReasonV1 &reason,
                 Presence required) noexcept {
  if (reason.presence != required) return false;
  if (required == Presence::absent) {
    return reason.size == 0 && reason.bytes[0] == '\0';
  }
  if (required != Presence::present || reason.size == 0 ||
      reason.size >= reason.bytes.size() ||
      reason.bytes[reason.size] != '\0') {
    return false;
  }
  return RealmLawGovernanceReasonViewV1(reason).size() == reason.size;
}

bool ValidOptionalKey(
    const RealmLawGovernanceOptionalKeyV1 &value) noexcept {
  if (value.presence == Presence::absent) return EmptyKey(value.value);
  if (value.presence == Presence::present) return ValidKey(value.value);
  return false;
}

bool ValidOptionalShare(
    const RealmLawGovernanceOptionalFixedPointV1 &value) noexcept {
  if (value.presence == Presence::absent) return value.value_raw == 0;
  return value.presence == Presence::present && value.value_raw >= 0 &&
      value.value_raw <= kRealmLawGovernanceFixedPointOneV1;
}

Failure ValidateSuccessionShape(
    const RealmLawGovernanceSuccessionShapeV1 &shape) noexcept {
  if (shape.presence == Presence::absent) {
    if (!EmptyKey(shape.order_of_succession) ||
        shape.title_division.presence != Presence::absent ||
        !EmptyKey(shape.title_division.value) ||
        shape.traversal_order.presence != Presence::absent ||
        !EmptyKey(shape.traversal_order.value) ||
        shape.rank.presence != Presence::absent ||
        !EmptyKey(shape.rank.value) ||
        shape.primary_heir_minimum_share.presence != Presence::absent ||
        shape.primary_heir_minimum_share.value_raw != 0) {
      return Failure::succession_shape_invalid;
    }
    return Failure::none;
  }
  if (shape.presence != Presence::present ||
      !ValidKey(shape.order_of_succession) ||
      !ValidOptionalKey(shape.title_division) ||
      !ValidOptionalKey(shape.traversal_order) ||
      !ValidOptionalKey(shape.rank) ||
      !ValidOptionalShare(shape.primary_heir_minimum_share)) {
    return Failure::succession_shape_invalid;
  }
  return Failure::none;
}

Failure ValidateCosts(const RealmLawGovernanceCandidateV1 &candidate) noexcept {
  if (!candidate.costs_complete) return Failure::cost_collection_incomplete;
  if (candidate.cost_count > candidate.costs.size()) {
    return Failure::cost_collection_invalid;
  }
  for (std::uint32_t index = 0; index < candidate.cost_count; ++index) {
    const auto &cost = candidate.costs[index];
    if (!ValidKey(cost.currency_key)) return Failure::cost_key_invalid;
    if (cost.amount_raw < 0) return Failure::cost_value_invalid;
    for (std::uint32_t prior = 0; prior < index; ++prior) {
      if (candidate.costs[prior].currency_key == cost.currency_key) {
        return Failure::duplicate_cost_key;
      }
    }
  }
  return Failure::none;
}

Failure ValidateCandidate(
    const RealmLawGovernanceCandidateV1 &candidate) noexcept {
  if (!ValidKey(candidate.law_key)) return Failure::candidate_key_invalid;
  if (!candidate.evaluation_complete) {
    return Failure::candidate_evaluation_incomplete;
  }
  if ((candidate.can_enact &&
       (!candidate.can_have || !candidate.can_pass || candidate.is_active)) ||
      (!candidate.can_have && candidate.can_pass) ||
      (!candidate.can_pass && candidate.can_enact)) {
    return Failure::candidate_legality_invariant_failed;
  }
  if (!ValidReason(candidate.blocked_reason,
                   candidate.can_enact ? Presence::absent
                                       : Presence::present)) {
    return Failure::candidate_reason_invariant_failed;
  }
  const auto cost_failure = ValidateCosts(candidate);
  if (cost_failure != Failure::none) return cost_failure;
  return ValidateSuccessionShape(candidate.succession);
}

Failure ValidateGroup(const RealmLawGovernanceGroupV1 &group) noexcept {
  if (!ValidKey(group.group_key)) return Failure::group_key_invalid;
  if (!ValidKey(group.active_law_key)) {
    return Failure::active_law_key_invalid;
  }
  if (!group.can_change_evaluated) {
    return Failure::candidate_evaluation_incomplete;
  }
  if (!group.candidates_complete) {
    return Failure::candidate_enumeration_incomplete;
  }
  if (group.candidate_count == 0 ||
      group.candidate_count > group.candidates.size()) {
    return Failure::candidate_count_invalid;
  }
  std::uint32_t active_count = 0;
  for (std::uint32_t index = 0; index < group.candidate_count; ++index) {
    const auto &candidate = group.candidates[index];
    const auto failure = ValidateCandidate(candidate);
    if (failure != Failure::none) return failure;
    if (candidate.is_active) {
      ++active_count;
      if (candidate.law_key != group.active_law_key) {
        return Failure::active_law_mismatch;
      }
    }
    if (!group.can_change && candidate.can_enact) {
      return Failure::candidate_legality_invariant_failed;
    }
    for (std::uint32_t prior = 0; prior < index; ++prior) {
      if (group.candidates[prior].law_key == candidate.law_key) {
        return Failure::duplicate_candidate_key;
      }
    }
  }
  return active_count == 1 ? Failure::none : Failure::active_law_mismatch;
}

Failure ValidateSuccessors(
    const std::array<std::int32_t,
                     kRealmLawGovernanceMaximumSuccessorsV1> &successors,
    std::uint32_t count) noexcept {
  if (count > successors.size()) {
    return Failure::successor_collection_invalid;
  }
  for (std::uint32_t index = 0; index < count; ++index) {
    if (successors[index] == -1) {
      return Failure::successor_collection_invalid;
    }
    for (std::uint32_t prior = 0; prior < index; ++prior) {
      if (successors[prior] == successors[index]) {
        return Failure::duplicate_successor_identity;
      }
    }
  }
  return Failure::none;
}

Failure ValidateTitleBaseline(
    const RealmLawGovernanceTitleBaselineV1 &baseline) noexcept {
  if (baseline.primary_title_presence == Presence::absent) {
    return baseline.primary_title_id == -1 &&
            baseline.primary_title_successor_count == 0 &&
            baseline.held_title_count == 0
        ? Failure::none
        : Failure::title_baseline_invalid;
  }
  if (baseline.primary_title_presence != Presence::present ||
      baseline.primary_title_id == -1 ||
      baseline.held_title_count == 0 ||
      baseline.held_title_count > baseline.held_titles.size()) {
    return Failure::title_baseline_invalid;
  }
  auto failure = ValidateSuccessors(
      baseline.primary_title_successor_character_ids,
      baseline.primary_title_successor_count);
  if (failure != Failure::none) return failure;

  std::uint32_t primary_count = 0;
  for (std::uint32_t index = 0; index < baseline.held_title_count; ++index) {
    const auto &title = baseline.held_titles[index];
    if (title.title_id == -1) return Failure::title_baseline_invalid;
    for (std::uint32_t prior = 0; prior < index; ++prior) {
      if (baseline.held_titles[prior].title_id == title.title_id) {
        return Failure::duplicate_title_identity;
      }
    }
    failure = ValidateSuccessors(title.successor_character_ids,
                                 title.successor_count);
    if (failure != Failure::none) return failure;
    if (title.primary) {
      ++primary_count;
      if (title.title_id != baseline.primary_title_id ||
          title.successor_count != baseline.primary_title_successor_count ||
          !std::equal(
              title.successor_character_ids.begin(),
              title.successor_character_ids.begin() + title.successor_count,
              baseline.primary_title_successor_character_ids.begin())) {
        return Failure::title_baseline_invalid;
      }
    } else if (title.title_id == baseline.primary_title_id) {
      return Failure::title_baseline_invalid;
    }
  }
  return primary_count == 1 ? Failure::none
                            : Failure::title_baseline_invalid;
}

Failure ValidateSample(const RealmLawGovernanceSourceSampleV1 &sample,
                       std::int32_t expected_player) noexcept {
  if (!sample.source_read_complete) return Failure::source_sample_incomplete;
  if (!sample.played_character_identity_round_trip ||
      sample.played_character_id != expected_player) {
    return Failure::player_identity_mismatch;
  }
  if (!sample.groups_complete) {
    return Failure::group_enumeration_incomplete;
  }
  if (sample.group_count == 0 || sample.group_count > sample.groups.size()) {
    return Failure::group_count_invalid;
  }
  for (std::uint32_t index = 0; index < sample.group_count; ++index) {
    const auto failure = ValidateGroup(sample.groups[index]);
    if (failure != Failure::none) return failure;
    for (std::uint32_t prior = 0; prior < index; ++prior) {
      if (sample.groups[prior].group_key == sample.groups[index].group_key) {
        return Failure::duplicate_group_key;
      }
    }
  }
  if (!sample.title_baseline_complete) {
    return Failure::title_baseline_incomplete;
  }
  return ValidateTitleBaseline(sample.title_baseline);
}

Failure ValidateFrame(const RealmLawGovernanceFrameV1 &frame) noexcept {
  if (!frame.paused) return Failure::not_paused;
  if (!frame.map_ready || frame.played_character_id == -1 ||
      !frame.played_character_alive ||
      !frame.played_character_identity_round_trip) {
    return Failure::played_character_unavailable;
  }
  return Failure::none;
}

void SetUnavailable(Snapshot &output, Failure failure) noexcept {
  output = {};
  output.status = RealmLawGovernanceSnapshotV1Status::unavailable;
  output.unavailable_reason = failure;
}

void Normalize(Snapshot &output) noexcept {
  for (std::uint32_t group_index = 0; group_index < output.group_count;
       ++group_index) {
    auto &group = output.groups[group_index];
    for (std::uint32_t candidate_index = 0;
         candidate_index < group.candidate_count; ++candidate_index) {
      auto &candidate = group.candidates[candidate_index];
      std::sort(candidate.costs.begin(),
                candidate.costs.begin() + candidate.cost_count,
                [](const auto &left, const auto &right) {
                  return KeyLess(left.currency_key, right.currency_key);
                });
    }
    std::sort(group.candidates.begin(),
              group.candidates.begin() + group.candidate_count,
              [](const auto &left, const auto &right) {
                return KeyLess(left.law_key, right.law_key);
              });
  }
  std::sort(output.groups.begin(), output.groups.begin() + output.group_count,
            [](const auto &left, const auto &right) {
              return KeyLess(left.group_key, right.group_key);
            });
  auto &baseline = output.title_baseline;
  for (std::uint32_t index = 0; index < baseline.held_title_count; ++index) {
    auto &title = baseline.held_titles[index];
    std::sort(title.successor_character_ids.begin(),
              title.successor_character_ids.begin() + title.successor_count);
  }
  std::sort(baseline.primary_title_successor_character_ids.begin(),
            baseline.primary_title_successor_character_ids.begin() +
                baseline.primary_title_successor_count);
  std::sort(baseline.held_titles.begin(),
            baseline.held_titles.begin() + baseline.held_title_count,
            [](const auto &left, const auto &right) {
              return left.title_id < right.title_id;
            });
}

} // namespace

bool AssignRealmLawGovernanceKeyV1(
    std::string_view value, RealmLawGovernanceKeyV1 &output) noexcept {
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

std::string_view RealmLawGovernanceKeyViewV1(
    const RealmLawGovernanceKeyV1 &value) noexcept {
  if (value.size >= value.bytes.size() || value.bytes[value.size] != '\0') {
    return {};
  }
  return {value.bytes.data(), value.size};
}

bool AssignRealmLawGovernanceReasonV1(
    std::string_view value, RealmLawGovernanceReasonV1 &output) noexcept {
  output = {};
  if (value.empty() || value.size() >= output.bytes.size()) return false;
  output.presence = Presence::present;
  output.size = static_cast<std::uint16_t>(value.size());
  std::copy(value.begin(), value.end(), output.bytes.begin());
  return true;
}

std::string_view RealmLawGovernanceReasonViewV1(
    const RealmLawGovernanceReasonV1 &value) noexcept {
  if (value.presence != Presence::present || value.size == 0 ||
      value.size >= value.bytes.size() || value.bytes[value.size] != '\0') {
    return {};
  }
  return {value.bytes.data(), value.size};
}

bool ObserveRealmLawGovernanceSnapshotV1(
    const RealmLawGovernanceCaptureV1 &capture,
    RealmLawGovernanceSnapshotV1 &output) noexcept {
  SetUnavailable(output, Failure::source_adapter_unavailable);
  if (!capture.exact_build_admitted ||
      FixedView(capture.admitted_executable_sha256) !=
          kRealmLawGovernanceSnapshotV1ExecutableSha256) {
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
  output.status = RealmLawGovernanceSnapshotV1Status::available;
  output.unavailable_reason = Failure::none;
  output.public_revision = capture.frame_before.public_revision;
  output.native_revision = capture.frame_before.native_revision;
  output.proof_epoch = capture.frame_before.proof_epoch;
  output.date_raw = capture.frame_before.date_raw;
  output.played_character_id = capture.frame_before.played_character_id;
  output.group_count = capture.first_sample.group_count;
  output.groups = capture.first_sample.groups;
  output.title_baseline = capture.first_sample.title_baseline;
  Normalize(output);
  output.readiness.groups_ready = true;
  output.readiness.engine_final_legality_ready = true;
  output.readiness.engine_final_costs_ready = true;
  output.readiness.succession_shapes_ready = true;
  output.readiness.title_successor_baseline_ready = true;
  output.readiness.same_frame_ready = true;
  return true;
}

std::string_view RealmLawGovernanceSnapshotV1FailureName(
    RealmLawGovernanceSnapshotV1Failure failure) noexcept {
  switch (failure) {
  case Failure::none: return "none";
  case Failure::exact_build_mismatch: return "exact_build_mismatch";
  case Failure::source_adapter_unavailable: return "source_adapter_unavailable";
  case Failure::application_main_thread_required:
    return "application_main_thread_required";
  case Failure::not_paused: return "not_paused";
  case Failure::frame_drift: return "frame_drift";
  case Failure::played_character_unavailable:
    return "played_character_unavailable";
  case Failure::source_sample_incomplete: return "source_sample_incomplete";
  case Failure::player_identity_mismatch: return "player_identity_mismatch";
  case Failure::source_sample_drift: return "source_sample_drift";
  case Failure::group_enumeration_incomplete:
    return "group_enumeration_incomplete";
  case Failure::group_count_invalid: return "group_count_invalid";
  case Failure::group_key_invalid: return "group_key_invalid";
  case Failure::duplicate_group_key: return "duplicate_group_key";
  case Failure::active_law_key_invalid: return "active_law_key_invalid";
  case Failure::candidate_enumeration_incomplete:
    return "candidate_enumeration_incomplete";
  case Failure::candidate_count_invalid: return "candidate_count_invalid";
  case Failure::candidate_key_invalid: return "candidate_key_invalid";
  case Failure::duplicate_candidate_key: return "duplicate_candidate_key";
  case Failure::active_law_mismatch: return "active_law_mismatch";
  case Failure::candidate_evaluation_incomplete:
    return "candidate_evaluation_incomplete";
  case Failure::candidate_legality_invariant_failed:
    return "candidate_legality_invariant_failed";
  case Failure::candidate_reason_invariant_failed:
    return "candidate_reason_invariant_failed";
  case Failure::cost_collection_incomplete:
    return "cost_collection_incomplete";
  case Failure::cost_collection_invalid: return "cost_collection_invalid";
  case Failure::cost_key_invalid: return "cost_key_invalid";
  case Failure::duplicate_cost_key: return "duplicate_cost_key";
  case Failure::cost_value_invalid: return "cost_value_invalid";
  case Failure::succession_shape_invalid: return "succession_shape_invalid";
  case Failure::title_baseline_incomplete:
    return "title_baseline_incomplete";
  case Failure::title_baseline_invalid: return "title_baseline_invalid";
  case Failure::duplicate_title_identity: return "duplicate_title_identity";
  case Failure::successor_collection_invalid:
    return "successor_collection_invalid";
  case Failure::duplicate_successor_identity:
    return "duplicate_successor_identity";
  }
  return "unknown";
}

} // namespace xar::bridge
