#include "activity_feast_stage5_start_private_transport_v1.hpp"
#include <fstream>
#include <cstring>
#include <cstdlib>

int main(int argc, char **argv) {
  if (argc != 2 && argc != 3) return 2;
  using namespace xar;
  ck3_11906::ActivityFeastStage5PrivateQueryV1 query{};
  query.completed = true;
  query.mode = ck3_11906::ActivityFeastStage5PrivateModeV1::hosted_post;
  query.post.frame = {12, 53220000, 29829, true, true, true, true};
  query.post.balances.frame = query.post.frame;
  query.post.balances.available = {true, false, true, false};
  query.post.balances.raw = {110644281, 0, 4000000, 0};
  query.post.hosted_identities_observed = true;
  query.post.hosted_count = 1;
  query.post.outcome_values.frame = query.post.frame;
  query.post.outcome_values.prestige_available = true;
  query.post.outcome_values.prestige_raw = 25000000;
  query.post.outcome_values.stress_available = true;
  query.post.outcome_values.stress_points = 42;
  query.post.outcome_values.reveler_available = true;
  query.post.outcome_values.reveler_present = false;
  auto &identity = query.post.hosted[0];
  identity.activity_id = 0x01000012;
  identity.host_character_id = 29829;
  std::memcpy(identity.type_key.data(), "activity_feast", 14);
  identity.type_key_size = 14;
  identity.terminal_flags_observed = true;
  std::ofstream output(argv[1], std::ios::binary);
  if (!output) return 3;
  output << "[";
  for (int phase = 0; phase < 3; ++phase) {
    identity.native_completed = phase == 1;
    identity.native_invalidated = phase == 2;
    const auto serialized = ck3_11906::SerializeActivityFeastStage5PrivateV1(query);
    if (serialized.empty()) return 4;
    if (phase) output << ",";
    output << serialized;
  }
  output << "]\n";
  if (!output.good()) return 5;
  if (argc == 2) return 0;
  query.mode = ck3_11906::ActivityFeastStage5PrivateModeV1::start_inputs;
  auto &input = query.inputs;
  input.frame = {11, 53175192, 29829, true, true, true, true};
  input.normal_cost_refresh_sequence = 4;
  input.feast_type_verified = true;
  input.generic_option_verified = true;
  input.final_can_start_observed = true;
  input.final_can_start = true;
  input.four_costs_observed = true;
  input.cost_resource_indices = {0, 6, 2, 9};
  input.cost_raw = {10000000, 0, 0, 0};
  input.balances.frame = input.frame;
  input.balances.available = {true, false, true, false};
  input.balances.raw = {148384115, 0, -103410000, 0};
  input.hosted_identities_observed = true;
  query.guest_status = bridge::ActivityFeastGuestJoinStatusV1::observed;
  query.arrival_time_observed = true;
  input.selected_guests.status = query.guest_status;
  input.selected_guests.frame = {11, 53175192, 29829, true, true, true, true};
  input.selected_guests.normal_refresh_sequence = 4;
  input.selected_guests.arrival_time_observed = true;
  auto &ordinary = input.ordinary_guest;
  ordinary.candidate.status = bridge::ActivityFeastGuestCandidateStatusV1::observed;
  ordinary.candidate.frame = input.selected_guests.frame;
  ordinary.candidate.normal_refresh_sequence = 4;
  ordinary.candidate.source_fingerprint = 0x72e1dc20192345ab;
  ordinary.candidate.native_filtered = true;
  ordinary.candidate.character_id = 37502;
  ordinary.candidate.planner_join_raw = 200000;
  ordinary.candidate.travel_days = 19;
  ordinary.candidate.arrival_raw = 53175648;
  ordinary.candidate.planned_start_raw = 53178936;
  ordinary.rule_status = bridge::ActivityFeastGuestRuleStatusV1::observed_active;
  ordinary.rule_active = true;
  ordinary.native_key_hash = ordinary.provenance_key_hash = 3893157043U;
  ordinary.provenance_refresh_sequence = 9;
  ordinary.raw_rule_character_count = 38;
  ordinary.filtered_rule_character_count = 19;
  std::ofstream ordinary_output(argv[2], std::ios::binary);
  if (!ordinary_output) return 6;
  ordinary_output << "[";
  for (int phase = 0; phase < 3; ++phase) {
    ordinary.provenance_status = phase == 2
        ? bridge::ActivityGuestRuleProvenanceStatusV1::no_normal_refresh
        : bridge::ActivityGuestRuleProvenanceStatusV1::observed;
    ordinary.candidate_membership = phase == 0;
    query.guest_route_qualified = bridge::IsActivityFeastGuestRouteQualifiedV1(input);
    const auto serialized = ck3_11906::SerializeActivityFeastStage5PrivateV1(query);
    if (serialized.empty()) return 7;
    if (phase) ordinary_output << ",";
    ordinary_output << serialized;
  }
  ordinary_output << "]\n";
  return ordinary_output.good() ? 0 : 8;
}
