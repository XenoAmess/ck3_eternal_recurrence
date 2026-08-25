#include "xar_bridge/actual_contact_scope_v1_mailbox.hpp"

#include <windows.h>

#include <atomic>
#include <charconv>

namespace xar::ck3_11906 {
namespace {

bool ParsePositive(std::string_view text, std::int32_t &output) noexcept {
  if (text.empty() || text.front() == '0') {
    return false;
  }
  const auto parsed =
      std::from_chars(text.data(), text.data() + text.size(), output);
  return parsed.ec == std::errc{} &&
         parsed.ptr == text.data() + text.size() && output > 0;
}

bool IsExecutingExactMailboxSlot(
    const ActualContactScopeMailboxContextV1 &query,
    const MainThreadExecutionStampV1 &stamp) noexcept {
  if (query.mailbox == nullptr || query.ticket.sequence == 0 ||
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
         mailbox.executor == &ExecuteActualContactScopeMailboxQueryV1 &&
         mailbox.executor_context ==
             const_cast<ActualContactScopeMailboxContextV1 *>(&query);
}

} // namespace

bool ParseActualContactScopeV1Step(
    std::string_view step,
    game::ActualContactScopeRequest &output) noexcept {
  output = {};
  if (!step.starts_with(kActualContactScopeV1StepPrefix)) {
    return false;
  }
  const auto body = step.substr(kActualContactScopeV1StepPrefix.size());
  const auto separator = body.find("-at-");
  if (separator == std::string_view::npos ||
      body.find("-at-", separator + 4) != std::string_view::npos ||
      !ParsePositive(body.substr(0, separator), output.subject_army_id) ||
      !ParsePositive(body.substr(separator + 4),
                     output.target_province_id)) {
    output = {};
    return false;
  }
  return true;
}

bool ParseActualContactExpectedRevisionV1(
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

bool ExecuteActualContactScopeMailboxQueryV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *const query =
      static_cast<ActualContactScopeMailboxContextV1 *>(opaque_context);
  if (query == nullptr || !IsExecutingExactMailboxSlot(*query, stamp) ||
      query->completion !=
          ActualContactScopeMailboxCompletionV1::not_executed ||
      query->executor_invocations != 0) {
    if (query != nullptr) {
      query->completion =
          ActualContactScopeMailboxCompletionV1::infrastructure_rejected;
    }
    return false;
  }
  try {
    ++query->executor_invocations;
    query->execution_stamp = stamp;
    const auto status = ReadActualContactScope(
        query->bindings, query->request, query->result);
    const bool pre_contact_result =
        query->result.scope_kind == "pre_contact_prediction" &&
        query->result.transition_kind != "in_combat";
    const bool post_contact_result =
        query->result.scope_kind == "post_contact_observation" &&
        query->result.transition_kind == "in_combat" &&
        query->result.selected_combat_id > 0 &&
        query->result.selected_combat_array_index >= 0;
    if (status == game::ActualContactScopeStatus::available &&
        query->result.status == status &&
        query->result.date_raw == stamp.date_raw &&
        query->result.actual_contact_scope_ready &&
        (pre_contact_result || post_contact_result) &&
        (query->result.transition_kind == "none" ||
         (!query->result.attacker_army_ids.empty() &&
          !query->result.defender_army_ids.empty()))) {
      query->completion =
          ActualContactScopeMailboxCompletionV1::available;
      return true;
    }
    query->result = {};
    query->result.status = status;
    query->completion =
        ActualContactScopeMailboxCompletionV1::query_unavailable;
    return true;
  } catch (...) {
    query->result = {};
    query->completion =
        ActualContactScopeMailboxCompletionV1::query_unavailable;
    return true;
  }
}

std::string_view ActualContactScopeFailureMessageV1(
    MainThreadQueryWaitResultV1 wait,
    ActualContactScopeMailboxCompletionV1 completion,
    game::ActualContactScopeStatus status,
    bool completion_snapshot_stable) noexcept {
  if (wait != MainThreadQueryWaitResultV1::completed) {
    switch (wait) {
    case MainThreadQueryWaitResultV1::executor_failed:
      return "application-main actual-contact executor failed";
    case MainThreadQueryWaitResultV1::infrastructure_failed:
      return "application-main actual-contact boundary drifted";
    case MainThreadQueryWaitResultV1::cancelled:
      return "application-main actual-contact query was cancelled";
    case MainThreadQueryWaitResultV1::timeout_cancelled_before_execution:
      return "application-main actual-contact query timed out";
    case MainThreadQueryWaitResultV1::timeout_executor_already_running:
      return "application-main actual-contact executor is still running";
    case MainThreadQueryWaitResultV1::ticket_mismatch:
      return "application-main actual-contact ticket mismatch";
    case MainThreadQueryWaitResultV1::completed:
      break;
    }
  }
  if (completion == ActualContactScopeMailboxCompletionV1::available &&
      status == game::ActualContactScopeStatus::available) {
    return completion_snapshot_stable
               ? "application-main actual-contact result is inconsistent"
               : "actual-contact completion snapshot changed";
  }
  switch (status) {
  case game::ActualContactScopeStatus::available:
    return "application-main actual-contact completion is inconsistent";
  case game::ActualContactScopeStatus::requires_paused:
    return "actual-contact query observed an unpaused map";
  case game::ActualContactScopeStatus::subject_army_not_found:
    return "actual-contact subject army was not found";
  case game::ActualContactScopeStatus::subject_army_not_controllable:
    return "actual-contact subject army is not player-controllable";
  case game::ActualContactScopeStatus::target_province_not_found:
    return "actual-contact target province was not found";
  case game::ActualContactScopeStatus::subject_not_at_target:
    return "actual-contact subject is not at the requested Province";
  case game::ActualContactScopeStatus::entry_rejected:
    return "CK3 contact entry gates reject the subject";
  case game::ActualContactScopeStatus::relation_unavailable:
    return "CK3 contact relation projection is unavailable";
  case game::ActualContactScopeStatus::state_changed:
    return "CK3 actual-contact state changed during query";
  case game::ActualContactScopeStatus::unavailable:
    return "CK3 actual-contact reader is unavailable";
  }
  return "application-main actual-contact failure state is unknown";
}

} // namespace xar::ck3_11906
