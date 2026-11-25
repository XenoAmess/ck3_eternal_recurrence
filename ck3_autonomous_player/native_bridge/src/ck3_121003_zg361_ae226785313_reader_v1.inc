// Source attachment: include in Readonly TU after existing LetterSet reader.
#if defined(XAR_CK3_ENABLE_121003_26785313_ZG361_AE2_V1) && XAR_CK3_ENABLE_121003_26785313_ZG361_AE2_V1
namespace {
bool Ae2ControlsSceneSample267V1(ReadonlyContext&q,const ck3_11906::MainThreadExecutionStampV1&s,const OwnerInvocationV1&i,std::uint64_t wall,std::uint64_t mono,zg361_ae2_control::Zg361Ae2ManageFrame267V1&out,std::string&reason){
 const auto valid=[&]{const auto n=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();return wall&&mono&&n>0&&static_cast<std::uint64_t>(n)<wall&&GetTickCount64()<mono&&Owner(q,s,i);};const auto fail=[&](const char*why){reason=why;return false;};if(!valid()||!Read(q,s,i)||!q.observation.available||q.observation.offline_fixture||!q.observation.main_owner_observed)return fail("zg361_ae2_controls_actual_paused_living_core_unavailable");out.core=q.observation.core;out.facts_verified=true;auto&e=out.scene;const auto image=q.bindings.module_base;std::uintptr_t app=0,first=0,vt=0,back=0;
 if(!At(image,kJominiStateSlotRva,e.jomini)||!At(e.jomini,0,vt)||vt!=image+0x4B45FE0||!At(e.jomini,0x10,e.gfx)||!At(e.gfx,0,vt)||vt!=image+0x4B24748||!At(e.gfx,0x20,back)||back!=e.jomini||!At(e.gfx,0x88,e.handler)||!At(e.handler,0,vt)||vt!=image+0x4B22578||!At(e.handler,0x58,vt)||vt!=image+0x4B22558||!At(e.jomini,0x18,app)||!At(app,0,vt)||vt!=image+kGuiRootApplicationVtableRvaV1||!At(app,0x1B8,first)||!At(first,0x58,e.context)||!e.context||!At(e.context,0xD0,e.global))return fail("zg361_ae2_controls_actual_application_handler_context_unavailable");
 GuiWindowNodeV1 root,windows,middle,hud,list,detail;std::unordered_set<std::uintptr_t>seen{e.global};std::size_t names=0;if(!GuiWindowNodeReadV1(image,e.global,e.context,0,root))return fail("zg361_ae2_controls_actual_global_widget_unavailable");out.witness.push_back(root);
 const auto children=[&](const GuiWindowNodeV1&parent,std::string_view wanted,GuiWindowNodeV1&found){for(std::int32_t n=0;n<parent.child_count;++n){std::uintptr_t p=0;GuiWindowNodeV1 row;if(!valid()||out.witness.size()>=4096||!At(parent.children,static_cast<std::size_t>(n)*8,p)||!seen.insert(p).second||!GuiWindowNodeReadV1(image,p,e.context,parent.widget,row))return false;row.sibling_index=static_cast<std::uint32_t>(n);row.visible=row.visible&&parent.visible;row.enabled=row.enabled&&parent.enabled;names+=row.name.size();if(names>131072)return false;out.witness.push_back(row);if(row.name==wanted){if(found.widget)return false;found=row;}}return true;};
 if(!children(root,"windows_layer",windows))return fail("zg361_ae2_controls_actual_global_layer_census_unavailable");for(const auto&n:out.witness){if(n.name=="middle"){if(middle.widget)return fail("zg361_ae2_controls_middle_layer_ambiguous");middle=n;}if(n.name=="hud_layer"){if(hud.widget)return fail("zg361_ae2_controls_hud_layer_ambiguous");hud=n;}}
 if(!windows.widget||!middle.widget||!hud.widget)return fail("zg361_ae2_controls_fixed_layers_missing");if(!children(windows,"decisions_view",list)||!children(middle,"decisiondetail_view",detail))return fail("zg361_ae2_controls_named_list_or_detail_census_unavailable");
 e.list_root=list.widget;e.list_visible=list.visible;e.list_enabled=list.enabled;e.detail_root=detail.widget;e.detail_visible=detail.visible;e.detail_enabled=detail.enabled;
 // Existing actual visible model/detail is independent of unrelated HUD descendants.
 if(!list.visible&&!detail.visible)e.hud.push_back(hud);for(std::size_t cursor=0;cursor<e.hud.size();++cursor){const auto parent=e.hud[cursor];if(parent.depth>=32)return fail("zg361_ae2_controls_hud_navigation_depth_exhausted");for(std::int32_t n=0;n<parent.child_count;++n){std::uintptr_t p=0;GuiWindowNodeV1 row;if(!valid()||out.witness.size()>=4096||!At(parent.children,static_cast<std::size_t>(n)*8,p)||!seen.insert(p).second||!GuiWindowNodeReadV1(image,p,e.context,parent.widget,row))return fail("zg361_ae2_controls_hud_navigation_source_unavailable");row.sibling_index=static_cast<std::uint32_t>(n);row.depth=parent.depth+1;row.visible=row.visible&&parent.visible;row.enabled=row.enabled&&parent.enabled;names+=row.name.size();if(names>131072)return fail("zg361_ae2_controls_hud_navigation_name_budget");e.hud.push_back(row);out.witness.push_back(row);}}
 return valid();
}
}


bool ReadZg361Ae2FrameOnOwner267V1(const ReadonlyBindings&b,
 ck3_11906::MainThreadQueryMailboxV1*m,const ck3_11906::MainThreadQueryTicketV1&t,
 const ck3_11906::MainThreadExecutionStampV1&s,void*context,const Zg361Ae2Request267V1&r,
 std::uint64_t mono,Zg361Ae2Frame267V1&out,std::string&why)noexcept{
 out={};why="zg361_ae2_current_owner_or_scene_unavailable";
 try{
  if(!m||m->offline_fixture||!context||m->permitted_executor_sextrigintary!=&ExecuteZg361Ae2OnOwner267V1)return false;
  ReadonlyContext q;q.bindings=b;q.mailbox=m;q.ticket=t;q.mode=ReadonlyModeV1::core_only;
  const OwnerInvocationV1 invocation{&ExecuteZg361Ae2OnOwner267V1,context};
  const auto world=[&](Zg361Ae2Frame267V1&f){
   return At(b.module_base,kGameStateSlotRva,f.game)&&f.game&&
    At(b.module_base,kJominiStateSlotRva,f.jomini)&&f.jomini&&
    At(b.module_base,kCharacterStorageSlotRva,f.character_storage)&&f.character_storage;};
  Zg361Ae2Frame267V1 a,z;
  if(Zg361Ae2KindFor267V1(r.action)==Zg361Ae2Kind267V1::scoreboard){
   const auto sample=[&](Zg361Ae2Frame267V1&f){
    if(!Read(q,s,invocation)||!q.observation.available||q.observation.offline_fixture||!q.observation.main_owner_observed)return false;
    f.core=q.observation.core;f.facts_verified=true;
    GuiWindowRequestV1 request;request.connection_generation=static_cast<const Zg361Ae2Context267V1*>(context)->connection_generation;
    request.deadline_unix_ms=r.deadline_unix_ms;request.expected_core=f.core;request.window_name="middle";
    q.gui_window_request=request;f.scoreboard.emplace();
    return request.connection_generation&&ReadGuiWindowV1(q,s,f.core,*f.scoreboard,invocation)&&f.scoreboard->window_found&&world(f);
   };
   if(!sample(a))return false;out.core=a.core;out.facts_verified=a.facts_verified;
   if(!sample(z)||!Same(a.core,z.core)||*a.scoreboard!=*z.scoreboard)return false;
  }else if(Zg361Ae2KindFor267V1(r.action)!=Zg361Ae2Kind267V1::events){
   a.controls.emplace();z.controls.emplace();
   const auto conn=static_cast<const Zg361Ae2Context267V1*>(context)->connection_generation;
   a.controls->scene.connection_generation=z.controls->scene.connection_generation=conn;
   a.controls->scene.wall_deadline=z.controls->scene.wall_deadline=r.deadline_unix_ms;
   if(!conn||!Ae2ControlsSceneSample267V1(q,s,invocation,r.deadline_unix_ms,mono,*a.controls,why)||!world(a))return false;
   out.core=a.controls->core;out.facts_verified=a.controls->facts_verified;
   if(!Ae2ControlsSceneSample267V1(q,s,invocation,r.deadline_unix_ms,mono,*z.controls,why)||!world(z)||
    !Same(a.controls->core,z.controls->core)||a.controls->scene!=z.controls->scene||a.controls->witness!=z.controls->witness)return false;
   z.controls->scene.owner_bound=true;z.core=z.controls->core;z.facts_verified=z.controls->facts_verified;
  }else{
   a.events.emplace();z.events.emplace();
   // Uses actual complete census DATA with this family's own executor/context.
   // The old LetterSet public owner wrapper/permission is never borrowed.
   if(!LetterSetSceneSample267V1(q,s,invocation,r.deadline_unix_ms,mono,*a.events,why)||!world(a))return false;
   out.core=a.events->core;out.facts_verified=a.events->facts_verified;
   if(!LetterSetSceneSample267V1(q,s,invocation,r.deadline_unix_ms,mono,*z.events,why)||!world(z)||
    !Same(a.events->core,z.events->core)||a.events->scene!=z.events->scene||a.events->witness!=z.events->witness)return false;
   z.core=z.events->core;z.facts_verified=z.events->facts_verified;
  }
  if(a.game!=z.game||a.jomini!=z.jomini||a.character_storage!=z.character_storage||!Owner(q,s,invocation))return false;
  out=std::move(z);why.clear();return true;
 }catch(...){why="zg361_ae2_current_owner_capture_unavailable";return false;}
}
#endif
