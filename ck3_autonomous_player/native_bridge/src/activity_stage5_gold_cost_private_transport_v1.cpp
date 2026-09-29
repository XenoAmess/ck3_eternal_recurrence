#include "activity_stage5_gold_cost_private_transport_v1.hpp"

#include <windows.h>

namespace xar::ck3_11906 {
namespace {

struct CaptureContext {
  ActivityStage5GoldCostPrivateQueryV1 *query = nullptr;
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
      !ReadSnapshot(context.query->bindings, snapshot))
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
                                                 0x3E631F4);
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

bool InvokeVisibility(void *opaque, std::uintptr_t planner,
                      std::uintptr_t entry, bool &output) noexcept {
  auto &context = *static_cast<CaptureContext *>(opaque);
  if (GetCurrentThreadId() != context.owner_thread_id || planner == 0 ||
      entry == 0)
    return false;
  const auto visible = reinterpret_cast<bool (*)(void *)>(entry);
  __try {
    output = visible(reinterpret_cast<void *>(planner));
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
}

bool InvokeGoldCost(void *opaque, std::uintptr_t module_base,
                    std::uintptr_t breakdown,
                    std::int64_t &gold_raw) noexcept {
  auto &context = *static_cast<CaptureContext *>(opaque);
  if (GetCurrentThreadId() != context.owner_thread_id ||
      module_base != context.module_base || breakdown == 0)
    return false;
  bool succeeded = false;
  __try {
    succeeded = bridge::InvokeActivityStage5NativeGoldCostV1(
        nullptr, module_base, breakdown, gold_raw);
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    succeeded = false;
  }
  return succeeded;
}

} // namespace

bool ExecuteActivityStage5GoldCostPrivateV1(
    void *opaque, const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *query = static_cast<ActivityStage5GoldCostPrivateQueryV1 *>(opaque);
  if (query == nullptr || query->mailbox == nullptr ||
      query->passive_cost == nullptr || query->ticket.sequence == 0 ||
      query->expected_revision == 0 || query->invocations != 0 ||
      stamp.pump_epoch == 0 || stamp.thread_id == 0 || !stamp.paused ||
      stamp.tls_initialized_flag_address == 0 ||
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
      mailbox.executor != &ExecuteActivityStage5GoldCostPrivateV1 ||
      mailbox.executor_context != query)
    return false;
  try {
    ++query->invocations;
    game::Snapshot current{};
    if (!ReadSnapshot(query->bindings, current) ||
        current != query->expected_snapshot || !current.paused ||
        !current.map_ready || !current.has_played_character ||
        !current.played_character_alive || current.date_raw != stamp.date_raw) {
      query->frame_changed = true;
      query->failure = "published_frame_changed";
      query->completed = true;
      return true;
    }
    const auto base = reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
    if (!query->bindings.enabled || base == 0 ||
        !query->passive_cost->installed) {
      query->failure = "exact_activity_stage5_gold_build_unavailable";
      query->completed = true;
      return true;
    }
    CaptureContext context{query, base, stamp.thread_id};
    bridge::ActivityStage5GoldCostEnvironmentV1 environment{};
    environment.enabled = true;
    environment.diagnostic = {true,
                              bridge::kActivityPlannerDiagExeSha256V1,
                              base,
                              &context,
                              &ReadMemory,
                              &ReadFrame,
                              &CastIdler,
                              &InvokeVisibility};
    environment.passive_cost = query->passive_cost;
    environment.invoke_gold_cost = &InvokeGoldCost;
    const bridge::ActivityPlannerDiagFrameV1 expected{
        query->expected_revision, current.date_raw,
        current.played_character_id, true, true, true, true};
    query->result = bridge::ReadActivityStage5GoldCostV1(
        environment, expected);
    if (query->result.status != bridge::ActivityStage5GoldCostStatusV1::observed)
      query->failure = "native_activity_stage5_gold_red:" +
          std::string(bridge::ActivityStage5GoldCostStatusKeyV1(
              query->result.status));
    query->completed = true;
    return true;
  } catch (...) {
    query->failure = "native_activity_stage5_gold_exception";
    query->completed = true;
    return true;
  }
}

std::string SerializeActivityStage5GoldCostPrivateV1(
    const ActivityStage5GoldCostPrivateQueryV1 &query) {
  if (!query.completed || !query.failure.empty() ||
      query.result.status != bridge::ActivityStage5GoldCostStatusV1::observed)
    return {};
  const auto &result = query.result;
  return "{\"schema\":\"activity-stage5-gold-cost-private-read-v1\","
         "\"snapshot_revision\":" + std::to_string(result.frame.revision) +
         ",\"date_raw\":" + std::to_string(result.frame.date_raw) +
         ",\"actor_character_id\":" +
         std::to_string(result.frame.actor_character_id) +
         ",\"activity_key\":\"activity_feast\",\"planning_stage\":5,"
         "\"normal_refresh_sequence\":" +
         std::to_string(result.normal_refresh_sequence) +
         ",\"configured_cost\":{\"resource\":\"gold\",\"raw\":" +
         std::to_string(result.gold_cost_raw) +
         ",\"scale\":100000,\"source\":\"CostBreakdown.GetCost\"},"
         "\"resource_value\":{\"resource\":\"gold\",\"raw\":" +
         std::to_string(result.actor_gold_raw) +
         ",\"scale\":100000,\"source\":\"CCharacter.GetGold\"},"
         "\"final_can_start\":null,\"raw_slot12_resource_mapping\":null,"
         "\"read_only\":true,\"raw_pointer_fields_persisted\":false}";
}

} // namespace xar::ck3_11906
