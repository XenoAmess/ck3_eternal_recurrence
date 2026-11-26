#include "xar_bridge/ck3_121003_save_mapped111.hpp"
#include "xar_bridge/ck3_26757580_save_mapped61.hpp"
#include "xar_bridge/ck3_1210_hotfix26757580_v1.hpp"
#include "xar_bridge/ck3_1210_core_control_v1.hpp"
#include "xar_bridge/ck3_1210_adapter.hpp"
#include <windows.h>
#include "xar_bridge/ck3_1210_date_sentinel_v1.hpp"
#include "xar_bridge/main_thread_timeline_policy_v1.hpp"

namespace xar::ck3_1210 {
namespace {
std::uint64_t WallNow(void *) noexcept {
  FILETIME value{}; GetSystemTimeAsFileTime(&value);
  const auto ticks = (std::uint64_t{value.dwHighDateTime} << 32) | value.dwLowDateTime;
  return (ticks - 116444736000000000ULL) / 10000;
}
std::uint64_t MonoNow(void *) noexcept { return GetTickCount64(); }
std::uint64_t Wall(const CoreControlContextV1 &c) noexcept {
  return (c.wall_clock == nullptr ? &WallNow : c.wall_clock)(c.clock_context);
}
std::uint64_t Mono(const CoreControlContextV1 &c) noexcept {
  return (c.monotonic_clock == nullptr ? &MonoNow : c.monotonic_clock)(c.clock_context);
}
bool Unexpired(const CoreControlContextV1 &c) noexcept {
  return c.monotonic_deadline_ms != 0 && Wall(c) < c.request.deadline_unix_ms &&
      Mono(c) < c.monotonic_deadline_ms;
}
const char *RequiredCapability(const CoreControlRequestV1 &r) noexcept {
  if (r.operation==CoreControlOperationV1::application_exit && r.step==kApplicationExitStepV1) return kApplicationExitCapabilityV1;
  if (r.operation==CoreControlOperationV1::sentinel_cancel && r.step.starts_with(ck3_11906::kTacticalDailySentinelCancelPrefixV1))
    return ck3_11906::kTacticalDailySentinelCancelCapabilityV1.data();
  if (r.operation==CoreControlOperationV1::sentinel_arm && r.step.starts_with(ck3_11906::kTacticalDailySentinelArmPrefixV1))
    return ck3_11906::kTacticalDailySentinelCapabilityV1.data();
  if (r.operation==CoreControlOperationV1::pause && r.step=="pause-map") return "game.command.pause-map";
  if (r.operation==CoreControlOperationV1::resume && r.step=="resume-map") return "game.command.resume-map";
  if (r.operation==CoreControlOperationV1::save && r.step=="save-checkpoint") return "game.command.save-checkpoint";
  static constexpr const char *speeds[]{"game.command.set-speed-1", "game.command.set-speed-2",
      "game.command.set-speed-3", "game.command.set-speed-4", "game.command.set-speed-5"};
  if (r.operation==CoreControlOperationV1::speed && r.public_speed>=1 && r.public_speed<=5 &&
      r.step.size()==11 && r.step.starts_with("set-speed-") &&
      r.step[10]=='0'+r.public_speed) return speeds[r.public_speed-1];
  return nullptr;
}
bool Owned(CoreControlContextV1 &c,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  const char *required=RequiredCapability(c.request);
  if (required==nullptr || c.game == nullptr || !c.game->enabled() || !c.game->supports(required) ||
      !game::IsCk3_1210BasicDescriptor(c.game->descriptor()) ||
      !c.game->supports(kCoreControlCapabilityV1) || c.mailbox == nullptr ||
      !c.core.enabled || c.core.image_build!=game::Ck3_1210BasicBuild(c.game->descriptor()) || (c.request.operation!=CoreControlOperationV1::application_exit && !c.commands.enabled) || c.ticket.sequence == 0 ||
      stamp.pump_epoch == 0 || stamp.thread_id == 0 ||
      GetCurrentThreadId() != stamp.thread_id || stamp.tls_initialized != 1 ||
      stamp.tls_main_thread_marker != 1 || stamp.tls_context == 0 ||
      stamp.game_state == 0 || stamp.jomini_state == 0) return false;
  const bool full=c.native_full_adapter!=nullptr || c.expected_full_snapshot!=nullptr;
  if(full && (c.native_full_adapter==nullptr || c.expected_full_snapshot==nullptr ||
      !c.game->supports(kFullClockControlCapabilityV1) ||
      !game::IsCk3_1210BasicDescriptor(c.native_full_adapter->descriptor()) ||
      !c.native_full_adapter->supports_snapshot() ||
      game::Ck3_1210BasicBuild(c.native_full_adapter->descriptor())!=c.core.image_build)) return false;
  const auto &m = *c.mailbox;
  return ck3_11906::IsMainThreadTimelineExecutorV1(m,&ExecuteCoreControlMailboxV1) &&
      m.owner_verified_pump_epochs.load(std::memory_order_acquire)>=
          ck3_11906::kMainThreadQueryMinimumOwnerVerifiedPumpEpochs &&
      m.state.load(std::memory_order_acquire) ==
          ck3_11906::MainThreadQueryMailboxStateV1::executing &&
      !m.stop_requested.load(std::memory_order_acquire) &&
      m.failure_flags.load(std::memory_order_acquire) == 0 &&
      m.published_sequence.load(std::memory_order_acquire) == c.ticket.sequence &&
      m.owner_thread_id.load(std::memory_order_acquire) == stamp.thread_id &&
      m.executor.load(std::memory_order_acquire) == &ExecuteCoreControlMailboxV1 &&
      m.executor_context == &c && c.core.game_state_slot != nullptr &&
      c.core.jomini_state_slot != nullptr &&
      reinterpret_cast<std::uintptr_t>(*c.core.game_state_slot) == stamp.game_state &&
      reinterpret_cast<std::uintptr_t>(*c.core.jomini_state_slot) == stamp.jomini_state;
}
bool VerifyFullBefore(CoreControlContextV1 &c) noexcept {
  if(c.native_full_adapter==nullptr && c.expected_full_snapshot==nullptr) return true;
  c.result.full_snapshot_before_verified=false;
  game::Snapshot current{};
  // A Full111 ordinary event summary is read-only evidence. Keep the empty-event
  // requirement at the owning read and immediately before queue submission.
  if(c.native_full_adapter==nullptr || c.expected_full_snapshot==nullptr ||
      (IsFull111(c.core.image_build)&&c.expected_full_snapshot->has_active_event) ||
      !c.native_full_adapter->read_snapshot(current) ||
      (IsFull111(c.core.image_build)&&current.has_active_event) || current!=*c.expected_full_snapshot) {
    c.result.status=CoreControlStatusV1::stale_full_snapshot;return false;
  }
  c.result.full_snapshot_before_verified=true;return true;
}
bool VerifyResume(CoreControlContextV1 &c) noexcept {
 if(c.request.operation!=CoreControlOperationV1::resume || !c.game->supports(kFullClockControlCapabilityV1)) return true;
 if(c.expected_full_snapshot==nullptr || c.date_sentinel==nullptr ||
    !DateSentinelAllowsResumeV1(*c.date_sentinel,c.request.expected)) {
   c.result.status=CoreControlStatusV1::unavailable;return false;
 }
 return true;
}
bool SaveMappingKnown(CoreControlContextV1 &c,const ck3_11906::MainThreadExecutionStampV1 &s) noexcept {
  if(c.request.operation==CoreControlOperationV1::save && ((IsHotfix(c.core.image_build)&&!SaveAdmission61(c,s)) ||
       (IsFull111(c.core.image_build)&&!SaveAdmission111(c,s)))) {
    c.result.status=CoreControlStatusV1::unavailable;return false;
  }
  return true;
}
bool SaveCleanupKnown(CoreControlContextV1 &c) noexcept {
  // Only SAVE is blocked by sticky native access cleanup uncertainty.
  // Application exit remains independent; unrelated Date failures retain their contracts.
  if(c.request.operation==CoreControlOperationV1::save && c.date_sentinel!=nullptr &&
      c.date_sentinel->access_cleanup_unknown.load(std::memory_order_seq_cst)) {
    c.result.status=CoreControlStatusV1::unavailable;return false;
  }
  return true;
}
struct Admission {
  CoreControlContextV1 &context;
  const ck3_11906::MainThreadExecutionStampV1 &stamp;
};
bool BeforeQueue(void *opaque) noexcept {
  auto &a = *static_cast<Admission *>(opaque); auto &c = a.context;
  if (!Unexpired(c)) { c.result.status=CoreControlStatusV1::expired; return false; }
  if(!SaveMappingKnown(c,a.stamp))return false;
  CoreSnapshotPrefix current{};
  if (!Owned(c,a.stamp) || !ReadCoreSnapshot(c.core,current) ||
      !EqualCorePrefixV1(current,c.request.expected) ||
      current.clock.date_raw != a.stamp.date_raw || current.clock.paused != a.stamp.paused) {
    c.result.status=CoreControlStatusV1::stale; return false;
  }
  if(!VerifyFullBefore(c) || !VerifyResume(c)) return false;
  if(!Unexpired(c)) {c.result.status=CoreControlStatusV1::expired;return false;}
  if(!SaveCleanupKnown(c))return false;
  if(!SaveMappingKnown(c,a.stamp))return false;
  c.result.effect_attempted=true;
  return true;
}
bool BeforeApplicationExit(void *opaque) noexcept {
  auto &c=static_cast<Admission *>(opaque)->context;
  const bool valid=BeforeQueue(opaque);
  // Validation alone is not an exit attempt. The lifetime claim/call below
  // determines whether this packet crossed a dispatch boundary.
  c.result.effect_attempted=false;
  return valid;
}
bool Execute(CoreControlContextV1 &c,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  c.result={};
  if (!Owned(c,stamp)) return true;
  if(!SaveMappingKnown(c,stamp))return true;
  if(!SaveCleanupKnown(c))return true;
  if(c.request.operation==CoreControlOperationV1::sentinel_cancel) {
    // Cancellation is generation-bound paused cleanup. The provider checks
    // its original ARM deadline; no new now-plus command window is minted.
    if(c.date_sentinel==nullptr || !c.date_cancel_generation || !c.game->supports(kDateSentinelCapabilityV1))return true;
    c.result.effect_attempted=true;
    const auto status=CancelDateSentinelV1(*c.date_sentinel,c.date_cancel_generation);
    const bool done=status==ck3_11906::TacticalDailySentinelCancelStatusV1::canceled ||
        status==ck3_11906::TacticalDailySentinelCancelStatusV1::not_armed;
    c.result.status=done?CoreControlStatusV1::sentinel_canceled:CoreControlStatusV1::rejected;
    if(status==ck3_11906::TacticalDailySentinelCancelStatusV1::not_armed ||
       status==ck3_11906::TacticalDailySentinelCancelStatusV1::generation_mismatch ||
       status==ck3_11906::TacticalDailySentinelCancelStatusV1::invalid_request ||
       status==ck3_11906::TacticalDailySentinelCancelStatusV1::requires_paused)c.result.effect_attempted=false;
    return true;
  }
  if (!Unexpired(c)) { c.result.status=CoreControlStatusV1::expired; return true; }
  if (!ReadCoreSnapshot(c.core,c.result.observed)) return true;
  const auto &current=c.result.observed;
  if (!EqualCorePrefixV1(current,c.request.expected) ||
      current.clock.date_raw!=stamp.date_raw || current.clock.paused!=stamp.paused) {
    c.result.status=CoreControlStatusV1::stale; return true;
  }
  if (c.request.operation!=CoreControlOperationV1::application_exit &&
      (!current.map_ready || current.local_player_id<0)) {
    c.result.status=CoreControlStatusV1::requires_map; return true;
  }
  if(!VerifyFullBefore(c) || !VerifyResume(c)) return true;
  if(!Unexpired(c)) {c.result.status=CoreControlStatusV1::expired;return true;}
  Admission admission{c,stamp};
  CommandSubmitResult submitted=CommandSubmitResult::unavailable;
  switch (c.request.operation) {
  case CoreControlOperationV1::sentinel_arm: {
    if(c.native_full_adapter==nullptr || c.date_sentinel==nullptr || c.date_arm_request==nullptr ||
        !c.game->supports(kDateSentinelCapabilityV1)) return true;
    c.result.effect_attempted=true;
    const auto status=ArmDateSentinelV1(*c.date_sentinel,*c.date_arm_request,c.request.deadline_unix_ms);
    c.result.status=status==ck3_11906::TacticalDailySentinelArmStatusV1::armed
        ?CoreControlStatusV1::sentinel_armed:CoreControlStatusV1::rejected;
    return true;
  }
  case CoreControlOperationV1::application_exit: {
    if (c.application_exit_session==nullptr) return true;
    const bool previously_claimed=c.application_exit_session->claimed.load(std::memory_order_acquire);
    const auto result=RequestApplicationExitV1(c.application_exit,*c.application_exit_session,
        &BeforeApplicationExit,&admission);
    c.result.effect_attempted=!previously_claimed &&
        c.application_exit_session->claimed.load(std::memory_order_acquire) &&
        (result==ApplicationExitStatusV1::requested || result==ApplicationExitStatusV1::indeterminate);
    if (c.result.status==CoreControlStatusV1::expired || c.result.status==CoreControlStatusV1::stale) return true;
    c.result.status=result==ApplicationExitStatusV1::requested ? CoreControlStatusV1::exit_requested
        : result==ApplicationExitStatusV1::already_requested ? CoreControlStatusV1::exit_already_requested
        : result==ApplicationExitStatusV1::indeterminate ? CoreControlStatusV1::indeterminate
        : result==ApplicationExitStatusV1::claim_consumed ? CoreControlStatusV1::exit_claim_consumed
        : CoreControlStatusV1::unavailable;
    return true;
  }
  case CoreControlOperationV1::pause:
  case CoreControlOperationV1::resume: {
    const bool paused=c.request.operation==CoreControlOperationV1::pause;
    if (current.clock.paused==paused) {
      c.result.status=CoreControlStatusV1::already_satisfied; return true;
    }
    const auto command=MakePauseCommand(c.commands,current.local_player_id,paused);
    submitted=SubmitCommandCopy(c.commands,&command,7,&BeforeQueue,&admission); break;
  }
  case CoreControlOperationV1::speed: {
    const auto speed=c.request.public_speed;
    // Current111 confirms an equal observed value with no native write.
    if(IsFull111(c.core.image_build) && c.native_full_adapter && c.expected_full_snapshot &&
        c.result.full_snapshot_before_verified && speed>=1 && speed<=5 && current.clock.speed==speed) {
      c.result.status=CoreControlStatusV1::already_satisfied;return true;
    }
    if (speed<1 || speed>5 || c.commands.game_speed_count==nullptr ||
        *c.commands.game_speed_count<speed || *c.commands.game_speed_count>1024) return true;
    if (current.clock.speed==speed) {
      c.result.status=CoreControlStatusV1::already_satisfied; return true;
    }
    const auto command=MakeSetSpeedCommand(c.commands,speed);
    submitted=SubmitCommandCopy(c.commands,&command,7,&BeforeQueue,&admission); break;
  }
  case CoreControlOperationV1::save: {
    if (!current.clock.paused) {
      c.result.status=CoreControlStatusV1::requires_paused; return true;
    }
    if(!SaveMappingKnown(c,stamp))return true;
    const auto command=MakeSaveCheckpointCommand(c.commands);
    submitted=SubmitCommandCopy(c.commands,&command,7,&BeforeQueue,&admission); break;
  }
  default: return true;
  }
  if (c.result.status==CoreControlStatusV1::expired ||
      c.result.status==CoreControlStatusV1::stale ||
      c.result.status==CoreControlStatusV1::stale_full_snapshot) return true;
  c.result.status=submitted==CommandSubmitResult::submitted
      ? CoreControlStatusV1::submitted : submitted==CommandSubmitResult::rejected
      ? CoreControlStatusV1::rejected : CoreControlStatusV1::unavailable;
  return true;
}
} // namespace

bool EqualCorePrefixV1(const CoreSnapshotPrefix &a, const CoreSnapshotPrefix &b) noexcept {
  return a.clock.date_raw==b.clock.date_raw && a.clock.speed==b.clock.speed &&
      a.clock.paused==b.clock.paused && a.local_player_id==b.local_player_id &&
      a.map_ready==b.map_ready && a.has_played_character==b.has_played_character &&
      a.played_character_id==b.played_character_id && a.played_character_alive==b.played_character_alive;
}
void ArmCoreControlDeadlineV1(CoreControlContextV1 &c) noexcept {
  const auto now=Wall(c); c.monotonic_deadline_ms=0;
  if (c.request.deadline_unix_ms<=now) return;
  const auto remaining=c.request.deadline_unix_ms-now;
  c.monotonic_deadline_ms=Mono(c)+(remaining<8000?remaining:8000);
}
bool ExecuteCoreControlMailboxV1(void *opaque,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  if (opaque==nullptr) return false;
  auto &c=*static_cast<CoreControlContextV1 *>(opaque);
#if defined(_MSC_VER)
  __try { return Execute(c,stamp); }
  __except (EXCEPTION_EXECUTE_HANDLER) {
    c.result.status=CoreControlStatusV1::indeterminate; return true;
  }
#else
  return Execute(c,stamp);
#endif
}

namespace {
void AppendString(std::string &output, std::string_view value) {
  constexpr char hex[] = "0123456789abcdef";
  output += '"';
  for (const unsigned char character : value) {
    switch (character) {
    case '"': output += "\\\""; break;
    case '\\': output += "\\\\"; break;
    case '\b': output += "\\b"; break;
    case '\f': output += "\\f"; break;
    case '\n': output += "\\n"; break;
    case '\r': output += "\\r"; break;
    case '\t': output += "\\t"; break;
    default:
      if (character < 0x20) {
        output += "\\u00";
        output += hex[character >> 4];
        output += hex[character & 15];
      } else {
        output += static_cast<char>(character);
      }
    }
  }
  output += '"';
}

const char *StatusName(CoreControlStatusV1 status) noexcept {
  switch (status) {
  case CoreControlStatusV1::exit_claim_consumed: return "claim_consumed";
  case CoreControlStatusV1::exit_requested: return "requested";
  case CoreControlStatusV1::exit_already_requested: return "already_requested";
  case CoreControlStatusV1::expired: return "expired";
  case CoreControlStatusV1::stale: return "stale_core_prefix";
  case CoreControlStatusV1::stale_full_snapshot: return "stale_full_snapshot";
  case CoreControlStatusV1::sentinel_armed: return "armed";
  case CoreControlStatusV1::sentinel_canceled: return "canceled";
  case CoreControlStatusV1::requires_map: return "requires_map";
  case CoreControlStatusV1::requires_paused: return "requires_paused";
  case CoreControlStatusV1::already_satisfied: return "already_satisfied";
  case CoreControlStatusV1::rejected: return "rejected";
  case CoreControlStatusV1::submitted: return "submitted";
  case CoreControlStatusV1::indeterminate: return "indeterminate";
  default: return "unavailable";
  }
}
} // namespace
std::string SerializeCoreControlCommandResultV1(std::string_view request_id,
    std::string_view step, const CoreControlResultV1 &result,
    std::string_view result_schema,std::uint64_t checkpoint_sequence,ImageBuildV1 build) {
  const bool accepted=result.status==CoreControlStatusV1::submitted ||
      result.status==CoreControlStatusV1::already_satisfied ||
      result.status==CoreControlStatusV1::exit_requested || result.status==CoreControlStatusV1::exit_already_requested;
  std::string output=R"({"type":"command_result","protocol_version":1,"request_id":)";
  AppendString(output,request_id);
  output += accepted ? R"(,"ok":true,"result":{"schema":)"
                     : R"(,"ok":false,"result":{"schema":)";
  const bool application_exit=step==kApplicationExitStepV1;
  AppendString(output,!result_schema.empty()?result_schema:
      application_exit?kApplicationExitResultSchemaV1:kCoreControlResultSchemaV1);
  output += R"(,"game_version":)"; AppendString(output,GameVersionForBuild(build));
  output += R"(,"executable_sha256":)"; AppendString(output,ExecutableShaForBuild(build));
  output += R"(,"adapter_id":)"; AppendString(output,AdapterIdForBuild(build));
  output += R"(,"backend":)"; AppendString(output,BackendForBuild(build));
  output += R"(,"step":)"; AppendString(output,step);
  output += accepted ? R"(,"accepted":true)" : R"(,"accepted":false)";
  output += application_exit?R"(,"dispatch_status":)":R"(,"queue_status":)"; AppendString(output,StatusName(result.status));
  output += result.effect_attempted ? R"(,"effect_attempted":true)"
                                    : R"(,"effect_attempted":false)";
  if(result_schema==kFullClockControlResultSchemaV1)
    output += result.full_snapshot_before_verified?R"(,"full_snapshot_before_verified":true)":R"(,"full_snapshot_before_verified":false)";
  output += R"(,"complete_snapshot":false,"physical_save_confirmed":false)";
  if (application_exit) output += R"(,"normal_exit_confirmed":false)";
  if (step=="save-checkpoint") {
    output += R"(,"save_name":)"; AppendString(output,kCheckpointSaveName);
  }
  if(result_schema==kFullClockControlResultSchemaV1 && step=="save-checkpoint" &&
      result.status==CoreControlStatusV1::submitted && checkpoint_sequence>0) {
    output += ",\"status\":\"submitted\",\"submission\":{\"sequence\":";
    output += std::to_string(checkpoint_sequence);
    output += ",\"requested_save_name\":";
    AppendString(output,kCheckpointSaveName);
    output += ",\"date_raw\":";
    output += std::to_string(result.observed.clock.date_raw);
    output += '}';
  }
  output += '}';
  if(result_schema==kFullClockControlResultSchemaV1 && !accepted &&
      !result.effect_attempted && result.status!=CoreControlStatusV1::indeterminate) {
    output += R"(,"error":)";
    AppendString(output,std::string("full_clock_")+StatusName(result.status));
  }
  output += '}'; return output;
}
} // namespace xar::ck3_1210
