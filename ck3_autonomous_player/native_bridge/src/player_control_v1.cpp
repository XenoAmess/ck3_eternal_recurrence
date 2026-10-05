#include "xar_bridge/player_control_v1.hpp"

namespace xar::ck3_12003 {
namespace {
bool Digest(std::string_view v) noexcept {
  if (v.size() != 64) return false;
  for (char c : v) if (!((c >= '0' && c <= '9') || (c >= 'a' && c <= 'f'))) return false;
  return true;
}
bool Target(const PlayerControlTargetV1 &t) noexcept {
  return t.read_complete && t.root_exists && t.root_visible && t.target_exists &&
      t.target_visible && t.target_enabled && t.unique_target && t.dispatch_admitted && t.target_vtable_rva != 0;
}
bool CurrentController(const PlayerControlObservationV1 &v) noexcept {
  if (!v.controller_records_complete || !v.local_player_id || !v.controlled_character_id ||
      !IsCompletePlayerControlCharacterIdV1(*v.controlled_character_id) || v.controlled_character_is_ai != false) return false;
  std::size_t matches = 0;
  for (const auto &r : v.controller_records) {
    if (!r.player_id || !r.character_id || !r.is_current_controller.has_value()) return false;
    if (r.player_id == v.local_player_id && r.is_current_controller == true) {
      if (r.character_id != v.controlled_character_id || r.is_ai != false) return false;
      ++matches;
    }
  }
  return matches == 1;
}
void JsonText(std::string &json, std::string_view v) {
  json += '"'; constexpr char hex[] = "0123456789abcdef";
  for (unsigned char c : v) {
    if (c == '"' || c == '\\') { json += '\\'; json += static_cast<char>(c); }
    else if (c < 0x20) { json += "\\u00"; json += hex[c >> 4]; json += hex[c & 15]; }
    else json += static_cast<char>(c);
  }
  json += '"';
}
struct Json {
  std::string value = "{"; bool first = true;
  void key(std::string_view k) { if (!first) value += ','; first = false; JsonText(value,k); value += ':'; }
  void text(std::string_view k, std::string_view v) { key(k); JsonText(value,v); }
  void number(std::string_view k, std::uint64_t v) { key(k); value += std::to_string(v); }
  void flag(std::string_view k, bool v) { key(k); value += v ? "true" : "false"; }
  template<class T> void nullable_number(std::string_view k, std::optional<T> v) { key(k); value += v ? std::to_string(*v) : "null"; }
  void nullable_bool(std::string_view k, std::optional<bool> v) { key(k); value += v.has_value() ? (*v ? "true" : "false") : "null"; }
  void nullable_text(std::string_view k, const std::optional<std::string> &v) { key(k); if (v) JsonText(value,*v); else value += "null"; }
  std::string finish() { return value + '}'; }
};
std::string_view Status(PlayerControlStatusV1 v) noexcept {
  switch(v) {
  case PlayerControlStatusV1::context_observed: return "context_observed";
  case PlayerControlStatusV1::dispatch_pending: return "dispatch_pending";
  case PlayerControlStatusV1::dispatch_unknown_claimed: return "dispatch_unknown_claimed";
  case PlayerControlStatusV1::control_observed: return "control_observed";
  default: return "unavailable";
  }
}
std::string_view Phase(PlayerControlPhaseV1 v) noexcept {
  switch(v) {
  case PlayerControlPhaseV1::map: return "map";
  case PlayerControlPhaseV1::pause_menu: return "pause_menu";
  case PlayerControlPhaseV1::switch_chooser: return "switch_chooser";
  case PlayerControlPhaseV1::control_confirmed: return "control_confirmed";
  default: return "unavailable";
  }
}
} // namespace

bool PlayerControlSourceProofV1(const PlayerControlObservationV1 &v) noexcept {
  return v.exact_build_verified && v.owner_verified && v.process_identity_verified &&
      v.source_abi_pins_verified && v.stock_files_verified && v.loaded_source_binding_verified &&
      v.frame_verified && v.pump_epoch > 0 && v.flow_id && Digest(*v.flow_id) &&
      Digest(v.control_context_signature);
}
bool PlayerControlStageAdmittedV1(const PlayerControlObservationV1 &v,
    PlayerControlActionV1 action, std::optional<std::uint64_t> candidate) noexcept {
  if (!PlayerControlSourceProofV1(v) || !v.context_signature_verified || v.flow_complete ||
      v.ironman != false || v.multiple_players != false || !CurrentController(v) ||
      v.flow_source_character_id != v.controlled_character_id || v.flow_local_player_id != v.local_player_id) return false;
  const auto raw = static_cast<std::uint32_t>(action);
  if (raw < 1 || raw > 4) return false;
  const auto stage = static_cast<std::size_t>(raw-1);
  if (v.stage_consumed[stage] || !Target(v.targets[stage])) return false;
  for (std::size_t i = stage+1; i < 4; ++i) if (v.stage_consumed[i]) return false;
  if (action == PlayerControlActionV1::open_pause_menu)
    return !candidate && v.phase == PlayerControlPhaseV1::map;
  if (action == PlayerControlActionV1::open_switch)
    return !candidate && v.phase == PlayerControlPhaseV1::pause_menu;
  if (!candidate || !IsCompletePlayerControlCharacterIdV1(*candidate) || candidate == v.controlled_character_id ||
      v.phase != PlayerControlPhaseV1::switch_chooser || !v.stage_consumed[1] || !v.candidates_complete) return false;
  std::size_t matches = 0;
  for (const auto &r : v.candidates) if (r.character_id == candidate) {
    if (!r.playable_id || r.source_verified != true || r.is_ruler != true || r.can_control != true ||
        r.selection_visible != true || r.selection_enabled != true) return false;
    ++matches;
  }
  if (matches != 1) return false;
  if (action == PlayerControlActionV1::choose_character) return !v.stage_consumed[2];
  return v.stage_consumed[2] && v.selected_character_id == candidate && v.flow_target_character_id == candidate;
}
bool PlayerControlActualControlObservedV1(const PlayerControlObservationV1 &v) noexcept {
  if (!PlayerControlSourceProofV1(v) || !v.flow_complete || v.phase != PlayerControlPhaseV1::control_confirmed ||
      !CurrentController(v) || !v.flow_source_character_id || !v.flow_target_character_id ||
      v.flow_source_character_id == v.flow_target_character_id || v.controlled_character_id != v.flow_target_character_id ||
      v.flow_local_player_id != v.local_player_id || !v.stage_consumed[3]) return false;
  for (const auto &r : v.controller_records)
    if (r.player_id == v.local_player_id && r.character_id == v.flow_source_character_id && r.is_current_controller == true) return false;
  return true;
}
PlayerControlObservationV1 UnavailablePlayerControlObservationV1(const PlayerControlRequestV1 &r) {
  PlayerControlObservationV1 v{};
  v.action=r.action; v.native_revision=r.expected_revision; v.connection_generation=r.expected_connection_generation;
  v.game_pid=r.expected_game_pid; v.played_character_id=r.expected_player_character_id;
  v.process_creation_filetime_100ns=r.expected_process_creation_filetime_100ns;
  v.reason="stock_chooser_controller_ai_runtime_sources_unavailable_provider_not_registered";
  return v;
}
std::string SerializePlayerControlObservationV1(const PlayerControlObservationV1 &v) {
  Json json;
  json.text("schema","ck3-player-control-v1"); json.text("step",kPlayerControlV1Step);
  json.text("action",PlayerControlActionNameV1(v.action)); json.text("status",Status(v.status));
  json.number("native_revision",v.native_revision); json.number("connection_generation",v.connection_generation);
  json.number("game_pid",v.game_pid); json.number("played_character_id",v.played_character_id);
  json.number("process_creation_filetime_100ns",v.process_creation_filetime_100ns); json.number("pump_epoch",v.pump_epoch);
  json.flag("exact_build_verified",v.exact_build_verified); json.flag("owner_verified",v.owner_verified);
  json.flag("process_identity_verified",v.process_identity_verified); json.flag("source_abi_pins_verified",v.source_abi_pins_verified);
  json.flag("stock_files_verified",v.stock_files_verified); json.flag("loaded_source_binding_verified",v.loaded_source_binding_verified);
  json.flag("frame_verified",v.frame_verified); json.flag("context_signature_verified",v.context_signature_verified);
  json.text("control_context_signature",v.control_context_signature); json.text("phase",Phase(v.phase));
  json.nullable_text("flow_id",v.flow_id); json.nullable_number("flow_source_character_id",v.flow_source_character_id);
  json.nullable_number("flow_target_character_id",v.flow_target_character_id); json.nullable_number("flow_local_player_id",v.flow_local_player_id);
  json.flag("flow_complete",v.flow_complete); json.nullable_number("local_player_id",v.local_player_id);
  json.nullable_number("controlled_character_id",v.controlled_character_id); json.nullable_number("selected_character_id",v.selected_character_id);
  json.nullable_bool("controlled_character_is_ai",v.controlled_character_is_ai); json.nullable_bool("ironman",v.ironman);
  json.nullable_bool("multiple_players",v.multiple_players); json.flag("controller_records_complete",v.controller_records_complete);
  json.flag("candidates_complete",v.candidates_complete);
  json.key("controller_records"); json.value+='[';
  for (std::size_t i=0;i<v.controller_records.size();++i) {
    if(i) json.value+=','; const auto &r=v.controller_records[i]; Json row;
    row.nullable_number("player_id",r.player_id); row.nullable_number("character_id",r.character_id);
    row.nullable_bool("is_current_controller",r.is_current_controller); row.nullable_bool("is_ai",r.is_ai); json.value+=row.finish();
  }
  json.value+=']'; json.key("candidates"); json.value+='[';
  for (std::size_t i=0;i<v.candidates.size();++i) {
    if(i) json.value+=','; const auto &r=v.candidates[i]; Json row;
    row.nullable_number("character_id",r.character_id); row.nullable_number("playable_id",r.playable_id);
    row.nullable_bool("is_ruler",r.is_ruler); row.nullable_bool("can_control",r.can_control);
    row.nullable_bool("selection_visible",r.selection_visible); row.nullable_bool("selection_enabled",r.selection_enabled);
    row.nullable_bool("source_verified",r.source_verified); json.value+=row.finish();
  }
  json.value+=']'; json.key("stage_consumed"); json.value+='[';
  for (std::size_t i=0;i<4;++i) { if(i) json.value+=','; json.value+=v.stage_consumed[i]?"true":"false"; }
  json.value+=']'; json.key("targets"); json.value+='[';
  for (std::size_t i=0;i<4;++i) {
    if(i) json.value+=','; const auto &t=v.targets[i]; Json row;
    row.flag("read_complete",t.read_complete); row.flag("root_exists",t.root_exists); row.flag("root_visible",t.root_visible);
    row.flag("target_exists",t.target_exists); row.flag("target_visible",t.target_visible); row.flag("target_enabled",t.target_enabled);
    row.flag("unique_target",t.unique_target); row.flag("dispatch_admitted",t.dispatch_admitted); row.number("target_vtable_rva",t.target_vtable_rva);
    json.value+=row.finish();
  }
  json.value+=']'; json.key("dispatches"); json.value+='[';
  for (std::size_t i=0;i<4;++i) {
    if(i) json.value+=','; const auto &d=v.dispatches[i]; Json row;
    row.flag("claim_latched",d.claim_latched); row.flag("dispatch_invoked",d.dispatch_invoked); row.flag("native_handled",d.native_handled);
    row.flag("post_read_complete",d.post_read_complete); row.flag("postcondition_observed",d.postcondition_observed); json.value+=row.finish();
  }
  json.value+=']'; json.flag("control_postcondition_verified",PlayerControlActualControlObservedV1(v)); json.text("reason",v.reason);
  return json.finish();
}
} // namespace xar::ck3_12003
