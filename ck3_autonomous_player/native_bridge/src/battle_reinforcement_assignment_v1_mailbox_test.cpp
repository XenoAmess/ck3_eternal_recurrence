#include "xar_bridge/battle_reinforcement_assignment_v1_mailbox.hpp"

#include <windows.h>

#include <cstdint>
#include <iostream>
#include <string>
#include <string_view>

namespace {

xar::game::Snapshot g_snapshot{};
xar::game::BattleReinforcementAssignmentSnapshot g_reader_result{};
bool g_read_snapshot = true;

bool Contains(std::string_view text, std::string_view token) {
  return text.find(token) != std::string_view::npos;
}

xar::game::BattleReinforcementAssignmentSnapshot AvailableSnapshot() {
  xar::game::BattleReinforcementAssignmentSnapshot result{};
  result.status =
      xar::game::BattleReinforcementAssignmentStatus::available;
  result.snapshot_revision = 17;
  result.observed_date_raw = 53'178'264;
  result.selected_public_cunit_id = 83'886'341;
  result.selected_native_carmy_id = 100'663'397;
  result.coordinator_id = 117'440'519;
  result.unit_stack_stored_index = 2;
  result.subunit_stored_index = 0;
  result.signal.emplace();
  result.signal->assigned_to_help = true;
  result.signal->asking_changed_last_evaluation = true;
  result.signal->cross_coordinator_request_valid_raw = 1;
  result.signal->cross_coordinator_request_power_raw = 2'300'000;
  result.signal->first_route_edge_remaining_duration_q100000 = 150'000;
  result.assignment.emplace();
  result.assignment->assignment_target_province_id = 2'579;
  result.assignment->target_provenance = "native_help_override";
  result.assignment->combat_binding_status = "unbound_until_contact";
  result.route.emplace();
  result.route->current_province_id = 2'578;
  result.route->move_target_province_id = 2'579;
  result.route->route_province_ids = {2'579, 2'579};
  result.route->route_alignment = "aligned_to_assignment";
  result.route->arrival_date_raws =
      std::vector<std::int32_t>{53'178'288, 53'178'288};
  result.route->assignment_eta_date_raw = 53'178'288;
  result.native_order.emplace();
  result.native_order->support_search_province_ids_in_stored_order =
      {2'579, 2'579};
  xar::game::BattleReinforcementParentSubunitSnapshot selected{};
  selected.public_cunit_ids_in_stored_order = {83'886'341};
  selected.assigned_to_help = true;
  selected.assignment_target_province_id = 2'579;
  result.native_order->parent_subunits_in_stored_order.push_back(selected);
  xar::game::BattleReinforcementParentSubunitSnapshot sibling{};
  sibling.public_cunit_ids_in_stored_order = {83'886'342};
  sibling.asking_for_help = true;
  result.native_order->parent_subunits_in_stored_order.push_back(sibling);
  result.contact_projection.emplace();
  result.contact_projection->status = "available";
  result.contact_projection->current_target_compatible_combat_ids_in_stored_order =
      {335'544'325, 335'544'326};
  result.contact_projection->contact_if_now_selected_combat_id =
      335'544'326;
  result.battle_reinforcement_assignment_ready = true;
  return result;
}

bool Run() {
  using namespace xar::ck3_11906;
  xar::game::BattleReinforcementAssignmentRequest request{};
  if (!ParseBattleReinforcementAssignmentV1Step(
          "query-battle-reinforcement-assignment-v1-83886341", request) ||
      request.selected_public_cunit_id != 83'886'341 ||
      ParseBattleReinforcementAssignmentV1Step(
          "query-battle-reinforcement-assignment-v1-083886341", request) ||
      ParseBattleReinforcementAssignmentV1Step(
          "query-battle-reinforcement-assignment-v1-0", request) ||
      ParseBattleReinforcementAssignmentV1Step(
          "query-battle-reinforcement-assignment-v1-2147483648", request)) {
    return false;
  }
  std::uint64_t revision = 0;
  if (!ParseBattleReinforcementAssignmentExpectedRevisionV1(
          "{\"expected_revision\":17}", revision) || revision != 17 ||
      ParseBattleReinforcementAssignmentExpectedRevisionV1(
          "{\"expected_revision\":017}", revision) ||
      ParseBattleReinforcementAssignmentExpectedRevisionV1(
          "{\"expected_revision\":17,\"expected_revision\":18}",
          revision)) {
    return false;
  }

  auto available = AvailableSnapshot();
  const auto wire = SerializeBattleReinforcementAssignmentV1(available);
  if (wire.empty() ||
      !Contains(wire, "\"contract_stage\":\"production_exact_ai_reinforcement_assignment\"") ||
      !Contains(wire, "\"route_province_ids\":[2579,2579]") ||
      !Contains(wire, "\"request_power_basis_raw\":null") ||
      !Contains(wire, "\"contact_if_now_selected_combat_id\":335544326")) {
    return false;
  }
  auto invalid = available;
  invalid.signal->request_power_basis_raw = 99;
  if (!SerializeBattleReinforcementAssignmentV1(invalid).empty()) {
    return false;
  }
  invalid = available;
  invalid.contact_projection->contact_if_now_selected_combat_id =
      335'544'325;
  if (!SerializeBattleReinforcementAssignmentV1(invalid).empty()) {
    return false;
  }
  invalid = available;
  invalid.route->route_province_ids.back() = 2'580;
  if (!SerializeBattleReinforcementAssignmentV1(invalid).empty()) {
    return false;
  }

  xar::game::BattleReinforcementAssignmentSnapshot unavailable{};
  unavailable.status =
      xar::game::BattleReinforcementAssignmentStatus::unavailable;
  unavailable.unavailable_reason = "subject_not_ai_managed";
  unavailable.snapshot_revision = 18;
  unavailable.observed_date_raw = 53'178'264;
  unavailable.selected_public_cunit_id = 83'886'341;
  const auto unavailable_wire =
      SerializeBattleReinforcementAssignmentV1(unavailable);
  if (unavailable_wire.empty() ||
      !Contains(unavailable_wire,
                "\"unavailable_reason\":\"subject_not_ai_managed\"") ||
      !Contains(unavailable_wire, "\"signal\":null") ||
      !Contains(unavailable_wire, "\"contact_projection\":null")) {
    return false;
  }

  g_snapshot = {};
  g_snapshot.paused = true;
  g_snapshot.map_ready = true;
  g_snapshot.has_played_character = true;
  g_snapshot.played_character_alive = true;
  g_snapshot.date_raw = 53'178'264;
  g_reader_result = available;
  g_reader_result.snapshot_revision = 0;
  MainThreadQueryMailboxV1 mailbox{};
  mailbox.state.store(MainThreadQueryMailboxStateV1::executing);
  mailbox.published_sequence.store(9);
  mailbox.owner_thread_id.store(GetCurrentThreadId());
  mailbox.paused_owner_verified_pump_epochs.store(
      kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs);
  mailbox.executor =
      &ExecuteBattleReinforcementAssignmentMailboxQueryV1;
  BattleReinforcementAssignmentMailboxContextV1 context{};
  context.mailbox = &mailbox;
  context.ticket.sequence = 9;
  context.bindings.enabled = true;
  context.request.selected_public_cunit_id = 83'886'341;
  context.expected_snapshot_revision = 17;
  context.expected_snapshot = g_snapshot;
  mailbox.executor_context = &context;
  MainThreadExecutionStampV1 stamp{};
  stamp.pump_epoch = 3;
  stamp.thread_id = GetCurrentThreadId();
  stamp.paused = true;
  stamp.date_raw = g_snapshot.date_raw;
  stamp.tls_initialized_flag_address = 1;
  stamp.tls_initialized = 1;
  stamp.tls_context = 2;
  stamp.tls_main_thread_marker = 1;
  stamp.jomini_state = 3;
  stamp.game_state = 4;
  if (!ExecuteBattleReinforcementAssignmentMailboxQueryV1(&context, stamp) ||
      context.completion !=
          BattleReinforcementAssignmentMailboxCompletionV1::completed ||
      context.executor_invocations != 1 ||
      context.result.snapshot_revision != 17 ||
      context.result.selected_public_cunit_id != 83'886'341 ||
      SerializeBattleReinforcementAssignmentV1(context.result).empty()) {
    return false;
  }
  return true;
}

} // namespace

namespace xar::ck3_11906 {

bool ReadSnapshot(const Bindings &, game::Snapshot &output) noexcept {
  output = g_snapshot;
  return g_read_snapshot;
}

BattleReinforcementAssignmentStatus ReadBattleReinforcementAssignmentV1(
    const Bindings &, const Snapshot &,
    const BattleReinforcementAssignmentRequest &,
    BattleReinforcementAssignmentSnapshot &output) noexcept {
  output = g_reader_result;
  return output.status;
}

} // namespace xar::ck3_11906

int main() {
  if (!Run()) {
    std::cerr << "battle reinforcement assignment v1 mailbox fixture failed\n";
    return 1;
  }
  return 0;
}
