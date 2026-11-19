#include "xar_bridge/ck3_1210_toast_query_v1.hpp"
#include "xar_bridge/ck3_1210_adapter.hpp"
#include <windows.h>
#include <algorithm>
#include <limits>

namespace xar::ck3_1210 {
namespace {
template<class T> bool Load(std::uintptr_t p,std::size_t offset,T &value) noexcept {
  if(!p || offset>(std::numeric_limits<std::uintptr_t>::max)()-p ||
      sizeof(T)>(std::numeric_limits<std::uintptr_t>::max)()-(p+offset))return false;
  SIZE_T got=0;return ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<const void *>(p+offset),
      &value,sizeof(value),&got) && got==sizeof(value);
}
std::uint64_t Wall() noexcept {
  FILETIME f{};GetSystemTimeAsFileTime(&f);
  return (((std::uint64_t{f.dwHighDateTime}<<32)|f.dwLowDateTime)-116444736000000000ULL)/10000;
}
bool Unexpired(const ToastQueryContextV1 &c) noexcept {
  return c.monotonic_deadline_ms && Wall()<c.request.deadline_unix_ms && GetTickCount64()<c.monotonic_deadline_ms;
}
bool Owned(ToastQueryContextV1 &c,const ck3_11906::MainThreadExecutionStampV1 &s) noexcept {
  if(!c.game || !c.game->enabled() || !game::IsCk3_1210Descriptor(c.game->descriptor()) ||
      !c.game->supports(kToastQueryCapabilityV1) || !c.native_full_adapter ||
      !c.native_full_adapter->supports_snapshot() || !game::IsCk3_1210Descriptor(c.native_full_adapter->descriptor()) ||
      !c.expected_full_snapshot || !c.mailbox || !c.core.enabled || !c.provider || !c.bindings.exact_build_admitted ||
      !c.ticket.sequence || !c.connection_generation || !s.pump_epoch || !s.thread_id ||
      GetCurrentThreadId()!=s.thread_id || !s.paused || s.tls_initialized!=1 ||
      s.tls_main_thread_marker!=1 || !s.tls_context || !s.game_state || !s.jomini_state)return false;
  const auto &m=*c.mailbox;std::uintptr_t gs=0,js=0;
  if(!Load(reinterpret_cast<std::uintptr_t>(c.core.game_state_slot),0,gs) ||
      !Load(reinterpret_cast<std::uintptr_t>(c.core.jomini_state_slot),0,js))return false;
  return !m.offline_fixture && m.state.load(std::memory_order_acquire)==ck3_11906::MainThreadQueryMailboxStateV1::executing &&
      !m.stop_requested.load(std::memory_order_acquire) && !m.failure_flags.load(std::memory_order_acquire) &&
      !m.proof_reset_requested.load(std::memory_order_acquire) &&
      m.pump_epochs.load(std::memory_order_acquire)==s.pump_epoch &&
      m.published_sequence.load(std::memory_order_acquire)==c.ticket.sequence &&
      m.owner_thread_id.load(std::memory_order_acquire)==s.thread_id &&
      m.executor.load(std::memory_order_acquire)==&ExecuteToastQueryMailboxV1 && m.executor_context==&c &&
      m.paused_owner_verified_pump_epochs.load(std::memory_order_acquire)>=ck3_11906::kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs &&
      m.owner_verified_pump_epochs.load(std::memory_order_acquire)>=ck3_11906::kMainThreadQueryMinimumOwnerVerifiedPumpEpochs &&
      gs==s.game_state && js==s.jomini_state;
}
bool Current(ToastQueryContextV1 &c,const ck3_11906::MainThreadExecutionStampV1 &s) noexcept {
  game::Snapshot fresh{};
  return Unexpired(c) && Owned(c,s) && c.native_full_adapter->read_snapshot(fresh) &&
      fresh==*c.expected_full_snapshot && fresh.paused && fresh.date_raw==s.date_raw && fresh.map_ready &&
      fresh.has_played_character && fresh.played_character_alive;
}
bool Graph(const ck3_11906::MainThreadExecutionStampV1 &s,IngameReadyGraphV1 &g) noexcept {
  g={};g.root=reinterpret_cast<void *>(s.jomini_state);
  return Load(s.jomini_state,0x18,g.application) && Load(s.jomini_state,0x10,g.gfx) &&
      Load(reinterpret_cast<std::uintptr_t>(g.gfx),0x88,g.handler) &&
      Load(reinterpret_cast<std::uintptr_t>(g.application),kIngameCompletedFrameEpochOffsetV1,g.completed_frame_epoch);
}
bool Execute(ToastQueryContextV1 &c,const ck3_11906::MainThreadExecutionStampV1 &s) {
  c.result={};
  auto fail=[&](const char *why) {if(c.provider)*c.provider={};c.result.available=false;
    c.result.observation={};c.result.unavailable_reason=why;return true;};
  if(!Current(c,s))return fail("toast_current_full_or_owner_unavailable");
  c.result.application_main_observed=true;c.result.full_snapshot_before_verified=true;
  c.result.source_abi_pins_verified=true;c.result.connection_generation=c.connection_generation;
  c.result.query_sequence=c.ticket.sequence;c.result.owner_thread_id=s.thread_id;
  const ToastQueryOwnerIdentityV1 owner{c.connection_generation,s.thread_id,s.tls_initialized,s.tls_main_thread_marker,
      s.tls_context,s.game_state,s.jomini_state,s.date_raw,c.expected_full_snapshot->played_character_id};
  if(!c.provider->owner_bound || c.provider->owner!=owner) {*c.provider={};c.provider->owner=owner;c.provider->owner_bound=true;}
  IngameReadyGraphV1 graph{};
  // Current() is a real owner-side Full read, including its existing completed-
  // application-frame witness. No synthetic readiness witness is seeded here.
  if(!Graph(s,graph))return fail("toast_graph_unreadable");
  if(!ObservePublishedToastObjectV1(c.bindings,graph,NativeToastObjectMemoryReaderV1(),
      c.provider->objects,c.result.observation)) {
    const auto why=c.result.observation.unavailable_reason;
    if(c.provider)*c.provider={};c.result.observation={};c.result.unavailable_reason.assign(why);return true;
  }
  IngameReadyGraphV1 after{};
  if(!Current(c,s) || !Graph(s,after) || after!=graph)return fail("toast_full_or_graph_changed_after_capture");
  c.result.full_snapshot_after_verified=true;c.result.available=true;return true;
}
} // namespace
void ArmToastQueryDeadlineV1(ToastQueryContextV1 &c) noexcept {
  c.monotonic_deadline_ms=0;const auto now=Wall();
  if(c.request.deadline_unix_ms>now) {
    const auto budget=(std::min)(c.request.deadline_unix_ms-now,std::uint64_t{120000});
    c.monotonic_deadline_ms=GetTickCount64()+budget;
  }
}
bool ExecuteToastQueryMailboxV1(void *p,const ck3_11906::MainThreadExecutionStampV1 &s) noexcept {
  if(!p)return false;auto &c=*static_cast<ToastQueryContextV1 *>(p);
  try{return Execute(c,s);}catch(...) {if(c.provider)*c.provider={};c.result={};
    try{c.result.unavailable_reason="toast_observation_exception";}catch(...) {}return false;}
}
} // namespace xar::ck3_1210
