#include "xar_bridge/ck3_121003_rmtm_observation26785313_owner_v1.hpp"
#include <algorithm>
#include <atomic>
#include <chrono>
#include <limits>
#include <mutex>
#include <windows.h>
namespace xar::ck3_121003::build26785313 {namespace {
[[maybe_unused]]std::uint64_t Wall()noexcept{const auto n=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();return n>0?static_cast<std::uint64_t>(n):0;}
[[maybe_unused]]bool Time(const RmtmObservationContext267V1&q){const auto w=Wall();return w&&w<q.request.deadline_unix_ms&&q.monotonic_deadline_ms&&GetTickCount64()<q.monotonic_deadline_ms;}
[[maybe_unused]]bool Core(const ck3_1210::CoreSnapshotPrefix&a,const ck3_1210::CoreSnapshotPrefix&b){return a.clock.date_raw==b.clock.date_raw&&a.clock.speed==b.clock.speed&&a.clock.paused==b.clock.paused&&a.local_player_id==b.local_player_id&&a.map_ready==b.map_ready&&a.has_played_character==b.has_played_character&&a.played_character_id==b.played_character_id&&a.played_character_alive==b.played_character_alive;}
[[maybe_unused]]bool Same(const RmtmObservationFrame267V1&a,const RmtmObservationFrame267V1&b){const auto&x=a.role.world;const auto&y=b.role.world;return a.facts_verified&&b.facts_verified&&Core(a.core,b.core)&&a.scene==b.scene&&a.witness==b.witness&&a.connection_generation==b.connection_generation&&x.game==y.game&&x.jomini==y.jomini&&x.storage==y.storage&&x.data==y.data&&x.players==y.players&&x.player==y.player&&x.actor==y.actor;}
[[maybe_unused]]bool Frame(RmtmObservationContext267V1&q,const ck3_11906::MainThreadExecutionStampV1&s,RmtmObservationFrame267V1&f){
 if(!Time(q)||!q.mailbox||q.mailbox->offline_fixture||!q.connection_generation||q.mailbox->permitted_executor_quattuortrigintary!=&ExecuteRmtmOnOwner267V1){q.result.reason="rmtm_observation_actual_owner_unavailable";return false;}
 q.bindings=BindReadonlyImage(reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)),kExecutableSha256);std::string why;const bool good=ReadRmtmObservationFrameOnOwner267V1(q.bindings,q.mailbox,q.ticket,s,&q.invocation,q.request.deadline_unix_ms,q.monotonic_deadline_ms,f,why);
 f.connection_generation=q.connection_generation;f.scene.connection_generation=q.connection_generation;f.scene.wall_deadline=q.request.deadline_unix_ms;
 if(f.facts_verified){q.result.facts_available=true;q.result.facts=f.core;q.result.connection_generation=q.connection_generation;q.result.ticket_sequence=q.ticket.sequence;q.result.pump_epoch=s.pump_epoch;q.result.thread_id=s.thread_id;}
 if(!good){q.result.reason=why;return false;}if(!Core(f.core,q.request.expected)){q.result.reason="rmtm_observation_actual_Core_changed";return false;}return Time(q);
}
[[maybe_unused]]bool Capture(RmtmObservationContext267V1&q,const ck3_11906::MainThreadExecutionStampV1&s,RmtmObservationFrame267V1&f,RmtmObservationRaw267V1&r){
 if(!Frame(q,s,f))return false;std::string why;const bool good=ReadRmtmObservationRaw267V1(q.bindings,f,q.request,q.monotonic_deadline_ms,r,why);q.observation_entered|=r.entered;q.result.cleanup_known&=r.cleanup_known;
 if(!good||!r.cleanup_known){q.result.reason=why;return false;}RmtmObservationFrame267V1 z;if(!Frame(q,s,z)||!Same(f,z)){q.result.reason="rmtm_observation_actual_world_or_GUI_changed_after_read";return false;}return Time(q);
}
[[maybe_unused]]bool ActionAllowed(const RmtmObservationSource267V1&r,RmtmObservationAction267V1 a){using A=RmtmObservationAction267V1;switch(a){case A::open_budget:return r.budget&&r.budget->open_admissible;case A::cancel_budget:return r.budget&&r.budget->cancel_admissible;case A::open_offer:return r.offer&&r.offer->open_admissible;case A::cancel_offer:return r.offer&&r.offer->cancel_admissible;default:return false;}}
[[maybe_unused]]std::size_t Purpose(const RmtmObservationRequest267V1&q){using A=RmtmObservationAction267V1;if(q.action==A::open_budget)return 0;if(q.action==A::cancel_budget)return 1;return 2+2*static_cast<std::size_t>(*q.offer_target)+(q.action==A::cancel_offer?1:0);}
}
struct RmtmObservationSession267V1::State {
 struct Lease{RmtmObservationRequest267V1 request;RmtmObservationFrame267V1 frame;RmtmObservationRaw267V1 raw;std::uint64_t query=0,connection=0,mono=0;bool consumed=false;};
 struct Claim{std::uint64_t sequence=0;std::string id;};std::atomic_bool unknown{false};std::mutex mutex;
 std::uint64_t generation=GetTickCount64()?GetTickCount64():1,query=0,claim=0;std::optional<Lease>latest;std::vector<Claim>claims;std::array<bool,6>spent{};
};
RmtmObservationSession267V1::RmtmObservationSession267V1():state_(std::make_unique<State>()){}
RmtmObservationSession267V1::~RmtmObservationSession267V1()=default;
RmtmObservationSession267V1&RetainedRmtmObservationSession267V1(){static RmtmObservationSession267V1 s;return s;}
void BlockRmtmObservationUnknown267V1(RmtmObservationSession267V1&s)noexcept{s.state_->unknown.store(true);}
void ArmRmtmObservationDeadline267V1(RmtmObservationContext267V1&q)noexcept{q.monotonic_deadline_ms=0;const auto w=Wall(),m=GetTickCount64();if(w&&q.request.deadline_unix_ms>w)q.monotonic_deadline_ms=m+(std::min)(q.request.deadline_unix_ms-w,std::uint64_t{8000});}
bool ExecuteRmtmObservationInner267V1(RmtmObservationContext267V1&q,[[maybe_unused]]const ck3_11906::MainThreadExecutionStampV1&s)noexcept{
 q.result={};q.result.action=q.request.action;q.result.provider_generation=q.request.provider_generation;q.result.query_sequence=q.request.query_sequence;q.result.reason="rmtm_observation_default_off";
#if defined(XAR_CK3_ENABLE_121003_26785313_RMTM_OBSERVATION_V1) && XAR_CK3_ENABLE_121003_26785313_RMTM_OBSERVATION_V1
 try{using S=RmtmObservationStatus267V1;const auto reject=[&](S status,const char*why){q.result.status=status;q.result.reason=why;q.result.source.reset();q.result.source_available=false;return true;};
 if(!q.session||!RmtmObservationRequestShape267V1(q.request))return reject(S::unavailable,"rmtm_observation_actual_request_or_session_unavailable");auto&st=*q.session->state_;std::scoped_lock lock(st.mutex);
 for(const auto&c:st.claims)if(c.id==q.request.id()){q.result.claim_sequence=c.sequence;return reject(S::claim_consumed,"rmtm_observation_original_effect_ID_retained");}
 if(st.unknown.load()){q.result.cleanup_known=false;return reject(S::indeterminate,"rmtm_observation_prior_UNKNOWN_retained");}if(!Time(q))return reject(S::expired,"rmtm_observation_original_deadline_expired");
 const auto failed=[&]{if(!q.result.cleanup_known){st.unknown.store(true);return reject(S::indeterminate,"rmtm_observation_actual_cleanup_UNKNOWN");}const auto why=q.result.reason;return reject(Time(q)?S::unavailable:S::expired,why.c_str());};
 RmtmObservationFrame267V1 f;RmtmObservationRaw267V1 raw;
 if(RmtmObservationQuery267V1(q.request.action)){
  st.latest.reset();if(!Capture(q,s,f,raw))return failed();if(st.query==128)return reject(S::claim_consumed,"rmtm_observation_finite_query_capacity");
  st.latest=RmtmObservationSession267V1::State::Lease{q.request,f,raw,++st.query,q.connection_generation,q.monotonic_deadline_ms,false};q.result.provider_generation=st.generation;q.result.query_sequence=st.query;q.result.status=S::available;q.result.source_available=true;q.result.source=raw.source;q.result.reason.clear();return true;
 }
 if(!st.latest)return reject(S::stale_source,"rmtm_observation_private_query_missing");auto&lease=*st.latest;
 if(lease.consumed)return reject(S::claim_consumed,"rmtm_observation_private_query_spent");
 if(q.request.provider_generation!=st.generation||q.request.query_sequence!=lease.query||q.connection_generation!=lease.connection||q.request.deadline_unix_ms!=lease.request.deadline_unix_ms||!Core(q.request.expected,lease.request.expected)||q.request.id()==lease.request.id()||RmtmObservationKindFor267V1(q.request.action)!=RmtmObservationKindFor267V1(lease.request.action)||q.request.phase!=lease.request.phase||q.request.offer_target!=lease.request.offer_target)return reject(S::stale_source,"rmtm_observation_original_query_custody_mismatch");
 q.monotonic_deadline_ms=(std::min)(q.monotonic_deadline_ms,lease.mono);if(!Time(q))return reject(S::expired,"rmtm_observation_private_query_original_deadline");
 if(!Capture(q,s,f,raw))return failed();if(!Same(f,lease.frame)||raw!=lease.raw)return reject(S::stale_source,"rmtm_observation_complete_private_Source_changed");
 if(!ActionAllowed(raw.source,q.request.action))return reject(S::unavailable,"rmtm_observation_actual_fixed_UI_action_refused");const auto purpose=Purpose(q.request);if(st.spent[purpose]||st.claims.size()>=6)return reject(S::claim_consumed,"rmtm_observation_fixed_UI_purpose_once_per_case");
 if(!Time(q))return reject(S::expired,"rmtm_observation_beforeclaim_original_deadline");const auto claim=++st.claim;st.claims.push_back({claim,std::string(q.request.id())});st.spent[purpose]=true;lease.consumed=true;q.result.claim_sequence=claim;
 const auto call=CallRmtmObservationRaw267V1(q.bindings,f,q.request,q.monotonic_deadline_ms,raw);q.result.effect_attempted=call.entered;q.result.native_returned=call.native_returned;q.result.native_handled=call.native_handled;q.result.cleanup_known=call.cleanup_known;
 if(!call.cleanup_known||call.status==RmtmObservationCallStatus267V1::indeterminate){st.unknown.store(true);return reject(S::indeterminate,"rmtm_observation_actual_UI_completion_UNKNOWN");}if(call.status!=RmtmObservationCallStatus267V1::returned)return reject(S::stale_source,"rmtm_observation_preentry_refused_spentclaim_retained");
 q.result.status=S::navigation_dispatched;q.result.source_available=true;q.result.source=lease.raw.source;q.result.reason.clear();return true;
 }catch(...){const bool unknown=q.observation_entered||q.result.effect_attempted;if(q.session&&unknown)BlockRmtmObservationUnknown267V1(*q.session);q.result.status=unknown?RmtmObservationStatus267V1::indeterminate:RmtmObservationStatus267V1::unavailable;q.result.cleanup_known=!unknown;q.result.source_available=false;q.result.source.reset();q.result.reason="rmtm_observation_owner_exception";}
#endif
 return true;
}
bool ExecuteRmtmObservationOnOwner267V1(void*p,const ck3_11906::MainThreadExecutionStampV1&s)noexcept{if(!p)return false;auto&q=*static_cast<RmtmObservationContext267V1*>(p);__try{return ExecuteRmtmObservationInner267V1(q,s);}__except(EXCEPTION_EXECUTE_HANDLER){if(q.session)BlockRmtmObservationUnknown267V1(*q.session);q.result.status=RmtmObservationStatus267V1::indeterminate;q.result.cleanup_known=false;q.result.source_available=false;q.result.source.reset();return true;}}
}
