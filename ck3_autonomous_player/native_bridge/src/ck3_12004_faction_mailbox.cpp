#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12004_faction_mailbox.hpp"

#include <windows.h>

namespace xar::ck3_12004 {
namespace {
bool CaptureFactionFrame(void *opaque, game::PlayerFactionAlertsFrameV1 &output) noexcept {
  auto *envelope = static_cast<ck3_12002::QueryMailboxEnvelope *>(opaque);
  game::Snapshot snapshot{};
  if (!envelope || !ck3_12002::CaptureQuerySnapshot(envelope, snapshot)) return false;
  output = {envelope->expected_snapshot_revision, snapshot.date_raw,
            snapshot.paused, snapshot.map_ready, snapshot.has_played_character,
            snapshot.played_character_alive, snapshot.played_character_id};
  return true;
}
std::string Quote(std::string_view input) {
  std::string output = "\"";
  constexpr char hex[] = "0123456789abcdef";
  for (unsigned char c : input) {
    if (c == '"' || c == '\\') { output += '\\'; output += static_cast<char>(c); }
    else if (c < 0x20) {
      output += "\\u00"; output += hex[c >> 4]; output += hex[c & 15];
    } else output += static_cast<char>(c);
  }
  return output + '"';
}
} // namespace

bool ExecutePlayerFactionAlertsMailbox12004(
    void *opaque, const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *envelope = static_cast<ck3_12002::QueryMailboxEnvelope *>(opaque);
  if (!envelope || !envelope->typed_context ||
      !ck3_12002::EnterQueryMailbox(*envelope, stamp, &ExecutePlayerFactionAlertsMailbox12004))
    return true;
  auto &query = *static_cast<PlayerFactionAlertsMailboxContext12004 *>(envelope->typed_context);
  PlayerFactionAlertsAccessV1 access{envelope, &CaptureFactionFrame,
                                    &ck3_12002::IsQueryOwningThread};
  (void)ck3_12004::ReadPlayerFactionAlerts12004(
      query.environment, access, {envelope->expected_snapshot_revision}, query.result);
  query.completed = true;
  (void)ck3_12002::FinishQueryMailbox(*envelope);
  return true;
}

std::string SerializePlayerFactionAlertsWhole12004(
    const game::PlayerFactionAlertsV1 &snapshot, std::uint64_t sequence,
    std::string_view request_id, const game::AdapterDescriptor &descriptor) {
  const auto material = ck3_12004::SerializePlayerFactionAlerts12004(snapshot);
  const auto status = snapshot.status == game::PlayerFactionAlertsStatusV1::available
      ? "available" : "unavailable";
  return game::Render12004BuildIdentity(
      "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":" +
      Quote(request_id) + ",\"ok\":true,\"result\":{\"step\":\"query-player-faction-alerts-v1\","
      "\"accepted\":true,\"status\":" + Quote(status) +
      ",\"query_sequence\":" + std::to_string(sequence) +
      ",\"snapshot_revision\":" + std::to_string(snapshot.snapshot_revision) +
      ",\"player_faction_alerts\":" + material +
      ",\"player_faction_alerts_ready\":" + (snapshot.readiness.alert_ready ? "true" : "false") +
      ",\"backend_id\":\"native-headless\"}}", descriptor);
}

bool HandlePlayerFactionAlerts12004(
    const game::GameAdapter &adapter, ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view payload, std::string_view request_id,
    std::string &serialized, std::string &failure,
    const PlayerFactionAlertsNativeEnvironmentV1 *fixture_environment) noexcept {
  serialized.clear(); failure.clear();
  try {
    std::uint64_t expected = 0;
    if (!adapter.enabled() || !game::IsCk3_12004Descriptor(adapter.descriptor()) ||
        !ck3_11906::ParsePlayerFactionAlertsExpectedRevisionV1(payload, expected) ||
        !revision || expected != revision || !published.paused || !published.map_ready ||
        !published.has_played_character || !published.played_character_alive) {
      failure = "player_faction_actual4_frame_invalid"; return false;
    }
    if (fixture_environment && !mailbox.offline_fixture) {
      failure = "player_faction_fixture_mailbox_required"; return false;
    }
    PlayerFactionAlertsMailboxContext12004 query{};
    query.envelope.game = &adapter;
    query.envelope.mailbox = &mailbox;
    query.envelope.expected_snapshot = published;
    query.envelope.expected_snapshot_revision = revision;
    // CaptureFactionFrame consumes precisely the eight shared core fields.
    query.envelope.snapshot_comparison = fixture_environment
        ? ck3_12002::QuerySnapshotComparison12002::full_snapshot
        : ck3_12002::QuerySnapshotComparison12002::core_frame;
    query.envelope.typed_context = &query;
    query.environment = fixture_environment ? *fixture_environment :
        ck3_12004::BindPlayerFactionAlertsImage12004(
            reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)), kExecutableSha256);
    if (ck3_11906::TrySubmitMainThreadQueryV1(mailbox,
        &ExecutePlayerFactionAlertsMailbox12004, &query.envelope,
        query.envelope.ticket) != ck3_11906::MainThreadQuerySubmitResultV1::submitted) {
      failure = "application-main faction query unavailable"; return false;
    }
    auto wait = ck3_11906::WaitForMainThreadQueryV1(mailbox, query.envelope.ticket, 8'000);
    while (wait == ck3_11906::MainThreadQueryWaitResultV1::timeout_executor_already_running)
      wait = ck3_11906::WaitForMainThreadQueryV1(mailbox, query.envelope.ticket, 2'000);
    const auto reclaimed = ck3_11906::ReclaimMainThreadQueryV1(mailbox, query.envelope.ticket);
    if (wait != ck3_11906::MainThreadQueryWaitResultV1::completed ||
        reclaimed != ck3_11906::MainThreadQueryReclaimResultV1::reclaimed ||
        !query.envelope.frame_stable || !query.completed) {
      failure = "application-main faction query did not complete"; return false;
    }
    serialized = ck3_12004::SerializePlayerFactionAlertsWhole12004(
        query.result, query.envelope.ticket.sequence, request_id, adapter.descriptor());
    return true;
  } catch (...) { failure = "application-main faction query failed"; return false; }
}
} // namespace xar::ck3_12004
