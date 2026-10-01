#include "xar_bridge/religion_doctrine12002_choices_mailbox.hpp"

#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINE_KNOWLEDGE_PRIVATE_QUERY_V1)
#include "xar_bridge/ck3_12002_semantic_adapter.hpp"
#include "xar_bridge/protocol.hpp"

#include <windows.h>

namespace xar::ck3_12002 {
namespace {
std::string Quote(std::string_view value) {
  std::string out = "\"";
  constexpr char hex[] = "0123456789abcdef";
  for (const unsigned char byte : value) {
    if (byte == '"' || byte == '\\') { out += '\\'; out += static_cast<char>(byte); }
    else if (byte < 32) { out += "\\u00"; out += hex[byte >> 4]; out += hex[byte & 15]; }
    else out += static_cast<char>(byte);
  }
  return out + '"';
}
bool HasField(std::string_view payload, std::string_view field) {
  return payload.find('"' + std::string(field) + '"') != std::string_view::npos;
}
bool ValidFrame(const game::Snapshot &frame, std::uint64_t revision) noexcept {
  return revision != 0 && frame.paused && frame.map_ready && frame.has_played_character &&
      frame.played_character_alive && frame.played_character_id > 0;
}
} // namespace

bool IsPlayerReligionDoctrineKnowledgePrivateStep12002(std::string_view step) noexcept {
  return step == kPlayerReligionDoctrineKnowledgePrivateStep12002;
}

bool ParsePlayerReligionDoctrineKnowledgeRequest12002(std::string_view payload,
    std::uint64_t &revision, std::optional<std::string> &doctrine_key) noexcept {
  revision = 0; doctrine_key.reset();
  try {
    const bool canonical_present = HasField(payload, "expected_snapshot_revision");
    const bool alias_present = HasField(payload, "expected_revision");
    std::uint64_t alias = 0;
    if (canonical_present && (!bridge::JsonUnsignedField(payload, "expected_snapshot_revision", revision) || revision == 0))
      return false;
    if (alias_present && (!bridge::JsonUnsignedField(payload, "expected_revision", alias) || alias == 0)) return false;
    if (canonical_present && alias_present && revision != alias) return false;
    if (!canonical_present) revision = alias;
    if (HasField(payload, "doctrine_key")) {
      std::string key;
      if (!bridge::JsonStringField(payload, "doctrine_key", key,
          bridge::kMaximumControlStringBytes) || key.empty()) return false;
      doctrine_key = std::move(key);
    }
    return true;
  } catch (...) { revision = 0; doctrine_key.reset(); return false; }
}

bool ExecutePlayerReligionDoctrineKnowledgeMailbox12002(void *opaque,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *envelope = static_cast<QueryMailboxEnvelope *>(opaque);
  if (!envelope || !envelope->typed_context) return false;
  auto &query = *static_cast<PlayerReligionDoctrineKnowledgeMailboxContext12002 *>(envelope->typed_context);
  try {
    if (!EnterQueryMailbox(*envelope, stamp, &ExecutePlayerReligionDoctrineKnowledgeMailbox12002)) {
      query.failure = "player_religion_doctrine_knowledge_published_frame_changed"; return true;
    }
    const auto &frame = envelope->expected_snapshot;
    if (query.doctrine_key) {
      auto &out = query.lookup_observation;
      (void)religion::doctrine12002::ReadPlayedDoctrineKnowledgeByKey12002(
          query.bindings, *query.doctrine_key, stamp.pump_epoch, out);
      if (out.available && (out.played_character_id != frame.played_character_id || out.date_raw != frame.date_raw)) {
        out = {}; out.unavailable_reason = "state_changed"; out.capture_epoch = stamp.pump_epoch;
        out.requested_doctrine_key = *query.doctrine_key;
      }
      if (!out.available) {
        out.date_raw = static_cast<std::int32_t>(frame.date_raw);
        out.played_character_id = static_cast<std::int32_t>(frame.played_character_id);
      }
    } else {
      auto &out = query.learned_observation;
      (void)religion::doctrine12002::ReadPlayedDoctrineKnowledge12002(query.bindings, stamp.pump_epoch, out);
      if (out.available && (out.played_character_id != frame.played_character_id || out.date_raw != frame.date_raw)) {
        out = {}; out.unavailable_reason = "state_changed"; out.capture_epoch = stamp.pump_epoch;
      }
      if (!out.available) {
        out.date_raw = static_cast<std::int32_t>(frame.date_raw);
        out.played_character_id = static_cast<std::int32_t>(frame.played_character_id);
      }
    }
    query.completed = true;
    (void)FinishQueryMailbox(*envelope);
    return true;
  } catch (...) { query.failure = "player_religion_doctrine_knowledge_native_capture_exception"; return false; }
}

std::string SerializePlayerReligionDoctrineKnowledgeResult12002(
    const PlayerReligionDoctrineKnowledgeMailboxContext12002 &query, std::string_view request_id) {
  if (!query.completed || !query.envelope.frame_stable || !query.failure.empty()) return {};
  const auto &frame = query.envelope.expected_snapshot;
  const bool available = query.doctrine_key ? query.lookup_observation.available : query.learned_observation.available;
  const auto value = query.doctrine_key ?
      religion::doctrine12002::SerializePlayedDoctrineKnowledgeLookup12002(query.lookup_observation) :
      religion::doctrine12002::SerializePlayedDoctrineKnowledge12002(query.learned_observation);
  return "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":" + Quote(request_id) +
      ",\"ok\":true,\"result\":{\"step\":" + Quote(kPlayerReligionDoctrineKnowledgePrivateStep12002) +
      ",\"accepted\":true,\"status\":" + Quote(available ? "observed" : "unavailable") +
      ",\"private_build\":true,\"read_only\":true,\"advertised\":false,\"game_version\":\"1.20.0.2\","
      "\"executable_sha256\":" + Quote(kExecutableSha256) +
      ",\"domain_key\":" + Quote(kPlayerReligionDoctrineKnowledgeDomainKey12002) +
      ",\"backend_id\":" + Quote(kPlayerReligionDoctrineKnowledgeBackend12002) +
      ",\"snapshot_revision\":" + std::to_string(query.envelope.expected_snapshot_revision) +
      ",\"date_raw\":" + std::to_string(frame.date_raw) +
      ",\"query_mode\":" + Quote(query.doctrine_key ? "by_key" : "learned_rows") +
      ",\"player_religion_doctrine_knowledge\":" + value + "}}";
}

bool RunPlayerReligionDoctrineKnowledgeMailbox12002(
    PlayerReligionDoctrineKnowledgeMailboxContext12002 &query, std::string_view request_id,
    std::string &serialized, std::string &failure) noexcept {
  using namespace ck3_11906;
  serialized.clear(); failure.clear();
  try {
    auto &envelope = query.envelope;
    if (!envelope.game || !envelope.mailbox || !ValidFrame(envelope.expected_snapshot, envelope.expected_snapshot_revision)) {
      failure = "player_religion_doctrine_knowledge_current_frame_unavailable"; return false;
    }
    envelope.typed_context = &query;
    if (TrySubmitMainThreadQueryV1(*envelope.mailbox, &ExecutePlayerReligionDoctrineKnowledgeMailbox12002,
        &envelope, envelope.ticket) != MainThreadQuerySubmitResultV1::submitted) {
      failure = "player_religion_doctrine_knowledge_mailbox_submit_unavailable"; return false;
    }
    auto wait = WaitForMainThreadQueryV1(*envelope.mailbox, envelope.ticket, 5000);
    while (wait == MainThreadQueryWaitResultV1::timeout_executor_already_running)
      wait = WaitForMainThreadQueryV1(*envelope.mailbox, envelope.ticket, 100);
    const auto reclaim = ReclaimMainThreadQueryV1(*envelope.mailbox, envelope.ticket);
    if (wait != MainThreadQueryWaitResultV1::completed || reclaim != MainThreadQueryReclaimResultV1::reclaimed ||
        !query.completed || !envelope.frame_stable) {
      failure = query.failure.empty() ? "player_religion_doctrine_knowledge_paused_capture_unavailable" : query.failure;
      return false;
    }
    serialized = SerializePlayerReligionDoctrineKnowledgeResult12002(query, request_id);
    if (!serialized.empty()) return true;
    failure = query.failure.empty() ? "player_religion_doctrine_knowledge_serialization_unavailable" : query.failure;
    return false;
  } catch (...) { serialized.clear(); failure = "player_religion_doctrine_knowledge_mailbox_exception"; return false; }
}

bool HandlePlayerReligionDoctrineKnowledgePrivate12002(const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox, const game::Snapshot &published,
    std::uint64_t revision, std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized, std::string &failure) noexcept {
  serialized.clear(); failure.clear();
  if (!IsPlayerReligionDoctrineKnowledgePrivateStep12002(step)) {
    failure = "player_religion_doctrine_knowledge_step_unavailable"; return false;
  }
  std::uint64_t expected = 0;
  std::optional<std::string> key;
  if (!ParsePlayerReligionDoctrineKnowledgeRequest12002(payload, expected, key)) {
    failure = "player_religion_doctrine_knowledge_request_invalid"; return false;
  }
  if (!adapter.enabled() || adapter.descriptor().game_version != "1.20.0.2" ||
      adapter.descriptor().executable_sha256 != kExecutableSha256 || !ValidFrame(published, revision) ||
      (expected != 0 && expected != revision)) {
    failure = "player_religion_doctrine_knowledge_current_frame_unavailable"; return false;
  }
  try {
    PlayerReligionDoctrineKnowledgeMailboxContext12002 query{};
    query.envelope.game = &NativeAdapter12002(adapter); query.envelope.mailbox = &mailbox;
    query.envelope.expected_snapshot = published; query.envelope.expected_snapshot_revision = revision;
    query.bindings = religion::doctrine12002::BindDoctrineKnowledgeImage12002(
        reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)), adapter.descriptor().executable_sha256);
    query.doctrine_key = std::move(key);
    return RunPlayerReligionDoctrineKnowledgeMailbox12002(query, request_id, serialized, failure);
  } catch (...) { failure = "player_religion_doctrine_knowledge_handler_exception"; return false; }
}
} // namespace xar::ck3_12002
#endif
