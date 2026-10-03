#include "xar_bridge/battle_transition_v1_mailbox.hpp"

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

bool ParseCanonicalFullComponentId(std::string_view text,
                                   std::int32_t &output) noexcept {
  output = -1;
  if (text.empty()) {
    return false;
  }
  std::int32_t value = -1;
  const auto parsed =
      std::from_chars(text.data(), text.data() + text.size(), value);
  if (parsed.ec != std::errc{} || parsed.ptr != text.data() + text.size() ||
      value == -1) {
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

bool SameExpectedFrame(
    const game::Snapshot &snapshot,
    const BattleTransitionMailboxContextV1 &query,
    const MainThreadExecutionStampV1 &stamp) noexcept {
  return snapshot == query.expected_snapshot && snapshot.paused &&
         snapshot.map_ready && snapshot.has_played_character &&
         snapshot.played_character_alive &&
         snapshot.date_raw == stamp.date_raw;
}

bool IsExecutingExactMailboxSlot(
    const BattleTransitionMailboxContextV1 &query,
    const MainThreadExecutionStampV1 &stamp) noexcept {
  if (query.mailbox == nullptr || query.ticket.sequence == 0 ||
      query.expected_snapshot_revision == 0 || query.request.combat_id == -1 ||
      stamp.pump_epoch == 0 || stamp.thread_id == 0 || !stamp.paused ||
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
         mailbox.executor == &ExecuteBattleTransitionMailboxQueryV1 &&
         mailbox.executor_context ==
             const_cast<BattleTransitionMailboxContextV1 *>(&query);
}

std::string_view StatusName(
    game::BattleTransitionSnapshotStatus status) noexcept {
  switch (status) {
  case game::BattleTransitionSnapshotStatus::available:
    return "available";
  case game::BattleTransitionSnapshotStatus::combat_not_found:
    return "combat_not_found";
  case game::BattleTransitionSnapshotStatus::state_changed:
    return "state_changed";
  case game::BattleTransitionSnapshotStatus::unavailable:
    return "unavailable";
  }
  return {};
}

bool ValidIds(const std::vector<std::int32_t> &values) noexcept {
  for (std::size_t index = 0; index < values.size(); ++index) {
    if (values[index] <= 0 ||
        std::find(values.begin(), values.begin() + index, values[index]) !=
            values.begin() + index) {
      return false;
    }
  }
  return true;
}

bool ValidCurrentSide(
    const game::BattleCurrentSideObservationSnapshotV1 &side) noexcept {
  if (side.derived_current_fighting_raw < 0 ||
      side.derived_soft_casualties_raw < 0 ||
      side.derived_main_fighting_entry_hard_casualties_raw < 0 ||
      side.non_main_start_minus_current_minus_soft_raw < 0 ||
      side.participant_hard_total_raw < 0) return false;
  std::int64_t total = 0;
  for (const auto &row : side.participant_hard_ledger) {
    if (row.participant_character_id <= 0 || row.hard_casualties_raw < 0 ||
        total > (std::numeric_limits<std::int64_t>::max)() -
                    row.hard_casualties_raw) return false;
    total += row.hard_casualties_raw;
  }
  return total == side.participant_hard_total_raw;
}

bool ValidCurrentObservation(
    const game::BattleCurrentObservationSnapshotV1 &observation) noexcept {
  if (observation.scale != 100'000) return false;
  if (!observation.available) return !observation.unavailable_reason.empty();
  return observation.unavailable_reason.empty() &&
         observation.base_combat_width >= 0 &&
         observation.final_combat_width >= 0 &&
         ValidCurrentSide(observation.attacker) &&
         ValidCurrentSide(observation.defender);
}

bool ValidateSnapshot(
    const game::BattleTransitionSnapshot &snapshot) noexcept {
  if (snapshot.snapshot_revision == 0 || snapshot.combat_id == -1 ||
      StatusName(snapshot.status).empty()) {
    return false;
  }
  if (snapshot.status != game::BattleTransitionSnapshotStatus::available) {
    const bool terminal_identity_ready =
        snapshot.status ==
        game::BattleTransitionSnapshotStatus::combat_not_found;
    return snapshot.battle_transition_ready == terminal_identity_ready &&
           snapshot.province_id == -1 && snapshot.phase.empty() &&
           snapshot.phase_raw == -1 && snapshot.phase_day == -1 &&
           snapshot.winner_side.empty() && snapshot.winner_raw == -1 &&
           snapshot.forced_winner_side.empty() &&
           snapshot.forced_winner_raw == -1 && !snapshot.finalized &&
           snapshot.battle_result_id == -1 &&
           snapshot.attacker_public_cunit_ids_in_stored_order.empty() &&
           snapshot.defender_public_cunit_ids_in_stored_order.empty() &&
           !snapshot.current_observation.has_value();
  }
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
  if (!snapshot.battle_transition_ready || snapshot.province_id <= 0 ||
      !phase_valid || snapshot.phase_day < 0 || !winner_valid ||
      !forced_winner_valid ||
      (snapshot.current_observation &&
       !ValidCurrentObservation(*snapshot.current_observation)) ||
      !ValidIds(snapshot.attacker_public_cunit_ids_in_stored_order) ||
      !ValidIds(snapshot.defender_public_cunit_ids_in_stored_order)) {
    return false;
  }
  return std::none_of(
      snapshot.attacker_public_cunit_ids_in_stored_order.begin(),
      snapshot.attacker_public_cunit_ids_in_stored_order.end(),
      [&snapshot](std::int32_t attacker_id) {
        return std::find(
                   snapshot.defender_public_cunit_ids_in_stored_order.begin(),
                   snapshot.defender_public_cunit_ids_in_stored_order.end(),
                   attacker_id) !=
               snapshot.defender_public_cunit_ids_in_stored_order.end();
      });
}

void AppendNullableNumber(std::string &output, std::int32_t value,
                          bool available) {
  if (available) {
    if (!AppendNumber(output, value)) {
      output += "null";
    }
  } else {
    output += "null";
  }
}

bool AppendCurrentSide(
    std::string &output,
    const game::BattleCurrentSideObservationSnapshotV1 &side) {
  output += "{\"derived_current_fighting_raw\":";
  if (!AppendNumber(output, side.derived_current_fighting_raw)) return false;
  output += ",\"derived_soft_casualties_raw\":";
  if (!AppendNumber(output, side.derived_soft_casualties_raw)) return false;
  output += ",\"derived_main_fighting_entry_hard_casualties_raw\":";
  if (!AppendNumber(output,
                    side.derived_main_fighting_entry_hard_casualties_raw))
    return false;
  output += ",\"non_main_start_minus_current_minus_soft_raw\":";
  if (!AppendNumber(output,
                    side.non_main_start_minus_current_minus_soft_raw))
    return false;
  output += ",\"participant_hard_total_raw\":";
  if (!AppendNumber(output, side.participant_hard_total_raw)) return false;
  output += ",\"participant_hard_ledger\":[";
  for (std::size_t index = 0; index < side.participant_hard_ledger.size(); ++index) {
    if (index != 0) output.push_back(',');
    const auto &row = side.participant_hard_ledger[index];
    output += "{\"participant_character_id\":";
    if (!AppendNumber(output, row.participant_character_id)) return false;
    output += ",\"hard_casualties_raw\":";
    if (!AppendNumber(output, row.hard_casualties_raw)) return false;
    output.push_back('}');
  }
  output += "]}";
  return true;
}

bool AppendCurrentObservation(
    std::string &output,
    const std::optional<game::BattleCurrentObservationSnapshotV1> &observation) {
  if (!observation) {
    output += "null";
    return true;
  }
  output += "{\"status\":";
  AppendJsonString(output, observation->available ? "available" : "unavailable");
  output += ",\"unavailable_reason\":";
  if (observation->available) output += "null";
  else AppendJsonString(output, observation->unavailable_reason);
  output += ",\"scale\":";
  if (!AppendNumber(output, observation->scale)) return false;
  if (!observation->available) {
    output += ",\"base_combat_width\":null,\"final_combat_width\":null,"
              "\"base_advantage_raw\":null,\"resolved_advantage_raw\":null,"
              "\"attacker\":null,\"defender\":null}";
    return true;
  }
  output += ",\"base_combat_width\":";
  if (!AppendNumber(output, observation->base_combat_width)) return false;
  output += ",\"final_combat_width\":";
  if (!AppendNumber(output, observation->final_combat_width)) return false;
  output += ",\"base_advantage_raw\":";
  if (!AppendNumber(output, observation->base_advantage_raw)) return false;
  output += ",\"resolved_advantage_raw\":";
  if (!AppendNumber(output, observation->resolved_advantage_raw)) return false;
  output += ",\"attacker\":";
  if (!AppendCurrentSide(output, observation->attacker)) return false;
  output += ",\"defender\":";
  if (!AppendCurrentSide(output, observation->defender)) return false;
  output.push_back('}');
  return true;
}

} // namespace

bool ParseBattleTransitionV1Step(
    std::string_view step, game::BattleTransitionRequest &output) noexcept {
  output = {};
  if (!step.starts_with(kBattleTransitionV1StepPrefix) ||
      !ParseCanonicalFullComponentId(
          step.substr(kBattleTransitionV1StepPrefix.size()),
          output.combat_id)) {
    output = {};
    return false;
  }
  return true;
}

std::string_view BattleTransitionStatusNameV1(
    game::BattleTransitionSnapshotStatus status) noexcept {
  return StatusName(status);
}

bool ParseBattleTransitionExpectedRevisionV1(
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

bool ExecuteBattleTransitionMailboxQueryV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *const query =
      static_cast<BattleTransitionMailboxContextV1 *>(opaque_context);
  if (query == nullptr || !IsExecutingExactMailboxSlot(*query, stamp) ||
      query->completion !=
          BattleTransitionMailboxCompletionV1::not_executed ||
      query->executor_invocations != 0) {
    if (query != nullptr) {
      query->completion =
          BattleTransitionMailboxCompletionV1::infrastructure_rejected;
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
      query->completion = BattleTransitionMailboxCompletionV1::frame_changed;
      return true;
    }
    ReadBattleTransitionSnapshot(query->bindings, query->request,
                                 query->result);
    game::Snapshot after{};
    if (!ReadSnapshot(query->bindings, after) || after != before ||
        !SameExpectedFrame(after, *query, stamp)) {
      query->result = {};
      query->completion = BattleTransitionMailboxCompletionV1::frame_changed;
      return true;
    }
    query->result.snapshot_revision = query->expected_snapshot_revision;
    query->result.observed_date_raw = stamp.date_raw;
    query->result.combat_id = query->request.combat_id;
    query->completion = BattleTransitionMailboxCompletionV1::completed;
    return true;
  } catch (...) {
    query->result = {};
    query->result.status =
        game::BattleTransitionSnapshotStatus::unavailable;
    query->result.snapshot_revision = query->expected_snapshot_revision;
    query->result.observed_date_raw = stamp.date_raw;
    query->result.combat_id = query->request.combat_id;
    query->completion = BattleTransitionMailboxCompletionV1::completed;
    return true;
  }
}

std::string_view BattleTransitionFailureMessageV1(
    MainThreadQueryWaitResultV1 wait,
    BattleTransitionMailboxCompletionV1 completion,
    bool completion_snapshot_stable) noexcept {
  switch (wait) {
  case MainThreadQueryWaitResultV1::executor_failed:
    return completion ==
                   BattleTransitionMailboxCompletionV1::
                       infrastructure_rejected
               ? "application-main battle-transition executor gate rejected execution"
               : "application-main battle-transition executor failed";
  case MainThreadQueryWaitResultV1::infrastructure_failed:
    return "application-main battle-transition boundary drifted";
  case MainThreadQueryWaitResultV1::cancelled:
    return "application-main battle-transition query was cancelled";
  case MainThreadQueryWaitResultV1::timeout_cancelled_before_execution:
    return "application-main battle-transition query timed out before execution";
  case MainThreadQueryWaitResultV1::timeout_executor_already_running:
    return "application-main battle-transition executor is still running";
  case MainThreadQueryWaitResultV1::ticket_mismatch:
    return "application-main battle-transition ticket mismatch";
  case MainThreadQueryWaitResultV1::completed:
    break;
  }
  if (completion == BattleTransitionMailboxCompletionV1::frame_changed) {
    return "battle-transition application-main frame changed";
  }
  if (completion == BattleTransitionMailboxCompletionV1::completed) {
    return completion_snapshot_stable
               ? "application-main battle-transition result is inconsistent"
               : "battle-transition completion snapshot changed";
  }
  return "application-main battle-transition completion is inconsistent";
}

std::string SerializeBattleTransitionV1(
    const game::BattleTransitionSnapshot &snapshot) {
  if (!ValidateSnapshot(snapshot)) {
    return {};
  }
  const bool available =
      snapshot.status == game::BattleTransitionSnapshotStatus::available;
  std::string output;
  output.reserve(1024U);
  output +=
      "{\"schema_version\":1,\"contract_stage\":"
      "\"production_exact_combat_lifecycle\",\"status\":";
  AppendJsonString(output, StatusName(snapshot.status));
  output += ",\"battle_transition_ready\":";
  output += snapshot.battle_transition_ready ? "true" : "false";
  output += ",\"snapshot_revision\":";
  if (!AppendNumber(output, snapshot.snapshot_revision)) return {};
  output += ",\"observed_date_raw\":";
  if (!AppendNumber(output, snapshot.observed_date_raw)) return {};
  output += ",\"combat_id\":";
  if (!AppendNumber(output, snapshot.combat_id)) return {};
  output += ",\"province_id\":";
  AppendNullableNumber(output, snapshot.province_id, available);
  output += ",\"phase\":";
  if (available) AppendJsonString(output, snapshot.phase);
  else output += "null";
  output += ",\"phase_raw\":";
  AppendNullableNumber(output, snapshot.phase_raw, available);
  output += ",\"phase_day\":";
  AppendNullableNumber(output, snapshot.phase_day, available);
  output += ",\"winner_side\":";
  if (available) AppendJsonString(output, snapshot.winner_side);
  else output += "null";
  output += ",\"winner_raw\":";
  AppendNullableNumber(output, snapshot.winner_raw, available);
  output += ",\"forced_winner_side\":";
  if (available) AppendJsonString(output, snapshot.forced_winner_side);
  else output += "null";
  output += ",\"forced_winner_raw\":";
  AppendNullableNumber(output, snapshot.forced_winner_raw, available);
  output += ",\"finalized\":";
  output += available ? (snapshot.finalized ? "true" : "false") : "null";
  output += ",\"battle_result_id\":";
  if (available && snapshot.battle_result_id != -1) {
    if (!AppendNumber(output, snapshot.battle_result_id)) return {};
  } else {
    output += "null";
  }
  output += ",\"attacker_public_cunit_ids_in_stored_order\":";
  if (!AppendInt32Array(
          output, snapshot.attacker_public_cunit_ids_in_stored_order)) {
    return {};
  }
  output += ",\"defender_public_cunit_ids_in_stored_order\":";
  if (!AppendInt32Array(
          output, snapshot.defender_public_cunit_ids_in_stored_order)) {
    return {};
  }
  output += ",\"current_observation\":";
  if (!AppendCurrentObservation(output, snapshot.current_observation)) return {};
  output.push_back('}');
  return output;
}

} // namespace xar::ck3_11906
