#include "xar_bridge/ck3_12003_battle_current_state.hpp"

#include <algorithm>
#include <cstring>
#include <limits>
#include <utility>
#include <vector>

namespace xar::ck3_12003 {
namespace {

using ck3_12002::BattleBindings;

template <typename T> T At(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset,
              sizeof(value));
  return value;
}

void *Resolve(void **slot, std::int32_t full_id,
              std::size_t identity_offset) noexcept {
  if (!slot || !*slot || full_id <= 0) return nullptr;
  const auto *storage = *slot;
  const auto *rows = At<const void *>(storage, 0x20);
  const auto capacity = At<std::int32_t>(storage, 0x2C);
  const auto index = static_cast<std::uint32_t>(full_id) & 0xFFFFFFU;
  if (!rows || capacity <= 0 || capacity > 1'000'000 ||
      index >= static_cast<std::uint32_t>(capacity)) return nullptr;
  auto *object = At<void *>(rows, static_cast<std::size_t>(index) * 0x10U + 8U);
  return object && At<std::int32_t>(object, identity_offset) == full_id
             ? object : nullptr;
}

bool Header(const void *object, std::size_t offset, const void *&data,
            std::int32_t &count) noexcept {
  data = At<const void *>(object, offset);
  const auto capacity = At<std::int32_t>(object, offset + 8U);
  count = At<std::int32_t>(object, offset + 12U);
  return count >= 0 && capacity >= count && capacity >= 0 && count <= 4096 &&
         (count == 0 || data != nullptr);
}

bool AddNonnegative(std::int64_t &total, std::int64_t value) noexcept {
  if (value < 0 || total > (std::numeric_limits<std::int64_t>::max)() - value)
    return false;
  total += value;
  return true;
}

bool SamePausedScope(const BattleBindings &bindings,
                     const game::Snapshot &scope) noexcept {
  return bindings.enabled && scope.paused && scope.map_ready &&
         bindings.game_state_slot && *bindings.game_state_slot &&
         bindings.jomini_state_slot && *bindings.jomini_state_slot &&
         At<std::int32_t>(*bindings.game_state_slot, 8U) == scope.date_raw &&
         At<std::uint8_t>(*bindings.jomini_state_slot, 0x20) != 0;
}

bool MatchesLifecycle(const BattleBindings &bindings, const void *combat,
                      const game::BattleTransitionSnapshot &transition) noexcept {
  if (At<std::uint8_t>(combat, ck3_12002::kBattleDailyGuardOffset) != 0 ||
      At<std::int32_t>(combat, ck3_12002::kBattlePhaseOffset) !=
          transition.phase_raw ||
      At<std::int32_t>(combat, ck3_12002::kBattlePhaseDayOffset) !=
          transition.phase_day ||
      At<std::int32_t>(combat, 0x6E0) != transition.winner_raw ||
      At<std::int32_t>(combat, 0x700) != transition.forced_winner_raw ||
      At<std::uint8_t>(combat, ck3_12002::kBattleFinalizedOffset) !=
          static_cast<std::uint8_t>(transition.finalized) ||
      At<std::int32_t>(combat, 0x708) != transition.battle_result_id)
    return false;
  auto *province = At<void *>(combat, 0x6B8);
  return province && bindings.resolve_province &&
         At<std::int32_t>(province, 0x10) == transition.province_id &&
         bindings.resolve_province(bindings.province_context,
                                   transition.province_id) == province;
}

bool ReadArmyIds(const BattleBindings &bindings, const void *combat,
                 const void *side, std::int32_t combat_id,
                 const std::vector<std::int32_t> &expected_public_ids,
                 std::vector<std::int32_t> &army_ids) {
  const void *data{};
  std::int32_t count{};
  if (At<const void *>(side, 0xB8) != combat ||
      !Header(side, 0x10, data, count) ||
      static_cast<std::size_t>(count) != expected_public_ids.size())
    return false;
  for (std::int32_t index = 0; index < count; ++index) {
    const auto army_id = At<std::int32_t>(
        data, static_cast<std::size_t>(index) * sizeof(std::int32_t));
    auto *army = Resolve(bindings.army_internal_storage_slot, army_id, 0x10);
    if (!army || At<std::int32_t>(army, 0x128) != combat_id ||
        std::find(army_ids.begin(), army_ids.end(), army_id) != army_ids.end())
      return false;
    const auto public_id = At<std::int32_t>(army, 0x124);
    auto *unit = Resolve(bindings.army_storage_slot, public_id, 0x10);
    if (!unit || At<std::int32_t>(unit, 0x178) != army_id ||
        public_id != expected_public_ids[static_cast<std::size_t>(index)] ||
        !Resolve(bindings.character_storage_slot,
                 At<std::int32_t>(unit, 0x174), 0x18))
      return false;
    army_ids.push_back(army_id);
  }
  return true;
}

bool ReadBucket(const BattleBindings &bindings, const void *side,
                std::size_t offset, const std::vector<std::int32_t> &army_ids,
                std::vector<std::int32_t> &seen_regiment_ids,
                game::BattleCurrentSideObservationSnapshotV1 &result) {
  const void *data{};
  std::int32_t count{};
  if (!Header(side, offset, data, count)) return false;
  for (std::int32_t index = 0; index < count; ++index) {
    const auto *entry = static_cast<const std::byte *>(data) +
                        static_cast<std::size_t>(index) * 0x60U;
    const auto regiment_id = At<std::int32_t>(entry, 8U);
    auto *regiment = Resolve(bindings.regiment_storage_slot, regiment_id, 0x10);
    if (!regiment || std::find(seen_regiment_ids.begin(), seen_regiment_ids.end(),
                              regiment_id) != seen_regiment_ids.end() ||
        std::find(army_ids.begin(), army_ids.end(),
                  At<std::int32_t>(regiment, 0x140)) == army_ids.end())
      return false;
    const auto *type = At<const void *>(regiment, 0x18);
    if (!type) return false;
    const auto main_eligible = At<std::uint8_t>(
        type, ck3_12002::kBattleMainPhaseTypeFlag);
    if (main_eligible > 1) return false;
    const auto starting = At<std::int64_t>(entry, 0x10);
    const auto current = At<std::int64_t>(entry, 0x18);
    const auto soft = At<std::int64_t>(entry, 0x20);
    if (starting < 0 || current < 0 || soft < 0 || current > starting ||
        soft > starting - current) return false;
    const auto residual = starting - current - soft;
    if (!AddNonnegative(result.derived_current_fighting_raw, current) ||
        !AddNonnegative(result.derived_soft_casualties_raw, soft) ||
        !AddNonnegative(main_eligible != 0
                            ? result.derived_main_fighting_entry_hard_casualties_raw
                            : result.non_main_start_minus_current_minus_soft_raw,
                        residual)) return false;
    seen_regiment_ids.push_back(regiment_id);
  }
  return true;
}

bool ReadSide(const BattleBindings &bindings, const void *combat,
              std::size_t side_offset, std::int32_t combat_id,
              const std::vector<std::int32_t> &expected_public_ids,
              game::BattleCurrentSideObservationSnapshotV1 &result) {
  const auto *side = static_cast<const std::byte *>(combat) + side_offset;
  std::vector<std::int32_t> army_ids;
  std::vector<std::int32_t> seen_regiment_ids;
  if (!ReadArmyIds(bindings, combat, side, combat_id, expected_public_ids,
                   army_ids) ||
      !ReadBucket(bindings, side, 0x28, army_ids, seen_regiment_ids, result) ||
      !ReadBucket(bindings, side, 0x40, army_ids, seen_regiment_ids, result))
    return false;
  const void *data{};
  std::int32_t count{};
  if (!Header(side, 0x58, data, count)) return false;
  for (std::int32_t index = 0; index < count; ++index) {
    const auto *row = static_cast<const std::byte *>(data) +
                      static_cast<std::size_t>(index) * 0x18U;
    game::BattleCurrentParticipantHardSnapshotV1 participant{
        At<std::int32_t>(row, 8U), At<std::int64_t>(row, 0x10)};
    if (!Resolve(bindings.character_storage_slot,
                 participant.participant_character_id, 0x18) ||
        !AddNonnegative(result.participant_hard_total_raw,
                        participant.hard_casualties_raw)) return false;
    result.participant_hard_ledger.push_back(participant);
  }
  return true;
}

bool Sample(const BattleBindings &bindings,
            const game::BattleTransitionSnapshot &transition,
            game::BattleCurrentObservationSnapshotV1 &result,
            const char *&reason) {
  auto *combat = Resolve(bindings.combat_storage_slot, transition.combat_id, 8U);
  if (!combat || !MatchesLifecycle(bindings, combat, transition)) {
    reason = "current_combat_or_lifecycle_changed";
    return false;
  }
  result.base_combat_width = At<std::int32_t>(combat, 0x6C0);
  result.final_combat_width = At<std::int32_t>(combat, 0x6C4);
  result.base_advantage_raw = At<std::int64_t>(combat, 0x6C8);
  result.resolved_advantage_raw = At<std::int64_t>(combat, 0x710);
  if (result.base_combat_width < 0 || result.final_combat_width < 0 ||
      !ReadSide(bindings, combat, ck3_12002::kBattleAttackerSideOffset,
                 transition.combat_id,
                 transition.attacker_public_cunit_ids_in_stored_order,
                 result.attacker) ||
      !ReadSide(bindings, combat, ck3_12002::kBattleDefenderSideOffset,
                 transition.combat_id,
                 transition.defender_public_cunit_ids_in_stored_order,
                 result.defender)) {
    reason = "combat_side_graph_or_casualty_totals_unavailable";
    return false;
  }
  if (Resolve(bindings.combat_storage_slot, transition.combat_id, 8U) != combat ||
      !MatchesLifecycle(bindings, combat, transition)) {
    reason = "current_combat_or_lifecycle_changed";
    return false;
  }
  result.available = true;
  return true;
}

void ReadOwnerRecallTarget(const BattleBindings &bindings, const void *land,
                          game::BattleNativeOwnerRecallOwnerInputsV1 &owner) {
  const auto source_title_id = At<std::int32_t>(land, 0x1F8);
  if (source_title_id == -1) {
    owner.target_status = "fallback_title_selection_unread_28B2220";
    return;
  }
  owner.owner_target_source_title_id = source_title_id;
  if (!bindings.native_owner_recall_title_storage_slot) {
    owner.target_status = "title_storage_unbound";
    return;
  }
  auto title_id = source_title_id;
  std::vector<std::int32_t> seen;
  for (;;) {
    auto *title = Resolve(bindings.native_owner_recall_title_storage_slot,
                          title_id, 0x10);
    if (!title) {
      owner.target_status = "source_title_unresolved";
      return;
    }
    const auto *type = At<const void *>(title, 0x48);
    if (!type) {
      owner.target_status = "title_type_unavailable";
      return;
    }
    if (At<std::int32_t>(type, 0x64) != 2) {
      auto *province = At<void *>(title, 0x338);
      if (!province || !bindings.resolve_province) {
        owner.target_status = "title_province_unavailable";
        return;
      }
      const auto province_id = At<std::int32_t>(province, 0x10);
      if (bindings.resolve_province(bindings.province_context, province_id) !=
          province) {
        owner.target_status = "title_province_unresolved";
        return;
      }
      owner.owner_native_recall_target_province_id = province_id;
      owner.target_status = "available_owner_land_1F8";
      return;
    }
    if (std::find(seen.begin(), seen.end(), title_id) != seen.end()) {
      owner.target_status = "title_child_chain_repeated";
      return;
    }
    seen.push_back(title_id);
    const auto *children = At<const void *>(title, 0x110);
    if (!children || At<std::int32_t>(title, 0x11C) == 0) {
      owner.target_status = "type2_first_child_unavailable";
      return;
    }
    title_id = At<std::int32_t>(children, 0);
  }
}

void ReadActivityContextEPrefix(
    const BattleBindings &bindings, const void *game_data,
    const void *context, const void *character,
    game::BattleNativeActivityContextMatchV1 &result) {
  const auto finish = [&result](bool admitted) {
    result.status = "available";
    result.unavailable_reason.clear();
    result.e_prefix_admitted = admitted;
  };
  result.context_16_raw = At<std::uint8_t>(context, 0x16);
  if ((*result.context_16_raw & 2U) == 0) {
    finish(false);
    return;
  }
  result.context_state_raw = At<std::int32_t>(context, 0x10);
  if (*result.context_state_raw < 2) {
    finish(false);
    return;
  }
  const auto *land = At<const void *>(character, 0x1C0);
  if (!land) {
    finish(false);
    return;
  }

  const void *government{};
  if (At<std::uint32_t>(character, 0x1C) == 0x43686172U &&
      At<std::int32_t>(character, 0x18) != -1) {
    const auto *death_data = At<const void *>(character, 0x1D0);
    government = death_data ? At<const void *>(death_data, 0x88)
                            : At<const void *>(land, 0x3F8);
  }
  if (!government) {
    if (!bindings.native_activity_context_government_fallback_slot ||
        !*bindings.native_activity_context_government_fallback_slot) {
      result.unavailable_reason = "government_fallback_unavailable";
      return;
    }
    government = *bindings.native_activity_context_government_fallback_slot;
  }
  if (At<std::uint32_t>(government, 0x38) != 0x4744624FU) {
    finish(false);
    return;
  }
  result.government_flags_40_raw = At<std::uint64_t>(government, 0x40);
  if ((*result.government_flags_40_raw & (std::uint64_t{1} << 41)) == 0) {
    finish(false);
    return;
  }
  result.context_2e_raw = At<std::uint8_t>(context, 0x2E);
  if (*result.context_2e_raw == 0) {
    finish(true);
    return;
  }

  const auto *rows = At<const void *>(game_data, 0x22340);
  const auto count = At<std::int32_t>(game_data, 0x2234C);
  if (count < 0 || (count != 0 && !rows)) {
    result.unavailable_reason = "plin_membership_unavailable";
    return;
  }
  const void *selected_plin{};
  for (std::int32_t i = 0; i < count; ++i) {
    const auto *plin = At<const void *>(
        rows, static_cast<std::size_t>(i) * sizeof(void *));
    if (!plin) {
      result.unavailable_reason = "plin_membership_element_unavailable";
      return;
    }
    if (At<std::int32_t>(plin, 0xB0) == result.actor_character_id) {
      selected_plin = plin;
      break;
    }
  }
  if (!selected_plin) {
    if (!bindings.native_activity_context_plin_fallback_slot ||
        !*bindings.native_activity_context_plin_fallback_slot) {
      result.unavailable_reason = "plin_fallback_unavailable";
      return;
    }
    selected_plin = *bindings.native_activity_context_plin_fallback_slot;
  }
  if (At<std::uint32_t>(selected_plin, 0xDC) != 0x506C496EU ||
      At<std::int32_t>(selected_plin, 0xD8) == -1) {
    finish(false);
    return;
  }
  result.plin_flags_2f0_raw = At<std::uint16_t>(selected_plin, 0x2F0);
  finish((*result.plin_flags_2f0_raw & (std::uint16_t{1} << 8)) != 0);
}

bool ReadActivityContextCollection(
    const BattleBindings &bindings, const void *game_data, const void *manager,
    std::size_t pointer_offset, std::size_t count_offset,
    const char *collection, std::int32_t owner_id,
    game::BattleNativeActivityContextV1 &result) {
  const auto *rows = At<const void *>(manager, pointer_offset);
  const auto count = At<std::int32_t>(manager, count_offset);
  if (count < 0 || (count != 0 && !rows)) return false;
  bool membership_observed = true;
  for (std::int32_t i = 0; i < count; ++i) {
    const auto *context = At<const void *>(
        rows, static_cast<std::size_t>(i) * sizeof(void *));
    if (!context) {
      membership_observed = false;
      continue;
    }
    const auto *character = At<const void *>(context, 0x18);
    if (!character) {
      membership_observed = false;
      continue;
    }
    const auto actor_id = At<std::int32_t>(character, 0x18);
    if (actor_id != owner_id) continue;
    game::BattleNativeActivityContextMatchV1 match{};
    match.collection = collection;
    match.stored_index = i;
    match.actor_character_id = actor_id;
    ReadActivityContextEPrefix(bindings, game_data, context, character, match);
    result.matched_contexts_in_native_order.push_back(std::move(match));
  }
  return membership_observed;
}


void ReadOwnerRecallInputs(const BattleBindings &bindings,
                          std::int32_t owner_id,
                          game::BattleNativeOwnerRecallOwnerInputsV1 &result) {
  result.owner_character_id = owner_id;
  if (bindings.native_activity_context_source_enabled)
    result.native_activity_context_v1 =
        ReadOwnerNativeActivityContextInputsV1(bindings, owner_id);
  auto *character = Resolve(bindings.character_storage_slot, owner_id, 0x18);
  if (!character) return;
  const auto *land = At<const void *>(character, 0x1C0);
  if (!land) return;
  // Source 1A7BB06/1A7E068 uses count!=0, not count>0.
  result.land_318_count_raw = At<std::int32_t>(land, 0x324);
  ReadOwnerRecallTarget(bindings, land, result);
  const void *data{};
  std::int32_t count{};
  if (!Header(land, 0x278, data, count)) {
    result.owned_cunit_roster_status = "owner_cunit_header_unavailable";
    return;
  }
  result.owned_cunit_roster_status = "available";
  result.raw_inputs_ready = true;
  for (std::int32_t i = 0; i < count; ++i) {
    game::BattleNativeOwnerRecallUnitInputsV1 unit_result{};
    const auto public_id = At<std::int32_t>(data, static_cast<std::size_t>(i) * 4U);
    unit_result.public_cunit_id = public_id;
    auto *unit = Resolve(bindings.army_storage_slot, public_id, 0x10);
    if (unit) {
      const auto receiver_owner = At<std::int32_t>(unit, 0x174);
      if (Resolve(bindings.character_storage_slot, receiver_owner, 0x18))
        unit_result.receiver_owner_character_id = receiver_owner;
      const auto army_id = At<std::int32_t>(unit, 0x178);
      auto *army = Resolve(bindings.army_internal_storage_slot, army_id, 0x10);
      unit_result.status = "army_unresolved";
      if (army) {
        unit_result.status = "available";
        unit_result.native_carmy_id = army_id;
        const auto combat_id = At<std::int32_t>(army, 0x128);
        if (Resolve(bindings.combat_storage_slot, combat_id, 8U))
          unit_result.attached_combat_id = combat_id;
        auto *province = At<void *>(unit, 0x20);
        if (province && bindings.resolve_province) {
          const auto province_id = At<std::int32_t>(province, 0x10);
          if (bindings.resolve_province(bindings.province_context, province_id) ==
              province) unit_result.current_province_id = province_id;
        }
        unit_result.army_1d4_raw = At<std::uint8_t>(army, 0x1D4);
        unit_result.army_1ec_raw = At<std::uint8_t>(army, 0x1EC);
      }
    }
    unit_result.first_fallback_raw_condition = OwnerRecallFallbackRawConditionV1(
        result.land_318_count_raw, unit_result.army_1d4_raw);
    unit_result.second_fallback_raw_condition = OwnerRecallFallbackRawConditionV1(
        result.land_318_count_raw, unit_result.army_1ec_raw);
    result.raw_inputs_ready = result.raw_inputs_ready &&
        unit_result.status == "available" &&
        unit_result.receiver_owner_character_id.has_value();
    result.owned_cunits_in_stored_order.push_back(std::move(unit_result));
  }
}

bool SampleOwnerRecallInputs(const BattleBindings &bindings,
                            const game::BattleTransitionSnapshot &transition,
                            game::BattleNativeOwnerRecallInputsV1 &result,
                            const char *&reason) {
  auto *combat = Resolve(bindings.combat_storage_slot, transition.combat_id, 8U);
  if (!combat || !MatchesLifecycle(bindings, combat, transition)) {
    reason = "current_combat_or_lifecycle_changed";
    return false;
  }
  std::vector<std::int32_t> army_ids;
  if (!ReadArmyIds(bindings, combat,
        static_cast<const std::byte *>(combat) + ck3_12002::kBattleAttackerSideOffset,
        transition.combat_id, transition.attacker_public_cunit_ids_in_stored_order,
        army_ids) ||
      !ReadArmyIds(bindings, combat,
        static_cast<const std::byte *>(combat) + ck3_12002::kBattleDefenderSideOffset,
        transition.combat_id, transition.defender_public_cunit_ids_in_stored_order,
        army_ids)) {
    reason = "combat_owner_roster_unavailable";
    return false;
  }
  std::vector<std::int32_t> owner_ids;
  result.raw_inputs_ready = true;
  for (const auto army_id : army_ids) {
    auto *army = Resolve(bindings.army_internal_storage_slot, army_id, 0x10);
    auto *unit = Resolve(bindings.army_storage_slot,
                        At<std::int32_t>(army, 0x124), 0x10);
    const auto owner_id = At<std::int32_t>(unit, 0x174);
    if (std::find(owner_ids.begin(), owner_ids.end(), owner_id) != owner_ids.end())
      continue;
    owner_ids.push_back(owner_id);
    game::BattleNativeOwnerRecallOwnerInputsV1 owner{};
    ReadOwnerRecallInputs(bindings, owner_id, owner);
    result.raw_inputs_ready = result.raw_inputs_ready && owner.raw_inputs_ready;
    result.owners_in_stored_order.push_back(std::move(owner));
  }
  if (!MatchesLifecycle(bindings, combat, transition)) {
    reason = "current_combat_or_lifecycle_changed";
    return false;
  }
  result.available = true;
  return true;
}
} // namespace

void AttachBattleCurrentObservationV1(
    const ck3_12002::BattleBindings &bindings,
    const game::Snapshot &paused_scope,
    game::BattleTransitionSnapshot &transition) noexcept {
  transition.current_observation.reset();
  if (transition.status != game::BattleTransitionSnapshotStatus::available ||
      !transition.battle_transition_ready) return;
  game::BattleCurrentObservationSnapshotV1 unavailable{};
  unavailable.unavailable_reason = "paused_exact_combat_scope_unavailable";
  try {
    if (transition.observed_date_raw != paused_scope.date_raw ||
        !SamePausedScope(bindings, paused_scope)) {
      transition.current_observation = std::move(unavailable);
      return;
    }
    game::BattleCurrentObservationSnapshotV1 first{}, second{};
    const char *reason = "current_combat_observation_changed";
    if (!Sample(bindings, transition, first, reason) ||
        !Sample(bindings, transition, second, reason)) {
      unavailable.unavailable_reason = reason;
    } else if (first != second || !SamePausedScope(bindings, paused_scope)) {
      unavailable.unavailable_reason = "current_combat_observation_changed";
    } else {
      transition.current_observation = std::move(second);
      return;
    }
  } catch (...) {
    unavailable.unavailable_reason = "current_combat_observation_unavailable";
  }
  transition.current_observation = std::move(unavailable);
}

game::BattleNativeOwnerPrefixInputsV1 ReadOwnerNativePrefixInputsV1(
    const ck3_12002::BattleBindings &bindings, std::int32_t owner_id) noexcept {
  game::BattleNativeOwnerPrefixInputsV1 result{};
  try {
    if (!bindings.enabled || !bindings.native_activity_context_source_enabled ||
        owner_id <= 0) {
      result.unavailable_reason = "independent_owner_source_unbound";
      return result;
    }
    const auto *character = Resolve(bindings.character_storage_slot, owner_id, 0x18);
    if (!character) {
      result.unavailable_reason = "independent_owner_character_unavailable";
      return result;
    }
    const auto *land = At<const void *>(character, 0x1C0);
    result.owner_land_present = land != nullptr;
    if (!land) result.owner_necessary_condition = false;

    const void *government{};
    bool government_expression_observed = true;
    if (At<std::uint32_t>(character, 0x1C) == 0x43686172U &&
        At<std::int32_t>(character, 0x18) != -1) {
      const auto *death_data = At<const void *>(character, 0x1D0);
      if (death_data) government = At<const void *>(death_data, 0x88);
      else if (land) government = At<const void *>(land, 0x3F8);
      else {
        // The getter's nonlanded receiver chain is outside this owner path.
        government_expression_observed = false;
        result.government_status = "owner_land_absent";
      }
    }
    if (government_expression_observed && !government &&
        bindings.native_activity_context_government_fallback_slot)
      government = *bindings.native_activity_context_government_fallback_slot;
    if (government) {
      if (At<std::uint32_t>(government, 0x38) != 0x4744624FU) {
        result.government_status = "invalid_magic";
        result.owner_necessary_condition = false;
      } else {
        result.government_flags_40_raw = At<std::uint64_t>(government, 0x40);
        result.government_bit41 =
            (*result.government_flags_40_raw & (std::uint64_t{1} << 41)) != 0;
        result.owner_necessary_condition = land != nullptr && *result.government_bit41;
        result.government_status = "available";
      }
    }

    // Observe PlIn independently even when the government's bit41 is false.
    // This does not claim that native E(context) traversed its PlIn branch.
    const void *game_data{};
    if (bindings.game_state_slot && *bindings.game_state_slot)
      game_data = At<const void *>(*bindings.game_state_slot, 0xA0);
    const void *selected_plin{};
    bool plin_membership_observed = false;
    if (game_data) {
      const auto *rows = At<const void *>(game_data, 0x22340);
      const auto count = At<std::int32_t>(game_data, 0x2234C);
      plin_membership_observed = count >= 0 && (count == 0 || rows != nullptr);
      if (plin_membership_observed) {
        for (std::int32_t i = 0; i < count; ++i) {
          const auto *plin = At<const void *>(
              rows, static_cast<std::size_t>(i) * sizeof(void *));
          if (!plin) {
            plin_membership_observed = false;
            break;
          }
          if (At<std::int32_t>(plin, 0xB0) == owner_id) {
            selected_plin = plin;
            result.plin_selection = "owner_first_match";
            break;
          }
        }
      }
    }
    if (plin_membership_observed && !selected_plin) {
      result.plin_selection = "native_fallback";
      if (bindings.native_activity_context_plin_fallback_slot)
        selected_plin = *bindings.native_activity_context_plin_fallback_slot;
    }
    if (plin_membership_observed && selected_plin) {
      if (At<std::uint32_t>(selected_plin, 0xDC) != 0x506C496EU ||
          At<std::int32_t>(selected_plin, 0xD8) == -1) {
        result.plin_status = "invalid_identity_native_literal5";
        result.plin_bit8 = false;
      } else {
        result.plin_flags_2f0_raw = At<std::uint16_t>(selected_plin, 0x2F0);
        result.plin_bit8 = (*result.plin_flags_2f0_raw & (std::uint16_t{1} << 8)) != 0;
        result.plin_status = "available";
      }
    }
    const bool government_observed =
        result.government_status == "available" || result.government_status == "invalid_magic";
    const bool plin_observed = result.plin_status == "available" ||
                              result.plin_status == "invalid_identity_native_literal5";
    if (government_observed && plin_observed) {
      result.status = "available";
      result.unavailable_reason.clear();
    } else if (!government_observed && plin_observed) {
      result.unavailable_reason = "independent_owner_government_unavailable";
    } else if (government_observed && !plin_observed) {
      result.unavailable_reason = "independent_owner_plin_unavailable";
    }
  } catch (...) {
    result.status = "unavailable";
    result.unavailable_reason = "independent_owner_operands_unavailable";
  }
  return result;
}

game::BattleNativeActivityContextV1 ReadOwnerNativeActivityContextInputsV1(
    const ck3_12002::BattleBindings &bindings, std::int32_t owner_id) noexcept {
  game::BattleNativeActivityContextV1 result{};
  try {
    if (!bindings.enabled || !bindings.native_activity_context_source_enabled) {
      result.unavailable_reason = "activity_context_source_unbound";
      return result;
    }
    result.owner_prefix_inputs = ReadOwnerNativePrefixInputsV1(bindings, owner_id);
    if (owner_id <= 0 || !bindings.game_state_slot ||
        !*bindings.game_state_slot) {
      result.unavailable_reason = "activity_context_game_state_unavailable";
      return result;
    }
    const auto *game_data = At<const void *>(*bindings.game_state_slot, 0xA0);
    if (!game_data) {
      result.unavailable_reason = "activity_context_game_data_unavailable";
      return result;
    }
    const auto *manager = static_cast<const std::byte *>(game_data) + 0x2D48;
    const auto fallback_observed = ReadActivityContextCollection(
        bindings, game_data, manager, 0xD8, 0xE4, "fallback_d8", owner_id, result);
    const auto mission_observed = ReadActivityContextCollection(
        bindings, game_data, manager, 0x90, 0x9C, "mission_90", owner_id, result);
    result.membership_observed = fallback_observed && mission_observed;
    if (!result.membership_observed) {
      result.unavailable_reason = "activity_context_membership_unavailable";
      return result;
    }
    if (std::any_of(result.matched_contexts_in_native_order.begin(),
                    result.matched_contexts_in_native_order.end(),
                    [](const auto &match) {
                      return match.status != "available";
                    })) {
      result.unavailable_reason = "e_prefix_operands_unavailable";
      return result;
    }
    result.status = "available";
    result.unavailable_reason.clear();
  } catch (...) {
    result = {};
    result.unavailable_reason = "native_activity_context_unavailable";
  }
  return result;
}


void EnableBattleNativeOwnerRecallInputs12003(
    ck3_12002::BattleBindings &bindings, std::uintptr_t image_base,
    std::string_view executable_sha256) noexcept {
  bindings.native_owner_recall_title_storage_slot = nullptr;
  bindings.native_activity_context_source_enabled = false;
  bindings.native_activity_context_government_fallback_slot = nullptr;
  bindings.native_activity_context_plin_fallback_slot = nullptr;
  if (image_base != 0 && executable_sha256 ==
      "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6") {
    // New source 28B1CDE /230F90A exact .3 TitleStorage pointer slot.
    bindings.native_owner_recall_title_storage_slot =
        reinterpret_cast<void **>(image_base + 0x5D1DAF8);
    // 28C2E10 and 1A78257 exact .3 raw government/PlIn fallback slots.
    bindings.native_activity_context_government_fallback_slot =
        reinterpret_cast<void **>(image_base + 0x5D1E2A8);
    bindings.native_activity_context_plin_fallback_slot =
        reinterpret_cast<void **>(image_base + 0x5D29008);
    bindings.native_activity_context_source_enabled = true;
  }
}

void AttachBattleNativeOwnerRecallInputsV1(
    const ck3_12002::BattleBindings &bindings,
    const game::Snapshot &paused_scope,
    game::BattleTransitionSnapshot &transition) noexcept {
  transition.native_owner_recall_inputs_v1.reset();
  if (transition.status != game::BattleTransitionSnapshotStatus::available ||
      !transition.battle_transition_ready) return;
  game::BattleNativeOwnerRecallInputsV1 result{};
  result.unavailable_reason = "paused_exact_combat_scope_unavailable";
  try {
    if (transition.observed_date_raw == paused_scope.date_raw &&
        SamePausedScope(bindings, paused_scope)) {
      const char *reason = "owner_recall_inputs_unavailable";
      if (!SampleOwnerRecallInputs(bindings, transition, result, reason) ||
          !SamePausedScope(bindings, paused_scope)) {
        result = {};
        result.unavailable_reason = reason;
      } else {
        result.unavailable_reason.clear();
      }
    }
  } catch (...) {
    result = {};
    result.unavailable_reason = "owner_recall_inputs_unavailable";
  }
  transition.native_owner_recall_inputs_v1 = std::move(result);
}

void AttachBattleNativeOwnerRecallInputsForUnitsV1(
    const ck3_12002::BattleBindings &bindings,
    const game::Snapshot &paused_scope,
    const std::vector<std::int32_t> &public_cunit_ids,
    game::BattleNativeOwnerRecallInputsV1 &result) noexcept {
  result = {};
  result.unavailable_reason = "paused_exact_unit_scope_unavailable";
  try {
    if (!SamePausedScope(bindings, paused_scope)) return;
    std::vector<std::int32_t> owner_ids;
    result.raw_inputs_ready = true;
    for (const auto public_id : public_cunit_ids) {
      auto *unit = Resolve(bindings.army_storage_slot, public_id, 0x10);
      if (!unit) {
        result = {};
        result.unavailable_reason = "scoped_public_unit_unresolved";
        return;
      }
      const auto owner_id = At<std::int32_t>(unit, 0x174);
      if (!Resolve(bindings.character_storage_slot, owner_id, 0x18)) {
        result = {};
        result.unavailable_reason = "scoped_unit_owner_unresolved";
        return;
      }
      if (std::find(owner_ids.begin(), owner_ids.end(), owner_id) != owner_ids.end())
        continue;
      owner_ids.push_back(owner_id);
      game::BattleNativeOwnerRecallOwnerInputsV1 owner{};
      ReadOwnerRecallInputs(bindings, owner_id, owner);
      result.raw_inputs_ready = result.raw_inputs_ready && owner.raw_inputs_ready;
      result.owners_in_stored_order.push_back(std::move(owner));
    }
    if (!SamePausedScope(bindings, paused_scope)) {
      result = {};
      result.unavailable_reason = "current_unit_scope_changed";
      return;
    }
    result.available = true;
    result.unavailable_reason.clear();
  } catch (...) {
    result = {};
    result.unavailable_reason = "owner_recall_inputs_unavailable";
  }
}
} // namespace xar::ck3_12003
