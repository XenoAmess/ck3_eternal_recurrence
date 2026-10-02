#pragma once

#include "xar_bridge/game_contract.hpp"

#include <algorithm>
#include <cstdint>
#include <initializer_list>
#include <limits>
#include <string_view>

namespace xar::ck3_11906 {

// Pure scope gate shared by the native reader and offline fixtures.  The
// control frame is itself required to be an available double-sampled frame.
inline const game::BattleControlRegimentEntrySnapshot *
SelectCurrentBattleKnightEntryV1(
    const game::BattleControlSnapshot &battle,
    const game::CurrentBattleKnightRequestV1 &request,
    std::string_view &failure) noexcept {
  failure = "battle_scope_invalid";
  if (battle.status != game::BattleControlSnapshotStatus::available ||
      !battle.battle_control_ready || request.subject_public_cunit_id <= 0 ||
      request.expected_played_character_id <= 0 ||
      request.expected_war_id < 0 ||
      request.expected_native_carmy_id <= 0 ||
      request.expected_combat_id == -1 ||
      request.expected_province_id <= 0 || request.expected_date_raw < 0 ||
      request.character_id <= 0 || request.regiment_id <= 0 ||
      battle.subject_public_cunit_id != request.subject_public_cunit_id ||
      battle.subject_native_carmy_id != request.expected_native_carmy_id ||
      battle.selected_owner_character_id !=
          request.expected_played_character_id ||
      battle.combat_id != request.expected_combat_id ||
      battle.combat_province_id != request.expected_province_id ||
      battle.province_id != request.expected_province_id ||
      battle.observed_date_raw != request.expected_date_raw) {
    return nullptr;
  }
  const game::BattleControlRegimentEntrySnapshot *selected = nullptr;
  for (const auto *side : {&battle.attacker, &battle.defender}) {
    for (const auto &entry : side->men_at_arms_entries) {
      if (entry.regiment_id != request.regiment_id) {
        continue;
      }
      if (selected != nullptr) {
        failure = "regiment_duplicate_in_battle";
        return nullptr;
      }
      selected = &entry;
    }
    for (const auto &entry : side->levy_entries) {
      if (entry.regiment_id == request.regiment_id) {
        failure = "regiment_not_knight_maa";
        return nullptr;
      }
    }
  }
  if (selected == nullptr) {
    failure = "regiment_outside_current_combat";
    return nullptr;
  }
  if (selected->bucket != "men_at_arms" ||
      selected->native_carmy_id != request.expected_native_carmy_id ||
      selected->public_cunit_id != request.subject_public_cunit_id ||
      selected->owner_character_id !=
          request.expected_played_character_id ||
      selected->knight_character_id_raw != request.character_id) {
    failure = "knight_regiment_pair_mismatch";
    return nullptr;
  }
  failure = {};
  return selected;
}

inline std::string_view CheckCurrentBattleKnightFormulaV1(
    std::int64_t effectiveness_raw, std::int32_t current_prowess,
    std::int64_t damage_per_prowess_raw,
    std::int64_t toughness_per_prowess_raw,
    std::int64_t fresh_damage_raw,
    std::int64_t fresh_toughness_raw) noexcept {
  if (effectiveness_raw < 0 || damage_per_prowess_raw < 0 ||
      toughness_per_prowess_raw < 0) {
    return "knight_effectiveness_unavailable";
  }
  const auto multiply = [](std::int64_t left, std::int64_t right,
                           std::int64_t &output) noexcept {
    if (left != 0 && right >
                         std::numeric_limits<std::int64_t>::max() / left) {
      return false;
    }
    output = left * right;
    return true;
  };
  std::int64_t per_prowess = 0;
  std::int64_t expected_damage = 0;
  std::int64_t expected_toughness = 0;
  if (!multiply(effectiveness_raw,
                std::max<std::int64_t>(1, current_prowess),
                per_prowess) ||
      !multiply(per_prowess, damage_per_prowess_raw,
                expected_damage) ||
      !multiply(per_prowess, toughness_per_prowess_raw,
                expected_toughness)) {
    return "knight_effectiveness_overflow";
  }
  return expected_damage == fresh_damage_raw &&
                 expected_toughness == fresh_toughness_raw
             ? std::string_view{}
             : "fresh_stats_knight_crosscheck_failed";
}

inline std::string_view CheckCurrentBattleKnightPairV1(
    const game::CurrentBattleKnightSnapshotV1 &first,
    const game::CurrentBattleKnightSnapshotV1 &second) noexcept {
  if (!first.available) {
    return first.unavailable_reason;
  }
  if (!second.available) {
    return second.unavailable_reason;
  }
  return first == second ? std::string_view{}
                         : "current_knight_double_sample_mismatch";
}

} // namespace xar::ck3_11906
