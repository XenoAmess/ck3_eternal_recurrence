#include "xar_bridge/ck3_12003_adapter.hpp"
#include "xar_bridge/religion_doctrine12002_numeric_mailbox.hpp"

#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_NUMERIC_SPECIAL_PARAMETERS_PRIVATE_QUERY_V1)
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12004_religion_parameter_bindings.hpp"
#include "xar_bridge/ck3_12002_semantic_adapter.hpp"
#include "xar_bridge/protocol.hpp"

#include <windows.h>
#include <utility>

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

bool IsPlayerReligionNumericSpecialParametersPrivateStep12002(std::string_view step) noexcept {
  return step == kPlayerReligionNumericSpecialParametersPrivateStep12002;
}

bool ParsePlayerReligionNumericSpecialParametersRevision12002(std::string_view payload,
                                     std::uint64_t &revision) noexcept {
  revision = 0;
  try {
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

bool ExecutePlayerReligionNumericSpecialParametersMailbox12002(
    void *opaque, const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *envelope = static_cast<QueryMailboxEnvelope *>(opaque);
  if (!envelope || !envelope->typed_context) return false;
  auto &query = *static_cast<PlayerReligionNumericSpecialParametersMailboxContext12002 *>(envelope->typed_context);
  try {
    if (!EnterQueryMailbox(*envelope, stamp, &ExecutePlayerReligionNumericSpecialParametersMailbox12002)) {
      query.failure = "player_religion_numeric_special_parameters_published_frame_changed";
      return true;
    }
    const bool actual4 = game::IsCk3_12004Descriptor(envelope->game->descriptor());
    if (actual4)
      (void)ck3_12004::religion::ReadPlayedNumericSpecialParameters12004(
          query.bindings, query.numeric_bindings, stamp.pump_epoch, query.observation);
    else
      (void)religion::doctrine12002::ReadPlayedNumericSpecialParameters12002(
          query.bindings, query.numeric_bindings, stamp.pump_epoch, query.observation);
    auto &out = query.observation;
    const auto &frame = envelope->expected_snapshot;
    if (out.available && (out.played_character_id != static_cast<std::uint32_t>(frame.played_character_id) ||
                          out.date_raw != frame.date_raw)) {
      out = {};
      out.failure = "state_changed";
      out.capture_epoch = stamp.pump_epoch;
    }
    if (!out.available) {
      // The owner envelope still identifies the frame whose native read failed.
      out.date_raw = static_cast<std::int32_t>(frame.date_raw);
      out.played_character_id = static_cast<std::uint32_t>(frame.played_character_id);
    }
    if (actual4)
      (void)ck3_12004::religion::ReadPlayedFaithNumericFinal12004(
          query.bindings, query.numeric_bindings, query.final_bindings,
          stamp.pump_epoch, query.final_observation);
    else
      (void)religion::doctrine12002::ReadPlayedFaithNumericFinal12002(
          query.bindings, query.numeric_bindings, query.final_bindings,
          stamp.pump_epoch, query.final_observation);
    auto &final = query.final_observation;
    const auto current_id = out.current_rite
        ? std::optional<std::uint32_t>(out.current_rite->rite_id) : std::nullopt;
    const auto main_id = out.faith_main_rite
        ? std::optional<std::uint32_t>(out.faith_main_rite->rite_id) : std::nullopt;
    if (final.available &&
        (final.played_character_id != static_cast<std::uint32_t>(frame.played_character_id) ||
         final.date_raw != frame.date_raw ||
         (out.available && (final.capture_epoch != out.capture_epoch ||
                            final.current_rite_id != current_id ||
                            final.faith_id != out.faith_id || final.main_rite_id != main_id)))) {
      final = {};
      final.failure = "state_changed";
      final.capture_epoch = stamp.pump_epoch;
    }
    if (!final.available) {
      final.date_raw = static_cast<std::int32_t>(frame.date_raw);
      final.played_character_id = static_cast<std::uint32_t>(frame.played_character_id);
    }
    query.completed = true;
    (void)FinishQueryMailbox(*envelope);
    return true;
  } catch (...) {
    query.failure = "player_religion_numeric_special_parameters_native_capture_exception";
    return false;
  }
}

std::string SerializePlayerReligionNumericSpecialParametersResult12002(
    const PlayerReligionNumericSpecialParametersMailboxContext12002 &query, std::string_view request_id) {
  if (!query.completed || !query.envelope.frame_stable || !query.failure.empty()) return {};
  const auto &frame = query.envelope.expected_snapshot;
  const auto final_serialized = query.envelope.game &&
      game::IsCk3_12004Descriptor(query.envelope.game->descriptor())
      ? ck3_12004::religion::SerializeFaithNumericFinal12004(query.final_observation)
      : religion::doctrine12002::SerializeFaithNumericFinal12002(query.final_observation);
  return "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":" + Quote(request_id) +
      ",\"ok\":true,\"result\":{\"step\":" + Quote(kPlayerReligionNumericSpecialParametersPrivateStep12002) +
      ",\"accepted\":true,\"status\":" + Quote(query.observation.available ? "observed" : "unavailable") +
      ",\"private_build\":true,\"read_only\":true,\"advertised\":false,\"game_version\":\"1.20.0.2\","
      "\"executable_sha256\":" + Quote(kExecutableSha256) +
      ",\"domain_key\":" + Quote(kPlayerReligionNumericSpecialParametersDomainKey12002) +
      ",\"backend_id\":" + Quote(kPlayerReligionNumericSpecialParametersBackend12002) +
      ",\"snapshot_revision\":" + std::to_string(query.envelope.expected_snapshot_revision) +
      ",\"date_raw\":" + std::to_string(frame.date_raw) +
      ",\"player_religion_numeric_special_parameters\":" +
          religion::doctrine12002::SerializeNumericSpecialParameters12002(query.observation) +
      ",\"faith_numeric_final\":" +
          final_serialized + "}}";
}

bool RunPlayerReligionNumericSpecialParametersMailbox12002(PlayerReligionNumericSpecialParametersMailboxContext12002 &query,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept {
  using namespace ck3_11906;
  serialized.clear(); failure.clear();
  try {
    auto &envelope = query.envelope;
    if (!envelope.game || !envelope.mailbox ||
        !ValidFrame(envelope.expected_snapshot, envelope.expected_snapshot_revision)) {
      failure = "player_religion_numeric_special_parameters_current_frame_unavailable"; return false;
    }
    envelope.typed_context = &query;
    if (TrySubmitMainThreadQueryV1(*envelope.mailbox,
        &ExecutePlayerReligionNumericSpecialParametersMailbox12002, &envelope, envelope.ticket) !=
        MainThreadQuerySubmitResultV1::submitted) {
      failure = "player_religion_numeric_special_parameters_mailbox_submit_unavailable"; return false;
    }
    auto wait = WaitForMainThreadQueryV1(*envelope.mailbox, envelope.ticket, 5000);
    while (wait == MainThreadQueryWaitResultV1::timeout_executor_already_running)
      wait = WaitForMainThreadQueryV1(*envelope.mailbox, envelope.ticket, 100);
    const auto reclaim = ReclaimMainThreadQueryV1(*envelope.mailbox, envelope.ticket);
    if (wait != MainThreadQueryWaitResultV1::completed ||
        reclaim != MainThreadQueryReclaimResultV1::reclaimed ||
        !query.completed || !envelope.frame_stable) {
      failure = query.failure.empty() ? "player_religion_numeric_special_parameters_paused_capture_unavailable" : query.failure;
      return false;
    }
    serialized = SerializePlayerReligionNumericSpecialParametersResult12002(query, request_id);
    if (game::IsCk3_12004Descriptor(envelope.game->descriptor()))
      serialized = game::Render12004BuildIdentity(
          std::move(serialized), envelope.game->descriptor());
    if (!serialized.empty()) return true;
    failure = query.failure.empty() ? "player_religion_numeric_special_parameters_serialization_unavailable" : query.failure;
    return false;
  } catch (...) {
    serialized.clear(); failure = "player_religion_numeric_special_parameters_mailbox_exception"; return false;
  }
}

bool HandlePlayerReligionNumericSpecialParametersPrivate12002(const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox, const game::Snapshot &published,
    std::uint64_t revision, std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept {
  serialized.clear(); failure.clear();
  if (!IsPlayerReligionNumericSpecialParametersPrivateStep12002(step)) {
    failure = "player_religion_numeric_special_parameters_step_unavailable"; return false;
  }
  std::uint64_t expected = 0;
  if (!ParsePlayerReligionNumericSpecialParametersRevision12002(payload, expected)) {
    failure = "player_religion_numeric_special_parameters_request_invalid"; return false;
  }
  const bool actual4 = game::IsCk3_12004Descriptor(adapter.descriptor());
  if (!adapter.enabled() || (!actual4 &&
      (game::ReviewedCrozierAbiVersion(adapter.descriptor()) != "1.20.0.2" ||
       game::ReviewedCrozierAbiSha256(adapter.descriptor()) != kExecutableSha256)) ||
      !ValidFrame(published, revision) || (expected != 0 && expected != revision)) {
    failure = "player_religion_numeric_special_parameters_current_frame_unavailable"; return false;
  }
  try {
    PlayerReligionNumericSpecialParametersMailboxContext12002 query{};
    query.envelope.game = actual4 ? &adapter : &NativeAdapter12002(adapter);
    query.envelope.mailbox = &mailbox;
    query.envelope.expected_snapshot = published;
    query.envelope.expected_snapshot_revision = revision;
    const auto base = reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
    if (actual4) {
      const auto sha = adapter.descriptor().executable_sha256;
      query.bindings = ck3_12004::religion::BindReligionContextImage12004(base, sha);
      query.numeric_bindings = ck3_12004::religion::BindNumericSpecialParametersImage12004(base, sha);
      query.final_bindings = ck3_12004::religion::BindFaithNumericFinalImage12004(base, sha);
    } else {
      const auto sha = game::ReviewedCrozierAbiSha256(adapter.descriptor());
      query.bindings = religion::BindReligionContextImage12002(base, sha);
      query.numeric_bindings = religion::doctrine12002::BindNumericSpecialParameters12002(base, sha);
      query.final_bindings = religion::doctrine12002::BindFaithNumericFinal12002(base, sha);
    }
    return RunPlayerReligionNumericSpecialParametersMailbox12002(query, request_id, serialized, failure);
  } catch (...) { failure = "player_religion_numeric_special_parameters_handler_exception"; return false; }
}
} // namespace xar::ck3_12002
#endif
