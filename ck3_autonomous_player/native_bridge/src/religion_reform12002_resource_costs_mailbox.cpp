#include "xar_bridge/ck3_12003_adapter.hpp"
#include "xar_bridge/religion_reform12002_resource_costs_mailbox.hpp"

#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_RESOURCE_COSTS_PRIVATE_QUERY_V1)
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

bool IsPlayerReligionDraftResourceCostsPrivateStep12002(std::string_view step) noexcept {
  return step == kPlayerReligionDraftResourceCostsPrivateStep12002;
}

bool ParsePlayerReligionDraftResourceCostsRevision12002(std::string_view payload,
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

bool ExecutePlayerReligionDraftResourceCostsMailbox12002(
    void *opaque, const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *envelope = static_cast<QueryMailboxEnvelope *>(opaque);
  if (!envelope || !envelope->typed_context) return false;
  auto &query = *static_cast<PlayerReligionDraftResourceCostsMailboxContext12002 *>(envelope->typed_context);
  try {
    if (!EnterQueryMailbox(*envelope, stamp, &ExecutePlayerReligionDraftResourceCostsMailbox12002)) {
      query.failure = "player_religion_draft_resource_costs_published_frame_changed";
      return true;
    }
    auto &out = query.observation;
    out = {};
    out.capture_epoch = stamp.pump_epoch;
    const auto &frame = envelope->expected_snapshot;
    out.date_raw = static_cast<std::int32_t>(frame.date_raw);
    out.played_character_id = static_cast<std::uint32_t>(frame.played_character_id);
    (void)religion_reform::ReadCurrentRiteCreationWindow12002(
        query.window_bindings, stamp.pump_epoch, out.current_window);
    const auto &window = out.current_window;
    if (!window.available) {
      out.failure = religion_reform::DraftWindowFailureKey(window.failure);
    } else if (window.played_character_id != out.played_character_id ||
               window.date_raw != out.date_raw) {
      out.failure = "published_frame_changed";
    } else {
      out.draft_observed = window.window != nullptr;
      religion_reform::CurrentDraftView view{
          const_cast<void *>(window.window), static_cast<std::int32_t>(window.played_character_id),
          stamp.pump_epoch, window.date_raw};
      (void)religion_reform::ReadCurrentRiteCreationBaseResourceCosts12002(
          query.cost_bindings, view, out.base_resource_cost_quote);
      if (out.draft_observed && !out.base_resource_cost_quote.draft_quote.available)
        out.failure = religion_reform::RiteCreationCostFailureKey(
            out.base_resource_cost_quote.draft_quote.failure);
      else
        out.available = true;
    }
    query.completed = true;
    (void)FinishQueryMailbox(*envelope);
    return true;
  } catch (...) {
    query.failure = "player_religion_draft_resource_costs_native_capture_exception";
    return false;
  }
}

std::string SerializePlayerReligionDraftResourceCostsObservation12002(
    const PlayerReligionDraftResourceCostsObservation12002 &out) {
  return "{\"schema\":\"ck3_12002_player_religion_draft_resource_costs_query_v1\","
      "\"available\":" + std::string(out.available ? "true" : "false") +
      ",\"window_present\":" + (out.current_window.present ? "true" : "false") +
      ",\"draft_observed\":" + (out.draft_observed ? "true" : "false") +
      ",\"failure\":" + (out.failure.empty() ? std::string("null") : Quote(out.failure)) +
      ",\"capture_epoch\":" + std::to_string(out.capture_epoch) +
      ",\"date_raw\":" + std::to_string(out.date_raw) +
      ",\"played_character_id\":" + std::to_string(out.played_character_id) +
      ",\"current_draft_window\":" +
      religion_reform::SerializeCurrentRiteCreationWindow12002(out.current_window) +
      ",\"base_resource_cost_quote\":" +
      religion_reform::SerializeCurrentRiteCreationBaseResourceCosts12002(out.base_resource_cost_quote) + "}";
}

std::string SerializePlayerReligionDraftResourceCostsResult12002(
    const PlayerReligionDraftResourceCostsMailboxContext12002 &query, std::string_view request_id) {
  if (!query.completed || !query.envelope.frame_stable || !query.failure.empty()) return {};
  const auto &frame = query.envelope.expected_snapshot;
  return "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":" + Quote(request_id) +
      ",\"ok\":true,\"result\":{\"step\":" + Quote(kPlayerReligionDraftResourceCostsPrivateStep12002) +
      ",\"accepted\":true,\"status\":" + Quote(query.observation.available ? "observed" : "unavailable") +
      ",\"private_build\":true,\"read_only\":true,\"advertised\":false,\"game_version\":\"1.20.0.2\","
      "\"executable_sha256\":" + Quote(kExecutableSha256) +
      ",\"domain_key\":" + Quote(kPlayerReligionDraftResourceCostsDomainKey12002) +
      ",\"backend_id\":" + Quote(kPlayerReligionDraftResourceCostsBackend12002) +
      ",\"snapshot_revision\":" + std::to_string(query.envelope.expected_snapshot_revision) +
      ",\"date_raw\":" + std::to_string(frame.date_raw) +
      ",\"player_religion_draft_resource_costs\":" +
      SerializePlayerReligionDraftResourceCostsObservation12002(query.observation) + "}}";
}

bool RunPlayerReligionDraftResourceCostsMailbox12002(PlayerReligionDraftResourceCostsMailboxContext12002 &query,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept {
  using namespace ck3_11906;
  serialized.clear(); failure.clear();
  try {
    auto &envelope = query.envelope;
    if (!envelope.game || !envelope.mailbox ||
        !ValidFrame(envelope.expected_snapshot, envelope.expected_snapshot_revision)) {
      failure = "player_religion_draft_resource_costs_current_frame_unavailable"; return false;
    }
    envelope.typed_context = &query;
    if (TrySubmitMainThreadQueryV1(*envelope.mailbox,
        &ExecutePlayerReligionDraftResourceCostsMailbox12002, &envelope, envelope.ticket) !=
        MainThreadQuerySubmitResultV1::submitted) {
      failure = "player_religion_draft_resource_costs_mailbox_submit_unavailable"; return false;
    }
    auto wait = WaitForMainThreadQueryV1(*envelope.mailbox, envelope.ticket, 5000);
    while (wait == MainThreadQueryWaitResultV1::timeout_executor_already_running)
      wait = WaitForMainThreadQueryV1(*envelope.mailbox, envelope.ticket, 100);
    const auto reclaim = ReclaimMainThreadQueryV1(*envelope.mailbox, envelope.ticket);
    if (wait != MainThreadQueryWaitResultV1::completed ||
        reclaim != MainThreadQueryReclaimResultV1::reclaimed ||
        !query.completed || !envelope.frame_stable) {
      failure = query.failure.empty() ? "player_religion_draft_resource_costs_paused_capture_unavailable" : query.failure;
      return false;
    }
    serialized = SerializePlayerReligionDraftResourceCostsResult12002(query, request_id);
    if (!serialized.empty()) return true;
    failure = query.failure.empty() ? "player_religion_draft_resource_costs_serialization_unavailable" : query.failure;
    return false;
  } catch (...) {
    serialized.clear(); failure = "player_religion_draft_resource_costs_mailbox_exception"; return false;
  }
}

bool HandlePlayerReligionDraftResourceCostsPrivate12002(const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox, const game::Snapshot &published,
    std::uint64_t revision, std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept {
  serialized.clear(); failure.clear();
  if (!IsPlayerReligionDraftResourceCostsPrivateStep12002(step)) {
    failure = "player_religion_draft_resource_costs_step_unavailable"; return false;
  }
  std::uint64_t expected = 0;
  if (!ParsePlayerReligionDraftResourceCostsRevision12002(payload, expected)) {
    failure = "player_religion_draft_resource_costs_request_invalid"; return false;
  }
  if (!adapter.enabled() || xar::game::ReviewedCrozierAbiVersion(adapter.descriptor()) != "1.20.0.2" ||
      xar::game::ReviewedCrozierAbiSha256(adapter.descriptor()) != kExecutableSha256 ||
      !ValidFrame(published, revision) || (expected != 0 && expected != revision)) {
    failure = "player_religion_draft_resource_costs_current_frame_unavailable"; return false;
  }
  try {
    PlayerReligionDraftResourceCostsMailboxContext12002 query{};
    query.envelope.game = &NativeAdapter12002(adapter);
    query.envelope.mailbox = &mailbox;
    query.envelope.expected_snapshot = published;
    query.envelope.expected_snapshot_revision = revision;
    const auto module = reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
    query.window_bindings = religion_reform::BindCurrentRiteCreationWindow12002(
        module, xar::game::ReviewedCrozierAbiSha256(adapter.descriptor()));
    query.cost_bindings = religion_reform::BindRiteCreationCostsImage12002(
        module, xar::game::ReviewedCrozierAbiSha256(adapter.descriptor()));
    return RunPlayerReligionDraftResourceCostsMailbox12002(query, request_id, serialized, failure);
  } catch (...) { failure = "player_religion_draft_resource_costs_handler_exception"; return false; }
}
} // namespace xar::ck3_12002
#endif
