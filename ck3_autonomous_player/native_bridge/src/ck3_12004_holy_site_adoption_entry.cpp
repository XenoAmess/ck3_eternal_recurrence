#include "xar_bridge/ck3_12004_holy_site_adoption_entry.hpp"
#include "xar_bridge/zhongguo_scoreboard_action_v1.hpp"
#include "xar_bridge/holy_site_decision_entry_parameters12004.hpp"
#include <windows.h>
#include <array>
#include <charconv>
#include <limits>
#include <utility>

namespace xar::ck3_11906 {
namespace {
template<class T>bool Read(const void*p,std::size_t offset,T&v)noexcept{
 const auto base=reinterpret_cast<std::uintptr_t>(p);SIZE_T got=0;
 return base&&offset<=std::numeric_limits<std::uintptr_t>::max()-base&&
  ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<const void*>(base+offset),&v,sizeof(v),&got)&&got==sizeof(v);
}
template<std::size_t N>bool Pin(std::uintptr_t base,std::uintptr_t rva,const std::array<unsigned char,N>&expected)noexcept{
 std::array<unsigned char,N>actual{};SIZE_T got=0;
 return ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<const void*>(base+rva),actual.data(),N,&got)&&got==N&&actual==expected;
}
bool Pins(std::uintptr_t base)noexcept{
 return Pin(base,0x17D6590,std::array<unsigned char,32>{0x48,0x89,0x5c,0x24,0x08,0x57,0x48,0x83,0xec,0x20,0x48,0x8b,0xf9,0x48,0x8b,0x0d,0xc4,0x0f,0x49,0x04,0x48,0x85,0xc9,0x74,0x29,0x8b,0x05,0x51,0x56,0xd0,0x03,0x8b})&&
 Pin(base,0x17D6360,std::array<unsigned char,32>{0x48,0x89,0x5c,0x24,0x10,0x57,0x48,0x83,0xec,0x20,0x48,0x8b,0xf9,0x48,0x8b,0x0d,0xf4,0x11,0x49,0x04,0x48,0x85,0xc9,0x74,0x29,0x8b,0x05,0x81,0x58,0xd0,0x03,0x8b})&&
 Pin(base,0x17D6480,std::array<unsigned char,32>{0x48,0x89,0x5c,0x24,0x10,0x57,0x48,0x83,0xec,0x20,0x48,0x8b,0xf9,0x48,0x8b,0x0d,0xd4,0x10,0x49,0x04,0x48,0x85,0xc9,0x74,0x29,0x8b,0x05,0x61,0x57,0xd0,0x03,0x8b})&&
 Pin(base,0xA79540,std::array<unsigned char,32>{0x48,0x89,0x5c,0x24,0x08,0x48,0x89,0x6c,0x24,0x10,0x56,0x57,0x41,0x56,0x48,0x83,0xec,0x40,0x4d,0x8b,0xf0,0xe8,0xc6,0xb4,0xde,0xff,0x48,0x8b,0xf0,0x41,0x8b,0x46})&&
 Pin(base,0x1031E60,std::array<unsigned char,28>{0x48,0x83,0xec,0x28,0x48,0x85,0xc9,0x74,0x0c,0xe8,0x96,0x67,0x00,0x00,0xb0,0x01,0x48,0x83,0xc4,0x28,0xc3,0x32,0xc0,0x48,0x83,0xc4,0x28,0xc3})&&
 Pin(base,0x1038604,std::array<unsigned char,9>{0x48,0x8b,0x01,0xff,0xa0,0x88,0x00,0x00,0x00});
}
bool Predicates(std::uintptr_t base,void*window,bool&a,bool&r,bool&e)noexcept{
#if defined(_MSC_VER)
 __try{
#endif
 a=reinterpret_cast<bool(__fastcall*)(void*)>(base+0x17D6590)(window);
 r=reinterpret_cast<bool(__fastcall*)(void*)>(base+0x17D6360)(window);
 e=reinterpret_cast<bool(__fastcall*)(void*)>(base+0x17D6480)(window);
 return true;
#if defined(_MSC_VER)
 }__except(EXCEPTION_EXECUTE_HANDLER){return false;}
#endif
}
bool Signature(const NamedGuiStandardClickBinding12004V1&b){
 // The producer already selects the original standard-mode group: +3F8
 // when populated, otherwise +338. HolySite's stock shortcut uses fallback.
 // Same() below still rejects a group change between the two owner reads.
 if(!b.button_base_slot13||b.callbacks.size()!=2)return false;
 const std::array<std::uint64_t,2>targets{0xA79540,0x1031E60};
 for(std::size_t i=0;i<2;++i){const auto&c=b.callbacks[i];const auto&d=c.expression_3a9f960;
  if(c.index!=i||c.callback_slot2_rva!=0x3AA30E0||!c.indirect_target_3aa30e0||
    c.native_target_8_rva!=0x3A9F960||!c.expression_descriptor_3a9f960||
    (d.final_kind_34_raw!=3&&d.final_kind_34_raw!=4)||d.final_target_38_rva!=targets[i])return false;
 }return true;
}
bool Same(const NamedGuiStandardClickBinding12004V1&a,const NamedGuiStandardClickBinding12004V1&b){
 if(a.button_base_slot13!=b.button_base_slot13||a.primary_group!=b.primary_group||a.callbacks.size()!=b.callbacks.size())return false;
 for(std::size_t i=0;i<a.callbacks.size();++i){const auto&x=a.callbacks[i];const auto&y=b.callbacks[i];
  if(x.index!=y.index||x.callback_vtable_rva!=y.callback_vtable_rva||x.callback_slot2_rva!=y.callback_slot2_rva||
    x.indirect_target_3aa30e0!=y.indirect_target_3aa30e0||x.native_target_8_rva!=y.native_target_8_rva||
    x.receiver_f0_present!=y.receiver_f0_present||x.expression_descriptor_3a9f960!=y.expression_descriptor_3a9f960||
    !(x.expression_3a9f960==y.expression_3a9f960))return false;
 }return true;
}
const NamedGuiWidgetInspectionV1*Unique(const NamedGuiTreeInspectionV1&t){
 const NamedGuiWidgetInspectionV1*found=nullptr;
 for(const auto&r:t.widgets)if(r.effective_visible&&r.enabled&&Signature(r.standard_click_binding_12004)){
  if(found)return nullptr;found=&r;
 }return found;
}
bool Tree(const ZhongguoScoreboardNativeEnvironmentV1&e,void*expected,NamedGuiTreeInspectionV1&t){
 ZhongguoScoreboardAccessV1 access{};void*root=nullptr,*widget=nullptr;
 return ResolveNamedGuiWidgetV1(e,access,"holy_site_window","holy_site_window",root,widget)&&
  root==expected&&widget==root&&InspectNamedGuiSubtreeV1(access,e.module_base,root,"holy_site_window",t,true,false)&&
  t.root_available&&!t.truncated&&t.widget_count==t.widgets.size()&&t.widget_count&&
  t.callback_thunk_3aa30e0_pin_verified&&t.expression_layout_3a9f960_pin_verified;
}
bool Receiver(const ZhongguoScoreboardNativeEnvironmentV1&e,void*root,void*context,
 const NamedGuiWidgetInspectionV1&row,void*&target,void*&vtable){
 std::vector<std::uint32_t>indices;std::string_view p=row.child_path;
 if(p.empty())return false;
 while(!p.empty()){
  const auto slash=p.find('/');const auto part=p.substr(0,slash);std::uint32_t n=0;
  auto parsed=std::from_chars(part.data(),part.data()+part.size(),n);
  if(part.empty()||parsed.ec!=std::errc{}||parsed.ptr!=part.data()+part.size()||n>=2048||indices.size()>=64)return false;
  indices.push_back(n);if(slash==std::string_view::npos)break;p.remove_prefix(slash+1);if(p.empty())return false;
 }
 ZhongguoScoreboardAccessV1 access{};void*previous=nullptr;
 for(std::size_t n=0;n<=indices.size();++n){void*actual_root=nullptr,*widget=nullptr,*owner=nullptr;
  if(!ResolveFixedGuiChildPathV1(e,access,"holy_site_window",indices.data(),n,actual_root,widget)||
   actual_root!=root||!widget||!Read(widget,kZhongguoWidgetGuiContextOffset,owner)||owner!=context)return false;
  if(previous){void*parent=nullptr;if(!Read(widget,kZhongguoWidgetParentOffset,parent)||parent!=previous)return false;}
  previous=widget;
 }
 target=previous;std::string name;bool visible=false,enabled=false;
 return ReadGuiWidgetRuntimeV1(access,target,name,vtable,visible,enabled)&&visible&&enabled&&
  name==row.runtime_name&&reinterpret_cast<std::uintptr_t>(vtable)==e.module_base+row.vtable_rva;
}
}
bool OpenHolySiteAdoptionEntry12004(const ZhongguoScoreboardNativeEnvironmentV1&e,
 void*handler,std::uint32_t id,void*context,IngameUiResultV1&out)noexcept{
 try{
  const auto fail=[&](const char*why){out.unavailable_reason=why;return false;};
  void*window=nullptr,*root=nullptr;
  if(!ResolveHolySiteUiSelection12004(e,handler,id,window,root)||!root||!out.effective_visible||
    !out.subject_id_available||out.current_subject_id!=id)return fail("adoption_entry_requires_visible_selected_holy_site");
  if(!Pins(e.module_base))return fail("adoption_entry_loaded_source_pins_changed");
  bool adopt=false,regular=false,eminent=false;
  if(!Predicates(e.module_base,window,adopt,regular,eminent))return fail("adoption_entry_visibility_predicates_unavailable");
  out.holy_site_adopt_visibility_observed=true;out.holy_site_adopt_visible=adopt;
  out.holy_site_regular_visible=regular;out.holy_site_eminent_visible=eminent;
  if(!adopt||regular||eminent)return fail("adoption_entry_visibility_not_exclusive");
  NamedGuiTreeInspectionV1 first{},second{};
  if(!Tree(e,root,first))return fail("adoption_entry_callback_census_incomplete");
  const auto*candidate=Unique(first);if(!candidate)return fail("adoption_entry_receiver_not_unique");
  void*target=nullptr,*vtable=nullptr;
  if(!Receiver(e,root,context,*candidate,target,vtable))return fail("adoption_entry_receiver_binding_changed");
  auto dispatch=BindZhongguoScoreboardActionDispatchEnvironmentV1(e.module_base,true,e.gui_abi_revision);
  if(!InspectFixedGuiWidgetDispatchAdmissionV1(dispatch,target,vtable))return fail("adoption_entry_dispatch_admission_failed");
  void*last_window=nullptr,*last_root=nullptr;bool last_a=false,last_r=false,last_e=false;
  if(!ResolveHolySiteUiSelection12004(e,handler,id,last_window,last_root)||last_window!=window||last_root!=root||
    !Predicates(e.module_base,window,last_a,last_r,last_e)||!last_a||last_r||last_e||!Tree(e,root,second))return fail("adoption_entry_pre_dispatch_binding_changed");
  const auto*last=Unique(second);void*last_target=nullptr,*last_vtable=nullptr;
  if(!last||last->child_path!=candidate->child_path||!Same(candidate->standard_click_binding_12004,last->standard_click_binding_12004)||
    !Receiver(e,root,context,*last,last_target,last_vtable)||last_target!=target||last_vtable!=vtable)return fail("adoption_entry_receiver_changed");
  out.holy_site_adopt_receiver_bound=true;out.holy_site_adopt_receiver_child_path=candidate->child_path;
  // This caller establishes a fresh semantic source binding and ancestry;
  // it reuses only the existing dispatcher's lower native input admission.
  out.native_dispatch_attempted=true;bool handled=false;
  return DispatchFixedGuiWidgetNativeV1(&dispatch,game::ZhongguoScoreboardActionV1::open,target,vtable,handled);
 }catch(...){out.unavailable_reason="adoption_entry_provider_exception";return false;}
}
bool OpenHolySiteDecisionEntry12004(const ZhongguoScoreboardNativeEnvironmentV1&e,
 void*handler,std::uint32_t id,void*context,
 ck3_12004::religion::holy_site::DecisionAction action,IngameUiResultV1&out)noexcept{
 namespace hs=ck3_12004::religion::holy_site;
 try{
  const auto fail=[&](std::string why){out.unavailable_reason=std::move(why);return false;};
  if(hs::DecisionKey(action).empty())return fail("holy_site_decision_action_invalid");
  void*window=nullptr,*root=nullptr;
  if(!ResolveHolySiteUiSelection12004(e,handler,id,window,root)||!root||!out.effective_visible||
     !out.subject_id_available||out.current_subject_id!=id)return fail("holy_site_decision_requires_visible_selected_site");
  if(!Pins(e.module_base))return fail("holy_site_decision_entry_source_pins_changed");
  bool adopt=false,regular=false,eminent=false;
  const auto visible=[&](bool a,bool r,bool m){
   if(action==hs::DecisionAction::adopt)return a&&!r&&!m;
   if(action==hs::DecisionAction::demote)return !a&&!r&&m;
   return !a&&r&&!m;
  };
  if(!Predicates(e.module_base,window,adopt,regular,eminent))return fail("holy_site_decision_visibility_unavailable");
  out.holy_site_adopt_visibility_observed=true;out.holy_site_adopt_visible=adopt;
  out.holy_site_regular_visible=regular;out.holy_site_eminent_visible=eminent;
  if(!visible(adopt,regular,eminent))return fail("holy_site_decision_visibility_differs_from_requested_action");
  const auto bindings=hs::BindHolySiteDecisionEntryParametersImage12004(e.module_base,e.executable_sha256);
  struct Selection{const NamedGuiWidgetInspectionV1*row=nullptr;void*target=nullptr,*vtable=nullptr;hs::EntryParameterSnapshot parameters{};};
  const auto select=[&](const NamedGuiTreeInspectionV1&tree,Selection&selection){
   for(const auto&row:tree.widgets){
    if(!row.effective_visible||!row.enabled||!Signature(row.standard_click_binding_12004))continue;
    void*widget=nullptr,*vt=nullptr;
    if(!Receiver(e,root,context,row,widget,vt)){out.unavailable_reason="holy_site_decision_receiver_owner_or_ancestry_changed";return false;}
    hs::EntryParameterSnapshot parameters{};
    if(!hs::ReadHolySiteDecisionEntryParameters12004(bindings,widget,action,id,parameters)){
     bool other_fixed=false;
     if(parameters.decision_key_verified)for(const auto other:{hs::DecisionAction::adopt,hs::DecisionAction::promote,hs::DecisionAction::demote,hs::DecisionAction::abandon})
      if(other!=action&&parameters.decision_key==hs::DecisionKey(other))other_fixed=true;
     if(other_fixed)continue;
     out.unavailable_reason=parameters.unavailable_reason.empty()?"holy_site_decision_receiver_parameters_unknown":parameters.unavailable_reason;return false;
    }
    if(selection.row){out.unavailable_reason="holy_site_decision_receiver_not_unique";return false;}
    selection={&row,widget,vt,std::move(parameters)};
   }
   if(!selection.row){out.unavailable_reason="holy_site_decision_exact_receiver_not_found";return false;}return true;
  };
  NamedGuiTreeInspectionV1 first{},second{};Selection before{},after{};
  if(!Tree(e,root,first)||!select(first,before))return fail(out.unavailable_reason.empty()?"holy_site_decision_callback_census_incomplete":out.unavailable_reason);
  auto dispatch=BindZhongguoScoreboardActionDispatchEnvironmentV1(e.module_base,true,e.gui_abi_revision);
  if(!InspectFixedGuiWidgetDispatchAdmissionV1(dispatch,before.target,before.vtable))return fail("holy_site_decision_dispatch_admission_failed");
  void*last_window=nullptr,*last_root=nullptr;bool last_a=false,last_r=false,last_e=false;
  if(!ResolveHolySiteUiSelection12004(e,handler,id,last_window,last_root)||last_window!=window||last_root!=root||
     !Predicates(e.module_base,window,last_a,last_r,last_e)||!visible(last_a,last_r,last_e)||!Tree(e,root,second)||!select(second,after))
   return fail(out.unavailable_reason.empty()?"holy_site_decision_pre_dispatch_binding_changed":out.unavailable_reason);
  if(before.target!=after.target||before.vtable!=after.vtable||before.row->child_path!=after.row->child_path||
     !Same(before.row->standard_click_binding_12004,after.row->standard_click_binding_12004)||
     before.parameters.params!=after.parameters.params||before.parameters.definition!=after.parameters.definition||
     before.parameters.source_widget!=after.parameters.source_widget||before.parameters.decision_key!=after.parameters.decision_key||
     before.parameters.holy_site_id!=after.parameters.holy_site_id||
     before.parameters.self_return_type_raw!=after.parameters.self_return_type_raw)return fail("holy_site_decision_actual_parameters_changed");
  out.holy_site_adopt_receiver_bound=true;out.holy_site_adopt_receiver_child_path=before.row->child_path;
  out.holy_site_decision_parameters_verified=true;out.holy_site_decision_definition_key=before.parameters.decision_key;
  out.holy_site_decision_parameter_id=before.parameters.holy_site_id;
  out.native_dispatch_attempted=true;bool handled=false;
  return DispatchFixedGuiWidgetNativeV1(&dispatch,game::ZhongguoScoreboardActionV1::open,before.target,before.vtable,handled);
 }catch(...){out.unavailable_reason="holy_site_decision_entry_exception";return false;}
}
}
