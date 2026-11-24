#include "xar_bridge/ck3_121003_rmtm_event26785313_owner_v1.hpp"
#include <algorithm>
#include <atomic>
#include <chrono>
#include <limits>
#include <mutex>
#include <windows.h>
namespace xar::ck3_121003::build26785313 {namespace {
std::uint64_t Wall()noexcept{const auto t=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();return t>0?static_cast<std::uint64_t>(t):0;}
[[maybe_unused]]bool Time(const RmtmEventContext267V1&q)noexcept{const auto t=Wall();return t&&t<q.request.deadline_unix_ms&&q.monotonic_deadline_ms&&GetTickCount64()<q.monotonic_deadline_ms;}
[[maybe_unused]]std::uint64_t OriginalMono(const RmtmEventContext267V1&q)noexcept{const auto t=Wall(),m=GetTickCount64();return t&&q.request.deadline_unix_ms>t?q.request.deadline_unix_ms-t>(std::numeric_limits<std::uint64_t>::max)()-m?(std::numeric_limits<std::uint64_t>::max)():m+q.request.deadline_unix_ms-t:0;}
[[maybe_unused]]bool SameCore(const ck3_1210::CoreSnapshotPrefix&a,const ck3_1210::CoreSnapshotPrefix&b)noexcept{return a.clock.date_raw==b.clock.date_raw&&a.clock.speed==b.clock.speed&&a.clock.paused==b.clock.paused&&a.local_player_id==b.local_player_id&&a.map_ready==b.map_ready&&a.has_played_character==b.has_played_character&&a.played_character_id==b.played_character_id&&a.played_character_alive==b.played_character_alive;}
[[maybe_unused]]bool SameFrame(const RmtmEventFrame267V1&a,const RmtmEventFrame267V1&b)noexcept{return a.facts_verified&&b.facts_verified&&SameCore(a.core,b.core)&&a.scene==b.scene&&a.witness==b.witness&&a.name_witness==b.name_witness&&a.fullscreen_scene==b.fullscreen_scene&&a.fullscreen_witness==b.fullscreen_witness&&a.fullscreen_bindings.image==b.fullscreen_bindings.image&&a.fullscreen_bindings.verified==b.fullscreen_bindings.verified;}
[[maybe_unused]]bool Frame(RmtmEventContext267V1&q,const ck3_11906::MainThreadExecutionStampV1&s,RmtmEventFrame267V1&out){
 if(!Time(q)||!q.mailbox||q.mailbox->offline_fixture||!q.connection_generation||q.mailbox->permitted_executor_quattuortrigintary!=&ExecuteRmtmOnOwner267V1){q.result.reason="rmtm_event_actual_owner_custody_unavailable";return false;}
 q.bindings=BindReadonlyImage(reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)),kExecutableSha256);std::string why;const bool good=ReadRmtmEventFrameOnOwner267V1(q.bindings,q.mailbox,q.ticket,s,&q.invocation,q.request.deadline_unix_ms,q.monotonic_deadline_ms,out,why);
 out.connection_generation=q.connection_generation;if(out.facts_verified){q.result.facts_available=true;q.result.facts=out.core;q.result.connection_generation=q.connection_generation;q.result.ticket_sequence=q.ticket.sequence;q.result.pump_epoch=s.pump_epoch;q.result.thread_id=s.thread_id;}
 if(!good){q.result.reason=why;return false;}if(!SameCore(out.core,q.request.expected)){q.result.status=RmtmEventStatus267V1::stale_source;q.result.reason="rmtm_event_actual_core_changed";return false;}return Time(q);
}
[[maybe_unused]]bool Capture(RmtmEventContext267V1&q,const ck3_11906::MainThreadExecutionStampV1&s,RmtmEventFrame267V1&frame,RmtmEventRaw267V1&raw){
 if(!Frame(q,s,frame))return false;std::string why;const bool good=ReadRmtmEventRaw267V1(q.bindings,frame,q.request,q.monotonic_deadline_ms,raw,why);q.observation_entered=q.observation_entered||(raw.fullscreen_channel?raw.fullscreen.native_read_entered:raw.material.native_read_entered);q.result.cleanup_known=q.result.cleanup_known&&(raw.fullscreen_channel?raw.fullscreen.cleanup_known:raw.material.cleanup_known);
 if(!good||!(raw.fullscreen_channel?raw.fullscreen.cleanup_known:raw.material.cleanup_known)){q.result.reason=why.empty()?"rmtm_event_actual_complete_source_unavailable":why;return false;}RmtmEventFrame267V1 after;if(!Frame(q,s,after)||!SameFrame(frame,after)){q.result.reason="rmtm_event_actual_world_changed_after_read";return false;}return Time(q);
}
[[maybe_unused]]bool SameAnchor(const RmtmPrivateCaseAnchor267V1&a,const RmtmPrivateCaseAnchor267V1&b)noexcept {
 return a.full_title_id==b.full_title_id&&a.predecessor==b.predecessor&&
        a.successor==b.successor&&a.completed_days==b.completed_days;
}
[[maybe_unused]]bool PostAnchor(const RmtmEventFrame267V1&f,const RmtmEventRaw267V1&r,
 RmtmPrivateCaseAnchor267V1&out)noexcept {
 return !r.fullscreen_channel&&ReadRmtmPrivateCaseAnchor267V1(f.core,f.connection_generation,
  r.material.manager_census.game,r.material.manager_census.jomini,out)&&
  out.successor&&*out.successor==f.core.played_character_id&&out.predecessor!=f.core.played_character_id&&
  out.completed_days>=5&&out.completed_days<=14;
}
}
struct RmtmEventSession267V1::State{
 struct Lease{RmtmEventFrame267V1 frame;RmtmEventRaw267V1 raw;RmtmEventRequest267V1 request;std::uint64_t sequence=0,connection=0,mono=0;bool consumed=false;std::optional<RmtmPrivateCaseAnchor267V1>post_anchor;};
 struct Claim{std::uint64_t sequence=0;std::string id;std::int32_t instance=0;std::uintptr_t game=0,jomini=0;std::int32_t actor=-1;};std::atomic_bool unknown{false};std::mutex mutex;std::uint64_t generation=GetTickCount64()?GetTickCount64():1,query_sequence=0,claim_sequence=0;std::optional<Lease>latest;std::vector<Claim>claims;std::array<bool,2>ack_spent{};
};
RmtmEventSession267V1::RmtmEventSession267V1():state_(std::make_unique<State>()){}
RmtmEventSession267V1::~RmtmEventSession267V1()=default;
RmtmEventSession267V1&RetainedRmtmEventSession267V1(){static RmtmEventSession267V1 s;return s;}
void BlockRmtmEventUnknown267V1(RmtmEventSession267V1&s)noexcept{s.state_->unknown.store(true,std::memory_order_release);}
void ArmRmtmEventDeadline267V1(RmtmEventContext267V1&q)noexcept{q.monotonic_deadline_ms=0;const auto t=Wall(),m=GetTickCount64();if(t&&q.request.deadline_unix_ms>t)q.monotonic_deadline_ms=m+(std::min)(q.request.deadline_unix_ms-t,std::uint64_t{8000});}
bool ExecuteRmtmEventInner267V1(RmtmEventContext267V1&q,[[maybe_unused]]const ck3_11906::MainThreadExecutionStampV1&s)noexcept{
 q.result={};q.result.action=q.request.action;q.result.provider_generation=q.request.provider_generation;q.result.query_sequence=q.request.query_sequence;q.result.instance_id=q.request.instance_id;q.result.reason="rmtm_event_default_off";
#if defined(XAR_CK3_ENABLE_121003_26785313_RMTM_EVENT_V1) && XAR_CK3_ENABLE_121003_26785313_RMTM_EVENT_V1
 try{using A=RmtmEventAction267V1;using S=RmtmEventStatus267V1;const auto reject=[&](S status,const char*why){q.result.status=status;q.result.reason=why;q.result.source.reset();q.result.source_available=false;return true;};if(!q.session||!RmtmEventRequestShape267V1(q.request))return reject(S::unavailable,"rmtm_event_actual_request_or_session_unavailable");auto&state=*q.session->state_;std::scoped_lock lock(state.mutex);
  for(const auto&c:state.claims)if(c.id==q.request.id()){q.result.claim_sequence=c.sequence;return reject(S::claim_consumed,"rmtm_event_original_effect_id_retained_no_replay");}if(state.unknown.load(std::memory_order_acquire)){q.result.cleanup_known=false;return reject(S::indeterminate,"rmtm_event_prior_unknown_no_permission");}if(!Time(q))return reject(S::expired,"rmtm_event_original_deadline_expired");
  const auto failed=[&]{if(!q.result.cleanup_known){state.unknown.store(true);return reject(S::indeterminate,"rmtm_event_actual_observation_cleanup_unknown");}const auto why=q.result.reason.empty()?std::string("rmtm_event_actual_source_unavailable"):q.result.reason;return reject(Time(q)?S::unavailable:S::expired,why.c_str());};
  if(RmtmEventQuery267V1(q.request.action)){state.latest.reset();RmtmEventFrame267V1 frame;RmtmEventRaw267V1 raw;if(!Capture(q,s,frame,raw))return failed();if(state.query_sequence==(std::numeric_limits<std::uint64_t>::max)())return reject(S::unavailable,"rmtm_event_query_capacity_exhausted");std::optional<RmtmPrivateCaseAnchor267V1>post_anchor;
   RmtmPrivateCaseAnchor267V1 anchor;
   if(q.request.action==A::query_summary&&PostAnchor(frame,raw,anchor))post_anchor=anchor;
   state.latest=RmtmEventSession267V1::State::Lease{frame,raw,q.request,++state.query_sequence,q.connection_generation,q.monotonic_deadline_ms,false,post_anchor};q.result.provider_generation=state.generation;q.result.query_sequence=state.query_sequence;q.result.source=raw.source;q.result.source_available=true;q.result.status=S::available;q.result.reason.clear();return true;}
  if(!state.latest)return reject(S::stale_source,"rmtm_event_actual_original_query_missing");auto&lease=*state.latest;
  if(((q.request.action==RmtmEventAction267V1::ack_summary||q.request.action==RmtmEventAction267V1::choose_post_succession_first_available)&&lease.request.action!=RmtmEventAction267V1::query_summary)||(q.request.action==RmtmEventAction267V1::ack_chaos&&lease.request.action!=RmtmEventAction267V1::query_chaos)){q.result.status=RmtmEventStatus267V1::stale_source;q.result.reason="rmtm_original_channel_query_mismatch";return true;}
 if(q.request.provider_generation!=state.generation||q.request.query_sequence!=lease.sequence||q.connection_generation!=lease.connection||q.request.deadline_unix_ms!=lease.request.deadline_unix_ms||!SameCore(q.request.expected,lease.request.expected)||q.request.id()==lease.request.id())return reject(S::stale_source,"rmtm_event_original_private_query_custody_mismatch");if(lease.consumed)return reject(S::claim_consumed,"rmtm_event_original_private_query_consumed");if(GetTickCount64()>=lease.mono)return reject(S::expired,"rmtm_event_original_query_deadline_expired");q.monotonic_deadline_ms=(std::min)(q.monotonic_deadline_ms,lease.mono);
  RmtmEventFrame267V1 frame;RmtmEventRaw267V1 raw;if(!Capture(q,s,frame,raw))return failed();if(!SameFrame(lease.frame,frame)||raw!=lease.raw)return reject(S::stale_source,"rmtm_event_actual_complete_draft_changed");const bool post=q.request.action==A::choose_post_succession_first_available;
  if(!q.request.instance_id)return reject(S::unavailable,"rmtm_event_actual_instance_missing");
  if(post){
   RmtmPrivateCaseAnchor267V1 anchor;
   if(!lease.post_anchor||!PostAnchor(frame,raw,anchor)||!SameAnchor(*lease.post_anchor,anchor)||
      !FindRmtmPostSuccessionChoice267V1(raw.source,frame.core.played_character_id,*q.request.instance_id))
    return reject(S::unavailable,"rmtm_post_succession_actual_epoch_or_first_option_refused");
  }else if((q.request.action!=A::ack_summary&&q.request.action!=A::ack_chaos)||
           !raw.source.ack_admissible||q.request.instance_id!=raw.source.fixed_instance_id)
   return reject(S::unavailable,"rmtm_event_actual_unique_instance_or_fixed_c_refused");for(const auto&old:state.claims)if(old.instance==*q.request.instance_id&&old.game==(raw.fullscreen_channel?raw.fullscreen.game:raw.material.manager_census.game)&&old.jomini==(raw.fullscreen_channel?raw.fullscreen.jomini:raw.material.manager_census.jomini)&&old.actor==frame.core.played_character_id)return reject(S::claim_consumed,"rmtm_event_same_actual_instance_claim_retained");if(state.claims.size()>=64||state.claim_sequence==(std::numeric_limits<std::uint64_t>::max)())return reject(S::claim_consumed,"rmtm_event_retained_capacity_exhausted");if(!Time(q))return reject(S::expired,"rmtm_event_original_preclaim_deadline_expired");
  const std::size_t fixed_target=q.request.action==A::ack_chaos?1:0;if(!post&&state.ack_spent[fixed_target])return reject(S::claim_consumed,"rmtm_fixed_event_ack_once_per_case");
  const auto claim=state.claim_sequence+1;state.claims.push_back({claim,std::string(q.request.id()),*q.request.instance_id,(raw.fullscreen_channel?raw.fullscreen.game:raw.material.manager_census.game),(raw.fullscreen_channel?raw.fullscreen.jomini:raw.material.manager_census.jomini),frame.core.played_character_id});state.claim_sequence=claim;lease.consumed=true;if(!post)state.ack_spent[fixed_target]=true;q.result.claim_sequence=claim;
  const auto call=CallRmtmEventRaw267V1(q.bindings,frame,q.request,q.monotonic_deadline_ms,raw);q.result.effect_attempted=call.entered;q.result.native_returned=call.native_returned;q.result.cleanup_known=call.cleanup_known;if(!call.cleanup_known||call.status==RmtmEventCallStatus267V1::indeterminate){state.unknown.store(true);return reject(S::indeterminate,"rmtm_event_native_completion_unknown_original_claim_retained");}if(call.status!=RmtmEventCallStatus267V1::returned)return reject(S::stale_source,"rmtm_event_pre_effect_refused_original_claim_retained");q.result.status=S::selection_dispatched;q.result.source=lease.raw.source;q.result.source_available=true;q.result.reason.clear();return true;
 }catch(...){if(q.session&&(q.observation_entered||q.result.effect_attempted))BlockRmtmEventUnknown267V1(*q.session);q.result.source.reset();q.result.source_available=false;q.result.status=q.observation_entered||q.result.effect_attempted?RmtmEventStatus267V1::indeterminate:RmtmEventStatus267V1::unavailable;q.result.cleanup_known=!(q.observation_entered||q.result.effect_attempted);q.result.reason="rmtm_event_owner_exception_original_claim_retained";}
#endif
 return true;
}
bool ExecuteRmtmEventOnOwner267V1(void*p,const ck3_11906::MainThreadExecutionStampV1&s)noexcept{if(!p)return false;auto&q=*static_cast<RmtmEventContext267V1*>(p);__try{return ExecuteRmtmEventInner267V1(q,s);}__except(EXCEPTION_EXECUTE_HANDLER){if(q.session)BlockRmtmEventUnknown267V1(*q.session);q.result.source.reset();q.result.source_available=false;q.result.status=RmtmEventStatus267V1::indeterminate;q.result.cleanup_known=false;return true;}}
}
