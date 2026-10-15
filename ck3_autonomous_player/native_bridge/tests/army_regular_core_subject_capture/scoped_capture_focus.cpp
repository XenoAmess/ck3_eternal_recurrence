#include "xar_bridge/army_regular_core_passive_12004.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/army_observed_phase_query_12004.hpp"
#include <algorithm>
#include <cstring>
#include <iostream>
#include <fstream>
#include <map>
#include <stdexcept>
#include <vector>

// Narrow pure-reader fixture. It calls the actual candidate Capture function;
// there is no game process, native getter invocation, hook or source EXE read.
namespace {
using namespace xar::ck3_12004;
constexpr std::uintptr_t image=0x10000000,manager=0x20000000,state=0x21000000;
constexpr std::uintptr_t persist=0x30000000,army=0x40000000,unit=0x41000000;
constexpr std::uintptr_t arrg=0x50000000,invalid_arrg=0x50001000,data=0x51000000;
constexpr std::uintptr_t persistent_ids=0x60000000,army_ids=0x60010000,arrg_ids=0x60020000;
constexpr std::uintptr_t registry=0x70000000,table=0x70100000;
constexpr std::uintptr_t army_registry=0x71000000,army_table=0x71001000;
constexpr std::uintptr_t unit_registry=0x72000000,unit_table=0x72001000;
constexpr std::uintptr_t arrg_registry=0x73000000,arrg_table=0x73001000;
constexpr std::int32_t count=4097,target=count,foreign=count-1,owner=17;
struct Memory {
  std::map<std::uintptr_t,std::vector<std::byte>> regions;
  std::uintptr_t fail_address=0;
  std::size_t read_calls=0;
  ArmyRegularCoreBindings12004 bindings;
  void Add(std::uintptr_t a,std::size_t n){if(!regions.emplace(a,std::vector<std::byte>(n)).second)throw std::runtime_error("duplicate fixture region");}
  template<class T>void Put(std::uintptr_t a,T value){auto it=regions.upper_bound(a);if(it==regions.begin())throw std::runtime_error("write unmapped");--it;
    const auto offset=a-it->first;if(offset>it->second.size() || sizeof value>it->second.size()-offset)throw std::runtime_error("write overflow");
    std::memcpy(it->second.data()+offset,&value,sizeof value);}
  static bool Read(void *context,std::uintptr_t a,void *out,std::size_t n)noexcept{
    auto &m=*static_cast<Memory *>(context);++m.read_calls;if(a==m.fail_address)return false;
    auto it=m.regions.upper_bound(a);if(it==m.regions.begin())return false;--it;const auto offset=a-it->first;
    if(offset>it->second.size() || n>it->second.size()-offset)return false;
    std::memcpy(out,it->second.data()+offset,n);return true;
  }
  static std::uintptr_t Persistent(std::int32_t id){return persist+static_cast<std::uintptr_t>(id)*0x200;}
  void Slot(std::uintptr_t rva,std::uintptr_t value){Add(image+rva,8);Put(image+rva,value);}
  void Registry(std::uintptr_t r,std::uintptr_t t,std::int32_t n){Add(r,0x40);Add(t,static_cast<std::size_t>(n)*16);Put(r+0x20,t);Put(r+0x2C,n);}
  Memory(){
    Add(manager,0x100);Add(state,0x100);Add(persist,static_cast<std::size_t>(count+1)*0x200);
    Add(army,0x200);Add(unit,0x200);Add(arrg,0x160);Add(invalid_arrg,0x160);Add(data,48);
    Add(persistent_ids,static_cast<std::size_t>(count+1)*4);Add(army_ids,8);Add(arrg_ids,8);
    Registry(registry,table,count+1);Registry(army_registry,army_table,2);
    Registry(unit_registry,unit_table,2);Registry(arrg_registry,arrg_table,2);
    Slot(0x5D1EB68,registry);Slot(0x5D1EB58,0);Slot(0x5D1DE48,army_registry);Slot(0x5D1DE50,0);
    Slot(0x5D1E380,unit_registry);Slot(0x5D1E378,0);Slot(0x5D1F340,arrg_registry);Slot(0x5D1F338,invalid_arrg);
    Slot(kGameStateSlotRva,state);Put<std::uint64_t>(state+8,0x12345678);
    Put<std::uint32_t>(state+0x9C,1234);Put<std::uint8_t>(state+0xC0,2);
    Put(manager+0x30,persistent_ids);Put<std::int32_t>(manager+0x3C,count+1);
    Put(manager+0x50,army_ids);Put<std::int32_t>(manager+0x5C,2);
    for(std::int32_t id=1;id<=count;++id){const auto p=Persistent(id);Put(table+static_cast<std::size_t>(id)*16+8,p);
      Put(p+0x10,id);Put<std::uint32_t>(p+0x14,0x52656769U);Put<std::int64_t>(p+0x148,10000);
      Put(persistent_ids+static_cast<std::size_t>(id-1)*4,id);
      for(std::int32_t slot=0;slot<7;++slot){const auto chunk=p+0x18+static_cast<std::size_t>(slot)*0x24;
        Put<std::int32_t>(chunk,100);Put<std::int32_t>(chunk+4,50+slot);Put<std::int32_t>(chunk+8,2);
        Put(chunk+0xC,slot);Put<std::int32_t>(chunk+0x10,-1);Put<std::uint8_t>(chunk+0x14,1);Put<std::int32_t>(chunk+0x18,3);}}
    Put(persistent_ids+static_cast<std::size_t>(count)*4,target); // repeated actual manager execution occurrence
    Put(army_table+24,army);Put(unit_table+24,unit);Put(arrg_table+24,arrg);
    Put<std::int32_t>(army_ids,1);Put<std::int32_t>(army_ids+4,1);Put<std::int32_t>(army+0x10,1);
    Put<std::uint32_t>(army+0x14,0x41726D79U);Put<std::int32_t>(army+0x124,1);
    Put(army+0x38,arrg_ids);Put<std::int32_t>(army+0x44,2);Put<std::int32_t>(arrg_ids,1);Put<std::int32_t>(arrg_ids+4,1);
    Put<std::int32_t>(unit+0x10,1);Put<std::uint32_t>(unit+0x14,0x556E6974U);Put<std::int32_t>(unit+0x174,owner);Put<std::int32_t>(unit+0x178,1);
    Put<std::int32_t>(arrg+0x10,1);Put<std::uint32_t>(arrg+0x14,0x41725267U);Put<std::int32_t>(arrg+0x148,-1);
    Put(arrg+0x20,data);Put<std::int32_t>(arrg+0x2C,3);Put<std::int32_t>(invalid_arrg+0x10,-1);
    Put<std::int32_t>(data+8,target);Put<std::int32_t>(data+12,0);
    Put<std::int32_t>(data+24,target);Put<std::int32_t>(data+28,0); // duplicate DATA alias, not another delta
    Put<std::int32_t>(data+40,foreign);Put<std::int32_t>(data+44,1);
    bindings=BindArmyRegularCoreImage12004(image,kExecutableSha256);bindings.read_context=this;bindings.read=&Read;
  }
  void Scoped(){ArmyRegularCoreSubjectScope12004 s;s.scope_epoch=7;s.game_state_identity=state;s.owner_character_id=owner;s.full_carmy_ids={1};s.allowed_public_unit_ids={1};bindings.subject_scope=std::move(s);}
  ArmyRegularCoreFrame12004 Capture(){return CaptureArmyRegularCoreFrame12004(bindings,reinterpret_cast<void *>(manager));}
};
std::size_t checks=0;
void Check(bool value,const char *name){++checks;if(!value)throw std::runtime_error(name);}
void Incomplete(Memory &m,const char *name){const auto f=m.Capture();Check(f.subject_coverage_v1 && !f.subject_coverage_v1->physical_closure_complete,name);}
Memory *active=nullptr;
std::size_t original_calls=0;
constexpr std::uintptr_t opaque=0xFEDCBA9876543210ULL;
ArmyRegularCoreObservation12004 observed;
std::uintptr_t __fastcall Original(void *){++original_calls;active->Put<std::int32_t>(Memory::Persistent(target)+0x1C,55);return opaque;}
std::uintptr_t __fastcall ParentOriginal(void *secondary){observed=InvokeArmyRegularCorePassive12004(active->bindings,&Original,
  reinterpret_cast<void *>(reinterpret_cast<std::uintptr_t>(secondary)-8),kArmyRegularCoreCallerReturnRva12004);return observed.raw_return_bits;}
}
int main(int argc,char **argv){try{
  Memory old;const auto global=old.Capture();Check(!global.capture_complete && !global.subject_coverage_v1,"legacy global remains bounded without new field");
  Memory m;m.Scoped();const auto frame=m.Capture();const auto &c=*frame.subject_coverage_v1;
  Check(!frame.capture_complete && c.physical_closure_complete && c.manager_occurrences_complete,"scoped raw coverage independently complete");
  Check(frame.persistent_occurrences.size()==static_cast<std::size_t>(count+1) && frame.army_refresh_occurrences.size()==2,"all manager source rows retained");
  Check(frame.persistent_occurrences.back().stored_index==count && frame.persistent_occurrences.back().raw_full_id==target,"duplicate occurrence ordinal retained");
  Check(frame.persistent_objects.size()==2 && frame.army_objects.size()==1,"only closure physical objects materialized");
  Check(frame.persistent_objects[0].resolved_full_id==foreign && frame.persistent_objects[1].resolved_full_id==target,"original manager first-known object order restored");
  Check(frame.persistent_objects[0].chunks.size()==7 && frame.persistent_objects[1].chunks.size()==7 && frame.persistent_objects[0].chunks[1].owner_persistent_regiment_id==2,"foreign receiver keeps all seven physical slots");
  Check(frame.army_objects[0].arrg_occurrences.size()==2 && frame.army_objects[0].arrg_occurrences[0].records.size()==3 && frame.army_objects[0].arrg_occurrences[1].records.size()==3,"all repeated ArRg DATA aliases retained");
  {Memory x;x.Scoped();x.bindings.maximum_physical_objects=2;auto f=x.Capture();Check(f.persistent_objects.size()+f.army_objects.size()<=2,"combined cap not exceeded by pending Army");Check(!f.subject_coverage_v1->physical_closure_complete,"target closure over cap remains incomplete");}
  {Memory x;x.Scoped();x.Put<std::int32_t>(unit+0x174,owner+1);Incomplete(x,"changed owner refused");}
  {Memory x;x.Scoped();x.Put(image+kGameStateSlotRva,state+0x100);Incomplete(x,"changed game state refused");}
  {Memory x;x.Scoped();x.Put<std::int32_t>(army+0x10,0x1000001);Incomplete(x,"generation reuse refused");}
  {Memory x;x.Scoped();x.Put<std::int32_t>(unit+0x178,2);Incomplete(x,"wrong Unit CArmy backref refused");}
  {Memory x;x.Scoped();x.Put<std::uintptr_t>(table+4090*16+8,0);Incomplete(x,"unknown outside-closure manager occurrence not dropped");}
  {Memory x;x.Scoped();x.Put<std::int32_t>(manager+0x5C,0);Incomplete(x,"subject absent from original manager refused");}
  {Memory x;x.Scoped();x.Put<std::int32_t>(data+12,7);Incomplete(x,"invalid DATA chunk index refused");}
  {Memory x;x.Scoped();x.fail_address=Memory::Persistent(target)+0x18;Incomplete(x,"unreadable seven slots refused");}
  {Memory x;x.Scoped();x.bindings.maximum_read_bytes=64;Incomplete(x,"read budget remains bounded");}
  {Memory x;x.Scoped();x.bindings.subject_scope->full_carmy_ids.push_back(1);Incomplete(x,"duplicate selected full ID refused");}
  {Memory x;x.Scoped();x.Put<std::int32_t>(arrg_ids,0x1000001);x.Put(image+0x5D1F338,arrg);const auto f=x.Capture();Check(f.army_objects[0].arrg_occurrences[0].occurrence.used_fallback==true && !f.subject_coverage_v1->physical_closure_complete,"actual ArRg fallback bytes retained but scoped qualification refused");}
  {Memory x;x.Scoped();x.Put<std::int32_t>(data+8,0x1000000|target);x.Put(image+0x5D1EB58,Memory::Persistent(target));const auto f=x.Capture();Check(f.army_objects[0].arrg_occurrences[0].records[0].native_record_admitted && !f.subject_coverage_v1->physical_closure_complete,"actual DATA fallback physical bytes retained but scoped qualification refused");}
  Memory connected;active=&connected;
  Check(InitializeArmyRegularCoreFixture12004(connected.bindings,&Original),"actual fixture initialization");
  Check(!SetArmyRegularCoreScopedResearchSampling12004({1,1},owner,{1}),"duplicate bind rejected before enable");
  Check(!SetArmyRegularCoreScopedResearchSampling12004({1},owner,{1,1}),"ambiguous fresh public membership refused");
  Check(SetArmyRegularCoreScopedResearchSampling12004({1},owner,{1}),"actual scoped setter binds and enables");
  const auto sampling=ReadArmyRegularCoreResearchSampling12004();
  Check(sampling.enabled && !sampling.busy,"sampling independently read back enabled");
  Check(!SetArmyRegularCoreScopedResearchSampling12004({1},owner,{1}),"already enabled explicit rebind refused");
  ArmyNaturalPhaseBindings12004 parent;parent.read_context=&connected;parent.read=&Memory::Read;parent.game_state_identity=state;
  const auto parent_record=InvokeArmyNaturalPhaseScope12004(parent,&ParentOriginal,reinterpret_cast<void *>(manager+8),ArmyNaturalPhaseKind12004::post_date,0xAA001);
  Check(original_calls==1 && observed.raw_return_bits==opaque && parent_record.raw_return_bits==opaque,"natural original once and opaque return");
  Check(observed.entry_provenance_complete && observed.return_provenance_complete && observed.entry.subject_coverage_v1 && observed.returned.subject_coverage_v1 && observed.entry.subject_coverage_v1->physical_closure_complete && observed.returned.subject_coverage_v1->physical_closure_complete,"actual natural entry return capture closure");
  Check(observed.entry.subject_coverage_v1->scope_epoch==sampling.epoch && observed.returned.subject_coverage_v1->scope_epoch==sampling.epoch,"actual setter sampling epoch retained");
  auto journal=ReadSampledArmyRegularCoreJournal12004();
  Check(journal && journal->events.size()==1,"actual owned retained journal read");
  const auto read_calls=connected.read_calls;journal->events[0].entry.persistent_occurrences.clear();
  Check(ReadSampledArmyRegularCoreJournal12004()->events[0].entry.persistent_occurrences.size()==static_cast<std::size_t>(count+1) && connected.read_calls==read_calls,"query owned copy isolates retention without resampling");
  std::string wire="{\"schema_version\":1,\"source\":\"native_natural_army_regular_core_entry_return\",\"membership_basis\":\"captured_core_entry_resolved_Army_roster_full_ID\",\"observer_initialized\":true,\"observer_installed\":false,\"latest_journal_sequence\":1,\"overwritten_events\":0,\"publication_failures\":0,\"events\":[";
  xar::game::observed_assault_json_12004::CoreEvent(wire,observed,[](auto x){return std::to_string(x);},[](std::string &out,std::string_view x){out+='"';for(const auto ch:x){if(ch=='"'||ch=='\\')out+='\\';out+=ch;}out+='"';});wire+="]}";
  if(argc!=2)throw std::runtime_error("serialized wire output required");std::ofstream file(argv[1],std::ios::binary);file<<wire;file.close();Check(static_cast<bool>(file),"real serializer wire file written");
  const auto disabled=SetArmyRegularCoreResearchSampling12004(false);Check(!disabled.enabled && disabled.clear_completed && ReadArmyRegularCoreJournal12004().events.empty(),"disable clear retained scope journal");
  const auto global_enabled=SetArmyRegularCoreResearchSampling12004(true);Check(global_enabled.enabled,"old boolean reenable restores default global policy");SetArmyRegularCoreResearchSampling12004(false);
  std::cout<<"{\"checks\":"<<checks<<",\"failed\":0,\"kind\":\"actual_candidate_pure_capture_mock_memory\"}\n";return 0;
}catch(const std::exception &e){std::cerr<<"fixture check failed: "<<e.what()<<'\n';return 1;}}
