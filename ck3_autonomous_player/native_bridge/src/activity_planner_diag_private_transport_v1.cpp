#include "activity_planner_diag_private_transport_v1.hpp"

#include <windows.h>

namespace xar::ck3_11906 {
namespace {

bool ReadMemory(void *, std::uintptr_t address, void *output,
                std::size_t size) noexcept {
  SIZE_T read = 0;
  return address != 0 && output != nullptr && size != 0 &&
         ReadProcessMemory(GetCurrentProcess(),
                           reinterpret_cast<const void *>(address), output,
                           size, &read) != 0 && read == size;
}

struct CaptureContext {
  ActivityPlannerDiagPrivateQueryV1 *query = nullptr;
  std::uintptr_t module_base = 0;
  DWORD owner_thread_id = 0;
};

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
                      std::uintptr_t exact_entry, bool &output) noexcept {
  if (planner == 0 || exact_entry == 0) return false;
  using NativeVisibility = bool (*)(void *);
  const auto visible = reinterpret_cast<NativeVisibility>(exact_entry);
  __try {
    output = visible(reinterpret_cast<void *>(planner));
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
}

bool IsSuccessful(bridge::ActivityPlannerDiagStatusV1 status) noexcept {
  return status == bridge::ActivityPlannerDiagStatusV1::observed ||
         status == bridge::ActivityPlannerDiagStatusV1::planner_absent;
}

} // namespace

bool ExecuteActivityPlannerDiagPrivateQueryV1(
    void *opaque, const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *query = static_cast<ActivityPlannerDiagPrivateQueryV1 *>(opaque);
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
      mailbox.executor != &ExecuteActivityPlannerDiagPrivateQueryV1 ||
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
    bridge::ActivityPlannerDiagEnvironmentV1 environment{};
    environment.enabled = true;
    environment.admitted_executable_sha256 =
        bridge::kActivityPlannerDiagExeSha256V1;
    environment.module_base = module_base;
    environment.context = &context;
    environment.read_memory = &ReadMemory;
    environment.read_frame = &ReadFrame;
    environment.rtti_cast = &CastIdler;
    environment.invoke_visibility = &InvokeVisibility;
    const bridge::ActivityPlannerDiagFrameV1 expected{
        query->expected_revision, current.date_raw,
        current.played_character_id, true, true, true, true};
    query->diagnostic = bridge::ReadActivityPlannerDiagV1(environment, expected);
    if (!IsSuccessful(query->diagnostic.status))
      query->failure = "native_activity_planner_diag_red:" +
                       std::string(bridge::ActivityPlannerDiagStatusKeyV1(
                           query->diagnostic.status));
    query->completed = true;
    return true;
  } catch (...) {
    query->failure = "native_activity_planner_diag_exception";
    query->completed = true;
    return true;
  }
}

std::string SerializeActivityPlannerDiagPrivateQueryV1(
    const ActivityPlannerDiagPrivateQueryV1 &query) {
  if (!query.completed || !query.failure.empty() ||
      !IsSuccessful(query.diagnostic.status))
    return {};
  const auto &value = query.diagnostic.value;
  std::string out =
      "{\"schema\":\"activity-planner-diag-private-read-v1\","
      "\"snapshot_revision\":" + std::to_string(query.expected_revision) +
      ",\"date_raw\":" +
      std::to_string(query.expected_snapshot.date_raw) +
      ",\"actor_character_id\":" +
      std::to_string(query.expected_snapshot.played_character_id) +
      ",\"planner_status\":\"" +
      std::string(bridge::ActivityPlannerDiagStatusKeyV1(
          query.diagnostic.status)) +
      "\",\"planner_present\":" +
      (value.planner_present ? "true" : "false") +
      ",\"widget_attached\":" +
      (value.widget_attached ? "true" : "false") +
      ",\"widget_visible\":" +
      (value.widget_visible ? "true" : "false") +
      ",\"planning_stage\":";
  if (value.planner_present) out += std::to_string(value.stage);
  else out += "null";
  out += ",\"host_view_activity_key_source\":\"host_view_current_type\","
         "\"host_view_activity_key\":";
  if (value.host_view_activity_key_known) {
    out += '"';
    out.append(value.host_view_activity_key.data(),
               value.host_view_activity_key_size);
    out += '"';
  } else {
    out += "null";
  }
  out += ",\"configured_cost_state\":\"unknown\","
         "\"final_can_start_state\":\"unknown\","
         "\"raw_pointer_fields_persisted\":false}";
  return out;
}

} // namespace xar::ck3_11906
