#include "xar_bridge/ck3_1210_date_sentinel_v1.hpp"
#include "xar_bridge/ck3_1210_date_worker_game_access_v1.hpp"
#include <array>
#include <bit>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <thread>
#include <vector>
using namespace xar::ck3_1210;
namespace old=xar::ck3_11906;
namespace {
void Check(bool ok,const char *why) {
  if(!ok){std::fprintf(stderr,"FAIL %s\n",why);std::exit(1);}
}
template<class B,class T> void Put(B &b,std::size_t n,T value) {
  Check(n<=b.size() && sizeof(value)<=b.size()-n,"fixture bounds");
  std::memcpy(b.data()+n,&value,sizeof(value));
}
struct AccessModel {
  DateWorkerGameAccessSampleV1 state{0x1000,0x2000,1,0};
  unsigned acquired=0,destroyed=0,bodies=0,samples=0,fail_sample_at=0;
  bool acquire_before=false,acquire_after=false,destroy_before=false,destroy_after=false;
  bool drift=false,body_fault=false,body_result=true,descriptor_valid=true;
  std::atomic<bool> block_destroy{false},destroy_entered{false};
  std::atomic<bool> nested_requested{false},nested_completed{false};
  DateSentinelStateV1 *nested_sentinel=nullptr;
};
bool Sample(void *p,DateWorkerGameAccessSampleV1 &out) {
  auto &m=*static_cast<AccessModel *>(p);++m.samples;out=m.state;
  return m.samples!=m.fail_sample_at;
}
void Acquire(void *p) {
  auto &m=*static_cast<AccessModel *>(p);++m.acquired;
  if(m.acquire_before)RaiseException(0xE0150001,0,0,nullptr);
  m.state.native_access=1;
  if(m.drift)++m.state.application;
  if(m.acquire_after)RaiseException(0xE0150002,0,0,nullptr);
}
void Destroy(void *p,void *descriptor) {
  auto &m=*static_cast<AccessModel *>(p);
  // Entry follows the real V2 body's return; the native release is not done.
  m.destroy_entered.store(true,std::memory_order_release);
  while(m.block_destroy.load(std::memory_order_acquire)) {
    if(m.nested_requested.exchange(false,std::memory_order_acq_rel)) {
      Check(m.nested_sentinel!=nullptr,"nested fixture state");
      PostDateSentinelV1(m.nested_sentinel);
      m.nested_completed.store(true,std::memory_order_release);
    }
    std::this_thread::yield();
  }
  ++m.destroyed;
  const auto *bytes=static_cast<const unsigned char *>(descriptor);
  if(bytes[0]!=1)m.descriptor_valid=false;
  for(unsigned i=1;i<0x48;++i)if(bytes[i])m.descriptor_valid=false;
  if(m.destroy_before)RaiseException(0xE0150003,0,0,nullptr);
  m.state.native_access=0;
  if(m.destroy_after)RaiseException(0xE0150004,0,0,nullptr);
}
bool Body(void *p) noexcept {
  auto &m=*static_cast<AccessModel *>(p);++m.bodies;
  if(m.body_fault)RaiseException(0xE0150005,0,0,nullptr);
  return m.body_result;
}
DateWorkerGameAccessBindingsV1 Bind(AccessModel &m) {
  DateWorkerGameAccessBindingsV1 b{};b.offline_fixture=true;
  b.fixture={&m,&Sample,&Acquire,&Destroy};return b;
}
DateWorkerGameAccessResultV2 Run(AccessModel &m) {
  auto b=Bind(m);return WithDateWorkerGameAccessV2(&b,&Body,&m);
}
void PairCases() {
  {AccessModel m;const auto r=Run(m);
    Check(r.Succeeded() && r.CleanupKnown() && r.acquisition==DateWorkerAcquisitionV2::owned &&
      r.release==DateWorkerReleaseV2::owned_released && m.acquired==1 && m.destroyed==1 &&
      !m.state.native_access && m.descriptor_valid,"owned release proven independently of body");}
  {AccessModel m;m.body_result=false;const auto r=Run(m);
    Check(!r.Succeeded() && r.CleanupKnown() && r.body==DateWorkerBodyV2::failed &&
      r.release==DateWorkerReleaseV2::owned_released,"failed body can still have proven cleanup");}
  {AccessModel m;m.state.native_access=1;const auto r=Run(m);
    Check(r.Succeeded() && r.acquisition==DateWorkerAcquisitionV2::borrowed &&
      r.release==DateWorkerReleaseV2::borrowed_preserved && !m.acquired && !m.destroyed &&
      m.state.native_access==1,"borrowed resource is never destroyed");}
  {AccessModel m;m.body_fault=true;const auto r=Run(m);
    Check(!r.Succeeded() && r.CleanupKnown() && r.body==DateWorkerBodyV2::failed &&
      r.release==DateWorkerReleaseV2::owned_released && m.destroyed==1,"body SEH preserves owned release proof");}
  {AccessModel m;m.acquire_after=true;const auto r=Run(m);
    Check(!r.Succeeded() && r.CleanupKnown() && r.acquisition==DateWorkerAcquisitionV2::owned &&
      r.body==DateWorkerBodyV2::not_called && m.destroyed==1,"acquire trace SEH pairs only after genuine owned proof");}
  {AccessModel m;m.acquire_before=true;const auto r=Run(m);
    Check(!r.CleanupKnown() && r.acquisition==DateWorkerAcquisitionV2::unknown &&
      r.release==DateWorkerReleaseV2::unknown && !m.destroyed && !m.bodies,
      "access zero after acquire SEH cannot prove absence of partial native acquisition");}
  {AccessModel m;m.drift=true;const auto r=Run(m);
    Check(!r.Succeeded() && !r.CleanupKnown() && r.acquisition==DateWorkerAcquisitionV2::unknown &&
      !m.destroyed && !m.bodies && m.state.native_access==1,"post-acquire identity drift retains UNKNOWN");}
  {AccessModel m;m.destroy_before=true;const auto r=Run(m);
    Check(!r.Succeeded() && !r.CleanupKnown() && r.acquisition==DateWorkerAcquisitionV2::owned &&
      r.release==DateWorkerReleaseV2::unknown && m.destroyed==1 && m.state.native_access==1,
      "pre-release SEH is owned plus release UNKNOWN, with no retry");}
  {AccessModel m;m.destroy_after=true;const auto r=Run(m);
    Check(!r.CleanupKnown() && m.destroyed==1 && !m.state.native_access,
      "post-release SEH remains conservatively UNKNOWN without a completed release proof");}
  {AccessModel m;m.fail_sample_at=5;const auto r=Run(m);
    Check(!r.CleanupKnown() && r.release==DateWorkerReleaseV2::unknown && m.destroyed==1 &&
      !m.state.native_access,"unreadable release sample cannot become cleanup proven");}
  {AccessModel m;m.state.native_access=1;m.body_fault=true;const auto r=Run(m);
    Check(!r.Succeeded() && r.CleanupKnown() && r.release==DateWorkerReleaseV2::borrowed_preserved &&
      !m.acquired && !m.destroyed,"borrowed body SEH preserves the outer owner");}
  {DateWorkerGameAccessResultV2 r{DateWorkerAcquisitionV2::borrowed,
      DateWorkerReleaseV2::owned_released,DateWorkerBodyV2::succeeded,true};
    Check(!r.CleanupKnown() && !r.Succeeded(),"invalid acquisition/release matrix fails closed");}
  {AccessModel m;auto b=Bind(m);
    Check(WithDateWorkerGameAccessV1(&b,&Body,&m) && m.destroyed==1,"legacy V1 bool entry remains callable");}
}
struct Consumer;
void InvokePostForFixture(Consumer *) noexcept;
Consumer *active=nullptr;
void *Local(void *);
void *__fastcall Tls() noexcept;
void __fastcall Pause(void *,bool,std::int32_t);
struct Consumer {
  std::array<std::byte,0xB0> game{};
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
  std::uintptr_t manager_token=0x1210,holder_token=0x1211;
  DateSentinelWorkerNativeV1 native{};
  old::MainThreadQueryMailboxV1 mailbox{};
  DateSentinelBindingsV1 bindings{};
  DateSentinelStateV1 sentinel{};
  AccessModel access{};
  DateWorkerGameAccessBindingsV1 access_binding{};
  std::atomic<std::uint32_t> worker_id{0};
  std::atomic<bool> go{false},done{false},worker_exit{false};
  std::thread worker;
  std::atomic<bool> post_fault_caught{false};
  bool duplicate_open=false,snapshot_fault=false;
  unsigned world_reads=0,tls_reads=0,native_reads=0,clock_reads=0,closes=0,pauses=0;
  static constexpr std::uintptr_t native_handle=0x1501,owned_handle=0x1502;
  explicit Consumer(bool drift,bool after,bool clean=false) {
    active=this;access.drift=drift;access.destroy_before=!drift&&!after&&!clean;access.destroy_after=after;
    access.nested_sentinel=&sentinel;
    access_binding=Bind(access);
    constexpr auto actor_id=std::bit_cast<std::int32_t>(std::uint32_t{0x81000001});
    Put(game,8,std::int32_t{24000});Put(game,0x70,std::int32_t{4});Put(game,0xA0,data.data());
    Put(jomini,0x18,players.data());Put(jomini,0x20,std::uint8_t{1});
    Put(players,0x1F0,std::int32_t{7});Put(player,0x70,std::int32_t{7});
    Put(entry,0xD8,std::int32_t{7});Put(entry,0xB0,actor_id);
    Put(data,kPlayerCharacterManagerOffset+0x58,entries.data());
    Put(data,kPlayerCharacterManagerOffset+0x64,std::int32_t{1});
    Put(storage,0x20,rows.data());Put(storage,0x2C,std::int32_t{4});Put(rows,0x18,actor.data());
    Put(actor,0x18,actor_id);Put(actor,0x1C,std::uint32_t{0x43686172});
    Put(actor,0x1D0,static_cast<void *>(nullptr));Put(tls,0x20,std::uint8_t{1});
    bindings.exact_build_admitted=true;bindings.offline_fixture=true;
    bindings.core={true,&game_slot,&jomini_slot,&storage_slot,&Local};bindings.set_paused=&Pause;
    bindings.command_manager=reinterpret_cast<std::uintptr_t>(&manager_token);bindings.worker_function=0x1210F000;
    bindings.clock_context=this;bindings.utc_now=&Wall;bindings.monotonic_now=&Mono;
    bindings.worker_fixture={this,&Snapshot,&Duplicate,&Probe,&Scope,&Close,nullptr,&Access};
    mailbox.state.store(old::MainThreadQueryMailboxStateV1::idle);
    mailbox.owner_thread_id.store(GetCurrentThreadId());mailbox.owner_verified_pump_epochs.store(2);
    mailbox.offline_fixture=true;mailbox.tls_initialized_flag=reinterpret_cast<std::uintptr_t>(&initialized);
    mailbox.tls_context_getter=&Tls;
    Check(InitializeDateSentinelV1(sentinel,bindings,mailbox),"typed-only NoGame fixture initializes");
    worker=std::thread([this] {
      worker_id.store(GetCurrentThreadId(),std::memory_order_release);
      while(!go.load(std::memory_order_acquire))std::this_thread::yield();
      InvokePostForFixture(this);done.store(true,std::memory_order_release);
      while(!worker_exit.load(std::memory_order_acquire))std::this_thread::yield();
    });
    while(!worker_id.load(std::memory_order_acquire))std::this_thread::yield();
    Check(worker_id.load()!=GetCurrentThreadId(),"UI owner and actual worker remain separate threads");
    native={bindings.command_manager,bindings.worker_function,bindings.command_manager,
      reinterpret_cast<std::uintptr_t>(&holder_token),native_handle,worker_id.load(),1,0};
  }
  ~Consumer(){worker_exit.store(true,std::memory_order_release);worker.join();}
  static bool Snapshot(void *p,DateSentinelWorkerNativeV1 &out) noexcept {
    auto &f=*static_cast<Consumer *>(p);++f.native_reads;
    if(f.snapshot_fault)RaiseException(0xE0150006,0,0,nullptr);
    out=f.native;return true;
  }
  static bool Duplicate(void *p,std::uintptr_t handle,std::uintptr_t &out) noexcept {
    auto &f=*static_cast<Consumer *>(p);++f.native_reads;
    if(handle!=native_handle)return false;out=owned_handle;f.duplicate_open=true;return true;
  }
  static bool Probe(void *p,std::uintptr_t h,std::uint32_t &id,std::uint64_t &birth,bool &live,bool &process) noexcept {
    auto &f=*static_cast<Consumer *>(p);++f.native_reads;
    if(h!=native_handle && !(h==owned_handle&&f.duplicate_open))return false;
    id=f.worker_id.load();birth=123456789;live=!f.worker_exit.load();process=true;return true;
  }
  static bool Scope(void *p,std::uint32_t &id,std::uint8_t &init,std::uint32_t &scope,std::uint8_t &access) noexcept {
    auto &f=*static_cast<Consumer *>(p);++f.native_reads;id=GetCurrentThreadId();
    init=1;scope=f.access.state.command_scope;access=f.access.state.native_access;return true;
  }
  static bool Close(void *p,std::uintptr_t h) noexcept {
    auto &f=*static_cast<Consumer *>(p);++f.closes;
    if(h!=owned_handle)return false;f.duplicate_open=false;return true;
  }
  static DateWorkerGameAccessResultV2 Access(void *p,DateSentinelGameBodyV1 body,void *context) noexcept {
    auto &f=*static_cast<Consumer *>(p);return WithDateWorkerGameAccessV2(&f.access_binding,body,context);
  }
  static std::uint64_t Wall(void *p) noexcept {++static_cast<Consumer *>(p)->clock_reads;return 1000000;}
  static std::uint64_t Mono(void *p) noexcept {++static_cast<Consumer *>(p)->clock_reads;return 1000;}
};
void InvokePostForFixture(Consumer *f) noexcept {
#if defined(_MSC_VER)
  __try {PostDateSentinelV1(&f->sentinel);}
  __except(GetExceptionCode()==0xE0150006?EXCEPTION_EXECUTE_HANDLER:EXCEPTION_CONTINUE_SEARCH) {
    f->post_fault_caught.store(true,std::memory_order_release);
  }
#else
  PostDateSentinelV1(&f->sentinel);
#endif
}
void *Local(void *) {++active->world_reads;return active->player.data();}
void *__fastcall Tls() noexcept {++active->tls_reads;return active->tls.data();}
void __fastcall Pause(void *j,bool paused,std::int32_t player) {
  auto &f=*active;
  Check(j==f.jomini.data() && paused && player==7 && GetCurrentThreadId()==f.worker_id.load() &&
      f.access.state.native_access==1,"pause runs only inside proven worker native access");
  ++f.pauses;Put(f.jomini,0x20,std::uint8_t{1});
}
void ConsumerCase(bool drift,bool after) {
  Consumer f(drift,after);
  old::TacticalDailySentinelArmRequestV1 request{};
  request.starting_date_raw=24000;request.target_date_raw=24024;request.speed=5;
  request.mode=old::TacticalDailySentinelModeV1::terminal_or_sentinel;
  Check(ArmDateSentinelV1(f.sentinel,request,1005000)==old::TacticalDailySentinelArmStatusV1::armed,
      "actual UI owner arms typed access consumer");
  const auto generation=f.sentinel.generation.load();
  const auto deadline=f.sentinel.original_deadline_unix_ms;
  Put(f.game,8,std::int32_t{24024});Put(f.jomini,0x20,std::uint8_t{0});
  f.go.store(true,std::memory_order_release);
  const auto until=std::chrono::steady_clock::now()+std::chrono::seconds(3);
  while(!f.done.load(std::memory_order_acquire) && std::chrono::steady_clock::now()<until)std::this_thread::yield();
  Check(f.done.load(std::memory_order_acquire),"bounded worker completion");
  const auto status=ReadDateSentinelStatusV1(f.sentinel);
  const auto diag=ReadDateSentinelDiagnosticsV1(f.sentinel);
  Check(diag.fixture_only && !diag.capability_granted && diag.access_cleanup_unknown &&
      !diag.shutdown_safe && !DateSentinelShutdownSafeV1(f.sentinel) &&
      (diag.failure_flags&date_sentinel_failure_access_cleanup_unknown),
      "typed native UNKNOWN remains visible and cannot acknowledge cleanup");
  Check(status.state==old::TacticalDailySentinelStateV1::failed && status.abnormal &&
      status.generation==generation && status.completed_daily_ticks==(drift?0U:1U) &&
      f.pauses==(drift?0U:1U),"resource failure preserves actual prior evaluator facts without successful publication");
  Check(f.duplicate_open && f.sentinel.worker.owned_handle==Consumer::owned_handle &&
      f.sentinel.post_callbacks.load()==0 && !f.closes && f.access.acquired==1 &&
      f.access.destroyed==(drift?0U:1U),"unknown cleanup retains owned epoch after actual callback rundown");
  const auto world=f.world_reads,tls=f.tls_reads,native=f.native_reads,clock=f.clock_reads;
  const auto acquired=f.access.acquired,destroyed=f.access.destroyed;
  Check(!ReleaseDateSentinelWorkerV1(f.sentinel) &&
      ArmDateSentinelV1(f.sentinel,request,1009000)==old::TacticalDailySentinelArmStatusV1::unavailable &&
      !DateSentinelAllowsResumeV1(f.sentinel,f.sentinel.initial.core) &&
      CancelDateSentinelV1(f.sentinel,generation)==old::TacticalDailySentinelCancelStatusV1::unavailable &&
      !PollDateSentinelOwnerV1(f.sentinel,{}),"unknown native cleanup rejects all new access and duplicate release");
  PostDateSentinelV1(&f.sentinel);RequestDateSentinelShutdownV1(f.sentinel);
  Check(!DateSentinelShutdownSafeV1(f.sentinel) && !ReleaseDateSentinelWorkerV1(f.sentinel) &&
      f.duplicate_open && f.sentinel.worker.owned_handle==Consumer::owned_handle &&
      f.sentinel.original_deadline_unix_ms==deadline && f.sentinel.generation.load()==generation &&
      f.world_reads==world && f.tls_reads==tls && f.native_reads==native && f.clock_reads==clock &&
      f.access.acquired==acquired && f.access.destroyed==destroyed && !f.closes &&
      f.sentinel.post_callbacks.load()==0,
      "sticky UNKNOWN never retries native destroy, refreshes original deadline or invents teardown proof");
}
template<class Predicate> void Wait(Predicate &&ready,const char *why) {
  const auto until=std::chrono::steady_clock::now()+std::chrono::seconds(3);
  while(!ready() && std::chrono::steady_clock::now()<until)std::this_thread::yield();
  Check(ready(),why);
}
old::TacticalDailySentinelArmRequestV1 ArmConsumer(Consumer &f) {
  old::TacticalDailySentinelArmRequestV1 request{};
  request.starting_date_raw=24000;request.target_date_raw=24024;request.speed=5;
  request.mode=old::TacticalDailySentinelModeV1::terminal_or_sentinel;
  Check(ArmDateSentinelV1(f.sentinel,request,1005000)==old::TacticalDailySentinelArmStatusV1::armed,
      "barrier owner ARM");
  return request;
}
void BarrierCase(bool unknown,bool nested) {
  Consumer f(false,false,!unknown);
  const auto request=ArmConsumer(f);const auto generation=f.sentinel.generation.load();
  const auto deadline=f.sentinel.original_deadline_unix_ms;
  f.access.block_destroy.store(true,std::memory_order_release);
  Put(f.game,8,std::int32_t{24024});Put(f.jomini,0x20,std::uint8_t{0});
  f.go.store(true,std::memory_order_release);
  Wait([&]{return f.access.destroy_entered.load(std::memory_order_acquire);},"real body returned into blocked Destroy");
  const auto raw=old::ReadTacticalDailySentinelStatusV1();
  Check(raw.state==old::TacticalDailySentinelStateV1::triggered && raw.pause_observed &&
      !raw.abnormal && raw.completed_daily_ticks==1 && !f.sentinel.pending_failure.load() &&
      !f.sentinel.access_cleanup_unknown.load() && f.sentinel.post_callbacks.load()==1,
      "legacy terminal exists before cleanup proof");
  old::TacticalDailySentinelStatusV1 status{},cancel_status{};
  std::atomic<bool> status_done{false},cancel_done{false};bool cancel_terminal=false;
  std::thread status_reader([&] {
    status=ReadDateSentinelStatusV1(f.sentinel);status_done.store(true,std::memory_order_release);
  });
  std::thread cancel_reader([&] {
    cancel_terminal=ReadDateSentinelTerminalForCancelV1(f.sentinel,generation,cancel_status);
    cancel_done.store(true,std::memory_order_release);
  });
  Wait([&]{return f.sentinel.status_readers_waiting.load(std::memory_order_acquire)==2;},
      "both public readers entered exclusive-acquire API window");
  Check(!status_done.load() && !cancel_done.load() && f.sentinel.post_callbacks.load()==1,
      "no public terminal before cleanup");
  Check(ArmDateSentinelV1(f.sentinel,request,1009000)==old::TacticalDailySentinelArmStatusV1::unavailable &&
      !DateSentinelAllowsResumeV1(f.sentinel,f.sentinel.initial.core) &&
      CancelDateSentinelV1(f.sentinel,generation)==old::TacticalDailySentinelCancelStatusV1::unavailable &&
      !ReleaseDateSentinelWorkerV1(f.sentinel) && !f.sentinel.pending_failure.load() &&
      f.sentinel.generation.load()==generation && f.sentinel.original_deadline_unix_ms==deadline &&
      f.sentinel.post_callbacks.load()==1 && !f.closes && f.access.acquired==1 && !f.access.destroyed,
      "busy mutations neither mutate nor mark failure");
  if(nested) {
    f.access.nested_requested.store(true,std::memory_order_release);
    Wait([&]{return f.access.nested_completed.load(std::memory_order_acquire);},
        "same-worker nested Post returns while readers wait");
    Check(f.sentinel.post_callbacks.load()==1 &&
        (f.sentinel.pending_failure.load()&date_sentinel_failure_sequence) &&
        !status_done.load() && !cancel_done.load(),"nested Post does not reacquire SRW");
  }
  f.access.block_destroy.store(false,std::memory_order_release);
  Wait([&]{return f.done.load(std::memory_order_acquire);},"outer wrapper completes");
  Wait([&]{return status_done.load(std::memory_order_acquire)&&cancel_done.load(std::memory_order_acquire);},
      "readers finish after real rundown");
  status_reader.join();cancel_reader.join();
  const auto expected=(unknown||nested)?old::TacticalDailySentinelStateV1::failed:
      old::TacticalDailySentinelStateV1::triggered;
  Check(status.state==expected && status.abnormal==(unknown||nested) && status.pause_observed &&
      status.completed_daily_ticks==1 && status.generation==generation && cancel_status==status &&
      cancel_terminal==!unknown && f.sentinel.post_callbacks.load()==0 &&
      f.sentinel.status_readers_waiting.load()==0,"Status/CANCEL return real final values");
  Check(f.sentinel.access_cleanup_unknown.load()==unknown &&
      DateSentinelShutdownSafeV1(f.sentinel)==!unknown &&
      f.access.acquired==(nested?2U:1U) && f.access.destroyed==(nested?2U:1U) &&
      f.sentinel.original_deadline_unix_ms==deadline,"resource proof and failure history remain independent");
  Check(ReleaseDateSentinelWorkerV1(f.sentinel)==!unknown &&
      f.duplicate_open==unknown && f.closes==(unknown?0U:1U),
      "duplicate release requires proven completed cleanup");
}
void PostSehCase() {
  Consumer f(false,false,true);ArmConsumer(f);
  const auto generation=f.sentinel.generation.load();f.snapshot_fault=true;
  Put(f.game,8,std::int32_t{24024});Put(f.jomini,0x20,std::uint8_t{0});
  f.go.store(true,std::memory_order_release);
  Wait([&]{return f.done.load(std::memory_order_acquire);},"fixture handles Post SEH");
  const auto status=ReadDateSentinelStatusV1(f.sentinel);
  old::TacticalDailySentinelStatusV1 cancel_status{};
  Check(f.post_fault_caught.load() && f.sentinel.post_callbacks.load()==0 &&
      f.sentinel.status_readers_waiting.load()==0 && f.sentinel.access_cleanup_unknown.load() &&
      status.state==old::TacticalDailySentinelStateV1::failed && status.abnormal &&
      !ReadDateSentinelTerminalForCancelV1(f.sentinel,generation,cancel_status) &&
      !ReleaseDateSentinelWorkerV1(f.sentinel) && !f.closes && !f.access.acquired && !f.access.destroyed,
      "Post SEH balances counter/shared lease and retains UNKNOWN");
}
} // namespace
int main(int argc,char **argv) {
  const bool drift=argc==2 && std::strcmp(argv[1],"application-drift")==0;
  const bool after=argc==2 && std::strcmp(argv[1],"destroy-after")==0;
  const bool barrier_success=argc==2 && std::strcmp(argv[1],"barrier-success")==0;
  const bool barrier_unknown=argc==2 && std::strcmp(argv[1],"barrier-unknown")==0;
  const bool barrier_nested=argc==2 && std::strcmp(argv[1],"barrier-nested")==0;
  const bool post_seh=argc==2 && std::strcmp(argv[1],"post-seh")==0;
  Check(argc==1 || drift || after || barrier_success || barrier_unknown || barrier_nested || post_seh,
      "supported NoGame fault mode");
  PairCases();
  if(barrier_success || barrier_unknown || barrier_nested)BarrierCase(barrier_unknown,barrier_nested);
  else if(post_seh)PostSehCase();
  else ConsumerCase(drift,after);
  std::printf("PASS typed Worker15 NoGame resource outcomes and sticky consumer retention\n");
  return 0;
}
