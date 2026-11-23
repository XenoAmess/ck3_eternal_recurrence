#include "xar_bridge/ck3_121003_rmtm_title_query26785313_owner_v1.hpp"
#include <algorithm>
#include <atomic>
#include <chrono>
#include <limits>
#include <mutex>
#include <windows.h>
namespace xar::ck3_121003::build26785313 {namespace {
std::uint64_t TitleQueryWall()noexcept{const auto t=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();return t>0?static_cast<std::uint64_t>(t):0;}
[[maybe_unused]]bool TitleQueryTime(const RmtmTitleQueryContext267V1&q)noexcept{const auto t=TitleQueryWall();return t&&t<q.request.deadline_unix_ms&&q.monotonic_deadline_ms&&GetTickCount64()<q.monotonic_deadline_ms;}
[[maybe_unused]]bool TitleQuerySame(const ck3_1210::CoreSnapshotPrefix&a,const ck3_1210::CoreSnapshotPrefix&b)noexcept{return a.clock.date_raw==b.clock.date_raw&&a.clock.speed==b.clock.speed&&a.clock.paused==b.clock.paused&&a.local_player_id==b.local_player_id&&a.map_ready==b.map_ready&&a.has_played_character==b.has_played_character&&a.played_character_id==b.played_character_id&&a.played_character_alive==b.played_character_alive;}
[[maybe_unused]]bool TitleQueryFrame(RmtmTitleQueryContext267V1&q,const ck3_11906::MainThreadExecutionStampV1&s,RmtmTitleFrame267V1&f){
 if(!TitleQueryTime(q)){q.result.status=RmtmTitleQueryStatus267V1::expired;q.result.reason="rmtm_title_query_original_deadline_expired_before_frame";return false;}
 if(!q.mailbox||q.mailbox->offline_fixture||!q.connection_generation||q.mailbox->permitted_executor_tritrigintary!=&ExecuteRmtmTitleQueryOnOwner267V1){q.result.reason="rmtm_title_query_actual_owner_slot_or_connection_unavailable";return false;}
 q.bindings=BindReadonlyImage(reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)),kExecutableSha256);std::string why;
 const bool good=ReadRmtmTitleQueryFrameOnOwner267V1(q.bindings,q.mailbox,q.ticket,s,&q,q.request,q.monotonic_deadline_ms,f,why);
 if(f.facts_verified){q.result.facts_available=true;q.result.facts=f.core;q.result.connection_generation=q.connection_generation;q.result.ticket_sequence=q.ticket.sequence;q.result.pump_epoch=s.pump_epoch;q.result.thread_id=s.thread_id;}
 if(!good){q.result.reason=why;return false;}if(!TitleQuerySame(f.core,q.request.expected)){q.result.status=RmtmTitleQueryStatus267V1::stale_source;q.result.reason="rmtm_title_query_actual_core_changed";return false;}return TitleQueryTime(q);
}
}
struct RmtmTitleQuerySession267V1::State{std::atomic_bool unknown{false};std::mutex mutex;std::uint64_t generation=GetTickCount64()?GetTickCount64():1,query_sequence=0;};
RmtmTitleQuerySession267V1::RmtmTitleQuerySession267V1():state_(std::make_unique<State>()){}
RmtmTitleQuerySession267V1::~RmtmTitleQuerySession267V1()=default;
RmtmTitleQuerySession267V1&RetainedRmtmTitleQuerySession267V1(){static RmtmTitleQuerySession267V1 s;return s;}
void BlockRmtmTitleQueryUnknown267V1(RmtmTitleQuerySession267V1&s)noexcept{s.state_->unknown.store(true,std::memory_order_release);}
void ArmRmtmTitleQueryDeadline267V1(RmtmTitleQueryContext267V1&q)noexcept{q.monotonic_deadline_ms=0;const auto t=TitleQueryWall();if(t&&q.request.deadline_unix_ms>t)q.monotonic_deadline_ms=GetTickCount64()+(std::min)(q.request.deadline_unix_ms-t,std::uint64_t{8000});}
bool ExecuteRmtmTitleQueryInner267V1(RmtmTitleQueryContext267V1&q,[[maybe_unused]]const ck3_11906::MainThreadExecutionStampV1&s)noexcept{
 q.result={};q.captured_full_title_id=0xFFFFFFFFU;q.result.reason="rmtm_title_query_default_off";
#if defined(XAR_CK3_ENABLE_121003_26785313_RMTM_TITLE_QUERY_V1) && XAR_CK3_ENABLE_121003_26785313_RMTM_TITLE_QUERY_V1 && defined(XAR_CK3_ENABLE_121003_26785313_RMTM_TITLE_V1) && XAR_CK3_ENABLE_121003_26785313_RMTM_TITLE_V1
 try{using Status=RmtmTitleQueryStatus267V1;const auto reject=[&](Status status,const char*why){q.result.status=status;q.result.reason=why;return true;};if(!q.session||!RmtmTitleQueryRequestShape267V1(q.request))return reject(Status::unavailable,"rmtm_title_query_actual_request_or_session_unavailable");auto&state=*q.session->state_;std::scoped_lock lock(state.mutex);
  if(state.unknown.load(std::memory_order_acquire)){q.result.cleanup_known=false;return reject(Status::indeterminate,"rmtm_title_query_prior_family_read_unknown");}
  if(!TitleQueryTime(q))return reject(Status::expired,"rmtm_title_query_original_deadline_expired");RmtmTitleFrame267V1 before,after;if(!TitleQueryFrame(q,s,before))return true;
  std::string why;bool cleanup=true;
  if(!CaptureRmtmTitleQueryPrimary267V1(q.bindings,before,q.request,q.monotonic_deadline_ms,q.captured_full_title_id,q.native_observation_entered,cleanup,why)){q.result.cleanup_known=cleanup;if(!cleanup){state.unknown.store(true,std::memory_order_release);q.result.status=Status::indeterminate;}q.result.reason=why;return true;}
  // The guard is created here from actual owner-side primary Title capture.
  // The public claim has no field able to choose or inject this identifier.
  RmtmTitleRequest267V1 inner{before.core,q.captured_full_title_id,q.request.deadline_unix_ms};RmtmTitleRaw267V1 raw;
  const bool good=ReadRmtmTitleRaw267V1(q.bindings,before,inner,q.monotonic_deadline_ms,raw,why);q.native_observation_entered=q.native_observation_entered||raw.entered;q.result.cleanup_known=raw.cleanup_known;
  if(!raw.cleanup_known){state.unknown.store(true,std::memory_order_release);return reject(Status::indeterminate,"rmtm_title_query_original_native_read_cleanup_unknown");}if(!good){q.result.reason=why;if(!TitleQueryTime(q))q.result.status=Status::expired;return true;}
  if(!TitleQueryFrame(q,s,after))return true;
  std::uint32_t observed=0xFFFFFFFFU;if(!CaptureRmtmTitleQueryPrimary267V1(q.bindings,after,q.request,q.monotonic_deadline_ms,observed,q.native_observation_entered,cleanup,why)){q.result.cleanup_known=cleanup;if(!cleanup){state.unknown.store(true,std::memory_order_release);q.result.status=Status::indeterminate;}q.result.reason=why;return true;}
  if(!TitleQuerySame(before.core,after.core)||before.game!=after.game||before.jomini!=after.jomini||before.storage!=after.storage||before.actor!=after.actor||before.data!=after.data||before.players!=after.players||before.player!=after.player||q.captured_full_title_id!=observed||raw.source.full_title_id!=observed)return reject(Status::stale_source,"rmtm_title_query_original_primary_title_or_world_changed");
  if(!TitleQueryTime(q))return reject(Status::expired,"rmtm_title_query_original_deadline_expired_after_read");
  RmtmTitleQuerySource267V1 source{after.core.played_character_id,std::move(raw.source)};if(!RmtmTitleQuerySourceShape267V1(source,after.core))return reject(Status::unavailable,"rmtm_title_query_actual_complete_source_shape_unavailable");
  if(state.query_sequence==(std::numeric_limits<std::uint64_t>::max)())return reject(Status::unavailable,"rmtm_title_query_private_sequence_exhausted");
  q.result.source=std::move(source);q.result.source_available=true;q.result.status=Status::available;q.result.provider_generation=state.generation;q.result.query_sequence=++state.query_sequence;q.result.reason.clear();return true;
 }catch(...){if(q.session)BlockRmtmTitleQueryUnknown267V1(*q.session);q.result.source.reset();q.result.source_available=false;q.result.cleanup_known=false;q.result.status=RmtmTitleQueryStatus267V1::indeterminate;q.result.reason="rmtm_title_query_owner_local_copy_unknown";return true;}
#endif
 return true;
}
bool ExecuteRmtmTitleQueryOnOwner267V1(void*p,const ck3_11906::MainThreadExecutionStampV1&s)noexcept{if(!p)return false;auto&q=*static_cast<RmtmTitleQueryContext267V1*>(p);__try{return ExecuteRmtmTitleQueryInner267V1(q,s);}__except(EXCEPTION_EXECUTE_HANDLER){if(q.session)BlockRmtmTitleQueryUnknown267V1(*q.session);q.result.source.reset();q.result.source_available=false;q.result.cleanup_known=false;q.result.status=RmtmTitleQueryStatus267V1::indeterminate;q.result.reason="rmtm_title_query_original_owner_exception_unknown";return true;}}
}
