#include "ck3_12002_feast_planner_private_transport_v1.hpp"

#include "xar_bridge/ck3_12002_activity_hosted_identity.hpp"
#include "xar_bridge/ck3_12003.hpp"

#include <windows.h>

#include <array>
#include <limits>

namespace xar::ck3_12002 {
namespace {

using ck3_11906::MainThreadExecutionStampV1;
using ck3_11906::MainThreadQueryExecutorV1;

template <class Query>
bool Prepare(Query &query, const MainThreadExecutionStampV1 &stamp,
             MainThreadQueryExecutorV1 executor, game::Snapshot &current,
             ActivityPlanner12002NativeV1 &native) {
  if (query.mailbox == nullptr || query.ticket.sequence == 0 ||
      query.expected_revision == 0 || query.invocations != 0 ||
      stamp.pump_epoch == 0 || stamp.thread_id == 0 || !stamp.paused ||
      stamp.tls_initialized_flag_address == 0 || stamp.tls_initialized != 1 ||
      stamp.tls_context == 0 || stamp.tls_main_thread_marker != 1 ||
      stamp.jomini_state == 0 || stamp.game_state == 0 ||
      GetCurrentThreadId() != stamp.thread_id)
    return false;
  auto &mailbox = *query.mailbox;
  if (mailbox.state.load(std::memory_order_acquire) !=
          ck3_11906::MainThreadQueryMailboxStateV1::executing ||
      mailbox.stop_requested.load(std::memory_order_acquire) ||
      mailbox.failure_flags.load(std::memory_order_acquire) != 0 ||
      mailbox.published_sequence.load(std::memory_order_acquire) != query.ticket.sequence ||
      mailbox.owner_thread_id.load(std::memory_order_acquire) != stamp.thread_id ||
      mailbox.paused_owner_verified_pump_epochs.load(std::memory_order_acquire) <
          ck3_11906::kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs ||
      mailbox.executor != executor || mailbox.executor_context != &query)
    return false;
  ++query.invocations;
  if (query.read_snapshot == nullptr ||
      !query.read_snapshot(query.native_context, current) ||
      current != query.expected_snapshot || !current.paused ||
      !current.map_ready || !current.has_played_character ||
      !current.played_character_alive || current.date_raw != stamp.date_raw) {
    if constexpr (requires { query.frame_changed; }) query.frame_changed = true;
    query.failure = "published_frame_changed";
    query.completed = true;
    return false;
  }
  if (!query.enabled || !BindActivityPlanner12002V1(
          native, query.module_base, query.executable_sha256,
          query.native_context, query.read_snapshot, query.read_memory,
          query.resolve_script_identifier, query.expected_revision,
          stamp.thread_id, stamp.game_state)) {
    query.failure = "exact_activity_planner_12002_build_unavailable";
    query.completed = true;
    return false;
  }
  return true;
}

bridge::ActivityPlannerDiagFrameV1 ExpectedFrame(
    std::uint64_t revision, const game::Snapshot &snapshot) noexcept {
  return {revision, snapshot.date_raw, snapshot.played_character_id,
          true, true, true, true};
}

bool SuccessfulDiagnostic(bridge::ActivityPlannerDiagStatusV1 status) noexcept {
  return status == bridge::ActivityPlannerDiagStatusV1::observed ||
         status == bridge::ActivityPlannerDiagStatusV1::planner_absent;
}

template <class T>
bool ReadCurrentActivityAt(
    const bridge::ActivityPlannerDiagEnvironmentV1 &environment,
    std::uintptr_t base, std::size_t offset, T &output) noexcept {
  return base != 0 &&
         offset <= (std::numeric_limits<std::uintptr_t>::max)() - base &&
         environment.read_memory != nullptr &&
         environment.read_memory(environment.context, base + offset,
                                 &output, sizeof(output));
}

bool ResolveCurrentFeastActivity12003(
    ActivityPlanner12002NativeV1 &native, std::uint32_t full_id,
    std::int32_t host_id, std::uintptr_t &activity) noexcept {
  activity = 0;
  if (full_id == 0 || full_id == 0xFFFFFFFFU || host_id <= 0) return false;
  const auto environment = BuildActivityPlanner12002DiagEnvironmentV1(native);
  const auto index = full_id & 0x00FFFFFFU;
  std::uintptr_t root = 0, world = 0, manager = 0, chunks = 0;
  std::uintptr_t index_table = 0, object = 0, chunk = 0;
  std::uint32_t chunk_count = 0, capacity = 0;
  std::int32_t highest_live = -1;
  std::uint8_t initialized = 0;
  if (!ReadCurrentActivityAt(environment, native.module_base,
                             bridge::ActivityHostedCrozierRvaV1(
                                 native.executable_sha256,
                                 bridge::kActivityHosted12002GameStateRva), root) ||
      root == 0 || root != native.game_state ||
      !ReadCurrentActivityAt(environment, root, 0xA0, world) || world == 0 ||
      bridge::kActivityHosted12002ManagerOffset >
          (std::numeric_limits<std::uintptr_t>::max)() - world)
    return false;
  manager = world + bridge::kActivityHosted12002ManagerOffset;
  // Reuse the hosted identity manager layout for this one full ID; no scan.
  if (!ReadCurrentActivityAt(environment, manager, 0x10, initialized) ||
      initialized == 0 ||
      !ReadCurrentActivityAt(environment, manager, 0x20, chunks) || chunks == 0 ||
      !ReadCurrentActivityAt(environment, manager, 0x2C, chunk_count) ||
      !ReadCurrentActivityAt(environment, manager, 0x38, index_table) ||
      index_table == 0 ||
      !ReadCurrentActivityAt(environment, manager, 0x44, capacity) ||
      index >= capacity ||
      !ReadCurrentActivityAt(environment, manager, 0x50, highest_live) ||
      highest_live < 0 || index > static_cast<std::uint32_t>(highest_live) ||
      index / 1024 >= chunk_count ||
      !ReadCurrentActivityAt(environment, index_table,
                            static_cast<std::size_t>(index) * 16 + 8, object) ||
      object == 0 ||
      !ReadCurrentActivityAt(environment, chunks,
                            static_cast<std::size_t>(index / 1024) * 8, chunk) ||
      chunk == 0)
    return false;
  const auto slot_offset = static_cast<std::size_t>(index % 1024) *
                           bridge::kActivityHosted12002ObjectStride;
  if (slot_offset > (std::numeric_limits<std::uintptr_t>::max)() - chunk ||
      object != chunk + slot_offset)
    return false;
  std::uint32_t observed_id = 0;
  std::int32_t observed_host = -1;
  std::uintptr_t vtable = 0, type = 0, type_vtable = 0;
  if (!ReadCurrentActivityAt(environment, object, 0x08, observed_id) ||
      observed_id != full_id ||
      !ReadCurrentActivityAt(environment, object, 0x3A8, observed_host) ||
      observed_host != host_id ||
      !ReadCurrentActivityAt(environment, object, 0, vtable) ||
      vtable != native.module_base + bridge::ActivityHostedCrozierRvaV1(
          native.executable_sha256, bridge::kActivityHosted12002ActivityVtableRva) ||
      !ReadCurrentActivityAt(environment, object, 0x3A0, type) || type == 0 ||
      !ReadCurrentActivityAt(environment, type, 0, type_vtable) ||
      type_vtable != native.module_base + bridge::ActivityHostedCrozierRvaV1(
          native.executable_sha256, bridge::kActivityHosted12002ActivityTypeVtableRva))
    return false;
  constexpr std::string_view key = "activity_feast";
  std::uint64_t size = 0, string_capacity = 0;
  std::uintptr_t data = 0;
  std::array<char, 16> actual{};
  if (!ReadCurrentActivityAt(environment, type, 0x28, size) ||
      size != key.size() ||
      !ReadCurrentActivityAt(environment, type, 0x30, string_capacity) ||
      string_capacity < size ||
      0x18 > (std::numeric_limits<std::uintptr_t>::max)() - type)
    return false;
  data = type + 0x18;
  if ((string_capacity > 15 &&
       !ReadCurrentActivityAt(environment, type, 0x18, data)) ||
      !environment.read_memory(environment.context, data, actual.data(), key.size()) ||
      std::string_view(actual.data(), key.size()) != key)
    return false;
  activity = object;
  return true;
}

bool InvokeCurrentActivityView12003(std::uintptr_t module_base,
                                   std::string_view admitted_sha256,
                                   std::uintptr_t activity) noexcept {
  using NativeOpen = void(__fastcall *)(void *);
  const auto open = reinterpret_cast<NativeOpen>(module_base + bridge::Activity12004RvaV1(admitted_sha256, 0xA90050));
  __try {
    // The original Activity.OpenActivityView callback calls this receiver-only
    // presentation leaf. Its return register does not prove materialization.
    open(reinterpret_cast<void *>(activity));
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
}

template <class Query>
bool CompleteException(Query &query, const char *failure) noexcept {
  query.failure = failure;
  query.completed = true;
  return true;
}

} // namespace

bool ExecuteActivityPlannerDiagPrivate12002QueryV1(
    void *opaque, const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *query = static_cast<ActivityPlannerDiagPrivate12002QueryV1 *>(opaque);
  if (query == nullptr) return false;
  try {
    game::Snapshot current{};
    ActivityPlanner12002NativeV1 native{};
    if (!Prepare(*query, stamp, &ExecuteActivityPlannerDiagPrivate12002QueryV1,
                 current, native))
      return query->completed;
    query->diagnostic = bridge::ReadActivityPlannerDiagV1(
        BuildActivityPlanner12002DiagEnvironmentV1(native),
        ExpectedFrame(query->expected_revision, current));
    if (!SuccessfulDiagnostic(query->diagnostic.status))
      query->failure = "native_activity_planner_diag_red:" +
          std::string(bridge::ActivityPlannerDiagStatusKeyV1(query->diagnostic.status));
    query->completed = true;
    return true;
  } catch (...) {
    return CompleteException(*query, "native_activity_planner_12002_diag_exception");
  }
}

bool ExecuteActivityFeastPlannerOpenPrivate12002V1(
    void *opaque, const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *query = static_cast<ActivityFeastPlannerOpenPrivate12002QueryV1 *>(opaque);
  if (query == nullptr) return false;
  try {
    game::Snapshot current{};
    ActivityPlanner12002NativeV1 native{};
    if (!Prepare(*query, stamp, &ExecuteActivityFeastPlannerOpenPrivate12002V1,
                 current, native))
      return query->completed;
    if (query->operation ==
        ActivityFeastPlannerOpenOperation12002V1::current_activity_view_open) {
      std::uintptr_t activity = 0;
      if (query->actual_executable_sha256 != ck3_12003::kExecutableSha256 &&
          !bridge::IsActivity12004BuildV1(query->actual_executable_sha256)) {
        query->failure = "exact_current_activity_view_12003_build_unavailable";
      } else if (!ResolveCurrentFeastActivity12003(
                     native, query->expected_activity_id,
                     current.played_character_id, activity)) {
        query->failure = "native_current_activity_view_identity_unavailable";
      } else if (!InvokeCurrentActivityView12003(
                     native.module_base, native.executable_sha256, activity)) {
        query->failure = "native_current_activity_view_dispatch_exception";
      } else {
        query->current_view_activity_id = query->expected_activity_id;
        query->current_view_dispatch_invoked = true;
      }
      query->completed = true;
      return true;
    }
    query->result = bridge::OpenActivityFeastPlannerV1(
        BuildActivityPlanner12002OpenEnvironmentV1(native),
        ExpectedFrame(query->expected_revision, current));
    if (query->result.status != bridge::ActivityFeastPlannerOpenStatusV1::opened &&
        query->result.status != bridge::ActivityFeastPlannerOpenStatusV1::already_open)
      query->failure = "native_activity_feast_open_red:" +
          std::string(bridge::ActivityFeastPlannerOpenStatusKeyV1(query->result.status));
    query->completed = true;
    return true;
  } catch (...) {
    return CompleteException(*query, "native_activity_feast_12002_open_exception");
  }
}

bool ExecuteActivityStage1OptionReadPrivate12002V1(
    void *opaque, const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *query = static_cast<ActivityStage1OptionReadPrivate12002QueryV1 *>(opaque);
  if (query == nullptr) return false;
  try {
    game::Snapshot current{};
    ActivityPlanner12002NativeV1 native{};
    if (!Prepare(*query, stamp, &ExecuteActivityStage1OptionReadPrivate12002V1,
                 current, native))
      return query->completed;
    const auto expected = ExpectedFrame(query->expected_revision, current);
    const auto environment = BuildActivityPlanner12002OptionEnvironmentV1(native);
    if (query->stage_two_location_read) {
      if (query->candidate_province_count > query->candidate_province_ids.size()) {
        query->failure = "native_activity_stage2_location_candidate_count_invalid";
      } else {
        query->stage_two_location_result = bridge::ReadActivityStage2LocationV1(
            BuildActivityPlanner12002LocationEnvironmentV1(native), expected,
            std::span<const std::int32_t>(query->candidate_province_ids.data(),
                                          query->candidate_province_count));
        if (query->stage_two_location_result.status !=
            bridge::ActivityStage2LocationReadStatusV1::observed)
          query->failure = "native_activity_stage2_location_red:" +
              std::string(bridge::ActivityStage2LocationReadStatusKeyV1(
                  query->stage_two_location_result.status));
      }
    } else if (query->stage_two_gate_read) {
      query->stage_two_gate_result = bridge::ReadActivityStage2GateV1(environment, expected);
      if (query->stage_two_gate_result.status != bridge::ActivityStage2GateReadStatusV1::observed)
        query->failure = "native_activity_stage2_gate_red:" +
            std::string(bridge::ActivityStage2GateReadStatusKeyV1(query->stage_two_gate_result.status));
    } else if (query->stage_two_read) {
      query->stage_two_result = bridge::ReadActivityStage2OptionV1(environment, expected);
      if (query->stage_two_result.status != bridge::ActivityStage2OptionReadStatusV1::observed)
        query->failure = "native_activity_stage2_option_red:" +
            std::string(bridge::ActivityStage2OptionReadStatusKeyV1(query->stage_two_result.status));
      else if (!query->stage_two_result.generic_feast_selected)
        query->failure = "native_activity_stage2_option_key_mismatch";
    } else if (query->confirm_stage_one) {
      query->confirm_result = bridge::ConfirmActivityStage1V1(environment, expected);
      query->post_snapshot_read = query->read_snapshot(query->native_context, query->post_snapshot);
      if (query->confirm_result.status != bridge::ActivityStage1ConfirmStatusV1::stage_two_verified ||
          !query->post_snapshot_read || query->post_snapshot != current)
        query->failure = "native_activity_stage1_confirm_red:" +
            std::string(bridge::ActivityStage1ConfirmStatusKeyV1(query->confirm_result.status));
    } else {
      query->result = bridge::ReadActivityStage1OptionV1(environment, expected);
      if (query->result.status != bridge::ActivityStage1OptionReadStatusV1::observed)
        query->failure = "native_activity_stage1_option_red:" +
            std::string(bridge::ActivityStage1OptionReadStatusKeyV1(query->result.status));
    }
    query->completed = true;
    return true;
  } catch (...) {
    return CompleteException(*query, "native_activity_stage1_12002_exception");
  }
}

bool ExecuteActivityStage2DestinationSelectPrivate12002V1(
    void *opaque, const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *query = static_cast<ActivityStage2DestinationSelectPrivate12002QueryV1 *>(opaque);
  if (query == nullptr || query->province_id < 1) return false;
  try {
    game::Snapshot current{};
    ActivityPlanner12002NativeV1 native{};
    if (!Prepare(*query, stamp, &ExecuteActivityStage2DestinationSelectPrivate12002V1,
                 current, native))
      return query->completed;
    query->result = bridge::SelectActivityStage2DestinationV1(
        BuildActivityPlanner12002DestinationEnvironmentV1(native),
        ExpectedFrame(query->expected_revision, current),
        static_cast<std::uint32_t>(query->province_id));
    query->before = native.destination_before;
    query->after = native.destination_after;
    query->before_read = native.destination_before_read;
    query->after_read = native.destination_after_read;
    query->completed = true;
    return true;
  } catch (...) {
    return CompleteException(*query, "native_activity_stage2_12002_destination_exception");
  }
}

bool ExecuteActivityStage2ConfirmPrivate12002V1(
    void *opaque, const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *query = static_cast<ActivityStage2ConfirmPrivate12002QueryV1 *>(opaque);
  if (query == nullptr) return false;
  try {
    game::Snapshot current{};
    ActivityPlanner12002NativeV1 native{};
    if (!Prepare(*query, stamp, &ExecuteActivityStage2ConfirmPrivate12002V1,
                 current, native))
      return query->completed;
    query->stage_two_confirm_result = bridge::ConfirmActivityStage2V1(
        BuildActivityPlanner12002ConfirmEnvironmentV1(native),
        ExpectedFrame(query->expected_revision, current));
    query->post_snapshot_read = query->read_snapshot(query->native_context, query->post_snapshot);
    if (query->stage_two_confirm_result.status !=
            bridge::ActivityStage2ConfirmStatusV1::stage_five_verified ||
        !query->post_snapshot_read || query->post_snapshot != current)
      query->failure = "native_activity_stage2_confirm_red:" +
          std::string(bridge::ActivityStage2ConfirmStatusKeyV1(query->stage_two_confirm_result.status));
    query->completed = true;
    return true;
  } catch (...) {
    return CompleteException(*query, "native_activity_stage2_12002_confirm_exception");
  }
}

std::string SerializeActivityStage2ConfirmPrivate12002V1(
    const ActivityStage2ConfirmPrivate12002QueryV1 &query) {
  if (!query.completed) return {};
  const auto &result = query.stage_two_confirm_result;
  const auto boolean = [](bool value) { return value ? "true" : "false"; };
  std::string out =
      "{\"schema\":\"activity-stage2-confirm-private-v1\","
      "\"snapshot_revision\":" + std::to_string(query.expected_revision) +
      ",\"date_raw\":" + std::to_string(query.expected_snapshot.date_raw) +
      ",\"actor_character_id\":" + std::to_string(query.expected_snapshot.played_character_id) +
      ",\"activity_key\":\"activity_feast\",\"selected_option_key\":\"feast_type_generic\","
      "\"precondition_status\":\"" +
      std::string(bridge::ActivityStage2OptionReadStatusKeyV1(result.precondition.status)) +
      "\",\"can_progress_stage2\":" + boolean(result.can_progress_stage_two) +
      ",\"status\":\"" + std::string(bridge::ActivityStage2ConfirmStatusKeyV1(result.status)) +
      "\",\"submitted\":" + boolean(result.submitted) +
      ",\"stage_five_visible\":" + boolean(result.stage_five_visible) +
      ",\"selected_option_retained\":" + boolean(result.selected_option_retained) +
      ",\"gold_unchanged\":" + boolean(result.gold_unchanged) +
      ",\"frame_unchanged\":" + boolean(result.frame_unchanged) +
      ",\"gold_before_raw\":" + std::to_string(query.expected_snapshot.played_character_gold.raw) +
      ",\"gold_after_raw\":";
  out += query.post_snapshot_read ? std::to_string(query.post_snapshot.played_character_gold.raw) : "null";
  out += ",\"snapshot_unchanged\":";
  out += boolean(query.post_snapshot_read && query.post_snapshot == query.expected_snapshot);
  out += ",\"planning_stage_after\":";
  out += result.stage_five_visible ? "5" : "null";
  out += ",\"activity_start_state\":\"";
  out += result.status == bridge::ActivityStage2ConfirmStatusV1::stage_five_verified &&
                 query.post_snapshot_read && query.post_snapshot == query.expected_snapshot
             ? "not_started_immediate" : "unknown";
  out += "\",\"next_turn_verified\":false,\"raw_pointer_fields_persisted\":false,"
         "\"advertised\":false}";
  return out;
}

} // namespace xar::ck3_12002
