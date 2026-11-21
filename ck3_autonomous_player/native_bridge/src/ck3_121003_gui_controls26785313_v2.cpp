#include "xar_bridge/ck3_121003_gui_controls26785313_v2.hpp"
#include "xar_bridge/ck3_121003_gui_controls26785313_pins_v2.hpp"
#include "xar_bridge/ck3_121003_core_route26785313_v1.hpp"
#include <algorithm>
#include <array>
#include <cstring>
#include <chrono>
#include <limits>
#include <windows.h>
namespace xar::ck3_121003::build26785313 {namespace {
using namespace ck3_1210;
[[maybe_unused]]bool Bytes(std::uintptr_t address,void *data,std::size_t size) noexcept {
 SIZE_T got=0;return address&&size&&address<=(std::numeric_limits<std::uintptr_t>::max)()-size&&
  ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<const void*>(address),data,size,&got)&&got==size;
}
template<class T>bool Load(std::uintptr_t object,std::size_t offset,T &out) noexcept {
 return object&&offset<=(std::numeric_limits<std::uintptr_t>::max)()-object&&Bytes(object+offset,&out,sizeof(out));
}
[[maybe_unused]]bool Image(const GuiControlImage267V2 &b,std::uintptr_t address,std::size_t size) noexcept {
 return address>=b.module_base&&size<=kImageSize&&address-b.module_base<=kImageSize-size;
}
[[maybe_unused]]bool SourceVector(std::uintptr_t object,std::size_t offset,std::size_t stride,
    std::vector<std::byte> &out,bool nested_chain=false) {
  std::uintptr_t data=0;std::int32_t capacity=0,count=0;
  if(!Load(object,offset,data) || !Load(object,offset+8,capacity) || !Load(object,offset+12,count) ||
      count<0 || count>64 || capacity<count || (count && !data))return false;
  const auto start=out.size(),size=static_cast<std::size_t>(count)*stride;
  if(start>65536||size>65536-start)return false;
  out.resize(start+size);if(size && !Bytes(data,out.data()+start,size))return false;
  if(nested_chain)for(std::int32_t i=0;i<count;++i)
    if(!SourceVector(data,static_cast<std::size_t>(i)*stride,0x18,out))return false;
  return true;
}
[[maybe_unused]]bool CallbackGroup(const GuiControlImage267V2 &b,std::uintptr_t widget,std::size_t group,
    std::vector<GuiControlCallbackV1> &out,bool &proven) {
  std::int32_t count=0,capacity=0;std::uintptr_t data=0;
  if(!Load(widget,group,data) || !Load(widget,group+8,capacity) || !Load(widget,group+12,count) ||
      count<0 || count>64 || capacity<count || (count && !data))return false;
  for(std::int32_t i=0;i<count;++i) {
    GuiControlCallbackV1 cb{};
    if(!Bytes(data+static_cast<std::size_t>(i)*0x48,cb.binding.data(),cb.binding.size()))return false;
    std::memcpy(&cb.object,cb.binding.data()+0x40,sizeof(cb.object));
    if(!cb.object || !Bytes(cb.object,cb.object_header.data(),cb.object_header.size()))return false;
    std::memcpy(&cb.vtable,cb.object_header.data(),sizeof(cb.vtable));
    if(!Image(b,cb.vtable,24) || !Load(cb.vtable,16,cb.invoke) || !Image(b,cb.invoke,1))return false;
    // The independently reviewed current constructor406FA30 and leaf406FFF0
    // bind an F8-byte expression source with receiver+F0 and expression+10.
    // Snapshot the whole source and
    // all bounded operand vectors, including each parameter's scope chain.
    // Other callback classes remain observable but cannot grant activation.
    if(cb.vtable==b.module_base+0x50BFE48 && cb.invoke==b.module_base+0x406FFF0) {
      cb.native_source.resize(0xF8);
      if(!Bytes(cb.object,cb.native_source.data(),0xF8) ||
          !SourceVector(cb.object,0x10,0x40,cb.native_source,true) ||
          !SourceVector(cb.object,0x28,0x18,cb.native_source) ||
          !SourceVector(cb.object,0x90,0x30,cb.native_source) ||
          !SourceVector(cb.object,0xA8,8,cb.native_source) ||
          !SourceVector(cb.object,0xC0,4,cb.native_source))return false;
    } else proven=false;
    out.push_back(cb);
  }return true;
}

[[maybe_unused]]GuiControlIdentityV1 Identity(const GuiWindowNodeV1 &n) {
 GuiControlIdentityV1 out;out.widget=n.widget;out.parent=n.parent;out.children=n.children;out.child_count=n.child_count;
 out.context=n.context;out.flags=n.flags;out.row.runtime_name=n.name;out.row.effective_visible=n.visible;out.row.enabled=n.enabled;return out;
}
[[maybe_unused]]bool Ancestor(const GuiWindowV1 &frame,std::uintptr_t ancestor,std::size_t index) {
 for(std::size_t depth=0;depth<=kGuiWindowMaxDepthV1;++depth) {
  const auto &n=frame.tree[index];if(n.widget==ancestor)return depth>0;
   if(n.parent_index<0) {
    // Selected Rite/Faith root can be nested below windows_layer. Its physical
    // outside ancestry is explicit, not an invented direct global-root edge.
    for(const auto &parent:frame.ancestors)if(parent.widget==ancestor)return true;
    return ancestor==frame.global_root;
   }
  if(static_cast<std::size_t>(n.parent_index)>=index)return false;index=static_cast<std::size_t>(n.parent_index);
 }return false;
}

// The current business requires exactly two navigation callbacks. A layer is
// observable, but it is not an open-ended input scope. Names below are current
// stock/DES assets; actual rows, ancestors and callback bytes must still come
// from this owner's fresh, bounded native capture.
[[maybe_unused]]bool NavigationRoot267V2(std::string_view root) noexcept {
 return root=="bottom"||root=="faith_window";
}
[[maybe_unused]]bool NavigationCandidate267V2(const GuiControlCaptureV1 &capture,std::size_t index) noexcept {
 if(!index||index>=capture.widgets.size())return false;
 const auto &target=capture.widgets[index];
 const bool hud=capture.root_name=="bottom";
 if((!hud&&capture.root_name!="faith_window")||
    target.row.runtime_name!=(hud?"faith_button":"edit_rite"))return false;
 const std::array<std::string_view,4> names=hud
  ?std::array<std::string_view,4>{"faith_button_container","left_edge_buttons","side_bottom_left_tabs","bottom_bar"}
  :std::array<std::string_view,4>{"actions","tab_beliefs","faith_window",{}};
 const std::size_t needed=hud?4U:3U;std::size_t matched=0;
 for(std::size_t depth=0;depth<kGuiWindowMaxDepthV1;++depth) {
  const auto parent=capture.widgets[index].parent;if(!parent)return false;
  std::size_t found=capture.widgets.size();
  for(std::size_t i=0;i<index;++i)if(capture.widgets[i].widget==parent){found=i;break;}
  if(found==capture.widgets.size())return false;
  index=found;
  if(capture.widgets[index].row.runtime_name==names[matched]&&++matched==needed)return true;
  if(!index)return false;
 }
 return false;
}
[[maybe_unused]]void RestrictNavigationRows267V2(GuiControlCaptureV1 &capture) noexcept {
 if(capture.root_name=="hud_layer"||capture.root_name=="windows_layer") {
  for(auto&widget:capture.widgets)widget.row.clickable=false;
  return; // Historical query scope is observable, never the actual OPEN_FAITH route.
 }
 if(!NavigationRoot267V2(capture.root_name))return;
 std::size_t unique=0;
 for(std::size_t i=0;i<capture.widgets.size();++i)
  if(NavigationCandidate267V2(capture,i))++unique;
 for(std::size_t i=0;i<capture.widgets.size();++i)
  capture.widgets[i].row.clickable=unique==1&&capture.widgets[i].row.clickable&&NavigationCandidate267V2(capture,i);
}

} // namespace
std::span<const ImagePin> GuiControlImagePins267V2() noexcept {return gui_control_pins_v2::kPins;}
bool VerifyGuiControlImage267V2([[maybe_unused]]std::uintptr_t image) noexcept {
#if !defined(XAR_CK3_ENABLE_121003_26785313_GUI_CONTROLS_V2) || !XAR_CK3_ENABLE_121003_26785313_GUI_CONTROLS_V2 || !XAR_CK3_ENABLE_121003_26785313_GUI_CONTROLS_V2
 return false;
#else
 if(!VerifyGuiWindowImageV1(image))return false;std::array<unsigned char,64> bytes{};
 for(const auto &pin:gui_control_pins_v2::kPins)if(pin.bytes.empty()||pin.bytes.size()>bytes.size()||pin.rva>kImageSize-pin.bytes.size()||
  !Bytes(image+pin.rva,bytes.data(),pin.bytes.size())||std::memcmp(bytes.data(),pin.bytes.data(),pin.bytes.size()))return false;
 std::uintptr_t col=0,invoke=0;
 return Load(image,0x50BFE48-8,col)&&col==image+0x58E4738&&Load(image,0x50BFE48+16,invoke)&&invoke==image+0x406FFF0;
#endif
}
GuiControlImage267V2 BindGuiControlImage267V2(std::uintptr_t image,std::string_view sha) noexcept {
 const auto core=BindReadonlyImage(image,sha);
 if(!core.exact_image_admitted||!VerifyGuiControlImage267V2(image))return {};
 return {image,true};
}
bool CaptureGuiControlWindow267V2([[maybe_unused]]const GuiControlImage267V2 &b,[[maybe_unused]]const GuiWindowV1 &frame,
 [[maybe_unused]]GuiControlCaptureV1 &out,[[maybe_unused]]std::string &reason) noexcept {
 out={};
#if !defined(XAR_CK3_ENABLE_121003_26785313_GUI_CONTROLS_V2) || !XAR_CK3_ENABLE_121003_26785313_GUI_CONTROLS_V2 || !XAR_CK3_ENABLE_121003_26785313_GUI_CONTROLS_V2
 reason="current_gui_controls_opt_in_disabled";return false;
#else
 try {
  const auto fail=[&](const char *why){out={};reason=why;return false;};
  // This internal leaf intentionally issues no provider generation, wire rows,
  // capability or effect. The owner-side caller still needs exact current Core,
  // ticket/TLS/paused guards, repeated whole captures and single-use semantics.
  if(!b.exact_image_admitted||!VerifyGuiControlImage267V2(b.module_base)||!frame.window_found||frame.tree.empty()||
    !frame.connection_generation||!frame.ticket_sequence||!frame.pump_epoch||!frame.owner_thread_id||
    frame.tree.size()>kGuiControlMaximumRowsV1||frame.tree.front().name!=frame.requested_name||
    (frame.requested_name!="faith_window"&&frame.requested_name!="rite_creation_window"&&frame.requested_name!="hud_layer"&&frame.requested_name!="windows_layer"&&!NavigationRoot267V2(frame.requested_name)))return fail("current_gui_window_source_required");
   if(!frame.ancestors.empty()) {
    if(frame.ancestors.size()>kGuiWindowMaxDepthV1||
       (frame.requested_name!="faith_window"&&frame.requested_name!="rite_creation_window"))
     return fail("current_gui_nested_scope_invalid");
    std::uintptr_t expected=frame.global_root;std::uint32_t depth=0;bool visible=frame.root.visible,enabled=frame.root.enabled;
    for(std::size_t i=0;i<frame.ancestors.size();++i) {
     const auto &parent=frame.ancestors[i];
     const auto &outer=i?frame.ancestors[i-1]:frame.root;
     if(!parent.widget||parent.parent!=expected||parent.context!=frame.context||parent.depth!=depth||
        parent.parent_index!=(i?static_cast<std::int32_t>(i-1):-1)||
         outer.child_count<=0||parent.sibling_index>=static_cast<std::uint32_t>(outer.child_count)||
        (!i&&parent.name!="middle")||(parent.visible&&!visible)||(parent.enabled&&!enabled))
      return fail("current_gui_nested_ancestor_invalid");
     expected=parent.widget;visible=parent.visible;enabled=parent.enabled;++depth;
    }
    const auto &selected=frame.tree.front();
    if(selected.parent!=expected||selected.depth!=depth||frame.ancestors.back().child_count<=0||
       selected.sibling_index>=static_cast<std::uint32_t>(frame.ancestors.back().child_count)||
       (selected.visible&&!visible)||(selected.enabled&&!enabled))return fail("current_gui_nested_root_invalid");
   }else if(frame.tree.front().parent!=frame.global_root)return fail("current_gui_root_parent_invalid");
   out.logical_owner=frame.logical_owner;out.application=frame.application;out.context=frame.context;out.global_root=frame.global_root;
  out.root=frame.tree.front().widget;out.root_name=frame.requested_name;out.connection_generation=frame.connection_generation;
  std::uintptr_t host=0,back=0;
  if(!Load(frame.context,0x3D8,host)||!Load(host,8,out.gui_owner)||out.gui_owner!=frame.context||
    !Load(frame.context,0x3E8,out.shortcut_manager)||!Load(out.shortcut_manager,0,back)||back!=frame.context)
    return fail("current_gui_host_shortcut_backref_unavailable");
  std::uintptr_t modals=0;std::int32_t capacity=0,count=0;
  if(!Load(frame.context,0x298,modals)||!Load(frame.context,0x2A0,capacity)||!Load(frame.context,0x2A4,count)||
    count<0||count>64||capacity<count||(count&&!modals))return fail("current_gui_modal_vector_unavailable");
  std::uintptr_t top_visible_modal=0;bool any_visible_modal=false;
  for(std::int32_t i=0;i<count;++i){std::uintptr_t modal=0;std::uint8_t flags=0;
   if(!Load(modals,static_cast<std::size_t>(i)*8,modal)||!modal||!Load(modal,0xD0,flags))return fail("current_gui_modal_source_unavailable");
   out.modal_receivers.push_back(modal);out.modal_flags.push_back(flags);if((flags&8)==0)any_visible_modal=true;
  }
  // Current4089380 scans for any visible modal, then passes the last modal
  // receiver to4043870. Preserve that exact engine selection conservatively.
  if(any_visible_modal)top_visible_modal=out.modal_receivers.back();
  std::size_t callback_bytes=0,callback_count=0;
  for(std::size_t i=0;i<frame.tree.size();++i){const auto &node=frame.tree[i];auto row=Identity(node);row.row.widget_id=i+1;
   if(!node.widget||node.context!=frame.context||(node.flags&1)||node.vtable<b.module_base||!Image(b,node.vtable,14*8))return fail("current_gui_node_identity_invalid");
   row.row.vtable_rva=static_cast<std::uint32_t>(node.vtable-b.module_base);
   if(i){if(node.parent_index<0||static_cast<std::size_t>(node.parent_index)>=i)return fail("current_gui_parent_order_invalid");
    row.row.child_path=out.widgets[static_cast<std::size_t>(node.parent_index)].row.child_path;
    if(!row.row.child_path.empty())row.row.child_path+='/';row.row.child_path+=std::to_string(node.sibling_index);
   }
   std::uintptr_t slot=0;if(!Load(node.vtable,13*8,slot))return fail("current_gui_input_slot_unavailable");
   if(slot==b.module_base+0x406DB30){bool proven=true;
    if(!CallbackGroup(b,node.widget,0x4B8,row.callbacks,proven)||!CallbackGroup(b,node.widget,0x3F8,row.callbacks,proven))return fail("current_gui_callback_source_unavailable");
    for(const auto&callback:row.callbacks){++callback_count;callback_bytes+=callback.native_source.size()+callback.binding.size()+callback.object_header.size();}
    if(callback_count>1024||callback_bytes>4*1024*1024)return fail("current_gui_callback_source_budget_exhausted");
    row.row.clickable=row.row.effective_visible&&row.row.enabled&&proven&&!row.callbacks.empty()&&
      (!top_visible_modal||Ancestor(frame,top_visible_modal,i));
   }
   out.widgets.push_back(std::move(row));
  }
  RestrictNavigationRows267V2(out);
  // complete is deliberately false until the real current owner wrapper also
  // supplies its Core/source identity and repeated capture. No fake Full proof.
  reason.clear();return true;
 }catch(...){out={};reason="current_gui_capture_exception";return false;}
#endif
}

namespace {
[[maybe_unused]]bool ControlsCoreEqual267V2(const ck3_1210::CoreSnapshotPrefix &a,const ck3_1210::CoreSnapshotPrefix &b) noexcept {
 return a.clock.date_raw==b.clock.date_raw&&a.clock.speed==b.clock.speed&&a.clock.paused==b.clock.paused&&
  a.local_player_id==b.local_player_id&&a.map_ready==b.map_ready&&a.has_played_character==b.has_played_character&&
  a.played_character_id==b.played_character_id&&a.played_character_alive==b.played_character_alive;
}
[[maybe_unused]]std::uint64_t ControlsWall267V2() noexcept {
 const auto n=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();
 return n<0?0:static_cast<std::uint64_t>(n);
}
[[maybe_unused]]bool ControlsUnexpired267V2(const GuiControlsContext267V2 &q) noexcept {
 const auto wall=ControlsWall267V2();return wall&&q.monotonic_deadline_ms&&wall<q.request.deadline_unix_ms&&GetTickCount64()<q.monotonic_deadline_ms;
}
[[maybe_unused]]GuiWindowV1 ControlsStructuralWindow267V2(GuiWindowV1 frame) {
 // Ticket/pump prove each invocation independently. A query handle compares
 // the exact remaining source across distinct, freshly proved owner requests.
 frame.ticket_sequence=0;frame.pump_epoch=0;return frame;
}
struct ControlsNative267V2 {
 GuiControlsContext267V2 &query;
 const ck3_11906::MainThreadExecutionStampV1 &stamp;
 GuiWindowV1 last_window;
 std::optional<GuiControlsRiteSource267V2> first_rite;
};
[[maybe_unused]]bool ReadControlsRiteSource267V2(const GuiControlImage267V2 &b,const GuiWindowV1 &w,
 std::uint32_t expected,std::int32_t actor,GuiControlsRiteSource267V2 &out) noexcept {
 out={};std::uintptr_t vt=0,back=0,root=0;GuiControlsRiteSource267V2 r;
 if(!b.exact_image_admitted||expected==0xFFFFFFFFU||w.requested_name!="rite_creation_window"||w.tree.empty()||
  !VerifyRiteDraftImageV2(b.module_base)||!Load(w.logical_owner,0,vt)||vt!=b.module_base+0x4B45FE0||
  !Load(w.logical_owner,0x10,r.gfx)||!Load(r.gfx,0,vt)||vt!=b.module_base+0x4B24748||
  !Load(r.gfx,0x20,back)||back!=w.logical_owner||!Load(r.gfx,0x88,r.handler)||
  !Load(r.handler,0,vt)||vt!=b.module_base+0x4B22578||!Load(r.handler,0x58,vt)||vt!=b.module_base+0x4B22558||
  !Load(r.handler,0x278,r.controller)||!Load(r.controller,0,vt)||vt!=b.module_base+0x4C09438||
  !Load(r.controller,0x10,vt)||vt!=b.module_base+0x4C09410||!Load(r.controller,0x98,back)||back!=w.logical_owner||
  !Load(r.controller,0xA0,back)||back!=r.handler||!Load(r.controller,0x60,root)||root!=w.tree.front().widget||
  !Load(r.controller,0xC8,r.source_rite_id)||r.source_rite_id!=expected||!Load(r.controller,0xCC,r.actor)||r.actor!=actor)return false;
 std::string reason;
 if(!ReadRiteDoctrineItems267V1(BindReadonlyImage(b.module_base,kExecutableSha256),r.controller,r.doctrine_items,reason))return false;
 out=std::move(r);return true;
}
[[maybe_unused]]bool ControlsCapture267V2(void *opaque,std::string_view root,
 ck3_1210::GuiControlCaptureV1 &out,std::string &reason) noexcept {
#if !defined(XAR_CK3_ENABLE_121003_26785313_GUI_CONTROLS_V2) || !XAR_CK3_ENABLE_121003_26785313_GUI_CONTROLS_V2
 (void)opaque;(void)root;out={};reason="current_gui_controls_opt_in_disabled";return false;
#else
 try {
  auto &native=*static_cast<ControlsNative267V2*>(opaque);auto&q=native.query;out={};ReadonlyObservation observed;
  if(!q.session||!ControlsUnexpired267V2(q)||root!=q.request.window_name||
   !ReadGuiControlsWindowOnOwner267V2(q.bindings,q.mailbox,q.ticket,native.stamp,&q,q.request,observed)||
   !observed.available||observed.offline_fixture||!observed.main_owner_observed||!observed.partial||
   !observed.gui_window||observed.raw_resources||observed.rite_draft||observed.gui_root_index||
   !ControlsCoreEqual267V2(observed.core,q.request.expected_core)) {reason=observed.unavailable_reason.starts_with("target_window_")?std::string(observed.unavailable_reason):"current_gui_core_owner_source_unavailable";return false;}
  auto normalized=ControlsStructuralWindow267V2(*observed.gui_window);
  std::optional<GuiControlsRiteSource267V2> rite;
  if(root=="rite_creation_window") {
   GuiControlsRiteSource267V2 source;
   if(!ReadControlsRiteSource267V2(BindGuiControlImage267V2(q.bindings.module_base,kExecutableSha256),
      *observed.gui_window,q.expected_source_rite_id,observed.core.played_character_id,source)) {
    reason="current_gui_rite_source_identity_unavailable";return false;
   }
   rite=source;
  }else if(q.control.activate&&!NavigationRoot267V2(root)){reason="current_faith_selected_rite_binding_not_reviewed";return false;}
  if(native.first_rite&&rite!=native.first_rite){reason="current_gui_rite_source_changed_during_capture";return false;}
  if(rite)native.first_rite=rite;
  if(q.control.activate&&(q.session->connection_generation!=q.request.connection_generation||
    !ControlsCoreEqual267V2(q.session->issued_core,observed.core)||normalized!=q.session->issued_window||rite!=q.session->issued_rite)) {
   reason="current_gui_issued_core_or_window_changed";return false;
  }
  const auto bound=BindGuiControlImage267V2(q.bindings.module_base,kExecutableSha256);
  if(!CaptureGuiControlWindow267V2(bound,*observed.gui_window,out,reason)||!ControlsUnexpired267V2(q))return false;
   // Faith is limited by RestrictNavigationRows to the one actual edit_rite
   // callback under actions/tab_beliefs. No other Faith action is admitted.
  out.played_character_id=observed.core.played_character_id;out.date_raw=observed.core.clock.date_raw;
  // Reuse the reducer's private revision slot as this connection epoch. No
  // full-snapshot/native-revision claim or caller-supplied address is created.
  out.native_revision=q.request.connection_generation;out.complete=true;
  q.verified_source_rite_id=rite?rite->source_rite_id:0xFFFFFFFFU;
  q.observed=observed.core;q.core_before_verified=true;q.witness_ticket_sequence=q.ticket.sequence;
  q.witness_pump_epoch=native.stamp.pump_epoch;q.witness_thread_id=native.stamp.thread_id;
  native.last_window=std::move(normalized);return true;
 }catch(...){out={};reason="current_gui_capture_exception";return false;}
#endif
}
[[maybe_unused]]bool ControlsNativeInvoke267V2(std::uintptr_t function,std::uintptr_t manager,
 void *text,void *pimpl,bool &handled) noexcept {
 using Native=bool(*)(void*,std::int32_t,void*,void*);
 __try {handled=reinterpret_cast<Native>(function)(reinterpret_cast<void*>(manager),0,text,pimpl);return true;}
 __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
[[maybe_unused]]bool ControlsDispatch267V2(void *opaque,const ck3_1210::GuiControlCaptureV1 &issued,
 const ck3_1210::GuiControlIdentityV1 &target,bool &handled,bool &attempted) noexcept {
 handled=false;attempted=false;
#if !defined(XAR_CK3_ENABLE_121003_26785313_GUI_CONTROLS_V2) || !XAR_CK3_ENABLE_121003_26785313_GUI_CONTROLS_V2
 (void)opaque;(void)issued;(void)target;return false;
#else
 try {
  auto &native=*static_cast<ControlsNative267V2*>(opaque);auto&q=native.query;std::string reason;ck3_1210::GuiControlCaptureV1 fresh;
  if(!q.control.activate||!target.row.clickable||!ControlsCapture267V2(opaque,q.request.window_name,fresh,reason)||fresh!=issued||
    !VerifyGuiControlImage267V2(q.bindings.module_base)||!ControlsUnexpired267V2(q))return false;
  alignas(void*)std::array<std::byte,0x20> text{};const std::uint64_t capacity=15;std::memcpy(text.data()+0x18,&capacity,8);
  alignas(void*)std::array<std::byte,0x50> pimpl{};std::memcpy(pimpl.data()+0x48,&target.widget,8);
  // The existing reducer consumes the one-use query before entering here.
  // Native mode0 performs the engine's disabled/hidden/modal/input/callback
  // dispatch path. No direct SelectDoctrine/EditRite/ScriptedGui call is made.
  attempted=true;q.result.effect_attempted=true;
  return ControlsNativeInvoke267V2(q.bindings.module_base+0x4089380,issued.shortcut_manager,text.data(),pimpl.data(),handled);
 }catch(...){return false;}
#endif
}
bool ExecuteGuiControlsInner267V2(GuiControlsContext267V2 &q,[[maybe_unused]]const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
 q.result={};q.core_before_verified=false;q.witness_ticket_sequence=0;q.witness_pump_epoch=0;q.witness_thread_id=0;q.verified_source_rite_id=0xFFFFFFFFU;
#if defined(XAR_CK3_ENABLE_121003_26785313_GUI_CONTROLS_V2) && XAR_CK3_ENABLE_121003_26785313_GUI_CONTROLS_V2
 try {
  using Status=ck3_1210::GuiControlStatusV1;
  const auto unavailable=[&](const char *reason){if(q.session&&q.control.activate)q.session->provider.valid=false;q.result.unavailable_reason=reason;return true;};
  if(!q.session||!q.mailbox||q.mailbox->offline_fixture||!q.game||!q.game->enabled()||
   !game::IsCk3_121003Core26785313Descriptor(q.game->descriptor())||
   !q.game->supports(kGuiControlsQueryCapability267V2)||
   (q.control.activate&&!q.game->supports(kGuiControlsActivateCapability267V2))||
   q.control.step!=(q.control.activate?kGuiControlsActivateStep267V2:kGuiControlsQueryStep267V2)||
   !q.request.connection_generation||q.control.root_name!=q.request.window_name||
   (q.request.window_name=="rite_creation_window"&&q.expected_source_rite_id==0xFFFFFFFFU)||
   (q.control.activate&&q.request.window_name!="rite_creation_window"&&!NavigationRoot267V2(q.request.window_name))||
   !q.request.expected_core.clock.paused||!q.request.expected_core.map_ready||!q.request.expected_core.has_played_character||
   !q.request.expected_core.played_character_alive||q.request.expected_core.played_character_id==0||q.request.expected_core.played_character_id==-1||
   q.control.deadline_unix_ms!=q.request.deadline_unix_ms)return unavailable("current_gui_request_profile_unavailable");
  if(!ControlsUnexpired267V2(q)){if(q.control.activate)q.session->provider.valid=false;q.result.status=Status::expired;return true;}
  if(q.control.activate&&(q.session->connection_generation!=q.request.connection_generation||
    !ControlsCoreEqual267V2(q.session->issued_core,q.request.expected_core))){q.session->provider.valid=false;q.result.status=Status::stale_gui;q.result.unavailable_reason="current_gui_issued_core_changed";return true;}
  q.control.native_revision=q.request.connection_generation;
  ControlsNative267V2 native{q,stamp,{},{}};ck3_1210::GuiControlResultV1 next;
  const ck3_1210::GuiControlBackendV1 backend{&native,&ControlsCapture267V2,&ControlsDispatch267V2};
  ck3_1210::ApplyGuiControlV1(q.session->provider,q.control,backend,next);
  const bool attempted=q.result.effect_attempted;q.result=std::move(next);q.result.effect_attempted=q.result.effect_attempted||attempted;
  q.result.application_main_observed=q.core_before_verified;q.result.source_abi_pins_verified=q.core_before_verified;
  // A current Core proof is never mislabeled as the old Full proof.
  q.result.full_snapshot_before_verified=false;
  if(!q.control.activate&&q.result.status==Status::available){q.session->issued_core=q.observed;q.session->issued_window=std::move(native.last_window);q.session->issued_rite=std::move(native.first_rite);q.session->connection_generation=q.request.connection_generation;}
 }catch(...){if(q.session)q.session->provider.valid=false;q.result.status=q.result.effect_attempted?ck3_1210::GuiControlStatusV1::indeterminate:ck3_1210::GuiControlStatusV1::unavailable;q.result.unavailable_reason="current_gui_executor_exception_no_retry";}
#endif
 return true;
}
} // namespace
void ArmGuiControlsDeadline267V2(GuiControlsContext267V2 &q) noexcept {
 q.monotonic_deadline_ms=0;const auto wall=ControlsWall267V2();if(!wall||q.request.deadline_unix_ms<=wall)return;
 const auto remaining=q.request.deadline_unix_ms-wall;q.monotonic_deadline_ms=GetTickCount64()+(std::min)(remaining,std::uint64_t{8000});
}
bool ExecuteGuiControlsOnOwner267V2(void *opaque,const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
 if(!opaque)return false;auto&q=*static_cast<GuiControlsContext267V2*>(opaque);
 __try {return ExecuteGuiControlsInner267V2(q,stamp);}
 __except(EXCEPTION_EXECUTE_HANDLER){if(q.session)q.session->provider.valid=false;q.result.status=q.result.effect_attempted?ck3_1210::GuiControlStatusV1::indeterminate:ck3_1210::GuiControlStatusV1::unavailable;q.result.unavailable_reason="current_gui_native_exception_no_retry";return true;}
}
} // namespace
