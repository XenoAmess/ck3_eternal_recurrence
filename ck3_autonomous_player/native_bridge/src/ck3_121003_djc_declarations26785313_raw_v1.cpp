#include "xar_bridge/ck3_121003_djc_declarations26785313_raw_v1.hpp"
#include "xar_bridge/ck3_121003_declarations26785313_abi_v1.hpp"
#include "xar_bridge/ck3_121003_declarations26785313_pins_v1.hpp"
#include <algorithm>
#include <cstring>
#include <limits>
#include <utility>
#include <windows.h>
namespace xar::ck3_121003::build26785313 {namespace {
namespace abi=declarations_abi_v1;
[[maybe_unused]]bool Copy(std::uintptr_t p,void*out,std::size_t n)noexcept{if(!p||!out||!n||n-1>(std::numeric_limits<std::uintptr_t>::max)()-p)return false;__try{std::memcpy(out,reinterpret_cast<const void*>(p),n);return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
template<class T>bool At(std::uintptr_t p,std::size_t off,T&v)noexcept{return off<=(std::numeric_limits<std::uintptr_t>::max)()-p&&Copy(p+off,&v,sizeof(v));}
[[maybe_unused]]bool Same(const ck3_1210::CoreSnapshotPrefix&a,const ck3_1210::CoreSnapshotPrefix&b)noexcept{return a.clock.date_raw==b.clock.date_raw&&a.clock.speed==b.clock.speed&&a.clock.paused==b.clock.paused&&a.local_player_id==b.local_player_id&&a.map_ready==b.map_ready&&a.has_played_character==b.has_played_character&&a.played_character_id==b.played_character_id&&a.played_character_alive==b.played_character_alive;}
[[maybe_unused]]bool Prefix(const ck3_1210::CoreSnapshotPrefix&p)noexcept{return p.clock.paused&&p.clock.speed>=1&&p.clock.speed<=5&&p.local_player_id>=0&&p.map_ready&&p.has_played_character&&p.played_character_id!=-1&&p.played_character_alive;}
[[maybe_unused]]bool Core(const ReadonlyBindings&b,ck3_1210::CoreSnapshotPrefix&out)noexcept{__try{return ck3_1210::ReadCoreSnapshot(b.core,out);}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
[[maybe_unused]]bool Character(const ReadonlyBindings&b,std::int32_t id,std::uintptr_t&out)noexcept{__try{out=reinterpret_cast<std::uintptr_t>(ck3_1210::ResolveCoreCharacter(b.core,id));void*death=nullptr;return out&&At(out,ck3_1210::kCharacterDeathDataOffset,death)&&!death;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
[[maybe_unused]]bool Key(std::uintptr_t p,std::string&out){std::uint64_t size=0,cap=0;std::uintptr_t chars=p+abi::k_cb_key_offset;if(!At(chars,16,size)||!At(chars,24,cap)||size==0||size>256||size>cap||cap<15)return false;if(cap>15&&!At(chars,0,chars))return false;std::string s(static_cast<std::size_t>(size),'\0');if(!Copy(chars,s.data(),s.size()))return false;for(char c:s)if(!((c>='a'&&c<='z')||(c>='A'&&c<='Z')||(c>='0'&&c<='9')||c=='_'))return false;out=std::move(s);return true;}
[[maybe_unused]]bool Array(std::uintptr_t p,std::vector<std::int32_t>&out){std::uintptr_t data=0;std::int32_t cap=0,count=0;if(!At(p,0,data)||!At(p,8,cap)||!At(p,12,count)||cap<0||count<0||count>cap||count>10000||(count&&!data))return false;out.resize(static_cast<std::size_t>(count));return !count||Copy(data,out.data(),out.size()*4);}
[[maybe_unused]]bool Database(std::uintptr_t base,std::uintptr_t&out)noexcept{__try{out=reinterpret_cast<std::uintptr_t>(reinterpret_cast<void*(*)()>(base+abi::k_cb_database_getter)());return out!=0;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
[[maybe_unused]]bool Evaluate(std::uintptr_t base,std::uintptr_t type,std::uintptr_t actor,std::uintptr_t target,bool&available)noexcept{__try{available=reinterpret_cast<abi::EvaluateCb>(base+abi::k_evaluate_cb)(reinterpret_cast<void*>(type),reinterpret_cast<void*>(actor),reinterpret_cast<void*>(target),reinterpret_cast<void*>(base+abi::k_configuration_scratch),false,false,nullptr);return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
[[maybe_unused]]bool Destroy(std::uintptr_t base,std::uintptr_t p)noexcept{__try{reinterpret_cast<abi::Destroy>(base+abi::k_destroy_configuration)(reinterpret_cast<void*>(p));return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
[[maybe_unused]]bool Scratch(std::uintptr_t base,std::uintptr_t&data,std::int32_t&count)noexcept{std::int32_t cap=0;const auto p=base+abi::k_configuration_scratch;return At(p,0,data)&&At(p,8,cap)&&At(p,12,count)&&cap>=0&&count>=0&&count<=cap&&count<=10000&&(!count||data);}
[[maybe_unused]]bool Clear(std::uintptr_t base)noexcept{std::uintptr_t data=0;std::int32_t count=0;if(!Scratch(base,data,count))return false;for(std::int32_t i=0;i<count;++i)if(!Destroy(base,data+static_cast<std::uintptr_t>(i)*abi::k_configuration_size))return false;__try{*reinterpret_cast<std::int32_t*>(base+abi::k_configuration_scratch+12)=0;return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
}
bool VerifyCurrentDjcDeclarationsImage267V1([[maybe_unused]]std::uintptr_t base)noexcept{
#if defined(XAR_CK3_ENABLE_121003_26785313_DJC_DECLARATIONS_V1) && XAR_CK3_ENABLE_121003_26785313_DJC_DECLARATIONS_V1
 if(base!=reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr))||!VerifyReadonlyImage(base))return false;
 std::array<unsigned char,256>buf{};for(const auto&p:abi::pins::kRaw)if(p.bytes.empty()||p.bytes.size()>buf.size()||p.rva>kImageSize-p.bytes.size()||!Copy(base+p.rva,buf.data(),p.bytes.size())||std::memcmp(buf.data(),p.bytes.data(),p.bytes.size()))return false;
 for(const auto&p:abi::pins::kASLR){std::uintptr_t v=0;if(!At(base,p.slot,v)||v!=base+p.target)return false;}return true;
#else
 return false;
#endif
}
DjcRawBindings267V1 BindCurrentDjcDeclarations267V1([[maybe_unused]]std::uintptr_t base,[[maybe_unused]]std::string_view sha)noexcept{
 DjcRawBindings267V1 out;
#if defined(XAR_CK3_ENABLE_121003_26785313_DJC_DECLARATIONS_V1) && XAR_CK3_ENABLE_121003_26785313_DJC_DECLARATIONS_V1
 if(BindReadonlyImage(base,sha).exact_image_admitted&&VerifyCurrentDjcDeclarationsImage267V1(base)){out.image=base;out.verified=true;}
#endif
 return out;
}
bool ReadCurrentDjcTargetRaw267V1([[maybe_unused]]const ReadonlyBindings&core,[[maybe_unused]]const DjcRawBindings267V1&b,
 [[maybe_unused]]const ck3_1210::CoreSnapshotPrefix&expected,std::int32_t target_id,[[maybe_unused]]std::uint64_t deadline,DjcRawTarget267V1&out)noexcept{
 out={};out.target_character_id=target_id;out.reason="current_djc_default_off";
#if defined(XAR_CK3_ENABLE_121003_26785313_DJC_DECLARATIONS_V1) && XAR_CK3_ENABLE_121003_26785313_DJC_DECLARATIONS_V1
 bool dirty=false;const auto base=b.image;
 try{
  const auto fail=[&](const char*why){out.reason=why;return false;};
  const auto fresh=[&]{ck3_1210::CoreSnapshotPrefix p{};return deadline&&GetTickCount64()<deadline&&Core(core,p)&&Same(p,expected);};
  if(!b.verified||core.module_base!=base||!core.exact_image_admitted||!core.core.enabled||!Prefix(expected)||target_id==-1||target_id==expected.played_character_id||!VerifyCurrentDjcDeclarationsImage267V1(base)||!fresh())return fail("current_djc_exact_image_or_core_unavailable");
  if(!Character(core,expected.played_character_id,out.actor)||!Character(core,target_id,out.target))return fail("current_djc_actual_actor_or_target_not_alive");
  if(!Database(base,out.database))return fail("current_djc_database_unavailable");std::uintptr_t types=0;std::int32_t count=0,cap=0;
  if(!At(out.database,abi::k_cb_array_offset,types)||!At(out.database,abi::k_cb_array_offset+8,cap)||!At(out.database,abi::k_cb_count_offset,count)||count<0||count>10000||cap<count||(count&&!types)||!Copy(out.database+abi::k_cb_array_offset,out.database_header.data(),16))return fail("current_djc_database_header_unavailable");
  std::array<std::int32_t,3>ordinals{-1,-1,-1};
  for(std::size_t j=0;j<3;++j)out.casus_belli[j].key=kDjcCbKeys267V1[j];
  for(std::int32_t i=0;i<count;++i){std::uintptr_t type=0;if(!At(types,static_cast<std::size_t>(i)*8,type))return fail("current_djc_database_type_unavailable");if(!type)continue;std::string key;if(!Key(type,key))return fail("current_djc_definition_key_unavailable");
   for(std::size_t j=0;j<3;++j)if(key==kDjcCbKeys267V1[j]){if(ordinals[j]!=-1)return fail("current_djc_fixed_definition_duplicate");ordinals[j]=i;out.casus_belli[j].definition=type;out.casus_belli[j].definition_present=true;}}
  for(std::size_t j=0;j<3;++j){auto&cb=out.casus_belli[j];if(ordinals[j]<0)return fail("current_djc_fixed_definition_missing");std::uintptr_t rule=0;std::uint8_t disabled=0;
   if(!At(cb.definition,abi::k_cb_rule_offset,rule)||!rule||!At(rule,abi::k_cb_disabled_offset,disabled)||!At(cb.definition,abi::k_cb_flags_offset,cb.flags))return fail("current_djc_rule_unavailable");cb.enabled=disabled==0;if(!cb.enabled)continue;
   if(!fresh())return fail("current_djc_pre_evaluation_source_changed_or_expired");if(!Clear(base)){out.cleanup_known=false;return fail("current_djc_initial_scratch_cleanup_unknown");}
   dirty=true;bool available=false;cb.evaluation_returned=Evaluate(base,cb.definition,out.actor,out.target,available);if(!cb.evaluation_returned){out.cleanup_known=Clear(base);dirty=false;return fail("current_djc_evaluation_exception");}cb.native_available=available;
   std::uintptr_t data=0;std::int32_t configurations=0;if(!Scratch(base,data,configurations)){out.cleanup_known=Clear(base);dirty=false;return fail("current_djc_configuration_header_unavailable");}
   if(available){const bool combined=!configurations||(cb.flags&(1U<<20));DjcRawChoice267V1 merged{ordinals[j],-1,-1,{},{}};cb.selection_materialization_available=true;
    for(std::int32_t i=0;i<configurations;++i){const auto entry=data+static_cast<std::uintptr_t>(i)*abi::k_configuration_size;std::array<std::byte,0x98>exact{};DjcRawChoice267V1 choice{ordinals[j],i,-1,{},{}};
     if(!Copy(entry,exact.data(),exact.size())||!At(entry,0,choice.claimant_character_id)||!Array(entry+8,choice.target_title_ids)||!Array(entry+0x50,choice.extra_configuration_ids)){out.cleanup_known=Clear(base);dirty=false;return fail("current_djc_configuration_tuple_unavailable");}cb.exact_configurations.push_back(exact);cb.configurations.push_back(choice);
     if(combined)merged.target_title_ids.insert(merged.target_title_ids.end(),choice.target_title_ids.begin(),choice.target_title_ids.end());else if(!choice.target_title_ids.empty())cb.choices.push_back(std::move(choice));}
    // Actual current UI1232164..12321C5 appends only primary titles.
    // The merged row keeps its builder-initialized empty extra array.
    if(combined)cb.choices.push_back(std::move(merged));}
   out.cleanup_known=Clear(base);dirty=false;if(!out.cleanup_known)return fail("current_djc_scratch_cleanup_unknown");
  }
  std::array<std::byte,16>again{};std::uintptr_t a=0,t=0;
  if(!fresh()||!Character(core,expected.played_character_id,a)||a!=out.actor||!Character(core,target_id,t)||t!=out.target||!Copy(out.database+abi::k_cb_array_offset,again.data(),16)||again!=out.database_header||!VerifyCurrentDjcDeclarationsImage267V1(base))return fail("current_djc_final_core_or_database_changed");
  out.available=true;out.reason.clear();return true;
 }catch(...){if(dirty)out.cleanup_known=Clear(base);out.reason="current_djc_query_exception";return false;}
#else
 return false;
#endif
}
}
