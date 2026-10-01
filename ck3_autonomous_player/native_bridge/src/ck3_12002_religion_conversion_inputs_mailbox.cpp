#include "xar_bridge/ck3_12002_religion_conversion_inputs_mailbox.hpp"

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
      frame.has_played_character && frame.played_character_alive && frame.played_character_id > 0;
}
} // namespace

bool IsPlayerReligionConversionInputsPrivateStep12002(std::string_view step) noexcept {
  return step == kPlayerReligionConversionInputsPrivateStep12002;
}
bool ParsePlayerReligionConversionInputsRequest12002(std::string_view payload,
    std::uint32_t &target_rite_id, std::uint64_t &revision) noexcept {
  revision = 0; target_rite_id = religion::kAbsentReference;
  try {
    std::uint64_t raw_target = 0;
    if (!bridge::JsonUnsignedField(payload, "target_rite_id", raw_target) ||
        raw_target >= religion::kAbsentReference) return false;
    target_rite_id = static_cast<std::uint32_t>(raw_target);
    std::uint64_t alias = 0;
    const bool canonical = HasField(payload, "expected_snapshot_revision");
    const bool alternate = HasField(payload, "expected_revision");
    if (canonical && (!bridge::JsonUnsignedField(payload, "expected_snapshot_revision", revision) || !revision)) return false;
    if (alternate && (!bridge::JsonUnsignedField(payload, "expected_revision", alias) || !alias)) return false;
    if (canonical && alternate && revision != alias) return false;
    if (!canonical) revision = alias;
    return true;
  } catch (...) { revision = 0; return false; }
}
bool ExecutePlayerReligionConversionInputsMailbox12002(void *opaque,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *envelope = static_cast<QueryMailboxEnvelope *>(opaque);
  if (!envelope || !envelope->typed_context) return false;
  auto &q = *static_cast<PlayerReligionConversionInputsMailboxContext12002 *>(envelope->typed_context);
  try {
    if (!EnterQueryMailbox(*envelope, stamp, &ExecutePlayerReligionConversionInputsMailbox12002)) {
      q.failure = "player_religion_conversion_inputs_published_frame_changed"; return true;
    }
    const auto &frame = envelope->expected_snapshot;
    auto &g = q.conversion_gates;
    auto &p = q.predicted_base_fulfillment;
    (void)religion::conversion_gates::ReadPlayedReligionConversionGates12002(
        q.gates_bindings, q.target_rite_id, stamp.pump_epoch, g);
    (void)religion_conversion_ai_inputs::ReadExpectedRiteFulfillment12002(
        q.prediction_bindings, stamp.pump_epoch, q.target_rite_id, p);
    const auto actor = static_cast<std::uint32_t>(frame.played_character_id);
    const bool gates_drift = g.available && (g.played_character_id != actor ||
        g.date_raw != frame.date_raw || g.capture_epoch != stamp.pump_epoch ||
        g.target_rite_id != q.target_rite_id);
    const bool prediction_drift = p.available && (static_cast<std::uint32_t>(p.played_character_id) != actor ||
        p.date_raw != frame.date_raw || p.capture_epoch != stamp.pump_epoch || p.target_rite_id != q.target_rite_id);
    if (gates_drift) { g = {}; g.failure = religion::conversion_gates::Failure::state_changed; }
    if (prediction_drift) { p = {}; p.failure = religion_conversion_ai_inputs::Failure::state_changed; }
    if (!g.available) {
      g.capture_epoch = stamp.pump_epoch; g.date_raw = static_cast<std::int32_t>(frame.date_raw);
      g.played_character_id = actor; g.requested_target_rite_id = q.target_rite_id;
    }
    if (!p.available) {
      p.capture_epoch = stamp.pump_epoch; p.date_raw = static_cast<std::int32_t>(frame.date_raw);
      p.played_character_id = frame.played_character_id; p.target_rite_id = q.target_rite_id;
    }
    q.available = g.available && p.available;
    if (gates_drift || prediction_drift) q.unavailable_reason = "conversion_inputs_state_changed";
    else if (!g.available) q.unavailable_reason = std::string("conversion_gates_") +
        religion::conversion_gates::ReligionConversionGatesFailureKey(g.failure);
    else if (!p.available) q.unavailable_reason = std::string("predicted_base_fulfillment_") +
        religion_conversion_ai_inputs::ConversionAIInputsFailureKey(p.failure);
    q.completed = true;
    (void)FinishQueryMailbox(*envelope);
    return true;
  } catch (...) { q.failure = "player_religion_conversion_inputs_native_capture_exception"; return false; }
}
std::string SerializePlayerReligionConversionInputsResult12002(
    const PlayerReligionConversionInputsMailboxContext12002 &q, std::string_view request_id) {
  if (!q.completed || !q.envelope.frame_stable || !q.failure.empty()) return {};
  const auto &frame = q.envelope.expected_snapshot;
  const auto dto = std::string("{\"schema\":\"ck3_12002_religion_conversion_inputs_v1\",\"available\":") +
      (q.available ? "true" : "false") + ",\"unavailable_reason\":" +
      (q.available ? "null" : Quote(q.unavailable_reason)) +
      ",\"capture_epoch\":" + std::to_string(q.envelope.execution_stamp.pump_epoch) +
      ",\"date_raw\":" + std::to_string(frame.date_raw) +
      ",\"played_character_id\":" + std::to_string(frame.played_character_id) +
      ",\"target_rite_id\":" + std::to_string(q.target_rite_id) +
      ",\"conversion_gates\":" + religion::conversion_gates::SerializePlayedReligionConversionGates12002(q.conversion_gates) +
      ",\"predicted_base_fulfillment\":" + religion_conversion_ai_inputs::SerializeExpectedRiteFulfillment12002(q.predicted_base_fulfillment) + "}";
  return "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":" + Quote(request_id) +
      ",\"ok\":true,\"result\":{\"step\":" + Quote(kPlayerReligionConversionInputsPrivateStep12002) +
      ",\"accepted\":true,\"status\":" + Quote(q.available ? "observed" : "unavailable") +
      ",\"private_build\":true,\"read_only\":true,\"advertised\":false,\"game_version\":\"1.20.0.2\","
      "\"executable_sha256\":" + Quote(kExecutableSha256) +
      ",\"domain_key\":" + Quote(kPlayerReligionConversionInputsDomainKey12002) +
      ",\"backend_id\":" + Quote(kPlayerReligionConversionInputsBackend12002) +
      ",\"snapshot_revision\":" + std::to_string(q.envelope.expected_snapshot_revision) +
      ",\"date_raw\":" + std::to_string(frame.date_raw) +
      ",\"player_religion_conversion_inputs\":" + dto + "}}";
}
bool RunPlayerReligionConversionInputsMailbox12002(PlayerReligionConversionInputsMailboxContext12002 &q,
    std::string_view request_id, std::string &serialized, std::string &failure) noexcept {
  using namespace ck3_11906;
  serialized.clear(); failure.clear();
  try {
    auto &e = q.envelope;
    if (!e.game || !e.mailbox || !ValidFrame(e.expected_snapshot, e.expected_snapshot_revision)) {
      failure = "player_religion_conversion_inputs_current_frame_unavailable"; return false;
    }
    e.typed_context = &q;
    if (TrySubmitMainThreadQueryV1(*e.mailbox, &ExecutePlayerReligionConversionInputsMailbox12002, &e, e.ticket) !=
        MainThreadQuerySubmitResultV1::submitted) {
      failure = "player_religion_conversion_inputs_mailbox_submit_unavailable"; return false;
    }
    auto wait = WaitForMainThreadQueryV1(*e.mailbox, e.ticket, 5000);
    while (wait == MainThreadQueryWaitResultV1::timeout_executor_already_running)
      wait = WaitForMainThreadQueryV1(*e.mailbox, e.ticket, 100);
    const auto reclaim = ReclaimMainThreadQueryV1(*e.mailbox, e.ticket);
    if (wait != MainThreadQueryWaitResultV1::completed || reclaim != MainThreadQueryReclaimResultV1::reclaimed ||
        !q.completed || !e.frame_stable) {
      failure = q.failure.empty() ? "player_religion_conversion_inputs_paused_capture_unavailable" : q.failure; return false;
    }
    serialized = SerializePlayerReligionConversionInputsResult12002(q, request_id);
    if (!serialized.empty()) return true;
    failure = q.failure.empty() ? "player_religion_conversion_inputs_serialization_unavailable" : q.failure; return false;
  } catch (...) { serialized.clear(); failure = "player_religion_conversion_inputs_mailbox_exception"; return false; }
}
bool HandlePlayerReligionConversionInputsPrivate12002(const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox, const game::Snapshot &published,
    std::uint64_t revision, std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized, std::string &failure) noexcept {
  serialized.clear(); failure.clear();
  if (!IsPlayerReligionConversionInputsPrivateStep12002(step)) {
    failure = "player_religion_conversion_inputs_step_unavailable"; return false;
  }
  std::uint32_t target = religion::kAbsentReference; std::uint64_t expected = 0;
  if (!ParsePlayerReligionConversionInputsRequest12002(payload, target, expected)) {
    failure = "player_religion_conversion_inputs_request_invalid"; return false;
  }
  if (!adapter.enabled() || adapter.descriptor().game_version != "1.20.0.2" ||
      adapter.descriptor().executable_sha256 != kExecutableSha256 ||
      !ValidFrame(published, revision) || (expected && expected != revision)) {
    failure = "player_religion_conversion_inputs_current_frame_unavailable"; return false;
  }
  try {
    PlayerReligionConversionInputsMailboxContext12002 q{};
    q.envelope.game = &NativeAdapter12002(adapter); q.envelope.mailbox = &mailbox;
    q.envelope.expected_snapshot = published; q.envelope.expected_snapshot_revision = revision;
    q.target_rite_id = target;
    const auto base = reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
    q.gates_bindings = religion::conversion_gates::BindReligionConversionGatesImage12002(base, adapter.descriptor().executable_sha256);
    q.prediction_bindings = religion_conversion_ai_inputs::BindConversionAIInputsImage12002(base, adapter.descriptor().executable_sha256);
    return RunPlayerReligionConversionInputsMailbox12002(q, request_id, serialized, failure);
  } catch (...) { failure = "player_religion_conversion_inputs_handler_exception"; return false; }
}
} // namespace xar::ck3_12002
#endif
