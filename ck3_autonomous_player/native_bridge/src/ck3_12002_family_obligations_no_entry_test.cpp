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
[[maybe_unused]] void NoEntryCases(const char *output) {
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

void *NullSpecialConstruct(void *context,void *definition,std::int32_t first,
                           std::int32_t second,void *extra,bool redirect) {
  Construct(context,definition,first,second,extra,redirect);
  Put(context,a::kContextSpecialInstanceOffset,static_cast<void *>(nullptr));
  return context;
}
void NullSpecialFinalize(void *context) {
  Check(Get<void *>(context,a::kContextSpecialInstanceOffset)==nullptr,
        "native finalization preserves optional null special payload");
  if(active->identity_drift) Put(context,a::kContextActorOffset,std::int32_t{-1});
  ++active->finalizations;
}
bool NullSpecialPick(void *context,const void *target,void *diagnostics) {
  Check(diagnostics==nullptr && Get<void *>(context,a::kContextSpecialInstanceOffset)==nullptr &&
        Get<std::uint16_t>(target,0)==a::kWarTargetType &&
        Get<std::uint16_t>(context,a::kContextTargetOffset)==0,
        "preselection receives null special payload and separate native WarTarget");
  ++active->target_gates; return active->pick;
}
bool NullSpecialValidate(void *context,void *diagnostics) {
  Check(diagnostics==nullptr && Get<void *>(context,a::kContextSpecialInstanceOffset)==nullptr,
        "complete native CanSend evaluates genuine selected null-special context");
  ++active->validates; return active->can_send && active->allied;
}
void InstallNullSpecial(Fixture &fixture) {
  fixture.bindings.construct_context=NullSpecialConstruct;
  fixture.bindings.context.finalize=NullSpecialFinalize;
  fixture.bindings.can_pick_war_target=NullSpecialPick;
  fixture.bindings.context.validate=NullSpecialValidate;
}
bool inject_copied_special=false;
void *NullSpecialSendConstruct(void *command,const void *context) {
  SendConstruct(command,context);
  if(inject_copied_special) Put(command,0x20+a::kContextSpecialInstanceOffset,active);
  return command;
}
bool NullSpecialQueue(void *manager,void **owned,std::uint32_t flags) {
  Check(Get<void *>(static_cast<const std::byte *>(*owned)+0x20,
                    a::kContextSpecialInstanceOffset)==nullptr,
        "owning native queue observes preserved null special payload");
  return Queue(manager,owned,flags);
}
void NullSpecialCases(const char *output) {
  {
    Fixture f; a::Snapshot snapshot; std::string_view reason; InstallNullSpecial(f);
    Put(f.ally_object,a::kCharacterRealmOffset,static_cast<void *>(nullptr));
    Check(a::Read(f.bindings,f.frame,actor,ally,snapshot,&reason) && reason.empty() &&
          snapshot.first_wars.size()==1 && snapshot.second_wars.empty(),
          "actual null-special context reads real caller graph without requiring recipient realm");
    const auto &row=snapshot.first_wars[0];
    Check(row.native_target_can_be_picked && row.native_selected_target_context_available &&
          row.native_complete_can_send && row.send_cost_raw[9]==900'000 &&
          row.recipient_acceptance_raw==-2'500'000 && row.recipient_answer_status_raw==2 &&
          f.validates==1 && f.cost_reads==1 && f.answer_reads==1 &&
          f.constructions==f.destructions,
          "all selected native terms are sampled once with a null optional special payload");
    FamilyObligationsObservation12002 o{};
    o.snapshot_revision=17; o.request.ally_character_id=ally;
    o.frame.date_raw=f.frame.clock.date_raw; o.frame.played_character_id=actor;
    o.frame.paused=o.frame.map_ready=o.frame.played_character_alive=true;
    o.alliance_available=true; o.alliance=snapshot;
    const auto wire=SerializeFamilyObligationsResult12002("call-ally-null-special-fixture",o);
    Check(wire.find("\"native_selected_target_context_available\":true")!=std::string::npos &&
          wire.find("\"native_complete_can_send\":true")!=std::string::npos &&
          wire.find("\"send_cost_raw\":[0,100000")!=std::string::npos,
          "existing wire emits genuinely evaluated selected terms without nullable-shape changes");
    if(output) { std::ofstream out(output,std::ios::binary); out<<wire<<'\n'; Check(bool(out),"null special wire file"); }
  }
  {
    Fixture f; a::Snapshot snapshot; InstallNullSpecial(f); f.can_send=false;
    Put(f.ally_object,a::kCharacterRealmOffset,static_cast<void *>(nullptr));
    Check(a::Read(f.bindings,f.frame,actor,ally,snapshot) &&
          snapshot.first_wars[0].native_selected_target_context_available &&
          !snapshot.first_wars[0].native_complete_can_send && f.cost_reads==1,
          "null optional payload does not manufacture complete CanSend true or missing-cost zeros");
  }
  {
    SendFixture f; a::CallAllySubmitReceipt receipt; InstallNullSpecial(f); inject_copied_special=false;
    f.bindings.context.construct_send_command=NullSpecialSendConstruct;
    f.bindings.context.commands.queue_owned_command=NullSpecialQueue;
    Check(a::SubmitCallAlly(f.bindings,f.frame,f.request,receipt)==CommandSubmitResult::submitted &&
          f.queues==1 && f.clones==1 && f.source_commands==1 && receipt.send_cost_sampled &&
          receipt.selected_target_native_legal && receipt.copied_context_identity_verified &&
          receipt.actual_send_cost_raw==f.request.expected_send_cost_raw,
          "genuine null-special source and owned copy submit once with full identities and sampled quote");
  }
  {
    SendFixture f; a::CallAllySubmitReceipt receipt; std::string_view reason;
    InstallNullSpecial(f); inject_copied_special=true;
    f.bindings.context.construct_send_command=NullSpecialSendConstruct;
    Check(a::SubmitCallAlly(f.bindings,f.frame,f.request,receipt,&reason)==CommandSubmitResult::unavailable &&
          reason=="call_ally_copied_context_identity_unavailable" && f.queues==0 &&
          !receipt.copied_context_identity_verified,
          "owned context preserves source special nullness without comparing deep-copy addresses");
    inject_copied_special=false;
  }
  std::cout<<"GREEN call ally optional-null-special: 4 focused changed production-path cases; no game\n";
}
}
int main(int argc,char **argv) {
  try {
#ifdef XAR_CK3_CALL_ALLY_NULL_SPECIAL_FOCUSED_ONLY
    NullSpecialCases(argc==2?argv[1]:nullptr);
#else
    NoEntryCases(argc==2?argv[1]:nullptr); NullSpecialCases(nullptr);
#endif
    return 0;
  }
  catch(const std::exception &e) { std::cerr<<"RED "<<e.what()<<'\n'; return 1; }
}
