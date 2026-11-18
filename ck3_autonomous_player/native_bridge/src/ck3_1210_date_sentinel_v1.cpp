#include "xar_bridge/ck3_1210_date_sentinel_v1.hpp"
#include <array>
#include <cstring>
#include <limits>
namespace xar::ck3_1210 {
namespace {
namespace old=ck3_11906;
using Arm=old::TacticalDailySentinelArmStatusV1;
using Cancel=old::TacticalDailySentinelCancelStatusV1;
using Phase=old::TacticalDailySentinelStateV1;
std::atomic<DateSentinelStateV1 *> g_runtime{nullptr};
constexpr std::uintptr_t kPauseRva=0x3E65500,kTlsFlagRva=0x695910C,kTlsGetterRva=0x44FEA30;
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
bool Read(const DateSentinelStateV1 &s,DateSentinelObservationV1 &o) noexcept {
  o={};const auto &b=s.bindings.core;
  return Fault([&]() noexcept {
    if(!b.enabled || !b.game_state_slot || !b.jomini_state_slot || !b.character_storage_slot || !b.get_local_player)return false;
    o.game=*b.game_state_slot;o.jomini=*b.jomini_state_slot;o.storage=*b.character_storage_slot;
    if(!o.game || !o.jomini || !o.storage)return false;
    o.data=At<void *>(o.game,0xA0);o.players=At<void *>(o.jomini,0x18);
    o.player=b.get_local_player(o.jomini);
    if(!o.data || !o.players || !o.player || !ReadCoreSnapshot(b,o.core) ||
        !o.core.map_ready || !o.core.has_played_character || !o.core.played_character_alive ||
        o.core.local_player_id<0 || o.core.played_character_id==-1 ||
        At<std::int32_t>(o.player,0x70)!=o.core.local_player_id)return false;
    o.actor=ResolveCoreCharacter(b,o.core.played_character_id);
    if(!o.actor || At<std::uint32_t>(o.actor,0x1C)!=0x43686172 ||
        At<std::int32_t>(o.actor,0x18)!=o.core.played_character_id)return false;
    return *b.game_state_slot==o.game && *b.jomini_state_slot==o.jomini &&
      *b.character_storage_slot==o.storage && At<void *>(o.game,0xA0)==o.data &&
      At<void *>(o.jomini,0x18)==o.players && At<std::int32_t>(o.game,8)==o.core.clock.date_raw &&
      static_cast<std::int64_t>(At<std::int32_t>(o.game,0x70))+1==o.core.clock.speed &&
      (At<std::uint8_t>(o.jomini,0x20)!=0)==o.core.clock.paused;
  });
}
bool Stable(const DateSentinelStateV1 &s,DateSentinelObservationV1 &o) noexcept {
  DateSentinelObservationV1 other{};return Read(s,o) && Read(s,other) && Same(o,other);
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
      m.tls_initialized_flag!=s.bindings.module_base+kTlsFlagRva ||
      reinterpret_cast<std::uintptr_t>(m.tls_context_getter)!=s.bindings.module_base+kTlsGetterRva ||
      m.game_state_slot!=reinterpret_cast<std::uintptr_t>(s.bindings.core.game_state_slot) ||
      m.jomini_state_slot!=reinterpret_cast<std::uintptr_t>(s.bindings.core.jomini_state_slot)))return date_sentinel_failure_owner;
  if(!m.tls_initialized_flag || !m.tls_context_getter || !Fault([&]() noexcept {
      if(*reinterpret_cast<const std::uint8_t *>(m.tls_initialized_flag)!=1)return false;
      context=reinterpret_cast<std::uintptr_t>(m.tls_context_getter());
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
bool ConfirmPausedDisarmed(DateSentinelStateV1 &s) noexcept {
  std::uintptr_t tls=0;DateSentinelObservationV1 o{};
  if(Owner(s,tls) || !Stable(s,o) || !PauseWorld(s,o) || !o.core.clock.paused)return false;
  const auto status=old::ReadTacticalDailySentinelStatusV1();
  if(status.generation!=s.generation.load(std::memory_order_acquire) ||
      status.state==Phase::armed || status.state==Phase::unavailable || Owner(s,tls))return false;
  s.armed.store(false,std::memory_order_release);
  s.shutdown_safe.store(true,std::memory_order_seq_cst);return true;
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
  if(!b.module_base || b.module_base>(std::numeric_limits<std::uintptr_t>::max)()-0x6FE5000)return false;
  const auto core=BindCoreImage(b.module_base,kExecutableSha256);
  if(b.core.enabled!=core.enabled || b.core.game_state_slot!=core.game_state_slot ||
      b.core.jomini_state_slot!=core.jomini_state_slot || b.core.character_storage_slot!=core.character_storage_slot ||
      b.core.get_local_player!=core.get_local_player ||
      reinterpret_cast<std::uintptr_t>(b.set_paused)!=b.module_base+kPauseRva ||
      b.utc_now || b.monotonic_now || b.clock_context)return false;
  return Fault([&]() noexcept {
    return std::memcmp(reinterpret_cast<const void *>(b.module_base+kPauseRva),kPauseEntry.data(),kPauseEntry.size())==0;
  });
}
} // namespace
DateSentinelBindingsV1 BindDateSentinelImageV1(std::uintptr_t base,std::string_view sha) noexcept {
  DateSentinelBindingsV1 b{};
  if(!base || sha!=kExecutableSha256 || base>(std::numeric_limits<std::uintptr_t>::max)()-0x6FE5000)return b;
  b.exact_build_admitted=true;b.module_base=base;b.core=BindCoreImage(base,sha);
  b.set_paused=reinterpret_cast<old::TacticalSetPausedV1>(base+kPauseRva);return b;
}
bool InitializeDateSentinelV1(DateSentinelStateV1 &s,const DateSentinelBindingsV1 &b,
    old::MainThreadQueryMailboxV1 &m) noexcept {
  if(s.initialized.load(std::memory_order_acquire) || !b.exact_build_admitted ||
      !b.core.enabled || !b.core.game_state_slot || !b.core.jomini_state_slot ||
      !b.core.character_storage_slot || !b.core.get_local_player || !b.set_paused ||
      (!b.offline_fixture && !ProductionGuard(b)))return false;
  DateSentinelStateV1 *empty=nullptr;
  if(!g_runtime.compare_exchange_strong(empty,&s,std::memory_order_acq_rel))return false;
  if(!old::InitializeTacticalDailySentinelDateOnlyV1(Legacy(b.core),b.set_paused)) {
    g_runtime.store(nullptr,std::memory_order_release);return false;
  }
  s.bindings=b;s.mailbox=&m;s.fixture_only=b.offline_fixture;
  s.initialized.store(true,std::memory_order_release);return true;
}
Arm ArmDateSentinelV1(DateSentinelStateV1 &s,const old::TacticalDailySentinelArmRequestV1 &r,
    std::uint64_t deadline) noexcept {
  if(!s.initialized.load(std::memory_order_acquire) || g_runtime.load(std::memory_order_acquire)!=&s)return Arm::unavailable;
  if(s.shutdown_requested.load(std::memory_order_seq_cst))return Arm::unavailable;
  std::uintptr_t tls=0;if(Owner(s,tls))return Arm::unavailable;
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
  bool safe=true;
  if(!s.shutdown_safe.compare_exchange_strong(safe,false,std::memory_order_seq_cst))return Arm::unavailable;
  // This total-order handoff prevents a new native arm after Stop observed safe.
  if(s.shutdown_requested.load(std::memory_order_seq_cst)) {
    s.shutdown_safe.store(true,std::memory_order_seq_cst);return Arm::unavailable;
  }
  s.initial=o;s.original_deadline_unix_ms=deadline;s.monotonic_deadline_ms=mono+(deadline-wall);
  s.armed_unix_ms=wall;s.armed_monotonic_ms=mono;s.owner_tls_context=tls;
  s.owner_thread_id.store(GetCurrentThreadId(),std::memory_order_release);
  // Preserve the attempted paused world even if shared arming fails before its
  // first generation; a restored owner can then confirm disarmed + paused.
  s.generation.store(prior.generation,std::memory_order_release);
  const auto result=old::ArmTacticalDailySentinelV1(r);
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
  // Retire prior recoverable failures without ever erasing a racing Stop bit.
  s.pending_failure.fetch_and(date_sentinel_failure_shutdown,std::memory_order_acq_rel);
  s.armed.store(true,std::memory_order_release);
  if(s.shutdown_requested.load(std::memory_order_seq_cst))Fail(s,date_sentinel_failure_shutdown);
  DateSentinelObservationV1 after{};
  if(!Stable(s,after) || !Same(o,after))Fail(s,date_sentinel_failure_observation);
  if(Expired(s))Fail(s,date_sentinel_failure_expired);
  if(const auto again=Owner(s,tls))Fail(s,again);
  return s.pending_failure.load(std::memory_order_acquire)?Arm::unavailable:Arm::armed;
}
bool DateSentinelAllowsResumeV1(DateSentinelStateV1 &s,const CoreSnapshotPrefix &expected) noexcept {
  if(s.shutdown_requested.load(std::memory_order_seq_cst) ||
      !s.armed.load(std::memory_order_acquire) || s.pending_failure.load(std::memory_order_acquire))return false;
  std::uintptr_t tls=0;const auto owner=Owner(s,tls);
  if(owner){Fail(s,owner);return false;}
  if(Expired(s)){Fail(s,date_sentinel_failure_expired);return false;}
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
  return !s.shutdown_requested.load(std::memory_order_seq_cst) &&
    !s.pending_failure.load(std::memory_order_acquire) && o.core.clock.paused && Same(o,s.initial) && Equal(o.core,expected);
}
void PostDateSentinelV1(void *opaque) noexcept {
  if(!opaque)return;auto &s=*static_cast<DateSentinelStateV1 *>(opaque);
  if(!s.armed.load(std::memory_order_acquire))return;
  if(s.shutdown_requested.load(std::memory_order_seq_cst)){Fail(s,date_sentinel_failure_shutdown);return;}
  std::uintptr_t tls=0;const auto owner=Owner(s,tls);
  if(owner){Fail(s,owner);return;}
  if(Expired(s)){Fail(s,date_sentinel_failure_expired);return;}
  if(s.pending_failure.load(std::memory_order_acquire))return;
  DateSentinelObservationV1 before{};
  if(!Stable(s,before)){Fail(s,date_sentinel_failure_observation);return;}
  const auto identity=Identity(s,before);if(identity){Fail(s,identity);return;}
  const auto prior=old::ReadTacticalDailySentinelStatusV1();
  if(prior.generation!=s.generation.load(std::memory_order_acquire) || prior.state!=Phase::armed) {
    Fail(s,date_sentinel_failure_runtime);return;
  }
  if(static_cast<std::int64_t>(before.core.clock.date_raw)!=static_cast<std::int64_t>(prior.last_observed_date_raw)+24) {
    Fail(s,date_sentinel_failure_sequence);return;
  }
  if(before.core.clock.paused && before.core.clock.date_raw<prior.target_date_raw) {
    Fail(s,date_sentinel_failure_unexpected_pause);return;
  }
  if(Expired(s)){Fail(s,date_sentinel_failure_expired);return;}
  if(const auto again=Owner(s,tls)){Fail(s,again);return;}
  if(s.shutdown_requested.load(std::memory_order_seq_cst)){Fail(s,date_sentinel_failure_shutdown);return;}
  // Sole call site: true final-stage post callback, never the raw owner pump.
  old::ProcessTacticalDailySentinelAfterTickV1();
  DateSentinelObservationV1 after{};
  const auto result=old::ReadTacticalDailySentinelStatusV1();
  if(!Stable(s,after) || Identity(s,after) || after.core.clock.date_raw!=before.core.clock.date_raw ||
      result.generation!=s.generation.load(std::memory_order_acquire)) {
    Fail(s,date_sentinel_failure_observation);return;
  }
  if(Expired(s)){Fail(s,date_sentinel_failure_expired);return;}
  if(const auto again=Owner(s,tls)){Fail(s,again);return;}
  if(result.state==Phase::armed) {
    if(after.core.clock.paused)Fail(s,date_sentinel_failure_unexpected_pause);
    return;
  }
  if(result.state!=Phase::triggered || !result.pause_observed || !after.core.clock.paused ||
      !(result.trigger_flags&old::tactical_daily_trigger_date_deadline) ||
      result.trigger_date_raw!=result.target_date_raw || result.overshoot_days!=0) {
    Fail(s,date_sentinel_failure_runtime);return;
  }
  if(s.shutdown_requested.load(std::memory_order_seq_cst)){Fail(s,date_sentinel_failure_shutdown);return;}
  if(s.pending_failure.load(std::memory_order_acquire))return;
  if(!ConfirmPausedDisarmed(s))Fail(s,date_sentinel_failure_observation);
}
bool PollDateSentinelOwnerV1(DateSentinelStateV1 &s,const old::MainThreadExecutionStampV1 &stamp) noexcept {
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
  const bool can_pause=Stable(s,current) && PauseWorld(s,current);
  const auto status=old::ReadTacticalDailySentinelStatusV1();
  if(s.generation.load(std::memory_order_acquire)==0 && status.generation==0 &&
      status.state==Phase::idle && can_pause && current.core.clock.paused) {
    // No shared generation was ever armed. This is a real owner observation,
    // not a synthetic abort or an unsafe acknowledgement by a worker.
    return ConfirmPausedDisarmed(s);
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
  if(!ConfirmPausedDisarmed(s))Fail(s,date_sentinel_failure_observation);
  return true;
}
Cancel CancelDateSentinelV1(DateSentinelStateV1 &s,std::uint64_t generation) noexcept {
  if(!s.initialized.load(std::memory_order_acquire))return Cancel::unavailable;
  std::uintptr_t tls=0;if(Owner(s,tls))return Cancel::unavailable;
  if(!generation)return Cancel::invalid_request;
  if(generation!=s.generation.load(std::memory_order_acquire))return Cancel::generation_mismatch;
  if(!s.armed.load(std::memory_order_acquire))return Cancel::not_armed;
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
  auto result=old::ReadTacticalDailySentinelStatusV1();
  if(result.generation!=s.generation.load(std::memory_order_acquire))return {};
  if(s.pending_failure.load(std::memory_order_acquire)) {
    result.state=Phase::failed;result.abnormal=true;result.trigger_flags|=old::tactical_daily_trigger_evaluation_failure;
  }
  return result;
}
void RequestDateSentinelShutdownV1(DateSentinelStateV1 &s) noexcept {
  s.shutdown_requested.store(true,std::memory_order_seq_cst);
  s.pending_failure.fetch_or(date_sentinel_failure_shutdown,std::memory_order_acq_rel);
}
bool DateSentinelShutdownSafeV1(const DateSentinelStateV1 &s) noexcept {
  return s.shutdown_safe.load(std::memory_order_seq_cst);
}
DateSentinelDiagnosticsV1 ReadDateSentinelDiagnosticsV1(const DateSentinelStateV1 &s) noexcept {
  DateSentinelDiagnosticsV1 d{};d.initialized=s.initialized.load(std::memory_order_acquire);
  d.armed=s.armed.load(std::memory_order_acquire);d.fixture_only=s.fixture_only;
  d.shutdown_requested=s.shutdown_requested.load(std::memory_order_seq_cst);
  d.shutdown_safe=s.shutdown_safe.load(std::memory_order_seq_cst);
  d.failure_flags=s.pending_failure.load(std::memory_order_acquire);d.generation=s.generation.load(std::memory_order_acquire);
  d.original_deadline_unix_ms=s.original_deadline_unix_ms;d.monotonic_deadline_ms=s.monotonic_deadline_ms;return d;
}
} // namespace xar::ck3_1210
