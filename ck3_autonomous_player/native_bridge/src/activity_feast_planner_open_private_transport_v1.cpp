#include "activity_feast_planner_open_private_transport_v1.hpp"

#include <windows.h>

#include <array>
#include <cstring>

namespace xar::ck3_11906 {
namespace {

struct CaptureContext {
  ActivityFeastPlannerOpenPrivateQueryV1 *query = nullptr;
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
  if (context.module_base == 0 || source == 0) return 0;
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

struct NativeTypePayload {
  std::uintptr_t descriptor = 0;
  std::array<std::uint8_t, 32> data{};
};
static_assert(sizeof(NativeTypePayload) == 0x28);

bool DispatchFeast(void *opaque, std::uintptr_t handler,
                  std::uintptr_t type) noexcept {
  auto &context = *static_cast<CaptureContext *>(opaque);
  if (handler == 0 || type == 0 || context.module_base == 0 ||
      GetCurrentThreadId() != context.owner_thread_id)
    return false;
  using DescriptorProvider = void *(*)();
  using NativeDispatch = void (*)(void *, std::int32_t, const void *);
  const auto descriptor = reinterpret_cast<DescriptorProvider>(
      context.module_base + 0xCAF920);
  const auto dispatch = reinterpret_cast<NativeDispatch>(
      context.module_base + 0xA79700);
  NativeTypePayload payload{};
  std::memcpy(payload.data.data(), &type, sizeof(type));
  __try {
    payload.descriptor = reinterpret_cast<std::uintptr_t>(descriptor());
    if (payload.descriptor != context.module_base + 0x4FE3DB0) return false;
    dispatch(reinterpret_cast<void *>(handler), 0x65, &payload);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
}

} // namespace

bool ExecuteActivityFeastPlannerOpenPrivateV1(
    void *opaque, const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *query = static_cast<ActivityFeastPlannerOpenPrivateQueryV1 *>(opaque);
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
      mailbox.executor != &ExecuteActivityFeastPlannerOpenPrivateV1 ||
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
    const auto module_base =
        reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
    if (!query->bindings.enabled || module_base == 0) {
      query->failure = "exact_activity_planner_build_unavailable";
      query->completed = true;
      return true;
    }
    CaptureContext context{query, module_base, stamp.thread_id};
    bridge::ActivityFeastPlannerOpenEnvironmentV1 environment{};
    auto &diagnostic = environment.diagnostic;
    diagnostic.enabled = true;
    diagnostic.admitted_executable_sha256 =
        bridge::kActivityPlannerDiagExeSha256V1;
    diagnostic.module_base = module_base;
    diagnostic.context = &context;
    diagnostic.read_memory = &ReadMemory;
    diagnostic.read_frame = &ReadFrame;
    diagnostic.rtti_cast = &CastIdler;
    diagnostic.invoke_visibility = &InvokeVisibility;
    environment.dispatch = &DispatchFeast;
    const bridge::ActivityPlannerDiagFrameV1 expected{
        query->expected_revision, current.date_raw,
        current.played_character_id, true, true, true, true};
    query->result = bridge::OpenActivityFeastPlannerV1(environment, expected);
    if (query->result.status !=
            bridge::ActivityFeastPlannerOpenStatusV1::opened &&
        query->result.status !=
            bridge::ActivityFeastPlannerOpenStatusV1::already_open)
      query->failure = "native_activity_feast_open_red:" +
                       std::string(bridge::ActivityFeastPlannerOpenStatusKeyV1(
                           query->result.status));
    query->completed = true;
    return true;
  } catch (...) {
    query->failure = "native_activity_feast_open_exception";
    query->completed = true;
    return true;
  }
}

std::string SerializeActivityFeastPlannerOpenPrivateV1(
    const ActivityFeastPlannerOpenPrivateQueryV1 &query) {
  if (!query.completed) return {};
  const auto &result = query.result;
  const auto &value = result.after.value;
  std::string out =
      "{\"schema\":\"activity-feast-planner-open-private-v1\",";
  out += "\"snapshot_revision\":" +
         std::to_string(query.expected_revision) +
         ",\"date_raw\":" +
         std::to_string(query.expected_snapshot.date_raw) +
         ",\"actor_character_id\":" +
         std::to_string(query.expected_snapshot.played_character_id) +
         ",\"open_status\":\"" +
         bridge::ActivityFeastPlannerOpenStatusKeyV1(result.status) +
         "\",\"native_dispatch_invoked\":" +
         (result.native_dispatch_invoked ? "true" : "false") +
         ",\"selected_feast_verified\":" +
         (result.selected_feast_verified ? "true" : "false") +
         ",\"widget_attached\":" +
         (value.widget_attached ? "true" : "false") +
         ",\"widget_visible\":" +
         (value.widget_visible ? "true" : "false") +
         ",\"planning_stage\":";
  if (result.after.status == bridge::ActivityPlannerDiagStatusV1::observed)
    out += std::to_string(value.stage);
  else out += "null";
  out += ",\"configured_cost_state\":\"unknown\",";
  out += "\"final_can_start_state\":\"unknown\",";
  out += "\"raw_pointer_fields_persisted\":false}";
  return out;
}

} // namespace xar::ck3_11906
