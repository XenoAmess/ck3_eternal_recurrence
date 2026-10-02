#pragma once

#include "xar_bridge/activity_feast_guest_candidate_v1.hpp"
#include "xar_bridge/activity_feast_guest_rule_provenance_v1.hpp"

#include <limits>

namespace xar::ck3_12002 {

// Internal Stage-5 leaf: the global first candidate can belong to another
// active invitation category. Use the actual close-family refresh rows and
// the existing requested-ID native reader, without toggling or inviting.
inline bridge::ActivityFeastGuestCandidateResultV1
SelectFeastOrdinaryCloseFamilyCandidateV1(
    const bridge::ActivityFeastGuestJoinEnvironmentV1 &environment,
    const bridge::ActivityPlannerDiagFrameV1 &expected,
    const bridge::ActivityGuestRuleProvenanceResultV1 &provenance,
    const bridge::ActivityFeastGuestCandidateResultV1 &first) noexcept {
  using bridge::ActivityFeastGuestCandidateStatusV1;
  if (provenance.status !=
      bridge::ActivityGuestRuleProvenanceStatusV1::observed)
    return first;
  for (std::uint32_t index = 0;
       index < provenance.filtered_rule_character_count; ++index) {
    const auto id = provenance.filtered_ids[index];
    if (id == 0 ||
        id > static_cast<std::uint32_t>((std::numeric_limits<std::int32_t>::max)()) ||
        id == static_cast<std::uint32_t>(expected.actor_character_id))
      continue;
    const auto candidate = id == static_cast<std::uint32_t>(first.character_id)
        ? first
        : bridge::ReadActivityFeastGuestCandidateV1(
              environment, expected, static_cast<std::int32_t>(id));
    if (candidate.status == ActivityFeastGuestCandidateStatusV1::target_not_filtered)
      continue;
    if (candidate.status != ActivityFeastGuestCandidateStatusV1::observed)
      return candidate;
    if (candidate.native_filtered && candidate.planner_join_raw > 0 &&
        candidate.travel_days >= 0 &&
        candidate.arrival_raw <= candidate.planned_start_raw)
      return candidate;
  }
  // Keep the actual global nonmember observation when this category has no
  // qualifying intersection. Its named membership stays false and holds.
  return first;
}

} // namespace xar::ck3_12002
