#include "ck3_121003_full111_event_read_v1.hpp"
#include "ck3_active_event_frame.hpp"
#include <windows.h>
#include <array>
#include <bit>
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <vector>

namespace {
namespace ck=xar::ck3_1210;
namespace current=xar::ck3_121003::full111;
namespace producer=xar::ck3_121003::build26785313;
void Need(bool ok,const char *why){if(!ok)throw std::runtime_error(why);}
template<class Buffer,class T> void Put(Buffer &buffer,std::size_t offset,T value){
 Need(offset<=buffer.size()&&sizeof(value)<=buffer.size()-offset,"owned RAM extent");
 std::memcpy(buffer.data()+offset,&value,sizeof(value));
}
class SparseImage {
 std::byte *base_=nullptr;
public:
 SparseImage(){base_=static_cast<std::byte*>(VirtualAlloc(nullptr,0x6FE5000,MEM_RESERVE,PAGE_NOACCESS));Need(base_!=nullptr,"own virtual reservation");}
 ~SparseImage(){if(base_)VirtualFree(base_,0,MEM_RELEASE);}
 std::uintptr_t base()const{return reinterpret_cast<std::uintptr_t>(base_);}
 template<class T>void Value(std::uintptr_t rva,T value){
  Need(rva<0x6FE5000&&sizeof(T)<=0x6FE5000-rva,"own sparse extent");
  const auto page=rva&~std::uintptr_t{4095};
  Need(VirtualAlloc(base_+page,8192,MEM_COMMIT,PAGE_READWRITE)!=nullptr,"own sparse page");
  std::memcpy(base_+rva,&value,sizeof(value));
 }
};
struct Fixture;
Fixture *active=nullptr;
void *LocalPlayer(void*);
struct Fixture {
 SparseImage image;
 std::array<std::byte,0xB0> state{};
 std::array<std::byte,0x48> jomini{};
 std::array<std::byte,0x200> players{};
 std::array<std::byte,0x80> player{};
 std::vector<std::byte> data=std::vector<std::byte>(0x46B00);
 std::array<std::byte,0xE0> entry{};
 std::array<void*,1> entries{entry.data()};
 std::array<std::byte,0x40> storage{};
 std::array<std::byte,0x30> slots{};
 std::array<std::byte,0x1E0> actor{},peer_zero{},peer_dead{};
 std::array<std::byte,0x300> living{};
 std::array<std::byte,0x30> family{};
 std::array<std::int32_t,2> spouses{};
 std::array<std::byte,0x58> pending{},units{},wars{},other_pending{};
 std::array<std::byte,0x20> pending_rows{};
 ck::FullSnapshotBindingsV1 bindings{};
 unsigned core_calls=0;bool mutate_gold=false;
 const std::int32_t actor_id=std::bit_cast<std::int32_t>(0x81000001U);
 const std::int32_t dead_id=std::bit_cast<std::int32_t>(0x82000002U);
 Fixture(){
  active=this;const auto b=image.base();
  image.Value(0x68B2090,state.data());image.Value(0x68B3B00,jomini.data());
  image.Value(0x68A8928,storage.data());
  image.Value(0x5D3E6F8,static_cast<void*>(nullptr));image.Value(0x5D3E6F8+0xC,std::int32_t{0});
  ck::CoreBindings core{true,reinterpret_cast<void**>(b+0x68B2090),
    reinterpret_cast<void**>(b+0x68B3B00),reinterpret_cast<void**>(b+0x68A8928),&LocalPlayer};
  core.image_build=ck::ImageBuildV1::full11126785313;
  bindings.core=core;bindings.exact_build_admitted=true;
  bindings.pending.core=core;bindings.pending.exact_build_admitted=true;
  bindings.pending.pending_storage_slot=reinterpret_cast<void**>(b+0x6A67480);
  bindings.pending.database_vtable=b+0x4E982F8;bindings.pending.pending_vtable=b+0x4E769B8;
  bindings.pending.reply_primary_vtable=b+0x4AF4900;bindings.pending.reply_secondary_vtable=b+0x4AF48C8;
  // Zero rows require no predicate/validator invocation. Nonempty is not modeled.
  bindings.pending.is_pending_for_character=+[](void*,void*){return false;};
  bindings.pending.validate_reply=+[](void*){return false;};
  bindings.military.core=core;bindings.military.exact_build_admitted=true;
  bindings.military.unit_registry_slot=reinterpret_cast<void**>(b+0x6A66AA0);
  bindings.military.war_registry_slot=reinterpret_cast<void**>(b+0x6A669D0);
  bindings.military.unit_manager_vtable=b+0x4EA42E0;bindings.military.unit_registry_vtable=b+0x4EA41E8;
  bindings.military.war_manager_vtable=b+0x4E9C470;bindings.military.war_registry_vtable=b+0x4E9C368;
  Put(state,8,std::int32_t{123456});Put(state,0x70,std::int32_t{4});Put(state,0xA0,data.data());
  Put(jomini,0x18,players.data());Put(jomini,0x20,std::uint8_t{1});
  Put(players,0x1F0,std::int32_t{7});Put(player,0x70,std::int32_t{7});
  // Actual current native operands are the entries pointer/count themselves,
  // at Data+26FB0/26FBC (manager base is 26F58).
  Put(data,0x26FB0,entries.data());Put(data,0x26FBC,std::int32_t{1});
  Put(entry,0xD8,std::int32_t{7});Put(entry,0xB0,actor_id);
  Put(storage,0x20,slots.data());Put(storage,0x2C,std::int32_t{3});
  Put(actor,0x18,actor_id);Put(actor,0x1C,std::uint32_t{0x43686172});
  Put(peer_zero,0x18,std::int32_t{0});Put(peer_zero,0x1C,std::uint32_t{0x43686172});
  Put(peer_dead,0x18,dead_id);Put(peer_dead,0x1C,std::uint32_t{0x43686172});
  Put(peer_dead,0x1D0,peer_dead.data());
  Put(slots,8,peer_zero.data());Put(slots,0x18,actor.data());Put(slots,0x28,peer_dead.data());
  Put(actor,0x1A8,family.data());Put(actor,0x1B0,living.data());
  Put(living,0x100,std::int64_t{-1234567});Put(living,0x110,std::int64_t{222222});
  Put(living,0x130,std::int64_t{333333});Put(living,0x2F8,std::int32_t{42});
  spouses={0,dead_id};Put(family,0x10,dead_id);Put(family,0x14,std::int32_t{0});
  Put(family,0x20,spouses.data());Put(family,0x2C,std::int32_t{2});
  Put(data,0x113C0,b+0x4E981B0);Put(pending,0,b+0x4E982F8);
  Put(pending,0x20,pending_rows.data());Put(pending,0x2C,std::int32_t{2});
  Put(other_pending,0,b+0x4E982F8);
  // Source contract: allocator-produced heap registry is stored in the input
  // cell. The conditional singleton publish is independently compared below.
  Put(data,0x113C0+0x50,pending.data());image.Value(0x6A67480,pending.data());
  Put(data,0x3ABF8,b+0x4EA42E0);Put(data,0x3ABF8+0x20,units.data());
  Put(data,0x3F2D8,b+0x4E9C470);Put(data,0x3F2D8+0x20,wars.data());
  Put(units,0,b+0x4EA41E8);Put(wars,0,b+0x4E9C368);
  image.Value(0x6A66AA0,units.data());image.Value(0x6A669D0,wars.data());
 }
 bool Read(xar::game::Snapshot &out,ck::FullSnapshotDiagnosticsV1 &d){core_calls=0;return current::ReadFull(bindings,out,d);}
};
void *LocalPlayer(void*){
 if(!active)return nullptr;
 if(++active->core_calls==2&&active->mutate_gold)Put(active->living,0x100,std::int64_t{99});
 return active->player.data();
}
struct EventFixture {
 Fixture &full;
 std::array<void*,2> rows{full.entry.data(),full.living.data()};
 unsigned calls=0;
 bool hidden=false,different_actor=false,wrong_runtime=false,mixed=false,owner_lost=false,window_drift=false,queue_drift=false;
 std::int32_t instance=17,authored_count=3;
 static constexpr std::size_t items=0x44BC0+0x1F18,capacity=items+8,count=items+12;
 explicit EventFixture(Fixture &f):full(f){
  Put(f.data,items,rows.data());Put(f.data,capacity,std::int32_t{2});Put(f.data,count,std::int32_t{1});
 }
 static bool Capture(void *opaque,const ck::CoreSnapshotPrefix &core,producer::Full111OrdinaryEventWitnessV1 &w){
  auto &f=*static_cast<EventFixture *>(opaque);
  ++f.calls;
  if(f.owner_lost&&f.calls==2)return false;
  w.queue.game_data=reinterpret_cast<std::uintptr_t>(f.full.data.data());
  w.queue.items=reinterpret_cast<std::uintptr_t>(f.rows.data());
  w.queue.capacity=2+(f.queue_drift&&f.calls==2?1:0);
  w.queue.count=1;
  w.queue.rows[0]=reinterpret_cast<std::uintptr_t>(f.rows.front());
  w.scene.kind=producer::LydKind267V1::events;
  w.raw.source.kind=w.scene.kind;
  w.scene.jomini=reinterpret_cast<std::uintptr_t>(f.full.jomini.data());
  const std::uintptr_t root=f.window_drift&&f.calls==2?0x2000:0x1000;
  w.scene.event_roots.push_back({root,!f.hidden,true});
  w.raw.manager_census.game=reinterpret_cast<std::uintptr_t>(f.full.state.data());
  auto &public_events=w.raw.source.events.emplace();
  public_events.census_complete=true;
  public_events.named_root_count=f.mixed?2:1;
  auto &event=public_events.events.emplace_back();
  event.instance_id=f.instance;
  event.recipient_character_id=f.different_actor?7:core.played_character_id;
  event.authored_option_count=f.authored_count;
  event.window_visible=!f.hidden;
  event.named_root_bound=true;
  auto &row=w.raw.event_rows.emplace_back();
  row.controller=0x3000;row.root=root;
  row.runtime=f.wrong_runtime?0x4000:w.queue.rows[0];row.definition=0x5000;
  row.instance_id=f.instance;row.material.authored_option_count=f.authored_count;
  return true;
 }
 bool Read(xar::game::Snapshot &out,ck::FullSnapshotDiagnosticsV1 &d){
  calls=0;full.core_calls=0;
  return current::ReadFullWithOrdinaryEventV1(full.bindings,out,d,{this,&Capture});
 }
};
void RunEventFixture(Fixture &full,xar::game::Snapshot &out,ck::FullSnapshotDiagnosticsV1 &d){
 EventFixture event(full);
 Need(event.Read(out,d)&&d.complete&&d.completed_passes==2&&event.calls==2&&
      out.has_active_event&&out.active_event_instance_id==17&&out.active_event_option_count==3,
      "same visible ordinary identity produces only the authored summary");
 constexpr std::array caps{current::kOrdinaryEventCapabilityV1};
 const xar::game::AdapterDescriptor opted_in{current::kAdapterId,current::kGameVersion,current::kExecutableSha256,"",caps};
 auto unavailable=opted_in;unavailable.capabilities={};
 auto unrelated=opted_in;unrelated.adapter_id="foreign";
 const auto serialize=[&](const auto &snapshot,const auto *descriptor){
  std::string result="{\"type\":\"state_snapshot\"";
  xar::bridge::AppendActiveEventFrame(result,snapshot,descriptor);
  return result+'}';
 };
 const auto encoded=serialize(out,&opted_in);
 Need(encoded==R"({"type":"state_snapshot","active_event":{"schema":"ck3_121003_full111_ordinary_event_v1","instance_id":17,"authored_option_count":3}})",
      "exact three-field Full111 read-only event JSON");
 std::cout<<encoded<<'\n';
 constexpr std::string_view legacy=R"({"type":"state_snapshot","active_event":{"instance_id":17,"option_count":3,"option_indexes":[1,2,3]}})";
 Need(serialize(out,&unavailable)==legacy&&serialize(out,&unrelated)==legacy,"legacy event bytes with missing capability or other descriptor");
 Need(serialize(xar::game::Snapshot{},&opted_in)==R"({"type":"state_snapshot","active_event":null})","unchanged null event JSON");

 const auto refused=[&](std::string_view why){
  Need(!event.Read(out,d)&&out==xar::game::Snapshot{}&&!d.complete&&d.reason==why,why.data());
 };
 Put(full.data,event.count,std::int32_t{2});
 refused("current111_ordinary_event_queue_not_single");
 Need(event.calls==0,"ambiguous runtime count refuses before the GUI read");
 Put(full.data,event.count,std::int32_t{1});
 event.hidden=true;refused("current111_ordinary_event_witness_mismatch");event.hidden=false;
 event.mixed=true;refused("current111_ordinary_event_witness_mismatch");event.mixed=false;
 event.different_actor=true;refused("current111_ordinary_event_identity_mismatch");event.different_actor=false;
 event.wrong_runtime=true;refused("current111_ordinary_event_identity_mismatch");event.wrong_runtime=false;
 event.owner_lost=true;refused("current111_ordinary_event_owner_observation_unavailable");event.owner_lost=false;
 event.window_drift=true;refused("current111_full_observations_changed");event.window_drift=false;
 event.queue_drift=true;refused("current111_full_observations_changed");event.queue_drift=false;
 event.instance=0;refused("current111_ordinary_event_identity_mismatch");event.instance=17;
 event.authored_count=65;refused("current111_ordinary_event_identity_mismatch");
 event.authored_count=64;Need(event.Read(out,d)&&out.active_event_option_count==64,"inclusive authored upper bound");
 event.authored_count=0;Need(event.Read(out,d)&&out.active_event_option_count==0,"zero authored options stay zero");
 Put(full.data,event.count,std::int32_t{0});
 Need(event.Read(out,d)&&!out.has_active_event&&event.calls==0,"unchanged empty fast path");
 Put(full.data,event.items,static_cast<void *>(nullptr));
}
void Run(){
 Fixture f;xar::game::Snapshot out{};ck::FullSnapshotDiagnosticsV1 d{};
 const bool first=f.Read(out,d);
 if(!first)std::cerr<<"initial actual reader stage="<<d.stage<<" reason="<<d.reason<<" passes="<<d.completed_passes<<'\n';
 Need(first&&d.complete&&d.completed_passes==2,"pointer-cell heap owner Full two-pass positive");
 Need(out.played_character_id==f.actor_id&&out.played_character_spouse_ids==std::vector<std::int32_t>({0,f.dead_id}),"full32 and dead peer preserved");
 const auto base=f.image.base();
 Put(f.data,0x11410,static_cast<void*>(nullptr));
 Need(!f.Read(out,d)&&!d.complete,"null pointer cell rejected");
 Put(f.data,0x11410,f.pending.data());f.image.Value(0x6A67480,f.other_pending.data());
 Need(!f.Read(out,d)&&d.reason=="current111_pending_owner_mismatch","conditional preexisting different global rejected");
 // Independent negative for the withdrawn111 model: putting a VT at the
 // manager cell and publishing its address is not the ctor's heap-pointer path.
 Put(f.data,0x11410,base+0x4E982F8);f.image.Value(0x6A67480,f.data.data()+0x11410);
 Need(!f.Read(out,d)&&d.reason=="current111_pending_owner_mismatch","embedded registry model rejected");
 Put(f.data,0x11410,f.pending.data());f.image.Value(0x6A67480,f.pending.data());
 Need(f.Read(out,d),"valid heap cell restored");
 Put(f.family,0x2C,std::int32_t{65});Need(!f.Read(out,d),"spouse finite extent rejected");Put(f.family,0x2C,std::int32_t{2});
 Put(f.peer_dead,0x18,std::bit_cast<std::int32_t>(0x83000002U));Need(!f.Read(out,d),"stale full generation not dropped");Put(f.peer_dead,0x18,f.dead_id);
 Put(f.actor,0x1A8,static_cast<void*>(nullptr));Need(f.Read(out,d)&&out.played_character_spouse_ids.empty()&&out.played_character_betrothed_id==-1,"actual default-vector null-family empty");Put(f.actor,0x1A8,f.family.data());
 f.mutate_gold=true;Need(!f.Read(out,d)&&!d.complete,"actual double-pass resource drift rejected");f.mutate_gold=false;
 constexpr std::size_t event_items=0x44BC0+0x1F18, event_count=0x44BC0+0x1F24;
 const auto event_rejected=[&](std::string_view reason){
  const bool available=f.Read(out,d);
  if(d.stage!="event"||d.reason!=reason)
   std::cerr<<"expected event diagnostic "<<reason<<", got "<<d.stage<<'/'<<d.reason<<'\n';
  Need(!available&&!d.complete&&out==xar::game::Snapshot{}&&d.stage=="event"&&d.reason==reason,
    reason.data());
 };
 Put(f.data,event_count,std::int32_t{-1});
 event_rejected("current111_event_queue_header_invalid");
 Put(f.data,event_count,std::int32_t{1});
 event_rejected("current111_event_queue_header_invalid");
 std::array<void*,1> event_rows{f.entry.data()};
 Put(f.data,event_items,event_rows.data());
 event_rejected("current111_nonempty_event_lifetime_unavailable");
 Put(f.data,event_count,std::int32_t{0});
 Need(f.Read(out,d)&&!out.has_active_event,"empty queue can retain allocated items storage");

 // Place the items cell at the end of an owned committed page. The count
 // cell then falls in the next reserved, inaccessible page.
 constexpr std::size_t test_page_size=4096;
 const auto test_page=f.image.base()+0x400000;
 Need(VirtualAlloc(reinterpret_cast<void*>(test_page),test_page_size,MEM_COMMIT,PAGE_READWRITE)!=nullptr,
   "own accessible event header page");
 const auto test_data=test_page+test_page_size-sizeof(void*)-event_items;
 for(const auto data_address:{test_data,test_data+test_page_size}){
  // The Core read must still resolve the played character from the relocated data root.
  const auto data_rva=data_address-f.image.base();
  f.image.Value(data_rva+0x26FB0,f.entries.data());
  f.image.Value(data_rva+0x26FBC,std::int32_t{1});
 }
 Put(f.state,0xA0,reinterpret_cast<void*>(test_data));
 event_rejected("current111_event_count_slot_unreadable");
 Put(f.state,0xA0,reinterpret_cast<void*>(test_data+test_page_size));
 event_rejected("current111_event_items_slot_unreadable");
 Put(f.state,0xA0,f.data.data());
 Need(f.Read(out,d)&&!out.has_active_event,"normal empty queue restored");
 RunEventFixture(f,out,d);
 std::cout<<"PASS current Full pointer-cell/heap/global contract; embedded/mismatch reject; full32, Family3 finite extent and coherence; RAM only\n";
}
}
int main(){try{Run();return 0;}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
