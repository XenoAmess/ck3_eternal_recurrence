#define main ArchivedSenderFixtureMain
#include "ck3_12002_call_ally_sender_test.cpp"
#undef main
#include "xar_bridge/ck3_12002_family_obligations_wire.hpp"
#include <fstream>
#include <algorithm>

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
struct SendLegalityFixtureState {
  bool setup = true, availability = true, precheck = true;
  bool already_considering_blocked = false, pair_restriction_blocked = false, range = true;
  std::array<bool, 7> gates{true, true, true, true, true, true, true};
  std::uint8_t preview_answer = 0, internal_answer = 2;
  int setup_reads = 0, availability_reads = 0, precheck_reads = 0;
  int considering_reads = 0, restriction_reads = 0, range_reads = 0;
  int preview_reads = 0, internal_reads = 0;
  std::array<int, 7> gate_reads{};
};
SendLegalityFixtureState *legality_fixture = nullptr;
constexpr std::array<std::size_t, 7> diagnostic_gate_offsets{
    0xAE8, 0xC88, 0xE28, 0x1168, 0xFC8, 0xD58, 0xEF8};
void CheckSelectedReasonContext(const void *context) {
  Check(Get<std::int32_t>(context, a::kContextActorOffset) == actor &&
        Get<std::int32_t>(context, a::kContextRecipientOffset) == ally &&
        Get<std::uint16_t>(context, a::kContextTargetOffset) == a::kWarTargetType &&
        Get<std::uint64_t>(context, a::kContextTargetTokenOffset) == static_cast<std::uint32_t>(own_war),
        "new native diagnostic callback receives genuine same finalized selected identity");
}
bool DiagnosticSetup(void *context) {
  CheckSelectedReasonContext(context); ++legality_fixture->setup_reads;
  return legality_fixture->setup;
}
bool DiagnosticAvailability(void *context, void *text) {
  CheckSelectedReasonContext(context); Check(text == nullptr, "availability exact null text");
  ++legality_fixture->availability_reads; return legality_fixture->availability;
}
bool DiagnosticPrecheck(void *context, std::uint8_t already, std::uint8_t gate1168, void *text) {
  CheckSelectedReasonContext(context);
  Check(already == 1 && gate1168 == 1 && text == nullptr,
        "new production uses four-argument precheck (context,1,1,null)");
  ++legality_fixture->precheck_reads; return legality_fixture->precheck;
}
bool DiagnosticConsidering(void *context) {
  CheckSelectedReasonContext(context); ++legality_fixture->considering_reads;
  return legality_fixture->already_considering_blocked;
}
bool DiagnosticRestriction(void *definition, void *first, void *second, void *text) {
  Check(definition == active->definition.data() && first == active->actor_object.data() &&
        second == active->ally_object.data() && text == nullptr,
        "native pair-restriction receives current full resolved identities and definition");
  ++legality_fixture->restriction_reads; return legality_fixture->pair_restriction_blocked;
}
bool DiagnosticRange(void *context, const void *scope) {
  CheckSelectedReasonContext(context);
  Check(scope == static_cast<std::byte *>(context) + 8, "native range exact context scope");
  ++legality_fixture->range_reads; return legality_fixture->range;
}
std::uint8_t DiagnosticAnswer(void *context, std::uint8_t first, std::uint8_t second,
                              void *left, void *right) {
  CheckSelectedReasonContext(context); Check(left == nullptr && right == nullptr, "answer null text inputs");
  if (first == 1 && second == 1) {
    ++legality_fixture->preview_reads; return legality_fixture->preview_answer;
  }
  Check(first == 0 && second == 0, "complete CanSend internal answer exact zero/zero flags");
  ++legality_fixture->internal_reads; return legality_fixture->internal_answer;
}
bool DiagnosticTrigger(void *compiled, const void *scope) {
  const auto context = static_cast<const std::byte *>(scope) - 8;
  CheckSelectedReasonContext(context);
  for (std::size_t index = 0; index < diagnostic_gate_offsets.size(); ++index) {
    if (compiled == active->definition.data() + diagnostic_gate_offsets[index]) {
      ++legality_fixture->gate_reads[index]; return legality_fixture->gates[index];
    }
  }
  throw std::runtime_error("new diagnostic called an unbound compiled definition offset");
}
void InstallSendLegality(Fixture &fixture, SendLegalityFixtureState &state) {
  legality_fixture = &state;
  Put(fixture.ally_object, a::kCharacterRealmOffset, static_cast<void *>(nullptr));
  fixture.can_send = false;
  fixture.bindings.setup = DiagnosticSetup; fixture.bindings.availability = DiagnosticAvailability;
  fixture.bindings.send_precheck = DiagnosticPrecheck;
  fixture.bindings.already_considering = DiagnosticConsidering;
  fixture.bindings.pair_restriction = DiagnosticRestriction;
  fixture.bindings.diplomatic_range = DiagnosticRange;
  fixture.bindings.final_answer = DiagnosticAnswer;
  fixture.bindings.context.evaluate_trigger = DiagnosticTrigger;
}
void EmitSendLegality(const a::Snapshot &snapshot, const Fixture &fixture,
                      const char *directory, const char *label) {
  FamilyObligationsObservation12002 observation{};
  observation.snapshot_revision = 17; observation.request.ally_character_id = ally;
  observation.frame.date_raw = fixture.frame.clock.date_raw;
  observation.frame.played_character_id = actor;
  observation.frame.paused = observation.frame.map_ready = observation.frame.played_character_alive = true;
  observation.alliance_available = true; observation.alliance = snapshot;
  const auto wire = SerializeFamilyObligationsResult12002(label, observation);
  Check(wire.find("\"native_send_answer_status_raw\":") != std::string::npos &&
        wire.find("\"native_send_precheck_passed\":") != std::string::npos &&
        wire.find("\"native_send_definition_gate_results\":[") != std::string::npos &&
        wire.find("\"native_first_failed_send_stage\":\"") != std::string::npos,
        "genuine production serializer emits sampled new diagnostic values");
  if (directory != nullptr) {
    const auto file = std::string(directory) + "/" + label + "-native-command-result.json";
    std::ofstream output(file, std::ios::binary); output << wire << '\n';
    Check(bool(output), "new reason packet emitted by actual production serializer");
  }
}
void ReadAndVerifySendLegality(Fixture &fixture, const SendLegalityFixtureState &state,
                             std::string_view expected, const char *directory, const char *label) {
  a::Snapshot snapshot; std::string_view reason;
  Check(a::Read(fixture.bindings, fixture.frame, actor, ally, snapshot, &reason) && reason.empty() &&
        snapshot.first_wars.size() == 1 && snapshot.second_wars.empty(),
        "new reason scenarios traverse genuine production reader and actual native world row");
  const auto &row = snapshot.first_wars[0];
  Check(row.native_selected_target_context_available && !row.native_complete_can_send &&
        row.recipient_answer_status_raw == state.preview_answer &&
        row.native_send_answer_status_raw == state.internal_answer &&
        row.native_send_precheck_passed == state.precheck &&
        row.native_send_setup_passed == state.setup &&
        row.native_send_availability_passed == state.availability &&
        row.native_send_already_considering_blocked == state.already_considering_blocked &&
        row.native_send_pair_restriction_blocked == state.pair_restriction_blocked &&
        row.native_send_diplomatic_range_passed == state.range &&
        row.native_send_definition_gate_results == state.gates &&
        row.native_first_failed_send_stage == expected,
        "production preserves independent exact native inputs and first actual failed-stage enum");
  Check(state.setup_reads == 1 && state.availability_reads == 1 && state.precheck_reads == 1 &&
        state.considering_reads == 1 && state.restriction_reads == 1 && state.range_reads == 1 &&
        state.preview_reads == 1 && state.internal_reads == 1,
        "one same-context native sample per new diagnostic getter and flag pair");
  Check(std::all_of(state.gate_reads.begin(), state.gate_reads.end(), [](int count) { return count == 1; }),
        "all seven raw compiled slots are actually sampled once");
  Check(fixture.validates == 1 && fixture.cost_reads == 1 && fixture.answer_reads == 1 &&
        fixture.constructions == fixture.destructions,
        "existing complete gate/quote/score and cleanup remain genuine independent observations");
  EmitSendLegality(snapshot, fixture, directory, label);
}
void SendLegalityCases(const char *directory) {
  {
    Fixture fixture; SendLegalityFixtureState state; InstallSendLegality(fixture, state);
    ReadAndVerifySendLegality(fixture, state, "internal_answer", directory, "internal-answer");
  }
  {
    Fixture fixture; SendLegalityFixtureState state;
    state.precheck = false; state.already_considering_blocked = true;
    InstallSendLegality(fixture, state);
    ReadAndVerifySendLegality(fixture, state, "already_considering", directory, "already-considering");
  }
  {
    Fixture fixture; SendLegalityFixtureState state;
    state.precheck = false; state.gates[2] = false; state.internal_answer = 1;
    InstallSendLegality(fixture, state);
    ReadAndVerifySendLegality(fixture, state, "definition_e28", directory, "definition-e28");
  }
  {
    Fixture fixture; SendLegalityFixtureState state;
    state.internal_answer = 0;
    InstallSendLegality(fixture, state);
    ReadAndVerifySendLegality(fixture, state, "complete_can_send_other", directory, "complete-other");
  }
  std::cout << "GREEN call ally send-legality: 4 focused new production reader/serializer reasons; no old cases\n";
}

}
int main(int argc,char **argv) {
  try {
#if defined(XAR_CK3_CALL_ALLY_SEND_LEGALITY_FOCUSED_ONLY)
    SendLegalityCases(argc==2?argv[1]:nullptr);
#elif defined(XAR_CK3_CALL_ALLY_NULL_SPECIAL_FOCUSED_ONLY)
    NullSpecialCases(argc==2?argv[1]:nullptr);
#else
    NoEntryCases(argc==2?argv[1]:nullptr); NullSpecialCases(nullptr);
#endif
    return 0;
  }
  catch(const std::exception &e) { std::cerr<<"RED "<<e.what()<<'\n'; return 1; }
}
