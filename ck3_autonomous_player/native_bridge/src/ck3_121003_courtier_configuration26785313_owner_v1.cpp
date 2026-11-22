#include "xar_bridge/ck3_121003_courtier_configuration26785313_owner_v1.hpp"
#include <algorithm>
#include <atomic>
#include <chrono>
#include <limits>
#include <mutex>
#include <windows.h>
namespace xar::ck3_121003::build26785313 {namespace {
std::uint64_t Wall()noexcept{const auto t=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();return t>0?static_cast<std::uint64_t>(t):0;}
[[maybe_unused]]bool Time(const CourtierConfigurationContext267V1&q)noexcept{const auto t=Wall();return t&&t<q.request.deadline_unix_ms&&q.monotonic_deadline_ms&&GetTickCount64()<q.monotonic_deadline_ms;}
[[maybe_unused]]bool SameCore(const ck3_1210::CoreSnapshotPrefix&a,const ck3_1210::CoreSnapshotPrefix&b)noexcept{return a.clock.date_raw==b.clock.date_raw&&a.clock.speed==b.clock.speed&&a.clock.paused==b.clock.paused&&a.local_player_id==b.local_player_id&&a.map_ready==b.map_ready&&a.has_played_character==b.has_played_character&&a.played_character_id==b.played_character_id&&a.played_character_alive==b.played_character_alive;}
[[maybe_unused]]bool SameFrame(const CourtierConfigurationFrame267V1&a,const CourtierConfigurationFrame267V1&b)noexcept{return a.facts_verified&&b.facts_verified&&SameCore(a.core,b.core)&&a.scene==b.scene&&a.witness==b.witness;}
[[maybe_unused]]bool Frame(CourtierConfigurationContext267V1&q,const ck3_11906::MainThreadExecutionStampV1&s,CourtierConfigurationFrame267V1&out){
 if(!Time(q)||!q.mailbox||q.mailbox->offline_fixture||!q.connection_generation||q.mailbox->permitted_executor_duovigintary!=&ExecuteCourtierConfigurationOnOwner267V1)return false;
 q.bindings=BindReadonlyImage(reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)),kExecutableSha256);std::string reason;const bool good=ReadCourtierConfigurationFrameOnOwner267V1(q.bindings,q.mailbox,q.ticket,s,&q,q.request.deadline_unix_ms,q.monotonic_deadline_ms,out,reason);
 q.native_observation_entered=q.native_observation_entered||out.native_read_entered;q.result.cleanup_known=q.result.cleanup_known&&out.cleanup_known;if(out.facts_verified){q.result.facts_available=true;q.result.facts=out.core;q.result.connection_generation=q.connection_generation;q.result.ticket_sequence=q.ticket.sequence;q.result.pump_epoch=s.pump_epoch;q.result.thread_id=s.thread_id;}
 if(!good){q.result.reason=reason;if(!out.cleanup_known){q.result.status=CourtierConfigurationStatus267V1::indeterminate;if(q.session)BlockCourtierConfigurationUnknown267V1(*q.session);}return false;}if(!SameCore(out.core,q.request.expected)){q.result.reason="courtier_configuration_actual_core_changed";return false;}return Time(q);
}
[[maybe_unused]]bool Observe(CourtierConfigurationContext267V1&q,const CourtierConfigurationFrame267V1&frame,CourtierConfigurationRaw267V1&raw){std::string reason;const bool good=ReadCourtierConfigurationRaw267V1(q.bindings,q.request.expected,frame.scene,q.monotonic_deadline_ms,q.request.product,q.request.setting,raw,reason);q.native_observation_entered=q.native_observation_entered||raw.native_read_entered;q.result.cleanup_known=raw.cleanup_known;if(!good){q.result.reason=reason;return false;}q.result.source_available=true;q.result.source=raw.source;return Time(q);}
}
struct CourtierConfigurationSession267V1::State{
 struct Lease{CourtierConfigurationFrame267V1 frame;CourtierConfigurationRaw267V1 raw;CourtierConfigurationRequest267V1 request;std::uint64_t query=0,connection=0,mono=0;bool consumed=false;};
struct Claim{std::uint64_t sequence=0;std::string id;std::uintptr_t global=0,jomini=0;std::int32_t actor=-1;};
 std::atomic_bool unknown{false};std::mutex mutex;std::uint64_t generation=GetTickCount64()?GetTickCount64():1,query_sequence=0,claim_sequence=0;std::optional<Lease>latest;std::vector<Claim>claims;
};
CourtierConfigurationSession267V1::CourtierConfigurationSession267V1():state_(std::make_unique<State>()){}
CourtierConfigurationSession267V1::~CourtierConfigurationSession267V1()=default;
void BlockCourtierConfigurationUnknown267V1(CourtierConfigurationSession267V1&s)noexcept{s.state_->unknown.store(true,std::memory_order_release);}
CourtierConfigurationSession267V1&RetainedCourtierConfigurationSession267V1(){static CourtierConfigurationSession267V1 s;return s;}
void ArmCourtierConfigurationDeadline267V1(CourtierConfigurationContext267V1&q)noexcept{q.monotonic_deadline_ms=0;const auto t=Wall();if(t&&q.request.deadline_unix_ms>t)q.monotonic_deadline_ms=GetTickCount64()+(std::min)(q.request.deadline_unix_ms-t,std::uint64_t{8000});}
bool ExecuteCourtierConfigurationInner267V1(CourtierConfigurationContext267V1&q,[[maybe_unused]]const ck3_11906::MainThreadExecutionStampV1&s)noexcept{
 q.result={};q.result.action=q.request.action;q.result.provider_generation=q.request.provider_generation;q.result.query_sequence=q.request.query_sequence;q.result.product=q.request.product;q.result.setting=q.request.setting;q.result.reason="current_courtier_configuration_default_off";
#if defined(XAR_CK3_ENABLE_121003_26785313_COURTIER_CONFIGURATION_V1) && XAR_CK3_ENABLE_121003_26785313_COURTIER_CONFIGURATION_V1
 try{using S=CourtierConfigurationStatus267V1;const auto reject=[&](S status,const char*why){q.result.status=status;q.result.reason=why;return true;};if(!q.session||!CourtierConfigurationRequestShape267V1(q.request))return reject(S::unavailable,"courtier_configuration_actual_request_or_retained_session_unavailable");auto&state=*q.session->state_;std::scoped_lock lock(state.mutex);
  for(const auto&claim:state.claims)if(claim.id==q.request.id()){q.result.claim_sequence=claim.sequence;return reject(S::claim_consumed,"courtier_configuration_original_effect_id_retained_no_replay");}
  if(state.unknown.load(std::memory_order_acquire)){q.result.cleanup_known=false;return reject(S::indeterminate,"courtier_configuration_prior_native_completion_unknown_no_retry");}if(!Time(q))return reject(S::expired,"courtier_configuration_original_deadline_expired");CourtierConfigurationFrame267V1 frame;if(!Frame(q,s,frame))return true;
  
  if(state.claims.size()>=64||state.query_sequence==(std::numeric_limits<std::uint64_t>::max)())return reject(S::claim_consumed,"courtier_configuration_retained_capacity_exhausted");
  const auto failed=[&]{if(!q.result.cleanup_known){state.unknown.store(true);q.result.status=S::indeterminate;}else q.result.status=Time(q)?S::unavailable:S::expired;return true;};
  if(q.request.action==CourtierConfigurationAction267V1::query_configuration){state.latest.reset();const auto before=frame;CourtierConfigurationRaw267V1 raw;if(!Observe(q,frame,raw))return failed();if(!Frame(q,s,frame)||!SameFrame(before,frame))return reject(S::stale_source,"courtier_configuration_actual_core_or_gui_changed_after_read");
   CourtierConfigurationSession267V1::State::Lease lease{frame,raw,q.request,++state.query_sequence,q.connection_generation,q.monotonic_deadline_ms,false};state.latest=std::move(lease);q.result.provider_generation=state.generation;q.result.query_sequence=state.query_sequence;q.result.status=S::available;q.result.reason.clear();return true;
  }
  if(!state.latest)return reject(S::stale_source,"courtier_configuration_original_private_query_unavailable");auto&lease=*state.latest;
  if(q.request.provider_generation!=state.generation||q.request.query_sequence!=lease.query||q.connection_generation!=lease.connection||q.request.deadline_unix_ms!=lease.request.deadline_unix_ms||q.request.product!=lease.request.product||q.request.setting!=lease.request.setting||!SameCore(q.request.expected,lease.request.expected)||q.request.id()==lease.request.id())return reject(S::stale_source,"courtier_configuration_original_private_query_source_mismatch");
  if(lease.consumed)return reject(S::claim_consumed,"courtier_configuration_original_private_query_consumed");if(GetTickCount64()>=lease.mono)return reject(S::expired,"courtier_configuration_original_query_deadline_expired");q.monotonic_deadline_ms=(std::min)(q.monotonic_deadline_ms,lease.mono);
  CourtierConfigurationRaw267V1 raw;if(!Observe(q,frame,raw))return failed();const auto before=frame;if(!Frame(q,s,frame)||!SameFrame(before,frame)||!SameFrame(lease.frame,frame)||raw!=lease.raw)return reject(S::stale_source,"courtier_configuration_actual_instance_definition_or_options_changed");
  if(!raw.source.panel_found||!raw.source.execute_admissible)return reject(S::unavailable,"courtier_configuration_actual_modal_or_native_predicate_refused");
if(!Time(q))return reject(S::expired,"courtier_configuration_original_preclaim_deadline_expired");const auto sequence=state.claim_sequence+1;state.claims.push_back({sequence,std::string(q.request.id()),frame.scene.global,frame.scene.jomini,q.request.expected.played_character_id});state.claim_sequence=sequence;lease.consumed=true;q.result.claim_sequence=sequence;
       const auto call=ExecuteCourtierControlRaw267V1(q.bindings,q.request.expected,frame.scene,q.monotonic_deadline_ms,raw);q.result.effect_attempted=call.effect_entered;q.result.native_returned=call.status==LetterRawCallStatus267V1::returned;q.result.cleanup_known=call.cleanup_known;
if(!call.cleanup_known||call.status==LetterRawCallStatus267V1::indeterminate){state.unknown.store(true);return reject(S::indeterminate,"courtier_configuration_native_execute_completion_unknown_no_replay");}
  if(call.status!=LetterRawCallStatus267V1::returned)return reject(S::stale_source,"courtier_configuration_pre_effect_refused_original_claim_retained");q.result.status=S::setting_dispatched;q.result.reason.clear();return true;
 }catch(...){if(q.session&&(q.native_observation_entered||q.result.effect_attempted))BlockCourtierConfigurationUnknown267V1(*q.session);q.result.status=q.native_observation_entered||q.result.effect_attempted?CourtierConfigurationStatus267V1::indeterminate:CourtierConfigurationStatus267V1::unavailable;q.result.reason="courtier_configuration_exception_original_claim_retained";}
#endif
 return true;
}
bool ExecuteCourtierConfigurationOnOwner267V1(void*p,const ck3_11906::MainThreadExecutionStampV1&s)noexcept{if(!p)return false;auto&q=*static_cast<CourtierConfigurationContext267V1*>(p);__try{return ExecuteCourtierConfigurationInner267V1(q,s);}__except(EXCEPTION_EXECUTE_HANDLER){if(q.session)BlockCourtierConfigurationUnknown267V1(*q.session);q.result.status=CourtierConfigurationStatus267V1::indeterminate;q.result.cleanup_known=false;return true;}}

} // namespace
