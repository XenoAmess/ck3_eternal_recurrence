#include "activity_stage5_feast_full_cost_private_transport_v1.hpp"

#include <windows.h>

namespace xar::ck3_11906 {
namespace {

struct CaptureContext {
  ActivityStage5FeastFullCostPrivateQueryV1 *query = nullptr;
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

bool InvokeNamedCost(void *opaque, std::uintptr_t module_base,
                     std::uintptr_t breakdown, std::string_view key,
                     std::uint32_t &resource_index,
                     std::int64_t &cost_raw) noexcept {
  auto &context = *static_cast<CaptureContext *>(opaque);
  if (GetCurrentThreadId() != context.owner_thread_id ||
      module_base != context.module_base || breakdown == 0)
    return false;
  bool succeeded = false;
  __try {
    succeeded = bridge::InvokeActivityStage5NativeNamedFeastCostV1(
        nullptr, module_base, breakdown, key, resource_index, cost_raw);
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    succeeded = false;
  }
  return succeeded;
}

bool EvaluateCanStart(void *opaque, std::uintptr_t planner,
                      bool &output) noexcept {
  auto &context = *static_cast<CaptureContext *>(opaque);
  if (GetCurrentThreadId() != context.owner_thread_id || planner == 0 ||
      context.module_base == 0)
    return false;
  using Predicate = bool (*)(void *, void *);
  const auto predicate =
      reinterpret_cast<Predicate>(context.module_base + 0x10B0DA0);
  __try {
    output = predicate(reinterpret_cast<void *>(planner), nullptr);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
}

} // namespace

bool ExecuteActivityStage5FeastFullCostPrivateV1(
    void *opaque, const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *query = static_cast<ActivityStage5FeastFullCostPrivateQueryV1 *>(opaque);
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
      mailbox.executor != &ExecuteActivityStage5FeastFullCostPrivateV1 ||
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
      query->failure = "exact_activity_stage5_feast_cost_build_unavailable";
      query->completed = true;
      return true;
    }
    CaptureContext context{query, base, stamp.thread_id};
    bridge::ActivityPlannerDiagEnvironmentV1 diagnostic{
        true, bridge::kActivityPlannerDiagExeSha256V1, base, &context,
        &ReadMemory, &ReadFrame, &CastIdler, &InvokeVisibility};
    const bridge::ActivityPlannerDiagFrameV1 expected{
        query->expected_revision, current.date_raw,
        current.played_character_id, true, true, true, true};
    bridge::ActivityStage5FeastFullCostEnvironmentV1 cost_environment{};
    cost_environment.enabled = true;
    cost_environment.gold.diagnostic = diagnostic;
    cost_environment.gold.passive_cost = query->passive_cost;
    cost_environment.invoke_named_cost = &InvokeNamedCost;
    cost_environment.named_context = &context;
    query->cost = bridge::ReadActivityStage5FeastFullCostV1(
        cost_environment, expected);
    if (query->cost.status !=
        bridge::ActivityStage5FeastFullCostStatusV1::observed) {
      query->failure = "native_activity_stage5_full_cost_red:" +
          std::string(bridge::ActivityStage5FeastFullCostStatusKeyV1(
              query->cost.status)) + ":" +
          std::string(bridge::ActivityStage5GoldCostStatusKeyV1(
              query->cost.gold_gate_status));
      query->completed = true;
      return true;
    }
    bridge::ActivityStage5CanStartEnvironmentV1 start_environment{};
    start_environment.diagnostic = diagnostic;
    start_environment.evaluate = &EvaluateCanStart;
    query->can_start = bridge::ReadActivityStage5CanStartV1(
        start_environment, expected);
    if (query->can_start.status !=
            bridge::ActivityStage5CanStartStatusV1::observed ||
        query->can_start.frame != query->cost.frame) {
      query->failure = "native_activity_stage5_canstart_red:" +
          std::string(bridge::ActivityStage5CanStartStatusKeyV1(
              query->can_start.status));
      query->completed = true;
      return true;
    }
    query->completed = true;
    return true;
  } catch (...) {
    query->failure = "native_activity_stage5_feast_full_cost_exception";
    query->completed = true;
    return true;
  }
}

std::string SerializeActivityStage5FeastFullCostPrivateV1(
    const ActivityStage5FeastFullCostPrivateQueryV1 &query) {
  if (!query.completed || !query.failure.empty() ||
      query.cost.status !=
          bridge::ActivityStage5FeastFullCostStatusV1::observed ||
      query.can_start.status !=
          bridge::ActivityStage5CanStartStatusV1::observed ||
      query.cost.frame != query.can_start.frame)
    return {};
  const auto &result = query.cost;
  std::string payload =
      "{\"schema\":\"activity-stage5-feast-full-cost-private-read-v1\","
      "\"snapshot_revision\":" + std::to_string(result.frame.revision) +
      ",\"date_raw\":" + std::to_string(result.frame.date_raw) +
      ",\"actor_character_id\":" +
      std::to_string(result.frame.actor_character_id) +
      ",\"activity_key\":\"activity_feast\",\"planning_stage\":5,"
      "\"normal_refresh_sequence\":" +
      std::to_string(result.normal_refresh_sequence) +
      ",\"scale\":" + std::to_string(result.scale) +
      ",\"actor_gold_raw\":" + std::to_string(result.actor_gold_raw) +
      ",\"resources\":{";
  for (std::size_t index = 0; index < bridge::kActivityFeastCostKeysV1.size();
       ++index) {
    if (index != 0) payload += ",";
    payload += "\"" +
        std::string(bridge::kActivityFeastCostKeysV1[index]) +
        "\":{\"resource_index\":" +
        std::to_string(result.resource_indices[index]) +
        ",\"configured_cost_raw\":" +
        std::to_string(result.configured_cost_raw[index]) + "}";
  }
  payload += "},\"final_can_start\":";
  payload += query.can_start.final_can_start ? "true" : "false";
  payload += ",\"read_only\":true,\"raw_pointer_fields_persisted\":false}";
  return payload;
}

} // namespace xar::ck3_11906
