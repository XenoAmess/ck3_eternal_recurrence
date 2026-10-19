#pragma once

#include "xar_bridge/activity_pilgrimage_stage5_start_v1.hpp"
#include "xar_bridge/activity_typed_full_cost_v1.hpp"
#include "xar_bridge/activity_pilgrimage_destination_v1.hpp"

namespace xar::bridge {

// Invocation-owned adapters. The native mailbox caller still must construct
// these from the CURRENT owner-bound context; this is not a public MCP route.
struct ActivityPilgrimageStartCaptureSourcesV1 {
  ActivityTypedFullCostEnvironmentV1 cost{};
  ActivityHostedIdentityEnvironmentV1 hosted{};
  ActivityPilgrimageDestinationReadStateV1 read_destination = nullptr;
  void *destination_context = nullptr;
};

bool CaptureActivityPilgrimageStage5V1(
    void *sources, const ActivityPlannerDiagFrameV1 &expected,
    ActivityPilgrimageStage5SnapshotV1 &output) noexcept;

// Binds the one Start context to Sources, forwarding memory reads to the
// diagnostic reader's own native context. Never pass that reader directly with
// a Sources pointer; the two callback contexts are different software objects.
ActivityPilgrimageStage5StartEnvironmentV1
BuildActivityPilgrimageStage5StartEnvironmentV1(
    ActivityPilgrimageStartCaptureSourcesV1 &sources) noexcept;

} // namespace xar::bridge
