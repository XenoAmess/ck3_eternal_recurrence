#include "xar_bridge/ck3_1210_date_sentinel_v1.hpp"
#include "xar_bridge/ck3_121003_ted_date_proof26785313_v1.hpp"
#include <array>
#include <bit>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <chrono>
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
void*pause_actor=nullptr;std::int32_t pause_actor_id=-1;
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
  std::array<std::byte,0x30> tls{},worker_tls{};
  std::vector<std::byte> data=std::vector<std::byte>(kPlayerCharacterManagerOffset+0x80);
  std::array<void *,1> entries{entry.data()};
  void *game_slot=game.data(),*jomini_slot=jomini.data(),*storage_slot=storage.data();
  std::uint8_t initialized=1;
  unsigned locals=0,tls_calls=0,wall_calls=0,mono_calls=0,pauses=0,mutate_at=0,reject_at=0,switch_root_at=0,switch_local_at=0;
  std::uint64_t wall=1000000,mono=1000;
  bool expire_on_pause=false,pause_fails=false;
  old::MainThreadQueryMailboxV1 mailbox{};
  DateSentinelBindingsV1 bindings{};
  DateSentinelStateV1 sentinel{};
  std::uintptr_t manager_token=0x1210,holder_token=0x1211;
  DateSentinelWorkerNativeV1 native{};
  std::atomic<std::uint32_t> worker_thread_id{0};
  std::uint64_t worker_birth=123456789;
  std::uintptr_t native_handle=0x121050,duplicate_token=0x121100;
  bool native_open=true,duplicate_open=false,worker_live=true,worker_process=true;
  bool snapshot_ok=true,duplicate_alias=false,game_access_active=false,access_allowed=true;
  unsigned access_enters=0,access_leaves=0,before_post_pauses=0;
  std::atomic<bool> block_pause{false},pause_entered{false};
  std::uint32_t command_scope=1;
  unsigned duplicates=0,closes=0,native_close_attempts=0,last_post_pause_delta=0,snapshot_reads=0;
  std::uint32_t last_pause_thread=0;
  std::mutex work_mutex;
  std::condition_variable work_cv;
  bool worker_ready=false,worker_exit=false,work_requested=false,work_done=false;
  std::thread worker;
  Fixture() {
    active=this;
    bindings.exact_build_admitted=true;bindings.offline_fixture=true;
    bindings.core={true,&game_slot,&jomini_slot,&storage_slot,&Local};bindings.set_paused=&Pause;
    bindings.clock_context=this;bindings.utc_now=&Wall;bindings.monotonic_now=&Mono;
    bindings.command_manager=reinterpret_cast<std::uintptr_t>(&manager_token);
    bindings.worker_function=0x1210F000;
    bindings.worker_fixture={this,&Snapshot,&Duplicate,&Probe,&Scope,&Close,&Access};
    mailbox.state.store(old::MainThreadQueryMailboxStateV1::idle);
    mailbox.owner_thread_id.store(GetCurrentThreadId());mailbox.owner_verified_pump_epochs.store(2);
    mailbox.offline_fixture=true;mailbox.tls_initialized_flag=reinterpret_cast<std::uintptr_t>(&initialized);
    mailbox.tls_context_getter=&Tls;
    Reset();
    worker=std::thread([this] {
      std::unique_lock lock(work_mutex);worker_thread_id.store(GetCurrentThreadId());
      worker_ready=true;work_cv.notify_all();
      for(;;) {
        work_cv.wait(lock,[&]{return work_requested||worker_exit;});
        if(worker_exit)break;
        work_requested=false;lock.unlock();PostDateSentinelV1(&sentinel);lock.lock();
        work_done=true;work_cv.notify_all();
      }
    });
    std::unique_lock lock(work_mutex);work_cv.wait(lock,[&]{return worker_ready;});ResetWorker();
  }
  ~Fixture() {
    if(DateSentinelShutdownSafeV1(sentinel))Check(ReleaseDateSentinelWorkerV1(sentinel),"safe fixture releases only owned duplicate");
    {std::lock_guard lock(work_mutex);worker_exit=true;work_cv.notify_all();}
    worker.join();
  }
  void ResetWorker() {
    native={bindings.command_manager,bindings.worker_function,bindings.command_manager,
      reinterpret_cast<std::uintptr_t>(&holder_token),native_handle,worker_thread_id.load(),1,0};
    native_open=true;worker_live=true;worker_process=true;snapshot_ok=true;duplicate_alias=false;
    worker_birth=123456789;command_scope=1;last_post_pause_delta=0;access_allowed=true;game_access_active=false;
  }
  void BeginPost() {
    std::lock_guard lock(work_mutex);before_post_pauses=pauses;work_done=false;work_requested=true;work_cv.notify_all();
  }
  void EndPost() {
    std::unique_lock lock(work_mutex);work_cv.wait(lock,[&]{return work_done;});last_post_pause_delta=pauses-before_post_pauses;
  }
  void Post(){BeginPost();EndPost();}
  static bool Snapshot(void *p,DateSentinelWorkerNativeV1 &out) noexcept {
    auto &f=*static_cast<Fixture *>(p);++f.snapshot_reads;out=f.native;return f.snapshot_ok;
  }
  static bool Duplicate(void *p,std::uintptr_t handle,std::uintptr_t &out) noexcept {
    auto &f=*static_cast<Fixture *>(p);out=0;
    if(handle!=f.native_handle || !f.native_open)return false;
    if(f.duplicate_alias){out=handle;return true;}
    ++f.duplicates;out=++f.duplicate_token;f.duplicate_open=true;return true;
  }
  static bool Probe(void *p,std::uintptr_t handle,std::uint32_t &id,std::uint64_t &birth,bool &live,bool &process) noexcept {
    auto &f=*static_cast<Fixture *>(p);
    if(!((handle==f.native_handle && f.native_open) || (handle==f.duplicate_token && f.duplicate_open)))return false;
    id=f.worker_thread_id.load();birth=f.worker_birth;live=f.worker_live;process=f.worker_process;return true;
  }
  static bool Scope(void *p,std::uint32_t &id,std::uint8_t &initialized,std::uint32_t &scope,std::uint8_t &access) noexcept {
    auto &f=*static_cast<Fixture *>(p);id=GetCurrentThreadId();initialized=f.initialized;scope=f.command_scope;
    access=f.game_access_active?1:0;return true;
  }
  static bool Access(void *p,DateSentinelGameBodyV1 body,void *context) noexcept {
    auto &f=*static_cast<Fixture *>(p);
    if(!f.access_allowed || GetCurrentThreadId()!=f.worker_thread_id.load())return false;
    const bool prior_access=f.game_access_active;f.game_access_active=true;++f.access_enters;
    const bool result=body(context);f.game_access_active=prior_access;++f.access_leaves;return result;
  }
  static bool Close(void *p,std::uintptr_t handle) noexcept {
    auto &f=*static_cast<Fixture *>(p);
    if(handle==f.native_handle){++f.native_close_attempts;return false;}
    if(handle!=f.duplicate_token)return false;
    ++f.closes;f.duplicate_open=false;return true;
  }
  static std::uint64_t Wall(void *p) noexcept {auto &f=*static_cast<Fixture *>(p);++f.wall_calls;return f.wall;}
  static std::uint64_t Mono(void *p) noexcept {auto &f=*static_cast<Fixture *>(p);++f.mono_calls;return f.mono;}
  void Reset() {
    game_slot=game.data();jomini_slot=jomini.data();storage_slot=storage.data();initialized=1;ResetWorker();
    block_pause.store(false);pause_entered.store(false);
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
    wall+=10000;mono+=10000;mutate_at=0;reject_at=0;switch_root_at=0;switch_local_at=0;expire_on_pause=false;pause_fails=false;
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
  if(f.switch_root_at && f.locals==f.switch_root_at)f.game_slot=f.other_game.data();
  if(f.switch_local_at && f.locals==f.switch_local_at) {
    Put(f.players,0x1F0,std::int32_t{8});Put(f.player,0x70,std::int32_t{8});
  }
  if(f.reject_at && f.locals==f.reject_at) {Put(f.tls,0x20,std::uint8_t{0});return nullptr;}
  if(f.mutate_at && f.locals==f.mutate_at) {
    std::int32_t date=0;std::memcpy(&date,f.game.data()+8,sizeof(date));Put(f.game,8,date+24);
  }
  return f.player.data();
}
void *__fastcall Tls() noexcept {
  ++active->tls_calls;
  return GetCurrentThreadId()==active->worker_thread_id.load()?active->worker_tls.data():active->tls.data();
}
void __fastcall Pause(void *j,bool paused,std::int32_t player) {
  auto &f=*active;Check(j==f.jomini.data() && paused && player==7,"pause exact local owner ABI");
  if(GetCurrentThreadId()==f.worker_thread_id.load()) {
    Check(f.game_access_active,"worker native pause requires explicit game-access scope");
    f.pause_entered.store(true,std::memory_order_release);
    while(f.block_pause.load(std::memory_order_acquire))std::this_thread::yield();
  }
  ++f.pauses;f.last_pause_thread=GetCurrentThreadId();if(f.pause_fails)return;Put(f.jomini,0x20,std::uint8_t{1});
  if(f.expire_on_pause)f.mono=f.sentinel.monotonic_deadline_ms;
  if(pause_actor){Put(f.rows,0x18,pause_actor);Put(f.entry,0xB0,pause_actor_id);pause_actor=nullptr;}
}
[[maybe_unused]]void Failed(Fixture &f,std::uint32_t why,bool expect_pause=true) {
  Check((ReadDateSentinelDiagnosticsV1(f.sentinel).failure_flags&why)!=0,"specific failure latched");
  Check(ReadDateSentinelStatusV1(f.sentinel).state==Phase::failed,"failure never exposes exact success");
  if(!DateSentinelShutdownSafeV1(f.sentinel))
    Check(PollDateSentinelOwnerV1(f.sentinel,f.Stamp()),"verified UI owner aborts retained failed generation");
  const auto s=ReadDateSentinelStatusV1(f.sentinel);
  Check(s.state==Phase::failed && s.abnormal && s.pause_observed==expect_pause,"abort keeps failed even when paused");
  Check(!f.sentinel.armed.load(),"abort closes provider arm");
  Check(DateSentinelShutdownSafeV1(f.sentinel)==expect_pause,"failed pause/world never fakes teardown safe");
}
[[maybe_unused]]void FinishActorFailure(Fixture &f,unsigned expected_pause_calls=1) {
  const auto before=f.pauses;
  const auto deadline=f.sentinel.original_deadline_unix_ms,mono=f.sentinel.monotonic_deadline_ms;
  const auto generation=f.sentinel.generation.load();
  Check(ReadDateSentinelStatusV1(f.sentinel).state==Phase::failed,"actor failure remains unavailable before owner cleanup");
  const bool already_safe=DateSentinelShutdownSafeV1(f.sentinel);
  if(!already_safe)Check(PollDateSentinelOwnerV1(f.sentinel,f.Stamp()),"complete same-world Core permits UI failure-only native pause");
  else Check(f.last_post_pause_delta==expected_pause_calls && f.last_pause_thread==f.worker_thread_id.load(),
      "qualified worker closes actor failure before another UI pump");
  const auto status=ReadDateSentinelStatusV1(f.sentinel);
  Check(status.state==Phase::failed && status.abnormal && status.generation==generation &&
      status.completed_daily_ticks==0 && !(status.trigger_flags&old::tactical_daily_trigger_date_deadline) &&
      status.pause_observed && f.Core().clock.paused && DateSentinelShutdownSafeV1(f.sentinel) &&
      !f.sentinel.armed.load() && (already_safe || f.pauses==before+expected_pause_calls),
      "actor-free pause-world cleanup never fabricates a successful day or actor");
  Check(f.sentinel.original_deadline_unix_ms==deadline && f.sentinel.monotonic_deadline_ms==mono,
      "actor failure cleanup preserves original UTC and monotonic cutoffs");
}
} // namespace

#if defined(XAR_CK3_ENABLE_121003_26785313_TED_TRANSITION_V1) && XAR_CK3_ENABLE_121003_26785313_TED_TRANSITION_V1
int main(){
 Fixture f;Check(InitializeDateSentinelV1(f.sentinel,f.bindings,f.mailbox),"explicit NoGame runtime initializes");
 constexpr auto recipient=std::bit_cast<std::int32_t>(std::uint32_t{0x82000001});
 constexpr auto third=std::bit_cast<std::int32_t>(std::uint32_t{0x83000001});
 std::array<std::byte,0x1E0>next{},other{};
 Put(next,0x18,recipient);Put(next,0x1C,std::uint32_t{0x43686172});Put(other,0x18,third);Put(other,0x1C,std::uint32_t{0x43686172});
 const auto change=[&]{Put(f.rows,0x18,static_cast<void*>(next.data()));Put(f.entry,0xB0,recipient);};
 const auto fixed=[&](TedFixedDayStage267V1 stage){Check(ArmTedFixedDay267V1(f.sentinel,f.Request(),f.wall+5000,stage)==Arm::armed,"new fixed arm");Check(DateSentinelAllowsResumeV1(f.sentinel,f.Core()),"same original paused before Resume");};
 const auto proof=[&]{TedFixedDayProof267V1 p;old::TacticalDailySentinelStatusV1 status;const bool found=ReadTedFixedDayProof267V1(f.sentinel,f.sentinel.generation.load(),p,status);return std::pair{found,p};};
 // Old entry is intentionally not opted in. It still rejects exactly this actor change.
 f.Start();f.Date(24024);change();f.Post();Check(!proof().first,"old actor abort never promoted");Failed(f,date_sentinel_failure_actor);FinishActorFailure(f);
 f.Reset();fixed(TedFixedDayStage267V1::song_transition);const auto original=f.sentinel.original_deadline_unix_ms;f.Date(24024);change();f.Post();auto p=proof();Check(p.first&&p.second.actor_changed&&p.second.before.core.played_character_id==kActor&&p.second.after.core.played_character_id==recipient&&p.second.before.actor!=p.second.after.actor&&p.second.original_deadline_unix_ms==original&&p.second.status.completed_daily_ticks==1&&p.second.after.core.clock.paused,"actual changed actor exact one tick captured");Check(p.second.worker.creation_time==f.worker_birth&&p.second.captured_unix_ms<original&&p.second.captured_monotonic_ms<p.second.monotonic_deadline_ms&&f.access_enters==f.access_leaves,"worker epoch, original bounds and actual cleanup retained");TedFixedDayProof267V1 missing;old::TacticalDailySentinelStatusV1 wrong;Check(!ReadTedFixedDayProof267V1(f.sentinel,p.second.generation+1,missing,wrong),"foreign generation refused");
 f.Reset();fixed(TedFixedDayStage267V1::recipient_stable);f.Date(24024);f.Post();p=proof();Check(p.first&&!p.second.actor_changed&&p.second.before.core.played_character_id==p.second.after.core.played_character_id,"D2 sameactor uses same sole evaluator proof");
 f.Reset();fixed(TedFixedDayStage267V1::recipient_stable);f.Date(24024);change();f.Post();Check(!proof().first,"D2 cannot perform another actor transition");Failed(f,date_sentinel_failure_actor);
 f.Reset();Check(ArmTedFixedDay267V1(f.sentinel,f.Request(2),f.wall+5000,TedFixedDayStage267V1::song_transition)==Arm::invalid_request,"fixed family cannot request 2days");
 for(unsigned which=0;which<8;++which){f.Reset();fixed(TedFixedDayStage267V1::song_transition);f.Date(24024);change();
  switch(which){case 0:f.game_slot=f.other_game.data();break;case 1:Put(f.game,0x70,std::int32_t{3});break;case 2:f.wall=f.sentinel.original_deadline_unix_ms;break;case 3:f.Date(24048);break;case 4:++f.worker_birth;break;case 5:f.expire_on_pause=true;break;case 6:pause_actor=other.data();pause_actor_id=third;break;case 7:Put(next,0x1D0,static_cast<void*>(next.data()));break;}
  f.Post();Check(!proof().first,"world/speed/deadline/sequence/worker/expiry-during-pause/thirdactor/dead actor never captured");Put(next,0x1D0,static_cast<void*>(nullptr));f.game_slot=f.game.data();Put(f.game,0x70,std::int32_t{4});f.ResetWorker();f.expire_on_pause=false;pause_actor=nullptr;
  if(!DateSentinelShutdownSafeV1(f.sentinel)){Put(f.jomini,0x20,std::uint8_t{1});Check(PollDateSentinelOwnerV1(f.sentinel,f.Stamp()),"sameworld failure cleanup");}
 }
 f.Reset();f.Start();f.Date(24024);f.Post();Check(!proof().first,"old sameactor completed date never receives new family proof");
 // A later owner observation is separate from the immutable worker proof.
 // This is the actual fixture worker/evaluator, not a hand-constructed proof.
 f.Reset();fixed(TedFixedDayStage267V1::song_transition);f.Date(24024);f.Post();p=proof();
 Check(p.first&&!p.second.actor_changed&&p.second.stage==TedFixedDayStage267V1::song_transition&&
     p.second.after.core.played_character_id==kActor&&p.second.after.core.clock.paused&&
     p.second.status.state==Phase::triggered&&p.second.status.completed_daily_ticks==1,
     "deferred proof starts at real worker sameactor exact24 pause");
 const auto frozen=p.second;
 const auto frozen_pauses=f.pauses,frozen_enters=f.access_enters,frozen_leaves=f.access_leaves;
 const auto same_observation=[](const DateSentinelObservationV1&a,const DateSentinelObservationV1&b) {
  const auto &x=a.core,&y=b.core;
  return x.clock.date_raw==y.clock.date_raw&&x.clock.speed==y.clock.speed&&x.clock.paused==y.clock.paused&&
    x.local_player_id==y.local_player_id&&x.map_ready==y.map_ready&&x.has_played_character==y.has_played_character&&
    x.played_character_id==y.played_character_id&&x.played_character_alive==y.played_character_alive&&
    a.game==b.game&&a.jomini==b.jomini&&a.storage==b.storage&&a.data==b.data&&a.players==b.players&&a.player==b.player&&a.actor==b.actor;
 };
 const auto no_new_work=[&] {
  const auto status=old::ReadTacticalDailySentinelStatusV1();
  Check(f.pauses==frozen_pauses&&f.access_enters==frozen_enters&&f.access_leaves==frozen_leaves&&
      f.sentinel.generation.load()==frozen.generation&&status.generation==frozen.generation&&
      status.state==Phase::triggered&&status.completed_daily_ticks==1,
      "owner observation never pauses, enters evaluator access, re-ARMs or adds daily ticks");
 };
 const auto cleared=[](const DateSentinelObservationV1&o) {
  return !o.game&&!o.jomini&&!o.storage&&!o.data&&!o.players&&!o.player&&!o.actor;
 };
 const auto denied=[&](const TedFixedDayProof267V1&input,const old::MainThreadExecutionStampV1&stamp) {
  DateSentinelObservationV1 observed=frozen.after;
  Check(!ReadTedDeferredActorOnOwner267V1(f.sentinel,input,stamp,observed)&&cleared(observed),
      "deferred rejection leaves no stale actor observation");no_new_work();
 };
 DateSentinelObservationV1 observed{};
 Check(ReadTedDeferredActorOnOwner267V1(f.sentinel,frozen,f.Stamp(),observed)&&
     same_observation(observed,frozen.after),"actual owner may observe original actor at exact paused day");no_new_work();
 change();
 Check(ReadTedDeferredActorOnOwner267V1(f.sentinel,frozen,f.Stamp(),observed)&&
     observed.core.played_character_id==recipient&&observed.actor==next.data()&&observed.core.clock.date_raw==24024&&observed.core.clock.paused,
     "actual later owner independently observes different living actor at original exact24 pause");no_new_work();
 auto stored_again=proof();
 Check(stored_again.first&&!stored_again.second.actor_changed&&same_observation(stored_again.second.before,frozen.before)&&
     same_observation(stored_again.second.after,frozen.after)&&stored_again.second.after.core.played_character_id==kActor&&
     stored_again.second.original_deadline_unix_ms==frozen.original_deadline_unix_ms&&
     stored_again.second.monotonic_deadline_ms==frozen.monotonic_deadline_ms&&stored_again.second.captured_unix_ms==frozen.captured_unix_ms&&
     stored_again.second.captured_monotonic_ms==frozen.captured_monotonic_ms&&stored_again.second.worker.native==frozen.worker.native&&
     stored_again.second.worker.owned_handle==frozen.worker.owned_handle&&stored_again.second.worker.creation_time==frozen.worker.creation_time,
     "later actor does not rewrite immutable proof after/worker/generation/original cutoffs");
 auto stamp=f.Stamp();auto bad_stamp=stamp;bad_stamp.thread_id=f.worker_thread_id.load();denied(frozen,bad_stamp);
 bad_stamp=stamp;bad_stamp.tls_context+=8;denied(frozen,bad_stamp);
 bad_stamp=stamp;bad_stamp.tls_initialized=0;denied(frozen,bad_stamp);
 Put(f.tls,0x20,std::uint8_t{0});denied(frozen,stamp);Put(f.tls,0x20,std::uint8_t{1});
 bool foreign_accepted=true;DateSentinelObservationV1 foreign_observed=frozen.after;
 std::thread foreign([&]{foreign_accepted=ReadTedDeferredActorOnOwner267V1(f.sentinel,frozen,stamp,foreign_observed);});foreign.join();
 Check(!foreign_accepted&&cleared(foreign_observed),"foreign actual thread cannot borrow owner stamp");no_new_work();
 ++f.worker_birth;denied(frozen,stamp);--f.worker_birth;
 ++f.native.holder;denied(frozen,stamp);--f.native.holder;
 f.other_game=f.game;f.game_slot=f.other_game.data();denied(frozen,f.Stamp());f.game_slot=f.game.data();
 Put(f.players,0x1F0,std::int32_t{8});Put(f.player,0x70,std::int32_t{8});denied(frozen,f.Stamp());
 Put(f.players,0x1F0,std::int32_t{7});Put(f.player,0x70,std::int32_t{7});
 f.Date(24048,true);denied(frozen,f.Stamp());f.Date(24024,true);
 Put(f.game,0x70,std::int32_t{3});denied(frozen,f.Stamp());Put(f.game,0x70,std::int32_t{4});
 f.Date(24024,false);denied(frozen,f.Stamp());f.Date(24024,true);
 const auto original_wall=f.wall,original_mono=f.mono;
 f.wall=frozen.original_deadline_unix_ms;denied(frozen,f.Stamp());f.wall=original_wall;
 f.mono=frozen.monotonic_deadline_ms;denied(frozen,f.Stamp());f.mono=original_mono;
 auto altered=frozen;++altered.generation;denied(altered,f.Stamp());
 altered=frozen;++altered.original_deadline_unix_ms;denied(altered,f.Stamp());
 altered=frozen;++altered.monotonic_deadline_ms;denied(altered,f.Stamp());
 altered=frozen;altered.after.actor=next.data();altered.after.core.played_character_id=recipient;denied(altered,f.Stamp());
 altered=frozen;++altered.worker.creation_time;denied(altered,f.Stamp());
 altered=frozen;altered.actor_changed=true;denied(altered,f.Stamp());
 altered=frozen;altered.stage=TedFixedDayStage267V1::recipient_stable;denied(altered,f.Stamp());
 // Only this NoGame fixture restores its intentionally injected refusal seams for teardown.
 // The called reader neither clears UNKNOWN/unsafe state nor acknowledges cleanup.
 f.sentinel.armed.store(true);denied(frozen,f.Stamp());f.sentinel.armed.store(false);
 f.sentinel.shutdown_safe.store(false);denied(frozen,f.Stamp());f.sentinel.shutdown_safe.store(true);
 f.sentinel.shutdown_requested.store(true);denied(frozen,f.Stamp());f.sentinel.shutdown_requested.store(false);
 f.sentinel.pending_failure.store(date_sentinel_failure_observation);denied(frozen,f.Stamp());f.sentinel.pending_failure.store(0);
 f.sentinel.access_cleanup_unknown.store(true);denied(frozen,f.Stamp());
 Check(f.sentinel.access_cleanup_unknown.load(),"readonly owner reader never clears unknown native cleanup");f.sentinel.access_cleanup_unknown.store(false);
 Check(ReadTedDeferredActorOnOwner267V1(f.sentinel,frozen,f.Stamp(),observed)&&observed.core.played_character_id==recipient,
     "pure failed observations did not consume or replace original finite proof");no_new_work();
 // A valid old Date completion has no opted-in fixed proof, even with fabricated input DATA.
 f.Reset();f.Start();f.Date(24024);f.Post();TedFixedDayProof267V1 old_input{};old_input.captured=true;
 old_input.generation=f.sentinel.generation.load();old_input.stage=TedFixedDayStage267V1::song_transition;
 const auto old_pauses=f.pauses;observed=frozen.after;
 Check(!ReadTedDeferredActorOnOwner267V1(f.sentinel,old_input,f.Stamp(),observed)&&cleared(observed)&&f.pauses==old_pauses,
     "old Date17 completed generation never acquires deferred TED owner authority");
 Check(!f.sentinel.access_cleanup_unknown.load()&&f.native_close_attempts==0,"no borrowed handle close or fake cleanup");
 std::cout<<"PASS TED finite sentinel actual Core/worker/evaluator proof and old strict path; no Game\n";return 0;
}

#else
int main(){Fixture f;Check(InitializeDateSentinelV1(f.sentinel,f.bindings,f.mailbox),"NoGame init");Check(ArmTedFixedDay267V1(f.sentinel,f.Request(),f.wall+5000,TedFixedDayStage267V1::song_transition)==Arm::unavailable,"new family defaultOFF");f.Start();f.Date(24024);f.Post();TedFixedDayProof267V1 p;old::TacticalDailySentinelStatusV1 status;Check(!ReadTedFixedDayProof267V1(f.sentinel,f.sentinel.generation.load(),p,status)&&status.state==Phase::triggered&&DateSentinelShutdownSafeV1(f.sentinel),"old sameactor works without new proof");DateSentinelObservationV1 unavailable{};unavailable.game=f.game.data();const auto off_stamp=f.Stamp();const auto off_pauses=f.pauses;Check(!ReadTedDeferredActorOnOwner267V1(f.sentinel,p,off_stamp,unavailable)&&!unavailable.game&&f.pauses==off_pauses,"deferred owner reader defaultOFF false and output clear, no pause");std::cout<<"PASS TED defaultOFF; old date remains strict and functional\n";return 0;}
#endif
