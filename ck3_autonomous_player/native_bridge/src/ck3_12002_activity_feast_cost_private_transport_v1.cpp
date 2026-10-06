#include "ck3_12002_activity_feast_cost_private_transport_v1.hpp"
#include "xar_bridge/ck3_12002_activity_feast_costs.hpp"

#include <windows.h>

namespace xar::ck3_12002 {
namespace {

struct CaptureContextGold {
  ActivityStage5GoldCostPrivateQueryV1 *query = nullptr;
  std::uintptr_t module_base = 0;
  DWORD owner_thread_id = 0;
};

bool ReadMemoryGold(void *, std::uintptr_t address, void *output,
                std::size_t size) noexcept {
  SIZE_T read = 0;
  return address != 0 && output != nullptr && size != 0 &&
         ReadProcessMemory(GetCurrentProcess(),
                           reinterpret_cast<const void *>(address), output,
                           size, &read) != 0 && read == size;
}

bool ReadFrameGold(void *opaque,
               bridge::ActivityPlannerDiagFrameV1 &output) noexcept {
  auto &context = *static_cast<CaptureContextGold *>(opaque);
  game::Snapshot snapshot{};
  if (GetCurrentThreadId() != context.owner_thread_id ||
      (context.query->read_snapshot == nullptr || !context.query->read_snapshot(context.query->native_context, snapshot)))
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

std::uintptr_t CastIdlerGold(void *opaque, std::uintptr_t source,
                         std::uintptr_t source_type,
                         std::uintptr_t target_type) noexcept {
  auto &context = *static_cast<CaptureContextGold *>(opaque);
  if (context.module_base == 0 || source == 0 ||
      GetCurrentThreadId() != context.owner_thread_id)
    return 0;
  using NativeCast = void *(*)(void *, std::int32_t, void *, void *, std::int32_t);
  const auto cast = reinterpret_cast<NativeCast>(context.module_base +
      bridge::Activity12004RvaV1(context.query->executable_sha256, 0x4260E94));
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

bool InvokeVisibilityGold(void *opaque, std::uintptr_t planner,
                      std::uintptr_t entry, bool &output) noexcept {
  auto &context = *static_cast<CaptureContextGold *>(opaque);
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

bool InvokeGoldCostGold(void *opaque, std::uintptr_t module_base,
                    std::uintptr_t breakdown,
                    std::int64_t &gold_raw) noexcept {
  auto &context = *static_cast<CaptureContextGold *>(opaque);
  if (GetCurrentThreadId() != context.owner_thread_id ||
      module_base != context.module_base || breakdown == 0)
    return false;
  bool succeeded = false;
  __try {
    succeeded = bridge::InvokeActivityStage5NativeGoldCost12002V1(
        &context.query->executable_sha256, module_base, breakdown, gold_raw);
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
    if ((query->read_snapshot == nullptr || !query->read_snapshot(query->native_context, current)) ||
        current != query->expected_snapshot || !current.paused ||
        !current.map_ready || !current.has_played_character ||
        !current.played_character_alive || current.date_raw != stamp.date_raw) {
      query->frame_changed = true;
      query->failure = "published_frame_changed";
      query->completed = true;
      return true;
    }
    const auto base = query->module_base;
    if (!query->enabled || !bridge::IsActivityFeastCostsModernBuildV1(query->executable_sha256) || base == 0 ||
        !query->passive_cost->installed) {
      query->failure = "exact_activity_stage5_gold_build_unavailable";
      query->completed = true;
      return true;
    }
    CaptureContextGold context{query, base, stamp.thread_id};
    bridge::ActivityStage5GoldCostEnvironmentV1 environment{};
    environment.enabled = true;
    environment.diagnostic = {true,
                              query->executable_sha256,
                              base,
                              &context,
                              &ReadMemoryGold,
                              &ReadFrameGold,
                              &CastIdlerGold,
                              &InvokeVisibilityGold};
    environment.passive_cost = query->passive_cost;
    environment.invoke_gold_cost = &InvokeGoldCostGold;
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

} // namespace xar::ck3_12002

#include "ck3_12002_activity_feast_cost_private_transport_v1.hpp"
#include "xar_bridge/ck3_12002_activity_feast_costs.hpp"

#include <windows.h>

namespace xar::ck3_12002 {
namespace {

struct CaptureContextFullCost {
  ActivityStage5FeastFullCostPrivateQueryV1 *query = nullptr;
  std::uintptr_t module_base = 0;
  DWORD owner_thread_id = 0;
};

bool ReadMemoryFullCost(void *, std::uintptr_t address, void *output,
                std::size_t size) noexcept {
  SIZE_T read = 0;
  return address != 0 && output != nullptr && size != 0 &&
         ReadProcessMemory(GetCurrentProcess(),
                           reinterpret_cast<const void *>(address), output,
                           size, &read) != 0 && read == size;
}

bool ReadFrameFullCost(void *opaque,
               bridge::ActivityPlannerDiagFrameV1 &output) noexcept {
  auto &context = *static_cast<CaptureContextFullCost *>(opaque);
  game::Snapshot snapshot{};
  if (GetCurrentThreadId() != context.owner_thread_id ||
      (context.query->read_snapshot == nullptr || !context.query->read_snapshot(context.query->native_context, snapshot)))
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

std::uintptr_t CastIdlerFullCost(void *opaque, std::uintptr_t source,
                         std::uintptr_t source_type,
                         std::uintptr_t target_type) noexcept {
  auto &context = *static_cast<CaptureContextFullCost *>(opaque);
  if (context.module_base == 0 || source == 0 ||
      GetCurrentThreadId() != context.owner_thread_id)
    return 0;
  using NativeCast = void *(*)(void *, std::int32_t, void *, void *, std::int32_t);
  const auto cast = reinterpret_cast<NativeCast>(context.module_base +
      bridge::Activity12004RvaV1(context.query->executable_sha256, 0x4260E94));
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

bool InvokeVisibilityFullCost(void *opaque, std::uintptr_t planner,
                      std::uintptr_t entry, bool &output) noexcept {
  auto &context = *static_cast<CaptureContextFullCost *>(opaque);
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

bool InvokeNamedCostFullCost(void *opaque, std::uintptr_t module_base,
                     std::uintptr_t breakdown, std::string_view key,
                     std::uint32_t &resource_index,
                     std::int64_t &cost_raw) noexcept {
  auto &context = *static_cast<CaptureContextFullCost *>(opaque);
  if (GetCurrentThreadId() != context.owner_thread_id ||
      module_base != context.module_base || breakdown == 0)
    return false;
  bool succeeded = false;
  __try {
    succeeded = bridge::InvokeActivityStage5NativeNamedFeastCost12002V1(
        &context.query->executable_sha256, module_base, breakdown, key, resource_index, cost_raw);
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    succeeded = false;
  }
  return succeeded;
}

bool EvaluateCanStartFullCost(void *opaque, std::uintptr_t planner,
                      bool &output) noexcept {
  auto &context = *static_cast<CaptureContextFullCost *>(opaque);
  if (GetCurrentThreadId() != context.owner_thread_id || planner == 0 ||
      context.module_base == 0)
    return false;
  const auto predicate =
      reinterpret_cast<ck3_11906::ActivityStage5CanStartPredicateV1>(
          context.module_base + bridge::Activity12004RvaV1(context.query->executable_sha256, 0x11B8670));
  const auto destroy_string =
      reinterpret_cast<ck3_11906::ActivityStage5NativeStringDestroyV1>(
          context.module_base + bridge::Activity12004RvaV1(context.query->executable_sha256, 0x856050));
  bool succeeded = false;
  __try {
    succeeded = ck3_11906::InvokeActivityStage5CanStartWithDisplayV1(
        reinterpret_cast<void *>(planner), predicate, destroy_string,
        context.query->can_start_failure_display);
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
  if (succeeded) output = context.query->can_start_failure_display.allowed;
  return succeeded;
}

void AppendCanStartFailureDisplayFullCost(
    std::string &payload, const ck3_11906::ActivityStage5FailureDisplayV1 &display,
    bool can_start) {
  if (can_start) {
    payload += "{\"state\":\"not_applicable\",\"value\":null,"
               "\"unknown_reason\":null}";
    return;
  }
  if (display.size == 0) {
    payload += "{\"state\":\"unknown\",\"value\":null,"
               "\"unknown_reason\":\"native_failure_display_empty\"}";
    return;
  }
  payload += "{\"state\":\"known\",\"value\":\"";
  constexpr char hex[] = "0123456789abcdef";
  for (std::size_t index = 0; index < display.size; ++index) {
    const auto byte = static_cast<unsigned char>(display.bytes[index]);
    if (byte == '"' || byte == '\\') {
      payload += '\\';
      payload += static_cast<char>(byte);
    } else if (byte < 0x20) {
      payload += "\\u00";
      payload += hex[byte >> 4];
      payload += hex[byte & 0x0F];
    } else {
      payload += static_cast<char>(byte);
    }
  }
  payload += "\",\"unknown_reason\":null}";
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
    if ((query->read_snapshot == nullptr || !query->read_snapshot(query->native_context, current)) ||
        current != query->expected_snapshot || !current.paused ||
        !current.map_ready || !current.has_played_character ||
        !current.played_character_alive || current.date_raw != stamp.date_raw) {
      query->frame_changed = true;
      query->failure = "published_frame_changed";
      query->completed = true;
      return true;
    }
    const auto base = query->module_base;
    if (!query->enabled || !bridge::IsActivityFeastCostsModernBuildV1(query->executable_sha256) || base == 0 ||
        !query->passive_cost->installed) {
      query->failure = "exact_activity_stage5_feast_cost_build_unavailable";
      query->completed = true;
      return true;
    }
    CaptureContextFullCost context{query, base, stamp.thread_id};
    bridge::ActivityPlannerDiagEnvironmentV1 diagnostic{
        true, query->executable_sha256, base, &context,
        &ReadMemoryFullCost, &ReadFrameFullCost, &CastIdlerFullCost, &InvokeVisibilityFullCost};
    const bridge::ActivityPlannerDiagFrameV1 expected{
        query->expected_revision, current.date_raw,
        current.played_character_id, true, true, true, true};
    bridge::ActivityStage5FeastFullCostEnvironmentV1 cost_environment{};
    cost_environment.enabled = true;
    cost_environment.gold.enabled = true;
    cost_environment.gold.diagnostic = diagnostic;
    cost_environment.gold.passive_cost = query->passive_cost;
    cost_environment.invoke_named_cost = &InvokeNamedCostFullCost;
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
    start_environment.evaluate = &EvaluateCanStartFullCost;
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
  payload += ",\"final_can_start_failure_display\":";
  AppendCanStartFailureDisplayFullCost(payload, query.can_start_failure_display,
                               query.can_start.final_can_start);
  payload += ",\"read_only\":true,\"raw_pointer_fields_persisted\":false}";
  return payload;
}

} // namespace xar::ck3_12002
