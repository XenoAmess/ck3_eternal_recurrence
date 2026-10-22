#pragma once

#include "xar_bridge/activity_pilgrimage_planner_native_v1.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"

namespace xar::ck3_12002 {

enum class ActivityPilgrimagePlannerOperation12004V1 : std::uint8_t {
  read = 0,
  open = 1,
  confirm = 2,
  can_select = 3,
  select = 4,
};

struct ActivityPilgrimagePlannerRequest12004V1 {
  ActivityPilgrimagePlannerOperation12004V1 operation =
      ActivityPilgrimagePlannerOperation12004V1::read;
  bridge::ActivityPlannerDiagFrameV1 expected_frame{};
  std::uint32_t province_id = 0;
  // Read-only stage filter. 0 uses the currently observed stage; no navigation.
  std::int32_t read_stage = 0;
  std::string_view option_key = "pilgrimage_type_pious";
};

enum class ActivityPilgrimagePlannerStatus12004V1 : std::uint8_t {
  context_rejected,
  frame_changed,
  operation_rejected,
  private_action_disabled,
  native_result_unavailable,
  observed,
  opened,
  already_open,
  confirmed,
  can_select_observed,
  selected,
  postcondition_failed,
};

// This DTO remains inside the owner invocation. Native addresses in core state
// must not be serialized; central transport emits semantic identities/flags.
struct ActivityPilgrimagePlannerResult12004V1 {
  ActivityPilgrimagePlannerStatus12004V1 status =
      ActivityPilgrimagePlannerStatus12004V1::context_rejected;
  ActivityPilgrimagePlannerOperation12004V1 operation{};
  bool invoked = false;
  bool needs_recovery = false;
  bool pre_snapshot_observed = false;
  bool post_snapshot_observed = false;
  bool snapshot_unchanged = false;
  bridge::ActivityPlannerDiagResultV1 diagnostic{};
  bridge::ActivityPilgrimagePlannerOpenResultV1 open{};
  bridge::ActivityPilgrimageStage1OptionReadResultV1 stage1{};
  bridge::ActivityPilgrimageStage1ConfirmResultV1 confirm{};
  bridge::ActivityPilgrimageDestinationResultV1 destination_operation{};
  bool selection_observed = false;
  bridge::ActivityTypedPlannerSelectionV1 selection{};
  bool destination_observed = false;
  bridge::ActivityPilgrimageDestinationStateV1 destination{};
};

// Caller is not a mailbox executor/registration surface. Central transport must
// already own and validate its executing mailbox/ticket/executor slot and TLS
// stamp before binding this real ActivityPlanner12002NativeV1. This function
// independently rechecks exact4/current owner/stamp/frame/snapshot, then uses
// only the frozen typed native builders. No new RVA or arbitrary callback DTO.
bool ExecuteActivityPilgrimagePlannerOperation12004V1(
    ActivityPlanner12002NativeV1 &native,
    const ck3_11906::MainThreadExecutionStampV1 &stamp,
    const game::Snapshot &expected_snapshot,
    const ActivityPilgrimagePlannerRequest12004V1 &request,
    ActivityPilgrimagePlannerResult12004V1 &result) noexcept;

} // namespace xar::ck3_12002
