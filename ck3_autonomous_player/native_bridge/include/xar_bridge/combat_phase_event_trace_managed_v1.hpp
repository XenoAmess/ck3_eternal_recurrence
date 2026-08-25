#pragma once

#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/combat_phase_event_trace_detour_v1.hpp"
#include "xar_bridge/combat_phase_event_trace_wire_v1.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"

#include <cstdint>
#include <string>
#include <type_traits>

namespace xar::ck3_11906 {

// The reader, detours and bounded wire DTO are production sources.  The
// adapter remains unadvertised until bridge.cpp admits this typed pair and a
// paused same-combat live fixture records the managed checkpoint transition.
inline constexpr bool kCombatPhaseEventTraceCapturePlanBuilderV1Ready = true;
inline constexpr bool kCombatPhaseEventTraceManagedExecutorV1Wired = false;

enum class BuildCombatPhaseEventTraceCapturePlanV1Result : std::uint32_t {
  built = 0,
  exact_build_rejected = 1,
  invalid_request = 2,
  combat_unavailable = 3,
  native_slot_unavailable = 4,
  roster_unavailable = 5,
  battle_result_unavailable = 6,
  accolade_unavailable = 7,
  capacity_exceeded = 8,
  memory_fault = 9,
};

// Production uses the frozen module RVAs.  Overrides are fixture-only and
// keep exact plan construction testable without mapping the CK3 image.
struct CombatPhaseEventTracePlanEnvironmentV1 {
  bool exact_build_admitted = false;
  bool offline_fixture = false;
  std::uintptr_t module_base = 0;
  std::uintptr_t phase_event_database_slot_override = 0;
  std::uintptr_t current_date_slot_override = 0;
  std::uintptr_t global_rng_wrapper_slot_override = 0;
  void **battle_result_storage_slot_override = nullptr;
  void *battle_result_fallback_override = nullptr;
  void **accolade_storage_slot_override = nullptr;
  void *accolade_fallback_override = nullptr;
  std::uintptr_t battle_event_vtable_override = 0;
  std::uintptr_t accolade_rank_threshold_data_slot_override = 0;
  std::uintptr_t accolade_rank_threshold_count_slot_override = 0;
};

BuildCombatPhaseEventTraceCapturePlanV1Result
BuildCombatPhaseEventTraceCapturePlanV1(
    const Bindings &bindings,
    const CombatPhaseEventTracePlanEnvironmentV1 &environment,
    std::int32_t combat_id, std::uint64_t managed_daily_sequence_token,
    CombatPhaseEventTraceCapturePlanV1 &output) noexcept;

enum class CombatPhaseEventTraceManagedStageV1 : std::uint32_t {
  idle = 0,
  armed_waiting_for_one_day = 1,
  drained = 2,
  failed = 3,
};

enum class CombatPhaseEventTraceManagedCompletionV1 : std::uint32_t {
  not_executed = 0,
  armed = 1,
  bounded_trace_available = 2,
  trace_unavailable = 3,
  infrastructure_rejected = 4,
};

struct CombatPhaseEventTraceManagedCheckpointV1 {
  std::uint64_t managed_daily_sequence_token = 0;
  std::uint64_t pump_epoch = 0;
  std::uint32_t thread_id = 0;
  std::int32_t date_raw = 0;
  std::int32_t combat_id = -1;
  bool paused = false;

  friend bool operator==(const CombatPhaseEventTraceManagedCheckpointV1 &,
                         const CombatPhaseEventTraceManagedCheckpointV1 &) =
      default;
};

// Worker-owned storage.  It must outlive both mailbox tickets and the managed
// one-day checkpoint.  The external driver must create a recoverable save
// checkpoint before advancing; neither executor changes speed or game time.
struct CombatPhaseEventTraceManagedSessionV1 {
  CombatPhaseEventTraceManagedStageV1 stage =
      CombatPhaseEventTraceManagedStageV1::idle;
  CombatPhaseEventTraceRingV1 ring{};
  CombatPhaseEventTraceDetourStateV1 detours{};
  CombatPhaseEventTraceCapturePlanV1 plan{};
  CombatPhaseEventTraceRingDrainV1 drain{};
  CombatPhaseEventTraceManagedCheckpointV1 before{};
  CombatPhaseEventTraceManagedCheckpointV1 after{};
  BuildCombatPhaseEventTraceCapturePlanV1Result plan_result =
      BuildCombatPhaseEventTraceCapturePlanV1Result::invalid_request;
  std::string serialized_drain;
  bool recoverable_checkpoint_created = false;
  bool exact_one_day_observed = false;
  bool detours_uninstalled = false;

  CombatPhaseEventTraceManagedSessionV1() = default;
  CombatPhaseEventTraceManagedSessionV1(
      const CombatPhaseEventTraceManagedSessionV1 &) = delete;
  CombatPhaseEventTraceManagedSessionV1 &operator=(
      const CombatPhaseEventTraceManagedSessionV1 &) = delete;
};

struct CombatPhaseEventTraceBeginContextV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  CombatPhaseEventTraceManagedSessionV1 *session = nullptr;
  const Bindings *bindings = nullptr;
  CombatPhaseEventTracePlanEnvironmentV1 plan_environment{};
  CombatPhaseEventTraceDetourEnvironmentV1 detour_environment{};
  std::int32_t combat_id = -1;
  std::uint64_t managed_daily_sequence_token = 0;
  bool recoverable_checkpoint_created = false;
  CombatPhaseEventTraceManagedCompletionV1 completion =
      CombatPhaseEventTraceManagedCompletionV1::not_executed;
  std::uint32_t executor_invocations = 0;
};

struct CombatPhaseEventTraceFinishContextV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  CombatPhaseEventTraceManagedSessionV1 *session = nullptr;
  std::uint64_t managed_daily_sequence_token = 0;
  CombatPhaseEventTraceManagedCompletionV1 completion =
      CombatPhaseEventTraceManagedCompletionV1::not_executed;
  std::uint32_t executor_invocations = 0;
};

bool ExecuteCombatPhaseEventTraceBeginV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept;
bool ExecuteCombatPhaseEventTraceFinishV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept;

// Wraps the bounded drain fragment with the two managed checkpoints.  Empty
// means the session has not reached a terminal drain or exceeded the wire cap.
std::string SerializeCombatPhaseEventTraceManagedResultV1(
    const CombatPhaseEventTraceManagedSessionV1 &session);

static_assert(std::is_same_v<decltype(&ExecuteCombatPhaseEventTraceBeginV1),
                             MainThreadQueryExecutorV1>);
static_assert(std::is_same_v<decltype(&ExecuteCombatPhaseEventTraceFinishV1),
                             MainThreadQueryExecutorV1>);

} // namespace xar::ck3_11906
