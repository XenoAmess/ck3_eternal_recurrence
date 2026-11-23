#if defined(XAR_CK3_ENABLE_121003_26785313_CCC_EVENT_V1) && XAR_CK3_ENABLE_121003_26785313_CCC_EVENT_V1
bool ReadCccEventFrameOnOwner267V1(const ReadonlyBindings&b,ck3_11906::MainThreadQueryMailboxV1*m,const ck3_11906::MainThreadQueryTicketV1&t,const ck3_11906::MainThreadExecutionStampV1&s,void*context,std::uint64_t wall,std::uint64_t mono,CccEventFrame267V1&out,std::string&reason)noexcept{
 const auto kind=LydKind267V1::events;
 out={};reason="ccc_event_original_main_owner_unavailable";try{if(!m||m->offline_fixture||!context||m->permitted_executor_duotrigintary!=&ExecuteCccOnOwner267V1)return false;ReadonlyContext q;q.bindings=b;q.mailbox=m;q.ticket=t;q.mode=kind==LydKind267V1::readback?ReadonlyModeV1::core_and_raw_resources:ReadonlyModeV1::core_only;const OwnerInvocationV1 i{&ExecuteCccOnOwner267V1,context};CccEventFrame267V1 a,z;
 if(!LydSceneSample267V1(q,s,i,kind,wall,mono,a,reason)){if(a.facts_verified){out.core=a.core;out.facts_verified=true;}return false;}out.core=a.core;out.facts_verified=true;if(!LydSceneSample267V1(q,s,i,kind,wall,mono,z,reason)||!Same(a.core,z.core)||a.scene!=z.scene||a.witness!=z.witness||!Owner(q,s,i)){reason="ccc_event_actual_world_or_fixed_gui_source_changed_between_samples";return false;}out=std::move(z);reason.clear();return true;
 }catch(...){reason="ccc_event_actual_owner_frame_exception";return false;}
}

#endif
