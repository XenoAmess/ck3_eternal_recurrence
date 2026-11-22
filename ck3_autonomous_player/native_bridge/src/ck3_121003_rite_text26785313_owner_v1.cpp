#include "xar_bridge/ck3_121003_rite_text26785313_owner_v1.hpp"
#include <algorithm>
#include <atomic>
#include <chrono>
#include <limits>
#include <mutex>
#include <windows.h>
namespace xar::ck3_121003::build26785313 {namespace {
std::uint64_t Wall()noexcept{const auto t=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();return t>0?static_cast<std::uint64_t>(t):0;}
[[maybe_unused]]bool Time(const RiteTextContext267V1&q)noexcept{const auto t=Wall();return t&&t<q.request.deadline_unix_ms&&q.monotonic_deadline_ms&&GetTickCount64()<q.monotonic_deadline_ms;}
[[maybe_unused]]std::uint64_t OriginalMono(const RiteTextContext267V1&q)noexcept{const auto t=Wall(),m=GetTickCount64();return t&&q.request.deadline_unix_ms>t?q.request.deadline_unix_ms-t>(std::numeric_limits<std::uint64_t>::max)()-m?(std::numeric_limits<std::uint64_t>::max)():m+q.request.deadline_unix_ms-t:0;}
[[maybe_unused]]bool SameCore(const ck3_1210::CoreSnapshotPrefix&a,const ck3_1210::CoreSnapshotPrefix&b)noexcept{return a.clock.date_raw==b.clock.date_raw&&a.clock.speed==b.clock.speed&&a.clock.paused==b.clock.paused&&a.local_player_id==b.local_player_id&&a.map_ready==b.map_ready&&a.has_played_character==b.has_played_character&&a.played_character_id==b.played_character_id&&a.played_character_alive==b.played_character_alive;}
[[maybe_unused]]bool SameFrame(const RiteTextFrame267V1&a,const RiteTextFrame267V1&b)noexcept{return a.facts_verified&&b.facts_verified&&SameCore(a.core,b.core)&&a.game==b.game&&a.jomini==b.jomini&&a.storage==b.storage&&a.actor==b.actor;}
[[maybe_unused]]bool Frame(RiteTextContext267V1&q,const ck3_11906::MainThreadExecutionStampV1&s,RiteTextFrame267V1&out){
 if(!Time(q)||!q.mailbox||q.mailbox->offline_fixture||!q.connection_generation||q.mailbox->permitted_executor_novemvigintary!=&ExecuteRiteTextOnOwner267V1){q.result.reason="rite_text_actual_owner_custody_unavailable";return false;}
 q.bindings=BindReadonlyImage(reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)),kExecutableSha256);std::string why;const bool good=ReadRiteTextFrameOnOwner267V1(q.bindings,q.mailbox,q.ticket,s,&q,q.request,q.monotonic_deadline_ms,out,why);
 if(out.facts_verified){q.result.facts_available=true;q.result.facts=out.core;q.result.connection_generation=q.connection_generation;q.result.ticket_sequence=q.ticket.sequence;q.result.pump_epoch=s.pump_epoch;q.result.thread_id=s.thread_id;}
 if(!good){q.result.reason=why;return false;}if(!SameCore(out.core,q.request.expected)){q.result.status=RiteTextStatus267V1::stale_source;q.result.reason="rite_text_actual_core_changed";return false;}return Time(q);
}
[[maybe_unused]]bool Capture(RiteTextContext267V1&q,const ck3_11906::MainThreadExecutionStampV1&s,RiteTextFrame267V1&frame,RiteTextRaw267V1&raw){
 if(!Frame(q,s,frame))return false;std::string why;const bool good=ReadRiteTextRaw267V1(q.bindings,frame,q.request,q.monotonic_deadline_ms,raw,why);q.observation_entered=q.observation_entered||raw.entered;q.result.cleanup_known=q.result.cleanup_known&&raw.cleanup_known;
 if(!good||!raw.cleanup_known){q.result.reason=why.empty()?"rite_text_actual_complete_source_unavailable":why;return false;}RiteTextFrame267V1 after;if(!Frame(q,s,after)||!SameFrame(frame,after)){q.result.reason="rite_text_actual_world_changed_after_read";return false;}return Time(q);
}
}
struct RiteTextSession267V1::State{
 struct Lease{RiteTextFrame267V1 frame;RiteTextRaw267V1 raw;RiteTextRequest267V1 request;std::uint64_t sequence=0,connection=0,mono=0;bool consumed=false;};
 struct Claim{std::uint64_t sequence=0;std::string id;};std::atomic_bool unknown{false};std::mutex mutex;std::uint64_t generation=GetTickCount64()?GetTickCount64():1,query_sequence=0,claim_sequence=0;std::optional<Lease>latest;std::vector<Claim>claims;
};
RiteTextSession267V1::RiteTextSession267V1():state_(std::make_unique<State>()){}
RiteTextSession267V1::~RiteTextSession267V1()=default;
RiteTextSession267V1&RetainedRiteTextSession267V1(){static RiteTextSession267V1 s;return s;}
void BlockRiteTextUnknown267V1(RiteTextSession267V1&s)noexcept{s.state_->unknown.store(true,std::memory_order_release);}
void ArmRiteTextDeadline267V1(RiteTextContext267V1&q)noexcept{q.monotonic_deadline_ms=0;const auto t=Wall(),m=GetTickCount64();if(t&&q.request.deadline_unix_ms>t)q.monotonic_deadline_ms=m+(std::min)(q.request.deadline_unix_ms-t,std::uint64_t{8000});}
bool ExecuteRiteTextInner267V1(RiteTextContext267V1&q,[[maybe_unused]]const ck3_11906::MainThreadExecutionStampV1&s)noexcept{
 q.result={};q.result.action=q.request.action;q.result.provider_generation=q.request.provider_generation;q.result.query_sequence=q.request.query_sequence;q.result.reason="rite_text_default_off";
#if defined(XAR_CK3_ENABLE_121003_26785313_RITE_TEXT_V1) && XAR_CK3_ENABLE_121003_26785313_RITE_TEXT_V1
 try{using A=RiteTextAction267V1;using S=RiteTextStatus267V1;const auto reject=[&](S status,const char*why){q.result.status=status;q.result.reason=why;q.result.source.reset();q.result.source_available=false;return true;};if(!q.session||!RiteTextRequestShape267V1(q.request))return reject(S::unavailable,"rite_text_actual_request_or_session_unavailable");auto&state=*q.session->state_;std::scoped_lock lock(state.mutex);
  for(const auto&c:state.claims)if(c.id==q.request.id()){q.result.claim_sequence=c.sequence;return reject(S::claim_consumed,"rite_text_original_effect_id_retained_no_replay");}if(state.unknown.load(std::memory_order_acquire)){q.result.cleanup_known=false;return reject(S::indeterminate,"rite_text_prior_unknown_no_permission");}if(!Time(q))return reject(S::expired,"rite_text_original_deadline_expired");
  const auto failed=[&]{if(!q.result.cleanup_known){state.unknown.store(true);return reject(S::indeterminate,"rite_text_actual_observation_cleanup_unknown");}const auto why=q.result.reason.empty()?std::string("rite_text_actual_source_unavailable"):q.result.reason;return reject(Time(q)?S::unavailable:S::expired,why.c_str());};
  if(q.request.action==A::query){state.latest.reset();RiteTextFrame267V1 frame;RiteTextRaw267V1 raw;if(!Capture(q,s,frame,raw))return failed();if(state.query_sequence==(std::numeric_limits<std::uint64_t>::max)())return reject(S::unavailable,"rite_text_query_capacity_exhausted");state.latest=RiteTextSession267V1::State::Lease{frame,raw,q.request,++state.query_sequence,q.connection_generation,OriginalMono(q),false};q.result.provider_generation=state.generation;q.result.query_sequence=state.query_sequence;q.result.source=raw.source;q.result.source_available=true;q.result.status=S::available;q.result.reason.clear();return true;}
  if(!state.latest)return reject(S::stale_source,"rite_text_actual_original_query_missing");auto&lease=*state.latest;
  if(q.request.provider_generation!=state.generation||q.request.query_sequence!=lease.sequence||q.connection_generation!=lease.connection||q.request.deadline_unix_ms!=lease.request.deadline_unix_ms||q.request.expected_source_rite_id!=lease.request.expected_source_rite_id||!SameCore(q.request.expected,lease.request.expected)||q.request.id()==lease.request.id())return reject(S::stale_source,"rite_text_original_private_query_custody_mismatch");if(lease.consumed)return reject(S::claim_consumed,"rite_text_original_private_query_consumed");if(GetTickCount64()>=lease.mono)return reject(S::expired,"rite_text_original_query_deadline_expired");q.monotonic_deadline_ms=(std::min)(q.monotonic_deadline_ms,lease.mono);
  RiteTextFrame267V1 frame;RiteTextRaw267V1 raw;if(!Capture(q,s,frame,raw))return failed();if(!SameFrame(lease.frame,frame)||raw!=lease.raw)return reject(S::stale_source,"rite_text_actual_complete_draft_changed");if(!raw.source.write_admissible)return reject(S::prerequisite_rejected,"rite_text_actual_creating_window_or_modal_refused");if(state.claims.size()>=64||state.claim_sequence==(std::numeric_limits<std::uint64_t>::max)())return reject(S::claim_consumed,"rite_text_retained_capacity_exhausted");if(!Time(q))return reject(S::expired,"rite_text_original_preclaim_deadline_expired");
  const auto claim=state.claim_sequence+1;state.claims.push_back({claim,std::string(q.request.id())});state.claim_sequence=claim;lease.consumed=true;q.result.claim_sequence=claim;
  const auto call=CallRiteTextRaw267V1(q.bindings,frame,q.request,q.monotonic_deadline_ms,raw);q.result.effect_attempted=call.entered;q.result.native_returned=call.status==RiteTextCallStatus267V1::returned;q.result.cleanup_known=call.cleanup_known;if(!call.cleanup_known||call.status==RiteTextCallStatus267V1::indeterminate){state.unknown.store(true);return reject(S::indeterminate,"rite_text_native_completion_unknown_original_claim_retained");}if(call.status!=RiteTextCallStatus267V1::returned)return reject(S::stale_source,"rite_text_pre_effect_refused_original_claim_retained");q.result.status=S::text_dispatched;q.result.source=lease.raw.source;q.result.source_available=true;q.result.reason.clear();return true;
 }catch(...){if(q.session&&(q.observation_entered||q.result.effect_attempted))BlockRiteTextUnknown267V1(*q.session);q.result.source.reset();q.result.source_available=false;q.result.status=q.observation_entered||q.result.effect_attempted?RiteTextStatus267V1::indeterminate:RiteTextStatus267V1::unavailable;q.result.cleanup_known=!(q.observation_entered||q.result.effect_attempted);q.result.reason="rite_text_owner_exception_original_claim_retained";}
#endif
 return true;
}
bool ExecuteRiteTextOnOwner267V1(void*p,const ck3_11906::MainThreadExecutionStampV1&s)noexcept{if(!p)return false;auto&q=*static_cast<RiteTextContext267V1*>(p);__try{return ExecuteRiteTextInner267V1(q,s);}__except(EXCEPTION_EXECUTE_HANDLER){if(q.session)BlockRiteTextUnknown267V1(*q.session);q.result.source.reset();q.result.source_available=false;q.result.status=RiteTextStatus267V1::indeterminate;q.result.cleanup_known=false;return true;}}
}
