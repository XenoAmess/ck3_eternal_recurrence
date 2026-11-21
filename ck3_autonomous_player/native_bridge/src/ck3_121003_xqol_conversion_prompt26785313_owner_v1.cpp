#include "xar_bridge/ck3_121003_xqol_conversion_prompt26785313_owner_v1.hpp"
#include <algorithm>
#include <atomic>
#include <chrono>
#include <limits>
#include <mutex>
#include <windows.h>
namespace xar::ck3_121003::build26785313 {namespace {
std::uint64_t Wall()noexcept{const auto t=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();return t>0?static_cast<std::uint64_t>(t):0;}
[[maybe_unused]]bool Time(const XqolPromptContext267V1&q)noexcept{const auto t=Wall();return t&&t<q.request.deadline_unix_ms&&q.monotonic_deadline_ms&&GetTickCount64()<q.monotonic_deadline_ms;}
[[maybe_unused]]bool SameCore(const ck3_1210::CoreSnapshotPrefix&a,const ck3_1210::CoreSnapshotPrefix&b)noexcept{return a.clock.date_raw==b.clock.date_raw&&a.clock.speed==b.clock.speed&&a.clock.paused==b.clock.paused&&a.local_player_id==b.local_player_id&&a.map_ready==b.map_ready&&a.has_played_character==b.has_played_character&&a.played_character_id==b.played_character_id&&a.played_character_alive==b.played_character_alive;}
[[maybe_unused]]bool SameFrame(const XqolPromptFrame267V1&a,const XqolPromptFrame267V1&b)noexcept{return a.facts_verified&&b.facts_verified&&SameCore(a.core,b.core)&&a.scene==b.scene&&a.witness==b.witness;}
[[maybe_unused]]bool Frame(XqolPromptContext267V1&q,const ck3_11906::MainThreadExecutionStampV1&s,XqolPromptFrame267V1&out){
 if(!Time(q)||!q.mailbox||q.mailbox->offline_fixture||!q.connection_generation||q.mailbox->permitted_executor_sexdenary!=&ExecuteXqolPromptOnOwner267V1)return false;
 q.bindings=BindReadonlyImage(reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)),kExecutableSha256);std::string reason;const bool good=ReadXqolPromptFrameOnOwner267V1(q.bindings,q.mailbox,q.ticket,s,&q,q.request.deadline_unix_ms,q.monotonic_deadline_ms,out,reason);
 if(out.facts_verified){q.result.facts_available=true;q.result.facts=out.core;q.result.connection_generation=q.connection_generation;q.result.ticket_sequence=q.ticket.sequence;q.result.pump_epoch=s.pump_epoch;q.result.thread_id=s.thread_id;}
 if(!good){q.result.reason=reason;return false;}if(!SameCore(out.core,q.request.expected)){q.result.reason="xqol_prompt_actual_core_changed";return false;}return Time(q);
}
[[maybe_unused]]bool Observe(XqolPromptContext267V1&q,const XqolPromptFrame267V1&frame,XqolConversionPromptRaw267V1&raw){
 const auto b=BindLetterImage267V1(q.bindings.module_base,kExecutableSha256);if(!b.verified){q.result.reason="xqol_prompt_actual_current_image_unavailable";return false;}std::string reason;const bool good=ReadXqolConversionPromptRaw267V1(q.bindings,b,q.request.expected,frame.scene,q.monotonic_deadline_ms,raw,reason);q.native_observation_entered=q.native_observation_entered||raw.native_read_entered;q.result.cleanup_known=raw.cleanup_known;
 if(!good){q.result.reason=reason;return false;}q.result.source_available=true;XqolPromptSource267V1 source;source.resident_count=raw.census.source.resident_count;source.named_root_count=static_cast<std::int32_t>(frame.scene.roots.size());source.census_complete=true;source.confirm_admissible=raw.confirm_admissible;source.cancel_admissible=raw.cancel_admissible;if(raw.known_event){const auto&event=raw.events[*raw.known_event];source.event=event.source;source.authored_option_count=event.authored_option_count;for(auto&option:source.event->options)option.source_bound_option_key=option.authored_option_index==0?kXqolConversionConfirm267V1:kXqolConversionCancel267V1;}q.result.source=std::move(source);return Time(q);
}
}
struct XqolPromptSession267V1::State{
 struct Lease{XqolPromptFrame267V1 frame;XqolConversionPromptRaw267V1 raw;XqolPromptRequest267V1 request;std::uint64_t query=0,connection=0,mono=0;bool consumed=false;};
struct Claim{std::uint64_t sequence=0;std::string id;std::uintptr_t game=0,jomini=0;std::int32_t actor=-1,instance=-1;};
 std::atomic_bool unknown{false};std::mutex mutex;std::uint64_t generation=GetTickCount64()?GetTickCount64():1,query_sequence=0,claim_sequence=0;std::optional<Lease>latest;std::vector<Claim>claims;
};
XqolPromptSession267V1::XqolPromptSession267V1():state_(std::make_unique<State>()){}
XqolPromptSession267V1::~XqolPromptSession267V1()=default;
void BlockXqolPromptUnknown267V1(XqolPromptSession267V1&s)noexcept{s.state_->unknown.store(true,std::memory_order_release);}
XqolPromptSession267V1&RetainedXqolPromptSession267V1(){static XqolPromptSession267V1 s;return s;}
void ArmXqolPromptDeadline267V1(XqolPromptContext267V1&q)noexcept{q.monotonic_deadline_ms=0;const auto t=Wall();if(t&&q.request.deadline_unix_ms>t)q.monotonic_deadline_ms=GetTickCount64()+(std::min)(q.request.deadline_unix_ms-t,std::uint64_t{8000});}
bool ExecuteXqolPromptInner267V1(XqolPromptContext267V1&q,[[maybe_unused]]const ck3_11906::MainThreadExecutionStampV1&s)noexcept{
 q.result={};q.result.action=q.request.action;q.result.provider_generation=q.request.provider_generation;q.result.query_sequence=q.request.query_sequence;q.result.instance_id=q.request.instance_id;q.result.reason="current_xqol_prompt_default_off";
#if defined(XAR_CK3_ENABLE_121003_26785313_XQOL_CONVERSION_PROMPT_V1) && XAR_CK3_ENABLE_121003_26785313_XQOL_CONVERSION_PROMPT_V1
 try{using S=XqolPromptStatus267V1;const auto reject=[&](S status,const char*why){q.result.status=status;q.result.reason=why;return true;};if(!q.session||!XqolPromptRequestShape267V1(q.request))return reject(S::unavailable,"xqol_prompt_actual_request_or_retained_session_unavailable");auto&state=*q.session->state_;std::scoped_lock lock(state.mutex);
  for(const auto&claim:state.claims)if(claim.id==q.request.id()){q.result.claim_sequence=claim.sequence;return reject(S::claim_consumed,"xqol_prompt_original_effect_id_retained_no_replay");}
  if(!Time(q))return reject(S::expired,"xqol_prompt_original_deadline_expired");XqolPromptFrame267V1 frame;if(!Frame(q,s,frame))return true;
  if(state.unknown.load(std::memory_order_acquire)){q.result.cleanup_known=false;return reject(S::indeterminate,"xqol_prompt_prior_native_completion_unknown_no_retry");}
  if(state.claims.size()>=64||state.query_sequence==(std::numeric_limits<std::uint64_t>::max)())return reject(S::claim_consumed,"xqol_prompt_retained_capacity_exhausted");
  const auto failed=[&]{if(!q.result.cleanup_known){state.unknown.store(true);q.result.status=S::indeterminate;}else q.result.status=Time(q)?S::unavailable:S::expired;return true;};
  if(q.request.action==XqolPromptAction267V1::query_prompt){state.latest.reset();const auto before=frame;XqolConversionPromptRaw267V1 raw;if(!Observe(q,frame,raw))return failed();if(!Frame(q,s,frame)||!SameFrame(before,frame))return reject(S::stale_source,"xqol_prompt_actual_core_or_gui_changed_after_read");
   XqolPromptSession267V1::State::Lease lease{frame,raw,q.request,++state.query_sequence,q.connection_generation,q.monotonic_deadline_ms,false};state.latest=std::move(lease);q.result.provider_generation=state.generation;q.result.query_sequence=state.query_sequence;q.result.status=S::available;q.result.reason.clear();return true;
  }
  if(!state.latest)return reject(S::stale_source,"xqol_prompt_original_private_query_unavailable");auto&lease=*state.latest;
  if(q.request.provider_generation!=state.generation||q.request.query_sequence!=lease.query||q.connection_generation!=lease.connection||q.request.deadline_unix_ms!=lease.request.deadline_unix_ms||!SameCore(q.request.expected,lease.request.expected)||q.request.id()==lease.request.id())return reject(S::stale_source,"xqol_prompt_original_private_query_source_mismatch");
  if(lease.consumed)return reject(S::claim_consumed,"xqol_prompt_original_private_query_consumed");if(GetTickCount64()>=lease.mono)return reject(S::expired,"xqol_prompt_original_query_deadline_expired");q.monotonic_deadline_ms=(std::min)(q.monotonic_deadline_ms,lease.mono);
  XqolConversionPromptRaw267V1 raw;if(!Observe(q,frame,raw))return failed();const auto before=frame;if(!Frame(q,s,frame)||!SameFrame(before,frame)||!SameFrame(lease.frame,frame)||raw!=lease.raw)return reject(S::stale_source,"xqol_prompt_actual_instance_definition_or_options_changed");
     if(!raw.known_event||*raw.known_event>=raw.events.size()||!q.request.instance_id)return reject(S::unavailable,"xqol_prompt_exact_known_source_unavailable");const auto&chosen=raw.events[*raw.known_event];if(chosen.source.instance_id!=q.request.instance_id)return reject(S::stale_source,"xqol_prompt_original_actual_instance_mismatch");const bool confirm=q.request.action==XqolPromptAction267V1::confirm_conversion;if(confirm?!raw.confirm_admissible:!raw.cancel_admissible)return reject(S::unavailable,"xqol_prompt_actual_native_can_refused");
   for(const auto&claim:state.claims)if(claim.game==raw.census.game&&claim.jomini==raw.census.jomini&&claim.actor==q.request.expected.played_character_id&&claim.instance==*q.request.instance_id)return reject(S::claim_consumed,"xqol_prompt_same_actual_event_instance_claim_retained_no_replay");
   if(!Time(q))return reject(S::expired,"xqol_prompt_original_preclaim_deadline_expired");const auto sequence=state.claim_sequence+1;state.claims.push_back({sequence,std::string(q.request.id()),raw.census.game,raw.census.jomini,q.request.expected.played_character_id,*q.request.instance_id});state.claim_sequence=sequence;lease.consumed=true;q.result.claim_sequence=sequence;
   const auto b=BindLetterImage267V1(q.bindings.module_base,kExecutableSha256);const auto call=SelectXqolConversionPromptRaw267V1(q.bindings,b,q.request.expected,frame.scene,q.monotonic_deadline_ms,raw,confirm?XqolConversionChoice267V1::confirm:XqolConversionChoice267V1::cancel);q.result.effect_attempted=call.effect_entered;q.result.native_returned=call.status==LetterRawCallStatus267V1::returned;q.result.cleanup_known=call.cleanup_known;
if(!call.cleanup_known||call.status==LetterRawCallStatus267V1::indeterminate){state.unknown.store(true);return reject(S::indeterminate,"xqol_prompt_native_select_completion_unknown_no_replay");}
  if(call.status!=LetterRawCallStatus267V1::returned)return reject(S::stale_source,"xqol_prompt_pre_effect_refused_original_claim_retained");q.result.status=confirm?S::confirmation_dispatched:S::cancellation_dispatched;q.result.reason.clear();return true;
 }catch(...){if(q.session&&(q.native_observation_entered||q.result.effect_attempted))BlockXqolPromptUnknown267V1(*q.session);q.result.status=q.native_observation_entered||q.result.effect_attempted?XqolPromptStatus267V1::indeterminate:XqolPromptStatus267V1::unavailable;q.result.reason="xqol_prompt_exception_original_claim_retained";}
#endif
 return true;
}
bool ExecuteXqolPromptOnOwner267V1(void*p,const ck3_11906::MainThreadExecutionStampV1&s)noexcept{if(!p)return false;auto&q=*static_cast<XqolPromptContext267V1*>(p);__try{return ExecuteXqolPromptInner267V1(q,s);}__except(EXCEPTION_EXECUTE_HANDLER){if(q.session)BlockXqolPromptUnknown267V1(*q.session);q.result.status=XqolPromptStatus267V1::indeterminate;q.result.cleanup_known=false;return true;}}

} // namespace
