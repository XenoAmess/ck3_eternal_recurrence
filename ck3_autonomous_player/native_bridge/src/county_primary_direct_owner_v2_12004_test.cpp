// Cold synthetic memory only. This target never loads or calls a CK3 image.
#include "xar_bridge/ck3_12004_actual_loss_writer_journal.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
namespace n=xar::ck3_12004;
extern "C" void XarCountyPrimaryFixtureInvoke12004(void *,std::int64_t,const void *,void *);
extern "C" void XarActualLossWriterCountyEntryThunk12004V1(void *,std::int64_t) noexcept;
extern "C" const char XarCountyPrimaryFixtureReturn12004;
namespace {
void Need(bool ok,const char *message){if(!ok)throw std::runtime_error(message);}
template<class T,std::size_t N>void Put(std::array<std::byte,N> &a,std::size_t off,T v){
  Need(off<=N&&sizeof v<=N-off,"fixture range");std::memcpy(a.data()+off,&v,sizeof v);
}
template<std::size_t N>bool In(const std::array<std::byte,N> &a,const void *p,std::size_t size){
  const auto b=reinterpret_cast<std::uintptr_t>(a.data()),x=reinterpret_cast<std::uintptr_t>(p);
  return x>=b&&x-b<=N&&size<=N-(x-b);
}
constexpr std::int32_t rid=0x03000001,pid=0x05000001;
constexpr std::uint64_t date=53147544;
std::array<std::byte,0x50> regiment{};
std::array<std::byte,0x130> army{},foreign_army{};
std::array<std::byte,0x180> unit{};
std::array<std::byte,0x120> persistent{};
std::array<std::byte,0x20> data{},state{},fake_physical{};
std::array<std::byte,0x30> ah{},uh{},rh{},ph{};
std::array<std::byte,0x20> ae{},ue{},re{},pe{};
std::array<std::int32_t,1> roster{rid};
void *as=ah.data(),*us=uh.data(),*rs=rh.data(),*ps=ph.data(),*ss=state.data();
bool sampling_on=true,wrong_selector=false,nested_unknown=false;
std::uint32_t calls=0,army_reads=0;
std::uint64_t clock_sequence=0;
n::CountyPrimaryPhaseCapture12004 phase{};
n::ArmyObserverResearchSamplingState12004 Sampling() noexcept {
  n::ArmyObserverResearchSamplingState12004 s{};s.available=true;s.enabled=sampling_on;s.epoch=1;return s;
}
n::CountyPrimaryPhaseCapture12004 Phase() noexcept {
  auto v=phase;v.sampling=Sampling();if(!v.sampling.enabled)return v;
  v.writer_event={0xABCDEF,++clock_sequence,GetCurrentThreadId()};return v;
}
void *__fastcall Select(void *p){
  return p==data.data()?(wrong_selector?static_cast<void *>(fake_physical.data()):persistent.data()+0x18):nullptr;
}
bool Read(void *,const void *p,void *out,std::size_t size)noexcept {
  if(!p)return false;
  if(In(army,p,size)||In(foreign_army,p,size))++army_reads;
  bool ok=In(regiment,p,size)||In(army,p,size)||In(foreign_army,p,size)||In(unit,p,size)||
    In(persistent,p,size)||In(data,p,size)||In(state,p,size)||In(fake_physical,p,size);
  const auto x=reinterpret_cast<std::uintptr_t>(p),b=reinterpret_cast<std::uintptr_t>(roster.data());
  ok=ok||(x>=b&&x-b<=sizeof roster&&size<=sizeof roster-(x-b));
  if(p==&ss&&size==sizeof ss)ok=true;
  // Actual MASM return slot is fixture-owned stack memory, read by the journal.
  // ReadProcessMemory provides a guarded copy for that one real stack source.
  if(!ok){SIZE_T got=0;return ReadProcessMemory(GetCurrentProcess(),p,out,size,&got)&&got==size;}
  std::memcpy(out,p,size);return true;
}
void __fastcall Original(void *p,std::int64_t request){
  ++calls;Need(p==regiment.data()&&request==700000,"original ABI changed");
  if(nested_unknown){nested_unknown=false;n::InvokeActualLossWriterJournalWithCaller12004V1(p,request,0x111111);}
  Put(regiment,0x38,std::int32_t{93});Put(persistent,0x1C,std::int32_t{93});
  Put(fake_physical,4,std::int32_t{93});
}
template<std::size_t N>void Registry(std::array<std::byte,0x30> &header,
    std::array<std::byte,0x20> &entries,std::int32_t id,std::array<std::byte,N> &object){
  Put(header,0x20,static_cast<void *>(entries.data()));Put(header,0x2C,std::int32_t{2});
  const auto index=static_cast<std::uint32_t>(id)&0xFFFFFFU;
  Put(entries,static_cast<std::size_t>(index)*0x10+8,static_cast<void *>(object.data()));
}

// All executable bytes are owned by this cold process. No CK3 address is used.
constexpr std::array<std::uint8_t,15> writer_prologue{
  0x40,0x53,0x41,0x57,0x48,0x83,0xEC,0x38,0x81,0x79,0x14,0x67,0x52,0x72,0x41};
constexpr std::array<std::uint8_t,7> writer_restorer{0x48,0x83,0xC4,0x38,0x41,0x5F,0x5B};
void *owned_writer=nullptr;
n::ActualLossWriterJournalDetourStateV1 installed_state{};
bool Released(const void *p) noexcept {
  MEMORY_BASIC_INFORMATION info{};
  return VirtualQuery(p,&info,sizeof info)==sizeof info&&info.State==MEM_FREE;
}
bool CleanupInstalled() noexcept {
  if(installed_state.installed.load(std::memory_order_acquire)!=0){
    const void *trampoline=installed_state.trampoline;
    if(!trampoline||!n::UninstallActualLossWriterJournal12004(installed_state,true))return false;
    if(installed_state.installed.load(std::memory_order_acquire)!=0||installed_state.trampoline||
       !Released(trampoline)||n::ReadActualLossWriterObservations12004(roster).has_value())return false;
  }
  if(owned_writer){
    if(std::memcmp(owned_writer,writer_prologue.data(),writer_prologue.size())!=0)return false;
    const void *old=owned_writer;
    if(VirtualFree(owned_writer,0,MEM_RELEASE)==FALSE)return false;
    owned_writer=nullptr;
    if(!Released(old))return false;
  }
  return true;
}
struct InstallationScope {
  ~InstallationScope(){if(!CleanupInstalled())std::cerr<<"owned installer cleanup failed\n";}
};

void Setup(){
  Need(CleanupInstalled(),"previous owned installation cleanup");
  regiment={};army={};foreign_army={};unit={};persistent={};data={};state={};fake_physical={};
  ah={};uh={};rh={};ph={};ae={};ue={};re={};pe={};phase={};
  sampling_on=true;wrong_selector=false;nested_unknown=false;calls=army_reads=0;clock_sequence=0;roster={rid};
  Put(regiment,0x10,rid);Put(regiment,0x14,std::uint32_t{0x41725267});
  Put(regiment,0x20,static_cast<void *>(data.data()));Put(regiment,0x28,std::int32_t{1});Put(regiment,0x2C,std::int32_t{1});
  Put(regiment,0x38,std::int32_t{100});Put(regiment,0x3C,std::int32_t{120});
  Put(data,8,pid);Put(data,12,std::int32_t{0});Put(persistent,0x10,pid);Put(persistent,0x14,std::uint32_t{0x52656769});
  Put(persistent,0x18,std::int32_t{120});Put(persistent,0x1C,std::int32_t{100});
  Put(persistent,0x20,pid);Put(persistent,0x24,std::int32_t{0});Put(persistent,0x28,rid);
  std::memcpy(fake_physical.data(),persistent.data()+0x18,0x1C);
  Put(army,0x10,std::int32_t{0});Put(army,0x14,std::uint32_t{0x41726D79});Put(army,0x124,std::int32_t{0});
  Put(army,0x38,static_cast<void *>(roster.data()));Put(army,0x40,std::int32_t{1});Put(army,0x44,std::int32_t{1});
  foreign_army=army;Put(unit,0x10,std::int32_t{0});Put(unit,0x178,std::int32_t{0});Put(state,8,date);
  Registry(ah,ae,0,army);Registry(uh,ue,0,unit);Registry(rh,re,rid,regiment);Registry(ph,pe,pid,persistent);
}
void Init(){
  n::ActualLossWriterJournalBindingsV1 b{};b.enabled=true;
  b.image_base=reinterpret_cast<std::uintptr_t>(&XarCountyPrimaryFixtureReturn12004)-0x24E25EE;
  b.game_state_slot=&ss;b.select_physical_slot=&Select;b.read_memory=&Read;
  b.county_primary_phase_reader=&Phase;b.county_direct_sampling_reader=&Sampling;b.county_direct_source_qualified=true;
  b.county_army_registry_slot=&as;b.county_unit_registry_slot=&us;b.county_arrg_registry_slot=&rs;b.county_regi_registry_slot=&ps;

  Need(!owned_writer&&installed_state.installed.load(std::memory_order_acquire)==0,"fixture already installed");
  // Reproduce the source-exact prologue, undo its stack saves, then tail-call
  // the owned Original. The production installer supplies the real trampoline.
  static_assert(sizeof(std::uintptr_t)==8);
  std::array<std::uint8_t,36> stub{};
  std::memcpy(stub.data(),writer_prologue.data(),writer_prologue.size());
  std::memcpy(stub.data()+15,writer_restorer.data(),writer_restorer.size());
  constexpr std::array<std::uint8_t,6> jump{0xFF,0x25,0,0,0,0};
  std::memcpy(stub.data()+22,jump.data(),jump.size());
  const auto original=reinterpret_cast<std::uintptr_t>(&Original);
  std::memcpy(stub.data()+28,&original,sizeof original);
  owned_writer=VirtualAlloc(nullptr,stub.size(),MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE);
  Need(owned_writer!=nullptr,"allocate owned writer");
  std::memcpy(owned_writer,stub.data(),stub.size());DWORD previous=0;
  Need(VirtualProtect(owned_writer,stub.size(),PAGE_EXECUTE_READ,&previous)!=FALSE,"protect owned writer");
  Need(FlushInstructionCache(GetCurrentProcess(),owned_writer,stub.size())!=FALSE,"flush owned writer");
  n::ActualLossWriterJournalInstallEnvironmentV1 environment{};
  environment.bindings=b;
  // Only this single cold-test thread owns or can call the newly allocated code.
  environment.primary_thread_suspended_proven=true;
  environment.writer_target_override=reinterpret_cast<std::uintptr_t>(owned_writer);
  Need(n::InstallActualLossWriterJournal12004(installed_state,environment,n::kExecutableSha256),"install owned writer");
  Need(installed_state.installed.load(std::memory_order_acquire)==1&&installed_state.trampoline&&
       installed_state.failure_flags.load(std::memory_order_acquire)==0,"installed state readback");
  Need(std::memcmp(owned_writer,jump.data(),jump.size())==0,"owned target hook prefix");
  std::uintptr_t destination=0;std::memcpy(&destination,static_cast<const std::byte *>(owned_writer)+6,sizeof destination);
  Need(destination==reinterpret_cast<std::uintptr_t>(&XarActualLossWriterCountyEntryThunk12004V1),"owned target hook destination");
}
void InvokeInstalled(const void *source){
  Need(owned_writer&&installed_state.installed.load(std::memory_order_acquire)==1,"call requires real installation");
  XarCountyPrimaryFixtureInvoke12004(regiment.data(),700000,source,owned_writer);
}
std::string results;
void Retain(const char *name,const xar::game::ArmyActualLossWriterObservationsV1 &v){
  Need(v.observer_installed,"wire requires actual installed observer");
  if(!results.empty())results+=',';results+="{\"case\":\"";results+=name;
  results+="\",\"synthetic_fixture_only\":true,\"observations\":";
  xar::game::AppendArmyActualLossWriterObservationsV1(results,v);results+='}';
}
void Run(const char *name,std::uint32_t expected_flags=0,bool thunk=true,const void *source=nullptr){
  Init();if(thunk)InvokeInstalled(source?source:army.data());
  else n::InvokeActualLossWriterJournalWithCaller12004V1(regiment.data(),700000,0x24E25EE);
  auto v=n::ReadActualLossWriterObservations12004(roster);Need(v.has_value(),"missing query");
  Need(calls==1,"original invocation count");Need(v->events.size()==1,"selected event count");
  const auto &e=v->events.front();Need(e.county_primary_direct_owner_at_writer_v2.has_value(),"direct child missing");
  const auto &o=*e.county_primary_direct_owner_at_writer_v2;
  if(expected_flags){Need(!o.source_complete&&(o.capture_failure_flags&expected_flags)==expected_flags,"negative source complete");}
  else Need(o.source_complete&&o.capture_failure_flags==0&&o.army_id==0&&o.native_carmy_id==0,"direct Army0 complete");
  Retain(name,*v);
}
}
int main(int argc,char **argv){InstallationScope lifetime;try {
  Need(argc==2,"usage: target NEW_C_WIRE_PATH");
  Setup();Run("ON_no_phaseTLS_direct_Army0_physical7");
  Setup();phase.scope.observed=true;phase.scope.phase=n::ArmyNaturalPhaseKind12004::post_date;
  phase.scope.actual_entry_rva=0x2A9A570;Run("ON_postDate_direct_complete_v1_absent");
  Setup();Run("ON_no_registerTLS_diagnostic",n::county_direct_registers_missing,false);
  Setup();Run("forged_R13_magic_only_rejected",n::county_direct_army_registry,true,foreign_army.data());
  Setup();Put(ae,8,static_cast<void *>(foreign_army.data()));Run("wrong_army_registry",n::county_direct_army_registry);
  Setup();Put(unit,0x178,std::int32_t{1});Run("cross_army_unit_backlink",n::county_direct_bidirectional);
  Setup();Put(re,0x18,static_cast<void *>(foreign_army.data()));Run("wrong_ArRg_registry",n::county_direct_writer_registry);
  Setup();roster[0]=0x03000002;Init();
  InvokeInstalled(army.data());
  {const std::array<std::int32_t,1> filter{rid};auto v=n::ReadActualLossWriterObservations12004(filter);
   Need(v&&v->events.size()==1&&!v->events[0].county_primary_direct_owner_at_writer_v2->source_complete,"foreign actual roster");Retain("writer_missing_actual_array",*v);}
  Setup();wrong_selector=true;Run("raw_physical_pointer_mismatch",n::county_direct_physical_association);
  Setup();Put(persistent,0x28,std::int32_t{0x03000002});Run("physical_backlink_other_ArRg",n::county_direct_physical_association);
  Setup();Put(persistent,0x14,std::uint32_t{0x41725267});Run("wrong_Regi_registry_type",n::county_direct_physical_association);
  Setup();phase.writer_event.thread_id=GetCurrentThreadId()+1;
  // Pure capture makes independent event-TID mismatch explicit, without a setter.
  {n::CountyPrimaryWriterRegisters12004 r{regiment.data(),army.data(),0x24E25EE,99,GetCurrentThreadId()};
   auto active=Phase();active.writer_event.thread_id=GetCurrentThreadId()+1;
   xar::game::ArmyActualLossWriterObservationV1 e{};e.caller_return_rva=0x24E25EE;e.army_regiment_id=rid;e.observed_date_raw=static_cast<std::int32_t>(date);
   n::CountyDirectPhysicalInputs12004 p{};
   auto o=n::CaptureCountyPrimaryDirectOwnerAtWriter12004(&Read,nullptr,nullptr,nullptr,&r,active,e,p,
      regiment.data(),GetCurrentThreadId(),reinterpret_cast<std::uintptr_t>(state.data()),true);
   Need((o.capture_failure_flags&n::county_direct_writer_event)!=0,"cross TID accepted");}
  Setup();sampling_on=false;Init();InvokeInstalled(army.data());
  {auto v=n::ReadActualLossWriterObservations12004(roster);Need(v&&calls==1&&army_reads==0&&
    !v->events[0].county_primary_direct_owner_at_writer_v2,"OFF owner read/capture");Retain("OFF_owner_capture_absent_original_once",*v);}
  Setup();Init();n::InvokeActualLossWriterJournalWithCaller12004V1(regiment.data(),700000,0x111111);
  {auto v=n::ReadActualLossWriterObservations12004(roster);Need(v&&calls==1&&army_reads==0&&
    !v->events[0].county_primary_direct_owner_at_writer_v2,"unknown caller borrowed owner");Retain("unknown_caller_no_owner",*v);}
  Setup();nested_unknown=true;Init();InvokeInstalled(army.data());
  {auto v=n::ReadActualLossWriterObservations12004(roster);Need(v&&calls==2&&v->events.size()==2&&
    !v->events[0].county_primary_direct_owner_at_writer_v2&&v->events[1].county_primary_direct_owner_at_writer_v2,"nested unknown borrowed outer");Retain("nested_unknown_masks_outer_context",*v);}
  Setup();Put(regiment,0x14,std::uint32_t{0});Init();InvokeInstalled(army.data());
  {auto v=n::ReadActualLossWriterObservations12004(roster);Need(v&&calls==1&&v->events.empty()&&v->latest_sequence==0&&
    v->unattributed_capture_failures==1&&v->unbound_county_primary_direct_diagnostics_v2.size()==1&&
    !v->unbound_county_primary_direct_diagnostics_v2[0].source_complete,"unbound diagnostic not retained");Retain("unreadable_ArRg_unbound_diagnostic_old_global_unchanged",*v);}
  Need(CleanupInstalled(),"final owned installation cleanup");
  const std::filesystem::path output=argv[1];Need(!std::filesystem::exists(output),"wire output must be new");
  std::filesystem::create_directories(output.parent_path());std::ofstream f(output,std::ios::binary);
  Need(static_cast<bool>(f),"wire open");f<<"{\"schema\":\"xar.county-primary-direct-owner-v2.cold.v1\",\"live_qualification\":false,\"cases\":["<<results<<"]}\n";
  f.close();Need(static_cast<bool>(f),"wire write");std::cout<<"cold fixture passed\n";return 0;
 }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}}
