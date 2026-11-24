// Include after the existing LydSceneSample data reader and Living inventory /
// fixed-GUI reader. The old LYD entrypoint and old slot are never submitted.
#if defined(XAR_CK3_ENABLE_121003_26785313_LIVING_UI_V1) && XAR_CK3_ENABLE_121003_26785313_LIVING_UI_V1 && defined(XAR_CK3_ENABLE_121003_26785313_LIVING_INVENTORY_V1) && XAR_CK3_ENABLE_121003_26785313_LIVING_INVENTORY_V1 && defined(XAR_CK3_ENABLE_121003_26785313_LIVING_WEAPON_V1) && XAR_CK3_ENABLE_121003_26785313_LIVING_WEAPON_V1 && defined(XAR_CK3_ENABLE_121003_26785313_LIVING_EVENT_V1) && XAR_CK3_ENABLE_121003_26785313_LIVING_EVENT_V1 && defined(XAR_CK3_ENABLE_121003_26785313_LIVING_DETAIL_V1) && XAR_CK3_ENABLE_121003_26785313_LIVING_DETAIL_V1 && defined(XAR_CK3_ENABLE_121003_26785313_LYD_V1) && XAR_CK3_ENABLE_121003_26785313_LYD_V1
bool ReadLivingUiFrameOnOwner267V1(const ReadonlyBindings&b,
 ck3_11906::MainThreadQueryMailboxV1*m,const ck3_11906::MainThreadQueryTicketV1&t,
 const ck3_11906::MainThreadExecutionStampV1&s,void*context,const LivingUiRequest267V1&r,
 std::uint64_t mono,LivingUiFrame267V1&out,std::string&why)noexcept {
 out={};why="living_UI_new_owner_or_data_reader_unavailable";
 try{
  if(!m||m->offline_fixture||!context||
     m->permitted_executor_artifact_personal_read12004!=&ExecuteLivingOnOwner267V1||
     !LivingOwnerConnection267V1(static_cast<const LivingOwnerInvocation267V1*>(context)))return false;
  if(LivingUiKindFor267V1(r.action)==LivingUiKind267V1::weapon){
   LivingWeaponFrame267V1 f;
   if(!ReadLivingWeaponFrameOnOwner267V1(b,m,t,s,context,r,mono,f,why))return false;
   out.inventory=f.inventory;out.weapon=std::move(f);return true;
  }
  if(!ReadLivingInventoryQueryFrameOnOwner267V1(b,m,t,s,context,r,mono,out.inventory,why))return false;
  ReadonlyContext q;q.bindings=b;q.mailbox=m;q.ticket=t;q.mode=ReadonlyModeV1::core_only;
  const OwnerInvocationV1 invocation{&ExecuteLivingOnOwner267V1,context};
  if(LivingUiKindFor267V1(r.action)==LivingUiKind267V1::detail){
   LivingDetailFrame267V1 a,z;a.inventory=z.inventory=out.inventory;
   if(!LivingGuiSceneSample267V1(q,s,invocation,r,mono,a,"artifact_details_view",why)||
      !LivingGuiSceneSample267V1(q,s,invocation,r,mono,z,"artifact_details_view",why)||
      a.gui!=z.gui||a.manager!=z.manager||a.gfx!=z.gfx||!Owner(q,s,invocation))return false;
   out.detail=std::move(z);return true;
  }
  LydFrame267V1 a,z;
  if(!LydSceneSample267V1(q,s,invocation,LydKind267V1::events,r.deadline_unix_ms,mono,a,why)||
     !LydSceneSample267V1(q,s,invocation,LydKind267V1::events,r.deadline_unix_ms,mono,z,why)||
     !Same(a.core,z.core)||!Same(z.core,out.inventory.core)||a.scene!=z.scene||a.witness!=z.witness||
     z.scene.jomini!=out.inventory.jomini||!Owner(q,s,invocation))return false;
  out.events=std::move(z);return true;
 }catch(...){why="living_UI_private_frame_copy_unavailable";return false;}
}
#endif
