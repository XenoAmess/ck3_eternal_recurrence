#include "xar_bridge/religion_ui12004.hpp"
#include "xar_bridge/religion_ui12004_source_pins.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include <windows.h>
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <map>
#include <stdexcept>
#include <vector>

namespace ui=xar::ck3_12004::religion_ui;
namespace {
constexpr std::uintptr_t image=0x140000000ULL,handler=0x300000000ULL;
constexpr std::uintptr_t character_window=handler+0x10000,faith_window=handler+0x20000;
constexpr std::uintptr_t character=handler+0x30000,faith=handler+0x40000,rite=handler+0x50000;
constexpr std::uint32_t character_id=0x12000001,faith_id=0x34000001,rite_id=0x56000001;
struct Memory {
  std::map<std::uintptr_t,unsigned char> bytes;
  std::uintptr_t mutate_address=0;unsigned reads=0;
  template<class T>void put(std::uintptr_t address,const T&value){
    const auto*p=reinterpret_cast<const unsigned char*>(&value);
    for(std::size_t i=0;i<sizeof(value);++i)bytes[address+i]=p[i];
  }
  void raw(std::uintptr_t address,const unsigned char*p,std::size_t n){for(std::size_t i=0;i<n;++i)bytes[address+i]=p[i];}
  static bool read(void*ctx,const void*p,void*out,std::size_t n) noexcept {
    auto&m=*static_cast<Memory*>(ctx);const auto address=reinterpret_cast<std::uintptr_t>(p);
    auto*dest=static_cast<unsigned char*>(out);
    for(std::size_t i=0;i<n;++i){const auto it=m.bytes.find(address+i);if(it==m.bytes.end())return false;dest[i]=it->second;}
    if(address==m.mutate_address&&++m.reads==2&&n==4)dest[3]^=1;
    return true;
  }
};
std::uintptr_t factory_result=0;unsigned calls=0;std::uint32_t called_index=0,called_id=0;bool raise_after_call=false;
void* __fastcall Factory(){return reinterpret_cast<void*>(factory_result);}
void __fastcall Open(void*owner,std::uint32_t index,const void*any){
  if(reinterpret_cast<std::uintptr_t>(owner)!=handler)throw std::runtime_error("wrong handler");
  ++calls;called_index=index;std::memcpy(&called_id,static_cast<const unsigned char*>(any)+8,4);
  if(raise_after_call)RaiseException(0xE0000042,0,0,nullptr);
}
void require(bool value,const char*label){if(!value){std::fprintf(stderr,"FAIL %s\n",label);throw std::runtime_error(label);}}
void registry(Memory&m,std::uintptr_t global,std::uintptr_t storage,std::uintptr_t rows,std::uintptr_t object,std::uint32_t id,std::size_t id_offset){
  m.put(image+global,storage);m.put(storage+0x20,rows);m.put(storage+0x2C,std::uint32_t{2});
  m.put(rows+(id&0xFFFFFFU)*16+8,object);m.put(object+id_offset,id);
}
void window(Memory&m,std::uintptr_t object,bool is_faith){
  const auto primary=image+(is_faith?0x45648D8:0x451BA18),secondary=image+(is_faith?0x45649F0:0x451BAE8);
  const auto col=image+(is_faith?0x4B710C0:0x4AEF4B8);const std::uint32_t td=is_faith?0x57A2378:0x5723010;
  m.put(handler+(is_faith?0x270:0xD8),object);m.put(object,primary);m.put(object+0x10,secondary);
  m.put(primary-8,col);m.put(col,std::uint32_t{1});m.put(col+4,std::uint32_t{0});m.put(col+12,td);m.put(col+20,static_cast<std::uint32_t>(col-image));
  m.put(primary+0x90,image+(is_faith?0x14C57A0:0x106CC70));m.put(primary+0x98,image+(is_faith?0x14C5820:0x1038B80));
  m.put(object+0xA0,handler);m.put(object+0x98,object+0x2000);m.put(object+0x60,object+0x3000);
  m.put(object+(is_faith?0xE8:0xC8),is_faith?faith_id:character_id);
  if(is_faith)m.put(object+0x258,rite_id);
}
void any(Memory&m,bool is_faith){
  const auto meta=image+(is_faith?0x54D70F8:0x542FE60),vt=image+(is_faith?0x44B92F0:0x44A1938);
  m.put(meta,vt);
  for(const auto&edge:std::array<std::pair<std::size_t,std::uintptr_t>,6>{{
      {0x18,0x8522C0},{0x28,0x876E00},{0x38,0x877200},{0x50,is_faith?0xB1AA90:0xA06180},{0x58,0x8771F0},{0x60,0x8771F0}}})
    m.put(vt+edge.first,image+edge.second);
}
Memory fixture(){
  Memory m;for(const auto&pin:ui::source::pins)m.raw(image+pin.rva,pin.bytes.data(),pin.size);
  registry(m,0x5C67568,handler+0x60000,handler+0x61000,character,character_id,0x18);
  registry(m,0x5D1E300,handler+0x70000,handler+0x71000,faith,faith_id,8);
  registry(m,0x5D1E2F8,handler+0x80000,handler+0x81000,rite,rite_id,8);
  m.put(character+0x1C,std::uint32_t{0x43686172});m.put(character+0x1A4,std::uint8_t{0});m.put(character+0x1A5,std::uint8_t{0});
  m.put(faith+0x98,rite_id);m.put(rite+0xC,std::uint32_t{0x52697465});m.put(rite+0x4B8,faith_id);
  window(m,character_window,false);window(m,faith_window,true);any(m,false);any(m,true);return m;
}
ui::Bindings bind(Memory&m){
  auto b=ui::BindImage12004(image,xar::ck3_12004::kExecutableSha256);b.read_memory=Memory::read;b.read_context=&m;
  b.character_any=Factory;b.faith_any=Factory;b.open_view_data=Open;return b;
}
}
int main(){
  unsigned cases=0;
  try{
    auto m=fixture();auto b=bind(m);ui::Selection state{};bool attempted=false;
    require(!ui::BindImage12004(image,"wrong").enabled,"wrong exact build");++cases;
    require(ui::ReadSelection12004(b,reinterpret_cast<void*>(handler),ui::Window::character,state)&&state.subject_available&&state.subject_id==character_id,"Character selected full ID");++cases;
    require(ui::ReadSelection12004(b,reinterpret_cast<void*>(handler),ui::Window::faith,state)&&state.subject_available&&state.subject_id==faith_id&&state.selected_rite_id==rite_id,"Faith and Rite join");++cases;
    require(!ui::CanOpen12004(b,reinterpret_cast<void*>(handler),ui::Window::faith,faith_id^0x01000000),"stale Faith generation");++cases;
    m.put(rite+0x4B8,faith_id^0x01000000);require(!ui::CanOpen12004(b,reinterpret_cast<void*>(handler),ui::Window::faith,faith_id),"foreign Rite owner");++cases;m=fixture();
    m.put(character+0x1A4,std::uint8_t{1});require(!ui::CanOpen12004(b,reinterpret_cast<void*>(handler),ui::Window::character,character_id),"original Character opening exclusion");++cases;m=fixture();
    m.put(faith_window+0x10,std::uintptr_t{0});require(!ui::ReadSelection12004(b,reinterpret_cast<void*>(handler),ui::Window::faith,state),"secondary window vtable");++cases;m=fixture();
    m.put(faith_window+0xA0,handler+8);require(!ui::ReadSelection12004(b,reinterpret_cast<void*>(handler),ui::Window::faith,state),"handler backlink");++cases;m=fixture();
    m.put(image+0x45648D8+0x90,image+0x14C57A1);require(!ui::ReadSelection12004(b,reinterpret_cast<void*>(handler),ui::Window::faith,state),"original SetData slot");++cases;m=fixture();
    m.put(image+0xB19AD0,std::uint8_t{0});require(!ui::CanOpen12004(b,reinterpret_cast<void*>(handler),ui::Window::faith,faith_id),"loaded source pin drift");++cases;m=fixture();
    m.mutate_address=faith_window+0xE8;require(!ui::ReadSelection12004(b,reinterpret_cast<void*>(handler),ui::Window::faith,state),"selection changes between reads");++cases;m=fixture();
    m.put(faith_window+0x60,std::uintptr_t{0});require(ui::CanOpen12004(b,reinterpret_cast<void*>(handler),ui::Window::faith,faith_id),"opening before GUI root creation");++cases;m=fixture();
    factory_result=image+0x54D70F8;calls=0;require(ui::InvokeOpen12004(b,reinterpret_cast<void*>(handler),ui::Window::faith,faith_id,attempted)&&attempted&&calls==1&&called_index==0x3B&&called_id==faith_id,"Faith exact Any and view index");++cases;
    require(ui::ReadSelection12004(b,reinterpret_cast<void*>(handler),ui::Window::faith,state)&&state.subject_id==faith_id,"ACK does not create a visible postcondition");++cases;
    factory_result=image+0x542FE60;calls=0;require(ui::InvokeOpen12004(b,reinterpret_cast<void*>(handler),ui::Window::character,character_id,attempted)&&attempted&&calls==1&&called_index==8&&called_id==character_id,"Character exact Any and view index");++cases;
    factory_result=image+0x542FE68;calls=0;require(!ui::InvokeOpen12004(b,reinterpret_cast<void*>(handler),ui::Window::character,character_id,attempted)&&!attempted&&calls==0,"wrong type singleton");++cases;
    factory_result=image+0x542FE60;m.put(image+0x44A1938+0x50,image+0xA06181);require(!ui::InvokeOpen12004(b,reinterpret_cast<void*>(handler),ui::Window::character,character_id,attempted)&&!attempted,"changed typed visitor edge");++cases;m=fixture();
    raise_after_call=true;calls=0;require(!ui::InvokeOpen12004(b,reinterpret_cast<void*>(handler),ui::Window::character,character_id,attempted)&&attempted&&calls==1,"fault after consumed single attempt");++cases;raise_after_call=false;
    m.put(faith_window+0xE8,std::uint32_t{0});m.put(faith+8,std::uint32_t{0});m.put(handler+0x71000+8,faith);m.put(rite+0x4B8,std::uint32_t{0});
    require(ui::CanOpen12004(b,reinterpret_cast<void*>(handler),ui::Window::faith,0),"Faith zero is a full typed ID");++cases;
    std::printf("{\"status\":\"PASS\",\"fixture_cases\":%u,\"game_contacted\":false,\"live_qualification\":false}\n",cases);return 0;
  }catch(const std::exception&e){std::fprintf(stderr,"%s\n",e.what());return 1;}
}
