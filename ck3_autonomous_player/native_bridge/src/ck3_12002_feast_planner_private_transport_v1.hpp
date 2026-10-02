#pragma once

#include "activity_feast_planner_open_private_transport_v1.hpp"
#include "activity_planner_diag_private_transport_v1.hpp"
#include "activity_stage1_option_read_private_transport_v1.hpp"
#include "activity_stage2_destination_select_private_transport_v1.hpp"
#include "xar_bridge/ck3_12002_feast_planner_native.hpp"

namespace xar::ck3_12002 {

// Legacy inheritance reuses the existing DTO and serializer contract only.
// No executor below reads the inherited 1.19 Bindings member.
template <class LegacyQuery>
struct ActivityPlannerPrivate12002QueryBaseV1 : LegacyQuery {
  bool enabled = false;
  std::uintptr_t module_base = 0;
  std::string_view executable_sha256{};
  void *native_context = nullptr;
  ActivityPlanner12002ReadSnapshotV1 read_snapshot = nullptr;
  ActivityPlanner12002ResolveScriptIdentifierV1 resolve_script_identifier = nullptr;
  bridge::ActivityPlannerDiagReadMemoryV1 read_memory = nullptr;
};

struct ActivityPlannerDiagPrivate12002QueryV1
    : ActivityPlannerPrivate12002QueryBaseV1<
          ck3_11906::ActivityPlannerDiagPrivateQueryV1> {};
enum class ActivityFeastPlannerOpenOperation12002V1 {
  planner_open,
  current_activity_view_open,
};

inline constexpr std::string_view kCurrentActivityViewOpenPrivate12003StepV1 =
    "open-current-activity-view-v1-private";

struct ActivityFeastPlannerOpenPrivate12002QueryV1
    : ActivityPlannerPrivate12002QueryBaseV1<
          ck3_11906::ActivityFeastPlannerOpenPrivateQueryV1> {
  ActivityFeastPlannerOpenOperation12002V1 operation =
      ActivityFeastPlannerOpenOperation12002V1::planner_open;
  std::string_view actual_executable_sha256{};
  std::uint32_t expected_activity_id = 0;
  std::uint32_t current_view_activity_id = 0;
  bool current_view_dispatch_invoked = false;
};
struct ActivityStage1OptionReadPrivate12002QueryV1
    : ActivityPlannerPrivate12002QueryBaseV1<
          ck3_11906::ActivityStage1OptionReadPrivateQueryV1> {};
struct ActivityStage2DestinationSelectPrivate12002QueryV1
    : ActivityPlannerPrivate12002QueryBaseV1<
          ck3_11906::ActivityStage2DestinationSelectPrivateQueryV1> {};
struct ActivityStage2ConfirmPrivate12002QueryV1
    : ActivityPlannerPrivate12002QueryBaseV1<
          ck3_11906::ActivityStage1OptionReadPrivateQueryV1> {
  bridge::ActivityStage2ConfirmResultV1 stage_two_confirm_result{};
};

inline constexpr std::string_view kActivityStage2ConfirmPrivate12002StepV1 =
    "confirm-activity-feast-stage2-v1-private";

bool ExecuteActivityPlannerDiagPrivate12002QueryV1(
    void *context,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept;
bool ExecuteActivityFeastPlannerOpenPrivate12002V1(
    void *context,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept;
bool ExecuteActivityStage1OptionReadPrivate12002V1(
    void *context,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept;
bool ExecuteActivityStage2DestinationSelectPrivate12002V1(
    void *context,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept;
bool ExecuteActivityStage2ConfirmPrivate12002V1(
    void *context,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept;

std::string SerializeActivityStage2ConfirmPrivate12002V1(
    const ActivityStage2ConfirmPrivate12002QueryV1 &query);

} // namespace xar::ck3_12002
