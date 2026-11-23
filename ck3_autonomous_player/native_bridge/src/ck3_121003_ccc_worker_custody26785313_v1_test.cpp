// SOURCE ONLY. Native owner compiles this external leaf against its actual
// candidate headers/sources. No process inspection, image binding or live ABI.
// Build twice: default = actual sentinel worker Fixture; XAR_CCC_CUSTODY_TEST=1
// = actual DateAdvance coordinator with explicit NoGame status DATA only.
// The closed CCC owner official epoch/13-day cap is NOT emulated by this leaf.

#if defined(XAR_CCC_CUSTODY_TEST) && XAR_CCC_CUSTODY_TEST
// Existing explicit NoGame bind seam, never defined for a production target.
#ifndef XAR_TED_CUSTODY_EXPLICIT_NOGAME_MODEL
#define XAR_TED_CUSTODY_EXPLICIT_NOGAME_MODEL 1
#endif
#if defined(XAR_CK3_ENABLE_121003_26785313_DATE_ADVANCE_V1) && XAR_CK3_ENABLE_121003_26785313_DATE_ADVANCE_V1
#error This custody-only DATA test compiles DATE_ADVANCE_V1=0, as the canonical custody test does
#endif
#ifndef XAR_CCC_DATE_ADVANCE_SOURCE
#define XAR_CCC_DATE_ADVANCE_SOURCE "ck3_121003_date_advance26785313_v1.cpp"
#endif
#include XAR_CCC_DATE_ADVANCE_SOURCE
#include <iostream>
#include <stdexcept>
#include <string_view>

namespace ccc_custody_model {
xar::ck3_11906::TacticalDailySentinelStatusV1 status{};
void Require(bool yes,const char*why){if(!yes)throw std::runtime_error(why);}
}
namespace xar::ck3_1210 {
ck3_11906::TacticalDailySentinelStatusV1 ReadDateSentinelStatusV1(const DateSentinelStateV1&)noexcept {
 return ccc_custody_model::status;
}
void RequestDateSentinelShutdownV1(DateSentinelStateV1&r)noexcept {r.shutdown_requested=true;}
}
int Custody(const bool zero){
 using namespace xar::ck3_121003::build26785313;
 using namespace ccc_custody_model;
 namespace old=xar::ck3_11906;
 xar::ck3_1210::DateSentinelStateV1 runtime,foreign_runtime;
 runtime.initialized=true;runtime.fixture_only=true;runtime.bindings.offline_fixture=true;
 foreign_runtime.initialized=true;foreign_runtime.fixture_only=true;foreign_runtime.bindings.offline_fixture=true;
 DateAdvanceSession267V1 retained;
 Require(!CccDatePredecessorResolved267V1(runtime)&&!ClaimCccDateCustody267V1(runtime,false),"unbound CCC runtime refused");
 Require(BindDateAdvanceSession267V1(retained,runtime),"bind actual retained old session");
 Require(CccDatePredecessorResolved267V1(runtime)&&TedDatePredecessorResolved267V1(runtime),"both finite families see same resolved old frontier");
 Require(!CccDatePredecessorResolved267V1(foreign_runtime)&&!ClaimCccDateCustody267V1(foreign_runtime,false),"foreign runtime cannot borrow custody");
 DateAdvanceRequest267V1 q;const std::string id="ccc-custody-old-request",op="ccc-old-day-one";
 std::copy(id.begin(),id.end(),q.request_id.begin());q.request_id_size=static_cast<std::uint8_t>(id.size());
 std::copy(op.begin(),op.end(),q.operation_id.begin());q.operation_id_size=static_cast<std::uint8_t>(op.size());
 q.deadline_unix_ms=1899999999999ULL;const auto original_deadline=q.deadline_unix_ms;
 auto&core=q.expected_core;core.clock.date_raw=53144328;core.clock.speed=1;core.clock.paused=true;
 core.local_player_id=0;core.map_ready=core.has_played_character=core.played_character_alive=true;
 core.played_character_id=zero?0:-2;const auto original_actor=core.played_character_id;
 DateAdvanceSource267V1 source{0x1000,0x2000,0x3000};DateAdvanceResult267V1 first;
 Require(ClaimDateAdvance267V1(retained,q,source,first)&&first.claim_sequence==1,"old exact signed32 actor 0 or -2 claim retained");
 Require(!CccDatePredecessorResolved267V1(runtime)&&!ClaimCccDateCustody267V1(runtime,false)&&!ClaimTedDateCustody267V1(runtime,false),"unresolved old date excludes both families");
 first.status=DateAdvanceStatus267V1::submitted;first.resume_submitted=true;first.generation=42;StoreDateAdvance267V1(retained,first);
 const auto complete=[&](const std::uint64_t generation){
  status={};status.generation=generation;status.state=old::TacticalDailySentinelStateV1::triggered;
  status.mode=old::TacticalDailySentinelModeV1::terminal_or_sentinel;status.starting_date_raw=q.expected_core.clock.date_raw;
  status.target_date_raw=status.last_observed_date_raw=status.trigger_date_raw=q.expected_core.clock.date_raw+24;
  status.speed=q.expected_core.clock.speed;status.completed_daily_ticks=1;status.overshoot_days=0;
  status.pause_observed=status.pause_wrapper_called=true;status.trigger_flags=old::tactical_daily_trigger_date_deadline;
  runtime.shutdown_safe=true;runtime.armed=false;q.status_query=true;
  return QueryDateAdvance267V1(retained,q,runtime);
 };
 auto exact=complete(42);
 Require(exact.status==DateAdvanceStatus267V1::completed&&exact.exact_day_confirmed&&CccDatePredecessorResolved267V1(runtime),"actual old Query path alone resolves explicit status DATA");
 auto changed_deadline=q;++changed_deadline.deadline_unix_ms;
 const auto no_body=QueryDateAdvance267V1(retained,changed_deadline,runtime);
 Require(!no_body.claim_found&&!no_body.exact_day_confirmed&&q.deadline_unix_ms==original_deadline,"different deadline cannot replace original old claim");
 Require(ClaimCccDateCustody267V1(runtime,false),"CCC initially claims resolved custody");
 Require(!ClaimCccDateCustody267V1(runtime,false)&&ClaimCccDateCustody267V1(runtime,true),"CCC continuation remains separate from duplicate initial claim");
 Require(!TedDatePredecessorResolved267V1(runtime)&&!ClaimTedDateCustody267V1(runtime,false)&&!ClaimTedDateCustody267V1(runtime,true),"TED initial and continuation cannot borrow active CCC");
 CompleteTedDateCustody267V1(runtime);
 Require(!ClaimTedDateCustody267V1(runtime,false)&&ClaimCccDateCustody267V1(runtime,true),"TED completion cannot release CCC active flag");
 q.status_query=false;q.operation_id={};const std::string op2="ccc-old-day-two";
 std::copy(op2.begin(),op2.end(),q.operation_id.begin());q.operation_id_size=static_cast<std::uint8_t>(op2.size());
 q.expected_core.clock.date_raw+=24;DateAdvanceResult267V1 blocked;
 Require(!ClaimDateAdvance267V1(retained,q,source,blocked)&&blocked.status==DateAdvanceStatus267V1::claim_consumed,"CCC active blocks old claim before consuming ID");
 CompleteCccDateCustody267V1(runtime);
 q.expected_core.played_character_id=zero?-2:0;DateAdvanceResult267V1 wrong_actor;
 Require(!ClaimDateAdvance267V1(retained,q,source,wrong_actor)&&wrong_actor.status==DateAdvanceStatus267V1::source_changed,"CCC closure never clears old firstActor, including zero/fullsigned -2");
 q.expected_core.played_character_id=original_actor;DateAdvanceResult267V1 second;
 Require(ClaimDateAdvance267V1(retained,q,source,second)&&second.claim_sequence==2,"same original old actor retains old claim sequence");
 second.status=DateAdvanceStatus267V1::submitted;second.resume_submitted=true;second.generation=43;StoreDateAdvance267V1(retained,second);
 exact=complete(43);Require(exact.exact_day_confirmed,"second old claim resolves by actual Query only");
 Require(ClaimTedDateCustody267V1(runtime,false),"TED custody still works after closed CCC");
 Require(!CccDatePredecessorResolved267V1(runtime)&&!ClaimCccDateCustody267V1(runtime,false)&&!ClaimCccDateCustody267V1(runtime,true),"CCC cannot borrow TED active custody");
 CompleteCccDateCustody267V1(runtime);
 Require(!ClaimCccDateCustody267V1(runtime,false)&&ClaimTedDateCustody267V1(runtime,true),"CCC completion cannot release TED active flag");
 CompleteTedDateCustody267V1(runtime);Require(ClaimCccDateCustody267V1(runtime,false),"CCC newly claims only after TED completes");
 BlockCccDateCustodyUnknown267V1(runtime);CompleteCccDateCustody267V1(runtime);CompleteTedDateCustody267V1(runtime);
 Require(!CccDatePredecessorResolved267V1(runtime)&&!TedDatePredecessorResolved267V1(runtime)&&
  !ClaimCccDateCustody267V1(runtime,false)&&!ClaimCccDateCustody267V1(runtime,true)&&!ClaimTedDateCustody267V1(runtime,false),"UNKNOWN retained across either family completion or continuation");
 q.status_query=false;q.expected_core.clock.date_raw+=24;q.operation_id={};const std::string op3="ccc-old-day-three";
 std::copy(op3.begin(),op3.end(),q.operation_id.begin());q.operation_id_size=static_cast<std::uint8_t>(op3.size());DateAdvanceResult267V1 unknown;
 Require(!ClaimDateAdvance267V1(retained,q,source,unknown)&&q.expected_core.played_character_id==original_actor&&q.deadline_unix_ms==original_deadline,"new operation ID cannot bypass UNKNOWN; firstActor/deadline unchanged");
 std::cout<<"PASS CCC/TED actual custody, original old claims/firstActor/deadline/UNKNOWN; status is explicit NoGame DATA; actor="<<original_actor<<'\n';return 0;
}
int main(int argc,char**argv){try{
 if(argc>2||(argc==2&&std::string_view(argv[1])!="--zero"))throw std::runtime_error("usage: custody-test [--zero]");
 return Custody(argc==2);
}catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<'\n';return 1;}}

#else
#ifndef XAR_CCC_TED_WORKER_FIXTURE_SOURCE
#define XAR_CCC_TED_WORKER_FIXTURE_SOURCE "ck3_121003_ted_date_proof26785313_v1_test.cpp"
#endif
// Reuse the unchanged actual worker/owner/evaluator fixture, not a copied proof.
#define main CccUnusedCanonicalTedFixtureMain
#include XAR_CCC_TED_WORKER_FIXTURE_SOURCE
#undef main
#include "xar_bridge/ck3_121003_ccc_date_proof26785313_v1.hpp"

int main(){
 Fixture f;Check(InitializeDateSentinelV1(f.sentinel,f.bindings,f.mailbox),"real NoGame sentinel Fixture initializes");
#if !defined(XAR_CK3_ENABLE_121003_26785313_CCC_TRANSITION_V1) || !XAR_CK3_ENABLE_121003_26785313_CCC_TRANSITION_V1
 Check(ArmCccFixedDay267V1(f.sentinel,f.Request(),f.wall+5000,CccFixedDayStage267V1::song_transition)==Arm::unavailable,"CCC defaultOFF arm unavailable");
 f.Start();f.Date(24024);f.Post();CccFixedDayProof267V1 p;old::TacticalDailySentinelStatusV1 status;
 Check(!ReadCccFixedDayProof267V1(f.sentinel,f.sentinel.generation.load(),p,status)&&!p.captured,"ordinary Date completion does not mint CCC proof");
 DateSentinelObservationV1 out{};out.actor=f.actor.data();
 Check(!ReadCccDeferredActorOnOwner267V1(f.sentinel,p,f.Stamp(),out)&&!out.actor,"CCC defaultOFF owner returns empty DATA without effects");
 std::cout<<"PASS CCC worker defaultOFF and old strict Date; no Game\n";return 0;
#else
#if !defined(XAR_CK3_ENABLE_121003_26785313_TED_TRANSITION_V1) || !XAR_CK3_ENABLE_121003_26785313_TED_TRANSITION_V1
#error CCC worker cross-family test requires both TED_TRANSITION_V1=1 and CCC_TRANSITION_V1=1
#endif
 constexpr auto recipient=std::bit_cast<std::int32_t>(std::uint32_t{0x82000001});
 std::array<std::byte,0x1E0> next{};Put(next,0x18,recipient);Put(next,0x1C,std::uint32_t{0x43686172});
 const auto change=[&]{Put(f.rows,0x18,static_cast<void*>(next.data()));Put(f.entry,0xB0,recipient);};
 const auto arm=[&](CccFixedDayStage267V1 stage){
  Check(ArmCccFixedDay267V1(f.sentinel,f.Request(),f.wall+5000,stage)==Arm::armed,"CCC actual worker arms exact +24");
  Check(DateSentinelAllowsResumeV1(f.sentinel,f.Core()),"only original paused actor/world may resume");
 };
 const auto proof=[&]{CccFixedDayProof267V1 p;old::TacticalDailySentinelStatusV1 status;
  const bool found=ReadCccFixedDayProof267V1(f.sentinel,f.sentinel.generation.load(),p,status);return std::pair{found,p};};
 const auto clear=[](const DateSentinelObservationV1&o){return !o.game&&!o.jomini&&!o.storage&&!o.data&&!o.players&&!o.player&&!o.actor;};
 // Opt-in is never borrowed from ordinary Date or the other fixed family.
 f.Start();f.Date(24024);f.Post();Check(!proof().first,"old strict Date does not mint CCC proof");
 f.Reset();Check(ArmTedFixedDay267V1(f.sentinel,f.Request(),f.wall+5000,TedFixedDayStage267V1::song_transition)==Arm::armed,"TED still independently arms");
 f.Date(24024);f.Post();Check(!proof().first,"CCC cannot read TED proof");
 TedFixedDayProof267V1 ted;old::TacticalDailySentinelStatusV1 status;
 Check(ReadTedFixedDayProof267V1(f.sentinel,f.sentinel.generation.load(),ted,status)&&ted.family==FixedDayFamily267V1::ted,"TED keeps actual TED proof tag");
 DateSentinelObservationV1 out{};out.actor=f.actor.data();
 Check(!ReadCccDeferredActorOnOwner267V1(f.sentinel,ted,f.Stamp(),out)&&clear(out),"CCC owner cannot borrow TED proof");
 f.Reset();arm(CccFixedDayStage267V1::song_transition);const auto first_deadline=f.sentinel.original_deadline_unix_ms;
 f.Date(24024);change();f.Post();auto p=proof();
 Check(p.first&&p.second.family==FixedDayFamily267V1::ccc&&p.second.actor_changed&&
  p.second.before.core.played_character_id==kActor&&p.second.after.core.played_character_id==recipient&&
  p.second.status.completed_daily_ticks==1&&p.second.after.core.clock.date_raw==24024&&p.second.after.core.clock.paused&&
  p.second.original_deadline_unix_ms==first_deadline&&p.second.worker.creation_time==f.worker_birth&&f.access_enters==f.access_leaves,
  "CCC actual worker captures exact24 actual actor change, original deadline and cleanup");
 Check(!ReadTedFixedDayProof267V1(f.sentinel,p.second.generation,ted,status)&&!ted.captured,"TED cannot read CCC proof");
 auto forged=p.second;forged.family=FixedDayFamily267V1::ted;out.actor=f.actor.data();
 Check(!ReadTedDeferredActorOnOwner267V1(f.sentinel,forged,f.Stamp(),out)&&clear(out),"retagging CCC DATA cannot borrow actual TED generation");
 f.Reset();arm(CccFixedDayStage267V1::recipient_stable);f.Date(24024);f.Post();p=proof();
 Check(p.first&&!p.second.actor_changed&&p.second.family==FixedDayFamily267V1::ccc,"official-stable stage worker proof retains CCC family");
 f.Reset();arm(CccFixedDayStage267V1::recipient_stable);f.Date(24024);change();f.Post();
 Check(!proof().first,"official-stable stage cannot permit second actor switch");Failed(f,date_sentinel_failure_actor);
 f.Reset();Check(ArmCccFixedDay267V1(f.sentinel,f.Request(2),f.wall+5000,CccFixedDayStage267V1::song_transition)==Arm::invalid_request,"one CCC fixed worker arm cannot request two days");
 Check(ArmCccFixedDay267V1(f.sentinel,f.Request(),f.wall+5000,static_cast<CccFixedDayStage267V1>(2))==Arm::invalid_request,"undefined worker stage refused");
 // Zero is a real packed reference with actual fixture row[0], not absence.
 f.Reset();Put(f.rows,8,static_cast<void*>(f.actor.data()));Put(f.actor,0x18,std::int32_t{0});Put(f.entry,0xB0,std::int32_t{0});
 arm(CccFixedDayStage267V1::song_transition);f.Date(24024);f.Post();p=proof();
 Check(p.first&&p.second.before.core.played_character_id==0&&p.second.after.core.played_character_id==0&&p.second.before.actor==f.actor.data(),"actual Core/worker resolves packed ID zero without positivity guard");
 // Independent later owner observations do not rewrite immutable worker proof.
 f.Reset();arm(CccFixedDayStage267V1::song_transition);f.Date(24024);f.Post();p=proof();
 Check(p.first&&!p.second.actor_changed,"deferred CCC starts with actual same-actor worker proof");const auto frozen=p.second;
 const auto pauses=f.pauses,enters=f.access_enters,leaves=f.access_leaves;
 const auto unchanged=[&]{Check(f.pauses==pauses&&f.access_enters==enters&&f.access_leaves==leaves&&
  f.sentinel.original_deadline_unix_ms==frozen.original_deadline_unix_ms&&f.sentinel.monotonic_deadline_ms==frozen.monotonic_deadline_ms&&
  f.sentinel.generation.load()==frozen.generation,"readonly owner does not pause/ARM/extend deadline/replace generation");};
 Check(ReadCccDeferredActorOnOwner267V1(f.sentinel,frozen,f.Stamp(),out)&&out.core.played_character_id==kActor,"owner sample before deferred switch");unchanged();
 change();Check(ReadCccDeferredActorOnOwner267V1(f.sentinel,frozen,f.Stamp(),out)&&out.actor==next.data()&&out.core.played_character_id==recipient,"owner first actual deferred recipient sample");unchanged();
 DateSentinelObservationV1 second{};Check(ReadCccDeferredActorOnOwner267V1(f.sentinel,frozen,f.Stamp(),second)&&second.actor==out.actor&&second.core.played_character_id==out.core.played_character_id&&second.core.clock.date_raw==24024&&second.core.clock.paused,"owner second independent stable deferred recipient sample");unchanged();
 auto again=proof();Check(again.first&&!again.second.actor_changed&&again.second.after.actor==frozen.after.actor&&again.second.after.core.played_character_id==kActor&&again.second.family==FixedDayFamily267V1::ccc,"owner samples never rewrite original worker after actor/family");
 const auto denied=[&](const CccFixedDayProof267V1&input,const old::MainThreadExecutionStampV1&stamp){
  DateSentinelObservationV1 rejected=frozen.after;Check(!ReadCccDeferredActorOnOwner267V1(f.sentinel,input,stamp,rejected)&&clear(rejected),"invalid owner observation returns no stale source");unchanged();};
 auto altered=frozen;altered.family=FixedDayFamily267V1::ted;denied(altered,f.Stamp());
 altered=frozen;++altered.generation;denied(altered,f.Stamp());
 altered=frozen;++altered.original_deadline_unix_ms;denied(altered,f.Stamp());
 altered=frozen;++altered.monotonic_deadline_ms;denied(altered,f.Stamp());
 altered=frozen;altered.after.actor=next.data();altered.after.core.played_character_id=recipient;denied(altered,f.Stamp());
 altered=frozen;altered.stage=CccFixedDayStage267V1::recipient_stable;denied(altered,f.Stamp());
 auto stamp=f.Stamp();++stamp.tls_context;denied(frozen,stamp);
 stamp=f.Stamp();stamp.thread_id=f.worker_thread_id.load();denied(frozen,stamp);
 const auto wall=f.wall,mono=f.mono;f.wall=frozen.original_deadline_unix_ms;denied(frozen,f.Stamp());f.wall=wall;
 f.mono=frozen.monotonic_deadline_ms;denied(frozen,f.Stamp());f.mono=mono;
 f.Date(24048,true);denied(frozen,f.Stamp());f.Date(24024,true);
 Put(next,0x1D0,static_cast<void*>(next.data()));denied(frozen,f.Stamp());Put(next,0x1D0,static_cast<void*>(nullptr));
 f.sentinel.pending_failure.store(date_sentinel_failure_observation);denied(frozen,f.Stamp());Check(f.sentinel.pending_failure.load()!=0,"owner never clears injected failure");f.sentinel.pending_failure.store(0);
 f.sentinel.access_cleanup_unknown.store(true);denied(frozen,f.Stamp());Check(f.sentinel.access_cleanup_unknown.load(),"owner never clears UNKNOWN cleanup");f.sentinel.access_cleanup_unknown.store(false);
 f.sentinel.shutdown_safe.store(false);denied(frozen,f.Stamp());f.sentinel.shutdown_safe.store(true);
 // Only this private NoGame fixture restores its injected seams for teardown.
 Check(ReadCccDeferredActorOnOwner267V1(f.sentinel,frozen,f.Stamp(),out)&&out.core.played_character_id==recipient,"failed readonly observations did not consume original proof");unchanged();
 for(unsigned bad=0;bad<6;++bad){f.Reset();arm(CccFixedDayStage267V1::song_transition);f.Date(24024);change();
  switch(bad){case 0:f.game_slot=f.other_game.data();break;case 1:Put(f.game,0x70,std::int32_t{3});break;case 2:f.wall=f.sentinel.original_deadline_unix_ms;break;case 3:f.Date(24048);break;case 4:++f.worker_birth;break;case 5:f.expire_on_pause=true;break;}
  f.Post();Check(!proof().first,"world/speed/deadline/overshoot/worker/expiry-during-pause do not mint CCC proof");
  f.game_slot=f.game.data();Put(f.game,0x70,std::int32_t{4});f.ResetWorker();f.expire_on_pause=false;
  if(!DateSentinelShutdownSafeV1(f.sentinel)){Put(f.jomini,0x20,std::uint8_t{1});Check(PollDateSentinelOwnerV1(f.sentinel,f.Stamp()),"same-world fixture failure cleanup");}
 }
 Check(f.native_close_attempts==0,"fixture never closes borrowed native worker handle");
 std::cout<<"PASS CCC actual worker/deferred owner proof and TED isolation; no Game; owner13-day/epoch not claimed\n";return 0;
#endif
}
#endif
