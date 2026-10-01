#include "xar_bridge/ck3_12003_adapter.hpp"
#include "xar_bridge/religion_rite_governance12002_clergy_mailbox.hpp"

#if defined(XAR_CK3_ENABLE_G2_PLAYER_CLERGY_APPOINTMENT_PRIVATE_QUERY_V1)
#include "xar_bridge/ck3_12002_semantic_adapter.hpp"
#include "xar_bridge/protocol.hpp"

#include <limits>
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

bool IsPlayerClergyAppointmentPrivateStep12002(std::string_view step) noexcept {
  return step == kPlayerClergyAppointmentPrivateStep12002;
}

bool ParsePlayerClergyAppointmentRequest12002(
    std::string_view payload, PlayerClergyAppointmentRequest12002 &request) noexcept {
  request = {};
  try {
    std::uint64_t candidate = 0, canonical = 0, alias = 0;
    if (!bridge::JsonUnsignedField(payload,"candidate_character_id",candidate) ||
        candidate == 0 || candidate > static_cast<std::uint64_t>((std::numeric_limits<std::int32_t>::max)()))
      return false;
    const bool has_canonical = HasField(payload,"expected_snapshot_revision");
    const bool has_alias = HasField(payload,"expected_revision");
    if (has_canonical && (!bridge::JsonUnsignedField(payload,"expected_snapshot_revision",canonical) || canonical == 0)) return false;
    if (has_alias && (!bridge::JsonUnsignedField(payload,"expected_revision",alias) || alias == 0)) return false;
    if (has_canonical && has_alias && canonical != alias) return false;
    request.candidate_character_id = static_cast<std::int32_t>(candidate);
    request.expected_revision = has_canonical ? canonical : alias;
    return true;
  } catch (...) { request = {}; return false; }
}

bool ExecutePlayerClergyAppointmentMailbox12002(
    void *opaque, const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *envelope = static_cast<QueryMailboxEnvelope *>(opaque);
  if (!envelope || !envelope->typed_context) return false;
  auto &query = *static_cast<PlayerClergyAppointmentMailboxContext12002 *>(envelope->typed_context);
  try {
    if (!EnterQueryMailbox(*envelope,stamp,&ExecutePlayerClergyAppointmentMailbox12002)) {
      query.failure = "player_clergy_appointment_published_frame_changed";
      return true;
    }
    query.bindings.application_main_thread_id = stamp.thread_id;
    (void)religion::clergy::ReadClergyAppointment12002(
        query.bindings,stamp.pump_epoch,query.request.candidate_character_id,query.observation);
    auto &out = query.observation;
    const auto &frame = envelope->expected_snapshot;
    if (out.available && (out.owner_character_id != frame.played_character_id ||
        out.date_raw != frame.date_raw || out.candidate_character_id != query.request.candidate_character_id)) {
      out = {};
      out.failure = religion::clergy::Failure::state_changed;
      out.capture_epoch = stamp.pump_epoch;
    }
    if (!out.available) {
      out.date_raw = static_cast<std::int32_t>(frame.date_raw);
      out.owner_character_id = static_cast<std::int32_t>(frame.played_character_id);
      out.candidate_character_id = query.request.candidate_character_id;
    }
    query.completed = true;
    (void)FinishQueryMailbox(*envelope);
    return true;
  } catch (...) {
    query.failure = "player_clergy_appointment_native_capture_exception";
    return false;
  }
}

std::string SerializePlayerClergyAppointmentResult12002(
    const PlayerClergyAppointmentMailboxContext12002 &query,std::string_view request_id) {
  if (!query.completed || !query.envelope.frame_stable || !query.failure.empty()) return {};
  const auto &frame = query.envelope.expected_snapshot;
  return "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":" + Quote(request_id) +
      ",\"ok\":true,\"result\":{\"step\":" + Quote(kPlayerClergyAppointmentPrivateStep12002) +
      ",\"accepted\":true,\"status\":" + Quote(query.observation.available ? "observed" : "unavailable") +
      ",\"private_build\":true,\"read_only\":true,\"advertised\":false,\"game_version\":\"1.20.0.2\","
      "\"executable_sha256\":" + Quote(kExecutableSha256) +
      ",\"domain_key\":" + Quote(kPlayerClergyAppointmentDomainKey12002) +
      ",\"backend_id\":" + Quote(kPlayerClergyAppointmentBackend12002) +
      ",\"snapshot_revision\":" + std::to_string(query.envelope.expected_snapshot_revision) +
      ",\"date_raw\":" + std::to_string(frame.date_raw) +
      ",\"player_clergy_appointment\":" + religion::clergy::SerializeClergyAppointment12002(query.observation) + "}}";
}

bool RunPlayerClergyAppointmentMailbox12002(
    PlayerClergyAppointmentMailboxContext12002 &query,std::string_view request_id,
    std::string &serialized,std::string &failure) noexcept {
  using namespace ck3_11906;
  serialized.clear(); failure.clear();
  try {
    auto &envelope = query.envelope;
    if (!envelope.game || !envelope.mailbox || query.request.candidate_character_id <= 0 ||
        !ValidFrame(envelope.expected_snapshot,envelope.expected_snapshot_revision) ||
        (query.request.expected_revision && query.request.expected_revision != envelope.expected_snapshot_revision)) {
      failure = "player_clergy_appointment_current_frame_unavailable"; return false;
    }
    envelope.typed_context = &query;
    if (TrySubmitMainThreadQueryV1(*envelope.mailbox,&ExecutePlayerClergyAppointmentMailbox12002,
        &envelope,envelope.ticket) != MainThreadQuerySubmitResultV1::submitted) {
      failure = "player_clergy_appointment_mailbox_submit_unavailable"; return false;
    }
    auto wait = WaitForMainThreadQueryV1(*envelope.mailbox,envelope.ticket,5000);
    while (wait == MainThreadQueryWaitResultV1::timeout_executor_already_running)
      wait = WaitForMainThreadQueryV1(*envelope.mailbox,envelope.ticket,100);
    const auto reclaim = ReclaimMainThreadQueryV1(*envelope.mailbox,envelope.ticket);
    if (wait != MainThreadQueryWaitResultV1::completed ||
        reclaim != MainThreadQueryReclaimResultV1::reclaimed || !query.completed || !envelope.frame_stable) {
      failure = query.failure.empty() ? "player_clergy_appointment_paused_capture_unavailable" : query.failure;
      return false;
    }
    serialized = SerializePlayerClergyAppointmentResult12002(query,request_id);
    if (!serialized.empty()) return true;
    failure = query.failure.empty() ? "player_clergy_appointment_serialization_unavailable" : query.failure;
    return false;
  } catch (...) {
    serialized.clear(); failure = "player_clergy_appointment_mailbox_exception"; return false;
  }
}

bool HandlePlayerClergyAppointmentPrivate12002(
    const game::GameAdapter &adapter,ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published,std::uint64_t revision,std::string_view step,
    std::string_view payload,std::string_view request_id,std::string &serialized,
    std::string &failure) noexcept {
  serialized.clear(); failure.clear();
  if (!IsPlayerClergyAppointmentPrivateStep12002(step)) {
    failure = "player_clergy_appointment_step_unavailable"; return false;
  }
  PlayerClergyAppointmentRequest12002 request{};
  if (!ParsePlayerClergyAppointmentRequest12002(payload,request)) {
    failure = "player_clergy_appointment_request_invalid"; return false;
  }
  if (!adapter.enabled() || xar::game::ReviewedCrozierAbiVersion(adapter.descriptor()) != "1.20.0.2" ||
      xar::game::ReviewedCrozierAbiSha256(adapter.descriptor()) != kExecutableSha256 || !ValidFrame(published,revision) ||
      (request.expected_revision && request.expected_revision != revision)) {
    failure = "player_clergy_appointment_current_frame_unavailable"; return false;
  }
  try {
    PlayerClergyAppointmentMailboxContext12002 query{};
    query.envelope.game = &NativeAdapter12002(adapter);
    query.envelope.mailbox = &mailbox;
    query.envelope.expected_snapshot = published;
    query.envelope.expected_snapshot_revision = revision;
    query.request = request;
    query.bindings = religion::clergy::BindClergyAppointmentImage12002(
        reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)),xar::game::ReviewedCrozierAbiSha256(adapter.descriptor()));
    return RunPlayerClergyAppointmentMailbox12002(query,request_id,serialized,failure);
  } catch (...) { failure = "player_clergy_appointment_handler_exception"; return false; }
}
} // namespace xar::ck3_12002
#endif
