#include "xar_bridge/ck3_1210_date_sentinel_v1.hpp"
#include <array>
#include <bit>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <thread>
#include <vector>
namespace {
using namespace xar::ck3_1210;
namespace old=xar::ck3_11906;
using Phase=old::TacticalDailySentinelStateV1;
using Arm=old::TacticalDailySentinelArmStatusV1;
using Cancel=old::TacticalDailySentinelCancelStatusV1;
constexpr auto kActor=std::bit_cast<std::int32_t>(std::uint32_t{0x81000001});
void Check(bool yes,const char *why) {
  if(!yes){std::cerr<<"FAIL "<<why<<std::endl;std::exit(1);}
}
template<class B,class T> void Put(B &b,std::size_t n,T v) {
  Check(n<=b.size() && sizeof(v)<=b.size()-n,"fixture bounds");std::memcpy(b.data()+n,&v,sizeof(v));
}
struct Fixture;Fixture *active=nullptr;
void *Local(void *);
void *__fastcall Tls() noexcept;
void __fastcall Pause(void *,bool,std::int32_t);
struct Fixture {
  std::array<std::byte,0xB0> game{},other_game{};
  std::array<std::byte,0x28> jomini{};
  std::array<std::byte,0x200> players{};
  std::array<std::byte,0x80> player{};
  std::array<std::byte,0xE0> entry{};
  std::array<std::byte,0x40> storage{},rows{};
  std::array<std::byte,0x1E0> actor{};
  std::array<std::byte,0x30> tls{};
  std::vector<std::byte> data=std::vector<std::byte>(kPlayerCharacterManagerOffset+0x80);
  std::array<void *,1> entries{entry.data()};
  void *game_slot=game.data(),*jomini_slot=jomini.data(),*storage_slot=storage.data();
  std::uint8_t initialized=1;
  unsigned locals=0,tls_calls=0,wall_calls=0,mono_calls=0,pauses=0,mutate_at=0,reject_at=0;
  std::uint64_t wall=1000000,mono=1000;
  bool expire_on_pause=false,pause_fails=false;
  old::MainThreadQueryMailboxV1 mailbox{};
  DateSentinelBindingsV1 bindings{};
  DateSentinelStateV1 sentinel{};
  Fixture() {
    active=this;
    bindings.exact_build_admitted=true;bindings.offline_fixture=true;
    bindings.core={true,&game_slot,&jomini_slot,&storage_slot,&Local};bindings.set_paused=&Pause;
    bindings.clock_context=this;bindings.utc_now=&Wall;bindings.monotonic_now=&Mono;
    mailbox.state.store(old::MainThreadQueryMailboxStateV1::idle);
    mailbox.owner_thread_id.store(GetCurrentThreadId());mailbox.owner_verified_pump_epochs.store(2);
    mailbox.offline_fixture=true;mailbox.tls_initialized_flag=reinterpret_cast<std::uintptr_t>(&initialized);
    mailbox.tls_context_getter=&Tls;
    Reset();
  }
  static std::uint64_t Wall(void *p) noexcept {auto &f=*static_cast<Fixture *>(p);++f.wall_calls;return f.wall;}
  static std::uint64_t Mono(void *p) noexcept {auto &f=*static_cast<Fixture *>(p);++f.mono_calls;return f.mono;}
  void Reset() {
    game_slot=game.data();jomini_slot=jomini.data();storage_slot=storage.data();initialized=1;
    mailbox.owner_thread_id.store(GetCurrentThreadId());mailbox.failure_flags.store(0);mailbox.stop_requested.store(false);
    Put(tls,0x20,std::uint8_t{1});Put(game,8,std::int32_t{24000});Put(game,0x70,std::int32_t{4});
    Put(game,0xA0,data.data());other_game=game;
    Put(jomini,0x18,players.data());Put(jomini,0x20,std::uint8_t{1});
    Put(players,0x1F0,std::int32_t{7});Put(player,0x70,std::int32_t{7});
    Put(entry,0xD8,std::int32_t{7});Put(entry,0xB0,kActor);
    Put(data,kPlayerCharacterManagerOffset+0x58,entries.data());
    Put(data,kPlayerCharacterManagerOffset+0x64,std::int32_t{1});
    Put(storage,0x20,rows.data());Put(storage,0x2C,std::int32_t{4});Put(rows,0x18,actor.data());
    Put(actor,0x18,kActor);Put(actor,0x1C,std::uint32_t{0x43686172});Put(actor,0x1D0,static_cast<void *>(nullptr));
    wall+=10000;mono+=10000;mutate_at=0;reject_at=0;expire_on_pause=false;pause_fails=false;
    if(sentinel.initialized.load() && !DateSentinelShutdownSafeV1(sentinel)) {
      Check(PollDateSentinelOwnerV1(sentinel,Stamp()),"owner recovers prior unsafe fixture world");
      Check(DateSentinelShutdownSafeV1(sentinel),"reset never erases an unsafe lifetime obligation");
    }
  }
  old::TacticalDailySentinelArmRequestV1 Request(unsigned days=1) {
    old::TacticalDailySentinelArmRequestV1 r{};r.starting_date_raw=24000;
    r.target_date_raw=24000+static_cast<std::int32_t>(days)*24;r.speed=5;
    r.mode=old::TacticalDailySentinelModeV1::terminal_or_sentinel;return r;
  }
  void Start(unsigned days=1,std::uint64_t ttl=5000) {
    Check(ArmDateSentinelV1(sentinel,Request(days),wall+ttl)==Arm::armed,"owner arms actual RAM reader");
    Check(!DateSentinelShutdownSafeV1(sentinel),"every admitted native arm starts unsafe");
  }
  void Date(std::int32_t n,bool paused=false) {Put(game,8,n);Put(jomini,0x20,static_cast<std::uint8_t>(paused));}
  CoreSnapshotPrefix Core() {CoreSnapshotPrefix c{};Check(ReadCoreSnapshot(bindings.core,c),"real core reader");return c;}
  old::MainThreadExecutionStampV1 Stamp() {
    auto c=Core();old::MainThreadExecutionStampV1 s{};s.pump_epoch=1;s.thread_id=GetCurrentThreadId();
    s.tls_initialized_flag_address=mailbox.tls_initialized_flag;s.tls_initialized=initialized;
    s.tls_context=reinterpret_cast<std::uintptr_t>(tls.data());s.tls_main_thread_marker=1;
    s.game_state=reinterpret_cast<std::uintptr_t>(game_slot);s.jomini_state=reinterpret_cast<std::uintptr_t>(jomini_slot);
    s.date_raw=c.clock.date_raw;s.paused=c.clock.paused;return s;
  }
};
void *Local(void *) {
  auto &f=*active;++f.locals;
  if(f.reject_at && f.locals==f.reject_at) {Put(f.tls,0x20,std::uint8_t{0});return nullptr;}
  if(f.mutate_at && f.locals==f.mutate_at) {
    std::int32_t date=0;std::memcpy(&date,f.game.data()+8,sizeof(date));Put(f.game,8,date+24);
  }
  return f.player.data();
}
void *__fastcall Tls() noexcept {++active->tls_calls;return active->tls.data();}
void __fastcall Pause(void *j,bool paused,std::int32_t player) {
  auto &f=*active;Check(j==f.jomini.data() && paused && player==7,"pause exact local owner ABI");
  ++f.pauses;if(f.pause_fails)return;Put(f.jomini,0x20,std::uint8_t{1});
  if(f.expire_on_pause)f.mono=f.sentinel.monotonic_deadline_ms;
}
void Failed(Fixture &f,std::uint32_t why,bool expect_pause=true) {
  Check((ReadDateSentinelDiagnosticsV1(f.sentinel).failure_flags&why)!=0,"specific failure latched");
  Check(ReadDateSentinelStatusV1(f.sentinel).state==Phase::failed,"failure never exposes exact success");
  Check(PollDateSentinelOwnerV1(f.sentinel,f.Stamp()),"verified owner aborts failed generation");
  const auto s=ReadDateSentinelStatusV1(f.sentinel);
  Check(s.state==Phase::failed && s.abnormal && s.pause_observed==expect_pause,"abort keeps failed even when paused");
  Check(!f.sentinel.armed.load(),"abort closes provider arm");
  Check(DateSentinelShutdownSafeV1(f.sentinel)==expect_pause,"failed pause/world never fakes teardown safe");
}
} // namespace
int main() {
  Fixture f;
  old::Bindings strict{};strict.enabled=true;strict.game_state_slot=&f.game_slot;
  strict.jomini_state_slot=&f.jomini_slot;strict.get_local_player=&Local;
  Check(!old::InitializeTacticalDailySentinelFixtureV1(strict,&Pause),"legacy default still requires every military storage slot");
  Check(!BindDateSentinelImageV1(0,kExecutableSha256).exact_build_admitted &&
      !BindDateSentinelImageV1(0x140000000,"old").exact_build_admitted,"binder exact hash and base gate");
  const auto image=BindDateSentinelImageV1(0x140000000,kExecutableSha256);
  Check(image.exact_build_admitted && !image.offline_fixture &&
      reinterpret_cast<std::uintptr_t>(image.set_paused)==0x143E65500,"new pause RVA only; address binding has no world call");
  auto forged=f.bindings;forged.offline_fixture=false;forged.module_base=0x140000000;
  Check(!InitializeDateSentinelV1(f.sentinel,forged,f.mailbox),"RAM roots cannot qualify production identity");
  Check(InitializeDateSentinelV1(f.sentinel,f.bindings,f.mailbox),"explicit fixture initializes date-only runtime");
  Check(!InitializeDateSentinelV1(f.sentinel,f.bindings,f.mailbox),"same fixed state cannot initialize twice");
  const auto idle_reads=f.locals,idle_tls=f.tls_calls,idle_wall=f.wall_calls,idle_mono=f.mono_calls;
  PostDateSentinelV1(&f.sentinel);
  Check(f.locals==idle_reads && f.tls_calls==idle_tls && f.wall_calls==idle_wall && f.mono_calls==idle_mono,
      "unarmed final callback has zero world/TLS/clock calls");
  auto c=f.Core();Check(c.has_played_character && c.played_character_id==kActor && kActor<0,"full signed generation ActorID is accepted");
  auto r=f.Request();r.army_count=1;r.army_ids[0]=1;
  Check(ArmDateSentinelV1(f.sentinel,r,f.wall+5000)==Arm::invalid_request &&
      old::ArmTacticalDailySentinelV1(r)==Arm::invalid_request,"date-only provider and shared runtime both reject non-a0");
  r=f.Request();r.mode=old::TacticalDailySentinelModeV1::decision_epoch;
  Check(ArmDateSentinelV1(f.sentinel,r,f.wall+5000)==Arm::invalid_request &&
      old::ArmTacticalDailySentinelV1(r)==Arm::invalid_request,"date-only initializer never widens decision mode");
  f.mailbox.owner_thread_id.store(GetCurrentThreadId()+1);
  Check(ArmDateSentinelV1(f.sentinel,f.Request(),f.wall+5000)==Arm::unavailable,"ARM owner identity mandatory");
  f.mailbox.owner_thread_id.store(GetCurrentThreadId());f.initialized=0;
  Check(ArmDateSentinelV1(f.sentinel,f.Request(),f.wall+5000)==Arm::unavailable,"ARM fresh TLS initialization mandatory");
  f.initialized=1;Put(f.tls,0x20,std::uint8_t{0});
  Check(ArmDateSentinelV1(f.sentinel,f.Request(),f.wall+5000)==Arm::unavailable,"ARM fresh TLS marker mandatory");
  Put(f.tls,0x20,std::uint8_t{1});f.Date(24024,true);
  Check(ArmDateSentinelV1(f.sentinel,f.Request(),f.wall+5000)==Arm::starting_date_mismatch,"ARM exact starting date");
  f.Date(24000,false);
  Check(ArmDateSentinelV1(f.sentinel,f.Request(),f.wall+5000)==Arm::requires_paused,"ARM paused requirement");
  f.Reset();f.reject_at=f.locals+5;
  Check(ArmDateSentinelV1(f.sentinel,f.Request(),f.wall+5000)==Arm::army_unavailable &&
      !DateSentinelShutdownSafeV1(f.sentinel) && f.sentinel.generation.load()==0,
      "failed first shared arm with lost fresh TLS preserves unsafe attempted world");
  Put(f.tls,0x20,std::uint8_t{1});f.reject_at=0;
  Check(PollDateSentinelOwnerV1(f.sentinel,f.Stamp()) && DateSentinelShutdownSafeV1(f.sentinel),
      "restored actual owner can prove generation-zero never-armed paused state safe");
  f.Reset();f.Start();
  c=f.Core();Check(DateSentinelAllowsResumeV1(f.sentinel,c),"same complete paused Core permits paired resume");
  auto wrong=c;wrong.played_character_id=0;
  Check(!DateSentinelAllowsResumeV1(f.sentinel,wrong),"different expected full-generation Core cannot resume");
  const auto first_generation=ReadDateSentinelStatusV1(f.sentinel).generation;
  const auto first_pauses=f.pauses;f.Date(24024);PostDateSentinelV1(&f.sentinel);
  auto status=ReadDateSentinelStatusV1(f.sentinel);
  Check(status.state==Phase::triggered && status.generation==first_generation && status.completed_daily_ticks==1 &&
      status.trigger_date_raw==24024 && status.target_date_raw==24024 && status.pause_wrapper_called &&
      status.pause_observed && status.overshoot_days==0 && status.signed_date_delta_from_target_raw==0 &&
      status.trigger_flags==old::tactical_daily_trigger_date_deadline && f.pauses==first_pauses+1,
      "one true day pauses exactly at target with shared real evaluator");
  const auto terminal_calls=f.locals;f.Date(24048);PostDateSentinelV1(&f.sentinel);
  Check(f.locals==terminal_calls && ReadDateSentinelStatusV1(f.sentinel).completed_daily_ticks==1,
      "target+24 callback after terminal cannot fabricate a second day");
  f.Reset();f.Start(3);const auto multiday_pauses=f.pauses;
  for(int day=1;day<=3;++day) {
    f.Date(24000+day*24);PostDateSentinelV1(&f.sentinel);
    status=ReadDateSentinelStatusV1(f.sentinel);
    Check(status.completed_daily_ticks==static_cast<unsigned>(day),"one increment per real post-day");
    Check(status.state==(day==3?Phase::triggered:Phase::armed),"multi-day state transition");
    Check(f.pauses==multiday_pauses+(day==3?1U:0U),"no intermediate synthetic pause");
    Check(!PollDateSentinelOwnerV1(f.sentinel,f.Stamp()) &&
        ReadDateSentinelStatusV1(f.sentinel).completed_daily_ticks==static_cast<unsigned>(day),"pump never evaluates or counts a day");
  }
  f.Reset();f.Start(2);f.Date(24024);PostDateSentinelV1(&f.sentinel);
  f.Date(24072);PostDateSentinelV1(&f.sentinel);Failed(f,date_sentinel_failure_sequence);
  Check(ReadDateSentinelStatusV1(f.sentinel).completed_daily_ticks==1,"target+24 skipped boundary is not counted as another day");
  f.Reset();f.Start();const auto cancel_generation=ReadDateSentinelStatusV1(f.sentinel).generation;
  Check(CancelDateSentinelV1(f.sentinel,cancel_generation+1)==Cancel::generation_mismatch,"cancel cannot cross generation");
  Check(CancelDateSentinelV1(f.sentinel,cancel_generation)==Cancel::canceled &&
      ReadDateSentinelStatusV1(f.sentinel).generation==cancel_generation &&
      ReadDateSentinelStatusV1(f.sentinel).state==Phase::idle,"cancel and status preserve shared generation");
  f.Reset();f.Start();f.Date(24024);const auto owner_reads=f.locals,owner_tls=f.tls_calls;
  std::thread foreign([&]{PostDateSentinelV1(&f.sentinel);});foreign.join();
  Check(f.locals==owner_reads && f.tls_calls==owner_tls,"foreign post records failure before any world/TLS callback");
  Failed(f,date_sentinel_failure_owner);
  Check(ReadDateSentinelStatusV1(f.sentinel).completed_daily_ticks==0,"foreign post does not call real evaluator");
  f.Reset();f.Start();f.Date(24024);f.initialized=0;
  const auto tls_reads=f.locals;PostDateSentinelV1(&f.sentinel);
  Check(f.locals==tls_reads,"fresh uninitialized TLS denies world reads");
  f.initialized=1;Failed(f,date_sentinel_failure_tls);
  f.Reset();f.Start();f.Date(24024);Put(f.tls,0x20,std::uint8_t{0});PostDateSentinelV1(&f.sentinel);
  Put(f.tls,0x20,std::uint8_t{1});Failed(f,date_sentinel_failure_tls);
  f.Reset();f.Start();f.Date(24024);Put(f.other_game,8,std::int32_t{24024});f.game_slot=f.other_game.data();
  const auto world_pauses=f.pauses;PostDateSentinelV1(&f.sentinel);Failed(f,date_sentinel_failure_world,false);
  Check(f.pauses==world_pauses,"different world is failed without pausing an unrelated application state");
  f.Reset();f.Start();f.Date(24024);
  constexpr auto changed=std::bit_cast<std::int32_t>(std::uint32_t{0x82000001});
  Put(f.entry,0xB0,changed);Put(f.actor,0x18,changed);PostDateSentinelV1(&f.sentinel);
  Failed(f,date_sentinel_failure_actor);
  Check(ReadDateSentinelStatusV1(f.sentinel).completed_daily_ticks==0,"same index different full generation is not same actor");
  f.Reset();f.Start();f.Date(24024);Put(f.game,0x70,std::int32_t{3});PostDateSentinelV1(&f.sentinel);
  Failed(f,date_sentinel_failure_speed);
  f.Reset();f.Start();f.Date(24024);Put(f.storage,0x2C,std::int32_t{0});PostDateSentinelV1(&f.sentinel);
  Put(f.storage,0x2C,std::int32_t{4});Failed(f,date_sentinel_failure_observation);
  f.Reset();f.Start(2);f.Date(24024);f.mutate_at=f.locals+3;PostDateSentinelV1(&f.sentinel);
  f.mutate_at=0;Failed(f,date_sentinel_failure_observation);
  f.Reset();f.mutate_at=f.locals+3;
  Check(ArmDateSentinelV1(f.sentinel,f.Request(),f.wall+5000)==Arm::unavailable && !f.sentinel.armed.load(),
      "changing Core across ARM observations cannot publish a runtime arm");
  f.Reset();f.Start(1,5);f.Date(24024);const auto original_deadline=f.sentinel.original_deadline_unix_ms;
  f.mono+=5;PostDateSentinelV1(&f.sentinel);Failed(f,date_sentinel_failure_expired);
  Check(f.sentinel.original_deadline_unix_ms==original_deadline &&
      ReadDateSentinelStatusV1(f.sentinel).completed_daily_ticks==0,"original monotonic cutoff is not renewed by a post");
  f.Reset();f.Start(1,5);c=f.Core();f.wall+=5;
  Check(!DateSentinelAllowsResumeV1(f.sentinel,c),"original UTC cutoff denies paired resume");
  Failed(f,date_sentinel_failure_expired);
  f.Reset();f.Start(1,5);f.Date(24024);f.expire_on_pause=true;PostDateSentinelV1(&f.sentinel);
  Failed(f,date_sentinel_failure_expired);
  Check(old::ReadTacticalDailySentinelStatusV1().state==Phase::failed,
      "expiry during target pause reclassifies actual shared terminal result as failed");
  f.Reset();f.Start(2);f.Date(24024,true);PostDateSentinelV1(&f.sentinel);
  Failed(f,date_sentinel_failure_unexpected_pause);
  f.Reset();Put(f.actor,0x1C,std::uint32_t{0});
  Check(ArmDateSentinelV1(f.sentinel,f.Request(),f.wall+5000)==Arm::unavailable,"real actor tag required at ARM");
  const auto final_diag=ReadDateSentinelDiagnosticsV1(f.sentinel);
  Check(final_diag.fixture_only && !final_diag.capability_granted,"NoGame fixture never confers runtime capability");
  f.Reset();
  DateSentinelStateV1 virgin{};
  const auto virgin_reads=f.locals,virgin_tls=f.tls_calls,virgin_wall=f.wall_calls,virgin_mono=f.mono_calls;
  std::thread idle_stop([&]{RequestDateSentinelShutdownV1(virgin);});idle_stop.join();
  Check(DateSentinelShutdownSafeV1(virgin) && virgin.shutdown_requested.load() &&
      !PollDateSentinelOwnerV1(virgin,{}),"never-armed stop is atomically safe without an owner");
  Check(f.locals==virgin_reads && f.tls_calls==virgin_tls && f.wall_calls==virgin_wall && f.mono_calls==virgin_mono,
      "unarmed shutdown request/poll performs zero native/world/TLS/clock calls");
  f.Start(3,5);f.Date(24024);f.pause_fails=true;
  const auto shutdown_generation=f.sentinel.generation.load();
  const auto shutdown_deadline=f.sentinel.original_deadline_unix_ms,shutdown_mono=f.sentinel.monotonic_deadline_ms;
  const auto stop_reads=f.locals,stop_tls=f.tls_calls,stop_wall=f.wall_calls,stop_clock=f.mono_calls,stop_pauses=f.pauses;
  std::thread stopping([&]{RequestDateSentinelShutdownV1(f.sentinel);});stopping.join();
  Check(!DateSentinelShutdownSafeV1(f.sentinel) &&
      (f.sentinel.pending_failure.load()&date_sentinel_failure_shutdown),"foreign stop only publishes sticky atomic request/failure");
  Check(f.locals==stop_reads && f.tls_calls==stop_tls && f.wall_calls==stop_wall &&
      f.mono_calls==stop_clock && f.pauses==stop_pauses,"stop caller invokes no native callback");
  Check(ArmDateSentinelV1(f.sentinel,f.Request(),f.wall+50000)==Arm::unavailable &&
      !DateSentinelAllowsResumeV1(f.sentinel,c),"requested shutdown closes new ARM and paired resume");
  Check(f.locals==stop_reads && f.tls_calls==stop_tls && f.wall_calls==stop_wall && f.mono_calls==stop_clock,
      "closed ARM/resume reject before any resource-dependent read");
  PostDateSentinelV1(&f.sentinel);
  Check(f.locals==stop_reads && f.tls_calls==stop_tls && f.pauses==stop_pauses,
      "post after stop cannot evaluate or invoke pause");
  f.mono=shutdown_mono+100;f.wall=shutdown_deadline+100;
  const auto stop_stamp=f.Stamp();f.mailbox.owner_thread_id.store(GetCurrentThreadId()+1);
  Check(!PollDateSentinelOwnerV1(f.sentinel,stop_stamp) && !DateSentinelShutdownSafeV1(f.sentinel) &&
      f.pauses==stop_pauses,"unknown owner retains resources without a pause call");
  f.mailbox.owner_thread_id.store(GetCurrentThreadId());
  Check(PollDateSentinelOwnerV1(f.sentinel,f.Stamp()) && !f.sentinel.armed.load() &&
      !DateSentinelShutdownSafeV1(f.sentinel) && f.pauses==stop_pauses+1,
      "native pause failure disarms evaluator but retains unsafe lifetime obligation");
  Check(PollDateSentinelOwnerV1(f.sentinel,f.Stamp()) && !DateSentinelShutdownSafeV1(f.sentinel) &&
      f.pauses==stop_pauses+2,"armed=false failed generation remains owner-pump retry eligible");
  Check(f.sentinel.original_deadline_unix_ms==shutdown_deadline && f.sentinel.monotonic_deadline_ms==shutdown_mono,
      "shutdown and failed retries never renew original UTC/monotonic cutoff");
  f.pause_fails=false;
  Check(PollDateSentinelOwnerV1(f.sentinel,f.Stamp()) && DateSentinelShutdownSafeV1(f.sentinel),
      "recovered owner/native pause proves actual paused and same-generation disarmed before safe");
  status=ReadDateSentinelStatusV1(f.sentinel);
  Check(status.state==Phase::failed && status.generation==shutdown_generation && status.pause_observed &&
      f.Core().clock.paused && !f.sentinel.armed.load(),"shutdown recovery remains failed and honestly paused");
  Check(ArmDateSentinelV1(f.sentinel,f.Request(),f.wall+50000)==Arm::unavailable &&
      !DateSentinelAllowsResumeV1(f.sentinel,f.Core()),"safe stop remains closed for this entire state lifetime");
  const auto safe_reads=f.locals,safe_tls=f.tls_calls,safe_wall=f.wall_calls,safe_mono=f.mono_calls,safe_pauses=f.pauses;
  RequestDateSentinelShutdownV1(f.sentinel);PostDateSentinelV1(&f.sentinel);
  Check(DateSentinelShutdownSafeV1(f.sentinel) && !PollDateSentinelOwnerV1(f.sentinel,{}),
      "acknowledged shutdown is idempotent and needs no owner world access");
  Check(f.locals==safe_reads && f.tls_calls==safe_tls && f.wall_calls==safe_wall &&
      f.mono_calls==safe_mono && f.pauses==safe_pauses,"safe shutdown request/post/poll has zero resource calls");
  std::cout<<"PASS date-only sentinel NoGame; real Core and shared evaluator; no hook/native code execution"<<std::endl;
  return 0;
}
