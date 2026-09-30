#include "activity_feast_guest_candidate_private_transport_v1.hpp"

#include <windows.h>

namespace xar::ck3_11906 {
namespace {

struct CaptureContext {
  ActivityFeastGuestCandidatePrivateQueryV1 *query = nullptr;
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

bool InvokeJoin(void *opaque, std::uintptr_t base, std::uintptr_t planner,
                std::uintptr_t character, std::int64_t &raw) noexcept {
  auto &context = *static_cast<CaptureContext *>(opaque);
  if (GetCurrentThreadId() != context.owner_thread_id ||
      base != context.module_base)
    return false;
  bool succeeded = false;
  __try {
    succeeded = bridge::InvokeActivityFeastNativePlannerGuestJoinV1(
        nullptr, base, planner, character, raw);
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    succeeded = false;
  }
  return succeeded;
}

std::uintptr_t InvokeActivity(void *opaque, std::uintptr_t base,
                              std::uintptr_t planner) noexcept {
  auto &context = *static_cast<CaptureContext *>(opaque);
  if (GetCurrentThreadId() != context.owner_thread_id ||
      base != context.module_base)
    return 0;
  std::uintptr_t result = 0;
  __try {
    result = bridge::InvokeActivityFeastNativePlannerActivityV1(
        nullptr, base, planner);
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    result = 0;
  }
  return result;
}

bool InvokeTravel(void *opaque, std::uintptr_t base,
                  std::uintptr_t character, std::uintptr_t destination,
                  std::int32_t &days) noexcept {
  auto &context = *static_cast<CaptureContext *>(opaque);
  if (GetCurrentThreadId() != context.owner_thread_id ||
      base != context.module_base)
    return false;
  bool succeeded = false;
  __try {
    succeeded = bridge::InvokeActivityFeastNativeTravelDaysV1(
        nullptr, base, character, destination, days);
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    succeeded = false;
  }
  return succeeded;
}

bool EvaluateCanStart(void *opaque, std::uintptr_t planner,
                      bool &value) noexcept {
  auto &context = *static_cast<CaptureContext *>(opaque);
  if (GetCurrentThreadId() != context.owner_thread_id || planner == 0 ||
      context.module_base == 0)
    return false;
  using Predicate = bool (*)(void *, void *);
  const auto predicate = reinterpret_cast<Predicate>(
      context.module_base + 0x10B0DA0);
  __try {
    value = predicate(reinterpret_cast<void *>(planner), nullptr);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
}

std::string FingerprintHex(std::uint64_t value) {
  constexpr char digits[] = "0123456789abcdef";
  std::string output = "0x0000000000000000";
  for (std::size_t i = 0; i < 16; ++i)
    output[2 + i] = digits[(value >> (60 - 4 * i)) & 0xF];
  return output;
}

bool TargetIsSelected(const bridge::ActivityFeastGuestJoinResultV1 &selected,
                      std::int32_t target_character_id) noexcept {
  for (std::uint32_t index = 0; index < selected.selected_nonhost_count;
       ++index) {
    if (selected.rows[index].character_id == target_character_id) return true;
  }
  return false;
}

} // namespace

bool ExecuteActivityFeastGuestCandidatePrivateV1(
    void *opaque, const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *query = static_cast<ActivityFeastGuestCandidatePrivateQueryV1 *>(opaque);
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
      mailbox.executor != &ExecuteActivityFeastGuestCandidatePrivateV1 ||
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
      query->failure = "exact_activity_feast_guest_candidate_build_unavailable";
      query->completed = true;
      return true;
    }
    CaptureContext context{query, base, stamp.thread_id};
    bridge::ActivityPlannerDiagEnvironmentV1 diagnostic{
        true, bridge::kActivityPlannerDiagExeSha256V1, base, &context,
        &ReadMemory, &ReadFrame, &CastIdler, &InvokeVisibility};
    bridge::ActivityFeastGuestJoinEnvironmentV1 environment{};
    environment.enabled = true;
    environment.diagnostic = diagnostic;
    environment.passive_cost = query->passive_cost;
    environment.invoke_join = &InvokeJoin;
    environment.join_context = &context;
    environment.invoke_activity = &InvokeActivity;
    environment.invoke_travel_days = &InvokeTravel;
    environment.arrival_context = &context;
    const bridge::ActivityPlannerDiagFrameV1 expected{
        query->expected_revision, current.date_raw,
        current.played_character_id, true, true, true, true};
    query->candidate = bridge::ReadActivityFeastGuestCandidateV1(
        environment, expected, query->target_character_id);
    if (query->route_proof) {
      query->selected_guests = bridge::ReadActivityFeastGuestJoinV1(
          environment, expected);
      bridge::ActivityStage5CanStartEnvironmentV1 start_environment{};
      start_environment.diagnostic = diagnostic;
      start_environment.evaluate = &EvaluateCanStart;
      query->start_gate = bridge::ReadActivityStage5CanStartV1(
          start_environment, expected);
      const auto repeated = bridge::ReadActivityFeastGuestCandidateV1(
          environment, expected, query->target_character_id);
      const auto candidate_complete =
          query->candidate.status ==
              bridge::ActivityFeastGuestCandidateStatusV1::observed ||
          (query->target_character_id == 0 &&
           query->candidate.status ==
               bridge::ActivityFeastGuestCandidateStatusV1::
                   no_qualified_candidate) ||
          (query->target_character_id != 0 &&
           query->candidate.status ==
               bridge::ActivityFeastGuestCandidateStatusV1::
                   target_not_filtered);
      query->route_proof_consistent =
          candidate_complete && repeated == query->candidate &&
          query->selected_guests.status ==
              bridge::ActivityFeastGuestJoinStatusV1::observed &&
          query->start_gate.status ==
              bridge::ActivityStage5CanStartStatusV1::observed &&
          query->selected_guests.frame == query->candidate.frame &&
          query->start_gate.frame == query->candidate.frame &&
          query->selected_guests.normal_refresh_sequence ==
              query->candidate.normal_refresh_sequence &&
          (query->target_character_id == 0 ||
           query->candidate.status !=
               bridge::ActivityFeastGuestCandidateStatusV1::observed ||
           query->candidate.selected_member ==
               TargetIsSelected(query->selected_guests,
                                query->target_character_id));
    }
    query->completed = true;
    return true;
  } catch (...) {
    query->failure = "native_activity_feast_guest_candidate_exception";
    query->completed = true;
    return true;
  }
}

std::string SerializeActivityFeastGuestCandidatePrivateV1(
    const ActivityFeastGuestCandidatePrivateQueryV1 &query) {
  if (!query.completed || !query.failure.empty() || query.frame_changed)
    return {};
  const auto &result = query.candidate;
  const auto observed =
      result.status == bridge::ActivityFeastGuestCandidateStatusV1::observed;
  const auto complete =
      observed || result.status ==
                      bridge::ActivityFeastGuestCandidateStatusV1::
                          no_qualified_candidate;
  std::string payload =
      "{\"schema\":\"activity-feast-guest-candidate-private-read-v1\","
      "\"snapshot_revision\":" + std::to_string(query.expected_revision) +
      ",\"date_raw\":" +
      std::to_string(query.expected_snapshot.date_raw) +
      ",\"actor_character_id\":" +
      std::to_string(query.expected_snapshot.played_character_id) +
      ",\"activity_key\":\"activity_feast\",\"planning_stage\":5,"
      "\"status\":\"" +
      std::string(bridge::ActivityFeastGuestCandidateStatusKeyV1(result.status)) +
      "\",\"normal_refresh_sequence\":";
  payload += complete ? std::to_string(result.normal_refresh_sequence) : "null";
  payload += ",\"source_fingerprint\":";
  payload += complete ? "\"" + FingerprintHex(result.source_fingerprint) + "\""
                      : "null";
  payload += ",\"native_filtered_pre_invitation\":";
  payload += observed ? "true" : complete ? "false" : "null";
  payload += ",\"candidate\":";
  if (observed) {
    payload += "{\"character_id\":" + std::to_string(result.character_id) +
               ",\"planner_join_raw\":" +
               std::to_string(result.planner_join_raw) +
               ",\"travel_days\":" + std::to_string(result.travel_days) +
               ",\"arrival_raw\":" + std::to_string(result.arrival_raw) +
               ",\"planned_start_raw\":" +
               std::to_string(result.planned_start_raw) + "}";
  } else {
    payload += "null";
  }
  payload += ",\"read_only\":true,\"raw_pointer_fields_persisted\":false}";
  return payload;
}

std::string SerializeActivityFeastGuestRouteProofPrivateV1(
    const ActivityFeastGuestCandidatePrivateQueryV1 &query) {
  if (!query.completed || !query.failure.empty() || query.frame_changed ||
      !query.route_proof)
    return {};
  const auto &candidate = query.candidate;
  const auto &selected = query.selected_guests;
  std::string payload =
      "{\"schema\":\"activity-feast-stage5-guest-route-proof-private-v1\","
      "\"snapshot_revision\":" + std::to_string(query.expected_revision) +
      ",\"date_raw\":" +
      std::to_string(query.expected_snapshot.date_raw) +
      ",\"actor_character_id\":" +
      std::to_string(query.expected_snapshot.played_character_id) +
      ",\"activity_key\":\"activity_feast\",\"planning_stage\":5,"
      "\"status\":\"" +
      std::string(query.route_proof_consistent ? "observed" : "unavailable") +
      "\",\"candidate_status\":\"" +
      std::string(bridge::ActivityFeastGuestCandidateStatusKeyV1(
          candidate.status)) +
      "\",\"selected_status\":\"" +
      std::string(bridge::ActivityFeastGuestJoinStatusKeyV1(selected.status)) +
      "\",\"start_gate_status\":\"" +
      std::string(bridge::ActivityStage5CanStartStatusKeyV1(
          query.start_gate.status)) + "\",\"normal_refresh_sequence\":";
  payload += query.route_proof_consistent
                 ? std::to_string(candidate.normal_refresh_sequence) : "null";
  payload += ",\"source_fingerprint\":";
  payload += query.route_proof_consistent
                 ? "\"" + FingerprintHex(candidate.source_fingerprint) + "\""
                 : "null";
  payload += ",\"active_rule_count\":";
  payload += query.route_proof_consistent
                 ? std::to_string(candidate.active_rule_count) : "null";
  payload += ",\"filtered_group_count\":";
  payload += query.route_proof_consistent
                 ? std::to_string(candidate.filtered_group_count) : "null";
  payload += ",\"selected_row_count\":";
  payload += query.route_proof_consistent
                 ? std::to_string(candidate.selected_row_count) : "null";
  payload += ",\"selected_nonhost_count\":";
  payload += query.route_proof_consistent
                 ? std::to_string(selected.selected_nonhost_count) : "null";
  payload += ",\"selected_nonhost_rows\":";
  if (query.route_proof_consistent) {
    payload += "[";
    for (std::uint32_t index = 0; index < selected.selected_nonhost_count;
         ++index) {
      if (index != 0) payload += ",";
      const auto &row = selected.rows[index];
      payload += "{\"character_id\":" + std::to_string(row.character_id) +
                 ",\"planner_join_raw\":" +
                 std::to_string(row.planner_join_raw) +
                 ",\"positive_join\":" +
                 (row.positive_join ? "true" : "false") +
                 ",\"predicted_arrival_raw\":" +
                 std::to_string(row.predicted_arrival_raw) +
                 ",\"travel_days\":" +
                 std::to_string(row.predicted_travel_days) +
                 ",\"late\":" +
                 (row.may_not_arrive_in_time ? "true" : "false") + "}";
    }
    payload += "]";
  } else {
    payload += "null";
  }
  payload += ",\"positive_join_count\":";
  payload += query.route_proof_consistent
                 ? std::to_string(selected.positive_join_count) : "null";
  payload += ",\"timely_positive_join_count\":";
  payload += query.route_proof_consistent
                 ? std::to_string(selected.timely_positive_join_count) : "null";
  payload += ",\"final_can_start\":";
  payload += query.route_proof_consistent
                 ? (query.start_gate.final_can_start ? "true" : "false") : "null";
  payload += ",\"pre_invitation_candidate\":";
  if (query.route_proof_consistent &&
      candidate.status == bridge::ActivityFeastGuestCandidateStatusV1::observed) {
    payload += "{\"character_id\":" + std::to_string(candidate.character_id) +
               ",\"planner_join_raw\":" +
               std::to_string(candidate.planner_join_raw) +
               ",\"travel_days\":" + std::to_string(candidate.travel_days) +
               ",\"arrival_raw\":" + std::to_string(candidate.arrival_raw) +
               ",\"planned_start_raw\":" +
               std::to_string(candidate.planned_start_raw) + "}";
  } else {
    payload += "null";
  }
  payload += ",\"candidate_selected_membership\":";
  payload += query.route_proof_consistent &&
                     candidate.status ==
                         bridge::ActivityFeastGuestCandidateStatusV1::observed
                 ? "false" : "null";
  payload += ",\"authored_rule_membership\":null,"
             "\"native_guest_route_qualified\":false,"
             "\"read_only\":true,\"advertised\":false}";
  return payload;
}

std::string SerializeActivityFeastGuestTargetPrivateV1(
    const ActivityFeastGuestCandidatePrivateQueryV1 &query) {
  if (!query.completed || !query.failure.empty() || query.frame_changed ||
      !query.route_proof || query.target_character_id <= 0)
    return {};
  const auto &target = query.candidate;
  const auto observed = query.route_proof_consistent;
  const auto member = observed &&
      target.status == bridge::ActivityFeastGuestCandidateStatusV1::observed;
  std::string payload =
      "{\"schema\":\"activity-feast-stage5-guest-target-private-v1\","
      "\"snapshot_revision\":" + std::to_string(query.expected_revision) +
      ",\"date_raw\":" + std::to_string(query.expected_snapshot.date_raw) +
      ",\"actor_character_id\":" +
      std::to_string(query.expected_snapshot.played_character_id) +
      ",\"activity_key\":\"activity_feast\",\"planning_stage\":5,"
      "\"status\":\"" + std::string(observed ? "observed" : "unavailable") +
      "\",\"target_status\":\"" +
      std::string(bridge::ActivityFeastGuestCandidateStatusKeyV1(target.status)) +
      "\",\"target_character_id\":" +
      std::to_string(query.target_character_id) +
      ",\"selected_status\":\"" +
      std::string(bridge::ActivityFeastGuestJoinStatusKeyV1(
          query.selected_guests.status)) +
      "\",\"start_gate_status\":\"" +
      std::string(bridge::ActivityStage5CanStartStatusKeyV1(
          query.start_gate.status)) +
      "\",\"normal_refresh_sequence\":";
  payload += observed ? std::to_string(target.normal_refresh_sequence) : "null";
  payload += ",\"source_fingerprint\":";
  payload += observed
                 ? "\"" + FingerprintHex(target.source_fingerprint) + "\""
                 : "null";
  payload += ",\"active_rule_count\":";
  payload += observed ? std::to_string(target.active_rule_count) : "null";
  payload += ",\"filtered_group_count\":";
  payload += observed ? std::to_string(target.filtered_group_count) : "null";
  payload += ",\"selected_row_count\":";
  payload += observed ? std::to_string(target.selected_row_count) : "null";
  payload += ",\"native_filtered_member\":";
  payload += observed ? (member ? "true" : "false") : "null";
  payload += ",\"selected_member\":";
  payload += observed
                 ? (TargetIsSelected(query.selected_guests,
                                     query.target_character_id) ? "true" : "false")
                 : "null";
  payload += ",\"planner_join_raw\":";
  payload += member ? std::to_string(target.planner_join_raw) : "null";
  payload += ",\"travel_days\":";
  payload += member ? std::to_string(target.travel_days) : "null";
  payload += ",\"arrival_raw\":";
  payload += member ? std::to_string(target.arrival_raw) : "null";
  payload += ",\"planned_start_raw\":";
  payload += member ? std::to_string(target.planned_start_raw) : "null";
  payload += ",\"positive_join\":";
  payload += member ? (target.planner_join_raw > 0 ? "true" : "false") : "null";
  payload += ",\"timely_arrival\":";
  payload += member ? (target.arrival_raw <= target.planned_start_raw
                           ? "true" : "false") : "null";
  payload += ",\"final_can_start\":";
  payload += observed ? (query.start_gate.final_can_start ? "true" : "false")
                      : "null";
  payload += ",\"authored_rule_membership\":null,"
             "\"native_guest_route_qualified\":false,"
             "\"read_only\":true,\"advertised\":false}";
  return payload;
}

} // namespace xar::ck3_11906
