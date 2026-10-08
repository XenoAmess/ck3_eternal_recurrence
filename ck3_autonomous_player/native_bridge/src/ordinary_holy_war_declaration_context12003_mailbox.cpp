#include "xar_bridge/ordinary_holy_war_declaration_context12003_mailbox.hpp"
#include "xar_bridge/ck3_12004_holy_war_defender_join_inputs.hpp"

#if defined(XAR_CK3_ENABLE_ORDINARY_HOLY_WAR_DECLARATION_CONTEXT_PRIVATE_V1)
#include "xar_bridge/ck3_12002_semantic_adapter.hpp"
#include "xar_bridge/ck3_12003_adapter.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12004_holy_war.hpp"
#include "xar_bridge/protocol.hpp"
#include <charconv>
#include <limits>
#include <sstream>
#include <utility>
#include <windows.h>

namespace xar::ck3_12002 {
namespace {
bool FrameValid(const game::Snapshot &frame, std::uint64_t revision) noexcept {
  return revision != 0 && frame.paused && frame.map_ready && frame.has_played_character &&
      frame.played_character_alive && frame.played_character_id > 0;
}
std::string_view Field(std::string_view json, std::string_view name) {
  const auto key = '"' + std::string(name) + '"';
  auto at = json.find(key);
  if (at == std::string_view::npos) return {};
  at += key.size();
  while (at < json.size() && (json[at] == ' ' || json[at] == '\t')) ++at;
  if (at == json.size() || json[at++] != ':') return {};
  while (at < json.size() && (json[at] == ' ' || json[at] == '\t')) ++at;
  return json.substr(at);
}
bool Integer(std::string_view json, std::string_view name, std::int32_t minimum, std::int32_t &out) {
  const auto value = Field(json, name);
  if (value.empty()) return false;
  std::int32_t parsed{};
  const auto result = std::from_chars(value.data(), value.data() + value.size(), parsed);
  if (result.ec != std::errc{} || parsed < minimum || result.ptr == value.data() + value.size() ||
      (*result.ptr != ',' && *result.ptr != '}' && *result.ptr != ' ' && *result.ptr != '\t')) return false;
  out = parsed; return true;
}
bool Titles(std::string_view json, std::vector<std::int32_t> &out) {
  auto value = Field(json, "target_title_ids");
  if (value.empty() || value.front() != '[') return false;
  value.remove_prefix(1); out.clear();
  for (;;) {
    while (!value.empty() && (value.front() == ' ' || value.front() == '\t')) value.remove_prefix(1);
    if (value.empty()) return false;
    if (value.front() == ']') return true;
    std::int32_t id{};
    const auto result = std::from_chars(value.data(), value.data() + value.size(), id);
    if (result.ec != std::errc{} || result.ptr == value.data() || id < 0 || out.size() >= 1000000) return false;
    out.push_back(id);
    value.remove_prefix(static_cast<std::size_t>(result.ptr - value.data()));
    while (!value.empty() && (value.front() == ' ' || value.front() == '\t')) value.remove_prefix(1);
    if (value.empty()) return false;
    if (value.front() == ']') return true;
    if (value.front() != ',') return false;
    value.remove_prefix(1);
    while (!value.empty() && (value.front() == ' ' || value.front() == '\t')) value.remove_prefix(1);
    if (value.empty() || value.front() == ']') return false;
  }
}
std::string Quote(std::string_view value) {
  constexpr char hex[] = "0123456789abcdef";
  std::string out = "\"";
  for (const unsigned char c : value) {
    if (c == '"' || c == '\\') { out += '\\'; out += static_cast<char>(c); }
    else if (c < 0x20) { out += "\\u00"; out += hex[c >> 4]; out += hex[c & 15]; }
    else out += static_cast<char>(c);
  }
  return out + '"';
}
} // namespace
bool IsOrdinaryHolyWarDeclarationContextPrivateStep12003(std::string_view step) noexcept {
  return step == kOrdinaryHolyWarDeclarationContextPrivateStep12003;
}
bool ParseOrdinaryHolyWarDeclarationContextRequest12003(std::string_view payload,
    OrdinaryHolyWarDeclarationContextRequest12003 &out) noexcept {
  out = {};
  try {
    std::uint64_t revision = 0, alias = 0;
    const bool canonical = !Field(payload, "expected_snapshot_revision").empty();
    const bool alternative = !Field(payload, "expected_revision").empty();
    if ((!canonical && !alternative) ||
        (canonical && (!bridge::JsonUnsignedField(payload, "expected_snapshot_revision", revision) || !revision)) ||
        (alternative && (!bridge::JsonUnsignedField(payload, "expected_revision", alias) || !alias)) ||
        (canonical && alternative && revision != alias)) return false;
    out.expected_revision = canonical ? revision : alias;
    if (!bridge::JsonUnsignedField(payload, "expected_public_revision", out.expected_public_revision) ||
        !out.expected_public_revision ||
        !bridge::JsonStringField(payload, "declaration_id", out.declaration_id, 128) ||
        !bridge::JsonStringField(payload, "casus_belli_key", out.selected.casus_belli_key, 128) ||
        !IsOrdinaryHolyWarKeyV1(out.selected.casus_belli_key) ||
        !Integer(payload, "target_character_id", 1, out.selected.target_character_id) ||
        !Integer(payload, "casus_belli_index", 0, out.selected.casus_belli_index) ||
        !Integer(payload, "configuration_index", -1, out.selected.configuration_index) ||
        !Integer(payload, "claimant_character_id", -1, out.selected.claimant_character_id) ||
        !Titles(payload, out.selected.target_title_ids)) return false;
    return out.declaration_id == std::to_string(out.selected.target_character_id) + '-' +
        std::to_string(out.selected.casus_belli_index) + '-' + std::to_string(out.selected.configuration_index);
  } catch (...) { out = {}; return false; }
}
bool ExecuteOrdinaryHolyWarDeclarationContextMailbox12003(void *opaque,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *envelope = static_cast<QueryMailboxEnvelope *>(opaque);
  if (!envelope || !envelope->typed_context) return false;
  auto &query = *static_cast<OrdinaryHolyWarDeclarationContextMailbox12003 *>(envelope->typed_context);
  try {
    if (!EnterQueryMailbox(*envelope, stamp, &ExecuteOrdinaryHolyWarDeclarationContextMailbox12003)) {
      query.failure = "ordinary_holy_war_declaration_context_published_frame_changed"; return true;
    }
    auto &out = query.observation;
    out = {};
    out.capture_epoch = stamp.pump_epoch;
    out.native_revision = envelope->expected_snapshot_revision;
    out.public_revision = query.request.expected_public_revision;
    out.date_raw = static_cast<std::int32_t>(envelope->expected_snapshot.date_raw);
    out.played_character_id = static_cast<std::int32_t>(envelope->expected_snapshot.played_character_id);
    out.declaration_id = query.request.declaration_id;
    auto &join = query.defender_join_observation;
    join = {};
    join.capture_epoch = out.capture_epoch;
    join.native_revision = out.native_revision;
    join.public_revision = out.public_revision;
    join.date_raw = out.date_raw;
    join.played_character_id = out.played_character_id;
    join.declaration_id = out.declaration_id;
    join.selected = query.request.selected;
    join.failure = religion::holy_war_defender_join::Failure::declaration_context_unavailable;
    (void)ReadSelectedOrdinaryHolyWarDeclarationContextV1(
        query.declarations, query.cost, query.request.selected, out,
        query.defender_join, join);
    query.completed = true;
    (void)FinishQueryMailbox(*envelope);
    return true;
  } catch (...) { query.failure = "ordinary_holy_war_declaration_context_capture_exception"; return false; }
}
std::string SerializeOrdinaryHolyWarDeclarationContextResult12003(
    const OrdinaryHolyWarDeclarationContextMailbox12003 &query, std::string_view request_id) {
  if (!query.completed || !query.envelope.frame_stable || !query.failure.empty()) return {};
  auto serialized = "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":" + Quote(request_id) +
      ",\"ok\":true,\"result\":{\"step\":" + Quote(kOrdinaryHolyWarDeclarationContextPrivateStep12003) +
      ",\"accepted\":true,\"status\":" + Quote(query.observation.available ? "observed" : "unavailable") +
      ",\"private_build\":true,\"read_only\":true,\"advertised\":false,\"game_version\":\"1.20.0.3\","
      "\"executable_sha256\":" + Quote(kOrdinaryHolyWarExactSha12003) +
      ",\"domain_key\":" + Quote(kOrdinaryHolyWarDeclarationContextDomainKey12003) +
      ",\"backend_id\":" + Quote(kOrdinaryHolyWarDeclarationContextBackend12003) +
      ",\"snapshot_revision\":" + std::to_string(query.envelope.expected_snapshot_revision) +
      ",\"public_revision\":" + std::to_string(query.request.expected_public_revision) +
      ",\"date_raw\":" + std::to_string(query.envelope.expected_snapshot.date_raw) +
      ",\"player_ordinary_holy_war_declaration_context\":" + SerializeOrdinaryHolyWarDeclarationContextV1(query.observation) +
      ",\"player_holy_war_defender_join_inputs\":" +
          religion::holy_war_defender_join::SerializeHolyWarDefenderJoinInputs12003(query.defender_join_observation) + "}}";
  if (query.envelope.game)
    serialized = game::Render12004BuildIdentity(std::move(serialized), query.envelope.game->descriptor());
  return serialized;
}
bool RunOrdinaryHolyWarDeclarationContextMailbox12003(OrdinaryHolyWarDeclarationContextMailbox12003 &query,
    std::string_view request_id, std::string &serialized, std::string &failure) noexcept {
  using namespace ck3_11906;
  serialized.clear(); failure.clear();
  try {
    auto &envelope = query.envelope;
    if (!envelope.game || !envelope.mailbox || !FrameValid(envelope.expected_snapshot, envelope.expected_snapshot_revision) ||
        query.request.expected_revision != envelope.expected_snapshot_revision || !query.request.expected_public_revision) {
      failure = "ordinary_holy_war_declaration_context_current_frame_unavailable"; return false;
    }
    envelope.typed_context = &query;
    if (TrySubmitMainThreadQueryV1(*envelope.mailbox, &ExecuteOrdinaryHolyWarDeclarationContextMailbox12003,
        &envelope, envelope.ticket) != MainThreadQuerySubmitResultV1::submitted) {
      failure = "ordinary_holy_war_declaration_context_mailbox_submit_unavailable"; return false;
    }
    auto wait = WaitForMainThreadQueryV1(*envelope.mailbox, envelope.ticket, 8000);
    while (wait == MainThreadQueryWaitResultV1::timeout_executor_already_running)
      wait = WaitForMainThreadQueryV1(*envelope.mailbox, envelope.ticket, 100);
    const auto reclaim = ReclaimMainThreadQueryV1(*envelope.mailbox, envelope.ticket);
    if (wait != MainThreadQueryWaitResultV1::completed || reclaim != MainThreadQueryReclaimResultV1::reclaimed ||
        !query.completed || !envelope.frame_stable) {
      failure = query.failure.empty() ? "ordinary_holy_war_declaration_context_capture_unavailable" : query.failure; return false;
    }
    serialized = SerializeOrdinaryHolyWarDeclarationContextResult12003(query, request_id);
    if (!serialized.empty()) return true;
    failure = "ordinary_holy_war_declaration_context_serialization_unavailable"; return false;
  } catch (...) { serialized.clear(); failure = "ordinary_holy_war_declaration_context_mailbox_exception"; return false; }
}
bool HandleOrdinaryHolyWarDeclarationContextPrivate12003(const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox, const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload, std::string_view request_id,
    std::string &serialized, std::string &failure) noexcept {
  serialized.clear(); failure.clear();
  OrdinaryHolyWarDeclarationContextRequest12003 request{};
  if (!IsOrdinaryHolyWarDeclarationContextPrivateStep12003(step) ||
      !ParseOrdinaryHolyWarDeclarationContextRequest12003(payload, request)) {
    failure = "ordinary_holy_war_declaration_context_request_invalid"; return false;
  }
  const bool actual4 = game::IsCk3_12004Descriptor(adapter.descriptor());
  const bool actual3 = adapter.descriptor().game_version == "1.20.0.3" &&
      adapter.descriptor().executable_sha256 == kOrdinaryHolyWarExactSha12003;
  if (!adapter.enabled() || (!actual3 && !actual4) ||
      !FrameValid(published, revision) || request.expected_revision != revision) {
    failure = "ordinary_holy_war_declaration_context_current_frame_unavailable"; return false;
  }
  try {
    OrdinaryHolyWarDeclarationContextMailbox12003 query{};
    query.request = std::move(request);
    query.envelope.game = &NativeAdapter12002(adapter);
    query.envelope.mailbox = &mailbox;
    query.envelope.expected_snapshot = published;
    query.envelope.expected_snapshot_revision = revision;
    const auto base = reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
    if (actual4) {
      const auto *declarations = game::BorrowOrdinaryHolyWarDeclarations12004(adapter);
      if (!declarations) {
        failure = "ordinary_holy_war_declaration_context_bindings_unavailable"; return false;
      }
      query.declarations = *declarations;
      query.cost = ck3_12004::BindOrdinaryHolyWarCbCostImage12004(
          base, adapter.descriptor().executable_sha256);
      auto faith = ck3_12004::religion::BindReligionContextImage12004(
          base, adapter.descriptor().executable_sha256);
      faith.core = query.declarations.core;
      query.defender_join = ck3_12004::religion::holy_war_defender_join::BindHolyWarDefenderJoinInputsImage12004(
          base, adapter.descriptor().executable_sha256, faith);
    } else {
      // Archived .3 keeps its separately reviewed declarations ABI.
      query.declarations = BindDeclarationsImage(base, game::ReviewedCrozierAbiSha256(adapter.descriptor()));
      query.cost = BindOrdinaryHolyWarCbCostImageV1(base, adapter.descriptor().executable_sha256);
      auto faith = religion::BindReligionContextImage12002(base, game::ReviewedCrozierAbiSha256(adapter.descriptor()));
      faith.core = query.declarations.core;
      query.defender_join = religion::holy_war_defender_join::BindHolyWarDefenderJoinInputsImage12003(
          base, adapter.descriptor().executable_sha256, faith);
    }
    return RunOrdinaryHolyWarDeclarationContextMailbox12003(query, request_id, serialized, failure);
  } catch (...) { failure = "ordinary_holy_war_declaration_context_handler_exception"; return false; }
}
} // namespace xar::ck3_12002
#endif
