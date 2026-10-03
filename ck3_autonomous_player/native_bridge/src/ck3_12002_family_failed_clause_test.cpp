#define main ArchivedAllianceMain
#include "ck3_12002_family_obligations_alliance_test.cpp"
#undef main
#include "xar_bridge/ck3_12002_family_obligations_wire.hpp"

#include <algorithm>
#include <fstream>
#include <string>

namespace {
struct ClauseState {
  std::array<std::byte, 0xD8> descriptor{};
  std::array<unsigned char, 3> modes{2,2,0};
  bool c88_passed = false;
  int allocations = 0, constructions = 0, evaluations = 0, formats = 0;
  int string_destroys = 0, descriptor_destroys = 0, frees = 0;
  int raw_c88_reads = 0, preview_reads = 0, internal_reads = 0;
  std::vector<std::string> operations;
};
ClauseState *clause = nullptr;
constexpr std::string_view formatted_group =
    "#N Native C88 receiver clause is false#!\n#P Native parent context is true#!; UTF8: \xE5\xAF\xB9\xE8\xB1\xA1";
constexpr std::array<std::size_t,7> compiled_gate_offsets{0xAE8,0xC88,0xE28,0x1168,0xFC8,0xD58,0xEF8};

void CheckSelectedClauseContext(const void *context) {
  Check(Get<std::int32_t>(context,a::kContextActorOffset)==actor &&
        Get<std::int32_t>(context,a::kContextRecipientOffset)==ally &&
        Get<std::uint16_t>(context,a::kContextTargetOffset)==a::kWarTargetType &&
        Get<std::uint64_t>(context,a::kContextTargetTokenOffset)==static_cast<std::uint32_t>(own_war),
        "new description and reason samples share genuine finalized full actor/recipient/war identities");
}
bool ClausePrecheck(void *context,std::uint8_t first,std::uint8_t second,void *text) {
  CheckSelectedClauseContext(context);
  Check(first==1 && second==1 && text==nullptr,"same native precheck flags and null output remain unchanged");
  return clause->c88_passed;
}
std::uint8_t ClauseAnswer(void *context,std::uint8_t first,std::uint8_t second,void *left,void *right) {
  CheckSelectedClauseContext(context);
  Check(left==nullptr && right==nullptr,"independent native answer arguments unchanged");
  if(first==1 && second==1) { ++clause->preview_reads; return 0; }
  Check(first==0 && second==0,"internal native answer stays the zero/zero query");
  ++clause->internal_reads; return 2;
}
bool ClauseTrigger(void *compiled,const void *scope) {
  CheckSelectedClauseContext(static_cast<const std::byte *>(scope)-8);
  for(const auto offset:compiled_gate_offsets) {
    if(compiled==active->definition.data()+offset) {
      if(offset==0xC88) { ++clause->raw_c88_reads; return clause->c88_passed; }
      return true;
    }
  }
  throw std::runtime_error("new clause case received an unexpected raw compiled gate");
}
void ZeroCost(const void *cost,const void *scope,std::int64_t *output) {
  Check(cost==active->definition.data()+0x40,"genuine immediate quote definition scope");
  CheckSelectedClauseContext(static_cast<const std::byte *>(scope)-8);
  std::fill(output,output+10,std::int64_t{0});
  ++active->cost_reads;
}
void *DescriptionAllocate(std::size_t size) {
  Check(size==0xD8 && clause->allocations==0,"native description owner allocates exact D8 storage once");
  ++clause->allocations; clause->operations.push_back("allocate");
  return clause->descriptor.data();
}
void *DescriptionConstruct(void *storage) {
  Check(storage==clause->descriptor.data(),"native constructor receives allocated storage");
  std::memset(storage,0,0xD8); Put(storage,0xD0,std::uint8_t{1});
  ++clause->constructions; clause->operations.push_back("construct");
  return storage;
}
bool DescribeTrigger(const void *compiled,void *scope,void *description) {
  Check(compiled==active->definition.data()+0xC88 && description==clause->descriptor.data(),
        "production failure getter evaluates actual C88 block into its owned native description");
  CheckSelectedClauseContext(static_cast<std::byte *>(scope)-8);
  Check(Get<std::uint8_t>(description,0xD0)==1,"native constructor default D0 preserved until description evaluation");
  ++clause->evaluations; clause->operations.push_back("evaluate");
  return false;
}
void DescriptionFormat(void **owner,const void *modes,void *output) {
  Check(owner!=nullptr && *owner==clause->descriptor.data() && modes==clause->modes.data(),
        "native formatter receives mutable current owner slot and exact stock parameter array");
  Check(Get<std::uint8_t>(*owner,0xD0)==0,"production mirrors native D0=0 before group formatting");
  Check(clause->modes==std::array<unsigned char,3>{2,2,0},"native formatter parameter bytes remain 02 02 00");
  std::memset(output,0,32);
  Put(output,0,formatted_group.data());
  Put(output,0x10,static_cast<std::uint64_t>(formatted_group.size()));
  Put(output,0x18,static_cast<std::uint64_t>(formatted_group.size()));
  ++clause->formats; clause->operations.push_back("format");
}
void DescriptionStringDestroy(void *text) {
  Check(Get<const char *>(text,0)==formatted_group.data() &&
        Get<std::uint64_t>(text,0x10)==formatted_group.size(),
        "native formatted string retains its independent owned output after descriptor cleanup");
  Check(clause->descriptor_destroys==1 && clause->frees==1,
        "stock cleanup releases descriptor allocation before destroying native output string");
  std::memset(text,0,32); ++clause->string_destroys; clause->operations.push_back("string_destroy");
}
void DescriptionDestroy(void *description) {
  Check(description==clause->descriptor.data() && clause->string_destroys==0,
        "native stock slot cleanup destroys the current same nonnull descriptor before string cleanup");
  ++clause->descriptor_destroys; clause->operations.push_back("description_destroy");
}
void DescriptionDeallocate(void *description,std::size_t size) {
  Check(description==clause->descriptor.data() && size==0xD8 && clause->descriptor_destroys==1 && clause->frees==0,
        "native description allocation is freed exactly once with its exact D8 size");
  ++clause->frees; clause->operations.push_back("free");
}
void InstallClause(Fixture &fixture,ClauseState &state) {
  clause=&state;
  Put(fixture.ally_object,a::kCharacterRealmOffset,static_cast<void *>(nullptr));
  fixture.can_send=false;
  fixture.bindings.send_precheck=ClausePrecheck;
  fixture.bindings.final_answer=ClauseAnswer;
  fixture.bindings.context.evaluate_trigger=ClauseTrigger;
  fixture.bindings.context.evaluate_cost=ZeroCost;
  fixture.bindings.description_allocate=DescriptionAllocate;
  fixture.bindings.description_deallocate=DescriptionDeallocate;
  fixture.bindings.description_construct=DescriptionConstruct;
  fixture.bindings.describe_trigger=DescribeTrigger;
  fixture.bindings.description_format=DescriptionFormat;
  fixture.bindings.description_destroy=DescriptionDestroy;
  fixture.bindings.description_string_destroy=DescriptionStringDestroy;
  fixture.bindings.description_format_parameters=state.modes.data();
}
void Emit(const a::Snapshot &snapshot,const Fixture &fixture,const char *directory,const char *label) {
  FamilyObligationsObservation12002 observation{};
  observation.snapshot_revision=17; observation.request.ally_character_id=ally;
  observation.frame.date_raw=fixture.frame.clock.date_raw;
  observation.frame.played_character_id=actor;
  observation.frame.paused=observation.frame.map_ready=observation.frame.played_character_alive=true;
  observation.alliance_available=true; observation.alliance=snapshot;
  const auto wire=SerializeFamilyObligationsResult12002(label,observation);
  Check(wire.find("\"native_c88_failure_description_status\":")!=std::string::npos &&
        wire.find("\"native_c88_failure_description_text\":")!=std::string::npos,
        "actual production serializer emits the two new native description observation fields");
  if(!snapshot.first_wars[0].native_selected_target_context_available) {
    Check(wire.find("\"native_c88_failure_description_status\":null")!=std::string::npos &&
          wire.find("\"native_c88_failure_description_text\":null")!=std::string::npos,
          "actual serializer keeps the two unselected native description fields unsampled null");
  } else if(snapshot.first_wars[0].native_c88_failure_description_status=="not_applicable") {
    Check(wire.find("\"native_c88_failure_description_status\":\"not_applicable\"")!=std::string::npos &&
          wire.find("\"native_c88_failure_description_text\":null")!=std::string::npos,
          "actual serializer keeps non-C88 failure text not applicable and null");
  }
  if(directory!=nullptr) {
    std::ofstream output(std::string(directory)+"/"+label+"-native-command-result.json",std::ios::binary);
    output<<wire<<'\n'; Check(bool(output),"actual new serialized native fixture packet written");
  }
}
void ClauseCases(const char *directory) {
  {
    Fixture fixture; ClauseState state; InstallClause(fixture,state);
    a::Snapshot snapshot; std::string_view reason;
    Check(a::Read(fixture.bindings,fixture.frame,actor,ally,snapshot,&reason) && reason.empty() &&
          snapshot.first_wars.size()==1 && snapshot.second_wars.empty(),
          "new C88 clause scenario uses actual production reader and exact current war participant graph");
    const auto &row=snapshot.first_wars[0];
    Check(row.native_selected_target_context_available && !row.native_complete_can_send &&
          !row.native_send_definition_gate_results[1] && row.native_first_failed_send_stage=="definition_c88" &&
          row.recipient_answer_status_raw==0 && row.native_send_answer_status_raw==2 &&
          row.send_cost_raw==std::array<std::int64_t,10>{},
          "same-frame raw C88 false, preview zero, independent internal two and genuine zero immediate quote remain distinct");
    Check(row.native_c88_failure_description_status=="observed" && row.native_c88_failure_description_text==formatted_group,
          "new production getter copies genuine native formatter group text verbatim with markup and UTF8");
    Check(state.operations==std::vector<std::string>{"allocate","construct","evaluate","format","description_destroy","free","string_destroy"} &&
          state.raw_c88_reads==1 && state.evaluations==1 && state.formats==1 && state.frees==1,
          "exact native builder/formatter/string and same-slot owner cleanup sequence once");
    Check(fixture.cost_reads==1 && fixture.constructions==fixture.destructions,
          "existing context and ten-cost observations remain complete and independently cleaned");
    Emit(snapshot,fixture,directory,"c88-native-group-description");
  }
  {
    Fixture fixture; ClauseState state; InstallClause(fixture,state); fixture.pick=false;
    a::Snapshot snapshot; std::string_view reason;
    Check(a::Read(fixture.bindings,fixture.frame,actor,ally,snapshot,&reason) && reason.empty() && snapshot.first_wars.size()==1,
          "new unselected description semantics preserve existing observed actual war row");
    const auto &row=snapshot.first_wars[0];
    Check(!row.native_selected_target_context_available && state.operations.empty(),
          "unselected context never invokes new description builder or formatter");
    Emit(snapshot,fixture,directory,"unselected-description-unsampled");
  }
  {
    Fixture fixture; ClauseState state; state.c88_passed=true; InstallClause(fixture,state);
    a::Snapshot snapshot; std::string_view reason;
    Check(a::Read(fixture.bindings,fixture.frame,actor,ally,snapshot,&reason) && reason.empty() && snapshot.first_wars.size()==1,
          "new non-C88 description semantics use genuine selected native context");
    const auto &row=snapshot.first_wars[0];
    Check(row.native_selected_target_context_available && row.native_send_definition_gate_results[1] &&
          row.native_first_failed_send_stage=="internal_answer" && row.native_c88_failure_description_status=="not_applicable" &&
          state.operations.empty(),
          "non-C88 first failure leaves native description not applicable and invokes zero new callbacks");
    Emit(snapshot,fixture,directory,"non-c88-description-not-applicable");
  }
  std::cout<<"GREEN C88 native group description: 3 new actual production getter/serializer cases; no archived suites\n";
}
}
int main(int argc,char **argv) {
  try { ClauseCases(argc==2?argv[1]:nullptr); return 0; }
  catch(const std::exception &error) { std::cerr<<"RED "<<error.what()<<'\n'; return 1; }
}
