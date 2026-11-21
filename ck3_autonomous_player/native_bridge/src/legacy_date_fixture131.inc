#include "xar_bridge/ck3_1210_date_sentinel_v1.hpp"
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
}

} // fixture anonymous namespace
