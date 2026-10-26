#include "xar_bridge/title_window12004.hpp"
#include "xar_bridge/title_window12004_source_pins.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include <array>
#include <cstring>
#include <limits>

namespace xar::ck3_12004::title_ui {
namespace {
constexpr std::uint32_t absent=0xFFFFFFFFU;
constexpr std::size_t handler_slot=0x1C0, selected_title_offset=0xCC;
constexpr std::uintptr_t primary_vtable=0x45206B0, secondary_vtable=0x4520780;
constexpr std::uint32_t primary_col=0x4AF5190, secondary_col=0x4AF5168;
constexpr std::uint32_t title_window_type=0x5729118, hierarchy=0x4AF4CA0;
constexpr std::uintptr_t title_storage=0x5D1DAF8, title_fallback=0x5D1DAE0;
const void *At(const void *object,std::size_t offset) noexcept {
  const auto base=reinterpret_cast<std::uintptr_t>(object);
  return base&&offset<=std::numeric_limits<std::uintptr_t>::max()-base?
      reinterpret_cast<const void *>(base+offset):nullptr;
}
template<class T> bool Read(const Bindings &b,const void *object,
    std::size_t offset,T &value) noexcept {
  const auto *address=At(object,offset);
  return address&&b.read_memory&&b.read_memory(b.read_context,address,&value,sizeof(value));
}
const void *Image(const Bindings &b,std::uintptr_t rva) noexcept {
  return At(reinterpret_cast<const void *>(b.image_base),rva);
}
bool Pins(const Bindings &b) noexcept {
  if(!b.enabled||!b.image_base||!b.read_memory)return false;
  for(const auto &pin:source::pins) {
    std::array<unsigned char,60> actual{};
    if(!b.read_memory(b.read_context,Image(b,pin.rva),actual.data(),pin.size)||
        actual!=pin.bytes)return false;
  }
  return true;
}
bool Locator(const Bindings &b,std::uintptr_t vtable,std::uint32_t expected,
    std::uint32_t expected_offset) noexcept {
  std::uintptr_t col=0;std::array<std::uint32_t,6> fields{};
  return vtable>=sizeof(void *)&&
      Read(b,reinterpret_cast<const void *>(vtable-sizeof(void *)),0,col)&&
      col==b.image_base+expected&&Read(b,reinterpret_cast<const void *>(col),0,fields)&&
      fields==std::array<std::uint32_t,6>{1,expected_offset,0,title_window_type,hierarchy,expected};
}
bool Typed(const Bindings &b,const void *window) noexcept {
  std::uintptr_t primary=0,secondary=0;
  constexpr char expected_name[]=".?AVCTitleViewWindow@@";
  std::array<char,sizeof(expected_name)> name{};
  return Read(b,window,0,primary)&&primary==b.image_base+primary_vtable&&
      Read(b,window,0x10,secondary)&&secondary==b.image_base+secondary_vtable&&
      Locator(b,primary,primary_col,0)&&Locator(b,secondary,secondary_col,0x10)&&
      Read(b,Image(b,title_window_type),0x10,name)&&
      std::memcmp(name.data(),expected_name,sizeof(expected_name))==0;
}
const void *ResolveTitle(const Bindings &b,std::uint32_t id) noexcept {
  // Original 10A9960 masks only the row index, then compares the complete ID
  // at Title+10. Never publish its fallback as a selected Title.
  const void *storage=nullptr,*rows=nullptr,*object=nullptr,*fallback=nullptr;
  std::int32_t capacity=0;std::uint32_t actual=absent;
  if(id==absent||!Read(b,Image(b,title_storage),0,storage)||!storage||
      !Read(b,Image(b,title_fallback),0,fallback)||
      !Read(b,storage,0x20,rows)||!rows||!Read(b,storage,0x2C,capacity)||
      capacity<=0||capacity>4'194'304||
      (id&0xFFFFFFU)>=static_cast<std::uint32_t>(capacity)||
      !Read(b,rows,static_cast<std::size_t>(id&0xFFFFFFU)*16+8,object)||
      !object||object==fallback||!Read(b,object,0x10,actual)||actual!=id)return nullptr;
  return object;
}
bool Pass(const Bindings &b,const void *handler,Selection &out) noexcept {
  const void *back=nullptr;
  if(!Read(b,handler,handler_slot,out.window)||!out.window||!Typed(b,out.window)||
      !Read(b,out.window,0xA0,back)||back!=handler||
      !Read(b,out.window,0x60,out.root)||
      !Read(b,out.window,selected_title_offset,out.raw_title_id))return false;
  out.title=ResolveTitle(b,out.raw_title_id);
  out.subject_available=out.title!=nullptr;
  return true;
}
} // namespace
Bindings BindImage12004(std::uintptr_t base,std::string_view sha,
    ReadMemory read_memory,void *read_context) noexcept {
  Bindings b{};
  if(!base||sha!=ck3_12004::kExecutableSha256||!read_memory||
      base>std::numeric_limits<std::uintptr_t>::max()-title_storage-sizeof(void *))return b;
  b.enabled=true;b.image_base=base;b.read_memory=read_memory;b.read_context=read_context;
  return b;
}
bool ReadSelection12004(const Bindings &b,const void *handler,Selection &out,
    std::string &unavailable_reason) noexcept {
  out={};unavailable_reason.clear();
  if(!Pins(b)) {unavailable_reason="title_window12004_loaded_source_pins_changed";return false;}
  Selection first{},second{};
  if(!Pass(b,handler,first)) {unavailable_reason="title_window12004_native_window_unverified";return false;}
  if(!Pass(b,handler,second)||first!=second) {
    unavailable_reason="title_window12004_native_selection_changed";return false;
  }
  out=first;return true;
}
} // namespace xar::ck3_12004::title_ui
