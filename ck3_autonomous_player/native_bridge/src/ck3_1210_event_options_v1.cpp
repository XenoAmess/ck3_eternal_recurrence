#include "xar_bridge/ck3_1210_event_options_v1.hpp"
#include <cstring>
#include <limits>
#if defined(_MSC_VER)
#include <windows.h>
#endif

namespace xar::ck3_1210 {
namespace {
constexpr std::array<std::uint8_t,54> kCanSelectBytes{
  0x48,0x83,0xEC,0x28,0x80,0xB9,0xB5,0x01,0x00,0x00,0x00,0x75,0x09,0x80,0xB9,0xB4,
  0x01,0x00,0x00,0x00,0x74,0x19,0x48,0x8B,0x89,0x60,0x01,0x00,0x00,0x33,0xD2,0xE8,
  0x6C,0xCF,0xFF,0xFF,0x84,0xC0,0x74,0x07,0xB0,0x01,0x48,0x83,0xC4,0x28,0xC3,0x32,
  0xC0,0x48,0x83,0xC4,0x28,0xC3};
constexpr std::array<std::uint8_t,32> kCloneEntry{
  0x48,0x89,0x5C,0x24,0x08,0x57,0x48,0x83,0xEC,0x30,0x48,0x8B,0xD9,0x48,0x8B,0xFA,
  0xB9,0x28,0x00,0x00,0x00,0xE8,0x56,0xEA,0x95,0x01,0x4C,0x8B,0xC8,0x48,0x8D,0x05};
bool Pins(std::uintptr_t base) noexcept {
#if defined(_MSC_VER)
  const auto copy=[](std::uintptr_t address,void *target,std::size_t size) noexcept {
    SIZE_T read=0;return ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<const void *>(address),target,size,&read)&&read==size;
  };
  std::array<std::uint8_t,54> can{};std::array<std::uint8_t,32> clone{};
  std::uintptr_t clone_pointer=0,execute_pointer=0;
  return copy(base+kEventOptionCanSelectRvaV1,can.data(),can.size()) && can==kCanSelectBytes &&
      copy(base+0x2EB1660,clone.data(),clone.size()) && clone==kCloneEntry &&
      copy(base+kSelectEventPrimaryVtableRvaV1+0x40,&clone_pointer,sizeof(clone_pointer)) && clone_pointer==base+0x2EB1660 &&
      copy(base+kSelectEventSecondaryVtableRvaV1+8,&execute_pointer,sizeof(execute_pointer)) && execute_pointer==base+0x2EB11C0;
#else
  static_cast<void>(base);return false;
#endif
}
template<class T> bool Load(const void *p, std::size_t offset, T &out) noexcept {
  if (!p) return false;
  const auto address = reinterpret_cast<std::uintptr_t>(p);
  constexpr auto maximum = (std::numeric_limits<std::uintptr_t>::max)();
  if (offset > maximum-address || sizeof(T)-1 > maximum-address-offset) return false;
  std::memcpy(&out,reinterpret_cast<const void *>(address+offset),sizeof(T));
  return true;
}
struct Surface {
  void *owner=nullptr,*idler=nullptr,*manager=nullptr,*windows=nullptr,*window=nullptr,*items=nullptr;
  std::int32_t windows_capacity=0,windows_count=0,capacity=0,count=0,event_id=-1;
  std::array<void *,kEventOptionsMaxWindowsV1> all_windows{};
  std::array<EventOptionRowV1,kEventOptionsMaxShownV1> rows{};
  std::array<std::uint8_t,kEventOptionsMaxShownV1> raw_enabled{},fallback{};
  bool operator==(const Surface &) const = default;
};
bool SurfaceRead(const EventOptionsBindingsV1 &b, std::int32_t event_id,
    std::int32_t authored_count, Surface &s, std::string_view &reason) noexcept {
  reason="event_window_root_unavailable";
  std::uintptr_t vtable=0;
  if (!Load(b.current.core.jomini_state_slot,0,s.owner) || !s.owner ||
      !Load(s.owner,0x10,s.idler) || !s.idler || !Load(s.idler,0,vtable) ||
      vtable!=b.idler_vtable || !Load(s.idler,0x28,s.manager) || !s.manager) return false;
  reason="event_window_vector_invalid";
  if (!Load(s.manager,0x18,s.windows) || !Load(s.manager,0x20,s.windows_capacity) ||
      !Load(s.manager,0x24,s.windows_count) || s.windows_count<0 ||
      s.windows_count>static_cast<std::int32_t>(kEventOptionsMaxWindowsV1) ||
      s.windows_capacity<s.windows_count || (s.windows_count && !s.windows)) return false;
  std::size_t matches=0;
  for (std::int32_t i=0;i<s.windows_count;++i) {
    void *window=nullptr; std::int32_t id=-1;
    if (!Load(s.windows,static_cast<std::size_t>(i)*8,window) || !window ||
        !Load(window,0,vtable) || vtable!=b.window_vtable || !Load(window,0xB8,id)) return false;
    s.all_windows[static_cast<std::size_t>(i)]=window;
    if (id==event_id) {s.window=window;++matches;}
  }
  reason=matches ? "event_window_ambiguous" : "event_window_not_materialized";
  if(matches!=1) return false;
  const auto address=reinterpret_cast<std::uintptr_t>(s.window);
  if(address>(std::numeric_limits<std::uintptr_t>::max)()-0xB8) return false;
  const auto *data=reinterpret_cast<const void *>(address+0xB8);
  std::uint8_t closed=0;
  void *custom_selection_handler=nullptr;
  reason="event_option_vector_invalid";
  if(!Load(data,0,s.event_id) || s.event_id!=event_id || !Load(data,0x30,closed) || closed!=0 ||
      !Load(data,0x10,s.items) || !Load(data,0x18,s.capacity) || !Load(data,0x1C,s.count) ||
      s.count<0 || s.count>static_cast<std::int32_t>(kEventOptionsMaxShownV1) ||
      s.capacity<s.count || (s.count && !s.items) ||
      !Load(data,0x7C0,custom_selection_handler)) return false;
  if(custom_selection_handler) {reason="custom_event_selection_unavailable";return false;}
  std::array<bool,kCurrentEventMaxAuthoredV1> seen{};
  for(std::int32_t i=0;i<s.count;++i) {
    const auto at=static_cast<std::size_t>(i)*0x1B8;
    std::int32_t index=-1; std::uint8_t enabled=0,fallback=0; void *item_owner=nullptr;
    if(!Load(s.items,at+0x160,item_owner) || item_owner!=data ||
        !Load(s.items,at+0x1B0,index) || index<0 || index>=authored_count ||
        static_cast<std::size_t>(index)>=seen.size() || seen[static_cast<std::size_t>(index)] ||
        !Load(s.items,at+0x1B4,enabled) || enabled>1 ||
        !Load(s.items,at+0x1B5,fallback) || fallback>1) return false;
    seen[static_cast<std::size_t>(index)]=true;
    const auto offset=static_cast<std::size_t>(i);
    s.raw_enabled[offset]=enabled;s.fallback[offset]=fallback;
    const auto item_address=reinterpret_cast<std::uintptr_t>(s.items);
    if(item_address>(std::numeric_limits<std::uintptr_t>::max)()-at) return false;
    s.rows[offset]={index,b.can_select(reinterpret_cast<const void *>(item_address+at))};
  }
  return true;
}
bool Read(const EventOptionsBindingsV1 &b,const CoreSnapshotPrefix &expected,
    std::int32_t event_id,EventOptionsObservationV1 &out) noexcept {
  out={};
  if(!b.current.exact_build_admitted || !b.source_abi_pins_verified || !b.idler_vtable || !b.window_vtable || !b.can_select ||
      !expected.clock.paused || event_id<=0) return false;
  CurrentEventSnapshotObservationV1 before{},after{};
  if(!ReadCurrentEventSnapshotV1(b.current,expected,before)) {
    out.unavailable_reason=before.unavailable_reason;return false;
  }
  if(!before.found || before.active_event_instance_id!=event_id) {
    out.unavailable_reason=before.found?"event_mismatch":"no_active_event";return false;
  }
  Surface first{},second{}; std::string_view reason;
  if(!SurfaceRead(b,event_id,before.active_event_option_count,first,reason)) {
    out.unavailable_reason=reason;return false;
  }
  if(!ReadCurrentEventSnapshotV1(b.current,expected,after) || !after.found ||
      after.active_event_instance_id!=event_id ||
      after.active_event_option_count!=before.active_event_option_count) {
    out.unavailable_reason="current_event_changed";return false;
  }
  if(!SurfaceRead(b,event_id,after.active_event_option_count,second,reason) || !(first==second)) {
    out.unavailable_reason="event_window_changed";return false;
  }
  CurrentEventSnapshotObservationV1 tail{};
  if(!ReadCurrentEventSnapshotV1(b.current,expected,tail) || !tail.found ||
      tail.active_event_instance_id!=event_id || tail.active_event_option_count!=before.active_event_option_count) {
    out.unavailable_reason="current_event_changed";return false;
  }
  out.available=true;out.frame=tail.frame;out.event_instance_id=event_id;
  out.count=static_cast<std::size_t>(first.count);out.rows=first.rows;out.unavailable_reason={};return true;
}
} // namespace
EventOptionsBindingsV1 BindEventOptionsImageV1(std::uintptr_t base,std::string_view hash) noexcept {
  EventOptionsBindingsV1 b{};b.current=BindCurrentEventSnapshotImageV1(base,hash);
  if(!b.current.exact_build_admitted || base>(std::numeric_limits<std::uintptr_t>::max)()-kSelectEventPrimaryVtableRvaV1) return {};
  b.idler_vtable=base+kEventOptionsIdlerVtableRvaV1;b.window_vtable=base+kEventOptionsWindowVtableRvaV1;
  b.select_primary_vtable=base+kSelectEventPrimaryVtableRvaV1;b.select_secondary_vtable=base+kSelectEventSecondaryVtableRvaV1;
  b.can_select=reinterpret_cast<decltype(b.can_select)>(base+kEventOptionCanSelectRvaV1);
  b.source_abi_pins_verified=Pins(base);
  return b;
}
bool ReadEventOptionsV1(const EventOptionsBindingsV1 &b,const CoreSnapshotPrefix &expected,
    std::int32_t event_id,EventOptionsObservationV1 &out) noexcept {
#if defined(_MSC_VER)
  __try {return Read(b,expected,event_id,out);}
  __except(EXCEPTION_EXECUTE_HANDLER) {out={};out.unavailable_reason="memory_read_failed";return false;}
#else
  return Read(b,expected,event_id,out);
#endif
}
SelectEventCommandV1 MakeSelectEventCommandV1(const EventOptionsBindingsV1 &b,
    std::int32_t event_id,std::int32_t index) noexcept {
  SelectEventCommandV1 result{};result.primary_vtable=b.select_primary_vtable;
  result.secondary_vtable=b.select_secondary_vtable;result.event_instance_id=event_id;
  result.native_option_index=index;return result;
}
} // namespace xar::ck3_1210
