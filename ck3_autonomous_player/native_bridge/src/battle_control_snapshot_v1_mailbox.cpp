#include "xar_bridge/battle_control_snapshot_v1_mailbox.hpp"

#include <windows.h>

#include <algorithm>
#include <array>
#include <atomic>
#include <charconv>
#include <limits>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_11906 {
namespace {

template <typename Value>
bool AppendNumber(std::string &output, Value value) {
  std::array<char, 32> buffer{};
  const auto encoded =
      std::to_chars(buffer.data(), buffer.data() + buffer.size(), value);
  if (encoded.ec != std::errc{}) {
    return false;
  }
  output.append(buffer.data(), encoded.ptr);
  return true;
}

void AppendJsonString(std::string &output, std::string_view value) {
  constexpr char hex[] = "0123456789ABCDEF";
  output.push_back('"');
  for (const unsigned char character : value) {
    if (character == '"' || character == '\\') {
      output.push_back('\\');
      output.push_back(static_cast<char>(character));
    } else if (character < 0x20U) {
      output += "\\u00";
      output.push_back(hex[(character >> 4U) & 0x0FU]);
      output.push_back(hex[character & 0x0FU]);
    } else {
      output.push_back(static_cast<char>(character));
    }
  }
  output.push_back('"');
}

bool ParseCanonicalPositiveInt32(std::string_view text,
                                 std::int32_t &output) noexcept {
  output = -1;
  if (text.empty() || text.front() == '0') {
    return false;
  }
  std::int32_t value = -1;
  const auto parsed =
      std::from_chars(text.data(), text.data() + text.size(), value);
  if (parsed.ec != std::errc{} || parsed.ptr != text.data() + text.size() ||
      value <= 0) {
    return false;
  }
  char canonical[16]{};
  const auto rendered =
      std::to_chars(canonical, canonical + sizeof(canonical), value);
  if (rendered.ec != std::errc{} ||
      std::string_view(canonical, rendered.ptr) != text) {
    return false;
  }
  output = value;
  return true;
}

bool CheckedAdd(std::int64_t left, std::int64_t right,
                std::int64_t &output) noexcept {
  if ((right > 0 &&
       left > std::numeric_limits<std::int64_t>::max() - right) ||
      (right < 0 &&
       left < std::numeric_limits<std::int64_t>::min() - right)) {
    return false;
  }
  output = left + right;
  return true;
}

bool CheckedSubtract(std::int64_t left, std::int64_t right,
                     std::int64_t &output) noexcept {
  if ((right > 0 &&
       left < std::numeric_limits<std::int64_t>::min() + right) ||
      (right < 0 &&
       left > std::numeric_limits<std::int64_t>::max() + right)) {
    return false;
  }
  output = left - right;
  return true;
}

bool AppendInt32Array(std::string &output,
                      const std::vector<std::int32_t> &values) {
  output.push_back('[');
  for (std::size_t index = 0; index < values.size(); ++index) {
    if (index != 0) {
      output.push_back(',');
    }
    if (!AppendNumber(output, values[index])) {
      return false;
    }
  }
  output.push_back(']');
  return true;
}

void AppendStringArray(std::string &output,
                       const std::vector<std::string> &values) {
  output.push_back('[');
  for (std::size_t index = 0; index < values.size(); ++index) {
    if (index != 0) {
      output.push_back(',');
    }
    AppendJsonString(output, values[index]);
  }
  output.push_back(']');
}

const game::ArmySnapshot *FindSubject(
    const game::Snapshot &snapshot,
    const game::BattleControlRequest &request) noexcept {
  const auto found = std::find_if(
      snapshot.player_armies.begin(), snapshot.player_armies.end(),
      [&request](const game::ArmySnapshot &army) {
        return army.army_id == request.subject_public_cunit_id;
      });
  return found == snapshot.player_armies.end() ? nullptr : &*found;
}

bool SameExpectedFrame(
    const game::Snapshot &snapshot,
    const BattleControlSnapshotMailboxContextV1 &query,
    const MainThreadExecutionStampV1 &stamp) noexcept {
  const auto *const subject = FindSubject(snapshot, query.request);
  return snapshot == query.expected_snapshot && snapshot.paused &&
         snapshot.map_ready && snapshot.has_played_character &&
         snapshot.played_character_alive &&
         snapshot.date_raw == stamp.date_raw && subject != nullptr &&
         subject->controllable && subject->in_combat && !subject->retreating;
}

bool IsExecutingExactMailboxSlot(
    const BattleControlSnapshotMailboxContextV1 &query,
    const MainThreadExecutionStampV1 &stamp) noexcept {
  if (query.mailbox == nullptr || query.ticket.sequence == 0 ||
      query.expected_snapshot_revision == 0 ||
      query.request.subject_public_cunit_id <= 0 || stamp.pump_epoch == 0 ||
      stamp.thread_id == 0 || !stamp.paused ||
      stamp.tls_initialized_flag_address == 0 ||
      stamp.tls_initialized != 1 || stamp.tls_context == 0 ||
      stamp.tls_main_thread_marker != 1 || stamp.jomini_state == 0 ||
      stamp.game_state == 0 || GetCurrentThreadId() != stamp.thread_id) {
    return false;
  }
  const auto &mailbox = *query.mailbox;
  return mailbox.state.load(std::memory_order_acquire) ==
             MainThreadQueryMailboxStateV1::executing &&
         !mailbox.stop_requested.load(std::memory_order_acquire) &&
         mailbox.failure_flags.load(std::memory_order_acquire) == 0 &&
         mailbox.published_sequence.load(std::memory_order_acquire) ==
             query.ticket.sequence &&
         mailbox.owner_thread_id.load(std::memory_order_acquire) ==
             stamp.thread_id &&
         mailbox.paused_owner_verified_pump_epochs.load(
             std::memory_order_acquire) >=
             kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs &&
         mailbox.executor == &ExecuteBattleControlSnapshotMailboxQueryV1 &&
         mailbox.executor_context ==
             const_cast<BattleControlSnapshotMailboxContextV1 *>(&query);
}

bool SideHasNativeArmy(const game::BattleControlSideSnapshot &side,
                       std::int32_t native_carmy_id) noexcept {
  return std::any_of(
      side.ordered_armies.begin(), side.ordered_armies.end(),
      [native_carmy_id](const game::BattleControlArmyIdentitySnapshot &army) {
        return army.native_carmy_id == native_carmy_id;
      });
}

const game::BattleControlArmyIdentitySnapshot *FindSideArmy(
    const game::BattleControlSideSnapshot &side,
    std::int32_t native_carmy_id) noexcept {
  const auto found = std::find_if(
      side.ordered_armies.begin(), side.ordered_armies.end(),
      [native_carmy_id](const game::BattleControlArmyIdentitySnapshot &army) {
        return army.native_carmy_id == native_carmy_id;
      });
  return found == side.ordered_armies.end() ? nullptr : &*found;
}

bool ValidArmyIdentities(const game::BattleControlSideSnapshot &side,
                         std::int32_t combat_id) noexcept {
  for (std::size_t index = 0; index < side.ordered_armies.size(); ++index) {
    const auto &army = side.ordered_armies[index];
    if (army.native_carmy_id <= 0 || army.public_cunit_id <= 0 ||
        army.owner_character_id <= 0 ||
        army.combat_backlink_id != combat_id) {
      return false;
    }
    for (std::size_t prior = 0; prior < index; ++prior) {
      if (side.ordered_armies[prior].native_carmy_id ==
              army.native_carmy_id ||
          side.ordered_armies[prior].public_cunit_id ==
              army.public_cunit_id) {
        return false;
      }
    }
  }
  return !side.ordered_armies.empty();
}

bool ValidateEntries(
    const game::BattleControlSideSnapshot &side,
    const std::vector<game::BattleControlRegimentEntrySnapshot> &entries,
    std::string_view bucket,
    std::int64_t &current_total,
    std::int64_t &soft_total,
    std::int64_t &main_hard_total,
    std::int64_t &non_main_difference_total) noexcept {
  for (std::size_t index = 0; index < entries.size(); ++index) {
    const auto &entry = entries[index];
    const auto *const army = FindSideArmy(side, entry.native_carmy_id);
    if (entry.bucket != bucket ||
        entry.bucket_index != static_cast<std::int32_t>(index) ||
        entry.regiment_id <= 0 || army == nullptr ||
        entry.public_cunit_id != army->public_cunit_id ||
        entry.owner_character_id != army->owner_character_id) {
      return false;
    }

    std::int64_t after_current = 0;
    std::int64_t difference = 0;
    if (!CheckedAdd(current_total, entry.current_fighting_raw,
                    after_current) ||
        !CheckedAdd(soft_total, entry.soft_casualties_raw, soft_total) ||
        !CheckedSubtract(entry.starting_raw, entry.current_fighting_raw,
                         difference) ||
        !CheckedSubtract(difference, entry.soft_casualties_raw,
                         difference)) {
      return false;
    }
    current_total = after_current;
    if (entry.fights_in_main_phase) {
      if (!entry.hard_casualties_available ||
          entry.hard_casualties_raw != difference ||
          !CheckedAdd(main_hard_total, entry.hard_casualties_raw,
                      main_hard_total)) {
        return false;
      }
    } else if (entry.hard_casualties_available ||
               !CheckedAdd(non_main_difference_total, difference,
                           non_main_difference_total)) {
      return false;
    }
  }
  return true;
}

bool ValidateSide(const game::BattleControlSideSnapshot &side,
                  std::int32_t expected_index,
                  std::string_view expected_role,
                  std::int32_t combat_id) noexcept {
  if (side.side_index != expected_index || side.role != expected_role ||
      side.primary_participant_character_id <= 0 ||
      (side.selected_commander_character_id != -1 &&
       side.selected_commander_character_id <= 0) ||
      side.side_strength_scale != 100'000 ||
      !ValidArmyIdentities(side, combat_id)) {
    return false;
  }

  std::int64_t current_total = 0;
  std::int64_t levy_current_total = 0;
  std::int64_t soft_total = 0;
  std::int64_t main_hard_total = 0;
  std::int64_t non_main_difference_total = 0;
  if (!ValidateEntries(side, side.levy_entries, "levy",
                       current_total, soft_total, main_hard_total,
                       non_main_difference_total)) {
    return false;
  }
  levy_current_total = current_total;
  if (!ValidateEntries(side, side.men_at_arms_entries, "men_at_arms",
                       current_total, soft_total, main_hard_total,
                       non_main_difference_total) ||
      side.stored_current_matches_derived !=
          (side.stored_current_fighting_raw == current_total) ||
      side.stored_levy_current_matches_derived !=
          (side.stored_levy_current_fighting_raw == levy_current_total) ||
      side.derived_current_fighting_raw != current_total ||
      side.derived_soft_casualties_raw != soft_total ||
      side.derived_main_fighting_entry_hard_casualties_raw !=
          main_hard_total ||
      side.non_main_start_minus_current_minus_soft_raw !=
          non_main_difference_total) {
    return false;
  }

  std::int64_t participant_hard_total = 0;
  for (std::size_t index = 0;
       index < side.participant_hard_ledger.size(); ++index) {
    const auto &row = side.participant_hard_ledger[index];
    if (row.row_index != static_cast<std::int32_t>(index) ||
        row.participant_character_id <= 0 ||
        !CheckedAdd(participant_hard_total, row.hard_casualties_raw,
                    participant_hard_total)) {
      return false;
    }
  }
  return participant_hard_total == side.participant_hard_total_raw;
}

bool ValidateActiveCombatRetreat(
    const game::BattleControlSnapshot &snapshot) noexcept {
  constexpr std::int64_t date_epoch_raw = 0x029C55C0;
  constexpr std::int64_t date_raw_per_whole_day = 24;
  const auto day_index = [&](std::int64_t date_raw) noexcept {
    return (date_raw - date_epoch_raw) / date_raw_per_whole_day;
  };
  if (snapshot.selected_public_cunit_id !=
          snapshot.subject_public_cunit_id ||
      snapshot.selected_native_carmy_id !=
          snapshot.subject_native_carmy_id ||
      snapshot.selected_owner_character_id <= 0 ||
      snapshot.combat_province_id != snapshot.province_id ||
      (snapshot.side_index != 0 && snapshot.side_index != 1) ||
      snapshot.legality.status != "available" ||
      snapshot.legality.phase_raw != snapshot.phase_raw ||
      snapshot.legality.phase != snapshot.phase ||
      snapshot.legality.minimum_elapsed_whole_days_exclusive < 0 ||
      snapshot.observed_date_raw <
          std::numeric_limits<std::int32_t>::min() ||
      snapshot.observed_date_raw >
          std::numeric_limits<std::int32_t>::max()) {
    return false;
  }

  const auto &selected_side =
      snapshot.side_index == 0 ? snapshot.attacker : snapshot.defender;
  const auto *const selected = FindSideArmy(
      selected_side, snapshot.selected_native_carmy_id);
  if (selected == nullptr ||
      selected->public_cunit_id != snapshot.selected_public_cunit_id ||
      selected->owner_character_id !=
          snapshot.selected_owner_character_id) {
    return false;
  }
  std::vector<std::int32_t> expected_affected;
  std::vector<std::int32_t> expected_unaffected;
  for (const auto &army : selected_side.ordered_armies) {
    auto &destination =
        army.owner_character_id == snapshot.selected_owner_character_id
            ? expected_affected
            : expected_unaffected;
    destination.push_back(army.public_cunit_id);
  }
  const auto expected_scope =
      expected_unaffected.empty() ? "full_side" : "owner_subset";
  if (expected_affected.empty() || snapshot.side_scope != expected_scope ||
      snapshot.affected_public_cunit_ids_in_stored_order !=
          expected_affected ||
      snapshot.unaffected_same_side_public_cunit_ids_in_stored_order !=
          expected_unaffected) {
    return false;
  }

  const auto baseline_day_index = day_index(
      snapshot.legality.retreat_elapsed_baseline_date_raw);
  const auto expected_elapsed =
      day_index(snapshot.observed_date_raw) - baseline_day_index;
  const auto expected_earliest =
      date_epoch_raw +
      (baseline_day_index +
       static_cast<std::int64_t>(
           snapshot.legality.minimum_elapsed_whole_days_exclusive) +
       1) *
          date_raw_per_whole_day;
  if (snapshot.legality.elapsed_whole_days != expected_elapsed ||
      !snapshot.legality.earliest_day_gate_date_raw.has_value() ||
      *snapshot.legality.earliest_day_gate_date_raw != expected_earliest) {
    return false;
  }

  std::vector<std::string> expected_codes;
  std::vector<std::string> expected_keys;
  const auto append_reason = [&](std::string_view code,
                                 std::string_view key) {
    expected_codes.emplace_back(code);
    expected_keys.emplace_back(key);
  };
  if (snapshot.side_flags.disallow_retreat) {
    append_reason("disallowed", "COMBAT_NO_RETREAT_DISALLOWED");
  }
  const bool too_early =
      !snapshot.side_flags.allow_early_retreat &&
      snapshot.legality.elapsed_whole_days <=
          snapshot.legality.minimum_elapsed_whole_days_exclusive;
  if (too_early) {
    append_reason("too_early", "COMBAT_NO_RETREAT_TOO_EARLY");
  }
  if (snapshot.phase_raw >= 2) {
    append_reason("pursuit_or_done", "COMBAT_NO_RETREAT_PURSUIT");
  }
  if (!snapshot.legality.landless_gate_allows_retreat) {
    append_reason("landless", "COMBAT_NO_RETREAT_LANDLESS");
  }
  const bool expected_legal =
      !snapshot.side_flags.disallow_retreat && !too_early &&
      snapshot.phase_raw < 2 &&
      snapshot.legality.landless_gate_allows_retreat;
  return snapshot.legality.reason_codes_in_native_order == expected_codes &&
         snapshot.legality.native_reason_keys_in_native_order ==
             expected_keys &&
         snapshot.legality.legal_now == expected_legal &&
         snapshot.legality.native_boolean == expected_legal;
}

bool ValidateSnapshot(const game::BattleControlSnapshot &snapshot) noexcept {
  const bool phase_valid =
      (snapshot.phase_raw == 0 && snapshot.phase == "maneuver") ||
      (snapshot.phase_raw == 1 && snapshot.phase == "main") ||
      (snapshot.phase_raw == 2 && snapshot.phase == "pursuit") ||
      (snapshot.phase_raw == 3 && snapshot.phase == "done");
  const bool winner_valid =
      (snapshot.winner_raw == -1 && snapshot.winner_side == "none") ||
      (snapshot.winner_raw == 0 && snapshot.winner_side == "attacker") ||
      (snapshot.winner_raw == 1 && snapshot.winner_side == "defender");
  const bool forced_winner_valid =
      (snapshot.forced_winner_raw == -1 &&
       snapshot.forced_winner_side == "none") ||
      (snapshot.forced_winner_raw == 0 &&
       snapshot.forced_winner_side == "attacker") ||
      (snapshot.forced_winner_raw == 1 &&
       snapshot.forced_winner_side == "defender");
  if (snapshot.status != game::BattleControlSnapshotStatus::available ||
      !snapshot.battle_control_ready || snapshot.snapshot_revision == 0 ||
      snapshot.subject_public_cunit_id <= 0 ||
      snapshot.subject_native_carmy_id <= 0 || snapshot.combat_id == -1 ||
      snapshot.province_id <= 0 || !phase_valid || !winner_valid ||
      !forced_winner_valid || snapshot.phase_day < 0 ||
      !ValidateActiveCombatRetreat(snapshot) ||
      !ValidateSide(snapshot.attacker, 0, "attacker", snapshot.combat_id) ||
      !ValidateSide(snapshot.defender, 1, "defender", snapshot.combat_id)) {
    return false;
  }

  const bool subject_in_attacker = std::any_of(
      snapshot.attacker.ordered_armies.begin(),
      snapshot.attacker.ordered_armies.end(),
      [&snapshot](const game::BattleControlArmyIdentitySnapshot &army) {
        return army.public_cunit_id == snapshot.subject_public_cunit_id &&
               army.native_carmy_id == snapshot.subject_native_carmy_id;
      });
  const bool subject_in_defender = std::any_of(
      snapshot.defender.ordered_armies.begin(),
      snapshot.defender.ordered_armies.end(),
      [&snapshot](const game::BattleControlArmyIdentitySnapshot &army) {
        return army.public_cunit_id == snapshot.subject_public_cunit_id &&
               army.native_carmy_id == snapshot.subject_native_carmy_id;
      });
  if (subject_in_attacker == subject_in_defender) {
    return false;
  }
  return std::none_of(
      snapshot.attacker.ordered_armies.begin(),
      snapshot.attacker.ordered_armies.end(),
      [&snapshot](const game::BattleControlArmyIdentitySnapshot &attacker) {
        return SideHasNativeArmy(snapshot.defender,
                                 attacker.native_carmy_id) ||
               std::any_of(
                   snapshot.defender.ordered_armies.begin(),
                   snapshot.defender.ordered_armies.end(),
                   [&attacker](
                       const game::BattleControlArmyIdentitySnapshot
                           &defender) {
                     return defender.public_cunit_id ==
                            attacker.public_cunit_id;
                   });
      });
}

bool AppendArmy(std::string &output,
                const game::BattleControlArmyIdentitySnapshot &army) {
  output += "{\"native_carmy_id\":";
  return AppendNumber(output, army.native_carmy_id) &&
         (output += ",\"public_cunit_id\":",
          AppendNumber(output, army.public_cunit_id)) &&
         (output += ",\"owner_character_id\":",
          AppendNumber(output, army.owner_character_id)) &&
         (output += ",\"combat_backlink_id\":",
          AppendNumber(output, army.combat_backlink_id)) &&
         (output.push_back('}'), true);
}

bool AppendRegimentEntry(
    std::string &output,
    const game::BattleControlRegimentEntrySnapshot &entry) {
  output += "{\"bucket\":";
  AppendJsonString(output, entry.bucket);
  output += ",\"bucket_index\":";
  if (!AppendNumber(output, entry.bucket_index)) {
    return false;
  }
  output += ",\"regiment_id\":";
  if (!AppendNumber(output, entry.regiment_id)) {
    return false;
  }
  output += ",\"native_carmy_id\":";
  if (!AppendNumber(output, entry.native_carmy_id)) {
    return false;
  }
  output += ",\"public_cunit_id\":";
  if (!AppendNumber(output, entry.public_cunit_id)) {
    return false;
  }
  output += ",\"owner_character_id\":";
  if (!AppendNumber(output, entry.owner_character_id)) {
    return false;
  }
  output += ",\"starting_raw\":";
  if (!AppendNumber(output, entry.starting_raw)) {
    return false;
  }
  output += ",\"current_fighting_raw\":";
  if (!AppendNumber(output, entry.current_fighting_raw)) {
    return false;
  }
  output += ",\"soft_casualties_raw\":";
  if (!AppendNumber(output, entry.soft_casualties_raw)) {
    return false;
  }
  output += ",\"fights_in_main_phase\":";
  output += entry.fights_in_main_phase ? "true" : "false";
  output += ",\"hard_casualties_status\":\"";
  output += entry.hard_casualties_available ? "available" : "unavailable";
  output += "\",\"hard_casualties_raw\":";
  if (entry.hard_casualties_available) {
    if (!AppendNumber(output, entry.hard_casualties_raw)) {
      return false;
    }
  } else {
    output += "null";
  }
  output += ",\"hard_casualties_source\":";
  if (entry.hard_casualties_available) {
    output += "\"derived_starting_minus_current_minus_soft\"";
  } else {
    output += "null";
  }
  output += ",\"hard_casualties_unavailable_reason\":";
  if (entry.hard_casualties_available) {
    output += "null";
  } else {
    output +=
        "\"non_main_reserve_not_distinguishable_from_hard\"";
  }
  output += ",\"effective_max_size\":";
  if (!AppendNumber(output, entry.effective_max_size)) {
    return false;
  }
  output += ",\"effective_siege_raw\":";
  if (!AppendNumber(output, entry.effective_siege_raw)) {
    return false;
  }
  output += ",\"effective_damage_raw\":";
  if (!AppendNumber(output, entry.effective_damage_raw)) {
    return false;
  }
  output += ",\"effective_toughness_raw\":";
  if (!AppendNumber(output, entry.effective_toughness_raw)) {
    return false;
  }
  output += ",\"effective_pursuit_raw\":";
  if (!AppendNumber(output, entry.effective_pursuit_raw)) {
    return false;
  }
  output += ",\"effective_screen_raw\":";
  if (!AppendNumber(output, entry.effective_screen_raw)) {
    return false;
  }
  output += ",\"entry_strength_raw\":";
  if (!AppendNumber(output, entry.entry_strength_raw)) {
    return false;
  }
  output.push_back('}');
  return true;
}

bool AppendActiveCombatRetreatLegality(
    std::string &output,
    const game::ActiveCombatRetreatLegalitySnapshot &legality) {
  output += "{\"status\":";
  AppendJsonString(output, legality.status);
  output += ",\"native_boolean\":";
  output += legality.native_boolean ? "true" : "false";
  output += ",\"phase_raw\":";
  if (!AppendNumber(output, legality.phase_raw)) {
    return false;
  }
  output += ",\"phase\":";
  AppendJsonString(output, legality.phase);
  output += ",\"retreat_elapsed_baseline_date_raw\":";
  if (!AppendNumber(output, legality.retreat_elapsed_baseline_date_raw)) {
    return false;
  }
  output += ",\"elapsed_whole_days\":";
  if (!AppendNumber(output, legality.elapsed_whole_days)) {
    return false;
  }
  output += ",\"minimum_elapsed_whole_days_exclusive\":";
  if (!AppendNumber(output,
                    legality.minimum_elapsed_whole_days_exclusive)) {
    return false;
  }
  output += ",\"landless_gate_allows_retreat\":";
  output += legality.landless_gate_allows_retreat ? "true" : "false";
  output += ",\"legal_now\":";
  output += legality.legal_now ? "true" : "false";
  output += ",\"reason_codes_in_native_order\":";
  AppendStringArray(output, legality.reason_codes_in_native_order);
  output += ",\"native_reason_keys_in_native_order\":";
  AppendStringArray(output, legality.native_reason_keys_in_native_order);
  output += ",\"earliest_day_gate_date_raw\":";
  if (legality.earliest_day_gate_date_raw.has_value()) {
    if (!AppendNumber(output, *legality.earliest_day_gate_date_raw)) {
      return false;
    }
  } else {
    output += "null";
  }
  output.push_back('}');
  return true;
}

bool AppendSide(std::string &output,
                const game::BattleControlSideSnapshot &side) {
  output += "{\"side_index\":";
  if (!AppendNumber(output, side.side_index)) {
    return false;
  }
  output += ",\"role\":";
  AppendJsonString(output, side.role);
  output += ",\"primary_participant_character_id\":";
  if (!AppendNumber(output, side.primary_participant_character_id)) {
    return false;
  }
  output += ",\"selected_commander_character_id\":";
  if (side.selected_commander_character_id > 0) {
    if (!AppendNumber(output, side.selected_commander_character_id)) {
      return false;
    }
  } else {
    output += "null";
  }
  output += ",\"current_roll_points\":";
  if (!AppendNumber(output, side.current_roll_points)) {
    return false;
  }
  output += ",\"ordered_armies\":[";
  for (std::size_t index = 0; index < side.ordered_armies.size(); ++index) {
    if (index != 0) {
      output.push_back(',');
    }
    if (!AppendArmy(output, side.ordered_armies[index])) {
      return false;
    }
  }
  output += "],\"levy_entries\":[";
  for (std::size_t index = 0; index < side.levy_entries.size(); ++index) {
    if (index != 0) {
      output.push_back(',');
    }
    if (!AppendRegimentEntry(output, side.levy_entries[index])) {
      return false;
    }
  }
  output += "],\"men_at_arms_entries\":[";
  for (std::size_t index = 0; index < side.men_at_arms_entries.size();
       ++index) {
    if (index != 0) {
      output.push_back(',');
    }
    if (!AppendRegimentEntry(output, side.men_at_arms_entries[index])) {
      return false;
    }
  }
  output += "],\"stored_current_fighting_raw\":";
  if (!AppendNumber(output, side.stored_current_fighting_raw)) {
    return false;
  }
  output += ",\"stored_levy_current_fighting_raw\":";
  if (!AppendNumber(output, side.stored_levy_current_fighting_raw)) {
    return false;
  }
  output += ",\"stored_current_matches_derived\":";
  output += side.stored_current_matches_derived ? "true" : "false";
  output += ",\"stored_levy_current_matches_derived\":";
  output += side.stored_levy_current_matches_derived ? "true" : "false";
  output += ",\"derived_current_fighting_raw\":";
  if (!AppendNumber(output, side.derived_current_fighting_raw)) {
    return false;
  }
  output += ",\"derived_soft_casualties_raw\":";
  if (!AppendNumber(output, side.derived_soft_casualties_raw)) {
    return false;
  }
  output +=
      ",\"derived_main_fighting_entry_hard_casualties_raw\":";
  if (!AppendNumber(
          output,
          side.derived_main_fighting_entry_hard_casualties_raw)) {
    return false;
  }
  output +=
      ",\"non_main_start_minus_current_minus_soft_raw\":";
  if (!AppendNumber(
          output, side.non_main_start_minus_current_minus_soft_raw)) {
    return false;
  }
  output += ",\"participant_hard_ledger\":[";
  for (std::size_t index = 0;
       index < side.participant_hard_ledger.size(); ++index) {
    if (index != 0) {
      output.push_back(',');
    }
    const auto &row = side.participant_hard_ledger[index];
    output += "{\"row_index\":";
    if (!AppendNumber(output, row.row_index)) {
      return false;
    }
    output += ",\"participant_character_id\":";
    if (!AppendNumber(output, row.participant_character_id)) {
      return false;
    }
    output += ",\"hard_casualties_raw\":";
    if (!AppendNumber(output, row.hard_casualties_raw)) {
      return false;
    }
    output.push_back('}');
  }
  output += "],\"participant_hard_total_raw\":";
  if (!AppendNumber(output, side.participant_hard_total_raw)) {
    return false;
  }
  output += ",\"side_strength_raw\":";
  if (!AppendNumber(output, side.side_strength_raw)) {
    return false;
  }
  output += ",\"side_strength_scale\":";
  if (!AppendNumber(output, side.side_strength_scale)) {
    return false;
  }
  output.push_back('}');
  return true;
}

} // namespace

bool ParseBattleControlSnapshotV1Step(
    std::string_view step,
    game::BattleControlRequest &output) noexcept {
  output = {};
  if (!step.starts_with(kBattleControlSnapshotV1StepPrefix) ||
      !ParseCanonicalPositiveInt32(
          step.substr(kBattleControlSnapshotV1StepPrefix.size()),
          output.subject_public_cunit_id)) {
    output = {};
    return false;
  }
  return true;
}

bool ParseBattleControlExpectedRevisionV1(
    std::string_view json, std::uint64_t &output) noexcept {
  output = 0;
  constexpr std::string_view key = "\"expected_revision\":";
  const auto at = json.find(key);
  if (at == std::string_view::npos ||
      json.find(key, at + key.size()) != std::string_view::npos) {
    return false;
  }
  auto begin = at + key.size();
  while (begin < json.size() &&
         (json[begin] == ' ' || json[begin] == '\t' ||
          json[begin] == '\r' || json[begin] == '\n')) {
    ++begin;
  }
  auto end = begin;
  while (end < json.size() && json[end] >= '0' && json[end] <= '9') {
    ++end;
  }
  auto delimiter = end;
  while (delimiter < json.size() &&
         (json[delimiter] == ' ' || json[delimiter] == '\t' ||
          json[delimiter] == '\r' || json[delimiter] == '\n')) {
    ++delimiter;
  }
  if (end == begin || (json[begin] == '0' && end - begin != 1U) ||
      (delimiter < json.size() && json[delimiter] != ',' &&
       json[delimiter] != '}')) {
    return false;
  }
  const auto parsed =
      std::from_chars(json.data() + begin, json.data() + end, output);
  return parsed.ec == std::errc{} && parsed.ptr == json.data() + end &&
         output > 0;
}

bool ExecuteBattleControlSnapshotMailboxQueryV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *const query =
      static_cast<BattleControlSnapshotMailboxContextV1 *>(opaque_context);
  if (query == nullptr || !IsExecutingExactMailboxSlot(*query, stamp) ||
      query->completion !=
          BattleControlSnapshotMailboxCompletionV1::not_executed ||
      query->executor_invocations != 0) {
    if (query != nullptr) {
      query->completion = BattleControlSnapshotMailboxCompletionV1::
          infrastructure_rejected;
    }
    return false;
  }

  try {
    ++query->executor_invocations;
    query->execution_stamp = stamp;
    game::Snapshot before{};
    if (!ReadSnapshot(query->bindings, before) ||
        !SameExpectedFrame(before, *query, stamp)) {
      query->result = {};
      query->completion =
          BattleControlSnapshotMailboxCompletionV1::frame_changed;
      return true;
    }

    const auto status = ReadBattleControlSnapshot(
        query->bindings, query->request, query->result);

    game::Snapshot after{};
    if (!ReadSnapshot(query->bindings, after) || after != before ||
        !SameExpectedFrame(after, *query, stamp)) {
      query->result = {};
      query->completion =
          BattleControlSnapshotMailboxCompletionV1::frame_changed;
      return true;
    }

    if (status == game::BattleControlSnapshotStatus::available &&
        query->result.status == status &&
        query->result.observed_date_raw == stamp.date_raw &&
        query->result.subject_public_cunit_id ==
            query->request.subject_public_cunit_id &&
        query->result.battle_control_ready) {
      query->result.snapshot_revision = query->expected_snapshot_revision;
      query->completion =
          BattleControlSnapshotMailboxCompletionV1::available;
      return true;
    }
    const auto diagnostic_reason = query->result.diagnostic_reason;
    query->result = {};
    query->result.status = status;
    query->result.diagnostic_reason = diagnostic_reason;
    query->completion =
        BattleControlSnapshotMailboxCompletionV1::query_unavailable;
    return true;
  } catch (...) {
    query->result = {};
    query->completion =
        BattleControlSnapshotMailboxCompletionV1::query_unavailable;
    return true;
  }
}

std::string_view BattleControlSnapshotFailureMessageV1(
    MainThreadQueryWaitResultV1 wait,
    BattleControlSnapshotMailboxCompletionV1 completion,
    game::BattleControlSnapshotStatus status,
    bool completion_snapshot_stable) noexcept {
  switch (wait) {
  case MainThreadQueryWaitResultV1::executor_failed:
    return completion ==
                   BattleControlSnapshotMailboxCompletionV1::
                       infrastructure_rejected
               ? "application-main battle-control executor gate rejected execution"
               : "application-main battle-control executor failed";
  case MainThreadQueryWaitResultV1::infrastructure_failed:
    return "application-main battle-control boundary drifted";
  case MainThreadQueryWaitResultV1::cancelled:
    return "application-main battle-control query was cancelled";
  case MainThreadQueryWaitResultV1::timeout_cancelled_before_execution:
    return "application-main battle-control query timed out before execution";
  case MainThreadQueryWaitResultV1::timeout_executor_already_running:
    return "application-main battle-control executor is still running";
  case MainThreadQueryWaitResultV1::ticket_mismatch:
    return "application-main battle-control ticket mismatch";
  case MainThreadQueryWaitResultV1::completed:
    break;
  }
  if (completion == BattleControlSnapshotMailboxCompletionV1::frame_changed) {
    return "battle-control application-main frame changed";
  }
  if (completion == BattleControlSnapshotMailboxCompletionV1::available &&
      status == game::BattleControlSnapshotStatus::available) {
    return completion_snapshot_stable
               ? "application-main battle-control result is inconsistent"
               : "battle-control completion snapshot changed";
  }
  switch (status) {
  case game::BattleControlSnapshotStatus::available:
    return "application-main battle-control completion is inconsistent";
  case game::BattleControlSnapshotStatus::requires_paused:
    return "battle-control query observed an unpaused map";
  case game::BattleControlSnapshotStatus::subject_cunit_not_found:
    return "battle-control subject CUnit was not found";
  case game::BattleControlSnapshotStatus::subject_not_controllable:
    return "battle-control subject is not player-controllable";
  case game::BattleControlSnapshotStatus::subject_not_in_combat:
    return "battle-control subject is not in an active combat";
  case game::BattleControlSnapshotStatus::subject_retreating:
    return "battle-control subject is retreating";
  case game::BattleControlSnapshotStatus::state_changed:
    return "CK3 battle-control state changed during query";
  case game::BattleControlSnapshotStatus::unavailable:
    return "CK3 battle-control reader is unavailable";
  }
  return "application-main battle-control failure state is unknown";
}

std::string SerializeBattleControlSnapshotV1(
    const game::BattleControlSnapshot &snapshot) {
  if (!ValidateSnapshot(snapshot)) {
    return {};
  }

  std::string output;
  const auto estimated_size =
      4096U +
      (snapshot.attacker.levy_entries.size() +
       snapshot.attacker.men_at_arms_entries.size() +
       snapshot.defender.levy_entries.size() +
       snapshot.defender.men_at_arms_entries.size()) *
          640U;
  output.reserve((std::min)(estimated_size,
                            kBattleControlSnapshotV1WireMaximumBytes));
  output +=
      "{\"schema_version\":1,\"contract_stage\":"
      "\"production_exact_ongoing_combat\",\"status\":\"available\",";
  output += "\"snapshot_revision\":";
  if (!AppendNumber(output, snapshot.snapshot_revision)) {
    return {};
  }
  output += ",\"observed_date_raw\":";
  if (!AppendNumber(output, snapshot.observed_date_raw)) {
    return {};
  }
  output += ",\"subject_public_cunit_id\":";
  if (!AppendNumber(output, snapshot.subject_public_cunit_id)) {
    return {};
  }
  output += ",\"subject_native_carmy_id\":";
  if (!AppendNumber(output, snapshot.subject_native_carmy_id)) {
    return {};
  }
  output += ",\"combat_id\":";
  if (!AppendNumber(output, snapshot.combat_id)) {
    return {};
  }
  output += ",\"province_id\":";
  if (!AppendNumber(output, snapshot.province_id)) {
    return {};
  }
  output += ",\"selected_public_cunit_id\":";
  if (!AppendNumber(output, snapshot.selected_public_cunit_id)) {
    return {};
  }
  output += ",\"selected_native_carmy_id\":";
  if (!AppendNumber(output, snapshot.selected_native_carmy_id)) {
    return {};
  }
  output += ",\"selected_owner_character_id\":";
  if (!AppendNumber(output, snapshot.selected_owner_character_id)) {
    return {};
  }
  output += ",\"combat_province_id\":";
  if (!AppendNumber(output, snapshot.combat_province_id)) {
    return {};
  }
  output += ",\"side_index\":";
  if (!AppendNumber(output, snapshot.side_index)) {
    return {};
  }
  output += ",\"side_scope\":";
  AppendJsonString(output, snapshot.side_scope);
  output += ",\"affected_public_cunit_ids_in_stored_order\":";
  if (!AppendInt32Array(
          output,
          snapshot.affected_public_cunit_ids_in_stored_order)) {
    return {};
  }
  output +=
      ",\"unaffected_same_side_public_cunit_ids_in_stored_order\":";
  if (!AppendInt32Array(
          output,
          snapshot.unaffected_same_side_public_cunit_ids_in_stored_order)) {
    return {};
  }
  output += ",\"side_flags\":{\"disallow_retreat\":";
  output += snapshot.side_flags.disallow_retreat ? "true" : "false";
  output += ",\"allow_early_retreat\":";
  output += snapshot.side_flags.allow_early_retreat ? "true" : "false";
  output += ",\"skip_pursuit\":";
  output += snapshot.side_flags.skip_pursuit ? "true}" : "false}";
  output += ",\"legality\":";
  if (!AppendActiveCombatRetreatLegality(output, snapshot.legality)) {
    return {};
  }
  output += ",\"phase\":";
  AppendJsonString(output, snapshot.phase);
  output += ",\"phase_raw\":";
  if (!AppendNumber(output, snapshot.phase_raw)) {
    return {};
  }
  output += ",\"phase_day\":";
  if (!AppendNumber(output, snapshot.phase_day)) {
    return {};
  }
  output += ",\"winner_side\":";
  AppendJsonString(output, snapshot.winner_side);
  output += ",\"winner_raw\":";
  if (!AppendNumber(output, snapshot.winner_raw)) {
    return {};
  }
  output += ",\"forced_winner_side\":";
  AppendJsonString(output, snapshot.forced_winner_side);
  output += ",\"forced_winner_raw\":";
  if (!AppendNumber(output, snapshot.forced_winner_raw)) {
    return {};
  }
  output += ",\"finalized\":";
  output += snapshot.finalized ? "true" : "false";
  output += ",\"battle_result_id\":";
  if (snapshot.battle_result_id != -1) {
    if (!AppendNumber(output, snapshot.battle_result_id)) {
      return {};
    }
  } else {
    output += "null";
  }
  output += ",\"base_combat_width\":";
  if (!AppendNumber(output, snapshot.base_combat_width)) {
    return {};
  }
  output += ",\"final_combat_width\":";
  if (!AppendNumber(output, snapshot.final_combat_width)) {
    return {};
  }
  output += ",\"roll_cadence_counter\":";
  if (!AppendNumber(output, snapshot.roll_cadence_counter)) {
    return {};
  }
  output += ",\"base_advantage_raw\":";
  if (!AppendNumber(output, snapshot.base_advantage_raw)) {
    return {};
  }
  output += ",\"resolved_advantage_raw\":";
  if (!AppendNumber(output, snapshot.resolved_advantage_raw)) {
    return {};
  }
  output += ",\"attacker\":";
  if (!AppendSide(output, snapshot.attacker)) {
    return {};
  }
  output += ",\"defender\":";
  if (!AppendSide(output, snapshot.defender)) {
    return {};
  }
  output += ",\"battle_control_ready\":true}";
  return output.size() <= kBattleControlSnapshotV1WireMaximumBytes
             ? output
             : std::string{};
}

} // namespace xar::ck3_11906
