#include "xar_bridge/ck3_12003_adapter.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12004_religion_adopted_observers.hpp"
#include "xar_bridge/religion_rite_governance12002_mailbox.hpp"

#if defined(XAR_CK3_ENABLE_G2_PLAYER_RITE_GOVERNANCE_PRIVATE_QUERY_V1)
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

bool IsPlayerRiteGovernancePrivateStep12002(std::string_view step) noexcept {
  return step == kPlayerRiteGovernancePrivateStep12002;
}

bool ParsePlayerRiteGovernanceRevision12002(std::string_view payload,
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

bool ExecutePlayerRiteGovernanceMailbox12002(
    void *opaque, const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *envelope = static_cast<QueryMailboxEnvelope *>(opaque);
  if (!envelope || !envelope->typed_context) return false;
  auto &query = *static_cast<PlayerRiteGovernanceMailboxContext12002 *>(envelope->typed_context);
  try {
    if (!EnterQueryMailbox(*envelope, stamp, &ExecutePlayerRiteGovernanceMailbox12002)) {
      query.failure = "player_rite_governance_published_frame_changed";
      return true;
    }
    if (game::IsCk3_12004Descriptor(envelope->game->descriptor())) {
      (void)ck3_12004::religion::adopted::ReadPlayedRiteGovernance12004(
          query.bindings, stamp.pump_epoch, query.observation);
    } else {
      (void)religion::governance::ReadPlayedRiteGovernance12002(
          query.bindings, stamp.pump_epoch, query.observation);
    }
    auto &out = query.observation;
    const auto &frame = envelope->expected_snapshot;
    if (out.available && (out.played_character_id != frame.played_character_id ||
                          out.date_raw != frame.date_raw)) {
      out = {};
      out.failure = religion::governance::Failure::state_changed;
      out.capture_epoch = stamp.pump_epoch;
    }
    if (!out.available) {
      // The owner envelope still identifies the frame whose native read failed.
      out.date_raw = static_cast<std::int32_t>(frame.date_raw);
      out.played_character_id = static_cast<std::int32_t>(frame.played_character_id);
    }
    query.completed = true;
    (void)FinishQueryMailbox(*envelope);
    return true;
  } catch (...) {
    query.failure = "player_rite_governance_native_capture_exception";
    return false;
  }
}

std::string SerializePlayerRiteGovernanceResult12002(
    const PlayerRiteGovernanceMailboxContext12002 &query, std::string_view request_id) {
  if (!query.completed || !query.envelope.frame_stable || !query.failure.empty()) return {};
  const auto &frame = query.envelope.expected_snapshot;
  return "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":" + Quote(request_id) +
      ",\"ok\":true,\"result\":{\"step\":" + Quote(kPlayerRiteGovernancePrivateStep12002) +
      ",\"accepted\":true,\"status\":" + Quote(query.observation.available ? "observed" : "unavailable") +
      ",\"private_build\":true,\"read_only\":true,\"advertised\":false,\"game_version\":\"1.20.0.2\","
      "\"executable_sha256\":" + Quote(kExecutableSha256) +
      ",\"domain_key\":" + Quote(kPlayerRiteGovernanceDomainKey12002) +
      ",\"backend_id\":" + Quote(kPlayerRiteGovernanceBackend12002) +
      ",\"snapshot_revision\":" + std::to_string(query.envelope.expected_snapshot_revision) +
      ",\"date_raw\":" + std::to_string(frame.date_raw) +
      ",\"player_rite_governance\":" + religion::governance::SerializePlayedRiteGovernance12002(query.observation) + "}}";
}

bool RunPlayerRiteGovernanceMailbox12002(PlayerRiteGovernanceMailboxContext12002 &query,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept {
  using namespace ck3_11906;
  serialized.clear(); failure.clear();
  try {
    auto &envelope = query.envelope;
    if (!envelope.game || !envelope.mailbox ||
        !ValidFrame(envelope.expected_snapshot, envelope.expected_snapshot_revision)) {
      failure = "player_rite_governance_current_frame_unavailable"; return false;
    }
    if (game::IsCk3_12004Descriptor(envelope.game->descriptor()))
      envelope.snapshot_comparison = QuerySnapshotComparison12002::core_frame;
    envelope.typed_context = &query;
    if (TrySubmitMainThreadQueryV1(*envelope.mailbox,
        &ExecutePlayerRiteGovernanceMailbox12002, &envelope, envelope.ticket) !=
        MainThreadQuerySubmitResultV1::submitted) {
      failure = "player_rite_governance_mailbox_submit_unavailable"; return false;
    }
    auto wait = WaitForMainThreadQueryV1(*envelope.mailbox, envelope.ticket, 5000);
    while (wait == MainThreadQueryWaitResultV1::timeout_executor_already_running)
      wait = WaitForMainThreadQueryV1(*envelope.mailbox, envelope.ticket, 100);
    const auto reclaim = ReclaimMainThreadQueryV1(*envelope.mailbox, envelope.ticket);
    if (wait != MainThreadQueryWaitResultV1::completed ||
        reclaim != MainThreadQueryReclaimResultV1::reclaimed ||
        !query.completed || !envelope.frame_stable) {
      failure = query.failure.empty() ? "player_rite_governance_paused_capture_unavailable" : query.failure;
      return false;
    }
    serialized = SerializePlayerRiteGovernanceResult12002(query, request_id);
    if (!serialized.empty()) return true;
    failure = query.failure.empty() ? "player_rite_governance_serialization_unavailable" : query.failure;
    return false;
  } catch (...) {
    serialized.clear(); failure = "player_rite_governance_mailbox_exception"; return false;
  }
}

bool HandlePlayerRiteGovernancePrivate12002(const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox, const game::Snapshot &published,
    std::uint64_t revision, std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept {
  serialized.clear(); failure.clear();
  if (!IsPlayerRiteGovernancePrivateStep12002(step)) {
    failure = "player_rite_governance_step_unavailable"; return false;
  }
  std::uint64_t expected = 0;
  if (!ParsePlayerRiteGovernanceRevision12002(payload, expected)) {
    failure = "player_rite_governance_request_invalid"; return false;
  }
  const bool actual4 = game::IsCk3_12004Descriptor(adapter.descriptor());
  if (!adapter.enabled() || (!actual4 &&
      (xar::game::ReviewedCrozierAbiVersion(adapter.descriptor()) != "1.20.0.2" ||
       xar::game::ReviewedCrozierAbiSha256(adapter.descriptor()) != kExecutableSha256)) ||
      !ValidFrame(published, revision) || (expected != 0 && expected != revision)) {
    failure = "player_rite_governance_current_frame_unavailable"; return false;
  }
  try {
    PlayerRiteGovernanceMailboxContext12002 query{};
    query.envelope.game = &NativeAdapter12002(adapter);
    query.envelope.mailbox = &mailbox;
    query.envelope.expected_snapshot = published;
    query.envelope.expected_snapshot_revision = revision;
    const auto image_base = reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
    if (actual4) {
      query.bindings = ck3_12004::religion::adopted::BindRiteGovernanceImage12004(
          image_base, adapter.descriptor().executable_sha256);
    } else {
      query.bindings = religion::governance::BindRiteGovernanceImage12002(
          image_base, xar::game::ReviewedCrozierAbiSha256(adapter.descriptor()));
    }
    return RunPlayerRiteGovernanceMailbox12002(query, request_id, serialized, failure);
  } catch (...) { failure = "player_rite_governance_handler_exception"; return false; }
}
} // namespace xar::ck3_12002
#endif
