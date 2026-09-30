#pragma once
// Attempt-local, read-only diagnostic of the existing full Snapshot equality.
#include "xar_bridge/game_contract.hpp"
#include <cstdint>
#include <string>
namespace xar::ck3_11906 {
inline std::uint64_t TitleMapNavigationSnapshotDiffMaskV1(
    const game::Snapshot &expected, const game::Snapshot &observed) {
  std::uint64_t mask = 0;
  if (expected.date_raw != observed.date_raw) mask |= std::uint64_t{1} << 0;
  if (expected.speed != observed.speed) mask |= std::uint64_t{1} << 1;
  if (expected.paused != observed.paused) mask |= std::uint64_t{1} << 2;
  if (expected.player_id != observed.player_id) mask |= std::uint64_t{1} << 3;
  if (expected.map_ready != observed.map_ready) mask |= std::uint64_t{1} << 4;
  if (expected.has_played_character != observed.has_played_character) mask |= std::uint64_t{1} << 5;
  if (expected.played_character_id != observed.played_character_id) mask |= std::uint64_t{1} << 6;
  if (expected.played_character_alive != observed.played_character_alive) mask |= std::uint64_t{1} << 7;
  if (expected.played_character_stress_points != observed.played_character_stress_points) mask |= std::uint64_t{1} << 8;
  if (expected.played_character_gold != observed.played_character_gold) mask |= std::uint64_t{1} << 9;
  if (expected.played_character_prestige != observed.played_character_prestige) mask |= std::uint64_t{1} << 10;
  if (expected.played_character_piety != observed.played_character_piety) mask |= std::uint64_t{1} << 11;
  if (expected.played_character_betrothed_id != observed.played_character_betrothed_id) mask |= std::uint64_t{1} << 12;
  if (expected.played_character_primary_spouse_id != observed.played_character_primary_spouse_id) mask |= std::uint64_t{1} << 13;
  if (expected.played_character_spouse_ids != observed.played_character_spouse_ids) mask |= std::uint64_t{1} << 14;
  if (expected.has_active_event != observed.has_active_event) mask |= std::uint64_t{1} << 15;
  if (expected.active_event_instance_id != observed.active_event_instance_id) mask |= std::uint64_t{1} << 16;
  if (expected.active_event_option_count != observed.active_event_option_count) mask |= std::uint64_t{1} << 17;
  if (expected.has_pending_character_interaction != observed.has_pending_character_interaction) mask |= std::uint64_t{1} << 18;
  if (expected.pending_character_interaction_id != observed.pending_character_interaction_id) mask |= std::uint64_t{1} << 19;
  if (expected.pending_sender_character_id != observed.pending_sender_character_id) mask |= std::uint64_t{1} << 20;
  if (expected.pending_auto_accept_notification != observed.pending_auto_accept_notification) mask |= std::uint64_t{1} << 21;
  if (expected.active_wars != observed.active_wars) mask |= std::uint64_t{1} << 22;
  if (expected.player_armies != observed.player_armies) mask |= std::uint64_t{1} << 23;
  if (expected.has_one_life_settlement != observed.has_one_life_settlement) mask |= std::uint64_t{1} << 24;
  if (expected.one_life_settlement != observed.one_life_settlement) mask |= std::uint64_t{1} << 25;
  return mask;
}
inline std::string TitleMapNavigationSnapshotDiffNamesV1(std::uint64_t mask) {
  std::string result = "[";
  if (mask & (std::uint64_t{1} << 0)) { if (result.size() > 1) result += ","; result += "\"date_raw\""; }
  if (mask & (std::uint64_t{1} << 1)) { if (result.size() > 1) result += ","; result += "\"speed\""; }
  if (mask & (std::uint64_t{1} << 2)) { if (result.size() > 1) result += ","; result += "\"paused\""; }
  if (mask & (std::uint64_t{1} << 3)) { if (result.size() > 1) result += ","; result += "\"player_id\""; }
  if (mask & (std::uint64_t{1} << 4)) { if (result.size() > 1) result += ","; result += "\"map_ready\""; }
  if (mask & (std::uint64_t{1} << 5)) { if (result.size() > 1) result += ","; result += "\"has_played_character\""; }
  if (mask & (std::uint64_t{1} << 6)) { if (result.size() > 1) result += ","; result += "\"played_character_id\""; }
  if (mask & (std::uint64_t{1} << 7)) { if (result.size() > 1) result += ","; result += "\"played_character_alive\""; }
  if (mask & (std::uint64_t{1} << 8)) { if (result.size() > 1) result += ","; result += "\"played_character_stress_points\""; }
  if (mask & (std::uint64_t{1} << 9)) { if (result.size() > 1) result += ","; result += "\"played_character_gold\""; }
  if (mask & (std::uint64_t{1} << 10)) { if (result.size() > 1) result += ","; result += "\"played_character_prestige\""; }
  if (mask & (std::uint64_t{1} << 11)) { if (result.size() > 1) result += ","; result += "\"played_character_piety\""; }
  if (mask & (std::uint64_t{1} << 12)) { if (result.size() > 1) result += ","; result += "\"played_character_betrothed_id\""; }
  if (mask & (std::uint64_t{1} << 13)) { if (result.size() > 1) result += ","; result += "\"played_character_primary_spouse_id\""; }
  if (mask & (std::uint64_t{1} << 14)) { if (result.size() > 1) result += ","; result += "\"played_character_spouse_ids\""; }
  if (mask & (std::uint64_t{1} << 15)) { if (result.size() > 1) result += ","; result += "\"has_active_event\""; }
  if (mask & (std::uint64_t{1} << 16)) { if (result.size() > 1) result += ","; result += "\"active_event_instance_id\""; }
  if (mask & (std::uint64_t{1} << 17)) { if (result.size() > 1) result += ","; result += "\"active_event_option_count\""; }
  if (mask & (std::uint64_t{1} << 18)) { if (result.size() > 1) result += ","; result += "\"has_pending_character_interaction\""; }
  if (mask & (std::uint64_t{1} << 19)) { if (result.size() > 1) result += ","; result += "\"pending_character_interaction_id\""; }
  if (mask & (std::uint64_t{1} << 20)) { if (result.size() > 1) result += ","; result += "\"pending_sender_character_id\""; }
  if (mask & (std::uint64_t{1} << 21)) { if (result.size() > 1) result += ","; result += "\"pending_auto_accept_notification\""; }
  if (mask & (std::uint64_t{1} << 22)) { if (result.size() > 1) result += ","; result += "\"active_wars\""; }
  if (mask & (std::uint64_t{1} << 23)) { if (result.size() > 1) result += ","; result += "\"player_armies\""; }
  if (mask & (std::uint64_t{1} << 24)) { if (result.size() > 1) result += ","; result += "\"has_one_life_settlement\""; }
  if (mask & (std::uint64_t{1} << 25)) { if (result.size() > 1) result += ","; result += "\"one_life_settlement\""; }
  return result + "]";
}
} // namespace xar::ck3_11906
