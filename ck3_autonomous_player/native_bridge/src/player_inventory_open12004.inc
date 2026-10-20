// SOURCE CANDIDATE ONLY. Include inside ingame_ui_navigation_v1.cpp's private
// namespace AFTER faith_power_presentation_opening12004.inc. No route is added.
// The including TU must include artifact_personal_use12004.hpp and
// player_inventory_open_post12004.hpp, plus <utility>. This reuses the
// existing real memory/GUI helpers; there is no fake InventoryView constructor.
namespace inventory_open12004 {
namespace item = xar::ck3_12004::artifact_personal_use;
inline constexpr std::uint32_t kIndex = 0x5C;
inline constexpr std::uint32_t kAbsent = 0xFFFFFFFFU;

// Producer must use Current/actual adapter snapshot and IsIngameUiPausedOwner-
// StampV1, not a public request. Jomini/window outer owner stays Frame.owner;
// the GUI lookup owner below is a distinct independently resolved type.
struct Admission {
  item::Frame frame{};
  bool published_snapshot_current=false;
  bool active_event=false, pending_interaction=false;
  bool operator==(const Admission&) const = default;
};
struct State {
  bool available=false;
  Admission admission{};
  void *actor=nullptr,*handler=nullptr,*view=nullptr,*root=nullptr;
  IngameUiGuiOwnerBindingV1 gui{};
  std::uint32_t subject_id=kAbsent;
  bool native_visible=false,effective_visible=false;
  bool operator==(const State&) const = default;
};
struct Hud {
  IngameUiGuiOwnerBindingV1 gui{};
  void *root=nullptr,*button=nullptr;
  std::uintptr_t root_vtable=0,button_vtable=0,modal_vector=0;
  std::vector<std::pair<std::uintptr_t,std::uint8_t>> modal_receivers;
  bool operator==(const Hud&) const = default;
};
struct Inputs {
  bool enabled=false,loaded_gui_sources_bound=false;
  void *context=nullptr;
  bool (*read_admission)(void*,Admission&) noexcept=nullptr;
  // Must atomically consume a process-life owner-bound pending UI intent,
  // preserving unknown across revision/generation/request-ID changes. It may
  // touch only software ledger state. Missing/full/pending ledger refuses.
  bool (*claim_once)(void*,std::uint64_t,const State&) noexcept=nullptr;
  std::uint64_t owner_mailbox_sequence=0;
  // Actual stock-file hashes, read by the host from the current installed tree.
  // These do not qualify another machine's installation or a mod override.
  std::string_view hud_sha256,buttons_sha256,inventory_sha256;
};
struct Result {
  State before{};
  bool once_consumed=false,invoked=false,call_returned=false,needs_recovery=false;
  bool desired_window_observed=false; // submit ACK never sets this
  std::string status="inventory_open_private_disabled";
};

// Generated from the exact .4 on-disk executable. It compares loaded original
// code/data bytes through the existing safe Read helper; it writes no memory.
#include "player_inventory_open12004_pins.inc"

bool AdmissionValid(const Admission&a) noexcept {
  const auto&f=a.frame;
  return a.published_snapshot_current && f.revision && f.capture_epoch &&
      f.connection_generation && f.bridge_pid && f.owner && f.actor_id &&
      f.actor_id!=kAbsent && f.application_main_thread && f.native_tls_ready &&
      f.paused && f.map_ready && f.actor_alive;
}
bool Current(const Inputs&i,const Admission&expected,bool action) noexcept {
  Admission now{};
  return i.read_admission && i.read_admission(i.context,now) && now==expected &&
      AdmissionValid(now) && (!action || (!now.active_event&&!now.pending_interaction));
}
bool Source(const ZhongguoScoreboardNativeEnvironmentV1&e) noexcept {
  return e.exact_build_admitted && !e.offline_fixture_function_overrides &&
      e.gui_abi_revision==GuiAbiRevisionV1::crozier12004 && e.module_base &&
      Actual4UiBoundV1(e) && PresentationOpeningSourcePins12004(e.module_base) &&
      InventoryOpeningSourcePins12004(e.module_base);
}
bool Visible(std::uintptr_t base,void*view,bool&out) noexcept {
  out=false;
#if defined(_MSC_VER)
  __try {out=reinterpret_cast<bool(__fastcall*)(const void*)>(base+0x2160380)(view);return true;}
  __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#else
  (void)base;(void)view;return false;
#endif
}
bool One(const ZhongguoScoreboardNativeEnvironmentV1&e,const Admission&a,State&out) {
  out={};out.admission=a;
  std::uint32_t player=kAbsent;void *verified_owner=nullptr,*view_owner=nullptr,*back=nullptr;
  std::uintptr_t primary=0,secondary=0,set_data=0,matches=0,visible=0,show=0;
  if(!Source(e)||!AdmissionValid(a)||
      !Slot(e.module_base+0x54DBC00,player)||player!=a.frame.actor_id||
      !PresentationCharacter12004(e.module_base,player,out.actor)||!out.actor||
      !ResolveHandler(e,out.handler)||!out.handler||
      !ReadPresentationOuterOwner12004(e,out.handler,nullptr,verified_owner)||
      reinterpret_cast<std::uintptr_t>(verified_owner)!=a.frame.owner||
      !ReadIngameUiGuiOwnerBindingV1(e,out.gui)||
      !Value(out.handler,0x378,out.view)||!out.view||
      !Value(out.view,0,primary)||primary!=e.module_base+0x4577608||
      !Value(out.view,0x10,secondary)||secondary!=e.module_base+0x45776D8||
      !TypedObject(e.module_base,out.view,kInventoryTypeDescriptor12004,
                   UiExactImageSizeV1(e.gui_abi_revision))||
      !Value(reinterpret_cast<void*>(primary),0x90,set_data)||set_data!=e.module_base+0x1624DA0||
      !Value(reinterpret_cast<void*>(primary),0x98,matches)||matches!=e.module_base+0x1038B80||
      !Value(reinterpret_cast<void*>(primary),0x38,visible)||visible!=e.module_base+0x2160380||
      !Value(reinterpret_cast<void*>(primary),0x18,show)||show!=e.module_base+0x1624FC0||
      !Value(out.view,0x98,view_owner)||view_owner!=verified_owner||
      !Value(out.view,0xA0,back)||back!=out.handler||
      !Value(out.view,0xC8,out.subject_id)||!Value(out.view,0x60,out.root)||
      !Visible(e.module_base,out.view,out.native_visible))return false;
  if(out.subject_id!=kAbsent){void*subject=nullptr;
    if(!PresentationCharacter12004(e.module_base,out.subject_id,subject)||!subject)return false;
  }
  // The stock view constructor starts subject=FFFFFFFF; a null root is a real
  // unopened view, not a made-up usable window. Only a real root can prove post.
  if(out.root){
    ZhongguoScoreboardAccessV1 access{};void *ctx=nullptr,*lookup=nullptr,*named=nullptr,*widget=nullptr,*vt=nullptr,*root_context=nullptr;
    std::string name;bool enabled=false;
    if(!ResolveZhongguoScoreboardNativeGuiContextAndOwnerV1(e,access,ctx,lookup)||
        ctx!=out.gui.context||lookup!=out.gui.owner||
        !ResolveNamedGuiWidgetV1(e,access,"inventory_view","inventory_view",named,widget)||
        named!=out.root||widget!=out.root||
        !ReadGuiWidgetRuntimeV1(access,out.root,name,vt,out.effective_visible,enabled)||
        name!="inventory_view"||!Value(out.root,0xD8,root_context)||root_context!=ctx)return false;
  }else if(out.native_visible)return false;
  out.available=true;return true;
}
bool Read(const ZhongguoScoreboardNativeEnvironmentV1&e,const Inputs&i,
          const Admission&a,State&out,std::string&reason) noexcept {
  out={};reason.clear();
  try {State first{},second{};
    if(!Current(i,a,false)||!One(e,a,first)||!One(e,a,second)||first!=second||
        !Current(i,a,false)){reason="inventory_current_window_double_read_unavailable";return false;}
    out=first;return true;
  }catch(...){reason="inventory_window_read_exception";return false;}
}
bool ReadHud(const ZhongguoScoreboardNativeEnvironmentV1&e,Hud&out) {
  out={};ZhongguoScoreboardAccessV1 access{};void *ctx=nullptr,*lookup=nullptr,*root_vt=nullptr,*button_vt=nullptr,*actual_context=nullptr;
  IngameUiModalAdmissionV1 modal{};NamedGuiTreeInspectionV1 tree{};
  if(!ReadIngameUiGuiOwnerBindingV1(e,out.gui)||
      !ResolveZhongguoScoreboardNativeGuiContextAndOwnerV1(e,access,ctx,lookup)||
      ctx!=out.gui.context||lookup!=out.gui.owner||
      !ReadModalNavigationAdmission(ctx,modal)||!modal.receivers_verified||modal.effective_visible_count||
      !ResolveNamedGuiWidgetV1(e,access,"bottom_bar","open_inventory_tutorial_uses_this",out.root,out.button)||
      !out.root||!out.button||
      !InspectNamedGuiSubtreeV1(access,e.module_base,out.root,"bottom_bar",tree)||
      !tree.root_available||tree.truncated)return false;
  // ResolveNamedGuiWidget picks one descendant; the bounded census rejects a
  // duplicated name instead of silently substituting another current button.
  std::size_t count=0;
  for(const auto&row:tree.widgets)if(row.runtime_name=="open_inventory_tutorial_uses_this")++count;
  if(count!=1)return false;
  std::string name;bool visible=false,enabled=false;
  if(!ReadGuiWidgetRuntimeV1(access,out.root,name,root_vt,visible,enabled)||
      name!="bottom_bar"||!visible||!enabled||
      !Value(out.root,0xD8,actual_context)||actual_context!=ctx||
      !ReadGuiWidgetRuntimeV1(access,out.button,name,button_vt,visible,enabled)||
      name!="open_inventory_tutorial_uses_this"||!visible||!enabled||
      !Value(out.button,0xD8,actual_context)||actual_context!=ctx)return false;
  out.root_vtable=reinterpret_cast<std::uintptr_t>(root_vt);
  out.button_vtable=reinterpret_cast<std::uintptr_t>(button_vt);
  out.modal_vector=modal.vector_address;
  for(const auto&r:modal.receivers)out.modal_receivers.emplace_back(r.address,r.flags_d0);
  IngameUiGuiOwnerBindingV1 later{};
  return ReadIngameUiGuiOwnerBindingV1(e,later)&&later==out.gui;
}
xar::ck3_12004::PlayerInventoryOpenPost12004 Project(const State&s) noexcept {
  xar::ck3_12004::PlayerInventoryOpenPost12004 out{};const auto&f=s.admission.frame;
  out.available=s.available;out.current_admission=AdmissionValid(s.admission);
  out.revision=f.revision;out.capture_epoch=f.capture_epoch;out.generation=f.connection_generation;
  out.date_raw=f.date_raw;out.pid=f.bridge_pid;out.actor_id=f.actor_id;out.subject_id=s.subject_id;
  out.owner=f.owner;out.actor=reinterpret_cast<std::uintptr_t>(s.actor);
  out.handler=reinterpret_cast<std::uintptr_t>(s.handler);out.view=reinterpret_cast<std::uintptr_t>(s.view);
  out.root=reinterpret_cast<std::uintptr_t>(s.root);out.native_visible=s.native_visible;
  out.gui_context=reinterpret_cast<std::uintptr_t>(s.gui.context);
  out.gui_lookup_owner=reinterpret_cast<std::uintptr_t>(s.gui.owner);
  out.effective_visible=s.effective_visible;return out;
}
bool DesiredObserved(const State&before,const State&independent_after) noexcept {
  return xar::ck3_12004::PlayerInventoryOpenDesiredObserved12004(Project(before),Project(independent_after));
}
Result Open(const ZhongguoScoreboardNativeEnvironmentV1&e,const Inputs&i,
            const Admission&a) noexcept {
  Result out{};
#if !defined(XAR_CK3_ENABLE_PLAYER_INVENTORY_WINDOW_OPEN_PRIVATE_V1)
  (void)e;(void)i;(void)a;return out;
#else
  if(!i.enabled||!i.owner_mailbox_sequence||!i.claim_once){return out;}
  try {
    if(!i.loaded_gui_sources_bound||
        !StockInventoryGuiSources12004(i.hud_sha256,i.buttons_sha256,i.inventory_sha256)){
      out.status="inventory_stock_gui_sources_unbound";return out;}
    std::string reason;Hud hud{},later_hud{};
    if(!Current(i,a,true)||!Read(e,i,a,out.before,reason)||!ReadHud(e,hud)){
      out.status="inventory_owner_window_hud_or_modal_admission_rejected";return out;}
    if(out.before.subject_id==a.frame.actor_id&&out.before.root&&
        out.before.native_visible&&out.before.effective_visible){
      out.status="inventory_current_player_already_visible_no_call";return out;}
    // Use the qualified original uint32 NativeAny metadata. No artifact or
    // slot is selected, and no selected-subject field is written by this code.
    void *type=nullptr;std::uintptr_t vt=0,copy=0,dtor=0,data=0;
    if(!PresentationAnyFactory12004(e.module_base,0xA05DE0,type)||
        reinterpret_cast<std::uintptr_t>(type)!=e.module_base+0x542FE60||
        !Value(type,0,vt)||vt!=e.module_base+0x44A1938||
        !TypedObject(e.module_base,type,0x566D0B0,UiExactImageSizeV1(e.gui_abi_revision))||
        !Value(reinterpret_cast<void*>(vt),0x10,copy)||copy!=e.module_base+0x8771F0||
        !Value(reinterpret_cast<void*>(vt),0x18,dtor)||dtor!=e.module_base+0x8522C0||
        !Value(reinterpret_cast<void*>(vt),0x28,data)||data!=e.module_base+0x876E00){
      out.status="inventory_uint32_any_metadata_unavailable";return out;}
    IdAnyV1 argument{};argument.type=type;std::memcpy(argument.data.data(),&a.frame.actor_id,4);
    State later{};
    if(!Read(e,i,a,later,reason)||later!=out.before||!ReadHud(e,later_hud)||later_hud!=hud||
        hud.gui!=out.before.gui||!Current(i,a,true)){
      out.status="inventory_binding_changed_before_open";return out;}
    // Claim persists the actual last native state. It cannot call native/game
    // methods or revise the frame. Never re-enter after an unknown invocation.
    if(!i.claim_once(i.context,i.owner_mailbox_sequence,later)){
      out.status="inventory_pending_or_once_ledger_rejected";return out;}
    out.once_consumed=true;out.needs_recovery=true;
    bool attempted=false;
    out.call_returned=PresentationInvokeOpen12004(e.module_base,later.handler,kIndex,argument,attempted);
    out.invoked=attempted;
    out.status=attempted?(out.call_returned?"inventory_original_open_invoked_post_pending":
        "inventory_original_open_result_unknown_no_replay"):"inventory_original_open_not_invoked_intent_retained";
    return out;
  }catch(...){out.status=out.once_consumed?"inventory_open_unknown_no_replay":"inventory_open_read_exception";return out;}
#endif
}
} // namespace inventory_open12004
