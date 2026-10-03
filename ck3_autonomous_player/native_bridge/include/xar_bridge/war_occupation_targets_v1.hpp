#pragma once

#include <cstdint>
#include <string_view>
#include <vector>

namespace xar::game {

inline constexpr std::string_view kWarOccupationTargetsV1Capability =
    "game.command.query-war-occupation-targets-v1-N";

struct WarOccupationTargetRowV1 {
  // The native collector returns barony CLandedTitle pointers. This full title
  // ID is the holding identity; no invented second CHolding ID is published.
  std::int32_t holding_title_id = -1;
  std::int32_t province_id = -1;
  std::int32_t legal_holder_character_id = -1;
  std::string_view territory_side = "unavailable"; // attacker / defender
  bool occupation_observable = false;
  bool is_occupied = false;
  std::int32_t occupying_character_id = -1; // absent iff not occupied
  std::string_view occupier_side = "unavailable";
  // occupier_side: attacker / defender / outside_war / none / unavailable.
  bool counted_occupied_by_opposing_side = false;
};

struct WarOccupationSideCountsV1 {
  // This names the territory side, whose land is eligible. "occupied" counts
  // eligible land occupied by the opposing participant side in the real native
  // counter, rather than every geographically occupied province.
  std::string_view territory_side = "unavailable";
  std::int32_t eligible = 0;
  std::int32_t occupied = 0;
  std::int32_t native_candidate_count = 0;
  bool collection_complete = false;
};

struct WarOccupationTargetsSnapshotV1 {
  bool available = false;
  std::string_view unavailable_reason = "not_read";
  std::int32_t date_raw = 0;
  std::int32_t actor_character_id = -1;
  std::int32_t war_id = -1;
  std::string_view player_side = "unavailable";
  std::int32_t primary_attacker_character_id = -1;
  std::int32_t primary_defender_character_id = -1;
  bool collection_complete = false;
  std::vector<WarOccupationSideCountsV1> side_counts;
  std::vector<WarOccupationTargetRowV1> rows;
};

using WarOccupationTargetsV1 = WarOccupationTargetsSnapshotV1;
enum class ReadWarOccupationTargetsV1Result { unavailable, available };

} // namespace xar::game
