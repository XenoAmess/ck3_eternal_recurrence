#include "xar_bridge/ck3_12002_epidemic_treatment_mailbox.hpp"

#if defined(XAR_CK3_ENABLE_G2_PLAYER_EPIDEMIC_TREATMENT_PRIVATE_QUERY_V1)
#include "xar_bridge/ck3_12002_semantic_adapter.hpp"
#include "xar_bridge/protocol.hpp"

#include <windows.h>

namespace xar::ck3_12002 {
namespace {
std::string Quote(std::string_view text) {
  static constexpr char hex[] = "0123456789abcdef";
  std::string out = "\"";
  for (const unsigned char byte : text) {
    if (byte == '"' || byte == '\\') { out += '\\'; out += static_cast<char>(byte); }
    else if (byte < 0x20) { out += "\\u00"; out += hex[byte >> 4]; out += hex[byte & 15]; }
    else out += static_cast<char>(byte);
  }
  return out + '"';
}
bool ValidFrame(const game::Snapshot &frame, std::uint64_t revision) noexcept {
  return revision != 0 && frame.paused && frame.map_ready &&
      frame.has_played_character && frame.played_character_alive &&
      frame.played_character_id > 0;
}
std::string SerializeResult(const PlayerEpidemicTreatmentMailboxContext12002 &query,
                            std::string_view request_id) {
  if (!query.completed || !query.envelope.frame_stable || !query.failure.empty()) return {};
  const auto payload = ck3_11906::SerializePlayerEpidemicTreatmentPresenceV1(query.observation);
  if (payload.empty()) return {};
  return "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":" + Quote(request_id) +
      ",\"ok\":true,\"result\":{\"step\":" + Quote(kPlayerEpidemicTreatmentPrivateStep12002) +
      ",\"accepted\":true,\"status\":" + Quote(query.observation.available ? "available" : "unavailable") +
      ",\"query_sequence\":" + std::to_string(query.envelope.ticket.sequence) +
      ",\"observation_revision\":" + std::to_string(query.envelope.execution_stamp.pump_epoch) +
      ",\"snapshot_revision\":" + std::to_string(query.envelope.expected_snapshot_revision) +
      ",\"player_epidemic_treatment_presence\":" + payload +
      ",\"private_build\":true,\"read_only\":true,\"advertised\":false,\"backend_id\":\"native-headless\"}}";
}
bool Run(PlayerEpidemicTreatmentMailboxContext12002 &query,
         std::string_view request_id, std::string &serialized, std::string &failure) {
  using namespace ck3_11906;
  auto &envelope = query.envelope;
  if (envelope.mailbox->permitted_executor_epidemic_treatment12002 !=
      &ExecutePlayerEpidemicTreatmentMailbox12002) {
    failure = "player_epidemic_treatment_mailbox_submit_unavailable"; return false;
  }
  envelope.typed_context = &query;
  if (TrySubmitMainThreadQueryV1(*envelope.mailbox,
      &ExecutePlayerEpidemicTreatmentMailbox12002, &envelope, envelope.ticket) !=
      MainThreadQuerySubmitResultV1::submitted) {
    failure = "player_epidemic_treatment_mailbox_submit_unavailable"; return false;
  }
  auto wait = WaitForMainThreadQueryV1(*envelope.mailbox, envelope.ticket, 5000);
  while (wait == MainThreadQueryWaitResultV1::timeout_executor_already_running)
    wait = WaitForMainThreadQueryV1(*envelope.mailbox, envelope.ticket, 100);
  const auto reclaim = ReclaimMainThreadQueryV1(*envelope.mailbox, envelope.ticket);
  if (wait != MainThreadQueryWaitResultV1::completed ||
      reclaim != MainThreadQueryReclaimResultV1::reclaimed ||
      !query.completed || !envelope.frame_stable) {
    failure = query.failure.empty() ? "player_epidemic_treatment_paused_capture_unavailable" : query.failure;
    return false;
  }
  serialized = SerializeResult(query, request_id);
  if (!serialized.empty()) return true;
  failure = "player_epidemic_treatment_serialization_unavailable"; return false;
}
} // namespace

bool IsPlayerEpidemicTreatmentPrivateStep12002(std::string_view step) noexcept {
  return step == kPlayerEpidemicTreatmentPrivateStep12002;
}

bool ExecutePlayerEpidemicTreatmentMailbox12002(
    void *opaque, const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *envelope = static_cast<QueryMailboxEnvelope *>(opaque);
  if (!envelope || !envelope->typed_context) return false;
  auto &query = *static_cast<PlayerEpidemicTreatmentMailboxContext12002 *>(envelope->typed_context);
  try {
    if (!EnterQueryMailbox(*envelope, stamp, &ExecutePlayerEpidemicTreatmentMailbox12002)) {
      query.failure = "player_epidemic_treatment_published_frame_changed"; return true;
    }
    const auto &frame = envelope->expected_snapshot;
    query.observation = ReadPlayerEpidemicTreatmentPresence12002(query.bindings,
        envelope->expected_snapshot_revision, static_cast<std::int32_t>(frame.date_raw),
        static_cast<std::int32_t>(frame.played_character_id));
    query.completed = true;
    (void)FinishQueryMailbox(*envelope);
    return true;
  } catch (...) {
    query.failure = "player_epidemic_treatment_native_capture_exception"; return false;
  }
}

bool HandlePlayerEpidemicTreatmentPrivate12002(const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox, const game::Snapshot &published,
    std::uint64_t revision, std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized, std::string &failure,
    const TreatmentPresenceBindings12002 *fixture_bindings) noexcept {
  serialized.clear(); failure.clear();
  if (!IsPlayerEpidemicTreatmentPrivateStep12002(step)) {
    failure = "player_epidemic_treatment_step_unavailable"; return false;
  }
  std::uint64_t expected = 0;
  if (!bridge::JsonUnsignedField(payload, "expected_revision", expected) || expected == 0) {
    failure = "player_epidemic_treatment_request_invalid"; return false;
  }
  if (!adapter.enabled() || adapter.descriptor().game_version != "1.20.0.2" ||
      adapter.descriptor().executable_sha256 != kExecutableSha256 ||
      !ValidFrame(published, revision) || expected != revision ||
      (fixture_bindings && !mailbox.offline_fixture)) {
    failure = "player_epidemic_treatment_current_frame_unavailable"; return false;
  }
  try {
    PlayerEpidemicTreatmentMailboxContext12002 query{};
    query.envelope.game = &NativeAdapter12002(adapter);
    query.envelope.mailbox = &mailbox;
    query.envelope.expected_snapshot = published;
    query.envelope.expected_snapshot_revision = revision;
    query.bindings = fixture_bindings ? *fixture_bindings : BindTreatmentPresenceImage12002(
        reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)),
        adapter.descriptor().executable_sha256);
    return Run(query, request_id, serialized, failure);
  } catch (...) {
    serialized.clear(); failure = "player_epidemic_treatment_handler_exception"; return false;
  }
}
} // namespace xar::ck3_12002
#endif
