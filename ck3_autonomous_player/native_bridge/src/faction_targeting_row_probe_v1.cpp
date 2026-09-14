#include "xar_bridge/faction_targeting_row_probe_v1.hpp"

#include <algorithm>

namespace xar::bridge {
namespace {

bool SameBinding(const FactionTargetingRowObservationDiagnosticsV1 &capture,
                 const FactionTargetingRowProbeBindingV1 &required) noexcept {
  return capture.last_proof_epoch == required.proof_epoch &&
      capture.last_snapshot_revision == required.snapshot_revision &&
      capture.last_date_raw == required.date_raw &&
      capture.last_player_character_id == required.player_character_id;
}

bool CaptureShapeIsValid(
    const FactionTargetingRowObservationDiagnosticsV1 &capture) noexcept {
  if (capture.last_faction_count >
          kFactionTargetingRowObserverMaximumRowsV1 ||
      capture.last_campaign_root_targeting_faction_count < 0 ||
      static_cast<std::uint32_t>(
          capture.last_campaign_root_targeting_faction_count) !=
          capture.last_faction_count) {
    return false;
  }

  std::uint32_t prior_faction_id = 0;
  for (std::size_t faction_index = 0;
       faction_index < capture.last_faction_count; ++faction_index) {
    const auto faction_id = capture.last_faction_ids[faction_index];
    const auto target_character_id =
        capture.last_target_character_ids[faction_index];
    const auto leader_present = capture.last_leader_present[faction_index];
    const auto leader_character_id =
        capture.last_leader_character_ids[faction_index];
    const auto leader_in_members =
        capture.last_leader_present_in_character_members[faction_index];
    const auto member_count =
        capture.last_character_member_counts[faction_index];
    if (faction_id == 0 ||
        (faction_index != 0 && faction_id <= prior_faction_id) ||
        target_character_id == 0 ||
        target_character_id != capture.last_player_character_id ||
        leader_present > 1 || leader_in_members > 1 ||
        (leader_present == 0 &&
         (leader_character_id != 0 || leader_in_members != 0)) ||
        (leader_present != 0 && leader_character_id == 0) ||
        member_count >
            kFactionTargetingRowObserverMaximumCharacterMembersPerFactionV1) {
      return false;
    }

    const auto member_base =
        faction_index *
        kFactionTargetingRowObserverMaximumCharacterMembersPerFactionV1;
    const auto first = capture.last_character_member_ids.begin() +
        member_base;
    const auto last = first + member_count;
    if (std::find(first, last, 0U) != last ||
        !std::is_sorted(first, last) ||
        std::adjacent_find(first, last) != last) {
      return false;
    }
    const bool derived_leader_in_members = leader_present != 0 &&
        std::binary_search(first, last, leader_character_id);
    if (derived_leader_in_members != (leader_in_members != 0)) {
      return false;
    }
    prior_faction_id = faction_id;
  }
  return true;
}

} // namespace

FactionTargetingRowProbeResultV1 ProbeFactionTargetingRowsV1(
    const FactionTargetingRowObserverDiagnosticsV1 &observer,
    const FactionTargetingRowProbeBindingV1 &required_binding) noexcept {
  FactionTargetingRowProbeResultV1 result{};
  result.observer_failure_flags = observer.failure_flags;
  result.published_generation = observer.observation.published_generation;
  result.required_binding = required_binding;
  result.observed_binding = {
      result.published_generation != 0 &&
          (result.published_generation & 1U) == 0,
      observer.observation.last_proof_epoch,
      observer.observation.last_snapshot_revision,
      observer.observation.last_date_raw,
      observer.observation.last_player_character_id};

  if (!observer.installed) {
    result.unavailable_reasons |=
        faction_targeting_row_probe_unavailable_observer_not_installed;
  }
  if (!required_binding.paused) {
    result.unavailable_reasons |=
        faction_targeting_row_probe_unavailable_unpaused;
  }
  if (observer.failure_flags !=
      faction_targeting_row_observer_failure_none) {
    result.unavailable_reasons |=
        faction_targeting_row_probe_unavailable_observer_failure;
  }
  if (result.published_generation == 0) {
    result.unavailable_reasons |=
        faction_targeting_row_probe_unavailable_no_generation;
  } else if ((result.published_generation & 1U) != 0) {
    result.unavailable_reasons |=
        faction_targeting_row_probe_unavailable_odd_generation;
  }
  if (!SameBinding(observer.observation, required_binding)) {
    result.unavailable_reasons |=
        faction_targeting_row_probe_unavailable_stale_binding;
  }
  if (!CaptureShapeIsValid(observer.observation)) {
    result.unavailable_reasons |=
        faction_targeting_row_probe_unavailable_invalid_capture;
  }
  if (result.unavailable_reasons !=
      faction_targeting_row_probe_unavailable_none) {
    return result;
  }

  const auto &capture = observer.observation;
  result.faction_count = capture.last_faction_count;
  for (std::size_t faction_index = 0;
       faction_index < capture.last_faction_count; ++faction_index) {
    auto &target = result.factions[faction_index];
    target.faction_id = capture.last_faction_ids[faction_index];
    target.target_character_id =
        capture.last_target_character_ids[faction_index];
    target.leader_present =
        capture.last_leader_present[faction_index] != 0;
    target.leader_character_id =
        capture.last_leader_character_ids[faction_index];
    target.leader_present_in_character_members =
        capture.last_leader_present_in_character_members[faction_index] != 0;
    target.character_member_count =
        capture.last_character_member_counts[faction_index];
    const auto member_base =
        faction_index *
        kFactionTargetingRowObserverMaximumCharacterMembersPerFactionV1;
    std::copy_n(capture.last_character_member_ids.begin() + member_base,
                target.character_member_count,
                target.character_member_ids.begin());
  }
  result.terminal = result.faction_count == 0
      ? FactionTargetingRowProbeTerminalV1::known_empty
      : FactionTargetingRowProbeTerminalV1::ready;
  return result;
}

std::string_view FactionTargetingRowProbeTerminalNameV1(
    FactionTargetingRowProbeTerminalV1 terminal) noexcept {
  switch (terminal) {
  case FactionTargetingRowProbeTerminalV1::unavailable:
    return "unavailable";
  case FactionTargetingRowProbeTerminalV1::known_empty:
    return "known-empty";
  case FactionTargetingRowProbeTerminalV1::ready:
    return "ready";
  }
  return "unavailable";
}

} // namespace xar::bridge
