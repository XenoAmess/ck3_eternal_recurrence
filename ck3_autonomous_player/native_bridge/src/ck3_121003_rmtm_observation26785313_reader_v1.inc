#if defined(XAR_CK3_ENABLE_121003_26785313_RMTM_OBSERVATION_V1) && XAR_CK3_ENABLE_121003_26785313_RMTM_OBSERVATION_V1
namespace {
bool RmtmObservationSample267V1(ReadonlyContext&q,const ck3_11906::MainThreadExecutionStampV1&s,const OwnerInvocationV1&i,std::uint64_t wall,std::uint64_t mono,RmtmObservationFrame267V1&out,std::string&why){
 RmtmDecisionFrame267V1 scene;
 if(!RmtmDecisionSceneSample267V1(q,s,i,wall,mono,scene,why)){out.core=scene.core;out.facts_verified=scene.facts_verified;return false;}
 out.core=scene.core;out.facts_verified=scene.facts_verified;out.scene=scene.scene;out.witness=std::move(scene.witness);
 // The ordinary interaction menu is in the actual top layer. Capture every
 // child, including hidden ones; no visible-only census or guessed widget.
 const auto layer=std::find_if(out.witness.begin(),out.witness.end(),[](const auto&n){return n.name=="top";});
 if(layer==out.witness.end()){why="rmtm_actual_top_layer_unavailable";return false;}
 const auto parent=*layer;std::unordered_set<std::uintptr_t>seen;for(const auto&n:out.witness)seen.insert(n.widget);
 for(std::int32_t n=0;n<parent.child_count;++n){
  std::uintptr_t p=0;GuiWindowNodeV1 row;
  if(!Owner(q,s,i)||GetTickCount64()>=mono||out.witness.size()>=4096||!At(parent.children,static_cast<std::size_t>(n)*8,p)||!seen.insert(p).second||!GuiWindowNodeReadV1(q.bindings.module_base,p,out.scene.context,parent.widget,row)){why="rmtm_actual_complete_top_layer_changed";return false;}
  row.sibling_index=static_cast<std::uint32_t>(n);row.visible&=parent.visible;row.enabled&=parent.enabled;out.witness.push_back(std::move(row));
 }
 if(!RmtmRoleWorldSample267V1(q,s,i,wall,mono,out.role,why)||!Same(out.core,out.role.world.core))return false;
 return Owner(q,s,i);
}
bool SameRmtmObservationFrame267V1(const RmtmObservationFrame267V1&a,const RmtmObservationFrame267V1&b){return a.facts_verified&&b.facts_verified&&Same(a.core,b.core)&&a.scene==b.scene&&a.witness==b.witness&&SameRmtmWorld267V1(a.role.world,b.role.world);}
}
bool ReadRmtmObservationFrameOnOwner267V1(const ReadonlyBindings&b,ck3_11906::MainThreadQueryMailboxV1*m,const ck3_11906::MainThreadQueryTicketV1&t,const ck3_11906::MainThreadExecutionStampV1&s,void*context,std::uint64_t wall,std::uint64_t mono,RmtmObservationFrame267V1&out,std::string&why)noexcept{
 out={};why="rmtm_observation_original_owner_unavailable";
 try{
  if(!m||m->offline_fixture||!context||m->permitted_executor_quattuortrigintary!=&ExecuteRmtmOnOwner267V1)return false;
  ReadonlyContext q;q.bindings=b;q.mailbox=m;q.ticket=t;q.mode=ReadonlyModeV1::core_only;const OwnerInvocationV1 i{&ExecuteRmtmOnOwner267V1,context};
  RmtmObservationFrame267V1 a,z;if(!RmtmObservationSample267V1(q,s,i,wall,mono,a,why)){out=std::move(a);return false;}out=a;
  if(!RmtmObservationSample267V1(q,s,i,wall,mono,z,why)||!SameRmtmObservationFrame267V1(a,z)||!Owner(q,s,i)){why="rmtm_observation_actual_world_or_complete_UI_census_changed";return false;}
  out=std::move(z);why.clear();return true;
 }catch(...){why="rmtm_observation_owner_capture_exception";return false;}
}
#endif
