#include "xar_bridge/ck3_121003_full111.hpp"
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
 std::cout<<"PASS current Full pointer-cell/heap/global contract; embedded/mismatch reject; full32, Family3 finite extent and coherence; RAM only\n";
}
}
int main(){try{Run();return 0;}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
