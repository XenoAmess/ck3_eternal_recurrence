#include "xar_bridge/ck3_12003_call_ally_private_action.hpp"
#include "xar_bridge/ck3_12002_family_obligations_mailbox.hpp"
#include "xar_bridge/ck3_12003.hpp"
#include "xar_bridge/protocol.hpp"

#if defined(XAR_CK3_ENABLE_G2_M5_FAMILY_OBLIGATIONS_PRIVATE_QUERY_V1) && \
    defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)
#include <charconv>
#include <limits>

namespace xar::ck3_12002 {
namespace {
void SkipWhitespace(std::string_view &value) {
  while (!value.empty() && (value.front() == ' ' || value.front() == '\t' ||
      value.front() == '\r' || value.front() == '\n')) value.remove_prefix(1);
}
bool FieldValue(std::string_view payload, std::string_view key,
                std::string_view &value) {
  const auto token = '"' + std::string(key) + '"';
  const auto at = payload.find(token);
  if (at == std::string_view::npos) return false;
  value = payload.substr(at + token.size());
  SkipWhitespace(value);
  if (value.empty() || value.front() != ':') return false;
  value.remove_prefix(1); SkipWhitespace(value);
  return !value.empty();
}
bool ReadInteger(std::string_view &value, std::int64_t &out) {
  SkipWhitespace(value);
  const auto result = std::from_chars(value.data(), value.data() + value.size(), out);
  if (result.ec != std::errc{} || result.ptr == value.data()) return false;
  value.remove_prefix(static_cast<std::size_t>(result.ptr - value.data()));
  SkipWhitespace(value);
  return true;
}
bool FullId(std::string_view payload, std::string_view key, std::int32_t &out) {
  std::string_view value;
  std::int64_t id = -1;
  if (!FieldValue(payload, key, value) || !ReadInteger(value, id) || id == -1 ||
      id < (std::numeric_limits<std::int32_t>::min)() ||
      id > (std::numeric_limits<std::int32_t>::max)() || value.empty() ||
      (value.front() != ',' && value.front() != '}')) return false;
  out = static_cast<std::int32_t>(id);
  return true;
}
bool Costs(std::string_view payload, std::array<std::int64_t, 10> &out) {
  std::string_view value;
  if (!FieldValue(payload, "expected_send_cost_raw", value) || value.front() != '[')
    return false;
  value.remove_prefix(1);
  for (std::size_t i = 0; i < out.size(); ++i) {
    if (!ReadInteger(value, out[i]) || value.empty()) return false;
    const char end = i + 1 == out.size() ? ']' : ',';
    if (value.front() != end) return false;
    value.remove_prefix(1);
  }
  SkipWhitespace(value);
  return !value.empty() && (value.front() == ',' || value.front() == '}');
}
void String(std::string &wire, std::string_view value) {
  constexpr char hex[] = "0123456789abcdef";
  wire += '"';
  for (const unsigned char c : value) {
    if (c == '"' || c == '\\') { wire += '\\'; wire += static_cast<char>(c); }
    else if (c < 0x20) {
      wire += "\\u00"; wire += hex[c >> 4]; wire += hex[c & 15];
    } else wire += static_cast<char>(c);
  }
  wire += '"';
}
void Boolean(std::string &wire, bool value) { wire += value ? "true" : "false"; }
} // namespace

bool ParseCallAllyPrivateActionRequest12003(
    std::string_view payload, CallAllyPrivateActionRequest12003 &out) noexcept {
  out = {};
  try {
    return bridge::JsonUnsignedField(payload, "expected_revision", out.expected_revision) &&
        out.expected_revision != 0 &&
        FullId(payload, "recipient_character_id", out.native_request.recipient_character_id) &&
        FullId(payload, "war_id", out.native_request.war_id) &&
        Costs(payload, out.native_request.expected_send_cost_raw);
  } catch (...) { out = {}; return false; }
}

std::string SerializeCallAllySubmissionResult12003(
    std::string_view request_id, const FamilyObligationsMailboxContext12002 &query) {
  const auto &frame = query.observation.frame;
  const auto &receipt = query.call_ally_receipt;
  const bool submitted = query.call_ally_result == CommandSubmitResult::submitted;
  std::string wire = "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":";
  String(wire, request_id);
  wire += ",\"ok\":true,\"result\":{\"schema_version\":1,\"schema\":";
  String(wire, "xar.ck3.call-ally-to-war-private-action.v1");
  wire += ",\"kind\":\"ck3_12003_call_ally_to_war_private_v1\",\"game_version\":";
  String(wire, ck3_12003::kGameVersion);
  wire += ",\"executable_sha256\":"; String(wire, ck3_12003::kExecutableSha256);
  wire += ",\"step\":"; String(wire, kCallAllySubmitPrivateStep12003);
  wire += ",\"status\":";
  String(wire, submitted ? "receipt_pending" :
      query.call_ally_result == CommandSubmitResult::rejected ? "rejected" : "unavailable");
  wire += ",\"reason\":"; String(wire, query.failure);
  wire += ",\"accepted\":"; Boolean(wire, submitted);
  wire += ",\"material_result\":false,\"private_build\":true,\"read_only\":false,\"advertised\":false";
  wire += ",\"pre_native_revision\":" + std::to_string(query.observation.snapshot_revision);
  wire += ",\"snapshot_revision\":" + std::to_string(query.observation.snapshot_revision);
  wire += ",\"date_raw\":" + std::to_string(frame.date_raw);
  wire += ",\"played_character_id\":" + std::to_string(frame.played_character_id);
  wire += ",\"recipient_character_id\":" + std::to_string(query.call_ally_request.recipient_character_id);
  wire += ",\"war_id\":" + std::to_string(query.call_ally_request.war_id);
  wire += ",\"selected_target_native_legal\":"; Boolean(wire, receipt.selected_target_native_legal);
  wire += ",\"copied_context_identity_verified\":"; Boolean(wire, receipt.copied_context_identity_verified);
  wire += ",\"send_cost_sampled\":"; Boolean(wire, receipt.send_cost_sampled);
  wire += ",\"actual_send_cost_raw\":";
  if (receipt.send_cost_sampled) {
    wire += '[';
    for (std::size_t i = 0; i < receipt.actual_send_cost_raw.size(); ++i) {
      if (i) wire += ',';
      wire += std::to_string(receipt.actual_send_cost_raw[i]);
    }
    wire += ']';
  } else {
    wire += "null";
  }
  wire += "}}";
  return wire;
}
} // namespace xar::ck3_12002
#endif
