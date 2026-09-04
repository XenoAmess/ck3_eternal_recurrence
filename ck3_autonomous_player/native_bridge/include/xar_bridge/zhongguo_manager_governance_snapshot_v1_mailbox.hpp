#pragma once

#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "xar_bridge/zhongguo_manager_governance_snapshot_v1.hpp"
#include "xar_bridge/zhongguo_manager_subordinate_selector_v1.hpp"

#include <cstdint>
#include <string_view>
#include <type_traits>

namespace xar::ck3_11906 {

inline constexpr std::uint32_t
    kZhongguoManagerGovernanceSnapshotV1QueuedWaitBudgetMilliseconds = 8'000;
inline constexpr std::uint32_t
    kZhongguoManagerGovernanceSnapshotV1ExecutingWaitSliceMilliseconds =
        2'000;

bool ParseZhongguoManagerGovernanceSnapshotV1Step(
    std::string_view step) noexcept;
bool ParseZhongguoManagerGovernanceSnapshotRequestV1(
    std::string_view json,
    ZhongguoManagerGovernanceSnapshotRequestV1 &output) noexcept;
bool ParseZhongguoManagerSubordinateSelectorV1Step(
    std::string_view step) noexcept;
bool ParseZhongguoManagerSubordinateSelectorRequestV1(
    std::string_view json,
    ZhongguoManagerSubordinateSelectorRequestV1 &output) noexcept;

enum class ZhongguoManagerGovernanceSnapshotMailboxCompletionV1
    : std::uint32_t {
  not_executed = 0,
  completed = 1,
  frame_changed = 2,
  infrastructure_rejected = 3,
};

enum class ZhongguoManagerGovernanceMailboxOperationV1 : std::uint32_t {
  manager_governance_snapshot = 0,
  manager_subordinate_selector = 1,
};

struct ZhongguoManagerGovernanceSnapshotMailboxContextV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  ZhongguoManagerGovernanceNativeEnvironmentV1 environment{};
  ZhongguoManagerGovernanceAccessV1 access{};
  ZhongguoManagerGovernanceSnapshotRequestV1 request{};
  ZhongguoManagerSubordinateSelectorNativeEnvironmentV1
      selector_environment{};
  ZhongguoManagerSubordinateSelectorAccessV1 selector_access{};
  ZhongguoManagerSubordinateSelectorRequestV1 selector_request{};
  game::Snapshot expected_snapshot{};
  ZhongguoManagerGovernanceMailboxOperationV1 operation =
      ZhongguoManagerGovernanceMailboxOperationV1::
          manager_governance_snapshot;

  ZhongguoManagerGovernanceSnapshotMailboxCompletionV1 completion =
      ZhongguoManagerGovernanceSnapshotMailboxCompletionV1::not_executed;
  game::ReadZhongguoManagerGovernanceSnapshotResultV1 read_result =
      game::ReadZhongguoManagerGovernanceSnapshotResultV1::unavailable;
  game::ZhongguoManagerGovernanceSnapshotV1 result{};
  game::ReadZhongguoManagerSubordinateSelectorResultV1 selector_read_result =
      game::ReadZhongguoManagerSubordinateSelectorResultV1::unavailable;
  game::ZhongguoManagerSubordinateSelectorSnapshotV1 selector_result{};
  MainThreadExecutionStampV1 execution_stamp{};
  std::uint32_t executor_invocations = 0;

  ZhongguoManagerGovernanceSnapshotMailboxContextV1() = default;
  ZhongguoManagerGovernanceSnapshotMailboxContextV1(
      const ZhongguoManagerGovernanceSnapshotMailboxContextV1 &) = delete;
  ZhongguoManagerGovernanceSnapshotMailboxContextV1 &operator=(
      const ZhongguoManagerGovernanceSnapshotMailboxContextV1 &) = delete;
  ZhongguoManagerGovernanceSnapshotMailboxContextV1(
      ZhongguoManagerGovernanceSnapshotMailboxContextV1 &&) = delete;
  ZhongguoManagerGovernanceSnapshotMailboxContextV1 &operator=(
      ZhongguoManagerGovernanceSnapshotMailboxContextV1 &&) = delete;
};

bool ExecuteZhongguoManagerGovernanceSnapshotMailboxQueryV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept;

std::string_view ZhongguoManagerGovernanceSnapshotFailureMessageV1(
    MainThreadQueryWaitResultV1 wait,
    ZhongguoManagerGovernanceSnapshotMailboxCompletionV1 completion,
    bool completion_snapshot_stable) noexcept;

static_assert(std::is_same_v<
              decltype(&ExecuteZhongguoManagerGovernanceSnapshotMailboxQueryV1),
              MainThreadQueryExecutorV1>);

} // namespace xar::ck3_11906
