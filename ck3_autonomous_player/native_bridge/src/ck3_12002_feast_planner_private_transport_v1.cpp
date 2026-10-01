#include "ck3_12002_feast_planner_private_transport_v1.hpp"

#include <windows.h>

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
