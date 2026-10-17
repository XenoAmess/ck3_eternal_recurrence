#include "xar_bridge/ck3_12004_holy_site_ui.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include <windows.h>
#include <array>
#include <cstring>
#include <limits>

namespace xar::ck3_11906 {
namespace {
constexpr std::uintptr_t kStorage=0x5D1DE80, kWindowVtable=0x4592338,
    kWindowSecondaryVtable=0x4592310;
template<class T> bool Read(const void *p,std::size_t o,T &out) noexcept {
  const auto base=reinterpret_cast<std::uintptr_t>(p);
  if(!base||o>std::numeric_limits<std::uintptr_t>::max()-base)return false;
  SIZE_T got=0;return ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<const void *>(base+o),&out,sizeof(out),&got)&&got==sizeof(out);
}
bool Exact(const ZhongguoScoreboardNativeEnvironmentV1 &e) noexcept {
  return e.exact_build_admitted&&!e.offline_fixture_function_overrides&&e.module_base&&
      e.gui_abi_revision==GuiAbiRevisionV1::crozier12004&&e.executable_sha256==ck3_12004::kExecutableSha256;
}
template<std::size_t N> bool Pin(std::uintptr_t base,std::uintptr_t rva,const std::array<unsigned char,N>&expected) noexcept {
  std::array<unsigned char,N> actual{};SIZE_T got=0;
  return ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<const void *>(base+rva),actual.data(),N,&got)&&got==N&&actual==expected;
}
bool Pins(const ZhongguoScoreboardNativeEnvironmentV1&e) noexcept {
  return Exact(e)&&
    Pin(e.module_base,0xAF39E0,std::array<unsigned char,32>{0x48,0x89,0x5c,0x24,0x08,0x48,0x89,0x74,0x24,0x10,0x48,0x89,0x7c,0x24,0x18,0x41,0x56,0x48,0x83,0xec,0x50,0x4d,0x8b,0xf0,0x8b,0xfa,0x48,0x8b,0xd9,0xe8,0x4e,0xff})&&
    Pin(e.module_base,0xD55AD0,std::array<unsigned char,32>{0x48,0x83,0xec,0x28,0x65,0x48,0x8b,0x04,0x25,0x58,0x00,0x00,0x00,0xba,0x10,0x00,0x00,0x00,0x48,0x8b,0x08,0x8b,0x04,0x0a,0x39,0x05,0xb6,0xa1,0xfc,0x04,0x7f,0x0c})&&
    Pin(e.module_base,0xAEB2D0,std::array<unsigned char,12>{0x8b,0x81,0xc8,0x00,0x00,0x00,0x89,0x02,0x48,0x8b,0xc2,0xc3})&&
    Pin(e.module_base,0x8771F0,std::array<unsigned char,6>{0x8b,0x02,0x41,0x89,0x00,0xc3})&&
    Pin(e.module_base,0x876E00,std::array<unsigned char,4>{0x48,0x8b,0xc2,0xc3})&&
    Pin(e.module_base,0x8522C0,std::array<unsigned char,3>{0xc2,0x00,0x00});
}
bool Site(const ZhongguoScoreboardNativeEnvironmentV1&e,std::uint32_t id) noexcept {
  if(id==0xFFFFFFFFU)return false;
  void *storage=nullptr,*rows=nullptr,*site=nullptr;std::uint32_t count=0,actual=0,magic=0;
  return Read(reinterpret_cast<void *>(e.module_base+kStorage),0,storage)&&storage&&
      Read(storage,0x20,rows)&&rows&&Read(storage,0x2C,count)&&(id&0xFFFFFFU)<count&&
      Read(rows,static_cast<std::size_t>(id&0xFFFFFFU)*16+8,site)&&site&&
      Read(site,0x10,actual)&&actual==id&&Read(site,0x14,magic)&&magic==0x486F5374U;
}
bool Window(const ZhongguoScoreboardNativeEnvironmentV1&e,void *handler,void *&window,void *&root) noexcept {
  std::uintptr_t a=0,b=0;void *back=nullptr,*gfx=nullptr;
  return Read(handler,0x5D8,window)&&window&&Read(window,0,a)&&a==e.module_base+kWindowVtable&&
      Read(window,0x10,b)&&b==e.module_base+kWindowSecondaryVtable&&
      Read(window,0xA0,back)&&back==handler&&Read(window,0x98,gfx)&&gfx&&Read(window,0x60,root);
}
struct Any {void *type=nullptr;std::array<std::uint8_t,32> data{};};
static_assert(sizeof(Any)==40);
bool NativeOpen(std::uintptr_t base,void *handler,std::uint32_t id,bool &attempted) noexcept {
  // The closed typed value is one inplace DWORD; copy and destructor source
  // prove no borrowed stack payload or heap ownership survives this call.
#if defined(_MSC_VER)
  __try {
#endif
    Any argument{};
    argument.type=reinterpret_cast<void *(__fastcall *)()>(base+0xD55AD0)();
    std::uintptr_t vt=0;
    if(!argument.type||!Read(argument.type,0,vt)||vt!=base+0x44E8DA0)return false;
    std::memcpy(argument.data.data(),&id,sizeof(id));
    attempted=true;
    reinterpret_cast<void(__fastcall *)(void *,std::uint32_t,const void *)>(base+0xAF39E0)(handler,0xA8,&argument);
    return true;
#if defined(_MSC_VER)
  }__except(EXCEPTION_EXECUTE_HANDLER){return false;}
#endif
}
}
bool HolySiteUiCanOpen12004(const ZhongguoScoreboardNativeEnvironmentV1&e,void *handler,std::uint32_t id) noexcept {
  void *window=nullptr,*root=nullptr;
  return Pins(e)&&Window(e,handler,window,root)&&Site(e,id);
}
bool InvokeHolySiteUi12004(const ZhongguoScoreboardNativeEnvironmentV1&e,void *handler,std::uint32_t id,bool &attempted) noexcept {
  attempted=false;
  if(!HolySiteUiCanOpen12004(e,handler,id))return false;
  return NativeOpen(e.module_base,handler,id,attempted);
}
bool ResolveHolySiteUiSelection12004(const ZhongguoScoreboardNativeEnvironmentV1&e,
    void *handler,std::uint32_t id,void *&window,void *&root) noexcept {
  window=root=nullptr;std::uint32_t selected=0xFFFFFFFFU;
  return Pins(e)&&Window(e,handler,window,root)&&Read(window,0xC8,selected)&&selected==id&&Site(e,id);
}
bool ReadHolySiteUi12004(const ZhongguoScoreboardNativeEnvironmentV1&e,void *handler,IngameUiResultV1&out) noexcept {
  out.tree.scope_root_name="holy_site_window";
  const auto fail=[&](const char *why){out.unavailable_reason=why;return false;};
  if(!Pins(e))return fail("holy_site_loaded_source_pins_changed");
  void *window=nullptr,*native_root=nullptr;
  if(!Window(e,handler,window,native_root))return fail("holy_site_registered_window_unverified");
  if(!native_root)return fail("holy_site_gui_root_not_created");
  ZhongguoScoreboardAccessV1 access{};void *root=nullptr,*widget=nullptr;
  if(!ResolveNamedGuiWidgetV1(e,access,"holy_site_window","holy_site_window",root,widget)||
      root!=native_root||widget!=root)return fail("holy_site_gui_root_binding_unavailable");
  std::string name;void *vt=nullptr;
  if(!ReadGuiWidgetRuntimeV1(access,root,name,vt,out.effective_visible,out.enabled)||name!="holy_site_window"||
      !InspectNamedGuiSubtreeV1(access,e.module_base,root,"holy_site_window",out.tree))return fail("holy_site_gui_census_unavailable");
  out.window_exists=true;
  std::uint32_t id=0xFFFFFFFFU;
  if(!Read(window,0xC8,id))return fail("holy_site_window_selection_unreadable");
  out.subject_id_available=Site(e,id);
  if(out.subject_id_available)out.current_subject_id=id;
  void *later_window=nullptr,*later_root=nullptr;std::uint32_t later_id=0;
  std::string later_name;void *later_vt=nullptr;bool visible=false,enabled=false;
  if(!Window(e,handler,later_window,later_root)||later_window!=window||later_root!=root||
      !Read(window,0xC8,later_id)||later_id!=id||Site(e,later_id)!=out.subject_id_available||
      !ReadGuiWidgetRuntimeV1(access,root,later_name,later_vt,visible,enabled)||later_name!=name||
      later_vt!=vt||visible!=out.effective_visible||enabled!=out.enabled)return fail("holy_site_window_changed_during_read");
  out.unavailable_reason.clear();return true;
}
}
