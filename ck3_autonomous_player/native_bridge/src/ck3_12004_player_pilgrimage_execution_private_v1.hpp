#pragma once

#include "xar_bridge/activity_pilgrimage_planner_caller12004_v1.hpp"
#include "xar_bridge/activity_pilgrimage_start_capture_v1.hpp"
#include "xar_bridge/game_adapter.hpp"
#include <string>

namespace xar::ck3_12002 {

inline constexpr std::string_view kPilgrimagePlannerQuery12004V1 =
    "query-player-pilgrimage-planner-v1-private";
inline constexpr std::string_view kPilgrimagePlannerSubmit12004V1 =
    "submit-player-pilgrimage-planner-v1-private";

enum class PilgrimageExecutionOperation12004V1 {
  read, open, confirm, can_select, select, quote, start, post,
};
using PilgrimageExecutionAdmission12004V1 = bool (*)(
    void *, const bridge::ActivityCostSlot12ObserverV1 *) noexcept;
// Cold configuration only; the pointed process-life owner outlives the hook.
bool ConfigurePilgrimageExecutionAdmission12004V1(
    PilgrimageExecutionAdmission12004V1, void *) noexcept;

struct PlayerPilgrimageExecutionQuery12004V1 {
  ck3_11906::MainThreadQueryMailboxV1 *mailbox = nullptr;
  ck3_11906::MainThreadQueryTicketV1 ticket{};
  bool enabled = false;
  std::uintptr_t module_base = 0;
  std::string_view executable_sha256{};
  void *native_context = nullptr;
  ActivityPlanner12002ReadSnapshotV1 read_snapshot = nullptr;
  ActivityPlanner12002ResolveScriptIdentifierV1 resolve_script_identifier = nullptr;
  game::Snapshot expected_snapshot{};
  std::uint64_t expected_revision = 0;
  bridge::ActivityCostSlot12ObserverV1 *passive_cost = nullptr;
  PilgrimageExecutionAdmission12004V1 admission = nullptr;
  void *admission_context = nullptr;
  bridge::ActivityPilgrimageStartLedgerV1 *ledger = nullptr;
  PilgrimageExecutionOperation12004V1 operation{};
  std::uint32_t province_id = 0;
  std::int32_t read_stage = 0;
  bool policy_positive = false;
  std::array<std::int64_t, 4> reserve_by_name_raw{};
  ActivityPilgrimagePlannerResult12004V1 planner{};
  bridge::ActivityTypedFullCostResultV1 cost{};
  bridge::ActivityPilgrimageStage5StartResultV1 start{};
  bridge::ActivityPilgrimageReconcileResultV1 post{};
  bridge::ActivityPilgrimageStartStateV1 ledger_state{};
  std::string operation_status = "unavailable";
  std::string failure{};
  bool completed = false;
  bool frame_changed = false;
  std::uint32_t invocations = 0;
};

bool ExecutePlayerPilgrimageExecutionPrivate12004V1(
    void *, const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
bool IsPlayerPilgrimageExecutionPrivate12004V1(std::string_view step) noexcept;
bool HandlePlayerPilgrimageExecutionPrivate12004V1(
    const game::GameAdapter &, ck3_11906::MainThreadQueryMailboxV1 &,
    const game::Snapshot &, std::uint64_t revision, std::string_view step,
    std::string_view payload, std::string_view request_id,
    bridge::ActivityCostSlot12ObserverV1 *, std::string &serialized,
    std::string &failure) noexcept;
std::string SerializePlayerPilgrimageExecutionPrivate12004V1(
    const PlayerPilgrimageExecutionQuery12004V1 &);
std::string SerializePlayerPilgrimageExecutionCommandResult12004V1(
    const PlayerPilgrimageExecutionQuery12004V1 &,
    std::string_view request_id, std::string_view step);

} // namespace xar::ck3_12002
