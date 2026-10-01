#pragma once

#include "xar_bridge/activity_feast_planner_open_v1.hpp"
#include "xar_bridge/activity_stage2_confirm_v1.hpp"
#include "xar_bridge/activity_stage2_destination_select_v1.hpp"
#include "xar_bridge/activity_stage2_location_read_v1.hpp"
#include "xar_bridge/ck3_12002_feast_planner.hpp"
#include "xar_bridge/game_contract.hpp"

namespace xar::ck3_12002 {

using ActivityPlanner12002ReadSnapshotV1 =
    bool (*)(void *, game::Snapshot &) noexcept;
using ActivityPlanner12002ResolveScriptIdentifierV1 =
    bool (*)(void *, std::int32_t, std::string_view &) noexcept;

// A single application-main invocation owns this context. All addresses and
// native objects remain here; serializers use only the existing semantic DTOs.
struct ActivityPlanner12002NativeV1 {
  bool enabled = false;
  std::uintptr_t module_base = 0;
  std::string_view executable_sha256{};
  void *native_context = nullptr;
  ActivityPlanner12002ReadSnapshotV1 read_snapshot = nullptr;
  bridge::ActivityPlannerDiagReadMemoryV1 read_memory = nullptr;
  ActivityPlanner12002ResolveScriptIdentifierV1 resolve_script_identifier = nullptr;
  std::uint64_t revision = 0;
  std::uint32_t owner_thread_id = 0;
  std::uintptr_t game_state = 0;
  std::uint32_t destination_state_reads = 0;
  bridge::ActivityStage2DestinationStateV1 destination_before{};
  bridge::ActivityStage2DestinationStateV1 destination_after{};
  bool destination_before_read = false;
  bool destination_after_read = false;
};

bool BindActivityPlanner12002V1(
    ActivityPlanner12002NativeV1 &output, std::uintptr_t module_base,
    std::string_view executable_sha256, void *native_context,
    ActivityPlanner12002ReadSnapshotV1 read_snapshot,
    bridge::ActivityPlannerDiagReadMemoryV1 read_memory,
    ActivityPlanner12002ResolveScriptIdentifierV1 resolve_script_identifier,
    std::uint64_t revision, std::uint32_t owner_thread_id,
    std::uintptr_t game_state) noexcept;

bridge::ActivityPlannerDiagEnvironmentV1
BuildActivityPlanner12002DiagEnvironmentV1(
    ActivityPlanner12002NativeV1 &context) noexcept;
bridge::ActivityFeastPlannerOpenEnvironmentV1
BuildActivityPlanner12002OpenEnvironmentV1(
    ActivityPlanner12002NativeV1 &context) noexcept;
bridge::ActivityStage1OptionEnvironmentV1
BuildActivityPlanner12002OptionEnvironmentV1(
    ActivityPlanner12002NativeV1 &context) noexcept;
bridge::ActivityStage2LocationEnvironmentV1
BuildActivityPlanner12002LocationEnvironmentV1(
    ActivityPlanner12002NativeV1 &context) noexcept;
bridge::ActivityStage2DestinationEnvironmentV1
BuildActivityPlanner12002DestinationEnvironmentV1(
    ActivityPlanner12002NativeV1 &context) noexcept;
bridge::ActivityStage2ConfirmEnvironmentV1
BuildActivityPlanner12002ConfirmEnvironmentV1(
    ActivityPlanner12002NativeV1 &context) noexcept;

} // namespace xar::ck3_12002
