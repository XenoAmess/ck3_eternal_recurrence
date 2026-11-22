#include "xar_bridge/ck3_121003_xqol_threshold26785313_raw_v1.hpp"
#include "xar_bridge/ck3_121003_xqol_threshold26785313_pins_v1.hpp"
#include <algorithm>
#include <bit>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <windows.h>
namespace xar::ck3_121003::build26785313 {
#include "ck3_121003_xqol_threshold26785313_native_v1.inc"
namespace {
[[maybe_unused]]bool Copy(std::uintptr_t p,void*out,std::size_t n)noexcept{if(!p||!n)return false;__try{std::memcpy(out,reinterpret_cast<const void*>(p),n);return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
template<class T>bool At(std::uintptr_t p,std::size_t off,T&v)noexcept{return p&&Copy(p+off,&v,sizeof(v));}
[[maybe_unused]]bool Fresh(const ReadonlyBindings&b,const ck3_1210::CoreSnapshotPrefix&expected,const XqolThresholdScene267V1&scene,std::uint64_t mono)noexcept{
 const auto wall=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();if(!mono||GetTickCount64()>=mono||wall<=0||static_cast<std::uint64_t>(wall)>=scene.prompt_scene.actual_owner.wall_deadline)return false;
 __try{ck3_1210::CoreSnapshotPrefix actual;return ck3_1210::ReadCoreSnapshot(b.core,actual)&&actual.clock.date_raw==expected.clock.date_raw&&actual.clock.speed==expected.clock.speed&&actual.clock.paused==expected.clock.paused&&actual.local_player_id==expected.local_player_id&&actual.map_ready==expected.map_ready&&actual.has_played_character==expected.has_played_character&&actual.played_character_id==expected.played_character_id&&actual.played_character_alive==expected.played_character_alive;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
[[maybe_unused]]bool Descendant(const std::vector<GuiWindowNodeV1>&nodes,std::uintptr_t child,std::uintptr_t parent){for(std::size_t n=0;n<32&&child;++n){if(child==parent)return true;const auto it=std::find_if(nodes.begin(),nodes.end(),[&](const auto&v){return v.widget==child;});if(it==nodes.end())return false;child=it->parent;}return false;}
[[maybe_unused]]bool Capture(const ReadonlyBindings&b,const ck3_1210::CoreSnapshotPrefix&core,const XqolThresholdScene267V1&scene,std::uint64_t mono,std::uint32_t target,XqolThresholdRaw267V1&out,std::string&reason){
 const auto fail=[&](const char*why){reason=why;return false;};if(target>100||!VerifyXqolThresholdImage267V1(b.module_base)||!Fresh(b,core,scene,mono))return fail("xqol_threshold_actual_image_core_or_original_deadline_unavailable");
 auto bindings=BindLetterImage267V1(b.module_base,kExecutableSha256);if(!bindings.verified||!ReadXqolConversionPromptRaw267V1(b,bindings,core,scene.prompt_scene,mono,out.prompt,reason)){out.native_read_entered=out.prompt.native_read_entered;out.cleanup_known=out.prompt.cleanup_known;return false;}
 out.native_read_entered=out.prompt.native_read_entered;out.cleanup_known=out.prompt.cleanup_known;if(out.prompt!=scene.sampled_prompt)return fail("xqol_threshold_known_prompt_changed_after_actual_widget_capture");
 auto&source=out.source;source.target_threshold=target;source.prompt.resident_count=out.prompt.census.source.resident_count;source.prompt.named_root_count=static_cast<std::int32_t>(scene.prompt_scene.roots.size());source.prompt.census_complete=true;source.prompt.confirm_admissible=out.prompt.confirm_admissible;source.prompt.cancel_admissible=out.prompt.cancel_admissible;
 if(!out.prompt.known_event){if(!scene.widgets.empty())return fail("xqol_threshold_no_known_prompt_but_widget_source_present");return true;}
 const auto index=*out.prompt.known_event;if(index>=out.prompt.events.size()||index>=scene.prompt_scene.roots.size())return fail("xqol_threshold_actual_known_root_mapping_unavailable");const auto root=scene.prompt_scene.roots[index].widget;const auto&event=out.prompt.events[index];source.prompt.event=event.source;source.prompt.authored_option_count=event.authored_option_count;for(auto&option:source.prompt.event->options)option.source_bound_option_key=option.authored_option_index==0?kXqolConversionConfirm267V1:kXqolConversionCancel267V1;
 std::uintptr_t top=0;if(!At(event.window,0x70,top)||top!=root)return fail("xqol_threshold_actual_event_root_mismatch");
 for(const auto&node:scene.widgets){if(!Descendant(scene.widgets,node.widget,root))return fail("xqol_threshold_widget_outside_actual_known_event");if(node.name=="xqol_conversion_threshold_slider"){if(out.slider)return fail("xqol_threshold_actual_slider_ambiguous");out.slider=node.widget;}else if(node.name=="xqol_conversion_threshold_scrollbar"){if(out.scrollbar)return fail("xqol_threshold_actual_scrollbar_ambiguous");out.scrollbar=node.widget;}else if(node.name=="xqol_conversion_threshold_handle"){if(out.handle)return fail("xqol_threshold_actual_handle_ambiguous");out.handle=node.widget;}}
 if(!out.slider||!out.scrollbar||!out.handle||!Descendant(scene.widgets,out.scrollbar,out.slider)||!Descendant(scene.widgets,out.handle,out.scrollbar))return fail("xqol_threshold_actual_named_slider_scrollbar_handle_missing");std::uintptr_t vt=0;if(!At(out.scrollbar,0,vt)||vt!=b.module_base+0x50CCCA8)return fail("xqol_threshold_actual_scrollbar_type_mismatch");
 std::uint32_t value=0,minimum=0,maximum=0,step=0;if(!At(out.scrollbar,0x418,value)||!At(out.scrollbar,0x41C,minimum)||!At(out.scrollbar,0x420,maximum)||!At(out.scrollbar,0x424,step)||minimum||maximum!=0x42C80000U||step!=0x3F800000U)return fail("xqol_threshold_actual_range_or_step_unavailable");const auto number=std::bit_cast<float>(value);if(!std::isfinite(number)||number<0||number>100)return fail("xqol_threshold_actual_widget_value_not_finite_in_range");source.scrollbar_found=source.handle_found=true;source.value_bits_u32=value;source.minimum_bits_u32=minimum;source.maximum_bits_u32=maximum;source.step_bits_u32=step;
 void*actor=nullptr;__try{actor=ck3_1210::ResolveCoreCharacter(b.core,core.played_character_id);}__except(EXCEPTION_EXECUTE_HANDLER){return fail("xqol_threshold_actual_player_resolution_unavailable");}if(!actor)return fail("xqol_threshold_actual_player_resolution_unavailable");out.actor=reinterpret_cast<std::uintptr_t>(actor);
 ThresholdNative267V1 native;const bool good=NativeFixedThreshold267V1(b.module_base,actor,static_cast<std::uint32_t>(core.played_character_id),target,scene.prompt_scene.actual_owner.wall_deadline,mono,0,ThresholdNativePhase267V1::read_predicates,native);out.native_read_entered=out.native_read_entered||native.entered;out.cleanup_known=native.cleanup_known;if(!good){if(!native.cleanup_known)return fail("xqol_threshold_native_predicate_or_scope_cleanup_unknown");if(!native.definition){source.native_fixed_route_found=false;return true;}return fail("xqol_threshold_actual_typed_predicate_source_unavailable");}
 out.definition=native.definition;if(!Copy(out.definition,out.definition_header.data(),out.definition_header.size()))return fail("xqol_threshold_actual_fixed_route_header_unavailable");source.native_fixed_route_found=true;source.native_shown=native.shown;source.native_valid=native.valid;bool active=source.prompt.event->window_visible&&source.prompt.event->window_enabled;for(const auto&node:scene.widgets)if(node.widget==out.slider||node.widget==out.scrollbar||node.widget==out.handle)active=active&&node.visible&&node.enabled;source.set_admissible=active&&native.shown&&native.valid;return Fresh(b,core,scene,mono);
}
}
bool VerifyXqolThresholdImage267V1([[maybe_unused]]std::uintptr_t image)noexcept{
#if defined(XAR_CK3_ENABLE_121003_26785313_XQOL_THRESHOLD_V1) && XAR_CK3_ENABLE_121003_26785313_XQOL_THRESHOLD_V1
 if(!VerifyLetterImage267V1(image))return false;std::array<unsigned char,4096>bytes{};for(const auto&pin:xqol_threshold_pins::kPins)if(pin.bytes.empty()||pin.bytes.size()>bytes.size()||!Copy(image+pin.rva,bytes.data(),pin.bytes.size())||std::memcmp(bytes.data(),pin.bytes.data(),pin.bytes.size()))return false;std::uintptr_t col=0;return At(image,0x50CCCA8-8,col)&&col==image+0x58F9790;
#else
 return false;
#endif
}
bool ReadXqolThresholdRaw267V1([[maybe_unused]]const ReadonlyBindings&b,[[maybe_unused]]const ck3_1210::CoreSnapshotPrefix&core,[[maybe_unused]]const XqolThresholdScene267V1&scene,[[maybe_unused]]std::uint64_t mono,[[maybe_unused]]std::uint32_t target,XqolThresholdRaw267V1&out,std::string&reason)noexcept{out={};reason="current_xqol_threshold_default_off";
#if defined(XAR_CK3_ENABLE_121003_26785313_XQOL_THRESHOLD_V1) && XAR_CK3_ENABLE_121003_26785313_XQOL_THRESHOLD_V1
 XqolThresholdRaw267V1 a,z;try{if(!Capture(b,core,scene,mono,target,a,reason)){out=std::move(a);return false;}if(!Capture(b,core,scene,mono,target,z,reason)){z.native_read_entered=z.native_read_entered||a.native_read_entered;out=std::move(z);return false;}if(a!=z){out=std::move(z);reason="xqol_threshold_actual_prompt_widgets_or_native_predicates_changed_between_samples";return false;}out=std::move(z);reason.clear();return true;}catch(...){out.native_read_entered=a.native_read_entered||z.native_read_entered;out.cleanup_known=!out.native_read_entered;reason="xqol_threshold_native_source_capture_exception";return false;}
#else
 return false;
#endif
}
LetterRawCall267V1 SetXqolThresholdRaw267V1([[maybe_unused]]const ReadonlyBindings&b,[[maybe_unused]]const ck3_1210::CoreSnapshotPrefix&core,[[maybe_unused]]const XqolThresholdScene267V1&scene,[[maybe_unused]]std::uint64_t mono,[[maybe_unused]]const XqolThresholdRaw267V1&issued)noexcept{LetterRawCall267V1 out;
#if defined(XAR_CK3_ENABLE_121003_26785313_XQOL_THRESHOLD_V1) && XAR_CK3_ENABLE_121003_26785313_XQOL_THRESHOLD_V1
 XqolThresholdRaw267V1 fresh;std::string reason;if(!ReadXqolThresholdRaw267V1(b,core,scene,mono,issued.source.target_threshold,fresh,reason)){out.cleanup_known=fresh.cleanup_known;if(!out.cleanup_known)out.status=LetterRawCallStatus267V1::indeterminate;return out;}if(fresh!=issued||!fresh.source.set_admissible||!fresh.actor||!Fresh(b,core,scene,mono))return out;
 ThresholdNative267V1 native;const bool good=NativeFixedThreshold267V1(b.module_base,reinterpret_cast<void*>(fresh.actor),static_cast<std::uint32_t>(core.played_character_id),fresh.source.target_threshold,scene.prompt_scene.actual_owner.wall_deadline,mono,fresh.definition,ThresholdNativePhase267V1::execute_fixed_route,native);out.effect_entered=native.effect_entered;out.cleanup_known=native.cleanup_known;if(!native.cleanup_known||(native.effect_entered&&!native.native_returned))out.status=LetterRawCallStatus267V1::indeterminate;else if(good&&native.native_returned)out.status=LetterRawCallStatus267V1::returned;
#endif
 return out;}
}
