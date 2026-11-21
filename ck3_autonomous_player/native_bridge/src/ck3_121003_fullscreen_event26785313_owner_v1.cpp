#include "xar_bridge/ck3_121003_fullscreen_event26785313_owner_v1.hpp"
#include <algorithm>
#include <atomic>
#include <chrono>
#include <limits>
#include <mutex>
#include <windows.h>
namespace xar::ck3_121003::build26785313 {namespace {
std::uint64_t Wall()noexcept{const auto t=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();return t>0?static_cast<std::uint64_t>(t):0;}
[[maybe_unused]]bool Time(const FullscreenEventContext267V1&q)noexcept{const auto t=Wall();return t&&t<q.request.deadline_unix_ms&&q.monotonic_deadline_ms&&GetTickCount64()<q.monotonic_deadline_ms;}
[[maybe_unused]]bool SameCore(const ck3_1210::CoreSnapshotPrefix&a,const ck3_1210::CoreSnapshotPrefix&b)noexcept{return a.clock.date_raw==b.clock.date_raw&&a.clock.speed==b.clock.speed&&a.clock.paused==b.clock.paused&&a.local_player_id==b.local_player_id&&a.map_ready==b.map_ready&&a.has_played_character==b.has_played_character&&a.played_character_id==b.played_character_id&&a.played_character_alive==b.played_character_alive;}
[[maybe_unused]]bool SameFrame(const FullscreenEventFrame267V1&a,const FullscreenEventFrame267V1&b)noexcept{return a.facts_verified&&b.facts_verified&&SameCore(a.core,b.core)&&a.scene==b.scene&&a.witness==b.witness;}
[[maybe_unused]]bool Frame(FullscreenEventContext267V1&q,const ck3_11906::MainThreadExecutionStampV1&s,FullscreenEventFrame267V1&out){
 if(!Time(q)||!q.mailbox||q.mailbox->offline_fixture||!q.connection_generation||q.mailbox->permitted_executor_quattuordenary!=&ExecuteFullscreenEventOnOwner267V1)return false;
 q.bindings=BindReadonlyImage(reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)),kExecutableSha256);std::string reason;const bool good=ReadFullscreenEventFrameOnOwner267V1(q.bindings,q.mailbox,q.ticket,s,&q,q.request.deadline_unix_ms,q.monotonic_deadline_ms,out,reason);
 if(out.facts_verified){q.result.facts_available=true;q.result.facts=out.core;q.result.connection_generation=q.connection_generation;q.result.ticket_sequence=q.ticket.sequence;q.result.pump_epoch=s.pump_epoch;q.result.thread_id=s.thread_id;}
 if(!good){q.result.reason=reason;return false;}if(!SameCore(out.core,q.request.expected)){q.result.reason="fullscreen_event_actual_core_changed";return false;}return Time(q);
}
[[maybe_unused]]bool Observe(FullscreenEventContext267V1&q,const FullscreenEventFrame267V1&frame,FullscreenEventRaw267V1&raw){
 const auto b=BindFullscreenEventImage267V1(q.bindings.module_base,kExecutableSha256);if(!b.verified){q.result.reason="fullscreen_event_actual_current_image_unavailable";return false;}std::string reason;const bool good=ReadFullscreenEventRaw267V1(q.bindings,b,q.request.expected,frame.scene,q.monotonic_deadline_ms,raw,reason);q.native_observation_entered=q.native_observation_entered||raw.native_read_entered;q.result.cleanup_known=raw.cleanup_known;
 if(!good){q.result.reason=reason;return false;}q.result.source_available=true;q.result.source=raw.source;return Time(q);
}
}
struct FullscreenEventSession267V1::State{
 struct Lease{FullscreenEventFrame267V1 frame;FullscreenEventRaw267V1 raw;FullscreenEventRequest267V1 request;std::uint64_t query=0,connection=0,mono=0;bool consumed=false;};
struct Claim{std::uint64_t sequence=0;std::string id;std::uintptr_t game=0,jomini=0;std::int32_t actor=-1,instance=-1;};
 std::atomic_bool unknown{false};std::mutex mutex;std::uint64_t generation=GetTickCount64()?GetTickCount64():1,query_sequence=0,claim_sequence=0;std::optional<Lease>latest;std::vector<Claim>claims;
};
FullscreenEventSession267V1::FullscreenEventSession267V1():state_(std::make_unique<State>()){}
FullscreenEventSession267V1::~FullscreenEventSession267V1()=default;
void BlockFullscreenEventUnknown267V1(FullscreenEventSession267V1&s)noexcept{s.state_->unknown.store(true,std::memory_order_release);}
FullscreenEventSession267V1& RetainedFullscreenEventSession267V1(){static FullscreenEventSession267V1 retained;return retained;}
void ArmFullscreenEventDeadline267V1(FullscreenEventContext267V1&q)noexcept{q.monotonic_deadline_ms=0;const auto t=Wall();if(t&&q.request.deadline_unix_ms>t)q.monotonic_deadline_ms=GetTickCount64()+(std::min)(q.request.deadline_unix_ms-t,std::uint64_t{8000});}
bool ExecuteFullscreenEventInner267V1(FullscreenEventContext267V1&q,[[maybe_unused]]const ck3_11906::MainThreadExecutionStampV1&s)noexcept{
 q.result={};q.result.action=q.request.action;q.result.provider_generation=q.request.provider_generation;q.result.query_sequence=q.request.query_sequence;q.result.instance_id=q.request.instance_id;q.result.reason="current_fullscreen_event_default_off";
#if defined(XAR_CK3_ENABLE_121003_26785313_FULLSCREEN_EVENT_V1) && XAR_CK3_ENABLE_121003_26785313_FULLSCREEN_EVENT_V1
 try{using S=FullscreenEventStatus267V1;const auto reject=[&](S status,const char*why){q.result.status=status;q.result.reason=why;return true;};if(!q.session||!FullscreenEventRequestShape267V1(q.request))return reject(S::unavailable,"fullscreen_event_actual_request_or_retained_session_unavailable");auto&state=*q.session->state_;std::scoped_lock lock(state.mutex);
  for(const auto&claim:state.claims)if(claim.id==q.request.id()){q.result.claim_sequence=claim.sequence;return reject(S::claim_consumed,"fullscreen_event_original_effect_id_retained_no_replay");}
  if(!Time(q))return reject(S::expired,"fullscreen_event_original_deadline_expired");FullscreenEventFrame267V1 frame;if(!Frame(q,s,frame))return true;
  if(state.unknown.load(std::memory_order_acquire)){q.result.cleanup_known=false;return reject(S::indeterminate,"fullscreen_event_prior_native_completion_unknown_no_retry");}
  if(state.claims.size()>=64||state.query_sequence==(std::numeric_limits<std::uint64_t>::max)())return reject(S::claim_consumed,"fullscreen_event_retained_capacity_exhausted");
  const auto failed=[&]{if(!q.result.cleanup_known){q.result.source_available=false;q.result.source.reset();state.unknown.store(true);q.result.status=S::indeterminate;}else q.result.status=Time(q)?S::unavailable:S::expired;return true;};
  if(q.request.action==FullscreenEventAction267V1::query_fullscreen){state.latest.reset();const auto before=frame;FullscreenEventRaw267V1 raw;if(!Observe(q,frame,raw))return failed();if(!Frame(q,s,frame)||!SameFrame(before,frame))return reject(S::stale_source,"fullscreen_event_actual_core_or_gui_changed_after_read");
   FullscreenEventSession267V1::State::Lease lease{frame,raw,q.request,++state.query_sequence,q.connection_generation,q.monotonic_deadline_ms,false};state.latest=std::move(lease);q.result.provider_generation=state.generation;q.result.query_sequence=state.query_sequence;q.result.status=S::available;q.result.reason.clear();return true;
  }
  if(!state.latest)return reject(S::stale_source,"fullscreen_event_original_private_query_unavailable");auto&lease=*state.latest;
  if(q.request.provider_generation!=state.generation||q.request.query_sequence!=lease.query||q.connection_generation!=lease.connection||q.request.deadline_unix_ms!=lease.request.deadline_unix_ms||!SameCore(q.request.expected,lease.request.expected)||q.request.id()==lease.request.id())return reject(S::stale_source,"fullscreen_event_original_private_query_source_mismatch");
  if(lease.consumed)return reject(S::claim_consumed,"fullscreen_event_original_private_query_consumed");if(GetTickCount64()>=lease.mono)return reject(S::expired,"fullscreen_event_original_query_deadline_expired");q.monotonic_deadline_ms=(std::min)(q.monotonic_deadline_ms,lease.mono);
  FullscreenEventRaw267V1 raw;if(!Observe(q,frame,raw))return failed();const auto before=frame;if(!Frame(q,s,frame)||!SameFrame(before,frame)||!SameFrame(lease.frame,frame)||raw!=lease.raw)return reject(S::stale_source,"fullscreen_event_actual_instance_definition_or_options_changed");
  if(!raw.source.known_ack_admissible||!raw.source.instance_id||q.request.instance_id!=raw.source.instance_id)return reject(S::unavailable,"fullscreen_event_exact_known_definition_single_option_or_native_validity_refused");
  for(const auto&claim:state.claims)if(claim.game==raw.game&&claim.jomini==raw.jomini&&claim.actor==q.request.expected.played_character_id&&claim.instance==*raw.source.instance_id)return reject(S::claim_consumed,"fullscreen_event_same_actual_event_instance_claim_retained_no_replay");
  if(!Time(q))return reject(S::expired,"fullscreen_event_original_preclaim_deadline_expired");const auto sequence=state.claim_sequence+1;state.claims.push_back({sequence,std::string(q.request.id()),raw.game,raw.jomini,q.request.expected.played_character_id,*raw.source.instance_id});state.claim_sequence=sequence;lease.consumed=true;q.result.claim_sequence=sequence;
  const auto b=BindFullscreenEventImage267V1(q.bindings.module_base,kExecutableSha256);const auto call=AcknowledgeKnownFullscreenEventRaw267V1(q.bindings,b,q.request.expected,frame.scene,q.monotonic_deadline_ms,raw);q.result.effect_attempted=call.effect_entered;q.result.native_returned=call.status==FullscreenEventRawCallStatus267V1::returned;q.result.cleanup_known=call.cleanup_known;
  if(!call.cleanup_known||call.status==FullscreenEventRawCallStatus267V1::indeterminate){q.result.source_available=false;q.result.source.reset();state.unknown.store(true);return reject(S::indeterminate,"fullscreen_event_native_select_completion_unknown_no_replay");}
  if(call.status!=FullscreenEventRawCallStatus267V1::returned)return reject(S::stale_source,"fullscreen_event_pre_effect_refused_original_claim_retained");q.result.status=S::ack_dispatched;q.result.reason.clear();return true;
 }catch(...){if(q.session&&(q.native_observation_entered||q.result.effect_attempted))BlockFullscreenEventUnknown267V1(*q.session);q.result.status=q.native_observation_entered||q.result.effect_attempted?FullscreenEventStatus267V1::indeterminate:FullscreenEventStatus267V1::unavailable;if(q.result.status==FullscreenEventStatus267V1::indeterminate){q.result.cleanup_known=false;q.result.source_available=false;q.result.source.reset();}q.result.reason="fullscreen_event_exception_original_claim_retained";}
#endif
 return true;
}
bool ExecuteFullscreenEventOnOwner267V1(void*p,const ck3_11906::MainThreadExecutionStampV1&s)noexcept{if(!p)return false;auto&q=*static_cast<FullscreenEventContext267V1*>(p);__try{return ExecuteFullscreenEventInner267V1(q,s);}__except(EXCEPTION_EXECUTE_HANDLER){if(q.session)BlockFullscreenEventUnknown267V1(*q.session);q.result.status=FullscreenEventStatus267V1::indeterminate;q.result.cleanup_known=false;q.result.source_available=false;q.result.source.reset();return true;}}
} // namespace
