#include "ck3_12002_activity_stage5_canstart_private_transport_v1.hpp"

#include <windows.h>

namespace xar::ck3_12002 {
using ck3_11906::MainThreadExecutionStampV1;
using ck3_11906::MainThreadQueryMailboxStateV1;
using ck3_11906::kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs;
namespace {

struct CaptureContext {
  ActivityStage5CanStartPrivate12002QueryV1 *query = nullptr;
  std::uintptr_t module_base = 0;
  DWORD owner_thread_id = 0;
};

bool ReadMemory(void *, std::uintptr_t address, void *output,
                std::size_t size) noexcept {
  SIZE_T read = 0;
  return address != 0 && output != nullptr && size != 0 &&
         ReadProcessMemory(GetCurrentProcess(),
                           reinterpret_cast<const void *>(address), output,
                           size, &read) != 0 && read == size;
}

bool ReadFrame(void *opaque,
               bridge::ActivityPlannerDiagFrameV1 &output) noexcept {
  auto &context = *static_cast<CaptureContext *>(opaque);
  game::Snapshot snapshot{};
  if (GetCurrentThreadId() != context.owner_thread_id ||
      context.query->read_snapshot == nullptr ||
      !context.query->read_snapshot(context.query->native_context, snapshot))
    return false;
  output = {context.query->expected_revision,
            snapshot.date_raw,
            snapshot.played_character_id,
            true,
            snapshot.paused,
            snapshot.map_ready,
            snapshot.has_played_character && snapshot.played_character_alive};
  return true;
}

std::uintptr_t CastIdler(void *opaque, std::uintptr_t source,
                         std::uintptr_t source_type,
                         std::uintptr_t target_type) noexcept {
  auto &context = *static_cast<CaptureContext *>(opaque);
  if (context.module_base == 0 || source == 0 ||
      GetCurrentThreadId() != context.owner_thread_id)
    return 0;
  using NativeCast = void *(*)(void *, std::int32_t, void *, void *, std::int32_t);
  const auto cast = reinterpret_cast<NativeCast>(context.module_base +
                                                 0x4260E94);
  void *result = nullptr;
  __try {
    result = cast(reinterpret_cast<void *>(source), 0,
                  reinterpret_cast<void *>(source_type),
                  reinterpret_cast<void *>(target_type), 0);
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    result = nullptr;
  }
  return reinterpret_cast<std::uintptr_t>(result);
}

bool InvokeVisibility(void *, std::uintptr_t planner,
                      std::uintptr_t entry, bool &output) noexcept {
  if (planner == 0 || entry == 0) return false;
  const auto visible = reinterpret_cast<bool (*)(void *)>(entry);
  __try {
    output = visible(reinterpret_cast<void *>(planner));
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
}

bool EvaluateCanStart(void *opaque, std::uintptr_t planner,
                      bool &output) noexcept {
  auto &context = *static_cast<CaptureContext *>(opaque);
  if (GetCurrentThreadId() != context.owner_thread_id || planner == 0 ||
      context.module_base == 0)
    return false;
  // At stage 5 the original evaluator builds and validates a temporary
  // CStartActivityCommand. nullptr requests no native failure string.
  using Predicate = bool (*)(void *, void *);
  const auto predicate =
      reinterpret_cast<Predicate>(context.module_base + kFeastFinalCanStartRva);
  __try {
    output = predicate(reinterpret_cast<void *>(planner), nullptr);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
}

} // namespace

bool ExecuteActivityStage5CanStartPrivate12002V1(
    void *opaque, const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *query = static_cast<ActivityStage5CanStartPrivate12002QueryV1 *>(opaque);
  if (query == nullptr || query->mailbox == nullptr ||
      query->ticket.sequence == 0 || query->expected_revision == 0 ||
      query->invocations != 0 || stamp.pump_epoch == 0 || stamp.thread_id == 0 ||
      !stamp.paused || stamp.tls_initialized_flag_address == 0 ||
      stamp.tls_initialized != 1 || stamp.tls_context == 0 ||
      stamp.tls_main_thread_marker != 1 || stamp.jomini_state == 0 ||
      stamp.game_state == 0 || GetCurrentThreadId() != stamp.thread_id)
    return false;
  auto &mailbox = *query->mailbox;
  if (mailbox.state.load(std::memory_order_acquire) !=
          MainThreadQueryMailboxStateV1::executing ||
      mailbox.stop_requested.load(std::memory_order_acquire) ||
      mailbox.failure_flags.load(std::memory_order_acquire) != 0 ||
      mailbox.published_sequence.load(std::memory_order_acquire) !=
          query->ticket.sequence ||
      mailbox.owner_thread_id.load(std::memory_order_acquire) != stamp.thread_id ||
      mailbox.paused_owner_verified_pump_epochs.load(std::memory_order_acquire) <
          kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs ||
      mailbox.executor != &ExecuteActivityStage5CanStartPrivate12002V1 ||
      mailbox.executor_context != query)
    return false;
  try {
    ++query->invocations;
    game::Snapshot current{};
    if (query->read_snapshot == nullptr ||
        !query->read_snapshot(query->native_context, current) ||
        current != query->expected_snapshot || !current.paused ||
        !current.map_ready || !current.has_played_character ||
        !current.played_character_alive || current.date_raw != stamp.date_raw) {
      query->frame_changed = true;
      query->failure = "published_frame_changed";
      query->completed = true;
      return true;
    }
    const auto base = query->module_base;
    if (!query->enabled || base == 0 ||
        query->executable_sha256 != kFeastExecutableSha256) {
      query->failure = "exact_activity_stage5_build_unavailable";
      query->completed = true;
      return true;
    }
    CaptureContext context{query, base, stamp.thread_id};
    bridge::ActivityStage5CanStartEnvironmentV1 environment{};
    environment.diagnostic = {true,
                              kFeastExecutableSha256,
                              base,
                              &context,
                              &ReadMemory,
                              &ReadFrame,
                              &CastIdler,
                              &InvokeVisibility};
    environment.evaluate = &EvaluateCanStart;
    const bridge::ActivityPlannerDiagFrameV1 expected{
        query->expected_revision, current.date_raw,
        current.played_character_id, true, true, true, true};
    query->result = bridge::ReadActivityStage5CanStartV1(environment, expected);
    if (query->result.status !=
        bridge::ActivityStage5CanStartStatusV1::observed)
      query->failure = "native_activity_stage5_canstart_red:" +
          std::string(bridge::ActivityStage5CanStartStatusKeyV1(
              query->result.status));
    query->completed = true;
    return true;
  } catch (...) {
    query->failure = "native_activity_stage5_canstart_exception";
    query->completed = true;
    return true;
  }
}

std::string SerializeActivityStage5CanStartPrivate12002V1(
    const ActivityStage5CanStartPrivate12002QueryV1 &query) {
  return ck3_11906::SerializeActivityStage5CanStartPrivateV1(query);
}
} // namespace xar::ck3_12002
