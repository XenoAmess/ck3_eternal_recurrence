#define main ArchivedSenderFixtureMain
#include "ck3_12002_call_ally_sender_test.cpp"
#undef main
#include "xar_bridge/ck3_12002_family_obligations_wire.hpp"
#include <fstream>

namespace {
void EmitNoEntry(const a::Snapshot &snapshot, const Fixture &fixture, const char *path) {
  FamilyObligationsObservation12002 o{};
  o.snapshot_revision=17; o.request.ally_character_id=ally;
  o.frame.date_raw=fixture.frame.clock.date_raw; o.frame.played_character_id=actor;
  o.frame.paused=o.frame.map_ready=o.frame.played_character_alive=true;
  o.alliance_available=true; o.alliance=snapshot;
  const auto wire=SerializeFamilyObligationsResult12002("call-ally-no-entry-fixture",o);
  Check(wire.find("\"native_selected_target_context_available\":false")!=std::string::npos &&
        wire.find("\"native_complete_can_send\":null")!=std::string::npos &&
        wire.find("\"send_cost_raw\":null")!=std::string::npos &&
        wire.find("\"recipient_answer_status_raw\":null")!=std::string::npos,
        "actual production serializer publishes unselected terms as unknown");
  if(path) { std::ofstream out(path,std::ios::binary); out<<wire<<'\n'; Check(bool(out),"wire file"); }
}
void NoEntryCases(const char *output) {
  {
    Fixture f; a::Snapshot snapshot; f.pick=false;
    // Mirrors the currently observed receiver's absence of a realm object;
    // this is not treated as the cause of the native predicate result.
    Put(f.ally_object,a::kCharacterRealmOffset,static_cast<void *>(nullptr));
    Check(a::Read(f.bindings,f.frame,actor,ally,snapshot) && snapshot.first_wars.size()==1 &&
          snapshot.second_wars.empty() && snapshot.first_has_second && snapshot.second_has_first,
          "observed false picker retains bilateral relation and actual caller war graph");
    const auto &row=snapshot.first_wars[0];
    Check(row.war_id==own_war && row.attacker_character_ids==std::vector<std::int32_t>{actor} &&
          !row.native_target_can_be_picked && !row.native_selected_target_context_available &&
          !row.native_target_row_selectable && f.refreshes==0 && f.finalizations==0 &&
          f.validates==0 && f.cost_reads==0 && f.answer_reads==0 && f.constructions==f.destructions,
          "unpickable candidate is never selected and has no evaluated selected terms");
    EmitNoEntry(snapshot,f,output);
  }
  {
    Fixture f; a::Snapshot snapshot;
    Check(a::Read(f.bindings,f.frame,actor,ally,snapshot) &&
          snapshot.first_wars[0].native_selected_target_context_available &&
          snapshot.first_wars[0].native_complete_can_send && f.target_gates==3 && f.validates==3,
          "pickable candidate preserves selected final native terms after one preselection check");
  }
  {
    Fixture f; a::Snapshot snapshot; f.can_send=false;
    Check(a::Read(f.bindings,f.frame,actor,ally,snapshot) &&
          snapshot.first_wars[0].native_selected_target_context_available &&
          !snapshot.first_wars[0].native_complete_can_send && f.cost_reads==3,
          "evaluated complete CanSend false stays separate from absent selected context");
  }
  {
    Fixture f; a::Snapshot snapshot; std::string_view reason; f.identity_drift=true;
    Check(!a::Read(f.bindings,f.frame,actor,ally,snapshot,&reason) &&
          reason=="call_ally_finalized_actor_identity_unavailable" && f.cost_reads==0,
          "pickable context identity loss remains unavailable with a specific failed predicate");
  }
  {
    SendFixture f; a::CallAllySubmitReceipt receipt; std::string_view reason; f.pick=false;
    Check(a::SubmitCallAlly(f.bindings,f.frame,f.request,receipt,&reason)==CommandSubmitResult::rejected &&
          reason=="call_ally_selected_war_target_not_pickable" && f.queues==0 && f.clones==0 &&
          f.refreshes==0 && f.finalizations==0 && !receipt.send_cost_sampled,
          "outgoing sender also preserves native UI preselection order and queues zero unpickable commands");
  }
  std::cout<<"GREEN call ally no-entry producer/serializer: 5 focused production-path cases; no game\n";
}
}
int main(int argc,char **argv) {
  try { NoEntryCases(argc==2?argv[1]:nullptr); return 0; }
  catch(const std::exception &e) { std::cerr<<"RED "<<e.what()<<'\n'; return 1; }
}
