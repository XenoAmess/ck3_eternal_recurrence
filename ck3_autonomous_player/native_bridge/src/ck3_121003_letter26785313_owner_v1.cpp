#include "xar_bridge/ck3_121003_letter26785313_owner_v1.hpp"
#include "xar_bridge/ck3_121003_letter_set26785313_owner_v1.hpp"
#include <algorithm>
#include <atomic>
#include <chrono>
#include <limits>
#include <mutex>
#include <windows.h>
namespace xar::ck3_121003::build26785313 {namespace {
std::uint64_t Wall()noexcept{const auto t=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();return t>0?static_cast<std::uint64_t>(t):0;}
[[maybe_unused]]bool Time(const LetterContext267V1&q)noexcept{const auto t=Wall();return t&&t<q.request.deadline_unix_ms&&q.monotonic_deadline_ms&&GetTickCount64()<q.monotonic_deadline_ms;}
[[maybe_unused]]bool SameCore(const ck3_1210::CoreSnapshotPrefix&a,const ck3_1210::CoreSnapshotPrefix&b)noexcept{return a.clock.date_raw==b.clock.date_raw&&a.clock.speed==b.clock.speed&&a.clock.paused==b.clock.paused&&a.local_player_id==b.local_player_id&&a.map_ready==b.map_ready&&a.has_played_character==b.has_played_character&&a.played_character_id==b.played_character_id&&a.played_character_alive==b.played_character_alive;}
[[maybe_unused]]bool SameFrame(const LetterFrame267V1&a,const LetterFrame267V1&b)noexcept{return a.facts_verified&&b.facts_verified&&SameCore(a.core,b.core)&&a.scene==b.scene&&a.witness==b.witness;}
[[maybe_unused]]bool Frame(LetterContext267V1&q,const ck3_11906::MainThreadExecutionStampV1&s,LetterFrame267V1&out){
 if(!Time(q)||!q.mailbox||q.mailbox->offline_fixture||!q.connection_generation||q.mailbox->permitted_executor_duodenary!=&ExecuteLetterOnOwner267V1)return false;
 q.bindings=BindReadonlyImage(reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)),kExecutableSha256);std::string reason;const bool good=ReadLetterFrameOnOwner267V1(q.bindings,q.mailbox,q.ticket,s,&q,q.request.deadline_unix_ms,q.monotonic_deadline_ms,out,reason);
 if(out.facts_verified){q.result.facts_available=true;q.result.facts=out.core;q.result.connection_generation=q.connection_generation;q.result.ticket_sequence=q.ticket.sequence;q.result.pump_epoch=s.pump_epoch;q.result.thread_id=s.thread_id;}
 if(!good){q.result.reason=reason;return false;}if(!SameCore(out.core,q.request.expected)){q.result.reason="letter_actual_core_changed";return false;}return Time(q);
}
[[maybe_unused]]bool Observe(LetterContext267V1&q,const LetterFrame267V1&frame,LetterRaw267V1&raw){
 const auto b=BindLetterImage267V1(q.bindings.module_base,kExecutableSha256);if(!b.verified){q.result.reason="letter_actual_current_image_unavailable";return false;}std::string reason;const bool good=ReadLetterRaw267V1(q.bindings,b,q.request.expected,frame.scene,q.monotonic_deadline_ms,raw,reason);q.native_observation_entered=q.native_observation_entered||raw.native_read_entered;q.result.cleanup_known=raw.cleanup_known;
 if(!good){q.result.reason=reason;return false;}q.result.source_available=true;q.result.source=raw.source;return Time(q);
}
}
struct LetterSession267V1::State{
 struct Lease{LetterFrame267V1 frame;LetterRaw267V1 raw;LetterRequest267V1 request;std::uint64_t query=0,connection=0,mono=0;bool consumed=false;};
   struct SetLease{LetterSetFrame267V1 frame;LetterSetRaw267V1 raw;LetterSetRequest267V1 request;std::uint64_t query=0,connection=0,mono=0;bool consumed=false;};
struct Claim{std::uint64_t sequence=0;std::string id;std::uintptr_t game=0,jomini=0;std::int32_t actor=-1,instance=-1;};
 std::atomic_bool unknown{false};std::mutex mutex;std::uint64_t generation=GetTickCount64()?GetTickCount64():1,query_sequence=0,claim_sequence=0;std::optional<Lease>latest;std::optional<SetLease>latest_set;std::vector<Claim>claims;
};
LetterSession267V1::LetterSession267V1():state_(std::make_unique<State>()){}
LetterSession267V1::~LetterSession267V1()=default;
void BlockLetterUnknown267V1(LetterSession267V1&s)noexcept{s.state_->unknown.store(true,std::memory_order_release);}
void ArmLetterDeadline267V1(LetterContext267V1&q)noexcept{q.monotonic_deadline_ms=0;const auto t=Wall();if(t&&q.request.deadline_unix_ms>t)q.monotonic_deadline_ms=GetTickCount64()+(std::min)(q.request.deadline_unix_ms-t,std::uint64_t{8000});}
bool ExecuteLetterInner267V1(LetterContext267V1&q,[[maybe_unused]]const ck3_11906::MainThreadExecutionStampV1&s)noexcept{
 q.result={};q.result.action=q.request.action;q.result.provider_generation=q.request.provider_generation;q.result.query_sequence=q.request.query_sequence;q.result.reason="current_letter_default_off";
#if defined(XAR_CK3_ENABLE_121003_26785313_LETTER_V1) && XAR_CK3_ENABLE_121003_26785313_LETTER_V1
 try{using S=LetterStatus267V1;const auto reject=[&](S status,const char*why){q.result.status=status;q.result.reason=why;return true;};if(!q.session||!LetterRequestShape267V1(q.request))return reject(S::unavailable,"letter_actual_request_or_retained_session_unavailable");auto&state=*q.session->state_;std::scoped_lock lock(state.mutex);
  for(const auto&claim:state.claims)if(claim.id==q.request.id()){q.result.claim_sequence=claim.sequence;return reject(S::claim_consumed,"letter_original_effect_id_retained_no_replay");}
  if(!Time(q))return reject(S::expired,"letter_original_deadline_expired");LetterFrame267V1 frame;if(!Frame(q,s,frame))return true;
  if(state.unknown.load(std::memory_order_acquire)){q.result.cleanup_known=false;return reject(S::indeterminate,"letter_prior_native_completion_unknown_no_retry");}
  if(state.claims.size()>=64||state.query_sequence==(std::numeric_limits<std::uint64_t>::max)())return reject(S::claim_consumed,"letter_retained_capacity_exhausted");
  const auto failed=[&]{if(!q.result.cleanup_known){state.unknown.store(true);q.result.status=S::indeterminate;}else q.result.status=Time(q)?S::unavailable:S::expired;return true;};
  if(q.request.action==LetterAction267V1::query_letter){state.latest.reset();state.latest_set.reset();const auto before=frame;LetterRaw267V1 raw;if(!Observe(q,frame,raw))return failed();if(!Frame(q,s,frame)||!SameFrame(before,frame))return reject(S::stale_source,"letter_actual_core_or_gui_changed_after_read");
   LetterSession267V1::State::Lease lease{frame,raw,q.request,++state.query_sequence,q.connection_generation,q.monotonic_deadline_ms,false};state.latest=std::move(lease);q.result.provider_generation=state.generation;q.result.query_sequence=state.query_sequence;q.result.status=S::available;q.result.reason.clear();return true;
  }
  if(!state.latest)return reject(S::stale_source,"letter_original_private_query_unavailable");auto&lease=*state.latest;
  if(q.request.provider_generation!=state.generation||q.request.query_sequence!=lease.query||q.connection_generation!=lease.connection||q.request.deadline_unix_ms!=lease.request.deadline_unix_ms||!SameCore(q.request.expected,lease.request.expected)||q.request.id()==lease.request.id())return reject(S::stale_source,"letter_original_private_query_source_mismatch");
  if(lease.consumed)return reject(S::claim_consumed,"letter_original_private_query_consumed");if(GetTickCount64()>=lease.mono)return reject(S::expired,"letter_original_query_deadline_expired");q.monotonic_deadline_ms=(std::min)(q.monotonic_deadline_ms,lease.mono);
  LetterRaw267V1 raw;if(!Observe(q,frame,raw))return failed();const auto before=frame;if(!Frame(q,s,frame)||!SameFrame(before,frame)||!SameFrame(lease.frame,frame)||raw!=lease.raw)return reject(S::stale_source,"letter_actual_instance_definition_or_options_changed");
  if(!raw.source.known_reply_admissible||!raw.source.instance_id)return reject(S::unavailable,"letter_exact_known_definition_single_option_or_native_validity_refused");
  for(const auto&claim:state.claims)if(claim.game==raw.game&&claim.jomini==raw.jomini&&claim.actor==q.request.expected.played_character_id&&claim.instance==*raw.source.instance_id)return reject(S::claim_consumed,"letter_same_actual_event_instance_claim_retained_no_replay");
  if(!Time(q))return reject(S::expired,"letter_original_preclaim_deadline_expired");const auto sequence=state.claim_sequence+1;state.claims.push_back({sequence,std::string(q.request.id()),raw.game,raw.jomini,q.request.expected.played_character_id,*raw.source.instance_id});state.claim_sequence=sequence;lease.consumed=true;q.result.claim_sequence=sequence;
  const auto b=BindLetterImage267V1(q.bindings.module_base,kExecutableSha256);const auto call=ReplyKnownLetterRaw267V1(q.bindings,b,q.request.expected,frame.scene,q.monotonic_deadline_ms,raw);q.result.effect_attempted=call.effect_entered;q.result.native_returned=call.status==LetterRawCallStatus267V1::returned;q.result.cleanup_known=call.cleanup_known;
  if(!call.cleanup_known||call.status==LetterRawCallStatus267V1::indeterminate){state.unknown.store(true);return reject(S::indeterminate,"letter_native_select_completion_unknown_no_replay");}
  if(call.status!=LetterRawCallStatus267V1::returned)return reject(S::stale_source,"letter_pre_effect_refused_original_claim_retained");q.result.status=S::reply_dispatched;q.result.reason.clear();return true;
 }catch(...){if(q.session&&(q.native_observation_entered||q.result.effect_attempted))BlockLetterUnknown267V1(*q.session);q.result.status=q.native_observation_entered||q.result.effect_attempted?LetterStatus267V1::indeterminate:LetterStatus267V1::unavailable;q.result.reason="letter_exception_original_claim_retained";}
#endif
 return true;
}
bool ExecuteLetterOnOwner267V1(void*p,const ck3_11906::MainThreadExecutionStampV1&s)noexcept{if(!p)return false;auto&q=*static_cast<LetterContext267V1*>(p);__try{return ExecuteLetterInner267V1(q,s);}__except(EXCEPTION_EXECUTE_HANDLER){if(q.session)BlockLetterUnknown267V1(*q.session);q.result.status=LetterStatus267V1::indeterminate;q.result.cleanup_known=false;return true;}}

namespace {
[[maybe_unused]]bool SetTime(const LetterSetContext267V1&q)noexcept{const auto t=Wall();return t&&t<q.request.deadline_unix_ms&&q.monotonic_deadline_ms&&GetTickCount64()<q.monotonic_deadline_ms;}
[[maybe_unused]]bool SetSameFrame(const LetterSetFrame267V1&a,const LetterSetFrame267V1&b)noexcept{return a.facts_verified&&b.facts_verified&&SameCore(a.core,b.core)&&a.scene==b.scene&&a.witness==b.witness;}
[[maybe_unused]]bool SetFrame(LetterSetContext267V1&q,const ck3_11906::MainThreadExecutionStampV1&s,LetterSetFrame267V1&out){
 if(!SetTime(q)||!q.mailbox||q.mailbox->offline_fixture||!q.connection_generation||q.mailbox->permitted_executor_thirdenary!=&ExecuteLetterSetOnOwner267V1)return false;
 q.bindings=BindReadonlyImage(reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)),kExecutableSha256);std::string reason;const bool good=ReadLetterSetFrameOnOwner267V1(q.bindings,q.mailbox,q.ticket,s,&q,q.request.deadline_unix_ms,q.monotonic_deadline_ms,out,reason);
 if(out.facts_verified){q.result.facts_available=true;q.result.facts=out.core;q.result.connection_generation=q.connection_generation;q.result.ticket_sequence=q.ticket.sequence;q.result.pump_epoch=s.pump_epoch;q.result.thread_id=s.thread_id;}
 if(!good){q.result.reason=reason;return false;}if(!SameCore(out.core,q.request.expected)){q.result.reason="letter_set_actual_core_changed";return false;}return SetTime(q);
}
[[maybe_unused]]bool SetObserve(LetterSetContext267V1&q,const LetterSetFrame267V1&frame,LetterSetRaw267V1&raw){
 const auto b=BindLetterImage267V1(q.bindings.module_base,kExecutableSha256);if(!b.verified){q.result.reason="letter_set_actual_current_image_unavailable";return false;}std::string reason;const bool good=ReadLetterSetRaw267V1(q.bindings,b,q.request.expected,frame.scene,q.monotonic_deadline_ms,raw,reason);q.native_observation_entered=q.native_observation_entered||raw.native_read_entered;q.result.cleanup_known=raw.cleanup_known;
 if(!good){q.result.reason=reason;return false;}q.result.source_available=true;q.result.source=raw.source;return SetTime(q);
}
}
LetterSession267V1& RetainedLetterSession267V1(){static LetterSession267V1 retained;return retained;}
void ArmLetterSetDeadline267V1(LetterSetContext267V1&q)noexcept{q.monotonic_deadline_ms=0;const auto t=Wall();if(t&&q.request.deadline_unix_ms>t)q.monotonic_deadline_ms=GetTickCount64()+(std::min)(q.request.deadline_unix_ms-t,std::uint64_t{8000});}
bool ExecuteLetterSetInner267V1(LetterSetContext267V1&q,[[maybe_unused]]const ck3_11906::MainThreadExecutionStampV1&s)noexcept{
 q.result={};q.result.action=q.request.action;q.result.provider_generation=q.request.provider_generation;q.result.query_sequence=q.request.query_sequence;q.result.instance_id=q.request.instance_id;q.result.reason="current_letter_set_default_off";
#if defined(XAR_CK3_ENABLE_121003_26785313_LETTER_SET_V1) && XAR_CK3_ENABLE_121003_26785313_LETTER_SET_V1
 try{using S=LetterStatus267V1;const auto reject=[&](S status,const char*why){q.result.status=status;q.result.reason=why;return true;};if(!q.session||!LetterSetRequestShape267V1(q.request))return reject(S::unavailable,"letter_set_actual_request_or_retained_session_unavailable");auto&state=*q.session->state_;std::scoped_lock lock(state.mutex);
  for(const auto&claim:state.claims)if(claim.id==q.request.id()){q.result.claim_sequence=claim.sequence;return reject(S::claim_consumed,"letter_set_original_effect_id_retained_no_replay");}
  if(!SetTime(q))return reject(S::expired,"letter_set_original_deadline_expired");LetterSetFrame267V1 frame;if(!SetFrame(q,s,frame))return true;
  if(state.unknown.load(std::memory_order_acquire)){q.result.cleanup_known=false;return reject(S::indeterminate,"letter_set_prior_native_completion_unknown_no_retry");}
  if(state.claims.size()>=64||state.query_sequence==(std::numeric_limits<std::uint64_t>::max)())return reject(S::claim_consumed,"letter_set_retained_capacity_exhausted");
  const auto failed=[&]{if(!q.result.cleanup_known){state.unknown.store(true);q.result.status=S::indeterminate;}else q.result.status=SetTime(q)?S::unavailable:S::expired;return true;};
  if(q.request.action==LetterSetAction267V1::query_letters){state.latest.reset();state.latest_set.reset();const auto before=frame;LetterSetRaw267V1 raw;if(!SetObserve(q,frame,raw))return failed();if(!SetFrame(q,s,frame)||!SetSameFrame(before,frame))return reject(S::stale_source,"letter_set_actual_core_or_gui_changed_after_read");
   LetterSession267V1::State::SetLease lease{frame,raw,q.request,++state.query_sequence,q.connection_generation,q.monotonic_deadline_ms,false};state.latest_set=std::move(lease);q.result.provider_generation=state.generation;q.result.query_sequence=state.query_sequence;q.result.status=S::available;q.result.reason.clear();return true;
  }
  if(!state.latest_set)return reject(S::stale_source,"letter_set_original_private_census_unavailable");auto&lease=*state.latest_set;
  if(q.request.provider_generation!=state.generation||q.request.query_sequence!=lease.query||q.connection_generation!=lease.connection||q.request.deadline_unix_ms!=lease.request.deadline_unix_ms||!SameCore(q.request.expected,lease.request.expected)||q.request.id()==lease.request.id())return reject(S::stale_source,"letter_set_original_private_census_source_mismatch");
  if(lease.consumed)return reject(S::claim_consumed,"letter_set_original_private_census_consumed");if(GetTickCount64()>=lease.mono)return reject(S::expired,"letter_set_original_query_deadline_expired");q.monotonic_deadline_ms=(std::min)(q.monotonic_deadline_ms,lease.mono);
  LetterSetRaw267V1 raw;if(!SetObserve(q,frame,raw))return failed();const auto before=frame;if(!SetFrame(q,s,frame)||!SetSameFrame(before,frame)||!SetSameFrame(lease.frame,frame)||raw!=lease.raw)return reject(S::stale_source,"letter_set_actual_full_census_or_sources_changed");
  const LetterSource267V1*chosen=nullptr;for(const auto&row:raw.source.letters)if(row.instance_id==q.request.instance_id){if(chosen)return reject(S::unavailable,"letter_set_requested_instance_ambiguous");chosen=&row;}
  if(!chosen||!chosen->known_reply_admissible||!chosen->instance_id)return reject(S::unavailable,"letter_set_exact_requested_known_instance_refused");
  for(const auto&claim:state.claims)if(claim.game==raw.manager_census.game&&claim.jomini==raw.manager_census.jomini&&claim.actor==q.request.expected.played_character_id&&claim.instance==*chosen->instance_id)return reject(S::claim_consumed,"letter_set_same_actual_instance_retained_no_replay");
  if(!SetTime(q))return reject(S::expired,"letter_set_original_preclaim_deadline_expired");const auto sequence=state.claim_sequence+1;state.claims.push_back({sequence,std::string(q.request.id()),raw.manager_census.game,raw.manager_census.jomini,q.request.expected.played_character_id,*chosen->instance_id});state.claim_sequence=sequence;lease.consumed=true;q.result.claim_sequence=sequence;
  const auto b=BindLetterImage267V1(q.bindings.module_base,kExecutableSha256);const auto call=ReplyKnownLetterSetRaw267V1(q.bindings,b,q.request.expected,frame.scene,q.monotonic_deadline_ms,raw,*chosen->instance_id);q.result.effect_attempted=call.effect_entered;q.result.native_returned=call.status==LetterRawCallStatus267V1::returned;q.result.cleanup_known=call.cleanup_known;
  if(!call.cleanup_known||call.status==LetterRawCallStatus267V1::indeterminate){state.unknown.store(true);return reject(S::indeterminate,"letter_set_native_select_completion_unknown_no_replay");}
  if(call.status!=LetterRawCallStatus267V1::returned)return reject(S::stale_source,"letter_set_pre_effect_refused_original_claim_retained");q.result.status=S::reply_dispatched;q.result.reason.clear();return true;
 }catch(...){if(q.session&&(q.native_observation_entered||q.result.effect_attempted))BlockLetterUnknown267V1(*q.session);q.result.status=q.native_observation_entered||q.result.effect_attempted?LetterStatus267V1::indeterminate:LetterStatus267V1::unavailable;q.result.reason="letter_set_exception_original_claim_retained";}
#endif
 return true;
}
bool ExecuteLetterSetOnOwner267V1(void*p,const ck3_11906::MainThreadExecutionStampV1&s)noexcept{if(!p)return false;auto&q=*static_cast<LetterSetContext267V1*>(p);__try{return ExecuteLetterSetInner267V1(q,s);}__except(EXCEPTION_EXECUTE_HANDLER){if(q.session)BlockLetterUnknown267V1(*q.session);q.result.status=LetterStatus267V1::indeterminate;q.result.cleanup_known=false;return true;}}
} // namespace
