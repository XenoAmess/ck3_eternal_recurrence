#include "xar_bridge/ck3_121003_rmtm_actor_transition26785313_owner_v1.hpp"
#include "xar_bridge/ck3_121003_date_postday26785313_v1.hpp"
#include "xar_bridge/ck3_121003_date_time_gate26785313_v1.hpp"
#include <algorithm>
#include <atomic>
#include <chrono>
#include <limits>
#include <mutex>
#include <vector>
#include <cstring>
#include "xar_bridge/ck3_121003_rmtm_title_query26785313_owner_v1.hpp"
namespace xar::ck3_121003::build26785313 {namespace {
using A=RmtmTransitionAction267V1;using S=RmtmTransitionStatus267V1;
std::uint64_t Wall()noexcept{const auto n=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();return n>0?static_cast<std::uint64_t>(n):0;}
std::string_view Id(const RmtmTransitionRequest267V1&q)noexcept{return {q.request_id.data(),q.request_id_size};}
std::string_view Op(const RmtmTransitionRequest267V1&q)noexcept{return {q.operation_id.data(),q.operation_id_size};}
bool Equal(const ck3_1210::CoreSnapshotPrefix&a,const ck3_1210::CoreSnapshotPrefix&b)noexcept{return a.clock.date_raw==b.clock.date_raw&&a.clock.speed==b.clock.speed&&a.clock.paused==b.clock.paused&&a.local_player_id==b.local_player_id&&a.map_ready==b.map_ready&&a.has_played_character==b.has_played_character&&a.played_character_id==b.played_character_id&&a.played_character_alive==b.played_character_alive;}
bool SameWorld(const ck3_1210::DateSentinelObservationV1&a,const ck3_1210::DateSentinelObservationV1&b)noexcept{return a.game==b.game&&a.jomini==b.jomini&&a.storage==b.storage&&a.data==b.data&&a.players==b.players&&a.player==b.player&&a.core.local_player_id==b.core.local_player_id&&a.core.clock.speed==b.core.clock.speed;}
bool SameFrame(const RmtmRoleFrame267V1&a,const RmtmRoleFrame267V1&b)noexcept{return a.facts_verified&&b.facts_verified&&Equal(a.world.core,b.world.core)&&SameWorld(a.world,b.world)&&a.world.actor==b.world.actor;}
bool Time(const RmtmTransitionContext267V1&q)noexcept{const auto t=Wall();return t&&t<q.request.deadline_unix_ms&&q.monotonic_deadline_ms&&GetTickCount64()<q.monotonic_deadline_ms;}
bool SameBody(const RmtmTransitionRequest267V1&a,const RmtmTransitionRequest267V1&b)noexcept{return Op(a)==Op(b)&&a.deadline_unix_ms==b.deadline_unix_ms&&a.provider_generation==b.provider_generation&&a.query_sequence==b.query_sequence&&a.actor_epoch==b.actor_epoch&&Equal(a.expected,b.expected);}
RmtmTransitionResult267V1 Initial(const RmtmTransitionRequest267V1&q){RmtmTransitionResult267V1 r;r.action=q.action;r.request_id=std::string(Id(q));r.operation_id=std::string(Op(q));r.provider_generation=q.provider_generation;r.query_sequence=q.query_sequence;r.actor_epoch=q.actor_epoch;r.deadline_unix_ms=q.deadline_unix_ms;return r;}
[[maybe_unused]]bool Frame(RmtmTransitionContext267V1&q,const ck3_11906::MainThreadExecutionStampV1&s,RmtmRoleFrame267V1&f,bool original_core=true){
 if(!Time(q)||!q.mailbox||q.mailbox->offline_fixture||!q.connection_generation||q.mailbox->permitted_executor_quattuortrigintary!=&ExecuteRmtmOnOwner267V1)return false;
 q.bindings=BindReadonlyImage(reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)),kExecutableSha256);std::string reason;
 const bool good=ReadRmtmRoleFrameOnOwner267V1(q.bindings,q.mailbox,q.ticket,s,&q.invocation,q.request.deadline_unix_ms,q.monotonic_deadline_ms,f,reason);
 if(f.facts_verified&&original_core){q.result.facts_available=true;q.result.facts=f.world.core;q.result.connection_generation=q.connection_generation;q.result.ticket_sequence=q.ticket.sequence;q.result.pump_epoch=s.pump_epoch;q.result.thread_id=s.thread_id;}
 if(!good){q.result.reason=reason;return false;}if(original_core&&!Equal(f.world.core,q.request.expected)){q.result.reason="rmtm_actual_original_core_changed";return false;}return Time(q);
}
struct ResumeAdmission{RmtmTransitionContext267V1&q;const ck3_11906::MainThreadExecutionStampV1&stamp;ck3_1210::DateSentinelStateV1&runtime;CommandImageBindingsV1 commands;};
[[maybe_unused]]bool BeforeResume(void*opaque)noexcept{
 if(!opaque)return false;auto&a=*static_cast<ResumeAdmission*>(opaque);auto&q=a.q;RmtmRoleFrame267V1 f;
 if(!Time(q)||!Frame(q,a.stamp,f)||!ck3_1210::DateSentinelAllowsResumeV1(a.runtime,q.request.expected))return false;
 const auto fresh=BindCurrentCommandImageV1(q.bindings.module_base,{kGameVersion,kSteamBuildId,kExecutableSha256});
 if(!fresh.current_image_verified||fresh.offline_fixture||!CurrentCommandTargetsMatchV1(fresh)||fresh.commands.command_manager!=a.commands.commands.command_manager||fresh.commands.queue_owned_command!=a.commands.commands.queue_owned_command||fresh.commands.pause_primary_vtable!=a.commands.commands.pause_primary_vtable||fresh.commands.pause_secondary_vtable!=a.commands.commands.pause_secondary_vtable||!Time(q))return false;
 q.result.progress->resume_attempted=true;return true;
}
bool RmtmActualPredecessorDead267V1(const ReadonlyBindings&b,std::int32_t expected)noexcept{
 __try{const auto p=reinterpret_cast<std::uintptr_t>(ck3_1210::ResolveCoreCharacter(b.core,expected));std::uint32_t id=0xFFFFFFFFU,magic=0;std::uintptr_t living=0,dead=0;
  if(p){std::memcpy(&id,reinterpret_cast<void*>(p+0x18),4);std::memcpy(&magic,reinterpret_cast<void*>(p+0x1C),4);std::memcpy(&living,reinterpret_cast<void*>(p+0x1C0),8);std::memcpy(&dead,reinterpret_cast<void*>(p+0x1D0),8);}return p&&id==static_cast<std::uint32_t>(expected)&&magic==0x43686172U&&!living&&dead;
 }__except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
bool ExactProof(const ck3_1210::RmtmFixedDayProof267V1&p,const RmtmTransitionRequest267V1&q,const RmtmRoleFrame267V1&before)noexcept{
 const auto&s=p.status;return p.family==ck3_1210::FixedDayFamily267V1::rmtm&&p.captured&&p.generation&&p.generation==s.generation&&p.original_deadline_unix_ms==q.deadline_unix_ms&&Equal(p.before.core,q.expected)&&SameWorld(p.before,before.world)&&p.before.actor==before.world.actor&&p.after.actor&&p.after.core.played_character_id!=-1&&p.after.core.has_played_character&&p.after.core.played_character_alive&&SameWorld(p.before,p.after)&&p.after.core.clock.paused&&static_cast<std::int64_t>(q.expected.clock.date_raw)+24==p.after.core.clock.date_raw&&p.captured_unix_ms<p.original_deadline_unix_ms&&p.captured_monotonic_ms<p.monotonic_deadline_ms&&s.state==ck3_11906::TacticalDailySentinelStateV1::triggered&&s.mode==ck3_11906::TacticalDailySentinelModeV1::terminal_or_sentinel&&s.army_count==0&&s.combat_count==0&&s.starting_date_raw==q.expected.clock.date_raw&&s.target_date_raw==p.after.core.clock.date_raw&&s.last_observed_date_raw==s.target_date_raw&&s.trigger_date_raw==s.target_date_raw&&s.speed==q.expected.clock.speed&&s.completed_daily_ticks==1&&s.signed_date_delta_from_target_raw==0&&s.overshoot_days==0&&s.pause_observed&&s.pause_wrapper_called&&s.trigger_flags==ck3_11906::tactical_daily_trigger_date_deadline&&!s.terminal_observed&&!s.abnormal;
}
}
struct RmtmTransitionSession267V1::State {
 struct Lease{RmtmTransitionRequest267V1 request;RmtmTransitionSource267V1 source;RmtmRoleFrame267V1 frame;RmtmRoleRaw267V1 raw;std::uint64_t query=0,connection=0,mono=0;bool consumed=false;};
 struct DateClaim{RmtmTransitionRequest267V1 request;RmtmRoleFrame267V1 before;RmtmTransitionResult267V1 result;std::uint64_t connection=0;bool deferred_wait=false,transition_allowed=false;};
 std::mutex mutex;std::atomic_bool unknown{false};DateAdvanceSession267V1*old=nullptr;ck3_1210::DateSentinelStateV1*runtime=nullptr;
 std::uint64_t generation=GetTickCount64()?GetTickCount64():1,query=0,claim=0,epoch=0,owner_connection=0;
 std::uint32_t completed=0;std::int32_t start_date=0;bool start_captured=false;std::optional<std::uint32_t>later_full_id;std::optional<RmtmRoleFrame267V1>admitted_frame;
 std::optional<std::int32_t>song,successor;std::optional<ck3_1210::RmtmFixedDayProof267V1>first_proof;
 struct DeferredProof{RmtmRoleFrame267V1 first,second;RmtmRoleRaw267V1 role;std::uint64_t wall=0,mono=0;};std::optional<DeferredProof>deferred;std::optional<RmtmRoleFrame267V1>successor_frame;
 std::optional<RmtmPendingTransition267V1>pending;std::optional<Lease>latest;std::vector<DateClaim>dates;std::vector<std::string>effect_ids,query_ids;
};
RmtmTransitionSession267V1::RmtmTransitionSession267V1():state_(std::make_unique<State>()){}
RmtmTransitionSession267V1::~RmtmTransitionSession267V1()=default;
RmtmTransitionSession267V1&RetainedRmtmTransitionSession267V1(){static RmtmTransitionSession267V1 s;return s;}
bool BindRmtmTransitionSession267V1(RmtmTransitionSession267V1&s,DateAdvanceSession267V1&old,ck3_1210::DateSentinelStateV1&runtime)noexcept{
 std::scoped_lock lock(s.state_->mutex);if(s.state_->runtime||s.state_->old||!runtime.initialized.load()||runtime.fixture_only||runtime.bindings.offline_fixture||runtime.bindings.runtime_profile!=ck3_1210::DateSentinelRuntimeProfileV1::current26785313||!DateAdvanceRuntimeMatches267V1(old,runtime))return false;
 s.state_->runtime=&runtime;s.state_->old=&old;return true;
}
void BlockRmtmTransitionUnknown267V1(RmtmTransitionSession267V1&s)noexcept{s.state_->unknown.store(true,std::memory_order_release);if(s.state_->runtime)BlockRmtmDateCustodyUnknown267V1(*s.state_->runtime);}
void ArmRmtmTransitionDeadline267V1(RmtmTransitionContext267V1&q)noexcept{q.monotonic_deadline_ms=0;const auto t=Wall(),mono=GetTickCount64();if(t&&q.request.deadline_unix_ms>t){const auto delta=(std::min)(q.request.deadline_unix_ms-t,std::uint64_t{8000});if(mono<=(std::numeric_limits<std::uint64_t>::max)()-delta)q.monotonic_deadline_ms=mono+delta;}}
bool ExecuteRmtmTransitionInner267V1(RmtmTransitionContext267V1&q,[[maybe_unused]]const ck3_11906::MainThreadExecutionStampV1&s)noexcept{
 q.result=Initial(q.request);q.result.reason="rmtm_current_transition_default_off";
#if defined(XAR_CK3_ENABLE_121003_26785313_RMTM_TRANSITION_V1) && XAR_CK3_ENABLE_121003_26785313_RMTM_TRANSITION_V1
 try{const auto reject=[&](S status,const char*reason){q.result.status=status;q.result.reason=reason;return true;};
 if(!q.session||!RmtmTransitionRequestShape267V1(q.request)||(q.request.action==A::query_operation&&!q.deferred_observation_only))return reject(S::unavailable,"rmtm_actual_request_or_session_unavailable");auto&st=*q.session->state_;std::scoped_lock lock(st.mutex);q.result.completed_natural_days=st.completed;
 // Only Dispatch's private flag enters this branch; the wire has no such input.
 if(q.deferred_observation_only){
  for(auto&entry:st.dates){if(Op(entry.request)!=Op(q.request))continue;
   if(!entry.deferred_wait||!SameBody(entry.request,q.request)||entry.connection!=q.connection_generation||st.owner_connection!=q.connection_generation||st.epoch||st.pending||!st.first_proof||!st.runtime||!st.old||!DateAdvanceRuntimeMatches267V1(*st.old,*st.runtime))return reject(S::unavailable,"rmtm_actual_deferred_private_frontier_unavailable");
   q.result=entry.result;q.result.action=A::query_operation;q.result.request_id=std::string(Id(q.request));q.result.source_available=false;q.result.source.reset();
   const auto unknown=[&](const char*why){BlockRmtmTransitionUnknown267V1(*q.session);q.result.status=S::indeterminate;q.result.reason=why;entry.result=q.result;entry.deferred_wait=false;return true;};
   const auto&p=*st.first_proof;q.monotonic_deadline_ms=(std::min)(q.monotonic_deadline_ms,p.monotonic_deadline_ms);
   if(st.unknown.load()||!Time(q)||!RmtmDatePredecessorResolved267V1(*st.runtime))return unknown("rmtm_original_deferred_deadline_or_predecessor_unknown");
   if(!ExactProof(p,entry.request,entry.before)||p.actor_changed||p.stage!=ck3_1210::RmtmFixedDayStage267V1::song_transition||!q.result.progress||q.result.status!=S::running||!q.result.progress->exact_day_confirmed)return unknown("rmtm_actual_deferred_worker_proof_unavailable");
   // The exact worker after-sample stays immutable. These are later UI-owner samples.
   RmtmRoleFrame267V1 a,z;ck3_1210::DateSentinelObservationV1 first{},last{};
   bool busy=false;if(!Frame(q,s,a,false))return unknown("rmtm_actual_deferred_owner_world_unavailable");
   if(!ck3_1210::ReadRmtmDeferredActorOnOwner267V1(*st.runtime,p,s,first,&busy)){if(busy){q.result.reason.clear();return true;}return unknown("rmtm_actual_deferred_owner_worker_or_world_unavailable");}
   RmtmRoleFrame267V1 checked;checked.facts_verified=true;checked.world=first;
   if(!SameFrame(a,checked)||!SameWorld(a.world,p.before)||a.world.core.clock.date_raw!=p.after.core.clock.date_raw)return unknown("rmtm_actual_deferred_first_world_changed");
   if(a.world.actor==p.before.actor&&a.world.core.played_character_id==p.before.core.played_character_id){q.result.reason.clear();return true;}
   if(a.world.actor==p.before.actor||a.world.core.played_character_id==p.before.core.played_character_id)return unknown("rmtm_actual_deferred_actor_pointer_id_disagree");
   RmtmRoleRaw267V1 raw;std::string reason;const bool read=ReadRmtmRoleRaw267V1(q.bindings,a,true,q.request.deadline_unix_ms,q.monotonic_deadline_ms,raw,reason);q.native_observation_entered=q.native_observation_entered||raw.entered;
   if(!raw.cleanup_known){q.result.cleanup_known=false;return unknown("rmtm_actual_deferred_owned_role_cleanup_unknown");}
   if(!read)return unknown("rmtm_actual_deferred_successor_role_unavailable");
   if(!Frame(q,s,z,false))return unknown("rmtm_actual_deferred_second_owner_world_unavailable");
   if(!ck3_1210::ReadRmtmDeferredActorOnOwner267V1(*st.runtime,p,s,last,&busy)){if(busy){q.result.reason.clear();return true;}return unknown("rmtm_actual_deferred_second_owner_worker_unavailable");}
   checked.world=last;if(!SameFrame(a,z)||!SameFrame(z,checked)||!Time(q))return unknown("rmtm_actual_deferred_actor_world_or_deadline_changed");
   if(!raw.definition||!raw.shown){q.result.reason.clear();return true;}
   RmtmPendingTransition267V1 pending;pending.operation_id=std::string(Op(entry.request));pending.claim_sequence=q.result.claim_sequence;pending.generation=p.generation;pending.original_deadline_unix_ms=p.original_deadline_unix_ms;pending.before_actor_id=p.before.core.played_character_id;pending.after_actor_id=z.world.core.played_character_id;pending.starting_date_raw=p.before.core.clock.date_raw;pending.target_date_raw=p.after.core.clock.date_raw;pending.completed_daily_ticks=1;pending.exact_day_confirmed=pending.shutdown_safe=pending.cleanup_known=true;
   st.deferred=RmtmTransitionSession267V1::State::DeferredProof{a,z,raw,Wall(),GetTickCount64()};st.successor_frame=z;st.pending=std::move(pending);entry.deferred_wait=false;
   q.result.progress->after_actor_id=z.world.core.played_character_id;q.result.progress->transition_pending=true;q.result.status=S::transition_pending;q.result.reason.clear();entry.result=q.result;return true;
  }return reject(S::unavailable,"rmtm_original_deferred_operation_unavailable");
 }
 if(!st.runtime||!st.old||!DateAdvanceRuntimeMatches267V1(*st.old,*st.runtime))return reject(S::unavailable,"rmtm_actual_retained_runtime_binding_unavailable");
 if(st.unknown.load(std::memory_order_acquire)){q.result.cleanup_known=false;return reject(S::indeterminate,"rmtm_original_unknown_retained_no_new_permission");}
 if(!Time(q))return reject(S::expired,"rmtm_original_deadline_expired");
 for(const auto&id:st.effect_ids)if(id==Id(q.request))return reject(S::claim_consumed,"rmtm_original_effect_request_id_consumed");
 if(st.owner_connection&&st.owner_connection!=q.connection_generation)return reject(S::stale_source,"rmtm_original_process_connection_custody_mismatch");
 if(st.pending){if(q.request.deadline_unix_ms!=st.pending->original_deadline_unix_ms)return reject(S::stale_source,"rmtm_original_pending_deadline_mismatch");q.monotonic_deadline_ms=(std::min)(q.monotonic_deadline_ms,st.first_proof->monotonic_deadline_ms);if(!Time(q))return reject(S::expired,"rmtm_original_pending_deadline_expired");}
 RmtmRoleFrame267V1 frame;if(!Frame(q,s,frame))return true;
 const auto*successor_world=st.successor_frame?&st.successor_frame->world:st.first_proof?&st.first_proof->after:nullptr;
 if(successor_world&&(!SameWorld(frame.world,*successor_world)||frame.world.actor!=successor_world->actor||frame.world.core.played_character_id!=successor_world->core.played_character_id||frame.world.core.clock.date_raw!=successor_world->core.clock.date_raw))return reject(S::stale_source,"rmtm_actual_retained_world_actor_or_date_changed");
 const bool successor=bool(st.pending)||st.epoch>0;RmtmRoleRaw267V1 raw;std::string reason;
 const bool read=ReadRmtmRoleRaw267V1(q.bindings,frame,successor,q.request.deadline_unix_ms,q.monotonic_deadline_ms,raw,reason);q.native_observation_entered=q.native_observation_entered||raw.entered;q.result.cleanup_known=raw.cleanup_known;
 if(!read){if(!raw.cleanup_known){BlockRmtmTransitionUnknown267V1(*q.session);return reject(S::indeterminate,"rmtm_actual_owned_role_cleanup_unknown");}q.result.reason=reason;return true;}
 const auto before=frame;if(!Frame(q,s,frame)||!SameFrame(before,frame))return reject(S::stale_source,"rmtm_actual_world_changed_after_fixed_role_read");
 // Actual fixed Later witness + qualified primary getter captures a private
 // full title. No caller title identifier can install or replace this anchor.
 if(raw.predicates[2]){
  const auto&w=frame.world;RmtmTitleFrame267V1 tf{w.core,reinterpret_cast<std::uintptr_t>(w.game),reinterpret_cast<std::uintptr_t>(w.jomini),reinterpret_cast<std::uintptr_t>(w.storage),reinterpret_cast<std::uintptr_t>(w.data),reinterpret_cast<std::uintptr_t>(w.players),reinterpret_cast<std::uintptr_t>(w.player),reinterpret_cast<std::uintptr_t>(w.actor),true};
  RmtmTitleQueryRequest267V1 guard;guard.expected=w.core;guard.deadline_unix_ms=q.request.deadline_unix_ms;std::uint32_t full=0xFFFFFFFFU;bool entered=false,cleanup=true;
  const bool captured=CaptureRmtmTitleQueryPrimary267V1(q.bindings,tf,guard,q.monotonic_deadline_ms,full,entered,cleanup,reason);q.native_observation_entered|=entered;
  if(!cleanup){q.result.cleanup_known=false;BlockRmtmTransitionUnknown267V1(*q.session);return reject(S::indeterminate,"rmtm_private_later_capture_cleanup_unknown");}
  if(!captured||full==0xFFFFFFFFU||(st.later_full_id&&*st.later_full_id!=full))return reject(S::stale_source,"rmtm_private_full_later_title_changed");
  RmtmTitleRaw267V1 title;RmtmTitleRequest267V1 tq{w.core,full,q.request.deadline_unix_ms};const bool readTitle=ReadRmtmTitleRaw267V1(q.bindings,tf,tq,q.monotonic_deadline_ms,title,reason);q.native_observation_entered|=title.entered;
  if(!title.cleanup_known){q.result.cleanup_known=false;BlockRmtmTransitionUnknown267V1(*q.session);return reject(S::indeterminate,"rmtm_private_later_read_cleanup_unknown");}
  if(!readTitle||!title.source.holder||!title.source.holder->alive||title.source.holder->full_id!=static_cast<std::uint32_t>(w.core.played_character_id))return reject(S::unavailable,"rmtm_actual_full_later_holder_not_current_player");
  st.later_full_id=full;
 }
 const bool actual_predecessor_dead=!successor||(st.song&&RmtmActualPredecessorDead267V1(q.bindings,*st.song));
 const auto&runtime=*st.runtime;const bool runtime_ready=runtime.initialized.load()&&!runtime.armed.load()&&(st.dates.empty()||runtime.shutdown_safe.load())&&!runtime.access_cleanup_unknown.load()&&!runtime.pending_failure.load()&&!runtime.shutdown_requested.load();
 const bool predecessor=RmtmDatePredecessorResolved267V1(runtime);
 RmtmTransitionSource267V1 source;source.role=successor?RmtmActorRole267V1::successor:RmtmActorRole267V1::song;source.definition_found=raw.definition!=0;if(raw.definition)source.native_shown=raw.shown;source.actor_epoch=st.epoch;source.song_actor_id=st.song;source.successor_actor_id=st.successor;source.pending=st.pending;source.runtime_ready=runtime_ready;source.predecessor_resolved=predecessor;source.completed_natural_days=st.completed;source.maximum_natural_days=14;source.case_start_date_raw=st.start_captured?st.start_date:frame.world.core.clock.date_raw;source.case_start_captured=st.start_captured||raw.shown;source.execute_time_identity_confirmed={};
 if(source.native_shown==true){if(successor){if(successor_world&&frame.world.core.played_character_id==successor_world->core.played_character_id)source.successor_actor_id=frame.world.core.played_character_id;}else if(!st.song||*st.song==frame.world.core.played_character_id)source.song_actor_id=frame.world.core.played_character_id;}
 source.advance_admissible=source.native_shown==true&&!raw.predicates[5]&&runtime_ready&&predecessor&&!st.pending&&st.completed<14&&(st.epoch==0?st.completed==st.dates.size()&&source.song_actor_id==frame.world.core.played_character_id:st.epoch==1&&st.completed==st.dates.size()&&source.successor_actor_id==frame.world.core.played_character_id);
 source.confirm_admissible=source.native_shown==true&&st.later_full_id&&raw.predicates[2]&&actual_predecessor_dead&&runtime_ready&&predecessor&&st.pending&&st.epoch==0&&source.successor_actor_id==frame.world.core.played_character_id&&st.first_proof&&(st.first_proof->actor_changed||st.deferred.has_value());
 if(!RmtmTransitionSourceShape267V1(source))return reject(S::unavailable,"rmtm_actual_role_source_coherence_unavailable");
 q.result.source_available=true;q.result.source=source;
 if(q.request.action==A::query_role){
  for(const auto&id:st.query_ids)if(id==Id(q.request))return reject(S::claim_consumed,"rmtm_original_query_request_id_retained");
  if(st.query_ids.size()>=128||st.query==(std::numeric_limits<std::uint64_t>::max)())return reject(S::capacity_exhausted,"rmtm_query_capacity_exhausted_no_reset");
  if(raw.shown){if(!st.start_captured){st.start_date=frame.world.core.clock.date_raw;st.start_captured=true;}if(!st.owner_connection)st.owner_connection=q.connection_generation;st.song=source.song_actor_id;st.admitted_frame=frame;}
  st.query_ids.emplace_back(Id(q.request));st.latest=RmtmTransitionSession267V1::State::Lease{q.request,source,frame,raw,++st.query,q.connection_generation,q.monotonic_deadline_ms,false};
  q.result.provider_generation=st.generation;q.result.query_sequence=st.query;q.result.actor_epoch=st.epoch;q.result.status=S::available;q.result.reason.clear();return true;
 }
 if(!st.latest)return reject(S::stale_source,"rmtm_original_private_role_query_unavailable");auto&lease=*st.latest;
 if(q.request.provider_generation!=st.generation||q.request.query_sequence!=lease.query||q.request.actor_epoch!=lease.source.actor_epoch||q.connection_generation!=lease.connection||q.request.deadline_unix_ms!=lease.request.deadline_unix_ms||!Equal(q.request.expected,lease.request.expected)||Id(q.request)==Id(lease.request))return reject(S::stale_source,"rmtm_original_private_role_query_mismatch");
 if(lease.consumed)return reject(S::claim_consumed,"rmtm_original_private_role_query_consumed");
 q.monotonic_deadline_ms=(std::min)(q.monotonic_deadline_ms,lease.mono);if(!Time(q))return reject(S::expired,"rmtm_original_private_role_query_expired");
 if(!SameFrame(frame,lease.frame)||raw!=lease.raw||source!=lease.source)return reject(S::stale_source,"rmtm_actual_complete_private_role_source_changed");q.result.source=lease.source;
 if(q.request.action==A::confirm_epoch){
  if(!source.confirm_admissible||!st.pending||Op(q.request)!=st.pending->operation_id||st.claim>=14)return reject(S::unavailable,"rmtm_actual_pending_successor_confirmation_refused");
  st.effect_ids.emplace_back(Id(q.request));lease.consumed=true;q.result.claim_sequence=++st.claim;st.song=source.song_actor_id;st.successor=source.successor_actor_id;st.epoch=1;st.pending.reset();st.admitted_frame=frame;
  q.result.accepted=true;q.result.actor_epoch=1;q.result.status=S::epoch_confirmed;q.result.reason.clear();return true;
 }
 if(!source.advance_admissible||q.request.actor_epoch!=st.epoch||st.dates.size()>=14)return reject(S::unavailable,"rmtm_actual_finite_frontier_or_role_not_admissible");
 for(const auto&entry:st.dates)if(Op(entry.request)==Op(q.request))return reject(S::claim_consumed,"rmtm_original_date_operation_retained_no_replay");
 if((st.start_captured&&static_cast<std::int64_t>(st.start_date)+static_cast<std::int64_t>(st.completed)*24!=q.request.expected.clock.date_raw)||q.request.expected.clock.date_raw>(std::numeric_limits<std::int32_t>::max)()-24)return reject(S::unavailable,"rmtm_actual_date_target_overflow");
 const auto commands=BindCurrentCommandImageV1(q.bindings.module_base,{kGameVersion,kSteamBuildId,kExecutableSha256});if(!commands.current_image_verified||commands.offline_fixture||!CurrentCommandTargetsMatchV1(commands))return reject(S::unavailable,"rmtm_actual_command_targets_unavailable");
 const auto gate=ReadRuntimeEventTimeGate267V1(q.bindings,q.request.expected);if(gate!=RuntimeEventTimeGate267V1::clear){if(gate==RuntimeEventTimeGate267V1::indeterminate){BlockRmtmTransitionUnknown267V1(*q.session);q.result.cleanup_known=false;return reject(S::indeterminate,"rmtm_actual_runtime_time_gate_unknown");}return reject(S::unavailable,gate==RuntimeEventTimeGate267V1::blocked?"rmtm_actual_runtime_event_still_blocks_date":"rmtm_actual_runtime_time_gate_unavailable");}
 RmtmRoleFrame267V1 final_frame;if(!Time(q)||!Frame(q,s,final_frame)||!SameFrame(frame,final_frame))return reject(S::stale_source,"rmtm_actual_world_changed_before_claim");
 if(!ClaimRmtmDateCustody267V1(runtime,!st.dates.empty()))return reject(S::claim_consumed,"rmtm_actual_other_date_or_unknown_blocks_claim");
 st.effect_ids.emplace_back(Id(q.request));lease.consumed=true;st.owner_connection=q.connection_generation;if(!st.start_captured){st.start_date=q.request.expected.clock.date_raw;st.start_captured=true;}st.song=source.song_actor_id;st.successor=source.successor_actor_id;q.result.claim_sequence=++st.claim;q.result.accepted=true;
 RmtmTransitionProgress267V1 progress;progress.starting_date_raw=q.request.expected.clock.date_raw;progress.target_date_raw=progress.starting_date_raw+24;progress.last_observed_date_raw=progress.starting_date_raw;progress.before_actor_id=q.request.expected.played_character_id;progress.arm_attempted=true;q.result.progress=progress;q.result.effect_attempted=true;q.result.status=S::indeterminate;
 st.dates.push_back({q.request,frame,q.result,q.connection_generation});auto&entry=st.dates.back();entry.transition_allowed=st.epoch==0&&raw.predicates[6];
 ck3_11906::TacticalDailySentinelArmRequestV1 arm{};arm.mode=ck3_11906::TacticalDailySentinelModeV1::terminal_or_sentinel;arm.starting_date_raw=progress.starting_date_raw;arm.target_date_raw=progress.target_date_raw;arm.speed=q.request.expected.clock.speed;
 if(ck3_1210::ArmRmtmFixedDay267V1(*st.runtime,arm,q.request.deadline_unix_ms,entry.transition_allowed?ck3_1210::RmtmFixedDayStage267V1::song_transition:ck3_1210::RmtmFixedDayStage267V1::recipient_stable)!=ck3_11906::TacticalDailySentinelArmStatusV1::armed){BlockRmtmTransitionUnknown267V1(*q.session);ck3_1210::RequestDateSentinelShutdownV1(*st.runtime);q.result.reason="rmtm_original_ARM_completion_unavailable_no_retry";entry.result=q.result;return true;}
 q.result.progress->generation=st.runtime->generation.load();q.result.progress->armed=st.runtime->armed.load();
 const auto command=ck3_1210::MakePauseCommand(commands.commands,q.request.expected.local_player_id,false);ResumeAdmission admission{q,s,*st.runtime,commands};q.command_ownership_entered=true;
 const auto submitted=ck3_1210::SubmitCommandCopy(commands.commands,&command,7,&BeforeResume,&admission);q.command_ownership_entered=false;q.result.native_returned=true;
 q.result.progress->resume_submitted=q.result.progress->resume_attempted&&submitted==ck3_1210::CommandSubmitResult::submitted;
 if(!q.result.progress->resume_submitted){(void)ck3_1210::CancelDateSentinelV1(*st.runtime,q.result.progress->generation);BlockRmtmTransitionUnknown267V1(*q.session);ck3_1210::RequestDateSentinelShutdownV1(*st.runtime);q.result.reason="rmtm_original_ARM_or_Resume_not_closed_no_retry";entry.result=q.result;return true;}
 q.result.status=S::submitted;q.result.reason.clear();entry.result=q.result;return true;
 }catch(...){if(q.session&&(q.command_ownership_entered||q.native_observation_entered||q.result.claim_sequence)){BlockRmtmTransitionUnknown267V1(*q.session);q.result.status=S::indeterminate;q.result.cleanup_known=false;}q.result.source_available=false;q.result.source.reset();q.result.reason="rmtm_original_owner_exception_custody_retained";return true;}
#else
 return true;
#endif
}
RmtmTransitionResult267V1 QueryRmtmTransitionOperation267V1(RmtmTransitionSession267V1&s,const RmtmTransitionRequest267V1&q,std::uint64_t connection,bool*deferred_needed)noexcept{
 if(deferred_needed)*deferred_needed=false;auto empty=Initial(q);empty.reason="rmtm_original_date_operation_unavailable";
 try{auto&st=*s.state_;std::scoped_lock lock(st.mutex);if(q.action!=A::query_operation||!RmtmTransitionRequestShape267V1(q)||!st.runtime||!connection)return empty;
 for(auto&entry:st.dates){if(Op(entry.request)!=Op(q))continue;if(!SameBody(q,entry.request))return empty;
  auto r=entry.result;if(r.progress&&r.progress->generation&&r.progress->resume_submitted&&r.status!=S::transition_pending&&r.status!=S::completed_day){
   ck3_1210::RmtmFixedDayProof267V1 proof;ck3_11906::TacticalDailySentinelStatusV1 status;const bool captured=ck3_1210::ReadRmtmFixedDayProof267V1(*st.runtime,r.progress->generation,proof,status);
   auto&p=*r.progress;p.failure_flags=st.runtime->pending_failure.load();p.shutdown_safe=st.runtime->shutdown_safe.load();p.armed=st.runtime->armed.load();p.access_cleanup_unknown=st.runtime->access_cleanup_unknown.load();p.last_observed_date_raw=status.last_observed_date_raw;p.completed_daily_ticks=status.completed_daily_ticks;p.overshoot_days=status.overshoot_days;
   if(!st.unknown.load()&&captured&&ExactProof(proof,entry.request,entry.before)&&!p.failure_flags&&!p.armed&&p.shutdown_safe&&!p.access_cleanup_unknown){
    p.after_actor_id=proof.after.core.played_character_id;p.exact_day_confirmed=true;st.completed=static_cast<std::uint32_t>(st.dates.size());r.completed_natural_days=st.completed;p.transition_pending=proof.actor_changed;
    if(entry.transition_allowed&&entry.request.actor_epoch==0&&proof.stage==ck3_1210::RmtmFixedDayStage267V1::song_transition){
     if(proof.actor_changed){RmtmPendingTransition267V1 pending;pending.operation_id=std::string(Op(entry.request));pending.claim_sequence=r.claim_sequence;pending.generation=proof.generation;pending.original_deadline_unix_ms=proof.original_deadline_unix_ms;pending.before_actor_id=proof.before.core.played_character_id;pending.after_actor_id=proof.after.core.played_character_id;pending.starting_date_raw=proof.before.core.clock.date_raw;pending.target_date_raw=proof.after.core.clock.date_raw;pending.completed_daily_ticks=1;pending.exact_day_confirmed=pending.shutdown_safe=pending.cleanup_known=true;st.first_proof=proof;st.successor_frame=RmtmRoleFrame267V1{true,proof.after};st.pending=std::move(pending);r.status=S::transition_pending;}
     else {st.first_proof=proof;entry.deferred_wait=true;r.status=S::running;}
    }else if(!entry.transition_allowed&&proof.stage==ck3_1210::RmtmFixedDayStage267V1::recipient_stable&&!proof.actor_changed&&entry.request.actor_epoch==st.epoch&&((st.epoch==0&&st.song==proof.after.core.played_character_id)||(st.epoch==1&&st.successor==proof.after.core.played_character_id))){r.status=S::completed_day;r.actor_epoch=st.epoch;st.admitted_frame=RmtmRoleFrame267V1{true,proof.after};if(st.epoch)st.successor_frame=*st.admitted_frame;if(st.completed==14)CompleteRmtmDateCustody267V1(*st.runtime);}
    else {r.status=S::indeterminate;r.reason="rmtm_actual_finite_stage_proof_mismatch";BlockRmtmTransitionUnknown267V1(s);}
   }else if(!st.unknown.load()&&status.generation==p.generation&&status.state==ck3_11906::TacticalDailySentinelStateV1::armed&&!p.failure_flags&&!p.access_cleanup_unknown)r.status=S::running;
   else {r.status=S::indeterminate;r.reason="rmtm_original_date_completion_unknown_no_replay";BlockRmtmTransitionUnknown267V1(s);}
   entry.result=r;
  }
  if(deferred_needed&&entry.deferred_wait&&connection==entry.connection&&!st.unknown.load())*deferred_needed=true;
  r.action=A::query_operation;r.request_id=std::string(Id(q));r.source_available=false;r.source.reset();return r;
 }
 return empty;
 }catch(...){BlockRmtmTransitionUnknown267V1(s);empty.status=S::indeterminate;empty.cleanup_known=false;empty.reason="rmtm_original_status_custody_unknown";return empty;}
}
bool ExecuteRmtmTransitionOnOwner267V1(void*opaque,const ck3_11906::MainThreadExecutionStampV1&s)noexcept{if(!opaque)return false;auto&q=*static_cast<RmtmTransitionContext267V1*>(opaque);__try{return ExecuteRmtmTransitionInner267V1(q,s);}__except(EXCEPTION_EXECUTE_HANDLER){if(q.session)BlockRmtmTransitionUnknown267V1(*q.session);q.result.status=S::indeterminate;q.result.cleanup_known=false;q.result.source_available=false;q.result.source.reset();q.result.reason="rmtm_original_native_owner_exception_unknown";return true;}}
bool RmtmCaseAdmitted267V1(const ck3_1210::CoreSnapshotPrefix&core,std::uint64_t connection,std::uintptr_t game,std::uintptr_t jomini)noexcept {
 auto&s=RetainedRmtmTransitionSession267V1();auto&st=*s.state_;std::scoped_lock lock(st.mutex);
 if(st.unknown.load()||!st.runtime||!st.old||!DateAdvanceRuntimeMatches267V1(*st.old,*st.runtime)||!RmtmDatePredecessorResolved267V1(*st.runtime)||!connection||st.owner_connection!=connection||st.pending||!st.start_captured||st.completed>14||static_cast<std::int64_t>(st.start_date)+static_cast<std::int64_t>(st.completed)*24!=core.clock.date_raw||!st.admitted_frame)return false;
 const auto&w=st.admitted_frame->world;const auto expected=st.epoch?st.successor:st.song;
 return expected&&*expected==core.played_character_id&&Equal(core,w.core)&&game==reinterpret_cast<std::uintptr_t>(w.game)&&jomini==reinterpret_cast<std::uintptr_t>(w.jomini)&&!st.runtime->armed.load()&&(st.dates.empty()||st.runtime->shutdown_safe.load())&&!st.runtime->access_cleanup_unknown.load()&&!st.runtime->pending_failure.load()&&!st.runtime->shutdown_requested.load();
}
bool ReadRmtmPrivateCaseAnchor267V1(const ck3_1210::CoreSnapshotPrefix&core,std::uint64_t connection,std::uintptr_t game,std::uintptr_t jomini,RmtmPrivateCaseAnchor267V1&out)noexcept{
 out={};auto&s=RetainedRmtmTransitionSession267V1();auto&st=*s.state_;std::scoped_lock lock(st.mutex);
 if(st.unknown.load()||!st.runtime||!st.old||!DateAdvanceRuntimeMatches267V1(*st.old,*st.runtime)||!RmtmDatePredecessorResolved267V1(*st.runtime)||!connection||st.owner_connection!=connection||st.pending||!st.start_captured||st.completed>14||static_cast<std::int64_t>(st.start_date)+static_cast<std::int64_t>(st.completed)*24!=core.clock.date_raw||!st.admitted_frame||!st.later_full_id||!st.song)return false;
 const auto&w=st.admitted_frame->world;const auto expected=st.epoch?st.successor:st.song;
 if(!expected||*expected!=core.played_character_id||!Equal(core,w.core)||game!=reinterpret_cast<std::uintptr_t>(w.game)||jomini!=reinterpret_cast<std::uintptr_t>(w.jomini)||st.runtime->armed.load()||(!st.dates.empty()&&!st.runtime->shutdown_safe.load())||st.runtime->access_cleanup_unknown.load()||st.runtime->pending_failure.load()||st.runtime->shutdown_requested.load())return false;
 out.full_title_id=*st.later_full_id;out.predecessor=*st.song;out.successor=st.successor;out.completed_days=st.completed;return true;
}
} // namespace
