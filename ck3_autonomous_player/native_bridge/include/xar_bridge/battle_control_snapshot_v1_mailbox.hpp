#pragma once

#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"

#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>
#include <type_traits>

namespace xar::ck3_11906 {

inline constexpr std::string_view kBattleControlSnapshotV1StepPrefix =
    "query-battle-control-snapshot-v1-";
inline constexpr std::string_view kBattleControlSnapshotV1Capability =
    "game.command.query-battle-control-snapshot-v1-N";
inline constexpr std::uint32_t
    kBattleControlSnapshotV1QueuedWaitBudgetMilliseconds = 8'000;
inline constexpr std::uint32_t
    kBattleControlSnapshotV1ExecutingWaitSliceMilliseconds = 2'000;
// Leave space for the enclosing command_result beneath protocol v1's frozen
// 1 MiB frame. Oversized real battles fail as a typed query instead of
// disconnecting the bridge only after the application-main read completed.
inline constexpr std::size_t kBattleControlSnapshotV1WireMaximumBytes =
    900U * 1024U;

bool ParseBattleControlSnapshotV1Step(
    std::string_view step,
    game::BattleControlRequest &output) noexcept;
bool ParseBattleControlExpectedRevisionV1(
    std::string_view json, std::uint64_t &output) noexcept;

enum class BattleControlSnapshotMailboxCompletionV1 : std::uint32_t {
  not_executed = 0,
  available = 1,
  query_unavailable = 2,
  frame_changed = 3,
  infrastructure_rejected = 4,
};

// Caller-owned stable storage. Once execution begins, the bridge worker keeps
// this object alive until a terminal wait and successful mailbox reclaim.
struct BattleControlSnapshotMailboxContextV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  game::BattleControlRequest request{};
  std::uint64_t expected_snapshot_revision = 0;
  game::Snapshot expected_snapshot{};

  BattleControlSnapshotMailboxCompletionV1 completion =
      BattleControlSnapshotMailboxCompletionV1::not_executed;
  game::BattleControlSnapshot result{};
  MainThreadExecutionStampV1 execution_stamp{};
  std::uint32_t executor_invocations = 0;

  BattleControlSnapshotMailboxContextV1() = default;
  BattleControlSnapshotMailboxContextV1(
      const BattleControlSnapshotMailboxContextV1 &) = delete;
  BattleControlSnapshotMailboxContextV1 &operator=(
      const BattleControlSnapshotMailboxContextV1 &) = delete;
  BattleControlSnapshotMailboxContextV1(
      BattleControlSnapshotMailboxContextV1 &&) = delete;
  BattleControlSnapshotMailboxContextV1 &operator=(
      BattleControlSnapshotMailboxContextV1 &&) = delete;
};

bool ExecuteBattleControlSnapshotMailboxQueryV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept;

std::string_view BattleControlSnapshotFailureMessageV1(
    MainThreadQueryWaitResultV1 wait,
    BattleControlSnapshotMailboxCompletionV1 completion,
    game::BattleControlSnapshotStatus status,
    bool completion_snapshot_stable) noexcept;

// Only a complete exact-build available frame is serializable. The payload
// includes every field frozen by battle_control_snapshot_v1_abi.json.
std::string SerializeBattleControlSnapshotV1(
    const game::BattleControlSnapshot &snapshot);

static_assert(
    std::is_same_v<decltype(&ExecuteBattleControlSnapshotMailboxQueryV1),
                   MainThreadQueryExecutorV1>);

} // namespace xar::ck3_11906
