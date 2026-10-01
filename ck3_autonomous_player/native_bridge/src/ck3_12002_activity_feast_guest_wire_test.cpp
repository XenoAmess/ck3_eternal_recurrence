#include "ck3_12002_activity_feast_guest_transport.hpp"

#include <cassert>
#include <iostream>
#include <string>

int main() {
  using namespace xar::ck3_12002;
  using namespace xar::bridge;
  ActivityFeastGuestCandidatePrivateQueryV1 query{};
  query.completed = true;
  query.expected_revision = 17;
  query.expected_snapshot.date_raw = 53219928;
  query.expected_snapshot.played_character_id = 29829;
  query.route_proof = true;
  query.route_proof_consistent = true;
  query.target_character_id = 43699;
  query.candidate.status = ActivityFeastGuestCandidateStatusV1::observed;
  query.candidate.character_id = 43699;
  query.candidate.normal_refresh_sequence = 21;
  query.candidate.selected_member = true;
  query.selected_guests.status = ActivityFeastGuestJoinStatusV1::observed;
  query.selected_guests.selected_nonhost_count = 1;
  query.selected_guests.rows[0].character_id = 43699;
  query.selected_guests.rows[0].positive_join = true;
  query.selected_guests.rows[0].planner_join_raw = 15000000;
  query.start_gate.status = ActivityStage5CanStartStatusV1::observed;
  query.start_gate.final_can_start = true;
  const auto route = SerializeActivityFeastGuestRouteProofPrivateV1(query);
  const auto target = SerializeActivityFeastGuestTargetPrivateV1(query);
  assert(route.find("\"candidate_selected_membership\":true") != std::string::npos);
  assert(route.find("\"character_id\":43699") != std::string::npos);
  assert(target.find("\"selected_member\":true") != std::string::npos);
  assert(target.find("\"target_character_id\":43699") != std::string::npos);
  query.candidate.selected_member = false;
  query.selected_guests.selected_nonhost_count = 0;
  assert(SerializeActivityFeastGuestRouteProofPrivateV1(query).find(
      "\"candidate_selected_membership\":false") != std::string::npos);
  query.route_proof_consistent = false;
  assert(SerializeActivityFeastGuestRouteProofPrivateV1(query).find(
      "\"candidate_selected_membership\":null") != std::string::npos);
  query.frame_changed = true;
  assert(SerializeActivityFeastGuestTargetPrivateV1(query).empty());
  ActivityFeastGuestOpinionPrivateQueryV1 opinion{};
  opinion.completed = true;
  opinion.expected_revision = 17;
  opinion.expected_snapshot = query.expected_snapshot;
  opinion.guest_character_id = 43699;
  opinion.opinion.status = ActivityFeastGuestOpinionStatusV1::observed;
  opinion.opinion.guest_opinion_of_actor = -8;
  assert(SerializeActivityFeastGuestOpinionPrivateV1(opinion).find(
      "\"guest_opinion_of_actor\":-8") != std::string::npos);
  opinion.opinion.status = ActivityFeastGuestOpinionStatusV1::opinion_unavailable;
  assert(SerializeActivityFeastGuestOpinionPrivateV1(opinion).find(
      "\"guest_opinion_of_actor\":null") != std::string::npos);
  std::cout << "PASS Feast 1.20 selected target / route proof / opinion wire fixture\n";
}
