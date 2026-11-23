#include "xar_bridge/ck3_121003_rmtm_event26785313_owner_v1.hpp"
#include <algorithm>
#include <chrono>
#include <cstring>
#include <limits>
#include <windows.h>
#ifndef XAR_RMTM_EVENT_CALL_ADDRESS
#define XAR_RMTM_EVENT_CALL_ADDRESS(image,rva) ((image)+(rva))
#endif
namespace xar::ck3_121003::build26785313 { namespace {
bool SameCore(const ck3_1210::CoreSnapshotPrefix&a,const ck3_1210::CoreSnapshotPrefix&z)noexcept {
 return a.clock.date_raw==z.clock.date_raw&&a.clock.speed==z.clock.speed&&a.clock.paused==z.clock.paused&&a.local_player_id==z.local_player_id&&a.map_ready==z.map_ready&&a.has_played_character==z.has_played_character&&a.played_character_id==z.played_character_id&&a.played_character_alive==z.played_character_alive;
}
bool Chaos(RmtmEventAction267V1 a)noexcept {return a==RmtmEventAction267V1::query_chaos||a==RmtmEventAction267V1::ack_chaos;}
bool Fresh(const ReadonlyBindings&b,const RmtmEventFrame267V1&f,const RmtmEventRequest267V1&q,std::uint64_t mono)noexcept {
 const auto wall=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();
 if(!f.facts_verified||!mono||GetTickCount64()>=mono||wall<=0||static_cast<std::uint64_t>(wall)>=q.deadline_unix_ms||!SameCore(f.core,q.expected)||!f.core.clock.paused)return false;
#if defined(XAR_CK3_26785313_OFFLINE_FIXTURE)
 if(b.offline_fixture)return false;
#endif
 __try {ck3_1210::CoreSnapshotPrefix actual;return ck3_1210::ReadCoreSnapshot(b.core,actual)&&SameCore(actual,f.core);}__except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
void Derive(const LydEventSource267V1&e,std::int32_t actor,bool chaos,RmtmEventSource267V1&out) {
 out={};out.event_census=e;out.sampled_twice=true;
 if(!e.census_complete||e.named_root_count!=1||e.events.size()!=1)return;
 const auto&r=e.events[0];const auto def=chaos?kRmtmChaosDefinition267V1:kRmtmSummaryDefinition267V1;
 if(r.definition_key!=def||r.recipient_character_id!=actor||r.authored_option_count!=1||!r.named_root_bound||!r.window_visible||!r.window_enabled)return;
 out.fixed_instance_id=r.instance_id;
 out.ack_admissible=r.options.size()==1&&r.options[0].authored_option_index==0&&r.options[0].native_can_select&&!r.options[0].text.empty();
}
bool Project(const FullscreenEventRaw267V1&r,LydEventSource267V1&out) {
 out={};const auto&s=r.source;
 // The fixed Chaos contract requires a complete unique material event. Never
 // turn an incomplete/multi-splash model into a one-row complete census.
 if(s.splash_item_count<0||s.splash_item_count>1)return false;
 out.census_complete=true;out.named_root_count=s.splash_item_count;
 if(!s.splash_item_count)return !s.instance_id&&!s.recipient_character_id&&!s.definition_key;
 if(!s.instance_id||!s.recipient_character_id||!s.definition_key||!s.opening||!s.description||r.authored_option_count<0)return false;
 LydEventRow267V1 row;row.instance_id=*s.instance_id;row.recipient_character_id=*s.recipient_character_id;row.definition_key=*s.definition_key;row.opening=*s.opening;row.description=*s.description;row.authored_option_count=r.authored_option_count;row.named_root_bound=s.named_root_bound;row.window_visible=s.window_visible;row.window_enabled=s.window_enabled;
 for(const auto&o:s.options){LydEventOption267V1 v;v.authored_option_index=o.authored_option_index;v.native_can_select=o.native_can_select;v.text=o.text;v.disabled_reason=o.disabled_reason;v.source_bound_option_key={};v.permitted_role={};row.options.push_back(std::move(v));}
 out.events.push_back(std::move(row));return true;
}
std::uintptr_t Option(const RmtmEventRaw267V1&r)noexcept {
 if(!r.source.ack_admissible||!r.source.fixed_instance_id||r.source.event_census.events.size()!=1)return 0;
 const auto&pub=r.source.event_census.events[0];if(pub.authored_option_count!=1||pub.options.size()!=1||pub.options[0].authored_option_index!=0)return 0;
 if(r.fullscreen_channel){if(!r.fullscreen.source.instance_id||r.fullscreen.source.instance_id!=r.source.fixed_instance_id||r.fullscreen.option_pointers.size()!=1||!r.fullscreen.runtime_event||!r.fullscreen.definition||!r.fullscreen.window)return 0;return r.fullscreen.option_pointers[0];}
 if(r.material.event_rows.size()!=1)return 0;const auto&row=r.material.event_rows[0];return row.instance_id==*r.source.fixed_instance_id&&row.controller&&row.root&&row.runtime&&row.definition&&row.options.size()==1?row.options[0]:0;
}
bool NativeCan(std::uintptr_t image,std::uintptr_t p,bool&out)noexcept {
 __try {out=reinterpret_cast<bool(__fastcall*)(const void*)>(XAR_RMTM_EVENT_CALL_ADDRESS(image,0x1B6CC30))(reinterpret_cast<const void*>(p));return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
bool NativeSelect(std::uintptr_t image,std::uintptr_t p)noexcept {
 __try {reinterpret_cast<void(__fastcall*)(void*)>(XAR_RMTM_EVENT_CALL_ADDRESS(image,0x1B6CA10))(reinterpret_cast<void*>(p));return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
bool EmptyChaosProof(const ReadonlyBindings&b,const RmtmEventFrame267V1&f,const RmtmEventRequest267V1&q,std::uint64_t mono,RmtmEventRaw267V1&out)noexcept{
 // Missing controller alone is not an empty census. Require two unchanged,
 // complete owned GUI captures, an absent resident splash controller, and an
 // independently empty actual runtime-event array. This proves no material
 // event in this source; it does not claim the global time gate is clear.
 const auto copy=[](std::uintptr_t p,void*dst,std::size_t n)noexcept{
  if(!p||!n||n-1>(std::numeric_limits<std::uintptr_t>::max)()-p)return false;
  __try{std::memcpy(dst,reinterpret_cast<const void*>(p),n);return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}
 };
 const auto sample=[&](std::array<std::uintptr_t,8>&ids,std::vector<std::byte>&proof){
  const auto at=[&]<class T>(std::uintptr_t p,std::size_t offset,T&v){return p&&offset<=(std::numeric_limits<std::uintptr_t>::max)()-p&&copy(p+offset,&v,sizeof(v));};
  const auto add=[&](std::uintptr_t p,std::size_t n){const auto size=proof.size();proof.resize(size+n);return copy(p,proof.data()+size,n);};
  if(!Fresh(b,f,q,mono)||f.fullscreen_scene.visible||f.fullscreen_witness.empty()||!f.fullscreen_bindings.verified)return false;
  std::uintptr_t gfx=0,vt=0,owner=0;std::int32_t count=-1,cap=-1;
  if(!at(b.module_base,kGameStateSlotRva,ids[0])||!at(b.module_base,kJominiStateSlotRva,ids[1])||ids[1]!=f.fullscreen_scene.jomini||!at(ids[1],0x10,gfx)||gfx!=f.fullscreen_scene.gfx||!at(gfx,0,vt)||vt!=b.module_base+0x4B24748||!at(gfx,0x28,ids[2])||!at(ids[2],0,owner)||owner!=ids[1]||!at(ids[2],0x10,ids[3])||ids[3]||!at(ids[0],0xA0,ids[4])||!ids[4])return false;
  const auto array=ids[4]+0x44BC0+0x1F18;if(array<ids[4]||!at(array,0,ids[5])||!at(array,8,cap)||cap<0||!at(array,12,count)||count!=0||!add(array,16))return false;
  for(const auto&n:f.fullscreen_witness){std::uintptr_t context=0,parent=0,children=0;std::int32_t childrenCount=0,childrenCap=0;std::uint8_t flags=0;
   if(!at(n.widget,0,vt)||vt!=n.vtable||!at(n.widget,0xD0,flags)||flags!=n.flags||!at(n.widget,0xD8,context)||context!=n.context||!at(n.widget,0xE8,parent)||parent!=n.parent||!at(n.widget,0xF0,children)||children!=n.children||!at(n.widget,0xF8,childrenCap)||childrenCap!=n.child_capacity||!at(n.widget,0xFC,childrenCount)||childrenCount!=n.child_count||!add(n.widget+0xD0,0x30))return false;
   if(n.name=="fullscreen_event"&&(flags&0x18)==0)return false;
   if(n.child_count&&!add(n.children,static_cast<std::size_t>(n.child_count)*8))return false;
  }
  return Fresh(b,f,q,mono);
 };
 try{std::array<std::uintptr_t,8>a{},z{};std::vector<std::byte>first,last;if(!sample(a,first)||!sample(z,last)||a!=z||first!=last)return false;
  out.fullscreen_channel=true;out.fullscreen={};out.fullscreen.game=a[0];out.fullscreen.jomini=a[1];out.fullscreen.manager=a[2];out.empty_chaos_proof=std::move(last);out.source={};out.source.event_census.census_complete=true;out.source.sampled_twice=true;return true;
 }catch(...){return false;}
}
}
bool VerifyRmtmEventImage267V1(std::uintptr_t image)noexcept {
#if defined(XAR_CK3_ENABLE_121003_26785313_RMTM_EVENT_V1) && XAR_CK3_ENABLE_121003_26785313_RMTM_EVENT_V1
 return image&&image==reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr))&&VerifyLydImage267V1(image)&&VerifyFullscreenEventImage267V1(image);
#else
 (void)image;return false;
#endif
}
bool ReadRmtmEventRaw267V1(const ReadonlyBindings&b,const RmtmEventFrame267V1&f,const RmtmEventRequest267V1&q,std::uint64_t mono,RmtmEventRaw267V1&out,std::string&why)noexcept {
 out={};why="rmtm_event_default_off";
#if defined(XAR_CK3_ENABLE_121003_26785313_RMTM_EVENT_V1) && XAR_CK3_ENABLE_121003_26785313_RMTM_EVENT_V1
 try {
  if(!VerifyRmtmEventImage267V1(b.module_base)||!Fresh(b,f,q,mono)){why="rmtm_event_current_image_core_deadline_unavailable";return false;}
  LydEventSource267V1 census;out.fullscreen_channel=Chaos(q.action);
  std::uintptr_t game=0,jomini=0;
  if(out.fullscreen_channel){
   FullscreenEventRaw267V1 a,z;
   if(!f.fullscreen_bindings.verified||!ReadFullscreenEventRaw267V1(b,f.fullscreen_bindings,f.core,f.fullscreen_scene,mono,a,why)){
    if(why=="fullscreen_actual_splash_controller_missing"&&a.cleanup_known&&EmptyChaosProof(b,f,q,mono,out)){census=out.source.event_census;game=out.fullscreen.game;jomini=out.fullscreen.jomini;}
    else{out.fullscreen=std::move(a);return false;}
   }else{
   if(!ReadFullscreenEventRaw267V1(b,f.fullscreen_bindings,f.core,f.fullscreen_scene,mono,z,why)){out.fullscreen=std::move(z);return false;}
   if(a!=z||!Project(z,census)){out.fullscreen=std::move(z);why="rmtm_chaos_fullscreen_complete_model_changed_or_not_unique";return false;}
   out.fullscreen=std::move(z);game=out.fullscreen.game;jomini=out.fullscreen.jomini;
   }
  }else {
   LydRequest267V1 read;read.action=LydAction267V1::query_events;read.expected=q.expected;read.deadline_unix_ms=q.deadline_unix_ms;read.request_id=q.request_id;read.request_id_size=q.request_id_size;
   if(!ReadLydRaw267V1(b,f.core,f.scene,mono,read,{},out.material,why)||!out.material.source.events||!out.material.cleanup_known)return false;
   census=*out.material.source.events;game=out.material.manager_census.game;jomini=out.material.manager_census.jomini;
  }
  Derive(census,f.core.played_character_id,out.fullscreen_channel,out.source);
  out.source.case_bound=RmtmCaseAdmitted267V1(f.core,f.connection_generation,game,jomini);if(!out.source.case_bound)out.source.ack_admissible=false;
  if(!RmtmEventSourceShape267V1(out.source)||!Fresh(b,f,q,mono)){why="rmtm_event_actual_source_or_final_Core_drift";return false;}why.clear();return true;
 }catch(...){if(out.fullscreen_channel)out.fullscreen.cleanup_known=!out.fullscreen.native_read_entered;else out.material.cleanup_known=!out.material.native_read_entered;why="rmtm_event_original_observation_exception";return false;}
#else
 (void)b;(void)f;(void)q;(void)mono;return false;
#endif
}
RmtmEventCall267V1 CallRmtmEventRaw267V1(const ReadonlyBindings&b,const RmtmEventFrame267V1&f,const RmtmEventRequest267V1&q,std::uint64_t mono,const RmtmEventRaw267V1&issued)noexcept {
 RmtmEventCall267V1 call;
#if defined(XAR_CK3_ENABLE_121003_26785313_RMTM_EVENT_V1) && XAR_CK3_ENABLE_121003_26785313_RMTM_EVENT_V1
 try {
  if((q.action!=RmtmEventAction267V1::ack_summary&&q.action!=RmtmEventAction267V1::ack_chaos)||!q.instance_id||q.instance_id!=issued.source.fixed_instance_id||Chaos(q.action)!=issued.fullscreen_channel)return call;
  RmtmEventRaw267V1 actual;std::string why;
  if(!ReadRmtmEventRaw267V1(b,f,q,mono,actual,why)){call.cleanup_known=actual.fullscreen_channel?actual.fullscreen.cleanup_known:actual.material.cleanup_known;if(!call.cleanup_known)call.status=RmtmEventCallStatus267V1::indeterminate;return call;}
  if(actual!=issued||!actual.source.ack_admissible||!Fresh(b,f,q,mono))return call;
  const auto p=Option(actual);bool can=false;if(!p)return call;
  if(!NativeCan(b.module_base,p,can)){call.cleanup_known=false;call.status=RmtmEventCallStatus267V1::indeterminate;return call;}
  if(!can||!Fresh(b,f,q,mono))return call;call.entered=true;
  if(!NativeSelect(b.module_base,p)){call.cleanup_known=false;call.status=RmtmEventCallStatus267V1::indeterminate;return call;}
  call.native_returned=true;call.status=Fresh(b,f,q,mono)?RmtmEventCallStatus267V1::returned:RmtmEventCallStatus267V1::indeterminate;return call;
 }catch(...){call.cleanup_known=false;call.status=RmtmEventCallStatus267V1::indeterminate;return call;}
#else
 (void)b;(void)f;(void)q;(void)mono;(void)issued;return call;
#endif
}
}
