#include "xar_bridge/ck3_121003_superman_health26785313_raw_v1.hpp"
#include "xar_bridge/ck3_121003_courtier_configuration26785313_pins_v1.hpp"
#include <algorithm>
#include <chrono>
#include <cstring>
#include <limits>
#include <unordered_set>
#include <windows.h>
namespace xar::ck3_121003::build26785313 {
#include "ck3_121003_superman_health26785313_native_v1.inc"
namespace {
[[maybe_unused]]bool HealthCopy(std::uintptr_t p,void*out,std::size_t n)noexcept{if(!p||!n||n-1>(std::numeric_limits<std::uintptr_t>::max)()-p)return false;__try{std::memcpy(out,reinterpret_cast<const void*>(p),n);return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
template<class T>bool HealthAt(std::uintptr_t p,std::size_t off,T&v)noexcept{return p&&off<=(std::numeric_limits<std::uintptr_t>::max)()-p&&HealthCopy(p+off,&v,sizeof(v));}
[[maybe_unused]]bool HealthFresh(const ReadonlyBindings&b,const ck3_1210::CoreSnapshotPrefix&e,const SupermanHealthScene267V1&s,std::uint64_t mono)noexcept{
 const auto wall=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();if(!mono||GetTickCount64()>=mono||wall<=0||!s.common.wall_deadline||static_cast<std::uint64_t>(wall)>=s.common.wall_deadline)return false;
 __try{ck3_1210::CoreSnapshotPrefix p;return ck3_1210::ReadCoreSnapshot(b.core,p)&&p.clock.date_raw==e.clock.date_raw&&p.clock.speed==e.clock.speed&&p.clock.paused==e.clock.paused&&p.local_player_id==e.local_player_id&&p.map_ready==e.map_ready&&p.has_played_character==e.has_played_character&&p.played_character_id==e.played_character_id&&p.played_character_alive==e.played_character_alive;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
[[maybe_unused]]bool HealthRootName(std::uintptr_t root,std::string&name){std::uint64_t n=0,cap=0;std::uintptr_t data=root+0x1B8;if(!HealthAt(root,0x1C8,n)||!HealthAt(root,0x1D0,cap)||n>256||n>cap||cap<15||cap>0x1000000)return false;if(cap==15){if(n>15)return false;}else if(!HealthAt(root,0x1B8,data)||!data)return false;std::array<char,257>bytes{};if(!HealthCopy(data,bytes.data(),static_cast<std::size_t>(n)+1)||bytes[n]||std::memchr(bytes.data(),0,static_cast<std::size_t>(n))||(n&&MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,bytes.data(),static_cast<int>(n),nullptr,0)==0))return false;name.assign(bytes.data(),static_cast<std::size_t>(n));return true;}
[[maybe_unused]]bool HealthSample(const ReadonlyBindings&b,const ck3_1210::CoreSnapshotPrefix&core,const SupermanHealthScene267V1&scene,std::uint64_t mono,SupermanHealthPhase267V1 phase,SupermanHealthRaw267V1&out,std::string&reason){
 const auto fail=[&](const char*why){reason=why;return false;};if(static_cast<unsigned>(phase)>1||!VerifySupermanHealthImage267V1(b.module_base)||!HealthFresh(b,core,scene,mono)||scene.roots.size()>32||scene.common.letter||scene.common.visible||scene.common.enabled)return fail("superman_health_actual_image_core_or_complete_scene_unavailable");
 HealthNames267V1 names;for(std::size_t n=0;n<40;++n){std::string key(kSupermanHealthCases267V1[n/2]);std::replace(key.begin(),key.end(),'-','_');names[n]="sxat_ref_"+std::string(n%2?"donor_":"receiver_")+key;}
 HealthNumericDiagnostic267V1 diagnostic;if(!HealthReadNumeric267V1(b,core.played_character_id,names,out.numeric,diagnostic)){out.native_read_entered=out.numeric.entered;out.cleanup_known=out.numeric.cleanup_known;reason=HealthNumericReason267V1(diagnostic);return false;}out.native_read_entered=out.numeric.entered;
 auto&s=out.source;s.phase=phase;s.fixture_state_available=true;s.reference_count=40;s.baseline_ready_raw=out.numeric.phase_vars[0];s.matrix_done_raw=out.numeric.phase_vars[1];
 std::unordered_set<std::int32_t>ids;for(std::size_t n=0;n<40;++n){SupermanHealthCharacter267V1 row;row.case_key=kSupermanHealthCases267V1[n/2];row.role=n%2?"donor":"receiver";std::memcpy(&row.character_id,out.numeric.references[n].data()+8,4);if(row.character_id==-1||!ids.insert(row.character_id).second)return fail("superman_health_original40_role_identity_not_unique");row.values=out.numeric.values[n];s.characters.push_back(std::move(row));}
 const auto bindings=BindLetterImage267V1(b.module_base,kExecutableSha256);if(!ReadLetterRaw267V1(b,bindings,core,scene.common,mono,out.manager_census,reason)){out.cleanup_known=out.manager_census.cleanup_known;return false;}
 s.named_root_count=static_cast<std::int32_t>(scene.roots.size());std::vector<std::uintptr_t>joined(scene.roots.size());std::unordered_set<std::uintptr_t>roots;
 for(const auto&root:scene.roots)if(!root.root||!roots.insert(root.root).second)return fail("superman_health_duplicate_character_event_root");
 for(const auto window:out.manager_census.window_pointers){std::uintptr_t vt=0,root=0,context=0;if(!HealthAt(window,0,vt))return fail("superman_health_resident_type_unreadable");if(vt!=b.module_base+0x4C5D448)continue;if(!HealthAt(window,0x70,root)||!HealthAt(window,0x78,context))return fail("superman_health_resident_root_context_unreadable");if(!root)continue;bool matched=false;for(std::size_t n=0;n<scene.roots.size();++n)if(scene.roots[n].root==root){if(context!=scene.common.context||joined[n])return fail("superman_health_actual_controller_root_ambiguous");joined[n]=window;matched=true;}if(!matched){std::string name;if(!HealthRootName(root,name))return fail("superman_health_unmatched_resident_name_unreadable");if(name=="character_event")return fail("superman_health_complete_character_root_census_missing_resident");}}
 std::unordered_set<std::int32_t>instances;for(std::size_t n=0;n<scene.roots.size();++n){const auto&root=scene.roots[n];if(!joined[n]||!root.visible)return fail("superman_health_actual_controller_or_inactive_material_unsupported");auto single=scene.common;single.letter=root.root;single.visible=root.visible;single.enabled=root.enabled;LetterRaw267V1 row;if(!ReadLetterRaw267V1(b,bindings,core,single,mono,row,reason)){out.cleanup_known=row.cleanup_known;return false;}
  if(row.window!=joined[n]||row.manager!=out.manager_census.manager||row.windows_header!=out.manager_census.windows_header||row.window_pointers!=out.manager_census.window_pointers||!row.source.instance_id||!instances.insert(*row.source.instance_id).second)return fail("superman_health_actual_complete_manager_or_instance_changed");
  if(row.source.definition_key==(phase==SupermanHealthPhase267V1::baseline?"sxat.2":"sxat.4")){if(out.chosen||row.source.recipient_character_id!=core.played_character_id)return fail("superman_health_known_phase_not_unique_or_wrong_recipient");out.chosen=out.events.size();s.event_found=row.source.letter_found;s.named_root_bound=row.source.named_root_bound;s.window_visible=row.source.window_visible;s.window_enabled=row.source.window_enabled;s.instance_id=row.source.instance_id;s.recipient_character_id=row.source.recipient_character_id;s.definition_key=row.source.definition_key;s.opening=row.source.opening;s.description=row.source.description;s.authored_option_count=row.authored_option_count;for(const auto&o:row.source.options)s.options.push_back({o.authored_option_index,o.text,o.disabled_reason,o.native_can_select,std::nullopt});
   if(row.authored_option_count==1&&s.options.size()==1&&s.options[0].authored_option_index==0){s.options[0].source_bound_option_key=phase==SupermanHealthPhase267V1::baseline?"sxat_health_begin":"sxat_health_done_close";s.native_choice_admissible=s.window_visible&&s.window_enabled&&s.options[0].native_can_select&&(phase==SupermanHealthPhase267V1::baseline?s.baseline_ready_raw:s.matrix_done_raw)==100000;}
  }out.events.push_back(std::move(row));
 }
 s.event_census_complete=true;return HealthFresh(b,core,scene,mono);
}
[[maybe_unused]]bool HealthSelect(std::uintptr_t image,std::uintptr_t option,bool&entered,bool&clean)noexcept{__try{if(!reinterpret_cast<bool(__fastcall*)(const void*)>(image+0x1B6CC30)(reinterpret_cast<const void*>(option)))return false;entered=true;reinterpret_cast<void(__fastcall*)(void*)>(image+0x1B6CA10)(reinterpret_cast<void*>(option));return true;}__except(EXCEPTION_EXECUTE_HANDLER){clean=false;return false;}}
}
bool VerifySupermanHealthImage267V1([[maybe_unused]]std::uintptr_t image)noexcept{
#if defined(XAR_CK3_ENABLE_121003_26785313_SUPERMAN_HEALTH_V1) && XAR_CK3_ENABLE_121003_26785313_SUPERMAN_HEALTH_V1
 if(!VerifyLetterImage267V1(image))return false;std::array<unsigned char,4096>bytes{};for(const auto&pin:courtier_configuration_pins::kPins){if(pin.bytes.empty()||pin.bytes.size()>bytes.size()||!HealthCopy(image+pin.rva,bytes.data(),pin.bytes.size())||std::memcmp(bytes.data(),pin.bytes.data(),pin.bytes.size()))return false;}return true;
#else
 return false;
#endif
}
bool ReadSupermanHealthRaw267V1([[maybe_unused]]const ReadonlyBindings&b,[[maybe_unused]]const ck3_1210::CoreSnapshotPrefix&core,[[maybe_unused]]const SupermanHealthScene267V1&scene,[[maybe_unused]]std::uint64_t mono,[[maybe_unused]]SupermanHealthPhase267V1 phase,SupermanHealthRaw267V1&out,std::string&reason)noexcept{
 out={};reason="current_superman_health_default_off";
#if defined(XAR_CK3_ENABLE_121003_26785313_SUPERMAN_HEALTH_V1) && XAR_CK3_ENABLE_121003_26785313_SUPERMAN_HEALTH_V1
 SupermanHealthRaw267V1 a,z;try{if(!HealthSample(b,core,scene,mono,phase,a,reason)){out=std::move(a);return false;}if(!HealthSample(b,core,scene,mono,phase,z,reason)){z.native_read_entered=z.native_read_entered||a.native_read_entered;out=std::move(z);return false;}if(a!=z){out=std::move(z);reason="superman_health_complete_actual_numeric_or_event_source_changed_between_samples";return false;}out=std::move(z);reason.clear();return true;}catch(...){out.native_read_entered=a.native_read_entered||z.native_read_entered;out.cleanup_known=!out.native_read_entered;reason="superman_health_actual_observation_completion_unknown";return false;}
#else
 return false;
#endif
}
LetterRawCall267V1 ChooseKnownSupermanHealthRaw267V1([[maybe_unused]]const ReadonlyBindings&b,[[maybe_unused]]const ck3_1210::CoreSnapshotPrefix&core,[[maybe_unused]]const SupermanHealthScene267V1&scene,[[maybe_unused]]std::uint64_t mono,[[maybe_unused]]const SupermanHealthRaw267V1&issued)noexcept{LetterRawCall267V1 call;
#if defined(XAR_CK3_ENABLE_121003_26785313_SUPERMAN_HEALTH_V1) && XAR_CK3_ENABLE_121003_26785313_SUPERMAN_HEALTH_V1
 SupermanHealthRaw267V1 actual;std::string reason;if(!ReadSupermanHealthRaw267V1(b,core,scene,mono,issued.source.phase,actual,reason)){call.cleanup_known=actual.cleanup_known;if(!call.cleanup_known)call.status=LetterRawCallStatus267V1::indeterminate;return call;}if(actual!=issued||!actual.source.native_choice_admissible||!actual.chosen||*actual.chosen>=actual.events.size()||actual.events[*actual.chosen].option_pointers.size()!=1||!HealthFresh(b,core,scene,mono))return call;
 if(!HealthSelect(b.module_base,actual.events[*actual.chosen].option_pointers[0],call.effect_entered,call.cleanup_known)){if(call.effect_entered||!call.cleanup_known){call.status=LetterRawCallStatus267V1::indeterminate;call.cleanup_known=false;}return call;}call.status=LetterRawCallStatus267V1::returned;
#endif
 return call;
}
}
