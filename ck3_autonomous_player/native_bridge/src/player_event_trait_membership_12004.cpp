#include "xar_bridge/player_event_trait_membership_12004.hpp"

#include <array>

namespace xar::ck3_12004::person_events {

Bindings BindImage(std::uintptr_t image_base,
                   std::string_view executable_sha256) noexcept {
  Bindings output;
  if (image_base == 0 || executable_sha256 != ck3_12004::kExecutableSha256)
    return output;
  output.core = ck3_12004::BindCoreImage(image_base, executable_sha256);
  output.traits = phase_character::BindImage(image_base, executable_sha256);
  output.enabled = output.core.enabled && output.traits.enabled;
  return output;
}

bool ReadPlayerEventTraitMembershipV1(
    const Bindings &bindings, std::uint64_t expected_native_revision,
    std::int32_t expected_date_raw, std::int32_t expected_played_character_id,
    PlayerEventTraitMembershipV1 &output) noexcept {
  output = {};
  output.snapshot_revision = expected_native_revision;
  output.date_raw = expected_date_raw;
  output.played_character_id = expected_played_character_id;
  if (!bindings.enabled || expected_native_revision == 0 ||
      expected_played_character_id <= 0) {
    output.unavailable_reason = "current_player_frame_unavailable";
    return false;
  }
  CoreSnapshotPrefix before;
  if (!ck3_12004::ReadCoreSnapshot(bindings.core, before) ||
      !before.clock.paused || !before.map_ready ||
      !before.has_played_character || !before.played_character_alive ||
      before.clock.date_raw != expected_date_raw ||
      before.played_character_id != expected_played_character_id) {
    output.unavailable_reason = "current_player_frame_unavailable";
    return false;
  }
  auto *character = ck3_12004::ResolveCoreCharacter(
      bindings.core, expected_played_character_id);
  const auto *database = bindings.traits.get_trait_database();
  auto *poet = ck3_12002::phase_character::FindUniqueTraitDefinition(
      database, "lifestyle_poet");
  auto *journaller = ck3_12002::phase_character::FindUniqueTraitDefinition(
      database, "journaller");
  std::array<void *, 1> poet_definition{poet};
  std::array<void *, 1> journaller_definition{journaller};
  bool has_poet = false;
  bool has_journaller = false;
  if (!ck3_12002::phase_character::ReadTraitPresence(
          bindings.traits, character, poet_definition, has_poet) ||
      !ck3_12002::phase_character::ReadTraitPresence(
          bindings.traits, character, journaller_definition, has_journaller)) {
    output.unavailable_reason = "event_trait_membership_unavailable";
    return false;
  }
  CoreSnapshotPrefix after;
  if (!ck3_12004::ReadCoreSnapshot(bindings.core, after) ||
      !after.clock.paused || !after.map_ready ||
      !after.has_played_character || !after.played_character_alive ||
      after.clock.date_raw != before.clock.date_raw ||
      after.played_character_id != before.played_character_id ||
      ck3_12004::ResolveCoreCharacter(bindings.core,
          expected_played_character_id) != character) {
    output.unavailable_reason = "current_player_frame_changed";
    return false;
  }
  output.available = true;
  output.lifestyle_poet = has_poet;
  output.journaller = has_journaller;
  output.unavailable_reason.clear();
  return true;
}

std::string SerializePlayerEventTraitMembershipV1(
    const PlayerEventTraitMembershipV1 &value) {
  std::string output =
      "{\"schema\":\"xar.ck3.player-event-trait-membership/v1\","
      "\"game_version\":\"1.20.0.4\",\"executable_sha256\":\"";
  output += ck3_12004::kExecutableSha256;
  output += "\",\"status\":\"";
  output += value.available ? "available" : "unavailable";
  output += "\",\"snapshot_revision\":" +
      std::to_string(value.snapshot_revision);
  output += ",\"date_raw\":" + std::to_string(value.date_raw);
  output += ",\"played_character_id\":" +
      std::to_string(value.played_character_id);
  if (value.available) {
    output += ",\"traits\":{\"lifestyle_poet\":";
    output += value.lifestyle_poet ? "true" : "false";
    output += ",\"journaller\":";
    output += value.journaller ? "true" : "false";
    output += "},\"unavailable_reason\":null}";
  } else {
    // Reasons are this reader's fixed literals, never game-authored text.
    output += ",\"traits\":null,\"unavailable_reason\":\"";
    output += value.unavailable_reason;
    output += "\"}";
  }
  return output;
}

} // namespace xar::ck3_12004::person_events
