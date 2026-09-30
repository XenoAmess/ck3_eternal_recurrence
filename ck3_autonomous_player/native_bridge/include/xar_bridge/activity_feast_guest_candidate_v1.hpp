#pragma once

#include "xar_bridge/activity_stage5_feast_guest_join_v1.hpp"

#include <cstdint>
#include <string_view>

namespace xar::bridge {

// One candidate from the current native-filtered planner groups. This is a
// read-only pre-invitation prediction, never an accepted guest or Start gate.
enum class ActivityFeastGuestCandidateStatusV1 {
  observed,
  no_qualified_candidate,
  target_not_filtered,
  exact_build_rejected,
  frame_changed,
  planner_unavailable,
  no_normal_refresh,
  candidate_source_unavailable,
  native_evaluation_failed,
  arrival_unavailable,
  configuration_changed,
};

struct ActivityFeastGuestCandidateResultV1 {
  ActivityFeastGuestCandidateStatusV1 status =
      ActivityFeastGuestCandidateStatusV1::exact_build_rejected;
  ActivityPlannerDiagFrameV1 frame{};
  std::uint64_t normal_refresh_sequence = 0;
  std::uint64_t source_fingerprint = 0;
  std::int32_t active_rule_count = 0;
  std::int32_t filtered_group_count = 0;
  std::int32_t selected_row_count = 0;
  bool native_filtered = false;
  bool selected_member = false;
  std::int32_t character_id = -1;
  std::int64_t planner_join_raw = 0;
  std::int32_t travel_days = 0;
  std::int32_t arrival_raw = 0;
  std::int32_t planned_start_raw = 0;

  friend bool operator==(const ActivityFeastGuestCandidateResultV1 &,
                         const ActivityFeastGuestCandidateResultV1 &) = default;
};

ActivityFeastGuestCandidateResultV1 ReadActivityFeastGuestCandidateV1(
    const ActivityFeastGuestJoinEnvironmentV1 &environment,
    const ActivityPlannerDiagFrameV1 &expected,
    std::int32_t target_character_id = 0) noexcept;

std::string_view ActivityFeastGuestCandidateStatusKeyV1(
    ActivityFeastGuestCandidateStatusV1 status) noexcept;

} // namespace xar::bridge
