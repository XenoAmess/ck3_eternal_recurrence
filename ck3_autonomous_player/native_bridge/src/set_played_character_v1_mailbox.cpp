#include "xar_bridge/set_played_character_v1_mailbox.hpp"

#include <windows.h>

#include <atomic>
#include <charconv>
#include <limits>

namespace xar::ck3_11906 {

std::optional<std::int32_t>
ParseSetPlayedCharacterV1Step(std::string_view step) noexcept {
  if (!step.starts_with(kSetPlayedCharacterV1StepPrefix)) {
    return std::nullopt;
  }
  const auto raw = step.substr(kSetPlayedCharacterV1StepPrefix.size());
  if (raw.empty() || raw.front() == '0') {
    return std::nullopt;
  }
  std::uint64_t value = 0;
  const auto parsed =
      std::from_chars(raw.data(), raw.data() + raw.size(), value);
  if (parsed.ec != std::errc{} || parsed.ptr != raw.data() + raw.size() ||
      value == 0 ||
      value > static_cast<std::uint64_t>(
                  std::numeric_limits<std::int32_t>::max())) {
    return std::nullopt;
  }
  return static_cast<std::int32_t>(value);
}

bool ExecuteSetPlayedCharacterMailboxV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *context =
      static_cast<SetPlayedCharacterMailboxContextV1 *>(opaque_context);
  if (context == nullptr || context->mailbox == nullptr ||
      context->ticket.sequence == 0 || context->target_character_id <= 0 ||
      stamp.pump_epoch == 0 || stamp.thread_id == 0 || !stamp.paused ||
      stamp.tls_initialized_flag_address == 0 || stamp.tls_initialized != 1 ||
      stamp.tls_context == 0 || stamp.tls_main_thread_marker != 1 ||
      stamp.jomini_state == 0 || stamp.game_state == 0 ||
      GetCurrentThreadId() != stamp.thread_id) {
    return false;
  }
  auto &mailbox = *context->mailbox;
  if (mailbox.state.load(std::memory_order_acquire) !=
          MainThreadQueryMailboxStateV1::executing ||
      mailbox.stop_requested.load(std::memory_order_acquire) ||
      mailbox.failure_flags.load(std::memory_order_acquire) != 0 ||
      mailbox.published_sequence.load(std::memory_order_acquire) !=
          context->ticket.sequence ||
      mailbox.owner_thread_id.load(std::memory_order_acquire) !=
          stamp.thread_id ||
      mailbox.paused_owner_verified_pump_epochs.load(
          std::memory_order_acquire) <
          kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs ||
      mailbox.executor != &ExecuteSetPlayedCharacterMailboxV1 ||
      mailbox.executor_context != context) {
    return false;
  }

  ++context->executor_invocations;
  context->execution_stamp = stamp;
  game::Snapshot current{};
  if (!ReadSnapshot(context->bindings, current) ||
      current != context->expected_snapshot || !current.paused ||
      !current.map_ready || current.date_raw != stamp.date_raw) {
    context->result = game::SetPlayedCharacterResult::unavailable;
    return false;
  }
  context->result = SubmitSetPlayedCharacter(
      context->bindings, context->target_character_id);
  return true;
}

bool RunSetPlayedCharacterMailboxV1(
    SetPlayedCharacterMailboxContextV1 &context,
    std::uint32_t wait_budget_milliseconds) noexcept {
  if (context.mailbox == nullptr || context.target_character_id <= 0 ||
      wait_budget_milliseconds == 0) {
    return false;
  }
  context.ticket = {};
  context.execution_stamp = {};
  context.executor_invocations = 0;
  context.result = game::SetPlayedCharacterResult::unavailable;
  if (TrySubmitMainThreadQueryV1(
          *context.mailbox, &ExecuteSetPlayedCharacterMailboxV1, &context,
          context.ticket) != MainThreadQuerySubmitResultV1::submitted) {
    return false;
  }
  const auto wait = WaitForMainThreadQueryV1(
      *context.mailbox, context.ticket, wait_budget_milliseconds);
  const auto reclaim =
      ReclaimMainThreadQueryV1(*context.mailbox, context.ticket);
  return wait == MainThreadQueryWaitResultV1::completed &&
         reclaim == MainThreadQueryReclaimResultV1::reclaimed &&
         context.executor_invocations == 1;
}

std::string_view SetPlayedCharacterResultCodeV1(
    game::SetPlayedCharacterResult result) noexcept {
  using Result = game::SetPlayedCharacterResult;
  switch (result) {
  case Result::switched:
    return "switched";
  case Result::already_played:
    return "already_played";
  case Result::target_not_found:
    return "target_not_found";
  case Result::target_dead:
    return "target_dead";
  case Result::target_controlled:
    return "target_controlled";
  case Result::requires_paused:
    return "requires_paused";
  case Result::map_not_ready:
    return "map_not_ready";
  case Result::postcondition_failed:
    return "postcondition_failed";
  case Result::unavailable:
    return "unavailable";
  }
  return "unavailable";
}

} // namespace xar::ck3_11906
