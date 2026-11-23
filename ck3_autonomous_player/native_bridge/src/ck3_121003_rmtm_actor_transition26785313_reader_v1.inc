#if defined(XAR_CK3_ENABLE_121003_26785313_RMTM_TRANSITION_V1) && XAR_CK3_ENABLE_121003_26785313_RMTM_TRANSITION_V1
namespace {
bool RmtmRoleWorldSample267V1(ReadonlyContext&q,const ck3_11906::MainThreadExecutionStampV1&s,const OwnerInvocationV1&i,std::uint64_t wall,std::uint64_t mono,RmtmRoleFrame267V1&out,std::string&reason){
 const auto valid=[&]{const auto n=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();return n>0&&wall&&mono&&static_cast<std::uint64_t>(n)<wall&&GetTickCount64()<mono&&Owner(q,s,i);};
 if(!valid()||!Read(q,s,i)||!q.observation.available||q.observation.offline_fixture||!q.observation.main_owner_observed){reason="rmtm_actual_paused_living_core_or_owner_unavailable";return false;}
 auto&w=out.world;w.core=q.observation.core;out.facts_verified=true;
 const auto&b=q.bindings.core;std::uintptr_t game=0,jomini=0,storage=0,data=0,players=0;std::int32_t player=-1,id=-1;std::uint32_t magic=0;
 if(!At(reinterpret_cast<std::uintptr_t>(b.game_state_slot),0,game)||!At(reinterpret_cast<std::uintptr_t>(b.jomini_state_slot),0,jomini)||!At(reinterpret_cast<std::uintptr_t>(b.character_storage_slot),0,storage)||!At(game,0xA0,data)||!data||!At(jomini,0x18,players)||!players){reason="rmtm_actual_world_storage_identity_unavailable";return false;}
 w.game=reinterpret_cast<void*>(game);w.jomini=reinterpret_cast<void*>(jomini);w.storage=reinterpret_cast<void*>(storage);w.data=reinterpret_cast<void*>(data);w.players=reinterpret_cast<void*>(players);
 w.player=b.get_local_player(w.jomini);w.actor=ck3_1210::ResolveCoreCharacter(b,w.core.played_character_id);
 if(!w.player||!w.actor||!At(reinterpret_cast<std::uintptr_t>(w.player),0x70,player)||player!=w.core.local_player_id||!At(reinterpret_cast<std::uintptr_t>(w.actor),0x18,id)||id!=w.core.played_character_id||!At(reinterpret_cast<std::uintptr_t>(w.actor),0x1C,magic)||magic!=0x43686172||!valid()){reason="rmtm_actual_world_player_or_actor_binding_unavailable";return false;}
 return true;
}
bool SameRmtmWorld267V1(const ck3_1210::DateSentinelObservationV1&a,const ck3_1210::DateSentinelObservationV1&b)noexcept{return Same(a.core,b.core)&&a.game==b.game&&a.jomini==b.jomini&&a.storage==b.storage&&a.data==b.data&&a.players==b.players&&a.player==b.player&&a.actor==b.actor;}
}
bool ReadRmtmRoleFrameOnOwner267V1(const ReadonlyBindings&b,ck3_11906::MainThreadQueryMailboxV1*m,const ck3_11906::MainThreadQueryTicketV1&t,const ck3_11906::MainThreadExecutionStampV1&s,void*context,std::uint64_t wall,std::uint64_t mono,RmtmRoleFrame267V1&out,std::string&reason)noexcept{
 out={};reason="rmtm_original_main_owner_unavailable";try{if(!m||m->offline_fixture||!context||m->permitted_executor_quattuortrigintary!=&ExecuteRmtmOnOwner267V1)return false;
 ReadonlyContext q;q.bindings=b;q.mailbox=m;q.ticket=t;q.mode=ReadonlyModeV1::core_only;const OwnerInvocationV1 i{&ExecuteRmtmOnOwner267V1,context};RmtmRoleFrame267V1 a,z;
 if(!RmtmRoleWorldSample267V1(q,s,i,wall,mono,a,reason)){out=a;return false;}out=a;
 if(!RmtmRoleWorldSample267V1(q,s,i,wall,mono,z,reason)||!SameRmtmWorld267V1(a.world,z.world)||!Owner(q,s,i)){reason="rmtm_actual_world_or_actor_changed_between_owner_samples";return false;}
 out=z;reason.clear();return true;
 }catch(...){reason="rmtm_owner_actual_world_read_exception";return false;}
}
#endif
