#include "xar_bridge/ck3_1210_event_options_v1.hpp"
#include <bit>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <vector>
namespace {
using namespace xar::ck3_1210;
void Require(bool value,const char *why) {if(!value){std::cerr<<"FAIL "<<why<<'\n';std::exit(1);}}
template<class B,class T>void Put(B &b,std::size_t at,T value) {
  Require(at<=b.size() && sizeof(value)<=b.size()-at,"fixture bounds");std::memcpy(b.data()+at,&value,sizeof(value));
}
struct Fixture;Fixture *active=nullptr;
void *Player(void *);void *Select(void *);bool Enabled(const void *);
struct Fixture {
  std::array<std::byte,0xA8> state{};std::array<std::byte,0x21> jomini{};
  std::array<std::byte,0x200> players{};std::array<std::byte,0x78> player{};
  std::vector<std::byte> data=std::vector<std::byte>(kCurrentEventManagerOffsetV1+0x1F28);
  std::array<std::byte,0xE0> entry{};std::array<void *,1> entries{entry.data()};
  std::array<std::byte,0x1D8> actor{};std::array<std::byte,0x30> storage{};
  std::array<std::byte,0x20> slots{};std::array<std::byte,0x1C8> event{};
  std::array<std::byte,0x148> definition{};std::array<std::byte,1> payload{};
  std::array<void *,3> authored{payload.data(),payload.data(),payload.data()};
  std::array<void *,1> queue{event.data()};
  std::array<std::byte,0x30> idler{},manager{};
  std::array<std::byte,0x8F0> window{},second_window{};
  std::array<void *,2> windows{window.data(),second_window.data()};
  std::array<std::byte,0x1B8*2> items{};
  void *state_pointer=state.data(),*jomini_pointer=jomini.data(),*storage_pointer=storage.data();
  std::int32_t id=std::bit_cast<std::int32_t>(std::uint32_t{0x81000001});
  EventOptionsBindingsV1 b{};unsigned enabled_calls=0;bool mutate=false;
  Fixture() {
    active=this;b=BindEventOptionsImageV1(0x140000000,kExecutableSha256);
    b.source_abi_pins_verified=true; // Explicit in-memory fixture; not a loaded-image admission.
    b.current.core={true,&state_pointer,&jomini_pointer,&storage_pointer,&Player};
    b.current.get_current_event=&Select;b.current.selector_character_id_slot=&id;b.can_select=&Enabled;
    Put(state,8,std::int32_t{123456});Put(state,0x70,std::int32_t{4});Put(state,0xA0,data.data());
    Put(jomini,0x10,idler.data());Put(jomini,0x18,players.data());jomini[0x20]=std::byte{1};
    Put(players,0x1F0,std::int32_t{7});Put(player,0x70,std::int32_t{7});
    Put(data,kPlayerCharacterManagerOffset+0x58,entries.data());Put(data,kPlayerCharacterManagerOffset+0x64,std::int32_t{1});
    Put(entry,0xD8,std::int32_t{7});Put(entry,0xB0,id);Put(actor,0x18,id);Put(actor,0x1C,std::uint32_t{0x43686172});
    Put(storage,0x20,slots.data());Put(storage,0x2C,std::int32_t{2});Put(slots,0x18,actor.data());
    Put(data,kCurrentEventManagerOffsetV1+0x1F18,queue.data());Put(data,kCurrentEventManagerOffsetV1+0x1F24,std::int32_t{1});
    Put(definition,0,b.current.definition_vtable);Put(definition,0x138,authored.data());
    Put(definition,0x140,std::int32_t{3});Put(definition,0x144,std::int32_t{3});
    Put(event,0x1B8,definition.data());Put(event,0x1C0,id);Put(event,0x1C4,std::int32_t{42});
    Put(idler,0,b.idler_vtable);Put(idler,0x28,manager.data());
    Put(manager,0x18,windows.data());Put(manager,0x20,std::int32_t{2});Put(manager,0x24,std::int32_t{1});
    Put(window,0,b.window_vtable);Put(window,0xB8,std::int32_t{42});
    Put(window,0xB8+0x10,items.data());Put(window,0xB8+0x18,std::int32_t{2});Put(window,0xB8+0x1C,std::int32_t{2});
    for(std::size_t i=0;i<2;++i) {
      Put(items,i*0x1B8+0x160,window.data()+0xB8);Put(items,i*0x1B8+0x1B0,static_cast<std::int32_t>(i*2));
      Put(items,i*0x1B8+0x1B4,std::uint8_t{1});
    }
  }
  CoreSnapshotPrefix Expected(){CoreSnapshotPrefix out{};Require(ReadCoreSnapshot(b.current.core,out),"fixture Core");return out;}
  bool Read(EventOptionsObservationV1 &out){return ReadEventOptionsV1(b,Expected(),42,out);}
};
void *Player(void *) {return active->player.data();}
void *Select(void *p) {Require(p==active->data.data()+kCurrentEventManagerOffsetV1,"owned manager");return active->event.data();}
bool Enabled(const void *p) {
  auto &f=*active;++f.enabled_calls;std::uint8_t enabled=0,fallback=0;
  std::memcpy(&enabled,static_cast<const std::byte *>(p)+0x1B4,1);std::memcpy(&fallback,static_cast<const std::byte *>(p)+0x1B5,1);
  if(f.mutate && f.enabled_calls==2)Put(f.items,0x1B4,std::uint8_t{0});
  return enabled!=0 || fallback!=0;
}
void Rejected(Fixture &f) {
  EventOptionsObservationV1 out{};out.available=true;out.count=99;
  Require(!f.Read(out) && !out.available && out.count==0 && !out.unavailable_reason.empty(),"failure clears observations");
}
}
int main(){
  {
    Fixture f;EventOptionsObservationV1 out{};Require(f.Read(out),"materialized shown rows");
    Require(out.available && out.event_instance_id==42 && out.count==2 && out.rows[0].native_option_index==0 &&
        out.rows[1].native_option_index==2 && out.rows[1].enabled && f.enabled_calls==4,
        "authored hidden index1 is absent, not display-index1");
    const auto command=MakeSelectEventCommandV1(f.b,42,2);
    Require(command.event_instance_id==42 && command.native_option_index==2 && command.metadata==std::array<std::byte,16>{},
        "exact ordinary UI command payload and zero flags");
  }
  {Fixture f;Put(f.items,0x1B4,std::uint8_t{0});EventOptionsObservationV1 out{};Require(f.Read(out)&&!out.rows[0].enabled,"disabled retained");}
  {Fixture f;Put(f.items,0x1B4,std::uint8_t{0});Put(f.items,0x1B5,std::uint8_t{1});EventOptionsObservationV1 out{};Require(f.Read(out)&&out.rows[0].enabled,"native fallback eligibility");}
  {Fixture f;Put(f.window,0xB8+0x7C0,f.payload.data());Rejected(f);Require(!f.enabled_calls,"custom handler never bypassed");}
  {Fixture f;Put(f.window,0xB8+0x30,std::uint8_t{1});Rejected(f);}
  {Fixture f;Put(f.window,0,std::uintptr_t{1});Rejected(f);}
  {Fixture f;Put(f.idler,0,std::uintptr_t{1});Rejected(f);}
  {Fixture f;Put(f.manager,0x24,std::int32_t{33});Rejected(f);}
  {Fixture f;Put(f.window,0xB8+0x1C,std::int32_t{513});Rejected(f);}
  {Fixture f;Put(f.items,0x160,f.event.data());Rejected(f);}
  {Fixture f;Put(f.items,0x1B0,std::int32_t{3});Rejected(f);}
  {Fixture f;Put(f.items,0x1B8+0x1B0,std::int32_t{0});Rejected(f);}
  {Fixture f;Put(f.items,0x1B4,std::uint8_t{2});Rejected(f);}
  {Fixture f;f.mutate=true;Rejected(f);}
  {Fixture f;f.b.source_abi_pins_verified=false;Rejected(f);Require(!f.enabled_calls,"mapped source pins required before native query");}
  {Fixture f;f.second_window=f.window;Put(f.manager,0x24,std::int32_t{2});Rejected(f);}
  {Fixture f;auto frame=f.Expected();frame.clock.paused=false;EventOptionsObservationV1 out{};Require(!ReadEventOptionsV1(f.b,frame,42,out)&&!f.enabled_calls,"paused custody required");}
  Require(!BindEventOptionsImageV1(0x140000000,"old-sha").current.exact_build_admitted,"wrong build closed");
  std::cout<<"PASS 1.21 materialized event options and rejection cases\n";
}
