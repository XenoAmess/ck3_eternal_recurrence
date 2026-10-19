// Existing presentation owner route only. No arbitrary key, pointer, callback,
// command, option intent, forced OnInit, or independent runtime is introduced.
using ClericalContext12004=ck3_12004::clerical_preview::Context;
inline const char*ClericalKey12004(std::string_view target) noexcept {
  if(target=="clerical_puppet")return "make_clerical_puppet_interaction";
  if(target=="external_clerical_puppet")return "make_external_clerical_puppet_interaction";
  return nullptr;
}
enum class ClericalPhase12004{none,default_observed,open_pending,visible_observed,close_pending,hidden_observed};
inline const char*ClericalPhaseName12004(ClericalPhase12004 phase) noexcept {
  switch(phase){case ClericalPhase12004::default_observed:return "default_observed";
    case ClericalPhase12004::open_pending:return "open_pending";case ClericalPhase12004::visible_observed:return "visible_observed";
    case ClericalPhase12004::close_pending:return "close_pending";case ClericalPhase12004::hidden_observed:return "hidden_observed";
    default:return "none";}
}
struct ClericalWindow12004 {
  void*window=nullptr,*root=nullptr;
  bool visible=false,enabled=false;
  bool operator==(const ClericalWindow12004&)const=default;
};
struct ClericalLease12004 {
  std::string nonce,target;ClericalContext12004 context{};ClericalWindow12004 window{};
  IngameUiGuiOwnerBindingV1 gui{};void*handler=nullptr;
  std::uint64_t connection=0,revision=0,query_epoch=0,action_epoch=0;
  std::int32_t date=0;ClericalPhase12004 phase=ClericalPhase12004::none;
};
inline bool ClericalActionPhase12004(ClericalPhase12004 phase,bool opening) noexcept {
  return phase==(opening?ClericalPhase12004::default_observed:ClericalPhase12004::visible_observed);
}
#if XAR_ENABLE_RELIGION_UI12004_PRESENTATION
#include "faith_power_clerical_preview_pins12004.inc"
ClericalLease12004 clerical_lease12004{}; // Accessed only by the admitted owner.
bool ClericalNativePins12004(const ZhongguoScoreboardNativeEnvironmentV1&e) {
  if(!e.exact_build_admitted||e.offline_fixture_function_overrides||e.gui_abi_revision!=GuiAbiRevisionV1::crozier12004||
      !ck3_12003::ordinary_interaction::BindOrdinaryInteractionImage12004(e.module_base,e.executable_sha256).enabled)return false;
  for(const auto&p:kClericalSourcePins12004){
    for(std::size_t i=0;i<p.hex.size();i+=784)
      if(!PtpHexMatches12004(e.module_base+p.rva+i/2,p.hex.substr(i,784)))return false;
  }
  return PresentationStockFile12004(e,"common/character_interactions/00_puppet_interactions.txt",kClericalInteractionSourceSha12004)&&
      PresentationStockFile12004(e,"common/character_interactions/_character_interactions.info",kClericalInfoSourceSha12004)&&
      PresentationStockFile12004(e,"gui/interaction_confirmation.gui",kClericalGuiSourceSha12004)&&
      PresentationStockFile12004(e,"gui/interaction_templates.gui",kClericalTemplatesSourceSha12004);
}
bool ClericalFrame12004(const ZhongguoScoreboardNativeEnvironmentV1&e,const game::Snapshot&s,
    const MainThreadExecutionStampV1&stamp,const IngameUiGuiOwnerBindingV1&gui,void*handler) {
  std::uintptr_t jomini=0,game=0;std::uint32_t actor=0;std::int32_t date=0;
  std::uint8_t initialized=0,main=0,paused=0;IngameUiGuiOwnerBindingV1 again{};void*handler2=nullptr;
  return stamp.thread_id==GetCurrentThreadId()&&stamp.pump_epoch&&stamp.tls_initialized==1&&stamp.tls_main_thread_marker==1&&
      stamp.tls_context&&stamp.tls_initialized_flag_address&&s.paused&&s.map_ready&&s.has_played_character&&
      !s.has_active_event&&!s.has_pending_character_interaction&&
      Slot(e.module_base+0x5C6A520,jomini)&&jomini==stamp.jomini_state&&
      Slot(e.module_base+0x5C68C50,game)&&game==stamp.game_state&&
      Value(reinterpret_cast<void*>(jomini),kJominiPausedOffset,paused)&&paused==1&&
      Value(reinterpret_cast<void*>(game),kGameStateDateRawOffset,date)&&date==s.date_raw&&date==stamp.date_raw&&
      Slot(stamp.tls_initialized_flag_address,initialized)&&initialized==1&&
      Value(reinterpret_cast<void*>(stamp.tls_context),kMainThreadTlsMarkerOffset,main)&&main==1&&
      Slot(e.module_base+0x54DBC00,actor)&&actor==static_cast<std::uint32_t>(s.played_character_id)&&
      ReadIngameUiGuiOwnerBindingV1(e,again)&&again==gui&&ResolveHandler(e,handler2)&&handler2==handler;
}
bool ReadClericalWindow12004(const ZhongguoScoreboardNativeEnvironmentV1&e,
    const IngameUiGuiOwnerBindingV1&gui,void*handler,ClericalWindow12004&out,
    NamedGuiTreeInspectionV1*tree=nullptr) {
  out={};const auto capture=[&](ClericalWindow12004&v){
    void*owner=nullptr,*back=nullptr,*root=nullptr,*widget=nullptr,*ctx=nullptr,*vt=nullptr;
    std::uintptr_t primary=0,secondary=0;std::string name;
    if(!Value(handler,0xF0,v.window)||!v.window||!Value(v.window,0,primary)||primary!=e.module_base+0x45250E8||
        !Value(v.window,0x10,secondary)||secondary!=e.module_base+0x45250C0||
        !TypedObject(e.module_base,v.window,0x5731D88,UiExactImageSizeV1(e.gui_abi_revision))||
        !ReadPresentationOuterOwner12004(e,handler,v.window,owner)||
        !Value(v.window,0xA0,back)||back!=handler||!Value(v.window,0x60,v.root)||!v.root)return false;
    for(const auto slot:std::array<std::pair<std::size_t,std::uintptr_t>,6>{{
        {0x08,0x10E64D0},{0x18,0x10E6730},{0x20,0x10E6CC0},{0x38,0x2160380},{0x50,0x10E5C70},{0x88,0x110B2C0}}}){
      std::uintptr_t method=0;if(!Value(reinterpret_cast<void*>(primary),slot.first,method)||method!=e.module_base+slot.second)return false;
    }
    ZhongguoScoreboardAccessV1 access{};
    return ResolveNamedGuiWidgetV1(e,access,"character_interaction_confirmation_window","character_interaction_confirmation_window",root,widget)&&
        root==v.root&&widget==root&&Value(root,0xD8,ctx)&&ctx==gui.context&&
        ReadGuiWidgetRuntimeV1(access,root,name,vt,v.visible,v.enabled)&&name=="character_interaction_confirmation_window";
  };
  ClericalWindow12004 first{},last{};if(!capture(first))return false;
  if(tree){ZhongguoScoreboardAccessV1 access{};
    if(!InspectNamedGuiSubtreeV1(access,e.module_base,first.root,"character_interaction_confirmation_window",*tree)||
        tree->truncated||!tree->root_available||tree->widget_count!=tree->widgets.size()||tree->widget_count>2048)return false;}
  if(!capture(last)||last!=first)return false;out=first;return true;
}
bool InvokeClericalClose12004(std::uintptr_t base,void*window,bool&attempted) noexcept {
#if defined(_MSC_VER)
  __try{attempted=true;reinterpret_cast<void(__fastcall*)(void*)>(base+0x110B2C0)(window);return true;}
  __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#else
  (void)base;(void)window;(void)attempted;return false;
#endif
}
bool ExecuteClericalPreview12004(const ZhongguoScoreboardNativeEnvironmentV1&e,const IngameUiRequestV1&r,
    const game::Snapshot&s,const MainThreadExecutionStampV1&stamp,const IngameUiGuiOwnerBindingV1&gui,
    void*handler,IngameUiResultV1&out) {
  auto&v=out.presentation_ui;auto&cv=v.clerical_preview.emplace();
  const auto fail=[&](const char*why){v.available=false;v.source_bound=false;v.status="unavailable";v.unavailable_reason=why;
    out.available=false;out.status=v.status;out.unavailable_reason=why;return true;};
  const char*key=ClericalKey12004(r.presentation_target);
  if(!key||!r.connection_generation||!r.native_revision||!ClericalNativePins12004(e)||!ClericalFrame12004(e,s,stamp,gui,handler))return fail("clerical_preview_exact_source_owner_frame_unverified");
  namespace ordinary=ck3_12003::ordinary_interaction;namespace preview=ck3_12004::clerical_preview;
  auto bindings=ordinary::BindOrdinaryInteractionImage12004(e.module_base,e.executable_sha256);
  ck3_12003::OrdinaryInteractionRequestV1 request{};request.interaction_key=key;request.recipient_id=r.subject_id;
  request.expected_player_character_id=s.played_character_id;request.expected_revision=r.native_revision;
  request.expected_game_pid=GetCurrentProcessId();request.expected_connection_generation=r.connection_generation;
  ClericalWindow12004 window{};
  if(!ReadClericalWindow12004(e,gui,handler,window,&out.tree))return fail("clerical_preview_initialized_typed_root_unverified");
  cv.root_bound=true;cv.window_visible=window.visible;
  if(!preview::ReadDefault(bindings,request,cv.default_context))return fail("clerical_preview_default_context_not_qualified");
  preview::Context installed{};
  const bool matching=preview::ReadInstalled(bindings,request,static_cast<std::byte*>(window.window)+0xC8,installed);
  if(matching){cv.window_context=installed;out.subject_id_available=true;out.current_subject_id=installed.recipient;v.subject_id=installed.recipient;}
  if(window.visible&&(!matching||installed!=cv.default_context))return fail("clerical_preview_visible_confirmation_context_differs");
  out.window_exists=true;out.effective_visible=window.visible;out.enabled=window.enabled;
  v.post_window_visible=window.visible;v.source_bound=window.visible&&matching;v.target_kind=r.presentation_target;
  const bool query=r.operation==IngameUiOperationV1::query;
  auto&lease=clerical_lease12004;
  if(query&&r.presentation_receipt.empty()){
    if((lease.phase==ClericalPhase12004::open_pending||lease.phase==ClericalPhase12004::close_pending)&&
        lease.connection==r.connection_generation&&lease.revision==r.native_revision)
      return fail("clerical_preview_pending_ui_attempt_requires_original_receipt_query");
    std::string nonce;if(!ArmyTooltipNewNonce(nonce))return fail("clerical_preview_query_nonce_unavailable");
    lease={nonce,r.presentation_target,cv.default_context,window,gui,handler,r.connection_generation,r.native_revision,
        stamp.pump_epoch,0,s.date_raw,window.visible?ClericalPhase12004::visible_observed:ClericalPhase12004::default_observed};
  }else if(r.presentation_receipt!=lease.nonce||lease.target!=r.presentation_target||lease.context!=cv.default_context||
      lease.window.window!=window.window||lease.window.root!=window.root||lease.gui!=gui||lease.handler!=handler||
      lease.connection!=r.connection_generation||lease.revision!=r.native_revision||lease.date!=s.date_raw)
    return fail("clerical_preview_query_receipt_or_context_changed");
  if(!ClericalFrame12004(e,s,stamp,gui,handler))return fail("clerical_preview_frame_changed_after_context_query");
  v.receipt_id=lease.nonce;
  if(query){
    if(lease.phase==ClericalPhase12004::open_pending||lease.phase==ClericalPhase12004::close_pending){
      if(stamp.pump_epoch<=lease.action_epoch)return fail("clerical_preview_independent_later_query_required");
      if(lease.phase==ClericalPhase12004::open_pending){
        if(!window.visible||!matching||installed!=lease.context)return fail("clerical_preview_open_not_observed");
        lease.phase=ClericalPhase12004::visible_observed;
      }else{
        if(window.visible)return fail("clerical_preview_close_not_observed");
        lease.phase=ClericalPhase12004::hidden_observed;
      }
    }
    lease.query_epoch=stamp.pump_epoch;
    cv.phase=ClericalPhaseName12004(lease.phase);cv.available=true;v.observation_owner_epoch=stamp.pump_epoch;
    if(lease.action_epoch)v.action_owner_epoch=lease.action_epoch;
    v.preview_observed=lease.phase==ClericalPhase12004::visible_observed&&window.visible&&matching;
    v.available=true;v.status="observed";v.unavailable_reason.clear();out.available=true;out.status=v.status;out.unavailable_reason.clear();return true;
  }
  const bool opening=r.operation==IngameUiOperationV1::open_clerical_preview;
  if(!ClericalActionPhase12004(lease.phase,opening)||stamp.pump_epoch<=lease.query_epoch||
      (opening?window.visible:(!window.visible||!matching||installed!=lease.context))||
      !ReadModalNavigationAdmission(gui.context,out.modal_admission))return fail("clerical_preview_action_requires_fresh_qualified_query");
  ClericalWindow12004 last{};
  if(!ReadClericalWindow12004(e,gui,handler,last)||last!=window||!ClericalFrame12004(e,s,stamp,gui,handler))return fail("clerical_preview_binding_changed_before_ui_leaf");
  // Consumed before entering any UI leaf. Unknown results are never resubmitted.
  lease.phase=opening?ClericalPhase12004::open_pending:ClericalPhase12004::close_pending;lease.action_epoch=stamp.pump_epoch;
  if(opening){
    struct Frame{const ZhongguoScoreboardNativeEnvironmentV1*env;const game::Snapshot*snapshot;const MainThreadExecutionStampV1*stamp;
      const IngameUiGuiOwnerBindingV1*gui;void*handler;ClericalWindow12004 window;};
    Frame frame{&e,&s,&stamp,&gui,handler,window};bindings.dispatch_frame_context=&frame;
    bindings.verify_dispatch_frame=[](void*opaque)noexcept{try{const auto&f=*static_cast<Frame*>(opaque);ClericalWindow12004 current{};
      return ClericalFrame12004(*f.env,*f.snapshot,*f.stamp,*f.gui,f.handler)&&
          ReadClericalWindow12004(*f.env,*f.gui,f.handler,current)&&current==f.window&&!current.visible;
      }catch(...){return false;}};
    preview::WindowBindings leaves{window.window,handler,
      reinterpret_cast<decltype(preview::WindowBindings::copy_context)>(e.module_base+0x10E6FE0),
      reinterpret_cast<decltype(preview::WindowBindings::open_window)>(e.module_base+0xAF34A0),
      reinterpret_cast<decltype(preview::WindowBindings::refresh_window)>(e.module_base+0x10E7800)};
    preview::Attempt attempt{};preview::OpenDefault(bindings,request,lease.context,leaves,attempt);
    out.native_dispatch_attempted=attempt.invoked;out.dispatch_invoked=attempt.invoked;out.verification_pending=attempt.invoked;
    if(!attempt.invoked){lease.phase=ClericalPhase12004::default_observed;lease.action_epoch=0;}
    if(!attempt.completed)return fail(attempt.reason?attempt.reason:"clerical_preview_open_unknown_no_retry");
  }else{
    if(!InvokeClericalClose12004(e.module_base,window.window,out.native_dispatch_attempted)){
      if(!out.native_dispatch_attempted){lease.phase=ClericalPhase12004::visible_observed;lease.action_epoch=0;}
      out.verification_pending=out.native_dispatch_attempted;return fail("clerical_preview_close_unknown_no_retry");}
    out.dispatch_invoked=true;out.verification_pending=true;
  }
  cv.available=true;cv.phase=ClericalPhaseName12004(lease.phase);cv.window_visible.reset();cv.window_context.reset();
  v.action_owner_epoch=stamp.pump_epoch;v.observation_owner_epoch.reset();v.post_window_visible.reset();v.preview_observed=false;
  v.available=true;v.status="acknowledged_verification_pending";v.unavailable_reason.clear();out.available=true;out.status=v.status;out.unavailable_reason.clear();return true;
}
#else
bool ExecuteClericalPreview12004(const ZhongguoScoreboardNativeEnvironmentV1&,const IngameUiRequestV1&,
    const game::Snapshot&,const MainThreadExecutionStampV1&,const IngameUiGuiOwnerBindingV1&,void*,IngameUiResultV1&out){
  out.available=false;out.unavailable_reason="clerical_preview_presentation_disabled";
  out.presentation_ui.available=false;out.presentation_ui.status="unavailable";
  out.presentation_ui.unavailable_reason=out.unavailable_reason;return true;
}
#endif
