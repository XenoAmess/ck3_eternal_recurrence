// Global original GUI action, independent of typed tooltip source/text ownership.
// Included inside navigation's private namespace after presentation tooltip helpers.
struct TooltipStackSample12004 {
  ArmyTooltipStackV1 stack{};
  std::uint8_t deferred=0;
  std::vector<PresentationTooltipRootIdentity12004> roots;
  friend bool operator==(const TooltipStackSample12004&,const TooltipStackSample12004&)=default;
};
struct TooltipStackLease12004 {
  IngameUiGuiOwnerBindingV1 gui{};
  void*handler=nullptr;
  std::string nonce;
  std::uint64_t generation=0,revision=0,query_epoch=0,action_epoch=0;
  std::int32_t actor=0,date=0;
  std::uint32_t thread=0;
  std::uintptr_t tls=0,jomini=0,game=0;
  bool pending=false,cleared=false;
  TooltipStackSample12004 before{};
};
TooltipStackLease12004 tooltip_stack_lease12004{};
// Exact original registration, action wrapper, deferred producer and consumer.
struct TooltipStackPin12004 {std::uintptr_t rva;std::size_t bytes;std::string_view sha;};
constexpr TooltipStackPin12004 kTooltipStackPins12004[]={
  // Filled from the finite exact disk spans by the candidate producer.
  {0x36ea0,218,"f324c0dc8c34073d2fd51845301ba88680a150bd138b2af620126c21f82fe9b1"},
  {0xab5500,16,"52f935140f55ad31566eb32bd23206e24eaa80c1fd8f4eef90697519f7804dde"},
  {0xa8f4e0,94,"de09896714b5b6a90e687474b1897d5fc1ea1d2c2e7a4dcec0d74c5590d92b95"},
  {0x3ab26b0,365,"097760ded1cb46aa6b3e7c71a29713e3de3c6c2a41c083004401b5b43f456783"},
  {0x3aa8620,536,"5095377a4d3d1d62e30bae414e319c9828667d4f81e832fbf7c32b63029d182a"},
  {0x44b8020,17,"2dc52bacb08210b70a31a82c51d167370bd618b000bf1dd5528aa9a7a724661f"},
};
bool TooltipStackPins12004(std::uintptr_t base) {
  for(const auto&p:kTooltipStackPins12004){std::vector<char>raw(p.bytes);std::string sha;
    if(!Read(reinterpret_cast<void*>(base+p.rva),raw.data(),raw.size())||
       !ArmyTooltipDigest(std::string_view(raw.data(),raw.size()),sha)||sha!=p.sha)return false;
  }return true;
}
bool ReadTooltipStackSample12004(const ZhongguoScoreboardNativeEnvironmentV1&e,
    const IngameUiGuiOwnerBindingV1&gui,TooltipStackSample12004&out) {
  const auto capture=[&](TooltipStackSample12004&v){
    if(!ArmyTooltipReadStack(gui.context,v.stack,nullptr,nullptr,true)||
       !Value(gui.context,0x42C,v.deferred)||v.deferred>1)return false;
    for(const auto&entry:v.stack.entries){PresentationTooltipRootIdentity12004 root{};
      if(!PresentationTooltipRootIdentityRead12004(e,entry.root,gui.context,false,root))return false;
      v.roots.push_back(std::move(root));
    }return true;
  };
  TooltipStackSample12004 first{},last{};
  if(!capture(first)||!capture(last)||first!=last)return false;
  out=std::move(first);return true;
}
bool InvokeOriginalCloseAllTooltips12004(std::uintptr_t base,bool&attempted) noexcept {
  // Original registered no-argument bool wrapper; its return is only an ACK.
  attempted=true;
#if defined(_MSC_VER)
  __try {return reinterpret_cast<bool(__fastcall*)()>(base+0xAB5500)();}
  __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#else
  return reinterpret_cast<bool(*)()>(base+0xAB5500)();
#endif
}
bool ExecuteTooltipStack12004(const ZhongguoScoreboardNativeEnvironmentV1&e,
    const IngameUiRequestV1&r,const game::Snapshot&s,const MainThreadExecutionStampV1&stamp,
    const IngameUiGuiOwnerBindingV1&gui,void*handler,IngameUiResultV1&out) {
  auto&leaf=out.presentation_ui;leaf={};leaf.requested=true;leaf.tooltip_clear.emplace();
  auto&v=*leaf.tooltip_clear;
  const auto fail=[&](std::string_view why){leaf.available=false;leaf.status="unavailable";
    leaf.unavailable_reason=why;v.available=false;out.available=false;out.status=leaf.status;
    out.unavailable_reason=why;out.verification_pending=out.native_dispatch_attempted;return true;};
  if(e.gui_abi_revision!=GuiAbiRevisionV1::crozier12004||!r.connection_generation||!r.native_revision||
     stamp.tls_initialized!=1||stamp.tls_main_thread_marker!=1||!stamp.tls_context||
     !stamp.jomini_state||!stamp.game_state||!handler||!TooltipStackPins12004(e.module_base))
    return fail("tooltip_stack_exact_source_or_owner_frame_unverified");
  TooltipStackSample12004 sample{};
  if(!ReadTooltipStackSample12004(e,gui,sample))return fail("tooltip_stack_double_observation_unavailable");
  out.tree.scope_root_name="tooltip_stack";out.window_exists=true;out.effective_visible=!sample.stack.entries.empty();out.enabled=true;
  v.active_count=sample.stack.count;v.deferred=sample.deferred!=0;
  for(const auto&entry:sample.stack.entries){v.locked.push_back(entry.locked!=0);v.source_null.push_back(!entry.source);}
  auto&lease=tooltip_stack_lease12004;
  const bool same=lease.gui==gui&&lease.handler==handler&&lease.generation==r.connection_generation&&
      lease.revision==r.native_revision&&lease.actor==s.played_character_id&&lease.date==s.date_raw&&
      lease.thread==stamp.thread_id&&lease.tls==stamp.tls_context&&lease.jomini==stamp.jomini_state&&
      lease.game==stamp.game_state;
  const bool query=r.operation==IngameUiOperationV1::query;
  if(query&&r.presentation_receipt.empty()){
    if(same&&lease.pending&&!lease.cleared)return fail("tooltip_stack_previous_action_pending_do_not_resubmit");
    std::string nonce;if(!ArmyTooltipNewNonce(nonce))return fail("tooltip_stack_nonce_unavailable");
    lease={gui,handler,std::move(nonce),r.connection_generation,r.native_revision,stamp.pump_epoch,0,
      s.played_character_id,s.date_raw,stamp.thread_id,stamp.tls_context,stamp.jomini_state,stamp.game_state,false,false,sample};
  }else{
    if(!same||r.presentation_receipt!=lease.nonce||!lease.query_epoch||stamp.pump_epoch<=lease.query_epoch)
      return fail("tooltip_stack_receipt_frame_or_later_epoch_differs");
    if(query){
      if(!lease.pending||!lease.action_epoch||stamp.pump_epoch<=lease.action_epoch)
        return fail("tooltip_stack_clear_action_not_independently_observed");
      if(sample.deferred||sample.stack.count)return fail("tooltip_stack_original_clear_still_pending");
      for(const auto&old:lease.before.roots){PresentationTooltipRootIdentity12004 first{},last{};
        if(!PresentationTooltipRootIdentityRead12004(e,old.root,gui.context,true,first)||first!=old||
           !PresentationTooltipRootIdentityRead12004(e,old.root,gui.context,true,last)||last!=first)
          return fail("tooltip_stack_previous_root_not_independently_hidden");
      }
      TooltipStackSample12004 last{};
      if(!ReadTooltipStackSample12004(e,gui,last)||last!=sample)return fail("tooltip_stack_clear_postcondition_changed");
      lease.cleared=true;v.cleared=true;v.phase="cleared";
    }else{
      if(lease.pending||lease.cleared||sample.deferred||sample!=lease.before)
        return fail("tooltip_stack_action_already_consumed_or_stack_changed");
      IngameUiGuiOwnerBindingV1 again{};void*again_handler=nullptr;
      TooltipStackSample12004 last{};
      if(!ReadIngameUiGuiOwnerBindingV1(e,again)||again!=gui||!ResolveHandler(e,again_handler)||again_handler!=handler||
         !ReadTooltipStackSample12004(e,gui,last)||last!=sample||!TooltipStackPins12004(e.module_base))
        return fail("tooltip_stack_binding_changed_before_original_action");
      lease.pending=true;lease.action_epoch=stamp.pump_epoch;
      CancelPresentationTooltipPosition12004();presentation_tooltip_receipt12004={};army_tooltip_receipt_v1={};
      leaf.receipt_id=lease.nonce;leaf.action_owner_epoch=lease.action_epoch;
      v.phase="pending";v.active_count.reset();v.deferred.reset();v.locked.clear();v.source_null.clear();
      if(!InvokeOriginalCloseAllTooltips12004(e.module_base,out.native_dispatch_attempted))
        return fail("tooltip_stack_original_action_result_unknown_do_not_resubmit");
      out.dispatch_invoked=true;out.verification_pending=true;
      v.available=true;leaf.available=true;leaf.status="acknowledged_verification_pending";
      out.available=true;out.status=leaf.status;out.unavailable_reason.clear();return true;
    }
  }
  leaf.receipt_id=lease.nonce;leaf.observation_owner_epoch=stamp.pump_epoch;
  if(lease.action_epoch)leaf.action_owner_epoch=lease.action_epoch;
  v.available=true;if(v.phase.empty())v.phase="observed";
  leaf.available=true;leaf.status="observed";out.available=true;out.status=leaf.status;
  out.unavailable_reason.clear();out.verification_pending=false;return true;
}
