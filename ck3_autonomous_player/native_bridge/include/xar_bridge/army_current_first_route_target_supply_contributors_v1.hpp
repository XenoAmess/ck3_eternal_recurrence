#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace xar::game {

// The template keeps this header independent of the existing contributor DTO.
// game_contract.hpp instantiates it after that DTO is complete.
template<class ContributorInputs>
struct ArmyCurrentFirstRouteTargetSupplyContributorsSnapshotV1 {
  std::string status = "unavailable";
  std::string unavailable_reason;
  bool current_target_inputs_ready = false;
  std::optional<std::int32_t> subject_army_id, subject_carmy_id;
  std::optional<std::int32_t> current_province_id, first_route_target_province_id;
  std::optional<std::int32_t> route_source_count;
  std::optional<ContributorInputs> target_contributors_v1;
  std::vector<std::int32_t> subject_matching_occurrence_indices;
  std::optional<std::int32_t> subject_included_occurrence_count;
  friend bool operator==(
      const ArmyCurrentFirstRouteTargetSupplyContributorsSnapshotV1 &,
      const ArmyCurrentFirstRouteTargetSupplyContributorsSnapshotV1 &) = default;
};

} // namespace xar::game
