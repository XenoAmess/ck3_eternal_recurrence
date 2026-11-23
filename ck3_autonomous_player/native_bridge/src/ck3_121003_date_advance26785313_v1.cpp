#include "xar_bridge/ck3_121003_date_advance26785313_v1.hpp"
#include "xar_bridge/ck3_121003_core_route26785313_v1.hpp"
#include "xar_bridge/ck3_121003_date_family_custody26785313_v1.hpp"
#if defined(XAR_CK3_ENABLE_121003_26785313_DATE_ADVANCE_V1) && XAR_CK3_ENABLE_121003_26785313_DATE_ADVANCE_V1
#include "xar_bridge/ck3_121003_date_postday26785313_v1.hpp"
#if !defined(XAR_CK3_ENABLE_121003_26785313_DATE_POSTDAY_BINDINGS_V1) || !XAR_CK3_ENABLE_121003_26785313_DATE_POSTDAY_BINDINGS_V1
#error Current_date_advance_requires_the_exact_current_postday_binding
#endif
#if !defined(XAR_CK3_ENABLE_121003_26785313_COMMAND_BINDINGS_V1) || XAR_CK3_ENABLE_121003_26785313_COMMAND_BINDINGS_V1 != 1
#error Current_date_advance_requires_the_exact_current_command_binding
#endif
#if !defined(XAR_CK3_ENABLE_121003_26785313_CORE_ROUTE_V1) || !XAR_CK3_ENABLE_121003_26785313_CORE_ROUTE_V1
#error Current_date_advance_requires_the_exact_current_core_owner_route
#endif
#endif
#if defined(XAR_CK3_ENABLE_121003_26785313_FULLSCREEN_EVENT_V1) && XAR_CK3_ENABLE_121003_26785313_FULLSCREEN_EVENT_V1
#include "xar_bridge/ck3_121003_date_time_gate26785313_v1.hpp"
#endif
#include <algorithm>
#include <chrono>
#include <limits>
#include <windows.h>
namespace xar::ck3_121003::build26785313 {namespace {
using Status=DateAdvanceStatus267V1;
struct Lock {SRWLOCK &lock;explicit Lock(SRWLOCK &v) noexcept:lock(v){AcquireSRWLockExclusive(&lock);}~Lock(){ReleaseSRWLockExclusive(&lock);}};
bool Equal(const ck3_1210::CoreSnapshotPrefix&a,const ck3_1210::CoreSnapshotPrefix&b) noexcept {
 return a.clock.date_raw==b.clock.date_raw&&a.clock.speed==b.clock.speed&&a.clock.paused==b.clock.paused&&
  a.local_player_id==b.local_player_id&&a.map_ready==b.map_ready&&a.has_played_character==b.has_played_character&&
  a.played_character_id==b.played_character_id&&a.played_character_alive==b.played_character_alive;
}
bool Id(const std::array<char,97>&id,std::uint8_t size) noexcept {
 if(!size||size>96||id[size]!=0)return false;
 for(std::size_t i=0;i<size;++i){const char c=id[i];if(!((c>='0'&&c<='9')||(c>='a'&&c<='z')||
  (c>='A'&&c<='Z')||c=='-'||c=='_'||c=='.'))return false;}return true;
}
bool SameBody(const DateAdvanceRequest267V1&a,const DateAdvanceRequest267V1&b) noexcept {
 return a.operation()==b.operation()&&a.deadline_unix_ms==b.deadline_unix_ms&&Equal(a.expected_core,b.expected_core);
}
std::uint64_t Wall() noexcept {
 const auto n=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();
 return n>0?static_cast<std::uint64_t>(n):0;
}
[[maybe_unused]]bool Unexpired(const DateAdvanceContext267V1&q) noexcept {
 const auto now=Wall();return now&&q.monotonic_deadline_ms&&now<q.request.deadline_unix_ms&&GetTickCount64()<q.monotonic_deadline_ms;
}
[[maybe_unused]]bool ReadCurrent(DateAdvanceContext267V1&q,const ck3_11906::MainThreadExecutionStampV1&s) noexcept {
#if defined(XAR_CK3_ENABLE_121003_26785313_DATE_ADVANCE_V1) && XAR_CK3_ENABLE_121003_26785313_DATE_ADVANCE_V1
 ReadonlyObservation actual;
 if(!ReadDateAdvanceCoreOnOwner267V1(q.bindings,q.mailbox,q.ticket,s,&q,actual)||!actual.available||
  actual.offline_fixture||!actual.main_owner_observed||!Equal(actual.core,q.request.expected_core)||
  actual.core.clock.date_raw!=s.date_raw||actual.core.clock.paused!=s.paused){q.result.status=Status::stale_core;return false;}
 q.result.core_before=actual.core;q.result.owner_before_verified=true;
 q.result.connection_generation=q.connection_generation;q.result.ticket_sequence=q.ticket.sequence;
 q.result.pump_epoch=s.pump_epoch;q.result.thread_id=s.thread_id;return true;
#else
 (void)q;(void)s;return false;
#endif
}
// All changes originate under the actual retained old-session lock. The separate
// lock only publishes cross-family unresolved/UNKNOWN state; it never reads or
// edits old firstActor, old claims, old outcomes or deadlines.
struct DateFamilyCustody267V1 {SRWLOCK lock=SRWLOCK_INIT;const DateAdvanceSession267V1*old_session=nullptr;const ck3_1210::DateSentinelStateV1*runtime=nullptr;bool old_open=false,ted_active=false,ccc_active=false,unknown=false;};
DateFamilyCustody267V1 g_date_family;
void PublishOldCustody(DateAdvanceSession267V1&s,bool open,bool unknown)noexcept {
 Lock lock(g_date_family.lock);if(g_date_family.old_session!=&s)return;
 g_date_family.old_open=open;g_date_family.unknown=g_date_family.unknown||unknown;
}
bool OldMayClaimCustody(DateAdvanceSession267V1&s)noexcept {
 Lock lock(g_date_family.lock);
#if (defined(XAR_CK3_ENABLE_121003_26785313_TED_TRANSITION_V1) && XAR_CK3_ENABLE_121003_26785313_TED_TRANSITION_V1) || (defined(XAR_CK3_ENABLE_121003_26785313_CCC_TRANSITION_V1) && XAR_CK3_ENABLE_121003_26785313_CCC_TRANSITION_V1)
 if(g_date_family.old_session!=&s||g_date_family.ted_active||g_date_family.ccc_active||g_date_family.unknown)return false;g_date_family.old_open=true;return true;
#else
 (void)s;return true;
#endif
}
struct Admission {DateAdvanceContext267V1&q;const ck3_11906::MainThreadExecutionStampV1&stamp;CommandImageBindingsV1 commands;};
[[maybe_unused]]bool BeforeResume(void *opaque) noexcept {
#if defined(XAR_CK3_ENABLE_121003_26785313_DATE_ADVANCE_V1) && XAR_CK3_ENABLE_121003_26785313_DATE_ADVANCE_V1
 if(!opaque)return false;auto&a=*static_cast<Admission*>(opaque);auto&q=a.q;
 if(!Unexpired(q)||!ReadCurrent(q,a.stamp)||!ck3_1210::DateSentinelAllowsResumeV1(*q.sentinel,q.request.expected_core))return false;
 const auto current=BindCurrentCommandImageV1(q.bindings.module_base,{kGameVersion,kSteamBuildId,kExecutableSha256});
 if(!current.current_image_verified||current.offline_fixture||!CurrentCommandTargetsMatchV1(current)||
  current.commands.command_manager!=a.commands.commands.command_manager||
  current.commands.queue_owned_command!=a.commands.commands.queue_owned_command||
  current.commands.pause_primary_vtable!=a.commands.commands.pause_primary_vtable||
  current.commands.pause_secondary_vtable!=a.commands.commands.pause_secondary_vtable||!Unexpired(q))return false;
 q.result.resume_attempted=true;q.result.status=Status::indeterminate;return true;
#else
 (void)opaque;return false;
#endif
}
bool Execute(DateAdvanceContext267V1&q,[[maybe_unused]]const ck3_11906::MainThreadExecutionStampV1&s) noexcept {
 q.result={};q.command_ownership_entered=false;
#if defined(XAR_CK3_ENABLE_121003_26785313_DATE_ADVANCE_V1) && XAR_CK3_ENABLE_121003_26785313_DATE_ADVANCE_V1
 if(!q.mailbox||q.mailbox->offline_fixture||!q.session||!q.sentinel||!q.connection_generation||
  !DateAdvanceRequestShape267V1(q.request)||q.request.status_query||
  !DateAdvanceRuntimeMatches267V1(*q.session,*q.sentinel)||
  q.sentinel->bindings.runtime_profile!=ck3_1210::DateSentinelRuntimeProfileV1::current26785313)return true;
 if(!Unexpired(q)){q.result.status=Status::expired;return true;}
 if(!ReadCurrent(q,s))return true;
 // Revalidate the fixed current source before claiming any mutation.
 const auto commands=BindCurrentCommandImageV1(q.bindings.module_base,{kGameVersion,kSteamBuildId,kExecutableSha256});
 if(!commands.current_image_verified||commands.offline_fixture||!CurrentCommandTargetsMatchV1(commands)||!Unexpired(q))return true;
 #if defined(XAR_CK3_ENABLE_121003_26785313_FULLSCREEN_EVENT_V1) && XAR_CK3_ENABLE_121003_26785313_FULLSCREEN_EVENT_V1
  const auto event_gate=ReadRuntimeEventTimeGate267V1(q.bindings,q.request.expected_core);
  if(!DateTimeGateAllowsArm267V1(event_gate,q.result)){if(q.result.access_cleanup_unknown)BlockDateAdvanceUnknown267V1(*q.session);return true;}
  if(!Unexpired(q)||!ReadCurrent(q,s))return true;
#endif
  if(!ClaimDateAdvance267V1(*q.session,q.request,{q.bindings.module_base,s.game_state,s.jomini_state},q.result))return true;
 q.result.arm_attempted=true;q.result.status=Status::indeterminate;
 ck3_11906::TacticalDailySentinelArmRequestV1 arm{};
 arm.mode=ck3_11906::TacticalDailySentinelModeV1::terminal_or_sentinel;
 arm.starting_date_raw=q.request.expected_core.clock.date_raw;arm.target_date_raw=arm.starting_date_raw+24;
 arm.speed=q.request.expected_core.clock.speed; // zero armies; not a fabricated Full wars/army census.
 if(ck3_1210::ArmDateSentinelV1(*q.sentinel,arm,q.request.deadline_unix_ms)!=ck3_11906::TacticalDailySentinelArmStatusV1::armed){
  ck3_1210::RequestDateSentinelShutdownV1(*q.sentinel);
  BlockDateAdvanceUnknown267V1(*q.session);StoreDateAdvance267V1(*q.session,q.result);return true;
 }
 const auto armed=ck3_1210::ReadDateSentinelStatusV1(*q.sentinel);
 q.result.generation=armed.generation;q.result.sentinel=armed;
 if(!armed.generation||armed.state!=ck3_11906::TacticalDailySentinelStateV1::armed||
  armed.starting_date_raw!=arm.starting_date_raw||armed.target_date_raw!=arm.target_date_raw||
  !Unexpired(q)||!ck3_1210::DateSentinelAllowsResumeV1(*q.sentinel,q.request.expected_core)){
  ck3_1210::RequestDateSentinelShutdownV1(*q.sentinel);
  BlockDateAdvanceUnknown267V1(*q.session);StoreDateAdvance267V1(*q.session,q.result);return true;
 }
 const auto command=ck3_1210::MakePauseCommand(commands.commands,q.request.expected_core.local_player_id,false);
 Admission admission{q,s,commands};q.command_ownership_entered=true;
 const auto result=ck3_1210::SubmitCommandCopy(commands.commands,&command,7,&BeforeResume,&admission);
 q.command_ownership_entered=false;
 q.result.resume_submitted=q.result.resume_attempted&&result==ck3_1210::CommandSubmitResult::submitted;
 q.result.status=q.result.resume_submitted?Status::submitted:
  result==ck3_1210::CommandSubmitResult::rejected?Status::rejected:Status::indeterminate;
 if(!q.result.resume_submitted){
  // This original ARM remains consumed, even if a known queue refusal can be
  // safely canceled on this owner. UNKNOWN is never reset or retried.
  (void)ck3_1210::CancelDateSentinelV1(*q.sentinel,q.result.generation);
  ck3_1210::RequestDateSentinelShutdownV1(*q.sentinel);
  BlockDateAdvanceUnknown267V1(*q.session);
 }
 StoreDateAdvance267V1(*q.session,q.result);
#endif
 return true;
}
} // namespace
bool DateAdvanceRequestShape267V1(const DateAdvanceRequest267V1&r) noexcept {
 const auto&p=r.expected_core;return Id(r.request_id,r.request_id_size)&&Id(r.operation_id,r.operation_id_size)&&
  r.deadline_unix_ms&&p.clock.date_raw>0&&p.clock.date_raw<=(std::numeric_limits<std::int32_t>::max)()-24&&
  p.clock.speed>=1&&p.clock.speed<=5&&p.clock.paused&&p.local_player_id>=0&&p.map_ready&&
  p.has_played_character&&p.played_character_id!=-1&&p.played_character_alive;
}
bool BindDateAdvanceSession267V1(DateAdvanceSession267V1&s,ck3_1210::DateSentinelStateV1&runtime) noexcept {
#if defined(XAR_TED_CUSTODY_EXPLICIT_NOGAME_MODEL)
 if(runtime.initialized.load()&&runtime.fixture_only&&runtime.bindings.offline_fixture&&runtime.bindings.module_base==0){
  Lock lock(s.lock_);if(s.runtime_||s.size_)return false;Lock shared(g_date_family.lock);if(g_date_family.runtime)return false;
  g_date_family.old_session=&s;g_date_family.runtime=&runtime;s.runtime_=&runtime;return true;
 }
#endif
#if defined(XAR_CK3_ENABLE_121003_26785313_DATE_ADVANCE_V1) && XAR_CK3_ENABLE_121003_26785313_DATE_ADVANCE_V1
 if(!runtime.initialized.load(std::memory_order_acquire)||runtime.fixture_only||runtime.bindings.offline_fixture||
  runtime.bindings.runtime_profile!=ck3_1210::DateSentinelRuntimeProfileV1::current26785313||
  !runtime.bindings.current_access_context||runtime.bindings.game_access_context!=runtime.bindings.current_access_context)return false;
 const auto bound=ck3_1210::BindCurrentDateRuntime267V1(runtime,
  *static_cast<DateWorkerAccessContext267V1*>(runtime.bindings.game_access_context));
 const auto &old=runtime.bindings;
 if(!bound.exact_build_admitted||!old.exact_build_admitted||old.module_base!=bound.module_base||old.core.image_build!=bound.core.image_build||
  old.core.enabled!=bound.core.enabled||old.core.game_state_slot!=bound.core.game_state_slot||old.core.jomini_state_slot!=bound.core.jomini_state_slot||
  old.core.character_storage_slot!=bound.core.character_storage_slot||old.core.get_local_player!=bound.core.get_local_player||
  old.set_paused!=bound.set_paused||old.command_manager!=bound.command_manager||old.worker_function!=bound.worker_function||
  old.worker_game_access||old.worker_game_access_v2!=bound.worker_game_access_v2||old.utc_now||old.monotonic_now||old.clock_context||
  old.worker_fixture.context||old.worker_fixture.snapshot||old.worker_fixture.duplicate||old.worker_fixture.probe||
  old.worker_fixture.scope||old.worker_fixture.close||old.worker_fixture.with_game_access||old.worker_fixture.with_game_access_v2)return false;
 Lock lock(s.lock_);if(s.runtime_||s.size_)return false;
 {Lock shared(g_date_family.lock);if(g_date_family.runtime)return false;g_date_family.old_session=&s;g_date_family.runtime=&runtime;}
 s.runtime_=&runtime;return true;
#else
 (void)s;(void)runtime;return false;
#endif
}
bool DateAdvanceRuntimeMatches267V1(DateAdvanceSession267V1&s,const ck3_1210::DateSentinelStateV1&r) noexcept {
 Lock lock(s.lock_);return s.runtime_==&r;
}
bool ClaimDateAdvance267V1(DateAdvanceSession267V1&s,const DateAdvanceRequest267V1&r,
 const DateAdvanceSource267V1&source,DateAdvanceResult267V1&result) noexcept {
 Lock lock(s.lock_);
 if(!s.runtime_||!DateAdvanceRequestShape267V1(r)||r.status_query||!source.module_base||!source.game_state||!source.jomini_state)return false;
 for(std::size_t i=0;i<s.size_;++i)if(s.claims_[i].request.operation()==r.operation()){
  result.status=Status::claim_consumed;return false;
 }
 if(s.unknown_){result.status=Status::claim_consumed;return false;}
 if(s.size_){const auto&first=s.claims_[0];const auto&last=s.claims_[s.size_-1];
  if(first.source.module_base!=source.module_base||first.source.game_state!=source.game_state||first.source.jomini_state!=source.jomini_state||
   first.request.expected_core.local_player_id!=r.expected_core.local_player_id||
   first.request.expected_core.played_character_id!=r.expected_core.played_character_id){result.status=Status::source_changed;return false;}
  if(!last.result.exact_day_confirmed||last.result.status!=Status::completed||
   r.expected_core.clock.date_raw<=last.request.expected_core.clock.date_raw){result.status=Status::claim_consumed;return false;}
 }
 if(s.size_==s.claims_.size()){result.status=Status::capacity_exhausted;return false;}
 if(!OldMayClaimCustody(s)){result.status=Status::claim_consumed;return false;}
 auto&entry=s.claims_[s.size_++];entry.request=r;entry.source=source;
 result.claim_found=true;result.claim_sequence=s.size_;entry.result=result;PublishOldCustody(s,true,false);return true;
}
void StoreDateAdvance267V1(DateAdvanceSession267V1&s,const DateAdvanceResult267V1&r) noexcept {
 Lock lock(s.lock_);if(!r.claim_sequence||r.claim_sequence!=s.size_){s.unknown_=true;PublishOldCustody(s,true,true);return;}
 // Completion is not a caller-settable bookkeeping boolean. Only the fixed
 // Query path below can derive it from the actual retained sentinel runtime.
 if(r.exact_day_confirmed||r.status==Status::completed||r.status==Status::running||
  (r.status!=Status::submitted&&r.status!=Status::rejected&&r.status!=Status::indeterminate)){
  s.unknown_=true;PublishOldCustody(s,true,true);return;
 }
 s.claims_[s.size_-1].result=r;
 if(r.status==Status::rejected||r.status==Status::indeterminate)s.unknown_=true;
 PublishOldCustody(s,true,s.unknown_);
}
void BlockDateAdvanceUnknown267V1(DateAdvanceSession267V1&s) noexcept {Lock lock(s.lock_);s.unknown_=true;PublishOldCustody(s,true,true);}
DateAdvanceResult267V1 QueryDateAdvance267V1(DateAdvanceSession267V1&s,const DateAdvanceRequest267V1&r,
 const ck3_1210::DateSentinelStateV1&sentinel) noexcept {
 DateAdvanceResult267V1 empty{};if(!r.status_query||!DateAdvanceRequestShape267V1(r))return empty;
 Lock lock(s.lock_);
 if(s.runtime_!=&sentinel)return empty;
 for(std::size_t i=0;i<s.size_;++i){auto&entry=s.claims_[i];if(entry.request.operation()!=r.operation())continue;
  if(!SameBody(entry.request,r))return empty;
  auto result=entry.result;
  if(i+1==s.size_&&result.resume_submitted&&result.generation&&result.status!=Status::completed){
   const auto status=ck3_1210::ReadDateSentinelStatusV1(sentinel);
   // ReadDateSentinelStatusV1 waits for post rundown. These public atomic
   // publications add no OS/world read or owner-only diagnostics invocation.
   result.sentinel=status;result.shutdown_safe=sentinel.shutdown_safe.load(std::memory_order_seq_cst);
   result.armed=sentinel.armed.load(std::memory_order_acquire);
   result.access_cleanup_unknown=sentinel.access_cleanup_unknown.load(std::memory_order_seq_cst);
   result.failure_flags=sentinel.pending_failure.load(std::memory_order_acquire);
   const auto start=entry.request.expected_core.clock.date_raw;
   result.exact_day_confirmed=!s.unknown_&&status.generation==result.generation&&status.state==ck3_11906::TacticalDailySentinelStateV1::triggered&&
    status.mode==ck3_11906::TacticalDailySentinelModeV1::terminal_or_sentinel&&status.army_count==0&&status.combat_count==0&&
    status.starting_date_raw==start&&status.target_date_raw==start+24&&status.last_observed_date_raw==start+24&&
    status.trigger_date_raw==start+24&&status.speed==entry.request.expected_core.clock.speed&&status.completed_daily_ticks==1&&
    status.signed_date_delta_from_target_raw==0&&status.overshoot_days==0&&status.pause_observed&&status.pause_wrapper_called&&
    status.trigger_flags==ck3_11906::tactical_daily_trigger_date_deadline&&!status.terminal_observed&&
    !status.abnormal&&result.shutdown_safe&&!result.armed&&!result.access_cleanup_unknown&&!result.failure_flags;
   if(result.exact_day_confirmed)result.status=Status::completed;
   else if(!s.unknown_&&status.generation==result.generation&&status.state==ck3_11906::TacticalDailySentinelStateV1::armed&&
    !result.failure_flags&&!result.access_cleanup_unknown)result.status=Status::running;
   else {result.status=Status::indeterminate;s.unknown_=true;}
   entry.result=result;PublishOldCustody(s,result.status!=Status::completed,s.unknown_);
  }
  return result;
 }
 return empty;
}
bool TedDatePredecessorResolved267V1(const ck3_1210::DateSentinelStateV1&runtime)noexcept {
 Lock lock(g_date_family.lock);
#if defined(XAR_CK3_ENABLE_121003_26785313_TED_TRANSITION_V1) && XAR_CK3_ENABLE_121003_26785313_TED_TRANSITION_V1
 return g_date_family.runtime==&runtime&&g_date_family.old_session&&!g_date_family.old_open&&!g_date_family.unknown&&!g_date_family.ccc_active;
#else
 (void)runtime;return false;
#endif
}
bool ClaimTedDateCustody267V1(const ck3_1210::DateSentinelStateV1&runtime,bool continuation)noexcept {
 Lock lock(g_date_family.lock);
#if defined(XAR_CK3_ENABLE_121003_26785313_TED_TRANSITION_V1) && XAR_CK3_ENABLE_121003_26785313_TED_TRANSITION_V1
 if(g_date_family.runtime!=&runtime||!g_date_family.old_session||g_date_family.old_open||g_date_family.unknown||g_date_family.ccc_active||g_date_family.ted_active!=continuation)return false;
 g_date_family.ted_active=true;return true;
#else
 (void)runtime;(void)continuation;return false;
#endif
}
void CompleteTedDateCustody267V1(const ck3_1210::DateSentinelStateV1&runtime)noexcept {Lock lock(g_date_family.lock);if(g_date_family.runtime==&runtime&&!g_date_family.unknown)g_date_family.ted_active=false;}
void BlockTedDateCustodyUnknown267V1(const ck3_1210::DateSentinelStateV1&runtime)noexcept {Lock lock(g_date_family.lock);if(g_date_family.runtime==&runtime){g_date_family.unknown=true;g_date_family.ted_active=true;}}
bool CccDatePredecessorResolved267V1(const ck3_1210::DateSentinelStateV1&r)noexcept{
 Lock lock(g_date_family.lock);return g_date_family.runtime==&r&&g_date_family.old_session&&!g_date_family.old_open&&!g_date_family.ted_active&&!g_date_family.unknown;
}
bool ClaimCccDateCustody267V1(const ck3_1210::DateSentinelStateV1&r,bool continuation)noexcept{
#if defined(XAR_CK3_ENABLE_121003_26785313_CCC_TRANSITION_V1) && XAR_CK3_ENABLE_121003_26785313_CCC_TRANSITION_V1
 Lock lock(g_date_family.lock);if(g_date_family.runtime!=&r||!g_date_family.old_session||g_date_family.old_open||g_date_family.ted_active||g_date_family.unknown||g_date_family.ccc_active!=continuation)return false;g_date_family.ccc_active=true;return true;
#else
 (void)r;(void)continuation;return false;
#endif
}
void CompleteCccDateCustody267V1(const ck3_1210::DateSentinelStateV1&r)noexcept{Lock lock(g_date_family.lock);if(g_date_family.runtime==&r&&!g_date_family.unknown)g_date_family.ccc_active=false;}
void BlockCccDateCustodyUnknown267V1(const ck3_1210::DateSentinelStateV1&r)noexcept{Lock lock(g_date_family.lock);if(g_date_family.runtime==&r){g_date_family.unknown=true;g_date_family.ccc_active=true;}}
void ArmDateAdvanceDeadline267V1(DateAdvanceContext267V1&q) noexcept {
 q.monotonic_deadline_ms=0;const auto now=Wall(),mono=GetTickCount64();if(!now||q.request.deadline_unix_ms<=now)return;
 const auto delta=(std::min)(q.request.deadline_unix_ms-now,std::uint64_t{8000});
 if(mono>(std::numeric_limits<std::uint64_t>::max)()-delta)return;q.monotonic_deadline_ms=mono+delta;
}
bool ExecuteDateAdvanceOnOwner267V1(void*opaque,const ck3_11906::MainThreadExecutionStampV1&s) noexcept {
 if(!opaque)return false;auto&q=*static_cast<DateAdvanceContext267V1*>(opaque);
 __try{return Execute(q,s);}__except(EXCEPTION_EXECUTE_HANDLER){
  if(q.session&&(q.result.arm_attempted||q.command_ownership_entered)){
   if(q.sentinel)ck3_1210::RequestDateSentinelShutdownV1(*q.sentinel);
   BlockDateAdvanceUnknown267V1(*q.session);q.result.status=Status::indeterminate;
   if(q.result.claim_sequence)StoreDateAdvance267V1(*q.session,q.result);
  }else q.result.status=Status::unavailable;return true;
 }
}
bool DateAdvanceRouteEnabled267V1([[maybe_unused]]const game::AdapterDescriptor&d) noexcept {
#if defined(XAR_CK3_ENABLE_121003_26785313_DATE_ADVANCE_V1) && XAR_CK3_ENABLE_121003_26785313_DATE_ADVANCE_V1
 return game::IsCk3_121003Core26785313Descriptor(d)&&
  std::find(d.capabilities.begin(),d.capabilities.end(),ck3_1210::kCoreFrameCapabilityV1)!=d.capabilities.end()&&
  std::find(d.capabilities.begin(),d.capabilities.end(),kDateAdvanceCapability267V1)!=d.capabilities.end();
#else
 return false;
#endif
}
} // namespace
