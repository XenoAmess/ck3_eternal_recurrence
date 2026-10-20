#include "xar_bridge/character_skill_effect12004_native.hpp"
#include "xar_bridge/character_skill_effect12004_pins.hpp"
#include <windows.h>
#include <array>
#include <cstring>
#include <limits>

namespace xar::bridge::character_skill_effect12004 {
namespace {
bool Copy(std::uintptr_t at,void *out,std::size_t n) noexcept {
  SIZE_T got=0;
  return at!=0&&out!=nullptr&&n!=0&&
      ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<const void *>(at),out,n,&got)!=0&&got==n;
}
template<class T>bool At(std::uintptr_t p,std::size_t off,T &out) noexcept {
  return p!=0&&off<=(std::numeric_limits<std::uintptr_t>::max)()-p&&Copy(p+off,&out,sizeof(out));
}
template<std::size_t N>bool Match(std::uintptr_t base,std::uintptr_t rva,
    const std::array<std::uint8_t,N> &expected) noexcept {
  std::array<std::uint8_t,N> actual{};
  return base!=0&&rva<=(std::numeric_limits<std::uintptr_t>::max)()-base&&
      Copy(base+rva,actual.data(),actual.size())&&actual==expected;
}
bool Current(NativeContext &c) noexcept {
  Frame f{};
  return c.enabled&&c.module_base!=0&&c.executable_sha256==kExeSha&&
      c.owner_thread_id!=0&&GetCurrentThreadId()==c.owner_thread_id&&
      c.snapshot_frame!=nullptr&&c.snapshot_frame(c.snapshot_context,f)&&
      f==c.expected&&f.owner_thread&&f.paused&&f.map_ready&&f.revision!=0;
}
bool ResolveActual(NativeContext &c,std::uintptr_t &actor,std::uintptr_t &values) noexcept {
  std::uintptr_t storage=0,rows=0;std::uint32_t count=0,id=0xFFFFFFFFU,magic=0;
  const auto wanted=c.requested_character_id;
  return wanted!=0xFFFFFFFFU&&At(c.module_base,0x5C67568,storage)&&storage!=0&&
      At(storage,0x20,rows)&&rows!=0&&At(storage,0x2C,count)&&count<=0x1000000U&&
      (wanted&0xFFFFFFU)<count&&At(rows,static_cast<std::size_t>(wanted&0xFFFFFFU)*16U+8U,actor)&&
      actor!=0&&At(actor,0x18,id)&&id==wanted&&At(actor,0x1C,magic)&&magic==0x43686172U&&
      At(actor,0x1B0,values)&&values!=0;
}
[[maybe_unused]] bool Memory(void *opaque,std::uintptr_t at,void *out,std::size_t n) noexcept {
  auto &c=*static_cast<NativeContext *>(opaque);
  return Current(c)&&Copy(at,out,n);
}
[[maybe_unused]] bool FrameRead(void *opaque,Frame &out) noexcept {
  auto &c=*static_cast<NativeContext *>(opaque);
  if(!Current(c))return false;out=c.expected;return true;
}
struct NativeString32 {
  std::array<unsigned char,16> storage{};
  std::uint64_t size=0,capacity=15;
};
static_assert(sizeof(NativeString32)==32);
static_assert(offsetof(NativeString32,size)==0x10&&offsetof(NativeString32,capacity)==0x18);
// SEH functions deliberately contain POD only; C++ string copying is outside.
bool LevelCall(std::uintptr_t base,std::uintptr_t actor,std::int32_t &out) noexcept {
  using Fn=std::int32_t (*)(void *);
  __try {out=reinterpret_cast<Fn>(base+pins::level_rva)(reinterpret_cast<void *>(actor));return true;}
  __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
bool TextCall(std::uintptr_t base,SkillItem &item,NativeString32 &out) noexcept {
  using Fn=NativeString32 *(*)(SkillItem *,NativeString32 *);
  __try {return reinterpret_cast<Fn>(base+pins::breakdown_rva)(&item,&out)==&out;}
  __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
bool DestroyCall(std::uintptr_t base,NativeString32 &value) noexcept {
  using Fn=void (*)(NativeString32 *);
  __try {reinterpret_cast<Fn>(base+pins::string_destroy_rva)(&value);return true;}
  __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
bool Utf8(std::string_view text) noexcept {
  std::size_t i=0;
  while(i<text.size()){
    const auto b=static_cast<unsigned char>(text[i++]);if(b<0x80)continue;
    unsigned n=0,lo=0x80,hi=0xBF;
    if(b>=0xC2&&b<=0xDF)n=1;
    else if(b>=0xE0&&b<=0xEF){n=2;if(b==0xE0)lo=0xA0;if(b==0xED)hi=0x9F;}
    else if(b>=0xF0&&b<=0xF4){n=3;if(b==0xF0)lo=0x90;if(b==0xF4)hi=0x8F;}
    else return false;
    if(n>text.size()-i)return false;
    for(unsigned j=0;j<n;++j){const auto c=static_cast<unsigned char>(text[i++]);if(c<(j==0?lo:0x80)||c>(j==0?hi:0xBF))return false;}
  }return true;
}
[[maybe_unused]] bool Level(void *opaque,std::uintptr_t actual,std::int32_t &out) noexcept {
  auto &c=*static_cast<NativeContext *>(opaque);std::uintptr_t actor=0,values=0;
  if(!Current(c)||!NativeSourceStillBound(c)||!ResolveActual(c,actor,values)||actor!=actual){c.failure="native_level_identity_or_source_unavailable";return false;}
  ++c.level_calls;
  const bool called=LevelCall(c.module_base,actual,out);
  std::uintptr_t after=0,after_values=0;
  if(!called||!Current(c)||!ResolveActual(c,after,after_values)||after!=actor||after_values!=values){c.failure="native_level_call_or_identity_changed";return false;}
  return true;
}
[[maybe_unused]] bool Breakdown(void *opaque,const SkillItem &requested,std::string &out) noexcept {
  auto &c=*static_cast<NativeContext *>(opaque);out.clear();
  std::uintptr_t actor=0,values=0;
  if(requested.skill<0||requested.skill>=6||requested.character_id!=c.requested_character_id||
      !Current(c)||!NativeSourceStillBound(c)||!ResolveActual(c,actor,values)){
    c.failure="native_breakdown_identity_or_source_unavailable";return false;
  }
  // SkillItem is the normal eight-byte GUI VALUE adapter, not a CCharacter,
  // Site or other fabricated gameplay object. CA1DF0 consumes enum+full ID;
  // it resolves the genuine stored character itself. No caller pointer is
  // inserted into a registry or treated as a game-owned identity.
  SkillItem item=requested;NativeString32 text{};++c.breakdown_calls;
  const bool invoked=TextCall(c.module_base,item,text);
  bool copied=false;
  try {
    if(invoked&&text.size<=kMaxBreakdownBytes&&text.size<=text.capacity){
      std::uintptr_t data=reinterpret_cast<std::uintptr_t>(text.storage.data());
      if(text.capacity>=16)std::memcpy(&data,text.storage.data(),sizeof(data));
      if(text.size==0)copied=true;
      else if(data!=0){out.resize(static_cast<std::size_t>(text.size));copied=Copy(data,out.data(),out.size())&&Utf8(out);}
    }
  }catch(...){copied=false;}
  // The owned empty string was initialized before the native member call.
  // Even a failed/partial invocation gets one protected real destructor try.
  ++c.string_destroy_calls;const bool destroyed=DestroyCall(c.module_base,text);
  std::uintptr_t after=0,after_values=0;
  if(!invoked||!copied||!destroyed||!Current(c)||!ResolveActual(c,after,after_values)||
      after!=actor||after_values!=values){out.clear();c.failure="native_breakdown_call_copy_cleanup_or_identity_changed";return false;}
  return true;
}
} // namespace
bool NativeSourceStillBound(NativeContext &c) noexcept {
  return Current(c)&&Match(c.module_base,pins::level_rva,pins::level_code)&&
      Match(c.module_base,pins::breakdown_rva,pins::breakdown_code)&&
      Match(c.module_base,pins::string_destroy_rva,pins::string_destroy_code);
}
Environment BindNative(NativeContext &c) noexcept {
  Environment e{};
#if defined(XAR_CK3_ENABLE_CHARACTER_SKILL_EFFECTS12004_PRIVATE_QUERY_V1)
  if(!Current(c)||!NativeSourceStillBound(c)){c.failure="exact4_native_actor_getter_pins_or_owner_unavailable";return e;}
  e={true,kExeSha,c.module_base,&c,&Memory,&FrameRead,&Level,&Breakdown,CallbackProvenance::exact4_native,false};
  c.failure="";
#else
  (void)c;
#endif
  return e;
}
} // namespace xar::bridge::character_skill_effect12004
