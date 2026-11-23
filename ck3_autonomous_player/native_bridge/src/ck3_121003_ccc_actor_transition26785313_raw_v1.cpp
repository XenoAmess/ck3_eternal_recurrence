#include "xar_bridge/ck3_121003_ccc_actor_transition26785313_owner_v1.hpp"
#include "xar_bridge/ck3_121003_xqol_threshold26785313_pins_v1.hpp"
#include <algorithm>
#include <chrono>
#include <cstddef>
#include <cstring>
#include <windows.h>
namespace xar::ck3_121003::build26785313 {
#include "ck3_121003_ccc_role26785313_native_v1.inc"
namespace {
bool Copy(std::uintptr_t p,void*out,std::size_t n)noexcept{if(!p||!n)return false;__try{std::memcpy(out,reinterpret_cast<const void*>(p),n);return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
template<class T>bool At(std::uintptr_t p,std::size_t n,T&v)noexcept{return p&&Copy(p+n,&v,sizeof(v));}
bool SameCore(const ck3_1210::CoreSnapshotPrefix&a,const ck3_1210::CoreSnapshotPrefix&b)noexcept{return a.clock.date_raw==b.clock.date_raw&&a.clock.speed==b.clock.speed&&a.clock.paused==b.clock.paused&&a.local_player_id==b.local_player_id&&a.map_ready==b.map_ready&&a.has_played_character==b.has_played_character&&a.played_character_id==b.played_character_id&&a.played_character_alive==b.played_character_alive;}
[[maybe_unused]]bool ExactScopeImage(std::uintptr_t image)noexcept{std::array<std::byte,4096>bytes{};for(const auto&pin:xqol_threshold_pins::kPins){if(pin.rva==0x4029740||pin.rva==0x4123FB0)continue;if(pin.bytes.empty()||pin.bytes.size()>bytes.size()||!Copy(image+pin.rva,bytes.data(),pin.bytes.size())||std::memcmp(bytes.data(),pin.bytes.data(),pin.bytes.size()))return false;}return true;}
[[maybe_unused]]bool Fresh(const ReadonlyBindings&b,const CccRoleFrame267V1&f,std::uint64_t wall,std::uint64_t mono)noexcept{
 if(!f.facts_verified||!b.exact_image_admitted||!CccRoleBeforeDeadline267V1(wall,mono))return false;
 __try{const auto&w=f.world;ck3_1210::CoreSnapshotPrefix core;std::uintptr_t data=0,players=0;std::int32_t id=-1;std::uint32_t magic=0;
  return ck3_1210::ReadCoreSnapshot(b.core,core)&&SameCore(core,w.core)&&*b.core.game_state_slot==w.game&&*b.core.jomini_state_slot==w.jomini&&*b.core.character_storage_slot==w.storage&&At(reinterpret_cast<std::uintptr_t>(w.game),0xA0,data)&&data==reinterpret_cast<std::uintptr_t>(w.data)&&At(reinterpret_cast<std::uintptr_t>(w.jomini),0x18,players)&&players==reinterpret_cast<std::uintptr_t>(w.players)&&b.core.get_local_player(w.jomini)==w.player&&ck3_1210::ResolveCoreCharacter(b.core,core.played_character_id)==w.actor&&At(reinterpret_cast<std::uintptr_t>(w.actor),0x18,id)&&id==core.played_character_id&&At(reinterpret_cast<std::uintptr_t>(w.actor),0x1C,magic)&&magic==0x43686172&&CccRoleBeforeDeadline267V1(wall,mono);
 }__except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
}
bool VerifyCccRoleImage267V1([[maybe_unused]]std::uintptr_t image)noexcept{
#if defined(XAR_CK3_ENABLE_121003_26785313_CCC_TRANSITION_V1) && XAR_CK3_ENABLE_121003_26785313_CCC_TRANSITION_V1
 return ExactScopeImage(image);
#else
 return false;
#endif
}
bool ReadCccRoleRaw267V1([[maybe_unused]]const ReadonlyBindings&b,[[maybe_unused]]const CccRoleFrame267V1&f,[[maybe_unused]]bool official,[[maybe_unused]]std::uint64_t wall,[[maybe_unused]]std::uint64_t mono,CccRoleRaw267V1&out,std::string&reason)noexcept{
 out={};reason="ccc_fixed_role_default_off";
#if defined(XAR_CK3_ENABLE_121003_26785313_CCC_TRANSITION_V1) && XAR_CK3_ENABLE_121003_26785313_CCC_TRANSITION_V1
 if(!ExactScopeImage(b.module_base)||!Fresh(b,f,wall,mono)){reason="ccc_actual_scope_image_or_world_unavailable";return false;}
 CccRoleRaw267V1 samples[2];
 for(auto&sample:samples){if(!Fresh(b,f,wall,mono)){reason="ccc_actual_role_world_changed";return false;}CccRoleNative267V1 actual;
  const bool good=NativeCccRole267V1(b.module_base,f.world.actor,static_cast<std::uint32_t>(f.world.core.played_character_id),official,wall,mono,actual);
  sample.entered=actual.entered;sample.cleanup_known=actual.cleanup_known;sample.definition=actual.definition;sample.shown=actual.shown;out=sample;
  if(!good||!actual.cleanup_known){reason=actual.cleanup_known?"ccc_actual_fixed_role_predicate_unavailable":"ccc_actual_owned_scope_cleanup_unknown";return false;}
  if(sample.definition&&!Copy(sample.definition,sample.definition_header.data(),sample.definition_header.size())){reason="ccc_actual_role_definition_header_unavailable";return false;}
  if(!Fresh(b,f,wall,mono)){reason="ccc_actual_role_world_changed_after_predicate";return false;}
 }
 if(samples[0]!=samples[1]){out=samples[1];out.entered=out.entered||samples[0].entered;reason="ccc_actual_role_definition_or_predicate_changed_between_samples";return false;}
 out=samples[1];reason.clear();return true;
#else
 return false;
#endif
}
}
