#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace xar::game {
struct PhaseEventCommanderSideIdentityOccurrenceV1 {
  std::uint32_t occurrence_index = 0;
  std::uint32_t character_id = 0;
  std::int32_t source_public_cunit_id = -1;
  std::optional<std::int32_t> source_native_carmy_id;
  std::string encounter_role;
  std::string status = "unavailable", unavailable_reason;
  std::optional<std::uint32_t> actual_physical_army_full_id_raw;
  std::optional<std::uint32_t> actual_selected_combat_full_id_raw;
  std::optional<bool> source_active_combat;
  std::optional<std::uint32_t> attacker_membership_count, defender_membership_count;
  std::optional<bool> unique_physical_membership;
  std::optional<std::uint32_t> actual_side_index;
  std::optional<std::string> actual_side_role;
  std::optional<bool> actual_side_parent_matches_selected_combat;
  std::optional<std::uint32_t> actual_side_commander_full_id_raw;
  std::optional<bool> actual_side_commander_present, full_id_equal;
  friend bool operator==(const PhaseEventCommanderSideIdentityOccurrenceV1 &,
                         const PhaseEventCommanderSideIdentityOccurrenceV1 &) = default;
};
struct PhaseEventCommanderSideIdentityV1 {
  std::string status = "unavailable", unavailable_reason;
  bool commander_side_identity_source_closed = false;
  std::string source_ck3_sha256 =
      "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
  std::vector<PhaseEventCommanderSideIdentityOccurrenceV1> occurrences;
  friend bool operator==(const PhaseEventCommanderSideIdentityV1 &,
                         const PhaseEventCommanderSideIdentityV1 &) = default;
};
} // namespace xar::game
