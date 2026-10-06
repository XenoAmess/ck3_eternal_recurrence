#include "xar_bridge/ck3_12003_adapter.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12004_religion_bindings.hpp"
#include "xar_bridge/religion_doctrine12002_tenet_rows_mailbox.hpp"

#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_TENETS_PRIVATE_QUERY_V1)
#include "xar_bridge/ck3_12002_semantic_adapter.hpp"
#include "xar_bridge/protocol.hpp"
#include "xar_bridge/religion_reform12002_tenet_sources.hpp"

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

bool IsPlayerReligionTenetsPrivateStep12002(std::string_view step) noexcept {
  return step == kPlayerReligionTenetsPrivateStep12002;
}

bool ParsePlayerReligionTenetsRevision12002(std::string_view payload,
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

bool ParsePlayerReligionTenetsComparisonRequest12003(std::string_view payload,
    std::optional<std::uint32_t> &target_rite_id, std::string &tenet_key) noexcept {
  target_rite_id.reset(); tenet_key.clear();
  try {
    const bool target_present = HasField(payload, "target_rite_id");
    const bool key_present = HasField(payload, "tenet_key");
    if (target_present != key_present) return false;
    if (!target_present) return true;
    std::uint64_t target = 0;
    if (!bridge::JsonUnsignedField(payload, "target_rite_id", target) ||
        target > 0xFFFFFFFFULL ||
        !bridge::JsonStringField(payload, "tenet_key", tenet_key,
            bridge::kMaximumControlStringBytes) || tenet_key.empty()) {
      tenet_key.clear(); return false;
    }
    target_rite_id = static_cast<std::uint32_t>(target);
    return true;
  } catch (...) { target_rite_id.reset(); tenet_key.clear(); return false; }
}

bool ParsePlayerReligionTenetsKnowledgeRequest12003(std::string_view payload,
    bool &include_knowledge_catalogue) noexcept {
  include_knowledge_catalogue = false;
  try {
    if (!HasField(payload, "include_knowledge_catalogue")) return true;
    return bridge::JsonBooleanField(payload, "include_knowledge_catalogue",
        include_knowledge_catalogue);
  } catch (...) { include_knowledge_catalogue = false; return false; }
}

bool ExecutePlayerReligionTenetsMailbox12002(
    void *opaque, const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *envelope = static_cast<QueryMailboxEnvelope *>(opaque);
  if (!envelope || !envelope->typed_context) return false;
  auto &query = *static_cast<PlayerReligionTenetsMailboxContext12002 *>(envelope->typed_context);
  try {
    if (!EnterQueryMailbox(*envelope, stamp, &ExecutePlayerReligionTenetsMailbox12002)) {
      query.failure = "player_religion_tenets_published_frame_changed";
      return true;
    }
    const bool actual4 = game::IsCk3_12004Descriptor(envelope->game->descriptor());
    if (actual4) {
      (void)ck3_12004::religion::ReadPlayedTenetRows12004(
          query.bindings, query.tenet_bindings, stamp.pump_epoch, query.observation);
    } else {
      (void)religion::doctrine12002::ReadPlayedTenetRows12002(
          query.bindings, query.tenet_bindings, stamp.pump_epoch, query.observation);
    }
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
    if (query.target_rite_id.has_value()) {
      if (actual4) {
        (void)ck3_12004::religion::ReadPlayedTargetRiteTenetComparison12004(
            query.comparison_bindings, *query.target_rite_id, query.tenet_key,
            stamp.pump_epoch, query.comparison);
      } else {
        (void)ck3_12003::religion::target_tenet::ReadPlayedTargetRiteTenetComparison12003(
            query.comparison_bindings, *query.target_rite_id, query.tenet_key,
            stamp.pump_epoch, query.comparison);
      }
      auto &comparison = query.comparison;
      if (comparison.available &&
          (comparison.played_character_id != static_cast<std::uint32_t>(frame.played_character_id) ||
           comparison.date_raw != frame.date_raw)) {
        comparison = {};
        comparison.requested_target_rite_id = *query.target_rite_id;
        comparison.tenet_key = query.tenet_key;
        comparison.failure = ck3_12003::religion::target_tenet::Failure::state_changed;
      }
      // Failure still belongs to this actual owner frame, independently of
      // whether the original current-member query succeeded.
      comparison.capture_epoch = stamp.pump_epoch;
      comparison.date_raw = static_cast<std::int32_t>(frame.date_raw);
      comparison.played_character_id = static_cast<std::uint32_t>(frame.played_character_id);
    }
    if (query.include_knowledge_catalogue) {
      if (actual4) {
        (void)ck3_12004::religion::ReadPlayedTenetKnowledgeCatalogue12004(
            query.knowledge_bindings, stamp.pump_epoch, query.knowledge_catalogue);
      } else {
        (void)ck3_12003::religion::tenet_knowledge::ReadPlayedTenetKnowledgeCatalogue12003(
            query.knowledge_bindings, stamp.pump_epoch, query.knowledge_catalogue);
      }
      auto &catalogue = query.knowledge_catalogue;
      if (catalogue.available &&
          (catalogue.played_character_id != static_cast<std::uint32_t>(frame.played_character_id) ||
           catalogue.date_raw != frame.date_raw)) {
        catalogue = {};
        catalogue.failure = ck3_12003::religion::tenet_knowledge::Failure::state_changed;
      }
      catalogue.capture_epoch = stamp.pump_epoch;
      catalogue.date_raw = static_cast<std::int32_t>(frame.date_raw);
      catalogue.played_character_id = static_cast<std::uint32_t>(frame.played_character_id);
    }
    query.completed = true;
    (void)FinishQueryMailbox(*envelope);
    return true;
  } catch (...) {
    query.failure = "player_religion_tenets_native_capture_exception";
    return false;
  }
}

std::string SerializePlayerReligionTenetsResult12002(
    const PlayerReligionTenetsMailboxContext12002 &query, std::string_view request_id) {
  if (!query.completed || !query.envelope.frame_stable || !query.failure.empty()) return {};
  const auto &frame = query.envelope.expected_snapshot;
  auto tenets = religion::doctrine12002::SerializeTenetRows12002(query.observation);
  if (query.target_rite_id.has_value()) {
    tenets.pop_back();
    tenets += ",\"target_rite_tenet_comparison\":" +
        ck3_12003::religion::target_tenet::SerializeTargetRiteTenetComparison12003(query.comparison) + "}";
  }
  if (query.include_knowledge_catalogue) {
    tenets.pop_back();
    tenets += ",\"player_tenet_knowledge_catalogue\":" +
        ck3_12003::religion::tenet_knowledge::SerializePlayedTenetKnowledgeCatalogue12003(
            query.knowledge_catalogue) + "}";
  }
  return "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":" + Quote(request_id) +
      ",\"ok\":true,\"result\":{\"step\":" + Quote(kPlayerReligionTenetsPrivateStep12002) +
      ",\"accepted\":true,\"status\":" + Quote(query.observation.available ? "observed" : "unavailable") +
      ",\"private_build\":true,\"read_only\":true,\"advertised\":false,\"game_version\":\"1.20.0.2\","
      "\"executable_sha256\":" + Quote(kExecutableSha256) +
      ",\"domain_key\":" + Quote(kPlayerReligionTenetsDomainKey12002) +
      ",\"backend_id\":" + Quote(kPlayerReligionTenetsBackend12002) +
      ",\"snapshot_revision\":" + std::to_string(query.envelope.expected_snapshot_revision) +
      ",\"date_raw\":" + std::to_string(frame.date_raw) +
      ",\"player_religion_tenets\":" + tenets + "}}";
}

bool RunPlayerReligionTenetsMailbox12002(PlayerReligionTenetsMailboxContext12002 &query,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept {
  using namespace ck3_11906;
  serialized.clear(); failure.clear();
  try {
    auto &envelope = query.envelope;
    if (!envelope.game || !envelope.mailbox ||
        !ValidFrame(envelope.expected_snapshot, envelope.expected_snapshot_revision)) {
      failure = "player_religion_tenets_current_frame_unavailable"; return false;
    }
    envelope.typed_context = &query;
    if (game::IsCk3_12004Descriptor(envelope.game->descriptor()))
      envelope.snapshot_comparison = QuerySnapshotComparison12002::core_frame;
    if (TrySubmitMainThreadQueryV1(*envelope.mailbox,
        &ExecutePlayerReligionTenetsMailbox12002, &envelope, envelope.ticket) !=
        MainThreadQuerySubmitResultV1::submitted) {
      failure = "player_religion_tenets_mailbox_submit_unavailable"; return false;
    }
    auto wait = WaitForMainThreadQueryV1(*envelope.mailbox, envelope.ticket, 5000);
    while (wait == MainThreadQueryWaitResultV1::timeout_executor_already_running)
      wait = WaitForMainThreadQueryV1(*envelope.mailbox, envelope.ticket, 100);
    const auto reclaim = ReclaimMainThreadQueryV1(*envelope.mailbox, envelope.ticket);
    if (wait != MainThreadQueryWaitResultV1::completed ||
        reclaim != MainThreadQueryReclaimResultV1::reclaimed ||
        !query.completed || !envelope.frame_stable) {
      failure = query.failure.empty() ? "player_religion_tenets_paused_capture_unavailable" : query.failure;
      return false;
    }
    serialized = SerializePlayerReligionTenetsResult12002(query, request_id);
    if (!serialized.empty()) return true;
    failure = query.failure.empty() ? "player_religion_tenets_serialization_unavailable" : query.failure;
    return false;
  } catch (...) {
    serialized.clear(); failure = "player_religion_tenets_mailbox_exception"; return false;
  }
}

bool HandlePlayerReligionTenetsPrivate12002(const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox, const game::Snapshot &published,
    std::uint64_t revision, std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept {
  serialized.clear(); failure.clear();
  if (!IsPlayerReligionTenetsPrivateStep12002(step)) {
    failure = "player_religion_tenets_step_unavailable"; return false;
  }
  std::uint64_t expected = 0;
  std::optional<std::uint32_t> target_rite_id;
  std::string tenet_key;
  bool include_knowledge_catalogue = false;
  const bool actual4 = game::IsCk3_12004Descriptor(adapter.descriptor());
  if (!ParsePlayerReligionTenetsRevision12002(payload, expected) ||
      !ParsePlayerReligionTenetsComparisonRequest12003(payload, target_rite_id, tenet_key) ||
      !ParsePlayerReligionTenetsKnowledgeRequest12003(payload, include_knowledge_catalogue) ||
      ((target_rite_id.has_value() || include_knowledge_catalogue) &&
       !xar::game::IsCk3_12003Descriptor(adapter.descriptor()) && !actual4)) {
    failure = "player_religion_tenets_request_invalid"; return false;
  }
  if (!adapter.enabled() ||
      (!actual4 && (xar::game::ReviewedCrozierAbiVersion(adapter.descriptor()) != "1.20.0.2" ||
       xar::game::ReviewedCrozierAbiSha256(adapter.descriptor()) != kExecutableSha256)) ||
      !ValidFrame(published, revision) || (expected != 0 && expected != revision)) {
    failure = "player_religion_tenets_current_frame_unavailable"; return false;
  }
  try {
    PlayerReligionTenetsMailboxContext12002 query{};
    query.envelope.game = &NativeAdapter12002(adapter);
    query.envelope.mailbox = &mailbox;
    query.envelope.expected_snapshot = published;
    query.envelope.expected_snapshot_revision = revision;
    const auto image_base =
        reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
    if (actual4) {
      const auto bindings = ck3_12004::religion::BindPlayerTenetImage12004(
          image_base, adapter.descriptor().executable_sha256);
      query.bindings = bindings.context;
      query.tenet_bindings = bindings.rows;
      if (target_rite_id.has_value()) {
        query.target_rite_id = target_rite_id;
        query.tenet_key = std::move(tenet_key);
        query.comparison_bindings = bindings.comparison;
      }
      if (include_knowledge_catalogue) {
        query.include_knowledge_catalogue = true;
        query.knowledge_bindings = bindings.knowledge;
      }
    } else {
      query.bindings = religion::BindReligionContextImage12002(
          image_base, xar::game::ReviewedCrozierAbiSha256(adapter.descriptor()));
      query.tenet_bindings = religion::doctrine12002::BindTenetRows12002(
          image_base, xar::game::ReviewedCrozierAbiSha256(adapter.descriptor()));
    }
    if (!actual4 && (target_rite_id.has_value() || include_knowledge_catalogue)) {
      const auto source = religion_reform::BindCurrentDraftTenetSources12002(
          image_base,
          xar::game::ReviewedCrozierAbiSha256(adapter.descriptor()));
      // Bind only. The current draft reader/window is never invoked.
      if (target_rite_id.has_value()) {
        query.target_rite_id = target_rite_id;
        query.tenet_key = std::move(tenet_key);
        query.comparison_bindings = {query.bindings, source.rite_storage_global,
            source.tenet_database_global, query.tenet_bindings.tenet_state};
      }
      if (include_knowledge_catalogue) {
        query.include_knowledge_catalogue = true;
        query.knowledge_bindings = {query.bindings, source.tenet_database_global,
            source.perk_database_global, source.actor_extra_collection,
            source.actor_perks_collection, source.contains};
      }
    }
    return RunPlayerReligionTenetsMailbox12002(query, request_id, serialized, failure);
  } catch (...) { failure = "player_religion_tenets_handler_exception"; return false; }
}
} // namespace xar::ck3_12002
#endif
