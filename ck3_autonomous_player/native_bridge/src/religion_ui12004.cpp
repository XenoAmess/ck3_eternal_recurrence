#include "xar_bridge/religion_ui12004.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/religion_ui12004_source_pins.hpp"
#include <windows.h>
#include <array>
#include <cstring>
#include <limits>
#include <utility>

namespace xar::ck3_12004::religion_ui {
namespace {
constexpr std::uint32_t absent=0xFFFFFFFFU;
const void*At(const void*p,std::size_t offset) noexcept {
  const auto base=reinterpret_cast<std::uintptr_t>(p);
  return base&&offset<=std::numeric_limits<std::uintptr_t>::max()-base?
      reinterpret_cast<const void*>(base+offset):nullptr;
}
template<class T>bool Read(const Bindings&b,const void*p,std::size_t offset,T&out) noexcept {
  const auto*q=At(p,offset);return q&&b.read_memory&&b.read_memory(b.read_context,q,&out,sizeof(out));
}
bool ProcessRead(void*,const void*p,void*out,std::size_t size) noexcept {
  SIZE_T got=0;return p&&out&&size&&ReadProcessMemory(GetCurrentProcess(),p,out,size,&got)&&got==size;
}
bool Valid(Window kind) noexcept {return kind==Window::character||kind==Window::faith;}
bool Pins(const Bindings&b,Window kind) noexcept {
  if(!b.enabled||!b.image_base||!b.read_memory||!Valid(kind))return false;
  for(const auto&pin:source::pins){
    if(pin.window!=2&&pin.window!=static_cast<std::uint32_t>(kind))continue;
    std::array<unsigned char,32>actual{};
    if(!b.read_memory(b.read_context,reinterpret_cast<const void*>(b.image_base+pin.rva),actual.data(),pin.size)||actual!=pin.bytes)return false;
  }
  return true;
}
bool Typed(const Bindings&b,const void*object,std::uintptr_t primary,std::uintptr_t secondary,std::uint32_t td) noexcept {
  std::uintptr_t a=0,s=0,col=0;std::uint32_t signature=0,offset=1,type=0,self=0;
  return Read(b,object,0,a)&&a==b.image_base+primary&&Read(b,object,0x10,s)&&s==b.image_base+secondary&&
      Read(b,reinterpret_cast<const void*>(a-8),0,col)&&col>=b.image_base&&
      Read(b,reinterpret_cast<const void*>(col),0,signature)&&signature==1&&
      Read(b,reinterpret_cast<const void*>(col),4,offset)&&offset==0&&
      Read(b,reinterpret_cast<const void*>(col),12,type)&&type==td&&
      Read(b,reinterpret_cast<const void*>(col),20,self)&&col==b.image_base+self;
}
const void*Resolve(const Bindings&b,std::uintptr_t global,std::uint32_t id,std::size_t id_offset) noexcept {
  const void*storage=nullptr,*rows=nullptr,*object=nullptr;std::uint32_t count=0,actual=absent;
  if(id==absent||!Read(b,reinterpret_cast<const void*>(b.image_base+global),0,storage)||!storage||
      !Read(b,storage,0x20,rows)||!rows||!Read(b,storage,0x2C,count)||(id&0xFFFFFFU)>=count||
      !Read(b,rows,static_cast<std::size_t>(id&0xFFFFFFU)*16+8,object)||!object||
      !Read(b,object,id_offset,actual)||actual!=id)return nullptr;
  return object;
}
bool FaithAndRite(const Bindings&b,std::uint32_t faith_id,std::uint32_t rite_id) noexcept {
  const auto*faith=Resolve(b,0x5D1E300,faith_id,8);
  const auto*rite=Resolve(b,0x5D1E2F8,rite_id,8);
  std::uint32_t magic=0,rite_faith=absent;
  return faith&&rite&&Read(b,rite,0xC,magic)&&magic==0x52697465U&&
      Read(b,rite,0x4B8,rite_faith)&&rite_faith==faith_id;
}
bool Subject(const Bindings&b,Window kind,std::uint32_t id,bool opening) noexcept {
  if(kind==Window::character){
    const auto*object=Resolve(b,0x5C67568,id,0x18);std::uint32_t magic=0;std::uint8_t a=0,busy=0;
    return object&&Read(b,object,0x1C,magic)&&magic==0x43686172U&&
        (!opening||(Read(b,object,0x1A4,a)&&Read(b,object,0x1A5,busy)&&a==0&&busy==0));
  }
  const auto*faith=Resolve(b,0x5D1E300,id,8);std::uint32_t main_rite=absent;
  return faith&&Read(b,faith,0x98,main_rite)&&FaithAndRite(b,id,main_rite);
}
struct Pass {
  const void*window=nullptr,*root=nullptr,*gfx=nullptr;
  std::uint32_t id=absent,rite=absent;bool subject=false;
  bool operator==(const Pass&)const=default;
};
bool WindowPass(const Bindings&b,const void*handler,Window kind,Pass&out) noexcept {
  const auto faith=kind==Window::faith;const void*back=nullptr;std::uintptr_t set_data=0,match_data=0;
  if(!Read(b,handler,faith?0x270:0xD8,out.window)||!out.window||
      !Typed(b,out.window,faith?0x45648D8:0x451BA18,faith?0x45649F0:0x451BAE8,faith?0x57A2378:0x5723010)||
      !Read(b,out.window,0xA0,back)||back!=handler||!Read(b,out.window,0x98,out.gfx)||!out.gfx||
      !Read(b,out.window,0x60,out.root))return false;
  const auto vt=b.image_base+(faith?0x45648D8:0x451BA18);
  if(!Read(b,reinterpret_cast<const void*>(vt),0x90,set_data)||set_data!=b.image_base+(faith?0x14C57A0:0x106CC70)||
      !Read(b,reinterpret_cast<const void*>(vt),0x98,match_data)||match_data!=b.image_base+(faith?0x14C5820:0x1038B80)||
      !Read(b,out.window,faith?0xE8:0xC8,out.id))return false;
  if(faith){if(!Read(b,out.window,0x258,out.rite))return false;out.subject=FaithAndRite(b,out.id,out.rite);}
  else out.subject=Subject(b,kind,out.id,false);
  return true;
}
struct Any {void*type=nullptr;std::array<std::uint8_t,32>data{};};
static_assert(sizeof(Any)==40);
bool NativeOpen(const Bindings&b,void*handler,Window kind,std::uint32_t id,bool&attempted) noexcept {
  if(!b.open_view_data)return false;
#if defined(_MSC_VER)
  __try{
#endif
    const auto factory=kind==Window::faith?b.faith_any:b.character_any;
    if(!factory)return false;
    Any value{};value.type=factory();std::uintptr_t vt=0;
    if(reinterpret_cast<std::uintptr_t>(value.type)!=b.image_base+(kind==Window::faith?0x54D70F8:0x542FE60)||
        !Read(b,value.type,0,vt)||vt!=b.image_base+(kind==Window::faith?0x44B92F0:0x44A1938))return false;
    // The original parser/history calls these exact typed Any virtuals. Verify
    // both their table edges and the loaded bodies retained in source::pins.
    for(const auto&edge:std::array<std::pair<std::size_t,std::uintptr_t>,6>{{
        {0x18,0x8522C0},{0x28,0x876E00},{0x38,0x877200},
        {0x50,kind==Window::faith?0xB1AA90:0xA06180},{0x58,0x8771F0},{0x60,0x8771F0}}}){
      std::uintptr_t target=0;
      if(!Read(b,reinterpret_cast<const void*>(vt),edge.first,target)||target!=b.image_base+edge.second)return false;
    }
    std::memcpy(value.data.data(),&id,sizeof(id));
    attempted=true;b.open_view_data(handler,kind==Window::faith?0x3B:8,&value);return true;
#if defined(_MSC_VER)
  }__except(EXCEPTION_EXECUTE_HANDLER){return false;}
#endif
}
}
Bindings BindImage12004(std::uintptr_t base,std::string_view sha) noexcept {
  Bindings b{};if(!base||sha!=ck3_12004::kExecutableSha256)return b;
  b.enabled=true;b.image_base=base;b.read_memory=&ProcessRead;
  b.character_any=reinterpret_cast<AnyType>(base+0xA05DE0);
  b.faith_any=reinterpret_cast<AnyType>(base+0xB19AD0);
  b.open_view_data=reinterpret_cast<OpenViewData>(base+0xAF39E0);return b;
}
bool ReadSelection12004(const Bindings&b,const void*handler,Window kind,Selection&out) noexcept {
  out={};out.handler=handler;
  if(!Pins(b,kind)){out.unavailable_reason="religion_ui12004_loaded_source_pins_changed";return false;}
  Pass first{},second{};
  if(!WindowPass(b,handler,kind,first)){out.unavailable_reason="religion_ui12004_native_window_unverified";return false;}
  if(!WindowPass(b,handler,kind,second)||first!=second){out.unavailable_reason="religion_ui12004_native_selection_changed";return false;}
  out.window=first.window;out.root=first.root;out.gfx=first.gfx;out.subject_available=first.subject;
  out.subject_id=first.id;out.selected_rite_id=first.rite;out.available=true;return true;
}
bool CanOpen12004(const Bindings&b,const void*handler,Window kind,std::uint32_t id) noexcept {
  Selection state{};return ReadSelection12004(b,handler,kind,state)&&Subject(b,kind,id,true);
}
bool InvokeOpen12004(const Bindings&b,void*handler,Window kind,std::uint32_t id,bool&attempted) noexcept {
  attempted=false;if(!CanOpen12004(b,handler,kind,id))return false;
  return NativeOpen(b,handler,kind,id,attempted);
}
}
