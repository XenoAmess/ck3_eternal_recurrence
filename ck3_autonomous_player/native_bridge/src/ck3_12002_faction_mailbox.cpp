#include "xar_bridge/ck3_12002_faction_mailbox.hpp"
#include "xar_bridge/ck3_12002_semantic_adapter.hpp"

#include <windows.h>

namespace xar::ck3_12002 {
namespace {

bool CaptureFactionFrame(void *opaque,
                         game::PlayerFactionAlertsFrameV1 &output) noexcept {
  auto *envelope = static_cast<QueryMailboxEnvelope *>(opaque);
  game::Snapshot snapshot{};
  if (!envelope || !CaptureQuerySnapshot(envelope, snapshot)) return false;
  output = {envelope->expected_snapshot_revision, snapshot.date_raw,
            snapshot.paused, snapshot.map_ready, snapshot.has_played_character,
            snapshot.played_character_alive, snapshot.played_character_id};
  return true;
}

} // namespace

bool ExecutePlayerFactionAlertsMailbox12002(
    void *opaque, const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *envelope = static_cast<QueryMailboxEnvelope *>(opaque);
  if (!envelope || !envelope->typed_context ||
      !EnterQueryMailbox(*envelope, stamp, &ExecutePlayerFactionAlertsMailbox12002))
    return true;
  auto &query = *static_cast<PlayerFactionAlertsMailboxContext12002 *>(
      envelope->typed_context);
  PlayerFactionAlertsAccessV1 access{envelope, &CaptureFactionFrame,
                                    &IsQueryOwningThread};
  query.read_result = ReadPlayerFactionAlertsV1(
      query.environment, access, {envelope->expected_snapshot_revision}, query.result);
  query.completed = !SerializePlayerFactionAlertsV1(query.result).empty();
  (void)FinishQueryMailbox(*envelope);
  return true;
}

bool ReadPlayerFactionAlertsOnApplicationMain12002(
    const game::GameAdapter &adapter, ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision,
    std::string &serialized, std::string &failure) noexcept {
  serialized.clear();
  failure.clear();
  try {
    if (!adapter.enabled() ||
        adapter.descriptor().executable_sha256 != kPlayerFactionAlertsV1ExecutableSha256 ||
        !revision || !published.paused || !published.map_ready ||
        !published.has_played_character || !published.played_character_alive) {
      failure = "requires_paused";
      return false;
    }
    PlayerFactionAlertsMailboxContext12002 query{};
    query.envelope.game = &NativeAdapter12002(adapter);
    query.envelope.mailbox = &mailbox;
    query.envelope.expected_snapshot = published;
    query.envelope.expected_snapshot_revision = revision;
    query.envelope.typed_context = &query;
    query.environment = BindPlayerFactionAlertsNativeEnvironmentV1(
        reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)), true);
    const auto submitted = ck3_11906::TrySubmitMainThreadQueryV1(
        mailbox, &ExecutePlayerFactionAlertsMailbox12002, &query.envelope,
        query.envelope.ticket);
    if (submitted != ck3_11906::MainThreadQuerySubmitResultV1::submitted) {
      failure = "application-main faction query unavailable";
      return false;
    }
    auto wait = ck3_11906::WaitForMainThreadQueryV1(mailbox, query.envelope.ticket, 8'000);
    while (wait == ck3_11906::MainThreadQueryWaitResultV1::timeout_executor_already_running)
      wait = ck3_11906::WaitForMainThreadQueryV1(mailbox, query.envelope.ticket, 2'000);
    const auto reclaimed = ck3_11906::ReclaimMainThreadQueryV1(mailbox, query.envelope.ticket);
    if (wait != ck3_11906::MainThreadQueryWaitResultV1::completed ||
        reclaimed != ck3_11906::MainThreadQueryReclaimResultV1::reclaimed ||
        !query.envelope.frame_stable || !query.completed) {
      failure = "application-main faction query did not complete";
      return false;
    }
    serialized = SerializePlayerFactionAlertsV1(query.result);
    return !serialized.empty();
  } catch (...) {
    failure = "application-main faction query failed";
    return false;
  }
}

} // namespace xar::ck3_12002
