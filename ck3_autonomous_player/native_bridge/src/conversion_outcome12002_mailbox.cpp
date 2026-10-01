#include "xar_bridge/conversion_outcome12002_mailbox.hpp"

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
} // namespace

bool IsPlayerReligionConversionOutcomePrivateStep12002(std::string_view step) noexcept {
  return step == kPlayerReligionConversionOutcomePrivateStep12002;
}

bool ParsePlayerReligionConversionOutcomeRequest12002(std::string_view payload,
                                     std::uint32_t &target_rite_id,
                                     std::uint64_t &revision) noexcept {
  revision = 0; target_rite_id = religion::kAbsentReference;
  if (HasField(payload, "actor_id") || HasField(payload, "played_character_id") ||
      HasField(payload, "target_faith_id")) return false;
  try {
    std::uint64_t raw_target = 0;
    if (!bridge::JsonUnsignedField(payload, "target_rite_id", raw_target) ||
        raw_target >= religion::kAbsentReference) return false;
    target_rite_id = static_cast<std::uint32_t>(raw_target);
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

bool ExecutePlayerReligionConversionOutcomeMailbox12002(
    void *opaque, const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *envelope = static_cast<QueryMailboxEnvelope *>(opaque);
  if (!envelope || !envelope->typed_context) return false;
  auto &query = *static_cast<PlayerReligionConversionOutcomeMailboxContext12002 *>(envelope->typed_context);
  try {
    if (!EnterQueryMailbox(*envelope, stamp, &ExecutePlayerReligionConversionOutcomeMailbox12002)) {
      query.failure = "player_religion_conversion_outcome_published_frame_changed";
      return true;
    }
    (void)religion_conversion::outcome::ReadPlayedConversionOutcome12002(
        query.bindings, query.target_rite_id, stamp.pump_epoch, query.observation);
    auto &out = query.observation;
    const auto &frame = envelope->expected_snapshot;
    const auto matches = [&](bool available, std::int32_t date, std::int64_t actor) {
      return !available || (actor == frame.played_character_id && date == frame.date_raw);
    };
    if (!matches(out.actor.available, out.actor.date_raw, out.actor.played_character_id) ||
        !matches(out.state.available, out.state.date_raw, out.state.played_character_id)) {
      out = {};
      out.failure = religion_conversion::outcome::Failure::state_changed;
      out.capture_epoch = stamp.pump_epoch;
      out.target_rite_id = query.target_rite_id;
      out.actor.capture_epoch = out.state.capture_epoch = stamp.pump_epoch;
    }
    // The owner envelope supplies the actual published frame even when a
    // component has a typed native-read failure; failed values remain absent.
    out.date_raw = static_cast<std::int32_t>(frame.date_raw);
    out.played_character_id = static_cast<std::int32_t>(frame.played_character_id);
    if (!out.actor.available) {
      out.actor.date_raw = out.date_raw;
      out.actor.played_character_id = out.played_character_id;
      out.actor.current_religion.date_raw = out.date_raw;
      out.actor.current_religion.played_character_id = out.played_character_id;
      out.actor.current_religion.capture_epoch = stamp.pump_epoch;
    }
    if (!out.state.available) {
      out.state.date_raw = out.date_raw;
      out.state.played_character_id = static_cast<std::uint32_t>(out.played_character_id);
      out.state.requested_target_rite_id = query.target_rite_id;
    }
    query.completed = true;
    (void)FinishQueryMailbox(*envelope);
    return true;
  } catch (...) {
    query.failure = "player_religion_conversion_outcome_native_capture_exception";
    return false;
  }
}

std::string SerializePlayerReligionConversionOutcomeResult12002(
    const PlayerReligionConversionOutcomeMailboxContext12002 &query, std::string_view request_id) {
  if (!query.completed || !query.envelope.frame_stable || !query.failure.empty()) return {};
  const auto &frame = query.envelope.expected_snapshot;
  return "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":" + Quote(request_id) +
      ",\"ok\":true,\"result\":{\"step\":" + Quote(kPlayerReligionConversionOutcomePrivateStep12002) +
      ",\"accepted\":true,\"status\":" + Quote(query.observation.available ? "observed" : "unavailable") +
      ",\"private_build\":true,\"read_only\":true,\"advertised\":false,\"game_version\":\"1.20.0.2\","
      "\"executable_sha256\":" + Quote(kExecutableSha256) +
      ",\"domain_key\":" + Quote(kPlayerReligionConversionOutcomeDomainKey12002) +
      ",\"backend_id\":" + Quote(kPlayerReligionConversionOutcomeBackend12002) +
      ",\"snapshot_revision\":" + std::to_string(query.envelope.expected_snapshot_revision) +
      ",\"date_raw\":" + std::to_string(frame.date_raw) +
      ",\"player_religion_conversion_outcome\":" + religion_conversion::outcome::SerializeConversionOutcome12002(query.observation) + "}}";
}

bool RunPlayerReligionConversionOutcomeMailbox12002(PlayerReligionConversionOutcomeMailboxContext12002 &query,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept {
  using namespace ck3_11906;
  serialized.clear(); failure.clear();
  try {
    auto &envelope = query.envelope;
    if (!envelope.game || !envelope.mailbox ||
        !ValidFrame(envelope.expected_snapshot, envelope.expected_snapshot_revision)) {
      failure = "player_religion_conversion_outcome_current_frame_unavailable"; return false;
    }
    envelope.typed_context = &query;
    if (TrySubmitMainThreadQueryV1(*envelope.mailbox,
        &ExecutePlayerReligionConversionOutcomeMailbox12002, &envelope, envelope.ticket) !=
        MainThreadQuerySubmitResultV1::submitted) {
      failure = "player_religion_conversion_outcome_mailbox_submit_unavailable"; return false;
    }
    auto wait = WaitForMainThreadQueryV1(*envelope.mailbox, envelope.ticket, 5000);
    while (wait == MainThreadQueryWaitResultV1::timeout_executor_already_running)
      wait = WaitForMainThreadQueryV1(*envelope.mailbox, envelope.ticket, 100);
    const auto reclaim = ReclaimMainThreadQueryV1(*envelope.mailbox, envelope.ticket);
    if (wait != MainThreadQueryWaitResultV1::completed ||
        reclaim != MainThreadQueryReclaimResultV1::reclaimed ||
        !query.completed || !envelope.frame_stable) {
      failure = query.failure.empty() ? "player_religion_conversion_outcome_paused_capture_unavailable" : query.failure;
      return false;
    }
    serialized = SerializePlayerReligionConversionOutcomeResult12002(query, request_id);
    if (!serialized.empty()) return true;
    failure = query.failure.empty() ? "player_religion_conversion_outcome_serialization_unavailable" : query.failure;
    return false;
  } catch (...) {
    serialized.clear(); failure = "player_religion_conversion_outcome_mailbox_exception"; return false;
  }
}

bool HandlePlayerReligionConversionOutcomePrivate12002(const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox, const game::Snapshot &published,
    std::uint64_t revision, std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept {
  serialized.clear(); failure.clear();
  if (!IsPlayerReligionConversionOutcomePrivateStep12002(step)) {
    failure = "player_religion_conversion_outcome_step_unavailable"; return false;
  }
  std::uint64_t expected = 0;
  std::uint32_t target_rite_id = religion::kAbsentReference;
  if (!ParsePlayerReligionConversionOutcomeRequest12002(payload, target_rite_id, expected)) {
    failure = "player_religion_conversion_outcome_request_invalid"; return false;
  }
  if (!adapter.enabled() || adapter.descriptor().game_version != "1.20.0.2" ||
      adapter.descriptor().executable_sha256 != kExecutableSha256 ||
      !ValidFrame(published, revision) || (expected != 0 && expected != revision)) {
    failure = "player_religion_conversion_outcome_current_frame_unavailable"; return false;
  }
  try {
    PlayerReligionConversionOutcomeMailboxContext12002 query{};
    query.envelope.game = &NativeAdapter12002(adapter);
    query.envelope.mailbox = &mailbox;
    query.envelope.expected_snapshot = published;
    query.envelope.expected_snapshot_revision = revision;
    query.target_rite_id = target_rite_id;
    query.bindings = religion_conversion::outcome::BindConversionOutcomeImage12002(
        reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)),
        adapter.descriptor().executable_sha256);
    return RunPlayerReligionConversionOutcomeMailbox12002(query, request_id, serialized, failure);
  } catch (...) { failure = "player_religion_conversion_outcome_handler_exception"; return false; }
}
} // namespace xar::ck3_12002
#endif
