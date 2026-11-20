// Included in the existing exact owner reader. Only the fixed current native eligibility/quote queries below are callable.
[[maybe_unused]]bool NativeRiteQuoteV2(std::uintptr_t image,std::uintptr_t window,bool &can,std::int64_t &cost,std::int64_t &missing) noexcept {
 using Can=bool(*)(const void*,void*);using Fixed=std::int64_t*(*)(void*,std::int64_t*);
 __try {
  can=reinterpret_cast<Can>(image+0x16B9E70)(reinterpret_cast<const void*>(window),nullptr);
  if(reinterpret_cast<Fixed>(image+0x16BA500)(reinterpret_cast<void*>(window),&cost)!=&cost)return false;
  return reinterpret_cast<Fixed>(image+0x16BA620)(reinterpret_cast<void*>(window),&missing)==&missing;
 }__except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
bool ReadRiteDraftV2([[maybe_unused]]ReadonlyContext&q,[[maybe_unused]]const ck3_11906::MainThreadExecutionStampV1&stamp,
 [[maybe_unused]]const ck3_1210::CoreSnapshotPrefix&core,[[maybe_unused]]RiteDraftV2 &out) noexcept {
#if !defined(XAR_CK3_ENABLE_121003_26785313_RITE_DRAFT_V2)
 return false;
#else
 try {
  const auto valid=[&](){const auto wall=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();return q.rite_draft_request&&wall>=0&&static_cast<std::uint64_t>(wall)<q.rite_draft_request->window.deadline_unix_ms&&Owner(q,stamp);};
  if(!q.rite_draft_request||q.rite_draft_request->expected_source_rite_id==0xFFFFFFFFU||!valid()||
     !Same(q.rite_draft_request->window.expected_core,core)||q.rite_draft_request->window.window_name!="rite_creation_window"||
     !VerifyRiteDraftImageV2(q.bindings.module_base))return false;
  q.gui_window_request=q.rite_draft_request->window;RiteDraftV2 v;const auto base=q.bindings.module_base;
  if(!ReadRiteFaithWindow267V1(q,stamp,core,v.window)||!v.window.window_found||v.window.tree.empty()||
     !v.window.tree[0].visible)return false;
  std::uintptr_t vt=0,again=0,root=0;std::int32_t actor=-1;
  if(!At(v.window.logical_owner,0,vt)||vt!=base+0x4B45FE0||!At(v.window.logical_owner,0x10,v.gfx)||
     !At(v.gfx,0,vt)||vt!=base+0x4B24748||!At(v.gfx,0x20,again)||again!=v.window.logical_owner||
     !At(v.gfx,0x88,v.handler)||!At(v.handler,0,vt)||vt!=base+0x4B22578||!At(v.handler,0x58,vt)||vt!=base+0x4B22558||
     !At(v.handler,0x278,v.controller)||!At(v.controller,0,vt)||vt!=base+0x4C09438||!At(v.controller,0x10,vt)||vt!=base+0x4C09410||
     !At(v.controller,0x98,again)||again!=v.window.logical_owner||!At(v.controller,0xA0,again)||again!=v.handler||
     !At(v.controller,0x60,root)||root!=v.window.tree[0].widget||!At(v.controller,0xCC,actor)||actor!=core.played_character_id||
     !At(v.controller,0xC8,v.source_rite_id)||v.source_rite_id!=q.rite_draft_request->expected_source_rite_id||!valid())return false;
#if defined(XAR_CK3_26785313_OFFLINE_FIXTURE)
  if(q.bindings.offline_fixture) {
   if(!q.rite_draft_fixture||!q.rite_draft_fixture->read||!q.rite_draft_fixture->read(q.rite_draft_fixture->context,v.controller,v.can_edit_rite_native,v.piety_cost_raw,v.piety_missing_raw))return false;
  }else
#endif
  if(!NativeRiteQuoteV2(base,v.controller,v.can_edit_rite_native,v.piety_cost_raw,v.piety_missing_raw))return false;
  // Native CanEdit evaluates the real full validator and name-conflict gate. It is not final GUI/Observer/action permission.
  // Quote calls are logical reads; no callback, draft setter, command or confirmation is invoked here.
  if(!valid()||!At(v.window.logical_owner,0x10,again)||again!=v.gfx||!At(v.gfx,0x88,again)||again!=v.handler||
     !At(v.handler,0x278,again)||again!=v.controller||!At(v.controller,0xCC,actor)||actor!=core.played_character_id||
     !At(v.controller,0xC8,v.source_rite_id)||v.source_rite_id!=q.rite_draft_request->expected_source_rite_id||
     !At(v.controller,0x60,again)||again!=root)return false;
  out=std::move(v);return true;
 }catch(...){return false;}
#endif
}
