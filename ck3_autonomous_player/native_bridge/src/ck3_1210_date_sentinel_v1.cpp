#include "xar_bridge/ck3_121003_ccc_date_proof26785313_v1.hpp"
#include "xar_bridge/date_worker_access_layout131.hpp"
#include "xar_bridge/ck3_121003_full111_pins.hpp"
#include "xar_bridge/ck3_1210_hotfix26757580_v1.hpp"
#include "xar_bridge/ck3_1210_date_sentinel_v1.hpp"
#include "xar_bridge/ck3_121003_ted_date_proof26785313_v1.hpp"
#if defined(XAR_CK3_ENABLE_121003_26785313_DATE_POSTDAY_BINDINGS_V1) && XAR_CK3_ENABLE_121003_26785313_DATE_POSTDAY_BINDINGS_V1
#include "xar_bridge/ck3_121003_date_postday26785313_v1.hpp"
#include "xar_bridge/ck3_121003_readonly26785313_v1.hpp"
#endif
#include <array>
#include <cstring>
#include <limits>
#if defined(_MSC_VER) && defined(_M_X64)
#include <intrin.h>
#endif
namespace xar::ck3_1210 {
namespace {
namespace old=ck3_11906;
namespace current=ck3_121003::build26785313;
bool ProductionGuard(const DateSentinelBindingsV1 &) noexcept;
bool IsCurrent(const DateSentinelBindingsV1 &b) noexcept {
  return b.runtime_profile==DateSentinelRuntimeProfileV1::current26785313;
}
std::uintptr_t TlsFlagRva(const DateSentinelBindingsV1 &b) noexcept {
  return IsCurrent(b)?0x695940C:ImageRva(b.core.image_build,0x695910C,hotfix26757580::kTlsFlag);
}
std::uintptr_t TlsGetterRva(const DateSentinelBindingsV1 &b) noexcept {
  return IsCurrent(b)?0x44FED60:ImageRva(b.core.image_build,0x44FEA30,hotfix26757580::kTlsGetter);
}
std::size_t AccessOffset(const DateSentinelBindingsV1 &b) noexcept {
  return IsCurrent(b)||IsFull111(b.core.image_build)?0x6E8:0x6E0;
}
using Arm=old::TacticalDailySentinelArmStatusV1;
using Cancel=old::TacticalDailySentinelCancelStatusV1;
using Phase=old::TacticalDailySentinelStateV1;
std::atomic<DateSentinelStateV1 *> g_runtime{nullptr};
// Private source-bound extension: original State/header/layout and Identity are unchanged.
struct TedFixedCapture267V1 {
 const DateSentinelStateV1*runtime=nullptr;
 bool active=false;
 TedFixedDayStage267V1 stage=TedFixedDayStage267V1::song_transition;FixedDayFamily267V1 family=FixedDayFamily267V1::ted;
 std::uint64_t generation=0;
 TedFixedDayProof267V1 proof{};
};
TedFixedCapture267V1 g_ted_fixed;

constexpr std::uintptr_t kPauseRva=0x3E65500;
constexpr std::array<unsigned char,32> kPauseEntry{
  0x48,0x89,0x5c,0x24,0x08,0x57,0x48,0x83,0xec,0x20,0x41,0x8b,0xf8,0x48,0x8b,0xd9,
  0x38,0x51,0x20,0x74,0x69,0x84,0xd2,0x74,0x1b,0xb2,0x01,0xe8,0x20,0xff,0xff,0xff};
template<class F> bool Fault(F &&f) noexcept {
#if defined(_MSC_VER)
  __try{return f();}__except(EXCEPTION_EXECUTE_HANDLER){return false;}
#else
  return f();
#endif
}
template<class T> T At(const void *p,std::size_t n) noexcept {
  T v{};std::memcpy(&v,static_cast<const std::byte *>(p)+n,sizeof(v));return v;
}
constexpr std::uintptr_t kManagerRva=0x69DA8A0,kWorkerRva=0x3E1CD90;
struct WorkerMutationLock {
  DateSentinelStateV1 &s;bool acquired=false;
  explicit WorkerMutationLock(DateSentinelStateV1 &v) noexcept:s(v),
      acquired(TryAcquireSRWLockExclusive(&s.worker_lifetime_lock)!=FALSE){}
  ~WorkerMutationLock(){if(acquired)ReleaseSRWLockExclusive(&s.worker_lifetime_lock);}
};
void AcquireWorkerStatusLock(const DateSentinelStateV1 &s) noexcept {
  // Diagnostic API-entry window, not a kernel waiter count or permission.
  s.status_readers_waiting.fetch_add(1,std::memory_order_acq_rel);
#if defined(_MSC_VER)
  __try {AcquireSRWLockExclusive(&s.worker_lifetime_lock);}
  __finally {s.status_readers_waiting.fetch_sub(1,std::memory_order_acq_rel);}
#else
  AcquireSRWLockExclusive(&s.worker_lifetime_lock);
  s.status_readers_waiting.fetch_sub(1,std::memory_order_acq_rel);
#endif
}
struct WorkerStatusLock {
  const DateSentinelStateV1 &s;
  explicit WorkerStatusLock(const DateSentinelStateV1 &v) noexcept:s(v) {
    AcquireWorkerStatusLock(s);
  }
  ~WorkerStatusLock(){ReleaseSRWLockExclusive(&s.worker_lifetime_lock);}
};
bool EnterPostCallback(DateSentinelStateV1 &s) noexcept {
  // A real overlapping/nested post is unsupported. In particular it must not
  // recursively acquire SRW shared while a status writer is waiting.
  if(s.post_callbacks.load(std::memory_order_acquire)!=0) {
    s.pending_failure.fetch_or(date_sentinel_failure_sequence,std::memory_order_acq_rel);return false;
  }
  AcquireSRWLockShared(&s.worker_lifetime_lock);
  // No engine/native setter is called between acquiring the gate and CAS.
  std::uint32_t empty=0;
  if(!s.post_callbacks.compare_exchange_strong(empty,1,std::memory_order_acq_rel,std::memory_order_acquire)) {
    ReleaseSRWLockShared(&s.worker_lifetime_lock);
    s.pending_failure.fetch_or(date_sentinel_failure_sequence,std::memory_order_acq_rel);return false;
  }
  return true;
}
void LeavePostCallback(DateSentinelStateV1 &s) noexcept {
  s.post_callbacks.fetch_sub(1,std::memory_order_acq_rel);
  ReleaseSRWLockShared(&s.worker_lifetime_lock);
}
bool AnyFixture(const DateSentinelWorkerFixtureV1 &f) noexcept {
  return f.context || f.snapshot || f.duplicate || f.probe || f.scope || f.close || f.with_game_access || f.with_game_access_v2;
}
bool CompleteFixture(const DateSentinelWorkerFixtureV1 &f) noexcept {
  return f.context && f.snapshot && f.duplicate && f.probe && f.scope && f.close && (f.with_game_access || f.with_game_access_v2);
}
bool NativeWorker(const DateSentinelStateV1 &s,DateSentinelWorkerNativeV1 &n) noexcept {
  n={};const auto &b=s.bindings;
  if(s.fixture_only)return b.worker_fixture.snapshot(b.worker_fixture.context,n);
  return Fault([&]() noexcept {
    n.manager=b.command_manager;if(!n.manager)return false;
    const auto *m=reinterpret_cast<const void *>(n.manager);
    n.started=At<std::uint8_t>(m,0x3F0);n.stop=At<std::uint8_t>(m,0xC8);
    if(n.started!=1 || n.stop!=0)return false; // Before touching a possibly freed holder.
    n.function=At<std::uintptr_t>(m,0xB8);n.context=At<std::uintptr_t>(m,0xC0);
    n.holder=At<std::uintptr_t>(m,0xD0);
    if(!n.holder || n.holder%8)return false;
    n.native_handle=At<std::uintptr_t>(reinterpret_cast<const void *>(n.holder),0);
    n.thread_id=At<std::uint32_t>(reinterpret_cast<const void *>(n.holder),8);return true;
  });
}
bool NativeFields(const DateSentinelStateV1 &s,const DateSentinelWorkerNativeV1 &n) noexcept {
  return n.manager==s.bindings.command_manager && n.function==s.bindings.worker_function &&
    n.context==n.manager && n.manager && n.started==1 && n.stop==0 && n.holder &&
    n.holder%8==0 && n.native_handle && n.native_handle!=(std::numeric_limits<std::uintptr_t>::max)() && n.thread_id;
}
bool ProbeThread(const DateSentinelStateV1 &s,std::uintptr_t handle,std::uint32_t &id,
    std::uint64_t &birth,bool &live,bool &same_process) noexcept {
  id=0;birth=0;live=false;same_process=false;
  if(!handle)return false;
  if(s.fixture_only)return s.bindings.worker_fixture.probe(s.bindings.worker_fixture.context,handle,id,birth,live,same_process);
  const auto h=reinterpret_cast<HANDLE>(handle);FILETIME creation{},exit_time{},kernel_time{},user_time{};
  id=GetThreadId(h);const auto process=GetProcessIdOfThread(h);
  if(!id || !process || !GetThreadTimes(h,&creation,&exit_time,&kernel_time,&user_time))return false;
  birth=(std::uint64_t{creation.dwHighDateTime}<<32)|creation.dwLowDateTime;
  DWORD code=0;if(!GetExitCodeThread(h,&code))return false;
  live=code==STILL_ACTIVE && WaitForSingleObject(h,0)==WAIT_TIMEOUT;
  same_process=process==GetCurrentProcessId();return true;
}
bool DuplicateThread(const DateSentinelStateV1 &s,std::uintptr_t native,std::uintptr_t &owned) noexcept {
  owned=0;if(s.fixture_only)return s.bindings.worker_fixture.duplicate(s.bindings.worker_fixture.context,native,owned);
  HANDLE duplicate=nullptr;const auto process=GetCurrentProcess();
  if(!DuplicateHandle(process,reinterpret_cast<HANDLE>(native),process,&duplicate,0,FALSE,DUPLICATE_SAME_ACCESS))return false;
  owned=reinterpret_cast<std::uintptr_t>(duplicate);return true;
}
bool CloseThread(const DateSentinelStateV1 &s,std::uintptr_t owned) noexcept {
  if(!owned)return true;
  if(s.fixture_only)return s.bindings.worker_fixture.close(s.bindings.worker_fixture.context,owned);
  return CloseHandle(reinterpret_cast<HANDLE>(owned))!=FALSE;
}
bool CloseWorker(DateSentinelStateV1 &s) noexcept {
  if(s.access_cleanup_unknown.load(std::memory_order_seq_cst))return false;
  if(!s.shutdown_safe.load(std::memory_order_seq_cst) || s.post_callbacks.load(std::memory_order_acquire))return false;
  if(s.worker.owned_handle==s.worker.native.native_handle && s.worker.owned_handle)return false;
  if(!CloseThread(s,s.worker.owned_handle))return false;
  s.worker={};s.captured_worker_thread_id.store(0,std::memory_order_release);return true;
}
bool HandleMatches(const DateSentinelStateV1 &s,std::uintptr_t h,std::uint32_t id,std::uint64_t birth) noexcept {
  std::uint32_t actual=0;std::uint64_t created=0;bool live=false,process=false;
  return ProbeThread(s,h,actual,created,live,process) && actual==id && created==birth && birth && live && process;
}
bool CaptureWorker(DateSentinelStateV1 &s) noexcept {
  DateSentinelWorkerNativeV1 before{},after{};
  if(!NativeWorker(s,before) || !NativeFields(s,before))return false;
  std::uintptr_t owned=0;
  if(!DuplicateThread(s,before.native_handle,owned) || !owned || owned==before.native_handle)return false;
  std::uint32_t id=0;std::uint64_t birth=0;bool live=false,process=false;
  const bool good=ProbeThread(s,owned,id,birth,live,process) && id==before.thread_id && birth && live && process &&
    HandleMatches(s,before.native_handle,id,birth) && NativeWorker(s,after) && NativeFields(s,after) &&
    after==before && HandleMatches(s,owned,id,birth);
  if(!good) {
    if(!CloseThread(s,owned))s.worker={before,owned,birth}; // Bounded retained resource, never permission.
    return false;
  }
  s.worker={before,owned,birth};s.captured_worker_thread_id.store(id,std::memory_order_release);return true;
}
bool CommandScope(const DateSentinelStateV1 &s,std::uint32_t &id,std::uint8_t &initialized,std::uint32_t &scope,std::uint8_t &access) noexcept {
  id=GetCurrentThreadId();initialized=0;scope=0;access=0;
  if(s.fixture_only)return s.bindings.worker_fixture.scope(s.bindings.worker_fixture.context,id,initialized,scope,access);
#if defined(_MSC_VER) && defined(_M_X64)
  return Fault([&]() noexcept {
    initialized=*reinterpret_cast<const std::uint8_t *>(s.bindings.module_base+TlsFlagRva(s.bindings));
    const auto vector=__readgsqword(0x58);if(!vector)return false;
    const auto block=At<std::uintptr_t>(reinterpret_cast<const void *>(vector),0);
    if(!block || block>(std::numeric_limits<std::uintptr_t>::max)()-(AccessOffset(s.bindings)+1))return false;
    scope=At<std::uint32_t>(reinterpret_cast<const void *>(block),0x140);
    access=IsCurrent(s.bindings)
        ?At<std::uint8_t>(reinterpret_cast<const void *>(block),AccessOffset(s.bindings))
        :ReadDateWorkerAccessByte131(reinterpret_cast<const void *>(block),s.bindings.core.image_build);return true;
  });
#else
  return false;
#endif
}
std::uint32_t WorkerOwnerUnlocked(const DateSentinelStateV1 &s,bool require_command_scope=true) noexcept {
  const auto &e=s.worker;
  if(!e.owned_handle || !e.creation_time || !NativeFields(s,e.native))return date_sentinel_failure_owner;
  // Check the owned epoch before touching a native holder that Stop can free.
  if(require_command_scope && GetCurrentThreadId()!=e.native.thread_id)return date_sentinel_failure_owner;
  if(!HandleMatches(s,e.owned_handle,e.native.thread_id,e.creation_time))return date_sentinel_failure_owner;
  if(require_command_scope) {
    std::uint32_t id=0,scope=0;std::uint8_t initialized=0,access=0;
    if(!CommandScope(s,id,initialized,scope,access) || id!=GetCurrentThreadId() || id!=e.native.thread_id ||
        initialized!=1 || scope!=1)return date_sentinel_failure_tls;
  }
  DateSentinelWorkerNativeV1 before{},after{};
  if(!NativeWorker(s,before) || !NativeFields(s,before) || before!=e.native ||
      !HandleMatches(s,before.native_handle,before.thread_id,e.creation_time) ||
      !NativeWorker(s,after) || after!=before || !NativeFields(s,after) ||
      !HandleMatches(s,e.owned_handle,e.native.thread_id,e.creation_time))return date_sentinel_failure_owner;
  return 0;
}

bool WorkerAccessConfigured(const DateSentinelStateV1 &s) noexcept {
  if(IsCurrent(s.bindings))return ProductionGuard(s.bindings);
  return s.fixture_only?(s.bindings.worker_fixture.with_game_access_v2 ||
      s.bindings.worker_fixture.with_game_access):(s.bindings.worker_game_access_v2 || s.bindings.worker_game_access);
}
struct GuardedWorkerCall {
  DateSentinelStateV1 &s;DateSentinelGameBodyV1 body;void *context;bool called=false,result=false;
};
bool InvokeGuardedWorkerBody(void *opaque) noexcept {
  auto &c=*static_cast<GuardedWorkerCall *>(opaque);if(c.called)return false;c.called=true;
  if(WorkerOwnerUnlocked(c.s))return false;
  std::uint32_t id=0,scope=0;std::uint8_t initialized=0,access=0;
  if(!CommandScope(c.s,id,initialized,scope,access) || id!=GetCurrentThreadId() ||
      initialized!=1 || scope!=1 || access!=1)return false;
  c.result=c.body(c.context);return c.result;
}
void RetainUnknownWorkerAccess(DateSentinelStateV1 &s) noexcept {
  s.access_cleanup_unknown.store(true,std::memory_order_seq_cst);
  s.shutdown_safe.store(false,std::memory_order_seq_cst);
  s.pending_failure.fetch_or(date_sentinel_failure_runtime|
      date_sentinel_failure_access_cleanup_unknown,std::memory_order_acq_rel);
}
bool WithWorkerAccess(DateSentinelStateV1 &s,DateSentinelGameBodyV1 body,void *context) noexcept {
  if(s.access_cleanup_unknown.load(std::memory_order_seq_cst) || !WorkerAccessConfigured(s))return false;
  GuardedWorkerCall call{s,body,context};
  const auto ctx=s.fixture_only?s.bindings.worker_fixture.context:s.bindings.game_access_context;
  const auto run=s.fixture_only?s.bindings.worker_fixture.with_game_access_v2:s.bindings.worker_game_access_v2;
  if(run) {
    const auto result=run(ctx,&InvokeGuardedWorkerBody,&call);
    if(!result.CleanupKnown()) {
      RetainUnknownWorkerAccess(s);
      return false;
    }
    return !s.access_cleanup_unknown.load(std::memory_order_seq_cst) &&
        result.Succeeded() && call.called && call.result;
  }
  // Retain V1 callers. A production bool failure has no release outcome, so
  // conservatively retain it as UNKNOWN; explicit NoGame V1 seams stay models.
  const auto legacy=s.fixture_only?s.bindings.worker_fixture.with_game_access:s.bindings.worker_game_access;
  const bool result=legacy && legacy(ctx,&InvokeGuardedWorkerBody,&call);
  if(!result && !s.fixture_only) {RetainUnknownWorkerAccess(s);return false;}
  return !s.access_cleanup_unknown.load(std::memory_order_seq_cst) && result && call.called && call.result;
}

template<std::size_t N> constexpr auto Bytes(const char (&text)[N]) noexcept {
  static_assert(N%2==1);std::array<unsigned char,(N-1)/2> bytes{};
  auto nibble=[](char c) constexpr {return c<='9'?c-'0':c-'a'+10;};
  for(std::size_t i=0;i<bytes.size();++i)bytes[i]=static_cast<unsigned char>(nibble(text[i*2])*16+nibble(text[i*2+1]));
  return bytes;
}
constexpr auto kConsumerEntry=Bytes("48895c241855565741564157488bec4881ec800000000f29742470488bf90fb6");
constexpr auto kRunnerEntry=Bytes("48895c241048896c24184889742420574883ec5065488b042558000000488bf2");
constexpr auto kScopeBegin=Bytes("65488b042558000000488bf2bb40010000488be90f297424400f297c2430480318f64208017506c70301000000");
constexpr auto kScopeEnd=Bytes("c70300000000");
std::uint64_t Utc(void *) noexcept {
  FILETIME ft{};GetSystemTimeAsFileTime(&ft);
  const auto ticks=(std::uint64_t{ft.dwHighDateTime}<<32)|ft.dwLowDateTime;
  return ticks>=116444736000000000ULL?(ticks-116444736000000000ULL)/10000:0;
}
std::uint64_t Mono(void *) noexcept{return GetTickCount64();}
std::uint64_t Wall(const DateSentinelStateV1 &s) noexcept {
  return (s.bindings.utc_now?s.bindings.utc_now:Utc)(s.bindings.clock_context);
}
std::uint64_t Clock(const DateSentinelStateV1 &s) noexcept {
  return (s.bindings.monotonic_now?s.bindings.monotonic_now:Mono)(s.bindings.clock_context);
}
bool Equal(const CoreSnapshotPrefix &a,const CoreSnapshotPrefix &b) noexcept {
  return a.clock.date_raw==b.clock.date_raw && a.clock.speed==b.clock.speed &&
    a.clock.paused==b.clock.paused && a.local_player_id==b.local_player_id &&
    a.map_ready==b.map_ready && a.has_played_character==b.has_played_character &&
    a.played_character_id==b.played_character_id && a.played_character_alive==b.played_character_alive;
}
bool Same(const DateSentinelObservationV1 &a,const DateSentinelObservationV1 &b) noexcept {
  return Equal(a.core,b.core) && a.game==b.game && a.jomini==b.jomini &&
    a.storage==b.storage && a.data==b.data && a.players==b.players &&
    a.player==b.player && a.actor==b.actor;
}
bool Read(const DateSentinelStateV1 &s,DateSentinelObservationV1 &o,
    bool failure_pause_world=false) noexcept {
  o={};const auto &b=s.bindings.core;
  return Fault([&]() noexcept {
    if(!b.enabled || !b.game_state_slot || !b.jomini_state_slot || !b.character_storage_slot || !b.get_local_player)return false;
    o.game=*b.game_state_slot;o.jomini=*b.jomini_state_slot;o.storage=*b.character_storage_slot;
    if(!o.game || !o.jomini || !o.storage)return false;
    o.data=At<void *>(o.game,0xA0);o.players=At<void *>(o.jomini,0x18);
    o.player=b.get_local_player(o.jomini);
    if(failure_pause_world) {
      // Failure/Stop may lose its played actor while retaining this actual
      // world and local player. Core must still be fully readable; never turn
      // a fault into an empty/no-actor observation. No actor result is invented.
      if(!o.data || !o.players || !o.player || !ReadCoreSnapshot(b,o.core) ||
          !o.core.map_ready || o.core.local_player_id<0 ||
          At<std::int32_t>(o.player,0x70)!=o.core.local_player_id ||
          b.get_local_player(o.jomini)!=o.player)return false;
    } else {
      if(!o.data || !o.players || !o.player || !ReadCoreSnapshot(b,o.core) ||
          !o.core.map_ready || !o.core.has_played_character || !o.core.played_character_alive ||
          o.core.local_player_id<0 || o.core.played_character_id==-1 ||
          At<std::int32_t>(o.player,0x70)!=o.core.local_player_id)return false;
      o.actor=ResolveCoreCharacter(b,o.core.played_character_id);
      if(!o.actor || At<std::uint32_t>(o.actor,0x1C)!=0x43686172 ||
          At<std::int32_t>(o.actor,0x18)!=o.core.played_character_id)return false;
    }
    return *b.game_state_slot==o.game && *b.jomini_state_slot==o.jomini &&
      *b.character_storage_slot==o.storage && At<void *>(o.game,0xA0)==o.data &&
      At<void *>(o.jomini,0x18)==o.players && At<std::int32_t>(o.game,8)==o.core.clock.date_raw &&
      static_cast<std::int64_t>(At<std::int32_t>(o.game,0x70))+1==o.core.clock.speed &&
      (At<std::uint8_t>(o.jomini,0x20)!=0)==o.core.clock.paused;
  });
}
bool Stable(const DateSentinelStateV1 &s,DateSentinelObservationV1 &o,
    bool failure_pause_world=false) noexcept {
  DateSentinelObservationV1 other{};
  return Read(s,o,failure_pause_world) && Read(s,other,failure_pause_world) && Same(o,other);
}
std::uint32_t Identity(const DateSentinelStateV1 &s,const DateSentinelObservationV1 &o) noexcept {
  const auto &i=s.initial;
  if(o.game!=i.game || o.jomini!=i.jomini || o.storage!=i.storage || o.data!=i.data ||
      o.players!=i.players || o.player!=i.player || o.core.local_player_id!=i.core.local_player_id)
    return date_sentinel_failure_world;
  if(o.actor!=i.actor || o.core.played_character_id!=i.core.played_character_id ||
      !o.core.has_played_character || !o.core.played_character_alive)return date_sentinel_failure_actor;
  if(o.core.clock.speed!=i.core.clock.speed)return date_sentinel_failure_speed;
  return 0;
}
std::uint32_t Owner(const DateSentinelStateV1 &s,std::uintptr_t &context,
    const old::MainThreadExecutionStampV1 *stamp=nullptr) noexcept {
  context=0;if(!s.mailbox)return date_sentinel_failure_owner;
  const auto &m=*s.mailbox;const auto tid=GetCurrentThreadId();
  const auto captured=s.owner_thread_id.load(std::memory_order_acquire);
  const auto phase=m.state.load(std::memory_order_acquire);
  if(!tid || m.owner_thread_id.load(std::memory_order_acquire)!=tid || (captured && captured!=tid) ||
      m.owner_verified_pump_epochs.load(std::memory_order_acquire)<old::kMainThreadQueryMinimumOwnerVerifiedPumpEpochs ||
      m.stop_requested.load(std::memory_order_acquire) || m.failure_flags.load(std::memory_order_acquire) ||
      phase==old::MainThreadQueryMailboxStateV1::detached || phase==old::MainThreadQueryMailboxStateV1::detaching ||
      phase==old::MainThreadQueryMailboxStateV1::infrastructure_failed)return date_sentinel_failure_owner;
  if(!s.fixture_only && (m.offline_fixture || m.module_base!=s.bindings.module_base ||
      m.tls_initialized_flag!=s.bindings.module_base+TlsFlagRva(s.bindings) ||
      reinterpret_cast<std::uintptr_t>(m.tls_context_getter)!=s.bindings.module_base+TlsGetterRva(s.bindings) ||
      m.game_state_slot!=reinterpret_cast<std::uintptr_t>(s.bindings.core.game_state_slot) ||
      m.jomini_state_slot!=reinterpret_cast<std::uintptr_t>(s.bindings.core.jomini_state_slot)))return date_sentinel_failure_owner;
  if(IsCurrent(s.bindings) && !ProductionGuard(s.bindings))return date_sentinel_failure_owner;
#if defined(XAR_CK3_ENABLE_121003_26785313_DATE_POSTDAY_BINDINGS_V1) && XAR_CK3_ENABLE_121003_26785313_DATE_POSTDAY_BINDINGS_V1
  if(IsCurrent(s.bindings) && !Fault([&]() noexcept {
      return s.bindings.current_access_context->hook->callback_context==&s;
    }))return date_sentinel_failure_owner;
#endif
  if(!m.tls_initialized_flag || !m.tls_context_getter || !Fault([&]() noexcept {
      if(*reinterpret_cast<const std::uint8_t *>(m.tls_initialized_flag)!=1)return false;
      if(IsCurrent(s.bindings)) {
#if defined(_MSC_VER) && defined(_M_X64)
        const auto vector=__readgsqword(0x58);if(!vector)return false;
        const auto block=At<std::uintptr_t>(reinterpret_cast<const void *>(vector),0);
        if(!block || (block&7U) || block>(std::numeric_limits<std::uintptr_t>::max)()-0x3649 ||
            (At<std::uint32_t>(reinterpret_cast<const void *>(block),0x3620)&1U)==0)return false;
        // Already-warm embedded context only. Never invoke the lazy getter.
        context=block+0x3628;
#else
        return false;
#endif
      } else context=reinterpret_cast<std::uintptr_t>(m.tls_context_getter());
      return context && At<std::uint8_t>(reinterpret_cast<const void *>(context),0x20)==1;
    }))return date_sentinel_failure_tls;
  if(s.owner_tls_context && (s.armed.load(std::memory_order_acquire) ||
      !s.shutdown_safe.load(std::memory_order_seq_cst)) && context!=s.owner_tls_context)return date_sentinel_failure_tls;
  if(stamp && (!stamp->pump_epoch || stamp->thread_id!=tid || stamp->tls_initialized!=1 ||
      stamp->tls_main_thread_marker!=1 || stamp->tls_context!=context ||
      stamp->tls_initialized_flag_address!=m.tls_initialized_flag))return date_sentinel_failure_owner;
  return 0;
}
bool PauseWorld(const DateSentinelStateV1 &s,const DateSentinelObservationV1 &o) noexcept {
  const auto &i=s.initial;
  return o.game==i.game && o.jomini==i.jomini && o.storage==i.storage && o.data==i.data &&
    o.players==i.players && o.player==i.player && o.core.local_player_id==i.core.local_player_id;
}
bool ConfirmPausedDisarmed(DateSentinelStateV1 &s,bool failure_pause_world=false,bool worker_role=false) noexcept {
  if(s.access_cleanup_unknown.load(std::memory_order_seq_cst))return false;
  std::uintptr_t tls=0;DateSentinelObservationV1 o{};
  const auto role=[&]() noexcept {return worker_role?WorkerOwnerUnlocked(s):Owner(s,tls);};
  if(role() || !Stable(s,o,failure_pause_world) || !PauseWorld(s,o) || !o.core.clock.paused)return false;
  const auto status=old::ReadTacticalDailySentinelStatusV1();
  if(status.generation!=s.generation.load(std::memory_order_acquire) ||
      status.state==Phase::armed || status.state==Phase::unavailable || role())return false;
  s.armed.store(false,std::memory_order_release);
  s.shutdown_safe.store(true,std::memory_order_seq_cst);
  return !s.access_cleanup_unknown.load(std::memory_order_seq_cst);
}
bool Expired(const DateSentinelStateV1 &s) noexcept {
  const auto wall=Wall(s),mono=Clock(s);
  return !s.original_deadline_unix_ms || !s.monotonic_deadline_ms ||
    wall<s.armed_unix_ms || mono<s.armed_monotonic_ms ||
    wall>=s.original_deadline_unix_ms || mono>=s.monotonic_deadline_ms;
}
void Fail(DateSentinelStateV1 &s,std::uint32_t flags) noexcept {
  s.pending_failure.fetch_or(flags,std::memory_order_acq_rel);
}
old::Bindings Legacy(const CoreBindings &c) noexcept {
  old::Bindings b{};b.enabled=c.enabled;b.game_state_slot=c.game_state_slot;
  b.jomini_state_slot=c.jomini_state_slot;b.get_local_player=c.get_local_player;return b;
}
bool ProductionGuard(const DateSentinelBindingsV1 &b) noexcept {
  if(IsCurrent(b)) {
#if defined(XAR_CK3_ENABLE_121003_26785313_DATE_POSTDAY_BINDINGS_V1) && XAR_CK3_ENABLE_121003_26785313_DATE_POSTDAY_BINDINGS_V1
    return Fault([&]() noexcept {
      if(b.offline_fixture || !b.module_base ||
          b.module_base!=reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)) ||
          b.utc_now || b.monotonic_now || b.clock_context || AnyFixture(b.worker_fixture) ||
          b.worker_game_access || b.worker_game_access_v2!=&current::WithCurrentDateWorkerGameAccess267V2 ||
          !b.current_access_context || b.game_access_context!=b.current_access_context)return false;
      const auto &access=*b.current_access_context;
      if(!access.image || !access.hook || access.image->module_base!=b.module_base ||
          access.hook->callback.load(std::memory_order_acquire)!=&PostDateSentinelV1 ||
          !current::VerifyCurrentDatePostdayHookImage267V1(*access.image,*access.hook))return false;
      const auto exact=current::BindReadonlyImage(b.module_base,current::kExecutableSha256);
      return exact.exact_image_admitted && exact.core.enabled &&
          b.core.image_build==ImageBuildV1::unknown && b.core.enabled==exact.core.enabled &&
          b.core.game_state_slot==exact.core.game_state_slot &&
          b.core.jomini_state_slot==exact.core.jomini_state_slot &&
          b.core.character_storage_slot==exact.core.character_storage_slot &&
          b.core.get_local_player==exact.core.get_local_player &&
          b.set_paused==access.image->set_paused &&
          b.command_manager==access.image->command_manager &&
          b.worker_function==access.image->worker_consumer;
    });
#else
    return false;
#endif
  }
  if(b.runtime_profile!=DateSentinelRuntimeProfileV1::legacy_image || b.current_access_context)return false;
  if(!b.module_base || b.module_base>(std::numeric_limits<std::uintptr_t>::max)()-ImageSize(b.core.image_build))return false;
  const auto core=BindCoreImage(b.module_base,ExecutableShaForBuild(b.core.image_build));
  if(b.core.enabled!=core.enabled || b.core.game_state_slot!=core.game_state_slot ||
      b.core.jomini_state_slot!=core.jomini_state_slot || b.core.character_storage_slot!=core.character_storage_slot ||
      b.core.get_local_player!=core.get_local_player ||
      reinterpret_cast<std::uintptr_t>(b.set_paused)!=b.module_base+ImageRva(b.core.image_build,kPauseRva,hotfix26757580::kPause) ||
      b.utc_now || b.monotonic_now || b.clock_context || AnyFixture(b.worker_fixture) ||
      b.command_manager!=b.module_base+ImageRva(b.core.image_build,kManagerRva,hotfix26757580::kManager) || b.worker_function!=b.module_base+ImageRva(b.core.image_build,kWorkerRva,hotfix26757580::kWorker))return false;
  return Fault([&]() noexcept {
    return std::memcmp(reinterpret_cast<const void *>(b.module_base+ImageRva(b.core.image_build,kPauseRva,hotfix26757580::kPause)),(IsFull111(b.core.image_build)?full111_pins::kPauseEntry:kPauseEntry).data(),kPauseEntry.size())==0 &&
      std::memcmp(reinterpret_cast<const void *>(b.module_base+ImageRva(b.core.image_build,kWorkerRva,hotfix26757580::kWorker)),kConsumerEntry.data(),kConsumerEntry.size())==0 &&
      std::memcmp(reinterpret_cast<const void *>(b.module_base+ImageRva(b.core.image_build,0x3E1D180,hotfix26757580::kRunner)),kRunnerEntry.data(),kRunnerEntry.size())==0 &&
      std::memcmp(reinterpret_cast<const void *>(b.module_base+ImageRva(b.core.image_build,0x3E1D194,hotfix26757580::kScopeBegin)),kScopeBegin.data(),kScopeBegin.size())==0 &&
      std::memcmp(reinterpret_cast<const void *>(b.module_base+ImageRva(b.core.image_build,0x3E1D286,hotfix26757580::kScopeEnd)),kScopeEnd.data(),kScopeEnd.size())==0;
  });
}
struct WorkerAbortCall {DateSentinelStateV1 &s;};
bool AbortWorkerBody(void *opaque) noexcept {
  auto &s=static_cast<WorkerAbortCall *>(opaque)->s;
  DateSentinelObservationV1 current{};
  const bool can_pause=Stable(s,current,true) && PauseWorld(s,current);
  std::uint32_t legacy_flags=old::tactical_daily_trigger_evaluation_failure;
  const auto all=s.pending_failure.load(std::memory_order_acquire);
  if(all&(date_sentinel_failure_world|date_sentinel_failure_actor))legacy_flags|=old::tactical_daily_trigger_world_identity_changed;
  if(all&date_sentinel_failure_sequence)legacy_flags|=old::tactical_daily_trigger_date_sequence_failure;
  if(WorkerOwnerUnlocked(s))return false;
  if(!old::AbortTacticalDailySentinelDateOnlyV1(s.generation.load(std::memory_order_acquire),legacy_flags,can_pause))return false;
  s.armed.store(false,std::memory_order_release);return true;
}
void AbortOnWorker(DateSentinelStateV1 &s,std::uint32_t flags) noexcept {
  Fail(s,flags);
  if(s.access_cleanup_unknown.load(std::memory_order_seq_cst))return;
  if(const auto role=WorkerOwnerUnlocked(s)){Fail(s,role);return;}
  WorkerAbortCall call{s};
  if(!WithWorkerAccess(s,&AbortWorkerBody,&call)){Fail(s,date_sentinel_failure_runtime);return;}
  if(!ConfirmPausedDisarmed(s,true,true))Fail(s,date_sentinel_failure_observation);
}
// Called only under the original worker mutation/Post/status lease.
bool TedFixedObservation(const DateSentinelStateV1&s,const DateSentinelObservationV1&o)noexcept {
#if (defined(XAR_CK3_ENABLE_121003_26785313_TED_TRANSITION_V1) && XAR_CK3_ENABLE_121003_26785313_TED_TRANSITION_V1) || (defined(XAR_CK3_ENABLE_121003_26785313_CCC_TRANSITION_V1) && XAR_CK3_ENABLE_121003_26785313_CCC_TRANSITION_V1)
 if(!g_ted_fixed.active||g_ted_fixed.runtime!=&s||!g_ted_fixed.generation||g_ted_fixed.generation!=s.generation.load(std::memory_order_acquire)||g_ted_fixed.proof.captured)return false;
 if(!PauseWorld(s,o)||o.core.clock.speed!=s.initial.core.clock.speed||!o.actor||!o.core.has_played_character||!o.core.played_character_alive||o.core.played_character_id==-1||static_cast<std::int64_t>(s.initial.core.clock.date_raw)+24!=o.core.clock.date_raw)return false;
 const auto identity=Identity(s,o);
 return identity==0||(identity==date_sentinel_failure_actor&&g_ted_fixed.stage==TedFixedDayStage267V1::song_transition&&o.actor!=s.initial.actor&&o.core.played_character_id!=s.initial.core.played_character_id);
#else
 (void)s;(void)o;return false;
#endif
}
bool SameAfterPause(DateSentinelObservationV1 a,DateSentinelObservationV1 b)noexcept {
 a.core.clock.paused=b.core.clock.paused;return Same(a,b);
}
bool CaptureTedFixedProof(DateSentinelStateV1&s,const DateSentinelObservationV1&before,const DateSentinelObservationV1&after,const old::TacticalDailySentinelStatusV1&status)noexcept {
 if(!TedFixedObservation(s,before)||!TedFixedObservation(s,after)||!SameAfterPause(before,after)||!after.core.clock.paused||Expired(s)||s.armed.load(std::memory_order_acquire)||!s.shutdown_safe.load(std::memory_order_seq_cst)||s.access_cleanup_unknown.load(std::memory_order_seq_cst)||s.pending_failure.load(std::memory_order_acquire)||WorkerOwnerUnlocked(s))return false;
 if(status.generation!=g_ted_fixed.generation||status.state!=Phase::triggered||!status.pause_observed||status.completed_daily_ticks!=1||status.trigger_flags!=old::tactical_daily_trigger_date_deadline||status.last_observed_date_raw!=status.target_date_raw||status.trigger_date_raw!=status.target_date_raw||status.overshoot_days||static_cast<std::int64_t>(s.initial.core.clock.date_raw)+24!=status.target_date_raw)return false;
 DateSentinelObservationV1 final{};if(!Stable(s,final)||!Same(after,final)||!TedFixedObservation(s,final)||Expired(s)||WorkerOwnerUnlocked(s))return false;
 TedFixedDayProof267V1 proof;proof.captured=true;proof.actor_changed=final.actor!=s.initial.actor;proof.stage=g_ted_fixed.stage;proof.family=g_ted_fixed.family;proof.before=s.initial;proof.after=final;proof.worker=s.worker;proof.generation=status.generation;proof.original_deadline_unix_ms=s.original_deadline_unix_ms;proof.monotonic_deadline_ms=s.monotonic_deadline_ms;proof.captured_unix_ms=Wall(s);proof.captured_monotonic_ms=Clock(s);proof.status=status;
 if(proof.captured_unix_ms>=proof.original_deadline_unix_ms||proof.captured_monotonic_ms>=proof.monotonic_deadline_ms)return false;
 g_ted_fixed.proof=proof;return true;
}
struct WorkerEvaluateCall {DateSentinelStateV1 &s;const DateSentinelObservationV1 &expected;};
bool EvaluateWorkerBody(void *opaque) noexcept {
  auto &call=*static_cast<WorkerEvaluateCall *>(opaque);auto &s=call.s;
  DateSentinelObservationV1 current{};
  if(Expired(s) || s.shutdown_requested.load(std::memory_order_seq_cst) ||
      s.pending_failure.load(std::memory_order_acquire) || !Stable(s,current) ||
      !Same(current,call.expected) || (Identity(s,current)&&!TedFixedObservation(s,current)) || WorkerOwnerUnlocked(s))return false;
  const auto status=old::ReadTacticalDailySentinelStatusV1();
  if(status.state!=Phase::armed || status.generation!=s.generation.load(std::memory_order_acquire))return false;
  // Sole evaluator call; guarded body required actual profile-specific access=1.
  old::ProcessTacticalDailySentinelAfterTickV1();return true;
}
} // namespace
DateSentinelBindingsV1 BindDateSentinelImageV1(std::uintptr_t base,std::string_view sha) noexcept {
  DateSentinelBindingsV1 b{};
  b.core.image_build=BasicFullImageBuildForSha(sha);
  if(!base || b.core.image_build==ImageBuildV1::unknown || base>(std::numeric_limits<std::uintptr_t>::max)()-ImageSize(b.core.image_build))return b;
  b.exact_build_admitted=true;b.module_base=base;b.core=BindCoreImage(base,sha);
  b.set_paused=reinterpret_cast<old::TacticalSetPausedV1>(base+ImageRva(b.core.image_build,kPauseRva,hotfix26757580::kPause));
  b.command_manager=base+ImageRva(b.core.image_build,kManagerRva,hotfix26757580::kManager);b.worker_function=base+ImageRva(b.core.image_build,kWorkerRva,hotfix26757580::kWorker);return b;
}
DateSentinelBindingsV1 BindCurrentDateRuntime267V1(DateSentinelStateV1 &s,
    current::DateWorkerAccessContext267V1 &access) noexcept {
  DateSentinelBindingsV1 b{};
#if defined(XAR_CK3_ENABLE_121003_26785313_DATE_POSTDAY_BINDINGS_V1) && XAR_CK3_ENABLE_121003_26785313_DATE_POSTDAY_BINDINGS_V1
  if(!Fault([&]() noexcept {
      if(!access.image || !access.hook || access.hook->callback_context!=&s)return false;
      b.module_base=access.image->module_base;
      b.core=current::BindReadonlyImage(b.module_base,current::kExecutableSha256).core;
      b.set_paused=access.image->set_paused;b.command_manager=access.image->command_manager;
      b.worker_function=access.image->worker_consumer;b.game_access_context=&access;
      b.worker_game_access_v2=&current::WithCurrentDateWorkerGameAccess267V2;
      b.current_access_context=&access;b.runtime_profile=DateSentinelRuntimeProfileV1::current26785313;
      b.exact_build_admitted=ProductionGuard(b);return b.exact_build_admitted;
    }))return {};
#else
  (void)s;(void)access;
#endif
  return b;
}
bool InitializeDateSentinelV1(DateSentinelStateV1 &s,const DateSentinelBindingsV1 &b,
    old::MainThreadQueryMailboxV1 &m) noexcept {
  if(s.initialized.load(std::memory_order_acquire) || !b.exact_build_admitted ||
      !b.core.enabled || !b.core.game_state_slot || !b.core.jomini_state_slot ||
      !b.core.character_storage_slot || !b.core.get_local_player || !b.set_paused ||
      !b.command_manager || !b.worker_function ||
      (b.offline_fixture && (b.module_base!=0 || !CompleteFixture(b.worker_fixture) || b.worker_game_access || b.worker_game_access_v2 || b.game_access_context)) ||
      (!b.offline_fixture && !ProductionGuard(b)))return false;
  if(IsCurrent(b)) {
#if defined(XAR_CK3_ENABLE_121003_26785313_DATE_POSTDAY_BINDINGS_V1) && XAR_CK3_ENABLE_121003_26785313_DATE_POSTDAY_BINDINGS_V1
    if(!Fault([&]() noexcept {return b.current_access_context->hook->callback_context==&s;}))return false;
#else
    return false;
#endif
  } else if(b.runtime_profile!=DateSentinelRuntimeProfileV1::legacy_image || b.current_access_context)return false;
  DateSentinelStateV1 *empty=nullptr;
  if(!g_runtime.compare_exchange_strong(empty,&s,std::memory_order_acq_rel))return false;
  if(!old::InitializeTacticalDailySentinelDateOnlyV1(Legacy(b.core),b.set_paused)) {
    g_runtime.store(nullptr,std::memory_order_release);return false;
  }
  s.bindings=b;s.mailbox=&m;s.fixture_only=b.offline_fixture;
  s.initialized.store(true,std::memory_order_release);return true;
}
static Arm ArmDateSentinelImplV1(DateSentinelStateV1 &s,const old::TacticalDailySentinelArmRequestV1 &r,
    std::uint64_t deadline,const TedFixedDayStage267V1*fixed,FixedDayFamily267V1 family=FixedDayFamily267V1::ted) noexcept {
  if(!s.initialized.load(std::memory_order_acquire) || g_runtime.load(std::memory_order_acquire)!=&s)return Arm::unavailable;
  if(s.access_cleanup_unknown.load(std::memory_order_seq_cst) ||
      s.shutdown_requested.load(std::memory_order_seq_cst) || !WorkerAccessConfigured(s))return Arm::unavailable;
  std::uintptr_t tls=0;if(Owner(s,tls))return Arm::unavailable;
  WorkerMutationLock lifetime(s);
  if(!lifetime.acquired)return Arm::unavailable;
  if(s.post_callbacks.load(std::memory_order_acquire))return Arm::unavailable;
  if(s.armed.load(std::memory_order_acquire))return Arm::already_armed;
  if(!s.shutdown_safe.load(std::memory_order_seq_cst))return Arm::unavailable;
  if(r.mode!=old::TacticalDailySentinelModeV1::terminal_or_sentinel || r.army_count!=0 ||
      r.speed<1 || r.speed>5 || r.starting_date_raw<=0 || r.target_date_raw<=r.starting_date_raw ||
      (static_cast<std::int64_t>(r.target_date_raw)-r.starting_date_raw)%24!=0)return Arm::invalid_request;
  const auto wall=Wall(s),mono=Clock(s);
  if(deadline<=wall || deadline-wall>(std::numeric_limits<std::uint64_t>::max)()-mono)return Arm::invalid_request;
  DateSentinelObservationV1 o{};
  if(!Stable(s,o))return Arm::unavailable;
  if(!o.core.clock.paused)return Arm::requires_paused;
  if(o.core.clock.date_raw!=r.starting_date_raw)return Arm::starting_date_mismatch;
  if(o.core.clock.speed!=r.speed)return Arm::invalid_request;
  const auto prior=old::ReadTacticalDailySentinelStatusV1();
  if(prior.state==Phase::armed)return Arm::already_armed;
  if(!CloseWorker(s))return Arm::unavailable;
  bool safe=true;
  if(!s.shutdown_safe.compare_exchange_strong(safe,false,std::memory_order_seq_cst))return Arm::unavailable;
  // This total-order handoff prevents a new native arm after Stop observed safe.
  if(s.shutdown_requested.load(std::memory_order_seq_cst)) {
    s.shutdown_safe.store(true,std::memory_order_seq_cst);return Arm::unavailable;
  }
  s.initial=o;s.original_deadline_unix_ms=deadline;s.monotonic_deadline_ms=mono+(deadline-wall);
  // Captured before this new ARM only. Old arms erase availability, never inherit a proof.
  g_ted_fixed={};
#if (defined(XAR_CK3_ENABLE_121003_26785313_TED_TRANSITION_V1) && XAR_CK3_ENABLE_121003_26785313_TED_TRANSITION_V1) || (defined(XAR_CK3_ENABLE_121003_26785313_CCC_TRANSITION_V1) && XAR_CK3_ENABLE_121003_26785313_CCC_TRANSITION_V1)
  if(fixed){g_ted_fixed.runtime=&s;g_ted_fixed.active=true;g_ted_fixed.stage=*fixed;g_ted_fixed.family=family;}
#else
  (void)fixed;
#endif
  s.armed_unix_ms=wall;s.armed_monotonic_ms=mono;s.owner_tls_context=tls;
  s.owner_thread_id.store(GetCurrentThreadId(),std::memory_order_release);
  // Preserve the attempted paused world even if shared arming fails before its
  // first generation; a restored owner can then confirm disarmed + paused.
  s.generation.store(prior.generation,std::memory_order_release);
  const bool worker_captured=CaptureWorker(s);
  if(!worker_captured)Fail(s,date_sentinel_failure_owner);
  const auto result=worker_captured?old::ArmTacticalDailySentinelV1(r):Arm::unavailable;
  if(result!=Arm::armed) {
    DateSentinelObservationV1 rejected{};
    const auto status=old::ReadTacticalDailySentinelStatusV1();
    if(status.state!=Phase::armed && !Owner(s,tls) && Stable(s,rejected) &&
        Same(o,rejected) && rejected.core.clock.paused && !Owner(s,tls))
      s.shutdown_safe.store(true,std::memory_order_seq_cst);
    else Fail(s,date_sentinel_failure_runtime);
    return result;
  }
  s.generation.store(old::ReadTacticalDailySentinelStatusV1().generation,std::memory_order_release);
  if(g_ted_fixed.active&&g_ted_fixed.runtime==&s)g_ted_fixed.generation=s.generation.load(std::memory_order_acquire);
  // Retire prior recoverable failures without ever erasing a racing Stop bit.
  s.pending_failure.fetch_and(date_sentinel_failure_shutdown,std::memory_order_acq_rel);
  s.last_post_thread_id.store(0,std::memory_order_relaxed);
  s.last_post_stage.store(0,std::memory_order_relaxed);
  s.last_post_date_raw.store(0,std::memory_order_relaxed);
  s.armed.store(true,std::memory_order_release);
  if(s.shutdown_requested.load(std::memory_order_seq_cst))Fail(s,date_sentinel_failure_shutdown);
  DateSentinelObservationV1 after{};
  if(!Stable(s,after) || !Same(o,after))Fail(s,date_sentinel_failure_observation);
  if(Expired(s))Fail(s,date_sentinel_failure_expired);
  if(const auto again=Owner(s,tls))Fail(s,again);
  if(const auto worker=WorkerOwnerUnlocked(s,false))Fail(s,worker);
  return s.pending_failure.load(std::memory_order_acquire)?Arm::unavailable:Arm::armed;
}
Arm ArmDateSentinelV1(DateSentinelStateV1&s,const old::TacticalDailySentinelArmRequestV1&r,std::uint64_t deadline)noexcept {
 return ArmDateSentinelImplV1(s,r,deadline,nullptr);
}
Arm ArmTedFixedDay267V1(DateSentinelStateV1&s,const old::TacticalDailySentinelArmRequestV1&r,std::uint64_t deadline,TedFixedDayStage267V1 stage)noexcept {
#if defined(XAR_CK3_ENABLE_121003_26785313_TED_TRANSITION_V1) && XAR_CK3_ENABLE_121003_26785313_TED_TRANSITION_V1
 if(static_cast<unsigned>(stage)>1||static_cast<std::int64_t>(r.starting_date_raw)+24!=r.target_date_raw)return Arm::invalid_request;
 if(!s.fixture_only&&!IsCurrent(s.bindings))return Arm::unavailable;
 return ArmDateSentinelImplV1(s,r,deadline,&stage);
#else
 (void)s;(void)r;(void)deadline;(void)stage;return Arm::unavailable;
#endif
}
bool ReadTedFixedDayProof267V1(const DateSentinelStateV1&s,std::uint64_t generation,TedFixedDayProof267V1&out,old::TacticalDailySentinelStatusV1&status)noexcept {
 out={};WorkerStatusLock lifetime(s);status=old::ReadTacticalDailySentinelStatusV1();
 if(status.generation!=s.generation.load(std::memory_order_acquire))return false;
 if(s.pending_failure.load(std::memory_order_acquire)){status.state=Phase::failed;status.abnormal=true;status.trigger_flags|=old::tactical_daily_trigger_evaluation_failure;return false;}
 if(!generation||generation!=status.generation||g_ted_fixed.family!=FixedDayFamily267V1::ted||g_ted_fixed.runtime!=&s||!g_ted_fixed.active||!g_ted_fixed.proof.captured||g_ted_fixed.proof.generation!=generation||s.armed.load(std::memory_order_acquire)||!s.shutdown_safe.load(std::memory_order_seq_cst)||s.access_cleanup_unknown.load(std::memory_order_seq_cst))return false;
 out=g_ted_fixed.proof;return true;
}
bool ReadTedDeferredActorOnOwner267V1(DateSentinelStateV1&s,const TedFixedDayProof267V1&p,const old::MainThreadExecutionStampV1&stamp,DateSentinelObservationV1&out,bool*busy)noexcept {
 out={};if(busy)*busy=false;
#if defined(XAR_CK3_ENABLE_121003_26785313_TED_TRANSITION_V1) && XAR_CK3_ENABLE_121003_26785313_TED_TRANSITION_V1
 WorkerMutationLock lifetime(s);if(!lifetime.acquired||s.post_callbacks.load(std::memory_order_acquire)){if(busy)*busy=true;return false;}
 const auto safe=[&]()noexcept{return s.initialized.load()&&!s.armed.load()&&s.shutdown_safe.load()&&!s.shutdown_requested.load()&&!s.pending_failure.load()&&!s.access_cleanup_unknown.load()&&!Expired(s);};
 if(!safe()||p.family!=FixedDayFamily267V1::ted||g_ted_fixed.family!=FixedDayFamily267V1::ted||!p.captured||p.actor_changed||p.stage!=TedFixedDayStage267V1::song_transition||!p.generation||p.generation!=s.generation.load()||g_ted_fixed.runtime!=&s||!g_ted_fixed.active||g_ted_fixed.generation!=p.generation)return false;
 const auto&stored=g_ted_fixed.proof;
 if(!stored.captured||stored.actor_changed||stored.stage!=p.stage||stored.generation!=p.generation||!Same(stored.before,p.before)||!Same(stored.after,p.after)||!Same(s.initial,p.before)||stored.captured_unix_ms!=p.captured_unix_ms||stored.captured_monotonic_ms!=p.captured_monotonic_ms||p.original_deadline_unix_ms!=s.original_deadline_unix_ms||p.monotonic_deadline_ms!=s.monotonic_deadline_ms||stored.worker.native!=p.worker.native||stored.worker.owned_handle!=p.worker.owned_handle||stored.worker.creation_time!=p.worker.creation_time||s.worker.native!=p.worker.native||s.worker.owned_handle!=p.worker.owned_handle||s.worker.creation_time!=p.worker.creation_time)return false;
 const auto status=old::ReadTacticalDailySentinelStatusV1();
 if(status.state!=Phase::triggered||status.generation!=p.generation||status.completed_daily_ticks!=1||status.overshoot_days||status.abnormal||status.trigger_flags!=old::tactical_daily_trigger_date_deadline||status.last_observed_date_raw!=p.after.core.clock.date_raw||status.target_date_raw!=status.last_observed_date_raw||status.trigger_date_raw!=status.target_date_raw||!status.pause_observed||!status.pause_wrapper_called)return false;
 std::uintptr_t tls=0;if(Owner(s,tls,&stamp)||tls!=s.owner_tls_context||WorkerOwnerUnlocked(s,false))return false;
 DateSentinelObservationV1 a{},z{};
 if(!Stable(s,a)||!PauseWorld(s,a)||!a.core.clock.paused||a.core.clock.speed!=p.before.core.clock.speed||a.core.clock.date_raw!=p.after.core.clock.date_raw||static_cast<std::int64_t>(p.before.core.clock.date_raw)+24!=a.core.clock.date_raw||!Stable(s,z)||!Same(a,z)||!safe()||Owner(s,tls,&stamp)||tls!=s.owner_tls_context||WorkerOwnerUnlocked(s,false))return false;
 out=z;return true;
#else
 (void)s;(void)p;(void)stamp;return false;
#endif
}
Arm ArmCccFixedDay267V1(DateSentinelStateV1&s,const old::TacticalDailySentinelArmRequestV1&r,std::uint64_t deadline,CccFixedDayStage267V1 stage)noexcept{
#if defined(XAR_CK3_ENABLE_121003_26785313_CCC_TRANSITION_V1) && XAR_CK3_ENABLE_121003_26785313_CCC_TRANSITION_V1
 if(static_cast<unsigned>(stage)>1||static_cast<std::int64_t>(r.starting_date_raw)+24!=r.target_date_raw)return Arm::invalid_request;
 if(!s.fixture_only&&!IsCurrent(s.bindings))return Arm::unavailable;
 return ArmDateSentinelImplV1(s,r,deadline,&stage,FixedDayFamily267V1::ccc);
#else
 (void)s;(void)r;(void)deadline;(void)stage;return Arm::unavailable;
#endif
}
bool ReadCccFixedDayProof267V1(const DateSentinelStateV1&s,std::uint64_t generation,TedFixedDayProof267V1&out,old::TacticalDailySentinelStatusV1&status)noexcept {
 out={};WorkerStatusLock lifetime(s);status=old::ReadTacticalDailySentinelStatusV1();
 if(status.generation!=s.generation.load(std::memory_order_acquire))return false;
 if(s.pending_failure.load(std::memory_order_acquire)){status.state=Phase::failed;status.abnormal=true;status.trigger_flags|=old::tactical_daily_trigger_evaluation_failure;return false;}
 if(!generation||generation!=status.generation||g_ted_fixed.family!=FixedDayFamily267V1::ccc||g_ted_fixed.runtime!=&s||!g_ted_fixed.active||!g_ted_fixed.proof.captured||g_ted_fixed.proof.generation!=generation||s.armed.load(std::memory_order_acquire)||!s.shutdown_safe.load(std::memory_order_seq_cst)||s.access_cleanup_unknown.load(std::memory_order_seq_cst))return false;
 out=g_ted_fixed.proof;return true;
}
bool ReadCccDeferredActorOnOwner267V1(DateSentinelStateV1&s,const TedFixedDayProof267V1&p,const old::MainThreadExecutionStampV1&stamp,DateSentinelObservationV1&out,bool*busy)noexcept {
 out={};if(busy)*busy=false;
#if defined(XAR_CK3_ENABLE_121003_26785313_CCC_TRANSITION_V1) && XAR_CK3_ENABLE_121003_26785313_CCC_TRANSITION_V1
 WorkerMutationLock lifetime(s);if(!lifetime.acquired||s.post_callbacks.load(std::memory_order_acquire)){if(busy)*busy=true;return false;}
 const auto safe=[&]()noexcept{return s.initialized.load()&&!s.armed.load()&&s.shutdown_safe.load()&&!s.shutdown_requested.load()&&!s.pending_failure.load()&&!s.access_cleanup_unknown.load()&&!Expired(s);};
 if(!safe()||p.family!=FixedDayFamily267V1::ccc||g_ted_fixed.family!=FixedDayFamily267V1::ccc||!p.captured||p.actor_changed||p.stage!=TedFixedDayStage267V1::song_transition||!p.generation||p.generation!=s.generation.load()||g_ted_fixed.runtime!=&s||!g_ted_fixed.active||g_ted_fixed.generation!=p.generation)return false;
 const auto&stored=g_ted_fixed.proof;
 if(!stored.captured||stored.actor_changed||stored.stage!=p.stage||stored.generation!=p.generation||!Same(stored.before,p.before)||!Same(stored.after,p.after)||!Same(s.initial,p.before)||stored.captured_unix_ms!=p.captured_unix_ms||stored.captured_monotonic_ms!=p.captured_monotonic_ms||p.original_deadline_unix_ms!=s.original_deadline_unix_ms||p.monotonic_deadline_ms!=s.monotonic_deadline_ms||stored.worker.native!=p.worker.native||stored.worker.owned_handle!=p.worker.owned_handle||stored.worker.creation_time!=p.worker.creation_time||s.worker.native!=p.worker.native||s.worker.owned_handle!=p.worker.owned_handle||s.worker.creation_time!=p.worker.creation_time)return false;
 const auto status=old::ReadTacticalDailySentinelStatusV1();
 if(status.state!=Phase::triggered||status.generation!=p.generation||status.completed_daily_ticks!=1||status.overshoot_days||status.abnormal||status.trigger_flags!=old::tactical_daily_trigger_date_deadline||status.last_observed_date_raw!=p.after.core.clock.date_raw||status.target_date_raw!=status.last_observed_date_raw||status.trigger_date_raw!=status.target_date_raw||!status.pause_observed||!status.pause_wrapper_called)return false;
 std::uintptr_t tls=0;if(Owner(s,tls,&stamp)||tls!=s.owner_tls_context||WorkerOwnerUnlocked(s,false))return false;
 DateSentinelObservationV1 a{},z{};
 if(!Stable(s,a)||!PauseWorld(s,a)||!a.core.clock.paused||a.core.clock.speed!=p.before.core.clock.speed||a.core.clock.date_raw!=p.after.core.clock.date_raw||static_cast<std::int64_t>(p.before.core.clock.date_raw)+24!=a.core.clock.date_raw||!Stable(s,z)||!Same(a,z)||!safe()||Owner(s,tls,&stamp)||tls!=s.owner_tls_context||WorkerOwnerUnlocked(s,false))return false;
 out=z;return true;
#else
 (void)s;(void)p;(void)stamp;return false;
#endif
}
bool DateSentinelAllowsResumeV1(DateSentinelStateV1 &s,const CoreSnapshotPrefix &expected) noexcept {
  if(s.access_cleanup_unknown.load(std::memory_order_seq_cst) ||
      s.shutdown_requested.load(std::memory_order_seq_cst) || !WorkerAccessConfigured(s) ||
      !s.armed.load(std::memory_order_acquire) || s.pending_failure.load(std::memory_order_acquire))return false;
  WorkerMutationLock lifetime(s);
  if(!lifetime.acquired || s.post_callbacks.load(std::memory_order_acquire))return false;
  std::uintptr_t tls=0;const auto owner=Owner(s,tls);
  if(owner){Fail(s,owner);return false;}
  if(Expired(s)){Fail(s,date_sentinel_failure_expired);return false;}
  if(const auto worker=WorkerOwnerUnlocked(s,false)){Fail(s,worker);return false;}
  DateSentinelObservationV1 o{};
  if(!Stable(s,o)){Fail(s,date_sentinel_failure_observation);return false;}
  const auto legacy=old::ReadTacticalDailySentinelStatusV1();
  if(legacy.generation!=s.generation.load(std::memory_order_acquire) || legacy.state!=Phase::armed) {
    Fail(s,date_sentinel_failure_runtime);return false;
  }
  const auto identity=Identity(s,o);
  if(identity){Fail(s,identity);return false;}
  if(Expired(s)){Fail(s,date_sentinel_failure_expired);return false;}
  if(const auto again=Owner(s,tls)){Fail(s,again);return false;}
  return !s.access_cleanup_unknown.load(std::memory_order_seq_cst) &&
    !s.shutdown_requested.load(std::memory_order_seq_cst) && !s.pending_failure.load(std::memory_order_acquire) && o.core.clock.paused && Same(o,s.initial) && Equal(o.core,expected);
}
static void RunPostDateSentinelV1(DateSentinelStateV1 &s) noexcept {
  if(s.access_cleanup_unknown.load(std::memory_order_seq_cst))return;
  if(!s.armed.load(std::memory_order_acquire) && s.shutdown_safe.load(std::memory_order_seq_cst))return;
  s.last_post_thread_id.store(GetCurrentThreadId(),std::memory_order_relaxed);
  s.last_post_stage.store(1,std::memory_order_relaxed);
  if(const auto role=WorkerOwnerUnlocked(s)){Fail(s,role);return;}
  s.last_post_stage.store(2,std::memory_order_relaxed);
  if(s.shutdown_requested.load(std::memory_order_seq_cst)){AbortOnWorker(s,date_sentinel_failure_shutdown);return;}
  if(Expired(s)){AbortOnWorker(s,date_sentinel_failure_expired);return;}
  s.last_post_stage.store(3,std::memory_order_relaxed);
  if(s.pending_failure.load(std::memory_order_acquire)){AbortOnWorker(s,0);return;}
  DateSentinelObservationV1 before{};
  const bool stable=Stable(s,before);
  s.last_post_date_raw.store(before.core.clock.date_raw,std::memory_order_relaxed);
  if(!stable){AbortOnWorker(s,date_sentinel_failure_observation);return;}
  s.last_post_stage.store(4,std::memory_order_relaxed);
  const auto identity=Identity(s,before);
  const bool fixed_observation=TedFixedObservation(s,before);
  if(identity&&!fixed_observation){AbortOnWorker(s,identity);return;}
  s.last_post_stage.store(5,std::memory_order_relaxed);
  const auto prior=old::ReadTacticalDailySentinelStatusV1();
  if(prior.generation!=s.generation.load(std::memory_order_acquire) || prior.state!=Phase::armed) {
    AbortOnWorker(s,date_sentinel_failure_runtime);return;
  }
  if(static_cast<std::int64_t>(before.core.clock.date_raw)!=static_cast<std::int64_t>(prior.last_observed_date_raw)+24) {
    AbortOnWorker(s,date_sentinel_failure_sequence);return;
  }
  s.last_post_stage.store(6,std::memory_order_relaxed);
  if(before.core.clock.paused && before.core.clock.date_raw<prior.target_date_raw) {
    AbortOnWorker(s,date_sentinel_failure_unexpected_pause);return;
  }
  if(Expired(s)){AbortOnWorker(s,date_sentinel_failure_expired);return;}
  if(const auto role=WorkerOwnerUnlocked(s)){Fail(s,role);return;}
  if(s.shutdown_requested.load(std::memory_order_seq_cst)){AbortOnWorker(s,date_sentinel_failure_shutdown);return;}
  // Sole evaluator call: original final already returned on the captured actual
  // native worker, with its own live creation epoch and command TLS scope.
  s.last_post_stage.store(7,std::memory_order_relaxed);
  WorkerEvaluateCall evaluate{s,before};
  if(!WithWorkerAccess(s,&EvaluateWorkerBody,&evaluate)){AbortOnWorker(s,date_sentinel_failure_runtime);return;}
  s.last_post_stage.store(8,std::memory_order_relaxed);
  DateSentinelObservationV1 after{};
  const auto result=old::ReadTacticalDailySentinelStatusV1();
  if(!Stable(s,after) || (Identity(s,after)&&!TedFixedObservation(s,after)) ||
      (fixed_observation&&!SameAfterPause(before,after)) || after.core.clock.date_raw!=before.core.clock.date_raw ||
      result.generation!=s.generation.load(std::memory_order_acquire)) {
    AbortOnWorker(s,date_sentinel_failure_observation);return;
  }
  if(Expired(s)){AbortOnWorker(s,date_sentinel_failure_expired);return;}
  if(const auto role=WorkerOwnerUnlocked(s)){Fail(s,role);return;}
  s.last_post_stage.store(9,std::memory_order_relaxed);
  if(s.shutdown_requested.load(std::memory_order_seq_cst)){AbortOnWorker(s,date_sentinel_failure_shutdown);return;}
  if(s.pending_failure.load(std::memory_order_acquire)){AbortOnWorker(s,0);return;}
  if(result.state==Phase::armed) {
    if(after.core.clock.paused)AbortOnWorker(s,date_sentinel_failure_unexpected_pause);
    return;
  }
  if(result.state!=Phase::triggered || !result.pause_observed || !after.core.clock.paused ||
      !(result.trigger_flags&old::tactical_daily_trigger_date_deadline) ||
      result.trigger_date_raw!=result.target_date_raw || result.overshoot_days!=0) {
    AbortOnWorker(s,date_sentinel_failure_runtime);return;
  }
  if(!ConfirmPausedDisarmed(s,false,true))AbortOnWorker(s,date_sentinel_failure_observation);
  else if(fixed_observation&&!CaptureTedFixedProof(s,before,after,result))AbortOnWorker(s,date_sentinel_failure_observation);
  else s.last_post_stage.store(10,std::memory_order_relaxed);
}
void PostDateSentinelV1(void *opaque) noexcept {
  if(!opaque)return;auto &s=*static_cast<DateSentinelStateV1 *>(opaque);
  if(!EnterPostCallback(s))return;
#if defined(_MSC_VER)
  // Trivial wrapper: SEH cannot strand the owned counter/shared lease.
  __try {RunPostDateSentinelV1(s);}
  __finally {
    if(AbnormalTermination())RetainUnknownWorkerAccess(s);
    LeavePostCallback(s);
  }
#else
  struct Leave {DateSentinelStateV1 &s;~Leave(){LeavePostCallback(s);}} leave{s};
  RunPostDateSentinelV1(s);
#endif
}

bool PollDateSentinelOwnerV1(DateSentinelStateV1 &s,const old::MainThreadExecutionStampV1 &stamp) noexcept {
  if(s.access_cleanup_unknown.load(std::memory_order_seq_cst))return false;
  // A failed native pause may already have disarmed the shared evaluator.
  // Unsafe is a separate lifetime obligation and remains pump-retry eligible.
  if(!s.armed.load(std::memory_order_acquire) && s.shutdown_safe.load(std::memory_order_seq_cst))return false;
  if(s.shutdown_requested.load(std::memory_order_seq_cst))Fail(s,date_sentinel_failure_shutdown);
  std::uintptr_t tls=0;const auto owner=Owner(s,tls,&stamp);
  if(owner){Fail(s,owner);return false;}
  if(Expired(s))Fail(s,date_sentinel_failure_expired);
  if(!s.pending_failure.load(std::memory_order_acquire))return false;
  // Even a broken Core read must not turn an unrelated world/stamp into pause.
  const bool stamped=Fault([&]() noexcept {
    const auto &c=s.bindings.core;const auto game=*c.game_state_slot,jomini=*c.jomini_state_slot;
    return game && jomini && reinterpret_cast<std::uintptr_t>(game)==stamp.game_state &&
      reinterpret_cast<std::uintptr_t>(jomini)==stamp.jomini_state &&
      At<std::int32_t>(game,8)==stamp.date_raw && (At<std::uint8_t>(jomini,0x20)!=0)==stamp.paused;
  });
  if(!stamped){Fail(s,date_sentinel_failure_observation);return false;}
  DateSentinelObservationV1 current{};
  const bool can_pause=Stable(s,current,true) && PauseWorld(s,current);
  const auto status=old::ReadTacticalDailySentinelStatusV1();
  if(s.generation.load(std::memory_order_acquire)==0 && status.generation==0 &&
      status.state==Phase::idle && can_pause && current.core.clock.paused) {
    // No shared generation was ever armed. This is a real owner observation,
    // not a synthetic abort or an unsafe acknowledgement by a worker.
    return ConfirmPausedDisarmed(s,true);
  }
  const auto flags=s.pending_failure.load(std::memory_order_acquire);
  std::uint32_t legacy_flags=old::tactical_daily_trigger_evaluation_failure;
  if(flags&(date_sentinel_failure_world|date_sentinel_failure_actor))legacy_flags|=old::tactical_daily_trigger_world_identity_changed;
  if(flags&date_sentinel_failure_sequence)legacy_flags|=old::tactical_daily_trigger_date_sequence_failure;
  if(const auto again=Owner(s,tls,&stamp)){Fail(s,again);return false;}
  if(!old::AbortTacticalDailySentinelDateOnlyV1(s.generation.load(std::memory_order_acquire),legacy_flags,can_pause))return false;
  s.armed.store(false,std::memory_order_release);
  // A failed/foreign pause never makes teardown safe. Keep all resources and
  // retry even with armed=false until actual owner-side pause is observed.
  if(!ConfirmPausedDisarmed(s,true))Fail(s,date_sentinel_failure_observation);
  return true;
}
Cancel CancelDateSentinelV1(DateSentinelStateV1 &s,std::uint64_t generation) noexcept {
  WorkerMutationLock lifetime(s);
  if(!lifetime.acquired || s.post_callbacks.load(std::memory_order_acquire))return Cancel::unavailable;
  if(s.access_cleanup_unknown.load(std::memory_order_seq_cst))return Cancel::unavailable;
  if(!s.initialized.load(std::memory_order_acquire))return Cancel::unavailable;
  std::uintptr_t tls=0;if(Owner(s,tls))return Cancel::unavailable;
  if(!generation)return Cancel::invalid_request;
  if(generation!=s.generation.load(std::memory_order_acquire))return Cancel::generation_mismatch;
  if(!s.armed.load(std::memory_order_acquire))return Cancel::not_armed;
  if(const auto worker=WorkerOwnerUnlocked(s,false)){Fail(s,worker);return Cancel::unavailable;}
  if(Expired(s)){Fail(s,date_sentinel_failure_expired);return Cancel::unavailable;}
  if(s.pending_failure.load(std::memory_order_acquire))return Cancel::unavailable;
  DateSentinelObservationV1 current{};
  if(!Stable(s,current) || Identity(s,current))return Cancel::unavailable;
  const auto result=old::CancelTacticalDailySentinelV1(generation);
  if(result==Cancel::canceled) {
    s.armed.store(false,std::memory_order_release);
    if(!ConfirmPausedDisarmed(s))Fail(s,date_sentinel_failure_observation);
  }
  return result;
}
old::TacticalDailySentinelStatusV1 ReadDateSentinelStatusV1(const DateSentinelStateV1 &s) noexcept {
  if(!s.initialized.load(std::memory_order_acquire))return {};
  WorkerStatusLock lifetime(s); // Pipe readers wait for the complete Post lease.
  auto result=old::ReadTacticalDailySentinelStatusV1();
  if(result.generation!=s.generation.load(std::memory_order_acquire))return {};
  if(s.pending_failure.load(std::memory_order_acquire)) {
    result.state=Phase::failed;result.abnormal=true;result.trigger_flags|=old::tactical_daily_trigger_evaluation_failure;
  }
  return result;
}
bool ReadDateSentinelTerminalForCancelV1(const DateSentinelStateV1 &s,
    std::uint64_t generation,old::TacticalDailySentinelStatusV1 &status) noexcept {
  status=ReadDateSentinelStatusV1(s); // Never invoked while already holding the gate.
  return !s.access_cleanup_unknown.load(std::memory_order_seq_cst) &&
      generation && status.generation==generation &&
      (status.state==Phase::idle || status.state==Phase::triggered || status.state==Phase::failed);
}
void RequestDateSentinelShutdownV1(DateSentinelStateV1 &s) noexcept {
  s.shutdown_requested.store(true,std::memory_order_seq_cst);
  s.pending_failure.fetch_or(date_sentinel_failure_shutdown,std::memory_order_acq_rel);
}
bool DateSentinelShutdownSafeV1(const DateSentinelStateV1 &s) noexcept {
  return s.shutdown_safe.load(std::memory_order_seq_cst) &&
      !s.access_cleanup_unknown.load(std::memory_order_seq_cst);
}
bool ReleaseDateSentinelWorkerV1(DateSentinelStateV1 &s) noexcept {
  WorkerMutationLock lifetime(s);return lifetime.acquired && CloseWorker(s);
}
DateSentinelDiagnosticsV1 ReadDateSentinelDiagnosticsV1(const DateSentinelStateV1 &s) noexcept {
  DateSentinelDiagnosticsV1 d{};d.initialized=s.initialized.load(std::memory_order_acquire);
  d.armed=s.armed.load(std::memory_order_acquire);d.fixture_only=s.fixture_only;
  d.shutdown_requested=s.shutdown_requested.load(std::memory_order_seq_cst);
  d.shutdown_safe=DateSentinelShutdownSafeV1(s);
  d.access_cleanup_unknown=s.access_cleanup_unknown.load(std::memory_order_seq_cst);
  d.failure_flags=s.pending_failure.load(std::memory_order_acquire);d.generation=s.generation.load(std::memory_order_acquire);
  d.captured_worker_thread_id=s.captured_worker_thread_id.load(std::memory_order_acquire);d.post_callbacks=s.post_callbacks.load(std::memory_order_acquire);
  d.status_readers_waiting=s.status_readers_waiting.load(std::memory_order_acquire);
  d.original_deadline_unix_ms=s.original_deadline_unix_ms;d.monotonic_deadline_ms=s.monotonic_deadline_ms;return d;
}
} // namespace xar::ck3_1210
