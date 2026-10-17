#include "xar_bridge/ck3_12004_holy_site_decision_cooldown.hpp"
#include <windows.h>
#include <array>
#include <limits>

namespace xar::ck3_12004::religion::holy_site {
namespace {
const void*At(const void*p,std::size_t offset) noexcept {
 const auto address=reinterpret_cast<std::uintptr_t>(p);
 return address&&offset<=std::numeric_limits<std::uintptr_t>::max()-address?
  reinterpret_cast<const void*>(address+offset):nullptr;
}
template<class T>bool Read(const DecisionCooldownBindings&b,const void*p,std::size_t offset,T&out)noexcept{
 const auto*address=At(p,offset);
 return address&&b.native.read_memory&&b.native.read_memory(b.native.read_context,address,&out,sizeof(out));
}
bool Pin(const DecisionCooldownBindings&b,std::uintptr_t rva,std::string_view hex)noexcept{
 if(hex.empty()||hex.size()%2||hex.size()>64)return false;
 std::array<unsigned char,32>expected{},actual{};
 const auto digit=[](char c){return c>='0'&&c<='9'?c-'0':c-'a'+10;};
 for(std::size_t i=0;i<hex.size()/2;++i)expected[i]=static_cast<unsigned char>((digit(hex[2*i])<<4)|digit(hex[2*i+1]));
 return b.native.read_memory&&b.native.read_memory(b.native.read_context,
  reinterpret_cast<const void*>(b.image_base+rva),actual.data(),hex.size()/2)&&actual==expected;
}
bool Pins(const DecisionCooldownBindings&b)noexcept{
 return Pin(b,0xA14850,"4883ec38488b05959630054885c07542c74424281e000000488d05a987a70348")&&
  Pin(b,0x3F7E220,"894c2408534883ec2033c0488d4c2430418bd889442430458bc8894424404c8b")&&
  Pin(b,0xCAA8D0,"48895c24084533c04863da443881e00e0000458bc8410f94c1458d58fe4585c9");
}
bool ExactDefinition(const DecisionCooldownBindings&b,const void*definition,std::string_view key){
 std::uintptr_t vt=0,col=0;std::uint32_t signature=0,td=0,self=0,magic=0;
 if(!Read(b,definition,0,vt)||vt!=b.image_base+0x48BD150||
    !Read(b,reinterpret_cast<const void*>(vt-8),0,col)||!col||
    !Read(b,reinterpret_cast<const void*>(col),0,signature)||signature!=1||
    !Read(b,reinterpret_cast<const void*>(col),12,td)||td!=0x5586B90||
    !Read(b,reinterpret_cast<const void*>(col),20,self)||col!=b.image_base+self||
    !Read(b,definition,0x38,magic)||magic!=0x4744624FU)return false;
 const void*text=At(definition,0x18);std::uint64_t size=0,capacity=0;
 if(!Read(b,text,16,size)||!Read(b,text,24,capacity)||size!=key.size()||size>capacity||
    (capacity<16&&capacity!=15))return false;
 if(capacity>=16&&(!Read(b,text,0,text)||!text))return false;
 std::array<char,64>bytes{};
 return size<bytes.size()&&b.native.read_memory(b.native.read_context,text,bytes.data(),
  static_cast<std::size_t>(size)+1)&&bytes[static_cast<std::size_t>(size)]==0&&
  std::string_view(bytes.data(),static_cast<std::size_t>(size))==key;
}
struct Resolution {
 void*database=nullptr;const void*fallback=nullptr,*definition=nullptr;
 bool operator==(const Resolution&)const=default;
};
bool CallLookup(const DecisionCooldownBindings&b,void*database,std::string_view key,const void*&definition)noexcept{
#if defined(_MSC_VER)
 __try{
#endif
  const auto hash=b.decision_hash(database,key.data(),static_cast<std::uint32_t>(key.size()));
  definition=b.decision_lookup(database,hash);return true;
#if defined(_MSC_VER)
 }__except(EXCEPTION_EXECUTE_HANDLER){return false;}
#endif
}
bool Resolve(const DecisionCooldownBindings&b,DecisionAction action,Resolution&out){
 const auto key=DecisionKey(action);void*after_database=nullptr;const void*after_fallback=nullptr;
 if(key.empty()||!Read(b,b.decision_database,0,out.database)||!out.database||
    !Read(b,b.decision_fallback,0,out.fallback)||
    !CallLookup(b,out.database,key,out.definition)||!out.definition||out.definition==out.fallback||
    !ExactDefinition(b,out.definition,key)||
    !Read(b,b.decision_database,0,after_database)||after_database!=out.database||
    !Read(b,b.decision_fallback,0,after_fallback)||after_fallback!=out.fallback)return false;
 return true;
}
}
DecisionCooldownBindings BindHolySiteDecisionCooldownImage12004(std::uintptr_t base,std::string_view sha)noexcept{
 DecisionCooldownBindings b{};if(!base||sha!=ck3_12004::kExecutableSha256)return b;
 b.enabled=true;b.image_base=base;b.native=BindHolySiteAdoptionDetailImage12004(base,sha);
 // Same exact .4 entries and types as religion_context_addons::DecisionBindings.
 b.decision_database=reinterpret_cast<void**>(base+0x5D1DEF0);
 b.decision_fallback=reinterpret_cast<const void**>(base+0x5D1F7E8);
 b.decision_hash=reinterpret_cast<decltype(b.decision_hash)>(base+0x3F7E220);
 b.decision_lookup=reinterpret_cast<decltype(b.decision_lookup)>(base+0xCAA8D0);return b;
}
bool ReadHolySiteDecisionCooldown12004(const DecisionCooldownBindings&b,
 const ck3_12002::religion::Context&context,DecisionAction action,DecisionCooldownSnapshot&out)noexcept{
 out={};out.action=action;out.capture_epoch=context.capture_epoch;out.date_raw=context.date_raw;
 out.played_character_id=context.played_character_id;
 const auto fail=[&](const char*why){out.unavailable_reason=why;return false;};
 try{
  if(!b.enabled||!b.image_base||!b.native.enabled||b.native.image_base!=b.image_base||
     !b.native.read_memory||!b.decision_database||!b.decision_fallback||!b.decision_hash||!b.decision_lookup||
     !context.available||!context.capture_epoch||context.played_character_id<=0||DecisionKey(action).empty())
   return fail("holy_site_decision_cooldown_bindings_or_frame_unavailable");
  if(!Pins(b))return fail("holy_site_decision_registry_source_pins_changed");
  Resolution before{},after{};
  if(!Resolve(b,action,before))return fail("holy_site_decision_definition_unavailable");
  DecisionCooldownObservation observed{};
  // The real helper verifies actor fullID, map/clock source, bounded rows and two
  // stable passes. No detail or synthetic actor-only script context is used.
  if(!ReadHolySiteDecisionCooldownByDefinition12004(b.native,context,action,before.definition,observed))
   return fail("holy_site_decision_cooldown_native_unavailable");
  if(!Resolve(b,action,after)||before!=after||!Pins(b))
   return fail("holy_site_decision_definition_or_registry_changed");
  out.cooldown=observed;out.available=true;return true;
 }catch(...){return fail("holy_site_decision_cooldown_capture_exception");}
}
}
