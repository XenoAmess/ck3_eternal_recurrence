#include "xar_bridge/activity_pilgrimage_planner_caller12004_v1.hpp"

namespace xar::ck3_12002 {
namespace {
using Operation = ActivityPilgrimagePlannerOperation12004V1;
using Status = ActivityPilgrimagePlannerStatus12004V1;

bool ValidOperation(const ActivityPilgrimagePlannerRequest12004V1 &request) noexcept {
  if (bridge::PilgrimageContractForKeyV1(request.option_key) == nullptr) return false;
  switch (request.operation) {
  case Operation::read:
    return request.province_id == 0 && request.read_stage >= 0 && request.read_stage <= 5;
  case Operation::open:
  case Operation::confirm:
    return request.province_id == 0 && request.read_stage == 0;
  case Operation::can_select:
  case Operation::select:
    return request.province_id > 0 && request.province_id <= 0x7FFFFFFFU &&
        request.read_stage == 0;
  }
  return false;
}

bool ContextMatches(const ActivityPlanner12002NativeV1 &native,
                    const ck3_11906::MainThreadExecutionStampV1 &stamp,
                    const game::Snapshot &snapshot,
                    const bridge::ActivityPlannerDiagFrameV1 &frame) noexcept {
  return native.enabled && native.module_base != 0 &&
      bridge::IsActivity12004BuildV1(native.executable_sha256) &&
      native.read_snapshot != nullptr && native.resolve_script_identifier != nullptr &&
      native.revision != 0 && native.revision == frame.revision &&
      native.owner_thread_id != 0 && GetCurrentThreadId() == native.owner_thread_id &&
      stamp.thread_id == native.owner_thread_id && stamp.pump_epoch != 0 &&
      stamp.paused && stamp.tls_initialized_flag_address != 0 &&
      stamp.tls_initialized == 1 && stamp.tls_context != 0 &&
      stamp.tls_main_thread_marker == 1 && stamp.jomini_state != 0 &&
      stamp.game_state != 0 && stamp.game_state == native.game_state &&
      stamp.date_raw == frame.date_raw && frame.application_main_thread &&
      frame.paused && frame.map_ready && frame.actor_alive &&
      frame.actor_character_id > 0 && snapshot.paused && snapshot.map_ready &&
      snapshot.has_played_character && snapshot.played_character_alive &&
      snapshot.date_raw == frame.date_raw &&
      snapshot.played_character_id == frame.actor_character_id;
}

bool SnapshotMatches(ActivityPlanner12002NativeV1 &native,
                     const game::Snapshot &expected, bool &observed) noexcept {
  game::Snapshot actual{};
  observed = native.read_snapshot != nullptr &&
      native.read_snapshot(native.native_context, actual);
  return observed && actual == expected;
}

void ReadCurrent(ActivityPlanner12002NativeV1 &native,
                 const bridge::ActivityPlannerDiagFrameV1 &frame,
                 ActivityPilgrimagePlannerResult12004V1 &result) noexcept {
  result.diagnostic = bridge::ReadActivityPlannerDiagV1(
      BuildActivityPlanner12002DiagEnvironmentV1(native), frame);
  if (result.diagnostic.status != bridge::ActivityPlannerDiagStatusV1::observed ||
      !result.diagnostic.value.widget_attached ||
      !result.diagnostic.value.widget_visible) return;
  const auto stage = result.diagnostic.value.stage;
  if (stage < 1 || stage > 5) return;
  result.selection_observed = ReadActivityPlanner12004PilgrimageSelectedOptionV1(
      &native, frame, stage, result.selection);
  if (stage == 1) {
    result.stage1 = bridge::ReadActivityPilgrimageStage1OptionV1(
        BuildActivityPlanner12004PilgrimageOptionEnvironmentV1(native), frame);
  } else {
    result.destination_observed = ReadActivityPlanner12004PilgrimageDestinationStateV1(
        &native, result.destination);
  }
}

} // namespace

bool ExecuteActivityPilgrimagePlannerOperation12004V1(
    ActivityPlanner12002NativeV1 &native,
    const ck3_11906::MainThreadExecutionStampV1 &stamp,
    const game::Snapshot &expected_snapshot,
    const ActivityPilgrimagePlannerRequest12004V1 &request,
    ActivityPilgrimagePlannerResult12004V1 &result) noexcept {
  result = {};
  result.operation = request.operation;
  if (!ValidOperation(request)) {
    result.status = Status::operation_rejected;
    return true;
  }
  // Freeze the reference before callbacks, including offline fixture aliases.
  const auto frame = request.expected_frame;
  if (!ContextMatches(native, stamp, expected_snapshot, frame)) return true;
  if (!SnapshotMatches(native, expected_snapshot, result.pre_snapshot_observed)) {
    result.status = Status::frame_changed;
    return true;
  }
#if !defined(XAR_CK3_ENABLE_PILGRIMAGE_PIOUS_PLANNER_PRIVATE_V1)
  if (request.operation == Operation::open || request.operation == Operation::confirm ||
      request.operation == Operation::select) {
    result.status = Status::private_action_disabled;
    return true;
  }
#endif
  result.status = Status::native_result_unavailable;
  // The requested option is a guard, never evidence of the current selection.
  // Read the original selected option before any confirmation/destination action.
  if (request.operation != Operation::open && request.operation != Operation::read) {
    ReadCurrent(native, frame, result);
    if (!result.selection_observed ||
        std::string_view(result.selection.option_key.data(),
                         result.selection.option_key_size) != request.option_key) {
      result.status = Status::operation_rejected;
      return true;
    }
  }
  switch (request.operation) {
  case Operation::read:
    ReadCurrent(native, frame, result);
    if (result.selection_observed &&
        (request.read_stage == 0 || request.read_stage == result.selection.planning_stage) &&
        (result.selection.planning_stage == 1 || result.destination_observed))
      result.status = Status::observed;
    break;
  case Operation::open:
    result.open = bridge::OpenActivityPilgrimagePlannerV1(
        BuildActivityPlanner12004PilgrimageOpenEnvironmentV1(native), frame);
    result.invoked = result.open.native_dispatch_invoked;
    result.needs_recovery = result.open.needs_recovery;
    if (result.open.status == bridge::ActivityPilgrimagePlannerOpenStatusV1::opened)
      result.status = Status::opened;
    else if (result.open.status == bridge::ActivityPilgrimagePlannerOpenStatusV1::already_open)
      result.status = Status::already_open;
    ReadCurrent(native, frame, result);
    break;
  case Operation::confirm:
    result.confirm = bridge::ConfirmActivityPilgrimageStage1V1(
        BuildActivityPlanner12004PilgrimageOptionEnvironmentV1(native), frame);
    result.invoked = result.confirm.submitted;
    result.needs_recovery = result.confirm.needs_recovery;
    if (result.confirm.status == bridge::ActivityPilgrimageStage1ConfirmStatusV1::stage_two_verified)
      result.status = Status::confirmed;
    ReadCurrent(native, frame, result);
    break;
  case Operation::can_select:
    result.destination_operation = bridge::ReadActivityPilgrimageDestinationCanSelectV1(
        BuildActivityPlanner12004PilgrimageDestinationEnvironmentV1(native), frame,
        request.province_id);
    if (result.destination_operation.status ==
        bridge::ActivityPilgrimageDestinationStatusV1::can_select_observed)
      result.status = Status::can_select_observed;
    ReadCurrent(native, frame, result);
    break;
  case Operation::select:
    result.destination_operation = bridge::SelectActivityPilgrimageDestinationV1(
        BuildActivityPlanner12004PilgrimageDestinationEnvironmentV1(native), frame,
        request.province_id);
    result.invoked = result.destination_operation.submitted;
    result.needs_recovery = result.destination_operation.needs_recovery;
    if (result.destination_operation.status ==
        bridge::ActivityPilgrimageDestinationStatusV1::selection_verified)
      result.status = Status::selected;
    ReadCurrent(native, frame, result);
    break;
  }
  const bool post_matches = SnapshotMatches(
      native, expected_snapshot, result.post_snapshot_observed);
  result.snapshot_unchanged = result.pre_snapshot_observed && post_matches;
  if (!result.snapshot_unchanged) {
    result.status = result.invoked ? Status::postcondition_failed : Status::frame_changed;
    if (result.invoked) result.needs_recovery = true;
  }
  // true means this typed request was examined. Only result.status/independent
  // receipts prove the semantic result; this is never an action-success ACK.
  return true;
}

} // namespace xar::ck3_12002
