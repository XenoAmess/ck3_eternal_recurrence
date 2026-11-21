// Included only by the current readonly TU. Reuses Owner and bounded widget
// copies; never calls Take/Read, whose living-only gameplay contract is unchanged.
#if defined(XAR_CK3_ENABLE_121003_26785313_SUCCESSION_CONTINUE_V1) && XAR_CK3_ENABLE_121003_26785313_SUCCESSION_CONTINUE_V1
namespace {
bool SuccessionWorldSample267V1(ReadonlyContext&q,const ck3_11906::MainThreadExecutionStampV1&s,
 const OwnerInvocationV1&i,SuccessionLifecycleFrame267V1&f) {
 if(!Owner(q,s,i)||!NativeCore(q.bindings.core,f.world)||!Owner(q,s,i))return false;
 const auto&b=q.bindings.core;std::uintptr_t players=0;
 if(!At(reinterpret_cast<std::uintptr_t>(b.game_state_slot),0,f.game_state)||f.game_state!=s.game_state||
  !At(reinterpret_cast<std::uintptr_t>(b.jomini_state_slot),0,f.jomini)||f.jomini!=s.jomini_state||
  !At(reinterpret_cast<std::uintptr_t>(b.character_storage_slot),0,f.storage)||!f.storage||
  !At(f.game_state,ck3_1210::kGameStateDataOffset,f.game_data)||!f.game_data||
  !At(f.jomini,ck3_1210::kJominiPlayersOffset,players)||!players)return false;
 const auto manager=f.game_data+ck3_1210::kPlayerCharacterManagerOffset;
 if(!At(manager,ck3_1210::kPlayerManagerEntriesOffset,f.player_entries)||
  !At(manager,ck3_1210::kPlayerManagerCountOffset,f.player_count)||f.player_count<0||f.player_count>1024||
  (f.player_count&&!f.player_entries))return false;
 // Complete the native player-manager read even when map_ready is false.
 // Old ReadCoreSnapshot's early-return defaults must not become "unassigned" facts.
 f.world.has_played_character=false;f.world.played_character_id=-1;f.world.played_character_alive=false;
 std::size_t matches=0;
 for(std::int32_t n=0;n<f.player_count;++n){std::uintptr_t entry=0;std::int32_t player=-1,id=-1;
  if(!At(f.player_entries,static_cast<std::size_t>(n)*8,entry))return false;if(!entry)continue;
  if(!At(entry,ck3_1210::kPlayerEntryLocalPlayerIdOffset,player))return false;if(player!=f.world.local_player_id)continue;
  if(++matches>1||!At(entry,ck3_1210::kPlayerEntryCharacterIdOffset,id))return false;if(id==-1)continue;
  const auto actor=Resolve(b,id);std::int32_t actual=-1;std::uint32_t type=0;std::uintptr_t death=0;
  if(!actor||!At(actor,0x18,actual)||actual!=id||!At(actor,0x1C,type)||type!=0x43686172U||!At(actor,0x1D0,death))return false;
  f.world.has_played_character=true;f.world.played_character_id=id;f.world.played_character_alive=death==0;
 }
 if(f.world.clock.date_raw!=s.date_raw||!Owner(q,s,i))return false;f.world_verified=true;return true;
}
bool SuccessionWorldSame267V1(const SuccessionLifecycleFrame267V1&a,const SuccessionLifecycleFrame267V1&b) {
 return a.world_verified&&b.world_verified&&Same(a.world,b.world)&&a.game_state==b.game_state&&a.jomini==b.jomini&&a.storage==b.storage&&a.game_data==b.game_data&&a.player_entries==b.player_entries&&a.player_count==b.player_count;
}
bool SuccessionWindowSample267V1(ReadonlyContext&q,const ck3_11906::MainThreadExecutionStampV1&s,
 const OwnerInvocationV1&i,std::uint64_t connection,SuccessionLifecycleFrame267V1&f,std::string&reason) {
 const auto fail=[&](const char*why){reason=why;return false;};const auto base=q.bindings.module_base;
 if(!Owner(q,s,i)||!VerifyGuiWindowImageV1(base))return fail("succession_widget_image_or_owner_unavailable");
 GuiWindowV1 v;v.requested_name="succession_event_window";v.connection_generation=connection;v.ticket_sequence=q.ticket.sequence;v.pump_epoch=s.pump_epoch;v.owner_thread_id=s.thread_id;v.logical_owner=f.jomini;std::uintptr_t vt=0;
 if(!At(v.logical_owner,0x18,v.application)||!At(v.application,0,vt)||vt!=base+kGuiRootApplicationVtableRvaV1||!At(v.application,0x1B8,v.first)||!At(v.first,0x58,v.context)||!v.context||!At(v.context,0xD0,v.global_root)||!GuiWindowNodeReadV1(base,v.global_root,v.context,0,v.root))return fail("succession_application_context_root_unavailable");
 if(!At(f.jomini,0x10,f.gfx)||!At(f.gfx,0x88,f.handler)||!f.handler)return fail("succession_actual_handler_unavailable");
 std::unordered_set<std::uintptr_t>unique{v.global_root};std::size_t bytes=v.root.name.size();
 const auto find=[&](const GuiWindowNodeV1&parent,std::string_view name,GuiWindowName267V1&found,std::uint32_t&index){
  for(std::int32_t n=0;n<parent.child_count;++n){std::uintptr_t p=0;GuiWindowName267V1 row;if(!Owner(q,s,i)||!At(parent.children,static_cast<std::size_t>(n)*8,p)||!unique.insert(p).second||!GuiWindowNameRead267V1(base,p,v.context,parent.widget,row))return false;
   bytes+=row.name.size();if(bytes>131072)return false;if(row.name==name){if(found.widget)return false;found=row;index=static_cast<std::uint32_t>(n);}}
  return true;};
 GuiWindowName267V1 layer_name,window_name;std::uint32_t layer_index=0,window_index=0;
 if(!find(v.root,"confirmation",layer_name,layer_index)||!layer_name.widget)return fail("succession_confirmation_layer_missing_or_ambiguous");
 GuiWindowNodeV1 layer,window;
 if(!GuiWindowNodeReadV1(base,layer_name.widget,v.context,v.global_root,layer)||!GuiWindowNameMatches267V1(layer_name,layer))return fail("succession_confirmation_header_changed");
 layer.sibling_index=layer_index;layer.visible=layer.visible&&v.root.visible;layer.enabled=layer.enabled&&v.root.enabled;
 if(!find(layer,v.requested_name,window_name,window_index)||!window_name.widget)return fail("succession_literal_window_missing_or_ambiguous");
 if(!GuiWindowNodeReadV1(base,window_name.widget,v.context,layer.widget,window)||!GuiWindowNameMatches267V1(window_name,window))return fail("succession_window_header_changed");
 window.sibling_index=window_index;window.depth=1;window.visible=window.visible&&layer.visible;window.enabled=window.enabled&&layer.enabled;
 if(!window.visible||!window.enabled)return fail("succession_default_window_not_visible_enabled");
 v.top_level.push_back(layer);v.ancestors.push_back(layer);v.tree.push_back(window);v.window_found=true;
 std::vector<std::size_t>todo{0};std::size_t buttons=0;
 while(!todo.empty()){const auto index=todo.back();todo.pop_back();const auto parent=v.tree[index];
  if(parent.name=="close_button"&&parent.visible&&parent.enabled){++buttons;f.default_button_index=static_cast<std::uint32_t>(index);}
  if(!Owner(q,s,i)||(parent.depth>=kGuiWindowMaxDepthV1&&parent.child_count))return fail("succession_selected_tree_depth_or_owner");
  for(std::int32_t n=0;n<parent.child_count;++n){std::uintptr_t p=0;GuiWindowNodeV1 row;if(v.tree.size()>=kGuiWindowMaxNodesV1||!At(parent.children,static_cast<std::size_t>(n)*8,p)||!unique.insert(p).second||!GuiWindowNodeReadV1(base,p,v.context,parent.widget,row))return fail("succession_selected_tree_context_parent_or_budget");
   row.parent_index=static_cast<std::int32_t>(index);row.depth=parent.depth+1;row.sibling_index=static_cast<std::uint32_t>(n);row.visible=row.visible&&parent.visible;row.enabled=row.enabled&&parent.enabled;bytes+=row.name.size();if(bytes>131072)return fail("succession_selected_name_budget");todo.push_back(v.tree.size());v.tree.push_back(std::move(row));}}
 if(buttons!=1)return fail("succession_default_close_button_not_unique_admissible");f.window=std::move(v);return Owner(q,s,i);
}
}
bool ReadSuccessionLifecycleFrameOnOwner267V1(const ReadonlyBindings&b,ck3_11906::MainThreadQueryMailboxV1*m,
 const ck3_11906::MainThreadQueryTicketV1&t,const ck3_11906::MainThreadExecutionStampV1&s,void*ctx,
 std::uint64_t connection,std::uint64_t deadline,std::uint64_t monotonic,SuccessionLifecycleFrame267V1&out,std::string&reason)noexcept{
 out={};reason="succession_original_owner_or_deadline_unavailable";
 try{if(!m||m->offline_fixture||!ctx||!connection||!deadline||!monotonic||m->permitted_executor_denary!=&ExecuteSuccessionLifecycleOnOwner267V1)return false;
  const auto time=[&]{const auto wall=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();return wall>0&&static_cast<std::uint64_t>(wall)<deadline&&GetTickCount64()<monotonic;};
  ReadonlyContext q;q.bindings=b;q.mailbox=m;q.ticket=t;q.mode=ReadonlyModeV1::core_only;
  const OwnerInvocationV1 invocation{&ExecuteSuccessionLifecycleOnOwner267V1,ctx};SuccessionLifecycleFrame267V1 a,z;
  if(!time()||!SuccessionWorldSample267V1(q,s,invocation,a))return false;
  out=a; // Genuine partial world facts may survive a missing lifecycle GUI.
  if(!SuccessionWindowSample267V1(q,s,invocation,connection,a,reason)||!time()||!SuccessionWorldSample267V1(q,s,invocation,z)||!SuccessionWindowSample267V1(q,s,invocation,connection,z,reason))return false;
  if(!time()||!SuccessionWorldSame267V1(a,z)||a.window!=z.window||a.gfx!=z.gfx||a.handler!=z.handler||a.default_button_index!=z.default_button_index||!Owner(q,s,invocation)){reason="succession_world_or_window_changed_between_samples";return false;}
  out=std::move(z);reason.clear();return true;
 }catch(...){reason="succession_lifecycle_read_exception";return false;}
}
#endif
