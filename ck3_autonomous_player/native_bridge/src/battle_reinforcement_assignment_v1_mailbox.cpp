#include "xar_bridge/battle_reinforcement_assignment_v1_mailbox.hpp"

#include <windows.h>

#include <algorithm>
#include <array>
#include <atomic>
#include <charconv>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_11906 {
namespace {

template <typename Value>
bool AppendNumber(std::string &output, Value value) {
  std::array<char, 32> buffer{};
  const auto encoded =
      std::to_chars(buffer.data(), buffer.data() + buffer.size(), value);
  if (encoded.ec != std::errc{}) {
    return false;
  }
  output.append(buffer.data(), encoded.ptr);
  return true;
}

void AppendJsonString(std::string &output, std::string_view value) {
  constexpr char hex[] = "0123456789ABCDEF";
  output.push_back('"');
  for (const unsigned char character : value) {
    if (character == '"' || character == '\\') {
      output.push_back('\\');
      output.push_back(static_cast<char>(character));
    } else if (character < 0x20U) {
      output += "\\u00";
      output.push_back(hex[(character >> 4U) & 0x0FU]);
      output.push_back(hex[character & 0x0FU]);
    } else {
      output.push_back(static_cast<char>(character));
    }
  }
  output.push_back('"');
}

bool AppendInt32Array(std::string &output,
                      const std::vector<std::int32_t> &values) {
  output.push_back('[');
  for (std::size_t index = 0; index < values.size(); ++index) {
    if (index != 0) {
      output.push_back(',');
    }
    if (!AppendNumber(output, values[index])) {
      return false;
    }
  }
  output.push_back(']');
  return true;
}

bool ParseCanonicalPositiveInt32(std::string_view text,
                                 std::int32_t &output) noexcept {
  output = -1;
  if (text.empty() || text.front() == '0') {
    return false;
  }
  std::int32_t value = -1;
  const auto parsed =
      std::from_chars(text.data(), text.data() + text.size(), value);
  if (parsed.ec != std::errc{} || parsed.ptr != text.data() + text.size() ||
      value <= 0) {
    return false;
  }
  char canonical[16]{};
  const auto rendered =
      std::to_chars(canonical, canonical + sizeof(canonical), value);
  if (rendered.ec != std::errc{} ||
      std::string_view(canonical, rendered.ptr) != text) {
    return false;
  }
  output = value;
  return true;
}

bool SameExpectedFrame(
    const game::Snapshot &snapshot,
    const BattleReinforcementAssignmentMailboxContextV1 &query,
    const MainThreadExecutionStampV1 &stamp) noexcept {
  return snapshot == query.expected_snapshot && snapshot.paused &&
         snapshot.map_ready && snapshot.has_played_character &&
         snapshot.played_character_alive &&
         snapshot.date_raw == stamp.date_raw;
}

bool IsExecutingExactMailboxSlot(
    const BattleReinforcementAssignmentMailboxContextV1 &query,
    const MainThreadExecutionStampV1 &stamp) noexcept {
  if (query.mailbox == nullptr || query.ticket.sequence == 0 ||
      query.expected_snapshot_revision == 0 ||
      query.request.selected_public_cunit_id <= 0 || stamp.pump_epoch == 0 ||
      stamp.thread_id == 0 || !stamp.paused ||
      stamp.tls_initialized_flag_address == 0 ||
      stamp.tls_initialized != 1 || stamp.tls_context == 0 ||
      stamp.tls_main_thread_marker != 1 || stamp.jomini_state == 0 ||
      stamp.game_state == 0 || GetCurrentThreadId() != stamp.thread_id) {
    return false;
  }
  const auto &mailbox = *query.mailbox;
  return mailbox.state.load(std::memory_order_acquire) ==
             MainThreadQueryMailboxStateV1::executing &&
         !mailbox.stop_requested.load(std::memory_order_acquire) &&
         mailbox.failure_flags.load(std::memory_order_acquire) == 0 &&
         mailbox.published_sequence.load(std::memory_order_acquire) ==
             query.ticket.sequence &&
         mailbox.owner_thread_id.load(std::memory_order_acquire) ==
             stamp.thread_id &&
         mailbox.paused_owner_verified_pump_epochs.load(
             std::memory_order_acquire) >=
             kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs &&
         mailbox.executor ==
             &ExecuteBattleReinforcementAssignmentMailboxQueryV1 &&
         mailbox.executor_context ==
             const_cast<BattleReinforcementAssignmentMailboxContextV1 *>(
                 &query);
}

bool ValidPositiveIds(const std::vector<std::int32_t> &values,
                      bool require_unique) noexcept {
  for (std::size_t index = 0; index < values.size(); ++index) {
    if (values[index] <= 0 ||
        (require_unique &&
         std::find(values.begin(), values.begin() + index, values[index]) !=
             values.begin() + index)) {
      return false;
    }
  }
  return true;
}

bool ValidUnavailableReason(std::string_view reason) noexcept {
  constexpr std::array<std::string_view, 9> reasons = {
      "unsupported_build",
      "requires_paused",
      "subject_cunit_not_found",
      "subject_not_ai_managed",
      "coordinator_generation_mismatch",
      "subunit_backlink_mismatch",
      "parent_membership_mismatch",
      "route_timeline_unavailable",
      "state_changed",
  };
  return std::find(reasons.begin(), reasons.end(), reason) != reasons.end();
}

bool ValidateAvailableSnapshot(
    const game::BattleReinforcementAssignmentSnapshot &snapshot) noexcept {
  if (!snapshot.unavailable_reason.empty() ||
      !snapshot.battle_reinforcement_assignment_ready ||
      !snapshot.coordinator_id.has_value() || *snapshot.coordinator_id <= 0 ||
      !snapshot.unit_stack_stored_index.has_value() ||
      *snapshot.unit_stack_stored_index < 0 ||
      !snapshot.subunit_stored_index.has_value() ||
      *snapshot.subunit_stored_index < 0 ||
      !snapshot.signal.has_value() || !snapshot.assignment.has_value() ||
      !snapshot.route.has_value() || !snapshot.native_order.has_value() ||
      !snapshot.contact_projection.has_value() ||
      (snapshot.selected_native_carmy_id.has_value() &&
       *snapshot.selected_native_carmy_id <= 0)) {
    return false;
  }

  const auto &signal = *snapshot.signal;
  if ((!signal.asking_for_help && signal.request_power_basis_raw.has_value()) ||
      (signal.cross_coordinator_request_valid_raw == 0 &&
       signal.cross_coordinator_request_power_raw.has_value()) ||
      (signal.first_route_edge_remaining_duration_q100000.has_value() &&
       *signal.first_route_edge_remaining_duration_q100000 < 0)) {
    return false;
  }

  const auto &assignment = *snapshot.assignment;
  const bool has_target =
      assignment.assignment_target_province_id.has_value();
  if ((has_target && *assignment.assignment_target_province_id <= 0) ||
      assignment.target_provenance !=
          (has_target ? "native_help_override" : "none") ||
      (assignment.combat_binding_status !=
           "already_in_active_combat" &&
       assignment.combat_binding_status != "unbound_until_contact") ||
      (assignment.combat_binding_status == "already_in_active_combat") !=
          assignment.active_combat_id.has_value() ||
      (assignment.active_combat_id.has_value() &&
       *assignment.active_combat_id <= 0)) {
    return false;
  }

  const auto &route = *snapshot.route;
  if (route.current_province_id <= 0 ||
      (route.move_target_province_id.has_value() &&
       *route.move_target_province_id <= 0) ||
      !ValidPositiveIds(route.route_province_ids, false) ||
      (route.route_alignment != "aligned_to_assignment" &&
       route.route_alignment != "not_aligned" &&
       route.route_alignment != "no_assignment" &&
       route.route_alignment != "timeline_unavailable") ||
      (route.arrival_date_raws.has_value() &&
       route.arrival_date_raws->size() != route.route_province_ids.size()) ||
      (!has_target && route.route_alignment != "no_assignment") ||
      (has_target && route.route_alignment == "no_assignment") ||
      (route.route_alignment == "aligned_to_assignment") !=
          route.assignment_eta_date_raw.has_value() ||
      (route.route_alignment == "timeline_unavailable" &&
       route.arrival_date_raws.has_value())) {
    return false;
  }
  if (route.arrival_date_raws.has_value() &&
      !std::is_sorted(route.arrival_date_raws->begin(),
                      route.arrival_date_raws->end())) {
    return false;
  }
  if (route.route_alignment == "aligned_to_assignment") {
    if (!route.arrival_date_raws.has_value()) {
      return false;
    }
    const bool ends_at_target =
        route.move_target_province_id ==
            assignment.assignment_target_province_id &&
        ((!route.route_province_ids.empty() &&
          route.route_province_ids.back() ==
              *assignment.assignment_target_province_id) ||
         (route.route_province_ids.empty() &&
          route.current_province_id ==
              *assignment.assignment_target_province_id));
    const auto expected_eta =
        route.arrival_date_raws->empty()
            ? static_cast<std::int32_t>(snapshot.observed_date_raw)
            : route.arrival_date_raws->back();
    if (!ends_at_target || *route.assignment_eta_date_raw != expected_eta) {
      return false;
    }
  }

  const auto &native_order = *snapshot.native_order;
  if (!ValidPositiveIds(
          native_order.support_search_province_ids_in_stored_order, false) ||
      static_cast<std::size_t>(*snapshot.subunit_stored_index) >=
          native_order.parent_subunits_in_stored_order.size()) {
    return false;
  }
  for (const auto &row : native_order.parent_subunits_in_stored_order) {
    if (!ValidPositiveIds(row.public_cunit_ids_in_stored_order, true) ||
        (row.assignment_target_province_id.has_value() &&
         *row.assignment_target_province_id <= 0) ||
        row.assigned_to_help !=
            row.assignment_target_province_id.has_value()) {
      return false;
    }
  }
  const auto &selected_row =
      native_order.parent_subunits_in_stored_order[
          static_cast<std::size_t>(*snapshot.subunit_stored_index)];
  if (std::count(selected_row.public_cunit_ids_in_stored_order.begin(),
                 selected_row.public_cunit_ids_in_stored_order.end(),
                 snapshot.selected_public_cunit_id) != 1 ||
      selected_row.asking_for_help != signal.asking_for_help ||
      selected_row.assigned_to_help != signal.assigned_to_help ||
      selected_row.assignment_target_province_id !=
          assignment.assignment_target_province_id) {
    return false;
  }

  const auto &contact = *snapshot.contact_projection;
  if (contact.temporal_semantics !=
          "present_time_only_not_future_binding" ||
      (contact.status != "available" && contact.status != "unavailable" &&
       contact.status != "not_applicable") ||
      !ValidPositiveIds(
          contact.current_target_compatible_combat_ids_in_stored_order,
          true)) {
    return false;
  }
  if (!has_target) {
    return contact.status == "not_applicable" &&
           contact.current_target_compatible_combat_ids_in_stored_order
               .empty() &&
           !contact.contact_if_now_selected_combat_id.has_value();
  }
  if (contact.status == "not_applicable" ||
      (contact.status == "unavailable" &&
       (!contact.current_target_compatible_combat_ids_in_stored_order.empty() ||
        contact.contact_if_now_selected_combat_id.has_value()))) {
    return false;
  }
  if (contact.status == "available") {
    const auto &candidates =
        contact.current_target_compatible_combat_ids_in_stored_order;
    return candidates.empty()
               ? !contact.contact_if_now_selected_combat_id.has_value()
               : contact.contact_if_now_selected_combat_id ==
                     candidates.back();
  }
  return true;
}

bool ValidateSnapshot(
    const game::BattleReinforcementAssignmentSnapshot &snapshot) noexcept {
  if (snapshot.snapshot_revision == 0 ||
      snapshot.selected_public_cunit_id <= 0) {
    return false;
  }
  if (snapshot.status ==
      game::BattleReinforcementAssignmentStatus::available) {
    return ValidateAvailableSnapshot(snapshot);
  }
  return !snapshot.battle_reinforcement_assignment_ready &&
         ValidUnavailableReason(snapshot.unavailable_reason) &&
         !snapshot.selected_native_carmy_id.has_value() &&
         !snapshot.coordinator_id.has_value() &&
         !snapshot.unit_stack_stored_index.has_value() &&
         !snapshot.subunit_stored_index.has_value() &&
         !snapshot.signal.has_value() && !snapshot.assignment.has_value() &&
         !snapshot.route.has_value() && !snapshot.native_order.has_value() &&
         !snapshot.contact_projection.has_value();
}

void AppendNullableInt32(std::string &output,
                         const std::optional<std::int32_t> &value) {
  if (value.has_value() && AppendNumber(output, *value)) {
    return;
  }
  output += "null";
}

void AppendNullableInt64(std::string &output,
                         const std::optional<std::int64_t> &value) {
  if (value.has_value() && AppendNumber(output, *value)) {
    return;
  }
  output += "null";
}

bool AppendSignal(
    std::string &output,
    const game::BattleReinforcementSignalSnapshot &signal) {
  output += "{\"asking_for_help\":";
  output += signal.asking_for_help ? "true" : "false";
  output += ",\"assigned_to_help\":";
  output += signal.assigned_to_help ? "true" : "false";
  output += ",\"asking_changed_last_evaluation\":";
  output += signal.asking_changed_last_evaluation ? "true" : "false";
  output += ",\"request_power_basis_raw\":";
  AppendNullableInt64(output, signal.request_power_basis_raw);
  output += ",\"cross_coordinator_request_valid_raw\":";
  if (!AppendNumber(output, signal.cross_coordinator_request_valid_raw)) {
    return false;
  }
  output += ",\"cross_coordinator_request_power_raw\":";
  AppendNullableInt64(output, signal.cross_coordinator_request_power_raw);
  output += ",\"first_route_edge_remaining_duration_q100000\":";
  AppendNullableInt64(
      output, signal.first_route_edge_remaining_duration_q100000);
  output.push_back('}');
  return true;
}

bool AppendAssignment(
    std::string &output,
    const game::BattleReinforcementAssignmentStateSnapshot &assignment) {
  output += "{\"assignment_target_province_id\":";
  AppendNullableInt32(output, assignment.assignment_target_province_id);
  output += ",\"target_provenance\":";
  AppendJsonString(output, assignment.target_provenance);
  output += ",\"combat_binding_status\":";
  AppendJsonString(output, assignment.combat_binding_status);
  output += ",\"active_combat_id\":";
  AppendNullableInt32(output, assignment.active_combat_id);
  output.push_back('}');
  return true;
}

bool AppendRoute(std::string &output,
                 const game::BattleReinforcementRouteSnapshot &route) {
  output += "{\"current_province_id\":";
  if (!AppendNumber(output, route.current_province_id)) return false;
  output += ",\"move_target_province_id\":";
  AppendNullableInt32(output, route.move_target_province_id);
  output += ",\"route_province_ids\":";
  if (!AppendInt32Array(output, route.route_province_ids)) return false;
  output += ",\"route_alignment\":";
  AppendJsonString(output, route.route_alignment);
  output += ",\"arrival_date_raws\":";
  if (route.arrival_date_raws.has_value()) {
    if (!AppendInt32Array(output, *route.arrival_date_raws)) return false;
  } else {
    output += "null";
  }
  output += ",\"assignment_eta_date_raw\":";
  AppendNullableInt32(output, route.assignment_eta_date_raw);
  output.push_back('}');
  return true;
}

bool AppendNativeOrder(
    std::string &output,
    const game::BattleReinforcementNativeOrderSnapshot &native_order) {
  output += "{\"support_search_province_ids_in_stored_order\":";
  if (!AppendInt32Array(
          output,
          native_order.support_search_province_ids_in_stored_order)) {
    return false;
  }
  output += ",\"parent_subunits_in_stored_order\":[";
  for (std::size_t index = 0;
       index < native_order.parent_subunits_in_stored_order.size();
       ++index) {
    if (index != 0) output.push_back(',');
    const auto &row = native_order.parent_subunits_in_stored_order[index];
    output += "{\"public_cunit_ids_in_stored_order\":";
    if (!AppendInt32Array(output, row.public_cunit_ids_in_stored_order)) {
      return false;
    }
    output += ",\"asking_for_help\":";
    output += row.asking_for_help ? "true" : "false";
    output += ",\"assigned_to_help\":";
    output += row.assigned_to_help ? "true" : "false";
    output += ",\"assignment_target_province_id\":";
    AppendNullableInt32(output, row.assignment_target_province_id);
    output.push_back('}');
  }
  output += "]}";
  return true;
}

bool AppendContactProjection(
    std::string &output,
    const game::BattleReinforcementContactProjectionSnapshot &contact) {
  output += "{\"status\":";
  AppendJsonString(output, contact.status);
  output += ",\"temporal_semantics\":";
  AppendJsonString(output, contact.temporal_semantics);
  output +=
      ",\"current_target_compatible_combat_ids_in_stored_order\":";
  if (!AppendInt32Array(
          output,
          contact.current_target_compatible_combat_ids_in_stored_order)) {
    return false;
  }
  output += ",\"contact_if_now_selected_combat_id\":";
  AppendNullableInt32(output, contact.contact_if_now_selected_combat_id);
  output.push_back('}');
  return true;
}

} // namespace

bool ParseBattleReinforcementAssignmentV1Step(
    std::string_view step,
    game::BattleReinforcementAssignmentRequest &output) noexcept {
  output = {};
  if (!step.starts_with(kBattleReinforcementAssignmentV1StepPrefix) ||
      !ParseCanonicalPositiveInt32(
          step.substr(kBattleReinforcementAssignmentV1StepPrefix.size()),
          output.selected_public_cunit_id)) {
    output = {};
    return false;
  }
  return true;
}

bool ParseBattleReinforcementAssignmentExpectedRevisionV1(
    std::string_view json, std::uint64_t &output) noexcept {
  output = 0;
  constexpr std::string_view key = "\"expected_revision\":";
  const auto at = json.find(key);
  if (at == std::string_view::npos ||
      json.find(key, at + key.size()) != std::string_view::npos) {
    return false;
  }
  auto begin = at + key.size();
  while (begin < json.size() &&
         (json[begin] == ' ' || json[begin] == '\t' ||
          json[begin] == '\r' || json[begin] == '\n')) {
    ++begin;
  }
  auto end = begin;
  while (end < json.size() && json[end] >= '0' && json[end] <= '9') {
    ++end;
  }
  auto delimiter = end;
  while (delimiter < json.size() &&
         (json[delimiter] == ' ' || json[delimiter] == '\t' ||
          json[delimiter] == '\r' || json[delimiter] == '\n')) {
    ++delimiter;
  }
  if (end == begin || (json[begin] == '0' && end - begin != 1U) ||
      (delimiter < json.size() && json[delimiter] != ',' &&
       json[delimiter] != '}')) {
    return false;
  }
  const auto parsed =
      std::from_chars(json.data() + begin, json.data() + end, output);
  return parsed.ec == std::errc{} && parsed.ptr == json.data() + end &&
         output > 0;
}

bool ExecuteBattleReinforcementAssignmentMailboxQueryV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *const query =
      static_cast<BattleReinforcementAssignmentMailboxContextV1 *>(
          opaque_context);
  if (query == nullptr || !IsExecutingExactMailboxSlot(*query, stamp) ||
      query->completion !=
          BattleReinforcementAssignmentMailboxCompletionV1::not_executed ||
      query->executor_invocations != 0) {
    if (query != nullptr) {
      query->completion =
          BattleReinforcementAssignmentMailboxCompletionV1::
              infrastructure_rejected;
    }
    return false;
  }
  try {
    ++query->executor_invocations;
    query->execution_stamp = stamp;
    game::Snapshot before{};
    if (!ReadSnapshot(query->bindings, before) ||
        !SameExpectedFrame(before, *query, stamp)) {
      query->result = {};
      query->completion =
          BattleReinforcementAssignmentMailboxCompletionV1::frame_changed;
      return true;
    }
    ReadBattleReinforcementAssignmentV1(
        query->bindings, before, query->request, query->result);
    game::Snapshot after{};
    if (!ReadSnapshot(query->bindings, after) || after != before ||
        !SameExpectedFrame(after, *query, stamp)) {
      query->result = {};
      query->completion =
          BattleReinforcementAssignmentMailboxCompletionV1::frame_changed;
      return true;
    }
    query->result.snapshot_revision = query->expected_snapshot_revision;
    query->result.observed_date_raw = stamp.date_raw;
    query->result.selected_public_cunit_id =
        query->request.selected_public_cunit_id;
    query->completion =
        BattleReinforcementAssignmentMailboxCompletionV1::completed;
    return true;
  } catch (...) {
    query->result = {};
    query->result.status =
        game::BattleReinforcementAssignmentStatus::unavailable;
    query->result.unavailable_reason = "state_changed";
    query->result.snapshot_revision = query->expected_snapshot_revision;
    query->result.observed_date_raw = stamp.date_raw;
    query->result.selected_public_cunit_id =
        query->request.selected_public_cunit_id;
    query->completion =
        BattleReinforcementAssignmentMailboxCompletionV1::completed;
    return true;
  }
}

std::string_view BattleReinforcementAssignmentFailureMessageV1(
    MainThreadQueryWaitResultV1 wait,
    BattleReinforcementAssignmentMailboxCompletionV1 completion,
    bool completion_snapshot_stable) noexcept {
  switch (wait) {
  case MainThreadQueryWaitResultV1::executor_failed:
    return completion ==
                   BattleReinforcementAssignmentMailboxCompletionV1::
                       infrastructure_rejected
               ? "application-main battle-reinforcement executor gate rejected execution"
               : "application-main battle-reinforcement executor failed";
  case MainThreadQueryWaitResultV1::infrastructure_failed:
    return "application-main battle-reinforcement boundary drifted";
  case MainThreadQueryWaitResultV1::cancelled:
    return "application-main battle-reinforcement query was cancelled";
  case MainThreadQueryWaitResultV1::timeout_cancelled_before_execution:
    return "application-main battle-reinforcement query timed out before execution";
  case MainThreadQueryWaitResultV1::timeout_executor_already_running:
    return "application-main battle-reinforcement executor is still running";
  case MainThreadQueryWaitResultV1::ticket_mismatch:
    return "application-main battle-reinforcement ticket mismatch";
  case MainThreadQueryWaitResultV1::completed:
    break;
  }
  if (completion ==
      BattleReinforcementAssignmentMailboxCompletionV1::frame_changed) {
    return "battle-reinforcement application-main frame changed";
  }
  if (completion ==
      BattleReinforcementAssignmentMailboxCompletionV1::completed) {
    return completion_snapshot_stable
               ? "application-main battle-reinforcement result is inconsistent"
               : "battle-reinforcement completion snapshot changed";
  }
  return "application-main battle-reinforcement completion is inconsistent";
}

std::string SerializeBattleReinforcementAssignmentV1(
    const game::BattleReinforcementAssignmentSnapshot &snapshot) {
  if (!ValidateSnapshot(snapshot)) {
    return {};
  }
  const bool available =
      snapshot.status ==
      game::BattleReinforcementAssignmentStatus::available;
  std::string output;
  output.reserve(4096U);
  output +=
      "{\"schema_version\":1,\"contract_stage\":"
      "\"production_exact_ai_reinforcement_assignment\",\"status\":";
  AppendJsonString(output, available ? "available" : "unavailable");
  output += ",\"unavailable_reason\":";
  if (available) output += "null";
  else AppendJsonString(output, snapshot.unavailable_reason);
  output += ",\"battle_reinforcement_assignment_ready\":";
  output += snapshot.battle_reinforcement_assignment_ready ? "true" : "false";
  output += ",\"snapshot_revision\":";
  if (!AppendNumber(output, snapshot.snapshot_revision)) return {};
  output += ",\"observed_date_raw\":";
  if (!AppendNumber(output, snapshot.observed_date_raw)) return {};
  output += ",\"selected_public_cunit_id\":";
  if (!AppendNumber(output, snapshot.selected_public_cunit_id)) return {};
  output += ",\"selected_native_carmy_id\":";
  AppendNullableInt32(output, snapshot.selected_native_carmy_id);
  output += ",\"coordinator_id\":";
  AppendNullableInt32(output, snapshot.coordinator_id);
  output += ",\"unit_stack_stored_index\":";
  AppendNullableInt32(output, snapshot.unit_stack_stored_index);
  output += ",\"subunit_stored_index\":";
  AppendNullableInt32(output, snapshot.subunit_stored_index);
  output += ",\"signal\":";
  if (available) {
    if (!AppendSignal(output, *snapshot.signal)) return {};
  } else output += "null";
  output += ",\"assignment\":";
  if (available) {
    if (!AppendAssignment(output, *snapshot.assignment)) return {};
  } else output += "null";
  output += ",\"route\":";
  if (available) {
    if (!AppendRoute(output, *snapshot.route)) return {};
  } else output += "null";
  output += ",\"native_order\":";
  if (available) {
    if (!AppendNativeOrder(output, *snapshot.native_order)) return {};
  } else output += "null";
  output += ",\"contact_projection\":";
  if (available) {
    if (!AppendContactProjection(output, *snapshot.contact_projection)) {
      return {};
    }
  } else output += "null";
  output.push_back('}');
  return output;
}

} // namespace xar::ck3_11906
