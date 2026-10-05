#include "xar_bridge/player_control_v1.hpp"

#include <charconv>
#include <limits>
#include <map>

namespace xar::ck3_12003 {
namespace {
enum class ScalarKind { number, text, null_value };
struct Scalar { ScalarKind kind = ScalarKind::number; std::string text; std::uint64_t number = 0; };
bool Space(char c) noexcept { return c == ' ' || c == '\t' || c == '\r' || c == '\n'; }
bool Token(std::string_view v) noexcept {
  if (v.empty() || v.size() > 128) return false;
  for (char c : v) if (!((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
      (c >= '0' && c <= '9') || c == '_' || c == '.' || c == ':' || c == '-')) return false;
  return true;
}
bool Digest(std::string_view v) noexcept {
  if (v.size() != 64) return false;
  for (char c : v) if (!((c >= '0' && c <= '9') || (c >= 'a' && c <= 'f'))) return false;
  return true;
}
bool Quoted(std::string_view json, std::size_t &at, std::string &v) {
  if (at >= json.size() || json[at++] != '"') return false;
  const auto start = at;
  while (at < json.size() && json[at] != '"') {
    const auto c = static_cast<unsigned char>(json[at]);
    if (c < 0x20 || c >= 0x7f || c == '\\') return false;
    ++at;
  }
  if (at == json.size() || at-start > 128) return false;
  v.assign(json.substr(start, at-start)); ++at; return true;
}
bool Object(std::string_view json, std::map<std::string, Scalar> &fields) {
  if (json.size() > 4096) return false;
  std::size_t at = 0;
  const auto skip = [&] { while (at < json.size() && Space(json[at])) ++at; };
  skip(); if (at == json.size() || json[at++] != '{') return false;
  skip();
  while (at < json.size()) {
    std::string key;
    if (!Quoted(json, at, key) || key.empty() || fields.contains(key)) return false;
    skip(); if (at == json.size() || json[at++] != ':') return false;
    skip(); Scalar scalar{};
    if (at < json.size() && json[at] == '"') {
      scalar.kind = ScalarKind::text;
      if (!Quoted(json, at, scalar.text)) return false;
    } else if (json.substr(at, 4) == "null") { scalar.kind = ScalarKind::null_value; at += 4; }
    else {
      const auto start = at;
      while (at < json.size() && json[at] >= '0' && json[at] <= '9') ++at;
      if (at == start || (at-start > 1 && json[start] == '0')) return false;
      auto result = std::from_chars(json.data()+start, json.data()+at, scalar.number);
      if (result.ec != std::errc{} || result.ptr != json.data()+at) return false;
    }
    fields.emplace(std::move(key), std::move(scalar));
    if (fields.size() > 14) return false;
    skip(); if (at == json.size()) return false;
    if (json[at] == '}') { ++at; skip(); return at == json.size(); }
    if (json[at++] != ',') return false;
    skip();
  }
  return false;
}
} // namespace

bool IsCompletePlayerControlCharacterIdV1(std::uint64_t id) noexcept {
  return id > 0 && id != UINT32_MAX && id != UINT64_MAX;
}
std::string_view PlayerControlActionNameV1(PlayerControlActionV1 action) noexcept {
  switch (action) {
  case PlayerControlActionV1::query_context: return "query_context";
  case PlayerControlActionV1::open_pause_menu: return "open_pause_menu";
  case PlayerControlActionV1::open_switch: return "open_switch";
  case PlayerControlActionV1::choose_character: return "choose_character";
  case PlayerControlActionV1::confirm_control: return "confirm_control";
  default: return {};
  }
}
bool ParsePlayerControlRequestV1(std::string_view json,
    PlayerControlRequestV1 &output, std::string &reason) noexcept {
  try {
    const auto reject = [&](const char *why) { reason = why; return false; };
    std::map<std::string, Scalar> fields;
    if (!Object(json, fields)) return reject("malformed_closed_player_control_request");
    constexpr std::array<std::string_view, 14> allowed{{"type", "protocol_version", "request_id", "step", "action",
      "expected_revision", "expected_player_character_id", "expected_game_pid", "expected_connection_generation",
      "expected_process_creation_filetime_100ns", "request_nonce", "source_inventory_sha256",
      "expected_control_context_signature", "candidate_character_id"}};
    for (const auto &[key, value] : fields) {
      (void)value; bool found = false;
      for (auto name : allowed) found = found || name == key;
      if (!found) return reject("unknown_player_control_request_field");
    }
    const auto text = [&](const char *name, std::string &value) {
      auto i = fields.find(name); if (i == fields.end() || i->second.kind != ScalarKind::text) return false;
      value = i->second.text; return true;
    };
    const auto number = [&](const char *name, std::uint64_t &value) {
      auto i = fields.find(name); if (i == fields.end() || i->second.kind != ScalarKind::number) return false;
      value = i->second.number; return true;
    };
    PlayerControlRequestV1 r{};
    std::string type, step, action; std::uint64_t protocol = 0, pid = 0;
    if (!text("type",type) || type != "execute_step" || !number("protocol_version",protocol) || protocol != 1 ||
        !text("step",step) || step != kPlayerControlV1Step || !text("request_id",r.request_id) || !Token(r.request_id) ||
        !text("request_nonce",r.request_nonce) || !Token(r.request_nonce) ||
        !text("source_inventory_sha256",r.source_inventory_sha256) || !Digest(r.source_inventory_sha256) ||
        !text("action",action) || !number("expected_revision",r.expected_revision) || r.expected_revision == 0 ||
        !number("expected_player_character_id",r.expected_player_character_id) || !IsCompletePlayerControlCharacterIdV1(r.expected_player_character_id) ||
        !number("expected_game_pid",pid) || pid == 0 || pid > UINT32_MAX ||
        !number("expected_connection_generation",r.expected_connection_generation) || r.expected_connection_generation == 0 ||
        !number("expected_process_creation_filetime_100ns",r.expected_process_creation_filetime_100ns) || r.expected_process_creation_filetime_100ns == 0)
      return reject("player_control_request_binding_missing_or_invalid");
    r.expected_game_pid = static_cast<std::uint32_t>(pid);
    bool found = false;
    for (std::uint32_t i = 0; i <= 4; ++i) {
      auto candidate = static_cast<PlayerControlActionV1>(i);
      if (PlayerControlActionNameV1(candidate) == action) { r.action = candidate; found = true; }
    }
    if (!found) return reject("unsupported_player_control_action");
    if (r.action == PlayerControlActionV1::query_context) {
      if (fields.size() != 12 || fields.contains("expected_control_context_signature") || fields.contains("candidate_character_id"))
        return reject("player_control_query_must_not_supply_action_fields");
    } else {
      if (fields.size() != 14 || !text("expected_control_context_signature",r.expected_control_context_signature) || !Digest(r.expected_control_context_signature))
        return reject("player_control_action_requires_backend_signature");
      auto candidate = fields.find("candidate_character_id");
      if (candidate == fields.end()) return reject("player_control_candidate_missing");
      if (r.action == PlayerControlActionV1::open_pause_menu || r.action == PlayerControlActionV1::open_switch) {
        if (candidate->second.kind != ScalarKind::null_value) return reject("player_control_open_requires_null_candidate");
      } else {
        if (candidate->second.kind != ScalarKind::number || !IsCompletePlayerControlCharacterIdV1(candidate->second.number))
          return reject("player_control_selection_requires_complete_candidate");
        r.candidate_character_id = candidate->second.number;
      }
    }
    output = std::move(r); reason.clear(); return true;
  } catch (...) { try { reason = "player_control_parser_exception"; } catch (...) {} return false; }
}
} // namespace xar::ck3_12003
