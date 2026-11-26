#if defined(XAR_CK3_ENABLE_121003_26785313_LYD_V1) && XAR_CK3_ENABLE_121003_26785313_LYD_V1
namespace {
bool LydDecisionSceneSample267V1(ReadonlyContext&q,const ck3_11906::MainThreadExecutionStampV1&s,const OwnerInvocationV1&i,std::uint64_t wall,std::uint64_t mono,LydFrame267V1&out,std::string&reason){
 const auto valid=[&]{const auto n=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();return wall&&mono&&n>0&&static_cast<std::uint64_t>(n)<wall&&GetTickCount64()<mono&&Owner(q,s,i);};const auto fail=[&](const char*why){reason=why;return false;};if(!valid()||!Read(q,s,i)||!q.observation.available||q.observation.offline_fixture||!q.observation.main_owner_observed)return fail("curated_actual_paused_living_core_unavailable");out.core=q.observation.core;out.facts_verified=true;auto&e=out.scene;e.kind=LydKind267V1::decisions;e.wall_deadline=wall;const auto image=q.bindings.module_base;std::uintptr_t app=0,first=0,vt=0,back=0;
 if(!At(image,kJominiStateSlotRva,e.jomini)||!At(e.jomini,0,vt)||vt!=image+0x4B45FE0||!At(e.jomini,0x10,e.gfx)||!At(e.gfx,0,vt)||vt!=image+0x4B24748||!At(e.gfx,0x20,back)||back!=e.jomini||!At(e.gfx,0x88,e.handler)||!At(e.handler,0,vt)||vt!=image+0x4B22578||!At(e.handler,0x58,vt)||vt!=image+0x4B22558||!At(e.jomini,0x18,app)||!At(app,0,vt)||vt!=image+kGuiRootApplicationVtableRvaV1||!At(app,0x1B8,first)||!At(first,0x58,e.context)||!e.context||!At(e.context,0xD0,e.global))return fail("curated_actual_application_handler_context_unavailable");
 e.application=app;GuiWindowNodeV1 root,windows,middle,hud,list,detail;std::unordered_set<std::uintptr_t>seen{e.global};std::size_t names=0;if(!GuiWindowNodeReadV1(image,e.global,e.context,0,root))return fail("curated_actual_global_widget_unavailable");out.witness.push_back(root);
 const auto children=[&](const GuiWindowNodeV1&parent,std::string_view wanted,GuiWindowNodeV1&found){for(std::int32_t n=0;n<parent.child_count;++n){std::uintptr_t p=0;GuiWindowNodeV1 row;if(!valid()||out.witness.size()>=4096||!At(parent.children,static_cast<std::size_t>(n)*8,p)||!seen.insert(p).second||!GuiWindowNodeReadV1(image,p,e.context,parent.widget,row))return false;row.sibling_index=static_cast<std::uint32_t>(n);row.visible=row.visible&&parent.visible;row.enabled=row.enabled&&parent.enabled;names+=row.name.size();if(names>131072)return false;out.witness.push_back(row);if(row.name==wanted){if(found.widget)return false;found=row;}}return true;};
 if(!children(root,"windows_layer",windows))return fail("curated_actual_global_layer_census_unavailable");for(const auto&n:out.witness){if(n.name=="middle"){if(middle.widget)return fail("curated_middle_layer_ambiguous");middle=n;}if(n.name=="hud_layer"){if(hud.widget)return fail("curated_hud_layer_ambiguous");hud=n;}}
 if(!windows.widget||!middle.widget||!hud.widget)return fail("curated_fixed_layers_missing");if(!children(windows,"decisions_view",list)||!children(middle,"decisiondetail_view",detail))return fail("curated_named_list_or_detail_census_unavailable");
 e.list_root=list.widget;e.list_visible=list.visible;e.list_enabled=list.enabled;e.detail_root=detail.widget;e.detail_visible=detail.visible;e.detail_enabled=detail.enabled;
 // Existing actual visible model/detail is independent of unrelated HUD descendants.
 if(!list.visible&&!detail.visible)e.hud.push_back(hud);for(std::size_t cursor=0;cursor<e.hud.size();++cursor){const auto parent=e.hud[cursor];if(parent.depth>=32)return fail("curated_hud_navigation_depth_exhausted");for(std::int32_t n=0;n<parent.child_count;++n){std::uintptr_t p=0;GuiWindowNodeV1 row;if(!valid()||out.witness.size()>=4096||!At(parent.children,static_cast<std::size_t>(n)*8,p)||!seen.insert(p).second||!GuiWindowNodeReadV1(image,p,e.context,parent.widget,row))return fail("curated_hud_navigation_source_unavailable");row.sibling_index=static_cast<std::uint32_t>(n);row.depth=parent.depth+1;row.visible=row.visible&&parent.visible;row.enabled=row.enabled&&parent.enabled;names+=row.name.size();if(names>131072)return fail("curated_hud_navigation_name_budget");e.hud.push_back(row);out.witness.push_back(row);}}
 return valid();
}
}
namespace {
template<class Valid>
bool LydGuiSceneSample267V1(std::uintptr_t image,LydFrame267V1 &out,std::string &reason,
 const Valid &valid,bool full111_ordinary_only=false){
 auto &e=out.scene;const auto kind=e.kind;
 const auto fail=[&](const char*why){reason=why;return false;};
 std::uintptr_t vt=0,first=0,back=0;
 if(!At(image,kJominiStateSlotRva,e.jomini)||!At(e.jomini,0,vt)||vt!=image+0x4B45FE0||!At(e.jomini,0x10,e.gfx)||!At(e.gfx,0,vt)||vt!=image+0x4B24748||!At(e.gfx,0x20,back)||back!=e.jomini||!At(e.gfx,0x88,e.handler)||!At(e.handler,0,vt)||vt!=image+0x4B22578||!At(e.handler,0x58,vt)||vt!=image+0x4B22558||!At(e.jomini,0x18,e.application)||!At(e.application,0,vt)||vt!=image+kGuiRootApplicationVtableRvaV1||!At(e.application,0x1B8,first)||!At(first,0x58,e.context)||!e.context||!At(e.context,0xD0,e.global))return fail("lyd_actual_handler_application_context_unavailable");
 GuiWindowNodeV1 root,events,middle,confirmation,personal;std::unordered_set<std::uintptr_t>seen{e.global};std::size_t names=0;if(!GuiWindowNodeReadV1(image,e.global,e.context,0,root))return fail("lyd_actual_global_widget_unavailable");out.witness.push_back(root);
 const auto children=[&](const GuiWindowNodeV1&parent,std::string_view wanted,GuiWindowNodeV1&found,std::vector<LydNamedRoot267V1>*many=nullptr){for(std::int32_t n=0;n<parent.child_count;++n){std::uintptr_t p=0;GuiWindowNodeV1 row;if(!valid()||out.witness.size()>=4096||!At(parent.children,static_cast<std::size_t>(n)*8,p)||!seen.insert(p).second||!GuiWindowNodeReadV1(image,p,e.context,parent.widget,row))return false;row.sibling_index=static_cast<std::uint32_t>(n);row.visible=row.visible&&parent.visible;row.enabled=row.enabled&&parent.enabled;names+=row.name.size();if(names>131072)return false;out.witness.push_back(row);if(many&&(wanted.empty()||row.name==wanted))many->push_back({row.widget,row.visible,row.enabled});else if(row.name==wanted){if(found.widget)return false;found=row;}}return true;};
 if(!children(root,kind==LydKind267V1::events?"events":"middle",kind==LydKind267V1::events?events:middle))return fail("lyd_complete_root_layer_census_unavailable");
 if(kind==LydKind267V1::events){
  if(!events.widget)return fail("lyd_actual_events_layer_missing");
  e.events_layer=events.widget;GuiWindowNodeV1 unused;
  if(!children(events,"character_event",unused,&e.event_roots)||e.event_roots.size()>32)
   return fail("lyd_complete_character_event_root_census_invalid");
  if(full111_ordinary_only){
   if(e.event_roots.size()!=1||!e.event_roots.front().visible)
    return fail("current111_ordinary_visible_event_not_single");
   GuiWindowNodeV1 top,fullscreen;
   for(const auto &node:out.witness){
    if(node.parent==events.widget&&node.visible&&node.name!="character_event")
     return fail("current111_ordinary_event_mixed_layer");
    if(node.parent==root.widget&&node.name=="top"){
     if(top.widget)return fail("current111_ordinary_event_top_layer_ambiguous");
     top=node;
    }
   }
   if(!top.widget||!children(top,"fullscreen_event",fullscreen)||fullscreen.visible)
    return fail("current111_ordinary_event_fullscreen_exclusion_unavailable");
  }
 }
 else{
  if(!middle.widget)return fail("lyd_actual_middle_layer_missing");for(const auto&r:out.witness)if(r.name=="confirmation"){if(confirmation.widget)return fail("lyd_confirmation_layer_ambiguous");confirmation=r;}
  if(!confirmation.widget)return fail("lyd_confirmation_layer_missing");e.confirmation_layer=confirmation.widget;GuiWindowNodeV1 unused;if(!children(middle,"window_personal_beliefs",personal)||!children(confirmation,"",unused,&e.confirmation_roots)||e.confirmation_roots.size()>128)return fail("lyd_personal_or_confirmation_root_census_unavailable");e.personal_root=personal.widget;e.personal_visible=personal.visible;e.personal_enabled=personal.enabled;
 }
 return valid();
}
bool LydSceneSample267V1(ReadonlyContext&q,const ck3_11906::MainThreadExecutionStampV1&s,const OwnerInvocationV1&i,LydKind267V1 kind,std::uint64_t wall,std::uint64_t mono,LydFrame267V1&out,std::string&reason){
 if(kind==LydKind267V1::decisions)return LydDecisionSceneSample267V1(q,s,i,wall,mono,out,reason);
 const auto valid=[&]{const auto t=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();return wall&&mono&&t>0&&static_cast<std::uint64_t>(t)<wall&&GetTickCount64()<mono&&Owner(q,s,i);};
 if(!valid()||!Read(q,s,i)||!q.observation.available||q.observation.offline_fixture||!q.observation.main_owner_observed){reason="lyd_actual_paused_living_core_unavailable";return false;}
 out.core=q.observation.core;out.facts_verified=true;auto&e=out.scene;e.kind=kind;e.wall_deadline=wall;
 if(kind==LydKind267V1::readback){
  if(!q.observation.raw_resources){reason="lyd_actual_resource_snapshot_unavailable";return false;}
  e.resources=q.observation.raw_resources;return valid();
 }
 return LydGuiSceneSample267V1(q.bindings.module_base,out,reason,valid);
}
}
bool ReadLydFrameOnOwner267V1(const ReadonlyBindings&b,ck3_11906::MainThreadQueryMailboxV1*m,const ck3_11906::MainThreadQueryTicketV1&t,const ck3_11906::MainThreadExecutionStampV1&s,void*context,LydKind267V1 kind,std::uint64_t wall,std::uint64_t mono,LydFrame267V1&out,std::string&reason)noexcept{
 out={};reason="lyd_original_main_owner_unavailable";try{if(!m||m->offline_fixture||!context||m->permitted_executor_quinquevigintary!=&ExecuteLydOnOwner267V1)return false;ReadonlyContext q;q.bindings=b;q.mailbox=m;q.ticket=t;q.mode=kind==LydKind267V1::readback?ReadonlyModeV1::core_and_raw_resources:ReadonlyModeV1::core_only;const OwnerInvocationV1 i{&ExecuteLydOnOwner267V1,context};LydFrame267V1 a,z;
 if(!LydSceneSample267V1(q,s,i,kind,wall,mono,a,reason)){if(a.facts_verified){out.core=a.core;out.facts_verified=true;}return false;}out.core=a.core;out.facts_verified=true;if(!LydSceneSample267V1(q,s,i,kind,wall,mono,z,reason)||!Same(a.core,z.core)||a.scene!=z.scene||a.witness!=z.witness||!Owner(q,s,i)){reason="lyd_actual_world_or_fixed_gui_source_changed_between_samples";return false;}out=std::move(z);reason.clear();return true;
 }catch(...){reason="lyd_actual_owner_frame_exception";return false;}
}
#if defined(XAR_CK3_ENABLE_121003_FULL111_ORDINARY_EVENT_SNAPSHOT_V1) && XAR_CK3_ENABLE_121003_FULL111_ORDINARY_EVENT_SNAPSHOT_V1
bool ReadFull111OrdinaryEventOnOwnerV1(const ReadonlyBindings &bindings,
 const ck3_1210::CoreSnapshotPrefix &core,std::uintptr_t game,std::uintptr_t jomini,
 std::uint64_t wall,std::uint64_t mono,const void *owner_context,
 bool (*still_owned)(const void*) noexcept,Full111OrdinaryEventWitnessV1 &out){
 const auto unexpired=[&]{
  const auto now=std::chrono::duration_cast<std::chrono::milliseconds>(
      std::chrono::system_clock::now().time_since_epoch()).count();
  return now>0&&static_cast<std::uint64_t>(now)<wall&&GetTickCount64()<mono;
 };
 if(!bindings.exact_image_admitted||!game||!jomini||!owner_context||!still_owned||
     !unexpired()||!still_owned(owner_context))return false;
 LydRequest267V1 request{};
 request.action=LydAction267V1::query_events;
 request.expected=core;request.deadline_unix_ms=wall;
 LydFrame267V1 first{},second{};
 first.scene.kind=second.scene.kind=LydKind267V1::events;
 first.scene.wall_deadline=second.scene.wall_deadline=wall;
 std::string reason;
 if(!LydGuiSceneSample267V1(bindings.module_base,first,reason,unexpired,true)||
     first.scene.jomini!=jomini||!still_owned(owner_context)||
     !ReadFull111LydEventsWithQueueV1(bindings,core,first.scene,mono,request,game,out.raw,reason,&out.queue)||
     !still_owned(owner_context)||
     !LydGuiSceneSample267V1(bindings.module_base,second,reason,unexpired,true)||
     first.scene!=second.scene||first.witness!=second.witness||!still_owned(owner_context))return false;
 out.scene=std::move(second.scene);out.widgets=std::move(second.witness);
 return true;
}
#endif
#endif
