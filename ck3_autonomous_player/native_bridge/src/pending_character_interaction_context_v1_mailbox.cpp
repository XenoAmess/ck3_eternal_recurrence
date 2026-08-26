#include "xar_bridge/pending_character_interaction_context_v1_mailbox.hpp"

#include <windows.h>

#include <atomic>
#include <charconv>
#include <string>

namespace xar::ck3_11906 {
namespace {

struct MailboxAccessProxyV1 {
  PendingCharacterInteractionContextMailboxContextV1 *query = nullptr;
  const MainThreadExecutionStampV1 *stamp = nullptr;
};

bool IsExecutingExactMailboxSlot(
    const PendingCharacterInteractionContextMailboxContextV1 &query,
    const MainThreadExecutionStampV1 &stamp) noexcept {
  if (query.mailbox == nullptr || query.ticket.sequence == 0 ||
      query.request.expected_snapshot_revision == 0 ||
      query.request.pending_interaction_id <= 0 ||
      query.request.played_character_id <= 0 || stamp.pump_epoch == 0 ||
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
         mailbox.executor ==
             &ExecutePendingCharacterInteractionContextMailboxQueryV1 &&
         mailbox.executor_context ==
             const_cast<PendingCharacterInteractionContextMailboxContextV1 *>(
                 &query);
}

bool ProxyIsMainThread(void *opaque) noexcept {
  const auto *proxy = static_cast<const MailboxAccessProxyV1 *>(opaque);
  return proxy != nullptr && proxy->query != nullptr &&
         proxy->stamp != nullptr &&
         IsExecutingExactMailboxSlot(*proxy->query, *proxy->stamp);
}

bool ProxyCaptureFrame(
    void *opaque, game::PendingCharacterInteractionFrameV1 &output) noexcept {
  const auto *proxy = static_cast<const MailboxAccessProxyV1 *>(opaque);
  if (proxy == nullptr || proxy->query == nullptr || proxy->stamp == nullptr ||
      !IsExecutingExactMailboxSlot(*proxy->query, *proxy->stamp)) {
    return false;
  }
  game::Snapshot snapshot{};
  if (!ReadSnapshot(proxy->query->bindings, snapshot) ||
      snapshot != proxy->query->expected_snapshot || !snapshot.paused ||
      !snapshot.map_ready || !snapshot.has_played_character ||
      !snapshot.played_character_alive ||
      snapshot.played_character_id !=
          proxy->query->request.played_character_id ||
      !snapshot.has_pending_character_interaction ||
      snapshot.pending_character_interaction_id !=
          proxy->query->request.pending_interaction_id ||
      snapshot.date_raw != proxy->stamp->date_raw) {
    return false;
  }
  output.snapshot_revision = proxy->query->request.expected_snapshot_revision;
  output.date_raw = snapshot.date_raw;
  output.paused = snapshot.paused;
  output.map_ready = snapshot.map_ready;
  return true;
}

bool ProxyReadMemory(void *opaque, const void *address, void *output,
                     std::size_t size) noexcept {
  const auto *proxy = static_cast<const MailboxAccessProxyV1 *>(opaque);
  return proxy != nullptr && proxy->query != nullptr &&
         proxy->stamp != nullptr &&
         proxy->query->access.read_memory != nullptr &&
         IsExecutingExactMailboxSlot(*proxy->query, *proxy->stamp) &&
         proxy->query->access.read_memory(proxy->query->access.context, address,
                                          output, size);
}

bool ProxyReadString(void *opaque, const void *native_string,
                     std::string &output) noexcept {
  const auto *proxy = static_cast<const MailboxAccessProxyV1 *>(opaque);
  return proxy != nullptr && proxy->query != nullptr &&
         proxy->stamp != nullptr &&
         proxy->query->access.read_string != nullptr &&
         IsExecutingExactMailboxSlot(*proxy->query, *proxy->stamp) &&
         proxy->query->access.read_string(proxy->query->access.context,
                                          native_string, output);
}

bool ProxyInvokeLocalRouting(void *opaque,
                             NativePendingInteractionLocalRoutingV1 function,
                             void *pending_interaction, void *played_character,
                             bool &output) noexcept {
  const auto *proxy = static_cast<const MailboxAccessProxyV1 *>(opaque);
  return proxy != nullptr && proxy->query != nullptr &&
         proxy->stamp != nullptr &&
         proxy->query->access.invoke_local_routing != nullptr &&
         IsExecutingExactMailboxSlot(*proxy->query, *proxy->stamp) &&
         proxy->query->access.invoke_local_routing(
             proxy->query->access.context, function, pending_interaction,
             played_character, output);
}

bool ProxyInvokeReplyValidator(
    void *opaque, NativePendingInteractionReplyValidatorV1 function,
    void *reply_command, bool &output) noexcept {
  const auto *proxy = static_cast<const MailboxAccessProxyV1 *>(opaque);
  return proxy != nullptr && proxy->query != nullptr &&
         proxy->stamp != nullptr &&
         proxy->query->access.invoke_reply_validator != nullptr &&
         IsExecutingExactMailboxSlot(*proxy->query, *proxy->stamp) &&
         proxy->query->access.invoke_reply_validator(
             proxy->query->access.context, function, reply_command, output);
}

bool ProxyInvokeTriggerEvaluator(
    void *opaque, NativePendingInteractionTriggerEvaluatorV1 function,
    void *trigger, const void *event_target_scope, bool &output) noexcept {
  const auto *proxy = static_cast<const MailboxAccessProxyV1 *>(opaque);
  return proxy != nullptr && proxy->query != nullptr &&
         proxy->stamp != nullptr &&
         proxy->query->access.invoke_trigger_evaluator != nullptr &&
         IsExecutingExactMailboxSlot(*proxy->query, *proxy->stamp) &&
         proxy->query->access.invoke_trigger_evaluator(
             proxy->query->access.context, function, trigger,
             event_target_scope, output);
}

bool ProxyInvokeCostEvaluator(
    void *opaque, NativePendingInteractionCostEvaluatorV1 function,
    const void *compiled_cost_block, const void *event_target_scope,
    std::array<std::int64_t,
               game::kPendingCharacterInteractionCostResourceCountV1>
        &output) noexcept {
  const auto *proxy = static_cast<const MailboxAccessProxyV1 *>(opaque);
  return proxy != nullptr && proxy->query != nullptr &&
         proxy->stamp != nullptr &&
         proxy->query->access.invoke_cost_evaluator != nullptr &&
         IsExecutingExactMailboxSlot(*proxy->query, *proxy->stamp) &&
         proxy->query->access.invoke_cost_evaluator(
             proxy->query->access.context, function, compiled_cost_block,
             event_target_scope, output);
}

bool ProxyInvokeCommonWarRelation(
    void *opaque, NativePendingInteractionCommonWarRelationV1 function,
    void *actor_character, void *recipient_character, void *&output) noexcept {
  const auto *proxy = static_cast<const MailboxAccessProxyV1 *>(opaque);
  return proxy != nullptr && proxy->query != nullptr &&
         proxy->stamp != nullptr &&
         proxy->query->access.invoke_common_war_relation != nullptr &&
         IsExecutingExactMailboxSlot(*proxy->query, *proxy->stamp) &&
         proxy->query->access.invoke_common_war_relation(
             proxy->query->access.context, function, actor_character,
             recipient_character, output);
}

bool ProxyResolveActiveWar(void *opaque, std::int32_t war_id,
                           void *&output) noexcept {
  output = nullptr;
  const auto *proxy = static_cast<const MailboxAccessProxyV1 *>(opaque);
  return proxy != nullptr && proxy->query != nullptr &&
         proxy->stamp != nullptr &&
         IsExecutingExactMailboxSlot(*proxy->query, *proxy->stamp) &&
         ResolvePendingCharacterInteractionActiveWarV1(
             proxy->query->bindings,
             reinterpret_cast<void *>(proxy->stamp->game_state), war_id,
             output);
}

bool ProxyInvokeTargetTypeRegistry(
    void *opaque, NativePendingInteractionTargetTypeRegistryGetterV1 function,
    void *&output) noexcept {
  const auto *proxy = static_cast<const MailboxAccessProxyV1 *>(opaque);
  return proxy != nullptr && proxy->query != nullptr &&
         proxy->stamp != nullptr &&
         proxy->query->access.invoke_target_type_registry != nullptr &&
         IsExecutingExactMailboxSlot(*proxy->query, *proxy->stamp) &&
         proxy->query->access.invoke_target_type_registry(
             proxy->query->access.context, function, output);
}

bool ProxyInvokeScriptIdentifierName(
    void *opaque, NativePendingInteractionScriptIdentifierNameV1 function,
    std::int32_t identifier, const std::string *&output) noexcept {
  const auto *proxy = static_cast<const MailboxAccessProxyV1 *>(opaque);
  return proxy != nullptr && proxy->query != nullptr &&
         proxy->stamp != nullptr &&
         proxy->query->access.invoke_script_identifier_name != nullptr &&
         IsExecutingExactMailboxSlot(*proxy->query, *proxy->stamp) &&
         proxy->query->access.invoke_script_identifier_name(
             proxy->query->access.context, function, identifier, output);
}

template <typename Integer>
bool ParseCanonicalPositiveIntegerField(std::string_view json,
                                        std::string_view key,
                                        Integer &output) noexcept {
  output = 0;
  const auto at = json.find(key);
  if (at == std::string_view::npos ||
      json.find(key, at + key.size()) != std::string_view::npos) {
    return false;
  }
  auto begin = at + key.size();
  while (begin < json.size() && (json[begin] == ' ' || json[begin] == '\t' ||
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

void MakeInternalUnavailable(
    PendingCharacterInteractionContextMailboxContextV1 &query,
    const MainThreadExecutionStampV1 &stamp) {
  query.result = {};
  query.result.status =
      game::PendingCharacterInteractionContextStatusV1::unavailable;
  query.result.snapshot_revision = query.request.expected_snapshot_revision;
  query.result.date_raw = stamp.date_raw;
  query.result.pending_interaction_id = query.request.pending_interaction_id;
  query.result.reason = "internal_error";
  const auto mark_unavailable = [](auto &legality) {
    legality.status =
        game::PendingCharacterInteractionSemanticStatusV1::unavailable;
    legality.allowed = false;
    legality.reason = "internal_error";
  };
  mark_unavailable(query.result.legality.accept);
  mark_unavailable(query.result.legality.reject);
  mark_unavailable(query.result.legality.block);
  mark_unavailable(query.result.legality.acknowledge);
  query.result.readiness.not_ready_reasons = {"internal_error"};
  query.read_result =
      game::ReadPendingCharacterInteractionContextResultV1::unavailable;
  query.completion =
      PendingCharacterInteractionContextMailboxCompletionV1::completed;
}

bool AllRepliesFailClosed(
    const game::PendingCharacterInteractionContextV1 &result) noexcept {
  return !result.legality.accept.allowed && !result.legality.reject.allowed &&
         !result.legality.block.allowed && !result.legality.acknowledge.allowed;
}

} // namespace

bool ParsePendingCharacterInteractionContextV1Step(
    std::string_view step) noexcept {
  return step == kPendingCharacterInteractionContextV1Step;
}

bool ParsePendingCharacterInteractionContextRequestV1(
    std::string_view json, std::uint64_t &expected_revision,
    std::int32_t &pending_interaction_id) noexcept {
  expected_revision = 0;
  pending_interaction_id = -1;
  std::uint64_t parsed_revision = 0;
  std::int32_t parsed_pending_id = 0;
  if (!ParseCanonicalPositiveIntegerField(
          json, "\"expected_revision\":", parsed_revision) ||
      !ParseCanonicalPositiveIntegerField(
          json, "\"pending_interaction_id\":", parsed_pending_id)) {
    return false;
  }
  expected_revision = parsed_revision;
  pending_interaction_id = parsed_pending_id;
  return true;
}

bool ExecutePendingCharacterInteractionContextMailboxQueryV1(
    void *opaque_context, const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *query =
      static_cast<PendingCharacterInteractionContextMailboxContextV1 *>(
          opaque_context);
  if (query == nullptr || !IsExecutingExactMailboxSlot(*query, stamp) ||
      query->completion !=
          PendingCharacterInteractionContextMailboxCompletionV1::not_executed ||
      query->executor_invocations != 0) {
    if (query != nullptr) {
      query->completion =
          PendingCharacterInteractionContextMailboxCompletionV1::
              infrastructure_rejected;
    }
    return false;
  }
  try {
    ++query->executor_invocations;
    query->execution_stamp = stamp;
    MailboxAccessProxyV1 proxy{query, &stamp};
    PendingCharacterInteractionAccessV1 access{};
    access.context = &proxy;
    access.capture_frame = &ProxyCaptureFrame;
    access.is_main_thread = &ProxyIsMainThread;
    access.read_memory =
        query->access.read_memory == nullptr ? nullptr : &ProxyReadMemory;
    access.read_string =
        query->access.read_string == nullptr ? nullptr : &ProxyReadString;
    access.invoke_local_routing = &ProxyInvokeLocalRouting;
    access.invoke_reply_validator = &ProxyInvokeReplyValidator;
    access.invoke_trigger_evaluator = &ProxyInvokeTriggerEvaluator;
    access.invoke_cost_evaluator = &ProxyInvokeCostEvaluator;
    access.invoke_common_war_relation = &ProxyInvokeCommonWarRelation;
    access.resolve_active_war = &ProxyResolveActiveWar;
    access.invoke_target_type_registry = &ProxyInvokeTargetTypeRegistry;
    access.invoke_script_identifier_name = &ProxyInvokeScriptIdentifierName;
    query->read_result = ReadPendingCharacterInteractionContextV1(
        query->environment, access, query->request, query->result);

    const bool identity_matches =
        query->result.snapshot_revision ==
            query->request.expected_snapshot_revision &&
        query->result.date_raw == stamp.date_raw &&
        query->result.pending_interaction_id ==
            query->request.pending_interaction_id;
    const bool typed_available =
        query->read_result ==
            game::ReadPendingCharacterInteractionContextResultV1::available &&
        query->result.status ==
            game::PendingCharacterInteractionContextStatusV1::available &&
        query->result.reason.empty() &&
        query->result.readiness.same_frame_ready;
    const bool typed_unavailable =
        query->read_result ==
            game::ReadPendingCharacterInteractionContextResultV1::unavailable &&
        query->result.status ==
            game::PendingCharacterInteractionContextStatusV1::unavailable &&
        !query->result.reason.empty() && AllRepliesFailClosed(query->result) &&
        !query->result.readiness.interaction_semantic_decision_ready;
    const bool typed_invalid =
        query->read_result ==
            game::ReadPendingCharacterInteractionContextResultV1::invalid &&
        query->result.status ==
            game::PendingCharacterInteractionContextStatusV1::invalid &&
        !query->result.reason.empty() && AllRepliesFailClosed(query->result) &&
        !query->result.readiness.interaction_semantic_decision_ready;
    if (identity_matches &&
        (typed_available || typed_unavailable || typed_invalid)) {
      query->completion =
          PendingCharacterInteractionContextMailboxCompletionV1::completed;
      return true;
    }
    MakeInternalUnavailable(*query, stamp);
    return true;
  } catch (...) {
    try {
      MakeInternalUnavailable(*query, stamp);
      return true;
    } catch (...) {
      query->completion =
          PendingCharacterInteractionContextMailboxCompletionV1::
              infrastructure_rejected;
      return false;
    }
  }
}

std::string_view PendingCharacterInteractionContextFailureMessageV1(
    MainThreadQueryWaitResultV1 wait,
    PendingCharacterInteractionContextMailboxCompletionV1 completion,
    bool completion_snapshot_stable) noexcept {
  if (wait != MainThreadQueryWaitResultV1::completed) {
    switch (wait) {
    case MainThreadQueryWaitResultV1::executor_failed:
      return "application-main pending-interaction executor failed";
    case MainThreadQueryWaitResultV1::infrastructure_failed:
      return "application-main pending-interaction boundary drifted";
    case MainThreadQueryWaitResultV1::cancelled:
      return "application-main pending-interaction query was cancelled";
    case MainThreadQueryWaitResultV1::timeout_cancelled_before_execution:
      return "application-main pending-interaction query timed out";
    case MainThreadQueryWaitResultV1::timeout_executor_already_running:
      return "application-main pending-interaction executor is still running";
    case MainThreadQueryWaitResultV1::ticket_mismatch:
      return "application-main pending-interaction ticket mismatch";
    case MainThreadQueryWaitResultV1::completed:
      break;
    }
  }
  if (completion ==
      PendingCharacterInteractionContextMailboxCompletionV1::completed) {
    return completion_snapshot_stable
               ? "application-main pending-interaction result is inconsistent"
               : "pending-interaction completion snapshot changed";
  }
  if (completion ==
      PendingCharacterInteractionContextMailboxCompletionV1::frame_changed) {
    return "pending-interaction application-main frame changed";
  }
  return "application-main pending-interaction executor was rejected";
}

} // namespace xar::ck3_11906
