// Included once by the existing character_skill_effect12004_native.cpp TU.
#include "xar_bridge/character_knight_effectiveness12004.hpp"
#include "xar_bridge/knight_stat_context_source12004.hpp"
#include "xar_bridge/character_knight_effectiveness12004_owned_string.hpp"
namespace xar::bridge::character_skill_effect12004 {
namespace knight_native {
// Exact pins are generated from ABI-SPANS.frozen.actual.json, not legacy RVA
// shifts. All four bodies are checked before and after each guarded callback.
#include "character_knight_effectiveness12004_pins.inc"
bool Source(NativeContext &c) noexcept {
  if(!Current(c)||!NativeSourceStillBound(c)||
      !Match(c.module_base,kNumericRva,kNumericCode)||
      !Match(c.module_base,kFormatterRva,kFormatterCode))return false;
#if defined(XAR_CK3_ENABLE_CHARACTER_SKILL_EFFECTS12004_PRIVATE_QUERY_V1)
  static_assert(kContextRva==xar::ck3_12004::kKnightStatContextSourceRva12004);
  if(!xar::ck3_12004::KnightStatContextSourceStillBound12004(c.module_base,kContextCode,c.failure))return false;
#else
  // Preserve the original disabled-build source route and standalone OFF link.
  if(!Match(c.module_base,kContextRva,kContextCode))return false;
#endif
  return Match(c.module_base,pins::string_destroy_rva,kDestroyCode);
}
bool Backing(NativeContext &c,std::uintptr_t &actor,std::uintptr_t &values,
             std::uintptr_t &block) noexcept {
  std::uintptr_t owner=0;
  return ResolveActual(c,actor,values)&&At(values,0x258,block)&&block&&
      At(block,8,owner)&&owner==actor;
}
// POD only: compiler SEH boundary contains no C++ string destructor.
bool Calls(std::uintptr_t base,std::uintptr_t actor,std::int64_t &raw,
           NativeString32 &text) noexcept {
  using Numeric=std::int64_t *(*)(std::int64_t *,void *,NativeString32 *);
  using Formatter=NativeString32 *(*)(NativeString32 *,void *);
  __try {
    return reinterpret_cast<Numeric>(base+kNumericRva)(&raw,reinterpret_cast<void *>(actor),nullptr)==&raw&&
        reinterpret_cast<Formatter>(base+kFormatterRva)(&text,reinterpret_cast<void *>(actor))==&text;
  }__except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
[[maybe_unused]] bool Read(void *opaque,std::uintptr_t requested,std::int64_t &raw,
                          std::string &out) noexcept {
  auto &c=*static_cast<NativeContext *>(opaque);out.clear();raw=0;
  std::uintptr_t actor=0,values=0,block=0;
  if(!Source(c)||!Backing(c,actor,values,block)||actor!=requested){
    c.failure="native_knight_own_actor_context_or_source_unavailable";return false;
  }
  NativeString32 text{};std::int64_t actual=0;++c.breakdown_calls;
  const bool invoked=Calls(c.module_base,actor,actual,text);
  // Copy before exactly one protected real destructor attempt, including the
  // initialized partial-call failure path. No free from another CRT is used.
  const bool copied_and_destroyed=knight_string_detail::CopyThenDestroy(invoked,text,out,
      [](std::uintptr_t at,void *to,std::size_t n) noexcept{return Copy(at,to,n);},
      [](std::string_view value) noexcept{return Utf8(value);},
      [&c](NativeString32 &value) noexcept{++c.string_destroy_calls;return DestroyCall(c.module_base,value);});
  std::uintptr_t after=0,after_values=0,after_block=0;
  if(!copied_and_destroyed||!Source(c)||!Backing(c,after,after_values,after_block)||
      after!=actor||after_values!=values||after_block!=block){
    out.clear();c.failure="native_knight_call_copy_cleanup_or_owner_changed";return false;
  }
  raw=actual;return true;
}
} // namespace knight_native
KnightEnvironment BindKnightNative(NativeContext &c) noexcept {
  KnightEnvironment out{};
#if defined(XAR_CK3_ENABLE_CHARACTER_SKILL_EFFECTS12004_PRIVATE_QUERY_V1)
  out.actor=BindNative(c);
  if(!out.actor.enabled){
    c.failure="exact4_knight_native_pins_or_owner_unavailable";return {};
  }
  if(!knight_native::Source(c)){
    if(c.failure==nullptr||*c.failure=='\0')c.failure="exact4_knight_native_pins_or_owner_unavailable";
    return {};
  }
  out.read_knight=&knight_native::Read;c.failure="";
#else
  (void)c;
#endif
  return out;
}
} // namespace xar::bridge::character_skill_effect12004
