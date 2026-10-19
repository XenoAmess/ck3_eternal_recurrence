#pragma once

#include "xar_bridge/ck3_12002_feast_planner_native.hpp"
#include "xar_bridge/activity_pilgrimage_planner_open_v1.hpp"
#include "xar_bridge/activity_pilgrimage_stage1_v1.hpp"
#include "xar_bridge/activity_pilgrimage_destination_v1.hpp"

namespace xar::ck3_12002 {

bridge::ActivityPilgrimagePlannerOpenEnvironmentV1
BuildActivityPlanner12004PilgrimageOpenEnvironmentV1(
    ActivityPlanner12002NativeV1 &context) noexcept;

bridge::ActivityPilgrimageStage1OptionEnvironmentV1
BuildActivityPlanner12004PilgrimageOptionEnvironmentV1(
    ActivityPlanner12002NativeV1 &context) noexcept;

bridge::ActivityPilgrimageDestinationEnvironmentV1
BuildActivityPlanner12004PilgrimageDestinationEnvironmentV1(
    ActivityPlanner12002NativeV1 &context) noexcept;

// Opaque is the current invocation's owner-bound ActivityPlanner12002NativeV1.
// This producer does not advance the planner or call a world action.
bool ReadActivityPlanner12004PilgrimageSelectedOptionV1(
    void *opaque, const bridge::ActivityPlannerDiagFrameV1 &expected,
    std::int32_t required_stage,
    bridge::ActivityTypedPlannerSelectionV1 &output) noexcept;

// Independent current read, including stage5. Does not reuse an action result.
bool ReadActivityPlanner12004PilgrimageDestinationStateV1(
    void *opaque, bridge::ActivityPilgrimageDestinationStateV1 &output) noexcept;

} // namespace xar::ck3_12002
