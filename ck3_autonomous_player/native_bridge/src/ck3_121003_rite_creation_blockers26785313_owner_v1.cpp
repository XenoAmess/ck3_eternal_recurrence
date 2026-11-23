#include "xar_bridge/ck3_121003_rite_creation_blockers26785313_owner_v1.hpp"
#include <algorithm>
#include <atomic>
#include <chrono>
#include <limits>
#include <mutex>
#include <windows.h>
namespace xar::ck3_121003::build26785313 {namespace {
std::uint64_t Wall()noexcept{const auto t=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();return t>0?static_cast<std::uint64_t>(t):0;}
[[maybe_unused]]bool Time(const RiteBlockersContext267V1&q)noexcept{const auto t=Wall();return t&&t<q.request.deadline_unix_ms&&q.monotonic_deadline_ms&&GetTickCount64()<q.monotonic_deadline_ms;}
[[maybe_unused]]bool Same(const ck3_1210::CoreSnapshotPrefix&a,const ck3_1210::CoreSnapshotPrefix&b)noexcept{return a.clock.date_raw==b.clock.date_raw&&a.clock.speed==b.clock.speed&&a.clock.paused==b.clock.paused&&a.local_player_id==b.local_player_id&&a.map_ready==b.map_ready&&a.has_played_character==b.has_played_character&&a.played_character_id==b.played_character_id&&a.played_character_alive==b.played_character_alive;}
[[maybe_unused]]bool SameFrame(const RiteBlockersFrame267V1&a,const RiteBlockersFrame267V1&b)noexcept{return a.facts_verified&&b.facts_verified&&Same(a.core,b.core)&&a.game==b.game&&a.jomini==b.jomini&&a.storage==b.storage&&a.actor==b.actor;}
[[maybe_unused]]bool Frame(RiteBlockersContext267V1&q,const ck3_11906::MainThreadExecutionStampV1&s,RiteBlockersFrame267V1&out){
 if(!Time(q)||!q.mailbox||q.mailbox->offline_fixture||!q.connection_generation||q.mailbox->permitted_executor_trigintary!=&ExecuteRiteBlockersOnOwner267V1)return false;
 q.bindings=BindReadonlyImage(reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)),kExecutableSha256);std::string reason;
 const bool good=ReadRiteBlockersFrameOnOwner267V1(q.bindings,q.mailbox,q.ticket,s,&q,q.request,q.monotonic_deadline_ms,out,reason);
 if(out.facts_verified){q.result.facts_available=true;q.result.facts=out.core;q.result.connection_generation=q.connection_generation;q.result.ticket_sequence=q.ticket.sequence;q.result.pump_epoch=s.pump_epoch;q.result.thread_id=s.thread_id;}
 if(!good){q.result.reason=reason;return false;}if(!Same(out.core,q.request.expected)){q.result.status=RiteBlockersStatus267V1::stale_source;q.result.reason="rite_creation_blockers_actual_core_changed";return false;}return Time(q);
}
}
struct RiteBlockersSession267V1::State{std::atomic_bool unknown{false};std::mutex mutex;std::uint64_t generation=GetTickCount64()?GetTickCount64():1,query_sequence=0;};
RiteBlockersSession267V1::RiteBlockersSession267V1():state_(std::make_unique<State>()){}
RiteBlockersSession267V1::~RiteBlockersSession267V1()=default;
RiteBlockersSession267V1&RetainedRiteBlockersSession267V1(){static RiteBlockersSession267V1 s;return s;}
void BlockRiteBlockersUnknown267V1(RiteBlockersSession267V1&s)noexcept{s.state_->unknown.store(true,std::memory_order_release);}
void ArmRiteBlockersDeadline267V1(RiteBlockersContext267V1&q)noexcept{q.monotonic_deadline_ms=0;const auto t=Wall();if(t&&q.request.deadline_unix_ms>t)q.monotonic_deadline_ms=GetTickCount64()+(std::min)(q.request.deadline_unix_ms-t,std::uint64_t{8000});}
bool ExecuteRiteBlockersInner267V1(RiteBlockersContext267V1&q,[[maybe_unused]]const ck3_11906::MainThreadExecutionStampV1&s)noexcept{
 q.result={};q.result.reason="rite_creation_blockers_default_off";
#if defined(XAR_CK3_ENABLE_121003_26785313_RITE_CREATION_BLOCKERS_V1) && XAR_CK3_ENABLE_121003_26785313_RITE_CREATION_BLOCKERS_V1
 try{using S=RiteBlockersStatus267V1;const auto reject=[&](S status,const char*why){q.result.status=status;q.result.reason=why;return true;};if(!q.session||!RiteBlockersRequestShape267V1(q.request))return reject(S::unavailable,"rite_creation_blockers_actual_request_or_session_unavailable");auto&state=*q.session->state_;std::scoped_lock lock(state.mutex);
  if(state.unknown.load(std::memory_order_acquire)){q.result.cleanup_known=false;return reject(S::indeterminate,"rite_creation_blockers_prior_cleanup_unknown_no_permission");}
  if(!Time(q))return reject(S::expired,"rite_creation_blockers_original_deadline_expired");RiteBlockersFrame267V1 before,after;if(!Frame(q,s,before))return true;
  RiteBlockersRaw267V1 raw;std::string reason;const bool good=ReadRiteBlockersRaw267V1(q.bindings,before,q.request,q.monotonic_deadline_ms,raw,reason);q.native_observation_entered=raw.entered;q.result.cleanup_known=raw.cleanup_known;
  if(!raw.cleanup_known){BlockRiteBlockersUnknown267V1(*q.session);return reject(S::indeterminate,"rite_creation_blockers_owned_scope_cleanup_unknown");}
  if(!good){q.result.reason=reason;q.result.status=Time(q)?S::unavailable:S::expired;return true;}
  if(raw.source.source_rite_id!=q.request.expected_source_rite_id||raw.source.actor_id!=before.core.played_character_id||!raw.source.sampled_twice)return reject(S::unavailable,"rite_creation_blockers_actual_raw_source_incomplete");
  if(!Frame(q,s,after)||!SameFrame(before,after))return reject(S::stale_source,"rite_creation_blockers_actual_world_changed_after_predicate");
  if(!Time(q))return reject(S::expired,"rite_creation_blockers_original_deadline_expired_after_predicate");if(state.query_sequence==(std::numeric_limits<std::uint64_t>::max)())return reject(S::unavailable,"rite_creation_blockers_query_capacity_exhausted");
  q.result.source=raw.source;q.result.source_available=true;q.result.provider_generation=state.generation;q.result.query_sequence=++state.query_sequence;q.result.status=S::available;q.result.reason.clear();return true;
 }catch(...){if(q.session&&q.native_observation_entered)BlockRiteBlockersUnknown267V1(*q.session);q.result.source.reset();q.result.source_available=false;q.result.status=q.native_observation_entered?RiteBlockersStatus267V1::indeterminate:RiteBlockersStatus267V1::unavailable;q.result.cleanup_known=!q.native_observation_entered;q.result.reason="rite_creation_blockers_owner_exception_no_permission";}
#endif
 return true;
}
bool ExecuteRiteBlockersOnOwner267V1(void*p,const ck3_11906::MainThreadExecutionStampV1&s)noexcept{if(!p)return false;auto&q=*static_cast<RiteBlockersContext267V1*>(p);__try{return ExecuteRiteBlockersInner267V1(q,s);}__except(EXCEPTION_EXECUTE_HANDLER){if(q.session)BlockRiteBlockersUnknown267V1(*q.session);q.result.source.reset();q.result.source_available=false;q.result.status=RiteBlockersStatus267V1::indeterminate;q.result.cleanup_known=false;return true;}}
}
