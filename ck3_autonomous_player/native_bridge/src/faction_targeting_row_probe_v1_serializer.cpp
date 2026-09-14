#include "xar_bridge/faction_targeting_row_probe_v1_serializer.hpp"

#include <cstddef>
#include <string>

namespace xar::bridge {
namespace {

void AppendBool(std::string &output, bool value) {
  output += value ? "true" : "false";
}

void AppendBinding(std::string &output,
                   const FactionTargetingRowProbeBindingV1 &binding) {
  output += "{\"paused\":";
  AppendBool(output, binding.paused);
  output += ",\"proof_epoch\":";
  output += std::to_string(binding.proof_epoch);
  output += ",\"snapshot_revision\":";
  output += std::to_string(binding.snapshot_revision);
  output += ",\"date_raw\":";
  output += std::to_string(binding.date_raw);
  output += ",\"player_character_id\":";
  output += std::to_string(binding.player_character_id);
  output += '}';
}

void AppendFaction(std::string &output,
                   const FactionTargetingRowProbeFactionV1 &faction) {
  output += "{\"faction_id\":";
  output += std::to_string(faction.faction_id);
  output += ",\"target_character_id\":";
  output += std::to_string(faction.target_character_id);
  output += ",\"leader_character_id\":";
  if (faction.leader_present) {
    output += std::to_string(faction.leader_character_id);
  } else {
    output += "null";
  }
  output += ",\"leader_present_in_character_members\":";
  AppendBool(output, faction.leader_present_in_character_members);
  output += ",\"character_member_ids\":[";
  for (std::size_t member_index = 0;
       member_index < faction.character_member_count; ++member_index) {
    if (member_index != 0) {
      output += ',';
    }
    output += std::to_string(faction.character_member_ids[member_index]);
  }
  output += "]}";
}

} // namespace

std::string SerializeFactionTargetingRowProbeV1(
    const FactionTargetingRowProbeResultV1 &result) {
  std::string output;
  output.reserve(512);
  output += "{\"schema\":\"";
  output += kFactionTargetingRowProbePrivateKeyV1;
  output += "\",\"private\":true,\"raw_pointers_persisted\":false";
  output += ",\"terminal\":\"";
  output += FactionTargetingRowProbeTerminalNameV1(result.terminal);
  output += "\",\"unavailable_reasons\":";
  output += std::to_string(result.unavailable_reasons);
  output += ",\"observer_failure_flags\":";
  output += std::to_string(result.observer_failure_flags);
  output += ",\"published_generation\":";
  output += std::to_string(result.published_generation);
  output += ",\"required_binding\":";
  AppendBinding(output, result.required_binding);
  output += ",\"observed_binding\":";
  AppendBinding(output, result.observed_binding);
  output += ",\"faction_count\":";
  output += std::to_string(result.faction_count);
  output += ",\"factions\":[";
  for (std::size_t faction_index = 0;
       faction_index < result.faction_count; ++faction_index) {
    if (faction_index != 0) {
      output += ',';
    }
    AppendFaction(output, result.factions[faction_index]);
  }
  output += "]}";
  return output;
}

} // namespace xar::bridge
