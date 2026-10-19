// Include after army_tooltip_v1.inc, inside navigation's private namespace.
// Exact .4 only. The shared mailbox owns owner/TLS/modal admission; this
// helper additionally rebinds the GUI, typed source and frame around its reads.
// No clicks, textbox setter, rich-text evaluator or rendered-pixels assertion.
struct PresentationTargetBinding12004 {
  IngameUiGuiOwnerBindingV1 gui{};
  void *root=nullptr,*source=nullptr;
  std::uint32_t subject=0,index=0;
  std::string kind,path;
  friend bool operator==(const PresentationTargetBinding12004 &,
                         const PresentationTargetBinding12004 &)=default;
};
bool ResolvePresentationTarget12004(const ZhongguoScoreboardNativeEnvironmentV1 &,
    const IngameUiRequestV1 &,const game::Snapshot &,std::uint64_t owner_epoch,
    const IngameUiGuiOwnerBindingV1 &,void *,PresentationTargetBinding12004 &,
    FaithPowerPresentationObservationV1 &);

void CancelPresentationTooltipPosition12004() noexcept;
bool PreparePresentationTooltipPosition12004(const ZhongguoScoreboardNativeEnvironmentV1&,const IngameUiRequestV1&,
    const game::Snapshot&,const MainThreadExecutionStampV1&,const PresentationTargetBinding12004&,void*,std::string_view,std::string&);
void ActivatePresentationTooltipPosition12004() noexcept;
bool PresentationTooltipPositionReceipt12004(std::string_view,std::string&);

constexpr std::size_t kPresentationTooltipWidgets12004=2048;
constexpr std::size_t kPresentationTooltipTexts12004=64;
constexpr std::size_t kPresentationTooltipOneText12004=16U*1024U;
constexpr std::size_t kPresentationTooltipTotalText12004=256U*1024U;
constexpr std::size_t kPresentationTooltipDepth12004=64;
bool PresentationTooltipTextFits12004(std::size_t count,std::size_t total,
                                    std::uint64_t next) noexcept {
  return count<kPresentationTooltipTexts12004 &&
      total<=kPresentationTooltipTotalText12004 && next<=kPresentationTooltipOneText12004 &&
      next<=kPresentationTooltipTotalText12004-total;
}
bool PresentationTooltipTargetKind12004(std::string_view kind) noexcept {
  return kind=="faith_core_tenet"||kind=="faith_doctrine"||kind=="personal_tenet"||
      kind=="rite_core_tenet_choice"||kind=="holding_building"||kind=="holding_building_preview"||kind=="holding_construct_conditions";
}
bool PresentationTooltipHoverPin12004(const ZhongguoScoreboardNativeEnvironmentV1 &env) {
  std::array<char,902>bytes{};std::string digest;
  return Read(reinterpret_cast<const void *>(env.module_base+ck3_12004::kUiArmyTooltipSetHover12004V1),bytes.data(),bytes.size())&&
      ArmyTooltipDigest(std::string_view(bytes.data(),bytes.size()),digest)&&
      digest=="d90611a741bebc3024b11f5d881490a68e5fe418b2bbca8243ff61c0ecee47ae";
}
struct PresentationTooltipWidget12004 {
  void *widget=nullptr,*parent=nullptr,*children=nullptr,*context=nullptr,*vtable=nullptr;
  std::int32_t child_count=0;
  bool visible=false,enabled=false;
  std::string name,path;
  friend bool operator==(const PresentationTooltipWidget12004 &,
                         const PresentationTooltipWidget12004 &)=default;
};
bool PresentationTooltipWidgetRead12004(const ZhongguoScoreboardNativeEnvironmentV1 &env,
    void *widget,void *context,std::string_view path,PresentationTooltipWidget12004 &out) {
  out={};out.widget=widget;out.path=path;ZhongguoScoreboardAccessV1 access{};
  if(!widget||!ReadGuiWidgetRuntimeV1(access,widget,out.name,out.vtable,out.visible,out.enabled)||
      !Value(widget,0xD8,out.context)||out.context!=context||!Value(widget,0xE8,out.parent)||
      !Value(widget,0xF0,out.children)||!Value(widget,0xFC,out.child_count)||
      out.child_count<0||out.child_count>4096||(out.child_count&&!out.children))return false;
  const auto vt=reinterpret_cast<std::uintptr_t>(out.vtable);
  return vt>=env.module_base&&vt-env.module_base<UiExactImageSizeV1(env.gui_abi_revision);
}
struct PresentationTooltipAncestor12004 {
  void *widget=nullptr,*parent=nullptr,*context=nullptr,*vtable=nullptr;
  bool visible=false,enabled=false;std::string name;
  friend bool operator==(const PresentationTooltipAncestor12004 &,
                         const PresentationTooltipAncestor12004 &)=default;
};
bool PresentationTooltipAncestors12004(const ZhongguoScoreboardNativeEnvironmentV1 &env,
    void *root,void *context,std::vector<PresentationTooltipAncestor12004> &out) {
  out.clear();ZhongguoScoreboardAccessV1 access{};
  for(void *widget=root;widget;) {
    if(out.size()>=kPresentationTooltipDepth12004 ||
        std::any_of(out.begin(),out.end(),[&](const auto &row){return row.widget==widget;}))return false;
    PresentationTooltipAncestor12004 row{};row.widget=widget;
    if(!ReadGuiWidgetRuntimeV1(access,widget,row.name,row.vtable,row.visible,row.enabled)||!row.visible||
        !Value(widget,0xD8,row.context)||row.context!=context||!Value(widget,0xE8,row.parent))return false;
    const auto vt=reinterpret_cast<std::uintptr_t>(row.vtable);
    if(vt<env.module_base||vt-env.module_base>=UiExactImageSizeV1(env.gui_abi_revision))return false;
    out.push_back(row);widget=row.parent;
  }
  return !out.empty();
}
struct PresentationTooltipTextCache12004 {
  void *widget=nullptr,*data=nullptr;
  std::uint64_t size=0,capacity=0;
  bool header_read=false,budget_reserved=false,bytes_read=false,utf8=false,emitted=false;
  std::string name,path,bytes,sha256;
  friend bool operator==(const PresentationTooltipTextCache12004 &,
                         const PresentationTooltipTextCache12004 &)=default;
};
// Only called after the exact CTextbox VT/COL/type/+66 getter pin has passed.
// A budget/encoding/read gap remains a gap; no other widget class is decoded.
bool PresentationTooltipCache12004(const PresentationTooltipWidget12004 &widget,
    std::size_t text_count,std::size_t total,PresentationTooltipTextCache12004 &out) {
  out={};out.widget=widget.widget;out.name=widget.name;out.path=widget.path;
  const auto address=reinterpret_cast<std::uintptr_t>(widget.widget);
  if(address>(std::numeric_limits<std::uintptr_t>::max)()-0x3B0)return false;
  const auto *header=reinterpret_cast<const void *>(address+0x390);
  out.data=const_cast<void *>(header);
  if(!Value(header,0x10,out.size)||!Value(header,0x18,out.capacity))return true;
  if(out.size>out.capacity||(out.capacity<16&&out.capacity!=15)||
      (out.capacity>=16&&(!Value(header,0,out.data)||!out.data)))return true;
  out.header_read=true;
  if(!PresentationTooltipTextFits12004(text_count,total,out.size))return true;
  out.budget_reserved=true;
  std::vector<char>bytes(static_cast<std::size_t>(out.size)+1);
  if(!Read(out.data,bytes.data(),bytes.size())||bytes.back()!=0)return true;
  out.bytes.assign(bytes.data(),static_cast<std::size_t>(out.size));out.bytes_read=true;
  out.utf8=out.bytes.find('\0')==std::string::npos&&(out.bytes.empty()||
      MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,out.bytes.data(),
          static_cast<int>(out.bytes.size()),nullptr,0)>0);
  if(out.utf8&&ArmyTooltipDigest(out.bytes,out.sha256))out.emitted=true;
  return true;
}
struct PresentationTooltipTree12004 {
  std::vector<PresentationTooltipWidget12004>widgets;
  std::vector<PresentationTooltipTextCache12004>texts;
  std::vector<PresentationTooltipAncestor12004>ancestors;
  bool complete=true;
  friend bool operator==(const PresentationTooltipTree12004 &,
                         const PresentationTooltipTree12004 &)=default;
};
bool PresentationTooltipReadTree12004(const ZhongguoScoreboardNativeEnvironmentV1 &env,
    void *root,void *context,PresentationTooltipTree12004 &out,std::string &why) {
  out={};const auto fail=[&](std::string_view reason){why=reason;return false;};
  if(!PresentationTooltipAncestors12004(env,root,context,out.ancestors))
    return fail("presentation_tooltip_visible_root_ancestors_unverified");
  struct Pending {void *widget=nullptr,*parent=nullptr;std::string path;std::size_t depth=0;};
  std::vector<Pending>pending;pending.push_back({root,nullptr,{},0});
  std::size_t sampled=0,total=0;
  for(std::size_t head=0;head<pending.size();++head) {
    const auto current=pending[head];
    if(std::any_of(out.widgets.begin(),out.widgets.end(),[&](const auto &row){return row.widget==current.widget;}))
      return fail("presentation_tooltip_child_cycle_or_duplicate");
    PresentationTooltipWidget12004 row{};
    if(!PresentationTooltipWidgetRead12004(env,current.widget,context,current.path,row)||
        (head&&row.parent!=current.parent))return fail("presentation_tooltip_widget_context_or_parent_unverified");
    out.widgets.push_back(row);
    if(row.visible) {
      if(reinterpret_cast<std::uintptr_t>(row.vtable)==env.module_base+ck3_12004::kUiArmyTooltipTextboxVtable12004V1) {
        if(!ArmyTooltipTextbox(env,row.widget))return fail("presentation_tooltip_textbox_source_pin_unverified");
        void *resolved=nullptr;
        if(!ArmyTooltipResolvePath(env,root,context,row.path,resolved,false)||resolved!=row.widget)
          return fail("presentation_tooltip_textbox_actual_path_changed");
        PresentationTooltipTextCache12004 text{};
        if(!PresentationTooltipCache12004(row,sampled,total,text))return fail("presentation_tooltip_cache_address_overflow");
        // Charge attempted bytes even if the memory/terminator/UTF-8 is bad.
        if(text.budget_reserved){++sampled;total+=static_cast<std::size_t>(text.size);}
        if(!text.emitted)out.complete=false;
        out.texts.push_back(std::move(text));
      } else {
        // Unknown classes may be decoration or own text; do not guess either.
        out.complete=false;
      }
    }
    if(current.depth+1>=kPresentationTooltipDepth12004) {
      if(row.child_count)out.complete=false;
      continue;
    }
    for(std::int32_t index=0;index<row.child_count;++index) {
      if(pending.size()>=kPresentationTooltipWidgets12004){out.complete=false;break;}
      void *child=nullptr;
      if(!Value(row.children,static_cast<std::size_t>(index)*sizeof(void *),child))
        return fail("presentation_tooltip_child_pointer_unreadable");
      if(!child)continue;
      std::string path=row.path;if(!path.empty())path+='/';path+=std::to_string(index);
      pending.push_back({child,row.widget,std::move(path),current.depth+1});
    }
  }
  std::vector<PresentationTooltipAncestor12004>later;
  if(!PresentationTooltipAncestors12004(env,root,context,later)||later!=out.ancestors)
    return fail("presentation_tooltip_root_ancestor_bookend_changed");
  why.clear();return !out.widgets.empty();
}
struct PresentationTooltipRootIdentity12004 {
  void *root=nullptr,*parent=nullptr,*context=nullptr,*vtable=nullptr;
  std::string name;
  friend bool operator==(const PresentationTooltipRootIdentity12004 &,
                         const PresentationTooltipRootIdentity12004 &)=default;
};
bool PresentationTooltipRootIdentityRead12004(const ZhongguoScoreboardNativeEnvironmentV1 &env,
    void *root,void *context,bool hidden,PresentationTooltipRootIdentity12004 &out) {
  out={};out.root=root;bool visible=false,enabled=false;ZhongguoScoreboardAccessV1 access{};
  if(!root||!ReadGuiWidgetRuntimeV1(access,root,out.name,out.vtable,visible,enabled)||visible==hidden||
      !Value(root,0xD8,out.context)||out.context!=context||!Value(root,0xE8,out.parent))return false;
  const auto vt=reinterpret_cast<std::uintptr_t>(out.vtable);
  return vt>=env.module_base&&vt-env.module_base<UiExactImageSizeV1(env.gui_abi_revision);
}
struct PresentationTooltipReceipt12004 {
  PresentationTargetBinding12004 binding{};
  void *handler=nullptr;
  std::string nonce;
  std::optional<std::string>active_tab;
  std::uint64_t action_epoch=0,connection_generation=0,native_revision=0;
  std::int32_t date_raw=0,actor=-1;
  std::uint32_t thread_id=0,window_kind=0;
  std::uintptr_t tls_context=0,jomini_state=0,game_state=0;
  bool leave=false;
  PresentationTooltipRootIdentity12004 observed_root{};
};
// One mailbox-owned current receipt. New hover/leave invalidates older nonces.
PresentationTooltipReceipt12004 presentation_tooltip_receipt12004{};
bool PresentationTooltipReceiptMatches12004(const PresentationTooltipReceipt12004 &receipt,
    const IngameUiRequestV1 &request,const game::Snapshot &snapshot,
    const MainThreadExecutionStampV1 &stamp,const PresentationTargetBinding12004 &binding,
    void *handler,const std::optional<std::string> &active_tab) noexcept {
  return ArmyTooltipNonceValid(request.presentation_receipt)&&receipt.nonce==request.presentation_receipt&&
      binding.subject==request.subject_id&&binding.index==request.presentation_index&&
      binding.kind==request.presentation_target&&PresentationTooltipTargetKind12004(binding.kind)&&
      receipt.binding==binding&&receipt.handler==handler&&receipt.active_tab==active_tab&&
      receipt.connection_generation==request.connection_generation&&receipt.native_revision==request.native_revision&&
      receipt.date_raw==snapshot.date_raw&&receipt.actor==snapshot.played_character_id&&
      receipt.window_kind==static_cast<std::uint32_t>(request.window_kind)&&receipt.thread_id==stamp.thread_id&&
      receipt.tls_context==stamp.tls_context&&receipt.jomini_state==stamp.jomini_state&&receipt.game_state==stamp.game_state&&
      receipt.action_epoch&&stamp.pump_epoch>receipt.action_epoch;
}
bool PresentationTooltipBind12004(const ZhongguoScoreboardNativeEnvironmentV1 &env,
    const IngameUiRequestV1 &request,const game::Snapshot &snapshot,std::uint64_t owner_epoch,
    const IngameUiGuiOwnerBindingV1 &gui,void *handler,
    PresentationTargetBinding12004 &binding,FaithPowerPresentationObservationV1 &observation) {
  IngameUiGuiOwnerBindingV1 current{};void *current_handler=nullptr,*source=nullptr;
  if(!owner_epoch||!ReadIngameUiGuiOwnerBindingV1(env,current)||current!=gui||!ResolveHandler(env,current_handler)||current_handler!=handler||
      !ResolvePresentationTarget12004(env,request,snapshot,owner_epoch,gui,handler,binding,observation)||
      binding.gui!=gui||!binding.root||!binding.source||binding.subject!=request.subject_id||
      binding.index!=request.presentation_index||binding.kind!=request.presentation_target||
      !PresentationTooltipTargetKind12004(binding.kind)||
      !ArmyTooltipResolvePath(env,binding.root,gui.context,binding.path,source,false)||source!=binding.source||
      !ArmyTooltipVisibleAncestors(env,binding.root,gui.context))return false;
  return true;
}
bool PresentationTooltipExecuteImpl12004(const ZhongguoScoreboardNativeEnvironmentV1 &env,
    const IngameUiRequestV1 &request,const game::Snapshot &snapshot,
    const MainThreadExecutionStampV1 &stamp,const IngameUiGuiOwnerBindingV1 &gui,
    void *handler,IngameUiResultV1 &out) {
  const auto operation=static_cast<std::uint32_t>(request.operation);
  const bool query=operation==0,leave=operation==205,hover=operation==204;
  if(!request.presentation_requested||(!hover&&!leave&&!(query&&!request.presentation_receipt.empty())))return false;
  auto &value=out.presentation_ui;value={};value.requested=true;
  bool receipt_bound=false;
  const auto reject=[&](std::string_view why) {
    value.available=false;value.status="unavailable";value.unavailable_reason=why;
    value.cache_complete=false;value.rendered_pixels_observed=false;value.cache_texts.clear();
    out.available=false;out.status=value.status;out.unavailable_reason=why;
    out.verification_pending=out.dispatch_invoked||(query&&receipt_bound);return true;
  };
  if(!env.exact_build_admitted||env.offline_fixture_function_overrides||!env.module_base||
      env.gui_abi_revision!=GuiAbiRevisionV1::crozier12004||!Actual4UiBoundV1(env)||
      !request.connection_generation||!request.native_revision||!snapshot.paused||!snapshot.map_ready||
      !snapshot.has_played_character||snapshot.played_character_id<=0||!stamp.paused||
      !stamp.pump_epoch||stamp.date_raw!=snapshot.date_raw||stamp.thread_id!=GetCurrentThreadId()||
      !gui.context||!gui.owner||!handler||!PresentationTooltipTargetKind12004(request.presentation_target)||
      !PresentationTooltipHoverPin12004(env))
    return reject("presentation_tooltip_owner_frame_or_exact_build_not_admitted");
  PresentationTargetBinding12004 binding{};FaithPowerPresentationObservationV1 first_binding_observation{};
  if(!PresentationTooltipBind12004(env,request,snapshot,stamp.pump_epoch,gui,handler,binding,first_binding_observation))
    return reject(first_binding_observation.unavailable_reason.empty()?"presentation_tooltip_typed_target_or_actual_path_unverified":first_binding_observation.unavailable_reason);
  value=first_binding_observation;value.requested=true;value.source_bound=true;
  value.subject_id=binding.subject;value.target_index=binding.index;value.target_kind=binding.kind;
  value.available=false;value.status="unavailable";value.unavailable_reason.clear();
  value.receipt_id.reset();value.action_owner_epoch.reset();value.observation_owner_epoch.reset();
  value.hover_source_matches=false;value.tooltip_stack_observed=false;value.tooltip_root_visible=false;
  value.tooltip_active_count.reset();value.tooltip_top_locked.reset();value.leave_observed=false;
  value.rendered_pixels_observed=false;value.cache_complete=false;value.cache_texts.clear();
  auto &receipt=presentation_tooltip_receipt12004;
  if(query||leave) {
    if(!PresentationTooltipReceiptMatches12004(receipt,request,snapshot,stamp,binding,handler,value.active_tab))
      return reject("presentation_tooltip_receipt_target_frame_or_later_owner_epoch_differs");
    receipt_bound=true;value.receipt_id=receipt.nonce;value.action_owner_epoch=receipt.action_epoch;
    if(leave)CancelPresentationTooltipPosition12004();
    if(query&&!receipt.leave){std::string why;if(!PresentationTooltipPositionReceipt12004(receipt.nonce,why))return reject(why);}
    value.observation_owner_epoch=stamp.pump_epoch;
  }
  if(!query) {
    if(!ReadModalNavigationAdmission(gui.context,out.modal_admission))return reject(out.modal_admission.unavailable_reason);
    PresentationTooltipRootIdentity12004 previous{};
    void *current_hover=nullptr;
    if(!Value(gui.context,0xF0,current_hover))return reject("presentation_tooltip_hover_pointer_unreadable");
    if(leave) {
      if(receipt.leave|| (current_hover&&current_hover!=binding.source))
        return reject("presentation_tooltip_leave_receipt_or_current_hover_differs");
      previous=receipt.observed_root;
      ArmyTooltipStackV1 active{};
      if(!ArmyTooltipReadStack(gui.context,active,nullptr,binding.source,true))
        return reject("presentation_tooltip_leave_current_stack_unreadable");
      if(!active.entries.empty()&&active.entries.back().source==binding.source&&active.entries.back().locked==0) {
        if(std::count_if(active.entries.begin(),active.entries.end(),[&](const auto &entry){return entry.source==binding.source;})!=1||
            !PresentationTooltipRootIdentityRead12004(env,active.entries.back().root,gui.context,false,previous))
          return reject("presentation_tooltip_leave_active_root_unverified");
      }
      if(!previous.root)return reject("presentation_tooltip_leave_previous_root_not_observed");
    }
    PresentationTargetBinding12004 later{};FaithPowerPresentationObservationV1 later_observation{};
    if(!PresentationTooltipBind12004(env,request,snapshot,stamp.pump_epoch,gui,handler,later,later_observation)||later!=binding||
        later_observation.active_tab!=value.active_tab)
      return reject("presentation_tooltip_source_changed_before_setter");
    void *final_hover=nullptr;
    if(leave&&(!Value(gui.context,0xF0,final_hover)||(final_hover&&final_hover!=binding.source)))
      return reject("presentation_tooltip_leave_hover_changed_before_setter");
    std::string nonce;if(!ArmyTooltipNewNonce(nonce))return reject("presentation_tooltip_receipt_nonce_unavailable");
    value.receipt_id=nonce;value.action_owner_epoch=stamp.pump_epoch;value.observation_owner_epoch.reset();
    value.post_window_visible.reset(); // The target bind preceded the UI event.
    PresentationTooltipReceipt12004 next{};
    next.binding=binding;next.handler=handler;next.nonce=std::move(nonce);
    next.active_tab=value.active_tab;next.action_epoch=stamp.pump_epoch;
    next.connection_generation=request.connection_generation;next.native_revision=request.native_revision;
    next.date_raw=snapshot.date_raw;next.actor=snapshot.played_character_id;next.thread_id=stamp.thread_id;
    next.window_kind=static_cast<std::uint32_t>(request.window_kind);next.tls_context=stamp.tls_context;
    next.jomini_state=stamp.jomini_state;next.game_state=stamp.game_state;
    next.leave=leave;next.observed_root=previous;
    std::string position_failure;
    if(hover&&!PreparePresentationTooltipPosition12004(env,request,snapshot,stamp,binding,handler,next.nonce,position_failure))
      return reject(position_failure.empty()?"presentation_tooltip_original_position_binding_or_geometry_unverified":position_failure);
    out.native_dispatch_attempted=true;
    if(!ArmyTooltipInvokeHover(env,gui.context,leave?nullptr:binding.source)) {
      CancelPresentationTooltipPosition12004();receipt={};return reject("presentation_tooltip_original_setter_fault_do_not_retry_if_attempted");
    }
    out.dispatch_invoked=true;out.verification_pending=true;
    receipt=std::move(next);if(hover)ActivatePresentationTooltipPosition12004();
    value.available=true;value.status="acknowledged_verification_pending";value.unavailable_reason.clear();
    out.available=true;out.dispatch_invoked=true;out.verification_pending=true;
    out.status=value.status;out.unavailable_reason.clear();return true;
  }
  ArmyTooltipStackV1 first{},second{};std::string why;
  if(!ArmyTooltipReadStack(gui.context,first,&why,binding.source,true))return reject(why);
  PresentationTooltipTree12004 tree{},later_tree{};
  PresentationTooltipRootIdentity12004 hidden{},later_hidden{},visible_root{};bool previous_rebound=false;
  if(receipt.leave) {
    if(first.hover==binding.source||std::any_of(first.entries.begin(),first.entries.end(),[&](const auto &entry){return entry.source==binding.source;}))
      return reject("presentation_tooltip_bound_source_still_active_after_leave");
    if(!receipt.observed_root.root)return reject("presentation_tooltip_previous_root_never_observed");
    // The original pool may reuse the old root for a provider tooltip whose
    // source is null. This proves retired target association, never target text.
    previous_rebound=std::any_of(first.entries.begin(),first.entries.end(),[&](const auto&e){return e.root==receipt.observed_root.root&&e.source!=binding.source;});
    if(!PresentationTooltipRootIdentityRead12004(env,receipt.observed_root.root,gui.context,!previous_rebound,hidden)||
        (!previous_rebound&&hidden!=receipt.observed_root))return reject("presentation_tooltip_previous_root_not_retired_or_rebound");
  } else {
    if(first.hover!=binding.source||first.entries.empty()||first.entries.back().source!=binding.source||
        first.entries.back().locked!=0||std::count_if(first.entries.begin(),first.entries.end(),
        [&](const auto &entry){return entry.source==binding.source;})!=1)
      return reject(std::string("presentation_")+ArmyTooltipStackJoinFailure(first,binding.source)+
          ";top_source_null="+(first.entries.empty()?std::string("unavailable"):first.entries.back().source?std::string("false"):std::string("true"))+
          ";bound_entries="+std::to_string(std::count_if(first.entries.begin(),first.entries.end(),
              [&](const auto &entry){return entry.source==binding.source;})));
    if(!PresentationTooltipRootIdentityRead12004(env,first.entries.back().root,gui.context,false,visible_root)||
        !PresentationTooltipReadTree12004(env,first.entries.back().root,gui.context,tree,why))
      return reject(why.empty()?"presentation_tooltip_visible_root_unverified":why);
  }
  PresentationTargetBinding12004 later{};FaithPowerPresentationObservationV1 later_observation{};
  if(!PresentationTooltipBind12004(env,request,snapshot,stamp.pump_epoch,gui,handler,later,later_observation)||later!=binding||
      later_observation.active_tab!=value.active_tab||!ArmyTooltipReadStack(gui.context,second,nullptr,binding.source,true)||second!=first)
    return reject("presentation_tooltip_target_or_stack_changed_during_read");
  if(receipt.leave) {
    if(!PresentationTooltipRootIdentityRead12004(env,hidden.root,gui.context,!previous_rebound,later_hidden)||later_hidden!=hidden)
      return reject("presentation_tooltip_hidden_root_bookend_changed");
    value.leave_observed=true;
  } else {
    PresentationTooltipRootIdentity12004 later_root{};
    if(!PresentationTooltipRootIdentityRead12004(env,second.entries.back().root,gui.context,false,later_root)||
        later_root!=visible_root||!PresentationTooltipReadTree12004(env,later_root.root,gui.context,later_tree,why)||tree!=later_tree)
      return reject("presentation_tooltip_tree_parent_or_cache_bookend_changed");
    // The final stack/hover read follows both complete bounded text captures.
    ArmyTooltipStackV1 final_stack{};
    PresentationTargetBinding12004 final_binding{};FaithPowerPresentationObservationV1 final_observation{};
    if(!ArmyTooltipReadStack(gui.context,final_stack,nullptr,binding.source,true)||final_stack!=first||
        !PresentationTooltipBind12004(env,request,snapshot,stamp.pump_epoch,gui,handler,final_binding,final_observation)||
        final_binding!=binding||final_observation.active_tab!=value.active_tab)
      return reject("presentation_tooltip_final_source_stack_bookend_changed");
    value.hover_source_matches=true;value.tooltip_root_visible=true;value.cache_complete=tree.complete;
    for(const auto &text:tree.texts)if(text.emitted)value.cache_texts.push_back({text.name,text.bytes,text.sha256});
    receipt.observed_root=visible_root;
  }
  value.tooltip_stack_observed=true;value.tooltip_active_count=first.count;
  if(!first.entries.empty())value.tooltip_top_locked=static_cast<std::int32_t>(first.entries.back().locked);
  value.available=true;value.status="observed";value.unavailable_reason.clear();value.rendered_pixels_observed=false;
  out.available=true;out.status=value.status;out.unavailable_reason.clear();out.verification_pending=true;return true;
}
bool PresentationTooltipExecute12004(const ZhongguoScoreboardNativeEnvironmentV1 &env,
    const IngameUiRequestV1 &request,const game::Snapshot &snapshot,
    const MainThreadExecutionStampV1 &stamp,const IngameUiGuiOwnerBindingV1 &gui,
    void *handler,IngameUiResultV1 &out) {
  try {return PresentationTooltipExecuteImpl12004(env,request,snapshot,stamp,gui,handler,out);}
  catch(...) {
    // Preserve a returned setter ACK even if a later C++ operation failed.
    if(static_cast<std::uint32_t>(request.operation)!=0)CancelPresentationTooltipPosition12004();
    auto &value=out.presentation_ui;value.requested=true;value.available=false;
    value.status="unavailable";value.unavailable_reason="presentation_tooltip_exception_do_not_retry_if_attempted";
    value.cache_complete=false;value.rendered_pixels_observed=false;value.cache_texts.clear();
    out.available=false;out.status=value.status;out.unavailable_reason=value.unavailable_reason;
    out.verification_pending=out.dispatch_invoked;return true;
  }
}
