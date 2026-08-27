#include "xar_bridge/battle_terminal_transition_v1_mailbox.hpp"

#include <windows.h>

#include <algorithm>
#include <array>
#include <charconv>
#include <optional>
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

template <typename Value>
bool AppendOptionalNumber(std::string &output,
                          const std::optional<Value> &value) {
  if (!value.has_value()) {
    output += "null";
    return true;
  }
  return AppendNumber(output, *value);
}

void AppendOptionalBool(std::string &output,
                        const std::optional<bool> &value) {
  output += !value.has_value() ? "null" : (*value ? "true" : "false");
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

bool AppendOptionalInt32Array(
    std::string &output,
    const std::optional<std::vector<std::int32_t>> &values) {
  if (!values.has_value()) {
    output += "null";
    return true;
  }
  return AppendInt32Array(output, *values);
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

bool ParseCanonicalUint64(std::string_view text,
                          std::uint64_t &output) noexcept {
  output = 0;
  if (text.empty() || (text.size() != 1 && text.front() == '0')) {
    return false;
  }
  const auto parsed =
      std::from_chars(text.data(), text.data() + text.size(), output);
  if (parsed.ec != std::errc{} || parsed.ptr != text.data() + text.size()) {
    return false;
  }
  char canonical[32]{};
  const auto rendered =
      std::to_chars(canonical, canonical + sizeof(canonical), output);
  return rendered.ec == std::errc{} &&
         std::string_view(canonical, rendered.ptr) == text;
}

std::string_view StatusName(
    game::BattleTerminalTransitionStatusV1 status) noexcept {
  switch (status) {
  case game::BattleTerminalTransitionStatusV1::available:
    return "available";
  case game::BattleTerminalTransitionStatusV1::unavailable:
    return "unavailable";
  }
  return {};
}

std::string_view TerminalKindName(
    game::BattleTerminalKindV1 kind) noexcept {
  switch (kind) {
  case game::BattleTerminalKindV1::active_not_terminal:
    return "active_not_terminal";
  case game::BattleTerminalKindV1::normal_result:
    return "normal_result";
  case game::BattleTerminalKindV1::no_normal_result:
    return "no_normal_result";
  case game::BattleTerminalKindV1::unavailable_after_removal:
    return "unavailable_after_removal";
  }
  return {};
}

std::string_view WarscoreStatusName(
    game::BattleTerminalWarscoreStatusV1 status) noexcept {
  switch (status) {
  case game::BattleTerminalWarscoreStatusV1::recorded:
    return "recorded";
  case game::BattleTerminalWarscoreStatusV1::not_recorded_by_native:
    return "not_recorded_by_native";
  case game::BattleTerminalWarscoreStatusV1::unavailable:
    return "unavailable";
  }
  return {};
}

std::string_view SuccessorStateName(
    game::BattleTerminalSuccessorStateV1 state) noexcept {
  switch (state) {
  case game::BattleTerminalSuccessorStateV1::no_successor:
    return "no_successor";
  case game::BattleTerminalSuccessorStateV1::residual_new_combat:
    return "residual_new_combat";
  case game::BattleTerminalSuccessorStateV1::subject_missing:
    return "subject_missing";
  case game::BattleTerminalSuccessorStateV1::subject_retreating:
    return "subject_retreating";
  case game::BattleTerminalSuccessorStateV1::subject_assignment_reopened:
    return "subject_assignment_reopened";
  case game::BattleTerminalSuccessorStateV1::unavailable:
    return "unavailable";
  }
  return {};
}

std::string_view AiMembershipStatusName(
    game::BattleTerminalAiMembershipStatusV1 status) noexcept {
  switch (status) {
  case game::BattleTerminalAiMembershipStatusV1::none:
    return "none";
  case game::BattleTerminalAiMembershipStatusV1::observed:
    return "observed";
  case game::BattleTerminalAiMembershipStatusV1::unavailable:
    return "unavailable";
  }
  return {};
}

bool ValidUnavailableReason(std::string_view reason) noexcept {
  constexpr std::array<std::string_view, 7> allowed{
      "unsupported_build", "requires_paused", "invalid_request",
      "journal_gap", "identity_unavailable", "state_changed",
      "bounds_exceeded"};
  return std::find(allowed.begin(), allowed.end(), reason) != allowed.end();
}

bool ValidPositiveIds(const std::vector<std::int32_t> &values) noexcept {
  return std::all_of(values.begin(), values.end(),
                     [](std::int32_t value) { return value > 0; });
}

bool ValidateSnapshot(
    const game::BattleTerminalTransitionSnapshotV1 &snapshot) noexcept {
  if (snapshot.snapshot_revision == 0 || snapshot.prior_combat_id <= 0 ||
      snapshot.subject_public_cunit_id <= 0 || StatusName(snapshot.status).empty()) {
    return false;
  }
  const auto &journal = snapshot.terminal_journal;
  if (journal.event_status ==
          game::BattleTerminalJournalEventStatusV1::observed &&
      (!journal.event_sequence.has_value() || *journal.event_sequence == 0)) {
    return false;
  }
  if (journal.event_status ==
          game::BattleTerminalJournalEventStatusV1::not_observed &&
      journal.event_sequence.has_value()) {
    return false;
  }
  if (snapshot.status == game::BattleTerminalTransitionStatusV1::unavailable) {
    return !snapshot.battle_terminal_transition_ready &&
           ValidUnavailableReason(snapshot.unavailable_reason) &&
           journal.event_status ==
               game::BattleTerminalJournalEventStatusV1::not_observed;
  }
  if (!snapshot.battle_terminal_transition_ready ||
      !snapshot.unavailable_reason.empty() ||
      snapshot.prior.combat_id != snapshot.prior_combat_id ||
      TerminalKindName(snapshot.prior.terminal_kind).empty() ||
      WarscoreStatusName(snapshot.prior.battle_warscore.status).empty() ||
      AiMembershipStatusName(
          snapshot.subject.ai_membership_status).empty() ||
      SuccessorStateName(snapshot.successor.state).empty() ||
      !ValidPositiveIds(snapshot.successor.matching_combat_ids_in_native_order) ||
      !ValidPositiveIds(snapshot.successor
                            .participant_overlap_public_cunit_ids_in_prior_order)) {
    return false;
  }
  const bool terminal_event_observed =
      journal.event_status ==
      game::BattleTerminalJournalEventStatusV1::observed;
  if ((terminal_event_observed &&
       (!snapshot.prior.terminal_date_raw.has_value() ||
        snapshot.prior.terminal_date_raw.value_or(-1) < 0 ||
        snapshot.prior.phase_day.value_or(-1) < 0)) ||
      (!terminal_event_observed &&
       snapshot.prior.terminal_kind ==
           game::BattleTerminalKindV1::active_not_terminal &&
       (snapshot.prior.terminal_date_raw.has_value() ||
        snapshot.prior.phase_day.value_or(-1) < 0))) {
    return false;
  }
  const bool any_ai_identity = snapshot.subject.coordinator_id.has_value() ||
      snapshot.subject.unit_stack_stored_index.has_value() ||
      snapshot.subject.subunit_stored_index.has_value();
  const bool complete_ai_identity =
      snapshot.subject.coordinator_id.value_or(-1) > 0 &&
      snapshot.subject.unit_stack_stored_index.value_or(-1) >= 0 &&
      snapshot.subject.subunit_stored_index.value_or(-1) >= 0;
  if ((!snapshot.subject.exists &&
       snapshot.subject.ai_membership_status !=
           game::BattleTerminalAiMembershipStatusV1::none) ||
      (snapshot.subject.ai_membership_status ==
           game::BattleTerminalAiMembershipStatusV1::observed
           ? !complete_ai_identity
           : any_ai_identity) ||
      (snapshot.successor.state ==
           game::BattleTerminalSuccessorStateV1::no_successor &&
       snapshot.subject.ai_membership_status !=
           game::BattleTerminalAiMembershipStatusV1::none) ||
      (snapshot.successor.state ==
           game::BattleTerminalSuccessorStateV1::
               subject_assignment_reopened &&
       snapshot.subject.ai_membership_status !=
           game::BattleTerminalAiMembershipStatusV1::observed)) {
    return false;
  }
  const auto selected = snapshot.successor.selected_successor_combat_id;
  const auto active = snapshot.subject.active_combat_id;
  const bool selected_is_matching =
      selected.has_value() &&
      std::find(snapshot.successor.matching_combat_ids_in_native_order.begin(),
                snapshot.successor.matching_combat_ids_in_native_order.end(),
                *selected) !=
          snapshot.successor.matching_combat_ids_in_native_order.end();
  if ((snapshot.subject.blocked_by_active_combat.value_or(false) &&
       !active.has_value()) ||
      (snapshot.successor.state ==
           game::BattleTerminalSuccessorStateV1::subject_missing &&
       snapshot.subject.exists) ||
      (snapshot.successor.state ==
           game::BattleTerminalSuccessorStateV1::residual_new_combat &&
       (!selected_is_matching || active != selected ||
        snapshot.subject.blocked_by_active_combat != true ||
        snapshot.successor
            .participant_overlap_public_cunit_ids_in_prior_order.empty())) ||
      (snapshot.successor.state ==
           game::BattleTerminalSuccessorStateV1::subject_retreating &&
       (snapshot.subject.blocked_by_active_combat != false ||
        active.has_value() ||
        snapshot.subject.movement_or_retreat_state_raw.value_or(0) <= 0)) ||
      (snapshot.successor.state ==
           game::BattleTerminalSuccessorStateV1::
               subject_assignment_reopened &&
       (snapshot.subject.blocked_by_active_combat.value_or(true) ||
        active.has_value() ||
        !snapshot.successor.matching_combat_ids_in_native_order.empty())) ||
      (snapshot.successor.state ==
           game::BattleTerminalSuccessorStateV1::no_successor &&
       (!snapshot.subject.exists ||
        snapshot.subject.blocked_by_active_combat != false ||
        active.has_value() ||
        selected.has_value() ||
        !snapshot.successor.matching_combat_ids_in_native_order.empty() ||
        snapshot.subject.movement_or_retreat_state_raw.value_or(0) > 0))) {
    return false;
  }
  if (snapshot.prior.attacker_public_cunit_ids_in_stored_order.has_value() &&
      !ValidPositiveIds(
          *snapshot.prior.attacker_public_cunit_ids_in_stored_order)) {
    return false;
  }
  if (snapshot.prior.defender_public_cunit_ids_in_stored_order.has_value() &&
      !ValidPositiveIds(
          *snapshot.prior.defender_public_cunit_ids_in_stored_order)) {
    return false;
  }
  return !snapshot.successor.selected_successor_combat_id.has_value() ||
         *snapshot.successor.selected_successor_combat_id > 0;
}

bool SameExpectedFrame(
    const game::Snapshot &snapshot,
    const BattleTerminalTransitionMailboxContextV1 &query,
    const MainThreadExecutionStampV1 &stamp) noexcept {
  return snapshot == query.expected_snapshot && snapshot.paused &&
         snapshot.map_ready && snapshot.has_played_character &&
         snapshot.played_character_alive &&
         snapshot.date_raw == stamp.date_raw;
}

bool IsExecutingExactMailboxSlot(
    const BattleTerminalTransitionMailboxContextV1 &query,
    const MainThreadExecutionStampV1 &stamp) noexcept {
  if (query.mailbox == nullptr || query.ticket.sequence == 0 ||
      query.expected_snapshot_revision == 0 ||
      query.request.prior_combat_id <= 0 ||
      query.request.subject_public_cunit_id <= 0 || stamp.pump_epoch == 0 ||
      stamp.thread_id == 0 || !stamp.paused ||
      stamp.tls_initialized_flag_address == 0 || stamp.tls_initialized != 1 ||
      stamp.tls_context == 0 || stamp.tls_main_thread_marker != 1 ||
      stamp.jomini_state == 0 || stamp.game_state == 0 ||
      GetCurrentThreadId() != stamp.thread_id) {
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
         mailbox.executor == &ExecuteBattleTerminalTransitionMailboxQueryV1 &&
         mailbox.executor_context ==
             const_cast<BattleTerminalTransitionMailboxContextV1 *>(&query);
}

bool AppendWarscore(
    std::string &output,
    const game::BattleTerminalWarscoreSnapshotV1 &warscore) {
  output += "{\"status\":";
  AppendJsonString(output, WarscoreStatusName(warscore.status));
  output += ",\"war_id\":";
  if (!AppendOptionalNumber(output, warscore.war_id)) return false;
  output += ",\"war_battle_row_index\":";
  if (!AppendOptionalNumber(output, warscore.war_battle_row_index)) return false;
  output += ",\"value_raw_q100000\":";
  if (!AppendOptionalNumber(output, warscore.value_raw_q100000)) return false;
  output += ",\"winner_is_war_attacker\":";
  AppendOptionalBool(output, warscore.winner_is_war_attacker);
  output += ",\"combat_side0_is_war_attacker\":";
  AppendOptionalBool(output, warscore.combat_side0_is_war_attacker);
  output += ",\"attacker_relative_delta_raw_q100000\":";
  if (!AppendOptionalNumber(output,
                            warscore.attacker_relative_delta_raw_q100000)) {
    return false;
  }
  output.push_back('}');
  return true;
}

} // namespace

bool ParseBattleTerminalTransitionV1Step(
    std::string_view step,
    game::BattleTerminalTransitionRequestV1 &output) noexcept {
  output = {};
  if (!step.starts_with(kBattleTerminalTransitionV1StepPrefix)) {
    return false;
  }
  const auto wire = step.substr(kBattleTerminalTransitionV1StepPrefix.size());
  const auto first = wire.find('-');
  const auto second =
      first == std::string_view::npos ? first : wire.find('-', first + 1);
  if (first == std::string_view::npos || second == std::string_view::npos ||
      wire.find('-', second + 1) != std::string_view::npos) {
    return false;
  }
  std::uint64_t cursor = 0;
  if (!ParseCanonicalPositiveInt32(wire.substr(0, first),
                                   output.prior_combat_id) ||
      !ParseCanonicalPositiveInt32(
          wire.substr(first + 1, second - first - 1),
          output.subject_public_cunit_id) ||
      !ParseCanonicalUint64(wire.substr(second + 1), cursor)) {
    output = {};
    return false;
  }
  if (cursor != 0) {
    output.after_terminal_sequence = cursor;
  }
  return true;
}

bool ParseBattleTerminalTransitionExpectedRevisionV1(
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

bool ExecuteBattleTerminalTransitionMailboxQueryV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *const query =
      static_cast<BattleTerminalTransitionMailboxContextV1 *>(opaque_context);
  if (query == nullptr || !IsExecutingExactMailboxSlot(*query, stamp) ||
      query->completion !=
          BattleTerminalTransitionMailboxCompletionV1::not_executed ||
      query->executor_invocations != 0) {
    if (query != nullptr) {
      query->completion = BattleTerminalTransitionMailboxCompletionV1::
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
          BattleTerminalTransitionMailboxCompletionV1::frame_changed;
      return true;
    }
    ReadBattleTerminalTransitionV1(query->bindings, before, query->request,
                                   query->result);
    game::Snapshot after{};
    if (!ReadSnapshot(query->bindings, after) || after != before ||
        !SameExpectedFrame(after, *query, stamp)) {
      query->result = {};
      query->completion =
          BattleTerminalTransitionMailboxCompletionV1::frame_changed;
      return true;
    }
    query->result.snapshot_revision = query->expected_snapshot_revision;
    query->result.observed_date_raw = stamp.date_raw;
    query->result.prior_combat_id = query->request.prior_combat_id;
    query->result.subject_public_cunit_id =
        query->request.subject_public_cunit_id;
    query->completion =
        BattleTerminalTransitionMailboxCompletionV1::completed;
    return true;
  } catch (...) {
    query->result = {};
    query->result.status = game::BattleTerminalTransitionStatusV1::unavailable;
    query->result.unavailable_reason = "state_changed";
    query->result.snapshot_revision = query->expected_snapshot_revision;
    query->result.observed_date_raw = stamp.date_raw;
    query->result.prior_combat_id = query->request.prior_combat_id;
    query->result.subject_public_cunit_id =
        query->request.subject_public_cunit_id;
    query->result.terminal_journal.requested_after_sequence =
        query->request.after_terminal_sequence;
    query->completion =
        BattleTerminalTransitionMailboxCompletionV1::completed;
    return true;
  }
}

std::string_view BattleTerminalTransitionFailureMessageV1(
    MainThreadQueryWaitResultV1 wait,
    BattleTerminalTransitionMailboxCompletionV1 completion,
    bool completion_snapshot_stable) noexcept {
  switch (wait) {
  case MainThreadQueryWaitResultV1::executor_failed:
    return completion == BattleTerminalTransitionMailboxCompletionV1::
                             infrastructure_rejected
               ? "application-main battle-terminal-transition executor gate rejected execution"
               : "application-main battle-terminal-transition executor failed";
  case MainThreadQueryWaitResultV1::infrastructure_failed:
    return "application-main battle-terminal-transition boundary drifted";
  case MainThreadQueryWaitResultV1::cancelled:
    return "application-main battle-terminal-transition query was cancelled";
  case MainThreadQueryWaitResultV1::timeout_cancelled_before_execution:
    return "application-main battle-terminal-transition query timed out before execution";
  case MainThreadQueryWaitResultV1::timeout_executor_already_running:
    return "application-main battle-terminal-transition executor is still running";
  case MainThreadQueryWaitResultV1::ticket_mismatch:
    return "application-main battle-terminal-transition ticket mismatch";
  case MainThreadQueryWaitResultV1::completed:
    break;
  }
  if (completion ==
      BattleTerminalTransitionMailboxCompletionV1::frame_changed) {
    return "battle-terminal-transition application-main frame changed";
  }
  if (completion == BattleTerminalTransitionMailboxCompletionV1::completed) {
    return completion_snapshot_stable
               ? "application-main battle-terminal-transition result is inconsistent"
               : "battle-terminal-transition completion snapshot changed";
  }
  return "application-main battle-terminal-transition completion is inconsistent";
}

std::string SerializeBattleTerminalTransitionV1(
    const game::BattleTerminalTransitionSnapshotV1 &snapshot) {
  if (!ValidateSnapshot(snapshot)) {
    return {};
  }
  const bool available =
      snapshot.status == game::BattleTerminalTransitionStatusV1::available;
  std::string output;
  output.reserve(2'048U);
  output += "{\"schema_version\":1,\"contract_stage\":"
            "\"production_exact_battle_terminal_transition\",\"status\":";
  AppendJsonString(output, StatusName(snapshot.status));
  output += ",\"unavailable_reason\":";
  if (available) output += "null";
  else AppendJsonString(output, snapshot.unavailable_reason);
  output += ",\"battle_terminal_transition_ready\":";
  output += snapshot.battle_terminal_transition_ready ? "true" : "false";
  output += ",\"snapshot_revision\":";
  if (!AppendNumber(output, snapshot.snapshot_revision)) return {};
  output += ",\"observed_date_raw\":";
  if (!AppendNumber(output, snapshot.observed_date_raw)) return {};
  output += ",\"prior_combat_id\":";
  if (!AppendNumber(output, snapshot.prior_combat_id)) return {};
  output += ",\"subject_public_cunit_id\":";
  if (!AppendNumber(output, snapshot.subject_public_cunit_id)) return {};
  const auto &journal = snapshot.terminal_journal;
  output += ",\"terminal_journal\":{\"requested_after_sequence\":";
  if (!AppendOptionalNumber(output, journal.requested_after_sequence)) return {};
  output += ",\"oldest_available_sequence\":";
  if (!AppendNumber(output, journal.oldest_available_sequence)) return {};
  output += ",\"latest_sequence\":";
  if (!AppendNumber(output, journal.latest_sequence)) return {};
  output += ",\"event_sequence\":";
  if (!AppendOptionalNumber(output, journal.event_sequence)) return {};
  output += ",\"event_status\":";
  AppendJsonString(
      output,
      journal.event_status == game::BattleTerminalJournalEventStatusV1::observed
          ? "observed"
          : "not_observed");
  output.push_back('}');
  if (!available) {
    output += ",\"prior\":null,\"removal\":null,\"subject\":null,\"successor\":null}";
    return output;
  }

  const auto &prior = snapshot.prior;
  output += ",\"prior\":{\"combat_id\":";
  if (!AppendNumber(output, prior.combat_id)) return {};
  output += ",\"terminal_kind\":";
  AppendJsonString(output, TerminalKindName(prior.terminal_kind));
  output += ",\"terminal_date_raw\":";
  if (!AppendOptionalNumber(output, prior.terminal_date_raw)) return {};
  output += ",\"suppress_normal_result_envelopes\":";
  AppendOptionalBool(output, prior.suppress_normal_result_envelopes);
  output += ",\"phase_raw\":";
  if (!AppendOptionalNumber(output, prior.phase_raw)) return {};
  output += ",\"phase_day\":";
  if (!AppendOptionalNumber(output, prior.phase_day)) return {};
  output += ",\"winner_raw\":";
  if (!AppendOptionalNumber(output, prior.winner_raw)) return {};
  output += ",\"finalized_before\":";
  AppendOptionalBool(output, prior.finalized_before);
  output += ",\"daily_guard_raw\":";
  if (!AppendOptionalNumber(output, prior.daily_guard_raw)) return {};
  output += ",\"province_id\":";
  if (!AppendOptionalNumber(output, prior.province_id)) return {};
  output += ",\"battle_result_id\":";
  if (!AppendOptionalNumber(output, prior.battle_result_id)) return {};
  output += ",\"wipe_raw\":";
  AppendOptionalBool(output, prior.wipe_raw);
  output += ",\"attacker_primary_participant_character_id\":";
  if (!AppendOptionalNumber(
          output, prior.attacker_primary_participant_character_id)) return {};
  output += ",\"defender_primary_participant_character_id\":";
  if (!AppendOptionalNumber(
          output, prior.defender_primary_participant_character_id)) return {};
  output += ",\"attacker_public_cunit_ids_in_stored_order\":";
  if (!AppendOptionalInt32Array(
          output, prior.attacker_public_cunit_ids_in_stored_order)) return {};
  output += ",\"defender_public_cunit_ids_in_stored_order\":";
  if (!AppendOptionalInt32Array(
          output, prior.defender_public_cunit_ids_in_stored_order)) return {};
  output += ",\"battle_warscore\":";
  if (!AppendWarscore(output, prior.battle_warscore)) return {};
  output.push_back('}');

  const auto &removal = snapshot.removal;
  output += ",\"removal\":{\"prior_combat_strictly_resolves\":";
  output += removal.prior_combat_strictly_resolves ? "true" : "false";
  output += ",\"prior_province_strictly_resolves\":";
  AppendOptionalBool(output, removal.prior_province_strictly_resolves);
  output += ",\"prior_province_contains_prior_combat_id\":";
  AppendOptionalBool(output,
                     removal.prior_province_contains_prior_combat_id);
  output += ",\"result_strictly_resolves\":";
  AppendOptionalBool(output, removal.result_strictly_resolves);
  output += ",\"result_relevant_player_count\":";
  if (!AppendOptionalNumber(output, removal.result_relevant_player_count)) return {};
  output.push_back('}');

  const auto &subject = snapshot.subject;
  output += ",\"subject\":{\"exists\":";
  output += subject.exists ? "true" : "false";
  output += ",\"current_province_id\":";
  if (!AppendOptionalNumber(output, subject.current_province_id)) return {};
  output += ",\"native_carmy_id\":";
  if (!AppendOptionalNumber(output, subject.native_carmy_id)) return {};
  output += ",\"combat_backlink_id\":";
  if (!AppendOptionalNumber(output, subject.combat_backlink_id)) return {};
  output += ",\"active_combat_id\":";
  if (!AppendOptionalNumber(output, subject.active_combat_id)) return {};
  output += ",\"movement_or_retreat_state_raw\":";
  if (!AppendOptionalNumber(output,
                            subject.movement_or_retreat_state_raw)) return {};
  output += ",\"move_target_province_id\":";
  if (!AppendOptionalNumber(output, subject.move_target_province_id)) return {};
  output += ",\"route_province_ids_in_stored_order\":";
  if (!AppendOptionalInt32Array(
          output, subject.route_province_ids_in_stored_order)) return {};
  output += ",\"ai_membership_status\":";
  AppendJsonString(output,
                   AiMembershipStatusName(subject.ai_membership_status));
  output += ",\"coordinator_id\":";
  if (!AppendOptionalNumber(output, subject.coordinator_id)) return {};
  output += ",\"unit_stack_stored_index\":";
  if (!AppendOptionalNumber(output, subject.unit_stack_stored_index)) return {};
  output += ",\"subunit_stored_index\":";
  if (!AppendOptionalNumber(output, subject.subunit_stored_index)) return {};
  output += ",\"blocked_by_active_combat\":";
  AppendOptionalBool(output, subject.blocked_by_active_combat);
  output.push_back('}');

  const auto &successor = snapshot.successor;
  output += ",\"successor\":{\"state\":";
  AppendJsonString(output, SuccessorStateName(successor.state));
  output += ",\"matching_combat_ids_in_native_order\":";
  if (!AppendInt32Array(output,
                        successor.matching_combat_ids_in_native_order)) return {};
  output += ",\"selected_successor_combat_id\":";
  if (!AppendOptionalNumber(output,
                            successor.selected_successor_combat_id)) return {};
  output += ",\"participant_overlap_public_cunit_ids_in_prior_order\":";
  if (!AppendInt32Array(
          output,
          successor.participant_overlap_public_cunit_ids_in_prior_order)) return {};
  output += "}}";
  return output;
}

} // namespace xar::ck3_11906
