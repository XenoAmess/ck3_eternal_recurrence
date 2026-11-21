#include "xar_bridge/ck3_121003_xqol_conversion_prompt26785313_raw_v1.hpp"
#include <algorithm>
#include <cstring>
#include <chrono>
#include <unordered_set>
#include <windows.h>
namespace xar::ck3_121003::build26785313 {namespace {
[[maybe_unused]]bool Copy(std::uintptr_t at,void*out,std::size_t n)noexcept{if(!at||!n)return false;__try{std::memcpy(out,reinterpret_cast<const void*>(at),n);return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
[[maybe_unused]]bool NamedCharacterRoot(std::uintptr_t root){std::array<std::byte,32>a{},z{};if(!Copy(root+0x1B8,a.data(),32))return false;std::uint64_t n=0,cap=0;std::uintptr_t data=root+0x1B8;std::memcpy(&n,a.data()+16,8);std::memcpy(&cap,a.data()+24,8);constexpr std::string_view wanted="character_event";if(n!=wanted.size()||n>cap||cap<15||cap>0x1000000)return false;if(cap>15)std::memcpy(&data,a.data(),8);std::array<char,16>text{};return Copy(data,text.data(),text.size())&&!std::memcmp(text.data(),wanted.data(),wanted.size())&&!text.back()&&Copy(root+0x1B8,z.data(),32)&&a==z;}
[[maybe_unused]]bool Fresh(const ReadonlyBindings&b,const ck3_1210::CoreSnapshotPrefix&e,const XqolConversionScene267V1&s,std::uint64_t mono)noexcept{const auto wall=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();if(!mono||GetTickCount64()>=mono||wall<=0||static_cast<std::uint64_t>(wall)>=s.actual_owner.wall_deadline)return false;__try{ck3_1210::CoreSnapshotPrefix p;return ck3_1210::ReadCoreSnapshot(b.core,p)&&p.clock.date_raw==e.clock.date_raw&&p.clock.speed==e.clock.speed&&p.clock.paused==e.clock.paused&&p.local_player_id==e.local_player_id&&p.map_ready==e.map_ready&&p.has_played_character==e.has_played_character&&p.played_character_id==e.played_character_id&&p.played_character_alive==e.played_character_alive;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
[[maybe_unused]]bool NativeSelect(std::uintptr_t image,std::uintptr_t option)noexcept{__try{reinterpret_cast<void(__fastcall*)(void*)>(image+0x1B6CA10)(reinterpret_cast<void*>(option));return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
[[maybe_unused]]bool Capture(const ReadonlyBindings&b,const LetterBindings267V1&bindings,const ck3_1210::CoreSnapshotPrefix&core,const XqolConversionScene267V1&scene,std::uint64_t mono,XqolConversionPromptRaw267V1&out,std::string&reason){
 const auto fail=[&](const char*why){reason=why;return false;};if(!scene.complete_named_root_census||scene.roots.size()>32||scene.actual_owner.letter||scene.actual_owner.visible||scene.actual_owner.enabled)return fail("xqol_prompt_complete_actual_named_census_required");if(!ReadLetterRaw267V1(b,bindings,core,scene.actual_owner,mono,out.census,reason)){out.cleanup_known=out.census.cleanup_known;out.native_read_entered=out.census.native_read_entered;return false;}
 std::unordered_set<std::uintptr_t>roots;std::unordered_set<std::int32_t>ids;
 for(const auto&root:scene.roots){if(!root.visible)return fail("xqol_prompt_inactive_character_root_material_unsupported_no_skip");if(!root.widget||!roots.insert(root.widget).second||!NamedCharacterRoot(root.widget))return fail("xqol_prompt_actual_character_root_name_or_identity_mismatch");auto owner=scene.actual_owner;owner.letter=root.widget;owner.visible=root.visible;owner.enabled=root.enabled;LetterRaw267V1 row;if(!ReadLetterRaw267V1(b,bindings,core,owner,mono,row,reason)){out.cleanup_known=row.cleanup_known;out.native_read_entered=out.native_read_entered||row.native_read_entered;return false;}out.native_read_entered=out.native_read_entered||row.native_read_entered;
  if(row.windows_header!=out.census.windows_header||row.window_pointers!=out.census.window_pointers||row.manager!=out.census.manager||row.game!=out.census.game||row.jomini!=out.census.jomini)return fail("xqol_prompt_manager_or_world_changed");if(row.source.instance_id&&!ids.insert(*row.source.instance_id).second)return fail("xqol_prompt_actual_instance_ambiguous");
  if(row.source.letter_found&&row.source.definition_key==kXqolConversionDefinition267V1&&row.source.recipient_character_id==core.played_character_id){if(out.known_event)return fail("xqol_prompt_duplicate_actual_known_instance_no_selection");out.known_event=out.events.size();if(row.authored_option_count!=2)return fail("xqol_prompt_loaded_definition_shape_not_reviewed_two_options");
   // This fixed authored ordering comes from the pinned production definition;
   // the caller supplies an enum, never a displayed-row index or arbitrary key.
   for(const auto&option:row.source.options){if(option.authored_option_index==0)out.confirm_admissible=root.visible&&root.enabled&&option.native_can_select;else if(option.authored_option_index==1)out.cancel_admissible=root.visible&&root.enabled&&option.native_can_select;else return fail("xqol_prompt_actual_authored_option_not_reviewed");}
  }out.events.push_back(std::move(row));
 }return true;
}
}
bool ReadXqolConversionPromptRaw267V1([[maybe_unused]]const ReadonlyBindings&b,[[maybe_unused]]const LetterBindings267V1&bindings,[[maybe_unused]]const ck3_1210::CoreSnapshotPrefix&core,[[maybe_unused]]const XqolConversionScene267V1&scene,[[maybe_unused]]std::uint64_t mono,XqolConversionPromptRaw267V1&out,std::string&reason)noexcept{
 out={};reason="current_xqol_prompt_default_off";
#if defined(XAR_CK3_ENABLE_121003_26785313_XQOL_CONVERSION_PROMPT_V1) && XAR_CK3_ENABLE_121003_26785313_XQOL_CONVERSION_PROMPT_V1
 XqolConversionPromptRaw267V1 a,z;try{if(!Capture(b,bindings,core,scene,mono,a,reason)){out=std::move(a);return false;}if(!Capture(b,bindings,core,scene,mono,z,reason)){z.native_read_entered=z.native_read_entered||a.native_read_entered;out=std::move(z);return false;}if(a!=z){out=std::move(z);reason="xqol_prompt_complete_sources_changed_between_samples";return false;}out=std::move(z);reason.clear();return true;}catch(...){out.native_read_entered=a.native_read_entered||z.native_read_entered;out.cleanup_known=!out.native_read_entered;reason="xqol_prompt_read_exception";return false;}
#else
 return false;
#endif
}
LetterRawCall267V1 SelectXqolConversionPromptRaw267V1([[maybe_unused]]const ReadonlyBindings&b,[[maybe_unused]]const LetterBindings267V1&bindings,[[maybe_unused]]const ck3_1210::CoreSnapshotPrefix&core,[[maybe_unused]]const XqolConversionScene267V1&scene,[[maybe_unused]]std::uint64_t mono,[[maybe_unused]]const XqolConversionPromptRaw267V1&issued,[[maybe_unused]]XqolConversionChoice267V1 choice)noexcept{LetterRawCall267V1 call;
#if defined(XAR_CK3_ENABLE_121003_26785313_XQOL_CONVERSION_PROMPT_V1) && XAR_CK3_ENABLE_121003_26785313_XQOL_CONVERSION_PROMPT_V1
 XqolConversionPromptRaw267V1 fresh;std::string reason;if(!ReadXqolConversionPromptRaw267V1(b,bindings,core,scene,mono,fresh,reason)){call.cleanup_known=fresh.cleanup_known;if(!call.cleanup_known)call.status=LetterRawCallStatus267V1::indeterminate;return call;}if(fresh!=issued||!fresh.known_event||*fresh.known_event>=fresh.events.size())return call;if(choice!=XqolConversionChoice267V1::confirm&&choice!=XqolConversionChoice267V1::cancel)return call;if(choice==XqolConversionChoice267V1::confirm?!fresh.confirm_admissible:!fresh.cancel_admissible)return call;
 const auto&event=fresh.events[*fresh.known_event];const auto authored=choice==XqolConversionChoice267V1::confirm?0:1;std::uintptr_t option=0;for(std::size_t i=0;i<event.source.options.size();++i)if(event.source.options[i].authored_option_index==authored){if(option||i>=event.option_pointers.size())return call;option=event.option_pointers[i];}if(!option||!VerifyLetterImage267V1(bindings.image)||!Fresh(b,core,scene,mono))return call;call.effect_entered=true;if(!NativeSelect(bindings.image,option)){call.status=LetterRawCallStatus267V1::indeterminate;call.cleanup_known=false;return call;}call.status=LetterRawCallStatus267V1::returned;
#endif
 return call;
}
}
