#include "ck3_12002_activity_feast_guest_transport.hpp"

#include <cassert>
#include <iostream>
#include <string>
#include <string_view>
#include <cstring>

int main(int argc, char **argv) {
  using namespace xar::ck3_12002;
  using namespace xar::bridge;
  if (argc == 2 && std::string_view(argv[1]) == "--target-only") {
    ActivityFeastGuestOpinionPrivateQueryV1 query{};
    query.completed = true;
    query.expected_revision = 4;
    query.expected_snapshot.date_raw = 53222952;
    query.expected_snapshot.played_character_id = 29829;
    query.guest_character_id = 37265;
    query.opinion.status = ActivityFeastGuestOpinionStatusV1::observed;
    query.opinion.guest_opinion_of_actor = 82;
    assert(SerializeActivityFeastGuestOpinionPrivateV1(query).find("activity_target") == std::string::npos);
    query.activity_id = 83886111;
    query.opinion.activity_target_requested = true;
    auto &target = query.opinion.activity_target;
    target.status = ActivityHostedTargetStatusV1::observed;
    target.activity_id = 83886111;
    target.guest_character_id = 37265;
    target.host_character_id = 29829;
    constexpr std::string_view type = "activity_feast";
    std::memcpy(target.type_key.data(), type.data(), type.size());
    target.type_key_size = static_cast<std::uint8_t>(type.size());
    target.native_completed = true;
    target.attending_list_observed = true;
    target.attending_count = 1;
    target.target_in_attending_list = true;
    target.character_record_observed = true;
    target.character_activity_id = 83886111;
    target.character_activity_state_raw = 2;
    target.character_record_matches_activity = true;
    target.native_active_attendee = true;
    const auto observed = SerializeActivityFeastGuestOpinionPrivateV1(query);
    for (const auto expected : {"\"activity_id\":83886111", "\"activity_type_key\":\"activity_feast\"",
        "\"native_completed\":true", "\"attending_count\":1", "\"target_in_attending_list\":true",
        "\"character_activity_id\":83886111", "\"character_activity_state_raw\":2",
        "\"character_record_matches_activity\":true", "\"native_active_attendee\":true"})
      assert(observed.find(expected) != std::string::npos);
    target.attending_count = 0;
    target.target_in_attending_list = false;
    target.character_record_observed = false;
    const auto empty = SerializeActivityFeastGuestOpinionPrivateV1(query);
    assert(empty.find("\"attending_count\":0") != std::string::npos);
    assert(empty.find("\"target_in_attending_list\":false") != std::string::npos);
    assert(empty.find("\"character_activity_id\":null") != std::string::npos);
    assert(empty.find("\"native_active_attendee\":null") != std::string::npos);
    target.status = ActivityHostedTargetStatusV1::activity_identity_unavailable;
    const auto unavailable = SerializeActivityFeastGuestOpinionPrivateV1(query);
    assert(unavailable.find("\"status\":\"activity_identity_unavailable\"") != std::string::npos);
    assert(unavailable.find("\"native_completed\":null") != std::string::npos);
    assert(unavailable.find("\"target_in_attending_list\":null") != std::string::npos);
    std::cout << "PASS optional Feast activity-target wire (3 cases)\n";
    return 0;
  }
#if defined(XAR_FEAST_TARGET_ONLY_FIXTURE)
  return 1;
#else
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
#endif
}
