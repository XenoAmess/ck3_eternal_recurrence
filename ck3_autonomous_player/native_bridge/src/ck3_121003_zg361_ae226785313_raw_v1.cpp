#include "xar_bridge/ck3_121003_zg361_ae226785313_owner_v1.hpp"
#include <algorithm>
#include <bit>
#include <chrono>
#include <windows.h>
#include "ck3_121003_zg361_ae2_controls26785313_private_v1.inc"
#include "ck3_121003_zg361_ae2_tooltip26785313_native_v1.inc"
namespace xar::ck3_121003::build26785313 {
bool VerifyZg361Ae2Image267V1(std::uintptr_t image)noexcept{
#if defined(XAR_CK3_ENABLE_121003_26785313_ZG361_AE2_V1) && XAR_CK3_ENABLE_121003_26785313_ZG361_AE2_V1
 return VerifyLetterImage267V1(image)&&zg361_ae2_control::VerifyZg361Ae2ManageImage267V1(image);
#else
 (void)image;return false;
#endif
}
namespace {
namespace control=zg361_ae2_control;
namespace tooltip=zg361_ae2_source;
#ifndef XAR_ZG361_AE2_SELECT_CALL_ADDRESS
#define XAR_ZG361_AE2_SELECT_CALL_ADDRESS(image,rva) ((image)+(rva))
#endif
[[maybe_unused]]Zg361Ae2Call267V1 SelectActualPay(std::uintptr_t image,std::uintptr_t option)noexcept{
 Zg361Ae2Call267V1 out;out.entered=true;out.cleanup_known=false;
 __try{using Fn=void(__fastcall*)(void*);
  reinterpret_cast<Fn>(XAR_ZG361_AE2_SELECT_CALL_ADDRESS(image,0x1B6CA10))(reinterpret_cast<void*>(option));
  out.native_returned=true;out.cleanup_known=true;
 }__except(EXCEPTION_EXECUTE_HANDLER){}
 return out;
}
[[maybe_unused]]bool RawCore(const ck3_1210::CoreSnapshotPrefix&a,const ck3_1210::CoreSnapshotPrefix&b)noexcept{
 return a.clock.date_raw==b.clock.date_raw&&a.clock.speed==b.clock.speed&&a.clock.paused==b.clock.paused&&
  a.local_player_id==b.local_player_id&&a.map_ready==b.map_ready&&a.has_played_character==b.has_played_character&&
  a.played_character_id==b.played_character_id&&a.played_character_alive==b.played_character_alive;
}
[[maybe_unused]]bool RawFresh(const ReadonlyBindings&b,const Zg361Ae2Frame267V1&f,
 const Zg361Ae2Request267V1&q,std::uint64_t mono)noexcept{
 if(!b.exact_image_admitted||!f.facts_verified||!f.game||!f.jomini||!f.character_storage||
  !RawCore(f.core,q.expected)||!tooltip::Deadline(q.deadline_unix_ms,mono))return false;
 std::uintptr_t game=0,jomini=0,storage=0;
 if(!tooltip::At(b.module_base,kGameStateSlotRva,game)||game!=f.game||
  !tooltip::At(b.module_base,kJominiStateSlotRva,jomini)||jomini!=f.jomini||
  !tooltip::At(b.module_base,kCharacterStorageSlotRva,storage)||storage!=f.character_storage)return false;
 ck3_1210::CoreSnapshotPrefix core;
 __try{return ck3_1210::ReadCoreSnapshot(b.core,core)&&RawCore(core,f.core);}
 __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
[[maybe_unused]]Zg361Ae2Controls267V1 ControlData(const control::Zg361Ae2ManageRaw267V1&r){
 const auto&s=r.source;Zg361Ae2Controls267V1 out;
 out.resident_available=r.list||r.detail||r.nav_widget;out.list_visible=s.list_visible;
 out.detail_visible=s.detail_visible;out.actor_bound=s.owner_bound;
 out.model_complete=s.complete_model_census;out.blocked_by_visible_modal=s.blocked_by_visible_modal;
 out.open_list_admissible=s.open_list_admissible&&!s.detail_visible;out.selected_control=s.selected_decision;
 for(const auto&row:s.rows){Zg361Ae2ControlRow267V1 v;v.control=row.decision;
  v.definition_key=kZg361Ae2ControlKeys267V1[static_cast<std::size_t>(row.decision)];
  // This is the captured native row/window navigation guard. It does not
  // pretend that RowSelect has an independent bool-returning Can method.
  v.native_can_open_detail=row.can_open_detail;v.open_detail_admissible=row.can_open_detail;
  if(s.selected_decision==row.decision&&s.detail_visible){v.native_can_confirm=s.native_can_confirm;
   v.confirm_admissible=s.confirm_admissible;}out.rows.push_back(std::move(v));
 }return out;
}
[[maybe_unused]]bool SameControl(const control::Zg361Ae2ManageRaw267V1&a,
 const control::Zg361Ae2ManageRaw267V1&b){
 for(std::size_t i=0;i<a.rows.size();++i)if(bool(a.rows[i])!=bool(b.rows[i]))return false;
 // Only across requests: official rebuild frees/moves row storage. Complete
 // semantic model and every stable receiver/callback/modal stay exact.
 return a.source==b.source&&a.list==b.list&&a.detail==b.detail&&a.definition==b.definition&&
  a.controller==b.controller&&a.shortcut_manager==b.shortcut_manager&&a.nav_widget==b.nav_widget&&
  a.exact_model==b.exact_model&&a.modal_source==b.modal_source&&a.nav_callbacks==b.nav_callbacks&&
  a.native_read_entered==b.native_read_entered&&a.cleanup_known==b.cleanup_known;
}
[[maybe_unused]]bool SameWorld(const Zg361Ae2Frame267V1&a,const Zg361Ae2Frame267V1&b){
 return a.facts_verified&&b.facts_verified&&RawCore(a.core,b.core)&&a.game==b.game&&
  a.jomini==b.jomini&&a.character_storage==b.character_storage;
}
}
struct Zg361Ae2Raw267V1::State {
 std::optional<control::Zg361Ae2ManageRaw267V1>controls;
 std::optional<LetterSetRaw267V1>events;
 friend bool operator==(const State&,const State&)=default;
};
#ifndef XAR_ZG361_AE2_PARENT_READ_CENSUS
#define XAR_ZG361_AE2_PARENT_READ_CENSUS ReadLetterSetRaw267V1
#endif
#ifndef XAR_ZG361_AE2_PARENT_FRESH
#define XAR_ZG361_AE2_PARENT_FRESH RawFresh
#endif
bool ReadZg361Ae2Raw267V1(const ReadonlyBindings&b,const Zg361Ae2Frame267V1&f,
 const Zg361Ae2Request267V1&q,std::uint64_t mono,Zg361Ae2Raw267V1&out,std::string&why)noexcept{
 out={};why="zg361_ae2_default_off";
#if defined(XAR_CK3_ENABLE_121003_26785313_ZG361_AE2_V1) && XAR_CK3_ENABLE_121003_26785313_ZG361_AE2_V1
 try{
  if(!XAR_ZG361_AE2_PARENT_FRESH(b,f,q,mono))return false;
  auto state=std::make_shared<Zg361Ae2Raw267V1::State>();out.source.kind=Zg361Ae2KindFor267V1(q.action);
  if(out.source.kind==Zg361Ae2Kind267V1::controls){
   if(!f.controls||!f.controls->facts_verified||!RawCore(f.controls->core,f.core))return false;
   state->controls.emplace();
   const bool good=control::ReadZg361Ae2ManageRaw267V1(b,f.core,f.controls->scene,mono,*state->controls,why);
   out.entered=state->controls->native_read_entered;out.cleanup_known=state->controls->cleanup_known;
   if(!good)return false;out.source.controls=ControlData(*state->controls);
  }else{
   if(!f.events||!f.events->facts_verified||!RawCore(f.events->core,f.core))return false;
   const auto bindings=BindLetterImage267V1(b.module_base,kExecutableSha256);
   if(!bindings.verified)return false;state->events.emplace();auto&before=*state->events;
   const bool good=XAR_ZG361_AE2_PARENT_READ_CENSUS(b,bindings,f.core,f.events->scene,mono,before,why);
   out.entered=before.native_read_entered;out.cleanup_known=before.cleanup_known;
   if(!good)return false;Zg361Ae2Events267V1 data;data.census_complete=before.source.census_complete;
   const LetterRaw267V1*chosen=nullptr;
   for(const auto&r:before.letters){const auto&s=r.source;
    if(!s.instance_id||*s.instance_id<=0||!s.recipient_character_id||!s.definition_key)return false;
    data.census.push_back({*s.instance_id,std::bit_cast<std::uint32_t>(*s.recipient_character_id),*s.definition_key});
    if(s.definition_key==kZg361Ae2Definition267V1&&s.recipient_character_id==f.core.played_character_id&&
     tooltip::FixedMaterial(f.core,r)){if(chosen){why="zg361_ae2_actual_phase_instance_ambiguous";return false;}chosen=&r;}
   }
   if(chosen){
    Zg361Ae2Snapshot267V1 ae2;const auto&s=chosen->source;
    ae2.instance_id=*s.instance_id;ae2.recipient_character_id=std::bit_cast<std::uint32_t>(*s.recipient_character_id);
    ae2.definition_key=*s.definition_key;ae2.authored_option_count=chosen->authored_option_count;
    ae2.phase_bound=true;ae2.named_root_bound=s.named_root_bound;ae2.window_visible=s.window_visible;
    ae2.window_enabled=s.window_enabled;
    for(std::size_t n=0;n<3;++n){const auto&row=s.options[n];auto&v=ae2.options[n];
     const auto slot=static_cast<std::size_t>(row.authored_option_index-15);
     v.authored_option_index=row.authored_option_index;v.option_key=kZg361Ae2OptionKeys267V1[slot];
     v.native_can_select=row.native_can_select;v.text=row.text;v.disabled_reason=row.disabled_reason;
     bool clean=true,entered=false;
     if(!tooltip::ReadFixedTooltip267V1(b.module_base,f.core,*chosen,static_cast<tooltip::Tooltip267V1>(slot),
       q.deadline_unix_ms,mono,v.tooltip,clean,entered)){
      out.entered|=entered;out.cleanup_known&=clean;why="zg361_ae2_actual_owned_tooltip_unavailable";return false;}
     out.entered|=entered;out.cleanup_known&=clean;
    }
    ae2.tooltips_complete=true;
    for(const auto&row:ae2.options)if(row.authored_option_index==15)ae2.pay_now_admissible=row.native_can_select;
    data.ae2=std::move(ae2);
   }
   // All three getters are bracketed by the unchanged complete ordinary model.
   // Instance reuse, another recipient, authored storage, row backref and Can
   // drift are rejected rather than hidden by a matching definition string.
   LetterSetRaw267V1 after;
   const bool stable=XAR_ZG361_AE2_PARENT_READ_CENSUS(b,bindings,f.core,f.events->scene,mono,after,why);
   out.entered|=after.native_read_entered;out.cleanup_known&=after.cleanup_known;
   if(!stable||before!=after){if(stable)why="zg361_ae2_complete_census_changed_after_tooltips";return false;}
   out.source.events=std::move(data);
  }
  if(!XAR_ZG361_AE2_PARENT_FRESH(b,f,q,mono)||!Zg361Ae2SourceShape267V1(out.source))return false;
  out.state_=std::move(state);why.clear();return true;
 }catch(...){out.cleanup_known=!out.entered;why="zg361_ae2_actual_source_completion_unknown";return false;}
#else
 (void)b;(void)f;(void)q;(void)mono;return false;
#endif
}
bool SameZg361Ae2Raw267V1(const Zg361Ae2Raw267V1&a,const Zg361Ae2Raw267V1&b)noexcept{
 try{return a.cleanup_known&&b.cleanup_known&&a.state_&&b.state_&&a.source==b.source&&
  a.state_->events==b.state_->events&&a.state_->controls.has_value()==b.state_->controls.has_value()&&
  (!a.state_->controls||SameControl(*a.state_->controls,*b.state_->controls));}catch(...){return false;}
}
// Implemented in the owner TU from complete captured copies only.
bool Zg361Ae2NavigationProjection267V1(const control::Zg361Ae2ManageFrame267V1&,
 const control::Zg361Ae2ManageFrame267V1&,std::uintptr_t);
bool SameZg361Ae2LeaseFrame267V1(Zg361Ae2Action267V1 action,const Zg361Ae2Frame267V1&a,
 const Zg361Ae2Raw267V1&ra,const Zg361Ae2Frame267V1&b,const Zg361Ae2Raw267V1&rb)noexcept;
struct Zg361Ae2CallAccess267V1 {
 static bool LeaseFrame(Zg361Ae2Action267V1 action,const Zg361Ae2Frame267V1&a,
  const Zg361Ae2Raw267V1&ra,const Zg361Ae2Frame267V1&b,const Zg361Ae2Raw267V1&rb){
  if(!SameWorld(a,b)||a.controls.has_value()!=b.controls.has_value()||a.events.has_value()!=b.events.has_value())return false;
  if(a.events)return a.events->scene==b.events->scene&&a.events->witness==b.events->witness;
  if(!a.controls||!b.controls)return false;
  if(action==Zg361Ae2Action267V1::open_controls_list&&ra.state_&&rb.state_&&ra.state_->controls&&rb.state_->controls){
   const auto&x=*ra.state_->controls;const auto&y=*rb.state_->controls;
   if(x.source.open_list_admissible&&y.source.open_list_admissible&&x.nav_widget&&x.nav_widget==y.nav_widget&&
    !x.nav_callbacks.empty()&&x.nav_callbacks==y.nav_callbacks)
    return Zg361Ae2NavigationProjection267V1(*a.controls,*b.controls,x.nav_widget);
  }
  return a.controls->scene==b.controls->scene&&a.controls->witness==b.controls->witness;
 }
 static Zg361Ae2Call267V1 Call(const ReadonlyBindings&b,const Zg361Ae2Frame267V1&f,
  const Zg361Ae2Request267V1&q,std::uint64_t mono,const Zg361Ae2Raw267V1&issued)noexcept{
  Zg361Ae2Call267V1 out;
  try{
   Zg361Ae2Raw267V1 actual;std::string why;
   if(!ReadZg361Ae2Raw267V1(b,f,q,mono,actual,why)||!SameZg361Ae2Raw267V1(actual,issued)){
    out.cleanup_known=actual.cleanup_known;return out;}
   if(q.action!=Zg361Ae2Action267V1::choose_pay_now){
    if(!f.controls||!actual.state_->controls)return out;
    using A=Zg361Ae2Action267V1;control::Zg361Ae2ManageAction267V1 action;
    std::optional<Zg361Ae2Control267V1>key;
    if(q.action==A::open_controls_list)action=control::Zg361Ae2ManageAction267V1::open_list;
    else if(q.action==A::open_present_detail||q.action==A::open_verify_detail){action=control::Zg361Ae2ManageAction267V1::open_detail;key=q.action==A::open_present_detail?Zg361Ae2Control267V1::present:Zg361Ae2Control267V1::verify;}
    else if(q.action==A::confirm_present||q.action==A::confirm_verify){action=control::Zg361Ae2ManageAction267V1::confirm;key=q.action==A::confirm_present?Zg361Ae2Control267V1::present:Zg361Ae2Control267V1::verify;}
    else return out;
    const auto call=control::CallZg361Ae2ManageRaw267V1(b,f.core,f.controls->scene,mono,*actual.state_->controls,action,key);
    return {call.effect_entered,call.status==control::Zg361Ae2ManageRawCallStatus267V1::returned,call.cleanup_known};
   }
   if(!actual.source.events||!actual.source.events->ae2||!actual.source.events->ae2->pay_now_admissible||
    !actual.state_->events||!RawFresh(b,f,q,mono))return out;
   const auto id=actual.source.events->ae2->instance_id;std::uintptr_t option=0;
   for(const auto&r:actual.state_->events->letters)if(r.source.instance_id==id){
    if(!tooltip::FixedMaterial(f.core,r))return out;
    for(std::size_t n=0;n<r.source.options.size();++n)if(r.source.options[n].authored_option_index==15){
     if(option||!r.source.options[n].native_can_select)return out;option=r.option_pointers[n];}
   }
   if(!option)return out;
   out=SelectActualPay(b.module_base,option);
   if(!out.native_returned)return out;
   if(!RawFresh(b,f,q,mono)||!VerifyLetterImage267V1(b.module_base))out.cleanup_known=false;
   return out;
  }catch(...){out.cleanup_known=false;return out;}
 }
};
bool SameZg361Ae2LeaseFrame267V1(Zg361Ae2Action267V1 action,const Zg361Ae2Frame267V1&a,
 const Zg361Ae2Raw267V1&ra,const Zg361Ae2Frame267V1&b,const Zg361Ae2Raw267V1&rb)noexcept{
 try{return Zg361Ae2CallAccess267V1::LeaseFrame(action,a,ra,b,rb);}catch(...){return false;}
}
Zg361Ae2Call267V1 CallZg361Ae2Raw267V1(const ReadonlyBindings&b,const Zg361Ae2Frame267V1&f,
 const Zg361Ae2Request267V1&q,std::uint64_t mono,const Zg361Ae2Raw267V1&raw)noexcept{
#if defined(XAR_CK3_ENABLE_121003_26785313_ZG361_AE2_V1) && XAR_CK3_ENABLE_121003_26785313_ZG361_AE2_V1
 return Zg361Ae2CallAccess267V1::Call(b,f,q,mono,raw);
#else
 (void)b;(void)f;(void)q;(void)mono;(void)raw;return {};
#endif
}
}
