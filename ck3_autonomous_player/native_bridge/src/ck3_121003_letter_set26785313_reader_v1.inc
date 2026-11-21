// Fixed living owner and shallow events layer only. Public v11 is unchanged.
#if defined(XAR_CK3_ENABLE_121003_26785313_LETTER_SET_V1) && XAR_CK3_ENABLE_121003_26785313_LETTER_SET_V1
namespace {
bool LetterSetSceneSample267V1(ReadonlyContext&q,const ck3_11906::MainThreadExecutionStampV1&s,const OwnerInvocationV1&i,
 std::uint64_t wall,std::uint64_t mono,LetterSetFrame267V1&out,std::string&reason){
 const auto valid=[&]{const auto t=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();return wall&&mono&&t>0&&static_cast<std::uint64_t>(t)<wall&&GetTickCount64()<mono&&Owner(q,s,i);};
 const auto fail=[&](const char*why){reason=why;return false;};if(!valid()||!Read(q,s,i)||!q.observation.available||q.observation.offline_fixture||!q.observation.main_owner_observed)return fail("letter_actual_paused_living_core_unavailable");
 out.core=q.observation.core;out.facts_verified=true;auto&e=out.scene.common;e.wall_deadline=wall;const auto image=q.bindings.module_base;std::uintptr_t app=0,vt=0,first=0;
 if(!At(image,kJominiStateSlotRva,e.jomini)||!At(e.jomini,0x10,e.gfx)||!At(e.gfx,0,vt)||vt!=image+0x4B24748||!At(e.jomini,0x18,app)||!At(app,0,vt)||vt!=image+kGuiRootApplicationVtableRvaV1||!At(app,0x1B8,first)||!At(first,0x58,e.context)||!e.context||!At(e.context,0xD0,e.global))return fail("letter_application_context_source_unavailable");
 GuiWindowNodeV1 root,events,letter;std::unordered_set<std::uintptr_t>seen{e.global};std::size_t names=0;if(!GuiWindowNodeReadV1(image,e.global,e.context,0,root))return fail("letter_global_widget_unavailable");out.witness.push_back(root);
 const auto children=[&](const GuiWindowNodeV1&parent,std::string_view wanted,GuiWindowNodeV1&found,bool many=false){for(std::int32_t n=0;n<parent.child_count;++n){std::uintptr_t p=0;GuiWindowNodeV1 row;if(!valid()||out.witness.size()>=4096||!At(parent.children,static_cast<std::size_t>(n)*8,p)||!seen.insert(p).second||!GuiWindowNodeReadV1(image,p,e.context,parent.widget,row))return false;row.sibling_index=static_cast<std::uint32_t>(n);row.visible=row.visible&&parent.visible;row.enabled=row.enabled&&parent.enabled;names+=row.name.size();if(names>131072)return false;out.witness.push_back(row);if(row.name==wanted){if(many)out.scene.roots.push_back({row.widget,row.visible,row.enabled});else{if(found.widget)return false;found=row;}}}return true;};
 if(!children(root,"events",events)||!events.widget)return fail("letter_events_layer_missing_or_ambiguous");e.events=events.widget;
 if(!children(events,"letter_event",letter,true)||out.scene.roots.size()>32)return fail("letter_set_complete_named_root_census_invalid");return valid();
}
}
bool ReadLetterSetFrameOnOwner267V1(const ReadonlyBindings&b,ck3_11906::MainThreadQueryMailboxV1*m,const ck3_11906::MainThreadQueryTicketV1&t,
 const ck3_11906::MainThreadExecutionStampV1&s,void*context,std::uint64_t wall,std::uint64_t mono,LetterSetFrame267V1&out,std::string&reason)noexcept{
 out={};reason="letter_original_owner_unavailable";try{if(!m||m->offline_fixture||!context||m->permitted_executor_thirdenary!=&ExecuteLetterSetOnOwner267V1)return false;
  ReadonlyContext q;q.bindings=b;q.mailbox=m;q.ticket=t;q.mode=ReadonlyModeV1::core_only;const OwnerInvocationV1 i{&ExecuteLetterSetOnOwner267V1,context};LetterSetFrame267V1 a,z;
  if(!LetterSetSceneSample267V1(q,s,i,wall,mono,a,reason)){if(a.facts_verified){out.core=a.core;out.facts_verified=true;}return false;}out.core=a.core;out.facts_verified=true;
  if(!LetterSetSceneSample267V1(q,s,i,wall,mono,z,reason)||!Same(a.core,z.core)||a.scene!=z.scene||a.witness!=z.witness||!Owner(q,s,i)){reason="letter_world_or_named_widget_changed_between_samples";return false;}out=std::move(z);reason.clear();return true;
 }catch(...){reason="letter_owner_read_exception";return false;}
}
#endif
