#include "active_scheme_sway_formal_private_transport_v1.hpp"

#include <windows.h>

#include <atomic>
#include <charconv>
#include <cstring>

namespace xar::ck3_11906 {
namespace {

using namespace xar::bridge;

struct SourceContext {
  ActiveSchemeSwayFormalPrivateCommandV1 *command = nullptr;
  const MainThreadExecutionStampV1 *stamp = nullptr;
};

bool CaptureFrame(void *opaque,
                  ActiveSchemeStateV1PrivateSourceFrame &frame) noexcept {
  const auto *context = static_cast<SourceContext *>(opaque);
  if (context == nullptr || context->command == nullptr ||
      context->stamp == nullptr) return false;
  game::Snapshot current{};
  if (!ReadSnapshot(context->command->bindings, current) ||
      current != context->command->expected_snapshot || !current.paused ||
      !current.map_ready || !current.has_played_character ||
      !current.played_character_alive ||
      current.date_raw != context->stamp->date_raw) {
    context->command->frame_changed = true;
    return false;
  }
  frame = {context->stamp->pump_epoch, current.date_raw,
           current.played_character_id, true};
  return true;
}

bool ValidMailbox(const ActiveSchemeSwayFormalPrivateCommandV1 &command,
                  const MainThreadExecutionStampV1 &stamp) noexcept {
  if (command.mailbox == nullptr || command.ticket.sequence == 0 ||
      command.expected_revision == 0 || command.target_character_id == 0 ||
      command.invocations != 0 || stamp.pump_epoch == 0 ||
      stamp.thread_id == 0 || !stamp.paused ||
      stamp.tls_initialized_flag_address == 0 || stamp.tls_initialized != 1 ||
      stamp.tls_context == 0 || stamp.tls_main_thread_marker != 1 ||
      stamp.jomini_state == 0 || stamp.game_state == 0 ||
      GetCurrentThreadId() != stamp.thread_id) return false;
  const auto &mailbox = *command.mailbox;
  return mailbox.state.load(std::memory_order_acquire) ==
             MainThreadQueryMailboxStateV1::executing &&
         !mailbox.stop_requested.load(std::memory_order_acquire) &&
         mailbox.failure_flags.load(std::memory_order_acquire) == 0 &&
         mailbox.published_sequence.load(std::memory_order_acquire) ==
             command.ticket.sequence &&
         mailbox.owner_thread_id.load(std::memory_order_acquire) ==
             stamp.thread_id &&
         mailbox.paused_owner_verified_pump_epochs.load(
             std::memory_order_acquire) >=
             kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs &&
         mailbox.executor == &ExecuteActiveSchemeSwayFormalPrivateCommandV1 &&
         mailbox.executor_context == &command;
}

bool MatchesSway(const ActiveSchemeStateV1PrivateRow &row,
                 std::int64_t actor, std::uint32_t target) noexcept {
  return row.owner_character_id == actor &&
         std::strncmp(row.scheme_type_key.data(), "sway", 5) == 0 &&
         row.target_kind == ActiveSchemeStateV1PrivateTargetKind::character &&
         row.target_id == target;
}

} // namespace

bool ParseActiveSchemeSwayFormalStepV1(std::string_view step,
                                       ActiveSchemeSwayFormalModeV1 &mode,
                                       std::uint32_t &target_id) noexcept {
  target_id = 0;
  std::string_view suffix;
  if (step.starts_with(kActiveSchemeSwayFormalSubmitPrefixV1)) {
    mode = ActiveSchemeSwayFormalModeV1::submit;
    suffix = step.substr(kActiveSchemeSwayFormalSubmitPrefixV1.size());
  } else if (step.starts_with(kActiveSchemeSwayFormalReceiptPrefixV1)) {
    mode = ActiveSchemeSwayFormalModeV1::receipt;
    suffix = step.substr(kActiveSchemeSwayFormalReceiptPrefixV1.size());
  } else {
    return false;
  }
  if (suffix.empty() || suffix.front() == '0') return false;
  const auto [end, error] = std::from_chars(
      suffix.data(), suffix.data() + suffix.size(), target_id);
  return error == std::errc{} && end == suffix.data() + suffix.size() &&
         target_id != 0;
}

bool ExecuteActiveSchemeSwayFormalPrivateCommandV1(
    void *opaque, const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *command = static_cast<ActiveSchemeSwayFormalPrivateCommandV1 *>(opaque);
  if (command == nullptr || !ValidMailbox(*command, stamp)) return false;
  try {
    ++command->invocations;
    game::Snapshot current{};
    if (!ReadSnapshot(command->bindings, current) ||
        current != command->expected_snapshot || !current.paused ||
        !current.map_ready || !current.has_played_character ||
        !current.played_character_alive || current.date_raw != stamp.date_raw ||
        current.played_character_id <= 0 ||
        static_cast<std::uint32_t>(current.played_character_id) ==
            command->target_character_id) {
      command->frame_changed = true;
      command->failure = "published_frame_changed";
      command->completed = true;
      return true;
    }
    SourceContext source_context{command, &stamp};
    ActiveSchemeStateV1PrivateSourceAccess access{};
    access.context = &source_context;
    access.capture_frame = &CaptureFrame;
    access.current_thread_id = GetCurrentThreadId();
    access.application_main_thread_id = stamp.thread_id;
    const auto module_base =
        reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
    ActiveSchemeStateV1PrivateNativeEnvironment source_environment{};
    source_environment.binding_enabled = true;
    source_environment.exact_build_admitted = command->bindings.enabled;
    source_environment.admitted_executable_sha256 =
        kActiveSchemeStateV1PrivateObserverExecutableSha256;
    source_environment.admitted_game_version =
        kActiveSchemeStateV1PrivateNativeBinderGameVersion;
    source_environment.module_base = module_base;
    ActiveSchemeStateV1PrivateNativeBindingState source_state{};
    if (!BindActiveSchemeStateV1PrivateNative(
            source_environment, source_state, access)) {
      command->failure = "native_scheme_source_bind_red";
      command->completed = true;
      return true;
    }
    ActiveSchemePreconditionCommandBindersV1PrivateEnvironment environment{};
    environment.binding_enabled = true;
    environment.exact_build_admitted = command->bindings.enabled;
    environment.admitted_executable_sha256 =
        kActiveSchemeStateV1PrivateObserverExecutableSha256;
    environment.admitted_game_version =
        kActiveSchemeStateV1PrivateNativeBinderGameVersion;
    environment.module_base = module_base;
    environment.source_access = access;
    ActiveSchemePreconditionCommandBindersV1PrivateState binder{};
    ActiveSchemePreconditionCommandBindersV1PrivateReadiness readiness{};
    if (!BindActiveSchemePreconditionCommandBindersV1Private(
            environment, binder, readiness)) {
      command->failure = "native_scheme_action_bind_red:";
      command->failure +=
          ActiveSchemePreconditionCommandBindersV1PrivateFailureName(
              readiness.failure);
      command->completed = true;
      return true;
    }
    const ActiveSchemePausedLiveNativeGlueV1PrivateExecution execution{
        GetCurrentThreadId(), stamp.thread_id};
    ActiveSchemePreconditionCommandBindersV1PrivateFailure failure{};
    if (command->mode == ActiveSchemeSwayFormalModeV1::receipt) {
      const auto status = VerifyActiveSchemePreconditionCommandReceiptV1Private(
          binder, execution, command->prior_ack, command->receipt, failure);
      if (status != ActiveSchemeSemanticActionV1PrivateReceiptStatus::applied ||
          failure != ActiveSchemePreconditionCommandBindersV1PrivateFailure::none) {
        command->failure = "native_sway_receipt_red:";
        command->failure += failure !=
                ActiveSchemePreconditionCommandBindersV1PrivateFailure::none
            ? ActiveSchemePreconditionCommandBindersV1PrivateFailureName(failure)
            : ActiveSchemeSemanticActionV1PrivateFailureName(
                  command->receipt.failure);
      }
      command->completed = true;
      return true;
    }
    if (!CaptureActiveSchemePreconditionCommandSnapshotV1Private(
            binder, execution, command->observed, failure)) {
      command->failure = "native_scheme_observation_red:";
      command->failure += ActiveSchemeStateV1PrivateSourceFailureName(
          binder.glue.last_source_failure);
      command->completed = true;
      return true;
    }
    // The source read and action run on separate owning-thread pump epochs.
    // Require a fresh action frame while retaining the same container/date.
    if (command->observed.capture_epoch <= command->expected_capture_epoch ||
        command->observed.container_generation !=
            command->expected_container_generation ||
        command->observed.date_raw != current.date_raw ||
        command->observed.played_character_id !=
            current.played_character_id) {
      command->failure = "sway_source_snapshot_changed";
      command->completed = true;
      return true;
    }
    for (std::size_t i = 0; i < command->observed.row_count; ++i) {
      if (MatchesSway(command->observed.rows[i],
                      current.played_character_id,
                      command->target_character_id)) {
        command->failure = "matching_sway_already_active";
        command->completed = true;
        return true;
      }
    }
    if (!ReadGiftOpinionExact11906V1(
            module_base, command->bindings, command->target_character_id,
            static_cast<std::uint32_t>(current.played_character_id),
            command->target_opinion) ||
        !command->target_opinion.query_complete ||
        command->target_opinion.recipient_opinion_of_player !=
            command->expected_target_opinion_of_actor) {
      command->failure = "sway_target_opinion_changed_or_red";
      command->completed = true;
      return true;
    }
    ActiveSchemeSemanticActionV1PrivateRequest request{};
    request.request_id = command->action_id;
    request.interaction_key = "sway_interaction";
    request.actor_character_id = current.played_character_id;
    request.target_kind = ActiveSchemeStateV1PrivateTargetKind::character;
    request.target_id = command->target_character_id;
    request.expected_capture_epoch = command->observed.capture_epoch;
    request.expected_container_generation =
        command->observed.container_generation;
    request.expected_date_raw = command->observed.date_raw;
    const auto status = ExecuteActiveSchemePreconditionCommandV1Private(
        binder, execution, request, command->ack, failure);
    if (status != ActiveSchemeSemanticActionV1PrivateAckStatus::
                      submitted_verification_pending ||
        failure != ActiveSchemePreconditionCommandBindersV1PrivateFailure::none) {
      command->failure = "native_sway_submit_rejected:";
      command->failure += failure !=
              ActiveSchemePreconditionCommandBindersV1PrivateFailure::none
          ? ActiveSchemePreconditionCommandBindersV1PrivateFailureName(failure)
          : ActiveSchemeSemanticActionV1PrivateFailureName(
                command->ack.failure);
    }
    command->completed = true;
    return true;
  } catch (...) {
    return false;
  }
}

std::string SerializeActiveSchemeSwayFormalPrivateCommandV1(
    const ActiveSchemeSwayFormalPrivateCommandV1 &command) {
  if (!command.completed || !command.failure.empty()) return {};
  if (command.mode == ActiveSchemeSwayFormalModeV1::submit) {
    const auto &ack = command.ack;
    if (ack.status != ActiveSchemeSemanticActionV1PrivateAckStatus::
                          submitted_verification_pending ||
        !ack.verification_pending || !ack.submit_attempted ||
        ack.submit_call_count != 1 || ack.request_id != command.action_id ||
        ack.interaction_key != "sway_interaction" ||
        ack.scheme_type_key != "sway" ||
        ack.target_id != command.target_character_id) return {};
    return "{\"schema\":\"active-scheme-sway-formal-private-v1\","
           "\"stage\":\"submitted_verification_pending\","
           "\"action_id\":\"" + ack.request_id +
           "\",\"actor_character_id\":" +
           std::to_string(ack.actor_character_id) +
           ",\"target_character_id\":" +
           std::to_string(ack.target_id) +
           ",\"pre_capture_epoch\":" +
           std::to_string(ack.pre_capture_epoch) +
           ",\"pre_container_generation\":" +
           std::to_string(ack.pre_container_generation) +
           ",\"pre_date_raw\":" + std::to_string(ack.pre_date_raw) +
           ",\"submit_call_count\":1,\"receipt_pending\":true}";
  }
  const auto &receipt = command.receipt;
  if (receipt.status !=
          ActiveSchemeSemanticActionV1PrivateReceiptStatus::applied ||
      !receipt.postcondition_verified ||
      receipt.request_id != command.action_id ||
      receipt.scheme_instance_id == 0) return {};
  return "{\"schema\":\"active-scheme-sway-formal-private-v1\","
         "\"stage\":\"applied\",\"action_id\":\"" +
         receipt.request_id + "\",\"post_capture_epoch\":" +
         std::to_string(receipt.post_capture_epoch) +
         ",\"post_container_generation\":" +
         std::to_string(receipt.post_container_generation) +
         ",\"post_date_raw\":" + std::to_string(receipt.post_date_raw) +
         ",\"scheme_instance_id\":" +
         std::to_string(receipt.scheme_instance_id) +
         ",\"scheme_instance_generation\":" +
         std::to_string(receipt.scheme_instance_generation) +
         ",\"postcondition_verified\":true}";
}

} // namespace xar::ck3_11906
