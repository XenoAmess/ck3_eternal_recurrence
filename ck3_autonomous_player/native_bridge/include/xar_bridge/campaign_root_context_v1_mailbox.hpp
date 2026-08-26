#pragma once

#include "xar_bridge/campaign_root_context_v1.hpp"
#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"

#include <cstdint>
#include <string_view>
#include <type_traits>

namespace xar::ck3_11906 {

inline constexpr std::uint32_t
    kCampaignRootContextV1QueuedWaitBudgetMilliseconds = 8'000;
inline constexpr std::uint32_t
    kCampaignRootContextV1ExecutingWaitSliceMilliseconds = 2'000;

bool ParseCampaignRootContextV1Step(std::string_view step) noexcept;
bool ParseCampaignRootContextExpectedRevisionV1(
    std::string_view json, std::uint64_t &output) noexcept;

enum class CampaignRootContextMailboxCompletionV1 : std::uint32_t {
  not_executed = 0,
  completed = 1,
  frame_changed = 2,
  infrastructure_rejected = 3,
};

struct CampaignRootContextMailboxContextV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  CampaignRootNativeEnvironmentV1 environment{};
  CampaignRootAccessV1 access{};
  CampaignRootContextRequestV1 request{};
  game::Snapshot expected_snapshot{};

  CampaignRootContextMailboxCompletionV1 completion =
      CampaignRootContextMailboxCompletionV1::not_executed;
  game::ReadCampaignRootContextResultV1 read_result =
      game::ReadCampaignRootContextResultV1::unavailable;
  game::CampaignRootContextV1 result{};
  MainThreadExecutionStampV1 execution_stamp{};
  std::uint32_t executor_invocations = 0;

  CampaignRootContextMailboxContextV1() = default;
  CampaignRootContextMailboxContextV1(
      const CampaignRootContextMailboxContextV1 &) = delete;
  CampaignRootContextMailboxContextV1 &operator=(
      const CampaignRootContextMailboxContextV1 &) = delete;
  CampaignRootContextMailboxContextV1(
      CampaignRootContextMailboxContextV1 &&) = delete;
  CampaignRootContextMailboxContextV1 &operator=(
      CampaignRootContextMailboxContextV1 &&) = delete;
};

bool ExecuteCampaignRootContextMailboxQueryV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept;

std::string_view CampaignRootContextFailureMessageV1(
    MainThreadQueryWaitResultV1 wait,
    CampaignRootContextMailboxCompletionV1 completion,
    bool completion_snapshot_stable) noexcept;

static_assert(
    std::is_same_v<decltype(&ExecuteCampaignRootContextMailboxQueryV1),
                   MainThreadQueryExecutorV1>);

} // namespace xar::ck3_11906
