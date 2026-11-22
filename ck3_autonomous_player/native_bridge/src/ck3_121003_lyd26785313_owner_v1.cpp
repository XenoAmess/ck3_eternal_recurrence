#include "xar_bridge/ck3_121003_lyd26785313_owner_v1.hpp"
#include <algorithm>
#include <atomic>
#include <chrono>
#include <limits>
#include <mutex>
#include <windows.h>
namespace xar::ck3_121003::build26785313 {namespace {
std::uint64_t Wall()noexcept{const auto t=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();return t>0?static_cast<std::uint64_t>(t):0;}
[[maybe_unused]]bool Time(const LydContext267V1&q)noexcept{const auto t=Wall();return t&&t<q.request.deadline_unix_ms&&q.monotonic_deadline_ms&&GetTickCount64()<q.monotonic_deadline_ms;}
[[maybe_unused]]bool SameCore(const ck3_1210::CoreSnapshotPrefix&a,const ck3_1210::CoreSnapshotPrefix&b)noexcept{return a.clock.date_raw==b.clock.date_raw&&a.clock.speed==b.clock.speed&&a.clock.paused==b.clock.paused&&a.local_player_id==b.local_player_id&&a.map_ready==b.map_ready&&a.has_played_character==b.has_played_character&&a.played_character_id==b.played_character_id&&a.played_character_alive==b.played_character_alive;}
[[maybe_unused]]bool SameFrame(const LydFrame267V1&a,const LydFrame267V1&b)noexcept{return a.facts_verified&&b.facts_verified&&SameCore(a.core,b.core)&&a.scene==b.scene&&a.witness==b.witness&&a.name_witness==b.name_witness;}
[[maybe_unused]]bool Frame(LydContext267V1&q,const ck3_11906::MainThreadExecutionStampV1&s,LydFrame267V1&out){
 if(!Time(q)||!q.mailbox||q.mailbox->offline_fixture||!q.connection_generation||q.mailbox->permitted_executor_quinquevigintary!=&ExecuteLydOnOwner267V1)return false;
 q.bindings=BindReadonlyImage(reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)),kExecutableSha256);std::string reason;
 const bool good=ReadLydFrameOnOwner267V1(q.bindings,q.mailbox,q.ticket,s,&q,LydKindForAction267V1(q.request.action),q.request.deadline_unix_ms,q.monotonic_deadline_ms,out,reason);
 if(out.facts_verified){q.result.facts_available=true;q.result.facts=out.core;q.result.connection_generation=q.connection_generation;q.result.ticket_sequence=q.ticket.sequence;q.result.pump_epoch=s.pump_epoch;q.result.thread_id=s.thread_id;}
 if(!good){q.result.reason=reason;return false;}if(!SameCore(out.core,q.request.expected)){q.result.reason="lyd_actual_core_changed";return false;}return Time(q);
}
[[maybe_unused]]bool Observe(LydContext267V1&q,const LydFrame267V1&frame,const std::optional<LydSelectionAssociation267V1>&pending,LydRaw267V1&raw){std::string reason;
 const bool good=ReadLydRaw267V1(q.bindings,q.request.expected,frame.scene,q.monotonic_deadline_ms,q.request,pending,raw,reason);
 q.native_observation_entered=q.native_observation_entered||raw.native_read_entered;q.result.cleanup_known=raw.cleanup_known;
 if(!good){q.result.reason=reason;return false;}q.result.source_available=true;q.result.source=raw.source;return Time(q);
}
[[maybe_unused]]bool SameSubject(const LydRequest267V1&a,const LydRequest267V1&b)noexcept{
 if(LydKindForAction267V1(a.action)!=LydKindForAction267V1(b.action)||a.personal!=b.personal)return false;
 if(a.action==LydAction267V1::confirm_personal_add)return b.action==LydAction267V1::query_add_confirmation;
 if(a.action==LydAction267V1::open_personal||a.action==LydAction267V1::start_add_personal||a.action==LydAction267V1::select_personal_candidate)return b.action==LydAction267V1::query_personal;
 if(a.action==LydAction267V1::choose_known_event_option)return b.action==LydAction267V1::query_events;
 // A complete decision census permits only an actual fixed row from that private source.
 return b.action==LydAction267V1::query_decisions;
}
}
struct LydSession267V1::State{
 struct Lease{LydFrame267V1 frame;LydRaw267V1 raw;LydRequest267V1 request;std::uint64_t query=0,connection=0,mono=0;bool consumed=false;};
 struct Claim{std::uint64_t sequence=0;std::string id;std::uintptr_t global=0,jomini=0;std::int32_t actor=-1;};
 std::atomic_bool unknown{false};std::mutex mutex;std::uint64_t generation=GetTickCount64()?GetTickCount64():1,query_sequence=0,claim_sequence=0;
 std::optional<Lease>latest;std::optional<LydSelectionAssociation267V1>pending;std::uint64_t pending_connection=0;std::vector<Claim>claims;
};
LydSession267V1::LydSession267V1():state_(std::make_unique<State>()){}
LydSession267V1::~LydSession267V1()=default;
void BlockLydUnknown267V1(LydSession267V1&s)noexcept{s.state_->unknown.store(true,std::memory_order_release);}
LydSession267V1&RetainedLydSession267V1(){static LydSession267V1 s;return s;}
void ArmLydDeadline267V1(LydContext267V1&q)noexcept{q.monotonic_deadline_ms=0;const auto t=Wall();if(t&&q.request.deadline_unix_ms>t)q.monotonic_deadline_ms=GetTickCount64()+(std::min)(q.request.deadline_unix_ms-t,std::uint64_t{8000});}
bool ExecuteLydInner267V1(LydContext267V1&q,[[maybe_unused]]const ck3_11906::MainThreadExecutionStampV1&s)noexcept{
 q.result={};q.result.action=q.request.action;q.result.provider_generation=q.request.provider_generation;q.result.query_sequence=q.request.query_sequence;
 q.result.decision=q.request.decision;q.result.personal=q.request.personal;q.result.event_role=q.request.event_role;q.result.instance_id=q.request.instance_id;q.result.reason="current_lyd_default_off";
#if defined(XAR_CK3_ENABLE_121003_26785313_LYD_V1) && XAR_CK3_ENABLE_121003_26785313_LYD_V1
 try{using S=LydStatus267V1;const auto reject=[&](S status,const char*why){q.result.status=status;q.result.reason=why;return true;};
  if(!q.session||!LydRequestShape267V1(q.request))return reject(S::unavailable,"lyd_actual_request_or_retained_session_unavailable");auto&state=*q.session->state_;std::scoped_lock lock(state.mutex);
  for(const auto&claim:state.claims)if(claim.id==q.request.id()){q.result.claim_sequence=claim.sequence;return reject(S::claim_consumed,"lyd_original_effect_id_retained_no_replay");}
  if(state.unknown.load(std::memory_order_acquire)){q.result.cleanup_known=false;return reject(S::indeterminate,"lyd_prior_native_completion_unknown_no_retry");}
  if(!Time(q))return reject(S::expired,"lyd_original_deadline_expired");
  if(q.request.action==LydAction267V1::query_add_confirmation&&state.pending&&state.pending_connection!=q.connection_generation)return reject(S::stale_source,"lyd_original_pending_selection_connection_mismatch");
  LydFrame267V1 frame;if(!Frame(q,s,frame))return true;
  if(state.claims.size()>=128||state.query_sequence==(std::numeric_limits<std::uint64_t>::max)()||state.claim_sequence==(std::numeric_limits<std::uint64_t>::max)())return reject(S::claim_consumed,"lyd_retained_capacity_exhausted_no_reset");
  const auto failed=[&]{if(!q.result.cleanup_known){state.unknown.store(true);q.result.status=S::indeterminate;q.result.source_available=false;q.result.source.reset();}else q.result.status=Time(q)?S::unavailable:S::expired;return true;};
  if(LydQueryAction267V1(q.request.action)){
   if(q.request.action==LydAction267V1::query_add_confirmation&&state.pending){
    if(q.request.personal!=state.pending->personal||q.request.deadline_unix_ms!=state.pending->wall_deadline)return reject(S::stale_source,"lyd_original_pending_selection_deadline_or_target_mismatch");
    q.monotonic_deadline_ms=(std::min)(q.monotonic_deadline_ms,state.pending->monotonic_deadline);
    if(!Time(q))return reject(S::expired,"lyd_original_pending_selection_deadline_expired");
   }
   state.latest.reset();const auto before=frame;LydRaw267V1 raw;if(!Observe(q,frame,state.pending,raw))return failed();
   if(!Frame(q,s,frame)||!SameFrame(before,frame))return reject(S::stale_source,"lyd_actual_core_or_gui_changed_after_read");
   const auto sequence=++state.query_sequence;TokenizeLydRaw267V1(raw,state.generation,sequence);q.result.source=raw.source;
   LydSession267V1::State::Lease lease{frame,raw,q.request,sequence,q.connection_generation,q.monotonic_deadline_ms,false};state.latest=std::move(lease);
   q.result.provider_generation=state.generation;q.result.query_sequence=sequence;q.result.status=S::available;q.result.reason.clear();return true;
  }
  if(!state.latest)return reject(S::stale_source,"lyd_original_private_query_unavailable");auto&lease=*state.latest;
  if(q.request.provider_generation!=state.generation||q.request.query_sequence!=lease.query||q.connection_generation!=lease.connection||q.request.deadline_unix_ms!=lease.request.deadline_unix_ms||!SameSubject(q.request,lease.request)||!SameCore(q.request.expected,lease.request.expected)||q.request.id()==lease.request.id())return reject(S::stale_source,"lyd_original_private_query_source_mismatch");
  if(lease.consumed)return reject(S::claim_consumed,"lyd_original_private_query_consumed");if(GetTickCount64()>=lease.mono)return reject(S::expired,"lyd_original_query_deadline_expired");q.monotonic_deadline_ms=(std::min)(q.monotonic_deadline_ms,lease.mono);
  LydRaw267V1 raw;if(!Observe(q,frame,state.pending,raw))return failed();TokenizeLydRaw267V1(raw,state.generation,lease.query);q.result.source=raw.source;const auto before=frame;
  if(!Frame(q,s,frame)||!SameFrame(before,frame)||!SameFrame(lease.frame,frame)||!SameLydRawForLease267V1(raw,lease.raw))return reject(S::stale_source,"lyd_actual_complete_source_changed");
  if(!LydRawAdmissible267V1(raw,q.request))return reject(S::unavailable,"lyd_actual_typed_source_or_native_can_refused");
  if(!Time(q))return reject(S::expired,"lyd_original_preclaim_deadline_expired");const auto sequence=state.claim_sequence+1;
  state.claims.push_back({sequence,std::string(q.request.id()),frame.scene.global,frame.scene.jomini,q.request.expected.played_character_id});state.claim_sequence=sequence;lease.consumed=true;q.result.claim_sequence=sequence;
  const auto call=CallLydRaw267V1(q.bindings,q.request.expected,frame.scene,q.monotonic_deadline_ms,q.request,state.pending,raw);
  q.result.effect_attempted=call.effect_entered;q.result.native_returned=call.status==LydRawCallStatus267V1::returned;q.result.native_handled=call.native_handled;q.result.cleanup_known=call.cleanup_known;
  if(!call.cleanup_known||call.status==LydRawCallStatus267V1::indeterminate){state.unknown.store(true);q.result.source_available=false;q.result.source.reset();return reject(S::indeterminate,"lyd_native_completion_unknown_no_replay");}
  if(call.status!=LydRawCallStatus267V1::returned)return reject(S::stale_source,"lyd_pre_effect_refused_original_claim_retained");
  if(q.request.action==LydAction267V1::select_personal_candidate){
   const auto chosen=std::find_if(raw.choices.begin(),raw.choices.end(),[&](const auto&v){return v.token==q.request.choice_token&&v.admissible;});
   if(!q.request.personal||chosen==raw.choices.end()){state.unknown.store(true);q.result.cleanup_known=false;return reject(S::indeterminate,"lyd_selected_association_not_retained");}
   state.pending=LydSelectionAssociation267V1{*q.request.personal,raw.resident,raw.root,frame.scene.context,chosen->definition,raw.actor,q.request.deadline_unix_ms,q.monotonic_deadline_ms};state.pending_connection=q.connection_generation;
  }
  if(q.request.action==LydAction267V1::confirm_personal_add){state.pending.reset();state.pending_connection=0;}
  q.result.status=q.request.action==LydAction267V1::confirm_decision||q.request.action==LydAction267V1::choose_known_event_option||q.request.action==LydAction267V1::confirm_personal_add?S::confirmation_dispatched:q.request.action==LydAction267V1::open_detail||q.request.action==LydAction267V1::select_personal_candidate?S::selection_dispatched:S::navigation_dispatched;q.result.reason.clear();return true;
 }catch(...){if(q.session&&(q.native_observation_entered||q.result.effect_attempted))BlockLydUnknown267V1(*q.session);q.result.status=q.native_observation_entered||q.result.effect_attempted?LydStatus267V1::indeterminate:LydStatus267V1::unavailable;q.result.source_available=false;q.result.source.reset();q.result.reason="lyd_exception_original_claim_retained";}
#endif
 return true;
}
bool ExecuteLydOnOwner267V1(void*p,const ck3_11906::MainThreadExecutionStampV1&s)noexcept{if(!p)return false;auto&q=*static_cast<LydContext267V1*>(p);__try{return ExecuteLydInner267V1(q,s);}__except(EXCEPTION_EXECUTE_HANDLER){if(q.session)BlockLydUnknown267V1(*q.session);q.result.status=LydStatus267V1::indeterminate;q.result.cleanup_known=false;q.result.source_available=false;q.result.source.reset();return true;}}
}
