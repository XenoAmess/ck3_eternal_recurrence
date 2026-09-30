#pragma once

#include <cstdint>
#include <cstddef>
#include <optional>
#include <string>
#include <vector>

namespace xar::bridge::h2743 {

// Evidence from a complete WarManager slot traversal. This is deliberately
// separate from the stock any_character_war condition and cannot authorize an
// exit or supply the actual directed-truce duration.
enum class SlotState : std::uint8_t { empty, ended, active };

struct WarSlot {
  std::int32_t index = -1;
  SlotState state = SlotState::empty;
  std::int32_t war_id = -1;
  std::uintptr_t object_address = 0;
  std::int32_t primary_attacker = -1;
  std::int32_t primary_defender = -1;
  std::int32_t cb_index = -1;
  std::uintptr_t cb_address = 0;
  std::string cb_key;
  bool primary_attacker_in_participants = false;
  bool primary_defender_in_participants = false;
  friend bool operator==(const WarSlot &, const WarSlot &) = default;
};

struct CompleteScan {
  std::int32_t capacity = 0;
  std::vector<WarSlot> slots;
  friend bool operator==(const CompleteScan &, const CompleteScan &) = default;
};

struct Candidate {
  bool border_raid_pair = false;
  std::int32_t active_wars = 0;
  std::int32_t matching_wars = 0;
};

// Invalid, partial, or drifting scans return nullopt, including attempts to
// prove false by looking only at the played defender's wars.
inline std::optional<Candidate> AdmitStableWarStorageCandidate(
    const CompleteScan &first, const CompleteScan &second,
    std::int32_t target_war_id, std::uintptr_t target_war_address,
    std::int32_t attacker_id, std::int32_t defender_id,
    std::int32_t target_cb_index, const std::string &target_cb_key) {
  constexpr std::int32_t kMaximumCapacity = 1'000'000;
  if (first != second || first.capacity <= 0 ||
      first.capacity > kMaximumCapacity ||
      first.slots.size() != static_cast<std::size_t>(first.capacity) ||
      target_war_id <= 0 || target_war_address == 0 || attacker_id <= 0 ||
      defender_id <= 0 || attacker_id == defender_id ||
      target_cb_index < 0 || target_cb_key.empty()) return std::nullopt;
  Candidate result{};
  std::int32_t target_rows = 0;
  for (std::int32_t index = 0; index < first.capacity; ++index) {
    const auto &row = first.slots[static_cast<std::size_t>(index)];
    if (row.index != index) return std::nullopt;
    if (row.state == SlotState::empty) {
      if (row.war_id != -1 || row.object_address != 0) return std::nullopt;
      continue;
    }
    if (row.war_id <= 0 || row.object_address == 0 ||
        (static_cast<std::uint32_t>(row.war_id) & 0x00FFFFFFU) !=
            static_cast<std::uint32_t>(index)) return std::nullopt;
    if (row.state == SlotState::ended) continue;
    if (row.state != SlotState::active || row.primary_attacker <= 0 ||
        row.primary_defender <= 0 ||
        row.primary_attacker == row.primary_defender || row.cb_index < 0 ||
        row.cb_index >= 10'000 || row.cb_address == 0 || row.cb_key.empty() ||
        !row.primary_attacker_in_participants ||
        !row.primary_defender_in_participants) return std::nullopt;
    ++result.active_wars;
    if (row.war_id == target_war_id) {
      ++target_rows;
      if (row.object_address != target_war_address ||
          row.primary_attacker != attacker_id ||
          row.primary_defender != defender_id ||
          row.cb_index != target_cb_index || row.cb_key != target_cb_key)
        return std::nullopt;
    }
    if (row.primary_attacker == attacker_id &&
        row.primary_defender == defender_id &&
        row.cb_key == "fp2_border_raid") ++result.matching_wars;
  }
  if (target_rows != 1) return std::nullopt;
  result.border_raid_pair = result.matching_wars > 0;
  return result;
}

}  // namespace xar::bridge::h2743
