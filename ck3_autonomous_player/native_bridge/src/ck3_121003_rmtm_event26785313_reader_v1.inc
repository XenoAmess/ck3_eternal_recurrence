#if defined(XAR_CK3_ENABLE_121003_26785313_RMTM_EVENT_V1) && XAR_CK3_ENABLE_121003_26785313_RMTM_EVENT_V1
namespace {
bool RmtmEventSceneSample267V1(ReadonlyContext&q,const ck3_11906::MainThreadExecutionStampV1&s,const OwnerInvocationV1&i,std::uint64_t wall,std::uint64_t mono,RmtmEventFrame267V1&out,std::string&why){
 if(!LydSceneSample267V1(q,s,i,LydKind267V1::events,wall,mono,out,why))return false;
 FullscreenEventFrame267V1 full;if(!FullscreenEventSceneSample267V1(q,s,i,wall,mono,full,why)||!Same(full.core,out.core)||full.scene.context!=out.scene.context||full.scene.jomini!=out.scene.jomini||full.scene.global!=out.scene.global)return false;
 out.fullscreen_scene=full.scene;out.fullscreen_witness=std::move(full.witness);out.fullscreen_bindings=BindFullscreenEventImage267V1(q.bindings.module_base,kExecutableSha256);return out.fullscreen_bindings.verified&&Owner(q,s,i);
}
}
bool ReadRmtmEventFrameOnOwner267V1(const ReadonlyBindings&b,ck3_11906::MainThreadQueryMailboxV1*m,const ck3_11906::MainThreadQueryTicketV1&t,const ck3_11906::MainThreadExecutionStampV1&s,void*context,std::uint64_t wall,std::uint64_t mono,RmtmEventFrame267V1&out,std::string&why)noexcept{
 out={};why="rmtm_event_original_main_owner_unavailable";
 try{if(!m||m->offline_fixture||!context||m->permitted_executor_quattuortrigintary!=&ExecuteRmtmOnOwner267V1)return false;ReadonlyContext q;q.bindings=b;q.mailbox=m;q.ticket=t;q.mode=ReadonlyModeV1::core_only;const OwnerInvocationV1 i{&ExecuteRmtmOnOwner267V1,context};RmtmEventFrame267V1 a,z;
 if(!RmtmEventSceneSample267V1(q,s,i,wall,mono,a,why)){out=std::move(a);return false;}out=a;
 if(!RmtmEventSceneSample267V1(q,s,i,wall,mono,z,why)||!Same(a.core,z.core)||a.scene!=z.scene||a.witness!=z.witness||a.name_witness!=z.name_witness||a.fullscreen_scene!=z.fullscreen_scene||a.fullscreen_witness!=z.fullscreen_witness||!Owner(q,s,i)){why="rmtm_event_actual_world_or_complete_channels_changed";return false;}out=std::move(z);why.clear();return true;
 }catch(...){why="rmtm_event_actual_owner_capture_exception";return false;}
}
#endif
