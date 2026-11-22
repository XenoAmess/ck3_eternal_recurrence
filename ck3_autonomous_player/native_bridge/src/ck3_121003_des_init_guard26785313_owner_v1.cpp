#include "xar_bridge/ck3_121003_des_init_guard26785313_owner_v1.hpp"
#include <algorithm>
#include <atomic>
#include <chrono>
#include <limits>
#include <mutex>
#include <windows.h>
namespace xar::ck3_121003::build26785313 {namespace {
std::uint64_t Wall()noexcept{const auto t=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();return t>0?static_cast<std::uint64_t>(t):0;}
[[maybe_unused]]bool Time(const DesInitGuardContext267V1&q)noexcept{const auto t=Wall();return t&&t<q.request.deadline_unix_ms&&q.monotonic_deadline_ms&&GetTickCount64()<q.monotonic_deadline_ms;}
[[maybe_unused]]bool Same(const ck3_1210::CoreSnapshotPrefix&a,const ck3_1210::CoreSnapshotPrefix&b)noexcept{return a.clock.date_raw==b.clock.date_raw&&a.clock.speed==b.clock.speed&&a.clock.paused==b.clock.paused&&a.local_player_id==b.local_player_id&&a.map_ready==b.map_ready&&a.has_played_character==b.has_played_character&&a.played_character_id==b.played_character_id&&a.played_character_alive==b.played_character_alive;}
[[maybe_unused]]bool SameFrame(const DesInitGuardFrame267V1&a,const DesInitGuardFrame267V1&b)noexcept{return a.facts_verified&&b.facts_verified&&Same(a.core,b.core)&&a.game==b.game&&a.jomini==b.jomini&&a.storage==b.storage&&a.data==b.data&&a.players==b.players&&a.player==b.player&&a.actor==b.actor;}
[[maybe_unused]]bool Frame(DesInitGuardContext267V1&q,const ck3_11906::MainThreadExecutionStampV1&s,DesInitGuardFrame267V1&out){
 if(!Time(q)||!q.mailbox||q.mailbox->offline_fixture||!q.connection_generation||q.mailbox->permitted_executor_septemvigintary!=&ExecuteDesInitGuardOnOwner267V1)return false;
 q.bindings=BindReadonlyImage(reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)),kExecutableSha256);std::string reason;
 const bool good=ReadDesInitGuardFrameOnOwner267V1(q.bindings,q.mailbox,q.ticket,s,&q,q.request.deadline_unix_ms,q.monotonic_deadline_ms,out,reason);
 if(out.facts_verified){q.result.facts_available=true;q.result.facts=out.core;q.result.connection_generation=q.connection_generation;q.result.ticket_sequence=q.ticket.sequence;q.result.pump_epoch=s.pump_epoch;q.result.thread_id=s.thread_id;}
 if(!good){q.result.reason=reason;return false;}if(!Same(out.core,q.request.expected)){q.result.status=DesInitGuardStatus267V1::stale_source;q.result.reason="des_init_guard_actual_core_changed";return false;}return Time(q);
}
}
struct DesInitGuardSession267V1::State{std::atomic_bool unknown{false};std::mutex mutex;std::uint64_t generation=GetTickCount64()?GetTickCount64():1,query_sequence=0;};
DesInitGuardSession267V1::DesInitGuardSession267V1():state_(std::make_unique<State>()){}
DesInitGuardSession267V1::~DesInitGuardSession267V1()=default;
DesInitGuardSession267V1&RetainedDesInitGuardSession267V1(){static DesInitGuardSession267V1 s;return s;}
void BlockDesInitGuardUnknown267V1(DesInitGuardSession267V1&s)noexcept{s.state_->unknown.store(true,std::memory_order_release);}
void ArmDesInitGuardDeadline267V1(DesInitGuardContext267V1&q)noexcept{q.monotonic_deadline_ms=0;const auto t=Wall();if(t&&q.request.deadline_unix_ms>t)q.monotonic_deadline_ms=GetTickCount64()+(std::min)(q.request.deadline_unix_ms-t,std::uint64_t{8000});}
bool ExecuteDesInitGuardInner267V1(DesInitGuardContext267V1&q,[[maybe_unused]]const ck3_11906::MainThreadExecutionStampV1&s)noexcept{
 q.result={};q.result.reason="des_init_guard_default_off";
#if defined(XAR_CK3_ENABLE_121003_26785313_DES_INIT_GUARD_V1) && XAR_CK3_ENABLE_121003_26785313_DES_INIT_GUARD_V1
 try{using S=DesInitGuardStatus267V1;const auto reject=[&](S status,const char*why){q.result.status=status;q.result.reason=why;return true;};if(!q.session||!DesInitGuardRequestShape267V1(q.request))return reject(S::unavailable,"des_init_guard_actual_request_or_session_unavailable");auto&state=*q.session->state_;std::scoped_lock lock(state.mutex);
  if(state.unknown.load(std::memory_order_acquire)){q.result.cleanup_known=false;return reject(S::indeterminate,"des_init_guard_prior_cleanup_unknown_no_permission");}
  if(!Time(q))return reject(S::expired,"des_init_guard_original_deadline_expired");DesInitGuardFrame267V1 before,after;if(!Frame(q,s,before))return true;
  DesInitGuardRaw267V1 raw;std::string reason;const bool good=ReadDesInitGuardRaw267V1(q.bindings,before,q.request.deadline_unix_ms,q.monotonic_deadline_ms,raw,reason);q.native_observation_entered=raw.entered;q.result.cleanup_known=raw.cleanup_known;
  if(!raw.cleanup_known){BlockDesInitGuardUnknown267V1(*q.session);return reject(S::indeterminate,"des_init_guard_owned_scope_cleanup_unknown");}
  if(!good){q.result.reason=reason;q.result.status=Time(q)?S::unavailable:S::expired;return true;}
  if(!Frame(q,s,after)||!SameFrame(before,after))return reject(S::stale_source,"des_init_guard_actual_world_changed_after_predicate");
  if(!Time(q))return reject(S::expired,"des_init_guard_original_deadline_expired_after_predicate");if(state.query_sequence==(std::numeric_limits<std::uint64_t>::max)())return reject(S::unavailable,"des_init_guard_query_capacity_exhausted");
  q.result.source=raw.source;q.result.source_available=true;q.result.provider_generation=state.generation;q.result.query_sequence=++state.query_sequence;q.result.status=S::available;q.result.reason.clear();return true;
 }catch(...){if(q.session&&q.native_observation_entered)BlockDesInitGuardUnknown267V1(*q.session);q.result.source.reset();q.result.source_available=false;q.result.status=q.native_observation_entered?DesInitGuardStatus267V1::indeterminate:DesInitGuardStatus267V1::unavailable;q.result.cleanup_known=!q.native_observation_entered;q.result.reason="des_init_guard_owner_exception_no_permission";}
#endif
 return true;
}
bool ExecuteDesInitGuardOnOwner267V1(void*p,const ck3_11906::MainThreadExecutionStampV1&s)noexcept{if(!p)return false;auto&q=*static_cast<DesInitGuardContext267V1*>(p);__try{return ExecuteDesInitGuardInner267V1(q,s);}__except(EXCEPTION_EXECUTE_HANDLER){if(q.session)BlockDesInitGuardUnknown267V1(*q.session);q.result.source.reset();q.result.source_available=false;q.result.status=DesInitGuardStatus267V1::indeterminate;q.result.cleanup_known=false;return true;}}
}
