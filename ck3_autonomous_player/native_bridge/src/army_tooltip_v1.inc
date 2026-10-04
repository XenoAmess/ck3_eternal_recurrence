// Included only inside ingame_ui_navigation_v1.cpp's private namespace.
// Exact .3 source: original hover3AA6040 and active-tooltip/text readback.
// A later application owner turn is not a GUI update or pixels proof.
constexpr std::uintptr_t kArmyTooltipSetHoverRva=0x3AA6040;
struct ArmyTooltipBindingV1 {
  IngameUiGuiOwnerBindingV1 gui{};
  void *handler=nullptr,*root=nullptr,*source=nullptr;
  std::uint32_t public_id=0,native_id=0,owner_id=0;
  std::string kind,path;
  friend bool operator==(const ArmyTooltipBindingV1 &,const ArmyTooltipBindingV1 &)=default;
};
struct ArmyTooltipReceiptV1 {
  ArmyTooltipBindingV1 binding{};
  std::string nonce;
  std::uint64_t action_epoch=0,connection_generation=0;
  std::int32_t date_raw=0;
  bool leave=false;
  void *observed_root=nullptr;
};
// Accessed only by the verified application owner thread mailbox.
ArmyTooltipReceiptV1 army_tooltip_receipt_v1{};
bool ArmyTooltipNonceValid(std::string_view value) noexcept {
  return value.size()==32 && std::all_of(value.begin(),value.end(),[](char c){return (c>='0'&&c<='9')||(c>='a'&&c<='f');});
}
bool ArmyTooltipNewNonce(std::string &out) {
  std::array<unsigned char,16> raw{};
  if(BCryptGenRandom(nullptr,raw.data(),static_cast<ULONG>(raw.size()),BCRYPT_USE_SYSTEM_PREFERRED_RNG)<0)return false;
  constexpr char hex[]="0123456789abcdef";out.clear();
  for(auto c:raw){out+=hex[c>>4];out+=hex[c&15];}return true;
}
bool ArmyTooltipDigest(std::string_view text,std::string &out) {
  BCRYPT_ALG_HANDLE algorithm=nullptr;
  if(BCryptOpenAlgorithmProvider(&algorithm,BCRYPT_SHA256_ALGORITHM,nullptr,0)<0)return false;
  std::array<unsigned char,32> digest{};
  const bool okay=BCryptHash(algorithm,nullptr,0,reinterpret_cast<PUCHAR>(const_cast<char *>(text.data())),
      static_cast<ULONG>(text.size()),digest.data(),static_cast<ULONG>(digest.size()))>=0;
  BCryptCloseAlgorithmProvider(algorithm,0);out.clear();if(!okay)return false;
  constexpr char hex[]="0123456789abcdef";for(auto c:digest){out+=hex[c>>4];out+=hex[c&15];}return true;
}
bool ArmyTooltipPath(std::string_view path,std::vector<std::uint32_t> &out) {
  out.clear();if(path.empty())return true;
  while(!path.empty()) {
    const auto slash=path.find('/');const auto part=path.substr(0,slash);std::uint32_t index=0;
    const auto parsed=std::from_chars(part.data(),part.data()+part.size(),index);
    if(part.empty()||parsed.ec!=std::errc{}||parsed.ptr!=part.data()+part.size()||index>=4096||out.size()>=64)return false;
    out.push_back(index);if(slash==std::string_view::npos)return true;path.remove_prefix(slash+1);if(path.empty())return false;
  }return false;
}
bool ArmyTooltipWidget(const ZhongguoScoreboardNativeEnvironmentV1 &env,void *widget,void *context,
    std::string &name,bool require_enabled=true) noexcept {
  ZhongguoScoreboardAccessV1 access{};void *vt=nullptr,*actual_context=nullptr;bool visible=false,enabled=false;
  if(!widget||!ReadGuiWidgetRuntimeV1(access,widget,name,vt,visible,enabled)||!visible||(require_enabled&&!enabled)||
      !Value(widget,0xD8,actual_context)||actual_context!=context)return false;
  const auto table=reinterpret_cast<std::uintptr_t>(vt);
  return table>=env.module_base&&table<env.module_base+UiExactImageSizeV1(env.gui_abi_revision);
}
// Re-resolve internally generated paths and verify each original child/backlink.
bool ArmyTooltipResolvePath(const ZhongguoScoreboardNativeEnvironmentV1 &env,void *root,
    void *context,std::string_view path,void *&widget,bool require_enabled=true) {
  std::vector<std::uint32_t> indices;if(!ArmyTooltipPath(path,indices))return false;
  std::string name;if(!ArmyTooltipWidget(env,root,context,name,require_enabled))return false;
  widget=root;
  for(auto index:indices) {
    void **children=nullptr,*child=nullptr,*parent=nullptr;std::int32_t count=0;
    if(!Value(widget,0xF0,children)||!Value(widget,0xFC,count)||count<0||count>4096||
        index>=static_cast<std::uint32_t>(count)||!children||!Value(children,std::size_t(index)*8,child)||!child||
        !Value(child,0xE8,parent)||parent!=widget||!ArmyTooltipWidget(env,child,context,name,require_enabled))return false;
    widget=child;
  }return true;
}
bool ArmyTooltipVisibleAncestors(const ZhongguoScoreboardNativeEnvironmentV1 &env,void *widget,
    void *context) {
  std::array<void *,64> seen{};std::string name;
  for(std::size_t n=0;widget&&n<seen.size();++n) {
    if(std::find(seen.begin(),seen.begin()+n,widget)!=seen.begin()+n||!ArmyTooltipWidget(env,widget,context,name,false))return false;
    seen[n]=widget;void *parent=nullptr;if(!Value(widget,0xE8,parent))return false;
    if(!parent)return true;widget=parent;
  }return false;
}
bool ArmyTooltipBind(const ZhongguoScoreboardNativeEnvironmentV1 &env,const IngameUiRequestV1 &request,
    const game::Snapshot &snapshot,const IngameUiGuiOwnerBindingV1 &gui,void *handler,ArmyTooltipBindingV1 &out) {
  out={};IngameUiResultV1 panel{};
  if(!ReadWindow(env,handler,IngameUiWindowKindV1::army,panel)||!panel.window_exists||!panel.effective_visible||!panel.enabled||
      !panel.subject_id_available||panel.current_subject_id!=request.subject_id||!panel.owner_character_id_available||
      panel.owner_character_id!=static_cast<std::uint32_t>(snapshot.played_character_id)||panel.tree.truncated||
      !panel.tree.root_available||panel.tree.scope_root_name!="army_window"||!panel.tree.widget_count||
      panel.tree.widget_count!=panel.tree.widgets.size()||panel.tree.widget_count>2048)return false;
  const std::string_view anchor=request.army_tooltip_kind=="supply_state"?"supplies":"attrition";
  const NamedGuiWidgetInspectionV1 *match=nullptr;std::size_t matches=0;
  for(const auto &row:panel.tree.widgets)if(row.runtime_name==anchor&&row.effective_visible){match=&row;++matches;}
  if(matches!=1||!match||!match->enabled)return false;
  ZhongguoScoreboardAccessV1 access{};void *root=nullptr,*root_widget=nullptr,*widget=nullptr;
  if(!ResolveNamedGuiWidgetV1(env,access,"army_window","army_window",root,root_widget)||root_widget!=root||!root)return false;
  std::vector<std::uint32_t> indices;if(!ArmyTooltipPath(match->child_path,indices)||indices.empty())return false;
  void *path_root=nullptr,*fixed_widget=nullptr;
  if(!ResolveFixedGuiChildPathV1(env,access,"army_window",indices.data(),indices.size(),path_root,fixed_widget)||
      path_root!=root||!ArmyTooltipResolvePath(env,root,gui.context,match->child_path,widget)||widget!=fixed_widget)return false;
  std::string actual;if(!ArmyTooltipWidget(env,widget,gui.context,actual)||actual!=anchor)return false;
  std::string source_path=match->child_path;
  if(request.army_tooltip_kind=="attrition") {
    const auto slash=source_path.rfind('/');source_path=slash==std::string::npos?std::string{}:source_path.substr(0,slash);
    void *parent=nullptr,*resolved_parent=nullptr;
    if(!Value(widget,0xE8,parent)||!ArmyTooltipResolvePath(env,root,gui.context,source_path,resolved_parent)||
        parent!=resolved_parent||!ArmyTooltipWidget(env,parent,gui.context,actual)||!actual.empty())return false;
    widget=parent;
  }
  // Rebind the complete native panel once more before accepting its source.
  IngameUiResultV1 later{};IngameUiGuiOwnerBindingV1 later_gui{};void *later_handler=nullptr;
  if(!ReadIngameUiGuiOwnerBindingV1(env,later_gui)||later_gui!=gui||!ResolveHandler(env,later_handler)||later_handler!=handler||
      !ReadWindow(env,handler,IngameUiWindowKindV1::army,later)||!later.effective_visible||!later.enabled||
      !later.subject_id_available||later.current_subject_id!=panel.current_subject_id||later.native_army_id!=panel.native_army_id||
      !later.owner_character_id_available||later.owner_character_id!=panel.owner_character_id)return false;
  void *later_root=nullptr,*later_widget=nullptr;
  if(!ResolveNamedGuiWidgetV1(env,access,"army_window","army_window",later_root,later_widget)||later_root!=root||later_widget!=root)return false;
  const NamedGuiWidgetInspectionV1 *later_match=nullptr;std::size_t later_matches=0;
  for(const auto &row:later.tree.widgets)if(row.runtime_name==anchor&&row.effective_visible){later_match=&row;++later_matches;}
  void *later_source=nullptr;
  if(later.tree.truncated||!later.tree.root_available||later.tree.widget_count!=later.tree.widgets.size()||
      later_matches!=1||!later_match||later_match->child_path!=match->child_path||!later_match->enabled||
      !ArmyTooltipResolvePath(env,root,gui.context,source_path,later_source)||later_source!=widget)return false;
  out={gui,handler,root,widget,panel.current_subject_id,panel.native_army_id,panel.owner_character_id,request.army_tooltip_kind,source_path};
  return true;
}
struct ArmyTooltipStackEntryV1 {
  void *root=nullptr,*source=nullptr;std::uint8_t locked=0;std::uint64_t anchor=0;
  friend bool operator==(const ArmyTooltipStackEntryV1 &,const ArmyTooltipStackEntryV1 &)=default;
};
struct ArmyTooltipStackV1 {
  void *data=nullptr,*hover=nullptr;std::int32_t capacity=0,count=0;
  std::vector<ArmyTooltipStackEntryV1> entries;
  friend bool operator==(const ArmyTooltipStackV1 &,const ArmyTooltipStackV1 &)=default;
};
bool ArmyTooltipReadStack(void *context,ArmyTooltipStackV1 &out,
    std::string *failure=nullptr,void *expected_source=nullptr) {
  out={};
  // Keep nullable failures distinct. Values below are reported only after the
  // corresponding real read succeeded; they are never presumed zero.
  const bool data_read=Value(context,0x190,out.data),capacity_read=Value(context,0x198,out.capacity),
      count_read=Value(context,0x19C,out.count),hover_read=Value(context,0xF0,out.hover);
  const auto fail=[&](std::string_view cause,std::int32_t index=-1) {
    if(failure) {
      *failure=std::string(cause)+";capacity="+(capacity_read?std::to_string(out.capacity):"unreadable")+
          ";count="+(count_read?std::to_string(out.count):"unreadable")+
          ";hover="+(!hover_read?"unreadable":!out.hover?"null":out.hover==expected_source?"bound":"different");
      if(index>=0)*failure+=";index="+std::to_string(index);
    }return false;
  };
  if(!data_read||!capacity_read||!count_read||!hover_read)return fail("tooltip_stack_header_unreadable");
  if(out.count<0||out.capacity<0)return fail("tooltip_stack_header_negative");
  if(out.count>32)return fail("tooltip_stack_count_policy_exceeded_32");
  // Original close retains capacity; only count determines our read budget.
  if(out.count>out.capacity)return fail("tooltip_stack_count_exceeds_capacity");
  if(out.count&&!out.data)return fail("tooltip_stack_data_null_with_active_entries");
  for(std::int32_t index=0;index<out.count;++index) {
    const auto offset=static_cast<std::size_t>(index)*0x20;ArmyTooltipStackEntryV1 entry{};
    if(!Value(out.data,offset,entry.root)||!Value(out.data,offset+8,entry.source)||!Value(out.data,offset+0x10,entry.locked)||
        !Value(out.data,offset+0x14,entry.anchor))return fail("tooltip_stack_entry_unreadable",index);
    if(!entry.root)return fail("tooltip_stack_entry_root_null",index);
    if(!entry.source)return fail("tooltip_stack_entry_source_null",index);
    out.entries.push_back(entry);
  }return true;
}
std::string ArmyTooltipStackJoinFailure(const ArmyTooltipStackV1 &stack,void *source) {
  return "tooltip_hover_source_top_unlocked_join_failed;capacity="+std::to_string(stack.capacity)+
      ";count="+std::to_string(stack.count)+";hover="+(!stack.hover?"null":stack.hover==source?"bound":"different")+
      ";top_source="+(stack.entries.empty()?"none":stack.entries.back().source==source?"bound":"different")+
      ";top_locked="+(stack.entries.empty()?std::string("unavailable"):std::to_string(stack.entries.back().locked));
}
bool ArmyTooltipTextbox(const ZhongguoScoreboardNativeEnvironmentV1 &env,void *widget) noexcept {
  void *vt=nullptr,*col=nullptr,*getter=nullptr;std::array<std::uint32_t,6> raw{};
  constexpr std::array<unsigned char,8> pin{0x48,0x8D,0x81,0x90,0x03,0,0,0xC3};std::array<unsigned char,8> actual{};
  const auto base=env.module_base;
  return Value(widget,0,vt)&&reinterpret_cast<std::uintptr_t>(vt)==base+0x497B828&&
      Value(vt,66*8,getter)&&reinterpret_cast<std::uintptr_t>(getter)==base+0x1042240&&
      Slot(base+0x497B820,col)&&reinterpret_cast<std::uintptr_t>(col)==base+0x50821A8&&
      Read(col,raw.data(),sizeof(raw))&&raw[0]==1&&raw[1]==0&&raw[3]==0x55BD330&&raw[5]==0x50821A8&&
      Read(reinterpret_cast<void *>(base+0x1042240),actual.data(),actual.size())&&actual==pin;
}
struct ArmyTooltipTextV1 {
  void *widget=nullptr,*data=nullptr;std::uint64_t size=0,capacity=0;
  std::string path,text;
  friend bool operator==(const ArmyTooltipTextV1 &,const ArmyTooltipTextV1 &)=default;
};
bool ArmyTooltipReadText(const ZhongguoScoreboardNativeEnvironmentV1 &env,void *root,void *context,ArmyTooltipTextV1 &out) {
  out={};if(!ArmyTooltipVisibleAncestors(env,root,context))return false;
  ZhongguoScoreboardAccessV1 access{};NamedGuiTreeInspectionV1 tree{};
  if(!InspectNamedGuiSubtreeV1(access,env.module_base,root,"army_tooltip",tree)||tree.scope_root_name!="army_tooltip"||
      !tree.root_available||tree.truncated||!tree.widget_count||tree.widget_count!=tree.widgets.size()||tree.widget_count>2048)return false;
  std::size_t count=0;const NamedGuiWidgetInspectionV1 *match=nullptr;
  for(const auto &row:tree.widgets)if(row.runtime_name=="TooltipText"&&row.effective_visible){match=&row;++count;}
  if(count!=1||!match||match->vtable_rva!=0x497B828||
      !ArmyTooltipResolvePath(env,root,context,match->child_path,out.widget,false)||!ArmyTooltipTextbox(env,out.widget))return false;
  std::string name;if(!ArmyTooltipWidget(env,out.widget,context,name,false)||name!="TooltipText")return false;
  out.path=match->child_path;const auto *header=reinterpret_cast<const unsigned char *>(out.widget)+0x390;
  out.data=const_cast<unsigned char *>(header);std::array<char,2049> bytes{};
  if(!Value(header,0x10,out.size)||!Value(header,0x18,out.capacity)||out.size>2048||out.size>out.capacity||
      (out.capacity<16&&out.capacity!=15)||(out.capacity>=16&&(!Value(header,0,out.data)||!out.data))||
      !Read(out.data,bytes.data(),static_cast<std::size_t>(out.size)+1)||bytes[out.size]!=0)return false;
  out.text.assign(bytes.data(),static_cast<std::size_t>(out.size));
  return out.text.find('\0')==std::string::npos&&(out.text.empty()||
      MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,out.text.data(),static_cast<int>(out.text.size()),nullptr,0)>0);
}
bool ArmyTooltipInvokeHover(std::uintptr_t base,void *context,void *target) noexcept {
#if defined(_MSC_VER)
  __try {reinterpret_cast<SetHoveredWidget>(base+kArmyTooltipSetHoverRva)(context,target);return true;}
  __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#else
  reinterpret_cast<SetHoveredWidget>(base+kArmyTooltipSetHoverRva)(context,target);return true;
#endif
}
void ArmyTooltipClearObservations(ArmyTooltipObservationV1 &out,std::string_view why) {
  const auto kind=out.semantic_kind;out={};out.requested=true;out.semantic_kind=kind;out.unavailable_reason=why;
}
bool ArmyTooltipExecute(const ZhongguoScoreboardNativeEnvironmentV1 &env,const IngameUiRequestV1 &request,
    const game::Snapshot &snapshot,const MainThreadExecutionStampV1 &stamp,
    const IngameUiGuiOwnerBindingV1 &gui,void *handler,IngameUiResultV1 &out) {
  auto &value=out.army_tooltip;value.requested=true;value.semantic_kind=request.army_tooltip_kind;
  const auto reject=[&](std::string_view why){ArmyTooltipClearObservations(value,why);out.available=false;out.status="unavailable";out.unavailable_reason=why;return true;};
  if(!request.connection_generation||!request.native_revision)return reject("tooltip_connection_revision_binding_missing");
  ArmyTooltipBindingV1 binding{};
  if(!ArmyTooltipBind(env,request,snapshot,gui,handler,binding))return reject("tooltip_current_army_unique_source_unverified");
  value.source_bound=true;value.source_child_path=binding.path;
  const bool query=request.operation==IngameUiOperationV1::query,leave=request.operation==IngameUiOperationV1::leave_army_tooltip;
  auto &receipt=army_tooltip_receipt_v1;
  if(query||leave) {
    if(receipt.nonce!=request.army_tooltip_receipt||receipt.binding!=binding||receipt.date_raw!=snapshot.date_raw||
        receipt.connection_generation!=request.connection_generation)return reject("tooltip_action_receipt_binding_changed");
    value.receipt_bound=true;value.receipt_id=receipt.nonce;value.action_owner_epoch=receipt.action_epoch;
    if(stamp.pump_epoch<=receipt.action_epoch)return reject("tooltip_requires_later_application_owner_epoch");
    value.later_owner_epoch_available=true;value.later_owner_epoch=stamp.pump_epoch;
  }
  if(!query) {
    void *hover=nullptr;if(!Value(gui.context,0xF0,hover))return reject("tooltip_hover_pointer_unreadable");
    if(leave&&(receipt.leave||(!hover&& !receipt.observed_root)))return reject("tooltip_leave_requires_hover_receipt_or_observed_root");
    if(leave&&hover&&hover!=binding.source)return reject("tooltip_leave_current_hover_differs_from_bound_source");
    std::string nonce;if(!ArmyTooltipNewNonce(nonce))return reject("tooltip_native_receipt_nonce_failed");
    if(!ArmyTooltipInvokeHover(env.module_base,gui.context,leave?nullptr:binding.source))return reject("tooltip_original_setter_fault");
    const auto previous=leave?receipt.observed_root:nullptr;
    receipt={binding,nonce,stamp.pump_epoch,request.connection_generation,snapshot.date_raw,leave,previous};
    value.receipt_bound=true;value.receipt_id=nonce;value.action_owner_epoch=stamp.pump_epoch;value.later_owner_epoch_available=false;
    value.status="acknowledged_verification_pending";out.available=true;out.dispatch_invoked=true;out.verification_pending=true;
    out.status=value.status;out.unavailable_reason.clear();return true;
  }
  ArmyTooltipStackV1 first{},second{};ArmyTooltipTextV1 text{},later_text{};
  std::string stack_failure;
  if(!ArmyTooltipReadStack(gui.context,first,&stack_failure,binding.source))return reject(stack_failure);
  if(receipt.leave) {
    if(first.hover==binding.source||std::any_of(first.entries.begin(),first.entries.end(),[&](const auto &entry){return entry.source==binding.source;}))
      return reject("tooltip_bound_source_still_active_after_leave");
    if(!receipt.observed_root)return reject("tooltip_leave_previous_active_root_not_observed");
    std::uint8_t flags=0;void *root_context=nullptr;
    if(!Value(receipt.observed_root,0xD0,flags)||!(flags&8)||!Value(receipt.observed_root,0xD8,root_context)||root_context!=gui.context)
      return reject("tooltip_previous_root_not_hidden_after_leave");
  } else {
    if(first.hover!=binding.source||first.entries.empty()||first.entries.back().source!=binding.source||first.entries.back().locked!=0)
      return reject(ArmyTooltipStackJoinFailure(first,binding.source));
    if(std::count_if(first.entries.begin(),first.entries.end(),[&](const auto &entry){return entry.source==binding.source;})!=1)
      return reject("tooltip_nested_or_duplicate_bound_source");
    if(!ArmyTooltipReadText(env,first.entries.back().root,gui.context,text))return reject("tooltip_unique_actual_text_cache_unavailable");
  }
  ArmyTooltipBindingV1 later_binding{};
  if(!ArmyTooltipBind(env,request,snapshot,gui,handler,later_binding)||later_binding!=binding||
      !ArmyTooltipReadStack(gui.context,second)||first!=second||
      (!receipt.leave&&(!ArmyTooltipReadText(env,second.entries.back().root,gui.context,later_text)||text!=later_text)))
    return reject("tooltip_source_root_stack_or_full_text_changed_during_read");
  if(receipt.leave) {
    std::uint8_t flags=0;void *later_root_context=nullptr;
    if(!Value(receipt.observed_root,0xD0,flags)||!(flags&8)||
        !Value(receipt.observed_root,0xD8,later_root_context)||later_root_context!=gui.context)
      return reject("tooltip_previous_root_visibility_or_context_changed");
    value.leave_observed=true;value.status="leave_observed_verification_pending";
  } else {
    if(!ArmyTooltipDigest(text.text,value.observed_text_sha256))return reject("tooltip_cache_digest_failed");
    value.cache_bytes_observed=true;value.observed_text=text.text;value.tooltip_text_child_path=text.path;
    value.active_root_available=true;value.status="cache_observed_verification_pending";receipt.observed_root=first.entries.back().root;
  }
  value.active_stack_read=true;value.active_count=first.count;
  if(first.count){value.active_top_index=first.count-1;value.active_top_locked=first.entries.back().locked;}
  value.hover_matches_source=first.hover==binding.source;
  value.unavailable_reason="gui_update_epoch_producer_not_available";
  out.available=true;out.status="observed";out.verification_pending=true;out.unavailable_reason.clear();return true;
}
void SerializeArmyTooltip(std::ostringstream &out,const ArmyTooltipObservationV1 &v,std::string_view inherited_failure_reason) {
  if(!v.requested)return;
  out<<",\"army_tooltip\":{\"schema\":\"ck3-army-tooltip-v1\",\"available\":false,\"verification_pending\":"<<v.receipt_bound
      <<",\"gui_update_epoch\":null,\"text_refresh_verified\":false,\"rendered_verified\":false"
      <<",\"semantic_kind\":\""<<JsonEscape(v.semantic_kind)<<"\",\"status\":\""<<JsonEscape(v.status)
      <<"\",\"unavailable_reason\":\""<<JsonEscape(!v.receipt_bound&&v.unavailable_reason.empty()?inherited_failure_reason:std::string_view{v.unavailable_reason})<<"\",\"receipt_id\":";
  if(v.receipt_bound)out<<'"'<<v.receipt_id<<'"';else out<<"null";
  out<<",\"action_owner_epoch\":";if(v.receipt_bound)out<<v.action_owner_epoch;else out<<"null";
  out<<",\"later_owner_epoch\":";if(v.later_owner_epoch_available)out<<v.later_owner_epoch;else out<<"null";
  out<<",\"source_bound\":"<<v.source_bound<<",\"source_child_path\":";
  if(v.source_bound)out<<'"'<<JsonEscape(v.source_child_path)<<'"';else out<<"null";
  out<<",\"hover_matches_source\":"<<v.hover_matches_source<<",\"active_stack_read\":"<<v.active_stack_read<<",\"active_count\":";
  if(v.active_stack_read)out<<v.active_count;else out<<"null";
  out<<",\"active_top_index\":";if(v.active_top_index>=0)out<<v.active_top_index;else out<<"null";
  out<<",\"active_top_locked\":";if(v.active_top_locked>=0)out<<(v.active_top_locked!=0);else out<<"null";
  out<<",\"active_root_available\":"<<v.active_root_available<<",\"tooltip_text_child_path\":";
  if(v.cache_bytes_observed)out<<'"'<<JsonEscape(v.tooltip_text_child_path)<<'"';else out<<"null";
  out<<",\"leave_observed\":"<<v.leave_observed<<",\"cache_bytes_observed\":"<<v.cache_bytes_observed<<",\"observed_cache\":";
  if(v.cache_bytes_observed)out<<"{\"text\":\""<<JsonEscape(v.observed_text)<<"\",\"utf8_bytes\":"<<v.observed_text.size()
      <<",\"sha256\":\""<<v.observed_text_sha256<<"\"}";else out<<"null";
  out<<'}';
}
