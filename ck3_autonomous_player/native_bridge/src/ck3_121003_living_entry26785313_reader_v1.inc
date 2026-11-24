#if defined(XAR_CK3_ENABLE_121003_26785313_LIVING_ENTRY_V1) && XAR_CK3_ENABLE_121003_26785313_LIVING_ENTRY_V1 && defined(XAR_CK3_ENABLE_121003_26785313_LIVING_INVENTORY_V1) && XAR_CK3_ENABLE_121003_26785313_LIVING_INVENTORY_V1
namespace {
bool LivingManageSceneSample267V1(ReadonlyContext&q,const ck3_11906::MainThreadExecutionStampV1&s,const OwnerInvocationV1&i,std::uint64_t wall,std::uint64_t mono,LivingManageFrame267V1&out,std::string&reason){
 const auto valid=[&]{const auto n=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();return wall&&mono&&n>0&&static_cast<std::uint64_t>(n)<wall&&GetTickCount64()<mono&&Owner(q,s,i);};const auto fail=[&](const char*why){reason=why;return false;};if(!valid()||!Read(q,s,i)||!q.observation.available||q.observation.offline_fixture||!q.observation.main_owner_observed)return fail("living_manage_actual_paused_living_core_unavailable");out.core=q.observation.core;out.facts_verified=true;auto&e=out.scene;const auto image=q.bindings.module_base;std::uintptr_t app=0,first=0,vt=0,back=0;
 if(!At(image,kJominiStateSlotRva,e.jomini)||!At(e.jomini,0,vt)||vt!=image+0x4B45FE0||!At(e.jomini,0x10,e.gfx)||!At(e.gfx,0,vt)||vt!=image+0x4B24748||!At(e.gfx,0x20,back)||back!=e.jomini||!At(e.gfx,0x88,e.handler)||!At(e.handler,0,vt)||vt!=image+0x4B22578||!At(e.handler,0x58,vt)||vt!=image+0x4B22558||!At(e.jomini,0x18,app)||!At(app,0,vt)||vt!=image+kGuiRootApplicationVtableRvaV1||!At(app,0x1B8,first)||!At(first,0x58,e.context)||!e.context||!At(e.context,0xD0,e.global))return fail("living_manage_actual_application_handler_context_unavailable");
 GuiWindowNodeV1 root,windows,middle,hud,list,detail;std::unordered_set<std::uintptr_t>seen{e.global};std::size_t names=0;if(!GuiWindowNodeReadV1(image,e.global,e.context,0,root))return fail("living_manage_actual_global_widget_unavailable");out.witness.push_back(root);
 const auto children=[&](const GuiWindowNodeV1&parent,std::string_view wanted,GuiWindowNodeV1&found){for(std::int32_t n=0;n<parent.child_count;++n){std::uintptr_t p=0;GuiWindowNodeV1 row;if(!valid()||out.witness.size()>=4096||!At(parent.children,static_cast<std::size_t>(n)*8,p)||!seen.insert(p).second||!GuiWindowNodeReadV1(image,p,e.context,parent.widget,row))return false;row.sibling_index=static_cast<std::uint32_t>(n);row.visible=row.visible&&parent.visible;row.enabled=row.enabled&&parent.enabled;names+=row.name.size();if(names>131072)return false;out.witness.push_back(row);if(row.name==wanted){if(found.widget)return false;found=row;}}return true;};
 if(!children(root,"windows_layer",windows))return fail("living_manage_actual_global_layer_census_unavailable");for(const auto&n:out.witness){if(n.name=="middle"){if(middle.widget)return fail("living_manage_middle_layer_ambiguous");middle=n;}if(n.name=="hud_layer"){if(hud.widget)return fail("living_manage_hud_layer_ambiguous");hud=n;}}
 if(!windows.widget||!middle.widget||!hud.widget)return fail("living_manage_fixed_layers_missing");if(!children(windows,"decisions_view",list)||!children(middle,"decisiondetail_view",detail))return fail("living_manage_named_list_or_detail_census_unavailable");
 e.list_root=list.widget;e.list_visible=list.visible;e.list_enabled=list.enabled;e.detail_root=detail.widget;e.detail_visible=detail.visible;e.detail_enabled=detail.enabled;
 // Existing actual visible model/detail is independent of unrelated HUD descendants.
 if(!list.visible&&!detail.visible)e.hud.push_back(hud);for(std::size_t cursor=0;cursor<e.hud.size();++cursor){const auto parent=e.hud[cursor];if(parent.depth>=32)return fail("living_manage_hud_navigation_depth_exhausted");for(std::int32_t n=0;n<parent.child_count;++n){std::uintptr_t p=0;GuiWindowNodeV1 row;if(!valid()||out.witness.size()>=4096||!At(parent.children,static_cast<std::size_t>(n)*8,p)||!seen.insert(p).second||!GuiWindowNodeReadV1(image,p,e.context,parent.widget,row))return fail("living_manage_hud_navigation_source_unavailable");row.sibling_index=static_cast<std::uint32_t>(n);row.depth=parent.depth+1;row.visible=row.visible&&parent.visible;row.enabled=row.enabled&&parent.enabled;names+=row.name.size();if(names>131072)return fail("living_manage_hud_navigation_name_budget");e.hud.push_back(row);out.witness.push_back(row);}}
 return valid();
}
}

// Include after LivingGuiSceneSample, in the actual Readonly TU only.
bool ReadLivingEntryFrameOnOwner267V1(const ReadonlyBindings&b,
 ck3_11906::MainThreadQueryMailboxV1*m,const ck3_11906::MainThreadQueryTicketV1&t,
 const ck3_11906::MainThreadExecutionStampV1&s,void*context,const LivingEntryRequest267V1&r,
 std::uint64_t mono,LivingEntryFrame267V1&out,std::string&why)noexcept{
 out={};why="living_entry_new_owner_or_complete_scene_unavailable";
 try{
  if(!m||m->offline_fixture||!context||m->permitted_executor_artifact_personal_read12004!=&ExecuteLivingOnOwner267V1)return false;
  const auto conn=LivingOwnerConnection267V1(static_cast<const LivingOwnerInvocation267V1*>(context));
  if(!conn||!ReadLivingInventoryQueryFrameOnOwner267V1(b,m,t,s,context,r,mono,out.inventory,why))return false;
  out.inventory.connection_generation=conn;
  ReadonlyContext q;q.bindings=b;q.mailbox=m;q.ticket=t;q.mode=ReadonlyModeV1::core_only;
  const OwnerInvocationV1 invocation{&ExecuteLivingOnOwner267V1,context};
  if(LivingEntryKindFor267V1(r.action)==LivingEntryKind267V1::manage){
   LivingManageFrame267V1 a,z;
   a.scene.connection_generation=z.scene.connection_generation=conn;
   a.scene.wall_deadline=z.scene.wall_deadline=r.deadline_unix_ms;
   if(!LivingManageSceneSample267V1(q,s,invocation,r.deadline_unix_ms,mono,a,why)||
    !LivingManageSceneSample267V1(q,s,invocation,r.deadline_unix_ms,mono,z,why)||
    !Same(a.core,z.core)||!Same(z.core,out.inventory.core)||a.scene!=z.scene||a.witness!=z.witness||
    a.scene.jomini!=out.inventory.jomini||!Owner(q,s,invocation))return false;
   out.manage=std::move(z);return true;
  }
  LivingWeaponFrame267V1 a,z;a.inventory=z.inventory=out.inventory;
  const auto name=LivingEntryKindFor267V1(r.action)==LivingEntryKind267V1::inventory?"inventory_view":"artifact_details_view";
  if(!LivingGuiSceneSample267V1(q,s,invocation,r,mono,a,name,why)||
   !LivingGuiSceneSample267V1(q,s,invocation,r,mono,z,name,why)||
   a.gui!=z.gui||a.manager!=z.manager||a.gfx!=z.gfx||!Owner(q,s,invocation))return false;
  out.view=std::move(z);return true;
 }catch(...){why="living_entry_current_frame_copy_unavailable";return false;}
}
#endif
