#include "xar_bridge/ck3_121003_rite_create26785313_owner_v1.hpp"
#include <algorithm>
#include <atomic>
#include <chrono>
#include <limits>
#include <mutex>
#include <windows.h>
namespace xar::ck3_121003::build26785313 {namespace {
std::uint64_t Wall()noexcept{const auto t=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();return t>0?static_cast<std::uint64_t>(t):0;}
[[maybe_unused]]bool Time(const RiteCreateContext267V1&q)noexcept{const auto t=Wall();return t&&t<q.request.deadline_unix_ms&&q.monotonic_deadline_ms&&GetTickCount64()<q.monotonic_deadline_ms;}
[[maybe_unused]]std::uint64_t OriginalMono(const RiteCreateContext267V1&q)noexcept{const auto t=Wall(),m=GetTickCount64();return t&&q.request.deadline_unix_ms>t?q.request.deadline_unix_ms-t>(std::numeric_limits<std::uint64_t>::max)()-m?(std::numeric_limits<std::uint64_t>::max)():m+q.request.deadline_unix_ms-t:0;}
[[maybe_unused]]bool SameCore(const ck3_1210::CoreSnapshotPrefix&a,const ck3_1210::CoreSnapshotPrefix&b)noexcept{return a.clock.date_raw==b.clock.date_raw&&a.clock.speed==b.clock.speed&&a.clock.paused==b.clock.paused&&a.local_player_id==b.local_player_id&&a.map_ready==b.map_ready&&a.has_played_character==b.has_played_character&&a.played_character_id==b.played_character_id&&a.played_character_alive==b.played_character_alive;}
[[maybe_unused]]bool SameFrame(const RiteCreateFrame267V1&a,const RiteCreateFrame267V1&b)noexcept{return a.facts_verified&&b.facts_verified&&SameCore(a.core,b.core)&&a.game==b.game&&a.jomini==b.jomini&&a.storage==b.storage&&a.actor==b.actor;}
[[maybe_unused]]bool Frame(RiteCreateContext267V1&q,const ck3_11906::MainThreadExecutionStampV1&s,RiteCreateFrame267V1&out){
 if(!Time(q)||!q.mailbox||q.mailbox->offline_fixture||!q.connection_generation||q.mailbox->permitted_executor_octovigintary!=&ExecuteRiteCreateOnOwner267V1){q.result.reason="rite_create_actual_owner_custody_unavailable";return false;}
 q.bindings=BindReadonlyImage(reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)),kExecutableSha256);std::string why;const bool good=ReadRiteCreateFrameOnOwner267V1(q.bindings,q.mailbox,q.ticket,s,&q,q.request,q.monotonic_deadline_ms,out,why);
 if(out.facts_verified){q.result.facts_available=true;q.result.facts=out.core;q.result.connection_generation=q.connection_generation;q.result.ticket_sequence=q.ticket.sequence;q.result.pump_epoch=s.pump_epoch;q.result.thread_id=s.thread_id;}
 if(!good){q.result.reason=why;return false;}if(!SameCore(out.core,q.request.expected)){q.result.status=RiteCreateStatus267V1::stale_source;q.result.reason="rite_create_actual_core_changed";return false;}return Time(q);
}
[[maybe_unused]]bool Capture(RiteCreateContext267V1&q,const ck3_11906::MainThreadExecutionStampV1&s,const std::optional<RiteCreateAssociation267V1>&association,RiteCreateFrame267V1&frame,RiteCreateRaw267V1&raw){
 if(!Frame(q,s,frame))return false;std::string why;const bool good=ReadRiteCreateRaw267V1(q.bindings,frame,q.request,association,q.monotonic_deadline_ms,raw,why);q.observation_entered=q.observation_entered||raw.entered;q.result.cleanup_known=q.result.cleanup_known&&raw.cleanup_known;
 if(!good||!raw.cleanup_known){q.result.reason=why.empty()?"rite_create_actual_complete_source_unavailable":why;return false;}
 if(!raw.pending&&raw.source.phase==RiteCreatePhase267V1::confirmation){GuiWindowV1 window;if(!ReadRiteCreateConfirmationWindowOnOwner267V1(q.bindings,q.mailbox,q.ticket,s,&q,q.request,q.monotonic_deadline_ms,window,why)||!BindRiteCreateConfirmationWindow267V1(q.bindings,window,raw,why)){q.result.reason=why.empty()?"rite_create_actual_named_modal_unavailable":why;return false;}}
 RiteCreateFrame267V1 after;if(!Frame(q,s,after)||!SameFrame(frame,after)){q.result.reason="rite_create_actual_world_changed_after_source";return false;}return Time(q);
}
}
struct RiteCreateSession267V1::State{
 struct Lease{RiteCreateFrame267V1 frame;RiteCreateRaw267V1 raw;RiteCreateRequest267V1 request;std::uint64_t sequence=0,connection=0,mono=0;bool consumed=false;};
 struct Pending{RiteCreateAssociation267V1 association;RiteCreateFrame267V1 frame;RiteCreateRequest267V1 request;std::uint64_t original_query=0,mono=0;};
 struct Claim{std::uint64_t sequence=0;std::string id;};
 std::atomic_bool unknown{false};std::mutex mutex;std::uint64_t generation=GetTickCount64()?GetTickCount64():1,query_sequence=0,claim_sequence=0;std::optional<Lease>latest;std::optional<Pending>pending;std::vector<Claim>claims;
};
RiteCreateSession267V1::RiteCreateSession267V1():state_(std::make_unique<State>()){}
RiteCreateSession267V1::~RiteCreateSession267V1()=default;
RiteCreateSession267V1&RetainedRiteCreateSession267V1(){static RiteCreateSession267V1 s;return s;}
void BlockRiteCreateUnknown267V1(RiteCreateSession267V1&s)noexcept{s.state_->unknown.store(true,std::memory_order_release);}
void ArmRiteCreateDeadline267V1(RiteCreateContext267V1&q)noexcept{q.monotonic_deadline_ms=0;const auto t=Wall(),m=GetTickCount64();if(t&&q.request.deadline_unix_ms>t)q.monotonic_deadline_ms=m+(std::min)(q.request.deadline_unix_ms-t,std::uint64_t{8000});}
bool ExecuteRiteCreateInner267V1(RiteCreateContext267V1&q,[[maybe_unused]]const ck3_11906::MainThreadExecutionStampV1&s)noexcept{
 q.result={};q.result.action=q.request.action;q.result.provider_generation=q.request.provider_generation;q.result.query_sequence=q.request.query_sequence;q.result.reason="rite_create_default_off";
#if defined(XAR_CK3_ENABLE_121003_26785313_RITE_CREATE_V1) && XAR_CK3_ENABLE_121003_26785313_RITE_CREATE_V1
 try{using A=RiteCreateAction267V1;using S=RiteCreateStatus267V1;const auto reject=[&](S status,const char*why){q.result.status=status;q.result.reason=why;q.result.source.reset();q.result.source_available=false;return true;};
  if(!q.session||!RiteCreateRequestShape267V1(q.request))return reject(S::unavailable,"rite_create_actual_request_or_session_unavailable");auto&state=*q.session->state_;std::scoped_lock lock(state.mutex);
  for(const auto&c:state.claims)if(c.id==q.request.id()){q.result.claim_sequence=c.sequence;return reject(S::claim_consumed,"rite_create_original_effect_id_retained_no_replay");}
  if(state.unknown.load(std::memory_order_acquire)){q.result.cleanup_known=false;return reject(S::indeterminate,"rite_create_prior_unknown_no_permission");}
  if(!Time(q))return reject(S::expired,"rite_create_original_deadline_expired");
  const auto failed=[&]{if(!q.result.cleanup_known){state.unknown.store(true);return reject(S::indeterminate,"rite_create_actual_observation_cleanup_unknown");}const auto why=q.result.reason.empty()?std::string("rite_create_actual_source_unavailable"):q.result.reason;return reject(Time(q)?S::unavailable:S::expired,why.c_str());};
  const auto mint=[&](const RiteCreateFrame267V1&f,const RiteCreateRaw267V1&r,std::uint64_t mono){if(state.query_sequence==(std::numeric_limits<std::uint64_t>::max)())return reject(S::unavailable,"rite_create_query_capacity_exhausted");state.latest=RiteCreateSession267V1::State::Lease{f,r,q.request,++state.query_sequence,q.connection_generation,mono,false};q.result.provider_generation=state.generation;q.result.query_sequence=state.query_sequence;q.result.source=r.source;q.result.source_available=true;q.result.status=S::available;q.result.reason.clear();return true;};
  if(q.request.action==A::query){if(state.pending)return reject(S::prerequisite_rejected,"rite_create_prior_create_awaits_original_confirmation");state.latest.reset();RiteCreateFrame267V1 frame;RiteCreateRaw267V1 raw;if(!Capture(q,s,std::nullopt,frame,raw))return failed();return mint(frame,raw,OriginalMono(q));}
  std::optional<RiteCreateAssociation267V1>association;
  if(q.request.action==A::query_confirmation){if(!state.pending)return reject(S::prerequisite_rejected,"rite_create_actual_original_create_unavailable");const auto&p=*state.pending;
   if(q.request.provider_generation!=state.generation||q.request.query_sequence!=p.original_query||q.connection_generation!=p.association.connection||q.request.deadline_unix_ms!=p.request.deadline_unix_ms||q.request.expected_source_rite_id!=p.request.expected_source_rite_id||!SameCore(q.request.expected,p.request.expected)||q.request.id()==p.request.id())return reject(S::stale_source,"rite_create_original_create_custody_mismatch");
   if(GetTickCount64()>=p.mono)return reject(S::expired,"rite_create_original_create_deadline_expired");q.monotonic_deadline_ms=(std::min)(q.monotonic_deadline_ms,p.mono);association=p.association;RiteCreateFrame267V1 frame;RiteCreateRaw267V1 raw;if(!Capture(q,s,association,frame,raw))return failed();if(!SameFrame(p.frame,frame))return reject(S::stale_source,"rite_create_original_world_changed_before_confirmation");if(raw.pending)return reject(S::confirmation_pending,"rite_create_original_creation_modal_not_yet_materialized");return mint(frame,raw,p.mono);
  }
  if(!state.latest)return reject(S::stale_source,"rite_create_actual_private_query_unavailable");auto&lease=*state.latest;
  if(q.request.provider_generation!=state.generation||q.request.query_sequence!=lease.sequence||q.connection_generation!=lease.connection||q.request.deadline_unix_ms!=lease.request.deadline_unix_ms||q.request.expected_source_rite_id!=lease.request.expected_source_rite_id||!SameCore(q.request.expected,lease.request.expected)||q.request.id()==lease.request.id())return reject(S::stale_source,"rite_create_original_private_source_mismatch");
  if(lease.consumed)return reject(S::claim_consumed,"rite_create_original_private_query_consumed");if(GetTickCount64()>=lease.mono)return reject(S::expired,"rite_create_original_query_deadline_expired");q.monotonic_deadline_ms=(std::min)(q.monotonic_deadline_ms,lease.mono);
  if(q.request.action==A::create){if(lease.raw.source.phase!=RiteCreatePhase267V1::draft||state.pending)return reject(S::prerequisite_rejected,"rite_create_original_draft_phase_required");}
  else{if(lease.raw.source.phase!=RiteCreatePhase267V1::confirmation||!state.pending||state.pending->association.connection!=q.connection_generation)return reject(S::prerequisite_rejected,"rite_create_original_confirmation_phase_required");association=state.pending->association;}
  RiteCreateFrame267V1 frame;RiteCreateRaw267V1 raw;if(!Capture(q,s,association,frame,raw))return failed();if(!SameFrame(lease.frame,frame)||raw.pending||raw!=lease.raw)return reject(S::stale_source,"rite_create_actual_complete_source_changed");
  if(q.request.action==A::create?(!raw.source.draft||!raw.source.draft->create_admissible):(!raw.source.confirmation||!raw.source.confirmation->accept_admissible))return reject(S::prerequisite_rejected,"rite_create_actual_native_predicate_or_button_refused");
  if(state.claims.size()>=64||state.claim_sequence==(std::numeric_limits<std::uint64_t>::max)())return reject(S::claim_consumed,"rite_create_retained_once_capacity_exhausted");if(!Time(q))return reject(S::expired,"rite_create_original_preclaim_deadline_expired");
  std::optional<RiteCreateSession267V1::State::Pending>prepared;if(q.request.action==A::create)prepared=RiteCreateSession267V1::State::Pending{{raw.controller,raw.context,raw.root,q.request.expected_source_rite_id,q.request.expected.played_character_id,q.connection_generation,q.request.deadline_unix_ms},frame,q.request,lease.sequence,lease.mono};
  if(prepared){prepared->association.selected_draft_header=raw.selected_draft_header;prepared->association.selected_draft_rows=raw.selected_draft_rows;}
  const auto claim=state.claim_sequence+1;state.claims.push_back({claim,std::string(q.request.id())});state.claim_sequence=claim;lease.consumed=true;q.result.claim_sequence=claim;
  const auto call=CallRiteCreateRaw267V1(q.bindings,frame,q.request,association,q.monotonic_deadline_ms,raw);q.result.effect_attempted=call.entered;q.result.native_returned=call.status==RiteCreateCallStatus267V1::returned;q.result.cleanup_known=call.cleanup_known;
  if(!call.cleanup_known||call.status==RiteCreateCallStatus267V1::indeterminate){state.unknown.store(true);return reject(S::indeterminate,"rite_create_native_completion_unknown_original_claim_retained");}
  if(call.status!=RiteCreateCallStatus267V1::returned)return reject(S::stale_source,"rite_create_pre_effect_refused_original_claim_retained");
  if(q.request.action==A::create){state.pending=std::move(prepared);q.result.status=S::create_dispatched;}else{state.pending.reset();q.result.status=S::confirmation_dispatched;}
  q.result.source=lease.raw.source;q.result.source_available=true;q.result.reason.clear();return true;
 }catch(...){if(q.session&&(q.observation_entered||q.result.effect_attempted))BlockRiteCreateUnknown267V1(*q.session);q.result.source.reset();q.result.source_available=false;q.result.status=q.observation_entered||q.result.effect_attempted?RiteCreateStatus267V1::indeterminate:RiteCreateStatus267V1::unavailable;q.result.cleanup_known=!(q.observation_entered||q.result.effect_attempted);q.result.reason="rite_create_owner_exception_original_claim_retained";}
#endif
 return true;
}
bool ExecuteRiteCreateOnOwner267V1(void*p,const ck3_11906::MainThreadExecutionStampV1&s)noexcept{if(!p)return false;auto&q=*static_cast<RiteCreateContext267V1*>(p);__try{return ExecuteRiteCreateInner267V1(q,s);}__except(EXCEPTION_EXECUTE_HANDLER){if(q.session)BlockRiteCreateUnknown267V1(*q.session);q.result.source.reset();q.result.source_available=false;q.result.status=RiteCreateStatus267V1::indeterminate;q.result.cleanup_known=false;return true;}}
}
