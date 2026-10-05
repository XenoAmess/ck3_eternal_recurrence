#include "xar_bridge/normal_exit_map_v1.hpp"

#include <charconv>
#include <limits>
#include <map>

namespace xar::ck3_12003 {
namespace {
struct Scalar {
  bool string = false;
  std::string text;
  std::uint64_t number = 0;
};
bool Whitespace(char c) noexcept { return c == ' ' || c == '\t' || c == '\r' || c == '\n'; }
bool Token(std::string_view value) noexcept {
  if (value.empty() || value.size() > 128) return false;
  for (char c : value)
    if (!((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
          (c >= '0' && c <= '9') || c == '_' || c == '.' || c == ':' || c == '-'))
      return false;
  return true;
}
bool Signature(std::string_view value) noexcept {
  if (value.size() != 64) return false;
  for (char c : value)
    if (!((c >= '0' && c <= '9') || (c >= 'a' && c <= 'f'))) return false;
  return true;
}
bool ReadQuoted(std::string_view input, std::size_t &at, std::string &value) {
  if (at >= input.size() || input[at++] != '"') return false;
  const auto start = at;
  while (at < input.size() && input[at] != '"') {
    const auto c = static_cast<unsigned char>(input[at]);
    if (c < 0x20 || c >= 0x7f || c == '\\') return false;
    ++at;
  }
  if (at == input.size() || at - start > 128) return false;
  value.assign(input.substr(start, at - start));
  ++at;
  return true;
}
bool ClosedObject(std::string_view input, std::map<std::string, Scalar> &values) {
  if (input.size() > 4096) return false;
  std::size_t at = 0;
  const auto skip = [&] { while (at < input.size() && Whitespace(input[at])) ++at; };
  skip();
  if (at == input.size() || input[at++] != '{') return false;
  skip();
  if (at < input.size() && input[at] == '}') return false;
  while (at < input.size()) {
    std::string key;
    if (!ReadQuoted(input, at, key) || key.empty() || values.contains(key)) return false;
    skip();
    if (at == input.size() || input[at++] != ':') return false;
    skip();
    Scalar scalar{};
    if (at < input.size() && input[at] == '"') {
      scalar.string = true;
      if (!ReadQuoted(input, at, scalar.text)) return false;
    } else {
      const auto start = at;
      while (at < input.size() && input[at] >= '0' && input[at] <= '9') ++at;
      if (at == start || (at - start > 1 && input[start] == '0')) return false;
      const auto parsed = std::from_chars(input.data() + start, input.data() + at, scalar.number);
      if (parsed.ec != std::errc{} || parsed.ptr != input.data() + at) return false;
    }
    values.emplace(std::move(key), std::move(scalar));
    if (values.size() > 13) return false;
    skip();
    if (at == input.size()) return false;
    if (input[at] == '}') { ++at; skip(); return at == input.size(); }
    if (input[at++] != ',') return false;
    skip();
  }
  return false;
}
void JsonText(std::string &json, std::string_view value) {
  json += '"';
  constexpr char hex[] = "0123456789abcdef";
  for (unsigned char c : value) {
    if (c == '"' || c == '\\') { json += '\\'; json += static_cast<char>(c); }
    else if (c < 0x20) { json += "\\u00"; json += hex[c >> 4]; json += hex[c & 15]; }
    else json += static_cast<char>(c);
  }
  json += '"';
}
std::string_view StatusName(NormalExitMapStatusV1 status) noexcept {
  switch (status) {
  case NormalExitMapStatusV1::context_observed: return "context_observed";
  case NormalExitMapStatusV1::confirmation_observed: return "confirmation_observed";
  case NormalExitMapStatusV1::dispatch_pending: return "dispatch_pending";
  case NormalExitMapStatusV1::dispatch_unknown_claimed: return "dispatch_unknown_claimed";
  default: return "unavailable";
  }
}
} // namespace

std::string_view NormalExitMapActionNameV1(NormalExitMapActionV1 action) noexcept {
  switch (action) {
  case NormalExitMapActionV1::query_context: return "query_context";
  case NormalExitMapActionV1::prepare_confirmation: return "prepare_confirmation";
  case NormalExitMapActionV1::confirm_desktop: return "confirm_desktop";
  case NormalExitMapActionV1::continue_preparation: return "continue_preparation";
  default: return {};
  }
}

bool ParseNormalExitMapRequestV1(std::string_view json,
    NormalExitMapRequestV1 &output, std::string &reason) noexcept {
  try {
    const auto reject = [&](const char *why) { reason = why; return false; };
    std::map<std::string, Scalar> fields;
    if (!ClosedObject(json, fields)) return reject("malformed_closed_exit_request");
    constexpr std::array<std::string_view, 13> allowed{
      "type", "protocol_version", "request_id", "step", "action",
      "expected_revision", "expected_player_character_id", "expected_game_pid",
      "expected_connection_generation", "expected_process_creation_filetime_100ns",
      "request_nonce", "source_inventory_sha256", "expected_exit_context_signature"};
    for (const auto &[key, value] : fields) {
      (void)value;
      bool found = false;
      for (auto name : allowed) found = found || name == key;
      if (!found) return reject("unknown_exit_request_field");
    }
    const auto text = [&](const char *name, std::string &value) {
      const auto it = fields.find(name);
      if (it == fields.end() || !it->second.string) return false;
      value = it->second.text; return true;
    };
    const auto number = [&](const char *name, std::uint64_t &value) {
      const auto it = fields.find(name);
      if (it == fields.end() || it->second.string) return false;
      value = it->second.number; return true;
    };
    NormalExitMapRequestV1 request{};
    std::string type, step, action;
    std::uint64_t protocol = 0, actor = 0, pid = 0;
    if (!text("type", type) || type != "execute_step" ||
        !number("protocol_version", protocol) || protocol != 1 ||
        !text("step", step) || step != kNormalExitMapV1Step ||
        !text("request_id", request.request_id) || !Token(request.request_id) ||
        !text("request_nonce", request.request_nonce) || !Token(request.request_nonce) ||
        !text("source_inventory_sha256", request.source_inventory_sha256) || !Signature(request.source_inventory_sha256) ||
        !text("action", action) ||
        !number("expected_revision", request.expected_revision) || request.expected_revision == 0 ||
        !number("expected_player_character_id", actor) || actor == 0 || actor > INT32_MAX ||
        !number("expected_game_pid", pid) || pid == 0 || pid > UINT32_MAX ||
        !number("expected_connection_generation", request.expected_connection_generation) ||
        request.expected_connection_generation == 0 ||
        !number("expected_process_creation_filetime_100ns", request.expected_process_creation_filetime_100ns) ||
        request.expected_process_creation_filetime_100ns == 0)
      return reject("exit_request_binding_missing_or_invalid");
    request.expected_player_character_id = static_cast<std::uint32_t>(actor);
    request.expected_game_pid = static_cast<std::uint32_t>(pid);
    if (action == "query_context") request.action = NormalExitMapActionV1::query_context;
    else if (action == "prepare_confirmation") request.action = NormalExitMapActionV1::prepare_confirmation;
    else if (action == "confirm_desktop") request.action = NormalExitMapActionV1::confirm_desktop;
    else if (action == "continue_preparation") request.action = NormalExitMapActionV1::continue_preparation;
    else return reject("unsupported_exit_action_frontend_unavailable");
    if (request.action == NormalExitMapActionV1::query_context) {
      if (fields.size() != 12 || fields.contains("expected_exit_context_signature"))
        return reject("query_context_must_not_supply_mutation_signature");
    } else if (fields.size() != 13 ||
        !text("expected_exit_context_signature", request.expected_exit_context_signature) ||
        !Signature(request.expected_exit_context_signature))
      return reject("exit_mutation_requires_backend_context_signature");
    output = std::move(request);
    reason.clear();
    return true;
  } catch (...) {
    try { reason = "exit_request_parser_exception"; } catch (...) {}
    return false;
  }
}

std::array<bool, 3> ReadNormalExitMapStageConsumptionV1(
    const NormalExitMapSessionV1 &session) noexcept {
  std::array<bool, 3> consumed{};
  for (std::size_t i = 0; i < consumed.size(); ++i)
    consumed[i] = session.claimed[i].load(std::memory_order_acquire);
  return consumed;
}

bool NormalExitMapStageConsumptionMatchesQueryV1(
    const NormalExitMapSessionV1 &session) noexcept {
  return ReadNormalExitMapStageConsumptionV1(session) == session.queried_stage_consumed;
}

bool NormalExitMapContinuePreparationAdmittedV1(
    const std::array<bool, 3> &consumed,
    const std::array<NormalExitMapTargetV1, 3> &targets,
    bool confirmation_visible) noexcept {
  if (consumed != std::array<bool, 3>{true, false, false} || confirmation_visible)
    return false;
  for (const auto &target : targets)
    if (!target.read_complete) return false;
  const auto &entry = targets[1];
  return entry.root_exists && entry.root_visible && entry.target_exists &&
      entry.target_visible && entry.target_enabled && entry.unique_target &&
      entry.dispatch_admitted && entry.target_vtable_rva != 0 &&
      !targets[2].root_visible;
}

std::string SerializeNormalExitMapObservationV1(const NormalExitMapObservationV1 &v) {
  std::string json = "{\"schema\":\"ck3-normal-exit-map-v1\",\"step\":\"normal-exit-map-v1\"";
  const auto number = [&](std::string_view key, auto value) { json += ",\""; json += key; json += "\":"; json += std::to_string(value); };
  const auto flag = [&](std::string_view key, bool value) { json += ",\""; json += key; json += "\":"; json += value ? "true" : "false"; };
  const auto text = [&](std::string_view key, std::string_view value) { json += ",\""; json += key; json += "\":"; JsonText(json, value); };
  text("action", NormalExitMapActionNameV1(v.action)); text("status", StatusName(v.status));
  number("native_revision",v.native_revision); number("connection_generation",v.connection_generation);
  number("game_pid",v.game_pid); number("played_character_id",v.played_character_id);
  number("process_creation_filetime_100ns",v.process_creation_filetime_100ns); number("pump_epoch",v.pump_epoch);
  flag("exact_build_verified",v.exact_build_verified); flag("owner_verified",v.owner_verified);
  flag("process_identity_verified",v.process_identity_verified); flag("source_abi_pins_verified",v.source_abi_pins_verified);
  flag("stock_files_verified",v.stock_files_verified); flag("loaded_source_binding_verified",v.loaded_source_binding_verified);
  flag("frame_verified",v.frame_verified); flag("context_signature_verified",v.context_signature_verified);
  flag("confirmation_visible",v.confirmation_visible);
  // These facts are outside this provider's proof domain, even for a malformed
  // internal observation. Never serialize caller/fixture values as exit/save proof.
  flag("orderly_exit_verified",false); flag("autosave_verified",false);
  text("exit_context_signature",v.exit_context_signature); text("reason",v.reason);
  json += ",\"stage_consumed\":[";
  for (std::size_t i = 0; i < v.stage_consumed.size(); ++i) {
    if (i) json += ',';
    json += v.stage_consumed[i] ? "true" : "false";
  }
  json += "],\"targets\":[";
  for (std::size_t i=0;i<v.targets.size();++i) {
    if(i) json+=','; json+='{';
    const auto &t=v.targets[i];
    json += "\"read_complete\":"; json += t.read_complete?"true":"false";
    flag("root_exists",t.root_exists); flag("root_visible",t.root_visible);
    flag("target_exists",t.target_exists); flag("target_visible",t.target_visible); flag("target_enabled",t.target_enabled);
    flag("unique_target",t.unique_target); flag("dispatch_admitted",t.dispatch_admitted); number("target_vtable_rva",t.target_vtable_rva);
    json+='}';
  }
  json += "],\"dispatches\":[";
  for (std::size_t i=0;i<v.dispatches.size();++i) {
    if(i) json+=','; json+='{';
    const auto &d=v.dispatches[i];
    json += "\"claim_latched\":"; json += d.claim_latched?"true":"false";
    flag("dispatch_invoked",d.dispatch_invoked); flag("native_handled",d.native_handled);
    flag("post_read_complete",d.post_read_complete); flag("postcondition_observed",d.postcondition_observed);
    json+='}';
  }
  json += "]}";
  return json;
}
} // namespace xar::ck3_12003
