#pragma once

#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "xar_bridge/player_prisoner_collection_query_v1_private.hpp"

#include <cstdint>
#include <string>
#include <string_view>

namespace xar::ck3_11906 {

inline constexpr std::string_view kPlayerPrisonerCollectionPrivateStepV1 =
    "query-player-prisoner-collection-private-v1";
inline constexpr std::uint32_t kPlayerPrisonerCollectionQueuedWaitMsV1 = 8'000;
inline constexpr std::uint32_t kPlayerPrisonerCollectionExecutingWaitMsV1 = 2'000;

struct PlayerPrisonerCollectionMailboxContextV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  game::Snapshot expected_snapshot{};
  std::uint64_t expected_revision = 0;
  xar::bridge::PlayerPrisonerCollectionSnapshotV1 result{};
  MainThreadExecutionStampV1 execution_stamp{};
  bool completed = false;
  bool frame_changed = false;
  std::uint32_t invocations = 0;
};

bool ExecutePlayerPrisonerCollectionPrivateQueryV1(
    void *context, const MainThreadExecutionStampV1 &stamp) noexcept;

// Value-only result for one exact paused native frame. No custody-kind or
// ransom/release legality is inferred from collection membership.
std::string SerializePlayerPrisonerCollectionPrivateV1(
    const xar::bridge::PlayerPrisonerCollectionSnapshotV1 &snapshot,
    std::uint64_t snapshot_revision);

} // namespace xar::ck3_11906
