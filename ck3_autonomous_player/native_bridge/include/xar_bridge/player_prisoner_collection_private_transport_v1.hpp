#pragma once

#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "xar_bridge/player_prisoner_collection_query_v1_private.hpp"
#if defined(XAR_CK3_ENABLE_G2_PRISONER_RELEASE_PREVIEW_PRIVATE_V1)
#include "xar_bridge/character_interaction_preview_v1.hpp"
#endif
#if defined(XAR_CK3_ENABLE_G2_PRISONER_RANSOM_PREVIEW_PRIVATE_V1)
#include "xar_bridge/player_prisoner_ransom_private_v1.hpp"
#endif

#include <cstdint>
#include <charconv>
#include <string>
#include <string_view>

namespace xar::ck3_11906 {

inline constexpr std::string_view kPlayerPrisonerCollectionPrivateStepV1 =
    "query-player-prisoner-collection-private-v1";
inline constexpr std::string_view kPlayerPrisonerCollectionRansomOrdinalPrefixV1 =
    "query-player-prisoner-collection-private-v1-ransom-ordinal-";

inline bool ParsePlayerPrisonerCollectionPrivateStepV1(
    std::string_view step, std::uint32_t &ransom_ordinal) noexcept {
  ransom_ordinal = 0;
  if (step == kPlayerPrisonerCollectionPrivateStepV1) return true;
#if defined(XAR_CK3_ENABLE_G2_PRISONER_RANSOM_PREVIEW_PRIVATE_V1)
  if (!step.starts_with(kPlayerPrisonerCollectionRansomOrdinalPrefixV1))
    return false;
  const auto suffix = step.substr(kPlayerPrisonerCollectionRansomOrdinalPrefixV1.size());
  if (suffix.empty() || suffix.front() == '0') return false;
  std::uint32_t parsed = 0;
  const auto [end, error] = std::from_chars(
      suffix.data(), suffix.data() + suffix.size(), parsed);
  if (error != std::errc{} || end != suffix.data() + suffix.size() ||
      parsed >= xar::bridge::kPlayerPrisonerMaximumRowsV1)
    return false;
  ransom_ordinal = parsed;
  return true;
#else
  return false;
#endif
}
inline constexpr std::uint32_t kPlayerPrisonerCollectionQueuedWaitMsV1 = 8'000;
inline constexpr std::uint32_t kPlayerPrisonerCollectionExecutingWaitMsV1 = 2'000;

// Keep the read-only query fail-closed while identifying which independent
// same-frame gate rejected it. A generic failure hides queued timeouts and
// executor failures behind the same error as a serializer failure.
inline constexpr std::string_view PlayerPrisonerCollectionFailureDetailV1(
    MainThreadQueryWaitResultV1 wait, bool completed, bool frame_changed,
    bool completion_snapshot_read, bool completion_snapshot_matches) noexcept {
  switch (wait) {
  case MainThreadQueryWaitResultV1::completed: break;
  case MainThreadQueryWaitResultV1::executor_failed:
    return "prisoner collection main-thread executor failed";
  case MainThreadQueryWaitResultV1::infrastructure_failed:
    return "prisoner collection main-thread infrastructure failed";
  case MainThreadQueryWaitResultV1::cancelled:
    return "prisoner collection main-thread query was cancelled";
  case MainThreadQueryWaitResultV1::timeout_cancelled_before_execution:
    return "prisoner collection main-thread query timed out before execution";
  case MainThreadQueryWaitResultV1::timeout_executor_already_running:
    return "prisoner collection main-thread executor did not finish";
  case MainThreadQueryWaitResultV1::ticket_mismatch:
    return "prisoner collection main-thread ticket mismatched";
  }
  if (!completed)
    return "prisoner collection executor did not mark completion";
  if (frame_changed)
    return "prisoner collection main-thread frame changed";
  if (!completion_snapshot_read)
    return "prisoner collection completion snapshot was unreadable";
  if (!completion_snapshot_matches)
    return "prisoner collection completion snapshot changed";
  return "prisoner collection result serialization failed";
}

struct PlayerPrisonerCollectionMailboxContextV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  game::Snapshot expected_snapshot{};
  std::uint64_t expected_revision = 0;
  std::uint32_t requested_ransom_ordinal = 0;
  xar::bridge::PlayerPrisonerCollectionSnapshotV1 result{};
#if defined(XAR_CK3_ENABLE_G2_PRISONER_RELEASE_PREVIEW_PRIVATE_V1)
  std::array<game::CharacterInteractionPreviewV1,
             xar::bridge::kPlayerPrisonerMaximumRowsV1>
      release_previews{};
  bool release_previews_complete = false;
#endif
#if defined(XAR_CK3_ENABLE_G2_PRISONER_RANSOM_PREVIEW_PRIVATE_V1)
  std::array<PlayerPrisonerRansomQuoteV1,
             xar::bridge::kPlayerPrisonerMaximumRowsV1>
      ransom_quotes{};
  bool ransom_quotes_complete = false;
#endif
  MainThreadExecutionStampV1 execution_stamp{};
  bool completed = false;
  bool frame_changed = false;
  std::uint32_t invocations = 0;
};

bool ExecutePlayerPrisonerCollectionPrivateQueryV1(
    void *context, const MainThreadExecutionStampV1 &stamp) noexcept;

#if defined(XAR_CK3_ENABLE_G2_PRISONER_RANSOM_ACTION_PRIVATE_V1)
inline constexpr std::string_view kPlayerPrisonerRansomSubmitPrivateStepV1 =
    "submit-player-prisoner-ransom-private-v1";

struct PlayerPrisonerRansomSubmitMailboxContextV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  game::Snapshot expected_snapshot{};
  PlayerPrisonerRansomQuoteV1 quote{};
  std::uint64_t expected_revision = 0;
  PlayerPrisonerRansomSubmitV1 result =
      PlayerPrisonerRansomSubmitV1::unavailable;
  bool completed = false;
  bool frame_changed = false;
  std::uint32_t invocations = 0;
};

bool ExecutePlayerPrisonerRansomPrivateSubmitV1(
    void *context, const MainThreadExecutionStampV1 &stamp) noexcept;
#endif

// Value-only result for one exact paused native frame. Collection membership
// never infers legality; the separately enabled native-final release preview
// records its own result for each exact prisoner ID.
std::string SerializePlayerPrisonerCollectionPrivateV1(
    const xar::bridge::PlayerPrisonerCollectionSnapshotV1 &snapshot,
    std::uint64_t snapshot_revision
#if defined(XAR_CK3_ENABLE_G2_PRISONER_RELEASE_PREVIEW_PRIVATE_V1)
    , const std::array<game::CharacterInteractionPreviewV1,
                       xar::bridge::kPlayerPrisonerMaximumRowsV1>
          &release_previews,
    bool release_previews_complete
#endif
#if defined(XAR_CK3_ENABLE_G2_PRISONER_RANSOM_PREVIEW_PRIVATE_V1)
    , const std::array<PlayerPrisonerRansomQuoteV1,
                       xar::bridge::kPlayerPrisonerMaximumRowsV1>
          &ransom_quotes,
    bool ransom_quotes_complete
#endif
);

} // namespace xar::ck3_11906
