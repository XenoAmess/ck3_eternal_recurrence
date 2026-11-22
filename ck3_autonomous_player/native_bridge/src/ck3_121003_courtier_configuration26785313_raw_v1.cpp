#include "xar_bridge/ck3_121003_courtier_configuration26785313_raw_v1.hpp"
#include "xar_bridge/ck3_121003_xqol_threshold26785313_pins_v1.hpp"
#include "xar_bridge/ck3_121003_courtier_configuration26785313_pins_v1.hpp"
#include <algorithm>
#include <chrono>
#include <cstring>
#include <windows.h>
namespace xar::ck3_121003::build26785313 {
#include "ck3_121003_courtier_configuration26785313_native_v1.inc"
namespace {
[[maybe_unused]]bool Copy(std::uintptr_t p,void*out,std::size_t n)noexcept{if(!p||!n)return false;__try{std::memcpy(out,reinterpret_cast<const void*>(p),n);return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
template<class T>bool At(std::uintptr_t p,std::size_t off,T&v)noexcept{return p&&Copy(p+off,&v,sizeof(v));}
[[maybe_unused]]bool Fresh(const ReadonlyBindings&b,const ck3_1210::CoreSnapshotPrefix&expected,const CourtierConfigurationScene267V1&scene,std::uint64_t mono)noexcept{
 const auto wall=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();if(!mono||GetTickCount64()>=mono||wall<=0||!scene.wall_deadline||static_cast<std::uint64_t>(wall)>=scene.wall_deadline)return false;
 __try{ck3_1210::CoreSnapshotPrefix actual;std::uintptr_t jomini=0,application=0,vt=0,first=0,context=0,global=0;
  return ck3_1210::ReadCoreSnapshot(b.core,actual)&&actual.clock.date_raw==expected.clock.date_raw&&actual.clock.speed==expected.clock.speed&&actual.clock.paused==expected.clock.paused&&actual.local_player_id==expected.local_player_id&&actual.map_ready==expected.map_ready&&actual.has_played_character==expected.has_played_character&&actual.played_character_id==expected.played_character_id&&actual.played_character_alive==expected.played_character_alive&&
   At(reinterpret_cast<std::uintptr_t>(b.core.jomini_state_slot),0,jomini)&&jomini==scene.jomini&&At(jomini,0x18,application)&&application==scene.application&&At(application,0,vt)&&vt==b.module_base+0x4AFA650&&At(application,0x1B8,first)&&At(first,0x58,context)&&context==scene.context&&At(context,0xD0,global)&&global==scene.global;
 }__except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
[[maybe_unused]]bool NodeStillCurrent(const GuiWindowNodeV1&n)noexcept{
 std::uint8_t flags=0;std::uintptr_t vt=0,context=0,parent=0,children=0,data=0;std::int32_t cap=0,count=0;std::uint64_t length=0,capacity=0;std::array<char,kGuiWindowMaxNameBytesV1+1>name{};
 if(!n.widget||n.name.size()>kGuiWindowMaxNameBytesV1||!At(n.widget,0,vt)||vt!=n.vtable||!At(n.widget,0xD0,flags)||flags!=n.flags||!At(n.widget,0xD8,context)||context!=n.context||!At(n.widget,0xE8,parent)||parent!=n.parent||!At(n.widget,0xF0,children)||children!=n.children||!At(n.widget,0xF8,cap)||cap!=n.child_capacity||!At(n.widget,0xFC,count)||count!=n.child_count||!At(n.widget,0x1C8,length)||length!=n.name_size||!At(n.widget,0x1D0,capacity)||capacity!=n.name_capacity)return false;
 if(capacity==15)data=n.widget+0x1B8;else if(capacity<=15||!At(n.widget,0x1B8,data))return false;
 return data==n.name_data&&length==n.name.size()&&Copy(data,name.data(),static_cast<std::size_t>(length)+1)&&name[length]==0&&std::string_view(name.data(),static_cast<std::size_t>(length))==n.name;
}
[[maybe_unused]]void* ResolveCourtierActor267V1(const ReadonlyBindings&b,std::int32_t id)noexcept{__try{return ck3_1210::ResolveCoreCharacter(b.core,id);}__except(EXCEPTION_EXECUTE_HANDLER){return nullptr;}}
[[maybe_unused]]bool Capture(const ReadonlyBindings&b,const ck3_1210::CoreSnapshotPrefix&core,const CourtierConfigurationScene267V1&scene,std::uint64_t mono,CourtierProduct267V1 product,CourtierSetting267V1 setting,CourtierConfigurationRaw267V1&out,std::string&reason){
 const auto fail=[&](const char*why){reason=why;return false;};
 if(static_cast<unsigned>(product)>1||static_cast<unsigned>(setting)>3||!VerifyCourtierConfigurationImage267V1(b.module_base)||!Fresh(b,core,scene,mono)||(scene.chain.size()!=2&&scene.chain.size()!=5))return fail("courtier_configuration_actual_image_core_or_fixed_chain_unavailable");
 const auto prefix=product==CourtierProduct267V1::main?"xar":"ervc";
 for(std::size_t n=0;n<scene.chain.size();++n){const auto&node=scene.chain[n];if(!NodeStillCurrent(node)||node.context!=scene.context||(n==0?(node.widget!=scene.global||node.parent!=0):node.parent!=scene.chain[n-1].widget))return fail("courtier_configuration_actual_chain_parent_context_or_source_changed");
  if(n==1&&node.name!="confirmation")return fail("courtier_configuration_actual_confirmation_layer_missing");
  if(n>=2){const auto expected=std::string(prefix)+(n==2?"_courtier_creator_window":n==3?"_courtier_creator_modal":"_courtier_creator_panel");if(node.name!=expected)return fail("courtier_configuration_actual_product_literal_mismatch");}
 }
 auto&s=out.source;s.product=product;s.setting=setting;s.confirmation_layer_found=true;
 if(scene.chain.size()==2)return Fresh(b,core,scene,mono);
 s.creator_window_found=s.modal_found=s.panel_found=true;s.window_visible=true;s.window_enabled=true;for(const auto&node:scene.chain){s.window_visible=s.window_visible&&node.visible;s.window_enabled=s.window_enabled&&node.enabled;}
 void*actor=ResolveCourtierActor267V1(b,core.played_character_id);if(!actor)return fail("courtier_configuration_actual_player_resolution_unavailable");out.actor=reinterpret_cast<std::uintptr_t>(actor);
 CourtierNative267V1 native;const bool good=NativeFixedCourtier267V1(b.module_base,actor,static_cast<std::uint32_t>(core.played_character_id),product,setting,scene.wall_deadline,mono,0,CourtierNativePhase267V1::read_predicates,native);out.native_read_entered=native.entered;out.cleanup_known=native.cleanup_known;s.configuration=native.configuration;s.numeric_complete=std::all_of(native.configuration.raw.begin(),native.configuration.raw.end(),[](const auto&v){return v.has_value();});out.cost_definition=native.cost_definition;
 if(!good){if(!native.cleanup_known)return fail("courtier_configuration_native_predicate_or_scope_cleanup_unknown");if(!native.definition){s.native_definition_found=false;return Fresh(b,core,scene,mono);}return fail("courtier_configuration_actual_typed_predicate_source_unavailable");}
 s.configuration=native.configuration;s.numeric_complete=std::all_of(native.configuration.raw.begin(),native.configuration.raw.end(),[](const auto&v){return v.has_value();});out.cost_definition=native.cost_definition;out.definition=native.definition;if(!Copy(out.definition,out.definition_header.data(),out.definition_header.size()))return fail("courtier_configuration_actual_definition_header_unavailable");s.native_definition_found=true;s.native_shown=native.shown;s.native_valid=native.valid;s.execute_admissible=s.window_visible&&s.window_enabled&&native.shown&&native.valid&&s.numeric_complete;return Fresh(b,core,scene,mono);
}
}
bool VerifyCourtierConfigurationImage267V1([[maybe_unused]]std::uintptr_t image)noexcept{
#if defined(XAR_CK3_ENABLE_121003_26785313_COURTIER_CONFIGURATION_V1) && XAR_CK3_ENABLE_121003_26785313_COURTIER_CONFIGURATION_V1
 std::array<unsigned char,4096>bytes{};for(const auto&pin:xqol_threshold_pins::kPins){if(pin.rva==0x4029740||pin.rva==0x4123FB0)continue;if(pin.bytes.empty()||pin.bytes.size()>bytes.size()||!Copy(image+pin.rva,bytes.data(),pin.bytes.size())||std::memcmp(bytes.data(),pin.bytes.data(),pin.bytes.size()))return false;}for(const auto&pin:courtier_configuration_pins::kPins){if(pin.bytes.empty()||pin.bytes.size()>bytes.size()||!Copy(image+pin.rva,bytes.data(),pin.bytes.size())||std::memcmp(bytes.data(),pin.bytes.data(),pin.bytes.size()))return false;}return true;
#else
 return false;
#endif
}
bool ReadCourtierConfigurationRaw267V1([[maybe_unused]]const ReadonlyBindings&b,[[maybe_unused]]const ck3_1210::CoreSnapshotPrefix&core,[[maybe_unused]]const CourtierConfigurationScene267V1&scene,[[maybe_unused]]std::uint64_t mono,[[maybe_unused]]CourtierProduct267V1 product,[[maybe_unused]]CourtierSetting267V1 setting,CourtierConfigurationRaw267V1&out,std::string&reason)noexcept{out={};reason="current_courtier_configuration_default_off";
#if defined(XAR_CK3_ENABLE_121003_26785313_COURTIER_CONFIGURATION_V1) && XAR_CK3_ENABLE_121003_26785313_COURTIER_CONFIGURATION_V1
 CourtierConfigurationRaw267V1 a,z;try{if(!Capture(b,core,scene,mono,product,setting,a,reason)){out=std::move(a);return false;}if(!Capture(b,core,scene,mono,product,setting,z,reason)){z.native_read_entered=z.native_read_entered||a.native_read_entered;out=std::move(z);return false;}if(a!=z){out=std::move(z);reason="courtier_configuration_actual_source_changed_between_samples";return false;}out=std::move(z);reason.clear();return true;}catch(...){out.native_read_entered=a.native_read_entered||z.native_read_entered;out.cleanup_known=!out.native_read_entered;reason="courtier_configuration_native_source_capture_exception";return false;}
#else
 return false;
#endif
}
LetterRawCall267V1 ExecuteCourtierControlRaw267V1([[maybe_unused]]const ReadonlyBindings&b,[[maybe_unused]]const ck3_1210::CoreSnapshotPrefix&core,[[maybe_unused]]const CourtierConfigurationScene267V1&scene,[[maybe_unused]]std::uint64_t mono,[[maybe_unused]]const CourtierConfigurationRaw267V1&issued)noexcept{LetterRawCall267V1 out;
#if defined(XAR_CK3_ENABLE_121003_26785313_COURTIER_CONFIGURATION_V1) && XAR_CK3_ENABLE_121003_26785313_COURTIER_CONFIGURATION_V1
 CourtierConfigurationRaw267V1 fresh;std::string reason;if(!ReadCourtierConfigurationRaw267V1(b,core,scene,mono,issued.source.product,issued.source.setting,fresh,reason)){out.cleanup_known=fresh.cleanup_known;if(!out.cleanup_known)out.status=LetterRawCallStatus267V1::indeterminate;return out;}
 if(fresh!=issued||!fresh.source.execute_admissible||!fresh.actor||!Fresh(b,core,scene,mono))return out;
 CourtierNative267V1 native;const bool good=NativeFixedCourtier267V1(b.module_base,reinterpret_cast<void*>(fresh.actor),static_cast<std::uint32_t>(core.played_character_id),fresh.source.product,fresh.source.setting,scene.wall_deadline,mono,fresh.definition,CourtierNativePhase267V1::execute_fixed_route,native);out.effect_entered=native.effect_entered;out.cleanup_known=native.cleanup_known;if(!native.cleanup_known||(native.effect_entered&&!native.native_returned))out.status=LetterRawCallStatus267V1::indeterminate;else if(good&&native.native_returned)out.status=LetterRawCallStatus267V1::returned;
#endif
 return out;
}
}
