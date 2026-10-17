#include "xar_bridge/holy_site_relic_navigation12004.hpp"
#include "xar_bridge/ck3_12004_holy_site_relic_actions.hpp"
#include "xar_bridge/ck3_12004_holy_site_ui.hpp"
#include "xar_bridge/ck3_12004.hpp"
#ifndef XAR_ENABLE_HOLY_SITE_RELIC_BUTTON_ACTION12004
#define XAR_ENABLE_HOLY_SITE_RELIC_BUTTON_ACTION12004 0
#endif
#if XAR_ENABLE_HOLY_SITE_RELIC_BUTTON_ACTION12004
#include "xar_bridge/holy_site_relic_action_preview_adapter12004.hpp"
#endif
#include <windows.h>
#include <charconv>
#include <limits>
#include <utility>

namespace xar::ck3_11906 {
namespace {
namespace relic=ck3_12004::religion::relic_actions;
struct PresentationContext {const ZhongguoScoreboardNativeEnvironmentV1*env=nullptr;const void*gui_context=nullptr;};
bool Signature(const NamedGuiStandardClickBinding12004V1&b,relic::Operation op) {
 if(!b.button_base_slot13||b.callbacks.size()!=1)return false;
 const auto&c=b.callbacks[0];const auto&d=c.expression_3a9f960;
 const std::uint64_t callback=op==relic::Operation::enshrine?0x17D8A40:0x17D8A60;
 return c.index==0&&c.callback_slot2_rva==0x3AA30E0&&c.indirect_target_3aa30e0&&
  c.native_target_8_rva==0x3A9F960&&c.expression_descriptor_3a9f960&&
  (d.final_kind_34_raw==3||d.final_kind_34_raw==4)&&d.final_target_38_rva==callback;
}
bool Same(const NamedGuiStandardClickBinding12004V1&a,const NamedGuiStandardClickBinding12004V1&b) {
 if(a.button_base_slot13!=b.button_base_slot13||a.primary_group!=b.primary_group||a.callbacks.size()!=b.callbacks.size())return false;
 for(std::size_t i=0;i<a.callbacks.size();++i){const auto&x=a.callbacks[i];const auto&y=b.callbacks[i];
  if(x.index!=y.index||x.callback_vtable_rva!=y.callback_vtable_rva||x.callback_slot2_rva!=y.callback_slot2_rva||
     x.indirect_target_3aa30e0!=y.indirect_target_3aa30e0||x.native_target_8_rva!=y.native_target_8_rva||
     x.receiver_f0_present!=y.receiver_f0_present||x.expression_descriptor_3a9f960!=y.expression_descriptor_3a9f960||
     x.expression_3a9f960!=y.expression_3a9f960)return false;
 }return true;
}
bool Tree(const ZhongguoScoreboardNativeEnvironmentV1&e,const void*expected,NamedGuiTreeInspectionV1&t) {
 ZhongguoScoreboardAccessV1 access{};void*root=nullptr,*widget=nullptr;
 return ResolveNamedGuiWidgetV1(e,access,"holy_site_window","holy_site_window",root,widget)&&root==expected&&widget==root&&
  InspectNamedGuiSubtreeV1(access,e.module_base,root,"holy_site_window",t,true,false)&&
  t.root_available&&!t.truncated&&t.widget_count==t.widgets.size()&&t.widget_count&&
  t.callback_thunk_3aa30e0_pin_verified&&t.expression_layout_3a9f960_pin_verified;
}
const NamedGuiWidgetInspectionV1*Unique(const NamedGuiTreeInspectionV1&t,relic::Operation op) {
 const NamedGuiWidgetInspectionV1*found=nullptr;
 for(const auto&r:t.widgets)if(r.effective_visible&&r.enabled&&Signature(r.standard_click_binding_12004,op)){
  if(found)return nullptr;found=&r;
 }return found;
}
bool ResolveRow(const ZhongguoScoreboardNativeEnvironmentV1&e,const relic::Admission&a,
 const NamedGuiWidgetInspectionV1&row,const void*expected_context,relic::ButtonPresentation&out) {
 std::vector<std::uint32_t>indexes;std::string_view path=row.child_path;
 while(!path.empty()){
  const auto slash=path.find('/');const auto part=path.substr(0,slash);std::uint32_t n=0;
  const auto parsed=std::from_chars(part.data(),part.data()+part.size(),n);
  if(part.empty()||parsed.ec!=std::errc{}||parsed.ptr!=part.data()+part.size()||n>=2048||indexes.size()>=64)return false;
  indexes.push_back(n);if(slash==std::string_view::npos)break;path.remove_prefix(slash+1);if(path.empty())return false;
 }
 if(indexes.empty())return false;
 ZhongguoScoreboardAccessV1 access{};void*root=nullptr,*widget=nullptr,*vt=nullptr,*context=nullptr;std::string name;
 bool visible=false,enabled=false;SIZE_T got=0;
 if(!ResolveFixedGuiChildPathV1(e,access,"holy_site_window",indexes.data(),indexes.size(),root,widget)||root!=a.actual_root||!widget||
    !ReadGuiWidgetRuntimeV1(access,widget,name,vt,visible,enabled)||!visible||!enabled||
    reinterpret_cast<std::uintptr_t>(vt)!=e.module_base+row.vtable_rva||name!=row.runtime_name||
    !ReadProcessMemory(GetCurrentProcess(),static_cast<const unsigned char*>(widget)+0xD8,&context,sizeof(context),&got)||
    got!=sizeof(context)||context!=expected_context)return false;
 out.available=true;out.visible=visible;out.enabled=enabled;out.child_path=row.child_path;out.widget=widget;out.vtable=vt;return true;
}
bool ReadPresentation(void*opaque,const relic::Admission&a,const relic::Request&r,relic::ButtonPresentation&out) noexcept {
 out={};try{
  auto*c=static_cast<PresentationContext*>(opaque);
  if(!c||!c->env||!c->gui_context)return false;
  const auto&e=*c->env;
  if(!e.exact_build_admitted||e.offline_fixture_function_overrides||!e.module_base||
     e.gui_abi_revision!=GuiAbiRevisionV1::crozier12004||e.executable_sha256!=ck3_12004::kExecutableSha256)return false;
  NamedGuiTreeInspectionV1 first{},last{};
  if(!Tree(e,a.actual_root,first))return false;
  const auto*x=Unique(first,r.operation);if(!x)return false;
  relic::ButtonPresentation observed{};
  if(!ResolveRow(e,a,*x,c->gui_context,observed)||!Tree(e,a.actual_root,last))return false;
  const auto*y=Unique(last,r.operation);
  if(!y||y->child_path!=x->child_path||y->vtable_rva!=x->vtable_rva||y->runtime_name!=x->runtime_name||
     !Same(x->standard_click_binding_12004,y->standard_click_binding_12004))return false;
  relic::ButtonPresentation again{};
  if(!ResolveRow(e,a,*y,c->gui_context,again)||again!=observed)return false;
  out=std::move(observed);return true;
 }catch(...){return false;}
}
}
bool ExecuteHolySiteRelicNavigation12004(const ZhongguoScoreboardNativeEnvironmentV1&e,void*handler,
 const IngameUiRequestV1&request,const game::Snapshot&snapshot,const MainThreadExecutionStampV1&stamp,
 const IngameUiGuiOwnerBindingV1&gui_binding,IngameUiResultV1&out) noexcept {
 namespace relic=ck3_12004::religion::relic_actions;
 out.relic_action_requested=true;
 if(!e.exact_build_admitted||e.offline_fixture_function_overrides||!e.module_base||
    e.gui_abi_revision!=GuiAbiRevisionV1::crozier12004||e.executable_sha256!=ck3_12004::kExecutableSha256||
    request.window_kind!=IngameUiWindowKindV1::holy_site||!relic::IsOperation(static_cast<std::uint32_t>(request.operation))||
    request.relic_action.holy_site_id!=request.subject_id){out.unavailable_reason="relic_ui_exact_build_or_typed_request_unverified";return true;}
 void*window=nullptr,*root=nullptr;
 if(!ResolveHolySiteUiSelection12004(e,handler,request.subject_id,window,root)||!root||!out.effective_visible||!out.enabled||
    !out.subject_id_available||out.current_subject_id!=request.subject_id||out.tree.truncated){
  out.unavailable_reason="relic_ui_actual_visible_site_root_unverified";return true;
 }
 relic::Frame frame{request.connection_generation,request.native_revision,stamp.pump_epoch,snapshot.date_raw,snapshot.played_character_id};
 IngameUiGuiOwnerBindingV1 current_gui{};
 const bool owner_frame=stamp.thread_id==GetCurrentThreadId()&&stamp.pump_epoch&&stamp.tls_initialized_flag_address&&
  stamp.tls_initialized==1&&stamp.tls_context&&stamp.tls_main_thread_marker==1&&stamp.jomini_state&&stamp.game_state&&
  snapshot.paused&&stamp.paused&&snapshot.date_raw==stamp.date_raw&&
  ReadIngameUiGuiOwnerBindingV1(e,current_gui)&&current_gui==gui_binding;
 relic::Admission admission{reinterpret_cast<const void*>(stamp.jomini_state),handler,root,
  owner_frame,
  out.modal_admission.receivers_verified&&out.modal_admission.effective_visible_count==0,out.effective_visible,out.enabled};
 auto binding=relic::BindHolySiteRelicActionsImage12004(e.module_base,e.executable_sha256);
 PresentationContext presentation{&e,gui_binding.context};binding.presentation_reader=&ReadPresentation;binding.presentation_context=&presentation;
 // First legitimate action is admitted by fresh real preview/source/GUI
 // observations, never by a claim that past action qualification passed.
#if XAR_ENABLE_HOLY_SITE_RELIC_BUTTON_ACTION12004
 relic::ProductionRelicActionPreviewContext12004 preview{e.module_base,e.executable_sha256};
 binding.preview_reader=&relic::ReadProductionRelicActionPreview12004;binding.preview_context=&preview;
 binding.gameplay_action_lane_enabled=true;
#endif
 relic::ExecuteHolySiteRelicAction12004(binding,admission,frame,request.relic_action,out.relic_action);
 out.available=out.relic_action.available;out.dispatch_invoked=out.relic_action.dispatch_invoked;
 out.native_dispatch_attempted=out.relic_action.native_dispatch_attempted;out.verification_pending=out.relic_action.verification_pending;
 out.status=out.relic_action.status;out.unavailable_reason=out.relic_action.unavailable_reason;return true;
}
}
