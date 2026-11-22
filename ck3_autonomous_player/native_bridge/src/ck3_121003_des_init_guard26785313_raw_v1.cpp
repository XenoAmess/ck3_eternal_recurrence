#include "xar_bridge/ck3_121003_des_init_guard26785313_owner_v1.hpp"
#include "xar_bridge/ck3_121003_xqol_threshold26785313_pins_v1.hpp"
#include "xar_bridge/ck3_121003_des_init_guard26785313_pins_v1.hpp"
#include <chrono>
#include <cstring>
#include <windows.h>
namespace xar::ck3_121003::build26785313 {
#include "ck3_121003_des_init_guard26785313_native_v1.inc"
namespace {
bool Copy(std::uintptr_t p,void*out,std::size_t n)noexcept{if(!p||!n)return false;__try{std::memcpy(out,reinterpret_cast<const void*>(p),n);return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
template<class T>bool At(std::uintptr_t p,std::size_t n,T&v)noexcept{return p&&Copy(p+n,&v,sizeof(v));}
bool SameCore(const ck3_1210::CoreSnapshotPrefix&a,const ck3_1210::CoreSnapshotPrefix&b)noexcept{return a.clock.date_raw==b.clock.date_raw&&a.clock.speed==b.clock.speed&&a.clock.paused==b.clock.paused&&a.local_player_id==b.local_player_id&&a.map_ready==b.map_ready&&a.has_played_character==b.has_played_character&&a.played_character_id==b.played_character_id&&a.played_character_alive==b.played_character_alive;}
[[maybe_unused]]bool ExactImage(std::uintptr_t image)noexcept{std::array<std::byte,4096>b{};const auto check=[&](const auto&p){return !p.bytes.empty()&&p.bytes.size()<=b.size()&&Copy(image+p.rva,b.data(),p.bytes.size())&&!std::memcmp(b.data(),p.bytes.data(),p.bytes.size());};for(const auto&p:xqol_threshold_pins::kPins)if(p.rva!=0x4029740&&p.rva!=0x4123FB0&&!check(p))return false;for(const auto&p:des_init_guard_pins::kPins)if(!check(p))return false;return true;}
[[maybe_unused]]bool Fresh(const ReadonlyBindings&b,const DesInitGuardFrame267V1&f,std::uint64_t wall,std::uint64_t mono)noexcept{
 if(!f.facts_verified||!b.exact_image_admitted||!DesInitGuardBeforeDeadline267V1(wall,mono))return false;
 __try{ck3_1210::CoreSnapshotPrefix core;std::uintptr_t data=0,players=0;std::int32_t id=-1;std::uint32_t magic=0;return ck3_1210::ReadCoreSnapshot(b.core,core)&&SameCore(core,f.core)&&*b.core.game_state_slot==f.game&&*b.core.jomini_state_slot==f.jomini&&*b.core.character_storage_slot==f.storage&&At(reinterpret_cast<std::uintptr_t>(f.game),0xA0,data)&&data==reinterpret_cast<std::uintptr_t>(f.data)&&At(reinterpret_cast<std::uintptr_t>(f.jomini),0x18,players)&&players==reinterpret_cast<std::uintptr_t>(f.players)&&b.core.get_local_player(f.jomini)==f.player&&ck3_1210::ResolveCoreCharacter(b.core,core.played_character_id)==f.actor&&At(reinterpret_cast<std::uintptr_t>(f.actor),0x18,id)&&id==core.played_character_id&&At(reinterpret_cast<std::uintptr_t>(f.actor),0x1C,magic)&&magic==0x43686172&&DesInitGuardBeforeDeadline267V1(wall,mono);}__except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
}
bool VerifyDesInitGuardImage267V1([[maybe_unused]]std::uintptr_t image)noexcept{
#if defined(XAR_CK3_ENABLE_121003_26785313_DES_INIT_GUARD_V1) && XAR_CK3_ENABLE_121003_26785313_DES_INIT_GUARD_V1
 return ExactImage(image);
#else
 return false;
#endif
}
bool ReadDesInitGuardRaw267V1([[maybe_unused]]const ReadonlyBindings&b,[[maybe_unused]]const DesInitGuardFrame267V1&f,[[maybe_unused]]std::uint64_t wall,[[maybe_unused]]std::uint64_t mono,DesInitGuardRaw267V1&out,std::string&reason)noexcept{
 out={};reason="des_init_guard_default_off";
#if defined(XAR_CK3_ENABLE_121003_26785313_DES_INIT_GUARD_V1) && XAR_CK3_ENABLE_121003_26785313_DES_INIT_GUARD_V1
 if(!ExactImage(b.module_base)||!Fresh(b,f,wall,mono)){reason="des_init_guard_actual_image_or_world_unavailable";return false;}
 DesInitGuardRaw267V1 samples[2];
 for(auto&sample:samples){if(!Fresh(b,f,wall,mono)){reason="des_init_guard_actual_world_changed";return false;}DesInitGuardNative267V1 actual;
  const bool good=NativeDesInitGuard267V1(b.module_base,f.actor,static_cast<std::uint32_t>(f.core.played_character_id),wall,mono,actual);
  sample.entered=actual.entered;sample.cleanup_known=actual.cleanup_known;sample.definition=actual.definition;out=sample;
  if(!good||!actual.cleanup_known){reason=!actual.cleanup_known?"des_init_guard_owned_scope_cleanup_unknown":(!actual.native_is_player?"des_init_guard_actual_player_predicate_or_type_unavailable":"des_init_guard_actual_fixed_definition_or_predicate_unavailable");return false;}
  if(!sample.definition||!Copy(sample.definition,sample.definition_header.data(),sample.definition_header.size())){reason="des_init_guard_actual_definition_header_unavailable";return false;}
  sample.source.character_id=f.core.played_character_id;sample.source.character_alive=f.core.played_character_alive;sample.source.native_is_player=actual.native_is_player;sample.source.native_definition_found=true;sample.source.native_shown=actual.shown;sample.source.scope_bound=true;
  if(!Fresh(b,f,wall,mono)){reason="des_init_guard_actual_world_changed_after_predicate";return false;}
 }
 if(samples[0]!=samples[1]){out=samples[1];out.entered=out.entered||samples[0].entered;reason="des_init_guard_actual_definition_or_predicate_changed_between_samples";return false;}
 out=samples[1];out.source.sampled_twice=true;reason.clear();return true;
#else
 return false;
#endif
}
}
