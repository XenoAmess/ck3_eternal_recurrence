// Fixed-owner actual strict living Core and shallow named-window source. Public v11 is unchanged.
#if defined(XAR_CK3_ENABLE_121003_26785313_DJC_UI_V1) && XAR_CK3_ENABLE_121003_26785313_DJC_UI_V1
namespace {
bool DjcUiSceneSample267V1(ReadonlyContext&q,const ck3_11906::MainThreadExecutionStampV1&s,const OwnerInvocationV1&i,
 std::uint64_t wall,std::uint64_t mono,DjcUiFrame267V1&out,std::string&reason){
 const auto valid=[&]{const auto t=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();return wall&&mono&&t>0&&static_cast<std::uint64_t>(t)<wall&&GetTickCount64()<mono&&Owner(q,s,i);};
 const auto fail=[&](const char*why){reason=why;return false;};if(!valid()||!Read(q,s,i)||!q.observation.available||q.observation.offline_fixture||!q.observation.main_owner_observed)return fail("djc_ui_actual_paused_living_core_unavailable");
 out.core=q.observation.core;out.facts_verified=true;auto&e=out.scene;e.deadline_unix_ms=wall;const auto image=q.bindings.module_base;std::uintptr_t app=0,vt=0,first=0;
 if(!At(image,kJominiStateSlotRva,e.jomini)||!At(e.jomini,0x10,e.gfx)||!At(e.gfx,0x88,e.handler)||!At(e.jomini,0x18,app)||!At(app,0,vt)||vt!=image+kGuiRootApplicationVtableRvaV1||!At(app,0x1B8,first)||!At(first,0x58,e.gui_context)||!e.gui_context||!At(e.gui_context,0xD0,e.global_root))return fail("djc_ui_application_handler_context_unavailable");
 std::unordered_set<std::uintptr_t>seen{e.global_root};std::size_t names=0;GuiWindowNodeV1 root,middle,confirmation,view,popup;
 if(!GuiWindowNodeReadV1(image,e.global_root,e.gui_context,0,root))return fail("djc_ui_global_widget_unavailable");out.witness.push_back(root);names+=root.name.size();
 const auto children=[&](const GuiWindowNodeV1&parent,std::string_view wanted,GuiWindowNodeV1&found){
  for(std::int32_t n=0;n<parent.child_count;++n){std::uintptr_t p=0;GuiWindowNodeV1 row;if(!valid()||!At(parent.children,static_cast<std::size_t>(n)*8,p)||!seen.insert(p).second||!GuiWindowNodeReadV1(image,p,e.gui_context,parent.widget,row))return false;row.sibling_index=static_cast<std::uint32_t>(n);row.visible=row.visible&&parent.visible;row.enabled=row.enabled&&parent.enabled;names+=row.name.size();if(names>131072)return false;out.witness.push_back(row);if(row.name==wanted){if(found.widget)return false;found=row;}}return true;};
 if(!children(root,"middle",middle)||!middle.widget)return fail("djc_ui_middle_layer_missing_or_ambiguous");
 for(const auto&row:out.witness)if(row.parent==root.widget&&row.name=="confirmation"){if(confirmation.widget)return fail("djc_ui_confirmation_layer_ambiguous");confirmation=row;}
 e.middle=middle.widget;if(!children(middle,"declare_war_window",view))return fail("djc_ui_named_declaration_window_ambiguous");
 e.view_root=view.widget;e.view_named_bound=view.widget!=0;e.view_visible=view.widget&&view.visible;e.view_enabled=view.widget&&view.enabled;
 if(confirmation.widget){
  if(!children(confirmation,"basic_confirmation_popup",popup))return fail("djc_ui_named_warning_popup_ambiguous");
  if(popup.widget&&popup.visible&&popup.enabled){e.warning_root=popup.widget;e.warning_named_bound=true;std::vector<GuiWindowNodeV1>todo{popup};std::size_t accepts=0;
   while(!todo.empty()){const auto parent=todo.back();todo.pop_back();if(parent.name=="accept_button"&&parent.visible&&parent.enabled)++accepts;if(parent.depth>=kGuiWindowMaxDepthV1&&parent.child_count)return fail("djc_ui_warning_tree_depth");
    for(std::int32_t n=0;n<parent.child_count;++n){std::uintptr_t p=0;GuiWindowNodeV1 row;if(!valid()||out.witness.size()>=kGuiWindowMaxNodesV1||!At(parent.children,static_cast<std::size_t>(n)*8,p)||!seen.insert(p).second||!GuiWindowNodeReadV1(image,p,e.gui_context,parent.widget,row))return fail("djc_ui_warning_tree_identity_or_budget");row.depth=parent.depth+1;row.sibling_index=static_cast<std::uint32_t>(n);row.visible=row.visible&&parent.visible;row.enabled=row.enabled&&parent.enabled;names+=row.name.size();if(names>131072)return fail("djc_ui_warning_name_budget");out.witness.push_back(row);todo.push_back(row);}
   }e.warning_accept_admissible=accepts==1;
  }
 }
 return valid();
}
}
bool ReadDjcUiFrameOnOwner267V1(const ReadonlyBindings&b,ck3_11906::MainThreadQueryMailboxV1*m,const ck3_11906::MainThreadQueryTicketV1&t,
 const ck3_11906::MainThreadExecutionStampV1&s,void*context,std::uint64_t wall,std::uint64_t mono,DjcUiFrame267V1&out,std::string&reason)noexcept{
 out={};reason="djc_ui_original_owner_unavailable";
 try{if(!m||m->offline_fixture||!context||m->permitted_executor_undenary!=&ExecuteDjcUiOnOwner267V1)return false;ReadonlyContext q;q.bindings=b;q.mailbox=m;q.ticket=t;q.mode=ReadonlyModeV1::core_only;const OwnerInvocationV1 i{&ExecuteDjcUiOnOwner267V1,context};DjcUiFrame267V1 a,z;
  if(!DjcUiSceneSample267V1(q,s,i,wall,mono,a,reason)){if(a.facts_verified){out.core=a.core;out.facts_verified=true;}return false;}out.core=a.core;out.facts_verified=true;
  if(!DjcUiSceneSample267V1(q,s,i,wall,mono,z,reason)||!Same(a.core,z.core)||a.scene!=z.scene||a.witness!=z.witness||!Owner(q,s,i)){reason="djc_ui_world_or_named_source_changed_between_samples";return false;}
  out=std::move(z);reason.clear();return true;
 }catch(...){reason="djc_ui_fixed_source_read_exception";return false;}
}
#endif
