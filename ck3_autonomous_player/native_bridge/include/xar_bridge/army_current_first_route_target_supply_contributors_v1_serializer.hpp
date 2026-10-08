#pragma once

#include "xar_bridge/army_current_first_route_target_supply_contributors_v1.hpp"

#include <cstddef>

namespace xar::game {

template<class ContributorInputs, class Number, class String, class Contributors>
void AppendArmyCurrentFirstRouteTargetSupplyContributorsV1(
    std::string &out,
    const ArmyCurrentFirstRouteTargetSupplyContributorsSnapshotV1<ContributorInputs> &value,
    Number number, String append_string, Contributors append_contributors) {
  out += "{\"source\":\"native_current_first_route_target_supply_contributors_12004\",\"status\":";
  append_string(out, value.status);
  out += ",\"unavailable_reason\":";
  if (value.unavailable_reason.empty()) out += "null";
  else append_string(out, value.unavailable_reason);
  out += ",\"current_target_inputs_ready\":";
  out += value.current_target_inputs_ready ? "true" : "false";
  const auto append_optional = [&](const char *name, const auto &raw) {
    out += ',';
    append_string(out, name);
    out += ':';
    out += raw ? number(*raw) : "null";
  };
  append_optional("subject_army_id", value.subject_army_id);
  append_optional("subject_carmy_id", value.subject_carmy_id);
  append_optional("current_province_id", value.current_province_id);
  append_optional("first_route_target_province_id", value.first_route_target_province_id);
  append_optional("route_source_count", value.route_source_count);
  out += ",\"target_contributors_v1\":";
  if (value.target_contributors_v1) append_contributors(out, *value.target_contributors_v1);
  else out += "null";
  out += ",\"subject_matching_occurrence_indices\":[";
  for (std::size_t i = 0; i < value.subject_matching_occurrence_indices.size(); ++i) {
    if (i) out += ',';
    out += number(value.subject_matching_occurrence_indices[i]);
  }
  out += ']';
  append_optional("subject_included_occurrence_count", value.subject_included_occurrence_count);
  out += ",\"input_basis\":\"captured_committed_first_route_target\","
      "\"actual_arrival_observed\":false,\"actual_after_arrival_usage_observed\":false,"
      "\"full_arrival_supply_transition_ready\":false}";
}

} // namespace xar::game
