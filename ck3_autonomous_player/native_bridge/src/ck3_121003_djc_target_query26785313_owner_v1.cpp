#include "xar_bridge/ck3_121003_djc_target_query26785313_owner_v1.hpp"
#include <algorithm>
#include <atomic>
#include <chrono>
#include <limits>
#include <mutex>
#include <windows.h>
namespace xar::ck3_121003::build26785313 {namespace {
std::uint64_t Wall()noexcept{const auto t=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();return t>0?static_cast<std::uint64_t>(t):0;}
[[maybe_unused]]bool Time(const DjcTargetQueryContext267V1&q)noexcept{const auto t=Wall();return t&&t<q.request.deadline_unix_ms&&q.monotonic_deadline_ms&&GetTickCount64()<q.monotonic_deadline_ms;}
[[maybe_unused]]bool Same(const ck3_1210::CoreSnapshotPrefix&a,const ck3_1210::CoreSnapshotPrefix&b)noexcept{return a.clock.date_raw==b.clock.date_raw&&a.clock.speed==b.clock.speed&&a.clock.paused==b.clock.paused&&a.local_player_id==b.local_player_id&&a.map_ready==b.map_ready&&a.has_played_character==b.has_played_character&&a.played_character_id==b.played_character_id&&a.played_character_alive==b.played_character_alive;}
[[maybe_unused]]bool Core(DjcTargetQueryContext267V1&q,const ck3_11906::MainThreadExecutionStampV1&s){
 if(!Time(q)||!q.mailbox||q.mailbox->offline_fixture||!q.connection_generation||q.mailbox->permitted_executor_octonary!=&ExecuteDjcTargetQueryOnOwner267V1)return false;
 ReadonlyObservation r;if(!ReadDjcTargetQueryCoreOnOwner267V1(q.bindings,q.mailbox,q.ticket,s,&q,r)||!r.available||r.offline_fixture||!r.main_owner_observed||!Same(r.core,q.request.expected))return false;
 q.result.core_available=true;q.result.observed=r.core;q.result.connection_generation=q.connection_generation;q.result.ticket_sequence=q.ticket.sequence;q.result.pump_epoch=s.pump_epoch;q.result.thread_id=s.thread_id;return true;
}
}
struct DjcTargetQuerySession267V1::State {
 std::atomic_bool unknown{false};std::mutex mutex;std::uint64_t generation=GetTickCount64()?GetTickCount64():1,sequence=0;
 // Only the latest query can later supply a private selector. No unbounded list.
 DjcRawTarget267V1 latest{};ck3_1210::CoreSnapshotPrefix source{};std::uint64_t connection=0,deadline=0;
};
DjcTargetQuerySession267V1::DjcTargetQuerySession267V1():state_(std::make_unique<State>()){}
DjcTargetQuerySession267V1::~DjcTargetQuerySession267V1()=default;
void BlockDjcTargetQueryUnknown267V1(DjcTargetQuerySession267V1&s)noexcept{s.state_->unknown.store(true,std::memory_order_release);}
void ArmDjcTargetQueryDeadline267V1(DjcTargetQueryContext267V1&q)noexcept{q.monotonic_deadline_ms=0;const auto now=Wall();if(now&&q.request.deadline_unix_ms>now)q.monotonic_deadline_ms=GetTickCount64()+(std::min)(q.request.deadline_unix_ms-now,std::uint64_t{8000});}
bool ExecuteDjcTargetQueryInner267V1(DjcTargetQueryContext267V1&q,[[maybe_unused]]const ck3_11906::MainThreadExecutionStampV1&s)noexcept{
 q.result={};q.result.raw.target_character_id=q.request.target_character_id;q.result.reason="current_djc_target_query_default_off";
#if defined(XAR_CK3_ENABLE_121003_26785313_DJC_DECLARATIONS_V1) && XAR_CK3_ENABLE_121003_26785313_DJC_DECLARATIONS_V1
 try{
  const auto reject=[&](DjcTargetQueryStatus267V1 v,const char*why){q.result.status=v;q.result.reason=why;return true;};
  if(!q.session||!DjcTargetQueryRequestShape267V1(q.request))return reject(DjcTargetQueryStatus267V1::unavailable,"current_djc_request_or_session_unavailable");
  auto&state=*q.session->state_;std::scoped_lock lock(state.mutex);
  if(state.unknown.load(std::memory_order_acquire))return reject(DjcTargetQueryStatus267V1::indeterminate,"current_djc_prior_scratch_unknown_retained");
  if(!Time(q))return reject(DjcTargetQueryStatus267V1::expired,"current_djc_original_deadline_expired");
  q.bindings=BindReadonlyImage(reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)),kExecutableSha256);
  const auto raw=BindCurrentDjcDeclarations267V1(q.bindings.module_base,kExecutableSha256);
  if(!raw.verified||!Core(q,s))return reject(DjcTargetQueryStatus267V1::unavailable,"current_djc_actual_owner_core_unavailable");
  q.native_query_entered=true;
  if(!ReadCurrentDjcTargetRaw267V1(q.bindings,raw,q.request.expected,q.request.target_character_id,q.monotonic_deadline_ms,q.result.raw)){
   if(!q.result.raw.cleanup_known){state.unknown.store(true);return reject(DjcTargetQueryStatus267V1::indeterminate,"current_djc_scratch_cleanup_unknown_no_replay");}
   q.result.status=Time(q)?DjcTargetQueryStatus267V1::unavailable:DjcTargetQueryStatus267V1::expired;q.result.reason=q.result.raw.reason;return true;
  }
  if(!Core(q,s)||!VerifyCurrentDjcDeclarationsImage267V1(q.bindings.module_base))return reject(Time(q)?DjcTargetQueryStatus267V1::stale_core:DjcTargetQueryStatus267V1::expired,"current_djc_post_query_source_changed");
  if(state.sequence==(std::numeric_limits<std::uint64_t>::max)()){state.unknown.store(true);return reject(DjcTargetQueryStatus267V1::indeterminate,"current_djc_provider_sequence_exhausted");}
  state.latest=q.result.raw;state.source=q.request.expected;state.connection=q.connection_generation;state.deadline=q.request.deadline_unix_ms;
  q.result.provider_generation=state.generation;q.result.query_sequence=++state.sequence;q.result.status=DjcTargetQueryStatus267V1::available;q.result.reason.clear();return true;
 }catch(...){if(q.session&&q.native_query_entered)BlockDjcTargetQueryUnknown267V1(*q.session);q.result.status=q.native_query_entered?DjcTargetQueryStatus267V1::indeterminate:DjcTargetQueryStatus267V1::unavailable;q.result.reason="current_djc_query_exception_retained";}
#endif
 return true;
}
bool ExecuteDjcTargetQueryOnOwner267V1(void*p,const ck3_11906::MainThreadExecutionStampV1&s)noexcept{if(!p)return false;auto&q=*static_cast<DjcTargetQueryContext267V1*>(p);__try{return ExecuteDjcTargetQueryInner267V1(q,s);}__except(EXCEPTION_EXECUTE_HANDLER){if(q.session)BlockDjcTargetQueryUnknown267V1(*q.session);q.result.status=DjcTargetQueryStatus267V1::indeterminate;return true;}}
}
