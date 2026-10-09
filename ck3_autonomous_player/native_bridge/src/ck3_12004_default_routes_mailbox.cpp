#include "xar_bridge/ck3_12004_default_routes_mailbox.hpp"

#include "xar_bridge/ck3_12004_features.hpp"

#include <array>

namespace xar::ck3_12004 {
namespace {

std::string Quote(std::string_view value) {
  constexpr char hex[] = "0123456789abcdef";
  std::string output = "\"";
  for (const unsigned char byte : value) {
    if (byte == '"' || byte == '\\') {
      output += '\\';
      output += static_cast<char>(byte);
    } else if (byte < 0x20) {
      output += "\\u00";
      output += hex[byte >> 4];
      output += hex[byte & 15];
    } else {
      output += static_cast<char>(byte);
    }
  }
  return output + '"';
}

std::string CommandResult(std::string_view request_id, std::string_view step,
                          bool accepted, std::string_view status) {
  std::string output =
      "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":";
  output += Quote(request_id);
  output += accepted ? ",\"ok\":true,\"result\":{\"step\":"
                     : ",\"ok\":false,\"error\":";
  if (accepted) {
    output += Quote(step);
    output += ",\"accepted\":true,\"status\":" + Quote(status) + "}}";
  } else {
    output += Quote(status) + "}";
  }
  return output;
}

std::string_view StateName(ck3_11906::TacticalDailySentinelStateV1 state) noexcept {
  using State = ck3_11906::TacticalDailySentinelStateV1;
  switch (state) {
  case State::idle: return "idle";
  case State::armed: return "armed";
  case State::triggered: return "triggered";
  case State::failed: return "failed";
  case State::unavailable: return "unavailable";
  }
  return "unavailable";
}

std::string TriggerReasons(std::uint32_t flags) {
  using namespace ck3_11906;
  struct Entry { std::uint32_t flag; std::string_view name; };
  constexpr std::array<Entry, 17> entries{{
      {tactical_daily_trigger_date_deadline, "date_deadline"},
      {tactical_daily_trigger_army_unavailable, "army_unavailable"},
      {tactical_daily_trigger_route_target_changed, "route_target_changed"},
      {tactical_daily_trigger_combat_transition, "combat_transition"},
      {tactical_daily_trigger_retreat_transition, "retreat_transition"},
      {tactical_daily_trigger_combat_unavailable, "combat_unavailable"},
      {tactical_daily_trigger_combat_phase_changed, "combat_phase_changed"},
      {tactical_daily_trigger_combat_roster_changed, "combat_roster_changed"},
      {tactical_daily_trigger_combat_terminal, "combat_terminal"},
      {tactical_daily_trigger_date_sequence_failure, "date_sequence_failure"},
      {tactical_daily_trigger_world_identity_changed, "world_identity_changed"},
      {tactical_daily_trigger_pause_not_observed, "pause_not_observed"},
      {tactical_daily_trigger_original_unavailable, "original_unavailable"},
      {tactical_daily_trigger_native_pause, "native_pause"},
      {tactical_daily_trigger_combat_winner_changed, "combat_winner_changed"},
      {tactical_daily_trigger_evaluation_failure, "evaluation_failure"},
      {tactical_daily_trigger_army_position_changed, "army_position_changed"},
  }};
  std::string output = "[";
  bool first = true;
  for (const auto &entry : entries) {
    if ((flags & entry.flag) == 0) continue;
    if (!first) output += ',';
    output += Quote(entry.name);
    first = false;
  }
  return output + ']';
}

} // namespace

std::string SerializeLoadedFeatureManifestResult12004(
    std::string_view request_id, std::uint64_t query_sequence,
    const game::LoadedFeatureManifestV1 &manifest) {
  const auto payload = SerializeLoadedFeatureManifestV1(manifest);
  if (payload.empty()) return {};
  const auto status =
      manifest.status == game::LoadedFeatureManifestStatusV1::available
          ? "available" : "unavailable";
  return "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":" +
      Quote(request_id) +
      ",\"ok\":true,\"result\":{\"step\":\"query-loaded-feature-manifest-v1\","
      "\"accepted\":true,\"status\":" + Quote(status) +
      ",\"query_sequence\":" + std::to_string(query_sequence) +
      ",\"snapshot_revision\":" + std::to_string(manifest.snapshot_revision) +
      ",\"loaded_feature_manifest\":" + payload +
      ",\"backend_id\":\"native-headless\"}}";
}

std::string SerializeTacticalDailySentinelResult12004(
    std::string_view request_id, std::string_view step,
    const ck3_11906::TacticalDailySentinelStatusV1 &status) {
  using Mode = ck3_11906::TacticalDailySentinelModeV1;
  std::string output =
      "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":" +
      Quote(request_id) + ",\"ok\":true,\"result\":{\"step\":" + Quote(step) +
      ",\"accepted\":true,\"status\":\"available\",\"tactical_daily_sentinel\":{\"state\":" +
      Quote(StateName(status.state));
  const auto integer = [&output](std::string_view name, auto value) {
    output += ",\"" + std::string(name) + "\":" + std::to_string(value);
  };
  const auto boolean = [&output](std::string_view name, bool value) {
    output += ",\"" + std::string(name) + "\":";
    output += value ? "true" : "false";
  };
  integer("generation", status.generation);
  integer("starting_date_raw", status.starting_date_raw);
  integer("target_date_raw", status.target_date_raw);
  integer("last_observed_date_raw", status.last_observed_date_raw);
  integer("trigger_date_raw", status.trigger_date_raw);
  integer("speed", status.speed);
  output += ",\"mode\":" + Quote(status.mode == Mode::terminal_or_sentinel
      ? "terminal_or_sentinel" : "decision_epoch");
  integer("army_count", status.army_count);
  integer("combat_count", status.combat_count);
  integer("completed_daily_ticks", status.completed_daily_ticks);
  integer("intermediate_pause_count", status.intermediate_pause_count);
  integer("trigger_flags", status.trigger_flags);
  output += ",\"trigger_reasons\":" + TriggerReasons(status.trigger_flags);
  integer("signed_date_delta_from_target_raw", status.signed_date_delta_from_target_raw);
  integer("overshoot_days", status.overshoot_days);
  boolean("pause_wrapper_called", status.pause_wrapper_called);
  boolean("pause_observed", status.pause_observed);
  boolean("terminal_observed", status.terminal_observed);
  boolean("abnormal", status.abnormal);
  return output + "}}}";
}

std::string SerializeTacticalDailySentinelArmResult12004(
    std::string_view request_id, std::string_view step,
    ck3_11906::TacticalDailySentinelArmStatusV1 result,
    const ck3_11906::TacticalDailySentinelStatusV1 &status) {
  using Arm = ck3_11906::TacticalDailySentinelArmStatusV1;
  if (result == Arm::armed) {
    return SerializeTacticalDailySentinelResult12004(request_id, step, status);
  }
  std::string_view reason = "tactical daily sentinel is unavailable";
  switch (result) {
  case Arm::invalid_request: reason = "invalid tactical daily sentinel request"; break;
  case Arm::requires_paused: reason = "tactical daily sentinel requires a paused map"; break;
  case Arm::starting_date_mismatch: reason = "tactical daily sentinel starting date mismatch"; break;
  case Arm::army_unavailable: reason = "tactical daily sentinel army is unavailable"; break;
  case Arm::combat_unavailable: reason = "tactical daily sentinel combat is unavailable"; break;
  case Arm::already_armed: reason = "tactical daily sentinel is already armed"; break;
  case Arm::unavailable: break;
  case Arm::armed: break;
  }
  return CommandResult(request_id, step, false, reason);
}

std::string SerializeTacticalDailySentinelCancelResult12004(
    std::string_view request_id, std::string_view step,
    ck3_11906::TacticalDailySentinelCancelStatusV1 result) {
  using Cancel = ck3_11906::TacticalDailySentinelCancelStatusV1;
  if (result == Cancel::canceled) {
    return CommandResult(request_id, step, true, "canceled");
  }
  std::string_view reason = "tactical daily sentinel cancel is unavailable";
  switch (result) {
  case Cancel::invalid_request: reason = "invalid tactical daily sentinel cancel request"; break;
  case Cancel::requires_paused: reason = "tactical daily sentinel cancel requires a paused map"; break;
  case Cancel::generation_mismatch: reason = "tactical daily sentinel cancel generation mismatch"; break;
  case Cancel::not_armed: reason = "tactical daily sentinel cancel requires an armed generation"; break;
  case Cancel::unavailable: break;
  case Cancel::canceled: break;
  }
  return CommandResult(request_id, step, false, reason);
}

} // namespace xar::ck3_12004
