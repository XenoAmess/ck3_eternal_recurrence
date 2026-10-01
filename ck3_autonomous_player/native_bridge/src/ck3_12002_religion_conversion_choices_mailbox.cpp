#include "xar_bridge/ck3_12003_adapter.hpp"
#include "xar_bridge/ck3_12002_religion_conversion_choices_mailbox.hpp"

#if defined(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
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
bool HasField(std::string_view payload, std::string_view name) {
  return payload.find('"' + std::string(name) + '"') != std::string_view::npos;
}
bool ValidFrame(const game::Snapshot &frame, std::uint64_t revision) noexcept {
  return revision != 0 && frame.paused && frame.map_ready &&
      frame.has_played_character && frame.played_character_alive &&
      frame.played_character_id > 0;
}
std::string SerializeObservation(const PlayerReligionConversionChoicesSnapshot12002 &out) {
  return "{\"schema\":\"ck3_12002_religion_conversion_choices_v1\","
      "\"game_version\":\"1.20.0.2\",\"executable_sha256\":" + Quote(kExecutableSha256) +
      ",\"read_only\":true,\"available\":" + (out.available ? "true" : "false") +
      ",\"unavailable_reason\":" + (out.available ? "null" : Quote(out.unavailable_reason)) +
      ",\"capture_epoch\":" + std::to_string(out.capture_epoch) +
      ",\"date_raw\":" + std::to_string(out.date_raw) +
      ",\"played_character_id\":" + std::to_string(out.played_character_id) +
      ",\"faith_choices\":" + religion_conversion::faith::SerializePlayedFaithConversionChoices12002(out.faith_choices) +
      ",\"current_faith_rites\":" + religion_conversion_rite::SerializeCurrentFaithRites12002(out.current_faith_rites) +
      ",\"membership_is_legality\":false}";
}
} // namespace

bool IsPlayerReligionConversionChoicesPrivateStep12002(std::string_view step) noexcept {
  return step == kPlayerReligionConversionChoicesPrivateStep12002;
}
bool ParsePlayerReligionConversionChoicesRequest12002(std::string_view payload,
    std::uint64_t &revision) noexcept {
  revision = 0;
  try {
    // This API only queries the current played actor; there is no target override.
    for (const auto field : {"actor_id", "played_character_id", "target_faith_id", "target_rite_id"})
      if (HasField(payload, field)) return false;
    std::uint64_t alias = 0;
    const bool canonical_present = HasField(payload, "expected_snapshot_revision");
    const bool alias_present = HasField(payload, "expected_revision");
    if (canonical_present && (!bridge::JsonUnsignedField(payload,
        "expected_snapshot_revision", revision) || revision == 0)) return false;
    if (alias_present && (!bridge::JsonUnsignedField(payload,
        "expected_revision", alias) || alias == 0)) return false;
    if (canonical_present && alias_present && revision != alias) return false;
    if (!canonical_present) revision = alias;
    return true;
  } catch (...) { revision = 0; return false; }
}
bool ExecutePlayerReligionConversionChoicesMailbox12002(
    void *opaque, const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *envelope = static_cast<QueryMailboxEnvelope *>(opaque);
  if (!envelope || !envelope->typed_context) return false;
  auto &query = *static_cast<PlayerReligionConversionChoicesMailboxContext12002 *>(envelope->typed_context);
  try {
    if (!EnterQueryMailbox(*envelope, stamp, &ExecutePlayerReligionConversionChoicesMailbox12002)) {
      query.failure = "player_religion_conversion_choices_published_frame_changed";
      return true;
    }
    auto &out = query.observation;
    out = {}; out.capture_epoch = stamp.pump_epoch;
    const auto &frame = envelope->expected_snapshot;
    out.date_raw = static_cast<std::int32_t>(frame.date_raw);
    out.played_character_id = static_cast<std::int32_t>(frame.played_character_id);
    const bool faith_ok = religion_conversion::faith::ReadPlayedFaithConversionChoices12002(
        query.faith_bindings, stamp.pump_epoch, out.faith_choices);
    const bool rites_ok = religion_conversion_rite::ReadCurrentFaithRites12002(
        query.rite_bindings, stamp.pump_epoch, out.current_faith_rites);
    auto &faith = out.faith_choices;
    auto &rites = out.current_faith_rites;
    const bool matches = (!faith_ok || (faith.played_character_id == frame.played_character_id &&
        faith.date_raw == frame.date_raw)) && (!rites_ok ||
        (rites.played_character_id == frame.played_character_id && rites.date_raw == frame.date_raw)) &&
        (!faith_ok || !rites_ok || faith.current_faith_id == rites.faith_id);
    if (!matches) {
      faith = {}; faith.capture_epoch = stamp.pump_epoch; faith.unavailable_reason = "state_changed";
      rites = {}; rites.capture_epoch = stamp.pump_epoch;
      rites.failure = religion_conversion_rite::Failure::state_changed;
      out.unavailable_reason = "state_changed";
    } else if (!faith_ok) out.unavailable_reason = "faith_choices_unavailable";
    else if (!rites_ok) out.unavailable_reason = "current_faith_rites_unavailable";
    else { out.available = true; out.unavailable_reason.clear(); }
    if (!faith.available) {
      faith.date_raw = out.date_raw; faith.played_character_id = out.played_character_id;
    }
    if (!rites.available) {
      rites.date_raw = out.date_raw; rites.played_character_id = out.played_character_id;
    }
    query.completed = true;
    (void)FinishQueryMailbox(*envelope);
    return true;
  } catch (...) {
    query.failure = "player_religion_conversion_choices_native_capture_exception";
    return false;
  }
}
std::string SerializePlayerReligionConversionChoicesResult12002(
    const PlayerReligionConversionChoicesMailboxContext12002 &query, std::string_view request_id) {
  if (!query.completed || !query.envelope.frame_stable || !query.failure.empty()) return {};
  const auto &frame = query.envelope.expected_snapshot;
  return "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":" + Quote(request_id) +
      ",\"ok\":true,\"result\":{\"step\":" + Quote(kPlayerReligionConversionChoicesPrivateStep12002) +
      ",\"accepted\":true,\"status\":" + Quote(query.observation.available ? "observed" : "unavailable") +
      ",\"private_build\":true,\"read_only\":true,\"advertised\":false,\"game_version\":\"1.20.0.2\","
      "\"executable_sha256\":" + Quote(kExecutableSha256) +
      ",\"domain_key\":" + Quote(kPlayerReligionConversionChoicesDomainKey12002) +
      ",\"backend_id\":" + Quote(kPlayerReligionConversionChoicesBackend12002) +
      ",\"snapshot_revision\":" + std::to_string(query.envelope.expected_snapshot_revision) +
      ",\"date_raw\":" + std::to_string(frame.date_raw) +
      ",\"player_religion_conversion_choices\":" + SerializeObservation(query.observation) + "}}";
}
bool RunPlayerReligionConversionChoicesMailbox12002(PlayerReligionConversionChoicesMailboxContext12002 &query,
    std::string_view request_id, std::string &serialized, std::string &failure) noexcept {
  using namespace ck3_11906;
  serialized.clear(); failure.clear();
  try {
    auto &envelope = query.envelope;
    if (!envelope.game || !envelope.mailbox ||
        !ValidFrame(envelope.expected_snapshot, envelope.expected_snapshot_revision)) {
      failure = "player_religion_conversion_choices_current_frame_unavailable"; return false;
    }
    envelope.typed_context = &query;
    if (TrySubmitMainThreadQueryV1(*envelope.mailbox,
        &ExecutePlayerReligionConversionChoicesMailbox12002, &envelope, envelope.ticket) !=
        MainThreadQuerySubmitResultV1::submitted) {
      failure = "player_religion_conversion_choices_mailbox_submit_unavailable"; return false;
    }
    auto wait = WaitForMainThreadQueryV1(*envelope.mailbox, envelope.ticket, 5000);
    while (wait == MainThreadQueryWaitResultV1::timeout_executor_already_running)
      wait = WaitForMainThreadQueryV1(*envelope.mailbox, envelope.ticket, 100);
    const auto reclaim = ReclaimMainThreadQueryV1(*envelope.mailbox, envelope.ticket);
    if (wait != MainThreadQueryWaitResultV1::completed ||
        reclaim != MainThreadQueryReclaimResultV1::reclaimed ||
        !query.completed || !envelope.frame_stable) {
      failure = query.failure.empty() ? "player_religion_conversion_choices_paused_capture_unavailable" : query.failure;
      return false;
    }
    serialized = SerializePlayerReligionConversionChoicesResult12002(query, request_id);
    if (!serialized.empty()) return true;
    failure = query.failure.empty() ? "player_religion_conversion_choices_serialization_unavailable" : query.failure;
    return false;
  } catch (...) {
    serialized.clear(); failure = "player_religion_conversion_choices_mailbox_exception"; return false;
  }
}
bool HandlePlayerReligionConversionChoicesPrivate12002(const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox, const game::Snapshot &published,
    std::uint64_t revision, std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized, std::string &failure) noexcept {
  serialized.clear(); failure.clear();
  if (!IsPlayerReligionConversionChoicesPrivateStep12002(step)) {
    failure = "player_religion_conversion_choices_step_unavailable"; return false;
  }
  std::uint64_t expected = 0;
  if (!ParsePlayerReligionConversionChoicesRequest12002(payload, expected)) {
    failure = "player_religion_conversion_choices_request_invalid"; return false;
  }
  if (!adapter.enabled() || xar::game::ReviewedCrozierAbiVersion(adapter.descriptor()) != "1.20.0.2" ||
      xar::game::ReviewedCrozierAbiSha256(adapter.descriptor()) != kExecutableSha256 ||
      !ValidFrame(published, revision) || (expected != 0 && expected != revision)) {
    failure = "player_religion_conversion_choices_current_frame_unavailable"; return false;
  }
  try {
    PlayerReligionConversionChoicesMailboxContext12002 query{};
    query.envelope.game = &NativeAdapter12002(adapter);
    query.envelope.mailbox = &mailbox;
    query.envelope.expected_snapshot = published;
    query.envelope.expected_snapshot_revision = revision;
    const auto base = reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
    const auto sha = xar::game::ReviewedCrozierAbiSha256(adapter.descriptor());
    query.faith_bindings = religion_conversion::faith::BindFaithConversionImage12002(base, sha);
    query.rite_bindings = religion_conversion_rite::BindRiteConversionImage12002(base, sha);
    return RunPlayerReligionConversionChoicesMailbox12002(query, request_id, serialized, failure);
  } catch (...) { failure = "player_religion_conversion_choices_handler_exception"; return false; }
}
} // namespace xar::ck3_12002
#endif
