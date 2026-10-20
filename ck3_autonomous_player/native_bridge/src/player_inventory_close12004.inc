// Fixed exact4 InventoryView.Close leaf, private to the global owner provider.
#if defined(XAR_CK3_ENABLE_PLAYER_INVENTORY_WINDOW_OPEN_PRIVATE_V1)
namespace inventory_close12004 {
namespace current=inventory_open12004;
struct Inputs {
  current::Inputs owner{};
  bool explicit_close_enabled=false;
  void* ledger_context=nullptr;
  // A distinct close intent, never the existing open-only desired-state ledger.
  bool (*claim_close_once)(void*,std::uint64_t,const current::State&) noexcept=nullptr;
};
struct Result {
  current::State before{};
  bool once_consumed=false,invoked=false,call_returned=false,needs_recovery=false;
  bool closed_observed=false; // Only a later independent owner query may set it.
  std::string status="inventory_close_private_disabled";
};
bool LoadedCloseSlots(const ZhongguoScoreboardNativeEnvironmentV1& e,void* view) noexcept {
  if(!current::Source(e)||!view)return false;
  // Exact4 on-disk CInventoryView::Close: 23 bytes, two original class-state
  // clears followed by tail jump to the original generic Hide implementation.
  if(!PtpHexMatches12004(e.module_base+0x1624E40,
      "c681b00200000048c781d002000000000000e98962aeff"))return false;
  // Reuse existing precise generic Hide/associated-view/widget callback pins.
  // The personal-beliefs class override itself is unrelated and excluded.
  for(const auto& p:kPresentationPersonalClosePins12004) {
    if(p.rva==0x17E1130U)continue;
    const std::string_view hex=p.hex;
    for(std::size_t at=0;at<hex.size();at+=784)
      if(!PtpHexMatches12004(e.module_base+p.rva+at/2,hex.substr(at,784)))return false;
  }
  std::uintptr_t vt=0,close=0,hide=0,visible=0,flags=0;
  return Value(view,0,vt)&&vt==e.module_base+0x4577608&&
      Value(reinterpret_cast<void*>(vt),0x88,close)&&close==e.module_base+0x1624E40&&
      Value(reinterpret_cast<void*>(vt),0x20,hide)&&hide==e.module_base+0x110B0E0&&
      Value(reinterpret_cast<void*>(vt),0x38,visible)&&visible==e.module_base+0x2160380&&
      Value(reinterpret_cast<void*>(vt),0x50,flags)&&flags==e.module_base+0xAED360;
}
bool Invoke(std::uintptr_t base,void* view,bool& attempted) noexcept {
#if defined(_MSC_VER)
  __try {attempted=true;reinterpret_cast<void(__fastcall*)(void*)>(base+0x1624E40)(view);return true;}
  __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#else
  (void)base;(void)view;(void)attempted;return false;
#endif
}
Result Close(const ZhongguoScoreboardNativeEnvironmentV1& e,const Inputs& i) noexcept {
  Result out{};
#if defined(XAR_CK3_ENABLE_PLAYER_INVENTORY_WINDOW_OPEN_PRIVATE_V1)
  const auto& owner=i.owner;
  if(!i.explicit_close_enabled||!owner.enabled||!owner.loaded_gui_sources_bound||
      !owner.owner_mailbox_sequence||!i.claim_close_once)return out;
  if(!current::StockInventoryGuiSources12004(owner.hud_sha256,owner.buttons_sha256,owner.inventory_sha256)) {
    out.status="inventory_close_gui_sources_unverified";return out;
  }
  try {
    current::Admission admission{};std::string reason;
    if(!owner.read_admission||!owner.read_admission(owner.context,admission)||
        !current::AdmissionValid(admission)||!current::Current(owner,admission,true)||
        !current::Read(e,owner,admission,out.before,reason)) {
      out.status="inventory_close_current_owner_unavailable";return out;
    }
    if(!out.before.native_visible&&!out.before.effective_visible) {
      out.status="inventory_already_hidden_no_call";return out;
    }
    if(!out.before.native_visible||!out.before.effective_visible||
        out.before.subject_id!=admission.frame.actor_id||!LoadedCloseSlots(e,out.before.view)) {
      out.status="inventory_close_current_view_or_method_unverified";return out;
    }
    // Existing stock HUD census also proves current GUI context and no active
    // visible modal. This conservative reuse avoids a new generic GUI surface.
    current::Hud hud{},later_hud{};current::State later{};
    if(!current::ReadHud(e,hud)||hud.gui!=out.before.gui||
        !current::Read(e,owner,admission,later,reason)||later!=out.before||
        !current::ReadHud(e,later_hud)||later_hud!=hud||
        !LoadedCloseSlots(e,later.view)||!current::Current(owner,admission,true)) {
      out.status="inventory_close_binding_changed_before_native";return out;
    }
    if(!i.claim_close_once(i.ledger_context,owner.owner_mailbox_sequence,later)) {
      out.status="inventory_close_pending_or_once_intent_rejected";return out;
    }
    out.once_consumed=true;out.needs_recovery=true;bool attempted=false;
    out.call_returned=Invoke(e.module_base,later.view,attempted);out.invoked=attempted;
    out.status=attempted?(out.call_returned?"inventory_close_invoked_post_pending":
        "inventory_close_unknown_do_not_retry"):"inventory_close_intent_retained_no_call";
    return out;
  } catch(...) {out.status=out.once_consumed?"inventory_close_unknown_do_not_retry":"inventory_close_read_exception";return out;}
#else
  (void)e;(void)i;return out;
#endif
}
} // namespace inventory_close12004
#endif
