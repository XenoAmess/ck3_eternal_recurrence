#pragma once

#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "xar_bridge/steward_develop_county_candidates_v1.hpp"

#include <cstdint>
#include <string_view>
#include <type_traits>

namespace xar::ck3_11906 {

inline constexpr std::uint32_t
    kStewardDevelopCountyCandidatesV1QueuedWaitBudgetMilliseconds = 8'000;
inline constexpr std::uint32_t
    kStewardDevelopCountyCandidatesV1ExecutingWaitSliceMilliseconds = 2'000;

bool ParseStewardDevelopCountyCandidatesV1Step(
    std::string_view step) noexcept;
bool ParseStewardDevelopCountyCandidatesExpectedRevisionV1(
    std::string_view json, std::uint64_t &output) noexcept;

enum class StewardDevelopCountyCandidatesMailboxCompletionV1 : std::uint32_t {
  not_executed = 0,
  completed = 1,
  frame_changed = 2,
  infrastructure_rejected = 3,
};

struct StewardDevelopCountyCandidatesMailboxContextV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  StewardDevelopCountyCandidatesNativeEnvironmentV1 environment{};
  StewardDevelopCountyCandidatesAccessV1 access{};
  StewardDevelopCountyCandidatesRequestV1 request{};
  game::Snapshot expected_snapshot{};

  StewardDevelopCountyCandidatesMailboxCompletionV1 completion =
      StewardDevelopCountyCandidatesMailboxCompletionV1::not_executed;
  game::ReadStewardDevelopCountyCandidatesResultV1 read_result =
      game::ReadStewardDevelopCountyCandidatesResultV1::unavailable;
  game::StewardDevelopCountyCandidatesV1 result{};
  MainThreadExecutionStampV1 execution_stamp{};
  std::uint32_t executor_invocations = 0;

  StewardDevelopCountyCandidatesMailboxContextV1() = default;
  StewardDevelopCountyCandidatesMailboxContextV1(
      const StewardDevelopCountyCandidatesMailboxContextV1 &) = delete;
  StewardDevelopCountyCandidatesMailboxContextV1 &operator=(
      const StewardDevelopCountyCandidatesMailboxContextV1 &) = delete;
  StewardDevelopCountyCandidatesMailboxContextV1(
      StewardDevelopCountyCandidatesMailboxContextV1 &&) = delete;
  StewardDevelopCountyCandidatesMailboxContextV1 &operator=(
      StewardDevelopCountyCandidatesMailboxContextV1 &&) = delete;
};

bool ExecuteStewardDevelopCountyCandidatesMailboxQueryV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept;

std::string_view StewardDevelopCountyCandidatesFailureMessageV1(
    MainThreadQueryWaitResultV1 wait,
    StewardDevelopCountyCandidatesMailboxCompletionV1 completion,
    bool completion_snapshot_stable) noexcept;

static_assert(
    std::is_same_v<
        decltype(&ExecuteStewardDevelopCountyCandidatesMailboxQueryV1),
        MainThreadQueryExecutorV1>);

} // namespace xar::ck3_11906
