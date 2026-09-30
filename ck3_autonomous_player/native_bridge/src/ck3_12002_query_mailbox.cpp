#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/ck3_12002.hpp"

#include <atomic>
#include <string_view>

namespace xar::ck3_12002 {
namespace {

bool OwnsSlot(const QueryMailboxEnvelope &query) noexcept {
  if (query.game == nullptr || query.mailbox == nullptr ||
      query.executor == nullptr || query.ticket.sequence == 0 ||
      query.expected_snapshot_revision == 0 || !query.entered ||
      !query.game->enabled() ||
      query.game->descriptor().adapter_id != "ck3-1.20.0.2-msvc-x64" ||
      query.game->descriptor().executable_sha256 != kExecutableSha256 ||
      GetCurrentThreadId() != query.execution_stamp.thread_id) {
    return false;
  }
  const auto &mailbox = *query.mailbox;
  return mailbox.state.load(std::memory_order_acquire) ==
             ck3_11906::MainThreadQueryMailboxStateV1::executing &&
         !mailbox.stop_requested.load(std::memory_order_acquire) &&
         mailbox.failure_flags.load(std::memory_order_acquire) == 0 &&
         mailbox.published_sequence.load(std::memory_order_acquire) ==
             query.ticket.sequence &&
         mailbox.owner_thread_id.load(std::memory_order_acquire) ==
             query.execution_stamp.thread_id &&
         mailbox.executor == query.executor &&
         mailbox.executor_context == &query;
}

void ReplaceIdentity(std::string &value, std::string_view from,
                     std::string_view to) {
  std::size_t at = 0;
  while ((at = value.find(from, at)) != std::string::npos) {
    value.replace(at, from.size(), to);
    at += to.size();
  }
}

} // namespace

bool EnterQueryMailbox(QueryMailboxEnvelope &query,
                       const ck3_11906::MainThreadExecutionStampV1 &stamp,
                       ck3_11906::MainThreadQueryExecutorV1 executor) noexcept {
  if (query.entered || executor == nullptr || stamp.pump_epoch == 0 ||
      stamp.thread_id == 0 || !stamp.paused || stamp.tls_initialized != 1 ||
      stamp.tls_main_thread_marker != 1 || stamp.tls_context == 0 ||
      stamp.jomini_state == 0 || stamp.game_state == 0) {
    return false;
  }
  query.execution_stamp = stamp;
  query.executor = executor;
  query.entered = true;
  game::Snapshot snapshot{};
  if (!CaptureQuerySnapshot(&query, snapshot)) {
    return false;
  }
  return true;
}

bool IsQueryOwningThread(void *opaque) noexcept {
  const auto *query = static_cast<const QueryMailboxEnvelope *>(opaque);
  return query != nullptr && OwnsSlot(*query);
}

bool CaptureQuerySnapshot(void *opaque, game::Snapshot &output) noexcept {
  const auto *query = static_cast<const QueryMailboxEnvelope *>(opaque);
  output = {};
  return query != nullptr && OwnsSlot(*query) &&
         game::ReadSnapshot(*query->game, output) &&
         output == query->expected_snapshot && output.paused &&
         output.date_raw == query->execution_stamp.date_raw;
}

bool FinishQueryMailbox(QueryMailboxEnvelope &query) noexcept {
  game::Snapshot snapshot{};
  query.frame_stable = CaptureQuerySnapshot(&query, snapshot);
  return query.frame_stable;
}

std::string RenderQueryBuildIdentity(std::string serialized) {
  ReplaceIdentity(serialized, "\"game_version\":\"1.19.0.6\"",
                  "\"game_version\":\"1.20.0.2\"");
  ReplaceIdentity(serialized, "\"version\":\"1.19.0.6\"",
                  "\"version\":\"1.20.0.2\"");
  ReplaceIdentity(serialized, "\"backend_id\":\"ck3-1.19.0.6-native-",
                  "\"backend_id\":\"ck3-1.20.0.2-native-");
  ReplaceIdentity(serialized,
                  "\"2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86\"",
                  "\"AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D\"");
  ReplaceIdentity(serialized,
                  "\"played-character-event-icon-indicators-1.19.0.6-v1\"",
                  "\"played-character-event-icon-indicators-1.20.0.2-v1\"");
  return serialized;
}

} // namespace xar::ck3_12002
