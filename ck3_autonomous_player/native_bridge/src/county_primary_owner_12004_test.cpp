// Source-focused cold only. Every address refers to owned fixture memory.
#include "xar_bridge/ck3_12004_actual_loss_writer_journal.hpp"
#include "xar_bridge/county_primary_owner_at_writer_12004.hpp"
#include <array>
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <string>
#include <windows.h>
namespace n=xar::ck3_12004;
extern "C" void XarCountyPrimaryFixtureInvoke12004(void*,std::int64_t,const void*);
extern "C" const char XarCountyPrimaryFixtureReturn12004;
namespace {
void Need(bool x,const char *s){if(!x)throw std::runtime_error(s);}
template<class T,std::size_t N>void Put(std::array<std::byte,N> &a,std::size_t o,T v){
  Need(o<=N&&sizeof v<=N-o,"fixture range");std::memcpy(a.data()+o,&v,sizeof v);
}
constexpr std::int32_t rid=0x03000001;
constexpr std::uint64_t date=53147544;
std::array<std::byte,0x50> reg{};
std::array<std::byte,0x130> army{};
std::array<std::byte,0x10> data{},state{};
std::array<std::byte,0x20> physical{};
std::array<std::int32_t,1> roster{rid};
void *state_slot=state.data();
std::uint32_t calls=0;
n::CountyPrimaryPhaseCapture12004 phase;
n::ArmyNaturalPhaseEvent12004 Token(std::uint64_t seq){return {0x123456,seq,GetCurrentThreadId()};}
n::CountyPrimaryPhaseCapture12004 Phase() noexcept {return phase;}
void *__fastcall Select(void *p){return p==data.data()?physical.data():nullptr;}
void __fastcall Original(void *p,std::int64_t request){
 ++calls;Need(p==reg.data()&&request==700000,"original ABI changed");
 Put(reg,0x38,std::int32_t{93});Put(physical,4,std::int32_t{93});
}
bool Read(void*,const void *p,void *out,std::size_t size) noexcept {
 if(!p)return false;std::memcpy(out,p,size);return true;
}
void Setup(){
 phase.sampling.available=true;phase.sampling.enabled=true;phase.sampling.epoch=1;
 Put(reg,0x10,rid);Put(reg,0x14,std::uint32_t{0x41725267});
 Put(reg,0x20,static_cast<void*>(data.data()));Put(reg,0x28,std::int32_t{1});
 Put(reg,0x2c,std::int32_t{1});Put(reg,0x38,std::int32_t{100});Put(reg,0x3c,std::int32_t{120});
 Put(data,8,std::int32_t{0x05000001});Put(data,12,std::int32_t{0});
 Put(physical,0,std::int32_t{120});Put(physical,4,std::int32_t{100});
 Put(physical,8,std::int32_t{0x05000001});Put(physical,12,std::int32_t{0});
 Put(physical,16,rid);Put(physical,24,std::int32_t{1});
 Put(army,0x10,std::int32_t{0});Put(army,0x14,std::uint32_t{0x41726D79});
 Put(army,0x124,std::int32_t{0});Put(army,0x38,static_cast<void*>(roster.data()));
 Put(army,0x40,std::int32_t{1});Put(army,0x44,std::int32_t{1});Put(state,8,date);
 auto &s=phase.scope;s.observed=true;s.phase=n::ArmyNaturalPhaseKind12004::pre_date;
 s.actual_entry_rva=0x2A99DA0;s.primary_manager_identity=0x10000;
 s.game_state_identity=reinterpret_cast<std::uintptr_t>(state.data());
 s.entry_event=Token(10);s.prefix_date_raw=date;
 auto &r=s.original_army_roster;r.complete=true;r.boundary=n::ArmyNaturalRosterBoundary12004::pre_date_prefix_return;
 r.capture_rva=0x2A99E76;r.capture_event=Token(20);r.ordered_full_ids={0};phase.writer_event=Token(30);
}
}
int main(){
 try {
  Setup();n::ActualLossWriterJournalBindingsV1 b{};b.enabled=true;
  // Synthetic image base makes the owned return label the held return RVA.
  // No CK3 image is scanned, loaded, patched or called.
  b.image_base=reinterpret_cast<std::uintptr_t>(&XarCountyPrimaryFixtureReturn12004)-0x24E25EE;
  b.game_state_slot=&state_slot;b.select_physical_slot=&Select;b.county_primary_phase_reader=&Phase;
  Need(n::InitializeActualLossWriterJournalFixture12004(b,&Original),"fixture init");
  XarCountyPrimaryFixtureInvoke12004(reg.data(),700000,army.data());
  auto f=n::ReadActualLossWriterObservations12004(roster);
  Need(calls==1&&f&&f->events.size()==1,"original not exactly once");
  const auto &e=f->events[0];const auto &c=e.county_primary_owner_at_writer_v1;
  Need(c&&c->source_complete&&c->army_id==0&&c->native_carmy_id==0,"R13 Army0 not captured");
  Need(c->source_carmy_identity==reinterpret_cast<std::uintptr_t>(army.data())&&
       c->writer_receiver_identity==reinterpret_cast<std::uintptr_t>(reg.data()),"incoming receiver changed");
  Need(e.actual_physical_soldier_debit==7&&e.physical_capture_complete,"physical proof lost");
  std::string wire;xar::game::AppendArmyCountyPrimaryOwnerAtWriterV1(wire,*c);
  Need(wire.find("\"army_id\":0")!=std::string::npos,"Army0 serializer lost");
  std::cout<<"{\"case\":\"actual_thunk_original_once_Army0_physical7\",\"owner\":"<<wire<<"}\n";
  n::CountyPrimaryWriterRegisters12004 call{reg.data(),army.data(),0x24E25EE,99,GetCurrentThreadId()};
  auto bad=phase;bad.writer_event.thread_id=GetCurrentThreadId()+1;
  auto x=n::CaptureCountyPrimaryOwnerAtWriter12004(&Read,nullptr,call,bad,rid,
      static_cast<std::int32_t>(date),reinterpret_cast<std::uintptr_t>(state.data()));
  Need(x&&!x->source_complete,"cross-thread accepted");
  bad=phase;bad.scope.original_army_roster.ordered_full_ids={1};
  x=n::CaptureCountyPrimaryOwnerAtWriter12004(&Read,nullptr,call,bad,rid,
      static_cast<std::int32_t>(date),reinterpret_cast<std::uintptr_t>(state.data()));
  Need(x&&!x->source_complete,"foreign Army roster accepted");
  call.caller_return_rva=0x24E35FF;
  Need(!n::CaptureCountyPrimaryOwnerAtWriter12004(&Read,nullptr,call,phase,rid,
      static_cast<std::int32_t>(date),reinterpret_cast<std::uintptr_t>(state.data())),"foreign caller accepted");
  std::cout<<"{\"case\":\"cross_thread_foreign_roster_foreign_caller_rejected\",\"qualified\":true}\n";
  return 0;
 }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
