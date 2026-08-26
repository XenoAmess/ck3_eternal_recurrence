#pragma once

#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/loaded_feature_manifest_v1.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"

#include <cstdint>
#include <string_view>
#include <type_traits>

namespace xar::ck3_11906 {

inline constexpr std::uint32_t
    kLoadedFeatureManifestV1QueuedWaitBudgetMilliseconds = 8'000;
inline constexpr std::uint32_t
    kLoadedFeatureManifestV1ExecutingWaitSliceMilliseconds = 2'000;

bool ParseLoadedFeatureManifestV1Step(std::string_view step) noexcept;
bool ParseLoadedFeatureManifestExpectedRevisionV1(
    std::string_view json, std::uint64_t &output) noexcept;

enum class LoadedFeatureManifestMailboxCompletionV1 : std::uint32_t {
  not_executed = 0,
  completed = 1,
  frame_changed = 2,
  infrastructure_rejected = 3,
};

struct LoadedFeatureManifestMailboxContextV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  LoadedFeatureManifestNativeEnvironmentV1 environment{};
  LoadedFeatureManifestAccessV1 access{};
  LoadedFeatureManifestRequestV1 request{};
  game::Snapshot expected_snapshot{};

  LoadedFeatureManifestMailboxCompletionV1 completion =
      LoadedFeatureManifestMailboxCompletionV1::not_executed;
  game::ReadLoadedFeatureManifestResultV1 read_result =
      game::ReadLoadedFeatureManifestResultV1::unavailable;
  game::LoadedFeatureManifestV1 result{};
  MainThreadExecutionStampV1 execution_stamp{};
  std::uint32_t executor_invocations = 0;

  LoadedFeatureManifestMailboxContextV1() = default;
  LoadedFeatureManifestMailboxContextV1(
      const LoadedFeatureManifestMailboxContextV1 &) = delete;
  LoadedFeatureManifestMailboxContextV1 &operator=(
      const LoadedFeatureManifestMailboxContextV1 &) = delete;
  LoadedFeatureManifestMailboxContextV1(
      LoadedFeatureManifestMailboxContextV1 &&) = delete;
  LoadedFeatureManifestMailboxContextV1 &operator=(
      LoadedFeatureManifestMailboxContextV1 &&) = delete;
};

bool ExecuteLoadedFeatureManifestMailboxQueryV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept;

std::string_view LoadedFeatureManifestFailureMessageV1(
    MainThreadQueryWaitResultV1 wait,
    LoadedFeatureManifestMailboxCompletionV1 completion,
    bool completion_snapshot_stable) noexcept;

static_assert(
    std::is_same_v<decltype(&ExecuteLoadedFeatureManifestMailboxQueryV1),
                   MainThreadQueryExecutorV1>);

} // namespace xar::ck3_11906
