#include "xar_bridge/artifact_personal_use12004.hpp"
#include <array>
#include <cstring>

#if defined(_WIN32) && defined(_MSC_VER)
#include <windows.h>
#endif

namespace xar::ck3_12004::artifact_personal_use {
namespace {
#if defined(_WIN32) && defined(_MSC_VER)
bool VisibleNative(const Env&e,const void*v,bool&out) noexcept {
  __try{out=reinterpret_cast<bool(__fastcall*)(const void*)>(e.existing.model.image_base+0x2160380)(v);return true;}
  __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
bool EquippedNative(const Env&e,const void*i,const void*a,bool&out) noexcept {
  __try{out=reinterpret_cast<bool(__fastcall*)(const void*,const void*)>(e.existing.model.image_base+0x22E4420)(i,a);return true;}
  __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
bool CanInSlotNative(const Env&e,const void*i,const void*a,const void*t,bool&out) noexcept {
  __try{out=reinterpret_cast<bool(__fastcall*)(const void*,const void*,const void*,void*)>(
      e.existing.model.image_base+0x22E47D0)(i,a,t,nullptr);return true;}
  __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
bool PickCall(const Env&e,const void*v,std::uint32_t category,const std::uint32_t*type,
              const void*&out) noexcept {
  __try{out=reinterpret_cast<const void*(__fastcall*)(const void*,std::uint32_t,
      const std::uint32_t*,const void*)>(e.existing.model.image_base+0x1623E70)(v,category,type,nullptr);return true;}
  __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
bool PickNative(const Env&e,const void*v,const void*a,const void*&out) noexcept {
  out=nullptr;const void*type=nullptr;std::uint32_t kind=0,category=absent;
  const auto&b=e.existing.model;
  if(!b.read_memory || !b.read_memory(b.read_context,static_cast<const char*>(a)+0xB8,&type,sizeof(type))||!type||
      !b.read_memory(b.read_context,static_cast<const char*>(type)+0x40,&kind,sizeof(kind))||
      !b.read_memory(b.read_context,static_cast<const char*>(type)+0x44,&category,sizeof(category)))return false;
  // These are the same two scalar arguments used by 1624420's default slot path.
  return PickCall(e,v,category,&kind,out);
}
struct NativeString {std::array<std::byte,32> bytes{};};
bool TextCall(const Env&e,const void*a,NativeString&out) noexcept {
  // Artifact.GetModifierEffects uses the out-string first ABI, unlike the older
  // holy-site window text helpers. This exact order is bound at 2536B36.
  __try{return reinterpret_cast<void*(__fastcall*)(void*,const void*)>(
      e.existing.model.image_base+0x252C000)(out.bytes.data(),a)==out.bytes.data();}
  __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
bool DestroyText(const Env&e,NativeString&out) noexcept {
  __try{reinterpret_cast<void(__fastcall*)(void*)>(e.existing.model.image_base+0x856050)(out.bytes.data());return true;}
  __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
bool TextNative(const Env&e,const void*a,std::string&text) noexcept {
  text.clear();NativeString raw{};if(!TextCall(e,a,raw))return false;
  bool copied=false;
  try{
    std::uint64_t size=0,capacity=0;const void*data=raw.bytes.data();
    std::memcpy(&size,raw.bytes.data()+16,8);std::memcpy(&capacity,raw.bytes.data()+24,8);
    if(size<=8192 && size<=capacity && (capacity==15||capacity>=16)){
      if(capacity>=16)std::memcpy(&data,raw.bytes.data(),sizeof(data));
      std::vector<char>copy(static_cast<std::size_t>(size)+1);
      if(data&&e.existing.model.read_memory&&e.existing.model.read_memory(
          e.existing.model.read_context,data,copy.data(),copy.size())&&copy.back()==0){
        text.assign(copy.data(),static_cast<std::size_t>(size));copied=true;
      }
    }
  }catch(...){copied=false;}
  const bool destroyed=DestroyText(e,raw);
  if(!copied||!destroyed)text.clear();return copied&&destroyed;
}
bool DispatchNative(const Env&e,const void*v,const void*a,bool desired_equipped) noexcept {
  // Both callbacks submit normal CK3 commands. Neither return proves acceptance
  // or final inventory state; never call low-level inventory mutators directly.
  __try{reinterpret_cast<void(__fastcall*)(const void*,const void*)>(e.existing.model.image_base+
      (desired_equipped?0x1624420:0x1625050))(v,a);return true;}
  __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
#endif
}
Env BindArtifactPersonalUseCallbacks12004(const religion::relic_permissions::Bindings&existing,
                                         std::string_view sha) noexcept {
  Env e{};e.existing=existing;e.admitted_executable_sha256=sha;
  if(sha!=kExecutableSha256||!existing.model.enabled||!existing.source_bound)return e;
#if defined(_WIN32) && defined(_MSC_VER)
  e.visible=&VisibleNative;e.pick=&PickNative;e.can_equip_in_slot=&CanInSlotNative;
  e.equipped=&EquippedNative;e.modifier_text=&TextNative;e.dispatch=&DispatchNative;
#endif
  // Mandatory integration inputs are intentionally absent. CMake, transport,
  // frame producer, public schema and central once ledger are not changed here.
  return e;
}
}
