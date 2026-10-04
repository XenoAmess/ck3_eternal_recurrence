#include "xar_bridge/ingame_decision_outcome_contract_v1.hpp"
#include "xar_bridge/protocol.hpp"
#include <cassert>
#include <iostream>
using namespace xar::ck3_11906;
int main(){
  assert(IngameDecisionOutcomeRequestValidV1("event_window","lyd.010"));
  assert(IngameDecisionOutcomeRequestValidV1("decision_closed",""));
  for(auto invalid:{"","lyd",".010","lyd.","lyd.010.extra","lyd.0\"10","lyd.0/10"})
    assert(!IngameDecisionOutcomeRequestValidV1("event_window",invalid));
  assert(!IngameDecisionOutcomeRequestValidV1("decision_closed","lyd.010"));
  assert(!IngameDecisionOutcomeRequestValidV1("arbitrary_callback",""));
  const std::string closed_wire=R"({"expected_outcome":"decision_closed","expected_event_definition_key":""})";
  const std::string event_wire=R"({"expected_outcome":"event_window","expected_event_definition_key":"lyd_im.1"})";
  std::string parsed;
  assert(!xar::bridge::JsonStringField(closed_wire,"expected_event_definition_key",parsed,192));
  assert(IngameDecisionOutcomeEmptyEventKeyWireV1(closed_wire));
  assert(xar::bridge::JsonStringField(event_wire,"expected_event_definition_key",parsed,192)&&parsed=="lyd_im.1");
  assert(IngameDecisionOutcomeRequestValidV1("event_window",parsed));
  for(auto invalid:{R"({"expected_outcome":"decision_closed"})",
      R"({"expected_event_definition_key":null})",R"({"expected_event_definition_key":"lyd_im.1"})",
      R"({"expected_event_definition_key":"","expected_event_definition_key":""})",
      R"({"nested":{"expected_event_definition_key":""}})",
      R"({"nested":[{"expected_event_definition_key":""}]})",
      R"({"expected_event_definition_key":"\u0000"})",
      R"({"expected_event_definition_key":"\""})",
      R"({"expected_event_definition_key":""junk})"})
    assert(!IngameDecisionOutcomeEmptyEventKeyWireV1(invalid));
  xar::game::Snapshot before{};
  before.date_raw=53144376;before.speed=1;before.paused=true;before.player_id=0;before.map_ready=true;
  before.has_played_character=true;before.played_character_id=31254;before.played_character_alive=true;
  assert(IngameDecisionOutcomeFrameMatchesV1(before,before,"decision_closed"));
  auto business=before;business.played_character_stress_points=50;business.played_character_gold.raw=200000;
  business.played_character_piety.raw=900000;business.played_character_prestige.raw=40000;
  assert(IngameDecisionOutcomeFrameMatchesV1(before,business,"decision_closed"));
  auto opened=business;opened.has_active_event=true;opened.active_event_instance_id=23;opened.active_event_option_count=4;
  assert(IngameDecisionOutcomeFrameMatchesV1(before,opened,"event_window"));
  assert(!IngameDecisionOutcomeFrameMatchesV1(before,opened,"decision_closed"));
  auto changed=opened;++changed.date_raw;assert(!IngameDecisionOutcomeFrameMatchesV1(before,changed,"event_window"));
  changed=opened;changed.paused=false;assert(!IngameDecisionOutcomeFrameMatchesV1(before,changed,"event_window"));
  changed=opened;++changed.speed;assert(!IngameDecisionOutcomeFrameMatchesV1(before,changed,"event_window"));
  changed=opened;++changed.player_id;assert(!IngameDecisionOutcomeFrameMatchesV1(before,changed,"event_window"));
  changed=opened;++changed.played_character_id;assert(!IngameDecisionOutcomeFrameMatchesV1(before,changed,"event_window"));
  changed=opened;changed.played_character_alive=false;assert(!IngameDecisionOutcomeFrameMatchesV1(before,changed,"event_window"));
  changed=opened;changed.map_ready=false;assert(!IngameDecisionOutcomeFrameMatchesV1(before,changed,"event_window"));
  changed=opened;changed.has_played_character=false;assert(!IngameDecisionOutcomeFrameMatchesV1(before,changed,"event_window"));
  changed=opened;changed.played_character_spouse_ids.push_back(36311);assert(!IngameDecisionOutcomeFrameMatchesV1(before,changed,"event_window"));
  changed=opened;changed.has_pending_character_interaction=true;assert(!IngameDecisionOutcomeFrameMatchesV1(before,changed,"event_window"));
  changed=opened;changed.has_one_life_settlement=true;assert(!IngameDecisionOutcomeFrameMatchesV1(before,changed,"event_window"));
  changed=business;++changed.played_character_gold.scale;assert(!IngameDecisionOutcomeFrameMatchesV1(before,changed,"decision_closed"));
  changed=business;++changed.played_character_prestige.scale;assert(!IngameDecisionOutcomeFrameMatchesV1(before,changed,"decision_closed"));
  changed=business;++changed.played_character_piety.scale;assert(!IngameDecisionOutcomeFrameMatchesV1(before,changed,"decision_closed"));
  auto blocked_before=before;blocked_before.has_active_event=true;
  assert(!IngameDecisionOutcomeFrameMatchesV1(blocked_before,blocked_before,"event_window"));
  blocked_before=before;blocked_before.has_pending_character_interaction=true;
  assert(!IngameDecisionOutcomeFrameMatchesV1(blocked_before,blocked_before,"decision_closed"));
  assert(!IngameDecisionOutcomeFrameMatchesV1(before,before,"unknown"));
  std::cout<<"PASS: typed branch validation and controlled post-dispatch DTO invariants; no CK3 attached\n";
}
