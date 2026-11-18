#include "xar_bridge/ck3_1210_event_option_control_v1.hpp"
#include "xar_bridge/ck3_1210_adapter.hpp"
#include "xar_bridge/ck3_1210_core_frame_v1.hpp"
#include <windows.h>

namespace xar::ck3_1210 {
namespace {
std::uint64_t WallNow(void *) noexcept {
  FILETIME ft{};GetSystemTimeAsFileTime(&ft);
  return (((std::uint64_t{ft.dwHighDateTime}<<32)|ft.dwLowDateTime)-116444736000000000ULL)/10000;
}
std::uint64_t MonoNow(void *) noexcept {return GetTickCount64();}
std::uint64_t Wall(const EventOptionControlContextV1 &c) noexcept {
  return (c.wall_clock?c.wall_clock:&WallNow)(c.clock_context);
}
std::uint64_t Mono(const EventOptionControlContextV1 &c) noexcept {
  return (c.monotonic_clock?c.monotonic_clock:&MonoNow)(c.clock_context);
}
bool Unexpired(const EventOptionControlContextV1 &c) noexcept {
  return c.monotonic_deadline_ms && Wall(c)<c.request.deadline_unix_ms && Mono(c)<c.monotonic_deadline_ms;
}
bool Owned(EventOptionControlContextV1 &c,const ck3_11906::MainThreadExecutionStampV1 &s) noexcept {
  if(!c.game || !c.game->enabled() || !game::IsCk3_1210Descriptor(c.game->descriptor()) ||
      !c.game->supports(kEventOptionsQueryCapabilityV1) ||
      (c.request.select && !c.game->supports(kEventOptionsSelectCapabilityV1)) ||
      !c.native_full_adapter || !c.native_full_adapter->supports_snapshot() ||
      !game::IsCk3_1210Descriptor(c.native_full_adapter->descriptor()) ||
      !c.expected_full_snapshot || !c.mailbox || !c.bindings.current.core.enabled ||
      (c.request.select && !c.commands.enabled) || !c.ticket.sequence || !s.pump_epoch ||
      !s.thread_id || GetCurrentThreadId()!=s.thread_id || !s.paused ||
      s.tls_initialized!=1 || s.tls_main_thread_marker!=1 || !s.tls_context ||
      !s.game_state || !s.jomini_state) return false;
  const auto &m=*c.mailbox;
  const auto &core=c.bindings.current.core;
  return !m.offline_fixture && m.state.load(std::memory_order_acquire)==ck3_11906::MainThreadQueryMailboxStateV1::executing &&
      !m.stop_requested.load(std::memory_order_acquire) && !m.proof_reset_requested.load(std::memory_order_acquire) &&
      !m.failure_flags.load(std::memory_order_acquire) && m.pump_epochs.load(std::memory_order_acquire)==s.pump_epoch &&
      m.published_sequence.load(std::memory_order_acquire)==c.ticket.sequence &&
      m.owner_thread_id.load(std::memory_order_acquire)==s.thread_id &&
      m.executor.load(std::memory_order_acquire)==&ExecuteEventOptionControlMailboxV1 &&
      m.executor_context==&c && m.paused_owner_verified_pump_epochs.load(std::memory_order_acquire)>=
          ck3_11906::kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs &&
      m.owner_verified_pump_epochs.load(std::memory_order_acquire)>=ck3_11906::kMainThreadQueryMinimumOwnerVerifiedPumpEpochs &&
      core.game_state_slot && core.jomini_state_slot &&
      reinterpret_cast<std::uintptr_t>(*core.game_state_slot)==s.game_state &&
      reinterpret_cast<std::uintptr_t>(*core.jomini_state_slot)==s.jomini_state;
}
CoreSnapshotPrefix Core(const game::Snapshot &s) noexcept {
  return {{s.date_raw,s.speed,s.paused},s.player_id,s.map_ready,s.has_played_character,
      s.played_character_id,s.played_character_alive};
}
bool Current(EventOptionControlContextV1 &c,const ck3_11906::MainThreadExecutionStampV1 &s) noexcept {
  if(!Unexpired(c)) {c.result.status=EventOptionStatusV1::expired;c.result.unavailable_reason="request_expired";return false;}
  game::Snapshot fresh{};
  if(!Owned(c,s) || !c.native_full_adapter->read_snapshot(fresh) ||
      fresh!=*c.expected_full_snapshot || fresh.date_raw!=s.date_raw || !fresh.paused) {
    c.result.status=EventOptionStatusV1::stale_full_snapshot;c.result.unavailable_reason="stale_full_snapshot";return false;
  }
  c.result.full_snapshot_before_verified=true;
  if(!fresh.has_active_event) {
    c.result.status=EventOptionStatusV1::no_active_event;c.result.unavailable_reason="no_active_event";return false;
  }
  if(fresh.active_event_instance_id!=c.request.event_instance_id) {
    c.result.status=EventOptionStatusV1::event_mismatch;c.result.unavailable_reason="event_mismatch";return false;
  }
  if(!ReadEventOptionsV1(c.bindings,Core(fresh),c.request.event_instance_id,c.result.observation)) {
    c.result.unavailable_reason=c.result.observation.unavailable_reason;return false;
  }
  if(c.request.select) {
    bool found=false,enabled=false;
    for(std::size_t i=0;i<c.result.observation.count;++i) {
      const auto &row=c.result.observation.rows[i];
      if(row.native_option_index==c.request.native_option_index) {found=true;enabled=row.enabled;break;}
    }
    if(!found || !enabled) {
      c.result.status=found?EventOptionStatusV1::option_disabled:EventOptionStatusV1::option_missing;
      c.result.unavailable_reason=found?"option_disabled":"option_missing";return false;
    }
  }
  if(!Unexpired(c)) {c.result.status=EventOptionStatusV1::expired;c.result.unavailable_reason="request_expired";return false;}
  return true;
}
struct Admission {EventOptionControlContextV1 &context;const ck3_11906::MainThreadExecutionStampV1 &stamp;};
bool BeforeQueue(void *p) noexcept {
  auto &a=*static_cast<Admission *>(p);
  if(!Current(a.context,a.stamp)) return false;
  a.context.result.effect_attempted=true;return true;
}
bool Execute(EventOptionControlContextV1 &c,const ck3_11906::MainThreadExecutionStampV1 &s) noexcept {
  c.result={};
  if(!Owned(c,s)) return true;
  c.result.application_main_observed=true;
  if(!Current(c,s)) return true;
  if(!c.request.select) {
    c.result.status=EventOptionStatusV1::available;c.result.unavailable_reason={};return true;
  }
  const auto command=MakeSelectEventCommandV1(c.bindings,c.request.event_instance_id,c.request.native_option_index);
  Admission admission{c,s};
  const auto result=SubmitCommandCopy(c.commands,&command,7,&BeforeQueue,&admission);
  if(!c.result.effect_attempted) return true;
  c.result.status=result==CommandSubmitResult::submitted?EventOptionStatusV1::submitted:
      result==CommandSubmitResult::rejected?EventOptionStatusV1::rejected:EventOptionStatusV1::indeterminate;
  c.result.unavailable_reason=result==CommandSubmitResult::submitted?std::string_view{}:
      result==CommandSubmitResult::rejected?"command_queue_rejected":"command_queue_indeterminate";
  return true;
}
const char *Status(EventOptionStatusV1 s) noexcept {
  switch(s) {
    case EventOptionStatusV1::available:return "available";
    case EventOptionStatusV1::submitted:return "submitted";
    case EventOptionStatusV1::expired:return "expired";
    case EventOptionStatusV1::stale_full_snapshot:return "stale_full_snapshot";
    case EventOptionStatusV1::no_active_event:return "no_active_event";
    case EventOptionStatusV1::event_mismatch:return "event_mismatch";
    case EventOptionStatusV1::option_missing:return "option_missing";
    case EventOptionStatusV1::option_disabled:return "option_disabled";
    case EventOptionStatusV1::rejected:return "rejected";
    case EventOptionStatusV1::indeterminate:return "indeterminate";
    default:return "unavailable";
  }
}
void String(std::string &s,std::string_view value) {
  constexpr char hex[]="0123456789abcdef";s+='"';
  for(const unsigned char ch:value) {
    if(ch=='"' || ch=='\\') {s+='\\';s+=static_cast<char>(ch);}
    else if(ch<0x20) {s+="\\u00";s+=hex[ch>>4];s+=hex[ch&15];}
    else s+=static_cast<char>(ch);
  }
  s+='"';
}
} // namespace
void ArmEventOptionDeadlineV1(EventOptionControlContextV1 &c) noexcept {
  const auto now=Wall(c);c.monotonic_deadline_ms=0;
  if(c.request.deadline_unix_ms<=now) return;
  const auto remaining=c.request.deadline_unix_ms-now;
  c.monotonic_deadline_ms=Mono(c)+(remaining<8000?remaining:8000);
}
bool ExecuteEventOptionControlMailboxV1(void *p,const ck3_11906::MainThreadExecutionStampV1 &s) noexcept {
  if(!p)return false;auto &c=*static_cast<EventOptionControlContextV1 *>(p);
#if defined(_MSC_VER)
  __try {return Execute(c,s);}
  __except(EXCEPTION_EXECUTE_HANDLER) {
    c.result.status=c.result.effect_attempted?EventOptionStatusV1::indeterminate:EventOptionStatusV1::unavailable;
    c.result.unavailable_reason="native_event_control_exception";return true;
  }
#else
  return Execute(c,s);
#endif
}
std::string SerializeEventOptionCommandResultV1(std::string_view id,
    const EventOptionRequestV1 &r,const EventOptionResultV1 &v) {
  const bool accepted=v.status==EventOptionStatusV1::available || v.status==EventOptionStatusV1::submitted;
  std::string s="{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":";String(s,id);
  s+=",\"ok\":true,\"result\":{\"schema\":";String(s,kEventOptionResultSchemaV1);
  s+=",\"step\":";String(s,r.step);s+=",\"game_version\":";String(s,kGameVersion);
  s+=",\"executable_sha256\":";String(s,kExecutableSha256);s+=",\"adapter_id\":";String(s,kAdapterId);
  s+=",\"backend\":";String(s,kCoreBackendV1);s+=",\"status\":";String(s,Status(v.status));
  s+=",\"accepted\":";s+=accepted?"true":"false";
  s+=",\"native_revision\":"+std::to_string(r.native_revision);
  s+=",\"event_instance_id\":"+std::to_string(r.event_instance_id);
  s+=",\"native_option_index\":";s+=r.select?std::to_string(r.native_option_index):"null";
  s+=",\"application_main_observed\":";s+=v.application_main_observed?"true":"false";
  s+=",\"full_snapshot_before_verified\":";s+=v.full_snapshot_before_verified?"true":"false";
  s+=",\"effect_attempted\":";s+=v.effect_attempted?"true":"false";
  s+=",\"options\":[";
  if(accepted) for(std::size_t i=0;i<v.observation.count;++i) {
    if(i)s+=',';const auto &row=v.observation.rows[i];
    s+="{\"native_option_index\":"+std::to_string(row.native_option_index)+",\"enabled\":";
    s+=row.enabled?"true}":"false}";
  }
  s+="],\"unavailable_reason\":";
  if(v.unavailable_reason.empty())s+="null";else String(s,v.unavailable_reason);
  s+="}}";return s;
}
} // namespace xar::ck3_1210
