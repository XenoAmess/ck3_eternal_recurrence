#if defined(XAR_CK3_ENABLE_121003_26785313_RMTM_TITLE_QUERY_V1) && XAR_CK3_ENABLE_121003_26785313_RMTM_TITLE_QUERY_V1 && defined(XAR_CK3_ENABLE_121003_26785313_RMTM_TITLE_V1) && XAR_CK3_ENABLE_121003_26785313_RMTM_TITLE_V1
bool ReadRmtmTitleQueryFrameOnOwner267V1(const ReadonlyBindings&b,ck3_11906::MainThreadQueryMailboxV1*m,const ck3_11906::MainThreadQueryTicketV1&t,const ck3_11906::MainThreadExecutionStampV1&s,void*context,const RmtmTitleQueryRequest267V1&r,std::uint64_t mono,RmtmTitleFrame267V1&out,std::string&why)noexcept{
 out={};why="rmtm_title_query_actual_owner_frame_unavailable";
 try{if(!m||m->offline_fixture||!context||m->permitted_executor_tritrigintary!=&ExecuteRmtmTitleQueryOnOwner267V1)return false;
  ReadonlyContext q;q.bindings=b;q.mailbox=m;q.ticket=t;q.mode=ReadonlyModeV1::core_only;const OwnerInvocationV1 i{&ExecuteRmtmTitleQueryOnOwner267V1,context};
  const auto valid=[&]{const auto wall=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();return wall>0&&static_cast<std::uint64_t>(wall)<r.deadline_unix_ms&&mono&&GetTickCount64()<mono&&Owner(q,s,i);};
  if(!valid()||!Read(q,s,i)||!q.observation.available||q.observation.offline_fixture||!q.observation.main_owner_observed)return false;
  out.core=q.observation.core;out.facts_verified=true;
  if(!At(reinterpret_cast<std::uintptr_t>(b.core.game_state_slot),0,out.game)||!At(reinterpret_cast<std::uintptr_t>(b.core.jomini_state_slot),0,out.jomini)||!At(reinterpret_cast<std::uintptr_t>(b.core.character_storage_slot),0,out.storage)||!At(out.game,0xA0,out.data)||!At(out.jomini,0x18,out.players))return false;
  out.actor=Resolve(b.core,out.core.played_character_id);out.player=reinterpret_cast<std::uintptr_t>(b.core.get_local_player(reinterpret_cast<void*>(out.jomini)));
  std::uint32_t id=0xFFFFFFFFU,magic=0;std::uintptr_t dead=1;
  if(!out.actor||!out.player||!At(out.actor,0x18,id)||id!=static_cast<std::uint32_t>(out.core.played_character_id)||!At(out.actor,0x1C,magic)||magic!=0x43686172U||!At(out.actor,0x1D0,dead)||dead||!valid())return false;
  why.clear();return true;
 }catch(...){why="rmtm_title_query_actual_frame_copy_unavailable";return false;}
}
#endif
