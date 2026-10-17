#include "xar_bridge/ck3_12004_holy_site_relic_actions.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include <algorithm>
#include <array>
#include <limits>
#include <utility>
#if defined(_WIN32)
#include <windows.h>
#endif
#ifndef XAR_ENABLE_HOLY_SITE_RELIC_TYPED_UI12004
#define XAR_ENABLE_HOLY_SITE_RELIC_TYPED_UI12004 0
#endif

namespace xar::ck3_12004::religion::relic_actions {
namespace {
const void*At(const void*p,std::size_t offset) noexcept {
 const auto v=reinterpret_cast<std::uintptr_t>(p);
 return v&&offset<=std::numeric_limits<std::uintptr_t>::max()-v?reinterpret_cast<const void*>(v+offset):nullptr;
}
template<class T>bool Read(const Bindings&b,const void*p,std::size_t o,T&v) noexcept {
 const auto*a=At(p,o);return a&&b.read_memory&&b.read_memory(b.read_context,a,&v,sizeof(v));
}
bool ProcessRead(void*,const void*p,void*out,std::size_t n) noexcept {
#if defined(_WIN32)
 SIZE_T got=0;return ReadProcessMemory(GetCurrentProcess(),p,out,n,&got)&&got==n;
#else
 (void)p;(void)out;(void)n;return false;
#endif
}
bool Resolve(const Bindings&b,void**storage_slot,std::uint32_t id,std::size_t id_offset,
 std::size_t magic_offset,std::uint32_t magic,const void*&out) noexcept {
 out=nullptr;const void*store=nullptr,*rows=nullptr;std::uint32_t count=0,actual=absent,actual_magic=0;
 return id!=absent&&Read(b,storage_slot,0,store)&&store&&Read(b,store,0x20,rows)&&rows&&
  Read(b,store,0x2C,count)&&(id&0xFFFFFFU)<count&&
  Read(b,rows,static_cast<std::size_t>(id&0xFFFFFFU)*16+8,out)&&out&&
  Read(b,out,id_offset,actual)&&actual==id&&Read(b,out,magic_offset,actual_magic)&&actual_magic==magic;
}
struct Header {const void*data=nullptr;std::int32_t capacity=0,count=0;std::uint64_t allocator=0;bool operator==(const Header&)const=default;};
struct Slot {std::uintptr_t vtable=0,type=0;std::uint32_t artifact=absent,magic=0;bool operator==(const Slot&)const=default;};
static_assert(sizeof(Header)==24&&sizeof(Slot)==24);
bool Array(const Bindings&b,const void*p,std::size_t o,Header&h) noexcept {
 return Read(b,p,o,h)&&h.count>=0&&h.count<=4096&&h.capacity>=h.count&&h.capacity<=8192&&(h.count==0||h.data);
}
template<class T>bool Rows(const Bindings&b,const Header&h,std::vector<T>&rows) {
 rows.resize(static_cast<std::size_t>(h.count));
 return rows.empty()||b.read_memory(b.read_context,h.data,rows.data(),rows.size()*sizeof(T));
}
std::optional<std::uint32_t>Id(std::uint32_t value) {return value==absent?std::nullopt:std::optional<std::uint32_t>{value};}
struct Pass {
 const void*actor=nullptr,*site=nullptr,*gfx=nullptr,*handler=nullptr,*window=nullptr,*window_owner=nullptr,*root=nullptr,*selected_slot=nullptr;
 std::uint32_t selected_site=absent,selected_artifact=absent;
 Header slots_header{};std::vector<Slot>slots;
 Selection observation{};
 bool operator==(const Pass&other)const {
  return actor==other.actor&&site==other.site&&gfx==other.gfx&&handler==other.handler&&window==other.window&&
   root==other.root&&window_owner==other.window_owner&&selected_slot==other.selected_slot&&selected_site==other.selected_site&&
   selected_artifact==other.selected_artifact&&slots_header==other.slots_header&&slots==other.slots;
 }
};
bool Capture(const Bindings&b,const Admission&a,const Frame&f,std::uint32_t site_id,Pass&p,std::string&why) {
 const auto fail=[&](const char*v){why=v;return false;};
 if(!b.enabled||!b.read_memory||!a.owner_tls_paused_verified||!a.modal_admitted||
    !a.actual_root_visible||!a.actual_root_enabled||!a.jomini_owner||!a.handler||!a.actual_root||
    !f.connection_generation||!f.native_revision||!f.capture_epoch||f.played_character_id<=0||site_id==absent)
  return fail("relic_ui_owner_paused_modal_frame_or_visible_root_not_admitted");
 std::uint32_t actor=absent;const void*back=nullptr;std::uintptr_t primary=0,secondary=0;
 if(!Read(b,b.current_actor_reference,0,actor)||actor!=static_cast<std::uint32_t>(f.played_character_id)||
    !Resolve(b,b.character_storage,actor,0x18,0x1C,0x43686172U,p.actor)||
    !Resolve(b,b.holy_site_storage,site_id,0x10,0x14,0x486F5374U,p.site))
  return fail("relic_ui_actor_or_site_full_reference_changed");
 if(!Read(b,a.jomini_owner,0x10,p.gfx)||!p.gfx||!Read(b,p.gfx,0x88,p.handler)||p.handler!=a.handler||
    !Read(b,p.handler,0x5D8,p.window)||!p.window||
    !Read(b,p.window,0,primary)||primary!=b.image_base+0x4592338||
    !Read(b,p.window,0x10,secondary)||secondary!=b.image_base+0x4592310||
    !Read(b,p.window,0xA0,back)||back!=p.handler||
    !Read(b,p.window,0x98,p.window_owner)||p.window_owner!=a.jomini_owner||
    !Read(b,p.window,0x60,p.root)||p.root!=a.actual_root||
    !Read(b,p.window,0xC8,p.selected_site)||p.selected_site!=site_id||
    !Read(b,p.window,0x108,p.selected_artifact)||!Read(b,p.window,0x110,p.selected_slot))
  return fail("relic_ui_registered_window_type_owner_root_or_selection_changed");
 if(!Array(b,p.site,0x68,p.slots_header)||!Rows(b,p.slots_header,p.slots)||
    std::any_of(p.slots.begin(),p.slots.end(),[](const Slot&s){return s.magic!=0x496E7653U;}))
  return fail("relic_ui_current_site_slot_table_unavailable");
 p.observation.artifact_id=Id(p.selected_artifact);
 for(std::size_t i=0;i<p.slots.size();++i){
  p.observation.slot_artifact_ids.push_back(Id(p.slots[i].artifact));
  if(p.selected_slot==At(p.slots_header.data,i*sizeof(Slot)))p.observation.slot_index=static_cast<std::uint32_t>(i);
 }
 if(p.selected_slot&&!p.observation.slot_index)return fail("relic_ui_selected_slot_not_current_site_row");
 p.observation.available=true;p.observation.unavailable_reason.clear();why.clear();return true;
}
bool Pin(const Bindings&b,std::uintptr_t rva,std::string_view hex) noexcept {
 if(hex.size()%2||hex.size()>128||rva>std::numeric_limits<std::uintptr_t>::max()-b.image_base)return false;
 std::array<unsigned char,64>raw{};
 if(!b.read_memory(b.read_context,reinterpret_cast<const void*>(b.image_base+rva),raw.data(),hex.size()/2))return false;
 const auto digit=[](char c)->int{return c>='0'&&c<='9'?c-'0':c>='a'&&c<='f'?c-'a'+10:-1;};
 for(std::size_t i=0;i<hex.size()/2;++i){const auto h=digit(hex[i*2]),l=digit(hex[i*2+1]);
  if(h<0||l<0||raw[i]!=static_cast<unsigned char>(h*16+l))return false;}
 return true;
}
#include "ck3_12004_holy_site_relic_actions_pins.inc"
bool Pins(const Bindings&b) noexcept {
 for(const auto&[rva,hex]:kRelicActionPins)if(!Pin(b,rva,hex))return false;
 return true;
}
bool NativeSelection(const Bindings&b,std::uintptr_t rva,const void*w,const void*object,bool&attempted) noexcept {
#if defined(_WIN32)&&defined(_MSC_VER)
 __try {attempted=true;reinterpret_cast<void(__fastcall*)(const void*,const void*)>(b.image_base+rva)(w,object);return true;}
 __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#else
 (void)b;(void)rva;(void)w;(void)object;(void)attempted;return false;
#endif
}
bool NativeSelect(const Bindings&b,const void*w,const void*a,bool&attempted) noexcept {return NativeSelection(b,0x17D52B0,w,a,attempted);}
bool NativeToggle(const Bindings&b,const void*w,const void*s,bool&attempted) noexcept {return NativeSelection(b,0x17D52F0,w,s,attempted);}
bool NativeButton(const Bindings&b,std::uintptr_t rva,const void*w,bool&value) noexcept {
#if defined(_WIN32)&&defined(_MSC_VER)
 __try {value=reinterpret_cast<bool(__fastcall*)(const void*)>(b.image_base+rva)(w);return true;}
 __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#else
 (void)b;(void)rva;(void)w;(void)value;return false;
#endif
}
bool NativeEnshrineButton(const Bindings&b,const void*w,bool&v) noexcept {return NativeButton(b,0x17D5970,w,v);}
bool NativeRemoveButton(const Bindings&b,const void*w,bool&v) noexcept {return NativeButton(b,0x17D5E40,w,v);}
bool NativeClick(const Bindings&b,std::uintptr_t rva,const void*w,bool&attempted) noexcept {
#if defined(_WIN32)&&defined(_MSC_VER)
 __try {attempted=true;reinterpret_cast<void(__fastcall*)(const void*)>(b.image_base+rva)(w);return true;}
 __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#else
 (void)b;(void)rva;(void)w;(void)attempted;return false;
#endif
}
bool NativeEnshrineClick(const Bindings&b,const void*w,bool&attempted) noexcept {return NativeClick(b,0x17D5DD0,w,attempted);}
bool NativeRemoveClick(const Bindings&b,const void*w,bool&attempted) noexcept {return NativeClick(b,0x17D62F0,w,attempted);}
bool Selectable(const Bindings&b,const Pass&p,std::uint32_t id) {
 if(std::any_of(p.slots.begin(),p.slots.end(),[&](const Slot&s){return s.artifact==id;}))return true;
 Header h{},later{};std::vector<std::uint32_t>ids,again;
 return Array(b,p.window,0x130,h)&&Rows(b,h,ids)&&
  std::find(ids.begin(),ids.end(),id)!=ids.end()&&Array(b,p.window,0x130,later)&&later==h&&Rows(b,later,again)&&ids==again;
}
bool ProofValid(const PreviewProof&p,const Frame&f,const Request&r,const Pass&state) {
 if(!p.available||!p.source_qualified||!p.live_qualified||p.frame!=f||p.holy_site_id!=r.holy_site_id||
    p.artifact_id!=r.artifact_id||p.selected_slot_index!=state.observation.slot_index||
    !p.preview_observed||
    p.preview_identity_sha256!=r.expected_preview_identity_sha256)return false;
 if(r.operation==Operation::enshrine){
  return p.artifact_character_owner_matches_player&&p.player_owned_ids_contains_artifact&&p.effective_slot_index==r.expected_effective_slot_index&&
   p.replacing_artifact_id==r.expected_replacing_artifact_id&&p.effective_slot_index&&
   *p.effective_slot_index<state.slots.size()&&Id(state.slots[*p.effective_slot_index].artifact)==p.replacing_artifact_id;
 }
 return p.site_equipped_slot_member&&!p.effective_slot_index&&!p.replacing_artifact_id;
}
bool Stable(const Bindings&b,const Admission&a,const Frame&f,const Request&r,const Pass&before) {
 Pass again{};std::string ignored;return Capture(b,a,f,r.holy_site_id,again,ignored)&&again==before;
}
void FinishDispatch(Result&out,bool invoked,bool gameplay) {
 out.dispatch_invoked=invoked;out.available=invoked;out.verification_pending=out.native_dispatch_attempted||invoked;
 out.gameplay_command_may_have_been_queued=gameplay&&out.native_dispatch_attempted;
 out.status=invoked?"acknowledged_verification_pending":out.native_dispatch_attempted?"dispatch_result_unknown":"unavailable";
 out.unavailable_reason=invoked?"":out.native_dispatch_attempted?"original_callback_result_unknown_do_not_retry":"original_callback_unavailable";
}
}
Bindings BindHolySiteRelicActionsImage12004(std::uintptr_t base,std::string_view sha) noexcept {
 Bindings b{};
 if(!XAR_ENABLE_HOLY_SITE_RELIC_TYPED_UI12004||!base||sha!=ck3_12004::kExecutableSha256)return b;
 b.enabled=true;b.source_bound=true;b.image_base=base;b.read_memory=&ProcessRead;
 b.holy_site_storage=reinterpret_cast<void**>(base+0x5D1DE80);b.artifact_storage=reinterpret_cast<void**>(base+0x5D1DE68);
 b.character_storage=reinterpret_cast<void**>(base+0x5C67568);b.current_actor_reference=reinterpret_cast<const std::uint32_t*>(base+0x54DBC00);
 b.select_artifact=&NativeSelect;b.toggle_slot=&NativeToggle;b.enshrine_button=&NativeEnshrineButton;b.remove_button=&NativeRemoveButton;
 b.enshrine_click=&NativeEnshrineClick;b.remove_click=&NativeRemoveClick;b.backend="source_bound_original_holy_site_ui";
 // No gameplay qualification or preview reader is silently installed here.
 return b;
}
bool ReadHolySiteRelicSelection12004(const Bindings&b,const Admission&a,const Frame&f,std::uint32_t site_id,Selection&out) noexcept {
 out={};try{
  if(b.source_bound&&!Pins(b)){out.unavailable_reason="relic_ui_loaded_source_pins_changed";return false;}
  Pass first{},last{};std::string why;
  if(!Capture(b,a,f,site_id,first,why)||!Capture(b,a,f,site_id,last,why)||first!=last){
   out.unavailable_reason=why.empty()?"relic_ui_selection_changed_during_read":why;return false;}
  out=std::move(first.observation);return true;
 }catch(...){out.unavailable_reason="relic_ui_selection_read_exception";return false;}
}
bool ExecuteHolySiteRelicAction12004(const Bindings&b,const Admission&a,const Frame&f,const Request&r,Result&out) noexcept {
 out={};const auto fail=[&](const char*why){out.unavailable_reason=why;return false;};
 try{
  if(!ValidateRequest(r))return fail("relic_ui_request_invalid");
  if(b.source_bound){if(!Pins(b))return fail("relic_ui_loaded_source_pins_changed");out.loaded_source_pins_verified=true;}
  Pass state{};std::string why;
  if(!Capture(b,a,f,r.holy_site_id,state,why)){out.unavailable_reason=why;return false;}
  out.before=state.observation;
  const void*artifact=nullptr;
  if(r.operation!=Operation::set_slot&&!Resolve(b,b.artifact_storage,r.artifact_id,0x10,0x14,0x41727469U,artifact))
   return fail("relic_ui_artifact_full_reference_unavailable");
  if(r.operation==Operation::select_artifact||r.operation==Operation::set_slot){
   const void*argument=artifact;SelectionCall call=b.select_artifact;
   bool change=state.selected_artifact!=r.artifact_id;
   if(r.operation==Operation::select_artifact){if(!Selectable(b,state,r.artifact_id))return fail("relic_ui_artifact_not_in_current_site_slots_or_window_candidates");}
   else {
    if(*r.slot_index>=state.slots.size())return fail("relic_ui_slot_index_not_current_site_row");
    argument=At(state.slots_header.data,static_cast<std::size_t>(*r.slot_index)*sizeof(Slot));call=b.toggle_slot;
    const bool selected=state.observation.slot_index==r.slot_index;
    change=selected!=*r.desired_selected;
    // Clearing an unselected target is already satisfied; never pass null.
   }
   if(!Stable(b,a,f,r,state))return fail("relic_ui_selection_inputs_changed_before_callback");
   bool invoked=true;
   if(change){if(!call)return fail("relic_ui_original_selection_callback_unavailable");invoked=call(b,state.window,argument,out.native_dispatch_attempted);}
   else out.already_in_requested_state=true;
   FinishDispatch(out,invoked,false);
   if(!change){out.dispatch_invoked=false;out.status="already_in_requested_state_verification_pending";}
   if(!ReadHolySiteRelicSelection12004(b,a,f,r.holy_site_id,out.after)){
    if(out.native_dispatch_attempted){out.verification_pending=true;out.unavailable_reason="relic_ui_selection_postcondition_unavailable_do_not_retry";}
    return invoked;
   }
   out.selection_postcondition_observed=out.after.slot_artifact_ids==out.before.slot_artifact_ids&&(r.operation==Operation::select_artifact?
    out.after.artifact_id==std::optional<std::uint32_t>{r.artifact_id}&&out.after.slot_index==out.before.slot_index:
    ((out.after.slot_index==r.slot_index)==*r.desired_selected)&&out.after.artifact_id==out.before.artifact_id);
   if(!out.selection_postcondition_observed){out.verification_pending=true;out.unavailable_reason="relic_ui_selection_postcondition_differs_do_not_retry";}
   return invoked;
  }
  if(!b.gameplay_action_lane_enabled||!b.preview_reader||!b.presentation_reader)return fail("relic_ui_action_optin_and_production_preview_required");
  if(state.selected_artifact!=r.artifact_id)return fail("relic_ui_selected_artifact_differs_from_request");
  std::uint32_t owner=absent;
  if(!Read(b,artifact,0x7C,owner))return fail("relic_ui_artifact_owner_unavailable");
  const bool enshrine=r.operation==Operation::enshrine;
  if((enshrine&&owner==r.holy_site_id)||(!enshrine&&owner!=r.holy_site_id))return fail("relic_ui_artifact_holy_site_owner_differs");
  ButtonPresentation button{},last_button{};
  if(!b.presentation_reader(b.presentation_context,a,r,button)||!button.available||!button.visible||!button.enabled||!button.widget)
   return fail("relic_ui_actual_visible_enabled_original_button_unverified");
  out.actual_button_presentation_observed=true;out.button_child_path=button.child_path;
  PreviewProof first{},last{};
  if(!b.preview_reader(b.preview_context,a,f,r,first)||!ProofValid(first,f,r,state))return fail("relic_ui_frozen_preview_unverified");
  auto predicate=enshrine?b.enshrine_button:b.remove_button;bool allowed=false;
  if(!predicate||!predicate(b,state.window,allowed))return fail("relic_ui_original_button_predicate_unavailable");
  out.original_button_enabled_observed=true;out.original_button_enabled=allowed;
  if(!allowed)return fail("relic_ui_original_button_predicate_false");
  if(!b.preview_reader(b.preview_context,a,f,r,last)||last!=first||!ProofValid(last,f,r,state)||
     !b.presentation_reader(b.presentation_context,a,r,last_button)||last_button!=button||!Stable(b,a,f,r,state))
   return fail("relic_ui_frozen_preview_or_selection_changed_before_callback");
  const void*again=nullptr;std::uint32_t later_owner=absent;
  if(!Resolve(b,b.artifact_storage,r.artifact_id,0x10,0x14,0x41727469U,again)||again!=artifact||
     !Read(b,artifact,0x7C,later_owner)||later_owner!=owner)return fail("relic_ui_artifact_identity_or_owner_changed_before_callback");
  auto click=enshrine?b.enshrine_click:b.remove_click;
  if(!click)return fail("relic_ui_original_button_callback_unavailable");
  out.frozen_preview_verified=true;
  const bool invoked=click(b,state.window,out.native_dispatch_attempted);
  FinishDispatch(out,invoked,true);
  // This is only a selection observation, never a gameplay postcondition.
  ReadHolySiteRelicSelection12004(b,a,f,r.holy_site_id,out.after);
  return invoked;
 }catch(...){
  if(out.native_dispatch_attempted){out.verification_pending=true;out.status="dispatch_result_unknown";
   out.gameplay_command_may_have_been_queued=r.operation==Operation::enshrine||r.operation==Operation::remove;}
  return fail("relic_ui_action_exception_do_not_retry_if_attempted");
 }
}
}
